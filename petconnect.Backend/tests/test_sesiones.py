"""
Pruebas de regresion del item 4.13 (A-03): revocar sesiones.

Antes, require_auth aceptaba el token solo por su firma: una sesion valia 24 h
aunque se quisiera cerrar o la cuenta se bloqueara, y el token llevaba el correo
(un JWT se puede leer: base64, no esta cifrado; Ley 1581).

Ahora:
- El token lleva sub (id), ver (usuarios.version_sesion), iat y exp. Sin correo.
- require_auth consulta la BD en cada peticion: la cuenta debe existir, estar
  "activo" y tener la misma version_sesion del token. Si no, 401 (el mismo
  mensaje para todo). Si la BD no responde, 503 (nunca 401: no saca a nadie).
- Un token sin "ver" (de antes del 4.13) no vale: hay que iniciar sesion otra vez.
- POST /api/auth/logout suma 1 a version_sesion: cierra TODAS las sesiones de la
  cuenta (web y movil).
- La API no arranca si falta la columna (migracion 2026-11-08_version_sesion.sql).

Sin BD: rutas con UsuarioDAO simulado. Con PETCONNECT_PRUEBA_BD=1: la migracion
en una base vieja y el ciclo completo con MariaDB, en las bases temporales
"petconnect_prueba_sesion" y "petconnect_prueba_sesion_migracion" (se borran al
final). Ninguna toca la base "petconnect". Datos inventados (Ley 1581).

Ejecutar desde petconnect.Backend:
    ../.venv/Scripts/python -m unittest tests.test_sesiones -v
"""
import base64
import contextlib
import io
import json
import os
import sys
import time
import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest import mock

from mysql.connector import errors as errores_bd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_errores import _importar_api  # noqa: E402  (claves de prueba, sin .env)

ID_USUARIO = 7
CORREO = "sesiones.prueba@ejemplo.test"          # inventado (Ley 1581)
MENSAJE_401 = {"error": "Token invalido o sesion expirada. Inicia sesion de nuevo"}
RUTA_API = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "api.py")
BD_PRUEBA_SESION = "petconnect_prueba_sesion"
BD_PRUEBA_SESION_MIGRACION = "petconnect_prueba_sesion_migracion"


def _contenido(token):
    """Lo que cualquiera puede leer de un JWT sin conocer la clave (parte central)."""
    parte = token.split(".")[1]
    return json.loads(base64.urlsafe_b64decode(parte + "=" * (-len(parte) % 4)))


def _usuario(**cambios):
    datos = dict(id_usuario=ID_USUARIO, nombres="Laura", apellidos="Gomez", correo=CORREO,
                 password_hash="hash-falso", estado="activo", acepta_datos=True,
                 fecha_autorizacion_datos=None, version_politica_datos=None)
    datos.update(cambios)
    return SimpleNamespace(**datos)


# ---------------------------------------------------------------------------
# 1. El token
# ---------------------------------------------------------------------------

class PruebasTokenSinCorreo(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.api = _importar_api()

    def test_solo_lleva_id_version_y_fechas(self):
        contenido = _contenido(self.api.generate_token(ID_USUARIO, 3))
        self.assertEqual(set(contenido), {"sub", "ver", "iat", "exp"})
        self.assertEqual((contenido["sub"], contenido["ver"]), ("7", 3))
        self.assertNotIn("@", json.dumps(contenido))

    def test_la_version_debe_ser_un_entero_no_negativo(self):
        for valor in (True, False, -1, "0", None, 1.0):
            with self.subTest(version=repr(valor)):
                with self.assertRaises(ValueError):
                    self.api.generate_token(ID_USUARIO, valor)

    def test_require_auth_ya_no_guarda_el_correo(self):
        with open(RUTA_API, encoding="utf-8") as f:
            self.assertNotIn("current_user_email", f.read())


# ---------------------------------------------------------------------------
# 2. require_auth y /api/auth/logout con UsuarioDAO simulado
# ---------------------------------------------------------------------------

class _BaseSesion(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.api = _importar_api()
        cls.cliente = cls.api.app.test_client()

    def setUp(self):
        parches = {
            "obtener_conexion": mock.patch.object(self.api._conexion_bd, "obtener_conexion",
                                                  return_value=mock.MagicMock()),
            "UsuarioDAO": mock.patch.object(self.api, "UsuarioDAO"),
        }
        for nombre, parche in parches.items():
            setattr(self, nombre, parche.start())
            self.addCleanup(parche.stop)
        self.dao = self.UsuarioDAO.return_value
        self.dao.consultar_por_id.return_value = _usuario()
        # La "BD": version_sesion y estado de la cuenta ID_USUARIO
        self.bd = {"version": 0, "estado": "activo", "existe": True}
        self.dao.consultar_sesion.side_effect = self._consultar_sesion
        self.dao.cerrar_sesiones.side_effect = self._cerrar_sesiones

    def _consultar_sesion(self, id_usuario):
        if id_usuario != ID_USUARIO or not self.bd["existe"]:
            return None
        return self.bd["version"], self.bd["estado"]

    def _cerrar_sesiones(self, id_usuario):
        self.bd["version"] += 1
        return True

    def _cabecera(self, token):
        return {"Authorization": f"Bearer {token}"}

    def _me(self, token):
        return self.cliente.get("/api/auth/me", headers=self._cabecera(token))

    def _logout(self, token=None):
        cabeceras = self._cabecera(token) if token else {}
        return self.cliente.post("/api/auth/logout", headers=cabeceras)

    def _firmar(self, **contenido):
        # Misma clave de pruebas con que firma generate_token; nunca se imprime
        import jwt
        from security import jwt_helper
        return jwt.encode(contenido, jwt_helper._SECRET, algorithm="HS256")


class PruebasRequireAuth(_BaseSesion):

    def test_sesion_vigente_entra(self):
        r = self._me(self.api.generate_token(ID_USUARIO, 0))
        self.assertEqual(r.status_code, 200)
        self.dao.consultar_sesion.assert_called_once_with(ID_USUARIO)   # entero

    def test_version_distinta_responde_401_sin_llegar_a_la_ruta(self):
        self.bd["version"] = 1
        for version in (0, 2):
            with self.subTest(version_del_token=version):
                r = self._me(self.api.generate_token(ID_USUARIO, version))
                self.assertEqual((r.status_code, r.get_json()), (401, MENSAJE_401))
        self.dao.consultar_por_id.assert_not_called()

    def test_cuenta_inactiva_bloqueada_o_borrada_responde_401(self):
        token = self.api.generate_token(ID_USUARIO, 0)
        for caso, cambio in {"inactivo": {"estado": "inactivo"}, "bloqueado": {"estado": "bloqueado"},
                             "borrada": {"existe": False}}.items():
            with self.subTest(cuenta=caso):
                self.bd.update({"estado": "activo", "existe": True, **cambio})
                r = self._me(token)
                self.assertEqual((r.status_code, r.get_json()), (401, MENSAJE_401))
        self.dao.consultar_por_id.assert_not_called()

    def test_token_viejo_con_correo_y_sin_version_no_vale(self):
        ahora = int(time.time())
        viejo = self._firmar(sub=str(ID_USUARIO), email=CORREO, iat=ahora, exp=ahora + 3600)
        r = self._me(viejo)
        self.assertEqual((r.status_code, r.get_json()), (401, MENSAJE_401))
        self.dao.consultar_sesion.assert_not_called()       # ni siquiera llega a la BD

    def test_version_que_no_es_un_entero_no_vale(self):
        ahora = int(time.time())
        for valor in (True, "0", -1, 0.0, None, [0]):
            with self.subTest(ver=repr(valor)):
                token = self._firmar(sub=str(ID_USUARIO), ver=valor, exp=ahora + 60)
                self.assertEqual(self._me(token).status_code, 401)
        self.dao.consultar_sesion.assert_not_called()

    def test_bd_caida_responde_503_y_no_cierra_la_sesion(self):
        self.dao.consultar_sesion.side_effect = errores_bd.InterfaceError("sin conexion")
        with self.assertLogs(self.api.app.logger, "ERROR"):
            r = self._me(self.api.generate_token(ID_USUARIO, 0))
        self.assertEqual(r.status_code, 503)
        self.assertNotIn(CORREO, r.get_data(as_text=True))


class PruebasLogout(_BaseSesion):

    def test_sin_token_responde_401_y_no_toca_la_bd(self):
        self.assertEqual(self._logout().status_code, 401)
        self.dao.cerrar_sesiones.assert_not_called()

    def test_cierra_la_sesion_en_todos_los_aparatos(self):
        web = self.api.generate_token(ID_USUARIO, 0)
        movil = self.api.generate_token(ID_USUARIO, 0)
        self.assertEqual(self._me(web).status_code, 200)
        self.assertEqual(self._me(movil).status_code, 200)

        r = self._logout(web)
        self.assertEqual((r.status_code, r.get_json()), (200, {"message": "Sesion cerrada"}))
        self.dao.cerrar_sesiones.assert_called_once_with(ID_USUARIO)

        for aparato, token in (("web", web), ("movil", movil)):
            with self.subTest(aparato=aparato):
                self.assertEqual(self._me(token).status_code, 401)
        self.assertEqual(self._logout(web).status_code, 401)       # no cierra dos veces
        self.assertEqual(self.bd["version"], 1)

    def test_despues_del_logout_un_inicio_de_sesion_nuevo_si_vale(self):
        self._logout(self.api.generate_token(ID_USUARIO, 0))
        self.assertEqual(self._me(self.api.generate_token(ID_USUARIO, 1)).status_code, 200)

    def test_si_la_bd_falla_no_dice_sesion_cerrada(self):
        self.dao.cerrar_sesiones.side_effect = errores_bd.OperationalError("Lost connection")
        with self.assertLogs(self.api.app.logger, "ERROR"):
            r = self._logout(self.api.generate_token(ID_USUARIO, 0))
        self.assertEqual(r.status_code, 503)
        self.assertNotIn("cerrada", r.get_data(as_text=True))


# ---------------------------------------------------------------------------
# 3. /login/verify y /verify firman el token con la version
# ---------------------------------------------------------------------------

class PruebasTokenAlIniciarSesion(_BaseSesion):

    def setUp(self):
        super().setUp()
        for nombre in ("enviar_codigo", "enviar_bienvenida"):
            parche = mock.patch.object(self.api, nombre)
            parche.start()
            self.addCleanup(parche.stop)
        for almacen in (self.api._otp_login, self.api._otp_registro):
            almacen.descartar(CORREO)
            self.addCleanup(almacen.descartar, CORREO)

    def test_login_verify_usa_la_version_de_la_bd(self):
        self.bd["version"] = 4
        self.dao.consultar_por_correo.return_value = _usuario(
            version_politica_datos=self.api.VERSION_POLITICA_DATOS)
        codigo = self.api._otp_login.crear(CORREO, {"id_usuario": ID_USUARIO})
        r = self.cliente.post("/api/auth/login/verify", json={"email": CORREO, "code": codigo})
        self.assertEqual(r.status_code, 200)
        contenido = _contenido(r.get_json()["token"])
        self.assertEqual((contenido["sub"], contenido["ver"]), ("7", 4))
        self.assertNotIn("email", contenido)
        self.assertEqual(self._me(r.get_json()["token"]).status_code, 200)

    def test_registro_nuevo_empieza_en_la_version_0(self):
        def insertar(usuario):
            usuario.id_usuario = ID_USUARIO
            return True
        self.dao.insertar.side_effect = insertar
        codigo = self.api._otp_registro.crear(CORREO, {
            "name": "Laura Gomez", "password_hash": "hash-falso",
            "fecha_autorizacion_datos": datetime(2026, 11, 8, 10, 0, 0),
            "version_politica_datos": self.api.VERSION_POLITICA_DATOS,
        })
        r = self.cliente.post("/api/auth/verify", json={"email": CORREO, "code": codigo})
        self.assertEqual(r.status_code, 201)
        contenido = _contenido(r.get_json()["token"])
        self.assertEqual((contenido["sub"], contenido["ver"]), ("7", 0))
        self.assertNotIn("email", contenido)


# ---------------------------------------------------------------------------
# 4. Arranque de la API y SQL del DAO (conexion simulada)
# ---------------------------------------------------------------------------

class PruebasArranque(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.api = _importar_api()

    def _preparar(self, **comportamiento):
        with mock.patch.object(self.api, "UsuarioDAO") as dao:
            dao.return_value.consultar_sesion.configure_mock(**comportamiento)
            return self.api._preparar_sesiones(), dao.return_value.consultar_sesion

    def test_con_la_columna_arranca_sin_leer_datos_de_nadie(self):
        resultado, consulta = self._preparar(return_value=None)
        self.assertTrue(resultado)
        consulta.assert_called_once_with(0)

    def test_sin_la_columna_avisa_que_migracion_falta_y_no_arranca(self):
        sin_columna = errores_bd.ProgrammingError(msg="Unknown column", errno=1054)
        salida = io.StringIO()
        with contextlib.redirect_stdout(salida):
            resultado, _ = self._preparar(side_effect=sin_columna)
        self.assertFalse(resultado)
        self.assertIn("2026-11-08_version_sesion.sql", salida.getvalue())

    def test_otro_error_de_sql_no_se_esconde(self):
        otro = errores_bd.ProgrammingError(msg="otro", errno=1064)
        with self.assertRaises(errores_bd.ProgrammingError):
            self._preparar(side_effect=otro)


class PruebasUsuarioDAOSesion(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        _importar_api()                       # config/ sin el .env real
        from dao.usuario_dao import UsuarioDAO
        cls.UsuarioDAO = UsuarioDAO

    def setUp(self):
        self.dao = self.UsuarioDAO()
        self.dao._conexion_bd = mock.MagicMock()   # BD simulada: nunca se toca la real
        self.conexion = self.dao._conexion_bd.obtener_conexion.return_value
        self.cursor = self.conexion.cursor.return_value

    def _sql(self):
        sql, params = self.cursor.execute.call_args.args
        return " ".join(sql.split()), params

    def test_consultar_sesion_es_parametrizada_y_devuelve_version_y_estado(self):
        self.cursor.fetchone.return_value = (3, "activo")
        self.assertEqual(self.dao.consultar_sesion(ID_USUARIO), (3, "activo"))
        sql, params = self._sql()
        self.assertEqual(sql, "SELECT version_sesion, estado FROM usuarios WHERE id_usuario = %s")
        self.assertEqual(params, (ID_USUARIO,))
        self.cursor.fetchone.return_value = None
        self.assertIsNone(self.dao.consultar_sesion(ID_USUARIO))

    def test_cerrar_sesiones_suma_1_sin_cambiar_la_fecha_de_actualizacion(self):
        self.cursor.rowcount = 1
        self.assertTrue(self.dao.cerrar_sesiones(ID_USUARIO))
        sql, params = self._sql()
        self.assertIn("SET version_sesion = version_sesion + 1, "
                      "fecha_actualizacion = fecha_actualizacion", sql)
        self.assertEqual(params, (ID_USUARIO,))
        self.conexion.commit.assert_called_once()

    def test_los_errores_de_la_bd_suben_para_que_la_api_responda_503(self):
        self.cursor.execute.side_effect = errores_bd.OperationalError("Lost connection")
        for metodo in ("consultar_sesion", "cerrar_sesiones"):
            with self.subTest(metodo=metodo):
                with self.assertRaises(errores_bd.OperationalError):
                    getattr(self.dao, metodo)(ID_USUARIO)
        self.conexion.commit.assert_not_called()
        self.conexion.rollback.assert_called_once()        # solo la escritura


# ---------------------------------------------------------------------------
# 5. Con MariaDB real (PETCONNECT_PRUEBA_BD=1), en bases temporales
# ---------------------------------------------------------------------------

def _conectar_servidor():
    import mysql.connector
    from config.db_config import DB_CONFIG
    servidor = {k: v for k, v in DB_CONFIG.items() if k not in ("database", "sql_mode")}
    try:
        conexion = mysql.connector.connect(**servidor)
    except mysql.connector.Error:
        raise unittest.SkipTest("No hay conexion con MariaDB")
    conexion.autocommit = True          # cada lectura ve lo ultimo que guardo la API
    return conexion


def _fecha_actualizacion(cursor, id_usuario):
    cursor.execute("SELECT fecha_actualizacion FROM usuarios WHERE id_usuario = %s", (id_usuario,))
    return cursor.fetchone()[0]


@unittest.skipUnless(os.getenv("PETCONNECT_PRUEBA_BD") == "1",
                     "Prueba con MariaDB real: activar con PETCONNECT_PRUEBA_BD=1")
class PruebasSesionEnBD(unittest.TestCase):
    """schema.sql real en petconnect_prueba_sesion: el ciclo completo con la API."""

    @classmethod
    def setUpClass(cls):
        from config.db_config import DB_CONFIG
        from conexion.conexion_bd import ConexionBD
        from test_esquema import RUTA_ESQUEMA, _leer, _sentencias

        cls.api = _importar_api()
        cls.cliente = cls.api.app.test_client()
        cls.db_config = DB_CONFIG
        cls.bd_original = DB_CONFIG["database"]
        if cls.bd_original == BD_PRUEBA_SESION:
            raise unittest.SkipTest("DB_NAME no puede ser la base temporal de pruebas")
        cls.conn = _conectar_servidor()
        cursor = cls.conn.cursor()
        # El nombre es una constante del archivo (no viene del usuario)
        cursor.execute(f"DROP DATABASE IF EXISTS `{BD_PRUEBA_SESION}`")
        cursor.execute(f"CREATE DATABASE `{BD_PRUEBA_SESION}` CHARACTER SET utf8mb4 "
                       f"COLLATE utf8mb4_spanish_ci")
        cls.addClassCleanup(cls._borrar_bd_prueba)
        cursor.execute(f"USE `{BD_PRUEBA_SESION}`")
        for sentencia in _sentencias(_leer(RUTA_ESQUEMA)):
            cursor.execute(sentencia)
        cursor.close()
        DB_CONFIG["database"] = BD_PRUEBA_SESION
        ConexionBD().cerrar_conexion()

    @classmethod
    def _borrar_bd_prueba(cls):
        from conexion.conexion_bd import ConexionBD
        cls.db_config["database"] = cls.bd_original
        ConexionBD().cerrar_conexion()
        cursor = cls.conn.cursor()
        cursor.execute(f"DROP DATABASE IF EXISTS `{BD_PRUEBA_SESION}`")
        cursor.close()
        cls.conn.close()

    def setUp(self):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO usuarios (nombres, correo, password_hash, fecha_actualizacion) "
                       "VALUES (%s, %s, %s, %s)", ("Prueba", CORREO, "hash-falso", "2026-01-01 00:00:00"))
        self.id_usuario = cursor.lastrowid
        cursor.close()

        def borrar():
            c = self.conn.cursor()
            c.execute("DELETE FROM usuarios WHERE id_usuario = %s", (self.id_usuario,))
            c.close()
        self.addCleanup(borrar)

    def test_la_api_arranca_con_el_esquema_nuevo(self):
        self.assertTrue(self.api._preparar_sesiones())

    def test_una_cuenta_nueva_empieza_en_0_y_activa(self):
        from dao.usuario_dao import UsuarioDAO
        self.assertEqual(UsuarioDAO().consultar_sesion(self.id_usuario),
                         (self.api.VERSION_SESION_INICIAL, "activo"))

    def test_logout_cierra_la_sesion_y_no_cambia_la_fecha_de_actualizacion(self):
        token = self.api.generate_token(self.id_usuario, 0)
        cabecera = {"Authorization": f"Bearer {token}"}
        self.assertEqual(self.cliente.get("/api/auth/me", headers=cabecera).status_code, 200)
        r = self.cliente.post("/api/auth/logout", headers=cabecera)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.cliente.get("/api/auth/me", headers=cabecera).status_code, 401)

        cursor = self.conn.cursor()
        cursor.execute("SELECT version_sesion FROM usuarios WHERE id_usuario = %s", (self.id_usuario,))
        self.assertEqual(cursor.fetchone()[0], 1)
        self.assertEqual(_fecha_actualizacion(cursor, self.id_usuario), datetime(2026, 1, 1))
        cursor.close()

    def test_bloquear_la_cuenta_cierra_la_sesion_al_momento(self):
        cabecera = {"Authorization": f"Bearer {self.api.generate_token(self.id_usuario, 0)}"}
        cursor = self.conn.cursor()
        cursor.execute("UPDATE usuarios SET estado = 'bloqueado' WHERE id_usuario = %s", (self.id_usuario,))
        cursor.close()
        self.assertEqual(self.cliente.get("/api/auth/me", headers=cabecera).status_code, 401)


@unittest.skipUnless(os.getenv("PETCONNECT_PRUEBA_BD") == "1",
                     "Prueba con MariaDB real: activar con PETCONNECT_PRUEBA_BD=1")
class PruebasMigracionSesionEnBD(unittest.TestCase):
    """La migracion agrega la columna a una tabla vieja, con 0, y se puede correr dos veces."""

    @classmethod
    def setUpClass(cls):
        cls.conn = _conectar_servidor()
        cursor = cls.conn.cursor()
        cursor.execute(f"DROP DATABASE IF EXISTS `{BD_PRUEBA_SESION_MIGRACION}`")
        cursor.execute(f"CREATE DATABASE `{BD_PRUEBA_SESION_MIGRACION}` "
                       "CHARACTER SET utf8mb4 COLLATE utf8mb4_spanish_ci")
        cls.addClassCleanup(cls._borrar_bd_prueba)
        cursor.execute(f"USE `{BD_PRUEBA_SESION_MIGRACION}`")
        # Base "vieja": usuarios como estaba antes del 4.13 (solo las columnas que importan)
        cursor.execute(
            "CREATE TABLE usuarios ("
            " id_usuario int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,"
            " correo varchar(120) NOT NULL,"
            " estado enum('activo','inactivo','bloqueado') DEFAULT 'activo',"
            " fecha_actualizacion timestamp NOT NULL DEFAULT current_timestamp()"
            "   ON UPDATE current_timestamp()"
            ") ENGINE=InnoDB")
        cursor.execute("INSERT INTO usuarios (correo, fecha_actualizacion) VALUES (%s, %s)",
                       (CORREO, "2026-01-01 00:00:00"))
        cursor.close()

    @classmethod
    def _borrar_bd_prueba(cls):
        cursor = cls.conn.cursor()
        cursor.execute(f"DROP DATABASE IF EXISTS `{BD_PRUEBA_SESION_MIGRACION}`")
        cursor.close()
        cls.conn.close()

    def test_agrega_la_columna_en_0_sin_tocar_la_fecha_y_se_puede_repetir(self):
        from test_esquema import RUTA_MIGRACION_SESION, _leer, _sentencias
        cursor = self.conn.cursor()
        for _ in range(2):
            for sentencia in _sentencias(_leer(RUTA_MIGRACION_SESION)):
                cursor.execute(sentencia)
        cursor.execute("SELECT version_sesion, fecha_actualizacion FROM usuarios")
        self.assertEqual(cursor.fetchall(), [(0, datetime(2026, 1, 1))])
        cursor.execute("SHOW COLUMNS FROM usuarios LIKE 'version_sesion'")
        columna = cursor.fetchone()
        self.assertEqual((columna[2], str(columna[4])), ("NO", "0"))   # NOT NULL DEFAULT 0
        cursor.close()


if __name__ == "__main__":
    unittest.main()
