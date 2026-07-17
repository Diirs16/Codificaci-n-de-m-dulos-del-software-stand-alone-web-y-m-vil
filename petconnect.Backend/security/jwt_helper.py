"""
Generacion y verificacion de tokens JWT para autenticacion de la API.
El secreto vive en .env (JWT_SECRET), nunca en el codigo.
"""
import os
import time
import jwt

_SECRET    = os.environ.get("JWT_SECRET", "dev-secret-inseguro")
_ALGORITHM = "HS256"
_EXPIRE    = 7 * 24 * 3600  # 7 dias en segundos


def generate_token(user_id: int, email: str) -> str:
    payload = {
        "sub":   user_id,
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
