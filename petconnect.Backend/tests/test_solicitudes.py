"""
Pruebas de regresion de A-21 (item 3.6 de PRIORIDADES): envio real de la solicitud
de adopcion y del mensaje de contacto.

- POST /api/solicitudes/adopcion y /api/solicitudes/contacto exigen token (401 sin
  el) y validan el mensaje (10 a 1000 caracteres), la mascota y el telefono opcional
  (solo adopcion) ANTES de tocar la BD.
- Solo una cuenta activa con la autorizacion de datos de la version VIGENTE de la
  politica (1.1) puede enviar: un token de antes del cambio vale 24 h, asi que la
  ruta revisa la cuenta en la BD (403 con "requiere_autorizacion": true si no).
- Solo mascotas en adopcion (404 igual que la ficha) y nunca la propia (400).
- 201 solo si la fila se guardo, con el usuario del TOKEN (no del cuerpo), la fecha
  y la version de la politica que acepto la cuenta. Contacto no guarda mascota ni
  telefono. Si la BD falla no dice "enviada" y los logs no llevan el mensaje ni el
  telefono (Ley 1581).
- SolicitudDAO: SQL parametrizado, commit/rollback y los errores de la BD suben.

No usan la base de datos real (se simula), no envian correos ni leen .env. El
limitador queda apagado (_importar_api); tests/test_limite.py prueba el de estas rutas.
La prueba con MariaDB real esta en tests/test_esquema.py (PETCONNECT_PRUEBA_BD=1).

Ejecutar desde petconnect.Backend, con el entorno virtual activo:
    python -m unittest discover -s tests -v
"""
import os
import sys
import unittest
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mysql.connector import errors as errores_bd  # noqa: E402

from test_errores import _importar_api  # noqa: E402

# Datos inventados (Ley 1581)
ID_USUARIO = 7
ID_DUENO = 5
ID_MASCOTA = 3
ID_SOLICITUD = 42
CORREO = "persona.adopta@ejemplo.test"
MENSAJE = "Hola, me gustaria conocer a Luna este fin de semana."
TELEFONO = "+57 300 000 0000"
VERSION = "1.1"
FECHA_AUTORIZACION = datetime(2026, 11, 7, 9, 0, 0)

ADOPCION = "/api/solicitudes/adopcion"
CONTACTO = "/api/solicitudes/contacto"
RUTAS = (ADOPCION, CONTACTO)

MENSAJE_403 = ("Para enviar tu solicitud debes autorizar la versión vigente de la política de "
               "datos. Cierra sesión y vuelve a iniciarla")


def _usuario(acepta_datos=True, version=VERSION, estado="activo"):
    """Usuario falso con los campos que mira la API (como los deja _mapear_usuario)."""
    return SimpleNamespace(
        id_usuario=ID_USUARIO, nombres="Persona", apellidos="Adopta", correo=CORREO,
        estado=estado, acepta_datos=acepta_datos,
        fecha_autorizacion_datos=FECHA_AUTORIZACION if acepta_datos else None,
        version_politica_datos=version if acepta_datos else None,
    )


def _cuerpo(ruta, **cambios):
    cuerpo = {"mensaje": MENSAJE}
    if ruta == ADOPCION:
        cuerpo.update(id_mascota=ID_MASCOTA, telefono=TELEFONO)
    cuerpo.update(cambios)
    return cuerpo


class PruebasEnvioDeSolicitudes(unittest.TestCase):
    """Rutas con BD y DAO simulados."""

    @classmethod
    def setUpClass(cls):
        cls.api = _importar_api()
        cls.cliente = cls.api.app.test_client()

    def setUp(self):
        parches = {
            "obtener_conexion": mock.patch.object(self.api._conexion_bd, "obtener_conexion",
                                                  return_value=mock.MagicMock()),
            "UsuarioDAO": mock.patch.object(self.api, "UsuarioDAO"),
            "SolicitudDAO": mock.patch.object(self.api, "SolicitudDAO"),
        }
        for nombre, parche in parches.items():
            setattr(self, nombre, parche.start())
            self.addCleanup(parche.stop)
        self.usuarios = self.UsuarioDAO.return_value
        self.usuarios.consultar_por_id.return_value = _usuario()
        self.solicitudes = self.SolicitudDAO.return_value
        self.solicitudes.dueno_de_mascota_en_adopcion.return_value = ID_DUENO
        self.solicitudes.insertar.return_value = ID_SOLICITUD

    def _token(self, id_usuario=ID_USUARIO):
        return {"Authorization": f"Bearer {self.api.generate_token(id_usuario, CORREO)}"}

    def _enviar(self, ruta, cuerpo=None, token=True):
        cabeceras = self._token() if token else {}
        return self.cliente.post(ruta, json=_cuerpo(ruta) if cuerpo is None else cuerpo,
                                 headers=cabeceras)

    def _nada_guardado(self):
        self.solicitudes.insertar.assert_not_called()

    def _sin_tocar_la_bd(self):
        self._nada_guardado()
        self.usuarios.consultar_por_id.assert_not_called()
        self.solicitudes.dueno_de_mascota_en_adopcion.assert_not_called()

    # -- Sesion -----------------------------------------------------------------

    def test_sin_token_responde_401(self):
        for ruta in RUTAS:
            with self.subTest(ruta=ruta):
                r = self._enviar(ruta, token=False)
                self.assertEqual(r.status_code, 401)
                self._sin_tocar_la_bd()

    def test_token_invalido_responde_401(self):
        for ruta in RUTAS:
            with self.subTest(ruta=ruta):
                r = self.cliente.post(ruta, json=_cuerpo(ruta),
                                      headers={"Authorization": "Bearer token-inventado"})
                self.assertEqual(r.status_code, 401)
                self._sin_tocar_la_bd()

    def test_cuenta_sin_autorizacion_vigente_responde_403_sin_guardar(self):
        cuentas = {
            "en 0 (antes del 3.1)": _usuario(acepta_datos=False),
            "acepto la 1.0 (antes del 3.6)": _usuario(version="1.0"),
        }
        for ruta in RUTAS:
            for caso, usuario in cuentas.items():
                with self.subTest(ruta=ruta, cuenta=caso):
                    self.usuarios.consultar_por_id.return_value = usuario
                    r = self._enviar(ruta)
                    self.assertEqual(r.status_code, 403)
                    self.assertEqual(r.get_json(), {"error": MENSAJE_403,
                                                    "requiere_autorizacion": True})
                    self._nada_guardado()

    def test_cuenta_inactiva_o_inexistente_no_envia(self):
        for ruta in RUTAS:
            with self.subTest(ruta=ruta, cuenta="bloqueada"):
                self.usuarios.consultar_por_id.return_value = _usuario(estado="bloqueado")
                r = self._enviar(ruta)
                self.assertEqual(r.status_code, 403)
                self.assertNotIn("requiere_autorizacion", r.get_json())
            with self.subTest(ruta=ruta, cuenta="borrada"):
                self.usuarios.consultar_por_id.return_value = None
                self.assertEqual(self._enviar(ruta).status_code, 404)
        self._nada_guardado()

    # -- Validaciones (antes de la BD) ------------------------------------------

    def test_mensaje_invalido_responde_400_sin_tocar_la_bd(self):
        invalidos = {
            "vacio": "", "solo espacios": " " * 20, "corto": "Hola",
            "largo": "a" * 1001, "numero": 12345678901, "null": None, "lista": [MENSAJE],
        }
        for ruta in RUTAS:
            for caso, valor in invalidos.items():
                with self.subTest(ruta=ruta, mensaje=caso):
                    r = self._enviar(ruta, _cuerpo(ruta, mensaje=valor))
                    self.assertEqual(r.status_code, 400)
                    self.assertIn("mensaje", r.get_json()["error"])
                    self._sin_tocar_la_bd()
            with self.subTest(ruta=ruta, mensaje="sin el campo"):
                cuerpo = _cuerpo(ruta)
                del cuerpo["mensaje"]
                self.assertEqual(self._enviar(ruta, cuerpo).status_code, 400)
                self._sin_tocar_la_bd()

    def test_mensaje_en_los_limites_se_acepta_recortado(self):
        for valor in ("a" * 10, "a" * 1000):
            with self.subTest(largo=len(valor)):
                r = self._enviar(CONTACTO, {"mensaje": f"   {valor}\n"})
                self.assertEqual(r.status_code, 201)
                self.assertEqual(self.solicitudes.insertar.call_args.args[4], valor)

    def test_mascota_invalida_responde_400(self):
        for valor in ("3", 0, -1, True, 3.5, None, [3]):
            with self.subTest(id_mascota=repr(valor)):
                r = self._enviar(ADOPCION, _cuerpo(ADOPCION, id_mascota=valor))
                self.assertEqual(r.status_code, 400)
                self._sin_tocar_la_bd()
        cuerpo = _cuerpo(ADOPCION)
        del cuerpo["id_mascota"]
        self.assertEqual(self._enviar(ADOPCION, cuerpo).status_code, 400)
        self._sin_tocar_la_bd()

    def test_telefono_invalido_responde_400(self):
        for valor in ("300-000-0000", "abc0000000", "123456", "1" * 16, "57+3000000000",
                      "++573000000000", "+57 300 000 0000 0000", 3000000000, None):
            with self.subTest(telefono=repr(valor)):
                r = self._enviar(ADOPCION, _cuerpo(ADOPCION, telefono=valor))
                self.assertEqual(r.status_code, 400)
                self._sin_tocar_la_bd()

    def test_telefono_es_opcional(self):
        for valor, guardado in (("", None), ("   ", None), ("3000000000", "3000000000"),
                                (TELEFONO, TELEFONO)):
            with self.subTest(telefono=repr(valor)):
                r = self._enviar(ADOPCION, _cuerpo(ADOPCION, telefono=valor))
                self.assertEqual(r.status_code, 201)
                self.assertEqual(self.solicitudes.insertar.call_args.args[3], guardado)
        cuerpo = _cuerpo(ADOPCION)
        del cuerpo["telefono"]
        self.assertEqual(self._enviar(ADOPCION, cuerpo).status_code, 201)

    # -- Mascota ------------------------------------------------------------------

    def test_mascota_que_no_esta_en_adopcion_responde_404(self):
        self.solicitudes.dueno_de_mascota_en_adopcion.return_value = None
        r = self._enviar(ADOPCION)
        self.assertEqual(r.status_code, 404)
        self.assertEqual(r.get_json(), {"error": "Mascota no encontrada"})
        self.solicitudes.dueno_de_mascota_en_adopcion.assert_called_once_with(ID_MASCOTA)
        self._nada_guardado()

    def test_no_se_puede_pedir_la_propia_mascota(self):
        self.solicitudes.dueno_de_mascota_en_adopcion.return_value = ID_USUARIO
        r = self._enviar(ADOPCION)
        self.assertEqual(r.status_code, 400)
        self.assertIn("propia mascota", r.get_json()["error"])
        self._nada_guardado()

    # -- Envio correcto ---------------------------------------------------------

    def _assert_fecha_de_ahora(self, fecha):
        self.assertIsInstance(fecha, datetime)
        self.assertEqual(fecha.microsecond, 0)
        self.assertLess(abs(datetime.now() - fecha), timedelta(minutes=1))

    def test_adopcion_guarda_usuario_mascota_fecha_y_version(self):
        r = self._enviar(ADOPCION)
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.get_json(), {"message": "Solicitud enviada", "id": ID_SOLICITUD})
        self.usuarios.consultar_por_id.assert_called_once_with(ID_USUARIO)
        self.solicitudes.insertar.assert_called_once()
        args = self.solicitudes.insertar.call_args.args
        self.assertEqual(args[:6], (ID_USUARIO, "adopcion", ID_MASCOTA, TELEFONO, MENSAJE, VERSION))
        self._assert_fecha_de_ahora(args[6])

    def test_contacto_no_guarda_mascota_ni_telefono(self):
        r = self._enviar(CONTACTO, {"mensaje": MENSAJE, "id_mascota": ID_MASCOTA,
                                    "telefono": TELEFONO})
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.get_json(), {"message": "Mensaje enviado", "id": ID_SOLICITUD})
        self.solicitudes.dueno_de_mascota_en_adopcion.assert_not_called()
        args = self.solicitudes.insertar.call_args.args
        self.assertEqual(args[:6], (ID_USUARIO, "contacto", None, None, MENSAJE, VERSION))
        self._assert_fecha_de_ahora(args[6])

    def test_el_usuario_sale_del_token_y_no_del_cuerpo(self):
        for ruta in RUTAS:
            with self.subTest(ruta=ruta):
                r = self._enviar(ruta, _cuerpo(ruta, id_usuario=99, version_politica_datos="9.9"))
                self.assertEqual(r.status_code, 201)
                args = self.solicitudes.insertar.call_args.args
                self.assertEqual((args[0], args[5]), (ID_USUARIO, VERSION))

    # -- Fallos de la BD ----------------------------------------------------------

    def test_si_la_bd_falla_no_dice_enviada_ni_registra_el_mensaje(self):
        fallos = {
            500: errores_bd.IntegrityError(f"Duplicate entry '{TELEFONO}' {MENSAJE}"),
            503: errores_bd.OperationalError(f"Lost connection {MENSAJE}"),
        }
        for ruta in RUTAS:
            for codigo, error in fallos.items():
                with self.subTest(ruta=ruta, codigo=codigo):
                    self.solicitudes.insertar.side_effect = error
                    with self.assertLogs(self.api.app.logger, "ERROR") as logs:
                        r = self._enviar(ruta)
                    self.assertEqual(r.status_code, codigo)
                    cuerpo = r.get_data(as_text=True)
                    self.assertNotIn("enviad", cuerpo.lower())
                    for dato in (MENSAJE, TELEFONO, CORREO):
                        self.assertNotIn(dato, cuerpo)
                        self.assertNotIn(dato, "\n".join(logs.output))


class PruebasSolicitudDAO(unittest.TestCase):
    """SQL parametrizado y manejo de la transaccion, con una conexion simulada."""

    def setUp(self):
        from dao.solicitud_dao import SolicitudDAO
        self.conexion = mock.MagicMock()
        self.cursor = self.conexion.cursor.return_value
        self.dao = SolicitudDAO()
        self.bd = mock.patch.object(self.dao, "_conexion_bd")
        self.conexion_bd = self.bd.start()
        self.addCleanup(self.bd.stop)
        self.conexion_bd.obtener_conexion.return_value = self.conexion

    def test_insertar_usa_parametros_y_confirma(self):
        fecha = datetime(2026, 11, 7, 10, 0, 0)
        self.cursor.lastrowid = ID_SOLICITUD
        self.assertEqual(self.dao.insertar(ID_USUARIO, "adopcion", ID_MASCOTA, TELEFONO,
                                           MENSAJE, VERSION, fecha), ID_SOLICITUD)
        sql, params = self.cursor.execute.call_args.args
        self.assertIn("INSERT INTO solicitudes", " ".join(sql.split()))
        self.assertNotIn(MENSAJE, sql)
        self.assertEqual(params, (ID_USUARIO, "adopcion", ID_MASCOTA, TELEFONO, MENSAJE,
                                  VERSION, fecha))
        # Item 4.5: commit sobre la conexion prestada, que despues se devuelve al pool
        self.conexion.commit.assert_called_once()
        self.cursor.close.assert_called_once()
        self.conexion.close.assert_called_once()

    def test_insertar_deshace_y_deja_subir_el_error(self):
        self.cursor.execute.side_effect = errores_bd.IntegrityError("falla de prueba")
        with self.assertRaises(errores_bd.IntegrityError):
            self.dao.insertar(ID_USUARIO, "contacto", None, None, MENSAJE, VERSION, datetime.now())
        self.conexion.rollback.assert_called_once()
        self.conexion.commit.assert_not_called()
        self.cursor.close.assert_called_once()
        self.conexion.close.assert_called_once()      # devuelta aunque haya error

    def test_dueno_solo_de_mascotas_en_adopcion(self):
        self.cursor.fetchone.return_value = (ID_DUENO,)
        self.assertEqual(self.dao.dueno_de_mascota_en_adopcion(ID_MASCOTA), ID_DUENO)
        sql, params = self.cursor.execute.call_args.args
        self.assertIn("estado = 'en_adopcion'", sql)
        self.assertEqual(params, (ID_MASCOTA,))
        self.cursor.fetchone.return_value = None
        self.assertIsNone(self.dao.dueno_de_mascota_en_adopcion(ID_MASCOTA))

    def test_sin_conexion_lanza_error_de_bd(self):
        self.conexion_bd.obtener_conexion.return_value = None
        with self.assertRaises(errores_bd.InterfaceError):
            self.dao.dueno_de_mascota_en_adopcion(ID_MASCOTA)


if __name__ == "__main__":
    unittest.main()
