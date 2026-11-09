"""
Pruebas de regresion de NC-001 (contrasenas con bcrypt), NC-008 (token JWT)
y NC-007 (JWT_SECRET obligatorio y decrypt() que falla, item 4.8). No necesitan
base de datos ni envian correos.

Ejecutar desde petconnect.Backend, con el entorno virtual activo:
    python -m unittest discover -s tests -v
"""
import hashlib
import os
import subprocess
import sys
import time
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Claves de prueba antes de importar los modulos que las leen al cargarse
from cryptography.fernet import Fernet  # noqa: E402

os.environ.setdefault("FERNET_KEY", Fernet.generate_key().decode())
os.environ.setdefault("JWT_SECRET", "clave-de-pruebas-petconnect-" + "x" * 32)
os.environ["EMAIL_MODE"] = "smtp"            # sin credenciales: nunca se envia un correo
os.environ["MAILTRAP_SMTP_USER"] = ""
os.environ["MAILTRAP_SMTP_PASS"] = ""

import jwt  # noqa: E402
from flask import jsonify, request  # noqa: E402

# Item 4.14 (A-41): api.py se importa con load_dotenv apagado para no cargar el .env
# real. Se llama aqui y no en setUpClass porque la ruta de prueba de abajo se registra
# al importar este archivo.
from test_errores import _importar_api  # noqa: E402

api = _importar_api()
from security import jwt_helper  # noqa: E402
from security.jwt_helper import generate_token, verify_token  # noqa: E402
from security.passwords import es_hash_heredado, hash_password, verificar_password  # noqa: E402
from security.crypto import decrypt, encrypt  # noqa: E402
from cryptography.fernet import InvalidToken  # noqa: E402

CONTRASENA = "Firulais2026!"


class PruebasPasswords(unittest.TestCase):
    """NC-001: las contrasenas se guardan con bcrypt (sal y costo 12)."""

    def test_hash_tiene_formato_bcrypt_costo_12(self):
        h = hash_password(CONTRASENA)
        self.assertTrue(h.startswith("$2b$12$"))
        self.assertEqual(len(h), 60)

    def test_misma_contrasena_genera_hashes_distintos(self):
        self.assertNotEqual(hash_password(CONTRASENA), hash_password(CONTRASENA))

    def test_verifica_la_correcta_y_rechaza_la_incorrecta(self):
        h = hash_password(CONTRASENA)
        self.assertTrue(verificar_password(CONTRASENA, h))
        self.assertFalse(verificar_password("Firulais2026?", h))

    def test_acepta_hash_sha256_heredado_para_migrarlo(self):
        heredado = hashlib.sha256(CONTRASENA.encode()).hexdigest()
        self.assertTrue(es_hash_heredado(heredado))
        self.assertTrue(verificar_password(CONTRASENA, heredado))
        self.assertFalse(verificar_password("otra-clave", heredado))
        self.assertFalse(es_hash_heredado(hash_password(CONTRASENA)))

    def test_contrasena_de_mas_de_72_bytes_no_lanza_error(self):
        self.assertFalse(verificar_password("A" * 73, hash_password(CONTRASENA)))

    def test_valores_vacios_se_rechazan(self):
        self.assertFalse(verificar_password("", hash_password(CONTRASENA)))
        self.assertFalse(verificar_password(CONTRASENA, ""))

    # La politica de contrasenas (longitud y composicion) se prueba en
    # tests/test_politica.py desde el item 4.1.


class PruebasToken(unittest.TestCase):
    """NC-008: el token emitido por la API debe ser aceptado por la API."""

    def test_ida_y_vuelta(self):
        payload = verify_token(generate_token(7, 0))
        self.assertIsNotNone(payload)
        self.assertEqual(payload["sub"], "7")
        self.assertEqual(int(payload["sub"]), 7)

    def test_firma_alterada_se_rechaza(self):
        token = generate_token(7, 0)
        alterado = token[:-2] + ("AA" if not token.endswith("AA") else "BB")
        self.assertIsNone(verify_token(alterado))

    def test_token_vencido_se_rechaza(self):
        ahora = int(time.time())
        vencido = jwt.encode({"sub": "7", "iat": ahora - 100, "exp": ahora - 10}, jwt_helper._SECRET, algorithm="HS256")
        self.assertIsNone(verify_token(vencido))


# La ruta de prueba se registra al importar el archivo: unittest importa todas las
# pruebas antes de correr la primera, y Flask prohibe registrar rutas despues de
# atender una peticion (otras pruebas, como test_errores.py, usan test_client()).
@api.app.route("/_prueba/protegida")
@api.require_auth
def _protegida():
    return jsonify(id=request.current_user_id, tipo=type(request.current_user_id).__name__)


class PruebasEndpointProtegido(unittest.TestCase):
    """NC-008 de punta a punta: una ruta con @require_auth acepta el token emitido."""

    @classmethod
    def setUpClass(cls):
        cls.cliente = api.app.test_client()

    def test_acepta_el_token_emitido(self):
        token = generate_token(7, 0)
        with mock.patch.object(api, "UsuarioDAO") as usuarios:   # sesion vigente (4.13)
            usuarios.return_value.consultar_sesion.return_value = (0, "activo")
            r = self.cliente.get("/_prueba/protegida", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json(), {"id": 7, "tipo": "int"})

    def test_rechaza_peticion_sin_token(self):
        self.assertEqual(self.cliente.get("/_prueba/protegida").status_code, 401)

    def test_rechaza_token_con_sub_no_numerico(self):
        token = jwt.encode({"sub": "abc", "exp": int(time.time()) + 60}, jwt_helper._SECRET, algorithm="HS256")
        r = self.cliente.get("/_prueba/protegida", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(r.status_code, 401)


class PruebasSecretoObligatorio(unittest.TestCase):
    """NC-007 (A-03): sin JWT_SECRET propio de al menos 32 bytes, jwt_helper no se importa.

    El modulo revisa la clave una sola vez, al cargarse; por eso cada caso corre en un
    Python aparte con un entorno minimo armado a mano (sin copiar os.environ ni leer .env).

    Con el codigo anterior (valor por defecto "dev-secret-inseguro") fallaban los tres
    casos "no_arranca", porque el modulo cargaba igual; el de 64 caracteres pasa con ambos.
    """

    CARPETA_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def _importar_con(self, jwt_secret=None):
        entorno = {
            "PATH": os.environ.get("PATH", ""),
            "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
            "FERNET_KEY": Fernet.generate_key().decode(),
        }
        if jwt_secret is not None:
            entorno["JWT_SECRET"] = jwt_secret
        return subprocess.run(
            [sys.executable, "-c", "import security.jwt_helper"],
            cwd=self.CARPETA_BACKEND, env=entorno,
            capture_output=True, text=True, timeout=60,
        )

    def test_sin_jwt_secret_no_arranca(self):
        r = self._importar_con(None)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("RuntimeError: JWT_SECRET", r.stderr)

    def test_secreto_publico_de_ejemplo_no_arranca(self):
        r = self._importar_con("dev-secret-inseguro")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("RuntimeError: JWT_SECRET", r.stderr)
        self.assertNotIn("dev-secret-inseguro", r.stderr)   # el error no muestra el valor

    def test_secreto_de_31_bytes_no_arranca(self):
        r = self._importar_con("s" * 31)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("RuntimeError: JWT_SECRET", r.stderr)

    def test_secreto_de_64_caracteres_importa_bien(self):
        r = self._importar_con("a1b2c3d4" * 8)   # inventado, solo para la prueba
        self.assertEqual(r.returncode, 0, r.stderr)


class PruebasDescifrado(unittest.TestCase):
    """
    NC-007 / A-13 (item 4.8): decrypt() debe FALLAR (InvalidToken) si no puede
    descifrar. Antes devolvia el texto cifrado como si fuera el original.
    """

    def test_ida_y_vuelta(self):
        self.assertEqual(decrypt(encrypt("123456")), "123456")

    def test_texto_que_no_es_fernet_lanza_error(self):
        with self.assertRaises(InvalidToken):
            decrypt("no-es-un-texto-de-fernet")

    def test_token_alterado_lanza_error(self):
        cifrado = encrypt("123456")
        # Cambia un caracter del medio: la firma (HMAC) ya no coincide
        medio = len(cifrado) // 2
        otro = "A" if cifrado[medio] != "A" else "B"
        alterado = cifrado[:medio] + otro + cifrado[medio + 1:]
        with self.assertRaises(InvalidToken):
            decrypt(alterado)

    def test_token_de_otra_clave_lanza_error(self):
        # Como si FERNET_KEY hubiera cambiado: otra clave, generada solo para la prueba
        de_otra_clave = Fernet(Fernet.generate_key()).encrypt(b"123456").decode()
        with self.assertRaises(InvalidToken):
            decrypt(de_otra_clave)

    def test_vacio_y_none_se_devuelven_igual(self):
        self.assertEqual(decrypt(""), "")
        self.assertIsNone(decrypt(None))


if __name__ == "__main__":
    unittest.main()
