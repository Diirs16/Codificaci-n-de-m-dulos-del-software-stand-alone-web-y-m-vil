"""
Servicio de envio de correo de PetConnect.

Soporta 3 modos configurables via EMAIL_CONFIG (config/email_config.py):
    sdk   -> API de Mailtrap
    smtp  -> sandbox de Mailtrap
    gmail -> SMTP real de Gmail

Aislado del resto de la API para poder agregar nuevos tipos de correo
(recordatorios, notificaciones de pedidos, etc.) sin tocar api.py.
"""

import html
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import mailtrap as mt

from config.email_config import EMAIL_CONFIG
from correo.plantillas import HTML_AVISO_REGISTRO, HTML_CODE, HTML_WELCOME

ASUNTO_AVISO_REGISTRO = "PetConnect - Intento de registro con tu correo"
CORREO_ATENCION = "proyectopetconnect+atencion@gmail.com"   # canal de A.8 de la politica


def enviar_correo(to_email: str, asunto: str, texto: str, html: str):
    modo = EMAIL_CONFIG["mode"]

    if modo in ("smtp", "gmail"):
        if modo == "gmail":
            host, port = EMAIL_CONFIG["gmail_host"], EMAIL_CONFIG["gmail_port"]
            user, password = EMAIL_CONFIG["gmail_user"], EMAIL_CONFIG["gmail_app_password"]
        else:
            host, port = EMAIL_CONFIG["smtp_host"], EMAIL_CONFIG["smtp_port"]
            user, password = EMAIL_CONFIG["smtp_user"], EMAIL_CONFIG["smtp_pass"]

        if not user or not password:
            raise RuntimeError(f"Modo de correo '{modo}' sin credenciales configuradas en .env")

        msg = MIMEMultipart("alternative")
        msg["From"]    = f"PetConnect <{user}>"
        msg["To"]      = to_email
        msg["Subject"] = asunto
        msg.attach(MIMEText(texto, "plain"))
        msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP(host, port) as s:
            s.ehlo()
            # Sin contexto, starttls() no revisa el certificado del servidor (A-06)
            s.starttls(context=ssl.create_default_context())
            s.login(user, password)
            s.sendmail(user, to_email, msg.as_string())
    else:
        mail = mt.Mail(
            sender=mt.Address(email=EMAIL_CONFIG["sender"], name=EMAIL_CONFIG["sender_name"]),
            to=[mt.Address(email=to_email)],
            subject=asunto,
            text=texto,
            html=html,
        )
        mt.MailtrapClient(token=EMAIL_CONFIG["api_token"]).send(mail)


def enviar_codigo(
    to_email: str,
    name: str,
    code: str,
    asunto: str = "PetConnect - Codigo de verificacion",
    proposito: str = "Usa este codigo para verificar tu correo:",
):
    # A-05: todo dato se escapa antes de entrar al HTML. Asi un nombre como
    # '<a href="...">' se ve como texto y no se convierte en un enlace del correo.
    # El texto plano no se escapa: ahi las etiquetas no se dibujan.
    cuerpo_html = HTML_CODE.format(
        name=html.escape(name),
        code=html.escape(code),
        proposito=html.escape(proposito),
    )
    texto = f"Hola {name},\n\n{proposito}\n\n{code}\n\nExpira en 10 minutos.\n\nEquipo PetConnect"
    enviar_correo(to_email, asunto, texto, cuerpo_html)


def enviar_bienvenida(to_email: str, name: str):
    cuerpo_html = HTML_WELCOME.format(name=html.escape(name))
    texto = (
        f"Bienvenido a la familia PetConnect, {name}!\n\n"
        "Todo para tu mascota en un solo lugar: productos de calidad y un "
        "programa de adopcion responsable.\n\n"
        "Equipo PetConnect"
    )
    enviar_correo(to_email, "Bienvenido a la familia PetConnect", texto, cuerpo_html)


def enviar_aviso_cuenta_existente(to_email: str, name: str):
    """
    Item 4.10 (A-14): alguien intento registrarse con un correo que ya tiene cuenta.
    La API le responde lo mismo que a un registro nuevo (para no revelar la cuenta)
    y este aviso le cuenta al titular lo que paso. `name` es el nombre guardado en la
    cuenta, nunca el que escribio quien intento registrarse (A-05). No lleva codigo.
    """
    cuerpo_html = HTML_AVISO_REGISTRO.format(name=html.escape(name))
    texto = (
        f"Hola {name},\n\n"
        "Alguien intento crear una cuenta en PetConnect con este correo, pero ya tienes una.\n\n"
        "Si fuiste tu, no necesitas registrarte: inicia sesion con tu correo y tu contrasena.\n\n"
        "Si no fuiste tu, puedes ignorar este mensaje: no se creo ninguna cuenta ni cambio "
        "tu contrasena.\n\n"
        f"Olvidaste tu contrasena? Escribenos a {CORREO_ATENCION}.\n\n"
        "Equipo PetConnect"
    )
    enviar_correo(to_email, ASUNTO_AVISO_REGISTRO, texto, cuerpo_html)
