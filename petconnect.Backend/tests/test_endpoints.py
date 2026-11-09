"""
Pruebas de endpoints con el cliente de Flask (item 4.4 de PRIORIDADES, A-31 segunda
parte). Cubren los huecos que dejo el inventario del 07/11/2026; lo que ya probaban
los otros archivos de tests/ no se repite aqui.

- Inventario de rutas: la lista de rutas de la API es la esperada, cada una nombra
  el archivo de pruebas que la cubre y toda ruta privada responde 401 sin token.
- Productos: lista y detalle (los dos filtran activo = TRUE; el detalle desde el 4.16).
- Lista de adopcion: el SQL filtra estado = 'en_adopcion' sin MariaDB (NC-009).
- GET /api/auth/me con el token real de generate_token (NC-008).
- Login: campos vacios, correo inexistente igual que contrasena mala (no revela
  cuentas) y migracion del hash SHA-256 heredado a bcrypt (NC-001).
- Verificacion del codigo (login/verify y verify): sin pendiente, vencido, usuario
  inexistente, BD caida sin gastar el codigo y fallo al crear la cuenta.
- Registro: campos vacios, correo ya registrado (respuesta neutra, item 4.10) y BD caida.
- Validar correo: formato, dominio sin MX, dominio con MX y DNS caido.

La BD, el DNS y el correo se simulan: no usan MariaDB, no envian correos, no salen
a internet ni leen .env (_importar_api). Los correos son inventados (Ley 1581) y los
tokens se firman dentro de la prueba con la clave de pruebas.

Ejecutar desde petconnect.Backend, con el entorno virtual activo:
    python -m unittest discover -s tests -v
"""
import ast
import hashlib
import importlib
import os
import re
import sys
import time
import unittest
from types import SimpleNamespace
from unittest import mock

import bcrypt
import dns.exception
import dns.resolver
import jwt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_errores import _importar_api  # noqa: E402

CARPETA_TESTS = os.path.dirname(os.path.abspath(__file__))

# Datos inventados (Ley 1581)
CORREO = "endpoints.prueba@ejemplo.test"
CLAVE = "Firulais2026!"
ID_USUARIO = 7


# ---------------------------------------------------------------------------
# Inventario: cada ruta de la API, si es publica o privada y que archivo la prueba
# ---------------------------------------------------------------------------
# Si alguien agrega una ruta, PruebasInventarioDeRutas falla hasta que la anote aqui
# con sus pruebas. Asi el inventario del 4.4 no se queda viejo.

RUTAS_PUBLICAS = {
    ("GET", "/api/productos"): ("test_endpoints.py", "test_errores.py", "test_limite.py",
                                "test_pool.py"),
    ("GET", "/api/productos/<int:id_producto>"): ("test_endpoints.py", "test_errores.py",
                                                  "test_pool.py"),
    ("GET", "/api/mascotas/adopcion"): ("test_endpoints.py", "test_ficha_mascota.py", "test_errores.py",
                                        "test_pool.py"),
    ("GET", "/api/mascotas/<int:id_mascota>"): ("test_mascotas.py", "test_ficha_mascota.py",
                                                "test_pool.py"),
    ("POST", "/api/utils/validar-correo"): ("test_endpoints.py", "test_errores.py", "test_limite.py",
                                            "test_pool.py"),
    ("POST", "/api/auth/login"): ("test_endpoints.py", "test_login_datos.py", "test_logs.py",
                                  "test_pool.py"),
    ("POST", "/api/auth/login/verify"): ("test_endpoints.py", "test_login_datos.py", "test_otp.py",
                                         "test_pool.py"),
    ("POST", "/api/auth/register"): ("test_endpoints.py", "test_registro.py", "test_registro_datos.py",
                                     "test_politica.py", "test_pool.py", "test_registro_neutro.py"),
    ("POST", "/api/auth/register/resend"): ("test_registro.py", "test_pool.py"),
    ("POST", "/api/auth/verify"): ("test_endpoints.py", "test_registro_datos.py", "test_otp.py",
                                   "test_logs.py", "test_pool.py", "test_registro_neutro.py"),
}

RUTAS_PRIVADAS = {   # llevan @require_auth: sin token, 401
    ("GET", "/api/usuarios/me/mascotas/<int:id_mascota>"): ("test_mascotas.py", "test_ficha_mascota.py",
                                                            "test_pool.py"),
    ("GET", "/api/auth/me"): ("test_endpoints.py", "test_pool.py"),
    ("POST", "/api/auth/logout"): ("test_sesiones.py", "test_pool.py"),
    ("POST", "/api/solicitudes/adopcion"): ("test_solicitudes.py", "test_limite.py", "test_pool.py"),
    ("POST", "/api/solicitudes/contacto"): ("test_solicitudes.py", "test_limite.py", "test_pool.py"),
}


def _url(regla):
    """URL de ejemplo para una regla de Flask: <int:...> se cambia por 1."""
    return re.sub(r"<[^>]+>", "1", regla)


def _parte_fija(regla):
    """Parte de la regla antes del primer <...>: es lo que aparece en las pruebas."""
    return regla.split("<", 1)[0]


def _textos_del_codigo(ruta_archivo):
    """
    Textos ("...") que usa el codigo de un archivo de pruebas. No cuentan los
    comentarios, los docstrings ni el propio inventario de este archivo: nombrar una
    ruta ahi no es probarla.
    """
    with open(ruta_archivo, encoding="utf-8") as f:
        arbol = ast.parse(f.read())
    excluidos = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, (ast.Module, ast.ClassDef, ast.FunctionDef)) and nodo.body:
            primero = nodo.body[0]
            if isinstance(primero, ast.Expr) and isinstance(primero.value, ast.Constant):
                excluidos.add(id(primero.value))                         # docstring
        if isinstance(nodo, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id in ("RUTAS_PUBLICAS", "RUTAS_PRIVADAS")
                for t in nodo.targets):
            excluidos.update(id(n) for n in ast.walk(nodo.value))       # el inventario
    return [n.value for n in ast.walk(arbol)
            if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in excluidos]


def _usuario(**cambios):
    """Usuario falso con los campos que mira la API (como los deja _mapear_usuario)."""
    datos = dict(
        id_usuario=ID_USUARIO, nombres="Laura", apellidos="Gomez", correo=CORREO,
        password_hash="hash-falso", estado="activo", acepta_datos=True,
        fecha_autorizacion_datos=None, version_politica_datos=None,
    )
    datos.update(cambios)
    return SimpleNamespace(**datos)


class _BaseEndpoints(unittest.TestCase):
    """BD simulada "encendida", UsuarioDAO falso y correos que no salen."""

    @classmethod
    def setUpClass(cls):
        cls.api = _importar_api()            # limitador apagado, sin .env
        cls.cliente = cls.api.app.test_client()

    def setUp(self):
        self.conexion = mock.MagicMock()
        self.cursor = self.conexion.cursor.return_value
        self.cursor.fetchall.return_value = []
        self.cursor.fetchone.return_value = None
        parches = {
            "obtener_conexion": mock.patch.object(self.api._conexion_bd, "obtener_conexion",
                                                  return_value=self.conexion),
            "UsuarioDAO": mock.patch.object(self.api, "UsuarioDAO"),
            "enviar_codigo": mock.patch.object(self.api, "enviar_codigo"),
            "enviar_bienvenida": mock.patch.object(self.api, "enviar_bienvenida"),
            "enviar_aviso": mock.patch.object(self.api, "enviar_aviso_cuenta_existente"),
        }
        for nombre, parche in parches.items():
            setattr(self, nombre, parche.start())
            self.addCleanup(parche.stop)
        self.dao = self.UsuarioDAO.return_value
        self.dao.consultar_por_correo.return_value = None
        self.dao.consultar_por_id.return_value = None

        for almacen in (self.api._otp_login, self.api._otp_registro):
            almacen.descartar(CORREO)
            self.addCleanup(almacen.descartar, CORREO)
        self.api._liberar_aviso(CORREO)               # item 4.10: avisos recientes
        self.addCleanup(self.api._liberar_aviso, CORREO)

    def _bd_apagada(self):
        self.obtener_conexion.return_value = None

    def _sql_y_parametros(self):
        """Consulta (en una linea) y parametros con que la ruta llamo a cursor.execute."""
        self.cursor.execute.assert_called_once()
        argumentos = self.cursor.execute.call_args.args
        sql = " ".join(argumentos[0].split())
        return sql, argumentos[1] if len(argumentos) > 1 else None

    def _sin_datos_internos(self, r):
        texto = r.get_data(as_text=True)
        for pista in ("Traceback", "NoneType", "cursor", CORREO, "hash-falso"):
            self.assertNotIn(pista, texto)


# ---------------------------------------------------------------------------
# 1. Inventario de rutas
# ---------------------------------------------------------------------------

class PruebasInventarioDeRutas(_BaseEndpoints):

    def _rutas_de_la_api(self):
        rutas = set()
        for regla in self.api.app.url_map.iter_rules():
            if not regla.rule.startswith("/api/"):
                continue          # static y la ruta de prueba de test_seguridad.py
            for metodo in regla.methods - {"HEAD", "OPTIONS"}:
                rutas.add((metodo, regla.rule))
        return rutas

    def test_las_rutas_de_la_api_son_las_del_inventario(self):
        esperadas = set(RUTAS_PUBLICAS) | set(RUTAS_PRIVADAS)
        rutas = self._rutas_de_la_api()
        self.assertEqual(rutas - esperadas, set(),
                         "Ruta nueva: anotala en RUTAS_PUBLICAS o RUTAS_PRIVADAS con sus pruebas")
        self.assertEqual(esperadas - rutas, set(), "Ruta del inventario que ya no existe")

    def test_cada_ruta_tiene_un_archivo_de_pruebas_que_la_nombra(self):
        for (metodo, regla), archivos in {**RUTAS_PUBLICAS, **RUTAS_PRIVADAS}.items():
            for archivo in archivos:
                with self.subTest(ruta=f"{metodo} {regla}", archivo=archivo):
                    textos = _textos_del_codigo(os.path.join(CARPETA_TESTS, archivo))
                    self.assertTrue(any(_parte_fija(regla) in t for t in textos),
                                    f"{archivo} no usa {regla} en su codigo")

    def test_rutas_privadas_sin_token_responden_401_sin_tocar_la_bd(self):
        for metodo, regla in RUTAS_PRIVADAS:
            with self.subTest(ruta=f"{metodo} {regla}"):
                self.obtener_conexion.reset_mock()
                r = self.cliente.open(_url(regla), method=metodo, json={})
                self.assertEqual(r.status_code, 401)
                self.assertEqual(r.get_json(), {"error": "Autenticacion requerida"})
                self.obtener_conexion.assert_not_called()

    def test_rutas_publicas_no_piden_token(self):
        # BD simulada vacia: las GET responden 200 o 404 y las POST vacias 400 o 200
        for metodo, regla in RUTAS_PUBLICAS:
            with self.subTest(ruta=f"{metodo} {regla}"):
                r = self.cliente.open(_url(regla), method=metodo, json={})
                self.assertNotEqual(r.status_code, 401)
                self.assertLess(r.status_code, 500)
        self.enviar_codigo.assert_not_called()


# ---------------------------------------------------------------------------
# 2. Productos (publico)
# ---------------------------------------------------------------------------

ID_PRODUCTO = 4321


def _producto():
    return {"id": ID_PRODUCTO, "name": "Collar de prueba", "description": "Collar inventado",
            "price": 25000.0, "stock": 3, "image": None, "activo": 1, "category": "Accesorios"}


class PruebasProductos(_BaseEndpoints):

    def test_lista_responde_200_con_los_productos(self):
        self.cursor.fetchall.return_value = [_producto()]
        r = self.cliente.get("/api/productos")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json(), [_producto()])

    def test_la_lista_solo_trae_productos_activos(self):
        self.cliente.get("/api/productos")
        sql, params = self._sql_y_parametros()
        self.assertIn("WHERE p.activo = TRUE", sql)
        self.assertEqual(params, (20, 0))       # item 4.17: primera pagina de 20

    def test_detalle_responde_200_y_va_parametrizado(self):
        self.cursor.fetchone.return_value = _producto()
        r = self.cliente.get(f"/api/productos/{ID_PRODUCTO}")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json(), _producto())
        sql, params = self._sql_y_parametros()
        self.assertIn("WHERE p.id_producto = %s", sql)
        self.assertEqual(params, (ID_PRODUCTO,))
        self.assertNotIn(str(ID_PRODUCTO), sql)        # el id no va pegado al texto

    def test_detalle_inexistente_responde_404(self):
        r = self.cliente.get("/api/productos/999999")
        self.assertEqual(r.status_code, 404)
        self.assertEqual(r.get_json(), {"error": "Producto no encontrado"})

    # Item 4.16: antes el detalle no filtraba activo = TRUE y un producto descontinuado
    # se veia (y se podia agregar al carrito) escribiendo su URL.
    def test_el_detalle_solo_trae_productos_activos(self):
        self.cliente.get(f"/api/productos/{ID_PRODUCTO}")
        sql, params = self._sql_y_parametros()
        self.assertIn("WHERE p.id_producto = %s AND p.activo = TRUE", sql)
        self.assertEqual(params, (ID_PRODUCTO,))

    def test_producto_descontinuado_responde_el_mismo_404(self):
        # Doble barrera: la BD simulada devuelve la fila aunque el SQL la filtraria
        for activo in (0, False):
            with self.subTest(activo=activo):
                self.cursor.fetchone.return_value = {**_producto(), "activo": activo}
                r = self.cliente.get(f"/api/productos/{ID_PRODUCTO}")
                self.assertEqual(r.status_code, 404)
                self.assertEqual(r.get_json(), {"error": "Producto no encontrado"})
                self.assertNotIn("Collar de prueba", r.get_data(as_text=True))


# ---------------------------------------------------------------------------
# 3. Lista de adopcion (NC-009 sin MariaDB)
# ---------------------------------------------------------------------------

class PruebasListaAdopcion(_BaseEndpoints):

    def test_la_lista_filtra_por_estado_en_adopcion(self):
        r = self.cliente.get("/api/mascotas/adopcion")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json(), [])          # lista vacia: 200, no error
        sql, params = self._sql_y_parametros()
        self.assertRegex(sql, r"WHERE estado = 'en_adopcion'")
        self.assertEqual(params, (20, 0))       # item 4.17: primera pagina de 20


# ---------------------------------------------------------------------------
# 4. GET /api/auth/me (NC-008 con la ruta real)
# ---------------------------------------------------------------------------

class PruebasAuthMe(_BaseEndpoints):
    RUTA = "/api/auth/me"

    def _con_token(self, token):
        return self.cliente.get(self.RUTA, headers={"Authorization": f"Bearer {token}"})

    def _token_firmado(self, **payload):
        # Misma clave de pruebas con que firma generate_token (ya importada por
        # _importar_api, sin .env); nunca se imprime
        jwt_helper = importlib.import_module("security.jwt_helper")
        return jwt.encode(payload, jwt_helper._SECRET, algorithm="HS256")

    def _token_vigente(self):
        # Item 4.13: require_auth consulta la sesion en la BD (version 0, activa)
        self.dao.consultar_sesion.return_value = (0, "activo")
        return self.api.generate_token(ID_USUARIO, 0)

    def test_token_recien_emitido_responde_200_con_los_datos_de_la_cuenta(self):
        self.dao.consultar_por_id.return_value = _usuario()
        r = self._con_token(self._token_vigente())
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json(), {"id": ID_USUARIO, "name": "Laura Gomez", "email": CORREO})
        self.dao.consultar_por_id.assert_called_once_with(ID_USUARIO)   # entero, sale del token
        self.assertNotIn("hash-falso", r.get_data(as_text=True))

    def test_tokens_invalidos_responden_401_sin_tocar_la_bd(self):
        ahora = int(time.time())
        casos = {
            "inventado": "token-inventado",
            "vencido": self._token_firmado(sub=str(ID_USUARIO), email=CORREO, exp=ahora - 60),
            "otra clave": jwt.encode({"sub": str(ID_USUARIO), "email": CORREO, "exp": ahora + 60},
                                     "otra-clave-que-no-es-la-del-servidor-" + "y" * 32,
                                     algorithm="HS256"),
            "sub no numerico": self._token_firmado(sub="abc", email=CORREO, exp=ahora + 60),
        }
        for caso, token in casos.items():
            with self.subTest(token=caso):
                r = self._con_token(token)
                self.assertEqual(r.status_code, 401)
                self.assertEqual(r.get_json(),
                                 {"error": "Token invalido o sesion expirada. Inicia sesion de nuevo"})
        self.obtener_conexion.assert_not_called()
        self.dao.consultar_por_id.assert_not_called()

    def test_usuario_borrado_responde_401(self):
        # Item 4.13: sin fila no hay sesion (antes llegaba a la ruta y daba 404)
        self.dao.consultar_sesion.return_value = None
        r = self._con_token(self.api.generate_token(ID_USUARIO, 0))
        self.assertEqual(r.status_code, 401)
        self.dao.consultar_por_id.assert_not_called()

    def test_usuario_borrado_entre_las_dos_consultas_responde_404(self):
        r = self._con_token(self._token_vigente())
        self.assertEqual(r.status_code, 404)
        self.assertEqual(r.get_json(), {"error": "Usuario no encontrado"})

    def test_bd_caida_responde_503(self):
        self._bd_apagada()
        with self.assertLogs(self.api.app.logger, "ERROR"):
            r = self._con_token(self._token_vigente())
        self.assertEqual(r.status_code, 503)
        self.assertIn("id_error", r.get_json())
        self._sin_datos_internos(r)


# ---------------------------------------------------------------------------
# 5. POST /api/auth/login
# ---------------------------------------------------------------------------

class PruebasLogin(_BaseEndpoints):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.hash_bcrypt = cls.api.hash_password(CLAVE)    # una vez: bcrypt es lento a proposito

    def _login(self, email=CORREO, password=CLAVE):
        return self.cliente.post("/api/auth/login", json={"email": email, "password": password})

    def test_campos_vacios_responden_400_sin_bd_ni_correo(self):
        for email, password in (("", CLAVE), ("   ", CLAVE), (CORREO, ""), ("", "")):
            with self.subTest(email=repr(email), password=bool(password)):
                r = self._login(email, password)
                self.assertEqual(r.status_code, 400)
                self.assertEqual(r.get_json(), {"error": "Correo y contrasena son requeridos"})
        self.assertEqual(self.cliente.post("/api/auth/login", json={}).status_code, 400)
        self.obtener_conexion.assert_not_called()
        self.enviar_codigo.assert_not_called()

    def test_correo_inexistente_responde_igual_que_contrasena_mala(self):
        r_sin_cuenta = self._login()                      # consultar_por_correo -> None
        self.dao.consultar_por_correo.return_value = _usuario(password_hash=self.hash_bcrypt)
        r_clave_mala = self._login(password="OtraClave2026!")
        for r in (r_sin_cuenta, r_clave_mala):
            self.assertEqual(r.status_code, 401)
            self.assertEqual(r.get_json(), {"error": "Correo o contrasena incorrectos"})
            self.assertNotIn(CORREO, r.get_data(as_text=True))
        self.enviar_codigo.assert_not_called()
        self.assertFalse(self.api._otp_login.tiene_pendiente(CORREO))

    def _usuario_autorizado(self, password_hash):
        return _usuario(password_hash=password_hash,
                        version_politica_datos=self.api.VERSION_POLITICA_DATOS)

    def test_hash_sha256_heredado_se_cambia_por_bcrypt_al_entrar(self):
        heredado = hashlib.sha256(CLAVE.encode()).hexdigest()
        self.dao.consultar_por_correo.return_value = self._usuario_autorizado(heredado)
        r = self._login()
        self.assertEqual(r.status_code, 200)
        self.dao.actualizar_password.assert_called_once()
        id_usuario, nuevo = self.dao.actualizar_password.call_args.args
        self.assertEqual(id_usuario, ID_USUARIO)
        self.assertTrue(nuevo.startswith("$2b$12$"), "debe ser bcrypt con costo 12")
        self.assertTrue(bcrypt.checkpw(CLAVE.encode(), nuevo.encode()))
        self.assertNotIn(CLAVE, nuevo)

    def test_hash_bcrypt_no_se_reescribe(self):
        self.dao.consultar_por_correo.return_value = self._usuario_autorizado(self.hash_bcrypt)
        r = self._login()
        self.assertEqual(r.status_code, 200)
        self.dao.actualizar_password.assert_not_called()

    def test_hash_heredado_con_contrasena_mala_no_se_migra(self):
        heredado = hashlib.sha256(CLAVE.encode()).hexdigest()
        self.dao.consultar_por_correo.return_value = self._usuario_autorizado(heredado)
        r = self._login(password="OtraClave2026!")
        self.assertEqual(r.status_code, 401)
        self.dao.actualizar_password.assert_not_called()


# ---------------------------------------------------------------------------
# 6. Verificacion del codigo: /api/auth/login/verify y /api/auth/verify
# ---------------------------------------------------------------------------

class PruebasVerificacionDelCodigo(_BaseEndpoints):
    LOGIN_VERIFY = "/api/auth/login/verify"
    VERIFY = "/api/auth/verify"

    def setUp(self):
        super().setUp()
        parche = mock.patch.object(self.api, "generate_token", return_value="token-falso")
        self.generate_token = parche.start()
        self.addCleanup(parche.stop)

    def _verificar(self, ruta, codigo):
        return self.cliente.post(ruta, json={"email": CORREO, "code": codigo})

    def _sin_token(self, r):
        self.assertNotIn("token", r.get_json())
        self.generate_token.assert_not_called()
        self.assertNotIn(CORREO, r.get_data(as_text=True))       # Ley 1581

    def _pendiente_de_registro(self):
        return self.api._otp_registro.crear(CORREO, {
            "name": "Laura Gomez", "password_hash": "hash-falso",
            "fecha_autorizacion_datos": "2026-11-07 10:00:00",
            "version_politica_datos": self.api.VERSION_POLITICA_DATOS,
        })

    def test_sin_codigo_pendiente_responde_400(self):
        mensajes = {
            self.LOGIN_VERIFY: "No hay inicio de sesion pendiente para este correo",
            self.VERIFY: self.api._MENSAJE_CODIGO_REGISTRO,     # item 4.10 (A-14)
        }
        for ruta, mensaje in mensajes.items():
            with self.subTest(ruta=ruta):
                r = self._verificar(ruta, "123456")
                self.assertEqual(r.status_code, 400)
                self.assertEqual(r.get_json(), {"error": mensaje})
                self._sin_token(r)
        self.UsuarioDAO.assert_not_called()

    def test_codigo_vencido_responde_400_y_se_borra(self):
        casos = {
            self.LOGIN_VERIFY: (self.api._otp_login, "El codigo expiro. Vuelve a iniciar sesion"),
            self.VERIFY: (self.api._otp_registro, self.api._MENSAJE_CODIGO_REGISTRO),   # item 4.10
        }
        for ruta, (almacen, mensaje) in casos.items():
            with self.subTest(ruta=ruta):
                codigo = almacen.crear(CORREO, {"id_usuario": ID_USUARIO, "name": "Laura Gomez"})
                # vencio hace mucho (fila del RepositorioMemoria de _importar_api, item 4.6)
                almacen._repositorio._filas[(CORREO, almacen._proposito)]["vence"] = 0
                r = self._verificar(ruta, codigo)                # aunque sea el correcto
                self.assertEqual(r.status_code, 400)
                self.assertEqual(r.get_json(), {"error": mensaje})
                self._sin_token(r)
                self.assertFalse(almacen.tiene_pendiente(CORREO))
        self.UsuarioDAO.assert_not_called()

    def test_login_verify_con_usuario_inexistente_responde_404(self):
        codigo = self.api._otp_login.crear(CORREO, {"id_usuario": ID_USUARIO})
        r = self._verificar(self.LOGIN_VERIFY, codigo)
        self.assertEqual(r.status_code, 404)
        self.assertEqual(r.get_json(), {"error": "Usuario no encontrado"})
        self._sin_token(r)

    def test_login_verify_con_bd_caida_no_gasta_el_codigo(self):
        codigo = self.api._otp_login.crear(CORREO, {"id_usuario": ID_USUARIO})
        self._bd_apagada()
        with self.assertLogs(self.api.app.logger, "ERROR"):
            r = self._verificar(self.LOGIN_VERIFY, codigo)
        self.assertEqual(r.status_code, 503)
        self._sin_token(r)
        self.assertTrue(self.api._otp_login.tiene_pendiente(CORREO))

        # Vuelve la BD: el mismo codigo sirve (no hay que iniciar sesion otra vez)
        self.obtener_conexion.return_value = self.conexion
        self.dao.consultar_por_correo.return_value = _usuario(
            version_politica_datos=self.api.VERSION_POLITICA_DATOS)
        r = self._verificar(self.LOGIN_VERIFY, codigo)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["token"], "token-falso")
        self.assertFalse(self.api._otp_login.tiene_pendiente(CORREO))   # ahora si se gasto

    def test_verify_con_bd_caida_no_crea_la_cuenta_ni_gasta_el_codigo(self):
        codigo = self._pendiente_de_registro()
        self._bd_apagada()
        with self.assertLogs(self.api.app.logger, "ERROR"):
            r = self._verificar(self.VERIFY, codigo)
        self.assertEqual(r.status_code, 503)
        self._sin_token(r)
        self.dao.insertar.assert_not_called()
        self.enviar_bienvenida.assert_not_called()
        self.assertTrue(self.api._otp_registro.tiene_pendiente(CORREO))

    def test_verify_si_no_se_puede_crear_la_cuenta_responde_500_sin_token(self):
        codigo = self._pendiente_de_registro()
        self.dao.insertar.return_value = False
        r = self._verificar(self.VERIFY, codigo)
        self.assertEqual(r.status_code, 500)
        self.assertEqual(r.get_json(), {"error": "Error al crear el usuario"})
        self._sin_token(r)
        self.enviar_bienvenida.assert_not_called()


# ---------------------------------------------------------------------------
# 7. POST /api/auth/register
# ---------------------------------------------------------------------------

class PruebasRegistro(_BaseEndpoints):

    def setUp(self):
        super().setUp()
        parche = mock.patch.object(self.api, "_validar_correo", return_value=(True, ""))
        self._validar_correo = parche.start()
        self.addCleanup(parche.stop)

    def _registrar(self, **cambios):
        cuerpo = {"name": "Laura Gomez", "email": CORREO, "password": CLAVE, "acepta_datos": True}
        cuerpo.update(cambios)
        return self.cliente.post("/api/auth/register", json=cuerpo)

    def _nada_enviado(self):
        self.enviar_codigo.assert_not_called()
        self.assertFalse(self.api._otp_registro.tiene_pendiente(CORREO))

    def test_campos_vacios_responden_400_sin_dns_ni_bd(self):
        for campo in ("name", "email", "password"):
            for valor in ("", "   ") if campo != "password" else ("",):
                with self.subTest(campo=campo, valor=repr(valor)):
                    r = self._registrar(**{campo: valor})
                    self.assertEqual(r.status_code, 400)
                    self.assertEqual(r.get_json(), {"error": "Nombre, correo y contrasena son requeridos"})
        self._validar_correo.assert_not_called()
        self.obtener_conexion.assert_not_called()
        self._nada_enviado()

    def test_correo_ya_registrado_responde_neutro_sin_enviar_codigo(self):
        # Item 4.10 (A-14): ya no hay 409. Mas casos en tests/test_registro_neutro.py
        self.dao.consultar_por_correo.return_value = _usuario()
        r = self._registrar()
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json(), {"message": "Codigo enviado", "email": CORREO})
        self._nada_enviado()
        self.enviar_aviso.assert_called_once_with(CORREO, "Laura")

    def test_bd_caida_responde_503_sin_enviar_codigo(self):
        self._bd_apagada()
        with self.assertLogs(self.api.app.logger, "ERROR"):
            r = self._registrar()
        self.assertEqual(r.status_code, 503)
        self._sin_datos_internos(r)
        self._nada_enviado()


# ---------------------------------------------------------------------------
# 8. POST /api/utils/validar-correo (DNS simulado)
# ---------------------------------------------------------------------------

class PruebasValidarCorreo(_BaseEndpoints):
    RUTA = "/api/utils/validar-correo"

    def setUp(self):
        super().setUp()
        parches = (
            mock.patch.object(self.api.dns.resolver, "resolve"),
            mock.patch.dict(self.api._mx_cache, clear=True),   # sin respuestas guardadas
        )
        self.resolve = parches[0].start()
        parches[1].start()
        for parche in parches:
            self.addCleanup(parche.stop)

    def _validar(self, email):
        r = self.cliente.post(self.RUTA, json={"email": email})
        self.assertEqual(r.status_code, 200)
        return r.get_json()

    def test_formato_malo_no_consulta_el_dns(self):
        for email, mensaje in (("", "El correo es requerido"),
                               ("laura@", "El formato del correo no es valido"),
                               ("laura.ejemplo.test", "El formato del correo no es valido")):
            with self.subTest(email=email):
                self.assertEqual(self._validar(email), {"valido": False, "mensaje": mensaje})
        self.resolve.assert_not_called()

    def test_dominio_sin_servidor_de_correo_no_es_valido(self):
        for error in (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
            with self.subTest(error=error.__name__):
                self.api._mx_cache.clear()
                self.resolve.side_effect = error
                respuesta = self._validar("laura@dominio-inventado.test")
                self.assertFalse(respuesta["valido"])
                self.assertIn("dominio-inventado.test", respuesta["mensaje"])

    def test_dominio_con_servidor_de_correo_es_valido(self):
        self.resolve.return_value = [object()]
        self.assertEqual(self._validar(CORREO),
                         {"valido": True, "mensaje": "El correo y el dominio son validos"})
        self.resolve.assert_called_once_with("ejemplo.test", "MX", lifetime=4)

    def test_dns_caido_no_bloquea_el_registro(self):
        self.resolve.side_effect = dns.exception.Timeout
        respuesta = self._validar(CORREO)
        self.assertTrue(respuesta["valido"])
        self.assertNotIn("ejemplo.test", self.api._mx_cache)   # un fallo temporal no se guarda

    # Item 4.6 (A-12): la memoria de dominios tiene tope (antes crecia sin limite)

    def _llenar(self, cantidad, desde=0):
        self.resolve.return_value = [object()]
        for i in range(desde, desde + cantidad):
            valido, _ = self.api._validar_correo(f"laura@dominio{i}.test")
            self.assertTrue(valido)

    def test_la_memoria_de_dominios_no_pasa_del_maximo(self):
        maximo = self.api.MX_CACHE_MAXIMO
        self.assertEqual(maximo, 1000)   # decision del dueno del 07/11/2026
        self._llenar(maximo + 500)
        self.assertEqual(len(self.api._mx_cache), maximo)
        self.assertFalse("dominio0.test" in self.api._mx_cache)          # los mas viejos se olvidan
        self.assertTrue(f"dominio{maximo + 499}.test" in self.api._mx_cache)  # los nuevos quedan

    def test_olvida_el_dominio_que_lleva_mas_tiempo_sin_usarse(self):
        maximo = self.api.MX_CACHE_MAXIMO
        self._llenar(maximo)
        self.resolve.reset_mock()
        self._llenar(1, desde=0)                 # dominio0 se vuelve a usar: sale de la memoria
        self.resolve.assert_not_called()
        self._llenar(1, desde=maximo)            # uno nuevo: se olvida dominio1, no dominio0
        self.assertTrue("dominio0.test" in self.api._mx_cache)
        self.assertFalse("dominio1.test" in self.api._mx_cache)
        self.assertEqual(len(self.api._mx_cache), maximo)


if __name__ == "__main__":
    unittest.main()
