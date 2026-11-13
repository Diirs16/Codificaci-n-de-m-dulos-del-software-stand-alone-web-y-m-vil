"""
Pruebas de regresion del servicio de correo: A-06 (TLS con certificado verificado),
A-05 (los datos del usuario se escapan en el HTML y no inyectan cabeceras) y el
item 6.12 (modo "brevo": correo por HTTPS, que Railway Hobby no bloquea).
No envian correos ni abren conexiones: smtplib.SMTP y urlopen se reemplazan por mocks.

Ejecutar desde petconnect.Backend, con el entorno virtual activo:
    python -m unittest discover -s tests -v
"""
import email.errors
import io
import json
import os
import ssl
import sys
import unittest
import urllib.error
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# No cargar el .env real al importar config.email_config; se restaura despues
# para no afectar a las otras pruebas que corren en el mismo proceso
import dotenv  # noqa: E402

_load_dotenv_original = dotenv.load_dotenv
dotenv.load_dotenv = lambda *a, **k: False
try:
    from config import email_config  # noqa: E402
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


# Valores inventados (nunca una clave ni un correo reales)
CONFIG_BREVO = {
    "mode": "brevo",
    "brevo_api_key": "clave-api-inventada",
    "brevo_sender": "remitente@ejemplo.test",
}
DESTINO = "destino@ejemplo.test"


def _respuesta_brevo(estado=201):
    """Lo que devuelve urlopen dentro del 'with': una respuesta con su codigo HTTP."""
    respuesta = mock.MagicMock()
    respuesta.status = estado
    respuesta.__enter__.return_value = respuesta
    return respuesta


class PruebasBrevo(unittest.TestCase):
    """
    Item 6.12: Railway Hobby bloquea SMTP (puertos 25, 465 y 587). El modo "brevo"
    envia por la API HTTPS de Brevo (puerto 443) con urllib, sin dependencias nuevas.
    """

    def _enviar(self, config=None, respuesta=None, error=None):
        """Envia con urlopen simulado y devuelve el mock para revisar la peticion."""
        urlopen = mock.MagicMock(return_value=respuesta or _respuesta_brevo())
        if error is not None:
            urlopen.side_effect = error
        with mock.patch.dict(servicio.EMAIL_CONFIG, config or CONFIG_BREVO), \
                mock.patch.object(servicio.urllib.request, "urlopen", urlopen):
            servicio.enviar_correo(DESTINO, "Asunto", "Texto 123456", "<p>Hola 123456</p>")
        return urlopen

    def test_envia_por_https_a_la_api_de_brevo(self):
        urlopen = self._enviar()
        peticion = urlopen.call_args.args[0]
        self.assertEqual(peticion.full_url, "https://api.brevo.com/v3/smtp/email")
        self.assertEqual(peticion.get_method(), "POST")
        # urllib guarda los nombres de cabecera con solo la primera letra en mayuscula
        self.assertEqual(peticion.get_header("Api-key"), "clave-api-inventada")
        self.assertEqual(peticion.get_header("Content-type"), "application/json")
        cuerpo = json.loads(peticion.data.decode("utf-8"))
        self.assertEqual(cuerpo["sender"], {"name": "PetConnect", "email": "remitente@ejemplo.test"})
        self.assertEqual(cuerpo["to"], [{"email": DESTINO}])
        self.assertEqual(cuerpo["subject"], "Asunto")
        self.assertEqual(cuerpo["textContent"], "Texto 123456")
        self.assertEqual(cuerpo["htmlContent"], "<p>Hola 123456</p>")

    def test_la_peticion_tiene_tiempo_maximo_y_verifica_el_certificado(self):
        urlopen = self._enviar()
        tiempo = urlopen.call_args.kwargs.get("timeout")
        self.assertIsNotNone(tiempo, "sin timeout una red lenta deja el hilo esperando")
        self.assertGreater(tiempo, 0)
        self.assertLess(tiempo, 30)          # menos que el limite de Gunicorn
        contexto = urlopen.call_args.kwargs.get("context")
        self.assertIsInstance(contexto, ssl.SSLContext)
        self.assertEqual(contexto.verify_mode, ssl.CERT_REQUIRED)
        self.assertTrue(contexto.check_hostname)

    def test_sin_clave_o_sin_remitente_no_se_conecta(self):
        for falta in ("brevo_api_key", "brevo_sender"):
            with self.subTest(falta=falta):
                config = dict(CONFIG_BREVO, **{falta: ""})
                urlopen = mock.MagicMock()
                with mock.patch.dict(servicio.EMAIL_CONFIG, config), \
                        mock.patch.object(servicio.urllib.request, "urlopen", urlopen):
                    with self.assertRaises(RuntimeError):
                        servicio.enviar_correo(DESTINO, "Asunto", "Texto", "<p>Hola</p>")
                urlopen.assert_not_called()

    def test_error_de_brevo_avisa_el_codigo_http_sin_el_correo_ni_la_clave(self):
        # Brevo puede repetir el correo del destinatario en su respuesta de error
        cuerpo = io.BytesIO(f'{{"message": "invalid recipient {DESTINO}"}}'.encode("utf-8"))
        error = urllib.error.HTTPError(
            "https://api.brevo.com/v3/smtp/email", 401, "Unauthorized", {}, cuerpo)
        with self.assertLogs("correo.servicio", level="WARNING") as registro, \
                self.assertRaises(RuntimeError) as contexto:
            self._enviar(error=error)
        mensajes = " ".join(registro.output) + " " + str(contexto.exception)
        self.assertIn("401", mensajes)              # para saber que fallo
        self.assertNotIn(DESTINO, mensajes)         # Ley 1581
        self.assertNotIn("clave-api-inventada", mensajes)
        # Sin la excepcion original encadenada (su texto no llega a ningun registro)
        self.assertIsNone(contexto.exception.__cause__)
        self.assertTrue(contexto.exception.__suppress_context__)

    def test_respuesta_inesperada_cuenta_como_fallo(self):
        with self.assertLogs("correo.servicio", level="WARNING") as registro, \
                self.assertRaises(RuntimeError):
            self._enviar(respuesta=_respuesta_brevo(estado=204))
        self.assertIn("204", " ".join(registro.output))


class PruebasModo(unittest.TestCase):
    """Item 6.12: un EMAIL_MODE mal escrito ya no cae sin aviso en Mailtrap."""

    def test_el_modo_ignora_mayusculas_y_espacios(self):
        for escrito, esperado in ((" Gmail ", "gmail"), ("BREVO", "brevo"),
                                  ("", "smtp"), (None, "smtp")):
            with self.subTest(escrito=escrito):
                self.assertEqual(email_config.normalizar_modo(escrito), esperado)

    def test_modo_desconocido_da_error_sin_enviar(self):
        with mock.patch.dict(servicio.EMAIL_CONFIG, {"mode": "gmial"}), \
                mock.patch.object(servicio.mt, "MailtrapClient") as cliente, \
                mock.patch.object(servicio.smtplib, "SMTP") as smtp, \
                mock.patch.object(servicio.urllib.request, "urlopen") as urlopen:
            with self.assertRaises(RuntimeError):
                servicio.enviar_correo(DESTINO, "Asunto", "Texto", "<p>Hola</p>")
        cliente.assert_not_called()
        smtp.assert_not_called()
        urlopen.assert_not_called()

    def test_el_modo_sdk_sigue_usando_mailtrap(self):
        config = {"mode": "sdk", "api_token": "token-inventado"}
        with mock.patch.dict(servicio.EMAIL_CONFIG, config), \
                mock.patch.object(servicio.mt, "MailtrapClient") as cliente:
            servicio.enviar_correo(DESTINO, "Asunto", "Texto", "<p>Hola</p>")
        cliente.return_value.send.assert_called_once()


if __name__ == "__main__":
    unittest.main()
