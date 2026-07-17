import os
from dotenv import load_dotenv
load_dotenv()

EMAIL_CONFIG = {
    # Modo: "sdk" usa API de Mailtrap (requiere dominio verificado)
    #       "smtp" usa sandbox de Mailtrap (funciona para cualquier correo sin dominio)
    "mode":        os.getenv("EMAIL_MODE", "smtp"),

    # SDK (dominio verificado)
    "api_token":   os.getenv("MAILTRAP_API_TOKEN", ""),
    "sender":      os.getenv("MAILTRAP_SENDER", "hello@demomailtrap.co"),
    "sender_name": "PetConnect",

    # SMTP sandbox (Email Testing)
    "smtp_host":   os.getenv("MAILTRAP_SMTP_HOST", "sandbox.smtp.mailtrap.io"),
    "smtp_port":   int(os.getenv("MAILTRAP_SMTP_PORT", 587)),
    "smtp_user":   os.getenv("MAILTRAP_SMTP_USER", ""),
    "smtp_pass":   os.getenv("MAILTRAP_SMTP_PASS", ""),
}
