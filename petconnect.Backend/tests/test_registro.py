"""
Pruebas de regresion de A-09 (item 2.7 de PRIORIDADES): un segundo /register con el
mismo correo NO pisa el registro pendiente (vale la primera contrasena) y la ruta
nueva /api/auth/register/resend reenvia el MISMO codigo sin dar intentos nuevos.
Reglas del reenvio (decididas el 05/11/2026): 60 s entre correos, maximo 3 reenvios,
no alarga los 10 minutos y no se reenvia un codigo bloqueado.

No usan la base de datos real (se simula), no envian correos, no consultan el DNS
ni leen .env. El reloj de otp/servicio.py se simula para no esperar minutos.

Ejecutar desde petconnect.Backend, con el entorno virtual activo:
    python -m unittest discover -s tests -v
"""
import contextlib
import io
import os
import sys
import unittest
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from otp import servicio  # noqa: E402
from otp.servicio import AlmacenOTP  # noqa: E402
from test_errores import _importar_api  # noqa: E402

# Datos inventados (Ley 1581)
CORREO = "victima.prueba@ejemplo.test"
OTRO_CORREO = "nadie.registrado@ejemplo.test"
NOMBRE_PRIMERO = "Ana Prueba"
NOMBRE_SEGUNDO = "Intruso Falso"
CLAVE_PRIMERA = "Firulais2026!"
CLAVE_SEGUNDA = "Michis2026#"

RESEND = "/api/auth/register/resend"
MENSAJE_REENVIO = "Si hay un registro pendiente para este correo, te reenviamos el codigo"
MENSAJE_503 = "No pudimos enviar el código a tu correo. Intenta de nuevo en unos minutos"
MENSAJE_429_LIMITE = "Demasiadas peticiones. Espera un minuto e intenta de nuevo"
INICIO = 1_000_000.0          # hora simulada (segundos) al empezar cada prueba


class FalloCorreoSimulado(Exception):
    """Error de envio inventado; su mensaje trae el correo, como uno real de SMTP."""


def _codigo_incorrecto(codigo: str) -> str:
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


class PruebasVigente(_ConReloj):
    """6. AlmacenOTP.vigente() por si solo, sin Flask."""

    def setUp(self):
        super().setUp()
        self.almacen = AlmacenOTP()
        self.codigo = self.almacen.crear(CORREO, {"name": NOMBRE_PRIMERO})

    def test_devuelve_el_pendiente_si_no_vencio(self):
        self._avanzar(servicio.EXPIRACION_SEGUNDOS - 1)
        pendiente = self.almacen.vigente(CORREO)
        self.assertIsNotNone(pendiente)
        self.assertEqual(pendiente["name"], NOMBRE_PRIMERO)
        self.assertTrue(self.almacen.tiene_pendiente(CORREO))

    def test_lo_borra_si_ya_vencio(self):
        self._avanzar(servicio.EXPIRACION_SEGUNDOS + 1)
        self.assertIsNone(self.almacen.vigente(CORREO))
        self.assertFalse(self.almacen.tiene_pendiente(CORREO))

    def test_sin_pendiente_devuelve_none(self):
        self.assertIsNone(self.almacen.vigente(OTRO_CORREO))

    def test_no_cambia_contador_ni_vencimiento(self):
        self.almacen.verificar(CORREO, _codigo_incorrecto(self.codigo))   # 1 fallo
        antes = dict(self.almacen.vigente(CORREO))
        self._avanzar(30)
        self.assertEqual(self.almacen.vigente(CORREO), antes)


class PruebasRegistroYReenvio(_ConReloj):
    """1 a 5 y 8: /register, /verify y /register/resend con BD, DNS y correo simulados."""

    @classmethod
    def setUpClass(cls):
        cls.api = _importar_api()            # limitador apagado
        cls.cliente = cls.api.app.test_client()

    def setUp(self):
        super().setUp()
        self.envios = []       # (correo, nombre, codigo) de cada correo "enviado"
        self.fallar_envio = False
        parches = {
            "obtener_conexion": mock.patch.object(self.api._conexion_bd, "obtener_conexion",
                                                  return_value=mock.MagicMock()),
            "UsuarioDAO": mock.patch.object(self.api, "UsuarioDAO"),
            "hash_password": mock.patch.object(self.api, "hash_password",
                                               side_effect=lambda clave: f"hash-de-{clave}"),
            "_validar_correo": mock.patch.object(self.api, "_validar_correo", return_value=(True, "")),
            "generate_token": mock.patch.object(self.api, "generate_token", return_value="token-falso"),
            "enviar_codigo": mock.patch.object(self.api, "enviar_codigo", side_effect=self._enviar),
            "enviar_bienvenida": mock.patch.object(self.api, "enviar_bienvenida"),
        }
        for nombre, parche in parches.items():
            setattr(self, nombre, parche.start())
            self.addCleanup(parche.stop)

        self.UsuarioDAO.return_value.consultar_por_correo.return_value = None   # correo libre
        self.UsuarioDAO.return_value.insertar.return_value = True

        for correo in (CORREO, OTRO_CORREO):
            self.api._otp_registro.descartar(correo)
            self.addCleanup(self.api._otp_registro.descartar, correo)

    # -- ayudas ---------------------------------------------------------------

    def _enviar(self, email, nombre, codigo, **_):
        if self.fallar_envio:
            raise FalloCorreoSimulado(f"550 buzon no disponible: {email}")
        self.envios.append((email, nombre, codigo))

    def _registrar(self, nombre=NOMBRE_PRIMERO, clave=CLAVE_PRIMERA, correo=CORREO):
        return self.cliente.post("/api/auth/register",
                                 json={"name": nombre, "email": correo, "password": clave,
                                       "acepta_datos": True})   # NC-005 (item 3.1)

    def _reenviar(self, correo=CORREO):
        return self.cliente.post(RESEND, json={"email": correo})

    def _verificar(self, codigo, correo=CORREO):
        return self.cliente.post("/api/auth/verify", json={"email": correo, "code": codigo})

    def _pendiente(self):
        return self.api._otp_registro.vigente(CORREO)

    def _fallar(self, codigo, veces):
        for _ in range(veces):
            r = self._verificar(_codigo_incorrecto(codigo))
            self.assertEqual(r.status_code, 400)
            self.assertEqual(r.get_json(), {"error": self.api._MENSAJE_CODIGO_REGISTRO})   # item 4.10

    def _reenvio_neutro(self, r):
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json(), {"message": MENSAJE_REENVIO})

    # -- 1. el segundo registro no pisa al primero -----------------------------

    def test_segundo_registro_no_cambia_el_hash_y_responde_igual(self):
        r1 = self._registrar(NOMBRE_PRIMERO, CLAVE_PRIMERA)
        r2 = self._registrar(NOMBRE_SEGUNDO, CLAVE_SEGUNDA)

        self.assertEqual((r1.status_code, r1.get_json()), (r2.status_code, r2.get_json()))
        self.assertEqual(r1.status_code, 200)
        pendiente = self._pendiente()
        self.assertEqual(pendiente["password_hash"], f"hash-de-{CLAVE_PRIMERA}")
        self.assertEqual(pendiente["name"], NOMBRE_PRIMERO)
        self.assertEqual(len(self.envios), 1, "el segundo registro no debe enviar otro correo")

        # Al verificar, la cuenta se crea con la contrasena del PRIMERO
        r = self._verificar(self.envios[0][2])
        self.assertEqual(r.status_code, 201)
        usuario = self.UsuarioDAO.return_value.insertar.call_args.args[0]
        self.assertEqual(usuario.password_hash, f"hash-de-{CLAVE_PRIMERA}")
        self.assertEqual(usuario.nombres, "Ana")

    def test_segundo_registro_no_cambia_codigo_ni_vencimiento(self):
        self._registrar()
        antes = dict(self._pendiente())
        self._avanzar(120)
        self._registrar(NOMBRE_SEGUNDO, CLAVE_SEGUNDA)
        self.assertEqual(self._pendiente(), antes)

    # -- 2. registrarse otra vez o reenviar no da intentos nuevos --------------

    def test_cinco_fallos_y_reenvio_siguen_bloqueados(self):
        self._registrar()
        codigo = self.envios[0][2]
        self._fallar(codigo, 5)
        self._avanzar(61)
        self._reenvio_neutro(self._reenviar())
        self._registrar(NOMBRE_PRIMERO, CLAVE_PRIMERA)
        self.assertEqual(len(self.envios), 1, "un codigo bloqueado no se reenvia (decision e)")

        r = self._verificar(codigo)
        self.assertEqual(r.status_code, 429)
        self.assertIn("Demasiados intentos fallidos", r.get_json()["error"])
        self.UsuarioDAO.return_value.insertar.assert_not_called()

    def test_reenvio_a_mitad_no_reinicia_el_contador(self):
        self._registrar()
        codigo = self.envios[0][2]
        self._fallar(codigo, 4)
        self._avanzar(61)
        self._reenvio_neutro(self._reenviar())
        self.assertEqual(len(self.envios), 2, "con 4 fallos el codigo aun sirve: se reenvia")
        self._registrar(NOMBRE_SEGUNDO, CLAVE_SEGUNDA)
        self._fallar(codigo, 1)                       # 5.o fallo, no el 1.o

        r = self._verificar(codigo)
        self.assertEqual(r.status_code, 429)
        self.UsuarioDAO.return_value.insertar.assert_not_called()

    # -- 3. un pendiente vencido si se reemplaza -------------------------------

    def test_pendiente_vencido_se_reemplaza(self):
        self._registrar(NOMBRE_PRIMERO, CLAVE_PRIMERA)
        self._avanzar(servicio.EXPIRACION_SEGUNDOS + 1)
        r = self._registrar(NOMBRE_SEGUNDO, CLAVE_SEGUNDA)

        self.assertEqual(r.status_code, 200)
        pendiente = self._pendiente()
        self.assertEqual(pendiente["password_hash"], f"hash-de-{CLAVE_SEGUNDA}")
        self.assertEqual(pendiente["name"], NOMBRE_SEGUNDO)
        self.assertEqual(pendiente["intentos"], 0)
        self.assertEqual(len(self.envios), 2)
        self.assertEqual(self.envios[1][2], pendiente["code"])

    # -- 4. el reenvio manda el mismo codigo -----------------------------------

    def test_reenvio_manda_el_mismo_codigo_y_el_primer_nombre(self):
        self._registrar(NOMBRE_PRIMERO, CLAVE_PRIMERA)
        self._registrar(NOMBRE_SEGUNDO, CLAVE_SEGUNDA)     # no cambia nada
        self._avanzar(61)
        self._reenvio_neutro(self._reenviar())

        self.assertEqual(len(self.envios), 2)
        primero, reenvio = self.envios
        self.assertEqual(reenvio, (CORREO, "Ana", primero[2]))
        self.assertEqual(self._verificar(reenvio[2]).status_code, 201)

    # -- 5. sin pendiente: misma respuesta y nada enviado ----------------------

    def test_reenviar_sin_pendiente_responde_igual_y_no_envia(self):
        self._registrar()
        self._avanzar(61)
        con_pendiente = self._reenviar(CORREO)
        sin_pendiente = self._reenviar(OTRO_CORREO)

        self.assertEqual((con_pendiente.status_code, con_pendiente.get_json()),
                         (sin_pendiente.status_code, sin_pendiente.get_json()))
        self.assertEqual([e[0] for e in self.envios], [CORREO, CORREO])
        self.assertFalse(self.api._otp_registro.tiene_pendiente(OTRO_CORREO))

    def test_reenviar_sin_correo_o_con_numero_responde_400(self):
        for cuerpo in ({}, {"email": ""}, {"email": "   "}, {"email": 5}):
            with self.subTest(cuerpo=cuerpo):
                self.assertEqual(self.cliente.post(RESEND, json=cuerpo).status_code, 400)
        self.assertEqual(self.envios, [])

    # -- 8. reglas (b), (c) y (d) ---------------------------------------------

    def test_reenvio_antes_de_60_segundos_no_envia(self):
        self._registrar()
        self._avanzar(59)
        self._reenvio_neutro(self._reenviar())
        self.assertEqual(len(self.envios), 1)

        self._avanzar(2)                              # 61 s desde el primer correo
        self._reenvio_neutro(self._reenviar())
        self.assertEqual(len(self.envios), 2)

        self._avanzar(30)                             # 30 s desde el reenvio
        self._reenvio_neutro(self._reenviar())
        self.assertEqual(len(self.envios), 2)

    def test_maximo_tres_reenvios_por_codigo(self):
        self._registrar()
        for _ in range(servicio.MAX_REENVIOS + 2):
            self._avanzar(61)
            self._reenvio_neutro(self._reenviar())
        self.assertEqual(len(self.envios), 1 + servicio.MAX_REENVIOS)

    def test_reenviar_no_alarga_el_vencimiento(self):
        self._registrar()
        vence = self._pendiente()["expires"]
        self._avanzar(servicio.EXPIRACION_SEGUNDOS - 30)
        self._reenvio_neutro(self._reenviar())
        self.assertEqual(len(self.envios), 2)
        self.assertEqual(self._pendiente()["expires"], vence)

        self._avanzar(31)                             # ya pasaron los 10 minutos
        codigo = self.envios[0][2]
        r = self._verificar(codigo)
        self.assertEqual(r.status_code, 400)
        # Item 4.10 (A-14): "vencido" ya no tiene mensaje propio. Que el codigo
        # correcto no sirvio por vencido se ve en que el pendiente ya no esta.
        self.assertEqual(r.get_json(), {"error": self.api._MENSAJE_CODIGO_REGISTRO})
        self.assertFalse(self.api._otp_registro.tiene_pendiente(CORREO))

    # -- envio fallido del reenvio (decision f y A-10) -------------------------

    def test_reenvio_fallido_responde_503_sin_datos_y_conserva_el_pendiente(self):
        self._registrar()
        codigo = self.envios[0][2]
        self._avanzar(61)
        self.fallar_envio = True
        salida = io.StringIO()
        with mock.patch.dict(os.environ), contextlib.redirect_stdout(salida):
            os.environ.pop("APP_ENV", None)
            with self.assertLogs(self.api.app.logger, level="WARNING") as logs:
                r = self._reenviar()

        self.assertEqual(r.status_code, 503)
        self.assertEqual(r.get_json(), {"error": MENSAJE_503})
        texto = salida.getvalue() + "\n".join(logs.output)
        self.assertNotIn(CORREO, texto)
        self.assertNotIn(codigo, texto)
        self.assertIn("FalloCorreoSimulado", texto)
        self.assertIsNotNone(self._pendiente(), "el primer codigo sigue sirviendo")
        self.assertEqual(self._verificar(codigo).status_code, 201)

    def test_reenvio_fallido_en_desarrollo_imprime_solo_el_codigo(self):
        self._registrar()
        codigo = self.envios[0][2]
        self._avanzar(61)
        self.fallar_envio = True
        salida = io.StringIO()
        with mock.patch.dict(os.environ, {"APP_ENV": "desarrollo"}), contextlib.redirect_stdout(salida):
            with self.assertLogs(self.api.app.logger, level="WARNING"):
                r = self._reenviar()

        self._reenvio_neutro(r)
        self.assertIn(codigo, salida.getvalue())
        self.assertNotIn(CORREO, salida.getvalue())


class PruebasLimiteReenvio(unittest.TestCase):
    """7. Con el limitador encendido, la 6.a peticion de reenvio en un minuto -> 429."""

    @classmethod
    def setUpClass(cls):
        cls.api = _importar_api()
        cls.cliente = cls.api.app.test_client()

    def setUp(self):
        parche = mock.patch.object(self.api, "enviar_codigo")
        self.enviar_codigo = parche.start()
        self.addCleanup(parche.stop)
        self.api.limiter.enabled = True
        self.api.limiter.reset()
        self.addCleanup(self.api.limiter.reset)
        self.addCleanup(setattr, self.api.limiter, "enabled", False)

    def test_sexta_peticion_de_reenvio_responde_429(self):
        ip = {"REMOTE_ADDR": "203.0.113.30"}   # IP de documentacion (RFC 5737)
        for i in range(5):
            r = self.cliente.post(RESEND, json={"email": OTRO_CORREO}, environ_base=ip)
            self.assertEqual(r.status_code, 200, f"peticion {i + 1}")
        r = self.cliente.post(RESEND, json={"email": OTRO_CORREO}, environ_base=ip)
        self.assertEqual(r.status_code, 429)
        self.assertEqual(r.get_json(), {"error": MENSAJE_429_LIMITE})
        self.assertTrue(r.headers.get("Retry-After"))
        self.enviar_codigo.assert_not_called()


if __name__ == "__main__":
    unittest.main()
