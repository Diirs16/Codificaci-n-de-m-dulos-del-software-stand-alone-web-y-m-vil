"""
Generacion y verificacion de tokens JWT para autenticacion de la API.
El secreto vive en .env (JWT_SECRET), nunca en el codigo.
"""
import os
import time
import jwt

# Sin valor por defecto (NC-007): con un secreto conocido cualquiera puede firmar
# tokens validos. HS256 pide una clave de al menos 32 bytes (RFC 7518, 3.2).
# El mensaje de error nunca muestra el valor recibido.
_MIN_BYTES = 32
_SECRET    = os.environ.get("JWT_SECRET", "")
if len(_SECRET.encode("utf-8")) < _MIN_BYTES:
    raise RuntimeError(
        f"JWT_SECRET falta en .env o tiene menos de {_MIN_BYTES} bytes. Genera uno con: "
        'python -c "import secrets; print(secrets.token_hex(32))" '
        "y pegalo a mano en la linea JWT_SECRET= de .env"
    )

_ALGORITHM = "HS256"
_EXPIRE    = 24 * 3600  # 24 horas en segundos


def generate_token(user_id: int, email: str) -> str:
    # El estandar JWT (RFC 7519) exige que "sub" sea texto; PyJWT >= 2.10 rechaza
    # un entero (NC-008). Quien lo lea debe convertirlo de nuevo con int().
    payload = {
        "sub":   str(user_id),
        "email": email,
        "iat":   int(time.time()),
        "exp":   int(time.time()) + _EXPIRE,
    }
    return jwt.encode(payload, _SECRET, algorithm=_ALGORITHM)


def verify_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, _SECRET, algorithms=[_ALGORITHM])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
