"""
Módulo de conexión a la base de datos MySQL.

Ítem 4.5 de PRIORIDADES (A-11, NC-003): antes había UNA sola conexión que
compartían todos los hilos de Flask; con 500 usuarios falló el 56 % de las
peticiones ('MySQL Connection not available', 'bytearray index out of range').

Ahora hay un pool de conexiones: un "estante" con varias conexiones abiertas.
Cada operación pide una con obtener_conexion(), la usa y la devuelve con
conexion.close() dentro de un finally. En una conexión del pool, close() no
cierra la conexión real: la regresa al estante para que la use otra petición.

Los DAO y la API no escriben ese try/finally a mano: usan conexion_y_cursor(),
que lo hace en un solo lugar:

    with conexion_y_cursor(self._conexion_bd) as (conexion, cursor):
        cursor.execute(sql, parametros)
        conexion.commit()
    # aquí el cursor ya está cerrado y la conexión devuelta, aunque haya habido error

ConexionBD sigue siendo Singleton (un solo objeto por proceso), pero lo único
que comparte es el pool, que la librería protege para varios hilos.

Ítem 4.9 (A-15): autocommit está apagado (config/db_config.py). Toda escritura
termina con conexion.commit() y, si falla, conexion.rollback(). Al devolver una
conexión, el pool "limpia" su sesión (pool_reset_session=True): descarta lo que
haya quedado sin confirmar, incluida la transacción que abre cualquier SELECT, y
vuelve a poner autocommit y sql_mode. Así la siguiente petición nunca recibe una
conexión con cambios a medias de otra.
"""

import logging
import threading
import time
from contextlib import contextmanager

from mysql.connector import Error
from mysql.connector.errors import InterfaceError, PoolError
from mysql.connector.pooling import MySQLConnectionPool

from config.db_config import DB_CONFIG, POOL_SIZE

_log = logging.getLogger(__name__)

# El pool de mysql-connector no espera: si todas las conexiones están prestadas
# lanza PoolError al instante. Se reintenta cada _PAUSA_REINTENTO segundos hasta
# ESPERA_MAXIMA_SEGUNDOS; si ninguna se libera, se devuelve None (503).
ESPERA_MAXIMA_SEGUNDOS = 5
_PAUSA_REINTENTO = 0.05


class ConexionBD:
    """Presta conexiones de un pool MySQL (una por operación, siempre devuelta)."""

    _instancia = None
    _candado_instancia = threading.Lock()

    def __new__(cls):
        if cls._instancia is None:
            # El candado evita que dos hilos creen dos objetos a la vez
            with cls._candado_instancia:
                if cls._instancia is None:
                    instancia = super().__new__(cls)
                    instancia._pool = None
                    instancia._candado_pool = threading.Lock()
                    cls._instancia = instancia
        return cls._instancia

    def _obtener_pool(self):
        """Crea el pool la primera vez que se necesita (una sola vez, aunque lo pidan varios hilos)."""
        if self._pool is None:
            with self._candado_pool:
                if self._pool is None:
                    # pool_reset_session=True ya es el valor por defecto; se escribe
                    # para que nadie lo apague sin ver que de eso depende el 4.9
                    self._pool = MySQLConnectionPool(
                        pool_name="petconnect", pool_size=POOL_SIZE,
                        pool_reset_session=True, **DB_CONFIG
                    )
        return self._pool

    @staticmethod
    def _registrar_fallo(e):
        # Solo el tipo y el número de error: el mensaje puede traer el usuario y
        # el host de la BD ("Access denied for user ...@...").
        _log.error("No se pudo conectar a la base de datos: %s (errno %s)",
                   type(e).__name__, getattr(e, "errno", None))

    def obtener_conexion(self):
        """
        Presta una conexión del pool. Quien la pide debe devolverla con
        conexion.close() en un finally. Devuelve None si la BD no responde o si
        el pool sigue lleno después de ESPERA_MAXIMA_SEGUNDOS.
        """
        try:
            pool = self._obtener_pool()
        except Error as e:
            self._registrar_fallo(e)
            return None

        limite = time.monotonic() + ESPERA_MAXIMA_SEGUNDOS
        while True:
            try:
                return pool.get_connection()
            except PoolError:
                # Todas prestadas: se espera un poco a que alguna petición devuelva la suya
                if time.monotonic() >= limite:
                    _log.error("Pool de conexiones lleno: ninguna se libero en %s s",
                               ESPERA_MAXIMA_SEGUNDOS)
                    return None
                time.sleep(_PAUSA_REINTENTO)
            except Error as e:
                self._registrar_fallo(e)
                return None

    def cerrar_conexion(self):
        """
        Cierra las conexiones libres del pool y lo descarta. La próxima llamada a
        obtener_conexion() crea otro con la configuración actual (las pruebas con
        MariaDB lo usan para cambiar de base de datos). La consola lo llama al salir.
        """
        with self._candado_pool:
            pool, self._pool = self._pool, None
        if pool is None:
            return
        try:
            # La librería no tiene un método público para cerrar el pool
            pool._remove_connections()
        except Error as e:
            _log.error("Al cerrar el pool de conexiones: %s", type(e).__name__)


@contextmanager
def conexion_y_cursor(conexion_bd, dictionary=False):
    """
    Presta una conexión del pool y un cursor para usarlos en un bloque with.
    Al salir del bloque (normal o por error) cierra el cursor y devuelve la
    conexión al pool: es el try/finally del ítem 4.5 escrito una sola vez.

    Si la BD no responde lanza InterfaceError: la API la contesta como 503 y los
    DAO viejos la atrapan como cualquier otro Error de la BD.
    """
    conexion = conexion_bd.obtener_conexion()
    if conexion is None:
        raise InterfaceError("No hay conexion con la base de datos")
    try:
        cursor = conexion.cursor(dictionary=dictionary)
        try:
            yield conexion, cursor
        finally:
            cursor.close()
    finally:
        conexion.close()      # en el pool, close() la devuelve al estante
