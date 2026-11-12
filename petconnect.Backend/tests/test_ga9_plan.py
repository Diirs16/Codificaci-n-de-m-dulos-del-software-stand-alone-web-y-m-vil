"""
Pruebas del item 6.2 de la auditoria (A-33): el plan de pruebas GA9
(Documentacion/GA9-220501096-AA1-EV02-PetConnect.md) describe las herramientas
que el repositorio usa de verdad. No necesitan base de datos ni internet: leen
el plan como texto.

Hasta la version 2.3, GA9 decia que las pruebas de la API se corrian con pytest
y pytest-cov, con las variables de un archivo .env.test, y su Figura 4 (CP-012)
usaba @pytest.fixture y "pytest -q". El repositorio nunca adopto nada de eso:
usa unittest (biblioteca estandar), el cliente de pruebas de Flask y
PETCONNECT_PRUEBA_BD=1 para las pruebas con MariaDB; cada prueba pone sus
propias claves y no lee el .env real. Lo que se vigila:

- Ninguna instruccion de pytest (import, fixture, "pytest -q", pytest-cov).
- "pytest" y ".env.test" solo aparecen en frases de historial (lo que decia
  antes), nunca como herramienta vigente.
- La Figura 4 es una clase unittest.TestCase con el cliente de pruebas de Flask.
- La version del plan es 2.4 o posterior (la que registra este cambio).

Si el plan no esta (por ejemplo, dentro de la imagen de Docker, que solo copia
petconnect.Backend), las pruebas se omiten.

Ejecutar desde petconnect.Backend, con el entorno virtual activo:
    python -m unittest discover -s tests -v
"""
import os
import re
import unittest

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAIZ_REPO = os.path.dirname(BACKEND)
RUTA_GA9 = os.path.join(RAIZ_REPO, "Documentacion", "GA9-220501096-AA1-EV02-PetConnect.md")

# Texto que nunca debe volver: son instrucciones de pytest, no historia.
PROHIBIDOS = ("import pytest", "@pytest.fixture", "pytest-cov", "pytest.ini", "conftest.py")

# Una linea que nombra pytest o .env.test debe contar que es lo de antes.
MARCAS_DE_HISTORIAL = ("antes decía", "hasta la versión 2.3", "en lugar de pytest")


def _leer_ga9():
    with open(RUTA_GA9, encoding="utf-8") as archivo:
        return archivo.read()


def _figura_4(texto):
    """Bloque de codigo que sigue al titulo **Figura 4** (entre las dos ```)."""
    inicio = texto.index("**Figura 4**")
    apertura = texto.index("```", inicio)
    cierre = texto.index("```", apertura + 3)
    return texto[apertura:cierre]


@unittest.skipUnless(os.path.exists(RUTA_GA9), "El plan GA9 no esta en esta copia del repositorio")
class PruebasPlanGA9(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.texto = _leer_ga9()

    def test_sin_instrucciones_de_pytest(self):
        for prohibido in PROHIBIDOS:
            with self.subTest(texto=prohibido):
                self.assertNotIn(prohibido, self.texto)

    def test_pytest_y_env_test_solo_como_historial(self):
        for numero, linea in enumerate(self.texto.splitlines(), start=1):
            minuscula = linea.lower()
            if "pytest" not in minuscula and ".env.test" not in minuscula:
                continue
            with self.subTest(linea=numero):
                self.assertTrue(
                    any(marca in minuscula for marca in MARCAS_DE_HISTORIAL),
                    f"La línea {numero} de GA9 nombra pytest o .env.test como si se usaran: "
                    f"el repositorio usa unittest y PETCONNECT_PRUEBA_BD (A-33)",
                )

    def test_figura_4_usa_unittest_y_el_cliente_de_flask(self):
        figura = _figura_4(self.texto)
        self.assertIn("unittest.TestCase", figura)
        self.assertIn("test_client()", figura)
        self.assertIn("_importar_api", figura)  # claves de prueba sin leer el .env real
        self.assertNotIn("pytest", figura)

    def test_version_registra_el_cambio(self):
        version = re.search(r"^\| Versión \| (\d+)\.(\d+)", self.texto, re.MULTILINE)
        self.assertIsNotNone(version, "No se encontró la fila Versión de la Tabla 1")
        self.assertGreaterEqual((int(version.group(1)), int(version.group(2))), (2, 4))


if __name__ == "__main__":
    unittest.main()
