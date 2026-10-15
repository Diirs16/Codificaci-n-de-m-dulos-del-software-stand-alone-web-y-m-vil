"""
Prueba de confirmación de NC-001 (contraseñas con bcrypt) y NC-008 (token JWT).
Repite contra la base de datos los flujos que fallaron el 5 de octubre de 2026
(evidencia GA9-220501096-AA2-EV01) después de aplicar las correcciones.

Igual que pruebas_aa2.py: crea la base aislada `petconnect_qa`, fuerza el correo a
no enviarse y elimina la base al terminar. Deja un log por verificación en ./logs
y el resumen en ./resultados.json.

Ejecutar desde la raíz del repositorio:
    .venv\\Scripts\\python.exe Documentacion\\Evidencias-Confirmacion-NC-001-NC-008\\confirmacion.py
"""
import builtins
import contextlib
import hashlib
import io
import json
import os
import secrets
import sys
import traceback
from datetime import datetime

AQUI = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.abspath(os.path.join(AQUI, "..", "..", "petconnect.Backend"))
LOGS = os.path.join(AQUI, "logs")
os.makedirs(LOGS, exist_ok=True)
sys.path.insert(0, BACKEND)

os.environ["DB_NAME"] = "petconnect_qa"
os.environ["EMAIL_MODE"] = "smtp"
os.environ["MAILTRAP_SMTP_USER"] = ""
os.environ["MAILTRAP_SMTP_PASS"] = ""
os.environ["JWT_SECRET"] = secrets.token_hex(32)

from dotenv import load_dotenv  # noqa: E402

load_dotenv(os.path.join(BACKEND, ".env"))
import mysql.connector  # noqa: E402
from config.db_config import DB_CONFIG  # noqa: E402

QA = "petconnect_qa"
SERVIDOR_BD = {k: v for k, v in DB_CONFIG.items() if k != "database"}
CONTRASENA = "Firulais2026!"
RESULTADOS = []


class Verificacion:
    def __init__(self, cid, nc, nombre):
        self.cid, self.nc, self.nombre, self.lineas, self.checks = cid, nc, nombre, [], []
        self.log(f"===== {cid} ({nc}) – {nombre} =====")
        self.log(f"Fecha de ejecución: {datetime.now():%d/%m/%Y %H:%M:%S}")

    def log(self, msg):
        linea = f"[{datetime.now():%H:%M:%S}] {msg}"
        self.lineas.append(linea)
        print(linea, file=sys.__stdout__, flush=True)

    def verificar(self, descripcion, ok, obtenido):
        self.checks.append({"descripcion": descripcion, "ok": bool(ok), "obtenido": str(obtenido)[:300]})
        self.log(f"{'OK   ' if ok else 'FALLA'} | {descripcion} | obtenido: {obtenido}")

    def cerrar(self):
        aprobado = all(c["ok"] for c in self.checks)
        self.log(f"RESULTADO: {'Aprobado' if aprobado else 'Rechazado'}")
        with open(os.path.join(LOGS, f"{self.cid}.log"), "w", encoding="utf-8") as f:
            f.write("\n".join(self.lineas) + "\n")
        RESULTADOS.append({"id": self.cid, "nc": self.nc, "nombre": self.nombre,
                           "resultado": "Aprobado" if aprobado else "Rechazado", "verificaciones": self.checks})


def sql(consulta, params=()):
    con = mysql.connector.connect(**{**SERVIDOR_BD, "database": QA})
    cur = con.cursor()
    try:
        cur.execute(consulta, params)
        filas = cur.fetchall() if cur.with_rows else None
        con.commit()
        return filas if filas is not None else cur.lastrowid
    finally:
        cur.close()
        con.close()


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
    cur.execute("SET FOREIGN_KEY_CHECKS = 1")
    con.commit()
    con.close()


def eliminar_bd():
    con = mysql.connector.connect(**SERVIDOR_BD)
    con.cursor().execute(f"DROP DATABASE IF EXISTS {QA}")
    con.close()


preparar_bd()
import api  # noqa: E402
from vista.menu_usuarios import MenuUsuarios  # noqa: E402

CLIENTE = api.app.test_client()


def llamar(metodo, ruta, cuerpo=None, token=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    with contextlib.redirect_stdout(io.StringIO()):
        r = CLIENTE.open(ruta, method=metodo, json=cuerpo, headers=headers)
    return r.status_code, r.get_json(silent=True)


def registrar(nombre, correo):
    s1, _ = llamar("POST", "/api/auth/register", {"name": nombre, "email": correo, "password": CONTRASENA})
    codigo = api._otp_registro._pendientes.get(correo, {}).get("code")
    s2, d2 = llamar("POST", "/api/auth/verify", {"email": correo, "code": codigo})
    return s1, s2, (d2 or {}).get("token")


def iniciar_sesion(correo, password):
    s1, d1 = llamar("POST", "/api/auth/login", {"email": correo, "password": password})
    if s1 != 200:
        return s1, None, None
    codigo = api._otp_login._pendientes.get(correo, {}).get("code")
    s2, d2 = llamar("POST", "/api/auth/login/verify", {"email": correo, "code": codigo})
    return s1, s2, (d2 or {}).get("token")


def conf_nc008():
    v = Verificacion("CONF-NC-008", "NC-008", "El token emitido por la API se acepta en las rutas protegidas")
    s1, s2, token = registrar("Laura Gómez", "laura.gomez.qa@example.com")
    v.verificar("Registro y verificación OTP entregan un token", s1 == 200 and s2 == 201 and token, f"HTTP {s1} y {s2}")
    s, d = llamar("GET", "/api/auth/me", token=token)
    v.verificar("GET /api/auth/me con el token del registro responde 200 (antes: 401)",
                s == 200 and (d or {}).get("email") == "laura.gomez.qa@example.com", f"HTTP {s} {d}")
    l1, l2, token2 = iniciar_sesion("laura.gomez.qa@example.com", CONTRASENA)
    v.verificar("Inicio de sesión en dos pasos entrega un token", l1 == 200 and l2 == 200 and token2, f"HTTP {l1} y {l2}")
    s, d = llamar("GET", "/api/auth/me", token=token2)
    v.verificar("GET /api/auth/me con el token del inicio de sesión responde 200", s == 200, f"HTTP {s} {d}")
    s, _ = llamar("GET", "/api/auth/me", token=token2[:-2] + "AA")
    v.verificar("Un token con la firma alterada se rechaza con 401", s == 401, f"HTTP {s}")
    v.cerrar()


def conf_nc001():
    v = Verificacion("CONF-NC-001", "NC-001", "Las contraseñas se guardan con bcrypt, costo 12 y sal aleatoria")
    registrar("Andrea Dueña", "duena.a@example.com")
    registrar("Bruno Usuario", "usuario.b@example.com")
    filas = dict(sql("SELECT correo, password_hash FROM usuarios WHERE correo IN (%s, %s, %s)",
                     ("laura.gomez.qa@example.com", "duena.a@example.com", "usuario.b@example.com")))
    h = filas.get("laura.gomez.qa@example.com", "")
    v.verificar("El hash tiene formato bcrypt: prefijo $2b$12$ y 60 caracteres (antes: 64 de SHA-256)",
                h.startswith("$2b$12$") and len(h) == 60, f"prefijo '{h[:7]}', longitud {len(h)}")
    v.verificar("El valor no coincide con el SHA-256 sin sal de la contraseña",
                h != hashlib.sha256(CONTRASENA.encode()).hexdigest(), "no coincide")
    v.verificar("Tres usuarios con la misma contraseña tienen hashes distintos (sal aleatoria)",
                len(set(filas.values())) == 3, f"{len(set(filas.values()))} hashes distintos de {len(filas)}")
    v.cerrar()


def conf_migracion():
    v = Verificacion("CONF-NC-001-MIG", "NC-001", "Las cuentas antiguas con SHA-256 migran a bcrypt al iniciar sesión")
    heredado = hashlib.sha256(CONTRASENA.encode()).hexdigest()
    for correo in ("cuenta.antigua@example.com", "cuenta.antigua2@example.com"):
        sql("INSERT INTO usuarios (nombres, apellidos, correo, password_hash, estado, verificado, acepta_datos) "
            "VALUES ('Cuenta', 'Antigua', %s, %s, 'activo', 1, 1)", (correo, heredado))
    v.log("Se crearon dos cuentas con el hash SHA-256 que guardaba el sistema anterior.")
    s, _, _ = iniciar_sesion("cuenta.antigua2@example.com", "Contrasena-equivocada1")
    h2 = sql("SELECT password_hash FROM usuarios WHERE correo = 'cuenta.antigua2@example.com'")[0][0]
    v.verificar("Con la contraseña equivocada: 401 y el hash no se modifica", s == 401 and h2 == heredado,
                f"HTTP {s}; hash {'sin cambios' if h2 == heredado else 'modificado'}")
    l1, l2, token = iniciar_sesion("cuenta.antigua@example.com", CONTRASENA)
    v.verificar("Con la contraseña correcta, la cuenta antigua inicia sesión", l1 == 200 and l2 == 200 and token,
                f"HTTP {l1} y {l2}")
    h = sql("SELECT password_hash FROM usuarios WHERE correo = 'cuenta.antigua@example.com'")[0][0]
    v.verificar("El hash quedó migrado a bcrypt", h.startswith("$2b$12$") and len(h) == 60, f"prefijo '{h[:7]}', longitud {len(h)}")
    l1, l2, _ = iniciar_sesion("cuenta.antigua@example.com", CONTRASENA)
    v.verificar("Después de migrar, el inicio de sesión sigue funcionando", l1 == 200 and l2 == 200, f"HTTP {l1} y {l2}")
    v.cerrar()


def conf_consola():
    v = Verificacion("CONF-NC-001-CON", "NC-001", "El módulo de consola también guarda las contraseñas con bcrypt")
    respuestas = iter(["Carlos", "Consola QA", "consola.qa@example.com", "", CONTRASENA])
    original = builtins.input
    builtins.input = lambda _="": next(respuestas)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            MenuUsuarios()._registrar_usuario()
    finally:
        builtins.input = original
    filas = sql("SELECT password_hash FROM usuarios WHERE correo = 'consola.qa@example.com'")
    h = filas[0][0] if filas else ""
    v.verificar("El usuario registrado desde la consola tiene hash bcrypt (antes: SHA-256)",
                h.startswith("$2b$12$") and len(h) == 60, f"prefijo '{h[:7]}', longitud {len(h)}")
    v.cerrar()


if __name__ == "__main__":
    inicio = datetime.now()
    try:
        for prueba in (conf_nc008, conf_nc001, conf_migracion, conf_consola):
            try:
                prueba()
            except Exception:
                traza = traceback.format_exc()
                print(traza, file=sys.__stdout__)
                RESULTADOS.append({"id": prueba.__name__, "resultado": "ERROR DE EJECUCIÓN", "traza": traza})
    finally:
        try:
            api._conexion_bd.cerrar_conexion()
        except Exception:
            pass
        eliminar_bd()
        print(f"Base {QA} eliminada.", flush=True)
        with open(os.path.join(AQUI, "resultados.json"), "w", encoding="utf-8") as f:
            json.dump({"inicio": f"{inicio:%d/%m/%Y %H:%M:%S}", "fin": f"{datetime.now():%d/%m/%Y %H:%M:%S}",
                       "verificaciones": RESULTADOS}, f, ensure_ascii=False, indent=2)
        print("\nRESUMEN", flush=True)
        for r in RESULTADOS:
            print(f"  {r['id']}: {r['resultado']}", flush=True)
