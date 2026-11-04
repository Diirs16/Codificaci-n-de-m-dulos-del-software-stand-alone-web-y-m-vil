"""
Pruebas de regresion de NC-007 / A-08 (item 2.3 de PRIORIDADES): la API responde
con el codigo HTTP real y nunca muestra detalles internos al cliente.
No usan la base de datos real (se simula apagada), no envian correos ni leen .env.

Ejecutar desde petconnect.Backend, con el entorno virtual activo:
    python -m unittest discover -s tests -v
"""
import importlib
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mysql.connector.errors import OperationalError  # noqa: E402

CORREO_PRUEBA = "laura@ejemplo.test"    # inventado
CONTRASENA = "Firulais2026!"


def _importar_api():
    """
    Importa api.py con claves de prueba. Si esta prueba es la primera en importarlo,
    se desactiva load_dotenv para no cargar el .env real (como en test_correo.py).
    Si otra prueba ya lo importo, se reutiliza: estas pruebas no usan ningun valor
    del .env (pendiente 4.14: test_seguridad.py todavia lo carga).
    """
    if "api" in sys.modules:
        return sys.modules["api"]

    from cryptography.fernet import Fernet
    import dotenv

    os.environ.setdefault("FERNET_KEY", Fernet.generate_key().decode())
    os.environ.setdefault("JWT_SECRET", "clave-de-pruebas-petconnect-" + "x" * 32)
    load_dotenv_original = dotenv.load_dotenv
    dotenv.load_dotenv = lambda *a, **k: False
    try:
        return importlib.import_module("api")
    finally:
        dotenv.load_dotenv = load_dotenv_original


class PruebasRespuestasDeError(unittest.TestCase):
    """404/405 con su codigo real, 503 sin BD, 500 generico y 400 si un dato no es texto."""

    @classmethod
    def setUpClass(cls):
        cls.api = _importar_api()
        cls.cliente = cls.api.app.test_client()

    def setUp(self):
        # BD "apagada" en todas las pruebas: nunca se toca la base real
        parche = mock.patch.object(self.api._conexion_bd, "obtener_conexion", return_value=None)
        self.obtener_conexion = parche.start()
        self.addCleanup(parche.stop)

    def _sin_detalles_internos(self, respuesta):
        texto = respuesta.get_data(as_text=True)
        for pista in ("NoneType", "cursor", "Traceback", "object has no attribute"):
            self.assertNotIn(pista, texto)

    def test_ruta_inexistente_responde_404(self):
        r = self.cliente.get("/api/no-existe")
        self.assertEqual(r.status_code, 404)
        self.assertEqual(r.get_json(), {"error": "Recurso no encontrado"})

    def test_metodo_no_permitido_responde_405(self):
        r = self.cliente.post("/api/productos")
        self.assertEqual(r.status_code, 405)
        self.assertIn("GET", r.headers.get("Allow", ""))
        self.assertEqual(r.get_json(), {"error": "Metodo no permitido para esta ruta"})

    def test_bd_caida_responde_503_sin_detalles(self):
        for ruta in ("/api/productos", "/api/productos/1", "/api/mascotas/adopcion", "/api/mascotas/1"):
            with self.subTest(ruta=ruta), self.assertLogs(self.api.app.logger, "ERROR"):
                r = self.cliente.get(ruta)
                self.assertEqual(r.status_code, 503)
                self.assertIn("id_error", r.get_json())
                self._sin_detalles_internos(r)

    def test_login_con_bd_caida_responde_503_y_no_credenciales_incorrectas(self):
        with self.assertLogs(self.api.app.logger, "ERROR"):
            r = self.cliente.post("/api/auth/login", json={"email": CORREO_PRUEBA, "password": CONTRASENA})
        self.assertEqual(r.status_code, 503)

    def test_bd_que_se_cae_a_mitad_de_consulta_responde_503(self):
        conexion = mock.MagicMock()
        conexion.cursor.return_value.execute.side_effect = OperationalError(
            msg="Lost connection to MySQL server at 'servidor-interno:3310'")
        self.obtener_conexion.return_value = conexion
        with self.assertLogs(self.api.app.logger, "ERROR"):
            r = self.cliente.get("/api/mascotas/adopcion")
        self.assertEqual(r.status_code, 503)
        self.assertNotIn("servidor-interno", r.get_data(as_text=True))

    def test_error_inesperado_responde_500_generico_y_se_registra_sin_datos_personales(self):
        self.obtener_conexion.side_effect = RuntimeError(f"fallo inesperado con {CORREO_PRUEBA}")
        with self.assertLogs(self.api.app.logger, "ERROR") as registro:
            r = self.cliente.get("/api/productos")

        self.assertEqual(r.status_code, 500)
        cuerpo = r.get_json()
        self.assertEqual(cuerpo["error"], "Error interno del servidor. Intenta de nuevo mas tarde")
        self.assertNotIn("RuntimeError", r.get_data(as_text=True))
        self.assertNotIn(CORREO_PRUEBA, r.get_data(as_text=True))

        log = "\n".join(registro.output)
        self.assertIn(cuerpo["id_error"], log)          # se puede buscar con el id
        self.assertIn("RuntimeError", log)              # el servidor si guarda el tipo
        self.assertIn("/api/productos", log)
        self.assertNotIn(CORREO_PRUEBA, log)            # pero no el mensaje (Ley 1581)

    def test_campos_que_no_son_texto_responden_400(self):
        casos = [
            ("/api/auth/login", {"email": 5, "password": CONTRASENA}, "email"),
            ("/api/auth/login", {"email": CORREO_PRUEBA, "password": 12345678}, "password"),
            ("/api/auth/login/verify", {"email": CORREO_PRUEBA, "code": 123456}, "code"),
            ("/api/auth/verify", {"email": CORREO_PRUEBA, "code": None}, "code"),
            ("/api/auth/register", {"name": 5, "email": CORREO_PRUEBA, "password": CONTRASENA}, "name"),
            ("/api/auth/register", {"name": "Laura", "email": [CORREO_PRUEBA], "password": CONTRASENA}, "email"),
            ("/api/utils/validar-correo", {"email": 5}, "email"),
        ]
        for ruta, cuerpo, campo in casos:
            with self.subTest(ruta=ruta, campo=campo):
                r = self.cliente.post(ruta, json=cuerpo)
                self.assertEqual(r.status_code, 400)
                self.assertEqual(r.get_json(), {"error": f"El campo '{campo}' debe ser texto"})

    def test_cuerpo_que_no_es_objeto_responde_400(self):
        r = self.cliente.post("/api/auth/login", json=[CORREO_PRUEBA, CONTRASENA])
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.get_json(), {"error": "El cuerpo de la peticion debe ser un objeto JSON"})


class PruebasNombreRegistro(unittest.TestCase):
    """
    A-05 (item 2.4): /api/auth/register solo acepta nombres de persona, porque el
    nombre viaja en el correo que se envia a la direccion que den. Se rechaza antes
    de consultar el DNS o la BD, y sin enviar ningun correo.
    """

    VALIDOS = ["Laura", "María José", "Ana O'Neil", "Pérez-Gil", "Ma. José", "Ñoño Núñez", "Lu"]
    INVALIDOS = [
        '<a href="https://sitio-falso.example">Reclama tu premio</a>',
        '<a/href="https://sitio-falso.example">Premio</a>',
        "https://sitio-falso.example",
        "sitio-falso.example",
        "www.premio.com",
        "Laura 🐶",
        "R2D2",
        "L",
        "A" * 61,
        "Laura\tGómez",
        "Laura\nBcc: otro@ejemplo.test",
    ]

    @classmethod
    def setUpClass(cls):
        cls.api = _importar_api()
        cls.cliente = cls.api.app.test_client()

    def setUp(self):
        # Si algo pasara el filtro, que no toque red, BD ni correo
        for nombre, valor in (("_validar_correo", (False, "correo rechazado en la prueba")),
                              ("enviar_codigo", None)):
            parche = mock.patch.object(self.api, nombre, return_value=valor)
            setattr(self, nombre, parche.start())
            self.addCleanup(parche.stop)

    def _registrar(self, nombre):
        return self.cliente.post("/api/auth/register",
                                 json={"name": nombre, "email": CORREO_PRUEBA, "password": CONTRASENA})

    def test_nombre_con_html_o_url_responde_400_sin_enviar_correo(self):
        for nombre in self.INVALIDOS:
            with self.subTest(nombre=nombre):
                r = self._registrar(nombre)
                self.assertEqual(r.status_code, 400)
                self.assertIn("El nombre debe tener entre 2 y 60", r.get_json()["error"])
        self._validar_correo.assert_not_called()    # ni siquiera llego al DNS
        self.enviar_codigo.assert_not_called()

    def test_nombres_de_persona_pasan_el_filtro(self):
        for nombre in self.VALIDOS:
            with self.subTest(nombre=nombre):
                r = self._registrar(nombre)
                # Sigue al siguiente paso (validar el correo, aqui simulado como invalido)
                self.assertEqual(r.get_json(), {"error": "correo rechazado en la prueba"})
        self.assertEqual(self._validar_correo.call_count, len(self.VALIDOS))


class PruebasModoDebug(unittest.TestCase):
    """El depurador de Werkzeug queda apagado salvo FLASK_DEBUG=1 explicito."""

    @classmethod
    def setUpClass(cls):
        cls.api = _importar_api()

    def _modo_debug_con(self, valor):
        with mock.patch.dict(os.environ):
            os.environ.pop("FLASK_DEBUG", None)
            if valor is not None:
                os.environ["FLASK_DEBUG"] = valor
            return self.api._modo_debug()

    def test_apagado_por_defecto(self):
        self.assertFalse(self._modo_debug_con(None))
        self.assertFalse(self._modo_debug_con(""))
        self.assertFalse(self._modo_debug_con("0"))

    def test_solo_se_enciende_con_1(self):
        self.assertTrue(self._modo_debug_con("1"))
        self.assertFalse(self._modo_debug_con("true"))


if __name__ == "__main__":
    unittest.main()
