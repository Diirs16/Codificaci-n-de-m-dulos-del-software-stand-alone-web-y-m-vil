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


def generate_token(user_id: int, version_sesion: int) -> str:
    # El estandar JWT (RFC 7519) exige que "sub" sea texto; PyJWT >= 2.10 rechaza
    # un entero (NC-008). Quien lo lea debe convertirlo de nuevo con int().
    # Item 4.13 (A-03): "ver" es usuarios.version_sesion al iniciar sesion;
    # require_auth la compara con la BD y, si alguien cerro las sesiones (la BD
    # sumo 1), el token deja de valer antes de las 24 h. El token NO lleva el
    # correo: un JWT se puede leer (base64, no esta cifrado) y es un dato personal
    # (Ley 1581). Solo el id, la version y las fechas.
    if type(version_sesion) is not int or version_sesion < 0:   # bool no vale
        raise ValueError("version_sesion debe ser un entero mayor o igual a 0")
    payload = {
        "sub": str(user_id),
        "ver": version_sesion,
        "iat": int(time.time()),
        "exp": int(time.time()) + _EXPIRE,
    }
    return jwt.encode(payload, _SECRET, algorithm=_ALGORITHM)


def verify_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, _SECRET, algorithms=[_ALGORITHM])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
