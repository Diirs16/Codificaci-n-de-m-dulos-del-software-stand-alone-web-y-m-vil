"""
DAO para la tabla 'solicitudes' (item 3.6 de PRIORIDADES, A-21): solicitudes de
adopcion y mensajes de contacto que una persona envia con su sesion iniciada.

A diferencia de los DAO mas viejos, este NO se traga los errores de la BD: los deja
subir para que la API responda 503 (sin conexion) o 500 con su manejador global, y
no un "todo bien" falso. Es lo que pide el item 4.15 para los demas DAO.
Nunca imprime el mensaje ni el telefono (son datos personales, Ley 1581).
"""

from conexion.conexion_bd import ConexionBD, conexion_y_cursor


class SolicitudDAO:
    """Acceso a datos para la tabla solicitudes."""

    # Solo una mascota en adopcion puede recibir solicitudes. Se devuelve el dueno
    # para que la API no deje pedir la mascota propia.
    _DUENO_MASCOTA_EN_ADOPCION = """
        SELECT id_usuario FROM mascotas
        WHERE id_mascota = %s AND estado = 'en_adopcion'
    """

    _INSERTAR = """
        INSERT INTO solicitudes (id_usuario, tipo, id_mascota, telefono, mensaje,
                                 version_politica_datos, fecha_envio)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """

    def __init__(self):
        self._conexion_bd = ConexionBD()

    def dueno_de_mascota_en_adopcion(self, id_mascota):
        """id_usuario del dueno si la mascota existe y esta en adopcion; None si no."""
        # Sin BD, conexion_y_cursor lanza InterfaceError (la API contesta 503)
        with conexion_y_cursor(self._conexion_bd) as (conexion, cursor):
            cursor.execute(self._DUENO_MASCOTA_EN_ADOPCION, (id_mascota,))
            fila = cursor.fetchone()
        return fila[0] if fila else None

    def insertar(self, id_usuario, tipo, id_mascota, telefono, mensaje, version, fecha):
        """Guarda la solicitud y devuelve su id. Si la BD falla, deshace y deja subir el error."""
        with conexion_y_cursor(self._conexion_bd) as (conexion, cursor):
            try:
                cursor.execute(self._INSERTAR, (id_usuario, tipo, id_mascota, telefono, mensaje,
                                                version, fecha))
                conexion.commit()
            except Exception:
                conexion.rollback()
                raise
            return cursor.lastrowid
