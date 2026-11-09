"""
Pruebas de regresion del item 4.18 de PRIORIDADES (A-14): /api/auth/login no debe
revelar por el TIEMPO de respuesta si un correo tiene cuenta.

Antes, con un correo sin cuenta, "usuario is None" cortaba antes de bcrypt y la API
respondia enseguida; con un correo registrado calculaba bcrypt (~0,3 s con costo 12)
aunque la contrasena fuera mala. Ahora se compara siempre: sin cuenta, contra un
hash bcrypt de relleno; con hash SHA-256 heredado (NC-001), se paga ademas un bcrypt
de relleno.

En vez de medir tiempos con un cronometro (en un PC compartido eso falla al azar),
se CUENTAN las llamadas reales a bcrypt.checkpw con un espia (mock con wraps: deja
pasar la llamada y solo la cuenta). Mismo numero de llamadas = mismo trabajo.

No usan la base de datos real (se simula), no envian correos ni leen .env. El
limitador del 2.6 queda apagado (_importar_api).

Ejecutar desde petconnect.Backend, con el entorno virtual activo:
    python -m unittest discover -s tests -v
"""
import hashlib
import os
import sys
import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest import mock

import bcrypt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_errores import _importar_api  # noqa: E402

from security import passwords  # noqa: E402
from security.passwords import COSTO_BCRYPT, hash_de_relleno, hash_password, verificar_password  # noqa: E402

# Datos inventados (Ley 1581)
CORREO = "cuenta.tiempo@ejemplo.test"
CORREO_SIN_CUENTA = "nadie.registrado@ejemplo.test"
CLAVE = "Firulais2026!"
CLAVE_MALA = "Michi2026?"
ID_USUARIO = 11
MENSAJE_401 = {"error": "Correo o contrasena incorrectos"}


class PruebasLoginSinFugaPorTiempo(unittest.TestCase):
    """/login con BD y correo simulados; bcrypt real, contado con un espia."""

    @classmethod
    def setUpClass(cls):
        cls.api = _importar_api()            # limitador apagado
        cls.cliente = cls.api.app.test_client()
        cls.hash_bcrypt = hash_password(CLAVE)                        # costo 12, como en la BD
        cls.hash_heredado = hashlib.sha256(CLAVE.encode()).hexdigest()  # NC-001

    def setUp(self):
        parches = {
            "obtener_conexion": mock.patch.object(self.api._conexion_bd, "obtener_conexion",
                                                  return_value=mock.MagicMock()),
            "UsuarioDAO": mock.patch.object(self.api, "UsuarioDAO"),
            "enviar_codigo": mock.patch.object(self.api, "enviar_codigo"),
            # El espia: bcrypt.checkpw sigue funcionando, pero se cuentan sus llamadas
            "checkpw": mock.patch.object(passwords.bcrypt, "checkpw", wraps=bcrypt.checkpw),
        }
        for nombre, parche in parches.items():
            setattr(self, nombre, parche.start())
            self.addCleanup(parche.stop)
        self.dao = self.UsuarioDAO.return_value
        for correo in (CORREO, CORREO_SIN_CUENTA):
            self.api._otp_login.descartar(correo)
            self.addCleanup(self.api._otp_login.descartar, correo)

    def _usuario(self, password_hash=None, estado="activo"):
        """Usuario falso con los campos que mira la API, con la autorizacion al dia."""
        return SimpleNamespace(
            id_usuario=ID_USUARIO, nombres="Cuenta", apellidos="Tiempo", correo=CORREO,
            password_hash=password_hash or self.hash_bcrypt, estado=estado,
            acepta_datos=True, fecha_autorizacion_datos=datetime(2026, 11, 7, 9, 0, 0),
            version_politica_datos=self.api.VERSION_POLITICA_DATOS,
        )

    def _login(self, usuario, correo=CORREO, clave=CLAVE_MALA):
        """Hace un /login y devuelve (respuesta, llamadas a bcrypt.checkpw)."""
        self.dao.consultar_por_correo.return_value = usuario
        self.checkpw.reset_mock()
        r = self.cliente.post("/api/auth/login", json={"email": correo, "password": clave})
        return r, self.checkpw.call_count

    def _sin_codigo(self):
        self.enviar_codigo.assert_not_called()
        self.dao.actualizar_password.assert_not_called()
        self.assertFalse(self.api._otp_login.tiene_pendiente(CORREO))
        self.assertFalse(self.api._otp_login.tiene_pendiente(CORREO_SIN_CUENTA))

    # -- El corazon del 4.18 -----------------------------------------------------

    def test_correo_sin_cuenta_tambien_calcula_bcrypt(self):
        r, llamadas = self._login(None, correo=CORREO_SIN_CUENTA)
        self.assertEqual(r.status_code, 401)
        self.assertEqual(r.get_json(), MENSAJE_401)
        self.assertEqual(llamadas, 1)
        # ...y contra el hash de relleno, no contra otro cualquiera
        self.assertEqual(self.checkpw.call_args.args[1], hash_de_relleno().encode("ascii"))
        self._sin_codigo()

    def test_sin_cuenta_y_con_cuenta_hacen_el_mismo_trabajo_y_responden_igual(self):
        sin_cuenta, llamadas_sin = self._login(None, correo=CORREO_SIN_CUENTA)
        con_cuenta, llamadas_con = self._login(self._usuario())
        self.assertEqual(llamadas_sin, llamadas_con)
        self.assertEqual(llamadas_con, 1)
        self.assertEqual(sin_cuenta.status_code, con_cuenta.status_code)
        self.assertEqual(sin_cuenta.get_data(), con_cuenta.get_data())   # el mismo JSON, byte a byte
        self._sin_codigo()

    def test_cuenta_heredada_con_clave_mala_tambien_paga_bcrypt(self):
        # Opcion B del dueno: el SHA-256 es instantaneo; sin el bcrypt de relleno
        # una cuenta heredada se distinguiria de las demas por lo rapido.
        sin_cuenta, llamadas_sin = self._login(None, correo=CORREO_SIN_CUENTA)
        heredada, llamadas_her = self._login(self._usuario(self.hash_heredado))
        self.assertEqual(llamadas_her, llamadas_sin)
        self.assertEqual(llamadas_her, 1)
        self.assertEqual(heredada.status_code, 401)
        self.assertEqual(heredada.get_data(), sin_cuenta.get_data())
        self._sin_codigo()

    def test_cuenta_inactiva_con_clave_mala_es_el_mismo_401(self):
        # El 403 "Cuenta inactiva o bloqueada" solo sale con la contrasena correcta
        sin_cuenta, llamadas_sin = self._login(None, correo=CORREO_SIN_CUENTA)
        for estado in ("inactivo", "bloqueado"):
            with self.subTest(estado=estado):
                r, llamadas = self._login(self._usuario(estado=estado))
                self.assertEqual(llamadas, llamadas_sin)
                self.assertEqual(r.status_code, 401)
                self.assertEqual(r.get_data(), sin_cuenta.get_data())
        self._sin_codigo()

    def test_clave_de_mas_de_72_bytes_responde_igual_con_y_sin_cuenta(self):
        # bcrypt 5 rechaza (ValueError) claves de mas de 72 bytes en los dos casos
        larga = "A" * 73
        sin_cuenta, llamadas_sin = self._login(None, correo=CORREO_SIN_CUENTA, clave=larga)
        con_cuenta, llamadas_con = self._login(self._usuario(), clave=larga)
        self.assertEqual(llamadas_sin, llamadas_con)
        self.assertEqual(sin_cuenta.status_code, 401)
        self.assertEqual(sin_cuenta.get_data(), con_cuenta.get_data())
        self._sin_codigo()

    # -- Que no se rompa el login bueno ni la migracion de NC-001 ------------------

    def test_clave_correcta_sigue_enviando_el_codigo(self):
        r, llamadas = self._login(self._usuario(), clave=CLAVE)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json(), {"message": "Codigo enviado", "email": CORREO})
        self.assertEqual(llamadas, 1)
        self.enviar_codigo.assert_called_once()

    def test_cuenta_heredada_con_clave_correcta_se_migra_a_bcrypt(self):
        r, _ = self._login(self._usuario(self.hash_heredado), clave=CLAVE)
        self.assertEqual(r.status_code, 200)
        self.dao.actualizar_password.assert_called_once()
        id_usuario, nuevo = self.dao.actualizar_password.call_args.args
        self.assertEqual(id_usuario, ID_USUARIO)
        self.assertTrue(nuevo.startswith(f"$2b${COSTO_BCRYPT}$"))


class PruebasHashDeRelleno(unittest.TestCase):
    """El hash de relleno de security/passwords.py."""

    def test_es_bcrypt_con_el_mismo_costo_que_los_reales(self):
        relleno = hash_de_relleno()
        self.assertTrue(relleno.startswith(f"$2b${COSTO_BCRYPT}$"))
        self.assertEqual(len(relleno), 60)
        self.assertEqual(relleno[:7], hash_password(CLAVE)[:7])

    def test_se_crea_una_sola_vez(self):
        # Si se creara en cada peticion, sin cuenta se pagarian dos bcrypt (hashpw + checkpw)
        with mock.patch.object(passwords.bcrypt, "hashpw", wraps=bcrypt.hashpw) as hashpw:
            self.assertEqual(hash_de_relleno(), hash_de_relleno())
            hashpw.assert_not_called()

    def test_no_acepta_claves_comunes(self):
        for clave in ("", "123456", "password", "Firulais2026!", "relleno", " "):
            with self.subTest(clave=clave):
                self.assertFalse(verificar_password(clave, hash_de_relleno()))

    def test_verificar_password_sigue_igual_con_hash_heredado(self):
        heredado = hashlib.sha256(CLAVE.encode()).hexdigest()
        self.assertTrue(verificar_password(CLAVE, heredado))
        self.assertFalse(verificar_password(CLAVE_MALA, heredado))
        self.assertTrue(verificar_password("A" * 80, hashlib.sha256(("A" * 80).encode()).hexdigest()))


if __name__ == "__main__":
    unittest.main()
