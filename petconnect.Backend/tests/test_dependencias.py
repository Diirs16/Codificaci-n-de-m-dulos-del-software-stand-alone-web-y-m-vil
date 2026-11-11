"""
Pruebas del item 5.4 de la auditoria (A-29): dependencias del backend sin
vulnerabilidades conocidas y pip-audit en la CI. No necesitan base de datos ni
internet: leen requirements.txt, requirements-dev.txt, el Dockerfile y la CI
(.github/workflows/ci.yml) como texto. La consulta real de los avisos del dia la
hace pip-audit (en tu PC y en la CI).

Lo que se vigila:
- El 10/11/2026 la base publica OSV dio avisos para PyJWT 2.13.0 (15; uno hacia
  responder 500 con un token de cabecera muy anidada, ver test_seguridad.py),
  dnspython 2.8.0 (CPU al buscar los MX del dominio del correo) y cryptography
  49.0.0. Si alguien vuelve a una version vulnerable, esta prueba falla.
- pip-audit es herramienta, no parte de la API: va en requirements-dev.txt con
  version fija y el Dockerfile no lo instala (el .dockerignore lo deja fuera; eso
  lo revisa test_dockerignore.py).
- La CI instala requirements-dev.txt y corre pip-audit sobre requirements.txt;
  falla de verdad (sin continue-on-error, "|| true" ni avisos ignorados).

Ejecutar desde petconnect.Backend, con el entorno virtual activo:
    python -m unittest discover -s tests -v
"""
import os
import re
import unittest

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAIZ_REPO = os.path.dirname(BACKEND)

# Primera version SIN los avisos del 10/11/2026
VERSION_MINIMA = {
    "pyjwt": "2.15.1",
    "dnspython": "2.9.2",
    "cryptography": "50.0.2",
}

LINEA_FIJADA = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._\-]*)==(\d+(?:\.\d+)*)$")


def _leer(*partes):
    with open(os.path.join(*partes), encoding="utf-8") as archivo:
        return archivo.read()


def _lineas_utiles(texto):
    """Lineas sin comentarios ni vacias."""
    lineas = (linea.strip() for linea in texto.splitlines())
    return [linea for linea in lineas if linea and not linea.startswith("#")]


def _paquetes(nombre_archivo):
    """{"pyjwt": "2.15.1", ...} con los nombres en minuscula."""
    paquetes = {}
    for linea in _lineas_utiles(_leer(BACKEND, nombre_archivo)):
        coincide = LINEA_FIJADA.match(linea)
        if coincide:
            paquetes[coincide.group(1).lower()] = coincide.group(2)
    return paquetes


def _como_tupla(version):
    return tuple(int(parte) for parte in version.split("."))


def _pasos_del_trabajo_backend():
    """Texto de cada paso del trabajo "backend" de la CI, sin comentarios."""
    lineas = _leer(RAIZ_REPO, ".github", "workflows", "ci.yml").splitlines()
    inicio = next(i for i, linea in enumerate(lineas) if re.match(r"^ {2}backend:\s*$", linea))
    fin = next((i for i in range(inicio + 1, len(lineas)) if re.match(r"^ {2}\S", lineas[i])), len(lineas))
    pasos = []
    for linea in lineas[inicio:fin]:
        if re.match(r"^\s*#", linea):
            continue
        if re.match(r"^ {6}- ", linea):
            pasos.append("")
        if pasos:
            pasos[-1] += linea.strip() + "\n"
    return pasos


def _indice(pasos, patron):
    return next((i for i, paso in enumerate(pasos) if re.search(patron, paso)), -1)


class PruebasRequirements(unittest.TestCase):
    """Las dependencias de la API: version fija y sin los avisos conocidos."""

    def test_toda_dependencia_de_la_api_con_version_fija(self):
        for linea in _lineas_utiles(_leer(BACKEND, "requirements.txt")):
            self.assertRegex(linea, LINEA_FIJADA, f"sin version fija (paquete==x.y.z): {linea}")

    def test_versiones_sin_los_avisos_del_10_11_2026(self):
        paquetes = _paquetes("requirements.txt")
        for nombre, minima in VERSION_MINIMA.items():
            self.assertIn(nombre, paquetes, f"{nombre} ya no esta en requirements.txt: revisa esta prueba")
            self.assertGreaterEqual(
                _como_tupla(paquetes[nombre]), _como_tupla(minima),
                f"{nombre} {paquetes[nombre]} tiene vulnerabilidades conocidas; minimo {minima}",
            )

    def test_pip_audit_no_es_dependencia_de_la_api(self):
        self.assertNotIn("pip-audit", _paquetes("requirements.txt"))


class PruebasHerramientas(unittest.TestCase):
    """pip-audit vive en requirements-dev.txt y no entra en la imagen de Docker."""

    def test_pip_audit_con_version_fija(self):
        lineas = _lineas_utiles(_leer(BACKEND, "requirements-dev.txt"))
        pip_audit = [linea for linea in lineas if linea.lower().startswith("pip-audit")]
        self.assertEqual(len(pip_audit), 1, "pip-audit debe estar una vez en requirements-dev.txt")
        self.assertRegex(pip_audit[0], LINEA_FIJADA)

    def test_el_dockerfile_solo_instala_las_dependencias_de_la_api(self):
        lineas = _lineas_utiles(_leer(BACKEND, "Dockerfile"))
        self.assertFalse([linea for linea in lineas if "requirements-dev" in linea])
        self.assertFalse([linea for linea in lineas if re.search(r"pip-audit|pip_audit", linea)])
        self.assertIn("RUN pip install -r requirements.txt", lineas)


class PruebasCi(unittest.TestCase):
    """La CI del backend corre pip-audit y falla si encuentra algo."""

    def setUp(self):
        self.pasos = _pasos_del_trabajo_backend()

    def test_instala_las_herramientas_y_audita_despues_de_las_dependencias(self):
        i_dependencias = _indice(self.pasos, r"run:\s*python -m pip install -r requirements\.txt")
        i_herramientas = _indice(self.pasos, r"run:\s*python -m pip install -r requirements-dev\.txt")
        i_auditoria = _indice(self.pasos, r"run:\s*python -m pip_audit\b")
        self.assertGreaterEqual(i_dependencias, 0, "falta instalar requirements.txt")
        self.assertGreaterEqual(i_herramientas, 0, "falta instalar requirements-dev.txt")
        self.assertGreaterEqual(i_auditoria, 0, "falta el paso de pip-audit")
        self.assertLess(i_herramientas, i_auditoria)

    def test_audita_requirements_y_falla_de_verdad(self):
        i_auditoria = _indice(self.pasos, r"run:\s*python -m pip_audit\b")
        self.assertGreaterEqual(i_auditoria, 0, "falta el paso de pip-audit")
        paso = self.pasos[i_auditoria]
        self.assertRegex(paso, r"-r requirements\.txt\b")
        self.assertIn("--strict", paso, "sin --strict, un paquete que no se pudo revisar pasa en silencio")
        self.assertNotIn("continue-on-error", paso, "si queda en 'solo avisar', nadie lo mira")
        self.assertNotRegex(paso, r"\|\|\s*true")
        self.assertNotIn("--ignore-vuln", paso, "ignorar un aviso se decide con el dueno y se anota aqui")

    def test_pip_audit_sale_de_requirements_dev_y_no_de_otra_version(self):
        for paso in self.pasos:
            self.assertNotRegex(paso, r"pip install[^\n]*\bpip-audit\b", "la version de pip-audit va solo en requirements-dev.txt")


if __name__ == "__main__":
    unittest.main()
