"""
Pruebas de regresion del servicio de correo (A-06: TLS con certificado verificado).
No envian correos ni abren conexiones: smtplib.SMTP se reemplaza por un mock.

Ejecutar desde petconnect.Backend, con el entorno virtual activo:
    python -m unittest discover -s tests -v
"""
import os
import ssl
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# No cargar el .env real al importar config.email_config; se restaura despues
# para no afectar a las otras pruebas que corren en el mismo proceso
import dotenv  # noqa: E402

_load_dotenv_original = dotenv.load_dotenv
dotenv.load_dotenv = lambda *a, **k: False
try:
    from correo import servicio  # noqa: E402
finally:
    dotenv.load_dotenv = _load_dotenv_original

CONFIG_PRUEBA = {
    "gmail_host": "smtp.gmail.com",
    "gmail_port": 587,
    "gmail_user": "remitente@ejemplo.test",
    "gmail_app_password": "clave-inventada",
    "smtp_host": "sandbox.smtp.mailtrap.io",
    "smtp_port": 587,
    "smtp_user": "usuario-inventado",
    "smtp_pass": "clave-inventada",
}


class PruebasTLS(unittest.TestCase):
    """A-06: el canal SMTP exige un certificado valido para el servidor."""

    def _enviar(self, modo):
        config = dict(CONFIG_PRUEBA, mode=modo)
        with mock.patch.dict(servicio.EMAIL_CONFIG, config), \
                mock.patch.object(servicio.smtplib, "SMTP") as smtp:
            servicio.enviar_correo("destino@ejemplo.test", "Asunto", "Texto", "<p>Hola</p>")
        return smtp.return_value.__enter__.return_value

    def test_starttls_verifica_el_certificado(self):
        for modo in ("gmail", "smtp"):
            with self.subTest(modo=modo):
                conexion = self._enviar(modo)
                contexto = conexion.starttls.call_args.kwargs.get("context")
                self.assertIsInstance(contexto, ssl.SSLContext)
                self.assertEqual(contexto.verify_mode, ssl.CERT_REQUIRED)
                self.assertTrue(contexto.check_hostname)

    def test_cifra_antes_de_enviar_la_contrasena(self):
        conexion = self._enviar("gmail")
        llamadas = [c[0] for c in conexion.method_calls]
        self.assertLess(llamadas.index("starttls"), llamadas.index("login"))


if __name__ == "__main__":
    unittest.main()
