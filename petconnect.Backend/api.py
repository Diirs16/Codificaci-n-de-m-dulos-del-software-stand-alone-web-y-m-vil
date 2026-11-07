"""
API REST de PetConnect.
Ejecutar con: python api.py
"""

import sys
import os
import re
import json
import secrets
import threading
import traceback
from collections import OrderedDict
from datetime import datetime, date
from functools import wraps

# Cargar .env antes que cualquier import de config
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import dns.resolver
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from mysql.connector.errors import InterfaceError, OperationalError
from werkzeug.exceptions import BadRequest, HTTPException

from conexion.conexion_bd import ConexionBD, conexion_y_cursor
from dao.usuario_dao import UsuarioDAO
from dao.solicitud_dao import SolicitudDAO
from modelo.usuario import Usuario
from correo import enviar_codigo, enviar_bienvenida
from otp import AlmacenOTP
from security.jwt_helper import generate_token, verify_token
from security.crypto import encrypt, decrypt
from security.passwords import hash_password, verificar_password, es_hash_heredado
from security.politica import validar_contrasena

app = Flask(__name__)
CORS(app, origins=[
    "http://localhost:5173",   # PetConnect.Front (React web)
    "http://localhost:8081",   # PetConnect.Mobile (Expo web)
    "http://localhost:19006",  # PetConnect.Mobile (Expo web, puerto legado)
])

# NC-006 / A-04 y A-05: limite de peticiones por IP en las rutas de autenticacion.
# Frena la fuerza bruta de contrasenas y codigos, y el envio de correos sin fin.
# Se cuenta en memoria (se reinicia al reiniciar la API), como los OTP (ver 4.6).
# La IP es request.remote_addr: si algun dia la API va detras de un proxy, hay
# que agregar ProxyFix para leer la IP real (ver 5.2).
LIMITE_AUTH = "5 per minute"
limiter = Limiter(
    get_remote_address,
    app=app,
    storage_uri="memory://",
    headers_enabled=True,   # cabecera Retry-After: cuantos segundos esperar
)

# NC-005 / A-20 (item 3.1): version de la politica de tratamiento de datos personales
# que acepta quien se registra (Ley 1581 de 2012, art. 9). La fija el servidor, no
# el cliente. Texto: Documentacion/Legal/POLITICA-TRATAMIENTO-DATOS-v1.0-BORRADOR.md.
# Si el texto cambia, se sube esta version (Decreto 1377 de 2013, art. 13).
# 1.1 (07/11/2026, item 3.6): agrega las solicitudes de adopcion y los mensajes de
# contacto (A.4, A.5 punto 7, A.11). Al subirla, toda cuenta que acepto la 1.0 debe
# autorizar otra vez al iniciar sesion (item 3.5).
VERSION_POLITICA_DATOS = "1.1"
_MENSAJE_SIN_AUTORIZACION = "Debes autorizar el tratamiento de tus datos personales para registrarte"
# Item 3.5 (A-20, R05): cuentas creadas antes del 3.1 (acepta_datos = 0) o que
# aceptaron otra version de la politica. Se les pide al iniciar sesion.
_MENSAJE_LOGIN_SIN_AUTORIZACION = (
    "Para seguir usando tu cuenta debes autorizar el tratamiento de tus datos personales"
)

_conexion_bd = ConexionBD()
_otp_registro = AlmacenOTP()
_otp_login = AlmacenOTP()


# ---------------------------------------------------------------------------
# Manejo de errores (NC-007): codigo HTTP real y nunca detalles internos al cliente
# ---------------------------------------------------------------------------

class BDNoDisponible(Exception):
    """La base de datos no respondio: la API contesta 503."""


class EntradaInvalida(BadRequest):
    """Dato de entrada con formato incorrecto (400); su mensaje si se muestra al cliente."""


_MENSAJES_HTTP = {
    400: "La peticion no es valida",
    404: "Recurso no encontrado",
    405: "Metodo no permitido para esta ruta",
    413: "La peticion es demasiado grande",
    415: "Tipo de contenido no soportado",
    429: "Demasiadas peticiones. Espera un minuto e intenta de nuevo",
}


def _registrar_error(e) -> str:
    """
    Registra el error en la consola del servidor y devuelve un id corto para
    encontrarlo despues. Se guarda el tipo de error y la pila (archivo, linea y
    funcion), pero NO el mensaje: puede traer datos personales, como
    "Duplicate entry 'correo@...'" (Ley 1581).
    """
    id_error = secrets.token_hex(4)
    ruta = request.url_rule.rule if request.url_rule else "(sin ruta)"
    pila = "".join(traceback.format_list(traceback.extract_tb(e.__traceback__)))
    app.logger.error("Error %s en %s %s: %s\n%s", id_error, request.method, ruta, type(e).__name__, pila)
    return id_error


@app.errorhandler(HTTPException)
def manejar_error_http(e):
    """404, 405, 400...: se responde con su codigo real y un mensaje en espanol."""
    if isinstance(e, EntradaInvalida):
        mensaje = e.description
    else:
        mensaje = _MENSAJES_HTTP.get(e.code, "No se pudo procesar la peticion")
    respuesta = e.get_response()   # conserva cabeceras como Allow (405)
    respuesta.set_data(json.dumps({"error": mensaje}))
    respuesta.content_type = "application/json"
    return respuesta


@app.errorhandler(BDNoDisponible)
@app.errorhandler(InterfaceError)
@app.errorhandler(OperationalError)
def manejar_bd_no_disponible(e):
    id_error = _registrar_error(e)
    return jsonify({
        "error": "El servicio no esta disponible en este momento. Intenta de nuevo mas tarde",
        "id_error": id_error,
    }), 503


@app.errorhandler(Exception)
def manejar_error_interno(e):
    id_error = _registrar_error(e)
    return jsonify({
        "error": "Error interno del servidor. Intenta de nuevo mas tarde",
        "id_error": id_error,
    }), 500


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def _modo_debug() -> bool:
    """
    NC-007: el depurador de Werkzeug permite ejecutar codigo en el servidor.
    Solo se enciende con FLASK_DEBUG=1 (en tu computador, nunca en un servidor publico).
    """
    return os.getenv("FLASK_DEBUG", "").strip() == "1"


def _es_desarrollo() -> bool:
    """
    A-10: solo con APP_ENV=desarrollo (sin importar mayusculas ni espacios) se
    puede mostrar en la consola el codigo OTP cuando el correo falla. Vacia,
    "produccion" o cualquier otro valor = no es desarrollo (lo seguro por defecto).
    Es aparte de FLASK_DEBUG: ver los codigos no debe exigir encender el depurador.
    """
    return os.getenv("APP_ENV", "").strip().lower() == "desarrollo"


def _avisar_fallo_envio(e, codigo=None) -> bool:
    """
    Registra que un correo no se pudo enviar, con la ruta y el tipo de error,
    pero NUNCA el correo del usuario ni str(e): el mensaje de la excepcion puede
    traer la direccion (Ley 1581), como en _registrar_error.

    Si se pasa `codigo` y APP_ENV=desarrollo, imprime SOLO el codigo (sin el
    correo) para poder probar sin correo real, y devuelve True. En cualquier
    otro caso devuelve False: quien llama decide que responder al cliente.
    """
    ruta = request.url_rule.rule if request.url_rule else "(sin ruta)"
    app.logger.warning("Fallo de envio de correo en %s: %s", ruta, type(e).__name__)
    if codigo is not None and _es_desarrollo():
        print(f"[DEV] Codigo de verificacion (el correo no se envio): {codigo}")
        return True
    return False


_MENSAJE_FALLO_CORREO = "No pudimos enviar el código a tu correo. Intenta de nuevo en unos minutos"


def _verificar_bd():
    """
    Comprueba que la BD responde; si no, lanza BDNoDisponible (la API contesta 503).
    Va antes de los DAO viejos, que sin BD devuelven None y pareceria "no encontrado".
    Item 4.5 (A-11, NC-003): la conexion se pide al pool y se devuelve enseguida.
    Antes se pedia y nunca se devolvia: con el pool, eso lo habria agotado.
    """
    conexion = _conexion_bd.obtener_conexion()
    if conexion is None:
        raise BDNoDisponible()
    conexion.close()


def _cuerpo_json() -> dict:
    """Cuerpo JSON de la peticion ({} si viene vacio); si no es un objeto responde 400."""
    datos = request.get_json(silent=True)
    if datos is None:
        return {}
    if not isinstance(datos, dict):
        raise EntradaInvalida("El cuerpo de la peticion debe ser un objeto JSON")
    return datos


def _texto(datos: dict, campo: str) -> str:
    """Devuelve el campo si es texto ("" si falta); si es numero, null, lista... responde 400."""
    valor = datos.get(campo, "")
    if not isinstance(valor, str):
        raise EntradaInvalida(f"El campo '{campo}' debe ser texto")
    return valor


def _serialize(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def _row_to_dict(row):
    return {k: _serialize(v) for k, v in row.items()}


# Item 4.1 (A-17, NC-004): la politica de contrasenas vive en security/politica.py
# (la usara tambien la consola en el 4.11). Se conserva el nombre viejo porque lo
# llama Documentacion/Evidencias-GA9-AA2-EV01/pruebas_aa2.py (evidencia del AA2).
_validate_password = validar_contrasena


# A-05: un nombre son palabras de letras (con tildes y ñ) separadas por espacios.
# Dentro de una palabra se permite ' o - (O'Neil, Pérez-Gil) y al final un punto
# (Ma. José). Sin numeros, ':', '/', '<' ni un punto pegado a otra palabra, asi
# que no cabe una URL (https://..., sitio-falso.example) ni HTML.
_PALABRA_NOMBRE = r"[^\W\d_]+(?:['\-][^\W\d_]+)*\.?"
_NOMBRE_REGEX = re.compile(rf"{_PALABRA_NOMBRE}(?: +{_PALABRA_NOMBRE})*")
NOMBRE_MIN, NOMBRE_MAX = 2, 60


def _validar_nombre(nombre: str) -> str | None:
    """Mensaje de error si el nombre no parece un nombre de persona; None si es valido."""
    if not (NOMBRE_MIN <= len(nombre) <= NOMBRE_MAX) or not _NOMBRE_REGEX.fullmatch(nombre):
        return (f"El nombre debe tener entre {NOMBRE_MIN} y {NOMBRE_MAX} caracteres y solo "
                "letras, espacios, guiones, apostrofos o puntos")
    return None


_EMAIL_REGEX =re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")

# Item 4.6 (A-12): memoria de "este dominio tiene o no servidor de correo", para no
# preguntar al DNS cada vez. Antes crecia sin limite (spam con dominios inventados).
# Ahora guarda como mucho MX_CACHE_MAXIMO dominios: al llenarse olvida el que lleva
# mas tiempo sin usarse (LRU). El candado evita que dos hilos la cambien a la vez.
MX_CACHE_MAXIMO = 1000
_mx_cache: "OrderedDict[str, bool]" = OrderedDict()
_mx_cache_candado = threading.Lock()


def _mx_guardado(dominio: str) -> bool | None:
    """Respuesta guardada para `dominio` (y lo marca como recien usado), o None."""
    with _mx_cache_candado:
        if dominio not in _mx_cache:
            return None
        _mx_cache.move_to_end(dominio)
        return _mx_cache[dominio]


def _guardar_mx(dominio: str, tiene_mx: bool):
    """Guarda la respuesta del DNS; si pasa del maximo, borra la menos usada."""
    with _mx_cache_candado:
        _mx_cache[dominio] = tiene_mx
        _mx_cache.move_to_end(dominio)
        while len(_mx_cache) > MX_CACHE_MAXIMO:
            _mx_cache.popitem(last=False)


def _validar_correo(email: str) -> tuple[bool, str]:
    """
    Valida el correo en dos niveles:
      1. Formato (regex) - rapido, sin red.
      2. Dominio (registros MX) - confirma que el dominio tiene
         servidores de correo configurados (detecta typos como
         "gmial.com" o dominios inventados). No confirma que la
         casilla especifica exista: eso solo lo confirma el codigo
         de verificacion que se envia al correo.
    """
    email = (email or "").strip()

    if not email:
        return False, "El correo es requerido"
    if not _EMAIL_REGEX.match(email):
        return False, "El formato del correo no es valido"

    dominio = email.rsplit("@", 1)[-1].lower()

    tiene_mx = _mx_guardado(dominio)
    if tiene_mx is None:
        try:
            respuestas = dns.resolver.resolve(dominio, "MX", lifetime=4)
            tiene_mx = len(respuestas) > 0
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
            tiene_mx = False
        except Exception:
            # Fallo de red/DNS temporal: no bloqueamos el registro por esto.
            return True, "No se pudo verificar el dominio en este momento, pero el formato es valido"
        _guardar_mx(dominio, tiene_mx)

    if not tiene_mx:
        return False, f'El dominio "{dominio}" no tiene servidores de correo configurados'

    return True, "El correo y el dominio son validos"


# ---------------------------------------------------------------------------
# Decorador de autenticacion JWT
# ---------------------------------------------------------------------------

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        token = auth_header.replace("Bearer ", "").strip()
        if not token:
            return jsonify({"error": "Autenticacion requerida"}), 401
        payload = verify_token(token)
        try:
            # "sub" viaja como texto (RFC 7519); el resto de la API usa el id entero
            user_id = int(payload["sub"]) if payload else None
        except (KeyError, TypeError, ValueError):
            user_id = None
        if user_id is None:
            return jsonify({"error": "Token invalido o sesion expirada. Inicia sesion de nuevo"}), 401
        request.current_user_id = user_id
        request.current_user_email = payload["email"]
        return f(*args, **kwargs)
    return decorated


# ---------------------------------------------------------------------------
# Productos  (publico - catalogo)
# ---------------------------------------------------------------------------
# Las rutas no atrapan los errores de la BD: los responden los manejadores
# globales (503 si la BD no responde, 500 generico en otro caso).

_SQL_PRODUCTOS = """
    SELECT p.id_producto AS id, p.nombre AS name, p.descripcion AS description,
           p.precio AS price, p.stock, p.imagen_url AS image, p.activo,
           COALESCE(c.nombre, CONCAT('Categoria ', p.id_categoria_producto)) AS category
    FROM productos p
    LEFT JOIN categorias_producto c ON p.id_categoria_producto = c.id_categoria_producto
    WHERE p.activo = TRUE ORDER BY p.id_producto
"""

_SQL_PRODUCTO_BY_ID = """
    SELECT p.id_producto AS id, p.nombre AS name, p.descripcion AS description,
           p.precio AS price, p.stock, p.imagen_url AS image, p.activo,
           COALESCE(c.nombre, CONCAT('Categoria ', p.id_categoria_producto)) AS category
    FROM productos p
    LEFT JOIN categorias_producto c ON p.id_categoria_producto = c.id_categoria_producto
    WHERE p.id_producto = %s
"""


@app.route("/api/productos", methods=["GET"])
def get_productos():
    with conexion_y_cursor(_conexion_bd, dictionary=True) as (_, cursor):
        cursor.execute(_SQL_PRODUCTOS)
        rows = cursor.fetchall()
    return jsonify([_row_to_dict(r) for r in rows])


@app.route("/api/productos/<int:id_producto>", methods=["GET"])
def get_producto(id_producto):
    with conexion_y_cursor(_conexion_bd, dictionary=True) as (_, cursor):
        cursor.execute(_SQL_PRODUCTO_BY_ID, (id_producto,))
        row = cursor.fetchone()
    if row is None:
        return jsonify({"error": "Producto no encontrado"}), 404
    return jsonify(_row_to_dict(row))


# ---------------------------------------------------------------------------
# Mascotas  (publico - catalogo)
# ---------------------------------------------------------------------------

_SQL_MASCOTAS_ADOPCION = """
    SELECT id_mascota AS id, nombre AS name, especie AS species, raza AS breed,
           sexo AS gender, edad_aprox AS age, foto AS image,
           observaciones AS description, estado
    FROM mascotas WHERE estado = 'en_adopcion' ORDER BY id_mascota
"""

# NC-002 (item 2.9): la ruta publica solo encuentra mascotas en adopcion. Las demas
# (activas, perdidas, adoptadas...) son privadas de su dueno.
_SQL_MASCOTA_ADOPCION_BY_ID = """
    SELECT id_mascota AS id, nombre AS name, especie AS species, raza AS breed,
           sexo AS gender, edad_aprox AS age, foto AS image,
           observaciones AS description, estado
    FROM mascotas WHERE id_mascota = %s AND estado = 'en_adopcion'
"""

# Mascota de un usuario: solo la encuentra su dueno (id_usuario del token)
_SQL_MASCOTA_DEL_USUARIO = """
    SELECT id_mascota AS id, nombre AS name, especie AS species, raza AS breed,
           sexo AS gender, edad_aprox AS age, foto AS image,
           observaciones AS description, estado, id_usuario
    FROM mascotas WHERE id_mascota = %s AND id_usuario = %s
"""

# Mismo mensaje si no existe, si no esta en adopcion o si es de otro usuario:
# asi la respuesta no revela que la mascota existe (NC-002)
_MENSAJE_MASCOTA_NO_ENCONTRADA = "Mascota no encontrada"


def _mascota_to_dict(row):
    # A-22 (item 3.4): solo se devuelven los datos que estan en la BD. Antes se
    # agregaban vaccinated=False, sterilized=False y size="Mediano" a todas las
    # mascotas (la tabla no tiene esas columnas) y la ficha decia "Pendiente de
    # vacunacion" a mascotas cuya descripcion las da por vacunadas. Un dato de
    # salud animal no se inventa: si no esta registrado, no se muestra.
    return _row_to_dict(row)


@app.route("/api/mascotas/adopcion", methods=["GET"])
def get_mascotas_adopcion():
    with conexion_y_cursor(_conexion_bd, dictionary=True) as (_, cursor):
        cursor.execute(_SQL_MASCOTAS_ADOPCION)
        rows = cursor.fetchall()
    return jsonify([_mascota_to_dict(r) for r in rows])


def _consultar_mascota(sql, params):
    """Devuelve la fila de la mascota (o None) con la consulta parametrizada dada."""
    with conexion_y_cursor(_conexion_bd, dictionary=True) as (_, cursor):
        cursor.execute(sql, params)
        row = cursor.fetchone()
    return row


def _mascota_no_encontrada():
    return jsonify({"error": _MENSAJE_MASCOTA_NO_ENCONTRADA}), 404


@app.route("/api/mascotas/<int:id_mascota>", methods=["GET"])
def get_mascota(id_mascota):
    row = _consultar_mascota(_SQL_MASCOTA_ADOPCION_BY_ID, (id_mascota,))
    # Doble barrera: el SQL ya filtra por estado y aqui se vuelve a revisar, por si
    # alguien cambia la consulta. Cualquier otro estado responde como si no existiera.
    if row is None or row.get("estado") != "en_adopcion":
        return _mascota_no_encontrada()
    return jsonify(_mascota_to_dict(row))


# ---------------------------------------------------------------------------
# Mascotas del usuario  (privado - solo el dueno)
# ---------------------------------------------------------------------------

@app.route("/api/usuarios/me/mascotas/<int:id_mascota>", methods=["GET"])
@require_auth
def get_mi_mascota(id_mascota):
    row = _consultar_mascota(_SQL_MASCOTA_DEL_USUARIO, (id_mascota, request.current_user_id))
    # Doble barrera: el SQL filtra por dueno y aqui se compara otra vez. Una mascota
    # ajena responde 404, igual que una inexistente (no 403: no se revela que existe).
    if row is None or row.pop("id_usuario", None) != request.current_user_id:
        return _mascota_no_encontrada()
    return jsonify(_mascota_to_dict(row))


# ---------------------------------------------------------------------------
# Utilidades publicas
# ---------------------------------------------------------------------------

@app.route("/api/utils/validar-correo", methods=["POST"])
@limiter.limit(LIMITE_AUTH)
def validar_correo():
    """
    Valida formato + dominio (registros MX) de un correo, sin crear nada.
    Pensado para llamarse en vivo mientras el usuario escribe en el
    formulario de registro (con debounce en el frontend).
    """
    email = _texto(_cuerpo_json(), "email")

    valido, mensaje = _validar_correo(email)
    return jsonify({"valido": valido, "mensaje": mensaje})


# ---------------------------------------------------------------------------
# Autenticacion
# ---------------------------------------------------------------------------

def _autorizacion_vigente(usuario) -> bool:
    """
    Item 3.5 (A-20, R05): la cuenta autorizo el tratamiento de sus datos con la
    version actual de la politica. Una cuenta en 0 (creada antes del 3.1) o que
    acepto otra version debe autorizar otra vez (Decreto 1377, art. 13).
    """
    return usuario.acepta_datos is True and usuario.version_politica_datos == VERSION_POLITICA_DATOS


def _pedir_autorizacion():
    """403 que el cliente reconoce por "requiere_autorizacion" para mostrar la casilla."""
    return jsonify({"error": _MENSAJE_LOGIN_SIN_AUTORIZACION, "requiere_autorizacion": True}), 403


@app.route("/api/auth/login", methods=["POST"])
@limiter.limit(LIMITE_AUTH)
def login():
    data = _cuerpo_json()
    email = _texto(data, "email").strip()
    password = _texto(data, "password")

    if not email or not password:
        return jsonify({"error": "Correo y contrasena son requeridos"}), 400

    # Sin BD el DAO devuelve None y pareceria "credenciales incorrectas": mejor 503
    _verificar_bd()
    dao = UsuarioDAO()
    usuario = dao.consultar_por_correo(email)

    if usuario is None or not verificar_password(password, usuario.password_hash):
        return jsonify({"error": "Correo o contrasena incorrectos"}), 401

    # NC-001: los hashes SHA-256 del sistema anterior se reemplazan por bcrypt
    # en el primer inicio de sesion exitoso, cuando se conoce la contrasena.
    if es_hash_heredado(usuario.password_hash):
        dao.actualizar_password(usuario.id_usuario, hash_password(password))

    if usuario.estado != "activo":
        return jsonify({"error": "Cuenta inactiva o bloqueada"}), 403

    # Item 3.5 (A-20, R05): va DESPUES de la contrasena (el 403 no revela que la
    # cuenta existe) y ANTES del correo. Sin autorizacion vigente no se manda el
    # codigo hasta que la persona marque la casilla: solo vale el booleano JSON
    # true, como en /register. Nunca se marca la cuenta como autorizada aqui: la
    # prueba (fecha y version) viaja en el pendiente y /login/verify la escribe solo
    # con el codigo correcto. Si la cuenta ya autorizo, "acepta_datos" se ignora y
    # su fecha original no se toca.
    pendiente = {"id_usuario": usuario.id_usuario}
    if not _autorizacion_vigente(usuario):
        if data.get("acepta_datos") is not True:
            return _pedir_autorizacion()
        pendiente["fecha_autorizacion_datos"] = datetime.now().replace(microsecond=0)
        pendiente["version_politica_datos"] = VERSION_POLITICA_DATOS

    # Segundo factor: se manda un codigo de un solo uso al correo antes de
    # entregar el token. La sesion solo se completa en /api/auth/login/verify.
    code = _otp_login.crear(email, pendiente)

    try:
        enviar_codigo(
            email, usuario.nombres, code,
            asunto="PetConnect - Codigo de inicio de sesion",
            proposito="Usa este codigo para confirmar que eres tu e iniciar sesion:",
        )
    except Exception as e:
        # A-10: fuera de desarrollo no se muestra el codigo; se borra para que
        # no quede un codigo valido que nadie recibio, y se pide reintentar.
        if not _avisar_fallo_envio(e, code):
            _otp_login.descartar(email)
            return jsonify({"error": _MENSAJE_FALLO_CORREO}), 503

    return jsonify({"message": "Codigo enviado", "email": email})


@app.route("/api/auth/login/verify", methods=["POST"])
@limiter.limit(LIMITE_AUTH)
def login_verify():
    data  = _cuerpo_json()
    email = _texto(data, "email").strip()
    code  = _texto(data, "code").strip()

    pending, error = _otp_login.verificar(email, code)
    if error == "no_pendiente":
        return jsonify({"error": "No hay inicio de sesion pendiente para este correo"}), 400
    if error == "expirado":
        return jsonify({"error": "El codigo expiro. Vuelve a iniciar sesion"}), 400
    if error == "bloqueado":   # 5 fallos: el codigo se borro (A-04, NC-006)
        return jsonify({"error": "Demasiados intentos fallidos. Vuelve a iniciar sesion para recibir otro codigo"}), 429
    if error == "incorrecto":
        return jsonify({"error": "Codigo incorrecto"}), 400

    _verificar_bd()   # 503 antes de gastar el codigo si la BD no responde
    _otp_login.descartar(email)

    dao = UsuarioDAO()
    usuario = dao.consultar_por_correo(email)
    if usuario is None:
        return jsonify({"error": "Usuario no encontrado"}), 404

    # Item 3.5 (A-20, R05), doble barrera: sin autorizacion vigente no hay token.
    # La prueba solo vale si es de la version actual (pudo cambiar en estos 10
    # minutos) y si es del mismo usuario que pidio el codigo.
    if not _autorizacion_vigente(usuario):
        fecha = pending.get("fecha_autorizacion_datos")
        version = pending.get("version_politica_datos")
        if (fecha is None or version != VERSION_POLITICA_DATOS
                or pending.get("id_usuario") != usuario.id_usuario):
            return _pedir_autorizacion()
        if not dao.registrar_autorizacion(usuario.id_usuario, fecha, version):
            return jsonify({"error": "No pudimos guardar tu autorizacion. Intenta de nuevo"}), 500

    token = generate_token(usuario.id_usuario, usuario.correo)
    return jsonify({
        "token": token,
        "id":    usuario.id_usuario,
        "name":  f"{usuario.nombres} {usuario.apellidos}".strip(),
        "email": usuario.correo,
    })


@app.route("/api/auth/register", methods=["POST"])
@limiter.limit(LIMITE_AUTH)
def register():
    data = _cuerpo_json()
    name     = _texto(data, "name").strip()
    email    = _texto(data, "email").strip()
    password = _texto(data, "password")

    if not name or not email or not password:
        return jsonify({"error": "Nombre, correo y contrasena son requeridos"}), 400

    # NC-005 (item 3.1): autorizacion previa y expresa (Ley 1581, art. 9). Solo vale
    # el booleano JSON true: "true", 1, "si", null o la ausencia del campo no son
    # una conducta inequivoca. Va antes del DNS, de la BD y del correo.
    if data.get("acepta_datos") is not True:
        return jsonify({"error": _MENSAJE_SIN_AUTORIZACION}), 400

    # Antes del DNS y de la BD: el nombre viaja en el correo que se envia (A-05)
    error_nombre = _validar_nombre(name)
    if error_nombre:
        return jsonify({"error": error_nombre}), 400

    correo_valido, mensaje_correo = _validar_correo(email)
    if not correo_valido:
        return jsonify({"error": mensaje_correo}), 400

    error_pw = validar_contrasena(password)
    if error_pw:
        return jsonify({"error": error_pw}), 400

    _verificar_bd()
    dao = UsuarioDAO()
    if dao.consultar_por_correo(email) is not None:
        return jsonify({"error": "El correo ya esta registrado"}), 409

    # A-09 (item 2.7): si ya hay un registro pendiente y vigente para este correo,
    # NO se toca (ni nombre, ni hash, ni codigo, ni intentos, ni vencimiento) y no
    # se envia nada: vale la primera contrasena. Se responde igual que siempre para
    # no revelar que alguien se esta registrando (A-14). Para recibir otra vez el
    # codigo esta /api/auth/register/resend.
    if _otp_registro.vigente(email) is not None:
        return jsonify({"message": "Codigo enviado", "email": email})

    # Prueba de la autorizacion (Decreto 1377, art. 8): la hora en que la persona la
    # dio y la version que acepto. /verify las escribe al crear el usuario.
    code = _otp_registro.crear(email, {
        "name":          name,
        "password_hash": hash_password(password),
        "fecha_autorizacion_datos": datetime.now().replace(microsecond=0),
        "version_politica_datos":   VERSION_POLITICA_DATOS,
    })

    try:
        enviar_codigo(
            email, name.split()[0], code,
            asunto="PetConnect - Codigo de verificacion",
            proposito="Usa este codigo para verificar tu correo y completar tu registro:",
        )
    except Exception as e:
        # A-10: solo con APP_ENV=desarrollo se imprime el codigo (nunca el correo).
        # Fuera de desarrollo se borra el registro pendiente y se pide reintentar.
        # No revela cuentas: el 409 de arriba ya se respondio antes (A-14).
        if not _avisar_fallo_envio(e, code):
            _otp_registro.descartar(email)
            return jsonify({"error": _MENSAJE_FALLO_CORREO}), 503

    return jsonify({"message": "Codigo enviado", "email": email})


_MENSAJE_REENVIO = "Si hay un registro pendiente para este correo, te reenviamos el codigo"


@app.route("/api/auth/register/resend", methods=["POST"])
@limiter.limit(LIMITE_AUTH)
def register_resend():
    """
    A-09 (item 2.7): reenvia EL MISMO codigo de un registro pendiente, con el nombre
    del primer registro y sin reiniciar el contador de intentos ni alargar el
    vencimiento. Las reglas (60 s entre correos, maximo 3 reenvios, no reenviar un
    codigo bloqueado) estan en AlmacenOTP.para_reenviar(). Haya o no pendiente, la
    respuesta es la misma (A-14). No consulta la BD ni el DNS.
    """
    email = _texto(_cuerpo_json(), "email").strip()
    if not email:
        return jsonify({"error": "El correo es requerido"}), 400

    pendiente = _otp_registro.para_reenviar(email)
    if pendiente is not None:
        try:
            enviar_codigo(
                email, pendiente["name"].split()[0], pendiente["code"],
                asunto="PetConnect - Codigo de verificacion",
                proposito="Usa este codigo para verificar tu correo y completar tu registro:",
            )
        except Exception as e:
            # A-10: nunca el correo ni str(e) en los logs; en desarrollo, solo el codigo.
            # El pendiente NO se borra: el primer correo pudo llegar y sigue sirviendo.
            if not _avisar_fallo_envio(e, pendiente["code"]):
                return jsonify({"error": _MENSAJE_FALLO_CORREO}), 503

    return jsonify({"message": _MENSAJE_REENVIO})


@app.route("/api/auth/verify", methods=["POST"])
@limiter.limit(LIMITE_AUTH)
def verify():
    data  = _cuerpo_json()
    email = _texto(data, "email").strip()
    code  = _texto(data, "code").strip()

    pending, error = _otp_registro.verificar(email, code)
    if error == "no_pendiente":
        return jsonify({"error": "No hay verificacion pendiente para este correo"}), 400
    if error == "expirado":
        return jsonify({"error": "El codigo expiro. Vuelve a registrarte"}), 400
    if error == "bloqueado":   # 5 fallos: el codigo se borro (A-04, NC-006)
        return jsonify({"error": "Demasiados intentos fallidos. Vuelve a registrarte para recibir otro codigo"}), 429
    if error == "incorrecto":
        return jsonify({"error": "Codigo incorrecto"}), 400

    # NC-005 (item 3.1), doble barrera: sin la prueba de la autorizacion guardada en
    # /register no se crea la cuenta (nunca un acepta_datos=True sin fecha ni version)
    fecha_autorizacion = pending.get("fecha_autorizacion_datos")
    version_politica = pending.get("version_politica_datos")
    if fecha_autorizacion is None or not version_politica:
        _otp_registro.descartar(email)
        return jsonify({"error": _MENSAJE_SIN_AUTORIZACION}), 400

    parts    = pending["name"].split(" ", 1)
    nombres  = parts[0]
    apellidos = parts[1] if len(parts) > 1 else ""

    # El telefono y datos sensibles adicionales se guardan cifrados con Fernet
    # encrypt(telefono) antes de insertar; decrypt(telefono) al leer
    usuario = Usuario(
        nombres=nombres,
        apellidos=apellidos,
        correo=email,
        password_hash=pending["password_hash"],
        estado="activo",
        verificado=True,
        acepta_datos=True,
        fecha_autorizacion_datos=fecha_autorizacion,
        version_politica_datos=version_politica,
    )

    _verificar_bd()
    dao = UsuarioDAO()
    if not dao.insertar(usuario):
        return jsonify({"error": "Error al crear el usuario"}), 500

    _otp_registro.descartar(email)

    try:
        enviar_bienvenida(email, nombres)
    except Exception as e:
        # La cuenta ya se creo: la respuesta sigue siendo 201, solo se registra el fallo
        _avisar_fallo_envio(e)

    token = generate_token(usuario.id_usuario, email)
    return jsonify({
        "token": token,
        "id":    usuario.id_usuario,
        "name":  f"{nombres} {apellidos}".strip(),
        "email": email,
    }), 201


# ---------------------------------------------------------------------------
# Solicitudes de adopcion y mensajes de contacto  (privado - con sesion)
# ---------------------------------------------------------------------------
# Item 3.6 (A-21): antes la web mostraba "Solicitud enviada" sin enviar nada.
# Ahora se guardan en la tabla solicitudes y el equipo las lee en la BD. Decisiones
# del dueno (07/11/2026): solo con sesion (nombre y correo salen de la cuenta), sin
# casilla aparte (vale la autorizacion de la cuenta con la politica vigente, que
# desde la 1.1 nombra esta finalidad) y telefono opcional solo en adopcion.
# Nunca se registra en los logs el mensaje ni el telefono (Ley 1581).

MENSAJE_MIN, MENSAJE_MAX = 10, 1000
TELEFONO_MAX = 20                       # como usuarios.telefono y solicitudes.telefono
TELEFONO_DIGITOS_MIN, TELEFONO_DIGITOS_MAX = 7, 15   # 15: maximo internacional (E.164)
_TELEFONO_REGEX = re.compile(r"\+?[0-9 ]+")

_MENSAJE_SOLICITUD_SIN_AUTORIZACION = (
    "Para enviar tu solicitud debes autorizar la versión vigente de la política de datos. "
    "Cierra sesión y vuelve a iniciarla"
)


def _validar_mensaje(mensaje: str) -> str | None:
    if not (MENSAJE_MIN <= len(mensaje) <= MENSAJE_MAX):
        return f"El mensaje debe tener entre {MENSAJE_MIN} y {MENSAJE_MAX} caracteres"
    return None


def _validar_telefono(telefono: str) -> str | None:
    """Vacio = no lo dio (es opcional). Solo numeros, espacios y un + al inicio."""
    if telefono == "":
        return None
    digitos = sum(c.isdigit() for c in telefono)
    if (len(telefono) > TELEFONO_MAX or not _TELEFONO_REGEX.fullmatch(telefono)
            or not (TELEFONO_DIGITOS_MIN <= digitos <= TELEFONO_DIGITOS_MAX)):
        return (f"El teléfono solo puede tener números, espacios y un + al inicio "
                f"(entre {TELEFONO_DIGITOS_MIN} y {TELEFONO_DIGITOS_MAX} dígitos)")
    return None


def _cuenta_que_envia():
    """
    Usuario del token, revisado en la BD: el token pudo emitirse antes de que la
    cuenta se bloqueara o de que subiera la version de la politica (vale 24 h).
    Devuelve (usuario, None) o (None, respuesta de error).
    """
    _verificar_bd()
    usuario = UsuarioDAO().consultar_por_id(request.current_user_id)
    if usuario is None:
        return None, (jsonify({"error": "Usuario no encontrado"}), 404)
    if usuario.estado != "activo":
        return None, (jsonify({"error": "Cuenta inactiva o bloqueada"}), 403)
    if not _autorizacion_vigente(usuario):
        return None, (jsonify({"error": _MENSAJE_SOLICITUD_SIN_AUTORIZACION,
                               "requiere_autorizacion": True}), 403)
    return usuario, None


def _guardar_solicitud(usuario, tipo, id_mascota, telefono, mensaje):
    """Guarda la fila con la version de la politica que la cuenta acepto y devuelve su id."""
    return SolicitudDAO().insertar(
        usuario.id_usuario, tipo, id_mascota, telefono or None, mensaje,
        usuario.version_politica_datos, datetime.now().replace(microsecond=0),
    )


@app.route("/api/solicitudes/adopcion", methods=["POST"])
@limiter.limit(LIMITE_AUTH)
@require_auth
def enviar_solicitud_adopcion():
    data = _cuerpo_json()
    id_mascota = data.get("id_mascota")
    # bool es un int en Python: True no puede pasar por la mascota 1
    if not isinstance(id_mascota, int) or isinstance(id_mascota, bool) or id_mascota < 1:
        return jsonify({"error": "Falta la mascota que quieres adoptar"}), 400
    mensaje = _texto(data, "mensaje").strip()
    telefono = _texto(data, "telefono").strip()
    error = _validar_mensaje(mensaje) or _validar_telefono(telefono)
    if error:
        return jsonify({"error": error}), 400

    usuario, respuesta = _cuenta_que_envia()
    if respuesta:
        return respuesta

    dueno = SolicitudDAO().dueno_de_mascota_en_adopcion(id_mascota)
    if dueno is None:
        return _mascota_no_encontrada()
    if dueno == usuario.id_usuario:
        return jsonify({"error": "No puedes solicitar la adopción de tu propia mascota"}), 400

    id_solicitud = _guardar_solicitud(usuario, "adopcion", id_mascota, telefono, mensaje)
    return jsonify({"message": "Solicitud enviada", "id": id_solicitud}), 201


@app.route("/api/solicitudes/contacto", methods=["POST"])
@limiter.limit(LIMITE_AUTH)
@require_auth
def enviar_mensaje_contacto():
    data = _cuerpo_json()
    mensaje = _texto(data, "mensaje").strip()
    error = _validar_mensaje(mensaje)
    if error:
        return jsonify({"error": error}), 400

    usuario, respuesta = _cuenta_que_envia()
    if respuesta:
        return respuesta

    # Contacto no lleva mascota ni telefono (regla chk_solicitud_tipo): se ignoran
    id_solicitud = _guardar_solicitud(usuario, "contacto", None, "", mensaje)
    return jsonify({"message": "Mensaje enviado", "id": id_solicitud}), 201


@app.route("/api/auth/me", methods=["GET"])
@require_auth
def me():
    """Endpoint protegido - valida que el token JWT es valido."""
    _verificar_bd()
    dao = UsuarioDAO()
    usuario = dao.consultar_por_id(request.current_user_id)
    if not usuario:
        return jsonify({"error": "Usuario no encontrado"}), 404
    return jsonify({
        "id":    usuario.id_usuario,
        "name":  f"{usuario.nombres} {usuario.apellidos}".strip(),
        "email": usuario.correo,
    })


# ---------------------------------------------------------------------------
# Inicio
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    try:
        _verificar_bd()
    except BDNoDisponible:
        print("[ERROR] No se pudo conectar a la base de datos.")
        sys.exit(1)
    print("[OK] Conexion a la base de datos establecida.")
    modo_debug = _modo_debug()
    if modo_debug:
        print("[AVISO] Modo debug activo (FLASK_DEBUG=1): usalo solo en tu computador.")
    if _es_desarrollo():
        print("[AVISO] APP_ENV=desarrollo: si el correo falla, el codigo OTP se muestra en esta consola. "
              "Usalo solo en tu computador.")
    print("[OK] API PetConnect corriendo en http://localhost:5000")
    app.run(debug=modo_debug, port=5000)
