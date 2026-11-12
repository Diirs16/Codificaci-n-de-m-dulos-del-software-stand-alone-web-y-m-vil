"""
Prueba de regresion de A-16 (item 6.3 de PRIORIDADES): generate_keys.py no debe
borrar ni cambiar nada de un archivo de entorno que ya existe.

Todo pasa en carpetas temporales: NUNCA se toca el .env real del backend. El modulo
se importa estando dentro de una carpeta temporal y con la salida silenciada, porque
la version anterior del script escribia ".env" (en la carpeta actual) apenas se
importaba: asi la contraprueba con el codigo viejo tampoco puede tocar el real.

Los valores de las claves nunca se imprimen: las comparaciones usan assertTrue con
un mensaje propio (assertEqual mostraria el contenido si fallara). Los datos que no
son claves (contrasena, correo) son inventados.

Ejecutar desde petconnect.Backend, con el entorno virtual activo:
    python -m unittest tests.test_generate_keys -v
"""
import contextlib
import importlib
import io
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from cryptography.fernet import Fernet

CARPETA_BACKEND = Path(__file__).resolve().parent.parent
NOMBRE_ENV = "." + "env"  # nombre del archivo de entorno
CLAVES = ("JWT_SECRET", "FERNET_KEY")


def _sin_escritura(*args, **kwargs):
    raise RuntimeError("generate_keys intento escribir al importarse")


def _importar_generate_keys():
    """
    Importa generate_keys dentro de una carpeta temporal; devuelve (modulo, archivos creados).
    Mientras se importa, tempfile.mkstemp (con el que escribe la version nueva) esta
    bloqueado: si alguien quita el 'if __name__ == "__main__"', la importacion falla en
    vez de escribir en el .env real.
    """
    anterior = os.getcwd()
    with tempfile.TemporaryDirectory() as carpeta:
        os.chdir(carpeta)
        try:
            if str(CARPETA_BACKEND) not in sys.path:
                sys.path.insert(0, str(CARPETA_BACKEND))
            sys.modules.pop("generate_keys", None)
            with contextlib.redirect_stdout(io.StringIO()), \
                    mock.patch.object(tempfile, "mkstemp", side_effect=_sin_escritura):
                modulo = importlib.import_module("generate_keys")
            creados = os.listdir(carpeta)
        finally:
            os.chdir(anterior)
    return modulo, creados


def _valores(texto):
    """Lee NOMBRE=valor de las lineas no comentadas (la ultima gana, como python-dotenv)."""
    valores = {}
    for linea in texto.splitlines():
        m = re.match(r"^\s*(?:export\s+)?([A-Z_][A-Z0-9_]*)\s*=(.*)$", linea)
        if m:
            valor = re.sub(r"\s+#.*$", "", m.group(2)).strip().strip("\"'")
            valores[m.group(1)] = valor
    return valores


class PruebasGenerateKeys(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.gk, cls.creados_al_importar = _importar_generate_keys()

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.carpeta = Path(self._tmp.name)
        self.env = self.carpeta / NOMBRE_ENV
        self.plantilla = self.carpeta / (NOMBRE_ENV + ".example")

    def _claves_validas(self, texto):
        valores = _valores(texto)
        jwt = valores.get("JWT_SECRET", "")
        self.assertTrue(re.fullmatch(r"[0-9a-f]{64}", jwt),
                        "JWT_SECRET debe ser de 32 bytes en hexadecimal")
        try:
            Fernet(valores.get("FERNET_KEY", "").encode())
        except Exception:
            self.fail("FERNET_KEY no es una clave Fernet valida")
        return valores

    # --- El script no actua al importarlo y usa la carpeta del backend -------------

    def test_importar_no_crea_archivos(self):
        self.assertEqual(self.creados_al_importar, [],
                         "importar generate_keys no debe escribir ningun archivo")

    def test_rutas_son_las_de_la_carpeta_del_script(self):
        # Solo compara rutas: no abre el archivo real.
        self.assertEqual(Path(self.gk.RUTA_ENV), CARPETA_BACKEND / NOMBRE_ENV)
        self.assertEqual(Path(self.gk.RUTA_PLANTILLA), CARPETA_BACKEND / (NOMBRE_ENV + ".example"))

    # --- Archivo nuevo ----------------------------------------------------------------

    def test_archivo_nuevo_copia_la_plantilla_y_crea_las_claves(self):
        plantilla = ("# Plantilla de prueba\nDB_PORT=3310\nDB_PASSWORD=\n\n"
                     "JWT_SECRET=\nFERNET_KEY=\nOTRA=valor\n")
        self.plantilla.write_text(plantilla, encoding="utf-8")
        estado, nuevo = self.gk.generar(self.env, self.plantilla)

        self.assertTrue(nuevo)
        self.assertEqual(estado, {"JWT_SECRET": "creada", "FERNET_KEY": "creada"})
        texto = self.env.read_text(encoding="utf-8")
        self._claves_validas(texto)
        originales = plantilla.splitlines()
        nuevas = texto.splitlines()
        self.assertEqual(len(nuevas), len(originales), "las claves se llenan en su linea")
        for antes, despues in zip(originales, nuevas):
            if not antes.startswith(CLAVES):
                self.assertEqual(antes, despues)
        # La plantilla no cambia.
        self.assertEqual(self.plantilla.read_text(encoding="utf-8"), plantilla)

    def test_archivo_nuevo_desde_la_plantilla_real_trae_todas_sus_variables(self):
        # .env.example es la plantilla publica (no tiene secretos): se copia a la carpeta temporal.
        real = (CARPETA_BACKEND / (NOMBRE_ENV + ".example")).read_text(encoding="utf-8")
        self.plantilla.write_text(real, encoding="utf-8")
        self.gk.generar(self.env, self.plantilla)
        texto = self.env.read_text(encoding="utf-8")
        valores = self._claves_validas(texto)
        for nombre in _valores(real):
            self.assertIn(nombre, valores, f"falta {nombre} de .env.example")

    def test_sin_plantilla_crea_solo_las_claves(self):
        estado, nuevo = self.gk.generar(self.env, self.plantilla)
        self.assertTrue(nuevo)
        self.assertEqual(set(estado.values()), {"creada"})
        self._claves_validas(self.env.read_text(encoding="utf-8"))

    # --- Archivo existente: nunca borrar ----------------------------------------------

    def test_conserva_las_demas_variables_byte_a_byte(self):
        # Fin de linea de Windows, comentarios, comillas, "=" en un valor y una enie.
        original = ("# Mi configuracion\r\n"
                    "DB_HOST=localhost\r\n"
                    "DB_PASSWORD=clave-inventada=123\r\n"
                    "GMAIL_USER=persona.inventada@ejemplo.test\r\n"
                    "GMAIL_APP_PASSWORD=\"abcd efgh ijkl mnop\"\r\n"
                    "\r\n"
                    "APP_ENV=desarrollo  # solo en mi PC, contrasena con enie: ñ\r\n"
                    "JWT_SECRET=\r\n"
                    "CORS_ORIGENES=https://ejemplo.test\r\n")
        self.env.write_bytes(original.encode("utf-8"))
        estado, nuevo = self.gk.generar(self.env, self.plantilla)

        self.assertFalse(nuevo)
        self.assertEqual(estado, {"JWT_SECRET": "creada", "FERNET_KEY": "creada"})
        texto = self.env.read_bytes().decode("utf-8")
        self._claves_validas(texto)
        antes = original.splitlines(keepends=True)
        despues = texto.splitlines(keepends=True)
        for i, linea in enumerate(antes):
            if linea.startswith("JWT_SECRET"):
                self.assertTrue(despues[i].startswith("JWT_SECRET=") and despues[i].endswith("\r\n"),
                                "JWT_SECRET se llena en su misma linea")
            else:
                self.assertEqual(despues[i], linea, f"la linea {i + 1} cambio")
        # FERNET_KEY no tenia linea: se agrega al final, con el mismo fin de linea.
        agregadas = despues[len(antes):]
        self.assertTrue(any(l.startswith("FERNET_KEY=") for l in agregadas))
        self.assertTrue(all(l.endswith("\r\n") for l in agregadas))

    def test_claves_presentes_no_cambian_ni_se_reescribe(self):
        original = ("DB_PASSWORD=clave-inventada\n"
                    "JWT_SECRET=valor-de-prueba-que-no-debe-cambiar\n"
                    "FERNET_KEY=otro-valor-de-prueba\n")
        self.env.write_bytes(original.encode("utf-8"))
        with mock.patch.object(self.gk.os, "replace") as reemplazar:
            estado, nuevo = self.gk.generar(self.env, self.plantilla)
        reemplazar.assert_not_called()
        self.assertFalse(nuevo)
        self.assertEqual(estado, {"JWT_SECRET": "ya estaba", "FERNET_KEY": "ya estaba"})
        self.assertTrue(self.env.read_bytes() == original.encode("utf-8"),
                        "el archivo cambio aunque las dos claves ya tenian valor")
        self.assertEqual(os.listdir(self.carpeta), [NOMBRE_ENV], "no deben quedar temporales")

    def test_correr_dos_veces_no_cambia_nada(self):
        self.gk.generar(self.env, self.plantilla)
        primera = self.env.read_bytes()
        estado, _ = self.gk.generar(self.env, self.plantilla)
        self.assertEqual(set(estado.values()), {"ya estaba"})
        self.assertTrue(self.env.read_bytes() == primera, "la segunda vez cambio las claves")

    def test_vacias_se_llenan_y_las_comentadas_no_cuentan(self):
        original = ("# JWT_SECRET=una-clave-vieja-comentada\n"
                    "JWT_SECRET=\"\"\n"
                    "FERNET_KEY=   # pon aqui la clave\n")
        self.env.write_text(original, encoding="utf-8")
        estado, _ = self.gk.generar(self.env, self.plantilla)
        self.assertEqual(set(estado.values()), {"creada"})
        lineas = self.env.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lineas), 3, "no se agregan lineas: se llenan las vacias")
        self.assertEqual(lineas[0], "# JWT_SECRET=una-clave-vieja-comentada")
        self.assertTrue(lineas[2].endswith("# pon aqui la clave"), "se conserva el comentario")
        self._claves_validas("\n".join(lineas))

    def test_si_falla_la_escritura_el_original_queda_entero(self):
        original = "DB_PASSWORD=clave-inventada\nJWT_SECRET=\n"
        self.env.write_bytes(original.encode("utf-8"))
        with mock.patch.object(self.gk.os, "replace", side_effect=OSError("disco lleno (simulado)")):
            with self.assertRaises(OSError):
                self.gk.generar(self.env, self.plantilla)
        self.assertEqual(self.env.read_bytes(), original.encode("utf-8"))
        self.assertEqual(os.listdir(self.carpeta), [NOMBRE_ENV], "no deben quedar temporales")

    # --- Lo que se muestra en la terminal ---------------------------------------------

    def test_no_imprime_los_valores_de_las_claves(self):
        salida = io.StringIO()
        with contextlib.redirect_stdout(salida):
            self.gk.main(self.env, self.plantilla)
        texto = salida.getvalue()
        valores = _valores(self.env.read_text(encoding="utf-8"))
        for clave in CLAVES:
            self.assertIn(clave, texto, "la salida debe decir que paso con cada clave")
            self.assertFalse(valores[clave][:8] in texto,
                             f"la salida muestra parte del valor de {clave}")


if __name__ == "__main__":
    unittest.main()
