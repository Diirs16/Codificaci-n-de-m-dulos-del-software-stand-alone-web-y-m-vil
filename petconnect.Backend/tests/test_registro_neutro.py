"""
Pruebas de regresion de A-14 (item 4.10 de PRIORIDADES): el registro no revela
quien tiene cuenta.

Antes, POST /api/auth/register respondia 409 "El correo ya esta registrado" y
cualquiera podia averiguar si un correo tenia cuenta. Ahora:
  - un correo con cuenta recibe EXACTAMENTE la misma respuesta que uno nuevo, por
    el mismo camino (bcrypt + un correo la primera vez; nada el segundo intento
    antes de 10 minutos) y el mismo 503 si el correo falla;
  - nunca se crea un codigo OTP para una cuenta que ya existe;
  - el titular recibe un aviso con el nombre de SU cuenta (no el escrito);
  - /api/auth/verify responde lo mismo sin pendiente, con codigo vencido o con
    codigo incorrecto (si no, bastaria probar un codigo para saberlo).

No usan la base de datos real (se simula), no envian correos, no consultan el DNS
ni leen .env. Los relojes se simulan. Datos inventados (Ley 1581).

Ejecutar desde petconnect.Backend, con el entorno virtual activo:
    python -m unittest discover -s tests -v
"""
import contextlib
import hashlib
import io
import os
import re
import sys
import unittest
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from otp import servicio  # noqa: E402
from test_errores import _importar_api  # noqa: E402

# Datos inventados (Ley 1581)
CON_CUENTA = "titular.prueba@ejemplo.test"
SIN_CUENTA = "persona.nueva@ejemplo.test"
CLAVE = "Firulais2026!"
NOMBRE_CUENTA = "Ana Maria"
NOMBRE_ESCRITO = "Intruso Falso"
MENSAJE_503 = "No pudimos enviar el código a tu correo. Intenta de nuevo en unos minutos"
INICIO = 1_000_000.0


class FalloCorreoSimulado(Exception):
    """Error de envio inventado; su mensaje trae el correo, como uno real de SMTP."""


def _cuenta(**cambios):
    datos = dict(id_usuario=7, nombres=NOMBRE_CUENTA, apellidos="Prueba", correo=CON_CUENTA,
                 password_hash="hash-guardado", estado="activo", acepta_datos=True,
                 fecha_autorizacion_datos=None, version_politica_datos=None)
    datos.update(cambios)
    return SimpleNamespace(**datos)


class _BaseNeutro(unittest.TestCase):
    """API con BD, DNS, correo y relojes simulados. CON_CUENTA tiene cuenta; SIN_CUENTA no."""

    @classmethod
    def setUpClass(cls):
        cls.api = _importar_api()            # limitador apagado, sin .env
        cls.cliente = cls.api.app.test_client()

    def setUp(self):
        self.ahora = INICIO
        self.codigos = []     # (correo, nombre, codigo) de cada codigo "enviado"
        self.avisos = []      # (correo, nombre) de cada aviso "enviado"
        self.fallar_envio = False
        self.cuenta = _cuenta()
        parches = {
            "reloj_otp": mock.patch.object(servicio, "time", SimpleNamespace(time=lambda: self.ahora)),
            "reloj_avisos": mock.patch.object(self.api, "_reloj_avisos", side_effect=lambda: self.ahora),
            "obtener_conexion": mock.patch.object(self.api._conexion_bd, "obtener_conexion",
                                                  return_value=mock.MagicMock()),
            "UsuarioDAO": mock.patch.object(self.api, "UsuarioDAO"),
            "hash_password": mock.patch.object(self.api, "hash_password",
                                               side_effect=lambda clave: f"hash-de-{clave}"),
            "_validar_correo": mock.patch.object(self.api, "_validar_correo", return_value=(True, "")),
            "generate_token": mock.patch.object(self.api, "generate_token", return_value="token-falso"),
            "enviar_codigo": mock.patch.object(self.api, "enviar_codigo", side_effect=self._enviar_codigo),
            "enviar_aviso": mock.patch.object(self.api, "enviar_aviso_cuenta_existente",
                                              side_effect=self._enviar_aviso),
            "enviar_bienvenida": mock.patch.object(self.api, "enviar_bienvenida"),
        }
        for nombre, parche in parches.items():
            setattr(self, nombre, parche.start())
            self.addCleanup(parche.stop)

        self.dao = self.UsuarioDAO.return_value
        self.dao.consultar_por_correo.side_effect = (
            lambda correo: self.cuenta if correo.lower() == CON_CUENTA else None)
        self.dao.insertar.return_value = True

        for correo in (CON_CUENTA, SIN_CUENTA):
            self.api._otp_registro.descartar(correo)
            self.api._liberar_aviso(correo)
            self.addCleanup(self.api._otp_registro.descartar, correo)
            self.addCleanup(self.api._liberar_aviso, correo)

    # -- ayudas ---------------------------------------------------------------

    def _enviar_codigo(self, email, nombre, codigo, **_):
        if self.fallar_envio:
            raise FalloCorreoSimulado(f"550 buzon no disponible: {email}")
        self.codigos.append((email, nombre, codigo))

    def _enviar_aviso(self, email, nombre):
        if self.fallar_envio:
            raise FalloCorreoSimulado(f"550 buzon no disponible: {email}")
        self.avisos.append((email, nombre))

    def _registrar(self, correo, nombre=NOMBRE_ESCRITO):
        return self.cliente.post("/api/auth/register", json={
            "name": nombre, "email": correo, "password": CLAVE, "acepta_datos": True})

    def _verificar(self, correo, codigo="000000"):
        return self.cliente.post("/api/auth/verify", json={"email": correo, "code": codigo})

    def _avanzar(self, segundos):
        self.ahora += segundos

    def _igual_salvo_el_correo(self, r_con_cuenta, r_sin_cuenta):
        """Mismo codigo HTTP, mismo tipo de contenido y mismo JSON (el correo es el que se escribio)."""
        self.assertEqual(r_con_cuenta.status_code, r_sin_cuenta.status_code)
        self.assertEqual(r_con_cuenta.content_type, r_sin_cuenta.content_type)
        cuerpo_con = r_con_cuenta.get_data(as_text=True).replace(CON_CUENTA, "<correo>")
        cuerpo_sin = r_sin_cuenta.get_data(as_text=True).replace(SIN_CUENTA, "<correo>")
        self.assertEqual(cuerpo_con, cuerpo_sin)


class PruebasRegistroNeutro(_BaseNeutro):

    def test_correo_con_cuenta_responde_igual_que_uno_nuevo(self):
        r_sin = self._registrar(SIN_CUENTA)
        r_con = self._registrar(CON_CUENTA)
        self.assertEqual(r_con.status_code, 200)                 # ya no hay 409
        self.assertEqual(r_con.get_json(), {"message": "Codigo enviado", "email": CON_CUENTA})
        self._igual_salvo_el_correo(r_con, r_sin)
        self.assertNotIn("registrado", r_con.get_data(as_text=True))

    def test_cuenta_inactiva_o_bloqueada_tambien_responde_neutro(self):
        for estado in ("inactivo", "bloqueado"):
            with self.subTest(estado=estado):
                self.api._liberar_aviso(CON_CUENTA)
                self.cuenta = _cuenta(estado=estado)
                r = self._registrar(CON_CUENTA)
                self.assertEqual(r.status_code, 200)
                self.assertEqual(r.get_json(), {"message": "Codigo enviado", "email": CON_CUENTA})

    def test_cuenta_existente_no_crea_codigo_ni_lo_envia(self):
        self._registrar(CON_CUENTA)
        self.assertFalse(self.api._otp_registro.tiene_pendiente(CON_CUENTA))
        self.assertEqual(self.codigos, [])
        self.dao.insertar.assert_not_called()

    def test_avisa_al_titular_con_el_nombre_de_su_cuenta(self):
        self._registrar(CON_CUENTA, nombre=NOMBRE_ESCRITO)
        self.assertEqual(self.avisos, [(CON_CUENTA, "Ana")])     # no "Intruso" (A-05)

    def test_cuenta_existente_calcula_bcrypt_como_un_registro_nuevo(self):
        # el tiempo de respuesta no debe delatar la cuenta (antes el 409 salia sin bcrypt)
        self._registrar(SIN_CUENTA)
        self.assertEqual(self.hash_password.call_count, 1)
        self._registrar(CON_CUENTA)
        self.assertEqual(self.hash_password.call_count, 2)
        self.hash_password.assert_called_with(CLAVE)

    def test_segundo_intento_antes_de_10_minutos_hace_lo_mismo_que_uno_nuevo(self):
        # Registro nuevo: el segundo intento no calcula bcrypt ni envia otro codigo (A-09).
        # Cuenta existente: el segundo intento no calcula bcrypt ni envia otro aviso.
        for correo, enviados in ((SIN_CUENTA, self.codigos), (CON_CUENTA, self.avisos)):
            with self.subTest(correo=correo):
                self.hash_password.reset_mock()
                primero = self._registrar(correo)
                self._avanzar(60)
                segundo = self._registrar(correo)
                self.assertEqual(segundo.get_json(), primero.get_json())
                self.assertEqual(segundo.status_code, 200)
                self.assertEqual(len(enviados), 1, "no se envia un segundo correo")
                self.assertEqual(self.hash_password.call_count, 1, "bcrypt solo la primera vez")

    def test_pasados_10_minutos_se_puede_avisar_otra_vez(self):
        self._registrar(CON_CUENTA)
        self._avanzar(self.api.AVISO_REGISTRO_ESPERA - 1)
        self._registrar(CON_CUENTA)
        self.assertEqual(len(self.avisos), 1)
        self._avanzar(1)
        self._registrar(CON_CUENTA)
        self.assertEqual(len(self.avisos), 2)

    def test_mayusculas_cuentan_como_el_mismo_correo(self):
        self._registrar(CON_CUENTA)
        r = self._registrar(CON_CUENTA.upper())
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(self.avisos), 1)

    def test_aviso_fallido_fuera_de_desarrollo_responde_el_mismo_503(self):
        self.fallar_envio = True
        with mock.patch.dict(os.environ), contextlib.redirect_stdout(io.StringIO()) as salida:
            os.environ.pop("APP_ENV", None)
            with self.assertLogs(self.api.app.logger, level="WARNING") as logs:
                r_sin = self._registrar(SIN_CUENTA)
                r_con = self._registrar(CON_CUENTA)
        self.assertEqual(r_con.status_code, 503)
        self.assertEqual(r_con.get_json(), {"error": MENSAJE_503})
        self._igual_salvo_el_correo(r_con, r_sin)
        registro = "\n".join(logs.output) + salida.getvalue()
        for dato in (CON_CUENTA, SIN_CUENTA, "buzon"):           # Ley 1581 / A-10
            self.assertNotIn(dato, registro)
        self.assertFalse(self.api._otp_registro.tiene_pendiente(CON_CUENTA))

        # el aviso que no salio no cuenta: el siguiente intento si lo envia
        self.fallar_envio = False
        self._registrar(CON_CUENTA)
        self.assertEqual(self.avisos, [(CON_CUENTA, "Ana")])

    def test_aviso_fallido_en_desarrollo_responde_200_como_un_registro_nuevo(self):
        self.fallar_envio = True
        with mock.patch.dict(os.environ, {"APP_ENV": "desarrollo"}), \
                contextlib.redirect_stdout(io.StringIO()) as salida:
            with self.assertLogs(self.api.app.logger, level="WARNING"):
                r_sin = self._registrar(SIN_CUENTA)
                r_con = self._registrar(CON_CUENTA)
        self.assertEqual(r_con.status_code, 200)
        self._igual_salvo_el_correo(r_con, r_sin)
        self.assertNotIn(CON_CUENTA, salida.getvalue())

    def test_la_memoria_de_avisos_guarda_el_hash_y_no_el_correo(self):
        self._registrar(CON_CUENTA)
        claves = list(self.api._avisos_registro)
        self.assertIn(hashlib.sha256(CON_CUENTA.encode()).hexdigest(), claves)
        self.assertFalse(any("@" in clave for clave in claves))

    def test_la_memoria_de_avisos_tiene_tope(self):
        with mock.patch.object(self.api, "AVISOS_MAXIMO", 3):
            correos = [f"tope{i}@ejemplo.test" for i in range(5)]
            for correo in correos:
                self.addCleanup(self.api._liberar_aviso, correo)
                self.assertTrue(self.api._reservar_aviso(correo))
            self.assertLessEqual(len(self.api._avisos_registro), 3)
            claves = set(self.api._avisos_registro)
            self.assertIn(self.api._clave_aviso(correos[-1]), claves)      # el mas nuevo queda
            self.assertNotIn(self.api._clave_aviso(correos[0]), claves)    # el mas viejo se va


class PruebasVerifyNeutro(_BaseNeutro):
    """Tras un /register neutro, /verify tampoco debe delatar la cuenta."""

    def test_sin_pendiente_y_codigo_incorrecto_responden_igual(self):
        self._registrar(SIN_CUENTA)        # tiene codigo: "000000" no es (salvo azar, ver abajo)
        self._registrar(CON_CUENTA)        # no tiene codigo
        codigo_real = self.codigos[0][2]
        malo = "000000" if codigo_real != "000000" else "111111"
        r_sin = self._verificar(SIN_CUENTA, malo)
        r_con = self._verificar(CON_CUENTA, malo)
        self.assertEqual(r_con.status_code, 400)
        self.assertEqual(r_con.get_json(), {"error": self.api._MENSAJE_CODIGO_REGISTRO})
        self._igual_salvo_el_correo(r_con, r_sin)
        self.dao.insertar.assert_not_called()
        self.generate_token.assert_not_called()

    def test_codigo_vencido_responde_igual_que_sin_pendiente(self):
        self._registrar(SIN_CUENTA)
        codigo_real = self.codigos[0][2]
        self._avanzar(servicio.EXPIRACION_SEGUNDOS + 1)
        r_vencido = self._verificar(SIN_CUENTA, codigo_real)       # el correcto, pero vencido
        r_sin_pendiente = self._verificar(CON_CUENTA, codigo_real)
        self.assertEqual(r_vencido.status_code, 400)
        self.assertEqual(r_vencido.get_json(), r_sin_pendiente.get_json())
        self.dao.insertar.assert_not_called()

    def test_el_codigo_correcto_sigue_creando_la_cuenta(self):
        self._registrar(SIN_CUENTA, nombre="Laura Gomez")
        r = self._verificar(SIN_CUENTA, self.codigos[0][2])
        self.assertEqual(r.status_code, 201)
        self.dao.insertar.assert_called_once()


class PruebasPlantillaDelAviso(unittest.TestCase):
    """correo/servicio.py: el aviso escapa el nombre y no lleva ningun codigo."""

    def setUp(self):
        from correo import servicio as correo_servicio
        self.correo_servicio = correo_servicio
        parche = mock.patch.object(correo_servicio, "enviar_correo")
        self.enviar_correo = parche.start()
        self.addCleanup(parche.stop)

    def _enviar(self, nombre):
        self.correo_servicio.enviar_aviso_cuenta_existente(CON_CUENTA, nombre)
        destino, asunto, texto, html = self.enviar_correo.call_args.args
        return destino, asunto, texto, html

    def test_destino_asunto_y_textos(self):
        destino, asunto, texto, html = self._enviar("Ana")
        self.assertEqual(destino, CON_CUENTA)
        self.assertEqual(asunto, "PetConnect - Intento de registro con tu correo")
        for cuerpo in (texto, html):
            self.assertIn("Ana", cuerpo)
            self.assertIn("proyectopetconnect+atencion@gmail.com", cuerpo)
        self.assertIn("ya tienes una", texto)

    def test_no_lleva_codigo_ni_el_correo_del_titular_en_el_cuerpo(self):
        _, _, texto, html = self._enviar("Ana")
        for cuerpo in (texto, html):
            # 6 cifras seguidas que no sean un color del HTML (#111111)
            self.assertIsNone(re.search(r"(?<![#\w])\d{6}\b", cuerpo), "un aviso no lleva codigo")
            self.assertNotIn(CON_CUENTA, cuerpo)
            self.assertNotIn("{", cuerpo)                    # sin marcadores sin llenar

    def test_escapa_el_html_del_nombre(self):
        _, _, _, html = self._enviar('<a href="https://sitio-falso.example">Ana</a>')
        self.assertNotIn("<a href=\"https://sitio-falso.example\"", html)
        self.assertIn("&lt;a href=", html)


if __name__ == "__main__":
    unittest.main()
