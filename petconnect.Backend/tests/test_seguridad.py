"""
Pruebas de regresion de NC-001 (contrasenas con bcrypt) y NC-008 (token JWT).
No necesitan base de datos ni envian correos.

Ejecutar desde petconnect.Backend, con el entorno virtual activo:
    python -m unittest discover -s tests -v
"""
import hashlib
import os
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


if __name__ == "__main__":
    unittest.main()
