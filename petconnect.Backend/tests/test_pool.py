"""
Pruebas del pool de conexiones (item 4.5 de PRIORIDADES, A-11, NC-003).

Antes habia UNA conexion a MySQL compartida por todos los hilos de Flask: con 500
usuarios fallo el 56 % de las peticiones. Ahora cada operacion pide una conexion al
pool, la usa y la devuelve (try/finally en conexion_y_cursor). Estas pruebas cuidan:

- DB_POOL_SIZE: vacio = 10, entre 1 y 32; otro valor detiene el arranque.
- ConexionBD con un pool falso: se crea una sola vez aunque lo pidan varios hilos,
  espera si esta lleno, devuelve None (503) si nadie suelta una conexion, no deja
  datos de la BD en el log y cerrar_conexion() lo descarta.
- conexion_y_cursor: cierra el cursor y devuelve la conexion, tambien con error.
- Fugas (conexion que se pide y nunca se devuelve): cada metodo de los 5 DAO y cada
  ruta del inventario de tests/test_endpoints.py devuelven todas las conexiones y
  cierran todos los cursores, con la BD vacia, con error de MySQL y con error
  inesperado. Lo mismo main.py (consola) y seed.py.
- PruebasPoolEnBD (solo con PETCONNECT_PRUEBA_BD=1, en una base temporal): 30 hilos
  consultan a la vez sin cruzarse, el modo estricto (NC-009) sigue tras devolver y
  volver a pedir una conexion, y muchas consultas seguidas no agotan el pool.

Sin PETCONNECT_PRUEBA_BD no se usa MariaDB ni se lee .env (_importar_api). Los
correos son inventados (Ley 1581).

Ejecutar desde petconnect.Backend, con el entorno virtual activo:
    python -m unittest discover -s tests -p "test_pool.py" -v
"""
import contextlib
import importlib
import inspect
import io
import os
import sys
import threading
import time
import unittest
from unittest import mock

from mysql.connector import errors as errores_bd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_errores import _importar_api  # noqa: E402
from test_endpoints import RUTAS_PRIVADAS, RUTAS_PUBLICAS, _url  # noqa: E402

# Datos inventados (Ley 1581)
CORREO = "pool.prueba@ejemplo.test"
CLAVE = "Firulais2026!"
ID_USUARIO = 7
BD_PRUEBA_POOL = "petconnect_prueba_pool"


def _modulo_conexion():
    # Se importa dentro de cada prueba: con el codigo viejo (contraprueba) falla
    # cada clase por separado y no todo el archivo de una vez.
    return importlib.import_module("conexion.conexion_bd")


# ---------------------------------------------------------------------------
# Pool falso: un "estante" con N conexiones que cuenta cuantas estan prestadas
# ---------------------------------------------------------------------------

class _ConexionFalsa:
    def __init__(self, pool):
        self._pool = pool

    def close(self):
        self._pool.devolver(self)


class _PoolFalso:
    def __init__(self, tamano):
        self._libres = [_ConexionFalsa(self) for _ in range(tamano)]
        self._candado = threading.Lock()
        self.prestadas = 0
        self.maximo_prestadas = 0
        self._remove_connections = mock.Mock(return_value=tamano)

    def get_connection(self):
        with self._candado:
            if not self._libres:
                raise errores_bd.PoolError("Failed getting connection; pool exhausted")
            self.prestadas += 1
            self.maximo_prestadas = max(self.maximo_prestadas, self.prestadas)
            return self._libres.pop()

    def devolver(self, conexion):
        with self._candado:
            self.prestadas -= 1
            self._libres.append(conexion)


# ---------------------------------------------------------------------------
# 1. Tamano del pool (DB_POOL_SIZE)
# ---------------------------------------------------------------------------

class PruebasTamanoPool(unittest.TestCase):

    def setUp(self):
        self.tamano_pool = importlib.import_module("config.db_config").tamano_pool

    def test_vacio_usa_10(self):
        for texto in (None, "", "   "):
            with self.subTest(texto=texto):
                self.assertEqual(self.tamano_pool(texto), 10)

    def test_valores_validos(self):
        for texto, esperado in (("1", 1), ("5", 5), (" 10 ", 10), ("32", 32)):
            with self.subTest(texto=texto):
                self.assertEqual(self.tamano_pool(texto), esperado)

    def test_valores_no_validos_detienen_el_arranque_con_mensaje_claro(self):
        for texto in ("0", "-1", "33", "abc", "5.5", "10 conexiones"):
            with self.subTest(texto=texto):
                with self.assertRaises(ValueError) as error:
                    self.tamano_pool(texto)
                self.assertIn("DB_POOL_SIZE", str(error.exception))
                self.assertIn("entre 1 y 32", str(error.exception))


# ---------------------------------------------------------------------------
# 2. ConexionBD con un pool falso
# ---------------------------------------------------------------------------

class PruebasConexionBD(unittest.TestCase):

    def setUp(self):
        self.modulo = _modulo_conexion()
        self.bd = self.modulo.ConexionBD()
        pool_anterior = self.bd._pool
        self.bd._pool = None

        def restaurar():
            self.bd._pool = pool_anterior
        self.addCleanup(restaurar)

        self.pools = []

        def crear_pool(**config):
            time.sleep(0.05)     # abre la ventana para que dos hilos choquen
            pool = _PoolFalso(config["pool_size"])
            self.pools.append(pool)
            return pool

        parche = mock.patch.object(self.modulo, "MySQLConnectionPool", side_effect=crear_pool)
        self.MySQLConnectionPool = parche.start()
        self.addCleanup(parche.stop)

    def _tamano(self, n):
        parche = mock.patch.object(self.modulo, "POOL_SIZE", n)
        parche.start()
        self.addCleanup(parche.stop)

    def _en_hilos(self, cantidad, trabajo):
        """Corre trabajo() en varios hilos que arrancan a la vez; devuelve sus resultados."""
        barrera = threading.Barrier(cantidad)
        resultados, errores = [], []

        def hilo():
            barrera.wait()
            try:
                resultados.append(trabajo())
            except Exception as e:      # noqa: BLE001 - se reporta abajo
                errores.append(e)

        hilos = [threading.Thread(target=hilo) for _ in range(cantidad)]
        for h in hilos:
            h.start()
        for h in hilos:
            h.join(timeout=20)
        self.assertEqual(errores, [])
        return resultados

    def test_es_singleton(self):
        self.assertIs(self.modulo.ConexionBD(), self.bd)

    def test_el_pool_se_crea_una_sola_vez_con_la_configuracion_del_env(self):
        def pedir_y_devolver():
            conexion = self.bd.obtener_conexion()
            conexion.close()
            return conexion

        self._en_hilos(20, pedir_y_devolver)
        self.MySQLConnectionPool.assert_called_once()
        config = self.MySQLConnectionPool.call_args.kwargs
        self.assertEqual(config["pool_size"], self.modulo.POOL_SIZE)
        self.assertEqual(config["pool_name"], "petconnect")
        db_config = importlib.import_module("config.db_config").DB_CONFIG
        for clave, valor in db_config.items():
            self.assertEqual(config[clave], valor)     # incluye sql_mode estricto (NC-009)

    def test_cada_hilo_recibe_su_propia_conexion_sin_pasar_del_tamano(self):
        self._tamano(3)

        def usar_un_rato():
            conexion = self.bd.obtener_conexion()
            self.assertIsNotNone(conexion)
            try:
                time.sleep(0.02)
            finally:
                conexion.close()
            return conexion

        conexiones = self._en_hilos(20, usar_un_rato)
        self.assertEqual(len(conexiones), 20)          # nadie se quedo sin conexion
        self.assertLessEqual(self.pools[0].maximo_prestadas, 3)
        self.assertEqual(self.pools[0].prestadas, 0)   # todas devueltas

    def test_si_el_pool_esta_lleno_espera_a_que_se_libere_una(self):
        self._tamano(1)
        ocupada = self.bd.obtener_conexion()
        threading.Timer(0.2, ocupada.close).start()

        inicio = time.monotonic()
        conexion = self.bd.obtener_conexion()
        self.assertIs(conexion, ocupada)                # la misma, ya devuelta
        self.assertGreaterEqual(time.monotonic() - inicio, 0.15)
        conexion.close()

    def test_si_nadie_devuelve_la_conexion_responde_none_sin_colgarse(self):
        self._tamano(1)
        parche = mock.patch.object(self.modulo, "ESPERA_MAXIMA_SEGUNDOS", 0.3)
        parche.start()
        self.addCleanup(parche.stop)
        ocupada = self.bd.obtener_conexion()
        self.addCleanup(ocupada.close)

        inicio = time.monotonic()
        with self.assertLogs("conexion.conexion_bd", level="ERROR") as logs:
            self.assertIsNone(self.bd.obtener_conexion())   # la API contesta 503
        duracion = time.monotonic() - inicio
        self.assertGreaterEqual(duracion, 0.25)
        self.assertLess(duracion, 3)
        self.assertIn("Pool de conexiones lleno", "\n".join(logs.output))

    def test_bd_caida_devuelve_none_y_el_log_no_trae_datos_de_la_conexion(self):
        error = errores_bd.ProgrammingError(
            msg="Access denied for user 'usuario_secreto'@'servidor_secreto'", errno=1045)
        self.MySQLConnectionPool.side_effect = error
        with self.assertLogs("conexion.conexion_bd", level="ERROR") as logs:
            self.assertIsNone(self.bd.obtener_conexion())
        texto = "\n".join(logs.output)
        self.assertIn("ProgrammingError", texto)
        self.assertIn("1045", texto)
        for dato in ("usuario_secreto", "servidor_secreto", "Access denied"):
            self.assertNotIn(dato, texto)
        # El pool fallido no se guarda: la siguiente peticion lo intenta de nuevo
        self.assertIsNone(self.bd._pool)
        self.MySQLConnectionPool.side_effect = lambda **c: _PoolFalso(c["pool_size"])
        self.assertIsNotNone(self.bd.obtener_conexion())

    def test_si_la_reconexion_falla_devuelve_none(self):
        pool = mock.Mock()
        pool.get_connection.side_effect = errores_bd.InterfaceError(msg="Can't connect", errno=2003)
        self.MySQLConnectionPool.side_effect = None
        self.MySQLConnectionPool.return_value = pool
        with self.assertLogs("conexion.conexion_bd", level="ERROR"):
            self.assertIsNone(self.bd.obtener_conexion())

    def test_cerrar_conexion_descarta_el_pool_y_el_siguiente_usa_la_config_nueva(self):
        self.bd.obtener_conexion().close()
        primero = self.pools[0]
        self.bd.cerrar_conexion()
        primero._remove_connections.assert_called_once()
        self.assertIsNone(self.bd._pool)

        self.bd.obtener_conexion().close()
        self.assertEqual(self.MySQLConnectionPool.call_count, 2)
        self.bd.cerrar_conexion()
        self.bd.cerrar_conexion()        # dos veces seguidas no falla

    def test_ya_no_hay_commit_ni_rollback_de_una_conexion_unica(self):
        # El commit va sobre la conexion prestada (conexion.commit()), no sobre ConexionBD
        self.assertFalse(hasattr(self.bd, "commit"))
        self.assertFalse(hasattr(self.bd, "rollback"))


# ---------------------------------------------------------------------------
# 3. conexion_y_cursor: el try/finally escrito una sola vez
# ---------------------------------------------------------------------------

class PruebasConexionYCursor(unittest.TestCase):

    def setUp(self):
        self.conexion_y_cursor = _modulo_conexion().conexion_y_cursor
        self.bd = mock.MagicMock()
        self.conexion = self.bd.obtener_conexion.return_value
        self.cursor = self.conexion.cursor.return_value
        self.orden = mock.Mock()
        self.orden.attach_mock(self.cursor.close, "cursor_close")
        self.orden.attach_mock(self.conexion.close, "conexion_close")

    def _cerrados_en_orden(self):
        self.assertEqual(self.orden.mock_calls, [mock.call.cursor_close(), mock.call.conexion_close()])

    def test_uso_normal_cierra_el_cursor_y_devuelve_la_conexion(self):
        with self.conexion_y_cursor(self.bd, dictionary=True) as (conexion, cursor):
            self.assertIs(conexion, self.conexion)
            self.assertIs(cursor, self.cursor)
        self.conexion.cursor.assert_called_once_with(dictionary=True)
        self._cerrados_en_orden()

    def test_con_error_tambien_cierra_y_deja_subir_el_error(self):
        for error in (errores_bd.OperationalError("falla de prueba"), RuntimeError("inesperado")):
            with self.subTest(error=type(error).__name__):
                self.orden.reset_mock()
                with self.assertRaises(type(error)):
                    with self.conexion_y_cursor(self.bd):
                        raise error
                self._cerrados_en_orden()

    def test_si_crear_el_cursor_falla_igual_devuelve_la_conexion(self):
        self.conexion.cursor.side_effect = errores_bd.OperationalError("sin cursor")
        with self.assertRaises(errores_bd.OperationalError):
            with self.conexion_y_cursor(self.bd):
                pass
        self.conexion.close.assert_called_once()

    def test_sin_bd_lanza_interface_error_que_la_api_contesta_503(self):
        self.bd.obtener_conexion.return_value = None
        with self.assertRaises(errores_bd.InterfaceError):
            with self.conexion_y_cursor(self.bd):
                self.fail("no debe entrar al bloque sin conexion")


# ---------------------------------------------------------------------------
# Fabrica de conexiones simuladas que recuerda cada conexion y cada cursor prestado
# ---------------------------------------------------------------------------

ESCENARIOS = {
    "BD vacia": None,
    "error de MySQL": errores_bd.OperationalError("falla de prueba"),
    "error inesperado": RuntimeError("falla de prueba"),
}


class _BDQueCuenta:
    """Hace de obtener_conexion(): cada llamada presta una conexion nueva y la anota."""

    def __init__(self, error=None):
        self.error = error
        self.conexiones = []
        self.cursores = []

    def __call__(self):
        conexion = mock.MagicMock(name=f"conexion{len(self.conexiones)}")
        conexion.cursor.side_effect = self._nuevo_cursor
        self.conexiones.append(conexion)
        return conexion

    def _nuevo_cursor(self, *args, **kwargs):
        cursor = mock.MagicMock(name=f"cursor{len(self.cursores)}")
        cursor.fetchone.return_value = None
        cursor.fetchall.return_value = []
        cursor.rowcount = 1
        cursor.lastrowid = 99
        if self.error is not None:
            cursor.execute.side_effect = self.error
        self.cursores.append(cursor)
        return cursor

    def revisar(self, prueba):
        """Toda conexion prestada se devolvio una vez y todo cursor se cerro una vez."""
        for conexion in self.conexiones:
            prueba.assertEqual(conexion.close.call_count, 1, f"{conexion} no se devolvio al pool")
        for cursor in self.cursores:
            prueba.assertEqual(cursor.close.call_count, 1, f"{cursor} no se cerro")


# ---------------------------------------------------------------------------
# 4. Los 5 DAO devuelven la conexion en todos sus metodos
# ---------------------------------------------------------------------------

DAOS = {
    "dao.usuario_dao": "UsuarioDAO",
    "dao.mascota_dao": "MascotaDAO",
    "dao.producto_dao": "ProductoDAO",
    "dao.proveedor_dao": "ProveedorDAO",
    "dao.solicitud_dao": "SolicitudDAO",
}


class PruebasDAOSinFugas(unittest.TestCase):

    def _metodos(self):
        for modulo, clase in DAOS.items():
            dao_clase = getattr(importlib.import_module(modulo), clase)
            for nombre, funcion in inspect.getmembers(dao_clase, inspect.isfunction):
                if not nombre.startswith("_"):
                    yield clase, dao_clase, nombre, funcion

    def test_todos_los_metodos_publicos_se_revisan(self):
        nombres = {f"{clase}.{nombre}" for clase, _, nombre, _ in self._metodos()}
        self.assertEqual(len(nombres), 32, sorted(nombres))   # si se agrega uno, entra solo

    def test_cada_metodo_devuelve_la_conexion_y_cierra_el_cursor(self):
        for escenario, error in ESCENARIOS.items():
            for clase, dao_clase, nombre, funcion in self._metodos():
                with self.subTest(escenario=escenario, metodo=f"{clase}.{nombre}"):
                    bd = _BDQueCuenta(error)
                    dao = dao_clase()
                    dao._conexion_bd = mock.Mock(obtener_conexion=bd)
                    parametros = list(inspect.signature(funcion).parameters)[1:]   # sin self
                    argumentos = [mock.MagicMock() for _ in parametros]
                    with contextlib.redirect_stdout(io.StringIO()):     # los print viejos (4.15)
                        try:
                            getattr(dao, nombre)(*argumentos)
                        except (errores_bd.Error, RuntimeError):
                            pass        # SolicitudDAO deja subir el error; los viejos no (4.15)
                    self.assertEqual(len(bd.conexiones), 1, "pide una sola conexion por operacion")
                    bd.revisar(self)


# ---------------------------------------------------------------------------
# 5. Ninguna ruta de la API deja conexiones prestadas
# ---------------------------------------------------------------------------

# Cuerpo que lleva cada ruta hasta la BD. Las que no la usan lo dicen (None).
_MENSAJE = "Quiero conocer a esta mascota, tengo patio grande."
PETICIONES = {
    ("GET", "/api/productos"): {},
    ("GET", "/api/productos/<int:id_producto>"): {},
    ("GET", "/api/mascotas/adopcion"): {},
    ("GET", "/api/mascotas/<int:id_mascota>"): {},
    ("POST", "/api/utils/validar-correo"): None,
    ("POST", "/api/auth/login"): {"email": CORREO, "password": CLAVE},
    ("POST", "/api/auth/login/verify"): {"email": CORREO, "code": "pendiente-login"},
    ("POST", "/api/auth/register"): {"name": "Laura Gomez", "email": CORREO, "password": CLAVE,
                                     "acepta_datos": True},
    ("POST", "/api/auth/register/resend"): None,
    ("POST", "/api/auth/verify"): {"email": CORREO, "code": "pendiente-registro"},
    ("GET", "/api/usuarios/me/mascotas/<int:id_mascota>"): {},
    ("GET", "/api/auth/me"): {},
    ("POST", "/api/solicitudes/adopcion"): {"id_mascota": 1, "mensaje": _MENSAJE},
    ("POST", "/api/solicitudes/contacto"): {"mensaje": _MENSAJE},
}


class PruebasAPISinFugas(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.api = _importar_api()            # limitador apagado, sin .env
        cls.cliente = cls.api.app.test_client()

    def setUp(self):
        for nombre in ("enviar_codigo", "enviar_bienvenida"):
            parche = mock.patch.object(self.api, nombre)
            parche.start()
            self.addCleanup(parche.stop)
        parche = mock.patch.object(self.api, "_validar_correo", return_value=(True, ""))
        parche.start()
        self.addCleanup(parche.stop)
        for almacen in (self.api._otp_login, self.api._otp_registro):
            almacen.descartar(CORREO)
            self.addCleanup(almacen.descartar, CORREO)
        self.token = self.api.generate_token(ID_USUARIO, CORREO)

    def _pedir(self, metodo, regla, cuerpo):
        cuerpo = dict(cuerpo or {})
        # Las verificaciones necesitan un codigo pendiente para llegar a la BD
        if cuerpo.get("code") == "pendiente-login":
            cuerpo["code"] = self.api._otp_login.crear(CORREO, {"id_usuario": ID_USUARIO})
        elif cuerpo.get("code") == "pendiente-registro":
            cuerpo["code"] = self.api._otp_registro.crear(CORREO, {
                "name": "Laura Gomez", "password_hash": "hash-falso",
                "fecha_autorizacion_datos": "2026-11-07 10:00:00",
                "version_politica_datos": self.api.VERSION_POLITICA_DATOS,
            })
        encabezados = ({"Authorization": f"Bearer {self.token}"}
                       if (metodo, regla) in RUTAS_PRIVADAS else {})
        if metodo == "GET":
            return self.cliente.open(_url(regla), method=metodo, headers=encabezados)
        return self.cliente.open(_url(regla), method=metodo, headers=encabezados, json=cuerpo)

    def test_las_peticiones_cubren_todo_el_inventario(self):
        self.assertEqual(set(PETICIONES), set(RUTAS_PUBLICAS) | set(RUTAS_PRIVADAS),
                         "Ruta nueva: agregala a PETICIONES con un cuerpo que llegue a la BD")

    def test_toda_conexion_prestada_se_devuelve_y_todo_cursor_se_cierra(self):
        for escenario, error in ESCENARIOS.items():
            for (metodo, regla), cuerpo in PETICIONES.items():
                with self.subTest(escenario=escenario, ruta=f"{metodo} {regla}"):
                    bd = _BDQueCuenta(error)
                    with mock.patch.object(self.api._conexion_bd, "obtener_conexion", bd), \
                            contextlib.redirect_stdout(io.StringIO()), \
                            self.assertNoLogs("conexion.conexion_bd", level="ERROR"):
                        self.api.app.logger.disabled = True      # el 500 registra la pila
                        try:
                            r = self._pedir(metodo, regla, cuerpo)
                        finally:
                            self.api.app.logger.disabled = False
                        self.api._otp_login.descartar(CORREO)
                        self.api._otp_registro.descartar(CORREO)
                    self.assertLess(r.status_code, 600)
                    if cuerpo is None:
                        self.assertEqual(bd.conexiones, [], "esta ruta no deberia usar la BD")
                    else:
                        self.assertGreaterEqual(len(bd.conexiones), 1, "la peticion no llego a la BD")
                    bd.revisar(self)


# ---------------------------------------------------------------------------
# 6. Consola (main.py) y seed.py
# ---------------------------------------------------------------------------

class PruebasConsolaYSeed(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        _importar_api()          # deja cargadas las claves de prueba sin leer .env
        cls.main = importlib.import_module("main")
        cls.seed = importlib.import_module("seed")

    def test_la_consola_devuelve_la_conexion_de_prueba_y_cierra_el_pool_al_salir(self):
        bd = mock.MagicMock()
        conexion = bd.obtener_conexion.return_value
        with mock.patch.object(self.main, "ConexionBD", return_value=bd), \
                mock.patch.object(self.main, "MenuPrincipal") as menu, \
                contextlib.redirect_stdout(io.StringIO()):
            menu.return_value.iniciar.side_effect = KeyboardInterrupt
            self.main.main()
        conexion.close.assert_called_once()
        bd.cerrar_conexion.assert_called_once()

    def test_seed_devuelve_la_conexion_aunque_falle(self):
        for escenario, error in ESCENARIOS.items():
            with self.subTest(escenario=escenario):
                bd = _BDQueCuenta(error)
                original = bd._nuevo_cursor

                def cursor_con_fila(*a, **k):
                    cursor = original(*a, **k)
                    cursor.fetchone.return_value = (ID_USUARIO,)   # id del refugio
                    return cursor
                bd._nuevo_cursor = cursor_con_fila

                with mock.patch.object(self.seed, "ConexionBD",
                                       return_value=mock.Mock(obtener_conexion=bd)), \
                        mock.patch.object(self.seed, "hash_password", return_value="hash-falso"), \
                        contextlib.redirect_stdout(io.StringIO()):
                    try:
                        self.seed.seed()
                    except (errores_bd.Error, RuntimeError):
                        pass
                self.assertEqual(len(bd.conexiones), 1)
                bd.revisar(self)
                if error is None:
                    bd.conexiones[0].commit.assert_called_once()
                else:
                    bd.conexiones[0].commit.assert_not_called()


# ---------------------------------------------------------------------------
# 7. Con MariaDB real (PETCONNECT_PRUEBA_BD=1), en una base temporal
# ---------------------------------------------------------------------------

@unittest.skipUnless(os.getenv("PETCONNECT_PRUEBA_BD") == "1",
                     "Prueba con MariaDB real: activar con PETCONNECT_PRUEBA_BD=1")
class PruebasPoolEnBD(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        import mysql.connector
        from config.db_config import DB_CONFIG
        from test_esquema import RUTA_ESQUEMA, _leer, _sentencias

        cls.ConexionBD = _modulo_conexion().ConexionBD
        cls.db_config = DB_CONFIG
        cls.bd_original = DB_CONFIG["database"]
        if cls.bd_original == BD_PRUEBA_POOL:
            raise unittest.SkipTest("DB_NAME no puede ser la base temporal de pruebas")

        servidor = {k: v for k, v in DB_CONFIG.items() if k != "database"}
        try:
            cls.conn = mysql.connector.connect(**servidor)
        except mysql.connector.Error:
            raise unittest.SkipTest("No hay conexion con MariaDB")
        cursor = cls.conn.cursor()
        # El nombre es una constante del archivo (no viene del usuario)
        cursor.execute(f"DROP DATABASE IF EXISTS `{BD_PRUEBA_POOL}`")
        cursor.execute(f"CREATE DATABASE `{BD_PRUEBA_POOL}` CHARACTER SET utf8mb4 "
                       f"COLLATE utf8mb4_spanish_ci")
        cls.addClassCleanup(cls._borrar_bd_prueba)
        cursor.execute(f"USE `{BD_PRUEBA_POOL}`")
        for sentencia in _sentencias(_leer(RUTA_ESQUEMA)):
            cursor.execute(sentencia)
        cursor.close()

        # El pool se crea de nuevo apuntando a la base temporal
        DB_CONFIG["database"] = BD_PRUEBA_POOL
        cls.ConexionBD().cerrar_conexion()

    @classmethod
    def _borrar_bd_prueba(cls):
        cls.db_config["database"] = cls.bd_original
        cls.ConexionBD().cerrar_conexion()
        cursor = cls.conn.cursor()
        cursor.execute(f"DROP DATABASE IF EXISTS `{BD_PRUEBA_POOL}`")
        cursor.close()
        cls.conn.close()

    def _consultar(self, sql, params=()):
        """Pide, usa y devuelve: el contrato del item 4.5 (vale con el codigo viejo y el nuevo)."""
        conexion = self.ConexionBD().obtener_conexion()
        self.assertIsNotNone(conexion)
        try:
            cursor = conexion.cursor()
            try:
                cursor.execute(sql, params)
                return cursor.fetchall()
            finally:
                cursor.close()
        finally:
            conexion.close()

    def test_30_hilos_consultan_a_la_vez_sin_cruzarse(self):
        # Con la conexion unica, aqui salian 'MySQL Connection not available' y
        # 'bytearray index out of range' (CP-008, 5/10/2026)
        barrera = threading.Barrier(30)
        errores = []

        def hilo(numero):
            barrera.wait()
            try:
                for vuelta in range(5):
                    filas = self._consultar("SELECT %s, SLEEP(0.01)", (numero * 100 + vuelta,))
                    if filas[0][0] != numero * 100 + vuelta:
                        errores.append(f"hilo {numero} recibio la respuesta de otro: {filas}")
            except Exception as e:      # noqa: BLE001 - se reporta abajo
                errores.append(f"hilo {numero}: {type(e).__name__}")

        hilos = [threading.Thread(target=hilo, args=(n,)) for n in range(30)]
        for h in hilos:
            h.start()
        for h in hilos:
            h.join(timeout=60)
        self.assertEqual(errores, [])

    def test_el_modo_estricto_sigue_al_devolver_y_volver_a_pedir_la_conexion(self):
        from config.db_config import POOL_SIZE
        # Se da la vuelta completa al pool dos veces: cada conexion se reutiliza
        for vuelta in range(POOL_SIZE * 2 + 1):
            conexion = self.ConexionBD().obtener_conexion()
            try:
                cursor = conexion.cursor()
                cursor.execute("SELECT @@SESSION.sql_mode, @@SESSION.character_set_connection, "
                               "@@SESSION.autocommit")
                sql_mode, juego, autocommit = cursor.fetchone()
                with self.subTest(vuelta=vuelta):
                    self.assertIn("STRICT_TRANS_TABLES", sql_mode)
                    self.assertEqual(juego, "utf8mb4")
                    self.assertEqual(int(autocommit), 1)
                if vuelta == 0:
                    # Alguien cambia la sesion: al devolverla, el pool la limpia
                    cursor.execute("SET SESSION sql_mode = ''")
                cursor.close()
            finally:
                conexion.close()

    def test_muchas_consultas_de_los_dao_no_agotan_el_pool(self):
        from config.db_config import POOL_SIZE
        from dao.usuario_dao import UsuarioDAO
        dao = UsuarioDAO()
        for _ in range(POOL_SIZE * 3):
            self.assertIsNone(dao.consultar_por_correo("nadie.pool@ejemplo.test"))
        inicio = time.monotonic()
        conexion = self.ConexionBD().obtener_conexion()
        self.assertIsNotNone(conexion)
        conexion.close()
        self.assertLess(time.monotonic() - inicio, 1)   # no tuvo que esperar: nada quedo prestado


if __name__ == "__main__":
    unittest.main()
