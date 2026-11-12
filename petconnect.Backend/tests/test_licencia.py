"""
Pruebas del item 6.5 de la auditoria (A-34): ningun archivo de licencia del
repositorio dice que el codigo es de Expo.

Antes, PetConnect.Mobile/LICENSE era la licencia MIT de la plantilla de Expo
("Copyright (c) 2015-present 650 Industries, Inc. (aka Expo)"): decia que el
codigo del movil era de Expo y daba permisos que el dueno nunca decidio dar.
El dueno eligio la opcion A: sin licencia abierta (todos los derechos
reservados) y una seccion "Licencia" en el README de la raiz.

Lo que se vigila:
- Ningun LICENSE / LICENCE / COPYING del repositorio (en cualquier carpeta)
  menciona "650 Industries" ni "aka Expo". Se saltan node_modules, entornos
  virtuales, carpetas que empiezan por punto (.git, .venv, .claude, que puede
  tener copias viejas del repo) y salidas de compilacion: las librerias de
  terceros conservan su propia licencia y no son parte de este codigo.
- El README de la raiz tiene la seccion "Licencia" y es coherente: si no hay
  LICENSE en la raiz dice "Todos los derechos reservados"; si algun dia se
  agrega uno (por ejemplo MIT), el README debe enlazarlo.
- La busqueda de archivos funciona (prueba con una carpeta temporal), para que
  una regla de exclusion mal escrita no deje la prueba pasando sin revisar nada.

No necesitan base de datos ni internet. Si el README no esta (por ejemplo,
dentro de la imagen de Docker, que solo copia petconnect.Backend), se omiten.

Ejecutar desde petconnect.Backend, con el entorno virtual activo:
    python -m unittest discover -s tests -v
"""
import os
import re
import tempfile
import unittest

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAIZ_REPO = os.path.dirname(BACKEND)
RUTA_README = os.path.join(RAIZ_REPO, "README.md")

# Nombres de archivo que se consideran "licencia" (sin importar mayusculas).
PREFIJOS_LICENCIA = ("license", "licence", "copying")
# Carpetas que no son codigo propio del proyecto.
CARPETAS_IGNORADAS = {"node_modules", "dist", "build", "__pycache__"}
# Textos de la licencia de la plantilla de Expo.
MARCAS_EXPO = ("650 industries", "aka expo")


def _leer(ruta):
    with open(ruta, encoding="utf-8", errors="replace") as archivo:
        return archivo.read()


def buscar_licencias(raiz):
    """Rutas de los archivos de licencia bajo `raiz`, saltando lo ajeno."""
    encontrados = []
    for carpeta, subcarpetas, archivos in os.walk(raiz):
        # Se modifica la lista en su lugar para que os.walk no entre ahi.
        subcarpetas[:] = [
            nombre for nombre in subcarpetas
            if not nombre.startswith(".") and nombre not in CARPETAS_IGNORADAS
        ]
        for nombre in archivos:
            if nombre.lower().startswith(PREFIJOS_LICENCIA):
                encontrados.append(os.path.join(carpeta, nombre))
    return sorted(encontrados)


def _seccion_licencia(texto_readme):
    """Texto de la seccion '## N. Licencia' del README, o None si no esta."""
    coincidencia = re.search(
        r"^## (?:\d+\.\s*)?Licencia\s*$(.*?)(?=^## |\Z)",
        texto_readme,
        flags=re.MULTILINE | re.DOTALL | re.IGNORECASE,
    )
    return coincidencia.group(1) if coincidencia else None


class BusquedaDeLicenciasTest(unittest.TestCase):
    """La funcion de busqueda encuentra lo propio y salta lo ajeno."""

    def test_encuentra_licencias_propias_y_salta_dependencias(self):
        with tempfile.TemporaryDirectory() as tmp:
            propias = [
                os.path.join(tmp, "LICENSE"),
                os.path.join(tmp, "movil", "LICENSE.md"),
                os.path.join(tmp, "web", "COPYING"),
            ]
            ajenas = [
                os.path.join(tmp, "node_modules", "expo", "LICENSE"),
                os.path.join(tmp, ".claude", "worktrees", "x", "LICENSE"),
                os.path.join(tmp, "web", "dist", "LICENSE.txt"),
            ]
            for ruta in propias + ajenas:
                os.makedirs(os.path.dirname(ruta), exist_ok=True)
                with open(ruta, "w", encoding="utf-8") as archivo:
                    archivo.write("texto")
            self.assertEqual(buscar_licencias(tmp), sorted(propias))


@unittest.skipUnless(os.path.isfile(RUTA_README),
                     "README.md de la raiz no disponible (p. ej. en Docker)")
class LicenciaDelRepositorioTest(unittest.TestCase):

    def test_ninguna_licencia_es_la_de_expo(self):
        con_expo = []
        for ruta in buscar_licencias(RAIZ_REPO):
            texto = _leer(ruta).lower()
            if any(marca in texto for marca in MARCAS_EXPO):
                con_expo.append(os.path.relpath(ruta, RAIZ_REPO))
        self.assertEqual(
            con_expo, [],
            "Estos archivos de licencia son la MIT de la plantilla de Expo "
            "(650 Industries) y no corresponden a este codigo: "
            + ", ".join(con_expo),
        )

    def test_readme_tiene_seccion_licencia_coherente(self):
        seccion = _seccion_licencia(_leer(RUTA_README))
        self.assertIsNotNone(seccion, "El README no tiene la seccion 'Licencia'")
        if os.path.isfile(os.path.join(RAIZ_REPO, "LICENSE")):
            self.assertIn("(LICENSE)", seccion,
                          "Hay LICENSE en la raiz: el README debe enlazarlo")
        else:
            self.assertIn("todos los derechos reservados", seccion.lower(),
                          "Sin LICENSE en la raiz, el README debe decir "
                          "'Todos los derechos reservados'")


if __name__ == "__main__":
    unittest.main()
