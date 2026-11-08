"""
Pruebas de regresion de A-18 (item 4.11 de PRIORIDADES): la consola
(vista/menu_usuarios.py, opcion "1. Registrar usuario") registra con las mismas
reglas que la API.

- La contrasena se pide con getpass (no se ve en pantalla), dos veces, y se
  guarda tal cual: sin .strip(), como /api/auth/register.
- Pasa por validar_contrasena (security/politica.py): PETCONNECT1! se rechaza.
- Nombre, apellidos y formato del correo usan security/datos_usuario.py, el
  mismo modulo que la API (sin DNS y sin importar api.py, A-41).
- Correo repetido: "ese correo ya tiene una cuenta", sin repetir el correo
  (Ley 1581), sin calcular bcrypt y sin INSERT.
- La autorizacion de datos NO se inventa: la cuenta queda con acepta_datos =
  False, sin fecha ni version, y la consola lo avisa (politica C.6 y C.10).

No usan la base de datos (UsuarioDAO se simula), no leen .env, no consultan el
DNS ni calculan bcrypt (hash_password se simula). Datos inventados.

Ejecutar desde petconnect.Backend, con el entorno virtual activo:
    python -m unittest discover -s tests -v
"""
import ast
import contextlib
import io
import os
import sys
import unittest
from unittest import mock

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

# El paquete security/ carga crypto.py y jwt_helper.py, que exigen estas claves
# al importarse. Son claves de prueba: no se lee el .env.
from cryptography.fernet import Fernet  # noqa: E402

os.environ.setdefault("FERNET_KEY", Fernet.generate_key().decode())
os.environ.setdefault("JWT_SECRET", "clave-de-pruebas-petconnect-" + "x" * 32)

# vista.menu_usuarios -> dao -> conexion -> config.db_config llama a load_dotenv():
# se desactiva mientras se importa (como en test_correo.py) y luego se restaura
import dotenv  # noqa: E402

_load_dotenv_original = dotenv.load_dotenv
dotenv.load_dotenv = lambda *a, **k: False
try:
    from vista import menu_usuarios  # noqa: E402
finally:
    dotenv.load_dotenv = _load_dotenv_original

from security import datos_usuario  # noqa: E402
from security.datos_usuario import validar_formato_correo, validar_nombre  # noqa: E402

NOMBRES = "Laura Maria"
APELLIDOS = "Perez-Gil"
CORREO = "laura.consola@ejemplo.test"
TELEFONO = "3001234567"
VALIDA = "Petconnect1!"
HASH_FALSO = "$2b$12$" + "h" * 53     # 60 caracteres, como un hash bcrypt


class _Consola:
    """Ejecuta _registrar_usuario con respuestas simuladas y guarda lo impreso."""

    def __init__(self, textos, claves, dao_existente=None, insertar_ok=True):
        self.textos = list(textos)          # respuestas a input(), en orden
        self.claves = list(claves)          # respuestas a getpass(), en orden
        self.preguntas_input = []
        self.preguntas_getpass = []
        self.dao = mock.MagicMock()
        self.dao.consultar_por_correo.return_value = dao_existente

        def insertar(usuario):
            usuario.id_usuario = 41
            return insertar_ok
        self.dao.insertar.side_effect = insertar

    def _input(self, pregunta=""):
        self.preguntas_input.append(pregunta)
        if self.textos:
            return self.textos.pop(0)
        # Sin mas textos: la persona escribe la contrasena en un input() visible
        # (lo que hacia el codigo viejo). Asi la contraprueba falla por el
        # comportamiento y no por un nombre que no existe. Si tampoco hay claves,
        # la consola siguio preguntando cuando debia detenerse: Enter vacio.
        return self.claves.pop(0) if self.claves else ""

    def _getpass(self, pregunta=""):
        self.preguntas_getpass.append(pregunta)
        return self.claves.pop(0)

    def ejecutar(self):
        salida = io.StringIO()
        with mock.patch.object(menu_usuarios, "UsuarioDAO", return_value=self.dao), \
                mock.patch("builtins.input", side_effect=self._input), \
                mock.patch.object(menu_usuarios, "getpass", side_effect=self._getpass,
                                  create=True), \
                mock.patch.object(menu_usuarios, "hash_password",
                                  return_value=HASH_FALSO) as self.hash_password, \
                contextlib.redirect_stdout(salida):
            menu_usuarios.MenuUsuarios()._registrar_usuario()
        self.salida = salida.getvalue()
        return self

    @property
    def usuario_guardado(self):
        return self.dao.insertar.call_args.args[0]


def _registro(nombres=NOMBRES, apellidos=APELLIDOS, correo=CORREO, telefono=TELEFONO,
              clave=VALIDA, confirmacion=None, **kwargs):
    confirmacion = clave if confirmacion is None else confirmacion
    return _Consola([nombres, apellidos, correo, telefono], [clave, confirmacion], **kwargs).ejecutar()


class PruebasContrasenaOculta(unittest.TestCase):
    """A-18: la contrasena no se ve en pantalla y se guarda como se escribio."""

    def test_la_contrasena_se_pide_con_getpass_dos_veces(self):
        consola = _registro()
        self.assertEqual(len(consola.preguntas_getpass), 2)
        for pregunta in consola.preguntas_input:
            self.assertNotIn("contrasena", pregunta.lower())

    def test_los_espacios_de_la_contrasena_se_conservan(self):
        # Como la API: si se recortaran, " Petconnect1! " no serviria al entrar por la web
        clave = " Petconnect1! "
        consola = _registro(clave=clave)
        consola.hash_password.assert_called_once_with(clave)
        consola.dao.insertar.assert_called_once()

    def test_la_salida_nunca_muestra_la_contrasena(self):
        for consola in (_registro(), _registro(confirmacion="Otra1234!"),
                        _registro(clave="PETCONNECT1!")):
            self.assertNotIn("Petconnect1!", consola.salida)
            self.assertNotIn("PETCONNECT1!", consola.salida)
            self.assertNotIn("Otra1234!", consola.salida)

    def test_confirmacion_distinta_no_guarda(self):
        consola = _registro(confirmacion="Petconnect1?")
        self.assertIn("no coinciden", consola.salida)
        consola.dao.insertar.assert_not_called()
        consola.hash_password.assert_not_called()

    def test_contrasena_vacia_no_guarda(self):
        consola = _Consola([NOMBRES, APELLIDOS, CORREO, TELEFONO], [""]).ejecutar()
        self.assertIn("obligatorios", consola.salida)
        consola.dao.insertar.assert_not_called()


class PruebasPoliticaContrasena(unittest.TestCase):
    """A-18 / NC-004: la consola usa la misma politica que la API (security/politica.py)."""

    def test_sin_minuscula_se_rechaza(self):
        consola = _registro(clave="PETCONNECT1!")
        self.assertIn("al menos una minuscula", consola.salida)
        consola.dao.insertar.assert_not_called()
        consola.hash_password.assert_not_called()

    def test_corta_se_rechaza(self):
        consola = _registro(clave="Abc12!x")
        self.assertIn("al menos 8", consola.salida)
        consola.dao.insertar.assert_not_called()

    def test_la_consola_llama_a_validar_contrasena(self):
        with mock.patch.object(menu_usuarios, "validar_contrasena", create=True,
                               return_value="regla simulada") as validar:
            consola = _registro()
        validar.assert_called_once_with(VALIDA)
        self.assertIn("regla simulada", consola.salida)
        consola.dao.insertar.assert_not_called()


class PruebasNombreYCorreo(unittest.TestCase):
    """A-18 / A-05: nombre, apellidos y correo con las reglas de la API, sin DNS."""

    def test_nombre_con_url_se_rechaza_antes_de_la_bd(self):
        consola = _Consola(["Visita https://sitio-falso.example"], []).ejecutar()
        self.assertIn("El nombre debe tener", consola.salida)
        consola.dao.consultar_por_correo.assert_not_called()
        consola.dao.insertar.assert_not_called()

    def test_nombre_vacio_se_rechaza(self):
        consola = _Consola([""], []).ejecutar()
        self.assertIn("obligatorios", consola.salida)
        consola.dao.insertar.assert_not_called()

    def test_apellidos_con_numeros_se_rechazan(self):
        consola = _Consola([NOMBRES, "Perez 2026"], []).ejecutar()
        self.assertIn("Los apellidos debe tener", consola.salida)
        consola.dao.insertar.assert_not_called()

    def test_apellidos_vacios_se_aceptan(self):
        consola = _registro(apellidos="")
        consola.dao.insertar.assert_called_once()
        self.assertEqual(consola.usuario_guardado.apellidos, "")

    def test_correo_sin_formato_se_rechaza(self):
        consola = _Consola([NOMBRES, APELLIDOS, "laura-sin-arroba"], []).ejecutar()
        self.assertIn("El formato del correo no es valido", consola.salida)
        consola.dao.consultar_por_correo.assert_not_called()
        consola.dao.insertar.assert_not_called()

    def test_correo_de_121_caracteres_se_rechaza(self):
        largo = "a" * (121 - len("@ejemplo.test")) + "@ejemplo.test"
        self.assertEqual(len(largo), 121)
        consola = _Consola([NOMBRES, APELLIDOS, largo], []).ejecutar()
        self.assertIn("mas de 120", consola.salida)
        consola.dao.insertar.assert_not_called()

    def test_la_consola_no_consulta_el_dns(self):
        import dns.resolver
        with mock.patch.object(dns.resolver, "resolve") as resolver:
            _registro()
        resolver.assert_not_called()


class PruebasCorreoRepetido(unittest.TestCase):
    """A-18: correo con cuenta: aviso claro (consola del administrador) sin el correo."""

    def test_correo_repetido_no_guarda_ni_calcula_bcrypt(self):
        consola = _Consola([NOMBRES, APELLIDOS, CORREO], [], dao_existente=object()).ejecutar()
        self.assertIn("Ese correo ya tiene una cuenta", consola.salida)
        self.assertNotIn(CORREO, consola.salida)
        consola.dao.consultar_por_correo.assert_called_once_with(CORREO)
        consola.dao.insertar.assert_not_called()
        consola.hash_password.assert_not_called()
        self.assertEqual(consola.preguntas_getpass, [])   # ni siquiera pide la contrasena


class PruebasAutorizacionDatos(unittest.TestCase):
    """A-18 / NC-005: la consola no afirma una autorizacion que el titular no dio."""

    def test_registro_valido_guarda_sin_autorizacion(self):
        consola = _registro()
        usuario = consola.usuario_guardado
        self.assertIs(usuario.acepta_datos, False)
        self.assertIsNone(usuario.fecha_autorizacion_datos)
        self.assertIsNone(usuario.version_politica_datos)
        self.assertEqual(usuario.password_hash, HASH_FALSO)
        self.assertEqual((usuario.nombres, usuario.apellidos, usuario.correo, usuario.telefono),
                         (NOMBRES, APELLIDOS, CORREO, TELEFONO))

    def test_la_consola_avisa_que_falta_la_autorizacion(self):
        consola = _registro()
        self.assertIn("Usuario registrado con ID: 41", consola.salida)
        self.assertIn("SIN autorizacion de tratamiento de datos", consola.salida)

    def test_si_el_insert_falla_no_se_muestra_el_aviso(self):
        consola = _registro(insertar_ok=False)
        self.assertIn("No se pudo registrar", consola.salida)
        self.assertNotIn("SIN autorizacion", consola.salida)


class PruebasModuloComun(unittest.TestCase):
    """A-18 / A-41: la API y la consola usan las mismas funciones; la consola no importa api.py."""

    def test_menu_usuarios_no_importa_api(self):
        with open(os.path.join(RAIZ, "vista", "menu_usuarios.py"), encoding="utf-8") as archivo:
            arbol = ast.parse(archivo.read())
        modulos = set()
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.Import):
                modulos.update(alias.name.split(".")[0] for alias in nodo.names)
            elif isinstance(nodo, ast.ImportFrom) and nodo.module:
                modulos.add(nodo.module.split(".")[0])
        self.assertNotIn("api", modulos)

    def test_la_consola_usa_las_funciones_comunes(self):
        self.assertIs(getattr(menu_usuarios, "validar_nombre", None), datos_usuario.validar_nombre)
        self.assertIs(getattr(menu_usuarios, "validar_formato_correo", None),
                      datos_usuario.validar_formato_correo)

    def test_la_api_usa_las_funciones_comunes(self):
        from test_errores import _importar_api
        api = _importar_api()
        self.assertIs(api._validar_nombre, validar_nombre)
        with mock.patch.object(api, "validar_formato_correo", return_value="regla simulada"), \
                mock.patch.object(api.dns.resolver, "resolve") as resolver:
            self.assertEqual(api._validar_correo(CORREO), (False, "regla simulada"))
        resolver.assert_not_called()

    def test_reglas_del_nombre(self):
        for valido in ("Ana", "Maria Jose", "O'Neil", "Perez-Gil", "Ma. Jose", "Íñigo Muñoz"):
            self.assertIsNone(validar_nombre(valido), valido)
        for invalido in ("A", "Ana2", "https://x.example", "<b>Ana</b>", "a" * 61, " Ana"):
            self.assertIsNotNone(validar_nombre(invalido), invalido)

    def test_mensaje_del_nombre_por_defecto_igual_al_de_la_api(self):
        self.assertTrue(validar_nombre("A").startswith("El nombre debe tener entre 2 y 60"))
        self.assertTrue(validar_nombre("A", "Los apellidos").startswith("Los apellidos debe"))

    def test_reglas_del_correo(self):
        self.assertIsNone(validar_formato_correo(CORREO))
        self.assertIsNone(validar_formato_correo("  " + CORREO + "  "))
        self.assertEqual(validar_formato_correo(""), "El correo es requerido")
        self.assertEqual(validar_formato_correo(None), "El correo es requerido")
        self.assertEqual(validar_formato_correo("a@b"), "El formato del correo no es valido")
        self.assertIn("mas de 120", validar_formato_correo("a" * 110 + "@ejemplo.test"))

    def test_los_mensajes_no_repiten_el_dato(self):
        self.assertNotIn("sitio-falso", validar_nombre("https://sitio-falso.example"))
        self.assertNotIn("laura-sin-arroba", validar_formato_correo("laura-sin-arroba"))


if __name__ == "__main__":
    unittest.main()
