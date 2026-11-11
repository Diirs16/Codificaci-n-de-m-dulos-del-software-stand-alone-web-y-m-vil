"""
Pruebas del item 5.5 de PRIORIDADES (la API alojada en Railway, antes de Vercel).

Lo que revisan, sin base de datos, sin red y sin leer ningun .env:
- _origenes_cors(): CORS_ORIGENES vacia = los origenes de desarrollo (ahora con
  el 8090 del export web del movil); con valores los REEMPLAZA; rechaza "*",
  http:// hacia afuera, rutas y usuario:clave@, y el aviso no imprime el valor.
- La API responde el CORS segun esa lista (tambien con la variable puesta, en
  un proceso aparte para no reimportar api.py en este).
- _ip_cliente() con PROXY_CONFIABLE=x-real-ip (Railway): cuenta por X-Real-IP;
  sin ese valor el encabezado se ignora (cualquiera podria inventarlo).
- correo/servicio.py: la conexion SMTP tiene tiempo maximo (puerto bloqueado).
- Dockerfile.bd: la misma MariaDB del compose con schema.sql adentro y sin secretos.

Los dominios e IP son inventados (.test, .example y RFC 5737).

Ejecutar desde petconnect.Backend, con el entorno virtual activo:
    python -m unittest discover -s tests -v
"""
import io
import json
import os
import re
import subprocess
import sys
import unittest
from contextlib import redirect_stderr
from unittest import mock

CARPETA_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, CARPETA_BACKEND)

from test_errores import _importar_api  # noqa: E402
from test_docker_compose import RUTA_COMPOSE, leer_yaml_simple  # noqa: E402

WEB_VERCEL = "https://petconnect-git-main-ejemplo.vercel.app"   # inventada
OTRA_WEB = "https://petconnect.example"
LOCALES = {"http://localhost:5173", "http://localhost:8081",
           "http://localhost:19006", "http://localhost:8090"}

LIMITE = 5
IP_BORDE = "100.64.0.9"        # la IP con la que el borde de Railway llega a la API
IP_ANA = "203.0.113.10"
IP_BETO = "203.0.113.20"
IP_INVENTADA = "198.51.100.7"


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
class PruebasOrigenesCors(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.api = _importar_api()

    def _origenes(self, texto):
        with redirect_stderr(io.StringIO()):
            return self.api._origenes_cors(texto)

    def test_sin_variable_quedan_los_de_desarrollo_con_el_8090(self):
        for texto in (None, "", "   ", " , "):
            with self.subTest(texto=texto):
                self.assertEqual(set(self._origenes(texto)), LOCALES)

    def test_con_valores_reemplazan_a_los_de_desarrollo(self):
        self.assertEqual(self._origenes(f"{WEB_VERCEL}, {OTRA_WEB}"), [WEB_VERCEL, OTRA_WEB])
        self.assertEqual(self._origenes(WEB_VERCEL), [WEB_VERCEL])

    def test_acepta_la_barra_final_mayusculas_y_puerto(self):
        self.assertEqual(self._origenes(WEB_VERCEL + "/"), [WEB_VERCEL])
        self.assertEqual(self._origenes(WEB_VERCEL.upper()), [WEB_VERCEL])
        self.assertEqual(self._origenes("https://petconnect.example:8443"),
                         ["https://petconnect.example:8443"])
        self.assertEqual(self._origenes("http://localhost:4173"), ["http://localhost:4173"])

    def test_rechaza_origenes_peligrosos_o_mal_escritos(self):
        malos = (
            "*",                                    # cualquiera
            "https://*.vercel.app",                 # comodin
            "http://petconnect.example",            # sin cifrar hacia afuera
            "petconnect.example",                   # sin esquema
            "https://petconnect.example/api",       # con ruta
            "https://usuario:clave@petconnect.example",
            "https://petconnect.example?x=1",
            "https://petconnect example",
            "ftp://petconnect.example",
            "http://localhost.example",             # parece local y no lo es
        )
        for malo in malos:
            with self.subTest(origen=malo):
                self.assertEqual(self._origenes(malo), [])
                self.assertEqual(self._origenes(f"{malo},{WEB_VERCEL}"), [WEB_VERCEL])

    def test_el_aviso_dice_la_posicion_y_no_el_valor(self):
        salida = io.StringIO()
        with redirect_stderr(salida):
            self.api._origenes_cors(f"{WEB_VERCEL},http://secreto-inventado.example")
        aviso = salida.getvalue()
        self.assertIn("CORS_ORIGENES", aviso)
        self.assertIn("2", aviso)
        self.assertNotIn("secreto-inventado", aviso)


class PruebasCorsEnLaApi(unittest.TestCase):
    """Lo que ve el navegador: el encabezado Access-Control-Allow-Origin."""

    @classmethod
    def setUpClass(cls):
        cls.api = _importar_api()
        cls.cliente = cls.api.app.test_client()

    def _permitido(self, origen):
        r = self.cliente.options("/api/auth/login", headers={
            "Origin": origen, "Access-Control-Request-Method": "POST"})
        return r.headers.get("Access-Control-Allow-Origin")

    def test_sin_variable_responde_a_los_de_desarrollo(self):
        # La CI y tu computador corren sin CORS_ORIGENES
        if os.getenv("CORS_ORIGENES", "").strip():
            self.skipTest("CORS_ORIGENES esta definida en este entorno")
        for origen in sorted(LOCALES):
            with self.subTest(origen=origen):
                self.assertEqual(self._permitido(origen), origen)
        self.assertIsNone(self._permitido(OTRA_WEB))

    def test_con_la_variable_responde_solo_a_esa_web(self):
        # api.py lee CORS_ORIGENES al importarse: se prueba en otro proceso, con
        # load_dotenv apagado (nunca el .env real) y claves inventadas.
        guion = (
            "import json, sys, dotenv\n"
            "dotenv.load_dotenv = lambda *a, **k: False\n"
            f"sys.path.insert(0, {CARPETA_BACKEND!r})\n"
            "import api\n"
            "c = api.app.test_client()\n"
            "def ver(o):\n"
            "    r = c.options('/api/auth/login', headers={'Origin': o,"
            " 'Access-Control-Request-Method': 'POST'})\n"
            "    return r.headers.get('Access-Control-Allow-Origin')\n"
            f"print(json.dumps([ver({WEB_VERCEL!r}), ver('http://localhost:5173'),"
            f" ver({OTRA_WEB!r})]))\n"
        )
        entorno = {k: v for k, v in os.environ.items() if not k.startswith(("DB_", "CORS_"))}
        entorno["CORS_ORIGENES"] = WEB_VERCEL + "/"
        resultado = subprocess.run([sys.executable, "-c", guion], cwd=CARPETA_BACKEND,
                                   env=entorno, capture_output=True, text=True, timeout=120)
        self.assertEqual(resultado.returncode, 0, "el proceso de prueba fallo")
        ultima = resultado.stdout.strip().splitlines()[-1]
        self.assertEqual(json.loads(ultima), [WEB_VERCEL, None, None])


# ---------------------------------------------------------------------------
# IP real detras de Railway
# ---------------------------------------------------------------------------
class PruebasIpRealEnRailway(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.api = _importar_api()
        cls.cliente = cls.api.app.test_client()

    def setUp(self):
        parches = (
            mock.patch.object(self.api._conexion_bd, "obtener_conexion", return_value=None),
            mock.patch.object(self.api, "enviar_codigo"),
        )
        for parche in parches:
            parche.start()
            self.addCleanup(parche.stop)
        self.api.limiter.enabled = True
        self.api.limiter.reset()
        self.addCleanup(self.api.limiter.reset)
        self.addCleanup(setattr, self.api.limiter, "enabled", False)

    def _proxy(self, valor):
        parche = mock.patch.dict(os.environ, {"PROXY_CONFIABLE": valor})
        parche.start()
        self.addCleanup(parche.stop)

    def _login(self, real=None, reenviada=None):
        cabeceras = {}
        if real is not None:
            cabeceras["X-Real-IP"] = real
        if reenviada is not None:
            cabeceras["X-Forwarded-For"] = reenviada
        # Cuerpo vacio: 400 sin tocar BD ni correo; el limite se cuenta antes
        return self.cliente.post("/api/auth/login", json={}, headers=cabeceras,
                                 environ_base={"REMOTE_ADDR": IP_BORDE}).status_code

    def test_dos_personas_no_se_bloquean_entre_si(self):
        # Sin esto todas contarian como la IP del borde de Railway
        for valor in ("x-real-ip", "X-Real-IP", " x-real-ip "):
            with self.subTest(PROXY_CONFIABLE=valor):
                self.api.limiter.reset()
                self._proxy(valor)
                for _ in range(LIMITE):
                    self.assertNotEqual(self._login(IP_ANA), 429)
                self.assertEqual(self._login(IP_ANA), 429)
                self.assertNotEqual(self._login(IP_BETO), 429)

    def test_x_forwarded_for_no_cuenta_en_railway(self):
        # Con x-real-ip, cambiar X-Forwarded-For en cada intento no salta el limite
        self._proxy("x-real-ip")
        for i in range(LIMITE):
            self._login(IP_ANA, reenviada=f"198.51.100.{i + 1}")
        self.assertEqual(self._login(IP_ANA, reenviada=IP_INVENTADA), 429)

    def test_sin_x_real_ip_valida_cuenta_la_ip_que_se_conecta(self):
        self._proxy("x-real-ip")
        for valor in ("", "no-es-una-ip", "203.0.113.10, 198.51.100.7"):
            with self.subTest(x_real_ip=valor):
                self.api.limiter.reset()
                for _ in range(LIMITE):
                    self._login(valor)
                # Todas contaron como IP_BORDE: el siguiente sin encabezado tambien
                self.assertEqual(self._login(), 429)

    def test_sin_ese_valor_x_real_ip_se_ignora(self):
        # En tu PC o detras de nginx, un X-Real-IP inventado no salta el limite
        for valor in ("", "0", "1", "si", "x-forwarded-for"):
            with self.subTest(PROXY_CONFIABLE=valor):
                self.api.limiter.reset()
                with mock.patch.dict(os.environ, {"PROXY_CONFIABLE": valor}):
                    for i in range(LIMITE):
                        self._login(f"198.51.100.{i + 1}")
                    self.assertEqual(self._login(IP_INVENTADA), 429)


# ---------------------------------------------------------------------------
# Correo: tiempo maximo
# ---------------------------------------------------------------------------
class PruebasTiempoMaximoSmtp(unittest.TestCase):

    def test_la_conexion_smtp_tiene_tiempo_maximo(self):
        from correo import servicio
        config = {"mode": "gmail", "gmail_user": "remitente@ejemplo.test",
                  "gmail_app_password": "clave-inventada"}
        with mock.patch.dict(servicio.EMAIL_CONFIG, config), \
                mock.patch.object(servicio.smtplib, "SMTP") as smtp:
            servicio.enviar_correo("destino@ejemplo.test", "Asunto", "Texto", "<p>Hola</p>")
        tiempo = smtp.call_args.kwargs.get("timeout")
        self.assertIsNotNone(tiempo, "sin timeout un puerto bloqueado deja el hilo esperando")
        # Menos que el limite de Gunicorn (30 s en gunicorn.conf.py)
        self.assertGreater(tiempo, 0)
        self.assertLess(tiempo, 30)


# ---------------------------------------------------------------------------
# Dockerfile.bd
# ---------------------------------------------------------------------------
def _instrucciones(ruta):
    with open(ruta, encoding="utf-8") as archivo:
        texto = archivo.read().replace("\\\n", " ")
    salida = []
    for linea in texto.splitlines():
        linea = linea.strip()
        if linea and not linea.startswith("#"):
            palabra, _, resto = linea.partition(" ")
            salida.append((palabra.upper(), resto.strip()))
    return salida


class PruebasDockerfileBd(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.instrucciones = _instrucciones(os.path.join(CARPETA_BACKEND, "Dockerfile.bd"))
        with open(RUTA_COMPOSE, encoding="utf-8") as archivo:
            cls.db = leer_yaml_simple(archivo.read())["services"]["db"]

    def _de(self, palabra):
        return [resto for p, resto in self.instrucciones if p == palabra]

    def test_misma_imagen_que_el_compose(self):
        self.assertEqual(self._de("FROM"), [self.db["image"]])

    def test_carga_solo_schema_sql_al_arrancar_vacia(self):
        self.assertEqual(self._de("COPY"),
                         ["sql/schema.sql /docker-entrypoint-initdb.d/01-schema.sql"])
        self.assertTrue(os.path.isfile(os.path.join(CARPETA_BACKEND, "sql", "schema.sql")))

    def test_mismo_juego_de_caracteres_que_el_compose(self):
        (cmd,) = self._de("CMD")
        self.assertEqual(json.loads(cmd), ["mariadbd"] + list(self.db["command"]))

    def test_la_base_se_llama_petconnect_y_no_hay_secretos(self):
        self.assertIn("MARIADB_DATABASE=petconnect", self._de("ENV"))
        for palabra, resto in self.instrucciones:
            if palabra in ("ENV", "ARG", "LABEL"):
                with self.subTest(instruccion=f"{palabra} {resto}"):
                    self.assertNotRegex(resto, re.compile(r"PASSWORD|SECRET|KEY|TOKEN|USER",
                                                          re.IGNORECASE))

    def test_el_dockerignore_no_deja_fuera_el_esquema(self):
        with open(os.path.join(CARPETA_BACKEND, ".dockerignore"), encoding="utf-8") as archivo:
            reglas = [l.strip() for l in archivo if l.strip() and not l.startswith("#")]
        for regla in reglas:
            with self.subTest(regla=regla):
                self.assertNotRegex(regla, r"(^|/)\*?sql")


if __name__ == "__main__":
    unittest.main()
