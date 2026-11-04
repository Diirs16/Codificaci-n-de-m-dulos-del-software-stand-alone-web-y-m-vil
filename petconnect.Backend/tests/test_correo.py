"""
Pruebas de regresion del servicio de correo: A-06 (TLS con certificado verificado)
y A-05 (los datos del usuario se escapan en el HTML y no inyectan cabeceras).
No envian correos ni abren conexiones: smtplib.SMTP se reemplaza por un mock.

Ejecutar desde petconnect.Backend, con el entorno virtual activo:
    python -m unittest discover -s tests -v
"""
import email.errors
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


# Nombres inventados que intentan meter un enlace en el correo (A-05)
NOMBRE_CON_ENLACE = '<a href="https://sitio-falso.example">Reclama tu premio</a>'
NOMBRE_SIN_ESPACIOS = '<a/href="https://sitio-falso.example">Premio</a>'


class PruebasEscapeHTML(unittest.TestCase):
    """A-05: lo que escribe el usuario se muestra como texto en el correo, nunca como HTML."""

    def _correo_generado(self, enviar, *args):
        """Llama a enviar_codigo / enviar_bienvenida sin enviar nada y devuelve (texto, html)."""
        with mock.patch.object(servicio, "enviar_correo") as enviar_correo:
            enviar("destino@ejemplo.test", *args)
        _destino, _asunto, texto, cuerpo_html = enviar_correo.call_args.args
        return texto, cuerpo_html

    def test_el_html_no_trae_el_enlace_del_nombre(self):
        casos = {
            "codigo": (servicio.enviar_codigo, "123456"),
            "bienvenida": (servicio.enviar_bienvenida,),
        }
        for correo, (enviar, *resto) in casos.items():
            for nombre in (NOMBRE_CON_ENLACE, NOMBRE_SIN_ESPACIOS):
                with self.subTest(correo=correo, nombre=nombre):
                    _texto, cuerpo_html = self._correo_generado(enviar, nombre, *resto)
                    # La plantilla de bienvenida tiene su propio <a href> (el boton),
                    # asi que se busca el enlace falso, no cualquier enlace
                    self.assertNotIn('href="https://sitio-falso.example"', cuerpo_html)
                    self.assertNotIn("<a/href", cuerpo_html)
                    self.assertIn("&lt;a", cuerpo_html)     # se ve como texto

    def test_nombre_con_simbolos_se_ve_bien(self):
        texto, cuerpo_html = self._correo_generado(servicio.enviar_codigo, "María & José", "123456")
        self.assertIn("María &amp; José", cuerpo_html)
        self.assertIn("Hola María & José,", texto)          # el texto plano no se escapa
        self.assertIn("123456", cuerpo_html)

    def test_la_plantilla_propia_sigue_siendo_html(self):
        # El escape es solo para los datos: el enlace del boton de bienvenida sigue
        _texto, cuerpo_html = self._correo_generado(servicio.enviar_bienvenida, "Laura")
        self.assertIn('<a href="http://localhost:5173"', cuerpo_html)


class PruebasCabeceras(unittest.TestCase):
    """
    A-05: un salto de linea no puede agregar cabeceras (por ejemplo, Bcc) al correo.
    Lo impide el propio Python al armar el mensaje; esta prueba deja constancia.
    """

    def test_salto_de_linea_en_cabeceras_no_envia_nada(self):
        config = dict(CONFIG_PRUEBA, mode="gmail")
        casos = [
            ("destino@ejemplo.test\r\nBcc: otro@ejemplo.test", "Asunto"),
            ("destino@ejemplo.test", "Asunto\r\nBcc: otro@ejemplo.test"),
        ]
        for destino, asunto in casos:
            with self.subTest(destino=destino, asunto=asunto), \
                    mock.patch.dict(servicio.EMAIL_CONFIG, config), \
                    mock.patch.object(servicio.smtplib, "SMTP") as smtp:
                with self.assertRaises(email.errors.MessageError):
                    servicio.enviar_correo(destino, asunto, "Texto", "<p>Hola</p>")
                smtp.return_value.__enter__.return_value.sendmail.assert_not_called()


if __name__ == "__main__":
    unittest.main()
