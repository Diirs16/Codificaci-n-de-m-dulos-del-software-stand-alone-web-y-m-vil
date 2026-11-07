"""
Pruebas de regresion de A-19 / NC-011 (item 4.2 de PRIORIDADES): la busqueda de
proveedores por nombre devolvia proveedores inactivos.

- ProveedorDAO.buscar_por_nombre filtra "activo = TRUE", igual que
  consultar_por_ciudad (las dos busquedas siguen la misma regla).
- '%', '_' y '!' que escriba el usuario se buscan como letras y no como
  comodines del LIKE (ESCAPE '!').
- La consulta sigue parametrizada y las filas se convierten en ProveedorServicio.

No usan la base de datos real (la conexion se simula) ni leen .env: api.py se
importa primero con load_dotenv apagado (_importar_api), asi config/ no carga el
.env al importar el DAO. Los datos son inventados (Ley 1581).

Ejecutar desde petconnect.Backend, con el entorno virtual activo:
    python -m unittest discover -s tests -v
"""
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_errores import _importar_api  # noqa: E402

# Fila inventada con el orden de columnas de las consultas del DAO
FILA_ACTIVA = (3, "Veterinaria Prueba Norte", "NIT", "900000000", "3000000000",
               "contacto@ejemplo.test", "Calle Falsa 123", "Bogota", "Consulta general",
               "Lun-Vie 8:00-18:00", 0, None, None, 1)


def _normalizar(sql):
    """Quita saltos de linea y espacios repetidos para comparar el SQL."""
    return " ".join(sql.split())


class PruebasBusquedaProveedoresPorNombre(unittest.TestCase):
    """buscar_por_nombre con la conexion simulada: nunca se toca la BD real."""

    @classmethod
    def setUpClass(cls):
        _importar_api()
        from dao.proveedor_dao import ProveedorDAO
        from modelo.proveedor_servicio import ProveedorServicio
        cls.ProveedorDAO = ProveedorDAO
        cls.ProveedorServicio = ProveedorServicio

    def setUp(self):
        self.dao = self.ProveedorDAO()
        conexion_bd = mock.MagicMock()
        self.cursor = conexion_bd.obtener_conexion.return_value.cursor.return_value
        self.cursor.fetchall.return_value = []
        self.dao._conexion_bd = conexion_bd     # BD simulada

    def _buscar(self, termino):
        """Busca y devuelve (resultado, sql normalizado, parametros enviados)."""
        resultado = self.dao.buscar_por_nombre(termino)
        sql, parametros = self.cursor.execute.call_args.args
        return resultado, _normalizar(sql), parametros

    def test_busqueda_por_nombre_solo_trae_activos(self):
        _, sql, _ = self._buscar("Veterinaria")
        self.assertIn("activo = TRUE", sql)

    def test_misma_regla_que_la_busqueda_por_ciudad(self):
        por_ciudad = _normalizar(self.ProveedorDAO._CONSULTAR_POR_CIUDAD)
        por_nombre = _normalizar(self.ProveedorDAO._BUSCAR_POR_NOMBRE)
        self.assertIn("activo = TRUE", por_ciudad)
        self.assertIn("activo = TRUE", por_nombre)

    def test_escapa_comodines(self):
        casos = {
            "50%_off": "%50!%!_off%",     # % y _ se buscan como letras
            "Pet!Shop": "%Pet!!Shop%",    # el propio caracter de escape tambien
            "Veterinaria": "%Veterinaria%",
        }
        for termino, esperado in casos.items():
            with self.subTest(termino=termino):
                _, sql, parametros = self._buscar(termino)
                self.assertIn("LIKE %s ESCAPE '!'", sql)
                self.assertEqual(parametros, (esperado,))

    def test_busqueda_sigue_parametrizada(self):
        termino = "x' OR '1'='1"
        _, sql, parametros = self._buscar(termino)
        self.assertEqual(sql.count("%s"), len(parametros))
        self.assertNotIn(termino, sql)
        self.assertIn(termino, parametros[0])

    def test_devuelve_proveedores_mapeados(self):
        self.cursor.fetchall.return_value = [FILA_ACTIVA]
        resultado, _, _ = self._buscar("Norte")
        self.assertEqual(len(resultado), 1)
        proveedor = resultado[0]
        self.assertIsInstance(proveedor, self.ProveedorServicio)
        self.assertEqual(proveedor.id_proveedor, 3)
        self.assertEqual(proveedor.nombre, "Veterinaria Prueba Norte")
        self.assertIs(proveedor.activo, True)


if __name__ == "__main__":
    unittest.main()
