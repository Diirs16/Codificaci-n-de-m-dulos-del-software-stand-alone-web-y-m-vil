"""
Servicio de envio de correo de PetConnect.

Soporta 3 modos configurables via EMAIL_CONFIG (config/email_config.py):
    sdk   -> API de Mailtrap
    smtp  -> sandbox de Mailtrap
    gmail -> SMTP real de Gmail

Aislado del resto de la API para poder agregar nuevos tipos de correo
(recordatorios, notificaciones de pedidos, etc.) sin tocar api.py.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import mailtrap as mt

from config.email_config import EMAIL_CONFIG
from correo.plantillas import HTML_CODE, HTML_WELCOME


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
            s.starttls()
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
    html = HTML_CODE.format(name=name, code=code, proposito=proposito)
    texto = f"Hola {name},\n\n{proposito}\n\n{code}\n\nExpira en 10 minutos.\n\nEquipo PetConnect"
    enviar_correo(to_email, asunto, texto, html)


def enviar_bienvenida(to_email: str, name: str):
    html = HTML_WELCOME.format(name=name)
    texto = (
        f"Bienvenido a la familia PetConnect, {name}!\n\n"
        "Todo para tu mascota en un solo lugar: productos de calidad y un "
        "programa de adopcion responsable.\n\n"
        "Equipo PetConnect"
    )
    enviar_correo(to_email, "Bienvenido a la familia PetConnect", texto, html)
