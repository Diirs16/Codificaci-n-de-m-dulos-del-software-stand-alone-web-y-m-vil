"""
Codigos de un solo uso (OTP) para verificar registro e inicio de sesion.

Guardados en memoria (no en base de datos): suficiente para el alcance de
este proyecto, ya que expiran solos y se descartan al usarse. Aislado de
api.py para poder reutilizarse en cualquier flujo que necesite un codigo
de verificacion (registro, login, recuperar contrasena, etc.) sin repetir
la logica de generar/expirar/validar en cada endpoint.
"""

import hmac
import secrets
import time

EXPIRACION_SEGUNDOS = 600  # 10 minutos
MAX_INTENTOS = 5           # fallos permitidos por codigo (A-04, NC-006)


def generar_codigo() -> str:
    """Codigo numerico de 6 digitos, criptograficamente seguro (no adivinable)."""
    return str(secrets.randbelow(900000) + 100000)


class AlmacenOTP:
    """
    Guarda codigos pendientes de verificacion en memoria, junto con
    cualquier dato adicional que el flujo necesite recordar (nombre,
    hash de contrasena, id de usuario, etc.).
    """

    def __init__(self):
        self._pendientes = {}

    def crear(self, clave: str, datos: dict | None = None) -> str:
        """Genera un codigo nuevo para `clave` (normalmente un correo) y lo guarda."""
        codigo = generar_codigo()
        self._pendientes[clave] = {
            **(datos or {}),
            "code": codigo,
            "expires": time.time() + EXPIRACION_SEGUNDOS,
            "intentos": 0,   # pedir un codigo nuevo reinicia el contador
        }
        return codigo

    def verificar(self, clave: str, codigo: str) -> tuple[dict | None, str | None]:
        """
        Retorna (datos_guardados, None) si el codigo es valido.
        Retorna (None, motivo) si no: motivo es "no_pendiente" | "expirado" |
        "bloqueado" | "incorrecto".

        Tras MAX_INTENTOS fallos, el siguiente intento (aunque traiga el codigo
        correcto) borra la entrada y devuelve "bloqueado": hay que pedir otro
        codigo. Desde ahi, como ya no hay entrada, responde "no_pendiente".

        No descarta la entrada al acertar: eso lo decide quien llama, con
        `descartar()`, una vez que su propia logica (ej. crear el usuario
        en la base de datos) haya terminado con exito. Asi, si esa logica
        falla, el codigo sigue siendo valido para reintentar.
        """
        pendiente = self._pendientes.get(clave)
        if not pendiente:
            return None, "no_pendiente"

        if time.time() > pendiente["expires"]:
            del self._pendientes[clave]
            return None, "expirado"

        if pendiente["intentos"] >= MAX_INTENTOS:
            del self._pendientes[clave]
            return None, "bloqueado"

        if not _mismo_codigo(pendiente["code"], codigo):
            pendiente["intentos"] += 1
            return None, "incorrecto"

        return pendiente, None

    def descartar(self, clave: str):
        self._pendientes.pop(clave, None)

    def tiene_pendiente(self, clave: str) -> bool:
        return clave in self._pendientes


def _mismo_codigo(guardado: str, recibido: str) -> bool:
    """
    Compara en tiempo constante (hmac.compare_digest) para no dar pistas por lo
    que tarda la respuesta. Se compara en bytes: con texto no ASCII (ej. digitos
    de ancho completo '１２３４５６') compare_digest lanzaria TypeError.
    """
    return hmac.compare_digest(guardado.encode("utf-8"), recibido.encode("utf-8"))
