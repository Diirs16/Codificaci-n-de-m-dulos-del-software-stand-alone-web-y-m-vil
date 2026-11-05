"""
Pruebas de regresion de A-07 / NC-002 (item 2.9 de PRIORIDADES): control de acceso
por objeto en las mascotas.

- GET /api/mascotas/<id> (publica): solo devuelve mascotas en adopcion. Si no existe
  o tiene otro estado, responde el MISMO 404 "Mascota no encontrada" y ningun dato.
- GET /api/usuarios/me/mascotas/<id> (privada): exige token (401 sin el) y solo
  responde al dueno; una mascota ajena da el mismo 404 que una inexistente.

La BD se simula: el cursor falso devuelve la fila que la prueba quiere, sin aplicar
el WHERE. Por eso se prueba (1) que el SQL lleva el filtro y sus parametros y (2) que
la ruta vuelve a revisar el estado / el dueno en Python aunque la BD le devuelva una
fila que no deberia. La prueba con MariaDB real del filtro esta en
tests/test_esquema.py (PruebasEsquemaEnBD, solo con PETCONNECT_PRUEBA_BD=1).

No usan la base real, no envian correos ni leen .env (_importar_api).

Ejecutar desde petconnect.Backend, con el entorno virtual activo:
    python -m unittest discover -s tests -v
"""
import os
import re
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_errores import _importar_api  # noqa: E402

ID_MASCOTA = 3
ID_DUENO = 7
ID_OTRO_USUARIO = 8
CORREO_DUENO = "dueno.prueba@ejemplo.test"      # inventado (Ley 1581)
CORREO_OTRO = "otra.persona@ejemplo.test"       # inventado (Ley 1581)
OBSERVACION = "Observacion privada de prueba"   # no debe salir en un 404
CUERPO_404 = {"error": "Mascota no encontrada"}

# Estados del enum de mascotas.estado (sql/schema.sql) que NO son publicos
ESTADOS_PRIVADOS = ("activa", "perdida", "adoptada", "fallecida")


def _fila(estado="en_adopcion", id_usuario=None):
    """Fila como la devuelve el cursor (dictionary=True) con los alias de la consulta."""
    fila = {
        "id": ID_MASCOTA, "name": "Toby", "species": "Perro", "breed": "Criollo",
        "gender": "macho", "age": 4, "image": None, "description": OBSERVACION,
        "estado": estado,
    }
    if id_usuario is not None:
        fila["id_usuario"] = id_usuario
    return fila


class _BaseMascotas(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.api = _importar_api()
        cls.cliente = cls.api.app.test_client()

    def setUp(self):
        # BD simulada "encendida": el cursor falso devuelve self.cursor.fetchone
        self.conexion = mock.MagicMock()
        self.cursor = self.conexion.cursor.return_value
        self.cursor.fetchone.return_value = None
        parche = mock.patch.object(self.api._conexion_bd, "obtener_conexion",
                                   return_value=self.conexion)
        self.obtener_conexion = parche.start()
        self.addCleanup(parche.stop)

    def _sql_y_parametros(self):
        """Consulta y parametros con que la ruta llamo a cursor.execute."""
        self.cursor.execute.assert_called_once()
        sql, params = self.cursor.execute.call_args.args
        return " ".join(sql.split()), params

    def _assert_404_sin_datos(self, r):
        self.assertEqual(r.status_code, 404)
        self.assertEqual(r.get_json(), CUERPO_404)
        texto = r.get_data(as_text=True)
        self.assertNotIn("Toby", texto)
        self.assertNotIn(OBSERVACION, texto)


class PruebasMascotaPublica(_BaseMascotas):
    """GET /api/mascotas/<id>: solo mascotas en adopcion, sin pedir sesion."""

    def test_mascota_en_adopcion_responde_200_sin_token(self):
        self.cursor.fetchone.return_value = _fila("en_adopcion")
        r = self.cliente.get(f"/api/mascotas/{ID_MASCOTA}")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["name"], "Toby")

    def test_mascota_que_no_esta_en_adopcion_responde_404_sin_datos(self):
        # La BD simulada devuelve la fila aunque el SQL la filtraria: la ruta
        # tiene que revisarla otra vez (doble barrera)
        for estado in ESTADOS_PRIVADOS:
            with self.subTest(estado=estado):
                self.cursor.reset_mock()
                self.cursor.fetchone.return_value = _fila(estado, id_usuario=ID_DUENO)
                r = self.cliente.get(f"/api/mascotas/{ID_MASCOTA}")
                self._assert_404_sin_datos(r)

    def test_mascota_inexistente_responde_el_mismo_404(self):
        self.cursor.fetchone.return_value = None
        r = self.cliente.get("/api/mascotas/999999")
        self._assert_404_sin_datos(r)

    def test_la_consulta_filtra_por_estado_en_adopcion(self):
        self.cliente.get(f"/api/mascotas/{ID_MASCOTA}")
        sql, params = self._sql_y_parametros()
        self.assertRegex(sql, r"WHERE id_mascota = %s AND estado = 'en_adopcion'")
        self.assertEqual(params, (ID_MASCOTA,))


class PruebasMascotaPrivada(_BaseMascotas):
    """GET /api/usuarios/me/mascotas/<id>: token obligatorio y solo el dueno."""

    RUTA = f"/api/usuarios/me/mascotas/{ID_MASCOTA}"

    def _token(self, id_usuario, correo):
        # Token firmado con la clave de pruebas de este proceso; nunca se imprime
        return {"Authorization": f"Bearer {self.api.generate_token(id_usuario, correo)}"}

    def test_sin_token_responde_401_sin_consultar_la_bd(self):
        r = self.cliente.get(self.RUTA)
        self.assertEqual(r.status_code, 401)
        self.assertNotIn("Toby", r.get_data(as_text=True))
        self.obtener_conexion.assert_not_called()

    def test_token_invalido_responde_401(self):
        r = self.cliente.get(self.RUTA, headers={"Authorization": "Bearer token-inventado"})
        self.assertEqual(r.status_code, 401)
        self.obtener_conexion.assert_not_called()

    def test_la_consulta_filtra_por_mascota_y_dueno_del_token(self):
        self.cliente.get(self.RUTA, headers=self._token(ID_OTRO_USUARIO, CORREO_OTRO))
        sql, params = self._sql_y_parametros()
        self.assertRegex(sql, r"WHERE id_mascota = %s AND id_usuario = %s")
        self.assertEqual(params, (ID_MASCOTA, ID_OTRO_USUARIO))

    def test_mascota_ajena_responde_el_mismo_404(self):
        # Caso real: el SQL filtra por dueno y no encuentra nada
        self.cursor.fetchone.return_value = None
        r = self.cliente.get(self.RUTA, headers=self._token(ID_OTRO_USUARIO, CORREO_OTRO))
        self._assert_404_sin_datos(r)

    def test_mascota_ajena_responde_404_aunque_la_bd_la_devuelva(self):
        # Doble barrera: si alguien cambia el SQL y la fila llega, Python la frena
        self.cursor.fetchone.return_value = _fila("activa", id_usuario=ID_DUENO)
        r = self.cliente.get(self.RUTA, headers=self._token(ID_OTRO_USUARIO, CORREO_OTRO))
        self._assert_404_sin_datos(r)

    def test_el_dueno_ve_su_mascota_en_cualquier_estado(self):
        for estado in ESTADOS_PRIVADOS + ("en_adopcion",):
            with self.subTest(estado=estado):
                self.cursor.fetchone.return_value = _fila(estado, id_usuario=ID_DUENO)
                r = self.cliente.get(self.RUTA, headers=self._token(ID_DUENO, CORREO_DUENO))
                self.assertEqual(r.status_code, 200)
                datos = r.get_json()
                self.assertEqual(datos["name"], "Toby")
                self.assertEqual(datos["estado"], estado)
                self.assertNotIn("id_usuario", datos)   # no hace falta devolverlo

    def test_bd_caida_responde_503(self):
        self.obtener_conexion.return_value = None
        # El error se registra en el servidor (assertLogs evita llenar la consola)
        with self.assertLogs(self.api.app.logger, level="ERROR"):
            r = self.cliente.get(self.RUTA, headers=self._token(ID_DUENO, CORREO_DUENO))
        self.assertEqual(r.status_code, 503)
        self.assertNotIn("Toby", r.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
