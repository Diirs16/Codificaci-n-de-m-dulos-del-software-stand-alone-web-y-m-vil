"""
Pruebas de regresion del item 4.6 de PRIORIDADES (A-12, NC-003): los codigos OTP
fuera de la memoria del proceso.

Antes (otp/servicio.py hasta el 07/11/2026) los codigos vivian en un diccionario de
la API: sin candado entre hilos, los vencidos nunca se limpiaban y con varios
procesos (Gunicorn) la verificacion podia llegar a otro proceso que no tenia el
codigo. Ahora AlmacenOTP guarda en la tabla otp_pendientes (OtpDAO).

- PruebasAlmacenEnMemoria: AlmacenOTP() tal como lo crean las pruebas viejas.
  20 intentos a la vez solo comparan 5 veces (antes comparaban los 20), crear un
  codigo borra los vencidos de otros correos (antes nunca se borraban) y el codigo
  queda cifrado. Fallan con el codigo anterior.
- PruebasContratoMemoria: las reglas (10 min, 5 fallos, reenvio del MISMO codigo
  con 60 s y maximo 3) con un repositorio compartido: dos procesos ven el mismo
  codigo. Las mismas pruebas corren con MariaDB en PruebasContratoEnBD.
- PruebasOtpDAOSinBD: SQL parametrizado y errores de la BD que suben (503/500).
- PruebasApiConOtp: la API guarda los OTP con OtpDAO, sin BD responde 503, otro
  proceso verifica el registro, no quedan datos del registro despues de verificar
  (Ley 1581), correos de mas de 120 caracteres y el aviso al arrancar sin la tabla.
- PruebasContratoEnBD y PruebasMigracionOtpEnBD: solo con PETCONNECT_PRUEBA_BD=1, en
  las bases temporales "petconnect_prueba_otp" y "petconnect_prueba_otp_migracion"
  (se borran al final). Nunca tocan la base "petconnect".

Sin PETCONNECT_PRUEBA_BD no usan MariaDB, no envian correos ni leen .env. Los
correos y nombres son inventados (Ley 1581).

Ejecutar desde petconnect.Backend, con el entorno virtual activo:
    python -m unittest discover -s tests -p "test_otp_bd.py" -v
"""
import ast
import contextlib
import io
import os
import re
import sys
import threading
import time
import unittest
from types import SimpleNamespace
from unittest import mock

from mysql.connector import errors as errores_bd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_errores import _importar_api  # noqa: E402  (deja una FERNET_KEY de prueba)
from otp import servicio  # noqa: E402
from otp.servicio import AlmacenOTP, RepositorioMemoria  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Datos inventados (Ley 1581)
CORREO = "otp.prueba@ejemplo.test"
NOMBRE = "Laura Gomez"
CLAVE = "Firulais2026!"
INICIO = 1_000_000.0          # hora simulada (segundos) al empezar cada prueba
BD_PRUEBA_OTP = "petconnect_prueba_otp"
BD_PRUEBA_OTP_MIGRACION = "petconnect_prueba_otp_migracion"


def _codigo_incorrecto(codigo):
    return "000000" if codigo != "000000" else "111111"


class _ConReloj(unittest.TestCase):
    """Reloj simulado de otp/servicio.py: self._avanzar(segundos) adelanta la hora."""

    def setUp(self):
        self.ahora = INICIO
        parche = mock.patch.object(servicio, "time", SimpleNamespace(time=lambda: self.ahora))
        parche.start()
        self.addCleanup(parche.stop)

    def _avanzar(self, segundos):
        self.ahora += segundos


def _veinte_a_la_vez(almacen, correo, codigo):
    """
    20 hilos mandan un codigo malo al mismo tiempo. La comparacion se hace lenta
    (0,05 s) para que todos alcancen a entrar antes de que alguno sume su fallo:
    asi se ve si el limite de 5 se cuenta antes o despues de comparar.
    """
    comparar = servicio._mismo_codigo
    comparaciones = []
    candado = threading.Lock()

    def comparar_lento(guardado, recibido):
        with candado:
            comparaciones.append(recibido)
        time.sleep(0.05)
        return comparar(guardado, recibido)

    salida = threading.Barrier(20)
    motivos = []

    def intento():
        salida.wait()
        _, motivo = almacen.verificar(correo, _codigo_incorrecto(codigo))
        with candado:
            motivos.append(motivo)

    with mock.patch.object(servicio, "_mismo_codigo", comparar_lento):
        hilos = [threading.Thread(target=intento) for _ in range(20)]
        for hilo in hilos:
            hilo.start()
        for hilo in hilos:
            hilo.join(10)
    return comparaciones, motivos


# ---------------------------------------------------------------------------
# 1. AlmacenOTP() como lo usan las pruebas viejas (fallan con el codigo anterior)
# ---------------------------------------------------------------------------

class PruebasAlmacenEnMemoria(_ConReloj):

    def setUp(self):
        super().setUp()
        self.almacen = AlmacenOTP()

    def test_20_intentos_a_la_vez_solo_comparan_5_veces(self):
        codigo = self.almacen.crear(CORREO, {"name": NOMBRE, "password_hash": "hash"})
        comparaciones, motivos = _veinte_a_la_vez(self.almacen, CORREO, codigo)
        self.assertEqual(len(comparaciones), servicio.MAX_INTENTOS)
        self.assertEqual(motivos.count("incorrecto"), servicio.MAX_INTENTOS)
        self.assertEqual(len(motivos), 20)
        # Los demas encuentran el codigo bloqueado (o ya borrado por el bloqueo)
        self.assertEqual(set(motivos) - {"incorrecto"}, {"bloqueado", "no_pendiente"} & set(motivos))
        r = self.almacen.verificar(CORREO, codigo)            # ni el correcto entra ya
        self.assertEqual(r, (None, "no_pendiente"))

    def test_quien_gana_un_intento_compara_aunque_otro_borre_la_fila(self):
        """
        Visto el 08/11/2026 con MariaDB (4 != 5): quien ganaba un intento leia la fila
        DESPUES, y un 6.o intento ("bloqueado") ya la habia borrado: respondia
        "no_pendiente" sin comparar, aunque trajera el codigo correcto. Aqui los 5 que
        ganan se demoran 0,2 s para que el borrado siempre llegue antes.
        """
        class ReservaLenta(RepositorioMemoria):
            def reservar_intento(self, *argumentos):
                gano = super().reservar_intento(*argumentos)
                if gano:
                    time.sleep(0.2)          # como una BD ocupada justo despues
                return gano

        almacen = AlmacenOTP("registro", ReservaLenta())
        codigo = almacen.crear(CORREO, {"name": NOMBRE, "password_hash": "hash"})
        comparaciones, motivos = _veinte_a_la_vez(almacen, CORREO, codigo)
        self.assertEqual(len(comparaciones), servicio.MAX_INTENTOS)
        self.assertEqual(motivos.count("incorrecto"), servicio.MAX_INTENTOS)

    def test_crear_un_codigo_borra_los_vencidos_de_otros_correos(self):
        correos = [f"spam{i}@ejemplo.test" for i in range(100)]
        for correo in correos:
            self.almacen.crear(correo, {"name": NOMBRE, "password_hash": "hash"})
        self._avanzar(servicio.EXPIRACION_SEGUNDOS + 1)
        self.almacen.crear(CORREO, {"name": NOMBRE, "password_hash": "hash"})
        quedan = [c for c in correos if self.almacen.tiene_pendiente(c)]
        self.assertEqual(quedan, [], "los 100 vencidos (nombre y hash incluidos) se borran")
        self.assertTrue(self.almacen.tiene_pendiente(CORREO))

    def test_los_vigentes_de_otros_correos_no_se_borran(self):
        self.almacen.crear("otro@ejemplo.test", {"name": NOMBRE, "password_hash": "hash"})
        self._avanzar(servicio.EXPIRACION_SEGUNDOS - 1)
        self.almacen.crear(CORREO, {"name": NOMBRE, "password_hash": "hash"})
        self.assertTrue(self.almacen.tiene_pendiente("otro@ejemplo.test"))

    def test_limpiar_vencidos_al_arrancar(self):
        self.almacen.crear(CORREO, {"name": NOMBRE, "password_hash": "hash"})
        self._avanzar(servicio.EXPIRACION_SEGUNDOS + 1)
        self.assertEqual(self.almacen.limpiar_vencidos(), 1)
        self.assertFalse(self.almacen.tiene_pendiente(CORREO))

    def test_el_codigo_se_guarda_cifrado(self):
        codigo = self.almacen.crear(CORREO, {"name": NOMBRE, "password_hash": "hash"})
        fila = self.almacen._repositorio.obtener(CORREO, "registro")
        self.assertNotIn(codigo, str(fila))
        from security.crypto import decrypt
        self.assertEqual(decrypt(fila["codigo_cifrado"]), codigo)


# ---------------------------------------------------------------------------
# 2. Reglas sobre un repositorio compartido (memoria aqui, MariaDB mas abajo)
# ---------------------------------------------------------------------------

class _ContratoAlmacen:
    """
    Las mismas reglas de siempre, con el repositorio que da _nuevo_repositorio().
    No es un TestCase: lo heredan PruebasContratoMemoria y PruebasContratoEnBD.
    """

    def _nuevo_repositorio(self):
        raise NotImplementedError

    def _contar_filas(self):
        raise NotImplementedError

    def _datos(self, proposito):
        if proposito == "login":
            return {"id_usuario": self.ID_USUARIO}
        return {"name": NOMBRE, "password_hash": "hash-bcrypt-falso",
                "fecha_autorizacion_datos": None, "version_politica_datos": "1.1"}

    ID_USUARIO = 1

    def setUp(self):
        super().setUp()
        self.repositorio = self._nuevo_repositorio()
        self.registro = AlmacenOTP("registro", self.repositorio)
        self.login = AlmacenOTP("login", self.repositorio)
        for almacen in (self.registro, self.login):
            almacen.descartar(CORREO)
            self.addCleanup(almacen.descartar, CORREO)

    def _crear(self, almacen=None):
        almacen = almacen or self.registro
        return almacen.crear(CORREO, self._datos(almacen._proposito))

    def test_otro_proceso_verifica_el_codigo(self):
        codigo = self._crear()
        otro_proceso = AlmacenOTP("registro", self._nuevo_repositorio())
        pendiente, motivo = otro_proceso.verificar(CORREO, codigo)
        self.assertIsNone(motivo)
        self.assertEqual(pendiente["name"], NOMBRE)
        self.assertEqual(pendiente["code"], codigo)

    def test_registro_y_login_no_se_mezclan(self):
        codigo_registro = self._crear(self.registro)
        codigo_login = self._crear(self.login)
        fallos = 0
        if codigo_login != codigo_registro:          # el del registro no sirve para el login
            self.assertEqual(self.login.verificar(CORREO, codigo_registro)[1], "incorrecto")
            fallos = 1
        pendiente, motivo = self.login.verificar(CORREO, codigo_login)
        self.assertIsNone(motivo)
        # Solo los datos con valor (sin "name" ni "password_hash" vacios) y los contadores
        self.assertEqual(pendiente, {"id_usuario": self.ID_USUARIO, "code": codigo_login,
                                     "expires": INICIO + servicio.EXPIRACION_SEGUNDOS,
                                     "intentos": fallos, "ultimo_envio": INICIO, "reenvios": 0})
        self.assertTrue(self.registro.tiene_pendiente(CORREO))

    def test_cuatro_fallos_y_luego_el_correcto_entra_sin_gastar_intento(self):
        codigo = self._crear()
        for _ in range(servicio.MAX_INTENTOS - 1):
            self.assertEqual(self.registro.verificar(CORREO, _codigo_incorrecto(codigo)),
                             (None, "incorrecto"))
        pendiente, motivo = self.registro.verificar(CORREO, codigo)
        self.assertIsNone(motivo)
        self.assertEqual(pendiente["intentos"], servicio.MAX_INTENTOS - 1)
        # Si la BD falla despues (503), el mismo codigo sigue sirviendo
        self.assertIsNone(self.registro.verificar(CORREO, codigo)[1])

    def test_cinco_fallos_bloquean_y_borran_los_datos(self):
        codigo = self._crear()
        for _ in range(servicio.MAX_INTENTOS):
            self.registro.verificar(CORREO, _codigo_incorrecto(codigo))
        self.assertEqual(self.registro.verificar(CORREO, codigo), (None, "bloqueado"))
        self.assertFalse(self.registro.tiene_pendiente(CORREO))
        self.assertEqual(self.registro.verificar(CORREO, codigo), (None, "no_pendiente"))

    def test_pedir_otro_codigo_reinicia_el_contador(self):
        codigo = self._crear()
        for _ in range(servicio.MAX_INTENTOS):
            self.registro.verificar(CORREO, _codigo_incorrecto(codigo))
        nuevo = self._crear()
        self.assertIsNone(self.registro.verificar(CORREO, nuevo)[1])

    def test_vencido_dice_expirado_y_se_borra(self):
        codigo = self._crear()
        self._avanzar(servicio.EXPIRACION_SEGUNDOS + 1)
        self.assertEqual(self.registro.verificar(CORREO, codigo), (None, "expirado"))
        self.assertFalse(self.registro.tiene_pendiente(CORREO))
        self.assertEqual(self._contar_filas(), 0)

    def test_vigente_hasta_el_ultimo_segundo(self):
        self._crear()
        self._avanzar(servicio.EXPIRACION_SEGUNDOS - 1)
        self.assertIsNotNone(self.registro.vigente(CORREO))
        self._avanzar(2)
        self.assertIsNone(self.registro.vigente(CORREO))
        self.assertFalse(self.registro.tiene_pendiente(CORREO))

    def test_reenvio_del_mismo_codigo_con_espera_y_maximo(self):
        codigo = self._crear()
        self.assertIsNone(self.registro.para_reenviar(CORREO))          # antes de 60 s
        enviados = []
        for _ in range(servicio.MAX_REENVIOS + 2):
            self._avanzar(servicio.ESPERA_REENVIO_SEGUNDOS)
            pendiente = self.registro.para_reenviar(CORREO)
            if pendiente:
                enviados.append(pendiente["code"])
        self.assertEqual(enviados, [codigo] * servicio.MAX_REENVIOS)
        # Reenviar no alarga el vencimiento ni da intentos nuevos
        self.assertEqual(self.registro.vigente(CORREO)["expires"],
                         INICIO + servicio.EXPIRACION_SEGUNDOS)

    def test_no_reenvia_un_codigo_bloqueado(self):
        codigo = self._crear()
        for _ in range(servicio.MAX_INTENTOS):
            self.registro.verificar(CORREO, _codigo_incorrecto(codigo))
        self._avanzar(servicio.ESPERA_REENVIO_SEGUNDOS)
        self.assertIsNone(self.registro.para_reenviar(CORREO))

    def test_codigo_ilegible_se_borra_y_no_se_reenvia(self):
        self._crear()
        fila = self.repositorio.obtener(CORREO, "registro")
        fila["codigo_cifrado"] = "no-es-un-texto-de-fernet"    # cambio la FERNET_KEY
        self.repositorio.guardar(fila)
        self._avanzar(servicio.ESPERA_REENVIO_SEGUNDOS)
        self.assertIsNone(self.registro.para_reenviar(CORREO))
        self.assertFalse(self.registro.tiene_pendiente(CORREO))
        self._crear()
        fila = self.repositorio.obtener(CORREO, "registro")
        fila["codigo_cifrado"] = "no-es-un-texto-de-fernet"
        self.repositorio.guardar(fila)
        self.assertEqual(self.registro.verificar(CORREO, "123456"), (None, "expirado"))
        self.assertFalse(self.registro.tiene_pendiente(CORREO))

    def test_datos_desconocidos_no_se_guardan(self):
        with self.assertRaises(ValueError):
            self.registro.crear(CORREO, {"telefono": "3000000000"})
        self.assertFalse(self.registro.tiene_pendiente(CORREO))

    def test_20_intentos_a_la_vez_solo_comparan_5_veces(self):
        codigo = self._crear()
        comparaciones, motivos = _veinte_a_la_vez(self.registro, CORREO, codigo)
        self.assertEqual(len(comparaciones), servicio.MAX_INTENTOS)
        self.assertEqual(motivos.count("incorrecto"), servicio.MAX_INTENTOS)


class PruebasContratoMemoria(_ContratoAlmacen, _ConReloj):
    """Un RepositorioMemoria compartido hace de tabla (dos 'procesos' lo ven)."""

    def setUp(self):
        self._compartido = RepositorioMemoria()
        super().setUp()

    def _nuevo_repositorio(self):
        return self._compartido

    def _contar_filas(self):
        return len(self._compartido._filas)

    def test_proposito_desconocido(self):
        with self.assertRaises(ValueError):
            AlmacenOTP("recuperar")


# ---------------------------------------------------------------------------
# 3. OtpDAO sin BD: SQL parametrizado y errores que suben
# ---------------------------------------------------------------------------

class PruebasOtpDAOSinBD(unittest.TestCase):

    LLAMADAS = {
        "obtener": (CORREO, "registro"),
        "guardar": ({"correo": CORREO, "proposito": "registro", "codigo_cifrado": "x",
                     "intentos": 0, "reenvios": 0, "vence": 1.0, "ultimo_envio": 0.0,
                     "nombre": NOMBRE, "password_hash": "h", "id_usuario": None,
                     "fecha_autorizacion_datos": None, "version_politica_datos": "1.1"},),
        "borrar": (CORREO, "registro"),
        "borrar_vencidos": (1.0,),
        "reservar_intento": (CORREO, "registro", 1.0, 5),
        "devolver_intento": (CORREO, "registro"),
        "anotar_reenvio": (CORREO, "registro", 100.0, 60, 5, 3),
    }

    def setUp(self):
        from dao.otp_dao import OtpDAO
        self.dao = OtpDAO()
        self.conexion = mock.MagicMock()
        self.cursor = self.conexion.cursor.return_value
        self.cursor.rowcount = 1
        self.cursor.fetchone.return_value = None
        self.dao._conexion_bd = mock.Mock(obtener_conexion=mock.Mock(return_value=self.conexion))

    def test_se_prueban_todos_los_metodos(self):
        from dao.otp_dao import OtpDAO
        publicos = {n for n in vars(OtpDAO) if not n.startswith("_") and callable(getattr(OtpDAO, n))}
        self.assertEqual(publicos, set(self.LLAMADAS))

    def test_todo_el_sql_va_parametrizado(self):
        for nombre, argumentos in self.LLAMADAS.items():
            with self.subTest(metodo=nombre):
                self.cursor.execute.reset_mock()
                getattr(self.dao, nombre)(*argumentos)
                sql, parametros = self.cursor.execute.call_args.args
                self.assertIsInstance(parametros, tuple)
                self.assertEqual(sql.count("%s"), len(parametros))
                self.assertNotIn(CORREO, sql)                    # el dato nunca va en el texto
                self.assertIn("otp_pendientes", sql)

    def test_un_error_de_la_bd_deshace_y_sube(self):
        self.cursor.execute.side_effect = errores_bd.DatabaseError("falla simulada")
        for nombre, argumentos in self.LLAMADAS.items():
            with self.subTest(metodo=nombre):
                self.conexion.rollback.reset_mock()
                with self.assertRaises(errores_bd.DatabaseError):
                    getattr(self.dao, nombre)(*argumentos)
                if nombre != "obtener":
                    self.conexion.rollback.assert_called_once()

    def test_sin_bd_lanza_interface_error(self):
        self.dao._conexion_bd = mock.Mock(obtener_conexion=mock.Mock(return_value=None))
        with self.assertRaises(errores_bd.InterfaceError):
            self.dao.obtener(CORREO, "registro")


# ---------------------------------------------------------------------------
# 4. La API con los OTP fuera de la memoria
# ---------------------------------------------------------------------------

class PruebasApiConOtp(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.api = _importar_api()            # limitador apagado, OTP en RepositorioMemoria
        cls.cliente = cls.api.app.test_client()

    def setUp(self):
        self.codigos = []
        self.validar_correo_real = self.api._validar_correo      # antes de simularlo
        parches = {
            "enviar_codigo": mock.patch.object(
                self.api, "enviar_codigo",
                side_effect=lambda correo, nombre, codigo, **_: self.codigos.append(codigo)),
            "enviar_bienvenida": mock.patch.object(self.api, "enviar_bienvenida"),
            "_validar_correo": mock.patch.object(self.api, "_validar_correo",
                                                 return_value=(True, "")),
            "UsuarioDAO": mock.patch.object(self.api, "UsuarioDAO"),
            "obtener_conexion": mock.patch.object(self.api._conexion_bd, "obtener_conexion"),
            "generate_token": mock.patch.object(self.api, "generate_token",
                                                return_value="token-falso"),
        }
        for nombre, parche in parches.items():
            setattr(self, nombre, parche.start())
            self.addCleanup(parche.stop)
        self.UsuarioDAO.return_value.consultar_por_correo.return_value = None
        self.UsuarioDAO.return_value.insertar.return_value = True
        for almacen in (self.api._otp_registro, self.api._otp_login):
            almacen.descartar(CORREO)
            self.addCleanup(almacen.descartar, CORREO)

    def _registrar(self):
        r = self.cliente.post("/api/auth/register", json={
            "name": NOMBRE, "email": CORREO, "password": CLAVE, "acepta_datos": True})
        self.assertEqual(r.status_code, 200)
        return self.codigos[-1]

    def test_la_api_guarda_los_codigos_en_la_bd(self):
        """api.py crea los dos almacenes con OtpDAO (las pruebas los pasan a memoria)."""
        with open(os.path.join(RAIZ, "api.py"), encoding="utf-8") as f:
            arbol = ast.parse(f.read())
        creados = {}
        for nodo in arbol.body:
            if isinstance(nodo, ast.Assign) and isinstance(nodo.value, ast.Call):
                for destino in nodo.targets:
                    if isinstance(destino, ast.Name) and destino.id in ("_otp_registro", "_otp_login"):
                        creados[destino.id] = ast.unparse(nodo.value)
        self.assertEqual(creados, {"_otp_registro": "AlmacenOTP('registro', OtpDAO())",
                                   "_otp_login": "AlmacenOTP('login', OtpDAO())"})

    def test_otro_proceso_completa_el_registro(self):
        codigo = self._registrar()
        repositorio = self.api._otp_registro._repositorio       # la "tabla" compartida
        otro_proceso = AlmacenOTP("registro", repositorio)
        with mock.patch.object(self.api, "_otp_registro", otro_proceso):
            r = self.cliente.post("/api/auth/verify", json={"email": CORREO, "code": codigo})
        self.assertEqual(r.status_code, 201)
        # Ley 1581: con la cuenta creada no queda nada del registro pendiente
        self.assertIsNone(repositorio.obtener(CORREO, "registro"))

    def test_sin_bd_las_rutas_de_codigo_responden_503(self):
        from dao.otp_dao import OtpDAO
        self.obtener_conexion.return_value = None                      # BD apagada
        rutas = {"/api/auth/verify": {"email": CORREO, "code": "123456"},
                 "/api/auth/login/verify": {"email": CORREO, "code": "123456"},
                 "/api/auth/register/resend": {"email": CORREO}}
        with mock.patch.object(self.api._otp_registro, "_repositorio", OtpDAO()), \
                mock.patch.object(self.api._otp_login, "_repositorio", OtpDAO()), \
                mock.patch.object(self.api.app.logger, "disabled", True):   # el 503 se registra
            for ruta, cuerpo in rutas.items():
                with self.subTest(ruta=ruta):
                    r = self.cliente.post(ruta, json=cuerpo)
                    self.assertEqual(r.status_code, 503)
                    self.assertNotIn(CORREO, r.get_data(as_text=True))

    def test_correo_de_mas_de_120_caracteres_no_se_acepta(self):
        largo = "a" * 109 + "@ejemplo.test"          # 122 caracteres
        with mock.patch.object(self.api.dns.resolver, "resolve") as resolve:
            valido, mensaje = self.validar_correo_real(largo)
            self.assertFalse(valido)
            self.assertIn("120", mensaje)
            resolve.assert_not_called()

    def test_al_arrancar_borra_vencidos(self):
        with mock.patch.object(self.api._otp_registro, "limpiar_vencidos", return_value=3) as limpiar:
            self.assertTrue(self.api._preparar_otp())
        limpiar.assert_called_once_with()

    def test_al_arrancar_sin_la_tabla_avisa_y_no_arranca(self):
        sin_tabla = errores_bd.ProgrammingError(msg="Table doesn't exist", errno=1146)
        salida = io.StringIO()
        with mock.patch.object(self.api._otp_registro, "limpiar_vencidos", side_effect=sin_tabla), \
                contextlib.redirect_stdout(salida):
            self.assertFalse(self.api._preparar_otp())
        self.assertIn("2026-11-07_otp_pendientes.sql", salida.getvalue())

    def test_al_arrancar_otro_error_de_sql_no_se_esconde(self):
        otro = errores_bd.ProgrammingError(msg="otro", errno=1064)
        with mock.patch.object(self.api._otp_registro, "limpiar_vencidos", side_effect=otro):
            with self.assertRaises(errores_bd.ProgrammingError):
                self.api._preparar_otp()


# ---------------------------------------------------------------------------
# 5. Con MariaDB real (PETCONNECT_PRUEBA_BD=1), en bases temporales
# ---------------------------------------------------------------------------

def _conectar_servidor():
    import mysql.connector
    from config.db_config import DB_CONFIG
    servidor = {k: v for k, v in DB_CONFIG.items() if k != "database"}
    try:
        conexion = mysql.connector.connect(**servidor)
    except mysql.connector.Error:
        raise unittest.SkipTest("No hay conexion con MariaDB")
    conexion.autocommit = True
    return conexion


@unittest.skipUnless(os.getenv("PETCONNECT_PRUEBA_BD") == "1",
                     "Prueba con MariaDB real: activar con PETCONNECT_PRUEBA_BD=1")
class PruebasContratoEnBD(_ContratoAlmacen, _ConReloj):
    """Las reglas con OtpDAO y la tabla real, en la base temporal petconnect_prueba_otp."""

    @classmethod
    def setUpClass(cls):
        from config.db_config import DB_CONFIG
        from conexion.conexion_bd import ConexionBD
        from test_esquema import RUTA_ESQUEMA, _leer, _sentencias

        _importar_api()                       # claves de prueba sin leer .env
        cls.db_config = DB_CONFIG
        cls.bd_original = DB_CONFIG["database"]
        if cls.bd_original == BD_PRUEBA_OTP:
            raise unittest.SkipTest("DB_NAME no puede ser la base temporal de pruebas")
        cls.conn = _conectar_servidor()
        cursor = cls.conn.cursor()
        # El nombre es una constante del archivo (no viene del usuario)
        cursor.execute(f"DROP DATABASE IF EXISTS `{BD_PRUEBA_OTP}`")
        cursor.execute(f"CREATE DATABASE `{BD_PRUEBA_OTP}` CHARACTER SET utf8mb4 "
                       f"COLLATE utf8mb4_spanish_ci")
        cls.addClassCleanup(cls._borrar_bd_prueba)
        cursor.execute(f"USE `{BD_PRUEBA_OTP}`")
        for sentencia in _sentencias(_leer(RUTA_ESQUEMA)):
            cursor.execute(sentencia)
        cursor.execute("INSERT INTO usuarios (nombres, correo, password_hash) VALUES (%s, %s, %s)",
                       (NOMBRE, "cuenta.otp@ejemplo.test", "hash-falso"))
        cls.ID_USUARIO = cursor.lastrowid
        cursor.close()
        DB_CONFIG["database"] = BD_PRUEBA_OTP
        ConexionBD().cerrar_conexion()

    @classmethod
    def _borrar_bd_prueba(cls):
        from conexion.conexion_bd import ConexionBD
        cls.db_config["database"] = cls.bd_original
        ConexionBD().cerrar_conexion()
        cursor = cls.conn.cursor()
        cursor.execute(f"DROP DATABASE IF EXISTS `{BD_PRUEBA_OTP}`")
        cursor.close()
        cls.conn.close()

    def setUp(self):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM otp_pendientes")
        cursor.close()
        super().setUp()

    def _nuevo_repositorio(self):
        from dao.otp_dao import OtpDAO
        return OtpDAO()

    def _contar_filas(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM otp_pendientes")
        total = cursor.fetchone()[0]
        cursor.close()
        return total

    def test_la_fila_no_trae_el_codigo_en_claro(self):
        codigo = self._crear()
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM otp_pendientes")
        fila = cursor.fetchone()
        cursor.close()
        self.assertNotIn(codigo, " ".join(str(valor) for valor in fila))

    def test_la_regla_y_la_clave_foranea_funcionan(self):
        cursor = self.conn.cursor()
        insertar = ("INSERT INTO otp_pendientes (correo, proposito, codigo_cifrado, vence, "
                    "ultimo_envio, nombre, password_hash, id_usuario) "
                    "VALUES (%s, %s, 'x', 1, 1, %s, %s, %s)")
        incoherentes = (("registro", None, "h", None), ("registro", NOMBRE, None, None),
                        ("login", None, None, None), ("login", NOMBRE, None, self.ID_USUARIO),
                        ("login", None, None, 999999))
        for proposito, nombre, hash_, id_usuario in incoherentes:
            with self.subTest(proposito=proposito, nombre=nombre, id_usuario=id_usuario):
                with self.assertRaises(errores_bd.Error):
                    cursor.execute(insertar, (CORREO, proposito, nombre, hash_, id_usuario))
        cursor.close()

    def test_borrar_la_cuenta_borra_su_inicio_de_sesion_pendiente(self):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO usuarios (nombres, correo, password_hash) VALUES (%s, %s, %s)",
                       (NOMBRE, "se.va@ejemplo.test", "hash-falso"))
        id_usuario = cursor.lastrowid
        self.login.crear(CORREO, {"id_usuario": id_usuario})
        cursor.execute("DELETE FROM usuarios WHERE id_usuario = %s", (id_usuario,))
        cursor.close()
        self.assertFalse(self.login.tiene_pendiente(CORREO))


@unittest.skipUnless(os.getenv("PETCONNECT_PRUEBA_BD") == "1",
                     "Prueba con MariaDB real: activar con PETCONNECT_PRUEBA_BD=1")
class PruebasMigracionOtpEnBD(unittest.TestCase):
    """La migracion crea la tabla en una base vieja y se puede correr dos veces."""

    @classmethod
    def setUpClass(cls):
        cls.conn = _conectar_servidor()
        cursor = cls.conn.cursor()
        cursor.execute(f"DROP DATABASE IF EXISTS `{BD_PRUEBA_OTP_MIGRACION}`")
        cursor.execute(f"CREATE DATABASE `{BD_PRUEBA_OTP_MIGRACION}` "
                       "CHARACTER SET utf8mb4 COLLATE utf8mb4_spanish_ci")
        cls.addClassCleanup(cls._borrar_bd_prueba)
        cursor.execute(f"USE `{BD_PRUEBA_OTP_MIGRACION}`")
        # Base "vieja": solo la tabla a la que apunta la clave foranea
        cursor.execute("CREATE TABLE usuarios (id_usuario int(11) AUTO_INCREMENT PRIMARY KEY) "
                       "ENGINE=InnoDB")
        cursor.close()

    @classmethod
    def _borrar_bd_prueba(cls):
        cursor = cls.conn.cursor()
        cursor.execute(f"DROP DATABASE IF EXISTS `{BD_PRUEBA_OTP_MIGRACION}`")
        cursor.close()
        cls.conn.close()

    def test_se_puede_ejecutar_dos_veces_sin_perder_filas(self):
        from test_esquema import RUTA_MIGRACION_OTP, _leer, _sentencias
        cursor = self.conn.cursor()
        for sentencia in _sentencias(_leer(RUTA_MIGRACION_OTP)):
            cursor.execute(sentencia)
        cursor.execute("INSERT INTO otp_pendientes (correo, proposito, codigo_cifrado, vence, "
                       "ultimo_envio, nombre, password_hash) VALUES (%s, 'registro', 'x', 1, 1, %s, 'h')",
                       (CORREO, NOMBRE))
        for sentencia in _sentencias(_leer(RUTA_MIGRACION_OTP)):
            cursor.execute(sentencia)
        cursor.execute("SELECT COUNT(*) FROM otp_pendientes")
        self.assertEqual(cursor.fetchone()[0], 1)
        cursor.close()


if __name__ == "__main__":
    unittest.main()
