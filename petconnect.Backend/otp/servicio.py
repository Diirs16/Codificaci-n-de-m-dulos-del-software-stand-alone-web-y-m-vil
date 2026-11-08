"""
Codigos de un solo uso (OTP) para verificar registro e inicio de sesion.

Item 4.6 de PRIORIDADES (A-12, NC-003): antes los codigos vivian en un diccionario
en la memoria de la API, sin candado entre hilos y sin limpiar los vencidos. Con
varios procesos (Gunicorn) el codigo se guardaba en uno y la verificacion podia
llegar a otro ("No hay verificacion pendiente"), y al reiniciar se perdian.

Ahora AlmacenOTP tiene las REGLAS y un "repositorio" decide DONDE se guarda:
  - OtpDAO (dao/otp_dao.py): tabla otp_pendientes. Es el que usa la API.
  - RepositorioMemoria (aqui abajo): diccionario con candado. Lo usan las pruebas
    y es el que se crea si no se indica otro.
Los dos tienen los mismos metodos (obtener, guardar, borrar, borrar_vencidos,
reservar_intento, devolver_intento, anotar_reenvio).

Reglas (no cambian):
  - el codigo vence a los 10 minutos;
  - con 5 fallos queda bloqueado (429) y se borra;
  - se compara en tiempo constante (hmac.compare_digest);
  - reenviar manda EL MISMO codigo, con 60 s de espera y maximo 3 reenvios;
  - pedir un codigo nuevo reinicia los contadores.

El codigo se guarda cifrado con Fernet (FERNET_KEY), nunca en claro: hay que poder
reenviar el mismo codigo, y un hash no se puede deshacer. Cada intento se "reserva"
antes de comparar (un solo UPDATE en la BD): aunque lleguen 20 intentos a la vez,
solo 5 llegan a comparar.

Ley 1581: los datos del registro pendiente (nombre, hash de la contrasena, prueba
de la autorizacion) se borran al verificar (quien llama usa descartar()), al
bloquearse y al vencer: cada vez que se crea un codigo se borran TODOS los vencidos.
"""

import hmac
import secrets
import threading
import time

EXPIRACION_SEGUNDOS = 600  # 10 minutos
MAX_INTENTOS = 5           # fallos permitidos por codigo (A-04, NC-006)
ESPERA_REENVIO_SEGUNDOS = 60   # minimo entre dos correos del mismo codigo (A-09, item 2.7)
MAX_REENVIOS = 3               # reenvios por codigo: como mucho 4 correos en total

PROPOSITOS = ("registro", "login")

# Datos que un flujo puede guardar junto al codigo -> columna de otp_pendientes
_COLUMNA_DE_DATO = {
    "name": "nombre",
    "password_hash": "password_hash",
    "id_usuario": "id_usuario",
    "fecha_autorizacion_datos": "fecha_autorizacion_datos",
    "version_politica_datos": "version_politica_datos",
}


def generar_codigo() -> str:
    """Codigo numerico de 6 digitos, criptograficamente seguro (no adivinable)."""
    return str(secrets.randbelow(900000) + 100000)


def _cifrar(codigo: str) -> str:
    # Import aqui: security.crypto exige FERNET_KEY al importarse
    from security.crypto import encrypt
    return encrypt(codigo)


def _descifrar(cifrado: str) -> str | None:
    """El codigo en claro, o None si no se puede descifrar (clave cambiada o dato alterado)."""
    from cryptography.fernet import InvalidToken
    from security.crypto import decrypt_estricto
    try:
        return decrypt_estricto(cifrado)
    except InvalidToken:
        return None


class AlmacenOTP:
    """
    Codigos pendientes de verificacion de un proposito ("registro" o "login"),
    junto con los datos que el flujo necesita recordar (nombre, hash de
    contrasena, id de usuario, prueba de la autorizacion).
    """

    def __init__(self, proposito: str = "registro", repositorio=None):
        if proposito not in PROPOSITOS:
            raise ValueError(f"Proposito de OTP desconocido: {proposito!r}")
        self._proposito = proposito
        self._repositorio = repositorio if repositorio is not None else RepositorioMemoria()

    def crear(self, clave: str, datos: dict | None = None) -> str:
        """Genera un codigo nuevo para `clave` (el correo) y lo guarda."""
        datos = datos or {}
        desconocidos = set(datos) - set(_COLUMNA_DE_DATO)
        if desconocidos:
            raise ValueError(f"Datos de OTP sin columna: {sorted(desconocidos)}")

        codigo = generar_codigo()
        ahora = time.time()
        self._repositorio.borrar_vencidos(ahora)      # Ley 1581: no guardar de mas
        fila = {columna: None for columna in _COLUMNA_DE_DATO.values()}
        for dato, valor in datos.items():
            fila[_COLUMNA_DE_DATO[dato]] = valor
        fila.update({
            "correo": clave,
            "proposito": self._proposito,
            "codigo_cifrado": _cifrar(codigo),
            "intentos": 0,        # pedir un codigo nuevo reinicia el contador
            "reenvios": 0,
            "vence": ahora + EXPIRACION_SEGUNDOS,
            "ultimo_envio": ahora,
        })
        self._repositorio.guardar(fila)
        return codigo

    def vigente(self, clave: str) -> dict | None:
        """
        Devuelve el pendiente de `clave` si todavia no vencio. Si ya vencio lo
        borra y devuelve None, para que se pueda crear uno nuevo (A-09).
        No cambia nada del pendiente vigente (ni contador ni vencimiento).
        """
        fila = self._obtener_vigente(clave)
        return self._pendiente(fila) if fila else None

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
        if self._obtener_vigente(clave) is None:
            return None
        anotado = self._repositorio.anotar_reenvio(
            clave, self._proposito, time.time(), ESPERA_REENVIO_SEGUNDOS,
            MAX_INTENTOS, MAX_REENVIOS)
        if not anotado:
            return None
        fila = self._repositorio.obtener(clave, self._proposito)
        return self._pendiente(fila) if fila else None

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
        # 1. Se lee la fila ANTES de gastar el intento. Si se leyera despues, otra
        #    peticion que llego tarde (6.o intento, "bloqueado") podria borrarla en
        #    medio y quien si gano su intento no tendria con que comparar: respondia
        #    "no_pendiente" aunque trajera el codigo correcto (visto con MariaDB).
        fila = self._repositorio.obtener(clave, self._proposito)
        if fila is None:
            return None, "no_pendiente"

        # 2. Se gasta un intento, de una vez en la BD; sin intento no se compara
        ahora = time.time()
        if not self._repositorio.reservar_intento(clave, self._proposito, ahora, MAX_INTENTOS):
            return None, self._motivo_sin_intento(clave, ahora)

        # 3. Se compara con el codigo leido en el paso 1
        guardado = _descifrar(fila["codigo_cifrado"])
        if guardado is None:
            # Ilegible (cambio la FERNET_KEY): nadie puede acertarlo, se pide otro
            self._repositorio.borrar(clave, self._proposito)
            return None, "expirado"
        if not _mismo_codigo(guardado, codigo):
            return None, "incorrecto"         # el intento ya quedo contado

        self._repositorio.devolver_intento(clave, self._proposito)   # acertar no gasta
        return self._pendiente(fila), None      # intentos: los de antes de este acierto

    def descartar(self, clave: str):
        self._repositorio.borrar(clave, self._proposito)

    def tiene_pendiente(self, clave: str) -> bool:
        return self._repositorio.obtener(clave, self._proposito) is not None

    def limpiar_vencidos(self) -> int:
        """Borra los codigos vencidos (de cualquier correo y proposito). Devuelve cuantos."""
        return self._repositorio.borrar_vencidos(time.time())

    # -- ayudantes ---------------------------------------------------------

    def _obtener_vigente(self, clave):
        fila = self._repositorio.obtener(clave, self._proposito)
        if fila is None:
            return None
        ahora = time.time()
        if ahora > fila["vence"]:
            # Solo borra lo vencido: si alguien acaba de pedir otro codigo, ese queda
            self._repositorio.borrar_vencidos(ahora)
            return None
        return fila

    def _motivo_sin_intento(self, clave, ahora) -> str:
        """Por que no se pudo gastar un intento: no hay, vencio o ya esta bloqueado."""
        fila = self._repositorio.obtener(clave, self._proposito)
        if fila is None:
            return "no_pendiente"
        if ahora > fila["vence"]:
            self._repositorio.borrar_vencidos(ahora)
            return "expirado"
        if fila["intentos"] < MAX_INTENTOS:
            # Justo ahora alguien pidio otro codigo (contadores en cero): no se borra
            return "incorrecto"
        # 5 fallos (A-04, NC-006): se borra y hay que pedir otro codigo
        self._repositorio.borrar(clave, self._proposito)
        return "bloqueado"

    def _pendiente(self, fila) -> dict | None:
        """
        La fila como la usa api.py: los datos guardados (solo los que tienen valor)
        mas "code", "expires", "intentos", "ultimo_envio" y "reenvios".
        """
        codigo = _descifrar(fila["codigo_cifrado"])
        if codigo is None:
            self._repositorio.borrar(fila["correo"], self._proposito)
            return None
        pendiente = {dato: fila[columna] for dato, columna in _COLUMNA_DE_DATO.items()
                     if fila[columna] is not None}
        pendiente.update({
            "code": codigo,
            "expires": fila["vence"],
            "intentos": fila["intentos"],
            "ultimo_envio": fila["ultimo_envio"],
            "reenvios": fila["reenvios"],
        })
        return pendiente


class RepositorioMemoria:
    """
    Guarda las filas de otp_pendientes en un diccionario, con un candado para que
    dos hilos no lo cambien a la vez. Hace lo mismo que OtpDAO pero solo sirve
    para UN proceso: lo usan las pruebas (y quien cree AlmacenOTP() sin repositorio).
    """

    def __init__(self):
        self._filas = {}
        self._candado = threading.Lock()

    def obtener(self, correo, proposito):
        with self._candado:
            fila = self._filas.get((correo, proposito))
            return dict(fila) if fila else None

    def guardar(self, fila):
        with self._candado:
            self._filas[(fila["correo"], fila["proposito"])] = dict(fila)

    def borrar(self, correo, proposito):
        with self._candado:
            self._filas.pop((correo, proposito), None)

    def borrar_vencidos(self, ahora):
        with self._candado:
            vencidas = [clave for clave, fila in self._filas.items() if fila["vence"] < ahora]
            for clave in vencidas:
                del self._filas[clave]
            return len(vencidas)

    def reservar_intento(self, correo, proposito, ahora, max_intentos):
        with self._candado:
            fila = self._filas.get((correo, proposito))
            if fila is None or fila["intentos"] >= max_intentos or fila["vence"] < ahora:
                return False
            fila["intentos"] += 1
            return True

    def devolver_intento(self, correo, proposito):
        with self._candado:
            fila = self._filas.get((correo, proposito))
            if fila is not None and fila["intentos"] > 0:
                fila["intentos"] -= 1

    def anotar_reenvio(self, correo, proposito, ahora, espera, max_intentos, max_reenvios):
        with self._candado:
            fila = self._filas.get((correo, proposito))
            if (fila is None or fila["vence"] < ahora or fila["intentos"] >= max_intentos
                    or fila["ultimo_envio"] > ahora - espera or fila["reenvios"] >= max_reenvios):
                return False
            fila["reenvios"] += 1
            fila["ultimo_envio"] = ahora
            return True


def _mismo_codigo(guardado: str, recibido: str) -> bool:
    """
    Compara en tiempo constante (hmac.compare_digest) para no dar pistas por lo
    que tarda la respuesta. Se compara en bytes: con texto no ASCII (ej. digitos
    de ancho completo '１２３４５６') compare_digest lanzaria TypeError.
    """
    return hmac.compare_digest(guardado.encode("utf-8"), recibido.encode("utf-8"))
