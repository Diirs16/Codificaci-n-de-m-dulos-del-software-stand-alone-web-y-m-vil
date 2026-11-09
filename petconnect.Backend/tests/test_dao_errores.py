"""
Pruebas de regresion del item 4.15 de PRIORIDADES (parte 1): los DAO dejan subir los
errores de la base de datos y nunca imprimen el mensaje de MySQL.

Antes MascotaDAO y ProductoDAO atrapaban el error, hacian print del mensaje (puede
traer un correo: "Duplicate entry 'correo@...'", Ley 1581) y devolvian None, [] o
False. Si la API los usara asi, sin BD diria "no encontrado" (404) o una lista vacia
en vez de 503. Estas pruebas cuidan:

- Cada metodo publico de los DAO que ya propagan (MascotaDAO, ProductoDAO,
  SolicitudDAO y OtpDAO) deja subir el error de MySQL y el InterfaceError de "no hay
  conexion", sin imprimir nada.
- La consola (vista/menu_mascotas.py y vista/menu_productos.py) atrapa ese error en
  su ciclo, muestra un aviso con el numero del error pero SIN el mensaje de MySQL, y
  vuelve al menu en vez de cerrarse con una traza.

UsuarioDAO y ProveedorDAO todavia se tragan los errores (fuera del 4.15).

No usan la base real ni leen .env (_importar_api; lo vigila test_sin_env_real.py).
Los correos son inventados (Ley 1581).

Ejecutar desde petconnect.Backend, con el entorno virtual activo:
    python -m unittest discover -s tests -p "test_dao_errores.py" -v
"""
import contextlib
import importlib
import inspect
import io
import os
import sys
import unittest
from unittest import mock

from mysql.connector import errors as errores_bd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_errores import _importar_api  # noqa: E402

CORREO = "dueno.repetido@ejemplo.test"      # inventado (Ley 1581)

# DAO que propagan los errores y cuantos metodos publicos tiene cada uno. Si se
# agrega un metodo, la cuenta falla y obliga a mirarlo.
DAOS_QUE_PROPAGAN = {
    ("dao.mascota_dao", "MascotaDAO"): 7,
    ("dao.producto_dao", "ProductoDAO"): 7,
    ("dao.solicitud_dao", "SolicitudDAO"): 2,
    ("dao.otp_dao", "OtpDAO"): 7,
}


def _error_con_correo(errno=1062):
    """Error de MySQL cuyo mensaje trae un dato personal, como los reales."""
    return errores_bd.IntegrityError(
        msg=f"Duplicate entry '{CORREO}' for key 'correo'", errno=errno)


class PruebasDAOPropaganErrores(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        _importar_api()     # antes de importar dao/: asi config/ no carga el .env

    def _metodos(self):
        for (modulo, clase), _ in DAOS_QUE_PROPAGAN.items():
            dao_clase = getattr(importlib.import_module(modulo), clase)
            for nombre, funcion in inspect.getmembers(dao_clase, inspect.isfunction):
                if not nombre.startswith("_"):
                    yield clase, dao_clase, nombre, funcion

    def _llamar(self, dao_clase, nombre, funcion, obtener_conexion):
        """Llama el metodo con argumentos falsos; devuelve lo que imprimio."""
        dao = dao_clase()
        dao._conexion_bd = mock.Mock(obtener_conexion=obtener_conexion)
        argumentos = [mock.MagicMock() for _ in list(inspect.signature(funcion).parameters)[1:]]
        salida = io.StringIO()
        with contextlib.redirect_stdout(salida):
            getattr(dao, nombre)(*argumentos)
        return salida.getvalue()

    def test_se_revisan_todos_los_metodos(self):
        for (modulo, clase), esperados in DAOS_QUE_PROPAGAN.items():
            with self.subTest(dao=clase):
                nombres = [n for c, _, n, _ in self._metodos() if c == clase]
                self.assertEqual(len(nombres), esperados, nombres)

    def test_el_error_de_mysql_sube_y_no_se_imprime(self):
        for clase, dao_clase, nombre, funcion in self._metodos():
            with self.subTest(metodo=f"{clase}.{nombre}"):
                conexion = mock.MagicMock()
                conexion.cursor.return_value.execute.side_effect = _error_con_correo()
                salida = io.StringIO()
                with contextlib.redirect_stdout(salida), \
                        self.assertRaises(errores_bd.IntegrityError):
                    self._llamar(dao_clase, nombre, funcion, lambda: conexion)
                self.assertEqual(salida.getvalue(), "", "el DAO no debe imprimir nada")

    def test_sin_conexion_sube_interface_error(self):
        # Con el codigo viejo devolvian None/[]/False: la API habria dicho 404
        for clase, dao_clase, nombre, funcion in self._metodos():
            with self.subTest(metodo=f"{clase}.{nombre}"):
                salida = io.StringIO()
                with contextlib.redirect_stdout(salida), \
                        self.assertRaises(errores_bd.InterfaceError):
                    self._llamar(dao_clase, nombre, funcion, lambda: None)
                self.assertEqual(salida.getvalue(), "")


class PruebasConsolaAvisaErrorBD(unittest.TestCase):
    """La consola no se cierra con una traza ni muestra el mensaje de MySQL."""

    @classmethod
    def setUpClass(cls):
        _importar_api()
        cls.MenuMascotas = importlib.import_module("vista.menu_mascotas").MenuMascotas
        cls.MenuProductos = importlib.import_module("vista.menu_productos").MenuProductos

    def _correr(self, menu, entradas):
        """Corre el menu con las teclas dadas (la ultima debe ser "0") y devuelve lo impreso."""
        salida = io.StringIO()
        with mock.patch("builtins.input", side_effect=entradas), \
                contextlib.redirect_stdout(salida):
            menu.mostrar_menu()      # si el error se escapara, la prueba fallaria aqui
        return salida.getvalue()

    def _menu(self, clase, atributo, **errores):
        menu = clase()
        dao = mock.MagicMock()
        for metodo, error in errores.items():
            getattr(dao, metodo).side_effect = error
        setattr(menu, atributo, dao)
        return menu

    def _assert_aviso_sin_datos(self, texto, codigo):
        self.assertIn(f"codigo MySQL {codigo}", texto)
        self.assertNotIn(CORREO, texto)
        self.assertNotIn("Duplicate entry", texto)
        self.assertNotIn("Traceback", texto)

    def test_mascotas_consultar_con_error_avisa_y_vuelve_al_menu(self):
        menu = self._menu(self.MenuMascotas, "_mascota_dao", consultar_todos=_error_con_correo())
        texto = self._correr(menu, ["2", "0"])
        self._assert_aviso_sin_datos(texto, 1062)
        # Volvio a mostrar el menu despues del aviso
        self.assertEqual(texto.count("GESTION DE MASCOTAS"), 2)

    def test_mascotas_eliminar_con_error_a_mitad_avisa(self):
        # 1451: la mascota tiene solicitudes que la referencian (llave foranea)
        menu = self._menu(self.MenuMascotas, "_mascota_dao", eliminar=_error_con_correo(1451))
        texto = self._correr(menu, ["7", "5", "s", "0"])
        self._assert_aviso_sin_datos(texto, 1451)
        self.assertNotIn("eliminada correctamente", texto)

    def test_productos_consultar_con_error_avisa_y_vuelve_al_menu(self):
        menu = self._menu(self.MenuProductos, "_producto_dao", consultar_todos=_error_con_correo())
        texto = self._correr(menu, ["2", "0"])
        self._assert_aviso_sin_datos(texto, 1062)
        self.assertEqual(texto.count("GESTION DE PRODUCTOS"), 2)

    def test_sin_conexion_avisa_que_la_bd_no_respondio(self):
        sin_bd = errores_bd.InterfaceError("No hay conexion con la base de datos")
        for clase, atributo, titulo in ((self.MenuMascotas, "_mascota_dao", "MASCOTAS"),
                                        (self.MenuProductos, "_producto_dao", "PRODUCTOS")):
            with self.subTest(menu=titulo):
                menu = self._menu(clase, atributo, consultar_todos=sin_bd)
                texto = self._correr(menu, ["2", "0"])
                self.assertIn("La base de datos no respondio", texto)
                self.assertNotIn("No hay conexion", texto)     # el mensaje interno no sale


if __name__ == "__main__":
    unittest.main()
