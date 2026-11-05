"""
Pruebas de regresion de NC-006 / A-04 y A-05 (item 2.6 de PRIORIDADES): las rutas
de autenticacion aceptan 5 peticiones por minuto por IP; la 6.a responde 429.
No usan la base de datos real (se simula apagada), no envian correos, no consultan
el DNS ni leen .env.

Ejecutar desde petconnect.Backend, con el entorno virtual activo:
    python -m unittest discover -s tests -v
"""
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_errores import _importar_api  # noqa: E402

LIMITE = 5                                  # lo que pide la auditoria (5/min por IP)
IP_ATACANTE = "203.0.113.10"                # IP de documentacion (RFC 5737), inventada
IP_OTRA = "203.0.113.20"
CORREO_PRUEBA = "laura@ejemplo.test"        # inventado
MENSAJE_429 = "Demasiadas peticiones. Espera un minuto e intenta de nuevo"

# Con cuerpo vacio todas responden 400 sin tocar BD, DNS ni correo
RUTAS_LIMITADAS = (
    "/api/auth/login",
    "/api/auth/login/verify",
    "/api/auth/register",
    "/api/auth/verify",
    "/api/utils/validar-correo",
)


class PruebasLimiteDePeticiones(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.api = _importar_api()          # lo deja apagado; aqui se enciende
        cls.cliente = cls.api.app.test_client()

    def setUp(self):
        parches = (
            mock.patch.object(self.api._conexion_bd, "obtener_conexion", return_value=None),
            mock.patch.object(self.api, "enviar_codigo"),
            mock.patch.object(self.api, "_validar_correo", return_value=(False, "correo rechazado en la prueba")),
        )
        for parche in parches:
            parche.start()
            self.addCleanup(parche.stop)

        limiter = getattr(self.api, "limiter", None)   # el api.py anterior al 2.6 no lo tiene
        if limiter is not None:
            limiter.enabled = True
            limiter.reset()                     # cada prueba empieza con el contador en 0
            self.addCleanup(limiter.reset)
            self.addCleanup(setattr, limiter, "enabled", False)

    def _post(self, ruta, ip=IP_ATACANTE):
        return self.cliente.post(ruta, json={}, environ_base={"REMOTE_ADDR": ip})

    def test_la_sexta_peticion_en_un_minuto_responde_429(self):
        for ruta in RUTAS_LIMITADAS:
            with self.subTest(ruta=ruta):
                for i in range(LIMITE):
                    r = self._post(ruta)
                    self.assertNotEqual(r.status_code, 429, f"peticion {i + 1}")
                r = self._post(ruta)
                self.assertEqual(r.status_code, 429)
                self.assertEqual(r.get_json(), {"error": MENSAJE_429})
                self.assertTrue(r.headers.get("Retry-After"))     # cuantos segundos esperar

    def test_otra_ip_no_queda_bloqueada(self):
        for _ in range(LIMITE + 1):
            self._post("/api/auth/login")
        self.assertEqual(self._post("/api/auth/login").status_code, 429)
        self.assertNotEqual(self._post("/api/auth/login", ip=IP_OTRA).status_code, 429)

    def test_cada_ruta_lleva_su_propia_cuenta(self):
        # Gastar el login no impide verificar el codigo (es el paso siguiente)
        for _ in range(LIMITE + 1):
            self._post("/api/auth/login")
        self.assertNotEqual(self._post("/api/auth/login/verify").status_code, 429)

    def test_el_correo_que_se_envia_queda_limitado(self):
        # A-05: no se pueden pedir codigos (correos) sin fin a la misma direccion
        cuerpo = {"name": "Laura Gomez", "email": CORREO_PRUEBA, "password": "Firulais2026!",
                  "acepta_datos": True}   # NC-005 (item 3.1)
        codigos = [self.cliente.post("/api/auth/register", json=cuerpo,
                                     environ_base={"REMOTE_ADDR": IP_ATACANTE}).status_code
                   for _ in range(LIMITE + 3)]
        self.assertEqual(codigos[LIMITE:], [429, 429, 429])
        self.assertEqual(self.api._validar_correo.call_count, LIMITE)   # las bloqueadas no avanzan
        self.assertNotIn(CORREO_PRUEBA, str(codigos))

    def test_las_rutas_publicas_no_tienen_limite(self):
        with self.assertLogs(self.api.app.logger, "ERROR"):      # BD simulada apagada → 503
            for _ in range(LIMITE + 3):
                r = self.cliente.get("/api/productos", environ_base={"REMOTE_ADDR": IP_ATACANTE})
                self.assertEqual(r.status_code, 503)


if __name__ == "__main__":
    unittest.main()
