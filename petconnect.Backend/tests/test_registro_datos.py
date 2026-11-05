"""
Pruebas de regresion de A-20 / NC-005 (item 3.1 de PRIORIDADES, parte 1: API):
la autorizacion del tratamiento de datos personales (Ley 1581 de 2012, art. 9).

- /register sin la autorizacion (sin el campo, con false, "true", 1, "si" o null)
  responde 400 sin consultar el DNS ni la BD, sin enviar correo y sin dejar un
  registro pendiente.
- /register con "acepta_datos": true guarda en el pendiente la fecha y la version
  de la politica, y /verify crea el usuario con acepta_datos=True, esa fecha y esa
  version.
- /verify no crea la cuenta si el pendiente no trae la prueba de la autorizacion.
- Usuario() ya no trae acepta_datos=True por defecto y UsuarioDAO.insertar escribe
  la fecha y la version.

No usan la base de datos real (se simula), no envian correos, no consultan el DNS
ni leen .env. El limitador del 2.6 queda apagado (_importar_api).

Ejecutar desde petconnect.Backend, con el entorno virtual activo:
    python -m unittest discover -s tests -v
"""
import os
import sys
import unittest
from datetime import datetime
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_errores import _importar_api  # noqa: E402

# Datos inventados (Ley 1581)
CORREO = "titular.prueba@ejemplo.test"
NOMBRE = "Titular Prueba"
CLAVE = "Firulais2026!"
VERSION = "1.0"
MENSAJE_400 = "Debes autorizar el tratamiento de tus datos personales para registrarte"

_SIN_CAMPO = object()   # marca: el cuerpo no trae "acepta_datos"

# Nada de esto es una autorizacion expresa: solo vale el booleano JSON true
NO_AUTORIZA = (_SIN_CAMPO, False, "true", 1, "si", None)


class PruebasAutorizacionEnElRegistro(unittest.TestCase):
    """/register y /verify con BD, DNS y correo simulados."""

    @classmethod
    def setUpClass(cls):
        cls.api = _importar_api()            # limitador apagado
        cls.cliente = cls.api.app.test_client()

    def setUp(self):
        self.codigos = []       # codigos "enviados" por correo
        parches = {
            "obtener_conexion": mock.patch.object(self.api._conexion_bd, "obtener_conexion",
                                                  return_value=mock.MagicMock()),
            "UsuarioDAO": mock.patch.object(self.api, "UsuarioDAO"),
            "hash_password": mock.patch.object(self.api, "hash_password", return_value="hash-falso"),
            "_validar_correo": mock.patch.object(self.api, "_validar_correo", return_value=(True, "")),
            "generate_token": mock.patch.object(self.api, "generate_token", return_value="token-falso"),
            "enviar_codigo": mock.patch.object(self.api, "enviar_codigo",
                                               side_effect=lambda correo, nombre, codigo, **_:
                                               self.codigos.append(codigo)),
            "enviar_bienvenida": mock.patch.object(self.api, "enviar_bienvenida"),
        }
        for nombre, parche in parches.items():
            setattr(self, nombre, parche.start())
            self.addCleanup(parche.stop)

        self.UsuarioDAO.return_value.consultar_por_correo.return_value = None   # correo libre
        self.UsuarioDAO.return_value.insertar.return_value = True

        self.api._otp_registro.descartar(CORREO)
        self.addCleanup(self.api._otp_registro.descartar, CORREO)

    def _registrar(self, acepta_datos=True):
        cuerpo = {"name": NOMBRE, "email": CORREO, "password": CLAVE}
        if acepta_datos is not _SIN_CAMPO:
            cuerpo["acepta_datos"] = acepta_datos
        return self.cliente.post("/api/auth/register", json=cuerpo)

    def _verificar(self, codigo):
        return self.cliente.post("/api/auth/verify", json={"email": CORREO, "code": codigo})

    def test_la_version_de_la_politica_la_fija_el_servidor(self):
        self.assertEqual(self.api.VERSION_POLITICA_DATOS, VERSION)

    def test_sin_autorizacion_responde_400_sin_correo_ni_pendiente(self):
        for valor in NO_AUTORIZA:
            etiqueta = "sin el campo" if valor is _SIN_CAMPO else repr(valor)
            with self.subTest(acepta_datos=etiqueta):
                r = self._registrar(valor)
                self.assertEqual(r.status_code, 400)
                self.assertEqual(r.get_json(), {"error": MENSAJE_400})
                self.assertFalse(self.api._otp_registro.tiene_pendiente(CORREO))
        # Se corta antes del DNS, de la BD y del correo
        self._validar_correo.assert_not_called()
        self.UsuarioDAO.assert_not_called()
        self.hash_password.assert_not_called()
        self.enviar_codigo.assert_not_called()

    def test_con_autorizacion_el_pendiente_guarda_fecha_y_version(self):
        antes = datetime.now().replace(microsecond=0)
        r = self._registrar(True)
        despues = datetime.now()

        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["message"], "Codigo enviado")
        self.assertEqual(len(self.codigos), 1)
        pendiente = self.api._otp_registro.vigente(CORREO)
        self.assertEqual(pendiente["version_politica_datos"], VERSION)
        fecha = pendiente["fecha_autorizacion_datos"]
        self.assertIsInstance(fecha, datetime)
        self.assertTrue(antes <= fecha <= despues, fecha)

    def test_verify_crea_el_usuario_con_autorizacion_fecha_y_version(self):
        self._registrar(True)
        fecha = self.api._otp_registro.vigente(CORREO)["fecha_autorizacion_datos"]

        r = self._verificar(self.codigos[0])

        self.assertEqual(r.status_code, 201)
        usuario = self.UsuarioDAO.return_value.insertar.call_args.args[0]
        self.assertIs(usuario.acepta_datos, True)
        self.assertEqual(usuario.fecha_autorizacion_datos, fecha)
        self.assertEqual(usuario.version_politica_datos, VERSION)

    def test_verify_sin_prueba_de_autorizacion_no_crea_la_cuenta(self):
        """Doble barrera: un pendiente sin fecha ni version nunca se vuelve cuenta."""
        for pendiente in ({"name": NOMBRE, "password_hash": "hash-falso"},
                          {"name": NOMBRE, "password_hash": "hash-falso",
                           "fecha_autorizacion_datos": datetime(2026, 11, 5, 10, 0, 0)},
                          {"name": NOMBRE, "password_hash": "hash-falso",
                           "version_politica_datos": VERSION}):
            with self.subTest(claves=sorted(pendiente)):
                codigo = self.api._otp_registro.crear(CORREO, pendiente)
                r = self._verificar(codigo)
                self.assertEqual(r.status_code, 400)
                self.assertEqual(r.get_json(), {"error": MENSAJE_400})
                self.assertFalse(self.api._otp_registro.tiene_pendiente(CORREO))
        self.UsuarioDAO.return_value.insertar.assert_not_called()
        self.generate_token.assert_not_called()


class PruebasModeloYDAO(unittest.TestCase):
    """El modelo no autoriza por defecto y el DAO guarda la prueba (sin BD real)."""

    @classmethod
    def setUpClass(cls):
        # api.py se importa primero (sin .env real): asi config/ no carga el .env
        # al importar el DAO, que ya queda en memoria.
        _importar_api()
        from dao.usuario_dao import UsuarioDAO
        from modelo.usuario import Usuario
        cls.UsuarioDAO = UsuarioDAO
        cls.Usuario = Usuario

    def test_usuario_nuevo_no_autoriza_por_defecto(self):
        usuario = self.Usuario(nombres="Titular", correo=CORREO, password_hash="hash-falso")
        self.assertIs(usuario.acepta_datos, False)
        self.assertIsNone(usuario.fecha_autorizacion_datos)
        self.assertIsNone(usuario.version_politica_datos)

    def test_insertar_escribe_fecha_y_version_parametrizadas(self):
        fecha = datetime(2026, 11, 5, 10, 30, 0)
        usuario = self.Usuario(nombres="Titular", apellidos="Prueba", correo=CORREO,
                               password_hash="hash-falso", verificado=True, acepta_datos=True,
                               fecha_autorizacion_datos=fecha, version_politica_datos=VERSION)
        dao = self.UsuarioDAO()
        conexion_bd = mock.MagicMock()
        cursor = conexion_bd.obtener_conexion.return_value.cursor.return_value
        cursor.lastrowid = 7
        dao._conexion_bd = conexion_bd      # BD simulada: nunca se toca la real

        self.assertTrue(dao.insertar(usuario))

        sql, valores = cursor.execute.call_args.args
        self.assertIn("fecha_autorizacion_datos", sql)
        self.assertIn("version_politica_datos", sql)
        self.assertEqual(sql.count("%s"), len(valores))      # todo parametrizado
        self.assertEqual(valores[-3:], (True, fecha, VERSION))


if __name__ == "__main__":
    unittest.main()
