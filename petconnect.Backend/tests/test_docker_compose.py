"""
Pruebas de regresion de A-30 (item 5.2 de PRIORIDADES, parte 3: docker-compose.yml).

Lo que revisan, sin Docker ni base de datos (corren en Windows y en la CI):
- docker-compose.yml (raiz): los servicios db, api y web; db con mariadb:10.11,
  volumen con nombre, SOLO schema.sql en docker-entrypoint-initdb.d y healthcheck;
  api con env_file, DB_HOST=db y PROXY_CONFIABLE=1, esperando a que la BD este
  sana; solo la web publica un puerto (8080); ninguna contrasena ni clave escrita.
- docker/bd.env.example y docker/api.env.example: solo nombres de variables, con
  el valor vacio, y los nombres de la API existen en petconnect.Backend/.env.example.
- Git ignora docker/bd.env y docker/api.env (pero no sus plantillas).

El compose se lee con un lector de YAML minimo (abajo), para no agregar PyYAML
como dependencia: solo entiende lo que usa este compose (mapas, listas con "- "
y comentarios). Si el compose usa algo mas, el lector falla y la prueba lo dice.

No se lee ningun .env real ni se imprime ningun valor de configuracion.

Ejecutar desde petconnect.Backend, con el entorno virtual activo:
    python -m unittest discover -s tests -v
"""
import os
import re
import shutil
import subprocess
import unittest

CARPETA_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAIZ = os.path.dirname(CARPETA_BACKEND)
RUTA_COMPOSE = os.path.join(RAIZ, "docker-compose.yml")
RUTA_NGINX = os.path.join(RAIZ, "PetConnect.Front", "petconnect-app", "nginx.conf")
RUTA_PLANTILLA_BACKEND = os.path.join(CARPETA_BACKEND, ".env" + ".example")
RUTA_PLANTILLA_BD = os.path.join(RAIZ, "docker", "bd.env.example")
RUTA_PLANTILLA_API = os.path.join(RAIZ, "docker", "api.env.example")

# Palabras que delatan un secreto en el nombre de una variable
PATRON_SECRETO = re.compile(r"PASSWORD|SECRET|KEY|TOKEN|PASS\b", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Lector de YAML minimo
# ---------------------------------------------------------------------------
def _quitar_comentario(linea):
    """Corta la linea en el primer # que no este dentro de comillas."""
    comilla = None
    for i, letra in enumerate(linea):
        if comilla:
            if letra == comilla:
                comilla = None
        elif letra in "\"'":
            comilla = letra
        elif letra == "#" and (i == 0 or linea[i - 1] in " \t"):
            return linea[:i]
    return linea


def _escalar(texto):
    """Quita las comillas de un valor. Las listas [a, b] quedan como texto."""
    texto = texto.strip()
    if len(texto) >= 2 and texto[0] == texto[-1] and texto[0] in "\"'":
        return texto[1:-1]
    return texto


def leer_yaml_simple(texto):
    """Convierte el YAML de un compose sencillo en diccionarios y listas."""
    lineas = []
    for linea in texto.splitlines():
        if "\t" in linea[: len(linea) - len(linea.lstrip())]:
            raise ValueError("YAML con tabuladores en la sangria")
        linea = _quitar_comentario(linea).rstrip()
        if linea.strip():
            lineas.append(linea)

    raiz = {}
    pila = [(-1, raiz)]  # (sangria del dueno, contenedor)
    for i, linea in enumerate(lineas):
        sangria = len(linea) - len(linea.lstrip(" "))
        contenido = linea.strip()
        while pila[-1][0] >= sangria:
            pila.pop()
        padre = pila[-1][1]

        if contenido.startswith("- "):
            item = contenido[2:]
            if not isinstance(padre, list):
                raise ValueError(f"Lista fuera de lugar en la linea: {contenido}")
            if re.match(r"^[\w.-]+:(\s|$)", item):
                raise ValueError(f"Lista de mapas no soportada: {contenido}")
            padre.append(_escalar(item))
            continue

        if not isinstance(padre, dict) or ":" not in contenido:
            raise ValueError(f"Linea no soportada: {contenido}")
        clave, _, valor = contenido.partition(":")
        clave = _escalar(clave)
        if clave in padre:
            raise ValueError(f"Clave repetida: {clave}")
        if valor.strip():
            padre[clave] = _escalar(valor)
            continue
        # Sin valor: lo que viene debajo (mas adentro) es una lista o un mapa
        siguiente = lineas[i + 1] if i + 1 < len(lineas) else ""
        sangria_sig = len(siguiente) - len(siguiente.lstrip(" "))
        if siguiente and sangria_sig > sangria:
            hijo = [] if siguiente.strip().startswith("- ") else {}
            pila.append((sangria, hijo))
        else:
            hijo = None  # clave vacia (p. ej. un volumen sin opciones)
        padre[clave] = hijo
    return raiz


def leer_plantilla(ruta):
    """Devuelve [(nombre, valor)] de las lineas NOMBRE=valor (sin comentarios)."""
    with open(ruta, encoding="utf-8") as archivo:
        lineas = archivo.read().splitlines()
    variables = []
    for linea in lineas:
        linea = linea.strip()
        if not linea or linea.startswith("#"):
            continue
        nombre, signo, valor = linea.partition("=")
        if not signo:
            raise ValueError(f"Linea sin '=' en {os.path.basename(ruta)}")
        variables.append((nombre.strip(), valor))
    return variables


def leer_compose():
    with open(RUTA_COMPOSE, encoding="utf-8") as archivo:
        return leer_yaml_simple(archivo.read())


# ---------------------------------------------------------------------------
# Pruebas del lector (para confiar en las demas)
# ---------------------------------------------------------------------------
class PruebasLectorYaml(unittest.TestCase):
    def test_lee_mapas_listas_comentarios_y_comillas(self):
        texto = (
            "# comentario\n"
            "servicios:\n"
            "  uno:\n"
            "    imagen: mariadb:10.11  # al final\n"
            "    puertos:\n"
            "      - \"8080:80\"\n"
            "    texto: 'con # dentro'\n"
            "  dos:\n"
            "    vacio:\n"
            "volumenes:\n"
            "  datos:\n"
        )
        datos = leer_yaml_simple(texto)
        self.assertEqual(datos["servicios"]["uno"]["imagen"], "mariadb:10.11")
        self.assertEqual(datos["servicios"]["uno"]["puertos"], ["8080:80"])
        self.assertEqual(datos["servicios"]["uno"]["texto"], "con # dentro")
        self.assertIsNone(datos["servicios"]["dos"]["vacio"])
        self.assertEqual(datos["volumenes"], {"datos": None})

    def test_rechaza_lo_que_no_entiende(self):
        for texto in ("a:\n  - b: 1\n", "a:\n\tb: 1\n", "a: 1\na: 2\n"):
            with self.subTest(texto=texto):
                with self.assertRaises(ValueError):
                    leer_yaml_simple(texto)


# ---------------------------------------------------------------------------
# docker-compose.yml
# ---------------------------------------------------------------------------
class PruebasCompose(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.compose = leer_compose()
        cls.servicios = cls.compose["services"]

    def test_tiene_los_tres_servicios(self):
        self.assertEqual(set(self.servicios), {"db", "api", "web"})

    def test_el_servicio_api_es_el_que_busca_nginx(self):
        with open(RUTA_NGINX, encoding="utf-8") as archivo:
            nginx = archivo.read()
        self.assertIn("proxy_pass http://api:5000;", nginx)
        self.assertIn("api", self.servicios)

    # ---------- db ----------
    def test_bd_es_mariadb_10_11(self):
        self.assertEqual(self.servicios["db"]["image"], "mariadb:10.11")

    def test_bd_monta_solo_schema_sql_en_el_arranque(self):
        montajes = self.servicios["db"]["volumes"]
        iniciales = [m for m in montajes if "/docker-entrypoint-initdb.d" in m]
        self.assertEqual(len(iniciales), 1, "un solo archivo en docker-entrypoint-initdb.d")
        origen, destino, *opciones = iniciales[0].split(":")
        self.assertEqual(origen, "./petconnect.Backend/sql/schema.sql")
        self.assertTrue(destino.endswith(".sql"), "se monta el archivo, no la carpeta sql/")
        self.assertEqual(opciones, ["ro"], "solo lectura")
        self.assertTrue(os.path.isfile(os.path.join(RAIZ, origen)))
        for montaje in montajes:
            self.assertNotIn("migraciones", montaje)

    def test_bd_guarda_los_datos_en_un_volumen_con_nombre(self):
        montajes = self.servicios["db"]["volumes"]
        datos = [m for m in montajes if m.split(":")[1] == "/var/lib/mysql"]
        self.assertEqual(len(datos), 1)
        nombre = datos[0].split(":")[0]
        self.assertRegex(nombre, r"^\w+$", "volumen con nombre, no una carpeta del PC")
        self.assertIn(nombre, self.compose["volumes"])

    def test_bd_tiene_healthcheck(self):
        prueba = self.servicios["db"]["healthcheck"]["test"]
        self.assertIn("healthcheck.sh", prueba)
        self.assertIn("--connect", prueba)

    def test_bd_crea_la_base_petconnect_con_utf8mb4(self):
        self.assertEqual(self.servicios["db"]["environment"]["MARIADB_DATABASE"], "petconnect")
        self.assertIn("--character-set-server=utf8mb4", self.servicios["db"]["command"])

    # ---------- api ----------
    def test_api_se_construye_del_backend(self):
        self.assertEqual(self.servicios["api"]["build"], "./petconnect.Backend")
        self.assertTrue(os.path.isfile(os.path.join(CARPETA_BACKEND, "Dockerfile")))

    def test_api_usa_la_bd_del_compose_y_el_proxy(self):
        entorno = self.servicios["api"]["environment"]
        self.assertEqual(entorno["DB_HOST"], "db")
        self.assertEqual(entorno["DB_PORT"], "3306")
        self.assertEqual(entorno["DB_NAME"], self.servicios["db"]["environment"]["MARIADB_DATABASE"])
        self.assertEqual(entorno["PROXY_CONFIABLE"], "1")

    def test_api_espera_a_que_la_bd_este_sana(self):
        self.assertEqual(self.servicios["api"]["depends_on"]["db"]["condition"], "service_healthy")

    def test_api_sin_depuracion_ni_modo_desarrollo(self):
        entorno = self.servicios["api"]["environment"]
        self.assertNotIn("FLASK_DEBUG", entorno)
        self.assertNotIn("APP_ENV", entorno)

    # ---------- web ----------
    def test_web_se_construye_del_front_y_espera_a_la_api(self):
        web = self.servicios["web"]
        self.assertEqual(web["build"], "./PetConnect.Front/petconnect-app")
        self.assertIn("api", web["depends_on"])

    def test_solo_la_web_publica_un_puerto(self):
        self.assertEqual(self.servicios["web"]["ports"], ["8080:80"])
        self.assertNotIn("ports", self.servicios["db"])
        self.assertNotIn("ports", self.servicios["api"])

    # ---------- secretos ----------
    def test_los_secretos_entran_por_env_file(self):
        self.assertEqual(self.servicios["db"]["env_file"], ["docker/bd.env"])
        self.assertEqual(self.servicios["api"]["env_file"], ["docker/api.env"])

    def test_ninguna_contrasena_ni_clave_escrita(self):
        for nombre, servicio in self.servicios.items():
            for variable in (servicio.get("environment") or {}):
                with self.subTest(servicio=nombre, variable=variable):
                    self.assertIsNone(PATRON_SECRETO.search(variable))
        with open(RUTA_COMPOSE, encoding="utf-8") as archivo:
            texto = archivo.read()
        # Ni en otra forma (lista "- CLAVE=valor" o un args de build)
        self.assertIsNone(re.search(r"^\s*-?\s*\w*(PASSWORD|SECRET|_KEY|TOKEN)\w*\s*[:=]\s*\S",
                                    texto, re.MULTILINE))


# ---------------------------------------------------------------------------
# docker/*.env.example
# ---------------------------------------------------------------------------
class PruebasPlantillasDocker(unittest.TestCase):
    def test_plantillas_solo_con_nombres_y_valores_vacios(self):
        for ruta in (RUTA_PLANTILLA_BD, RUTA_PLANTILLA_API):
            variables = leer_plantilla(ruta)
            self.assertTrue(variables)
            for nombre, valor in variables:
                with self.subTest(archivo=os.path.basename(ruta), variable=nombre):
                    self.assertRegex(nombre, r"^[A-Z][A-Z0-9_]*$")
                    self.assertEqual(valor, "", "la plantilla no lleva valores")

    def test_plantilla_de_la_bd(self):
        nombres = {n for n, _ in leer_plantilla(RUTA_PLANTILLA_BD)}
        self.assertEqual(nombres, {"MARIADB_ROOT_PASSWORD", "MARIADB_USER", "MARIADB_PASSWORD"})

    def test_plantilla_de_la_api_sale_del_env_example_del_backend(self):
        api = {n for n, _ in leer_plantilla(RUTA_PLANTILLA_API)}
        backend = {n for n, _ in leer_plantilla(RUTA_PLANTILLA_BACKEND)}
        self.assertLessEqual(api, backend, "variables que el backend no conoce")
        self.assertLessEqual({"DB_USER", "DB_PASSWORD", "JWT_SECRET", "FERNET_KEY"}, api)

    def test_plantilla_de_la_api_sin_lo_que_pone_el_compose(self):
        api = {n for n, _ in leer_plantilla(RUTA_PLANTILLA_API)}
        for nombre in ("DB_HOST", "DB_PORT", "DB_NAME", "PROXY_CONFIABLE", "FLASK_DEBUG", "API_HOST"):
            with self.subTest(variable=nombre):
                self.assertNotIn(nombre, api)

    @unittest.skipUnless(shutil.which("git") and os.path.isdir(os.path.join(RAIZ, ".git")),
                         "sin git o fuera del repositorio")
    def test_git_ignora_los_archivos_reales_y_no_las_plantillas(self):
        def ignorado(ruta):
            resultado = subprocess.run(["git", "check-ignore", "-q", "--no-index", ruta],
                                       cwd=RAIZ, capture_output=True)
            return resultado.returncode == 0

        for nombre in ("bd", "api"):
            with self.subTest(archivo=nombre):
                self.assertTrue(ignorado(f"docker/{nombre}" + ".env"))
                self.assertFalse(ignorado(f"docker/{nombre}" + ".env.example"))


if __name__ == "__main__":
    unittest.main()
