"""
Pruebas del item 6.6 de la auditoria (A-35): el repositorio tiene UNA sola
coleccion de Postman, la del backend, y esta al dia con la API.

Antes habia tres colecciones con lo mismo: la JSON del backend
(petconnect.Backend/postman/PetConnect.postman_collection.json) y dos en
formato YAML de la app de Postman dentro de PetConnect.Mobile/postman/postman/
("PetConnect API" y "PetConnect API Copy", identicas, sin el paso 2 del inicio
de sesion), con los id de Postman Cloud en .postman/resources.yaml. El dueno
eligio la opcion A: quedarse solo con la JSON del backend, que es la mas
completa y la que citan VERIFICACION.md y la guia GA9.

Lo que se vigila:
- En todo el repositorio solo existe esa coleccion: ningun otro
  *.postman_collection.json, ningun *.request.yaml ni carpeta .postman de la
  app de Postman, y ninguna carpeta postman/postman anidada. Se saltan
  node_modules, entornos virtuales, .git, .claude (copias viejas del repo) y
  salidas de compilacion. Ojo: las carpetas .postman NO se saltan, son
  justamente lo que se busca.
- La coleccion no trae datos reales: correos solo @example.com, la variable
  token vacia, ningun JWT pegado (empiezan por "eyJ") y el encabezado
  Authorization solo con la variable {{token}}.
- Cada peticion de la coleccion corresponde a una ruta que existe en api.py
  (con el mismo metodo). Se lee api.py como texto: NO se importa, para no
  cargar el entorno real.
- Las guias que la citan (README, VERIFICACION, GA9) solo nombran rutas de
  Postman que existen y, si dicen cuantos endpoints trae, el numero coincide.
- La busqueda funciona (prueba con una carpeta temporal), para que una regla
  de exclusion mal escrita no deje la prueba pasando sin revisar nada.

No necesitan base de datos ni internet. Si la coleccion no esta (por ejemplo,
dentro de la imagen de Docker, que deja fuera postman/), se omiten.

Ejecutar desde petconnect.Backend, con el entorno virtual activo:
    python -m unittest discover -s tests -v
"""
import json
import os
import re
import tempfile
import unittest

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAIZ_REPO = os.path.dirname(BACKEND)
RUTA_COLECCION = os.path.join(BACKEND, "postman", "PetConnect.postman_collection.json")
RUTA_API = os.path.join(BACKEND, "api.py")

# Guias que pueden citar la coleccion (rutas relativas a la raiz del repo).
GUIAS = (
    "README.md",
    "VERIFICACION.md",
    os.path.join("Documentacion", "GA9-220501096-AA1-EV02-PetConnect.md"),
)

# Carpetas que no son codigo propio o que son copias/salidas generadas.
CARPETAS_IGNORADAS = {
    ".git", ".venv", "venv", ".claude", "node_modules", "dist", "build",
    "__pycache__", ".gradle", ".expo", ".kotlin",
}

# Dominios reservados para ejemplos (RFC 2606): nunca son correos reales.
DOMINIOS_EJEMPLO = ("example.com", "example.org", "example.net")


def _leer(ruta):
    with open(ruta, encoding="utf-8", errors="replace") as archivo:
        return archivo.read()


def buscar_postman(raiz):
    """Devuelve (colecciones_json, archivos_app, carpetas_anidadas) bajo `raiz`.

    - colecciones_json: archivos *.postman_collection.json
    - archivos_app: archivos del formato de la app de Postman (*.request.yaml,
      *.globals.yaml, *.postman_environment.json o cualquier archivo dentro de
      una carpeta .postman)
    - carpetas_anidadas: carpetas postman/postman (sin importar mayusculas)
    Todas las rutas van relativas a `raiz`, con "/".
    """
    colecciones, archivos_app, anidadas = [], [], []
    for carpeta, subcarpetas, archivos in os.walk(raiz):
        subcarpetas[:] = [n for n in subcarpetas if n not in CARPETAS_IGNORADAS]
        relativa = os.path.relpath(carpeta, raiz).replace(os.sep, "/")
        partes = [] if relativa == "." else relativa.lower().split("/")
        # Solo la carpeta postman/postman misma (no cada subcarpeta suya).
        if partes[-2:] == ["postman", "postman"]:
            anidadas.append(relativa)
        dentro_de_punto_postman = ".postman" in partes
        for nombre in archivos:
            ruta = nombre if relativa == "." else f"{relativa}/{nombre}"
            minuscula = nombre.lower()
            if minuscula.endswith(".postman_collection.json"):
                colecciones.append(ruta)
            elif (dentro_de_punto_postman
                  or minuscula.endswith(".request.yaml")
                  or minuscula.endswith(".globals.yaml")
                  or minuscula.endswith(".postman_environment.json")):
                archivos_app.append(ruta)
    return sorted(colecciones), sorted(archivos_app), sorted(anidadas)


def _peticiones(items, carpeta=""):
    """Recorre las carpetas de la coleccion y devuelve (nombre, request)."""
    for item in items:
        if "item" in item:
            yield from _peticiones(item["item"], f"{carpeta}{item['name']}/")
        else:
            yield f"{carpeta}{item['name']}", item["request"]


def _textos(objeto):
    """Todos los textos sueltos dentro de un JSON (para buscar datos reales)."""
    if isinstance(objeto, dict):
        for valor in objeto.values():
            yield from _textos(valor)
    elif isinstance(objeto, list):
        for valor in objeto:
            yield from _textos(valor)
    elif isinstance(objeto, str):
        yield objeto


def rutas_de_api(texto_api):
    """Lista de (metodo, regex) de cada @app.route de api.py."""
    rutas = []
    patron = re.compile(r'@app\.route\(\s*"([^"]+)"\s*,\s*methods=\[([^\]]+)\]')
    for ruta, metodos in patron.findall(texto_api):
        regex = re.sub(r"<int:[^>]+>", r"\\d+", ruta)
        regex = re.sub(r"<[^>]+>", r"[^/]+", regex)
        for metodo in re.findall(r'"(\w+)"', metodos):
            rutas.append((metodo.upper(), re.compile(f"^{regex}$")))
    return rutas


@unittest.skipUnless(os.path.isfile(RUTA_COLECCION),
                     "sin la coleccion de Postman (p. ej. dentro de la imagen de Docker)")
class PruebaUnaSolaColeccion(unittest.TestCase):

    def test_solo_existe_la_coleccion_del_backend(self):
        colecciones, archivos_app, anidadas = buscar_postman(RAIZ_REPO)
        self.assertEqual(
            colecciones, ["petconnect.Backend/postman/PetConnect.postman_collection.json"],
            "Debe haber UNA sola coleccion de Postman (la del backend); si cambio la API, "
            "actualiza esa en vez de crear otra.")
        self.assertEqual(
            archivos_app, [],
            "Hay archivos de la app de Postman (YAML o .postman): borralos o exporta la "
            "coleccion como JSON sobre la del backend. Primeros: " + ", ".join(archivos_app[:5]))
        self.assertEqual(anidadas, [], f"Carpeta de Postman anidada: {anidadas}")

    def test_la_coleccion_no_trae_datos_reales(self):
        datos = json.loads(_leer(RUTA_COLECCION))
        variables = {v.get("key"): v.get("value", "") for v in datos.get("variable", [])}
        self.assertEqual(variables.get("token", ""), "",
                         "La variable token debe ir vacia: se llena sola al iniciar sesion.")
        self.assertNotIn("auth", datos, "La coleccion no debe guardar credenciales propias.")

        for texto in _textos(datos):
            self.assertIsNone(re.search(r"eyJ[\w-]{10,}\.", texto),
                              "La coleccion trae un JWT pegado: quitalo y usa {{token}}.")
            for dominio in re.findall(r"[\w.+-]+@([\w-]+(?:\.[\w-]+)+)", texto):
                self.assertIn(dominio.lower(), DOMINIOS_EJEMPLO,
                              "Correo con un dominio que no es de ejemplo (Ley 1581): "
                              "usa @example.com.")

        for nombre, peticion in _peticiones(datos["item"]):
            for encabezado in peticion.get("header", []):
                if encabezado.get("key", "").lower() == "authorization":
                    self.assertEqual(encabezado.get("value"), "Bearer {{token}}",
                                     f"{nombre}: Authorization debe usar la variable {{{{token}}}}.")
            self.assertNotIn("auth", peticion, f"{nombre}: no guardes credenciales en la peticion.")

    def test_cada_peticion_existe_en_la_api(self):
        rutas = rutas_de_api(_leer(RUTA_API))
        self.assertGreater(len(rutas), 5, "No se pudieron leer las rutas de api.py.")
        datos = json.loads(_leer(RUTA_COLECCION))
        peticiones = list(_peticiones(datos["item"]))
        self.assertGreater(len(peticiones), 0)
        for nombre, peticion in peticiones:
            url = peticion["url"]["raw"] if isinstance(peticion["url"], dict) else peticion["url"]
            self.assertTrue(url.startswith("{{base_url}}/"),
                            f"{nombre}: la URL debe empezar por {{{{base_url}}}}.")
            camino = "/api/" + url[len("{{base_url}}/"):].split("?")[0]
            metodo = peticion["method"].upper()
            self.assertTrue(
                any(m == metodo and regex.match(camino) for m, regex in rutas),
                f"{nombre}: {metodo} {camino} no existe en api.py (coleccion desactualizada).")

    def test_las_guias_citan_rutas_que_existen(self):
        total = len(list(_peticiones(json.loads(_leer(RUTA_COLECCION))["item"])))
        revisadas = 0
        for guia in GUIAS:
            ruta_guia = os.path.join(RAIZ_REPO, guia)
            if not os.path.isfile(ruta_guia):
                continue
            revisadas += 1
            texto = _leer(ruta_guia)
            citas = re.findall(
                r"(?:PetConnect\.Mobile|petconnect\.Backend|PetConnect\.Front)/[\w./ -]*?postman[\w./-]*",
                texto, re.IGNORECASE)
            for cita in citas:
                self.assertTrue(os.path.exists(os.path.join(RAIZ_REPO, cita.rstrip("./"))),
                                f"{guia} cita {cita}, que ya no existe.")
            for numero in re.findall(r"PetConnect\.postman_collection\.json`?\s*\((\d+) endpoints", texto):
                self.assertEqual(int(numero), total,
                                 f"{guia} dice {numero} endpoints, pero la coleccion trae {total}.")
        self.assertGreater(revisadas, 0, "No se encontro ninguna guia para revisar.")


class PruebaBusqueda(unittest.TestCase):
    """La busqueda encuentra lo que debe (control positivo con carpeta temporal)."""

    def test_detecta_duplicados_anidados_y_formato_de_la_app(self):
        with tempfile.TemporaryDirectory() as raiz:
            def crear(relativa):
                ruta = os.path.join(raiz, *relativa.split("/"))
                os.makedirs(os.path.dirname(ruta), exist_ok=True)
                with open(ruta, "w", encoding="utf-8") as archivo:
                    archivo.write("{}")

            crear("back/postman/A.postman_collection.json")
            crear("movil/postman/postman/collections/API Copy/Login.request.yaml")
            crear("movil/.postman/resources.yaml")
            crear("movil/postman/globals/workspace.globals.yaml")
            # Lo ignorado no cuenta
            crear("web/node_modules/x/B.postman_collection.json")
            crear(".claude/worktrees/vieja/C.postman_collection.json")

            colecciones, archivos_app, anidadas = buscar_postman(raiz)
            self.assertEqual(colecciones, ["back/postman/A.postman_collection.json"])
            self.assertEqual(archivos_app, [
                "movil/.postman/resources.yaml",
                "movil/postman/globals/workspace.globals.yaml",
                "movil/postman/postman/collections/API Copy/Login.request.yaml",
            ])
            self.assertEqual(anidadas, ["movil/postman/postman"])


if __name__ == "__main__":
    unittest.main()
