"""
Pruebas del item 6.10 de la auditoria (A-37): ningun archivo del repositorio
vuelve a citar el nombre viejo del repositorio de GitHub.

El repositorio se llamaba "Codificaci-n-de-m-dulos-del-software-stand-alone-
web-y-m-vil": GitHub cambio cada letra con tilde por un guion. En el 5.5
(11/11/2026) el dueno lo renombro a Diirs16/PETCONNECT-PROYECTO. GitHub
redirige la direccion vieja a la nueva mientras nadie cree otro repositorio
con el nombre viejo en la misma cuenta.

Decision del dueno (opcion A): los dos Word de GA8 (evidencias ya entregadas)
se dejan como estan; por eso solo se revisan los archivos de TEXTO con
seguimiento de git. Se saltan AUDITORIA y PRIORIDADES (son el registro de lo
que se encontro y no se cambian).

Lo que se vigila:
- Ningun archivo de texto con seguimiento (git ls-files) tiene el nombre viejo.
- La busqueda funciona (prueba con un repositorio temporal), para que una
  regla mal escrita no deje la prueba pasando sin revisar nada.

No necesitan base de datos ni internet. Si no hay git o la carpeta no es un
repositorio (por ejemplo, dentro de la imagen de Docker), se omiten.

Ejecutar desde petconnect.Backend, con el entorno virtual activo:
    python -m unittest discover -s tests -v
"""
import os
import shutil
import subprocess
import tempfile
import unittest

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAIZ_REPO = os.path.dirname(BACKEND)

# Se arma por partes para que este mismo archivo no cuente como hallazgo.
NOMBRE_VIEJO = "codificaci" + "-n-de-m-dulos"

# Registro de la auditoria: citan el nombre viejo a proposito.
ARCHIVOS_REGISTRO = {
    "Documentacion/Auditoria/AUDITORIA-PetConnect-2026-11-03.md",
    "Documentacion/Auditoria/PRIORIDADES-PetConnect-2026-11-03.md",
}


def _git_disponible(carpeta):
    """True si hay git y `carpeta` esta dentro de un repositorio."""
    if shutil.which("git") is None:
        return False
    resultado = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=carpeta, capture_output=True, text=True,
    )
    return resultado.returncode == 0 and resultado.stdout.strip() == "true"


def archivos_con_nombre_viejo(raiz):
    """Rutas (con /) de los archivos de texto con seguimiento que lo citan."""
    salida = subprocess.run(
        ["git", "-c", "core.quotepath=off", "ls-files", "-z"],
        cwd=raiz, capture_output=True, check=True,
    ).stdout.decode("utf-8")
    encontrados = []
    for relativa in filter(None, salida.split("\0")):
        if relativa in ARCHIVOS_REGISTRO:
            continue
        ruta = os.path.join(raiz, *relativa.split("/"))
        if not os.path.isfile(ruta):
            continue  # borrado en la copia de trabajo y aun sin commit
        with open(ruta, "rb") as archivo:
            datos = archivo.read()
        if b"\0" in datos:
            continue  # binario (Word, Excel, imagenes): fuera, opcion A
        if NOMBRE_VIEJO in datos.decode("utf-8", errors="replace").lower():
            encontrados.append(relativa)
    return sorted(encontrados)


@unittest.skipUnless(shutil.which("git"), "git no esta instalado")
class BusquedaDelNombreViejoTest(unittest.TestCase):
    """La busqueda encuentra lo propio y salta el registro y los binarios."""

    def test_busqueda_con_repositorio_temporal(self):
        nombre = "Codificaci-n-de-m-dulos-del-software"
        archivos = {
            # Deben aparecer (texto con seguimiento, sin importar mayusculas).
            "README.md": f"Repo: https://github.com/x/{nombre}\n",
            "docs/guia.txt": f"ver {nombre.upper()}\n",
            # No deben aparecer.
            "Documentacion/Auditoria/AUDITORIA-PetConnect-2026-11-03.md":
                f"| A-37 | `{nombre}` |\n",
            "Documentacion/Auditoria/PRIORIDADES-PetConnect-2026-11-03.md":
                f"{nombre}\n",
            "evidencia.docx": f"PK\0\0{nombre}",
            "limpio.md": "Repo: PETCONNECT-PROYECTO\n",
        }
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(["git", "init", "-q"], cwd=tmp, check=True)
            for relativa, contenido in archivos.items():
                ruta = os.path.join(tmp, *relativa.split("/"))
                os.makedirs(os.path.dirname(ruta), exist_ok=True)
                with open(ruta, "wb") as archivo:
                    archivo.write(contenido.encode("utf-8"))
            # Este no se agrega a git: no tiene seguimiento.
            with open(os.path.join(tmp, "suelto.md"), "w",
                      encoding="utf-8") as archivo:
                archivo.write(nombre)
            # capture_output: que los avisos de fin de linea de git (LF/CRLF)
            # no ensucien la salida de las pruebas.
            subprocess.run(["git", "add", "--"] + list(archivos),
                           cwd=tmp, check=True, capture_output=True)
            self.assertEqual(archivos_con_nombre_viejo(tmp),
                             ["README.md", "docs/guia.txt"])


@unittest.skipUnless(_git_disponible(RAIZ_REPO),
                     "Sin repositorio git (p. ej. dentro de Docker)")
class NombreDelRepositorioTest(unittest.TestCase):

    def test_ningun_archivo_de_texto_cita_el_nombre_viejo(self):
        problemas = archivos_con_nombre_viejo(RAIZ_REPO)
        self.assertEqual(
            problemas, [],
            "Estos archivos citan el nombre viejo del repositorio; usar "
            "https://github.com/Diirs16/PETCONNECT-PROYECTO: "
            + ", ".join(problemas),
        )


if __name__ == "__main__":
    unittest.main()
