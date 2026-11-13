import os
from dotenv import load_dotenv
load_dotenv()

MODO_POR_DEFECTO = "smtp"


def normalizar_modo(valor) -> str:
    """
    Item 6.12: " Gmail " o "BREVO" valen como "gmail" y "brevo". Vacio o sin
    definir = MODO_POR_DEFECTO. Un modo que no existe lo rechaza correo/servicio.py
    (antes caia sin aviso en Mailtrap).
    """
    return (valor or MODO_POR_DEFECTO).strip().lower() or MODO_POR_DEFECTO


EMAIL_CONFIG = {
    # Modo: "brevo" -> API HTTPS de Brevo (funciona en Railway Hobby, que bloquea SMTP)
    #       "sdk"   -> API de Mailtrap (requiere dominio verificado)
    #       "smtp"  -> sandbox de Mailtrap (sirve para pruebas, no llega a bandejas reales)
    #       "gmail" -> SMTP real de Gmail (el correo SI llega a la bandeja del destinatario)
    "mode":        normalizar_modo(os.getenv("EMAIL_MODE")),

    # SDK (dominio verificado)
    "api_token":   os.getenv("MAILTRAP_API_TOKEN", ""),
    "sender":      os.getenv("MAILTRAP_SENDER", "hello@demomailtrap.co"),
    "sender_name": "PetConnect",

    # SMTP sandbox de Mailtrap (Email Testing)
    "smtp_host":   os.getenv("MAILTRAP_SMTP_HOST", "sandbox.smtp.mailtrap.io"),
    "smtp_port":   int(os.getenv("MAILTRAP_SMTP_PORT", 587)),
    "smtp_user":   os.getenv("MAILTRAP_SMTP_USER", ""),
    "smtp_pass":   os.getenv("MAILTRAP_SMTP_PASS", ""),

    # SMTP real de Gmail. GMAIL_APP_PASSWORD debe ser una "contrasena de
    # aplicacion" de 16 caracteres (NO la contrasena normal de la cuenta),
    # generada en https://myaccount.google.com/apppasswords - requiere
    # tener la verificacion en dos pasos activada en la cuenta de Gmail.
    "gmail_host":          "smtp.gmail.com",
    "gmail_port":          587,
    "gmail_user":          os.getenv("GMAIL_USER", ""),
    "gmail_app_password":  os.getenv("GMAIL_APP_PASSWORD", ""),

    # API HTTPS de Brevo (item 6.12). BREVO_API_KEY se genera en Brevo, en
    # "SMTP y API" -> "Claves de API". BREVO_SENDER es un remitente que ya
    # validaste en Brevo ("Remitentes"); si es un Gmail, Brevo lo cambia por una
    # direccion @brevosend.com porque no puede autenticar dominios gratuitos.
    "brevo_api_key":  os.getenv("BREVO_API_KEY", ""),
    "brevo_sender":   os.getenv("BREVO_SENDER", ""),
}
