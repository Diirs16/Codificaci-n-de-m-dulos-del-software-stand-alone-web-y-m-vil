"""
Almacenamiento seguro de contrasenas (requisito RS03, no conformidad NC-001).

Las contrasenas se guardan con bcrypt: sal aleatoria por usuario y factor de
costo 12. Los hashes SHA-256 heredados (64 caracteres hexadecimales, sin sal)
solo se aceptan para migrarlos a bcrypt en el siguiente inicio de sesion
exitoso; nunca se generan hashes nuevos con SHA-256.

Uso:
    from security.passwords import hash_password, verificar_password

    guardado = hash_password("Firulais2026!")          # guardar en BD
    verificar_password("Firulais2026!", guardado)      # True

Item 4.18 (A-14): para no revelar por el tiempo de respuesta si un correo tiene
cuenta, el inicio de sesion sin usuario compara contra hash_de_relleno() y una
cuenta con hash heredado tambien paga un bcrypt. Asi los tres casos (sin cuenta,
cuenta bcrypt, cuenta heredada) hacen el mismo trabajo cuando la clave es mala.
"""
import hashlib
import hmac
import re
import secrets

import bcrypt

COSTO_BCRYPT = 12
MAX_BYTES_BCRYPT = 72   # bcrypt solo procesa los primeros 72 bytes
_SHA256_HEREDADO = re.compile(r"^[0-9a-f]{64}$")


def hash_password(password: str) -> str:
    """Retorna el hash bcrypt (60 caracteres, prefijo $2b$12$) de la contrasena."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=COSTO_BCRYPT)).decode("ascii")


# Item 4.18: hash bcrypt de un texto aleatorio que nadie conoce (no es un secreto:
# solo sirve para gastar el mismo tiempo). Se crea al importar el modulo, con el
# mismo costo que los hashes reales, para que la primera peticion no tarde el doble.
_HASH_RELLENO = hash_password(secrets.token_urlsafe(32))


def hash_de_relleno() -> str:
    """Hash bcrypt con el que se compara cuando el correo no tiene cuenta (4.18)."""
    return _HASH_RELLENO


def es_hash_heredado(password_hash: str) -> bool:
    """True si el hash guardado es un SHA-256 sin sal del sistema anterior."""
    return bool(password_hash) and _SHA256_HEREDADO.match(password_hash) is not None


def _bcrypt_coincide(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("ascii"))
    except ValueError:
        # Contrasena de mas de 72 bytes o hash con formato invalido
        return False


def verificar_password(password: str, password_hash: str) -> bool:
    """Compara la contrasena con el hash guardado (bcrypt o SHA-256 heredado)."""
    if not password or not password_hash:
        return False
    if es_hash_heredado(password_hash):
        # Item 4.18: el SHA-256 es instantaneo; sin este bcrypt de relleno (cuyo
        # resultado se descarta) una cuenta heredada responderia tan rapido como un
        # correo sin cuenta y se distinguiria de las cuentas con bcrypt.
        _bcrypt_coincide(password, _HASH_RELLENO)
        calculado = hashlib.sha256(password.encode()).hexdigest()
        return hmac.compare_digest(calculado, password_hash)
    return _bcrypt_coincide(password, password_hash)
