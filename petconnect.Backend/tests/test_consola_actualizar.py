"""
Pruebas de regresion del item 4.19 de PRIORIDADES (A-18): la consola
(vista/menu_usuarios.py, opcion "6. Actualizar usuario") revisa los datos con las
mismas reglas que el registro y la API.

- Nombre, apellidos y formato del correo: security/datos_usuario.py (como el 4.11).
- Correo que ya es de OTRA cuenta: "Ese correo ya tiene una cuenta", sin repetir
  el correo (Ley 1581) y sin UPDATE, asi el mensaje de MySQL (que trae el correo)
  nunca llega a la pantalla. El correo de la misma cuenta si se acepta.
- Telefono: la regla de las solicitudes de adopcion, que paso de api.py a
  security/datos_usuario.py (validar_telefono). La usan la API, el registro y la
  actualizacion de la consola.
- Estado mal escrito: antes se ignoraba en silencio y la consola decia "[OK]".
- Dejar un dato vacio mantiene el valor actual; ante un error no se guarda nada.

No usan la base de datos (UsuarioDAO se simula), no leen .env ni consultan el
DNS. Datos inventados.

Ejecutar desde petconnect.Backend, con el entorno virtual activo:
    python -m unittest discover -s tests -v
"""
import contextlib
import copy
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
# se desactiva mientras se importa (como en test_consola_registro.py) y se restaura
import dotenv  # noqa: E402

_load_dotenv_original = dotenv.load_dotenv
dotenv.load_dotenv = lambda *a, **k: False
try:
    from vista import menu_usuarios  # noqa: E402
finally:
    dotenv.load_dotenv = _load_dotenv_original

from modelo.usuario import Usuario  # noqa: E402
from security import datos_usuario  # noqa: E402
from security.datos_usuario import validar_telefono  # noqa: E402
from test_consola_registro import _registro  # noqa: E402

ID = 7
ACTUAL = Usuario(id_usuario=ID, nombres="Laura Maria", apellidos="Perez-Gil",
                 correo="laura.actual@ejemplo.test", telefono="3001234567",
                 estado="activo", verificado=True)
CORREO_NUEVO = "laura.nueva@ejemplo.test"
CORREO_DE_OTRA = "otra.persona@ejemplo.test"
TELEFONOS_INVALIDOS = ("abc0000000", "300-000-0000", "123456", "1" * 16, "57+3000000000",
                       "+57 300 000 0000 0000")


class _Consola:
    """Ejecuta _actualizar_usuario con respuestas simuladas y guarda lo impreso.

    `textos` son, en orden: nombres, apellidos, correo, telefono y estado (el ID
    se agrega solo). Un texto vacio = "mantener el valor actual".
    """

    def __init__(self, textos, dueno_del_correo=None, actualizar_ok=True):
        self.textos = [str(ID)] + list(textos)
        self.dao = mock.MagicMock()
        self.dao.consultar_por_id.return_value = copy.copy(ACTUAL)
        self.dao.consultar_por_correo.return_value = dueno_del_correo
        self.dao.actualizar.return_value = actualizar_ok

    def _input(self, pregunta=""):
        # Si la consola sigue preguntando cuando debia detenerse: Enter vacio
        return self.textos.pop(0) if self.textos else ""

    def ejecutar(self):
        salida = io.StringIO()
        with mock.patch.object(menu_usuarios, "UsuarioDAO", return_value=self.dao), \
                mock.patch("builtins.input", side_effect=self._input), \
                contextlib.redirect_stdout(salida):
            menu_usuarios.MenuUsuarios()._actualizar_usuario()
        self.salida = salida.getvalue()
        return self

    @property
    def usuario_guardado(self):
        return self.dao.actualizar.call_args.args[0]

    def no_guardo(self, prueba):
        prueba.assertNotIn("[OK]", self.salida)
        self.dao.actualizar.assert_not_called()


def _actualizar(nombres="", apellidos="", correo="", telefono="", estado="", **kwargs):
    return _Consola([nombres, apellidos, correo, telefono, estado], **kwargs).ejecutar()


class PruebasNombreYApellidos(unittest.TestCase):
    """A-05 / A-18: el nombre nuevo cumple la misma regla que en el registro."""

    def test_nombre_con_url_no_se_guarda(self):
        consola = _actualizar(nombres="Visita https://sitio-falso.example")
        self.assertIn("El nombre debe tener", consola.salida)
        consola.no_guardo(self)

    def test_nombre_con_html_no_se_guarda(self):
        consola = _actualizar(nombres="<b>Laura</b>")
        self.assertIn("El nombre debe tener", consola.salida)
        consola.no_guardo(self)

    def test_apellidos_con_numeros_no_se_guardan(self):
        consola = _actualizar(apellidos="Perez 2026")
        self.assertIn("Los apellidos debe tener", consola.salida)
        consola.no_guardo(self)


class PruebasCorreo(unittest.TestCase):
    """A-18: formato del correo y correo de otra cuenta, sin mostrar el correo."""

    def test_correo_sin_formato_no_se_guarda(self):
        consola = _actualizar(correo="x")
        self.assertIn("El formato del correo no es valido", consola.salida)
        consola.dao.consultar_por_correo.assert_not_called()
        consola.no_guardo(self)

    def test_correo_de_121_caracteres_no_se_guarda(self):
        largo = "a" * (121 - len("@ejemplo.test")) + "@ejemplo.test"
        consola = _actualizar(correo=largo)
        self.assertIn("mas de 120", consola.salida)
        consola.no_guardo(self)

    def test_correo_de_otra_cuenta_avisa_sin_repetirlo(self):
        otra = Usuario(id_usuario=99, correo=CORREO_DE_OTRA)
        consola = _actualizar(correo=CORREO_DE_OTRA, dueno_del_correo=otra)
        self.assertIn("Ese correo ya tiene una cuenta", consola.salida)
        self.assertNotIn(CORREO_DE_OTRA, consola.salida)
        consola.dao.consultar_por_correo.assert_called_once_with(CORREO_DE_OTRA)
        consola.no_guardo(self)

    def test_correo_de_la_misma_cuenta_se_acepta(self):
        # Por ejemplo, el mismo correo con otras mayusculas (la BD no distingue)
        mismo = Usuario(id_usuario=ID, correo=ACTUAL.correo)
        consola = _actualizar(correo=ACTUAL.correo.upper(), dueno_del_correo=mismo)
        consola.dao.actualizar.assert_called_once()
        self.assertEqual(consola.usuario_guardado.correo, ACTUAL.correo.upper())

    def test_correo_libre_se_guarda(self):
        consola = _actualizar(correo=CORREO_NUEVO)
        consola.dao.actualizar.assert_called_once()
        self.assertEqual(consola.usuario_guardado.correo, CORREO_NUEVO)
        self.assertIn("[OK] Usuario actualizado", consola.salida)

    def test_la_consola_no_consulta_el_dns(self):
        import dns.resolver
        with mock.patch.object(dns.resolver, "resolve") as resolver:
            _actualizar(correo=CORREO_NUEVO)
        resolver.assert_not_called()


class PruebasTelefono(unittest.TestCase):
    """Item 4.19: el telefono sigue la regla de las solicitudes de adopcion."""

    def test_telefono_invalido_no_se_guarda_al_actualizar(self):
        for valor in TELEFONOS_INVALIDOS:
            with self.subTest(telefono=valor):
                consola = _actualizar(telefono=valor)
                self.assertIn("El teléfono solo puede tener", consola.salida)
                consola.no_guardo(self)

    def test_telefono_valido_se_guarda_al_actualizar(self):
        consola = _actualizar(telefono="+57 300 765 4321")
        self.assertEqual(consola.usuario_guardado.telefono, "+57 300 765 4321")

    def test_telefono_invalido_no_se_registra(self):
        # Opcion "1. Registrar usuario": ni siquiera pide la contrasena
        consola = _registro(telefono="abc0000000")
        self.assertIn("El teléfono solo puede tener", consola.salida)
        self.assertEqual(consola.preguntas_getpass, [])
        consola.dao.insertar.assert_not_called()
        consola.hash_password.assert_not_called()

    def test_registro_sin_telefono_se_acepta(self):
        consola = _registro(telefono="")
        consola.dao.insertar.assert_called_once()
        self.assertEqual(consola.usuario_guardado.telefono, "")


class PruebasEstado(unittest.TestCase):
    """Item 4.19: un estado mal escrito ya no se ignora en silencio."""

    def test_estado_mal_escrito_no_se_guarda(self):
        for valor in ("Activo", "bloquado", "eliminado"):
            with self.subTest(estado=valor):
                consola = _actualizar(nombres="Ana", estado=valor)
                self.assertIn("Estado no valido", consola.salida)
                consola.no_guardo(self)

    def test_estado_valido_se_guarda(self):
        consola = _actualizar(estado="bloqueado")
        self.assertEqual(consola.usuario_guardado.estado, "bloqueado")


class PruebasValoresActuales(unittest.TestCase):
    """Lo que ya funcionaba: vacio mantiene y un cambio valido se guarda."""

    def test_todo_vacio_mantiene_los_valores(self):
        consola = _actualizar()
        consola.dao.consultar_por_correo.assert_not_called()
        guardado = consola.usuario_guardado
        self.assertEqual(
            (guardado.nombres, guardado.apellidos, guardado.correo, guardado.telefono,
             guardado.estado),
            (ACTUAL.nombres, ACTUAL.apellidos, ACTUAL.correo, ACTUAL.telefono, ACTUAL.estado))

    def test_cambio_valido_guarda_todo(self):
        consola = _actualizar("Ana Lucia", "Gomez", CORREO_NUEVO, "3109876543", "inactivo")
        guardado = consola.usuario_guardado
        self.assertEqual(
            (guardado.nombres, guardado.apellidos, guardado.correo, guardado.telefono,
             guardado.estado),
            ("Ana Lucia", "Gomez", CORREO_NUEVO, "3109876543", "inactivo"))
        self.assertIn("[OK] Usuario actualizado", consola.salida)

    def test_si_el_update_falla_lo_dice(self):
        consola = _actualizar(nombres="Ana", actualizar_ok=False)
        self.assertIn("No se pudo actualizar", consola.salida)
        self.assertNotIn("[OK]", consola.salida)


class PruebasReglaComunDelTelefono(unittest.TestCase):
    """La API y la consola usan la misma funcion; los limites no cambiaron."""

    def test_la_consola_usa_la_funcion_comun(self):
        self.assertIs(getattr(menu_usuarios, "validar_telefono", None),
                      datos_usuario.validar_telefono)

    def test_la_api_usa_la_funcion_comun(self):
        from test_errores import _importar_api
        api = _importar_api()
        self.assertIs(api._validar_telefono, validar_telefono)

    def test_reglas_del_telefono(self):
        for valido in ("", "3001234567", "+57 300 123 4567", "1234567", "1" * 15):
            self.assertIsNone(validar_telefono(valido), valido)
        for invalido in TELEFONOS_INVALIDOS + ("1" * 21, "++573000000000"):
            self.assertIsNotNone(validar_telefono(invalido), invalido)

    def test_el_mensaje_no_repite_el_dato(self):
        self.assertNotIn("abc0000000", validar_telefono("abc0000000"))


if __name__ == "__main__":
    unittest.main()
