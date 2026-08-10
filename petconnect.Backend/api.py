"""
API REST de PetConnect.
Ejecutar con: python api.py
"""

import sys
import os
import hashlib
import re
from datetime import datetime, date
from functools import wraps

# Cargar .env antes que cualquier import de config
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import dns.resolver
from flask import Flask, jsonify, request
from flask_cors import CORS
from mysql.connector import Error

from conexion.conexion_bd import ConexionBD
from dao.usuario_dao import UsuarioDAO
from modelo.usuario import Usuario
from correo import enviar_codigo, enviar_bienvenida
from otp import AlmacenOTP
from security.jwt_helper import generate_token, verify_token
from security.crypto import encrypt, decrypt

app = Flask(__name__)
CORS(app, origins=[
    "http://localhost:5173",   # PetConnect.Front (React web)
    "http://localhost:8081",   # PetConnect.Mobile (Expo web)
    "http://localhost:19006",  # PetConnect.Mobile (Expo web, puerto legado)
])

@app.errorhandler(Exception)
def handle_exception(e):
    return jsonify({"error": str(e)}), 500

_conexion_bd = ConexionBD()
_otp_registro = AlmacenOTP()
_otp_login = AlmacenOTP()


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def _get_conn():
    return _conexion_bd.obtener_conexion()


def _serialize(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def _row_to_dict(row):
    return {k: _serialize(v) for k, v in row.items()}


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _validate_password(password: str) -> str | None:
    if len(password) < 8:
        return "La contrasena debe tener al menos 8 caracteres"
    if not re.search(r'[A-Z]', password):
        return "La contrasena debe tener al menos una mayuscula"
    if not re.search(r'[0-9]', password):
        return "La contrasena debe tener al menos un numero"
    if not re.search(r'[@#!"$&?¡\-_*.]', password):
        return 'La contrasena debe tener al menos un caracter especial: @ # ! " $ & ? ¡'
    return None


_EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")
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
        if not payload:
            return jsonify({"error": "Token invalido o sesion expirada. Inicia sesion de nuevo"}), 401
        request.current_user_id = payload["sub"]
        request.current_user_email = payload["email"]
        return f(*args, **kwargs)
    return decorated


# ---------------------------------------------------------------------------
# Productos  (publico - catalogo)
# ---------------------------------------------------------------------------

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
    try:
        cursor = _get_conn().cursor(dictionary=True)
        cursor.execute(_SQL_PRODUCTOS)
        rows = cursor.fetchall()
        cursor.close()
        return jsonify([_row_to_dict(r) for r in rows])
    except Error as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/productos/<int:id_producto>", methods=["GET"])
def get_producto(id_producto):
    try:
        cursor = _get_conn().cursor(dictionary=True)
        cursor.execute(_SQL_PRODUCTO_BY_ID, (id_producto,))
        row = cursor.fetchone()
        cursor.close()
        if row is None:
            return jsonify({"error": "Producto no encontrado"}), 404
        return jsonify(_row_to_dict(row))
    except Error as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------
# Mascotas  (publico - catalogo)
# ---------------------------------------------------------------------------

_SQL_MASCOTAS_ADOPCION = """
    SELECT id_mascota AS id, nombre AS name, especie AS species, raza AS breed,
           sexo AS gender, edad_aprox AS age, foto AS image,
           observaciones AS description, estado
    FROM mascotas WHERE estado = 'en_adopcion' ORDER BY id_mascota
"""

_SQL_MASCOTA_BY_ID = """
    SELECT id_mascota AS id, nombre AS name, especie AS species, raza AS breed,
           sexo AS gender, edad_aprox AS age, foto AS image,
           observaciones AS description, estado
    FROM mascotas WHERE id_mascota = %s
"""


def _mascota_to_dict(row):
    m = _row_to_dict(row)
    m.setdefault("vaccinated", False)
    m.setdefault("sterilized", False)
    m.setdefault("size", "Mediano")
    return m


@app.route("/api/mascotas/adopcion", methods=["GET"])
def get_mascotas_adopcion():
    try:
        cursor = _get_conn().cursor(dictionary=True)
        cursor.execute(_SQL_MASCOTAS_ADOPCION)
        rows = cursor.fetchall()
        cursor.close()
        return jsonify([_mascota_to_dict(r) for r in rows])
    except Error as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/mascotas/<int:id_mascota>", methods=["GET"])
def get_mascota(id_mascota):
    try:
        cursor = _get_conn().cursor(dictionary=True)
        cursor.execute(_SQL_MASCOTA_BY_ID, (id_mascota,))
        row = cursor.fetchone()
        cursor.close()
        if row is None:
            return jsonify({"error": "Mascota no encontrada"}), 404
        return jsonify(_mascota_to_dict(row))
    except Error as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------
# Utilidades publicas
# ---------------------------------------------------------------------------

@app.route("/api/utils/validar-correo", methods=["POST"])
def validar_correo():
    """
    Valida formato + dominio (registros MX) de un correo, sin crear nada.
    Pensado para llamarse en vivo mientras el usuario escribe en el
    formulario de registro (con debounce en el frontend).
    """
    data = request.get_json(silent=True) or {}
    email = data.get("email", "")

    valido, mensaje = _validar_correo(email)
    return jsonify({"valido": valido, "mensaje": mensaje})


# ---------------------------------------------------------------------------
# Autenticacion
# ---------------------------------------------------------------------------

@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "Correo y contrasena son requeridos"}), 400

    dao = UsuarioDAO()
    usuario = dao.consultar_por_correo(email)

    if usuario is None or usuario.password_hash != _hash_password(password):
        return jsonify({"error": "Correo o contrasena incorrectos"}), 401

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
        print(f"[DEV] No se pudo enviar el correo ({e}). Codigo de inicio de sesion para {email}: {code}")

    return jsonify({"message": "Codigo enviado", "email": email})


@app.route("/api/auth/login/verify", methods=["POST"])
def login_verify():
    data  = request.get_json(silent=True) or {}
    email = data.get("email", "").strip()
    code  = data.get("code", "").strip()

    pending, error = _otp_login.verificar(email, code)
    if error == "no_pendiente":
        return jsonify({"error": "No hay inicio de sesion pendiente para este correo"}), 400
    if error == "expirado":
        return jsonify({"error": "El codigo expiro. Vuelve a iniciar sesion"}), 400
    if error == "incorrecto":
        return jsonify({"error": "Codigo incorrecto"}), 400

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
def register():
    data = request.get_json(silent=True) or {}
    name     = data.get("name", "").strip()
    email    = data.get("email", "").strip()
    password = data.get("password", "")

    if not name or not email or not password:
        return jsonify({"error": "Nombre, correo y contrasena son requeridos"}), 400

    correo_valido, mensaje_correo = _validar_correo(email)
    if not correo_valido:
        return jsonify({"error": mensaje_correo}), 400

    error_pw = _validate_password(password)
    if error_pw:
        return jsonify({"error": error_pw}), 400

    dao = UsuarioDAO()
    if dao.consultar_por_correo(email) is not None:
        return jsonify({"error": "El correo ya esta registrado"}), 409

    code = _otp_registro.crear(email, {
        "name":          name,
        "password_hash": _hash_password(password),
    })

    try:
        enviar_codigo(
            email, name.split()[0], code,
            asunto="PetConnect - Codigo de verificacion",
            proposito="Usa este codigo para verificar tu correo y completar tu registro:",
        )
    except Exception as e:
        # Si el envio de correo falla (Mailtrap no configurado/no disponible),
        # el registro continua igual y el codigo queda visible en la consola
        # del servidor para poder completar la verificacion sin depender del correo.
        print(f"[DEV] No se pudo enviar el correo ({e}). Codigo para {email}: {code}")

    return jsonify({"message": "Codigo enviado", "email": email})


@app.route("/api/auth/verify", methods=["POST"])
def verify():
    data  = request.get_json(silent=True) or {}
    email = data.get("email", "").strip()
    code  = data.get("code", "").strip()

    pending, error = _otp_registro.verificar(email, code)
    if error == "no_pendiente":
        return jsonify({"error": "No hay verificacion pendiente para este correo"}), 400
    if error == "expirado":
        return jsonify({"error": "El codigo expiro. Vuelve a registrarte"}), 400
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

    dao = UsuarioDAO()
    if not dao.insertar(usuario):
        return jsonify({"error": "Error al crear el usuario"}), 500

    _otp_registro.descartar(email)

    try:
        enviar_bienvenida(email, nombres)
    except Exception as e:
        print(f"[DEV] No se pudo enviar el correo de bienvenida ({e}) a {email}")

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
    conn = _get_conn()
    if conn is None:
        print("[ERROR] No se pudo conectar a la base de datos.")
        sys.exit(1)
    print("[OK] Conexion a la base de datos establecida.")
    print("[OK] API PetConnect corriendo en http://localhost:5000")
    app.run(debug=True, port=5000)
