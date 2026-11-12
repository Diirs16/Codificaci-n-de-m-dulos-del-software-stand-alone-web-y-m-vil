"""
Pruebas del item 6.7 de la auditoria (A-36): las guias del repositorio no
llevan rutas personales de Windows (C:\\Users\\<nombre-real>\\...).

Antes, PetConnect.Mobile/EJECUCION.md llamaba a adb.exe y emulator.exe con la
ruta completa del SDK de Android en el PC del dueno, y
Documentacion/DESPLIEGUE-Railway-Vercel.md citaba la carpeta del proyecto en
su Escritorio. A otra persona esos comandos no le funcionan y ademas dejan ver
el nombre de la cuenta de Windows del dueno (dato personal, Ley 1581).
El dueno aprobo la opcion A: usar $env:LOCALAPPDATA (variable que Windows ya
trae y que apunta a C:\\Users\\<quien-sea>\\AppData\\Local).

Lo que se vigila:
- Ningun .md del repositorio tiene una ruta C:\\Users\\<nombre>\\ (tambien
  C:/Users/... o /c/Users/... de Git Bash) con un nombre real. Se permiten los
  rellenos entre < > (por ejemplo <usuario>) y las cuentas genericas de
  Windows (Public, Default). Se saltan AUDITORIA y PRIORIDADES (son el
  registro de lo que se encontro y no se cambian), node_modules, salidas de
  compilacion y carpetas que empiezan por punto (.git, .venv, .claude).
- En EJECUCION.md, cada comando que llama a adb.exe o emulator.exe empieza
  con $env:LOCALAPPDATA\\Android\\Sdk\\.
- La busqueda funciona (prueba con una carpeta temporal), para que una regla
  de exclusion mal escrita no deje la prueba pasando sin revisar nada.

No necesitan base de datos ni internet. Si las guias no estan (por ejemplo,
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
RUTA_EJECUCION = os.path.join(RAIZ_REPO, "PetConnect.Mobile", "EJECUCION.md")

# Registro de la auditoria: citan las rutas viejas a proposito.
ARCHIVOS_REGISTRO = {
    "Documentacion/Auditoria/AUDITORIA-PetConnect-2026-11-03.md",
    "Documentacion/Auditoria/PRIORIDADES-PetConnect-2026-11-03.md",
}
CARPETAS_IGNORADAS = {"node_modules", "dist", "build", "__pycache__"}
# Cuentas de Windows que no son de una persona.
CUENTAS_GENERICAS = {"public", "default", "default user", "all users"}

# C:\Users\nombre, C:/Users/nombre o /c/Users/nombre. El nombre no puede
# empezar por "<", asi que los rellenos como <usuario> no coinciden.
PATRON_RUTA_USUARIO = re.compile(
    r"(?:\b[A-Za-z]:|(?<![\w.])/[A-Za-z])[\\/]+Users[\\/]+([^\\/\s`\"'<>|*?]+)",
    flags=re.IGNORECASE,
)
# Linea de PowerShell que ejecuta un .exe con el operador &.
PATRON_LLAMADA_EXE = re.compile(r'^\s*&\s*"([^"]*\\(?:adb|emulator)\.exe)"',
                                flags=re.IGNORECASE)
PREFIJO_SDK = "$env:LOCALAPPDATA\\Android\\Sdk\\"


def _leer(ruta):
    with open(ruta, encoding="utf-8", errors="replace") as archivo:
        return archivo.read()


def buscar_markdown(raiz):
    """Rutas relativas (con /) de los .md bajo `raiz`, saltando lo ajeno."""
    encontrados = []
    for carpeta, subcarpetas, archivos in os.walk(raiz):
        # Se modifica la lista en su lugar para que os.walk no entre ahi.
        subcarpetas[:] = [
            nombre for nombre in subcarpetas
            if not nombre.startswith(".") and nombre not in CARPETAS_IGNORADAS
        ]
        for nombre in archivos:
            if not nombre.lower().endswith(".md"):
                continue
            relativa = os.path.relpath(os.path.join(carpeta, nombre), raiz)
            relativa = relativa.replace(os.sep, "/")
            if relativa not in ARCHIVOS_REGISTRO:
                encontrados.append(relativa)
    return sorted(encontrados)


def rutas_personales(texto):
    """Lista de (numero de linea, ruta) con un nombre de usuario real."""
    hallazgos = []
    for numero, linea in enumerate(texto.splitlines(), start=1):
        for coincidencia in PATRON_RUTA_USUARIO.finditer(linea):
            nombre = coincidencia.group(1).strip().lower()
            if nombre not in CUENTAS_GENERICAS:
                hallazgos.append((numero, coincidencia.group(0)))
    return hallazgos


class BusquedaDeRutasTest(unittest.TestCase):
    """La busqueda encuentra lo propio, salta lo ajeno y distingue rellenos."""

    def test_busca_markdown_propios_y_salta_registro_y_dependencias(self):
        with tempfile.TemporaryDirectory() as tmp:
            propios = [
                "README.md",
                "PetConnect.Mobile/EJECUCION.md",
                "Documentacion/GUIA.md",
            ]
            ajenos = [
                "Documentacion/Auditoria/AUDITORIA-PetConnect-2026-11-03.md",
                "Documentacion/Auditoria/PRIORIDADES-PetConnect-2026-11-03.md",
                "PetConnect.Mobile/node_modules/expo/README.md",
                ".claude/worktrees/x/EJECUCION.md",
                "web/dist/NOTAS.md",
                "Documentacion/notas.txt",
            ]
            for relativa in propios + ajenos:
                ruta = os.path.join(tmp, *relativa.split("/"))
                os.makedirs(os.path.dirname(ruta), exist_ok=True)
                with open(ruta, "w", encoding="utf-8") as archivo:
                    archivo.write("texto")
            self.assertEqual(buscar_markdown(tmp), sorted(propios))

    def test_detecta_nombres_reales_y_deja_pasar_rellenos(self):
        con_nombre = (
            '& "C:\\Users\\maria\\AppData\\Local\\Android\\Sdk\\adb.exe"\n'
            "Desde `C:/Users/Juan Perez/Escritorio/proyecto`\n"
            "cd /c/Users/pedro/OneDrive\n"
            "d:\\users\\ana\\x\n"
        )
        self.assertEqual([n for n, _ in rutas_personales(con_nombre)],
                         [1, 2, 3, 4])
        sin_nombre = (
            "| Android SDK | `C:\\Users\\<usuario>\\AppData\\Local\\Android\\Sdk` |\n"
            "vale `C:\\Users\\<tu-usuario>\\AppData\\Local`\n"
            '& "$env:LOCALAPPDATA\\Android\\Sdk\\platform-tools\\adb.exe" devices\n'
            "C:\\Users\\Public\\Documents y C:\\Program Files\\Android\n"
            "https://ejemplo.com/api/Users/5\n"
        )
        self.assertEqual(rutas_personales(sin_nombre), [])


@unittest.skipUnless(os.path.isfile(RUTA_EJECUCION),
                     "Guias del repositorio no disponibles (p. ej. en Docker)")
class RutasDelRepositorioTest(unittest.TestCase):

    def test_ningun_markdown_tiene_rutas_personales(self):
        problemas = []
        for relativa in buscar_markdown(RAIZ_REPO):
            ruta = os.path.join(RAIZ_REPO, *relativa.split("/"))
            for numero, _ruta in rutas_personales(_leer(ruta)):
                # Solo archivo y linea: no se repite el nombre de usuario.
                problemas.append(f"{relativa}:{numero}")
        self.assertEqual(
            problemas, [],
            "Estas lineas tienen una ruta C:\\Users\\<nombre-real>\\; usar "
            "$env:LOCALAPPDATA, una ruta relativa o un relleno como "
            "<usuario>: " + ", ".join(problemas),
        )

    def test_ejecucion_llama_adb_y_emulator_con_localappdata(self):
        llamadas = [
            coincidencia.group(1)
            for coincidencia in map(PATRON_LLAMADA_EXE.match,
                                    _leer(RUTA_EJECUCION).splitlines())
            if coincidencia
        ]
        nombres = {os.path.basename(r.replace("\\", "/")).lower()
                   for r in llamadas}
        self.assertEqual(nombres, {"adb.exe", "emulator.exe"},
                         "EJECUCION.md debe tener los comandos de adb y del "
                         "emulador")
        sin_variable = [r for r in llamadas if not r.startswith(PREFIJO_SDK)]
        self.assertEqual(
            sin_variable, [],
            f"Cada llamada a adb.exe/emulator.exe debe empezar con "
            f"{PREFIJO_SDK}",
        )


if __name__ == "__main__":
    unittest.main()
