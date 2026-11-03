"""
Pruebas de regresion de A-01 (esquema de la BD), NC-009 (estado en_adopcion
y modo estricto) y NC-010 (fechas de vacunas).

- PruebasEsquemaSinBD: leen sql/schema.sql como texto. No necesitan base de datos.
- PruebasEsquemaEnBD: solo corren con PETCONNECT_PRUEBA_BD=1. Crean una base
  temporal "petconnect_prueba", cargan schema.sql y seed.py, y al final la borran.
  Nunca tocan la base "petconnect".

Ejecutar desde petconnect.Backend, con el entorno virtual activo:
    python -m unittest discover -s tests -v
"""
import contextlib
import glob
import io
import os
import re
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

RUTA_ESQUEMA = os.path.join(RAIZ, "sql", "schema.sql")
BD_PRUEBA = "petconnect_prueba"


def _leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return f.read()


def _sentencias(sql):
    """Quita los comentarios '--' y separa las sentencias por punto y coma."""
    sin_comentarios = "\n".join(
        linea for linea in sql.splitlines() if not linea.lstrip().startswith("--")
    )
    return [s.strip() for s in sin_comentarios.split(";") if s.strip()]


def _tablas_del_esquema(sql):
    return set(re.findall(r"CREATE TABLE IF NOT EXISTS `(\w+)`", sql))


def _bloque_tabla(sql, tabla):
    encontrado = re.search(
        r"CREATE TABLE IF NOT EXISTS `%s` \((.*?)\n\) ENGINE" % tabla, sql, re.DOTALL
    )
    return encontrado.group(1) if encontrado else ""


class PruebasEsquemaSinBD(unittest.TestCase):
    """A-01: el repositorio trae un esquema completo y corregido."""

    @classmethod
    def setUpClass(cls):
        cls.sql = _leer(RUTA_ESQUEMA)

    def test_activa_el_modo_estricto_antes_de_crear_tablas(self):
        modo = self.sql.find("SET SESSION sql_mode")
        self.assertNotEqual(modo, -1)
        self.assertLess(modo, self.sql.find("CREATE TABLE IF NOT EXISTS `"))
        self.assertIn("STRICT_TRANS_TABLES", self.sql[modo:self.sql.find(";", modo)])

    def test_la_conexion_de_la_api_usa_modo_estricto(self):
        from config.db_config import DB_CONFIG
        self.assertIn("STRICT_TRANS_TABLES", DB_CONFIG.get("sql_mode", ""))

    def test_estado_de_mascotas_incluye_en_adopcion(self):
        """NC-009: antes el enum no tenia este valor y se guardaba vacio."""
        estado = re.search(r"`estado` enum\(([^)]*)\)", _bloque_tabla(self.sql, "mascotas"))
        self.assertIsNotNone(estado)
        self.assertIn("'en_adopcion'", estado.group(1))

    def test_vacunas_exigen_proxima_dosis_posterior(self):
        """NC-010: regla CHECK de fechas en aplicaciones_vacuna."""
        bloque = _bloque_tabla(self.sql, "aplicaciones_vacuna")
        self.assertRegex(bloque, r"CHECK \(`fecha_proxima` IS NULL OR `fecha_proxima` > `fecha_aplicacion`\)")

    def test_existen_todas_las_tablas_que_usa_el_codigo(self):
        archivos = [os.path.join(RAIZ, "api.py"), os.path.join(RAIZ, "seed.py")]
        archivos += glob.glob(os.path.join(RAIZ, "dao", "*.py"))
        usadas = set()
        for ruta in archivos:
            usadas |= set(re.findall(r"(?<!KEY )\b(?:FROM|INTO|UPDATE|JOIN)\s+`?(\w+)", _leer(ruta)))
        faltantes = usadas - _tablas_del_esquema(self.sql)
        self.assertEqual(faltantes, set(), f"Tablas usadas en el codigo y ausentes en schema.sql: {faltantes}")

    def test_tiene_las_32_tablas(self):
        self.assertEqual(len(_tablas_del_esquema(self.sql)), 32)

    def test_no_trae_datos_personales_ni_contadores(self):
        self.assertNotRegex(self.sql, r"INSERT[^;]*INTO `?(usuarios|mascotas|direcciones|metodos_pago)")
        self.assertNotRegex(self.sql, r"AUTO_INCREMENT=\d+")

    def test_seed_usa_edades_numericas(self):
        """En modo estricto, un texto como '2 anos' en edad_aprox (INT) produce error."""
        import seed
        for mascota in seed.MASCOTAS_ADOPCION:
            self.assertIsInstance(mascota[4], int, mascota[0])


@unittest.skipUnless(os.getenv("PETCONNECT_PRUEBA_BD") == "1",
                     "Prueba con MariaDB real: activar con PETCONNECT_PRUEBA_BD=1")
class PruebasEsquemaEnBD(unittest.TestCase):
    """Una BD vacia se crea solo con el repositorio y la adopcion devuelve 6 mascotas."""

    @classmethod
    def setUpClass(cls):
        import mysql.connector
        from config.db_config import DB_CONFIG
        from conexion.conexion_bd import ConexionBD

        cls.Error = mysql.connector.Error
        cls.db_config = DB_CONFIG
        cls.bd_original = DB_CONFIG["database"]
        if cls.bd_original == BD_PRUEBA:
            raise unittest.SkipTest("DB_NAME no puede ser la base temporal de pruebas")

        servidor = {k: v for k, v in DB_CONFIG.items() if k != "database"}
        try:
            cls.conn = mysql.connector.connect(**servidor)
        except mysql.connector.Error:
            raise unittest.SkipTest("No hay conexion con MariaDB")

        cursor = cls.conn.cursor()
        # El nombre es una constante del archivo (no viene del usuario): los
        # identificadores no se pueden pasar como parametro en SQL.
        cursor.execute(f"DROP DATABASE IF EXISTS `{BD_PRUEBA}`")
        cursor.execute(f"CREATE DATABASE `{BD_PRUEBA}` CHARACTER SET utf8mb4 COLLATE utf8mb4_spanish_ci")
        cls.addClassCleanup(cls._borrar_bd_prueba)
        cursor.execute(f"USE `{BD_PRUEBA}`")
        for sentencia in _sentencias(_leer(RUTA_ESQUEMA)):
            cursor.execute(sentencia)
        cursor.close()

        # seed.py y la API usan la conexion Singleton: se apunta a la base temporal
        DB_CONFIG["database"] = BD_PRUEBA
        ConexionBD().cerrar_conexion()
        cls._cargar_seed()

    @classmethod
    def _borrar_bd_prueba(cls):
        from conexion.conexion_bd import ConexionBD
        cls.db_config["database"] = cls.bd_original
        ConexionBD().cerrar_conexion()
        cursor = cls.conn.cursor()
        cursor.execute(f"DROP DATABASE IF EXISTS `{BD_PRUEBA}`")
        cursor.close()
        cls.conn.close()

    @staticmethod
    def _cargar_seed():
        import seed
        with contextlib.redirect_stdout(io.StringIO()):
            seed.seed()

    def _contar(self, sql, params=()):
        cursor = self.conn.cursor()
        cursor.execute(sql, params)
        total = cursor.fetchone()[0]
        cursor.close()
        return total

    def test_la_sesion_queda_en_modo_estricto(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT @@SESSION.sql_mode")
        self.assertIn("STRICT_TRANS_TABLES", cursor.fetchone()[0])
        cursor.close()

    def test_api_de_adopcion_devuelve_las_6_mascotas(self):
        from cryptography.fernet import Fernet
        os.environ.setdefault("FERNET_KEY", Fernet.generate_key().decode())
        os.environ.setdefault("JWT_SECRET", "clave-de-pruebas-petconnect-" + "x" * 32)
        import api

        respuesta = api.app.test_client().get("/api/mascotas/adopcion")
        self.assertEqual(respuesta.status_code, 200)
        mascotas = respuesta.get_json()
        self.assertEqual(len(mascotas), 6)
        self.assertTrue(all(m["estado"] == "en_adopcion" for m in mascotas))

    def test_seed_no_duplica_al_repetirse(self):
        self._cargar_seed()
        self.assertEqual(self._contar("SELECT COUNT(*) FROM mascotas WHERE estado = 'en_adopcion'"), 6)
        self.assertEqual(self._contar("SELECT COUNT(*) FROM productos"), 12)
        self.assertEqual(self._contar("SELECT COUNT(*) FROM usuarios WHERE estado = 'inactivo'"), 1)

    def test_rechaza_un_estado_de_mascota_que_no_existe(self):
        """NC-009: en modo no estricto este valor se guardaba vacio."""
        cursor = self.conn.cursor()
        with self.assertRaises(self.Error):
            cursor.execute(
                "INSERT INTO mascotas (id_usuario, nombre, especie, estado) "
                "SELECT id_usuario, %s, %s, %s FROM usuarios LIMIT 1",
                ("Prueba", "Perro", "estado_inventado"),
            )
        cursor.close()

    def test_rechaza_proxima_dosis_igual_o_anterior(self):
        """NC-010: regla chk_aplicacion_fechas."""
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO vacunas (nombre) VALUES (%s)", ("Vacuna de prueba",))
        id_vacuna = cursor.lastrowid
        cursor.execute("SELECT MIN(id_mascota) FROM mascotas")
        id_mascota = cursor.fetchone()[0]
        sql = ("INSERT INTO aplicaciones_vacuna (id_mascota, id_vacuna, fecha_aplicacion, fecha_proxima) "
               "VALUES (%s, %s, %s, %s)")

        for proxima in ("2026-10-01", "2026-10-05"):
            with self.subTest(fecha_proxima=proxima), self.assertRaises(self.Error):
                cursor.execute(sql, (id_mascota, id_vacuna, "2026-10-05", proxima))

        cursor.execute(sql, (id_mascota, id_vacuna, "2026-10-05", "2027-10-05"))
        cursor.execute(sql, (id_mascota, id_vacuna, "2026-10-05", None))
        self.assertEqual(self._contar("SELECT COUNT(*) FROM aplicaciones_vacuna"), 2)
        cursor.close()


if __name__ == "__main__":
    unittest.main()
