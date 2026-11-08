"""
Pruebas de regresion de NC-006 / A-04 (item 2.5 de PRIORIDADES): un codigo OTP
admite 5 fallos; el 6.o intento lo borra y responde "bloqueado", aunque traiga el
codigo correcto. La comparacion usa hmac.compare_digest.
No usan la base de datos real (se simula apagada), no envian correos ni leen .env.

Ejecutar desde petconnect.Backend, con el entorno virtual activo:
    python -m unittest discover -s tests -v
"""
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from otp import servicio  # noqa: E402
from otp.servicio import AlmacenOTP  # noqa: E402
from test_errores import _importar_api  # noqa: E402

CORREO_PRUEBA = "laura@ejemplo.test"    # inventado
MAX_INTENTOS = 5                         # lo que pide la auditoria (A-04)
_ANCHO_COMPLETO = str.maketrans("0123456789", "０１２３４５６７８９")


def _codigo_incorrecto(codigo: str) -> str:
    """Un codigo de 6 digitos que seguro no es el correcto."""
    return "000000" if codigo != "000000" else "111111"


class PruebasAlmacenOTP(unittest.TestCase):
    """El almacen solo, sin Flask."""

    def setUp(self):
        self.almacen = AlmacenOTP()
        self.codigo = self.almacen.crear(CORREO_PRUEBA, {"id_usuario": 7})
        self.malo = _codigo_incorrecto(self.codigo)

    def _fallar(self, veces):
        for _ in range(veces):
            datos, motivo = self.almacen.verificar(CORREO_PRUEBA, self.malo)
            self.assertIsNone(datos)
            self.assertEqual(motivo, "incorrecto")

    def test_cinco_fallos_y_luego_el_correcto_queda_bloqueado(self):
        self._fallar(MAX_INTENTOS)
        datos, motivo = self.almacen.verificar(CORREO_PRUEBA, self.codigo)
        self.assertIsNone(datos)
        self.assertEqual(motivo, "bloqueado")

    def test_el_bloqueo_borra_el_codigo(self):
        self._fallar(MAX_INTENTOS)
        self.almacen.verificar(CORREO_PRUEBA, self.codigo)        # 6.o: bloqueado
        self.assertFalse(self.almacen.tiene_pendiente(CORREO_PRUEBA))
        self.assertEqual(self.almacen.verificar(CORREO_PRUEBA, self.codigo), (None, "no_pendiente"))

    def test_cuatro_fallos_y_luego_el_correcto_entra(self):
        self._fallar(MAX_INTENTOS - 1)
        datos, motivo = self.almacen.verificar(CORREO_PRUEBA, self.codigo)
        self.assertIsNone(motivo)
        self.assertEqual(datos["id_usuario"], 7)

    def test_pedir_otro_codigo_reinicia_el_contador(self):
        self._fallar(MAX_INTENTOS)
        nuevo = self.almacen.crear(CORREO_PRUEBA, {"id_usuario": 7})
        self.malo = _codigo_incorrecto(nuevo)
        self._fallar(MAX_INTENTOS - 1)
        datos, motivo = self.almacen.verificar(CORREO_PRUEBA, nuevo)
        self.assertIsNone(motivo)
        self.assertEqual(datos["id_usuario"], 7)

    def test_digitos_de_ancho_completo_son_incorrectos_sin_error(self):
        # '１２３４５６' no es ASCII: compare_digest con str lanzaria TypeError (500)
        ancho = self.codigo.translate(_ANCHO_COMPLETO)
        self.assertEqual(self.almacen.verificar(CORREO_PRUEBA, ancho), (None, "incorrecto"))
        self.assertEqual(self.almacen.verificar(CORREO_PRUEBA, "１２３４５６"), (None, "incorrecto"))

    def test_se_compara_con_compare_digest(self):
        with mock.patch.object(servicio.hmac, "compare_digest", wraps=servicio.hmac.compare_digest) as cmp:
            self.almacen.verificar(CORREO_PRUEBA, self.codigo)
        cmp.assert_called_once()

    def test_codigo_vencido_sigue_diciendo_expirado(self):
        with mock.patch.object(servicio.time, "time", return_value=10**12):
            self.assertEqual(self.almacen.verificar(CORREO_PRUEBA, self.codigo), (None, "expirado"))


class PruebasRutasOTP(unittest.TestCase):
    """Las dos rutas de verificacion: el 6.o intento responde 429 y no entrega token."""

    @classmethod
    def setUpClass(cls):
        cls.api = _importar_api()
        cls.cliente = cls.api.app.test_client()

    def setUp(self):
        # BD "apagada", sin correos ni tokens: nada de esto deberia usarse al bloquear
        parches = {
            "obtener_conexion": mock.patch.object(self.api._conexion_bd, "obtener_conexion", return_value=None),
            "UsuarioDAO": mock.patch.object(self.api, "UsuarioDAO"),
            "generate_token": mock.patch.object(self.api, "generate_token", return_value="token-falso"),
            "enviar_bienvenida": mock.patch.object(self.api, "enviar_bienvenida"),
        }
        for nombre, parche in parches.items():
            setattr(self, nombre, parche.start())
            self.addCleanup(parche.stop)

        self.api._otp_login.descartar(CORREO_PRUEBA)
        self.api._otp_registro.descartar(CORREO_PRUEBA)
        self.addCleanup(self.api._otp_login.descartar, CORREO_PRUEBA)
        self.addCleanup(self.api._otp_registro.descartar, CORREO_PRUEBA)

    def _seis_intentos(self, ruta, codigo):
        malo = _codigo_incorrecto(codigo)
        # Item 4.10 (A-14): /verify del registro usa un solo mensaje para "incorrecto",
        # "vencido" y "sin pendiente"; /login/verify conserva el suyo
        mensaje = (self.api._MENSAJE_CODIGO_REGISTRO if ruta == "/api/auth/verify"
                   else "Codigo incorrecto")
        for i in range(MAX_INTENTOS):
            r = self.cliente.post(ruta, json={"email": CORREO_PRUEBA, "code": malo})
            self.assertEqual(r.status_code, 400, f"intento {i + 1}")
            self.assertEqual(r.get_json(), {"error": mensaje})
        return self.cliente.post(ruta, json={"email": CORREO_PRUEBA, "code": codigo})

    def _sin_token_ni_bd(self, r):
        self.assertNotIn("token", r.get_json())
        self.assertNotIn(CORREO_PRUEBA, r.get_data(as_text=True))    # Ley 1581
        self.generate_token.assert_not_called()
        self.UsuarioDAO.assert_not_called()          # ni se busca ni se crea el usuario

    def test_registro_sexto_intento_correcto_responde_429_bloqueado(self):
        codigo = self.api._otp_registro.crear(CORREO_PRUEBA, {"name": "Laura Gomez", "password_hash": "x"})
        r = self._seis_intentos("/api/auth/verify", codigo)

        self.assertEqual(r.status_code, 429)
        self.assertIn("Demasiados intentos fallidos", r.get_json()["error"])
        self._sin_token_ni_bd(r)
        self.enviar_bienvenida.assert_not_called()
        self.assertFalse(self.api._otp_registro.tiene_pendiente(CORREO_PRUEBA))

    def test_login_sexto_intento_correcto_responde_429_bloqueado(self):
        codigo = self.api._otp_login.crear(CORREO_PRUEBA, {"id_usuario": 7})
        r = self._seis_intentos("/api/auth/login/verify", codigo)

        self.assertEqual(r.status_code, 429)
        self.assertIn("Demasiados intentos fallidos", r.get_json()["error"])
        self._sin_token_ni_bd(r)
        self.assertFalse(self.api._otp_login.tiene_pendiente(CORREO_PRUEBA))


if __name__ == "__main__":
    unittest.main()
