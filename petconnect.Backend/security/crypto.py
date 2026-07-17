"""
Cifrado simetrico con Fernet para datos sensibles en la base de datos.
La clave vive en .env (FERNET_KEY), nunca en el codigo ni en la BD.

Uso:
    from security.crypto import encrypt, decrypt

    cifrado = encrypt("3001234567")      # guardar en BD
    original = decrypt(cifrado)          # recuperar para mostrar
"""
import os
from cryptography.fernet import Fernet, InvalidToken

_raw_key = os.environ.get("FERNET_KEY", "")
if not _raw_key:
    raise RuntimeError(
        "FERNET_KEY no esta en .env. Ejecuta: python generate_keys.py"
    )

_fernet = Fernet(_raw_key.encode())


def encrypt(value: str) -> str:
    """Cifra un valor de texto. Retorna cadena cifrada en base64."""
    if not value:
        return value
    return _fernet.encrypt(value.encode()).decode()


def decrypt(value: str) -> str:
    """Descifra un valor previamente cifrado con encrypt()."""
    if not value:
        return value
    try:
        return _fernet.decrypt(value.encode()).decode()
    except (InvalidToken, Exception):
        return value
