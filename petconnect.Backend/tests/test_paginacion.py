"""
Pruebas de regresion del item 4.17 de PRIORIDADES (NC-003, A-11): paginacion de los
listados publicos GET /api/productos y GET /api/mascotas/adopcion.

Antes las dos rutas devolvian todas las filas en cada peticion. Ahora:
- ?pagina= y ?por_pagina= son opcionales: sin ellos, primera pagina de 20.
- por_pagina mayor que 50 se recorta a 50 (nunca mas filas que eso).
- Texto, 0, negativos, decimales o pagina > 10000 responden 400 en espanol, sin
  llegar a la base de datos (tambien con miles de cifras: nunca un 500).
- La respuesta sigue siendo una lista (la web y el movil no se rompen).
- El LIMIT y el OFFSET van como parametros de la consulta, nunca pegados al SQL.

No necesitan base de datos: la conexion es un MagicMock (como en test_endpoints.py).
La paginacion con MariaDB real esta en
test_esquema.PruebasEsquemaEnBD.test_la_adopcion_se_pagina_sin_repetir_ni_saltar_mascotas.

Ejecutar desde petconnect.Backend, con el entorno virtual activo:
    python -m unittest discover -s tests -v
"""
import os
import re
import sys
import unittest
from urllib.parse import quote

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_endpoints import _BaseEndpoints  # noqa: E402

RUTAS = ("/api/productos", "/api/mascotas/adopcion")


class PruebasPaginacionAPI(_BaseEndpoints):
    """Las dos rutas leen ?pagina= y ?por_pagina= igual."""

    def _pedir(self, ruta, consulta=""):
        return self.cliente.get(ruta + (f"?{consulta}" if consulta else ""))

    def test_sin_parametros_es_la_primera_pagina_de_20(self):
        for ruta in RUTAS:
            with self.subTest(ruta=ruta):
                self.cursor.execute.reset_mock()
                r = self._pedir(ruta)
                self.assertEqual(r.status_code, 200)
                self.assertEqual(self._sql_y_parametros()[1], (20, 0))

    def test_convierte_la_pagina_en_limite_y_desplazamiento(self):
        casos = (
            ("pagina=1&por_pagina=5", (5, 0)),
            ("pagina=2&por_pagina=5", (5, 5)),
            ("pagina=3", (20, 40)),
            ("por_pagina=12", (12, 0)),
            ("pagina=10000&por_pagina=1", (1, 9999)),       # la ultima pagina permitida
            ("pagina=%202%20&por_pagina=5", (5, 5)),        # espacios alrededor
        )
        for ruta in RUTAS:
            for consulta, esperado in casos:
                with self.subTest(ruta=ruta, consulta=consulta):
                    self.cursor.execute.reset_mock()
                    self.assertEqual(self._pedir(ruta, consulta).status_code, 200)
                    self.assertEqual(self._sql_y_parametros()[1], esperado)

    def test_nunca_pide_mas_de_50_filas(self):
        for ruta in RUTAS:
            for por_pagina in ("50", "51", "999", "9999999999", "9" * 5000):
                with self.subTest(ruta=ruta, por_pagina=por_pagina):
                    self.cursor.execute.reset_mock()
                    self.assertEqual(self._pedir(ruta, f"por_pagina={por_pagina}").status_code, 200)
                    self.assertEqual(self._sql_y_parametros()[1], (50, 0))

    def test_valores_que_no_sirven_responden_400_sin_tocar_la_bd(self):
        malos = ("abc", "0", "000", "-1", "1.5", "", "1e3", "²", "0x10", "1;DROP", "1 2")
        for ruta in RUTAS:
            for parametro in ("pagina", "por_pagina"):
                for valor in malos:
                    with self.subTest(ruta=ruta, parametro=parametro, valor=valor):
                        self.cursor.execute.reset_mock()
                        r = self._pedir(ruta, f"{parametro}={quote(valor)}")
                        self.assertEqual(r.status_code, 400)
                        self.assertEqual(
                            r.get_json(),
                            {"error": f"El parametro '{parametro}' debe ser un numero entero mayor que 0"})
                        self.cursor.execute.assert_not_called()

    def test_pagina_mayor_que_10000_responde_400(self):
        for ruta, pagina in ((r, p) for r in RUTAS for p in ("10001", "9999999999", "9" * 5000)):
            with self.subTest(ruta=ruta, cifras=len(pagina)):
                self.cursor.execute.reset_mock()
                r = self._pedir(ruta, f"pagina={pagina}")
                self.assertEqual(r.status_code, 400)
                self.assertEqual(r.get_json(),
                                 {"error": "El parametro 'pagina' no puede ser mayor que 10000"})
                self.cursor.execute.assert_not_called()

    def test_la_respuesta_sigue_siendo_una_lista(self):
        filas = [{"id": 1, "name": "Uno"}, {"id": 2, "name": "Dos"}]
        self.cursor.fetchall.return_value = filas
        for ruta in RUTAS:
            with self.subTest(ruta=ruta):
                r = self._pedir(ruta, "pagina=1&por_pagina=2")
                self.assertEqual(r.status_code, 200)
                self.assertEqual(r.get_json(), filas)

    def test_los_numeros_van_como_parametros_no_pegados_al_sql(self):
        for ruta in RUTAS:
            with self.subTest(ruta=ruta):
                self.cursor.execute.reset_mock()
                self._pedir(ruta, "pagina=7&por_pagina=13")
                sql, params = self._sql_y_parametros()
                self.assertTrue(sql.endswith("LIMIT %s OFFSET %s"), sql)
                self.assertEqual(params, (13, 78))
                self.assertNotRegex(sql, r"\b(13|78)\b")


class PruebasPaginacionDAO(unittest.TestCase):
    """El orden de las paginas es estable: se ordena por la clave primaria, unica."""

    def test_las_consultas_ordenan_por_id_y_luego_limitan(self):
        from dao.mascota_dao import MascotaDAO
        from dao.producto_dao import ProductoDAO
        for sql, orden in ((ProductoDAO._CATALOGO, "ORDER BY p.id_producto"),
                           (MascotaDAO._EN_ADOPCION, "ORDER BY id_mascota")):
            with self.subTest(orden=orden):
                una_linea = " ".join(sql.split())
                self.assertTrue(una_linea.endswith(f"{orden} LIMIT %s OFFSET %s"), una_linea)
                self.assertEqual(len(re.findall(r"%s", una_linea)), 2)


if __name__ == "__main__":
    unittest.main()
