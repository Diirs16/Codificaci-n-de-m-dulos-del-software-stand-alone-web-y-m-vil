"""
API REST de PetConnect.
Ejecutar con: python api.py
"""

import sys
import os
import hashlib
import random
import time
import re
from datetime import datetime, date
from functools import wraps

# Cargar .env antes que cualquier import de config
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import mailtrap as mt
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, jsonify, request
from flask_cors import CORS
from mysql.connector import Error

from conexion.conexion_bd import ConexionBD
from dao.usuario_dao import UsuarioDAO
from modelo.usuario import Usuario
from config.email_config import EMAIL_CONFIG
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
_pending = {}


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
# Email
# ---------------------------------------------------------------------------

_HTML_CODE = """
<div style="font-family:Arial,sans-serif;max-width:480px;margin:auto;padding:32px;
            border:1px solid #e5e5e5;border-radius:12px;">
  <h2 style="color:#111;margin-bottom:8px;">PetConnect</h2>
  <p style="color:#555;">Hola <strong>{name}</strong>,</p>
  <p style="color:#555;">Tu codigo de verificacion es:</p>
  <div style="font-size:40px;font-weight:bold;letter-spacing:10px;text-align:center;
              padding:24px;background:#f5f5f5;border-radius:8px;margin:16px 0;">{code}</div>
  <p style="color:#999;font-size:13px;">Expira en <strong>10 minutos</strong>.<br>
  Si no solicitaste esto, ignora este mensaje.</p>
</div>"""


def _send_code(to_email: str, name: str, code: str):
    html = _HTML_CODE.format(name=name, code=code)
    texto = f"Hola {name},\n\nTu codigo: {code}\n\nExpira en 10 minutos.\n\nEquipo PetConnect"

    if EMAIL_CONFIG["mode"] == "smtp":
        msg = MIMEMultipart("alternative")
        msg["From"]    = f"PetConnect <{EMAIL_CONFIG['smtp_user']}>"
        msg["To"]      = to_email
        msg["Subject"] = "PetConnect - Codigo de verificacion"
        msg.attach(MIMEText(texto, "plain"))
        msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP(EMAIL_CONFIG["smtp_host"], EMAIL_CONFIG["smtp_port"]) as s:
            s.ehlo()
            s.starttls()
            s.login(EMAIL_CONFIG["smtp_user"], EMAIL_CONFIG["smtp_pass"])
            s.sendmail(EMAIL_CONFIG["smtp_user"], to_email, msg.as_string())
    else:
        mail = mt.Mail(
            sender=mt.Address(email=EMAIL_CONFIG["sender"], name=EMAIL_CONFIG["sender_name"]),
            to=[mt.Address(email=to_email)],
            subject="PetConnect - Codigo de verificacion",
            text=texto,
            html=html,
        )
        mt.MailtrapClient(token=EMAIL_CONFIG["api_token"]).send(mail)


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

    error_pw = _validate_password(password)
    if error_pw:
        return jsonify({"error": error_pw}), 400

    dao = UsuarioDAO()
    if dao.consultar_por_correo(email) is not None:
        return jsonify({"error": "El correo ya esta registrado"}), 409

    code = str(random.randint(100000, 999999))
    _pending[email] = {
        "code":          code,
        "name":          name,
        "password_hash": _hash_password(password),
        "expires":       time.time() + 600,
    }

    try:
        _send_code(email, name.split()[0], code)
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

    pending = _pending.get(email)
    if not pending:
        return jsonify({"error": "No hay verificacion pendiente para este correo"}), 400

    if time.time() > pending["expires"]:
        del _pending[email]
        return jsonify({"error": "El codigo expiro. Vuelve a registrarte"}), 400

    if pending["code"] != code:
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

    del _pending[email]

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
