"""
Pruebas de regresion de A-22 (item 3.4 de PRIORIDADES): la ficha de la mascota no
debe inventar datos de salud ni de tamano.

- La API devolvia vaccinated=False, sterilized=False y size="Mediano" a TODAS las
  mascotas aunque la tabla no tiene esas columnas. La web decia "Pendiente de
  vacunacion" a Luna, Milo y Max, cuya descripcion dice que estan vacunados.
  Ahora la API solo devuelve lo que trae la consulta.
- seed.py guardaba "Tamano Grande/Mediano/Pequeno" en la columna color.
- Regla 6 de CLAUDE.md: cada descripcion de seed.py que habla de salud o
  alimentacion lleva encima la marca "# REVISAR-VETERINARIO".

seed.py se lee como texto con ast (no se importa): asi la prueba no carga el .env.
La migracion que limpia el color en bases ya cargadas se prueba en
tests/test_esquema.py (PruebasMigracionColorSinBD / PruebasMigracionColorEnBD).

No usan la base real, no envian correos ni leen .env (_importar_api).

Ejecutar desde petconnect.Backend, con el entorno virtual activo:
    python -m unittest discover -s tests -v
"""
import ast
import os
import re
import sys
import unittest
from unittest import mock

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from test_errores import _importar_api  # noqa: E402

RUTA_SEED = os.path.join(RAIZ, "seed.py")

ID_MASCOTA = 3
ID_DUENO = 7
CORREO_DUENO = "dueno.prueba@ejemplo.test"   # inventado (Ley 1581)

# Los alias de las consultas de mascotas en api.py: lo unico que la API puede devolver
CAMPOS_DE_LA_BD = {"id", "name", "species", "breed", "gender", "age", "image",
                   "description", "estado"}
CAMPOS_INVENTADOS = ("vaccinated", "sterilized", "size")

# Palabras que convierten un texto en contenido de salud o alimentacion (regla 6)
PATRON_SALUD = re.compile(
    r"vacun|esteril|desparasit|cepill|aliment|prote[ií]n|hipoalerg|piel|dental|ortop",
    re.IGNORECASE,
)
MARCA = "# REVISAR-VETERINARIO"


def _fila(estado="en_adopcion"):
    """Fila como la devuelve el cursor (dictionary=True) con los alias de la consulta."""
    return {
        "id": ID_MASCOTA, "name": "Toby", "species": "Perro", "breed": "Criollo",
        "gender": "macho", "age": 4, "image": None,
        "description": "Descripcion inventada de prueba", "estado": estado,
    }


class PruebasFichaSinDatosInventados(unittest.TestCase):
    """Las 3 rutas de mascotas devuelven solo las columnas consultadas."""

    @classmethod
    def setUpClass(cls):
        cls.api = _importar_api()
        cls.cliente = cls.api.app.test_client()

    def setUp(self):
        # BD simulada "encendida" (modelo: tests/test_mascotas.py)
        self.conexion = mock.MagicMock()
        self.cursor = self.conexion.cursor.return_value
        parche = mock.patch.object(self.api._conexion_bd, "obtener_conexion",
                                   return_value=self.conexion)
        parche.start()
        self.addCleanup(parche.stop)

    def _assert_sin_datos_inventados(self, mascota):
        for campo in CAMPOS_INVENTADOS:
            with self.subTest(campo=campo):
                self.assertNotIn(campo, mascota)
        self.assertEqual(set(mascota), CAMPOS_DE_LA_BD)

    def test_lista_de_adopcion(self):
        self.cursor.fetchall.return_value = [_fila()]
        r = self.cliente.get("/api/mascotas/adopcion")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.get_json()), 1)
        self._assert_sin_datos_inventados(r.get_json()[0])

    def test_ficha_publica(self):
        self.cursor.fetchone.return_value = _fila()
        r = self.cliente.get(f"/api/mascotas/{ID_MASCOTA}")
        self.assertEqual(r.status_code, 200)
        self._assert_sin_datos_inventados(r.get_json())

    def test_ficha_privada_del_dueno(self):
        fila = _fila("activa")
        fila["id_usuario"] = ID_DUENO
        self.cursor.fetchone.return_value = fila
        # Token firmado con la clave de pruebas de este proceso; nunca se imprime
        token = self.api.generate_token(ID_DUENO, CORREO_DUENO)
        r = self.cliente.get(f"/api/usuarios/me/mascotas/{ID_MASCOTA}",
                             headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(r.status_code, 200)
        self._assert_sin_datos_inventados(r.get_json())


def _lista_del_seed(nombre):
    """Nodo ast de la lista NOMBRE = [...] de seed.py y las lineas del archivo."""
    with open(RUTA_SEED, encoding="utf-8") as f:
        fuente = f.read()
    for nodo in ast.parse(fuente).body:
        if isinstance(nodo, ast.Assign) and getattr(nodo.targets[0], "id", None) == nombre:
            return nodo.value, fuente.splitlines()
    raise AssertionError(f"seed.py no tiene la lista {nombre}")


class PruebasSemilla(unittest.TestCase):
    """seed.py: color real o vacio, y textos de salud marcados (regla 6)."""

    def test_el_color_no_guarda_el_tamano(self):
        lista, _ = _lista_del_seed("MASCOTAS_ADOPCION")
        mascotas = ast.literal_eval(lista)
        self.assertEqual(len(mascotas), 6)
        for nombre, _esp, _raza, _sexo, _edad, color, _foto, _obs in mascotas:
            with self.subTest(mascota=nombre):
                self.assertFalse(color and color.lower().startswith("tama"),
                                 f"color = {color!r}")

    def _assert_marcados(self, nombre_lista, posicion_texto):
        lista, lineas = _lista_del_seed(nombre_lista)
        con_salud = 0
        for nodo in lista.elts:
            fila = ast.literal_eval(nodo)
            if not PATRON_SALUD.search(fila[posicion_texto]):
                continue
            con_salud += 1
            # La linea anterior a la tupla debe ser la marca (lineno empieza en 1)
            anterior = lineas[nodo.lineno - 2].strip()
            with self.subTest(fila=fila[0] if nombre_lista == "MASCOTAS_ADOPCION" else fila[1]):
                self.assertTrue(anterior.startswith(MARCA), f"linea anterior: {anterior!r}")
        self.assertGreater(con_salud, 0)

    def test_mascotas_con_texto_de_salud_estan_marcadas(self):
        self._assert_marcados("MASCOTAS_ADOPCION", 7)

    def test_productos_con_texto_de_salud_estan_marcados(self):
        self._assert_marcados("PRODUCTOS", 2)


if __name__ == "__main__":
    unittest.main()
