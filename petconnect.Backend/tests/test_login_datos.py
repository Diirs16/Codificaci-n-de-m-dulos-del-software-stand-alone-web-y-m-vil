"""
Pruebas de regresion del item 3.5 de PRIORIDADES (A-20, riesgo R05 del plan GA9):
pedir la autorizacion de datos personales al iniciar sesion (Ley 1581, art. 9;
Decreto 1377, art. 13) a las cuentas que no la tienen (acepta_datos = 0, creadas
antes del 3.1) o que aceptaron otra version de la politica.

- /login con la contrasena correcta y sin autorizacion vigente responde 403 con
  "requiere_autorizacion": true, sin enviar codigo ni dejar pendiente. Con la
  contrasena mala sigue siendo 401 (no revela si la cuenta existe).
- Solo vale el booleano JSON true; con la casilla, el pendiente guarda la fecha y
  la version, y /login/verify las escribe con el codigo correcto (nunca antes).
- /login/verify no entrega token sin una prueba valida (doble barrera).
- Una cuenta ya autorizada entra igual que antes y su fecha no se toca.
- UsuarioDAO lee la fecha y la version y las actualiza con SQL parametrizado.

No usan la base de datos real (se simula), no envian correos ni leen .env. El
limitador del 2.6 queda apagado (_importar_api).

Ejecutar desde petconnect.Backend, con el entorno virtual activo:
    python -m unittest discover -s tests -v
"""
import os
import sys
import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_errores import _importar_api  # noqa: E402

# Datos inventados (Ley 1581)
CORREO = "cuenta.vieja@ejemplo.test"
CLAVE = "Firulais2026!"
VERSION = "1.0"
ID_USUARIO = 7
MENSAJE_403 = "Para seguir usando tu cuenta debes autorizar el tratamiento de tus datos personales"
FECHA_VIEJA = datetime(2026, 11, 5, 10, 30, 0)

_SIN_CAMPO = object()   # marca: el cuerpo no trae "acepta_datos"

# Nada de esto es una autorizacion expresa: solo vale el booleano JSON true
NO_AUTORIZA = (_SIN_CAMPO, False, "true", 1, "si", None)


def _usuario(acepta_datos=False, fecha=None, version=None):
    """Usuario falso con los campos que mira la API (como los deja _mapear_usuario)."""
    return SimpleNamespace(
        id_usuario=ID_USUARIO, nombres="Cuenta", apellidos="Vieja", correo=CORREO,
        password_hash="hash-falso", estado="activo", acepta_datos=acepta_datos,
        fecha_autorizacion_datos=fecha, version_politica_datos=version,
    )


# Cuentas que deben autorizar: la de antes del 3.1 y una que acepto otra version
SIN_AUTORIZACION = {
    "cuenta en 0": lambda: _usuario(),
    "otra version": lambda: _usuario(True, FECHA_VIEJA, "0.9"),
}


class PruebasAutorizacionAlIniciarSesion(unittest.TestCase):
    """/login y /login/verify con BD y correo simulados."""

    @classmethod
    def setUpClass(cls):
        cls.api = _importar_api()            # limitador apagado
        cls.cliente = cls.api.app.test_client()

    def setUp(self):
        self.codigos = []       # codigos "enviados" por correo
        parches = {
            "obtener_conexion": mock.patch.object(self.api._conexion_bd, "obtener_conexion",
                                                  return_value=mock.MagicMock()),
            "UsuarioDAO": mock.patch.object(self.api, "UsuarioDAO"),
            "verificar_password": mock.patch.object(self.api, "verificar_password", return_value=True),
            "es_hash_heredado": mock.patch.object(self.api, "es_hash_heredado", return_value=False),
            "generate_token": mock.patch.object(self.api, "generate_token", return_value="token-falso"),
            "enviar_codigo": mock.patch.object(self.api, "enviar_codigo",
                                               side_effect=lambda correo, nombre, codigo, **_:
                                               self.codigos.append(codigo)),
        }
        for nombre, parche in parches.items():
            setattr(self, nombre, parche.start())
            self.addCleanup(parche.stop)

        self.dao = self.UsuarioDAO.return_value
        self.dao.consultar_por_correo.return_value = _usuario()
        self.dao.registrar_autorizacion.return_value = True

        self.api._otp_login.descartar(CORREO)
        self.addCleanup(self.api._otp_login.descartar, CORREO)

    def _login(self, acepta_datos=_SIN_CAMPO):
        cuerpo = {"email": CORREO, "password": CLAVE}
        if acepta_datos is not _SIN_CAMPO:
            cuerpo["acepta_datos"] = acepta_datos
        return self.cliente.post("/api/auth/login", json=cuerpo)

    def _verificar(self, codigo):
        return self.cliente.post("/api/auth/login/verify", json={"email": CORREO, "code": codigo})

    def _sin_codigo_ni_token(self):
        self.enviar_codigo.assert_not_called()
        self.assertFalse(self.api._otp_login.tiene_pendiente(CORREO))
        self.generate_token.assert_not_called()
        self.dao.registrar_autorizacion.assert_not_called()

    # -- /login ----------------------------------------------------------------

    def test_sin_autorizacion_responde_403_sin_codigo(self):
        for caso, usuario in SIN_AUTORIZACION.items():
            for valor in NO_AUTORIZA:
                etiqueta = "sin el campo" if valor is _SIN_CAMPO else repr(valor)
                with self.subTest(cuenta=caso, acepta_datos=etiqueta):
                    self.dao.consultar_por_correo.return_value = usuario()
                    r = self._login(valor)
                    self.assertEqual(r.status_code, 403)
                    self.assertEqual(r.get_json(), {"error": MENSAJE_403,
                                                    "requiere_autorizacion": True})
                    self.assertNotIn(CORREO, r.get_data(as_text=True))    # Ley 1581
        self._sin_codigo_ni_token()

    def test_contrasena_mala_sigue_siendo_401_sin_revelar_nada(self):
        self.verificar_password.return_value = False
        r = self._login()
        self.assertEqual(r.status_code, 401)
        self.assertNotIn("requiere_autorizacion", r.get_json())
        self._sin_codigo_ni_token()

    def test_cuenta_inactiva_no_llega_a_pedir_la_autorizacion(self):
        usuario = _usuario()
        usuario.estado = "bloqueado"
        self.dao.consultar_por_correo.return_value = usuario
        r = self._login(True)
        self.assertEqual(r.status_code, 403)
        self.assertEqual(r.get_json(), {"error": "Cuenta inactiva o bloqueada"})
        self._sin_codigo_ni_token()

    def test_con_la_casilla_el_pendiente_guarda_fecha_y_version(self):
        for caso, usuario in SIN_AUTORIZACION.items():
            with self.subTest(cuenta=caso):
                self.dao.consultar_por_correo.return_value = usuario()
                antes = datetime.now().replace(microsecond=0)
                r = self._login(True)
                despues = datetime.now()

                self.assertEqual(r.status_code, 200)
                self.assertEqual(r.get_json()["message"], "Codigo enviado")
                pendiente = self.api._otp_login.vigente(CORREO)
                self.assertEqual(pendiente["id_usuario"], ID_USUARIO)
                self.assertEqual(pendiente["version_politica_datos"], VERSION)
                fecha = pendiente["fecha_autorizacion_datos"]
                self.assertIsInstance(fecha, datetime)
                self.assertTrue(antes <= fecha <= despues, fecha)
        # Antes del codigo nada se escribe en la BD
        self.dao.registrar_autorizacion.assert_not_called()

    def test_cuenta_autorizada_entra_sin_casilla_y_sin_nueva_prueba(self):
        self.dao.consultar_por_correo.return_value = _usuario(True, FECHA_VIEJA, VERSION)
        r = self._login()
        self.assertEqual(r.status_code, 200)
        pendiente = self.api._otp_login.vigente(CORREO)
        self.assertEqual(pendiente["id_usuario"], ID_USUARIO)
        self.assertNotIn("fecha_autorizacion_datos", pendiente)   # no se crea otra prueba
        self.assertNotIn("version_politica_datos", pendiente)

        r = self._verificar(self.codigos[0])
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["token"], "token-falso")
        self.dao.registrar_autorizacion.assert_not_called()     # su fecha no se toca

    # -- /login/verify ---------------------------------------------------------

    def test_codigo_correcto_guarda_la_autorizacion_y_entrega_el_token(self):
        for caso, usuario in SIN_AUTORIZACION.items():
            with self.subTest(cuenta=caso):
                self.dao.registrar_autorizacion.reset_mock()
                self.dao.consultar_por_correo.return_value = usuario()
                self._login(True)
                fecha = self.api._otp_login.vigente(CORREO)["fecha_autorizacion_datos"]

                r = self._verificar(self.codigos[-1])

                self.assertEqual(r.status_code, 200)
                self.assertEqual(r.get_json()["token"], "token-falso")
                self.dao.registrar_autorizacion.assert_called_once_with(ID_USUARIO, fecha, VERSION)

    def test_codigo_incorrecto_no_guarda_nada(self):
        self._login(True)
        malo = "000000" if self.codigos[0] != "000000" else "111111"
        r = self._verificar(malo)
        self.assertEqual(r.status_code, 400)
        self.dao.registrar_autorizacion.assert_not_called()
        self.generate_token.assert_not_called()

    def test_verify_sin_prueba_valida_no_entrega_token(self):
        """Doble barrera: el pendiente debe traer fecha, la version actual y el mismo usuario."""
        pendientes = {
            "sin prueba": {"id_usuario": ID_USUARIO},
            "sin fecha": {"id_usuario": ID_USUARIO, "version_politica_datos": VERSION},
            "version vieja": {"id_usuario": ID_USUARIO, "fecha_autorizacion_datos": FECHA_VIEJA,
                              "version_politica_datos": "0.9"},
            "otro usuario": {"id_usuario": ID_USUARIO + 1, "fecha_autorizacion_datos": FECHA_VIEJA,
                             "version_politica_datos": VERSION},
        }
        for caso, pendiente in pendientes.items():
            with self.subTest(pendiente=caso):
                codigo = self.api._otp_login.crear(CORREO, pendiente)
                r = self._verificar(codigo)
                self.assertEqual(r.status_code, 403)
                self.assertEqual(r.get_json(), {"error": MENSAJE_403,
                                                "requiere_autorizacion": True})
                self.assertFalse(self.api._otp_login.tiene_pendiente(CORREO))
        self.dao.registrar_autorizacion.assert_not_called()
        self.generate_token.assert_not_called()

    def test_si_no_se_puede_guardar_la_autorizacion_no_hay_token(self):
        self.dao.registrar_autorizacion.return_value = False
        self._login(True)
        r = self._verificar(self.codigos[0])
        self.assertEqual(r.status_code, 500)
        self.assertNotIn("token", r.get_json())
        self.generate_token.assert_not_called()


class PruebasDAOAutorizacion(unittest.TestCase):
    """UsuarioDAO lee la prueba de la autorizacion y la actualiza (sin BD real)."""

    @classmethod
    def setUpClass(cls):
        # api.py se importa primero (sin .env real): asi config/ no carga el .env
        _importar_api()
        from dao.usuario_dao import UsuarioDAO
        cls.UsuarioDAO = UsuarioDAO

    def _dao_con_cursor(self):
        dao = self.UsuarioDAO()
        conexion_bd = mock.MagicMock()
        cursor = conexion_bd.obtener_conexion.return_value.cursor.return_value
        dao._conexion_bd = conexion_bd      # BD simulada: nunca se toca la real
        return dao, cursor

    def test_consultar_por_correo_lee_fecha_y_version(self):
        dao, cursor = self._dao_con_cursor()
        cursor.fetchone.return_value = (ID_USUARIO, "Cuenta", "Vieja", CORREO, None, "hash-falso",
                                        None, "activo", 1, 1, None, None, FECHA_VIEJA, VERSION)
        usuario = dao.consultar_por_correo(CORREO)

        sql = cursor.execute.call_args.args[0]
        self.assertIn("fecha_autorizacion_datos", sql)
        self.assertIn("version_politica_datos", sql)
        self.assertIs(usuario.acepta_datos, True)
        self.assertEqual(usuario.fecha_autorizacion_datos, FECHA_VIEJA)
        self.assertEqual(usuario.version_politica_datos, VERSION)

    def test_todos_los_select_leen_la_prueba(self):
        for nombre in ("_CONSULTAR_TODOS", "_CONSULTAR_POR_ID", "_CONSULTAR_POR_CORREO",
                       "_BUSCAR_POR_NOMBRE"):
            with self.subTest(consulta=nombre):
                sql = getattr(self.UsuarioDAO, nombre)
                self.assertIn("fecha_autorizacion_datos, version_politica_datos", sql)

    def test_registrar_autorizacion_escribe_las_tres_columnas_parametrizadas(self):
        dao, cursor = self._dao_con_cursor()
        cursor.rowcount = 1
        fecha = datetime(2026, 11, 6, 9, 0, 0)

        self.assertTrue(dao.registrar_autorizacion(ID_USUARIO, fecha, VERSION))

        sql, valores = cursor.execute.call_args.args
        self.assertIn("acepta_datos = 1", sql)
        self.assertIn("fecha_autorizacion_datos = %s", sql)
        self.assertIn("version_politica_datos = %s", sql)
        self.assertIn("WHERE id_usuario = %s", sql)
        self.assertEqual(sql.count("%s"), len(valores))      # todo parametrizado
        self.assertEqual(valores, (fecha, VERSION, ID_USUARIO))
        dao._conexion_bd.commit.assert_called_once()


if __name__ == "__main__":
    unittest.main()
