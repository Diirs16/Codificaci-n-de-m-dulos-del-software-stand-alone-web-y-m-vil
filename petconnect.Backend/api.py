"""
API REST de PetConnect.
Ejecutar con: python api.py
"""

import sys
import os
import re
import json
import secrets
import traceback
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

from conexion.conexion_bd import ConexionBD
from dao.usuario_dao import UsuarioDAO
from modelo.usuario import Usuario
from correo import enviar_codigo, enviar_bienvenida
from otp import AlmacenOTP
from security.jwt_helper import generate_token, verify_token
from security.crypto import encrypt, decrypt
from security.passwords import hash_password, verificar_password, es_hash_heredado, MAX_BYTES_BCRYPT

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


def _get_conn():
    """Conexion a la BD; si no responde lanza BDNoDisponible (la API contesta 503)."""
    conn = _conexion_bd.obtener_conexion()
    if conn is None:
        raise BDNoDisponible()
    return conn


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


def _validate_password(password: str) -> str | None:
    if len(password) < 8:
        return "La contrasena debe tener al menos 8 caracteres"
    if len(password) > 64 or len(password.encode("utf-8")) > MAX_BYTES_BCRYPT:
        return "La contrasena debe tener maximo 64 caracteres"
    if not re.search(r'[A-Z]', password):
        return "La contrasena debe tener al menos una mayuscula"
    if not re.search(r'[0-9]', password):
        return "La contrasena debe tener al menos un numero"
    if not re.search(r'[@#!"$&?¡\-_*.]', password):
        return 'La contrasena debe tener al menos un caracter especial: @ # ! " $ & ? ¡'
    return None


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
_mx_cache: dict[str, bool] = {}


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

    if dominio in _mx_cache:
        tiene_mx = _mx_cache[dominio]
    else:
        try:
            respuestas = dns.resolver.resolve(dominio, "MX", lifetime=4)
            tiene_mx = len(respuestas) > 0
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
            tiene_mx = False
        except Exception:
            # Fallo de red/DNS temporal: no bloqueamos el registro por esto.
            return True, "No se pudo verificar el dominio en este momento, pero el formato es valido"
        _mx_cache[dominio] = tiene_mx

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
    cursor = _get_conn().cursor(dictionary=True)
    cursor.execute(_SQL_PRODUCTOS)
    rows = cursor.fetchall()
    cursor.close()
    return jsonify([_row_to_dict(r) for r in rows])


@app.route("/api/productos/<int:id_producto>", methods=["GET"])
def get_producto(id_producto):
    cursor = _get_conn().cursor(dictionary=True)
    cursor.execute(_SQL_PRODUCTO_BY_ID, (id_producto,))
    row = cursor.fetchone()
    cursor.close()
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
    m = _row_to_dict(row)
    m.setdefault("vaccinated", False)
    m.setdefault("sterilized", False)
    m.setdefault("size", "Mediano")
    return m


@app.route("/api/mascotas/adopcion", methods=["GET"])
def get_mascotas_adopcion():
    cursor = _get_conn().cursor(dictionary=True)
    cursor.execute(_SQL_MASCOTAS_ADOPCION)
    rows = cursor.fetchall()
    cursor.close()
    return jsonify([_mascota_to_dict(r) for r in rows])


def _consultar_mascota(sql, params):
    """Devuelve la fila de la mascota (o None) con la consulta parametrizada dada."""
    cursor = _get_conn().cursor(dictionary=True)
    cursor.execute(sql, params)
    row = cursor.fetchone()
    cursor.close()
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

@app.route("/api/auth/login", methods=["POST"])
@limiter.limit(LIMITE_AUTH)
def login():
    data = _cuerpo_json()
    email = _texto(data, "email").strip()
    password = _texto(data, "password")

    if not email or not password:
        return jsonify({"error": "Correo y contrasena son requeridos"}), 400

    # Sin BD el DAO devuelve None y pareceria "credenciales incorrectas": mejor 503
    _get_conn()
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

    # Segundo factor: se manda un codigo de un solo uso al correo antes de
    # entregar el token. La sesion solo se completa en /api/auth/login/verify.
    code = _otp_login.crear(email, {"id_usuario": usuario.id_usuario})

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

    _get_conn()   # 503 antes de gastar el codigo si la BD no responde
    _otp_login.descartar(email)

    dao = UsuarioDAO()
    usuario = dao.consultar_por_correo(email)
    if usuario is None:
        return jsonify({"error": "Usuario no encontrado"}), 404

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

    # Antes del DNS y de la BD: el nombre viaja en el correo que se envia (A-05)
    error_nombre = _validar_nombre(name)
    if error_nombre:
        return jsonify({"error": error_nombre}), 400

    correo_valido, mensaje_correo = _validar_correo(email)
    if not correo_valido:
        return jsonify({"error": mensaje_correo}), 400

    error_pw = _validate_password(password)
    if error_pw:
        return jsonify({"error": error_pw}), 400

    _get_conn()
    dao = UsuarioDAO()
    if dao.consultar_por_correo(email) is not None:
        return jsonify({"error": "El correo ya esta registrado"}), 409

    code = _otp_registro.crear(email, {
        "name":          name,
        "password_hash": hash_password(password),
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
    )

    _get_conn()
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


@app.route("/api/auth/me", methods=["GET"])
@require_auth
def me():
    """Endpoint protegido - valida que el token JWT es valido."""
    _get_conn()
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
        _get_conn()
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
