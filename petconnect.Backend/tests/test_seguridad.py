"""
Pruebas de regresion de NC-001 (contrasenas con bcrypt), NC-008 (token JWT)
y NC-007 (JWT_SECRET obligatorio). No necesitan base de datos ni envian correos.

Ejecutar desde petconnect.Backend, con el entorno virtual activo:
    python -m unittest discover -s tests -v
"""
import hashlib
import os
import subprocess
import sys
import time
import unittest

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

import api  # noqa: E402
from security import jwt_helper  # noqa: E402
from security.jwt_helper import generate_token, verify_token  # noqa: E402
from security.passwords import es_hash_heredado, hash_password, verificar_password  # noqa: E402

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

    def test_politica_de_longitud(self):
        self.assertIsNone(api._validate_password("Abc12345!"))
        self.assertIn("al menos 8", api._validate_password("Abc12!x"))
        self.assertIsNone(api._validate_password("Aa1!" + "b" * 60))          # 64 caracteres
        self.assertIn("maximo 64", api._validate_password("Aa1!" + "b" * 61))  # 65 caracteres
        self.assertIn("maximo 64", api._validate_password("Aa1!" + "🐶" * 20))  # 84 bytes


class PruebasToken(unittest.TestCase):
    """NC-008: el token emitido por la API debe ser aceptado por la API."""

    def test_ida_y_vuelta(self):
        payload = verify_token(generate_token(7, "laura@example.com"))
        self.assertIsNotNone(payload)
        self.assertEqual(payload["sub"], "7")
        self.assertEqual(int(payload["sub"]), 7)

    def test_firma_alterada_se_rechaza(self):
        token = generate_token(7, "laura@example.com")
        alterado = token[:-2] + ("AA" if not token.endswith("AA") else "BB")
        self.assertIsNone(verify_token(alterado))

    def test_token_vencido_se_rechaza(self):
        ahora = int(time.time())
        vencido = jwt.encode({"sub": "7", "iat": ahora - 100, "exp": ahora - 10}, jwt_helper._SECRET, algorithm="HS256")
        self.assertIsNone(verify_token(vencido))


class PruebasEndpointProtegido(unittest.TestCase):
    """NC-008 de punta a punta: una ruta con @require_auth acepta el token emitido."""

    @classmethod
    def setUpClass(cls):
        @api.app.route("/_prueba/protegida")
        @api.require_auth
        def _protegida():
            return jsonify(id=request.current_user_id, tipo=type(request.current_user_id).__name__)

        cls.cliente = api.app.test_client()

    def test_acepta_el_token_emitido(self):
        token = generate_token(7, "laura@example.com")
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


if __name__ == "__main__":
    unittest.main()
