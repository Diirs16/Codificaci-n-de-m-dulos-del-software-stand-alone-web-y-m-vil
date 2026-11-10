"""
Pruebas de regresion de A-30 (item 5.2 de PRIORIDADES, parte 1: backend en Docker).

Lo que revisan, sin Docker ni base de datos (corren en Windows y en la CI):
- _host_api(): "python api.py" sigue escuchando solo en 127.0.0.1 salvo que
  API_HOST diga otra cosa (antes app.run no tenia host: imposible abrirla).
- _ip_cliente(): detras de nginx (PROXY_CONFIABLE=1) el limite de peticiones
  cuenta por la IP real de cada persona, no por la de nginx; sin esa variable el
  encabezado X-Forwarded-For se ignora (si no, cualquiera se salta el limite).
- preparar_arranque(): las revisiones que antes estaban sueltas en el bloque
  __main__ (que Gunicorn nunca ejecuta) ahora estan en una funcion.
- gunicorn.conf.py: 0.0.0.0:5000, un proceso con hilos y, si el arranque falla,
  sale con el codigo que apaga Gunicorn.
- Dockerfile y requirements.txt: Gunicorn con version fija, usuario sin permisos
  de administrador y ningun secreto escrito en la imagen.

Las IP son de documentacion (RFC 5737), inventadas. No se lee ningun .env ni se
imprime ningun valor de configuracion.

Ejecutar desde petconnect.Backend, con el entorno virtual activo:
    python -m unittest discover -s tests -v
"""
import ast
import io
import os
import re
import runpy
import sys
import types
import unittest
from contextlib import redirect_stdout
from unittest import mock

CARPETA_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, CARPETA_BACKEND)

from test_errores import _importar_api  # noqa: E402

LIMITE = 5                     # 5 por minuto en las rutas de autenticacion (item 2.6)
IP_NGINX = "172.18.0.4"        # la que veria la API detras de nginx en Docker
IP_ANA = "203.0.113.10"        # dos personas distintas (inventadas)
IP_BETO = "203.0.113.20"
IP_INVENTADA = "198.51.100.7"  # la que un atacante escribe en el encabezado

# Variables que guardan secretos: ninguna puede quedar escrita en el Dockerfile
SECRETOS = ("JWT_SECRET", "FERNET_KEY", "DB_PASSWORD", "DB_USER", "MAILTRAP_API_TOKEN",
            "GMAIL_APP_PASSWORD", "GMAIL_USER")


def _leer(nombre):
    with open(os.path.join(CARPETA_BACKEND, nombre), encoding="utf-8") as archivo:
        return archivo.read()


def _instrucciones_dockerfile():
    """Lista de (INSTRUCCION, resto) del Dockerfile, sin comentarios ni lineas vacias."""
    texto = _leer("Dockerfile").replace("\\\n", " ")
    instrucciones = []
    for linea in texto.splitlines():
        linea = linea.strip()
        if linea and not linea.startswith("#"):
            palabra, _, resto = linea.partition(" ")
            instrucciones.append((palabra.upper(), resto.strip()))
    return instrucciones


class PruebasHostApi(unittest.TestCase):
    """python api.py: 127.0.0.1 por defecto, API_HOST solo si se pide."""

    @classmethod
    def setUpClass(cls):
        cls.api = _importar_api()

    def _host(self, valor=None):
        entorno = {} if valor is None else {"API_HOST": valor}
        with mock.patch.dict(os.environ, entorno):
            if valor is None:
                os.environ.pop("API_HOST", None)
            return self.api._host_api()

    def test_sin_variable_solo_escucha_en_este_computador(self):
        self.assertEqual(self._host(), "127.0.0.1")
        self.assertEqual(self._host(""), "127.0.0.1")
        self.assertEqual(self._host("   "), "127.0.0.1")

    def test_con_variable_usa_ese_host(self):
        self.assertEqual(self._host("0.0.0.0"), "0.0.0.0")
        self.assertEqual(self._host(" 0.0.0.0 "), "0.0.0.0")

    def test_el_bloque_main_usa_preparar_arranque_y_el_host(self):
        # Gunicorn no ejecuta el bloque __main__: las revisiones deben estar en una
        # funcion que tambien llame gunicorn.conf.py, y app.run debe recibir el host.
        arbol = ast.parse(_leer("api.py"))
        bloque = next(n for n in arbol.body if isinstance(n, ast.If)
                      and "__main__" in ast.unparse(n.test))
        codigo = ast.unparse(bloque)
        self.assertIn("preparar_arranque()", codigo)
        self.assertIn("_host_api()", codigo)
        llamada_run = next(n for n in ast.walk(bloque) if isinstance(n, ast.Call)
                           and ast.unparse(n.func) == "app.run")
        self.assertIn("host", [k.arg for k in llamada_run.keywords])
        self.assertNotIn("_verificar_bd", codigo)   # ya no va suelto aqui


class PruebasIpCliente(unittest.TestCase):
    """El limite cuenta por persona detras de nginx, sin creer encabezados inventados."""

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

    def _login(self, reenviada=None, ip=IP_NGINX):
        cabeceras = {"X-Forwarded-For": reenviada} if reenviada else {}
        # Cuerpo vacio: responde 400 sin tocar BD ni correo; el limite se cuenta antes
        return self.cliente.post("/api/auth/login", json={}, headers=cabeceras,
                                 environ_base={"REMOTE_ADDR": ip}).status_code

    def test_detras_de_nginx_dos_personas_no_se_bloquean_entre_si(self):
        # Antes: todas las peticiones contaban como la IP de nginx y Beto quedaba
        # bloqueado por los intentos de Ana.
        self._proxy("1")
        for _ in range(LIMITE):
            self.assertNotEqual(self._login(IP_ANA), 429)
        self.assertEqual(self._login(IP_ANA), 429)
        self.assertNotEqual(self._login(IP_BETO), 429)

    def test_detras_de_nginx_inventar_el_encabezado_no_salta_el_limite(self):
        # nginx AGREGA al final la IP que ve: "lo que escribio el cliente, IP real".
        # Solo se cree la ultima.
        self._proxy("1")
        for i in range(LIMITE):
            self._login(f"198.51.100.{i + 1}, {IP_ANA}")
        self.assertEqual(self._login(f"{IP_INVENTADA}, {IP_ANA}"), 429)

    def test_sin_proxy_confiable_el_encabezado_se_ignora(self):
        # python api.py sin nginx: cada peticion con una IP inventada distinta en el
        # encabezado igual cuenta como la misma IP que se conecta.
        for valor in ("", "0", "si"):
            with self.subTest(PROXY_CONFIABLE=valor):
                self.api.limiter.reset()
                with mock.patch.dict(os.environ, {"PROXY_CONFIABLE": valor}):
                    for i in range(LIMITE):
                        self._login(f"198.51.100.{i + 1}", ip=IP_ANA)
                    self.assertEqual(self._login(IP_INVENTADA, ip=IP_ANA), 429)

    def test_con_proxy_y_sin_encabezado_cuenta_la_ip_que_se_conecta(self):
        self._proxy("1")
        for _ in range(LIMITE):
            self._login(ip=IP_ANA)
        self.assertEqual(self._login(ip=IP_ANA), 429)
        self.assertNotEqual(self._login(ip=IP_BETO), 429)


class PruebasPrepararArranque(unittest.TestCase):
    """Las revisiones de arranque estan en una funcion (Gunicorn no corre __main__)."""

    @classmethod
    def setUpClass(cls):
        cls.api = _importar_api()

    def _arrancar(self, bd_ok=True, otp_ok=True, sesiones_ok=True):
        conexion = mock.Mock() if bd_ok else None
        salida = io.StringIO()
        with mock.patch.object(self.api._conexion_bd, "obtener_conexion", return_value=conexion), \
                mock.patch.object(self.api, "_preparar_otp", return_value=otp_ok), \
                mock.patch.object(self.api, "_preparar_sesiones", return_value=sesiones_ok), \
                redirect_stdout(salida):
            return self.api.preparar_arranque(), salida.getvalue()

    def test_todo_bien_permite_arrancar(self):
        listo, salida = self._arrancar()
        self.assertTrue(listo)
        self.assertIn("[OK] Conexion a la base de datos establecida.", salida)

    def test_sin_bd_no_arranca(self):
        listo, salida = self._arrancar(bd_ok=False)
        self.assertFalse(listo)
        self.assertIn("[ERROR] No se pudo conectar a la base de datos.", salida)

    def test_sin_tabla_otp_o_sin_version_sesion_no_arranca(self):
        self.assertFalse(self._arrancar(otp_ok=False)[0])
        self.assertFalse(self._arrancar(sesiones_ok=False)[0])


class PruebasGunicornConf(unittest.TestCase):
    """gunicorn.conf.py: lo leemos como Gunicorn (un archivo de Python con variables)."""

    @classmethod
    def setUpClass(cls):
        cls.conf = runpy.run_path(os.path.join(CARPETA_BACKEND, "gunicorn.conf.py"))

    def test_escucha_en_todas_las_interfaces_del_contenedor(self):
        self.assertEqual(self.conf["bind"], "0.0.0.0:5000")

    def test_un_proceso_con_hilos_que_caben_en_el_pool(self):
        # El limite cuenta en memoria: con mas de 1 proceso se multiplicaria
        self.assertEqual(self.conf["workers"], 1)
        self.assertEqual(self.conf["worker_class"], "gthread")
        self.assertGreater(self.conf["threads"], 1)
        self.assertLessEqual(self.conf["threads"], 10)      # pool por defecto (DB_POOL_SIZE)

    def test_sin_registro_de_accesos(self):
        # Cada linea traeria la IP y la ruta de cada persona (Ley 1581)
        self.assertIsNone(self.conf.get("accesslog"))

    def test_si_el_arranque_falla_gunicorn_se_apaga(self):
        api_falsa = types.SimpleNamespace(preparar_arranque=mock.Mock(return_value=False))
        with mock.patch.dict(sys.modules, {"api": api_falsa}):
            with self.assertRaises(SystemExit) as salida:
                self.conf["post_worker_init"](mock.Mock())
        self.assertEqual(salida.exception.code, 3)          # Arbiter.WORKER_BOOT_ERROR
        api_falsa.preparar_arranque.assert_called_once_with()

    def test_si_el_arranque_va_bien_sigue(self):
        api_falsa = types.SimpleNamespace(preparar_arranque=mock.Mock(return_value=True))
        with mock.patch.dict(sys.modules, {"api": api_falsa}):
            self.assertIsNone(self.conf["post_worker_init"](mock.Mock()))


class PruebasDockerfile(unittest.TestCase):
    """La imagen corre con Gunicorn, sin root y sin secretos escritos."""

    @classmethod
    def setUpClass(cls):
        cls.instrucciones = _instrucciones_dockerfile()

    def _todas(self, instruccion):
        return [resto for palabra, resto in self.instrucciones if palabra == instruccion]

    def test_parte_de_python_314_slim(self):
        self.assertEqual(self._todas("FROM"), ["python:3.14-slim"])

    def test_arranca_con_gunicorn_y_su_configuracion(self):
        cmd = self._todas("CMD")
        self.assertEqual(len(cmd), 1)
        self.assertEqual(cmd[0], '["gunicorn", "-c", "gunicorn.conf.py", "api:app"]')
        self.assertFalse(self._todas("ENTRYPOINT"))
        self.assertIn("5000", self._todas("EXPOSE"))

    def test_corre_sin_permisos_de_administrador(self):
        usuarios = self._todas("USER")
        self.assertTrue(usuarios, "falta USER: la API correria como root")
        self.assertNotIn(usuarios[-1].split(":")[0], ("root", "0"))
        # USER va antes de CMD (lo que va despues de CMD no cambia nada)
        palabras = [palabra for palabra, _ in self.instrucciones]
        self.assertLess(len(palabras) - 1 - palabras[::-1].index("USER"), palabras.index("CMD"))

    def test_ningun_secreto_escrito_en_la_imagen(self):
        for palabra, resto in self.instrucciones:
            if palabra in ("ENV", "ARG", "LABEL"):
                for secreto in SECRETOS:
                    with self.subTest(instruccion=palabra, variable=secreto):
                        self.assertNotIn(secreto, resto)

    def test_no_copia_archivos_de_configuracion_secreta(self):
        for resto in self._todas("COPY") + self._todas("ADD"):
            with self.subTest(copia=resto):
                self.assertNotRegex(resto, r"\.env|\.pem|\.key")

    def test_no_escucha_con_app_run(self):
        # La orden real (sin comentarios) no usa el servidor de desarrollo
        orden = " ".join(resto for palabra, resto in self.instrucciones
                         if palabra in ("CMD", "RUN", "ENTRYPOINT"))
        self.assertNotIn("api.py", orden)
        self.assertNotIn("flask run", orden)


class PruebasRequirements(unittest.TestCase):

    def test_gunicorn_con_version_fija(self):
        lineas = [linea.strip() for linea in _leer("requirements.txt").splitlines()]
        gunicorn = [linea for linea in lineas if linea.lower().startswith("gunicorn")]
        self.assertEqual(len(gunicorn), 1, "Gunicorn debe estar una vez en requirements.txt")
        self.assertRegex(gunicorn[0], r"^gunicorn==\d+\.\d+\.\d+$")


if __name__ == "__main__":
    unittest.main()
