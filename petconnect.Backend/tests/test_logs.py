"""
Pruebas de regresion de A-10 (item 2.8 de PRIORIDADES): cuando el correo falla,
ni la consola (stdout) ni los logs muestran el correo del usuario, y el codigo OTP
solo se imprime con APP_ENV=desarrollo. Fuera de desarrollo, /login y /register
responden 503 y descartan el codigo pendiente.

No usan la base de datos real (se simula), no envian correos, no consultan el DNS
ni leen .env. El limitador del 2.6 queda apagado (_importar_api).

Ejecutar desde petconnect.Backend, con el entorno virtual activo:
    python -m unittest discover -s tests -v
"""
import contextlib
import io
import os
import sys
import unittest
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_errores import _importar_api  # noqa: E402

CORREO_PRUEBA = "persona.prueba@ejemplo.test"   # inventado (Ley 1581)
CONTRASENA = "Firulais2026!"
NOMBRE = "Persona Prueba"
MENSAJE_503 = "No pudimos enviar el código a tu correo. Intenta de nuevo en unos minutos"

# Valores de APP_ENV que NO son desarrollo (None = la variable no existe)
FUERA_DE_DESARROLLO = (None, "", "produccion", "dev")
# Valores que SI lo son: se ignoran espacios y mayusculas
EN_DESARROLLO = ("desarrollo", "  Desarrollo  ")


class FalloCorreoSimulado(Exception):
    """Error de envio inventado; su mensaje trae el correo, como uno real de SMTP."""


@contextlib.contextmanager
def _app_env(valor):
    """Pone APP_ENV solo durante la prueba (None = la quita) y la restaura al salir."""
    with mock.patch.dict(os.environ):
        os.environ.pop("APP_ENV", None)
        if valor is not None:
            os.environ["APP_ENV"] = valor
        yield


class PruebasLogsSinDatosPersonales(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.api = _importar_api()
        cls.cliente = cls.api.app.test_client()

    def setUp(self):
        self.codigo_enviado = None
        usuario = SimpleNamespace(
            id_usuario=7, nombres="Persona", apellidos="Prueba", correo=CORREO_PRUEBA,
            password_hash="hash-falso", estado="activo",
        )
        parches = {
            # BD simulada "encendida" (un objeto cualquiera): el DAO tambien es falso
            "obtener_conexion": mock.patch.object(self.api._conexion_bd, "obtener_conexion",
                                                  return_value=mock.MagicMock()),
            "UsuarioDAO": mock.patch.object(self.api, "UsuarioDAO"),
            "verificar_password": mock.patch.object(self.api, "verificar_password", return_value=True),
            "es_hash_heredado": mock.patch.object(self.api, "es_hash_heredado", return_value=False),
            "hash_password": mock.patch.object(self.api, "hash_password", return_value="hash-falso"),
            "_validar_correo": mock.patch.object(self.api, "_validar_correo", return_value=(True, "")),
            "generate_token": mock.patch.object(self.api, "generate_token", return_value="token-falso"),
            "enviar_codigo": mock.patch.object(self.api, "enviar_codigo", side_effect=self._codigo_falla),
            "enviar_bienvenida": mock.patch.object(self.api, "enviar_bienvenida",
                                                   side_effect=self._bienvenida_falla),
        }
        for nombre, parche in parches.items():
            setattr(self, nombre, parche.start())
            self.addCleanup(parche.stop)

        self.UsuarioDAO.return_value.consultar_por_correo.return_value = usuario
        self.UsuarioDAO.return_value.insertar.return_value = True

        for almacen in (self.api._otp_login, self.api._otp_registro):
            almacen.descartar(CORREO_PRUEBA)
            self.addCleanup(almacen.descartar, CORREO_PRUEBA)

    # -- correos falsos que siempre fallan -----------------------------------

    def _codigo_falla(self, email, nombre, codigo, **_):
        self.codigo_enviado = codigo          # para buscarlo despues en la salida
        raise FalloCorreoSimulado(f"550 buzon no disponible: {email}")

    def _bienvenida_falla(self, email, nombre):
        raise FalloCorreoSimulado(f"550 buzon no disponible: {email}")

    # -- ayudas ---------------------------------------------------------------

    def _pedir(self, ruta, cuerpo, app_env):
        """Hace la peticion y devuelve (respuesta, texto de stdout, texto de los logs)."""
        salida = io.StringIO()
        with _app_env(app_env), contextlib.redirect_stdout(salida):
            try:
                with self.assertLogs(self.api.app.logger, level="WARNING") as logs:
                    r = self.cliente.post(ruta, json=cuerpo)
                texto_logs = "\n".join(logs.output)
            except AssertionError:
                # No hubo ningun log: no se corta aqui para revisar antes la consola;
                # _log_correcto lo marca como fallo despues.
                texto_logs = ""
        return r, salida.getvalue(), texto_logs

    def _login(self, app_env):
        return self._pedir("/api/auth/login", {"email": CORREO_PRUEBA, "password": CONTRASENA}, app_env)

    def _registro(self, app_env):
        self.UsuarioDAO.return_value.consultar_por_correo.return_value = None   # correo libre
        return self._pedir("/api/auth/register",
                           {"name": NOMBRE, "email": CORREO_PRUEBA, "password": CONTRASENA}, app_env)

    def _log_correcto(self, logs):
        self.assertIn("Fallo de envio", logs)
        self.assertIn("FalloCorreoSimulado", logs)    # el tipo de error si queda
        self.assertNotIn(CORREO_PRUEBA, logs)         # el correo y str(e) no (Ley 1581)
        self.assertNotIn("550 buzon", logs)

    # -- fuera de desarrollo: 503, nada en la consola ------------------------

    def _fuera_de_desarrollo(self, pedir, almacen):
        for valor in FUERA_DE_DESARROLLO:
            with self.subTest(APP_ENV=valor):
                r, salida, logs = pedir(valor)

                self.assertIsNotNone(self.codigo_enviado)
                self.assertNotIn(CORREO_PRUEBA, salida)
                self.assertNotIn(self.codigo_enviado, salida)
                self.assertNotIn(self.codigo_enviado, logs)
                self.assertEqual(r.status_code, 503)
                self.assertEqual(r.get_json(), {"error": MENSAJE_503})
                self.assertNotIn(CORREO_PRUEBA, r.get_data(as_text=True))
                self._log_correcto(logs)
                # el codigo que nadie recibio ya no sirve
                self.assertFalse(almacen.tiene_pendiente(CORREO_PRUEBA))

    def test_login_fuera_de_desarrollo_responde_503_sin_codigo_ni_correo(self):
        self._fuera_de_desarrollo(self._login, self.api._otp_login)

    def test_registro_fuera_de_desarrollo_responde_503_sin_codigo_ni_correo(self):
        self._fuera_de_desarrollo(self._registro, self.api._otp_registro)

    # -- en desarrollo: solo el codigo en la consola --------------------------

    def _en_desarrollo(self, pedir, almacen):
        for valor in EN_DESARROLLO:
            with self.subTest(APP_ENV=valor):
                # En desarrollo el pendiente queda guardado; desde el 2.7 (A-09) un
                # segundo /register no lo reemplaza ni reenvia, asi que cada caso
                # empieza sin pendiente para que de verdad se intente enviar.
                almacen.descartar(CORREO_PRUEBA)
                self.codigo_enviado = None
                r, salida, logs = pedir(valor)

                self.assertEqual(r.status_code, 200)
                self.assertEqual(r.get_json()["message"], "Codigo enviado")
                self.assertIn(self.codigo_enviado, salida)
                self.assertNotIn(CORREO_PRUEBA, salida)
                self.assertNotIn("550 buzon", salida)
                self.assertNotIn(self.codigo_enviado, logs)   # el log nunca lleva el codigo
                self._log_correcto(logs)
                self.assertTrue(almacen.tiene_pendiente(CORREO_PRUEBA))

    def test_login_en_desarrollo_imprime_solo_el_codigo(self):
        self._en_desarrollo(self._login, self.api._otp_login)

    def test_registro_en_desarrollo_imprime_solo_el_codigo(self):
        self._en_desarrollo(self._registro, self.api._otp_registro)

    # -- bienvenida: la cuenta ya existe, la respuesta no cambia --------------

    def test_bienvenida_fallida_responde_201_sin_mostrar_el_correo(self):
        for valor in (None, "desarrollo"):
            with self.subTest(APP_ENV=valor):
                self.api._otp_registro.descartar(CORREO_PRUEBA)
                codigo = self.api._otp_registro.crear(
                    CORREO_PRUEBA, {"name": NOMBRE, "password_hash": "hash-falso"})
                r, salida, logs = self._pedir(
                    "/api/auth/verify", {"email": CORREO_PRUEBA, "code": codigo}, valor)

                self.assertEqual(r.status_code, 201)
                self.assertEqual(r.get_json()["token"], "token-falso")
                self.enviar_bienvenida.assert_called()
                self.assertNotIn(CORREO_PRUEBA, salida)
                self._log_correcto(logs)

    # -- control: si el correo SI sale, no se imprime ni se registra nada ------

    def test_correo_enviado_no_imprime_ni_registra(self):
        """Pasa con el codigo viejo y con el nuevo, a proposito: el camino normal no cambia."""
        self.enviar_codigo.side_effect = None
        salida = io.StringIO()
        with _app_env("desarrollo"), contextlib.redirect_stdout(salida), \
                self.assertNoLogs(self.api.app.logger, level="WARNING"):
            r = self.cliente.post("/api/auth/login", json={"email": CORREO_PRUEBA, "password": CONTRASENA})

        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["message"], "Codigo enviado")
        self.assertEqual(salida.getvalue(), "")
        self.assertTrue(self.api._otp_login.tiene_pendiente(CORREO_PRUEBA))


if __name__ == "__main__":
    unittest.main()
