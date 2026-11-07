"""
Pruebas de regresion de A-17 / NC-004 (item 4.1 de PRIORIDADES, parte 1: API):
la politica de contrasenas (RS03, caso CP-003) vive en security/politica.py.

- Valores limite de longitud: 7, 8, 9, 64 y 65 caracteres; 72 y 73 bytes.
- Composicion: mayuscula, MINUSCULA (antes faltaba: PETCONNECT1! pasaba),
  numero y caracter especial (control adicional del proyecto).
- /api/auth/register rechaza PETCONNECT1! con 400 antes de la BD, del hash y
  del correo, y acepta Petconnect1!.

No usan la base de datos real (se simula), no envian correos, no consultan el
DNS ni leen .env. Contrasenas inventadas.

Ejecutar desde petconnect.Backend, con el entorno virtual activo:
    python -m unittest discover -s tests -v
"""
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# El paquete security/ carga crypto.py y jwt_helper.py, que exigen estas claves
# al importarse. Son claves de prueba: no se lee el .env.
from cryptography.fernet import Fernet  # noqa: E402

os.environ.setdefault("FERNET_KEY", Fernet.generate_key().decode())
os.environ.setdefault("JWT_SECRET", "clave-de-pruebas-petconnect-" + "x" * 32)

from security.politica import CARACTERES_ESPECIALES, validar_contrasena  # noqa: E402
from test_errores import _importar_api  # noqa: E402

SIN_MINUSCULA = "PETCONNECT1!"       # la evidencia de A-17
VALIDA = "Petconnect1!"
CORREO = "politica.prueba@ejemplo.test"
NOMBRE = "Titular Prueba"


class PruebasLongitud(unittest.TestCase):
    """CP-003: valores limite de 8 y 64 caracteres (y 72 bytes de bcrypt)."""

    def test_7_caracteres_se_rechaza(self):
        self.assertIn("al menos 8", validar_contrasena("Abc12!x"))

    def test_8_y_9_caracteres_se_aceptan(self):
        self.assertIsNone(validar_contrasena("Abc1234!"))
        self.assertIsNone(validar_contrasena("Abc12345!"))

    def test_64_caracteres_se_acepta(self):
        self.assertIsNone(validar_contrasena("Aa1!" + "b" * 60))

    def test_65_caracteres_se_rechaza(self):
        self.assertIn("maximo 64", validar_contrasena("Aa1!" + "b" * 61))

    def test_72_bytes_se_acepta_y_73_se_rechaza(self):
        # Cada emoji ocupa 4 bytes: 4 + 17 * 4 = 72
        self.assertIsNone(validar_contrasena("Aa1!" + "🐶" * 17))
        self.assertIn("maximo 64", validar_contrasena("Aa1!b" + "🐶" * 17))

    def test_vacia_pide_la_longitud(self):
        self.assertIn("al menos 8", validar_contrasena(""))


class PruebasComposicion(unittest.TestCase):
    """CP-003: mayuscula, minuscula, numero y caracter especial."""

    def test_sin_minuscula_se_rechaza(self):
        # A-17: antes de este item esta contrasena se aceptaba
        self.assertEqual(validar_contrasena(SIN_MINUSCULA),
                         "La contrasena debe tener al menos una minuscula")

    def test_con_todo_se_acepta(self):
        self.assertIsNone(validar_contrasena(VALIDA))

    def test_sin_mayuscula_se_rechaza(self):
        self.assertIn("mayuscula", validar_contrasena("petconnect1!"))

    def test_sin_numero_se_rechaza(self):
        self.assertIn("numero", validar_contrasena("Petconnect!!"))

    def test_sin_caracter_especial_se_rechaza(self):
        self.assertIn("caracter especial", validar_contrasena("Petconnect12"))

    def test_letras_con_tilde_no_cuentan_como_minuscula(self):
        # Decision del 4.1: solo a-z, igual que la web y el movil
        self.assertIn("minuscula", validar_contrasena("PETCONNECTÑÁ1!"))

    def test_cada_caracter_especial_del_mensaje_se_acepta(self):
        for caracter in CARACTERES_ESPECIALES.split():
            with self.subTest(caracter=caracter):
                self.assertIsNone(validar_contrasena("Petconnect1" + caracter))

    def test_el_mensaje_nombra_todos_los_especiales(self):
        mensaje = validar_contrasena("Petconnect12")
        for caracter in ("@", "#", "!", '"', "$", "&", "?", "¡", "-", "_", "*", "."):
            with self.subTest(caracter=caracter):
                self.assertIn(caracter, mensaje)


class PruebasRegistroConLaPolitica(unittest.TestCase):
    """/api/auth/register usa la politica comun (BD, DNS y correo simulados)."""

    @classmethod
    def setUpClass(cls):
        cls.api = _importar_api()            # limitador apagado
        cls.cliente = cls.api.app.test_client()

    def setUp(self):
        parches = {
            "obtener_conexion": mock.patch.object(self.api._conexion_bd, "obtener_conexion",
                                                  return_value=mock.MagicMock()),
            "UsuarioDAO": mock.patch.object(self.api, "UsuarioDAO"),
            "hash_password": mock.patch.object(self.api, "hash_password", return_value="hash-falso"),
            "_validar_correo": mock.patch.object(self.api, "_validar_correo", return_value=(True, "")),
            "enviar_codigo": mock.patch.object(self.api, "enviar_codigo"),
        }
        for nombre, parche in parches.items():
            setattr(self, nombre, parche.start())
            self.addCleanup(parche.stop)
        self.UsuarioDAO.return_value.consultar_por_correo.return_value = None   # correo libre

        self.api._otp_registro.descartar(CORREO)
        self.addCleanup(self.api._otp_registro.descartar, CORREO)

    def _registrar(self, clave):
        return self.cliente.post("/api/auth/register", json={
            "name": NOMBRE, "email": CORREO, "password": clave, "acepta_datos": True})

    def test_rechaza_contrasena_sin_minuscula_antes_de_la_bd(self):
        r = self._registrar(SIN_MINUSCULA)
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.get_json(), {"error": "La contrasena debe tener al menos una minuscula"})
        self.UsuarioDAO.assert_not_called()
        self.hash_password.assert_not_called()
        self.enviar_codigo.assert_not_called()
        self.assertFalse(self.api._otp_registro.tiene_pendiente(CORREO))

    def test_acepta_contrasena_que_cumple_la_politica(self):
        r = self._registrar(VALIDA)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["message"], "Codigo enviado")
        self.enviar_codigo.assert_called_once()

    def test_la_api_usa_la_politica_comun(self):
        # El nombre viejo (lo usa la evidencia del AA2) es la misma funcion
        self.assertIs(self.api._validate_password, validar_contrasena)


if __name__ == "__main__":
    unittest.main()
