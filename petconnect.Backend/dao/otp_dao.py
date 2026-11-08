"""
DAO para la tabla 'otp_pendientes' (item 4.6 de PRIORIDADES, A-12, NC-003): los
codigos de un solo uso del registro y del inicio de sesion.

Antes los codigos vivian en un diccionario en la memoria de la API: con varios
procesos (Gunicorn) el codigo se guardaba en uno y la verificacion llegaba a otro,
y al reiniciar se perdian. En la BD los ven todos los procesos.

Este DAO solo guarda, lee y borra filas: las reglas (10 minutos, 5 fallos, reenvios)
estan en otp/servicio.py (AlmacenOTP). Las operaciones que cuentan intentos o
reenvios son una sola sentencia que suma y revisa el limite a la vez (la condicion
va en el WHERE): la BD lo hace de una vez (atomico), asi dos peticiones a la vez
nunca pasan del limite.

Como SolicitudDAO, NO se traga los errores de la BD: los deja subir para que la API
responda 503 (sin conexion) o 500. Cada metodo pide una sola conexion y la devuelve
con conexion_y_cursor (item 4.5). Nunca imprime el correo, el nombre ni el codigo
(datos personales, Ley 1581).
"""

from conexion.conexion_bd import ConexionBD, conexion_y_cursor

# Columnas de una fila, en el orden del INSERT
COLUMNAS = ("correo", "proposito", "codigo_cifrado", "intentos", "reenvios", "vence",
            "ultimo_envio", "nombre", "password_hash", "id_usuario",
            "fecha_autorizacion_datos", "version_politica_datos")


class OtpDAO:
    """Acceso a datos para la tabla otp_pendientes."""

    _OBTENER = """
        SELECT correo, proposito, codigo_cifrado, intentos, reenvios, vence, ultimo_envio,
               nombre, password_hash, id_usuario, fecha_autorizacion_datos,
               version_politica_datos
        FROM otp_pendientes
        WHERE correo = %s AND proposito = %s
    """

    # Pedir un codigo nuevo reemplaza la fila entera (contadores en cero)
    _GUARDAR = """
        INSERT INTO otp_pendientes (correo, proposito, codigo_cifrado, intentos, reenvios,
                                    vence, ultimo_envio, nombre, password_hash, id_usuario,
                                    fecha_autorizacion_datos, version_politica_datos)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            codigo_cifrado = VALUES(codigo_cifrado), intentos = VALUES(intentos),
            reenvios = VALUES(reenvios), vence = VALUES(vence),
            ultimo_envio = VALUES(ultimo_envio), nombre = VALUES(nombre),
            password_hash = VALUES(password_hash), id_usuario = VALUES(id_usuario),
            fecha_autorizacion_datos = VALUES(fecha_autorizacion_datos),
            version_politica_datos = VALUES(version_politica_datos)
    """

    _BORRAR = "DELETE FROM otp_pendientes WHERE correo = %s AND proposito = %s"

    _BORRAR_VENCIDOS = "DELETE FROM otp_pendientes WHERE vence < %s"

    # Gasta un intento solo si queda alguno y el codigo no vencio
    _RESERVAR_INTENTO = """
        UPDATE otp_pendientes SET intentos = intentos + 1
        WHERE correo = %s AND proposito = %s AND intentos < %s AND vence >= %s
    """

    _DEVOLVER_INTENTO = """
        UPDATE otp_pendientes SET intentos = intentos - 1
        WHERE correo = %s AND proposito = %s AND intentos > 0
    """

    _ANOTAR_REENVIO = """
        UPDATE otp_pendientes SET reenvios = reenvios + 1, ultimo_envio = %s
        WHERE correo = %s AND proposito = %s AND vence >= %s AND intentos < %s
          AND ultimo_envio <= %s AND reenvios < %s
    """

    def __init__(self):
        self._conexion_bd = ConexionBD()

    def obtener(self, correo, proposito):
        """La fila pendiente (diccionario con COLUMNAS) o None si no hay."""
        with conexion_y_cursor(self._conexion_bd, dictionary=True) as (conexion, cursor):
            cursor.execute(self._OBTENER, (correo, proposito))
            return cursor.fetchone()

    def guardar(self, fila):
        """Crea la fila o la reemplaza si ya habia una para ese correo y proposito."""
        with conexion_y_cursor(self._conexion_bd) as (conexion, cursor):
            self._escribir(conexion, cursor, self._GUARDAR,
                           tuple(fila[columna] for columna in COLUMNAS))

    def borrar(self, correo, proposito):
        with conexion_y_cursor(self._conexion_bd) as (conexion, cursor):
            self._escribir(conexion, cursor, self._BORRAR, (correo, proposito))

    def borrar_vencidos(self, ahora):
        """Borra todos los codigos vencidos (de cualquier correo). Devuelve cuantos."""
        with conexion_y_cursor(self._conexion_bd) as (conexion, cursor):
            self._escribir(conexion, cursor, self._BORRAR_VENCIDOS, (ahora,))
            return cursor.rowcount

    def reservar_intento(self, correo, proposito, ahora, max_intentos):
        """Suma 1 a los intentos si quedan y no vencio. True si se pudo."""
        with conexion_y_cursor(self._conexion_bd) as (conexion, cursor):
            self._escribir(conexion, cursor, self._RESERVAR_INTENTO,
                           (correo, proposito, max_intentos, ahora))
            return cursor.rowcount == 1

    def devolver_intento(self, correo, proposito):
        """Resta el intento reservado (acertar el codigo no gasta intentos)."""
        with conexion_y_cursor(self._conexion_bd) as (conexion, cursor):
            self._escribir(conexion, cursor, self._DEVOLVER_INTENTO, (correo, proposito))

    def anotar_reenvio(self, correo, proposito, ahora, espera, max_intentos, max_reenvios):
        """Anota un reenvio si se puede (ver AlmacenOTP.para_reenviar). True si se anoto."""
        with conexion_y_cursor(self._conexion_bd) as (conexion, cursor):
            self._escribir(conexion, cursor, self._ANOTAR_REENVIO,
                           (ahora, correo, proposito, ahora, max_intentos, ahora - espera,
                            max_reenvios))
            return cursor.rowcount == 1

    @staticmethod
    def _escribir(conexion, cursor, sql, parametros):
        """Ejecuta y confirma; si la BD falla, deshace y deja subir el error."""
        try:
            cursor.execute(sql, parametros)
            conexion.commit()
        except Exception:
            conexion.rollback()
            raise
