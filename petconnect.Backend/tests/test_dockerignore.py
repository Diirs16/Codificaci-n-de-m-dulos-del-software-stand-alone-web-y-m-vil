"""
Prueba de regresion de A-30 (item 5.1 de PRIORIDADES): cada modulo tiene un
.dockerignore que deja FUERA de la imagen de Docker los secretos (.env, claves),
las dependencias y compilaciones locales (node_modules, .venv, __pycache__, dist)
y, a la vez, deja DENTRO lo que la imagen necesita (api.py, package.json, src/...).

Docker NO lee el .gitignore, por eso cada modulo necesita su .dockerignore.

No hace falta Docker ni base de datos: la prueba trae un pequeno simulador de las
reglas de Docker (las mismas de moby/patternmatcher, que usa "docker build"):
- cada linea es un patron; las vacias y las que empiezan por # se ignoran;
- "*" no cruza carpetas, "?" es un caracter, "**" cruza cualquier numero de carpetas;
- un patron sin "**/" solo aplica desde la raiz del modulo ("__pycache__" no
  excluye "dao/__pycache__");
- si un patron excluye una carpeta, excluye todo lo que hay dentro;
- "!" al inicio es una excepcion, y el ultimo patron que coincide es el que gana.

Las rutas que se revisan son nombres inventados: la prueba nunca abre el .env ni
ningun otro archivo del modulo, solo lee los .dockerignore.

Ejecutar desde petconnect.Backend, con el entorno virtual activo:
    python -m unittest discover -s tests -v
"""
import os
import re
import unittest

CARPETA_TESTS = os.path.dirname(os.path.abspath(__file__))
CARPETA_BACKEND = os.path.dirname(CARPETA_TESTS)
RAIZ_REPO = os.path.dirname(CARPETA_BACKEND)


def _patron_a_regex(patron):
    """Traduce un patron de .dockerignore a una expresion regular (como Docker)."""
    regex = "^"
    i = 0
    while i < len(patron):
        ch = patron[i]
        if ch == "*":
            if i + 1 < len(patron) and patron[i + 1] == "*":
                i += 1
                # "**/" se trata como "**"
                if i + 1 < len(patron) and patron[i + 1] == "/":
                    i += 1
                if i + 1 >= len(patron):
                    regex += ".*"
                else:
                    regex += "(.*/)?"
            else:
                regex += "[^/]*"
        elif ch == "?":
            regex += "[^/]"
        elif ch in ".+()|{}$^":
            regex += "\\" + ch
        else:
            # Letras, "/" y los corchetes de [cod] pasan tal cual
            regex += ch
        i += 1
    return re.compile(regex + "$")


def leer_patrones(texto):
    """Devuelve la lista de (es_excepcion, regex) de un .dockerignore."""
    patrones = []
    for linea in texto.splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#"):
            continue
        excepcion = linea.startswith("!")
        if excepcion:
            linea = linea[1:].strip()
        # Docker limpia la ruta: sin "/" al inicio ni al final
        linea = linea.strip("/")
        if linea:
            patrones.append((excepcion, _patron_a_regex(linea)))
    return patrones


def queda_fuera(patrones, ruta):
    """True si Docker NO mandaria esa ruta (relativa al modulo) a la imagen."""
    partes = ruta.split("/")
    # La ruta y cada carpeta que la contiene: si se excluye la carpeta, se
    # excluye lo de adentro.
    candidatos = ["/".join(partes[:n]) for n in range(1, len(partes) + 1)]
    fuera = False
    for excepcion, regex in patrones:
        if any(regex.match(c) for c in candidatos):
            fuera = not excepcion
    return fuera


# Por modulo: rutas inventadas que deben quedar fuera y dentro de la imagen.
MODULOS = {
    "petconnect.Backend": {
        "fuera": [
            ".env",
            ".env.example",
            ".env.produccion",
            "config/.env",
            "produccion.env",
            "certs/servidor.key",
            "clave.pem",
            # Las carpetas mismas, no solo sus .pyc (que tambien caen por *.py[cod])
            "dao/__pycache__",
            "tests/__pycache__",
            "__pycache__/api.cpython-314.pyc",
            "dao/__pycache__/usuario_dao.cpython-314.pyc",
            "tests/__pycache__/test_seguridad.cpython-314.pyc",
            "modelo/usuario.pyc",
            ".venv/Scripts/python.exe",
            "venv/lib/site.py",
            "postman/PetConnect.postman_collection.json",
            "DOCUMENTACION_PETCONNECT.docx",
            "api.log",
            ".git/config",
            "CLAUDE.md",
            # Item 5.2 (decision del dueno): las pruebas no van en la imagen
            "tests/test_seguridad.py",
            "tests/test_dockerignore.py",
        ],
        "dentro": [
            "api.py",
            "gunicorn.conf.py",
            "main.py",
            "seed.py",
            "requirements.txt",
            "sql/schema.sql",
            "sql/migraciones/2026-11-09.sql",
            "config/db_config.py",
            "conexion/conexion_bd.py",
            "security/passwords.py",
            "dao/usuario_dao.py",
            "vista/menu_usuarios.py",
        ],
    },
    "PetConnect.Front/petconnect-app": {
        "fuera": [
            ".env",
            ".env.production",
            ".env.local",
            "src/.env",
            "node_modules/react/index.js",
            "src/node_modules/x/index.js",
            "dist/index.html",
            "dist/assets/index.js",
            "dist-ssr/server.js",
            "npm-debug.log",
            ".vscode/settings.json",
            "CLAUDE.md",
        ],
        "dentro": [
            "package.json",
            "package-lock.json",
            "index.html",
            "vite.config.js",
            "src/main.jsx",
            "src/App.jsx",
            "src/services/api.js",
            "src/index.css",
            "public/logo.svg",
        ],
    },
    "PetConnect.Mobile": {
        "fuera": [
            ".env",
            ".env.local",
            "src/.env",
            "firma.jks",
            "credenciales/AuthKey.p8",
            "node_modules/expo/package.json",
            "android/app/build.gradle",
            "android/app/debug.keystore",
            "ios/Podfile",
            ".expo/settings.json",
            "dist/index.html",
            "web-build/index.html",
            ".kotlin/sesion.txt",
            "postman/PetConnect.postman_collection.json",
            ".postman/api.json",
            "CLAUDE.md",
        ],
        "dentro": [
            "App.js",
            "index.js",
            "app.json",
            "package.json",
            "package-lock.json",
            "assets/icon.png",
            "src/navigation/AppNavigator.js",
            "src/services/api.js",
        ],
    },
}


class TestSimuladorDocker(unittest.TestCase):
    """El simulador sigue las reglas de Docker (si fallara, las demas pruebas mentirian)."""

    def test_sin_dos_asteriscos_solo_aplica_en_la_raiz(self):
        patrones = leer_patrones("__pycache__\n")
        self.assertTrue(queda_fuera(patrones, "__pycache__/x.pyc"))
        self.assertFalse(queda_fuera(patrones, "dao/__pycache__/x.pyc"))

    def test_dos_asteriscos_aplica_en_cualquier_carpeta(self):
        patrones = leer_patrones("**/__pycache__\n")
        self.assertTrue(queda_fuera(patrones, "__pycache__/x.pyc"))
        self.assertTrue(queda_fuera(patrones, "dao/__pycache__/x.pyc"))
        self.assertFalse(queda_fuera(patrones, "dao/usuario_dao.py"))

    def test_asterisco_no_cruza_carpetas(self):
        patrones = leer_patrones("*.env\n")
        self.assertTrue(queda_fuera(patrones, "produccion.env"))
        self.assertFalse(queda_fuera(patrones, "config/produccion.env"))

    def test_gana_el_ultimo_patron_y_se_ignoran_comentarios(self):
        patrones = leer_patrones("# comentario\n\n*.md\n!README.md\n")
        self.assertTrue(queda_fuera(patrones, "CLAUDE.md"))
        self.assertFalse(queda_fuera(patrones, "README.md"))
        self.assertFalse(queda_fuera(patrones, "# comentario"))

    def test_corchetes_y_signo_de_pregunta(self):
        patrones = leer_patrones("**/*.py[cod]\nlog?.txt\n")
        self.assertTrue(queda_fuera(patrones, "modelo/usuario.pyc"))
        self.assertFalse(queda_fuera(patrones, "modelo/usuario.py"))
        self.assertTrue(queda_fuera(patrones, "log1.txt"))
        self.assertFalse(queda_fuera(patrones, "log10.txt"))


class TestDockerignoreModulos(unittest.TestCase):
    """Cada .dockerignore protege los secretos sin dejar fuera lo necesario."""

    def _patrones(self, modulo):
        ruta = os.path.join(RAIZ_REPO, *modulo.split("/"), ".dockerignore")
        self.assertTrue(
            os.path.isfile(ruta),
            f"Falta {modulo}/.dockerignore: un docker build meteria el .env en la imagen",
        )
        with open(ruta, encoding="utf-8") as archivo:
            patrones = leer_patrones(archivo.read())
        self.assertTrue(patrones, f"{modulo}/.dockerignore no tiene patrones")
        return patrones

    def _revisar(self, modulo):
        patrones = self._patrones(modulo)
        for ruta in MODULOS[modulo]["fuera"]:
            with self.subTest(modulo=modulo, ruta=ruta, debe="quedar fuera"):
                self.assertTrue(
                    queda_fuera(patrones, ruta),
                    f"{modulo}: {ruta} entraria en la imagen de Docker",
                )
        for ruta in MODULOS[modulo]["dentro"]:
            with self.subTest(modulo=modulo, ruta=ruta, debe="quedar dentro"):
                self.assertFalse(
                    queda_fuera(patrones, ruta),
                    f"{modulo}: {ruta} hace falta en la imagen y quedo excluido",
                )

    def test_backend(self):
        self._revisar("petconnect.Backend")

    def test_web(self):
        self._revisar("PetConnect.Front/petconnect-app")

    def test_movil(self):
        self._revisar("PetConnect.Mobile")


if __name__ == "__main__":
    unittest.main()
