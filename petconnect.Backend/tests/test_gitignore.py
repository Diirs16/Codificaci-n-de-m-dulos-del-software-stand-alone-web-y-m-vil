"""
Pruebas del item 6.8 de la auditoria (A-38): los archivos temporales de Office
("~$nombre.docx") nunca entran a git.

Word, Excel y PowerPoint crean un archivo oculto "~$" + nombre mientras el
documento esta abierto y lo borran al cerrarlo. Guarda el nombre de quien lo
abrio (un dato personal pequeno) y no es contenido del proyecto. El 31/10/2026
un commit llego a incluir "Documentacion/GA9/~$9-220501096-AA3-EV02-PetConnect.docx"
(ese commit se descarto despues con un reset; no esta en ninguna rama). Desde
el 6.8 el .gitignore de la raiz tiene la regla ~$*.

Lo que se vigila:
- El .gitignore de la raiz tiene la linea ~$* activa (no comentada) y ninguna
  regla "!~$..." la anula.
- git check-ignore confirma que se ignoran temporales de ejemplo (el de GA9,
  uno de Excel y uno en la raiz).
- git check-ignore confirma que NO se ignora un documento real de evidencias,
  para que una regla demasiado ancha (por ejemplo *.docx) no tape las guias.
- git ls-files -ci --exclude-standard sale vacio: ninguna regla del .gitignore
  tapa archivos que ya estan en git.

No necesitan base de datos ni internet. Si no hay .gitignore en la raiz (por
ejemplo, dentro de la imagen de Docker, que solo copia petconnect.Backend) o
no hay git, se omiten.

Ejecutar desde petconnect.Backend, con el entorno virtual activo:
    python -m unittest discover -s tests -v
"""
import os
import shutil
import subprocess
import unittest

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAIZ_REPO = os.path.dirname(BACKEND)
RUTA_GITIGNORE = os.path.join(RAIZ_REPO, ".gitignore")
GIT = shutil.which("git")

REGLA_TEMPORALES_OFFICE = "~$*"
# Rutas de ejemplo: no tienen que existir, git check-ignore solo mira el nombre.
TEMPORALES_DE_EJEMPLO = (
    "Documentacion/GA9/~$9-220501096-AA3-EV02-PetConnect.docx",
    "Documentacion/GA9/~$9-220501096-AA2-EV01_Casos_Prueba_PetConnect.xlsx",
    "~$presentacion.pptx",
)
DOCUMENTO_REAL = "Documentacion/GA9/GA9-220501096-AA1-EV02-PetConnect.docx"


def _reglas_activas(ruta):
    """Lineas del .gitignore sin comentarios ni lineas vacias."""
    with open(ruta, encoding="utf-8") as archivo:
        lineas = [linea.strip() for linea in archivo]
    return [linea for linea in lineas if linea and not linea.startswith("#")]


def _git(*argumentos):
    """Corre git en la raiz del repositorio y devuelve el resultado."""
    return subprocess.run(
        [GIT, "-C", RAIZ_REPO, *argumentos],
        capture_output=True, text=True, encoding="utf-8", check=False,
    )


def _esta_ignorado(ruta_relativa):
    # --no-index: decide solo por las reglas, aunque el archivo estuviera en git.
    # Codigos de salida: 0 = ignorado, 1 = no ignorado, 128 = error.
    resultado = _git("check-ignore", "-q", "--no-index", ruta_relativa)
    if resultado.returncode not in (0, 1):
        raise AssertionError("git check-ignore fallo: " + resultado.stderr.strip())
    return resultado.returncode == 0


@unittest.skipUnless(os.path.isfile(RUTA_GITIGNORE),
                     ".gitignore de la raiz no disponible (p. ej. en Docker)")
class ReglaTemporalesOfficeTest(unittest.TestCase):

    def test_gitignore_tiene_regla_activa_y_sin_anular(self):
        reglas = _reglas_activas(RUTA_GITIGNORE)
        self.assertIn(REGLA_TEMPORALES_OFFICE, reglas,
                      "Falta la regla ~$* en el .gitignore de la raiz")
        anulan = [regla for regla in reglas if regla.startswith("!~$")]
        self.assertEqual(anulan, [],
                         "Estas reglas vuelven a dejar entrar temporales de "
                         "Office: " + ", ".join(anulan))


@unittest.skipUnless(os.path.isfile(RUTA_GITIGNORE) and GIT,
                     "Sin .gitignore en la raiz o sin git instalado")
class GitConfirmaLasReglasTest(unittest.TestCase):

    def test_git_ignora_los_temporales_de_office(self):
        for ruta in TEMPORALES_DE_EJEMPLO:
            with self.subTest(ruta=ruta):
                self.assertTrue(_esta_ignorado(ruta),
                                "git no ignora el temporal de Office " + ruta)

    def test_git_no_ignora_un_documento_real(self):
        self.assertFalse(_esta_ignorado(DOCUMENTO_REAL),
                         "Una regla del .gitignore tapa un documento real: "
                         + DOCUMENTO_REAL)

    def test_ninguna_regla_tapa_archivos_que_ya_estan_en_git(self):
        resultado = _git("ls-files", "-ci", "--exclude-standard")
        self.assertEqual(resultado.returncode, 0, resultado.stderr.strip())
        tapados = resultado.stdout.splitlines()
        self.assertEqual(tapados, [],
                         "Archivos en git que el .gitignore ahora ignora: "
                         + ", ".join(tapados))


if __name__ == "__main__":
    unittest.main()
