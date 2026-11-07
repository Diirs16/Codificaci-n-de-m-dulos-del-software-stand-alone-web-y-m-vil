"""
Pruebas de regresion de A-01 (esquema de la BD), NC-009 (estado en_adopcion
y modo estricto) y NC-010 (fechas de vacunas).

- PruebasEsquemaSinBD y PruebasMigracionSinBD: leen los .sql como texto.
  No necesitan base de datos.
- PruebasEsquemaEnBD: solo corren con PETCONNECT_PRUEBA_BD=1. Crean una base
  temporal "petconnect_prueba", cargan schema.sql y seed.py, y al final la borran.
  Tambien prueban el filtro real de NC-002 (item 2.9): una mascota "activa"
  no sale por la ruta publica ni para otro usuario, solo para su dueno.
- PruebasMigracionEnBD: tambien con PETCONNECT_PRUEBA_BD=1. Crean la tabla vieja
  en "petconnect_prueba_migracion", reproducen el estado vacio y aplican la
  migracion de PRIORIDADES 1.2. Al final borran esa base.
- NC-005 (item 3.1): PruebasEsquemaSinBD y PruebasMigracionDatosSinBD revisan que
  acepta_datos no valga 1 por defecto y la regla chk_autorizacion_datos.
  PruebasMigracionDatosEnBD (PETCONNECT_PRUEBA_BD=1) aplica la migracion del
  05/11/2026 a una tabla vieja en "petconnect_prueba_autorizacion" y la borra al final.
- A-22 (item 3.4): PruebasMigracionEjemploSinBD revisa la migracion del 06/11/2026
  (tamano guardado en color y edad de Nala, solo en las 6 mascotas de ejemplo).
  PruebasMigracionEjemploEnBD (PETCONNECT_PRUEBA_BD=1) la aplica en
  "petconnect_prueba_ejemplo" y la borra al final.
- A-21 (item 3.6): PruebasEsquemaSinBD y PruebasMigracionSolicitudesSinBD revisan la
  tabla solicitudes y su migracion del 07/11/2026. PruebasEsquemaEnBD prueba
  SolicitudDAO y la regla chk_solicitud_tipo con la base real, y
  PruebasMigracionSolicitudesEnBD (PETCONNECT_PRUEBA_BD=1) aplica la migracion en
  "petconnect_prueba_solicitudes" y la borra al final.
  Ninguna toca la base "petconnect".

Ejecutar desde petconnect.Backend, con el entorno virtual activo:
    python -m unittest discover -s tests -v
"""
import contextlib
import datetime
import glob
import io
import os
import re
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

RUTA_ESQUEMA = os.path.join(RAIZ, "sql", "schema.sql")
RUTA_MIGRACION = os.path.join(RAIZ, "sql", "migraciones", "2026-11-03_estado_en_adopcion.sql")
RUTA_MIGRACION_DATOS = os.path.join(RAIZ, "sql", "migraciones", "2026-11-05_autorizacion_datos.sql")
RUTA_MIGRACION_EJEMPLO = os.path.join(RAIZ, "sql", "migraciones", "2026-11-06_mascotas_ejemplo.sql")
BD_PRUEBA = "petconnect_prueba"
BD_PRUEBA_MIGRACION = "petconnect_prueba_migracion"
BD_PRUEBA_AUTORIZACION = "petconnect_prueba_autorizacion"
BD_PRUEBA_EJEMPLO = "petconnect_prueba_ejemplo"
RUTA_MIGRACION_SOLICITUDES = os.path.join(RAIZ, "sql", "migraciones", "2026-11-07_solicitudes.sql")
BD_PRUEBA_SOLICITUDES = "petconnect_prueba_solicitudes"

# Item 3.6 (A-21): regla de la tabla solicitudes, igual en schema.sql y en la migracion
REGLA_SOLICITUDES = ("(`tipo` = 'adopcion' AND `id_mascota` IS NOT NULL OR `tipo` = 'contacto' "
                     "AND `id_mascota` IS NULL AND `telefono` IS NULL)")


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

    def test_usuarios_no_autorizan_datos_por_defecto(self):
        """NC-005: antes acepta_datos valia 1 por defecto (autorizacion que nadie dio)."""
        bloque = _bloque_tabla(self.sql, "usuarios")
        self.assertIn("`acepta_datos` tinyint(1) NOT NULL DEFAULT 0", bloque)
        self.assertNotRegex(bloque, r"`acepta_datos`[^,]*DEFAULT 1")
        self.assertIn("`fecha_autorizacion_datos` datetime DEFAULT NULL", bloque)
        self.assertIn("`version_politica_datos` varchar(20) DEFAULT NULL", bloque)

    def test_autorizacion_exige_fecha_y_version(self):
        """NC-005: regla chk_autorizacion_datos (prueba de la autorizacion)."""
        self.assertEqual(
            _regla_autorizacion(_bloque_tabla(self.sql, "usuarios")),
            "(`acepta_datos` = 0 OR (`fecha_autorizacion_datos` IS NOT NULL "
            "AND `version_politica_datos` IS NOT NULL))",
        )

    def test_tiene_las_33_tablas(self):
        # 32 hasta el 07/11/2026, + solicitudes (item 3.6)
        self.assertEqual(len(_tablas_del_esquema(self.sql)), 33)

    def test_solicitudes_guardan_la_prueba_y_no_repiten_datos_de_la_cuenta(self):
        """A-21 (item 3.6): usuario, version de la politica y fecha; nombre y correo no."""
        bloque = _bloque_tabla(self.sql, "solicitudes")
        for columna in ("`id_usuario` int(11) NOT NULL",
                        "`tipo` enum('adopcion','contacto') NOT NULL",
                        "`id_mascota` int(11) DEFAULT NULL",
                        "`telefono` varchar(20) DEFAULT NULL",
                        "`mensaje` varchar(1000) NOT NULL",
                        "`version_politica_datos` varchar(20) NOT NULL",
                        "`fecha_envio` datetime NOT NULL DEFAULT current_timestamp()"):
            with self.subTest(columna=columna):
                self.assertIn(columna, bloque)
        self.assertNotRegex(bloque, r"`(nombres?|apellidos|correo)`")
        self.assertEqual(_regla_solicitudes(bloque), REGLA_SOLICITUDES)
        # Si se borra la cuenta o la mascota, se borran sus solicitudes (politica v1.1, A.11)
        for clave in ("FOREIGN KEY (`id_usuario`) REFERENCES `usuarios` (`id_usuario`) ON DELETE CASCADE",
                      "FOREIGN KEY (`id_mascota`) REFERENCES `mascotas` (`id_mascota`) ON DELETE CASCADE"):
            with self.subTest(clave=clave):
                self.assertIn(clave, bloque)

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

        # Se llama la funcion de la ruta sin test_client(): una peticion completa
        # marca la app como "ya atendio su primera peticion" y Flask prohibe
        # despues registrar rutas, como hace test_seguridad.PruebasEndpointProtegido.
        with api.app.test_request_context("/api/mascotas/adopcion"):
            respuesta = api.get_mascotas_adopcion()
        self.assertEqual(respuesta.status_code, 200)
        mascotas = respuesta.get_json()
        self.assertEqual(len(mascotas), 6)
        self.assertTrue(all(m["estado"] == "en_adopcion" for m in mascotas))

    def test_mascota_privada_solo_la_ve_su_dueno(self):
        """NC-002 (item 2.9) con el SQL real: la ruta publica no la encuentra."""
        from cryptography.fernet import Fernet
        os.environ.setdefault("FERNET_KEY", Fernet.generate_key().decode())
        os.environ.setdefault("JWT_SECRET", "clave-de-pruebas-petconnect-" + "x" * 32)
        import api

        # Mascota "activa" (privada) del dueno ficticio de la semilla
        cursor = self.conn.cursor()
        cursor.execute("SELECT id_usuario FROM mascotas WHERE estado = 'en_adopcion' LIMIT 1")
        id_dueno = cursor.fetchone()[0]
        cursor.execute(
            "INSERT INTO mascotas (id_usuario, nombre, especie, observaciones, estado) "
            "VALUES (%s, %s, %s, %s, %s)",
            (id_dueno, "Privada", "Gato", "Observacion privada de prueba", "activa"),
        )
        id_privada = cursor.lastrowid
        self.conn.commit()
        cursor.close()

        def borrar():
            c = self.conn.cursor()
            c.execute("DELETE FROM mascotas WHERE id_mascota = %s", (id_privada,))
            self.conn.commit()
            c.close()
        self.addCleanup(borrar)

        def token(id_usuario):
            # Correo inventado; el token se firma en este proceso y nunca se imprime
            return {"Authorization": f"Bearer {api.generate_token(id_usuario, 'dueno@ejemplo.test')}"}

        # Igual que arriba: se llama la funcion sin test_client()
        with api.app.test_request_context(f"/api/mascotas/{id_privada}"):
            r_publica, codigo_publica = api.get_mascota(id_privada)
        with api.app.test_request_context(f"/api/usuarios/me/mascotas/{id_privada}",
                                          headers=token(id_dueno + 1000)):
            r_ajena, codigo_ajena = api.get_mi_mascota(id_privada)
        with api.app.test_request_context(f"/api/usuarios/me/mascotas/{id_privada}",
                                          headers=token(id_dueno)):
            r_dueno = api.get_mi_mascota(id_privada)

        self.assertEqual((codigo_publica, r_publica.get_json()), (404, {"error": "Mascota no encontrada"}))
        self.assertEqual((codigo_ajena, r_ajena.get_json()), (404, {"error": "Mascota no encontrada"}))
        self.assertEqual(r_dueno.status_code, 200)
        self.assertEqual(r_dueno.get_json()["name"], "Privada")

    def test_seed_no_guarda_el_tamano_en_color(self):
        """A-22 (item 3.4): antes las 6 mascotas quedaban con el tamano en color."""
        self.assertEqual(self._contar("SELECT COUNT(*) FROM mascotas WHERE color IS NOT NULL"), 0)

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

    def test_autorizacion_de_datos_solo_con_fecha_y_version(self):
        """NC-005 (item 3.1) con la base real: regla chk_autorizacion_datos y UsuarioDAO."""
        from dao.usuario_dao import UsuarioDAO
        from modelo.usuario import Usuario

        # Correos inventados (Ley 1581)
        correos = ["sin.fecha@ejemplo.test", "sin.version@ejemplo.test",
                   "por.defecto@ejemplo.test", "con.prueba@ejemplo.test", "consola@ejemplo.test"]

        def borrar():
            c = self.conn.cursor()
            c.execute("DELETE FROM usuarios WHERE correo IN (%s, %s, %s, %s, %s)", tuple(correos))
            self.conn.commit()
            c.close()
        self.addCleanup(borrar)

        cursor = self.conn.cursor()
        sql = ("INSERT INTO usuarios (nombres, correo, password_hash, acepta_datos, "
               "fecha_autorizacion_datos, version_politica_datos) VALUES (%s, %s, %s, %s, %s, %s)")
        for correo, fecha, version in ((correos[0], None, "1.0"),
                                       (correos[1], "2026-11-05 10:00:00", None)):
            with self.subTest(correo=correo), self.assertRaises(self.Error):
                cursor.execute(sql, ("Prueba", correo, "hash-falso", 1, fecha, version))

        cursor.execute("INSERT INTO usuarios (nombres, correo, password_hash) VALUES (%s, %s, %s)",
                       ("Prueba", correos[2], "hash-falso"))
        self.conn.commit()

        # La API crea el usuario con la prueba; la consola, con el valor por defecto
        fecha = datetime.datetime(2026, 11, 5, 10, 30, 0)
        dao = UsuarioDAO()
        self.assertTrue(dao.insertar(Usuario(
            nombres="Prueba", correo=correos[3], password_hash="hash-falso", verificado=True,
            acepta_datos=True, fecha_autorizacion_datos=fecha, version_politica_datos="1.0")))
        self.assertTrue(dao.insertar(Usuario(nombres="Prueba", correo=correos[4],
                                             password_hash="hash-falso")))

        cursor.execute(
            "SELECT correo, acepta_datos, fecha_autorizacion_datos, version_politica_datos "
            "FROM usuarios WHERE correo IN (%s, %s, %s) ORDER BY correo",
            (correos[2], correos[3], correos[4]),
        )
        filas = {f[0]: f[1:] for f in cursor.fetchall()}
        cursor.close()
        self.assertEqual(filas[correos[2]], (0, None, None))
        self.assertEqual(filas[correos[3]], (1, fecha, "1.0"))
        self.assertEqual(filas[correos[4]], (0, None, None))

    def test_autorizacion_al_iniciar_sesion_con_la_base_real(self):
        """Item 3.5 (A-20, R05): UsuarioDAO lee la prueba y registrar_autorizacion la escribe."""
        from dao.usuario_dao import UsuarioDAO
        from modelo.usuario import Usuario

        # Correos inventados (Ley 1581)
        correos = ["cuenta.en.cero@ejemplo.test", "version.vieja@ejemplo.test"]

        def borrar():
            c = self.conn.cursor()
            c.execute("DELETE FROM usuarios WHERE correo IN (%s, %s)", tuple(correos))
            self.conn.commit()
            c.close()
        self.addCleanup(borrar)

        dao = UsuarioDAO()
        fecha_vieja = datetime.datetime(2026, 11, 5, 10, 30, 0)
        self.assertTrue(dao.insertar(Usuario(nombres="Prueba", correo=correos[0],
                                             password_hash="hash-falso")))
        self.assertTrue(dao.insertar(Usuario(
            nombres="Prueba", correo=correos[1], password_hash="hash-falso", verificado=True,
            acepta_datos=True, fecha_autorizacion_datos=fecha_vieja, version_politica_datos="0.9")))

        # Los SELECT del DAO ya traen la prueba (antes no la leian)
        en_cero = dao.consultar_por_correo(correos[0])
        vieja = dao.consultar_por_correo(correos[1])
        self.assertEqual((en_cero.acepta_datos, en_cero.fecha_autorizacion_datos,
                          en_cero.version_politica_datos), (False, None, None))
        self.assertEqual((vieja.acepta_datos, vieja.fecha_autorizacion_datos,
                          vieja.version_politica_datos), (True, fecha_vieja, "0.9"))

        # La persona marca la casilla y pone el codigo: se guardan las tres juntas
        fecha = datetime.datetime(2026, 11, 6, 9, 0, 0)
        for usuario in (en_cero, vieja):
            with self.subTest(correo=usuario.correo):
                self.assertTrue(dao.registrar_autorizacion(usuario.id_usuario, fecha, "1.0"))
                despues = dao.consultar_por_correo(usuario.correo)
                self.assertEqual((despues.acepta_datos, despues.fecha_autorizacion_datos,
                                  despues.version_politica_datos), (True, fecha, "1.0"))

    def test_solicitudes_con_la_base_real(self):
        """Item 3.6 (A-21): SolicitudDAO, la regla chk_solicitud_tipo y el borrado en cascada."""
        from dao.solicitud_dao import SolicitudDAO
        from dao.usuario_dao import UsuarioDAO
        from modelo.usuario import Usuario

        correo = "envia.solicitud@ejemplo.test"     # inventado (Ley 1581)
        telefono = "3000000000"                     # inventado
        mensaje = "Mensaje de prueba para la solicitud"

        def borrar():
            c = self.conn.cursor()
            c.execute("DELETE FROM usuarios WHERE correo = %s", (correo,))
            self.conn.commit()
            c.close()
        self.addCleanup(borrar)

        usuarios = UsuarioDAO()
        fecha = datetime.datetime(2026, 11, 7, 10, 0, 0)
        self.assertTrue(usuarios.insertar(Usuario(
            nombres="Prueba", correo=correo, password_hash="hash-falso", verificado=True,
            acepta_datos=True, fecha_autorizacion_datos=fecha, version_politica_datos="1.1")))
        id_usuario = usuarios.consultar_por_correo(correo).id_usuario

        cursor = self.conn.cursor()
        cursor.execute("SELECT id_mascota, id_usuario FROM mascotas "
                       "WHERE estado = 'en_adopcion' ORDER BY id_mascota LIMIT 1")
        id_mascota, id_dueno = cursor.fetchone()

        dao = SolicitudDAO()
        self.assertEqual(dao.dueno_de_mascota_en_adopcion(id_mascota), id_dueno)
        self.assertIsNone(dao.dueno_de_mascota_en_adopcion(id_mascota + 100000))
        self.assertGreater(dao.insertar(id_usuario, "adopcion", id_mascota, telefono, mensaje,
                                        "1.1", fecha), 0)
        self.assertGreater(dao.insertar(id_usuario, "contacto", None, None, mensaje, "1.1", fecha), 0)

        # La regla y el modo estricto rechazan filas incoherentes
        malas = {
            "adopcion sin mascota": (id_usuario, "adopcion", None, None, mensaje, "1.1", fecha),
            "contacto con mascota": (id_usuario, "contacto", id_mascota, None, mensaje, "1.1", fecha),
            "contacto con telefono": (id_usuario, "contacto", None, telefono, mensaje, "1.1", fecha),
            "mensaje de 1001": (id_usuario, "contacto", None, None, "a" * 1001, "1.1", fecha),
            "tipo inventado": (id_usuario, "otro", None, None, mensaje, "1.1", fecha),
            "sin version": (id_usuario, "contacto", None, None, mensaje, None, fecha),
        }
        for caso, valores in malas.items():
            with self.subTest(caso=caso), self.assertRaises(self.Error):
                dao.insertar(*valores)

        self.conn.commit()      # lectura nueva: ver lo que guardo la conexion del DAO
        cursor.execute("SELECT tipo, id_mascota, telefono, mensaje, version_politica_datos, "
                       "fecha_envio FROM solicitudes WHERE id_usuario = %s ORDER BY id_solicitud",
                       (id_usuario,))
        self.assertEqual(cursor.fetchall(), [
            ("adopcion", id_mascota, telefono, mensaje, "1.1", fecha),
            ("contacto", None, None, mensaje, "1.1", fecha),
        ])

        # Si se borra la cuenta se borran sus solicitudes (politica v1.1, A.11)
        self.assertTrue(usuarios.eliminar(id_usuario))
        self.conn.commit()
        cursor.execute("SELECT COUNT(*) FROM solicitudes WHERE id_usuario = %s", (id_usuario,))
        self.assertEqual(cursor.fetchone()[0], 0)
        cursor.close()


def _lista_estados(sql):
    """Devuelve la ultima lista enum de `estado` que aparece en el texto."""
    return re.findall(r"`estado` enum\(([^)]*)\)", sql)[-1]


def _regla_fechas(sql):
    return re.search(r"`chk_aplicacion_fechas` CHECK (\(.*\))", sql).group(1)


def _regla_autorizacion(sql):
    encontrada = re.search(r"`chk_autorizacion_datos` CHECK (\(.*\))", sql)
    return encontrada.group(1) if encontrada else None


def _regla_solicitudes(sql):
    encontrada = re.search(r"`chk_solicitud_tipo` CHECK (\(.*\))", sql)
    return encontrada.group(1) if encontrada else None


def _columna(sql, nombre):
    """Tipo y opciones de una columna (ej. 'datetime DEFAULT NULL'), sin el AFTER.
    Exige un tipo para no confundirla con un SET o una regla CHECK."""
    encontrada = re.search(
        r"`%s` ((?:tinyint|datetime|varchar)[^,;\n]*?)(?: AFTER `\w+`)?\s*(?:,|;|\n|$)" % nombre, sql)
    return encontrada.group(1).strip() if encontrada else None


class PruebasMigracionSinBD(unittest.TestCase):
    """PRIORIDADES 1.2: la migracion de la BD existente sigue igual a schema.sql."""

    @classmethod
    def setUpClass(cls):
        cls.sql = _leer(RUTA_MIGRACION)
        cls.esquema = _leer(RUTA_ESQUEMA)
        cls.sentencias = _sentencias(cls.sql)

    def test_usa_la_misma_lista_de_estados_que_el_esquema(self):
        self.assertEqual(_lista_estados(self.sql), _lista_estados(_bloque_tabla(self.esquema, "mascotas")))

    def test_usa_la_misma_regla_de_fechas_que_el_esquema(self):
        self.assertEqual(_regla_fechas(self.sql), _regla_fechas(self.esquema))

    def test_nunca_apaga_el_modo_estricto(self):
        """Sin modo estricto, un estado desconocido se vaciaria y luego pasaria a en_adopcion."""
        modos = [s for s in self.sentencias if "sql_mode" in s]
        self.assertTrue(self.sentencias[0].startswith("SET SESSION sql_mode"))
        for modo in modos:
            self.assertIn("STRICT_TRANS_TABLES", modo)

    def test_corrige_los_vacios_antes_de_cerrar_la_lista(self):
        def posicion(patron):
            return next(i for i, s in enumerate(self.sentencias) if re.search(patron, s))

        a_texto = posicion(r"MODIFY `estado` varchar")
        correccion = posicion(r"UPDATE `mascotas` SET `estado` = 'en_adopcion' WHERE `estado` = ''")
        a_lista = posicion(r"MODIFY `estado` enum")
        self.assertLess(a_texto, correccion)
        self.assertLess(correccion, a_lista)


@unittest.skipUnless(os.getenv("PETCONNECT_PRUEBA_BD") == "1",
                     "Prueba con MariaDB real: activar con PETCONNECT_PRUEBA_BD=1")
class PruebasMigracionEnBD(unittest.TestCase):
    """PRIORIDADES 1.2: una BD vieja queda sin estados vacios y sin perder datos."""

    ESTADOS_VIEJOS = "'activa','perdida','adoptada','fallecida'"

    @classmethod
    def setUpClass(cls):
        import mysql.connector
        from config.db_config import DB_CONFIG

        cls.Error = mysql.connector.Error
        servidor = {k: v for k, v in DB_CONFIG.items() if k not in ("database", "sql_mode")}
        try:
            cls.conn = mysql.connector.connect(**servidor)
        except mysql.connector.Error:
            raise unittest.SkipTest("No hay conexion con MariaDB")
        cls.conn.autocommit = True

        cursor = cls.conn.cursor()
        # Nombre constante del archivo: los identificadores no van como parametro.
        cursor.execute(f"DROP DATABASE IF EXISTS `{BD_PRUEBA_MIGRACION}`")
        cursor.execute(f"CREATE DATABASE `{BD_PRUEBA_MIGRACION}` CHARACTER SET utf8mb4 COLLATE utf8mb4_spanish_ci")
        cls.addClassCleanup(cls._borrar_bd_prueba)
        cursor.execute(f"USE `{BD_PRUEBA_MIGRACION}`")
        cursor.close()

    @classmethod
    def _borrar_bd_prueba(cls):
        cursor = cls.conn.cursor()
        cursor.execute(f"DROP DATABASE IF EXISTS `{BD_PRUEBA_MIGRACION}`")
        cursor.close()
        cls.conn.close()

    def setUp(self):
        self.cursor = self.conn.cursor()
        self._crear_tablas_viejas(self.ESTADOS_VIEJOS)

    def tearDown(self):
        self.cursor.close()

    def _crear_tablas_viejas(self, estados):
        """Tablas como las de la BD creada antes del 03/11/2026, en modo no estricto."""
        self.cursor.execute("SET SESSION sql_mode = 'NO_ENGINE_SUBSTITUTION'")
        self.cursor.execute("DROP TABLE IF EXISTS mascotas, aplicaciones_vacuna")
        # La lista de estados es una constante de la prueba, no un dato del usuario.
        self.cursor.execute(
            "CREATE TABLE mascotas (id_mascota int AUTO_INCREMENT PRIMARY KEY, "
            f"nombre varchar(80) NOT NULL, estado enum({estados}) DEFAULT 'activa') ENGINE=InnoDB"
        )
        self.cursor.execute(
            "CREATE TABLE aplicaciones_vacuna (id_aplicacion int AUTO_INCREMENT PRIMARY KEY, "
            "fecha_aplicacion date NOT NULL, fecha_proxima date DEFAULT NULL) ENGINE=InnoDB"
        )

    def _insertar_mascota(self, nombre, estado):
        self.cursor.execute("INSERT INTO mascotas (nombre, estado) VALUES (%s, %s)", (nombre, estado))

    def _estados(self):
        self.cursor.execute("SELECT nombre, estado FROM mascotas")
        return dict(self.cursor.fetchall())

    def _migrar(self):
        for sentencia in _sentencias(_leer(RUTA_MIGRACION)):
            self.cursor.execute(sentencia)

    def test_corrige_los_estados_vacios_y_respeta_los_demas(self):
        self._insertar_mascota("Luna", "en_adopcion")
        self._insertar_mascota("Toby", "activa")
        self._insertar_mascota("Max", "adoptada")
        self.assertEqual(self._estados()["Luna"], "", "No se reprodujo NC-009 en la tabla vieja")

        self._migrar()

        self.assertEqual(self._estados(), {"Luna": "en_adopcion", "Toby": "activa", "Max": "adoptada"})

    def test_se_puede_ejecutar_dos_veces(self):
        self._insertar_mascota("Luna", "en_adopcion")
        self._migrar()
        self._migrar()
        self._insertar_mascota("Kira", "en_adopcion")
        self.assertEqual(self._estados(), {"Luna": "en_adopcion", "Kira": "en_adopcion"})

    def test_un_estado_desconocido_detiene_la_migracion_sin_perderse(self):
        """Con el modo estricto apagado, 'extraviada' se habria vaciado y publicado en adopcion."""
        self._crear_tablas_viejas(self.ESTADOS_VIEJOS + ",'extraviada'")
        self._insertar_mascota("Rocky", "extraviada")

        with self.assertRaises(self.Error):
            self._migrar()

        self.assertEqual(self._estados(), {"Rocky": "extraviada"})

    def test_agrega_la_regla_de_fechas(self):
        self._migrar()
        with self.assertRaises(self.Error):
            self.cursor.execute(
                "INSERT INTO aplicaciones_vacuna (fecha_aplicacion, fecha_proxima) VALUES (%s, %s)",
                ("2026-10-05", "2026-10-01"),
            )

    def test_fechas_invertidas_detienen_la_migracion(self):
        self.cursor.execute(
            "INSERT INTO aplicaciones_vacuna (fecha_aplicacion, fecha_proxima) VALUES (%s, %s)",
            ("2026-10-05", "2026-10-01"),
        )
        with self.assertRaises(self.Error):
            self._migrar()


class PruebasMigracionDatosSinBD(unittest.TestCase):
    """NC-005 (item 3.1): la migracion del 05/11/2026 sigue igual a schema.sql."""

    @classmethod
    def setUpClass(cls):
        cls.sql = _leer(RUTA_MIGRACION_DATOS)
        cls.usuarios = _bloque_tabla(_leer(RUTA_ESQUEMA), "usuarios")
        cls.sentencias = _sentencias(cls.sql)

    def test_usa_la_misma_regla_que_el_esquema(self):
        self.assertIsNotNone(_regla_autorizacion(self.sql))
        self.assertEqual(_regla_autorizacion(self.sql), _regla_autorizacion(self.usuarios))

    def test_usa_las_mismas_columnas_que_el_esquema(self):
        for columna in ("acepta_datos", "fecha_autorizacion_datos", "version_politica_datos"):
            with self.subTest(columna=columna):
                self.assertIsNotNone(_columna(self.sql, columna))
                self.assertEqual(_columna(self.sql, columna), _columna(self.usuarios, columna))

    def test_nunca_apaga_el_modo_estricto(self):
        self.assertTrue(self.sentencias[0].startswith("SET SESSION sql_mode"))
        for modo in (s for s in self.sentencias if "sql_mode" in s):
            self.assertIn("STRICT_TRANS_TABLES", modo)

    def test_quita_las_autorizaciones_sin_prueba_antes_de_la_regla(self):
        """Si la regla fuera antes, los usuarios viejos (1 sin fecha) la harian fallar."""
        def posicion(patron):
            return next(i for i, s in enumerate(self.sentencias) if re.search(patron, s))

        columnas = posicion(r"ADD COLUMN IF NOT EXISTS `fecha_autorizacion_datos`")
        correccion = posicion(r"UPDATE `usuarios` SET `acepta_datos` = 0")
        sin_nulos = posicion(r"MODIFY `acepta_datos` tinyint\(1\) NOT NULL DEFAULT 0")
        regla = posicion(r"ADD CONSTRAINT `chk_autorizacion_datos`")
        self.assertLess(columnas, correccion)
        self.assertLess(correccion, sin_nulos)
        self.assertLess(sin_nulos, regla)

    def test_no_inventa_fechas_de_autorizacion(self):
        """Ley 1581: no se puede fabricar la prueba de una autorizacion que nadie dio."""
        for sentencia in self.sentencias:
            self.assertNotRegex(sentencia, r"SET[^;]*`(fecha_autorizacion_datos|version_politica_datos)`\s*=")


@unittest.skipUnless(os.getenv("PETCONNECT_PRUEBA_BD") == "1",
                     "Prueba con MariaDB real: activar con PETCONNECT_PRUEBA_BD=1")
class PruebasMigracionDatosEnBD(unittest.TestCase):
    """NC-005 (item 3.1): los usuarios viejos quedan sin autorizacion y la regla se aplica."""

    @classmethod
    def setUpClass(cls):
        import mysql.connector
        from config.db_config import DB_CONFIG

        cls.Error = mysql.connector.Error
        servidor = {k: v for k, v in DB_CONFIG.items() if k not in ("database", "sql_mode")}
        try:
            cls.conn = mysql.connector.connect(**servidor)
        except mysql.connector.Error:
            raise unittest.SkipTest("No hay conexion con MariaDB")
        cls.conn.autocommit = True

        cursor = cls.conn.cursor()
        # Nombre constante del archivo: los identificadores no van como parametro.
        cursor.execute(f"DROP DATABASE IF EXISTS `{BD_PRUEBA_AUTORIZACION}`")
        cursor.execute(f"CREATE DATABASE `{BD_PRUEBA_AUTORIZACION}` "
                       "CHARACTER SET utf8mb4 COLLATE utf8mb4_spanish_ci")
        cls.addClassCleanup(cls._borrar_bd_prueba)
        cursor.execute(f"USE `{BD_PRUEBA_AUTORIZACION}`")
        cursor.close()

    @classmethod
    def _borrar_bd_prueba(cls):
        cursor = cls.conn.cursor()
        cursor.execute(f"DROP DATABASE IF EXISTS `{BD_PRUEBA_AUTORIZACION}`")
        cursor.close()
        cls.conn.close()

    def setUp(self):
        self.cursor = self.conn.cursor()
        # Tabla como la de antes del 05/11/2026 (acepta_datos con DEFAULT 1)
        self.cursor.execute("DROP TABLE IF EXISTS usuarios")
        self.cursor.execute(
            "CREATE TABLE usuarios (id_usuario int AUTO_INCREMENT PRIMARY KEY, "
            "correo varchar(120) NOT NULL, acepta_datos tinyint(1) DEFAULT 1) ENGINE=InnoDB"
        )

    def tearDown(self):
        self.cursor.close()

    def _insertar_viejo(self, correo, acepta_datos=None):
        if acepta_datos is None:
            self.cursor.execute("INSERT INTO usuarios (correo) VALUES (%s)", (correo,))
        else:
            self.cursor.execute("INSERT INTO usuarios (correo, acepta_datos) VALUES (%s, %s)",
                                (correo, acepta_datos))

    def _usuarios(self):
        self.cursor.execute("SELECT correo, acepta_datos, fecha_autorizacion_datos, "
                            "version_politica_datos FROM usuarios")
        return {f[0]: f[1:] for f in self.cursor.fetchall()}

    def _migrar(self):
        for sentencia in _sentencias(_leer(RUTA_MIGRACION_DATOS)):
            self.cursor.execute(sentencia)

    def test_los_usuarios_viejos_quedan_sin_autorizacion(self):
        self._insertar_viejo("por.defecto@ejemplo.test")          # DEFAULT 1 viejo
        self._insertar_viejo("con.uno@ejemplo.test", 1)
        self._insertar_viejo("con.cero@ejemplo.test", 0)
        self.cursor.execute("INSERT INTO usuarios (correo, acepta_datos) VALUES (%s, NULL)",
                            ("con.nulo@ejemplo.test",))

        self._migrar()

        self.assertEqual(self._usuarios(), {
            "por.defecto@ejemplo.test": (0, None, None),
            "con.uno@ejemplo.test": (0, None, None),
            "con.cero@ejemplo.test": (0, None, None),
            "con.nulo@ejemplo.test": (0, None, None),
        })

    def test_se_puede_ejecutar_dos_veces_sin_quitar_autorizaciones_reales(self):
        self._insertar_viejo("viejo@ejemplo.test", 1)
        self._migrar()
        fecha = datetime.datetime(2026, 11, 5, 10, 30, 0)
        self.cursor.execute(
            "INSERT INTO usuarios (correo, acepta_datos, fecha_autorizacion_datos, version_politica_datos) "
            "VALUES (%s, %s, %s, %s)", ("nuevo@ejemplo.test", 1, fecha, "1.0"))

        self._migrar()

        self.assertEqual(self._usuarios(), {
            "viejo@ejemplo.test": (0, None, None),
            "nuevo@ejemplo.test": (1, fecha, "1.0"),
        })

    def test_despues_de_migrar_un_si_sin_fecha_da_error(self):
        self._migrar()
        with self.assertRaises(self.Error):
            self._insertar_viejo("sin.fecha@ejemplo.test", 1)
        self._insertar_viejo("por.defecto@ejemplo.test")
        self.assertEqual(self._usuarios(), {"por.defecto@ejemplo.test": (0, None, None)})


class PruebasMigracionEjemploSinBD(unittest.TestCase):
    """A-22 (item 3.4): la migracion del 06/11/2026 solo corrige las 6 mascotas de ejemplo."""

    @classmethod
    def setUpClass(cls):
        cls.sentencias = [" ".join(s.split()) for s in _sentencias(_leer(RUTA_MIGRACION_EJEMPLO))]
        cls.cambios = [s for s in cls.sentencias if not s.startswith("SET SESSION")]

    def test_nunca_apaga_el_modo_estricto(self):
        self.assertTrue(self.sentencias[0].startswith("SET SESSION sql_mode"))
        for modo in (s for s in self.sentencias if "sql_mode" in s):
            self.assertIn("STRICT_TRANS_TABLES", modo)

    def test_solo_dos_cambios_color_en_null_y_edad_de_nala(self):
        self.assertEqual(len(self.cambios), 2)
        color, edad = self.cambios
        self.assertTrue(color.startswith("UPDATE `mascotas` SET `color` = NULL WHERE"), color)
        for tamano in ("`color` LIKE 'Tama_o %'", "'Grande'", "'Mediano'", "'Pequenio'",
                       "`color` LIKE 'Peque_o'"):
            self.assertIn(tamano, color)
        self.assertTrue(edad.startswith(
            "UPDATE `mascotas` SET `edad_aprox` = 0 WHERE `nombre` = 'Nala' "
            "AND `especie` = 'Gato' AND `edad_aprox` = 6"), edad)

    def test_no_borra_ni_cambia_la_estructura(self):
        for sentencia in self.sentencias:
            self.assertNotRegex(sentencia.upper(), r"\b(DELETE|DROP|ALTER|TRUNCATE|INSERT)\b")

    def test_solo_toca_las_mascotas_de_ejemplo_en_adopcion(self):
        """Las reconoce por nombre y especie de seed.py, no por id ni dueno (cambian entre bases)."""
        import ast
        with open(os.path.join(RAIZ, "seed.py"), encoding="utf-8") as f:
            arbol = ast.parse(f.read())
        lista = next(n.value for n in arbol.body if isinstance(n, ast.Assign)
                     and getattr(n.targets[0], "id", None) == "MASCOTAS_ADOPCION")
        de_la_semilla = {(m[0], m[1]) for m in ast.literal_eval(lista)}

        color, _edad = self.cambios
        self.assertEqual(set(re.findall(r"\('(\w+)', '(\w+)'\)", color)), de_la_semilla)
        for cambio in self.cambios:
            with self.subTest(cambio=cambio[:45]):
                self.assertIn("`estado` = 'en_adopcion'", cambio)
                self.assertNotRegex(cambio, r"id_usuario|id_mascota|correo")


@unittest.skipUnless(os.getenv("PETCONNECT_PRUEBA_BD") == "1",
                     "Prueba con MariaDB real: activar con PETCONNECT_PRUEBA_BD=1")
class PruebasMigracionEjemploEnBD(unittest.TestCase):
    """A-22 (item 3.4): la migracion corrige solo las 6 mascotas de ejemplo en adopcion."""

    @classmethod
    def setUpClass(cls):
        import mysql.connector
        from config.db_config import DB_CONFIG

        servidor = {k: v for k, v in DB_CONFIG.items() if k not in ("database", "sql_mode")}
        try:
            cls.conn = mysql.connector.connect(**servidor)
        except mysql.connector.Error:
            raise unittest.SkipTest("No hay conexion con MariaDB")
        cls.conn.autocommit = True

        cursor = cls.conn.cursor()
        # Nombre constante del archivo: los identificadores no van como parametro.
        cursor.execute(f"DROP DATABASE IF EXISTS `{BD_PRUEBA_EJEMPLO}`")
        cursor.execute(f"CREATE DATABASE `{BD_PRUEBA_EJEMPLO}` "
                       "CHARACTER SET utf8mb4 COLLATE utf8mb4_spanish_ci")
        cls.addClassCleanup(cls._borrar_bd_prueba)
        cursor.execute(f"USE `{BD_PRUEBA_EJEMPLO}`")
        cursor.close()

    @classmethod
    def _borrar_bd_prueba(cls):
        cursor = cls.conn.cursor()
        cursor.execute(f"DROP DATABASE IF EXISTS `{BD_PRUEBA_EJEMPLO}`")
        cursor.close()
        cls.conn.close()

    def setUp(self):
        self.cursor = self.conn.cursor()
        # Solo las columnas que usa la migracion
        self.cursor.execute("DROP TABLE IF EXISTS mascotas")
        self.cursor.execute(
            "CREATE TABLE mascotas (id_mascota int AUTO_INCREMENT PRIMARY KEY, "
            "id_usuario int NOT NULL, nombre varchar(80) NOT NULL, especie varchar(50) NOT NULL, "
            "edad_aprox int DEFAULT NULL, color varchar(50) DEFAULT NULL, "
            "estado varchar(20) DEFAULT 'activa') ENGINE=InnoDB"
        )

    def tearDown(self):
        self.cursor.close()

    def _insertar(self, nombre, especie, edad, color, estado="en_adopcion", id_usuario=5):
        self.cursor.execute(
            "INSERT INTO mascotas (id_usuario, nombre, especie, edad_aprox, color, estado) "
            "VALUES (%s, %s, %s, %s, %s, %s)", (id_usuario, nombre, especie, edad, color, estado))

    def _mascotas(self):
        """{(nombre, especie, estado): (edad_aprox, color)}"""
        self.cursor.execute("SELECT nombre, especie, estado, edad_aprox, color FROM mascotas")
        return {f[:3]: f[3:] for f in self.cursor.fetchall()}

    def _migrar(self):
        for sentencia in _sentencias(_leer(RUTA_MIGRACION_EJEMPLO)):
            self.cursor.execute(sentencia)

    def test_corrige_las_6_de_ejemplo_sea_quien_sea_el_dueno(self):
        # Como estaba la BD de desarrollo el 06/11/2026 (dueno: usuario 5, no el refugio)
        self._insertar("Luna", "Perro", 2, "Grande")
        self._insertar("Milo", "Gato", 1, "Mediano")
        self._insertar("Rocky", "Perro", 3, "Pequenio")
        self._insertar("Nala", "Gato", 6, "Pequenio")
        # Valores de seed.py antes del 3.4, con otro dueno
        self._insertar("Max", "Perro", 4, "Tamaño Grande", id_usuario=9)
        self._insertar("Cleo", "Gato", 2, "Pequeño", id_usuario=9)

        self._migrar()

        self.assertEqual(self._mascotas(), {
            ("Luna", "Perro", "en_adopcion"): (2, None),
            ("Milo", "Gato", "en_adopcion"): (1, None),
            ("Rocky", "Perro", "en_adopcion"): (3, None),
            ("Nala", "Gato", "en_adopcion"): (0, None),
            ("Max", "Perro", "en_adopcion"): (4, None),
            ("Cleo", "Gato", "en_adopcion"): (2, None),
        })

    def test_no_toca_otras_mascotas(self):
        self._insertar("Canela", "Perro", 5, "Grande")                  # no es de ejemplo
        self._insertar("Luna", "Gato", 2, "Grande")                     # otra especie
        self._insertar("Max", "Perro", 4, "Grande", estado="activa")    # no esta en adopcion
        self._insertar("Nala", "Perro", 6, None)                        # otra especie
        self._insertar("Nala", "Gato", 6, None, estado="adoptada")      # no esta en adopcion
        self._insertar("Milo", "Gato", 1, "Café")                       # color real

        self._migrar()

        self.assertEqual(self._mascotas(), {
            ("Canela", "Perro", "en_adopcion"): (5, "Grande"),
            ("Luna", "Gato", "en_adopcion"): (2, "Grande"),
            ("Max", "Perro", "activa"): (4, "Grande"),
            ("Nala", "Perro", "en_adopcion"): (6, None),
            ("Nala", "Gato", "adoptada"): (6, None),
            ("Milo", "Gato", "en_adopcion"): (1, "Café"),
        })

    def test_no_cambia_una_edad_de_nala_distinta_de_6(self):
        self._insertar("Nala", "Gato", 1, None)
        self._migrar()
        self.assertEqual(self._mascotas(), {("Nala", "Gato", "en_adopcion"): (1, None)})

    def test_se_puede_ejecutar_dos_veces(self):
        self._insertar("Nala", "Gato", 6, "Pequenio")
        self._migrar()
        self._migrar()
        self.assertEqual(self._mascotas(), {("Nala", "Gato", "en_adopcion"): (0, None)})


class PruebasMigracionSolicitudesSinBD(unittest.TestCase):
    """A-21 (item 3.6): la migracion del 07/11/2026 crea la misma tabla que schema.sql."""

    @classmethod
    def setUpClass(cls):
        cls.sql = _leer(RUTA_MIGRACION_SOLICITUDES)
        cls.sentencias = _sentencias(cls.sql)

    def test_crea_la_misma_tabla_que_el_esquema(self):
        bloque = _bloque_tabla(self.sql, "solicitudes")
        self.assertNotEqual(bloque, "")
        self.assertEqual(bloque, _bloque_tabla(_leer(RUTA_ESQUEMA), "solicitudes"))
        self.assertEqual(_regla_solicitudes(bloque), REGLA_SOLICITUDES)

    def test_nunca_apaga_el_modo_estricto(self):
        self.assertTrue(self.sentencias[0].startswith("SET SESSION sql_mode"))
        for modo in (s for s in self.sentencias if "sql_mode" in s):
            self.assertIn("STRICT_TRANS_TABLES", modo)

    def test_solo_crea_la_tabla(self):
        """No borra ni cambia nada: se puede correr en la BD del dueno sin riesgo."""
        self.assertEqual(len(self.sentencias), 2)
        self.assertTrue(self.sentencias[1].startswith("CREATE TABLE IF NOT EXISTS `solicitudes`"))
        for sentencia in self.sentencias:
            # "ON DELETE / ON UPDATE CASCADE" son parte de las claves foraneas, no ordenes
            sin_claves = re.sub(r"\bON (DELETE|UPDATE)\b", "", sentencia)
            self.assertNotRegex(sin_claves, r"\b(DROP|ALTER|DELETE|UPDATE|INSERT|TRUNCATE)\b")


@unittest.skipUnless(os.getenv("PETCONNECT_PRUEBA_BD") == "1",
                     "Prueba con MariaDB real: activar con PETCONNECT_PRUEBA_BD=1")
class PruebasMigracionSolicitudesEnBD(unittest.TestCase):
    """A-21 (item 3.6): la migracion crea la tabla en una base vieja y su regla funciona."""

    @classmethod
    def setUpClass(cls):
        import mysql.connector
        from config.db_config import DB_CONFIG

        cls.Error = mysql.connector.Error
        servidor = {k: v for k, v in DB_CONFIG.items() if k not in ("database", "sql_mode")}
        try:
            cls.conn = mysql.connector.connect(**servidor)
        except mysql.connector.Error:
            raise unittest.SkipTest("No hay conexion con MariaDB")
        cls.conn.autocommit = True

        cursor = cls.conn.cursor()
        # Nombre constante del archivo: los identificadores no van como parametro.
        cursor.execute(f"DROP DATABASE IF EXISTS `{BD_PRUEBA_SOLICITUDES}`")
        cursor.execute(f"CREATE DATABASE `{BD_PRUEBA_SOLICITUDES}` "
                       "CHARACTER SET utf8mb4 COLLATE utf8mb4_spanish_ci")
        cls.addClassCleanup(cls._borrar_bd_prueba)
        cursor.execute(f"USE `{BD_PRUEBA_SOLICITUDES}`")
        cursor.close()

    @classmethod
    def _borrar_bd_prueba(cls):
        cursor = cls.conn.cursor()
        cursor.execute(f"DROP DATABASE IF EXISTS `{BD_PRUEBA_SOLICITUDES}`")
        cursor.close()
        cls.conn.close()

    def setUp(self):
        self.cursor = self.conn.cursor()
        # Base "vieja": solo las tablas a las que apuntan las claves foraneas
        for tabla in ("solicitudes", "mascotas", "usuarios"):
            self.cursor.execute(f"DROP TABLE IF EXISTS {tabla}")
        self.cursor.execute("CREATE TABLE usuarios (id_usuario int(11) AUTO_INCREMENT PRIMARY KEY) "
                            "ENGINE=InnoDB")
        self.cursor.execute("CREATE TABLE mascotas (id_mascota int(11) AUTO_INCREMENT PRIMARY KEY) "
                            "ENGINE=InnoDB")
        self.cursor.execute("INSERT INTO usuarios VALUES (1)")
        self.cursor.execute("INSERT INTO mascotas VALUES (1)")

    def tearDown(self):
        self.cursor.close()

    def _migrar(self):
        for sentencia in _sentencias(_leer(RUTA_MIGRACION_SOLICITUDES)):
            self.cursor.execute(sentencia)

    def _insertar(self, tipo, id_mascota, telefono):
        self.cursor.execute(
            "INSERT INTO solicitudes (id_usuario, tipo, id_mascota, telefono, mensaje, "
            "version_politica_datos) VALUES (%s, %s, %s, %s, %s, %s)",
            (1, tipo, id_mascota, telefono, "Mensaje de prueba", "1.1"))

    def test_se_puede_ejecutar_dos_veces_sin_perder_filas(self):
        self._migrar()
        self._insertar("adopcion", 1, None)
        self._migrar()
        self.cursor.execute("SELECT COUNT(*) FROM solicitudes")
        self.assertEqual(self.cursor.fetchone()[0], 1)

    def test_la_regla_y_las_claves_funcionan(self):
        self._migrar()
        self._insertar("adopcion", 1, "3000000000")
        self._insertar("contacto", None, None)
        incoherentes = (("adopcion", None, None), ("contacto", 1, None),
                        ("contacto", None, "3000000000"), ("adopcion", 99, None))
        for tipo, id_mascota, telefono in incoherentes:
            with self.subTest(tipo=tipo, id_mascota=id_mascota, telefono=telefono):
                with self.assertRaises(self.Error):
                    self._insertar(tipo, id_mascota, telefono)
        # Borrar la cuenta borra sus solicitudes
        self.cursor.execute("DELETE FROM usuarios WHERE id_usuario = 1")
        self.cursor.execute("SELECT COUNT(*) FROM solicitudes")
        self.assertEqual(self.cursor.fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()
