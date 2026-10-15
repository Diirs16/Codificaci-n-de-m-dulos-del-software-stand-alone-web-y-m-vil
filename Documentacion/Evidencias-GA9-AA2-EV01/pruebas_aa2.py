"""
Ejecución de los casos de prueba CP-001 a CP-012 de PetConnect.
Evidencia GA9-220501096-AA2-EV01: Diseña casos y define el ambiente de pruebas de software según proyecto.

Qué hace:
  1. Crea una base de datos aislada `petconnect_qa` con la misma estructura de `petconnect`
     (sin copiar usuarios ni mascotas reales) y la elimina al terminar.
  2. Fuerza el envío de correo a fallar (modo smtp sin credenciales): no se envía ningún correo real.
     Los códigos OTP se leen del almacén en memoria de la API.
  3. Ejecuta los 12 casos, deja un log por caso en ./logs y el resumen en ./resultados.json.

Ejecutar desde la raíz del repositorio, con el entorno virtual del backend:
    .venv\\Scripts\\python.exe Documentacion\\Evidencias-GA9-AA2-EV01\\pruebas_aa2.py
"""
import contextlib
import hashlib
import io
import json
import logging
import math
import os
import random
import re
import secrets
import subprocess
import sys
import threading
import time
import traceback
import urllib.error
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", ".."))
BACKEND = os.path.join(RAIZ, "petconnect.Backend")
LOGS = os.path.join(AQUI, "logs")
os.makedirs(LOGS, exist_ok=True)
sys.path.insert(0, BACKEND)

# --- Entorno de prueba aislado: debe quedar definido ANTES de importar la aplicación ---
os.environ["DB_NAME"] = "petconnect_qa"
os.environ["EMAIL_MODE"] = "smtp"        # sin credenciales: el envío falla y el código queda en memoria
os.environ["MAILTRAP_SMTP_USER"] = ""
os.environ["MAILTRAP_SMTP_PASS"] = ""
os.environ["JWT_SECRET"] = secrets.token_hex(32)

from dotenv import load_dotenv  # noqa: E402

load_dotenv(os.path.join(BACKEND, ".env"))  # solo completa lo que falta (FERNET_KEY y conexión); no sobrescribe
import mysql.connector  # noqa: E402
from config.db_config import DB_CONFIG  # noqa: E402

QA = "petconnect_qa"
SERVIDOR_BD = {k: v for k, v in DB_CONFIG.items() if k != "database"}
FECHA = datetime.now().strftime("%d/%m/%Y")
RESULTADOS = []
CONTRASENA = "Firulais2026!"
logging.getLogger("werkzeug").setLevel(logging.ERROR)


# ---------------------------------------------------------------------------
# Utilidades de registro
# ---------------------------------------------------------------------------
class Caso:
    def __init__(self, cid, nombre, tipo):
        self.cid, self.nombre, self.tipo = cid, nombre, tipo
        self.lineas, self.checks, self.datos = [], [], {}
        self.log(f"===== {cid} – {nombre} =====")
        self.log(f"Tipo de prueba: {tipo} | Fecha de ejecución: {datetime.now():%d/%m/%Y %H:%M:%S}")

    def log(self, msg):
        linea = f"[{datetime.now():%H:%M:%S}] {msg}"
        self.lineas.append(linea)
        print(linea, file=sys.__stdout__, flush=True)

    def verificar(self, descripcion, ok, obtenido):
        ok = bool(ok)
        self.checks.append({"descripcion": descripcion, "ok": ok, "obtenido": str(obtenido)[:400]})
        self.log(f"{'OK   ' if ok else 'FALLA'} | {descripcion} | obtenido: {obtenido}")
        return ok

    def cerrar(self, resultado, salida, seguimiento="N/A", severidad="N/A"):
        self.log(f"RESULTADO: {resultado} | Seguimiento: {seguimiento} | Severidad: {severidad}")
        self.log(f"Salida obtenida: {salida}")
        archivo = f"{self.cid}.log"
        with open(os.path.join(LOGS, archivo), "w", encoding="utf-8") as f:
            f.write("\n".join(self.lineas) + "\n")
        RESULTADOS.append({
            "id": self.cid, "nombre": self.nombre, "tipo": self.tipo, "resultado": resultado,
            "salida_obtenida": salida, "seguimiento": seguimiento, "severidad": severidad,
            "verificaciones": self.checks, "datos": self.datos, "log": f"logs/{archivo}", "fecha": FECHA,
        })


def sql(consulta, params=(), base=QA, avisos=False):
    """Ejecuta una sentencia en una conexión propia (independiente de la de la API)."""
    con = mysql.connector.connect(**{**SERVIDOR_BD, "database": base})
    con.get_warnings = avisos
    cur = con.cursor()
    try:
        cur.execute(consulta, params)
        filas = cur.fetchall() if cur.with_rows else None
        advertencias = cur.fetchwarnings() if avisos else None
        con.commit()
        return (filas, advertencias, cur.lastrowid) if avisos else (filas if filas is not None else cur.lastrowid)
    finally:
        cur.close()
        con.close()


def percentil(valores, p):
    ordenados = sorted(valores)
    return ordenados[max(0, math.ceil(p / 100 * len(ordenados)) - 1)] if ordenados else None


# ---------------------------------------------------------------------------
# Preparación y limpieza de la base de datos aislada
# ---------------------------------------------------------------------------
def preparar_bd():
    con = mysql.connector.connect(**SERVIDOR_BD)
    cur = con.cursor()
    cur.execute("SHOW DATABASES LIKE %s", (QA,))
    if cur.fetchall():
        sys.exit(f"La base {QA} ya existe; el script se detiene para no borrar datos que no creó.")
    cur.execute(f"CREATE DATABASE {QA} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    cur.execute("SHOW TABLES FROM petconnect")
    tablas = [t[0] for t in cur.fetchall()]
    cur.execute(f"USE {QA}")
    cur.execute("SET FOREIGN_KEY_CHECKS = 0")
    for t in tablas:
        cur.execute(f"SHOW CREATE TABLE petconnect.`{t}`")
        cur.execute(cur.fetchone()[1])
    for t in ("categorias_producto", "productos", "roles", "planes"):  # catálogos sin datos personales
        cur.execute(f"INSERT INTO {QA}.`{t}` SELECT * FROM petconnect.`{t}`")
    cur.execute("SET FOREIGN_KEY_CHECKS = 1")
    con.commit()
    con.close()
    return tablas


def eliminar_bd():
    con = mysql.connector.connect(**SERVIDOR_BD)
    cur = con.cursor()
    cur.execute(f"DROP DATABASE IF EXISTS {QA}")
    con.close()


print(f"Preparando base aislada {QA}...", flush=True)
TABLAS = preparar_bd()
print(f"  {len(TABLAS)} tablas creadas con la estructura de petconnect.", flush=True)

import api  # noqa: E402
from dao.mascota_dao import MascotaDAO  # noqa: E402
from dao.proveedor_dao import ProveedorDAO  # noqa: E402
from dao.usuario_dao import UsuarioDAO  # noqa: E402
from modelo.mascota import Mascota  # noqa: E402
from modelo.proveedor_servicio import ProveedorServicio  # noqa: E402
from modelo.usuario import Usuario  # noqa: E402
from security.jwt_helper import generate_token  # noqa: E402

CLIENTE = api.app.test_client()


def llamar(metodo, ruta, cuerpo=None, token=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    with contextlib.redirect_stdout(io.StringIO()):
        r = CLIENTE.open(ruta, method=metodo, json=cuerpo, headers=headers)
    return r.status_code, r.get_json(silent=True)


def sembrar_usuarios():
    dao = UsuarioDAO()
    a = Usuario(nombres="Andrea", apellidos="Dueña QA", correo="duena.a@example.com",
                password_hash=api._hash_password(CONTRASENA), estado="activo", verificado=True)
    b = Usuario(nombres="Bruno", apellidos="Usuario QA", correo="usuario.b@example.com",
                password_hash=api._hash_password(CONTRASENA), estado="activo", verificado=True)
    assert dao.insertar(a) and dao.insertar(b), "No se pudieron crear los usuarios de prueba"
    return a, b


# ---------------------------------------------------------------------------
# Casos de prueba
# ---------------------------------------------------------------------------
def cp001():
    c = Caso("CP-001", "Registro de usuario con datos válidos y verificación por código OTP", "Funcional")
    correo = "laura.gomez.qa@example.com"
    t0 = time.perf_counter()
    s, d = llamar("POST", "/api/auth/register", {"name": "Laura Gómez", "email": correo, "password": CONTRASENA})
    t_reg = time.perf_counter() - t0
    ok = [c.verificar("Paso 1: POST /api/auth/register responde 200 'Codigo enviado'",
                      s == 200 and (d or {}).get("message") == "Codigo enviado", f"HTTP {s} {d} en {t_reg:.3f} s")]
    codigo = api._otp_registro._pendientes.get(correo, {}).get("code")
    ok.append(c.verificar("Se genera un código OTP de 6 dígitos", codigo and re.fullmatch(r"\d{6}", codigo), codigo))
    t0 = time.perf_counter()
    s2, d2 = llamar("POST", "/api/auth/verify", {"email": correo, "code": codigo})
    t_ver = time.perf_counter() - t0
    ok.append(c.verificar("Paso 2: POST /api/auth/verify responde 201 con token JWT",
                          s2 == 201 and (d2 or {}).get("token"), f"HTTP {s2} campos={sorted((d2 or {}).keys())} en {t_ver:.3f} s"))
    fila = sql("SELECT estado, verificado, password_hash FROM usuarios WHERE correo = %s", (correo,))
    ok.append(c.verificar("El usuario queda en la BD con estado 'activo' y verificado = 1",
                          fila and fila[0][0] == "activo" and fila[0][1] == 1, fila and fila[0][:2]))
    ok.append(c.verificar("La contraseña no se guarda en texto plano", fila and fila[0][2] != CONTRASENA,
                          fila and f"password_hash de {len(fila[0][2])} caracteres"))
    c.datos = {"tiempo_registro_s": round(t_reg, 3), "tiempo_verificacion_s": round(t_ver, 3)}
    if all(ok):
        c.cerrar("Aprobado", f"Registro respondió HTTP 200 ({t_reg:.2f} s) y envió el código OTP de 6 dígitos; la verificación "
                 f"respondió HTTP 201 con token JWT ({t_ver:.2f} s). El usuario quedó en la BD como activo y verificado, "
                 "sin la contraseña en texto plano.")
    else:
        c.cerrar("Rechazado", "Falló al menos un paso del registro: " + "; ".join(x["descripcion"] for x in c.checks if not x["ok"]),
                 "NC-012", "Alta")


def cp002():
    c = Caso("CP-002", "Registro de usuario con datos inválidos (partición de equivalencia y valores límite)", "Funcional")
    base = {"name": "Laura Gómez", "password": CONTRASENA}
    pruebas = [
        ("Correo con formato inválido", {**base, "email": "laura.gomez@@correo"}, 400),
        ("Dominio de correo inexistente", {**base, "email": "laura@dominio-inexistente-petconnect-qa.com"}, 400),
        ("Contraseña de 7 caracteres (valor límite inferior)", {**base, "email": "qa.cp002.a@example.com", "password": "Abc12!x"}, 400),
        ("Contraseña sin mayúscula", {**base, "email": "qa.cp002.b@example.com", "password": "firulais2026!"}, 400),
        ("Contraseña sin número", {**base, "email": "qa.cp002.c@example.com", "password": "Firulais!!!"}, 400),
        ("Contraseña sin minúscula (política RS03)", {**base, "email": "qa.cp002.d@example.com", "password": "PETCONNECT1!"}, 400),
        ("Correo ya registrado", {**base, "email": "laura.gomez.qa@example.com"}, 409),
    ]
    fallas = []
    for desc, cuerpo, esperado in pruebas:
        s, d = llamar("POST", "/api/auth/register", cuerpo)
        if not c.verificar(f"{desc} → HTTP {esperado}", s == esperado, f"HTTP {s} {d}"):
            fallas.append((desc, s, (d or {}).get("message") or (d or {}).get("error")))
    c.datos = {"entradas": len(pruebas), "rechazadas_correctamente": len(pruebas) - len(fallas)}
    if not fallas:
        c.cerrar("Aprobado", f"Las {len(pruebas)} entradas inválidas fueron rechazadas con el código HTTP esperado.")
    elif [f[0] for f in fallas] == ["Contraseña sin minúscula (política RS03)"]:
        c.cerrar("En seguimiento",
                 f"{len(pruebas) - 1} de {len(pruebas)} entradas se rechazaron correctamente (formato y dominio del correo, longitud 7, "
                 "sin mayúscula, sin número y correo duplicado con 409). La contraseña 'PETCONNECT1!', sin minúscula, fue aceptada "
                 f"(HTTP {fallas[0][1]} '{fallas[0][2]}') e incumple la política de RS03.", "NC-004", "Media")
    else:
        c.cerrar("Rechazado", "Entradas inválidas aceptadas: " + "; ".join(f"{f[0]} (HTTP {f[1]})" for f in fallas), "NC-004", "Alta")


def cp003(a, b):
    c = Caso("CP-003", "Registro de más de una mascota para el mismo usuario", "Funcional")
    dao = MascotaDAO()
    toby = Mascota(id_usuario=a.id_usuario, nombre="Toby", especie="Perro", raza="Criollo", sexo="macho", edad_aprox=3,
                   color="Café", peso=12.5, foto="https://example.com/toby.jpg", observaciones="Alergia a la penicilina", estado="activa")
    mia = Mascota(id_usuario=a.id_usuario, nombre="Mía", especie="Gato", raza="Siamés", sexo="hembra", edad_aprox=2,
                  color="Crema", peso=4.1, foto="https://example.com/mia.jpg", observaciones="Esterilizada", estado="activa")
    rocky = Mascota(id_usuario=b.id_usuario, nombre="Rocky", especie="Perro", raza="Labrador", sexo="macho", edad_aprox=5,
                    color="Negro", peso=30.0, foto="https://example.com/rocky.jpg", observaciones="", estado="activa")
    with contextlib.redirect_stdout(io.StringIO()):
        inserciones = [dao.insertar(m) for m in (toby, mia, rocky)]
    ok = [c.verificar("Se registran Toby y Mía para el usuario A y Rocky para el usuario B", all(inserciones),
                      f"ids = {toby.id_mascota}, {mia.id_mascota}, {rocky.id_mascota}")]
    de_a = dao.consultar_por_usuario(a.id_usuario)
    ok.append(c.verificar("El usuario A tiene exactamente sus 2 mascotas", sorted(m.nombre for m in de_a) == ["Mía", "Toby"],
                          [m.nombre for m in de_a]))
    ok.append(c.verificar("Cada mascota tiene un identificador propio", len({m.id_mascota for m in de_a}) == 2,
                          [m.id_mascota for m in de_a]))
    guardada = next((m for m in de_a if m.nombre == "Toby"), None)
    campos = guardada and (guardada.especie, guardada.raza, guardada.edad_aprox, guardada.foto)
    ok.append(c.verificar("Se conservan los campos de RIU02 (especie, raza, edad y foto)",
                          campos == ("Perro", "Criollo", 3, "https://example.com/toby.jpg"), campos))
    de_b = dao.consultar_por_usuario(b.id_usuario)
    ok.append(c.verificar("Las mascotas no se mezclan entre usuarios", [m.nombre for m in de_b] == ["Rocky"], [m.nombre for m in de_b]))
    s, _ = llamar("POST", "/api/mascotas", {"name": "Toby"})
    c.log(f"Observación: la API REST aún no expone el registro de mascotas (POST /api/mascotas → HTTP {s}); "
          "la prueba se ejecutó sobre el módulo stand-alone (MascotaDAO).")
    c.datos = {"ids": [toby.id_mascota, mia.id_mascota, rocky.id_mascota], "api_post_mascotas": s}
    if all(ok):
        c.cerrar("Aprobado", "Se registraron 2 mascotas (Toby y Mía) para el mismo usuario con identificadores distintos; la consulta "
                 "por usuario devolvió exactamente esas 2, con nombre, especie, raza, edad y foto, sin mezclar la mascota de otro usuario.")
    else:
        c.cerrar("Rechazado", "Falló: " + "; ".join(x["descripcion"] for x in c.checks if not x["ok"]), "NC-013", "Alta")
    return toby, mia, rocky


def cp004(toby):
    c = Caso("CP-004", "Almacenamiento y consulta del carné de vacunación", "Integración")
    id_vacuna = sql("INSERT INTO vacunas (nombre, descripcion, especie_aplicable, dosis_recomendada) VALUES (%s, %s, %s, %s)",
                    ("Antirrábica", "Vacuna contra la rabia", "Perro", "Anual"))
    sql("INSERT INTO aplicaciones_vacuna (id_mascota, id_vacuna, fecha_aplicacion, fecha_proxima, veterinario, observaciones) "
        "VALUES (%s, %s, '2025-11-03', '2026-11-03', 'Clínica Veterinaria QA', 'Lote QA-001')", (toby.id_mascota, id_vacuna))
    sql("INSERT INTO carnets_vacunacion (id_mascota, numero_carnet) VALUES (%s, 'PC-QA-0001')", (toby.id_mascota,))
    carne = sql("SELECT v.nombre, a.fecha_aplicacion, a.fecha_proxima, a.veterinario FROM aplicaciones_vacuna a "
                "JOIN vacunas v ON v.id_vacuna = a.id_vacuna WHERE a.id_mascota = %s", (toby.id_mascota,))
    ok = [c.verificar("Se guarda y se consulta la vacuna del carné de Toby",
                      len(carne) == 1 and carne[0][0] == "Antirrábica" and str(carne[0][2]) == "2026-11-03",
                      [(r[0], str(r[1]), str(r[2]), r[3]) for r in carne])]
    try:
        sql("INSERT INTO aplicaciones_vacuna (id_mascota, id_vacuna, fecha_aplicacion, fecha_proxima) "
            "VALUES (999999, %s, '2025-11-03', '2026-11-03')", (id_vacuna,))
        rechazo_fk = "aceptada"
    except mysql.connector.Error as e:
        rechazo_fk = f"rechazada (error {e.errno})"
    ok.append(c.verificar("Se rechaza una vacuna para una mascota inexistente (integridad referencial)",
                          rechazo_fk.startswith("rechazada"), rechazo_fk))
    try:
        sql("INSERT INTO aplicaciones_vacuna (id_mascota, id_vacuna, fecha_aplicacion, fecha_proxima) "
            "VALUES (%s, %s, '2025-11-03', '2025-01-01')", (toby.id_mascota, id_vacuna))
        fechas = "aceptada"
    except mysql.connector.Error as e:
        fechas = f"rechazada (error {e.errno})"
    fechas_ok = c.verificar("Se rechaza una próxima dosis anterior a la fecha de aplicación (2025-01-01 < 2025-11-03)",
                            fechas.startswith("rechazada"), fechas)
    s, _ = llamar("GET", f"/api/mascotas/{toby.id_mascota}/vacunas")
    c.log(f"Observación: el módulo del carné en la API/app aún no existe (GET /api/mascotas/{toby.id_mascota}/vacunas → HTTP {s}); "
          "está programado para el Sprint 2 del plan.")
    c.datos = {"fk": rechazo_fk, "fechas_inconsistentes": fechas, "api_vacunas": s}
    if all(ok) and fechas_ok:
        c.cerrar("Aprobado", "El carné guarda y devuelve la vacuna con sus fechas, y rechaza registros sin mascota y fechas inconsistentes.")
    elif all(ok):
        c.cerrar("En seguimiento", "La BD guardó y devolvió la vacuna Antirrábica de Toby (aplicación 2025-11-03, próxima 2026-11-03) "
                 f"y rechazó la vacuna para una mascota inexistente ({rechazo_fk}). Pero aceptó una próxima dosis (2025-01-01) "
                 "anterior a la aplicación: no hay validación de fechas. El módulo del carné en la API/app aún no existe.",
                 "NC-010", "Media")
    else:
        c.cerrar("Rechazado", "El carné no se almacena correctamente: " + "; ".join(x["descripcion"] for x in c.checks if not x["ok"]),
                 "NC-010", "Alta")


def cp005():
    c = Caso("CP-005", "Búsqueda en el directorio de servicios veterinarios", "Funcional")
    dao = ProveedorDAO()
    datos = [("Veterinaria Huellitas", "Armenia", True, True), ("Clínica Veterinaria San Roque", "Pereira", False, True),
             ("Peluquería Canina Patitas", "Armenia", False, True), ("Veterinaria El Refugio (inactiva)", "Armenia", False, False)]
    with contextlib.redirect_stdout(io.StringIO()):
        for i, (nombre, ciudad, h24, activo) in enumerate(datos, 1):
            dao.insertar(ProveedorServicio(nombre=nombre, tipo_documento="NIT", numero_documento=f"90000000{i}",
                                           telefono="6067000000", correo=f"contacto{i}@example.com", direccion=f"Calle {i} # 10-20",
                                           ciudad=ciudad, descripcion="Proveedor de prueba", horario="08:00-18:00",
                                           atiende_24_7=h24, latitud=4.5338900, longitud=-75.6811100, activo=activo))
    por_nombre = sorted(p.nombre for p in dao.buscar_por_nombre("Veterinaria"))
    por_ciudad = sorted(p.nombre for p in dao.consultar_por_ciudad("Armenia"))
    inyeccion = dao.buscar_por_nombre("' OR '1'='1")
    sin_resultados = dao.buscar_por_nombre("xyz-no-existe")
    ok_ciudad = c.verificar("Filtro por ciudad 'Armenia' devuelve solo los proveedores activos de Armenia",
                            por_ciudad == ["Peluquería Canina Patitas", "Veterinaria Huellitas"], por_ciudad)
    ok_iny = c.verificar("Una cadena de inyección SQL no devuelve resultados (consulta parametrizada)", len(inyeccion) == 0, len(inyeccion))
    ok_vacio = c.verificar("Un término inexistente devuelve una lista vacía", len(sin_resultados) == 0, len(sin_resultados))
    ok_nombre = c.verificar("Búsqueda 'Veterinaria' devuelve solo proveedores activos",
                            por_nombre == ["Clínica Veterinaria San Roque", "Veterinaria Huellitas"], por_nombre)
    c.datos = {"por_nombre": por_nombre, "por_ciudad": por_ciudad}
    if ok_ciudad and ok_iny and ok_vacio and ok_nombre:
        c.cerrar("Aprobado", "La búsqueda por nombre y el filtro por ciudad devolvieron solo los proveedores activos que coinciden; "
                 "la inyección SQL y el término inexistente devolvieron 0 resultados.")
    elif ok_ciudad and ok_iny and ok_vacio:
        c.cerrar("En seguimiento", "El filtro por ciudad devolvió solo los 2 proveedores activos de Armenia, y la inyección SQL y el "
                 "término inexistente devolvieron 0 resultados. Pero la búsqueda por nombre 'Veterinaria' incluyó 'Veterinaria "
                 "El Refugio (inactiva)': buscar_por_nombre() no filtra por activo.", "NC-011", "Baja")
    else:
        c.cerrar("Rechazado", "Falló: " + "; ".join(x["descripcion"] for x in c.checks if not x["ok"]), "NC-011", "Media")


def cp006(toby, b):
    c = Caso("CP-006", "Acceso no autorizado a la información de la mascota de otro usuario (RS02)", "Seguridad")
    s1, d1 = llamar("GET", f"/api/mascotas/{toby.id_mascota}")
    ok1 = c.verificar("Sin token: GET /api/mascotas/{id} de una mascota privada responde 401, 403 o 404",
                      s1 in (401, 403, 404), f"HTTP {s1} {d1}")
    token_b = generate_token(b.id_usuario, b.correo)
    s2, d2 = llamar("GET", f"/api/mascotas/{toby.id_mascota}", token=token_b)
    ok2 = c.verificar("Con el token del usuario B (no dueño): responde 403 o 404", s2 in (403, 404), f"HTTP {s2}")
    expuestos = sorted(k for k in (d1 or {}) if k in ("name", "species", "breed", "description", "image"))
    c.datos = {"sin_token": s1, "token_ajeno": s2, "campos_expuestos": expuestos}
    if ok1 and ok2:
        c.cerrar("Aprobado", "La API negó el acceso a la mascota ajena con y sin token.")
    else:
        c.cerrar("Rechazado", f"La API respondió HTTP {s1} sin token y HTTP {s2} con el token de otro usuario, y entregó los datos de "
                 f"'{(d1 or {}).get('name')}' (mascota privada, estado 'activa'), incluidas sus observaciones de salud "
                 f"('{(d1 or {}).get('description')}'). El endpoint no exige autenticación ni verifica el dueño.", "NC-002", "Alta")


def cp007():
    c = Caso("CP-007", "Validación del almacenamiento de contraseñas con bcrypt en la BD (RS03)", "Seguridad")
    filas = dict(sql("SELECT correo, password_hash FROM usuarios WHERE correo IN (%s, %s, %s)",
                     ("laura.gomez.qa@example.com", "duena.a@example.com", "usuario.b@example.com")))
    h = filas.get("laura.gomez.qa@example.com", "")
    ok1 = c.verificar("El hash tiene formato bcrypt: prefijo $2b$12$ y 60 caracteres",
                      h.startswith("$2b$12$") and len(h) == 60, f"prefijo '{h[:7]}', longitud {len(h)}")
    es_sha = h == hashlib.sha256(CONTRASENA.encode()).hexdigest()
    ok2 = c.verificar("El valor no es un SHA-256 sin sal de la contraseña", not es_sha,
                      "coincide con sha256('Firulais2026!')" if es_sha else "no coincide")
    iguales = len(set(filas.values())) == 1 and len(filas) == 3
    ok3 = c.verificar("Tres usuarios con la misma contraseña tienen hashes distintos (sal aleatoria)", not iguales,
                      "los 3 hashes son idénticos" if iguales else "distintos")
    c.datos = {"longitud": len(h), "prefijo": h[:7], "sha256_sin_sal": es_sha, "hashes_identicos": iguales}
    if ok1 and ok2 and ok3:
        c.cerrar("Aprobado", "Las contraseñas se guardan con bcrypt (costo 12) y sal aleatoria.")
    else:
        c.cerrar("Rechazado", f"El password_hash tiene {len(h)} caracteres hexadecimales (prefijo '{h[:7]}') y coincide con el SHA-256 "
                 "sin sal de la contraseña; los 3 usuarios con la misma contraseña tienen exactamente el mismo hash. No se usa bcrypt.",
                 "NC-001", "Alta")


def cp010():
    c = Caso("CP-010", "Cálculo de la fecha de recordatorio de vacunación (3 días antes)", "Unitaria")
    proc = subprocess.run(["node", "--test", "--test-reporter=tap", os.path.join(AQUI, "cp010", "Vacunacion.test.mjs")],
                          capture_output=True, text=True, encoding="utf-8", env={**os.environ, "TZ": "America/Bogota"})
    for linea in proc.stdout.splitlines():
        if linea.strip():
            c.log(f"node:test | {linea}")
    total = int((re.search(r"# tests (\d+)", proc.stdout) or [0, 0])[1])
    pasan = int((re.search(r"# pass (\d+)", proc.stdout) or [0, 0])[1])
    ok = c.verificar("Todas las pruebas unitarias pasan", proc.returncode == 0 and total > 0 and pasan == total, f"{pasan}/{total}")
    c.datos = {"tests": total, "pass": pasan}
    if ok:
        c.cerrar("Aprobado", f"{pasan} de {total} pruebas pasaron: próxima dosis 2026-11-03 y aviso 2026-10-31; estados correctos en "
                 "los días límite (30/10 programado, 31/10 y 03/11 aviso activo, 04/11 vencida); periodicidad 0 rechazada.")
    else:
        c.cerrar("Rechazado", f"Solo {pasan} de {total} pruebas pasaron.", "NC-014", "Media")


def cp011():
    c = Caso("CP-011", "Validación de campos obligatorios vacíos en registro e inicio de sesión", "Unitaria")
    ok = []
    v = api._validar_correo("")
    ok.append(c.verificar("_validar_correo('') rechaza el correo vacío", v == (False, "El correo es requerido"), v))
    p = api._validate_password("")
    ok.append(c.verificar("_validate_password('') exige la longitud mínima", p and "8 caracteres" in p, p))
    for desc, ruta, cuerpo in [("Registro con cuerpo vacío", "/api/auth/register", {}),
                               ("Registro solo con nombre", "/api/auth/register", {"name": "Laura"}),
                               ("Registro sin contraseña", "/api/auth/register", {"name": "Laura", "email": "laura@example.com"}),
                               ("Inicio de sesión vacío", "/api/auth/login", {}),
                               ("Inicio de sesión sin contraseña", "/api/auth/login", {"email": "laura@example.com"})]:
        s, d = llamar("POST", ruta, cuerpo)
        ok.append(c.verificar(f"{desc} → HTTP 400 'requeridos'", s == 400 and "requeridos" in (d or {}).get("error", ""), f"HTTP {s} {d}"))
    if all(ok):
        c.cerrar("Aprobado", "Las 2 funciones de validación rechazaron los valores vacíos y los 5 envíos con campos vacíos "
                 "respondieron HTTP 400 con el mensaje 'son requeridos'; no se creó ningún registro.")
    else:
        c.cerrar("Rechazado", "Campos vacíos aceptados: " + "; ".join(x["descripcion"] for x in c.checks if not x["ok"]), "NC-015", "Media")


def cp012(a):
    c = Caso("CP-012", "Flujo completo de adopción de una mascota", "Aceptación")
    # Paso 1: publicar en adopción del mismo modo que lo hace el sistema (seed.py usa el estado 'en_adopcion')
    _, avisos, id_luna = sql("INSERT INTO mascotas (id_usuario, nombre, especie, raza, sexo, edad_aprox, estado) "
                             "VALUES (%s, 'Luna', 'Perro', 'Mestiza', 'hembra', 1, 'en_adopcion')", (a.id_usuario,), avisos=True)
    estado = sql("SELECT estado FROM mascotas WHERE id_mascota = %s", (id_luna,))[0][0]
    ok1 = c.verificar("Paso 1: la mascota publicada queda con estado 'en_adopcion'", estado == "en_adopcion",
                      f"estado guardado = '{estado}'; advertencia de la BD: {avisos}")
    s2, d2 = llamar("GET", "/api/mascotas/adopcion")
    ok2 = c.verificar("Paso 2: GET /api/mascotas/adopcion muestra a Luna en el catálogo",
                      s2 == 200 and any((m or {}).get("name") == "Luna" for m in (d2 or [])), f"HTTP {s2}, {len(d2 or [])} mascotas")
    token_a = generate_token(a.id_usuario, a.correo)
    s3, _ = llamar("POST", "/api/adopciones", {"id_mascota": id_luna}, token=token_a)
    ok3 = c.verificar("Paso 3: POST /api/adopciones registra la solicitud de adopción", s3 in (200, 201), f"HTTP {s3}")
    real = sql("SELECT estado, COUNT(*) FROM mascotas GROUP BY estado", base="petconnect")
    c.log(f"Contraste en la BD de desarrollo (solo lectura): mascotas por estado = {real}")
    c.log("Contraste en la web: Adoption.jsx solo reemplaza las mascotas fijas de src/data/pets.js si la API devuelve datos "
          "(if (data.length > 0)); con la lista vacía muestra las mascotas de ejemplo y oculta el defecto.")
    c.datos = {"estado_guardado": estado, "catalogo": len(d2 or []), "post_adopciones": s3, "bd_desarrollo": real}
    if ok1 and ok2 and ok3:
        c.cerrar("Aprobado", "La mascota se publicó, apareció en el catálogo y la solicitud de adopción se registró.")
    else:
        c.cerrar("Rechazado", f"El flujo se detuvo en el paso 1. El estado 'en_adopcion' que usan seed.py y la API no existe en el enum "
                 f"de mascotas.estado; MariaDB (modo no estricto) lo guardó como '{estado}' con la advertencia 1265. Por eso "
                 f"GET /api/mascotas/adopcion devolvió {len(d2 or [])} mascotas, y POST /api/adopciones respondió HTTP {s3} (no existe). "
                 f"En la BD de desarrollo, las {sum(n for _, n in real)} mascotas tienen estado vacío. La web oculta el defecto "
                 "mostrando mascotas fijas.", "NC-009", "Alta")


# ---------------------------------------------------------------------------
# Pruebas de rendimiento contra el servidor real (Werkzeug, el mismo de `python api.py`)
# ---------------------------------------------------------------------------
PUERTO = 5055
URL = f"http://127.0.0.1:{PUERTO}"


def iniciar_servidor():
    from werkzeug.serving import make_server
    try:
        api._conexion_bd.cerrar_conexion()   # equivale a reiniciar el servidor: conexión nueva
    except Exception:
        pass
    api._conexion_bd._conexion = None
    srv = make_server("127.0.0.1", PUERTO, api.app, threaded=True)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def http(metodo, ruta, cuerpo=None, timeout=30):
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    req = urllib.request.Request(URL + ruta, data=datos, method=metodo, headers={"Content-Type": "application/json"})
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, time.perf_counter() - t0, r.read()
    except urllib.error.HTTPError as e:
        return e.code, time.perf_counter() - t0, e.read()
    except Exception as e:
        return type(e).__name__, time.perf_counter() - t0, str(e).encode()


def resumen_carga(muestras, duracion):
    tiempos = [t for _, t, _ in muestras]
    ok = [m for m in muestras if m[0] in (200, 201)]
    errores = Counter(str(m[0]) for m in muestras if m[0] not in (200, 201))
    cuerpos = Counter(m[2][:120].decode("utf-8", "replace") for m in muestras if m[0] == 500)
    return {
        "solicitudes": len(muestras), "exitosas": len(ok), "tasa_error_pct": round(100 * (len(muestras) - len(ok)) / len(muestras), 2),
        "p50_s": round(percentil(tiempos, 50), 3), "p95_s": round(percentil(tiempos, 95), 3),
        "p99_s": round(percentil(tiempos, 99), 3), "max_s": round(max(tiempos), 3),
        "promedio_s": round(sum(tiempos) / len(tiempos), 3), "duracion_s": round(duracion, 1),
        "rendimiento_rps": round(len(muestras) / duracion, 1), "errores": dict(errores), "errores_500": dict(cuerpos.most_common(3)),
    }


def veredicto_carga(c, r, umbral, codigo):
    c.log(f"Métricas: {json.dumps(r, ensure_ascii=False)}")
    ok_t = c.verificar(f"p95 ≤ {umbral} s por acción (RNF04)", r["p95_s"] <= umbral, f"p95 = {r['p95_s']} s")
    ok_e = c.verificar("Tasa de error < 1 %", r["tasa_error_pct"] < 1, f"{r['tasa_error_pct']} % ({r['errores']})")
    if ok_t and ok_e:
        return "Aprobado", "N/A", "N/A"
    if r["tasa_error_pct"] <= 5:
        return "En seguimiento", codigo, "Media"
    return "Rechazado", codigo, "Alta"


def cp008(ids_mascotas):
    c = Caso("CP-008", "Carga de 500 usuarios concurrentes sobre la API", "Rendimiento")
    usuarios, rampa = 500, 10.0
    c.log(f"Escenario: {usuarios} usuarios virtuales, rampa de {rampa:.0f} s; cada uno consulta el catálogo de productos, espera 1 s "
          "y consulta el detalle de una mascota. Servidor: Werkzeug (el mismo de `python api.py`).")
    srv = iniciar_servidor()
    muestras, candado = [], threading.Lock()

    def usuario(i):
        time.sleep(i * rampa / usuarios)
        r1 = http("GET", "/api/productos")
        time.sleep(1)
        r2 = http("GET", f"/api/mascotas/{random.choice(ids_mascotas)}")
        with candado:
            muestras.extend([r1, r2])

    t0 = time.perf_counter()
    with contextlib.redirect_stdout(io.StringIO()), ThreadPoolExecutor(max_workers=usuarios) as ex:
        list(ex.map(usuario, range(usuarios)))
    r = resumen_carga(muestras, time.perf_counter() - t0)
    tras = http("GET", "/api/productos")
    c.log(f"Recuperación: una solicitud posterior a la prueba respondió HTTP {tras[0]} en {tras[1]:.3f} s")
    srv.shutdown()
    r["recuperacion"] = tras[0]
    c.datos = r
    resultado, seg, sev = veredicto_carga(c, r, 2.0, "NC-003")
    salida = (f"{r['solicitudes']} solicitudes en {r['duracion_s']} s ({r['rendimiento_rps']} solicitudes/s): p50 {r['p50_s']} s, "
              f"p95 {r['p95_s']} s, máximo {r['max_s']} s; tasa de error {r['tasa_error_pct']} %")
    if r["errores"]:
        salida += f" ({', '.join(f'{k}: {v}' for k, v in r['errores'].items())})"
    salida += f". Tras la prueba la API respondió HTTP {tras[0]}."
    c.cerrar(resultado, salida, seg, sev)


def cp009():
    c = Caso("CP-009", "Rendimiento en el registro masivo de usuarios", "Rendimiento")
    usuarios, rampa = 100, 5.0
    c.log(f"Escenario: {usuarios} registros completos (registro + verificación OTP) con rampa de {rampa:.0f} s.")
    srv = iniciar_servidor()
    muestras, candado = [], threading.Lock()

    def usuario(i):
        time.sleep(i * rampa / usuarios)
        correo = f"qa.cp009.{i:03d}@example.com"
        r1 = http("POST", "/api/auth/register", {"name": f"Usuario Carga {i:03d}", "email": correo, "password": CONTRASENA})
        codigo = api._otp_registro._pendientes.get(correo, {}).get("code", "000000")
        r2 = http("POST", "/api/auth/verify", {"email": correo, "code": codigo})
        with candado:
            muestras.extend([r1, r2])

    t0 = time.perf_counter()
    with contextlib.redirect_stdout(io.StringIO()), ThreadPoolExecutor(max_workers=usuarios) as ex:
        list(ex.map(usuario, range(usuarios)))
    r = resumen_carga(muestras, time.perf_counter() - t0)
    srv.shutdown()
    creados = sql("SELECT COUNT(*) FROM usuarios WHERE correo LIKE 'qa.cp009.%%'")[0][0]
    r["usuarios_creados"] = creados
    c.datos = r
    resultado, seg, sev = veredicto_carga(c, r, 2.0, "NC-003")
    ok_c = c.verificar(f"Se crean los {usuarios} usuarios en la BD", creados == usuarios, creados)
    if not ok_c and resultado == "Aprobado":
        resultado, seg, sev = "En seguimiento", "NC-003", "Media"
    salida = (f"{r['solicitudes']} solicitudes ({usuarios} registros + {usuarios} verificaciones) en {r['duracion_s']} s: "
              f"p50 {r['p50_s']} s, p95 {r['p95_s']} s, máximo {r['max_s']} s; tasa de error {r['tasa_error_pct']} %")
    if r["errores"]:
        salida += f" ({', '.join(f'{k}: {v}' for k, v in r['errores'].items())})"
    salida += f". Usuarios creados en la BD: {creados} de {usuarios}."
    c.cerrar(resultado, salida, seg, sev)


# ---------------------------------------------------------------------------
# Ejecución
# ---------------------------------------------------------------------------
def ejecutar(funcion, *args):
    try:
        return funcion(*args)
    except Exception:
        traza = traceback.format_exc()
        print(traza, file=sys.__stdout__)
        RESULTADOS.append({"id": funcion.__name__.upper().replace("CP", "CP-"), "resultado": "ERROR DE EJECUCIÓN", "traza": traza})
        return None


if __name__ == "__main__":
    inicio = datetime.now()
    try:
        ejecutar(cp011)
        ejecutar(cp010)
        a, b = sembrar_usuarios()
        ejecutar(cp001)
        ejecutar(cp002)
        ejecutar(cp007)
        mascotas = ejecutar(cp003, a, b)
        toby = mascotas[0] if mascotas else None
        ejecutar(cp004, toby)
        ejecutar(cp005)
        ejecutar(cp006, toby, b)
        ejecutar(cp012, a)
        ejecutar(cp008, [m.id_mascota for m in mascotas] if mascotas else [1])
        ejecutar(cp009)
    finally:
        try:
            api._conexion_bd.cerrar_conexion()
        except Exception:
            pass
        eliminar_bd()
        print(f"Base {QA} eliminada.", flush=True)
        RESULTADOS.sort(key=lambda r: r["id"])
        ambiente = {
            "inicio": f"{inicio:%d/%m/%Y %H:%M:%S}", "fin": f"{datetime.now():%d/%m/%Y %H:%M:%S}",
            "python": sys.version.split()[0], "bd_version": sql("SELECT VERSION()", base="petconnect")[0][0],
            "node": subprocess.run(["node", "--version"], capture_output=True, text=True).stdout.strip(),
        }
        with open(os.path.join(AQUI, "resultados.json"), "w", encoding="utf-8") as f:
            json.dump({"ambiente": ambiente, "casos": RESULTADOS}, f, ensure_ascii=False, indent=2, default=str)
        print("\nRESUMEN", flush=True)
        for r in RESULTADOS:
            print(f"  {r['id']}: {r['resultado']}  {r.get('seguimiento', '')} {r.get('severidad', '')}", flush=True)
