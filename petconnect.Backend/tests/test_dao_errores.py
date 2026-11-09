"""
Pruebas de regresion de los items 4.15 y 4.21 de PRIORIDADES: los DAO dejan subir los
errores de la base de datos y nunca imprimen el mensaje de MySQL, y el SQL vive solo
en dao/, no en api.py (4.15, parte 2).

Antes los DAO atrapaban el error, hacian print del mensaje (puede traer un correo:
"Duplicate entry 'correo@...'", Ley 1581) y devolvian None, [] o False. Asi, sin BD,
la API diria "no encontrado" (404) o una lista vacia en vez de 503, y la consola
tomaria un correo como "libre". El 4.15 lo arreglo en MascotaDAO y ProductoDAO; el
4.21, en UsuarioDAO y ProveedorDAO. Estas pruebas cuidan:

- Cada metodo publico de TODOS los DAO de dao/ deja subir el error de MySQL y el
  InterfaceError de "no hay conexion", sin imprimir nada. Un DAO nuevo que no este
  en DAOS_QUE_PROPAGAN hace fallar la prueba (asi no vuelve a pasar).
- La consola (menus de mascotas, productos, usuarios y proveedores) atrapa ese error
  en su ciclo, muestra un aviso con el numero del error pero SIN el mensaje de MySQL,
  y vuelve al menu en vez de cerrarse con una traza.
- api.py no tiene SQL: ningun texto con SELECT ... FROM, INSERT INTO, UPDATE ... SET
  o DELETE FROM, ni cursor.execute ni conexion_y_cursor (regla de
  petconnect.Backend/CLAUDE.md). Que las rutas sigan respondiendo igual lo cuidan
  test_mascotas.py, test_endpoints.py y test_errores.py, que no cambiaron.

No usan la base real ni leen .env (_importar_api; lo vigila test_sin_env_real.py).
Los correos son inventados (Ley 1581).

Ejecutar desde petconnect.Backend, con el entorno virtual activo:
    python -m unittest discover -s tests -p "test_dao_errores.py" -v
"""
import ast
import contextlib
import importlib
import inspect
import io
import os
import re
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
    ("dao.mascota_dao", "MascotaDAO"): 10,      # 7 + 3 de la API (parte 2)
    ("dao.producto_dao", "ProductoDAO"): 9,     # 7 + 2 de la API (parte 2)
    ("dao.solicitud_dao", "SolicitudDAO"): 2,
    ("dao.otp_dao", "OtpDAO"): 7,
    ("dao.usuario_dao", "UsuarioDAO"): 11,      # item 4.21 (2 ya propagaban desde el 4.13)
    ("dao.proveedor_dao", "ProveedorDAO"): 7,   # item 4.21
}

CARPETA_DAO = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dao")


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

    def test_todos_los_dao_de_la_carpeta_estan_en_la_lista(self):
        # Item 4.21: ya no queda ningun DAO que se trague los errores. Si se crea uno
        # nuevo, debe entrar en DAOS_QUE_PROPAGAN (y pasar estas pruebas).
        en_la_carpeta = sorted(f"dao.{archivo[:-3]}" for archivo in os.listdir(CARPETA_DAO)
                               if archivo.endswith("_dao.py"))
        self.assertEqual(en_la_carpeta, sorted(modulo for modulo, _ in DAOS_QUE_PROPAGAN))

    def test_ningun_dao_usa_print(self):
        # print mostraria el mensaje de MySQL, que puede traer un correo (Ley 1581)
        for archivo in sorted(os.listdir(CARPETA_DAO)):
            if archivo.endswith(".py"):
                with self.subTest(archivo=archivo):
                    with open(os.path.join(CARPETA_DAO, archivo), encoding="utf-8") as f:
                        llamadas = [n.func.id for n in ast.walk(ast.parse(f.read()))
                                    if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)]
                    self.assertNotIn("print", llamadas)

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
        cls.MenuUsuarios = importlib.import_module("vista.menu_usuarios").MenuUsuarios
        cls.MenuProveedores = importlib.import_module("vista.menu_proveedores").MenuProveedores
        cls.Usuario = importlib.import_module("modelo.usuario").Usuario

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
                                        (self.MenuProductos, "_producto_dao", "PRODUCTOS"),
                                        (self.MenuUsuarios, "_usuario_dao", "USUARIOS"),
                                        (self.MenuProveedores, "_proveedor_dao", "PROVEEDORES")):
            with self.subTest(menu=titulo):
                menu = self._menu(clase, atributo, consultar_todos=sin_bd)
                texto = self._correr(menu, ["2", "0"])
                self.assertIn("La base de datos no respondio", texto)
                self.assertNotIn("No hay conexion", texto)     # el mensaje interno no sale
                self.assertEqual(texto.count(f"GESTION DE {titulo}"), 2)

    # --- Item 4.21: usuarios y proveedores --------------------------------------

    def test_usuarios_consultar_con_error_avisa_y_vuelve_al_menu(self):
        menu = self._menu(self.MenuUsuarios, "_usuario_dao", consultar_todos=_error_con_correo())
        texto = self._correr(menu, ["2", "0"])
        self._assert_aviso_sin_datos(texto, 1062)
        self.assertEqual(texto.count("GESTION DE USUARIOS"), 2)

    def test_actualizar_usuario_con_correo_repetido_a_la_vez_no_muestra_el_correo(self):
        # Lo que quedo del 4.19: la consola reviso el correo y estaba libre, pero otro
        # administrador lo guardo antes del UPDATE. MySQL responde 1062 con el correo
        # en el mensaje; antes el print del DAO lo mostraba.
        menu = self._menu(self.MenuUsuarios, "_usuario_dao", actualizar=_error_con_correo())
        menu._usuario_dao.consultar_por_id.return_value = self.Usuario(
            id_usuario=7, nombres="Laura", apellidos="Perez",
            correo="laura.actual@ejemplo.test", estado="activo")
        menu._usuario_dao.consultar_por_correo.return_value = None     # "libre" al revisar
        #                         ID   nombre apellido correo  telefono estado
        texto = self._correr(menu, ["6", "7", "", "", CORREO, "", "", "0"])
        menu._usuario_dao.actualizar.assert_called_once()
        self._assert_aviso_sin_datos(texto, 1062)
        self.assertNotIn("[OK]", texto)

    def test_registrar_usuario_sin_bd_no_toma_el_correo_como_libre(self):
        # Antes consultar_por_correo devolvia None sin BD: la consola seguia como si el
        # correo estuviera libre. Ahora el error sube y no se pide nada mas.
        sin_bd = errores_bd.InterfaceError("No hay conexion con la base de datos")
        menu = self._menu(self.MenuUsuarios, "_usuario_dao", consultar_por_correo=sin_bd)
        #                         nombres  apellidos correo
        texto = self._correr(menu, ["1", "Laura", "", CORREO, "0"])
        self.assertIn("La base de datos no respondio", texto)
        menu._usuario_dao.insertar.assert_not_called()
        self.assertNotIn("[OK]", texto)

    def test_proveedores_eliminar_con_error_a_mitad_avisa(self):
        menu = self._menu(self.MenuProveedores, "_proveedor_dao",
                          eliminar=_error_con_correo(1451))
        texto = self._correr(menu, ["7", "5", "s", "0"])
        self._assert_aviso_sin_datos(texto, 1451)
        self.assertNotIn("eliminado correctamente", texto)
        self.assertEqual(texto.count("GESTION DE PROVEEDORES"), 2)

    def test_proveedores_registrar_con_error_avisa(self):
        menu = self._menu(self.MenuProveedores, "_proveedor_dao", insertar=_error_con_correo())
        # nombre, tipo y numero de documento, telefono, correo, direccion, ciudad,
        # descripcion, horario y 24/7
        datos = ["Vet Prueba", "NIT", "900000000", "3000000000", CORREO, "Calle 1",
                 "Bogota", "Consulta general", "Lun-Vie", "n"]
        texto = self._correr(menu, ["1", *datos, "0"])
        self._assert_aviso_sin_datos(texto, 1062)
        self.assertNotIn("[OK]", texto)

    def test_mascotas_registrar_con_fallo_de_usuario_dao_avisa(self):
        # menu_mascotas tambien usa UsuarioDAO (para revisar el dueno): ya atrapaba
        # los errores desde el 4.15, esto lo deja probado.
        sin_bd = errores_bd.InterfaceError("No hay conexion con la base de datos")
        menu = self._menu(self.MenuMascotas, "_usuario_dao", consultar_por_id=sin_bd)
        texto = self._correr(menu, ["1", "3", "0"])
        self.assertIn("La base de datos no respondio", texto)
        self.assertNotIn("[OK]", texto)


RUTA_API = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "api.py")

# Sentencias SQL escritas en mayusculas, como en los DAO
_PARECE_SQL = re.compile(
    r"\bSELECT\b.*\bFROM\b|\bINSERT\s+INTO\b|\bUPDATE\s+\w+\s+SET\b|\bDELETE\s+FROM\b",
    re.DOTALL)


class PruebasSQLSoloEnDAO(unittest.TestCase):
    """Parte 2: el SQL de productos y mascotas salio de api.py a dao/."""

    @classmethod
    def setUpClass(cls):
        # Se lee el texto del archivo (no se importa): no ejecuta nada ni lee el .env
        with open(RUTA_API, encoding="utf-8") as archivo:
            cls.codigo = archivo.read()

    def test_ningun_texto_de_api_es_una_consulta_sql(self):
        textos = [nodo.value for nodo in ast.walk(ast.parse(self.codigo))
                  if isinstance(nodo, ast.Constant) and isinstance(nodo.value, str)]
        consultas = [" ".join(t.split())[:80] for t in textos if _PARECE_SQL.search(t)]
        self.assertEqual(consultas, [], "el SQL va en dao/, no en api.py")

    def test_verificar_bd_solo_se_usa_al_arrancar(self):
        # Item 4.21: con todos los DAO propagando, las rutas no necesitan comprobar la
        # BD antes (el error sube solo y se responde 503). _verificar_bd() queda solo
        # en "if __name__ == '__main__'", fuera de toda funcion.
        arbol = ast.parse(self.codigo)
        dentro_de_funciones = []
        for funcion in ast.walk(arbol):
            if isinstance(funcion, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for nodo in ast.walk(funcion):
                    if (isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Name)
                            and nodo.func.id == "_verificar_bd"):
                        dentro_de_funciones.append(f"{funcion.name} (linea {nodo.lineno})")
        self.assertEqual(dentro_de_funciones, [])
        self.assertIn("_verificar_bd()", self.codigo)      # sigue el chequeo al arrancar

    def test_api_no_usa_cursores(self):
        for pista in ("cursor.execute", "conexion_y_cursor", ".cursor("):
            with self.subTest(pista=pista):
                # assertFalse y no assertNotIn: si falla, no imprime todo api.py
                self.assertFalse(pista in self.codigo, f"api.py usa {pista}: el SQL va en dao/")


if __name__ == "__main__":
    unittest.main()
