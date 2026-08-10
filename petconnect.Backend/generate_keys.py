"""
Ejecuta este script UNA sola vez para generar las claves de seguridad.
Crea el archivo .env con todas las credenciales necesarias.
"""
import os
from cryptography.fernet import Fernet

fernet_key = Fernet.generate_key().decode()
jwt_secret  = os.urandom(32).hex()

env = f"""# ================================================================
# PETCONNECT - Variables de entorno (NO subir a Git / GitHub)
# ================================================================

# Base de datos
DB_HOST=localhost
DB_PORT=3310
DB_NAME=petconnect
DB_USER=root
DB_PASSWORD=

# Envio de correo (opcional: si falla o no esta configurado, el codigo de
# verificacion se imprime en la consola del servidor igualmente)
# EMAIL_MODE=sdk | smtp | gmail  (ver comentarios en .env.example)
EMAIL_MODE=gmail

MAILTRAP_API_TOKEN=
MAILTRAP_SENDER=noreply@tudominio.com

# Gmail SMTP: GMAIL_APP_PASSWORD es una "contrasena de aplicacion" de 16
# caracteres (no la contrasena normal), generada en
# https://myaccount.google.com/apppasswords
GMAIL_USER=
GMAIL_APP_PASSWORD=

# Claves de seguridad (generadas automaticamente - NUNCA compartir)
JWT_SECRET={jwt_secret}
FERNET_KEY={fernet_key}
"""

with open(".env", "w", encoding="utf-8") as f:
    f.write(env)

print("[OK] .env generado correctamente")
print(f"     JWT_SECRET : {jwt_secret[:12]}...")
print(f"     FERNET_KEY : {fernet_key[:12]}...")
print()
print("IMPORTANTE: Nunca subas el archivo .env a GitHub.")
