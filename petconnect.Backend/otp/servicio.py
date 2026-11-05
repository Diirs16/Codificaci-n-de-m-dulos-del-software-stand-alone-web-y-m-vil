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
ESPERA_REENVIO_SEGUNDOS = 60   # minimo entre dos correos del mismo codigo (A-09, item 2.7)
MAX_REENVIOS = 3               # reenvios por codigo: como mucho 4 correos en total


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
        ahora = time.time()
        self._pendientes[clave] = {
            **(datos or {}),
            "code": codigo,
            "expires": ahora + EXPIRACION_SEGUNDOS,
            "intentos": 0,        # pedir un codigo nuevo reinicia el contador
            "ultimo_envio": ahora,
            "reenvios": 0,
        }
        return codigo

    def vigente(self, clave: str) -> dict | None:
        """
        Devuelve el pendiente de `clave` si todavia no vencio. Si ya vencio lo
        borra y devuelve None, para que se pueda crear uno nuevo (A-09).
        No cambia nada del pendiente vigente (ni contador ni vencimiento).
        """
        pendiente = self._pendientes.get(clave)
        if not pendiente:
            return None
        if time.time() > pendiente["expires"]:
            del self._pendientes[clave]
            return None
        return pendiente

    def para_reenviar(self, clave: str) -> dict | None:
        """
        Devuelve el pendiente si se puede reenviar SU MISMO codigo y anota el
        reenvio; si no, None. Quien llama responde lo mismo en ambos casos
        (no revela si hay un registro en curso, A-14). No se reenvia si:
          - no hay pendiente o ya vencio (reenviar no alarga los 10 minutos);
          - ya lleva MAX_INTENTOS fallos (el codigo ya no sirve, esta bloqueado);
          - no han pasado ESPERA_REENVIO_SEGUNDOS desde el ultimo correo;
          - ya se reenvio MAX_REENVIOS veces (para no llenar el buzon de nadie).
        El contador de intentos no se toca: reenviar no da intentos nuevos.
        """
        pendiente = self.vigente(clave)
        if pendiente is None or pendiente["intentos"] >= MAX_INTENTOS:
            return None
        ahora = time.time()
        if ahora - pendiente["ultimo_envio"] < ESPERA_REENVIO_SEGUNDOS:
            return None
        if pendiente["reenvios"] >= MAX_REENVIOS:
            return None
        pendiente["ultimo_envio"] = ahora
        pendiente["reenvios"] += 1
        return pendiente

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
