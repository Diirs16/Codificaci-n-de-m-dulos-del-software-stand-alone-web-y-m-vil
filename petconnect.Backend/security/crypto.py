"""
Cifrado simetrico con Fernet para datos que se guardan en la base de datos.
La clave vive en .env (FERNET_KEY), nunca en el codigo ni en la BD.

Hoy lo usan los codigos OTP (item 4.6, otp/servicio.py). El telefono NO se
cifra: se decidio en el item 4.8 (A-13) dejarlo en claro y corregir el
comentario de api.py que decia lo contrario.

Uso:
    from security.crypto import encrypt, decrypt

    cifrado = encrypt("123456")          # guardar en BD
    original = decrypt(cifrado)          # recuperar; si no se puede, InvalidToken
"""
import os
from cryptography.fernet import Fernet

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
    """
    Descifra un valor previamente cifrado con encrypt().

    Si el texto no se puede descifrar (clave cambiada, dato alterado o un texto
    que nunca fue cifrado) lanza cryptography.fernet.InvalidToken. Antes del
    item 4.8 (A-13, NC-007) devolvia el texto cifrado como si fuera el original:
    un dato ilegible nunca debe mostrarse, compararse ni enviarse sin avisar.
    Vacio o None se devuelven igual, como hace encrypt().
    """
    if not value:
        return value
    return _fernet.decrypt(value.encode()).decode()
