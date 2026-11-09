"""
Prueba de regresion de A-41 (item 4.14 de PRIORIDADES): las pruebas no cargan el
.env real. Importar api.py o config/ llama a load_dotenv(), que copia el .env a
os.environ; las pruebas deben importarlos con load_dotenv apagado (_importar_api()
de test_errores.py).

Cada caso corre un archivo de pruebas en un Python aparte, con un entorno minimo armado
a mano (sin copiar os.environ ni PETCONNECT_PRUEBA_BD, asi que no toca la BD) y con
dotenv.load_dotenv cambiado por un "espia": una funcion que NO carga nada y solo cuenta
cuantas veces la llamaron. Como el espia nunca lee el archivo, ni siquiera el codigo
viejo carga el .env durante esta prueba. Nunca se imprime ningun valor de configuracion.

Va en un archivo aparte porque si test_seguridad.py se corriera a si mismo se
repetiria sin fin.

Ejecutar desde petconnect.Backend, con el entorno virtual activo:
    python -m unittest discover -s tests -v
"""
import os
import re
import subprocess
import sys
import unittest

CARPETA_TESTS = os.path.dirname(os.path.abspath(__file__))
CARPETA_BACKEND = os.path.dirname(CARPETA_TESTS)

# Programa que corre en el Python aparte. Recibe la carpeta del backend, la de las
# pruebas y el nombre del modulo; al final escribe solo tres numeros.
PROGRAMA_ESPIA = """
import os, sys, unittest
import dotenv

llamadas = []

def espia(*args, **kwargs):
    llamadas.append(1)
    return False

dotenv.load_dotenv = espia
backend, tests, modulo = sys.argv[1:4]
sys.path[:0] = [backend, tests]
suite = unittest.defaultTestLoader.loadTestsFromName(modulo)
with open(os.devnull, "w") as nada:
    r = unittest.TextTestRunner(stream=nada, verbosity=0).run(suite)
print("llamadas=%d corridas=%d fallos=%d"
      % (len(llamadas), r.testsRun, len(r.failures) + len(r.errors)))
"""


class PruebasSinEnvReal(unittest.TestCase):
    """A-41: test_seguridad.py y test_esquema.py corren sin llamar a load_dotenv."""

    def _correr_con_espia(self, modulo):
        entorno = {
            "PATH": os.environ.get("PATH", ""),
            "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
            "TEMP": os.environ.get("TEMP", ""),
            "TMP": os.environ.get("TMP", ""),
        }
        r = subprocess.run(
            [sys.executable, "-c", PROGRAMA_ESPIA, CARPETA_BACKEND, CARPETA_TESTS, modulo],
            cwd=CARPETA_BACKEND, env=entorno,
            capture_output=True, text=True, timeout=300,
        )
        self.assertEqual(r.returncode, 0, "el Python aparte no termino bien")
        resultado = re.search(r"llamadas=(\d+) corridas=(\d+) fallos=(\d+)", r.stdout)
        self.assertIsNotNone(resultado, "no se encontro el resumen del espia")
        return [int(n) for n in resultado.groups()]

    def _revisar(self, modulo):
        llamadas, corridas, fallos = self._correr_con_espia(modulo)
        self.assertGreater(corridas, 0)
        self.assertEqual(fallos, 0, f"{modulo}: fallan pruebas sin el .env real")
        self.assertEqual(llamadas, 0, f"{modulo} llama a load_dotenv (cargaria el .env real)")

    def test_seguridad_no_carga_el_env(self):
        self._revisar("test_seguridad")

    def test_esquema_sin_bd_no_carga_el_env(self):
        self._revisar("test_esquema")

    def test_dao_errores_no_carga_el_env(self):
        # Item 4.15: importa dao/ y vista/ (que cargan config/) despues de _importar_api()
        self._revisar("test_dao_errores")


if __name__ == "__main__":
    unittest.main()
