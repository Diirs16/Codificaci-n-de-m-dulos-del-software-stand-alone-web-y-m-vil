"""
Pruebas del item 6.1 de la auditoria (A-32): el README.md de la raiz dice la
verdad sobre el proyecto. No necesitan base de datos ni internet: leen como texto
README.md, requirements.txt, sql/schema.sql y config/db_config.py.

Lo que se vigila:
- Las versiones de la tabla "Tecnologias y versiones" del README coinciden con
  las fijadas en requirements.txt (antes decia mysql-connector-python 9.7.0 y
  requirements.txt fija 9.1.0). Si alguien sube una version y no toca el README,
  esta prueba falla.
- No vuelve a decir que el motor es MySQL 8 / MySQL Server / MySQL Workbench: el
  motor real es MariaDB (10.4 en el PC, 10.11 en Docker y Railway).
- El numero de tablas del README es el de sql/schema.sql (antes decia 32).
- autocommit: el README y config/db_config.py dicen False (item 4.9, A-15).
- Los enlaces relativos del README llevan a archivos que existen.
- Las variables aparecen solo por nombre: ninguna linea NOMBRE=valor.

Si el README no esta (por ejemplo, dentro de la imagen de Docker, que solo copia
petconnect.Backend), las pruebas se omiten.

Ejecutar desde petconnect.Backend, con el entorno virtual activo:
    python -m unittest discover -s tests -v
"""
import os
import re
import unittest

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAIZ_REPO = os.path.dirname(BACKEND)
RUTA_README = os.path.join(RAIZ_REPO, "README.md")

LINEA_FIJADA = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._\-]*)==(\d+(?:\.\d+)*)$")


def _leer(ruta):
    with open(ruta, encoding="utf-8") as archivo:
        return archivo.read()


def _versiones_requirements():
    """{nombre en minusculas: version} de requirements.txt."""
    versiones = {}
    for linea in _leer(os.path.join(BACKEND, "requirements.txt")).splitlines():
        coincidencia = LINEA_FIJADA.match(linea.strip())
        if coincidencia:
            versiones[coincidencia.group(1).lower()] = coincidencia.group(2)
    return versiones


def _versiones_readme(texto):
    """
    Pares (paquete, version) de las filas de la tabla de tecnologias que nombran
    paquetes de Python. Una fila puede juntar varios: "| a / b | 1.0 / 2.0 | ...".
    """
    pares = []
    for linea in texto.splitlines():
        celdas = [c.strip() for c in linea.strip().strip("|").split("|")]
        if len(celdas) < 2:
            continue
        nombres = [n.strip() for n in celdas[0].split("/")]
        versiones = [v.strip() for v in celdas[1].split("/")]
        if len(nombres) == len(versiones):
            pares.extend(zip(nombres, versiones))
    return pares


@unittest.skipUnless(os.path.exists(RUTA_README), "README.md no esta (imagen de Docker)")
class PruebasReadme(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.readme = _leer(RUTA_README)

    def test_versiones_iguales_a_requirements(self):
        requeridas = _versiones_requirements()
        revisadas = {}
        for nombre, version in _versiones_readme(self.readme):
            clave = nombre.lower()
            if clave in requeridas:
                revisadas[clave] = version
                self.assertEqual(
                    version, requeridas[clave],
                    f"El README dice {nombre} {version}; requirements.txt fija {requeridas[clave]}",
                )
        # El conector es el que estaba mal (A-32): debe estar en la tabla
        self.assertIn("mysql-connector-python", revisadas)
        self.assertIn("flask", revisadas)

    def test_no_dice_que_el_motor_es_mysql(self):
        # assertFalse/assertTrue con mensaje propio: assertNotIn imprimiria el README entero
        for texto_viejo in ("MySQL 8.x", "MySQL Server", "MySQL Workbench", "9.7.0"):
            self.assertFalse(texto_viejo in self.readme, f"El README vuelve a decir '{texto_viejo}'")
        self.assertTrue("MariaDB" in self.readme, "El README debe nombrar el motor real: MariaDB")

    def test_numero_de_tablas_igual_al_esquema(self):
        esquema = _leer(os.path.join(BACKEND, "sql", "schema.sql"))
        tablas = len(re.findall(r"^\s*CREATE TABLE\b", esquema, re.IGNORECASE | re.MULTILINE))
        coincidencia = re.search(r"^\|\s*Tablas\s*\|\s*(\d+)", self.readme, re.MULTILINE)
        self.assertIsNotNone(coincidencia, "El README debe tener la fila '| Tablas | N ...'")
        self.assertEqual(int(coincidencia.group(1)), tablas)

    def test_autocommit_false_en_readme_y_configuracion(self):
        configuracion = _leer(os.path.join(BACKEND, "config", "db_config.py"))
        self.assertIsNotNone(re.search(r'"autocommit":\s*False', configuracion),
                             'config/db_config.py debe tener "autocommit": False')
        self.assertIsNotNone(re.search(r"autocommit[^\n]*\bFalse\b", self.readme),
                             "El README debe decir autocommit `False`")
        self.assertIsNone(re.search(r"autocommit[^\n]*True", self.readme),
                          "El README no debe decir autocommit True")

    def test_enlaces_relativos_existen(self):
        enlaces = re.findall(r"\]\(([^)#\s]+)\)", self.readme)
        relativos = [e for e in enlaces if not re.match(r"^[a-z]+://", e)]
        self.assertTrue(relativos, "El README deberia enlazar las otras guias")
        for enlace in relativos:
            ruta = os.path.join(RAIZ_REPO, *enlace.rstrip("/").split("/"))
            self.assertTrue(os.path.exists(ruta), f"Enlace roto en el README: {enlace}")

    def test_variables_solo_por_nombre(self):
        # Ninguna clave, contrasena o direccion escrita con su valor (NOMBRE, signo
        # igual y valor), por ejemplo de JWT_SECRET o VITE_API_URL (Regla 4 de
        # CLAUDE.md). Interruptores como la variable de las pruebas con BD si valen.
        con_valor = re.compile(
            r"\b[A-Z0-9_]*(SECRET|PASSWORD|KEY|TOKEN|USER|URL|HOST|SENDER|ORIGENES)=\S"
        )
        for numero, linea in enumerate(self.readme.splitlines(), start=1):
            coincidencia = con_valor.search(linea)
            # Solo se muestra el nombre de la variable, nunca el valor
            self.assertIsNone(
                coincidencia,
                f"Linea {numero} del README: variable con valor "
                f"({coincidencia.group(0)[:-2] if coincidencia else ''})",
            )


if __name__ == "__main__":
    unittest.main()
