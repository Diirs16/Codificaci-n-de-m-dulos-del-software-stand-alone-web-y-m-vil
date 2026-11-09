"""
Ítem 4.12 de PRIORIDADES (NC-003, A-11): repite la prueba de carga CP-008 / CP-017
después del pool de conexiones (4.5), los OTP en la BD (4.6) y la paginación con
índices (4.17).

Qué hace (solo al ejecutarlo; importar este archivo no toca la base ni lee el .env):
  1. Crea una base temporal "petconnect_carga" con sql/schema.sql y seed.py
     (12 productos, 6 mascotas en adopción y la cuenta inventada del refugio).
     Si ya existe, se detiene SIN borrarla. Nunca toca la base "petconnect".
  2. Levanta la API con Werkzeug y un hilo por petición (el mismo servidor de
     `python api.py` y de la medición del 5/10/2026) en el puerto 5055, con un pool
     de 10 conexiones.
  3. Corre los escalones de 500, 1000 y 1500 usuarios, con 50 usuarios nuevos por
     segundo. Cada usuario hace 3 peticiones (el 5/10/2026 eran 2: el catálogo
     completo y el detalle de una mascota):
       GET /api/productos?pagina=1&por_pagina=50
       GET /api/mascotas/adopcion?pagina=1&por_pagina=12
       espera 1 s
       GET /api/mascotas/{id de una mascota en adopción}
     Cada petición espera como máximo 30 s, como antes.
  4. Después de cada escalón mide cuánto tarda la API en volver a responder 200
     (RR01 pide recuperarse en 5 min como máximo después del estrés de 1500).
  5. Borra la base temporal siempre (finally) y deja resultados.json y
     carga_nc003.log en esta carpeta.

Solo escribe métricas: nunca imprime DB_CONFIG, claves ni otros valores del .env.
El .env solo se usa para conectarse a MariaDB y para la FERNET_KEY; DB_NAME,
JWT_SECRET (desechable), DB_POOL_SIZE y el correo se fijan aquí antes de importar
la configuración (load_dotenv no pisa lo que ya está definido).

Criterios (bitácora GA9):
  - 500 usuarios: p95 de cada acción ≤ 2 s y error < 1 % (RNF04).
  - 1000 usuarios: p95 de cada acción ≤ 5 s y error < 1 % (RR01).
  - 1500 usuarios: estrés; solo se exige volver a responder 200 en ≤ 5 min (RR01).

Limitación: el generador de carga y la API corren en el mismo computador y compiten
por la CPU. CP-017 con JMeter en staging queda para la Fase 5.

Ejecutar desde la raíz Evidecia (la API normal puede seguir encendida en el 5000):
    .venv\\Scripts\\python.exe Documentacion\\Evidencias-4.12-carga\\carga_nc003.py
    .venv\\Scripts\\python.exe Documentacion\\Evidencias-4.12-carga\\carga_nc003.py --usuarios 500
"""
import argparse
import contextlib
import io
import json
import logging
import math
import os
import platform
import random
import secrets
import sys
import threading
import time
import traceback
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", ".."))
BACKEND = os.path.join(RAIZ, "petconnect.Backend")
RUTA_ESQUEMA = os.path.join(BACKEND, "sql", "schema.sql")
RUTA_RESULTADOS = os.path.join(AQUI, "resultados.json")
RUTA_LOG = os.path.join(AQUI, "carga_nc003.log")

BD_CARGA = "petconnect_carga"
PUERTO = 5055
URL = f"http://127.0.0.1:{PUERTO}"
TAMANO_POOL = "10"                # decisión del dueño en el 4.5; fijo para poder comparar
TIMEOUT_S = 30                    # igual que el 5/10/2026
USUARIOS_POR_SEGUNDO = 50         # 500 usuarios en 10 s, como la rampa del 5/10/2026
ESCALONES = (500, 1000, 1500)
PAUSA_USUARIO_S = 1
RECUPERACION_MAXIMA_S = 300       # RR01: recuperación ≤ 5 min
PAUSA_ENTRE_ESCALONES_S = 15
MAX_AVISOS_EN_LOG = 50            # los avisos del servidor se cuentan todos, pero solo se copian 50

RUTA_PRODUCTOS = "/api/productos?pagina=1&por_pagina=50"
RUTA_ADOPCION = "/api/mascotas/adopcion?pagina=1&por_pagina=12"
ACCIONES = ("productos", "adopcion", "detalle_mascota")

# AA2, CP-008 (Documentacion/Evidencias-GA9-AA2-EV01/resultados.json). Solo para comparar.
MEDICION_5_10_2026 = {
    "fecha": "05/10/2026",
    "usuarios": 500,
    "peticiones_por_usuario": 2,
    "escenario": "GET /api/productos (catálogo completo), espera 1 s, GET /api/mascotas/{id}",
    "servidor": "Werkzeug threaded, puerto 5055, una sola conexión compartida",
    "solicitudes": 1000,
    "exitosas": 440,
    "tasa_error_pct": 56.0,
    "p50_s": 0.103,
    "p95_s": 30.016,
    "max_s": 30.04,
    "rendimiento_rps": 14.2,
    "errores": {"TimeoutError": 396, "500": 161, "404": 3},
}

LIMITACIONES = [
    "El generador de carga y la API corren en el mismo computador: compiten por la CPU, "
    "así que los tiempos son una cota pesimista y no reemplazan CP-017 en staging con JMeter (Fase 5).",
    "Servidor de desarrollo Werkzeug con un hilo por petición (el mismo del 5/10/2026); "
    "Gunicorn es el ítem 5.2.",
    "Base temporal con los datos de seed.py (12 productos y 6 mascotas), no con el volumen de producción.",
    "Escenario de solo lectura (catálogo, adopción y ficha); el registro y el login no se cargan aquí.",
]


# ---------------------------------------------------------------------------
# Cálculos (funciones puras: se pueden probar sin base de datos ni servidor)
# ---------------------------------------------------------------------------
def percentil(valores, p):
    """Percentil por rango más cercano (el mismo cálculo de pruebas_aa2.py)."""
    ordenados = sorted(valores)
    if not ordenados:
        return None
    return ordenados[max(0, math.ceil(p / 100 * len(ordenados)) - 1)]


def _redondear(valor, decimales=3):
    return None if valor is None else round(valor, decimales)


def tipo_de_error(excepcion):
    """Nombre corto de un fallo de red (TimeoutError, ConnectionResetError...), sin su mensaje."""
    if isinstance(excepcion, urllib.error.URLError) and isinstance(excepcion.reason, BaseException):
        excepcion = excepcion.reason
    return type(excepcion).__name__


def _tiempos(muestras):
    tiempos = [m[2] for m in muestras]
    return {
        "p50_s": _redondear(percentil(tiempos, 50)),
        "p95_s": _redondear(percentil(tiempos, 95)),
        "p99_s": _redondear(percentil(tiempos, 99)),
        "max_s": _redondear(max(tiempos)),
        "promedio_s": _redondear(sum(tiempos) / len(tiempos)),
    }


def resumen_carga(muestras, duracion):
    """
    Métricas de un escalón. Cada muestra es (acción, código, segundos, cuerpo del error).
    El código es el número HTTP o el nombre del fallo de red. Solo 200 cuenta como éxito.
    """
    if not muestras:
        return {"solicitudes": 0, "exitosas": 0, "tasa_error_pct": 100.0, "por_accion": {}, "errores": {}}
    exitosas = sum(1 for m in muestras if m[1] == 200)
    errores = Counter(str(m[1]) for m in muestras if m[1] != 200)
    cuerpos = Counter(m[3] for m in muestras if isinstance(m[1], int) and m[1] >= 500 and m[3])
    por_accion = {}
    for accion in ACCIONES:
        de_la_accion = [m for m in muestras if m[0] == accion]
        if de_la_accion:
            ok = sum(1 for m in de_la_accion if m[1] == 200)
            por_accion[accion] = {"solicitudes": len(de_la_accion), "exitosas": ok, **_tiempos(de_la_accion)}
    duracion = max(duracion, 0.001)
    return {
        "solicitudes": len(muestras),
        "exitosas": exitosas,
        "tasa_error_pct": round(100 * (len(muestras) - exitosas) / len(muestras), 2),
        **_tiempos(muestras),
        "duracion_s": round(duracion, 1),
        "rendimiento_rps": round(len(muestras) / duracion, 1),
        "por_accion": por_accion,
        "errores": dict(errores.most_common()),
        "errores_5xx": dict(cuerpos.most_common(3)),
    }


def criterio(usuarios):
    """Qué se le exige a cada escalón (bitácora GA9: RNF04 y RR01)."""
    if usuarios <= 500:
        return {"nombre": "RNF04 (carga normal)", "umbral_p95_s": 2.0, "error_max_pct": 1.0}
    if usuarios <= 1000:
        return {"nombre": "RR01 (carga pico)", "umbral_p95_s": 5.0, "error_max_pct": 1.0}
    return {"nombre": "RR01 (estrés: solo recuperación)", "recuperacion_max_s": RECUPERACION_MAXIMA_S}


def veredicto_carga(usuarios, resumen, recuperacion_s):
    """Aprobado o Fallido según el criterio del escalón, con cada verificación anotada."""
    c = criterio(usuarios)
    verificaciones = []
    if "umbral_p95_s" in c:
        umbral = c["umbral_p95_s"]
        if resumen["por_accion"]:
            accion, datos = max(resumen["por_accion"].items(), key=lambda par: par[1]["p95_s"])
            peor = datos["p95_s"]
            obtenido = f"peor p95 = {peor} s ({accion})"
        else:
            peor, obtenido = None, "sin muestras"
        verificaciones.append({
            "descripcion": f"p95 de cada acción ≤ {umbral} s",
            "ok": peor is not None and peor <= umbral,
            "obtenido": obtenido,
        })
        verificaciones.append({
            "descripcion": f"Tasa de error < {c['error_max_pct']} %",
            "ok": resumen["solicitudes"] > 0 and resumen["tasa_error_pct"] < c["error_max_pct"],
            "obtenido": f"{resumen['tasa_error_pct']} % {resumen['errores']}",
        })
    else:
        maximo = c["recuperacion_max_s"]
        verificaciones.append({
            "descripcion": f"Vuelve a responder 200 en ≤ {maximo} s",
            "ok": recuperacion_s is not None and recuperacion_s <= maximo,
            "obtenido": "no se recuperó" if recuperacion_s is None else f"{recuperacion_s} s",
        })
    resultado = "Aprobado" if all(v["ok"] for v in verificaciones) else "Fallido"
    return {"criterio": c["nombre"], "resultado": resultado, "verificaciones": verificaciones}


def linea_resumen(escalon):
    """Una línea legible con las métricas del escalón (para la consola y el log)."""
    r = escalon
    if not r["solicitudes"]:
        return f"{r['usuarios']} usuarios: sin muestras"
    acciones = ", ".join(f"{a} {d['p95_s']} s" for a, d in r["por_accion"].items())
    texto = (f"{r['usuarios']} usuarios: {r['solicitudes']} solicitudes en {r['duracion_s']} s "
             f"({r['rendimiento_rps']} solicitudes/s); p50 {r['p50_s']} s, p95 {r['p95_s']} s, "
             f"p99 {r['p99_s']} s, máximo {r['max_s']} s; p95 por acción: {acciones}; "
             f"error {r['tasa_error_pct']} %")
    if r["errores"]:
        texto += " (" + ", ".join(f"{k}: {v}" for k, v in r["errores"].items()) + ")"
    recuperacion = r.get("recuperacion_s")
    texto += ". Recuperación: " + ("no respondió 200 en 5 min" if recuperacion is None else f"{recuperacion} s")
    return texto + f". Resultado: {r['veredicto']['resultado']} ({r['veredicto']['criterio']})."


# ---------------------------------------------------------------------------
# Registro (consola + carga_nc003.log)
# ---------------------------------------------------------------------------
_candado_log = threading.Lock()


def anotar(texto, en_consola=True):
    linea = f"[{datetime.now():%H:%M:%S}] {texto}"
    with _candado_log:
        if en_consola:
            print(linea, flush=True)
        with open(RUTA_LOG, "a", encoding="utf-8") as archivo:
            archivo.write(linea + "\n")


class AvisosDelServidor(logging.Handler):
    """
    Cuenta los avisos y errores que registra la API (pool lleno, error 500...) y copia
    los primeros al log. Solo el mensaje formateado y el tipo de excepción: nunca el
    texto de la excepción, que podría traer usuario o host de la BD.
    """

    def __init__(self):
        super().__init__(logging.WARNING)
        self.conteo = Counter()

    def emit(self, record):
        clave = f"{record.name}:{record.levelname}"
        self.conteo[clave] += 1
        if sum(self.conteo.values()) <= MAX_AVISOS_EN_LOG:
            try:
                mensaje = record.getMessage()[:500]
            except Exception:
                mensaje = "(mensaje no legible)"
            if record.exc_info and record.exc_info[0]:
                mensaje += f" [{record.exc_info[0].__name__}]"
            anotar(f"[servidor] {clave} {mensaje}", en_consola=False)


def _pila_sin_mensaje(e):
    """Archivo, línea y función de un error, sin su mensaje (como _registrar_error de api.py)."""
    return "".join(traceback.format_list(traceback.extract_tb(e.__traceback__)))


# ---------------------------------------------------------------------------
# Cliente HTTP y escenario
# ---------------------------------------------------------------------------
def http(ruta, timeout=TIMEOUT_S):
    """(código, segundos, cuerpo del error). El tiempo incluye leer toda la respuesta."""
    peticion = urllib.request.Request(URL + ruta, method="GET")
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(peticion, timeout=timeout) as respuesta:
            respuesta.read()
            return respuesta.status, time.perf_counter() - t0, ""
    except urllib.error.HTTPError as e:
        cuerpo = e.read()[:120].decode("utf-8", "replace").strip()
        return e.code, time.perf_counter() - t0, cuerpo
    except Exception as e:
        return tipo_de_error(e), time.perf_counter() - t0, ""


def http_json(ruta):
    with urllib.request.urlopen(URL + ruta, timeout=TIMEOUT_S) as respuesta:
        return respuesta.status, json.loads(respuesta.read())


def usuario_virtual(ids_mascotas, muestras, candado):
    propias = [("productos", *http(RUTA_PRODUCTOS)), ("adopcion", *http(RUTA_ADOPCION))]
    time.sleep(PAUSA_USUARIO_S)
    propias.append(("detalle_mascota", *http(f"/api/mascotas/{random.choice(ids_mascotas)}")))
    with candado:
        muestras.extend(propias)


def correr_escalon(usuarios, ids_mascotas):
    """Lanza `usuarios` usuarios virtuales a USUARIOS_POR_SEGUNDO y espera que terminen."""
    muestras, candado, hilos = [], threading.Lock(), []
    t0 = time.perf_counter()
    for i in range(usuarios):
        espera = t0 + i / USUARIOS_POR_SEGUNDO - time.perf_counter()
        if espera > 0:
            time.sleep(espera)
        hilo = threading.Thread(target=usuario_virtual, args=(ids_mascotas, muestras, candado), daemon=True)
        hilo.start()
        hilos.append(hilo)
    for hilo in hilos:
        hilo.join()
    return resumen_carga(muestras, time.perf_counter() - t0)


def medir_recuperacion():
    """Segundos hasta el primer 200 de /api/productos (None si no llega en 5 min) e intentos."""
    t0 = time.perf_counter()
    intentos = 0
    while True:
        intentos += 1
        codigo, _, _ = http(RUTA_PRODUCTOS, timeout=10)
        transcurrido = time.perf_counter() - t0
        if codigo == 200:
            return round(transcurrido, 2), intentos
        if transcurrido >= RECUPERACION_MAXIMA_S:
            return None, intentos
        time.sleep(1)


# ---------------------------------------------------------------------------
# Base temporal (conexiones propias, fuera del pool de la API)
# ---------------------------------------------------------------------------
def _sentencias(sql):
    """Quita los comentarios '--' y separa por punto y coma (igual que tests/test_esquema.py)."""
    sin_comentarios = "\n".join(l for l in sql.splitlines() if not l.lstrip().startswith("--"))
    return [s.strip() for s in sin_comentarios.split(";") if s.strip()]


def _conectar(conector, servidor_bd, base=None):
    datos = dict(servidor_bd)
    if base:
        datos["database"] = base
    conexion = conector.connect(**datos)
    conexion.autocommit = True
    return conexion


def _consultar(conector, servidor_bd, sql, params=(), base=None):
    conexion = _conectar(conector, servidor_bd, base)
    try:
        cursor = conexion.cursor()
        try:
            cursor.execute(sql, params)
            return cursor.fetchall()
        finally:
            cursor.close()
    finally:
        conexion.close()


def _ejecutar(conector, servidor_bd, sentencias, base=None):
    conexion = _conectar(conector, servidor_bd, base)
    try:
        cursor = conexion.cursor()
        try:
            for sentencia in sentencias:
                cursor.execute(sentencia)
        finally:
            cursor.close()
    finally:
        conexion.close()


# ---------------------------------------------------------------------------
# Programa principal (solo al ejecutar el archivo)
# ---------------------------------------------------------------------------
def _leer_argumentos(argv):
    lector = argparse.ArgumentParser(description="Prueba de carga del ítem 4.12 (NC-003).")
    lector.add_argument("--usuarios", type=int, nargs="+", default=list(ESCALONES),
                        help="Escalones a medir (por defecto: 500 1000 1500).")
    args = lector.parse_args(argv)
    if any(n < 1 or n > 1500 for n in args.usuarios):
        lector.error("cada escalón debe estar entre 1 y 1500 usuarios")
    return args


def _preparar_entorno():
    """Se fija ANTES de importar config/ o api: load_dotenv no pisa lo que ya existe."""
    os.environ["DB_NAME"] = BD_CARGA
    os.environ["JWT_SECRET"] = secrets.token_hex(32)       # desechable, solo para esta corrida
    os.environ["DB_POOL_SIZE"] = TAMANO_POOL
    os.environ["APP_ENV"] = ""                             # nunca mostrar OTP en consola
    os.environ["FLASK_DEBUG"] = ""
    os.environ["EMAIL_MODE"] = "smtp"                      # sin credenciales: no sale ningún correo
    for variable in ("MAILTRAP_API_TOKEN", "MAILTRAP_SMTP_USER", "MAILTRAP_SMTP_PASS",
                     "GMAIL_USER", "GMAIL_APP_PASSWORD"):
        os.environ[variable] = ""
    sys.path.insert(0, BACKEND)


def main(argv=None):
    args = _leer_argumentos(argv)
    with contextlib.suppress(AttributeError, ValueError):
        sys.stdout.reconfigure(errors="replace")           # una consola sin UTF-8 no rompe la prueba
    _preparar_entorno()

    avisos = AvisosDelServidor()
    logging.getLogger().addHandler(avisos)                 # antes de importar api: Flask no pone el suyo
    logging.getLogger("werkzeug").setLevel(logging.ERROR)  # sin una línea por petición

    import mysql.connector
    from config.db_config import DB_CONFIG

    if DB_CONFIG["database"] != BD_CARGA:                  # nunca la base "petconnect"
        print(f"La configuración no apunta a {BD_CARGA}; el script se detiene.")
        return 1
    servidor_bd = {k: v for k, v in DB_CONFIG.items() if k != "database"}

    try:
        ya_existe = _consultar(mysql.connector, servidor_bd, "SHOW DATABASES LIKE %s", (BD_CARGA,))
    except mysql.connector.Error as e:
        # Solo el tipo y el número: el mensaje de MySQL puede traer usuario, host o puerto
        print(f"No se pudo conectar a MariaDB ({type(e).__name__} {e.errno}). ¿Está encendido XAMPP?")
        return 1
    if ya_existe:
        print(f"La base {BD_CARGA} ya existe; el script se detiene para no borrar datos que no creó.")
        return 1

    with open(RUTA_LOG, "w", encoding="utf-8"):
        pass                                               # log nuevo en cada corrida
    inicio = datetime.now()
    resultados = {
        "item": "4.12", "no_conformidad": "NC-003", "casos": ["CP-008", "CP-017"],
        "estado": "en curso",
        "ambiente": {
            "fecha": f"{inicio:%d/%m/%Y}", "inicio": f"{inicio:%H:%M:%S}",
            "python": platform.python_version(), "sistema": platform.platform(), "cpus": os.cpu_count(),
            "servidor": f"Werkzeug con un hilo por petición, puerto {PUERTO}",
            "pool_conexiones": int(TAMANO_POOL), "base": f"{BD_CARGA} (temporal, schema.sql + seed.py)",
        },
        "escenario": {
            "peticiones_por_usuario": 3,
            "nota": "El 5/10/2026 eran 2 peticiones por usuario (catálogo completo y detalle de una mascota).",
            "pasos": [f"GET {RUTA_PRODUCTOS}", f"GET {RUTA_ADOPCION}", f"espera {PAUSA_USUARIO_S} s",
                      "GET /api/mascotas/{id} (mascota en adopción al azar)"],
            "usuarios_nuevos_por_segundo": USUARIOS_POR_SEGUNDO, "timeout_s": TIMEOUT_S,
            "escalones": args.usuarios,
        },
        "criterios": {str(n): criterio(n) for n in args.usuarios},
        "escalones": [],
        "medicion_anterior_5_10_2026": MEDICION_5_10_2026,
        "limitaciones": LIMITACIONES,
    }

    creada, servidor, codigo_salida = False, None, 0
    try:
        anotar(f"Creando la base temporal {BD_CARGA} con schema.sql...")
        _ejecutar(mysql.connector, servidor_bd,
                  [f"CREATE DATABASE `{BD_CARGA}` CHARACTER SET utf8mb4 COLLATE utf8mb4_spanish_ci"])
        creada = True                                      # desde aquí el finally la borra
        with open(RUTA_ESQUEMA, encoding="utf-8") as archivo:
            _ejecutar(mysql.connector, servidor_bd, _sentencias(archivo.read()), base=BD_CARGA)

        import seed
        with contextlib.redirect_stdout(io.StringIO()):
            seed.seed()
        ids_mascotas = [fila[0] for fila in _consultar(
            mysql.connector, servidor_bd,
            "SELECT id_mascota FROM mascotas WHERE estado = %s ORDER BY id_mascota", ("en_adopcion",), BD_CARGA)]
        productos = _consultar(mysql.connector, servidor_bd,
                               "SELECT COUNT(*) FROM productos WHERE activo = TRUE", base=BD_CARGA)[0][0]
        version_bd = _consultar(mysql.connector, servidor_bd, "SELECT VERSION()")[0][0]
        resultados["ambiente"]["bd_version"] = version_bd
        anotar(f"Base lista: {productos} productos activos y {len(ids_mascotas)} mascotas en adopción.")
        if not ids_mascotas:
            raise RuntimeError("seed.py no dejó mascotas en adopción")

        import api
        if not api._preparar_otp() or not api._preparar_sesiones():
            raise RuntimeError("la base temporal no tiene las tablas que la API revisa al arrancar")

        from werkzeug.serving import make_server
        servidor = make_server("127.0.0.1", PUERTO, api.app, threaded=True)
        threading.Thread(target=servidor.serve_forever, daemon=True).start()

        estado, lista = http_json(RUTA_PRODUCTOS)
        estado2, lista2 = http_json(RUTA_ADOPCION)
        anotar(f"API en {URL}: /api/productos -> {estado} ({len(lista)}), "
               f"/api/mascotas/adopcion -> {estado2} ({len(lista2)}). Pool de {TAMANO_POOL} conexiones.")

        for numero, usuarios in enumerate(args.usuarios):
            if numero:
                time.sleep(PAUSA_ENTRE_ESCALONES_S)
            antes = Counter(avisos.conteo)
            anotar(f"Escalón de {usuarios} usuarios ({usuarios / USUARIOS_POR_SEGUNDO:.0f} s de rampa)...")
            escalon = {"usuarios": usuarios, **correr_escalon(usuarios, ids_mascotas)}
            anotar("  Midiendo la recuperación (primer 200 de /api/productos)...")
            recuperacion, intentos = medir_recuperacion()
            escalon["recuperacion_s"] = recuperacion
            escalon["intentos_recuperacion"] = intentos
            escalon["avisos_servidor"] = dict(avisos.conteo - antes)
            escalon["veredicto"] = veredicto_carga(usuarios, escalon, recuperacion)
            resultados["escalones"].append(escalon)
            anotar("  " + linea_resumen(escalon))
            if escalon["avisos_servidor"]:
                anotar(f"  Avisos de la API: {escalon['avisos_servidor']}")
        resultados["estado"] = "completo"
    except (Exception, KeyboardInterrupt) as e:
        codigo_salida = 1
        resultados["estado"] = f"interrumpido ({type(e).__name__})"
        anotar(f"La prueba se interrumpió: {type(e).__name__}\n{_pila_sin_mensaje(e)}")
    finally:
        if servidor is not None:
            servidor.shutdown()
        try:
            from conexion.conexion_bd import ConexionBD
            ConexionBD().cerrar_conexion()
        except Exception:
            pass
        if creada:
            try:
                _ejecutar(mysql.connector, servidor_bd, [f"DROP DATABASE IF EXISTS `{BD_CARGA}`"])
                anotar(f"Base temporal {BD_CARGA} eliminada.")
            except Exception as e:
                codigo_salida = 1
                anotar(f"No se pudo borrar {BD_CARGA} ({type(e).__name__}): bórrala a mano con "
                       f"DROP DATABASE {BD_CARGA};")
        resultados["ambiente"]["fin"] = f"{datetime.now():%H:%M:%S}"
        with open(RUTA_RESULTADOS, "w", encoding="utf-8") as archivo:
            json.dump(resultados, archivo, ensure_ascii=False, indent=2)

    print("\nRESUMEN", flush=True)
    for escalon in resultados["escalones"]:
        print(f"  {escalon['usuarios']} usuarios: {escalon['veredicto']['resultado']} "
              f"({escalon['veredicto']['criterio']})", flush=True)
    print(f"  Estado: {resultados['estado']}. Detalle en {RUTA_RESULTADOS}", flush=True)
    return codigo_salida


if __name__ == "__main__":
    sys.exit(main())
