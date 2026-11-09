"""
DAO (Data Access Object) para la entidad Mascota.
Implementa operaciones CRUD sobre la tabla 'mascotas'.
Item 4.5 (A-11, NC-003): cada metodo pide una conexion del pool con
conexion_y_cursor y, al salir del with, cierra el cursor y la devuelve.
Item 4.15: si la BD falla, el error SUBE a quien llamo (la API lo responde
como 503 o 500; la consola muestra un aviso). Antes se imprimia el mensaje de
MySQL, que puede traer datos personales (Ley 1581), y se devolvia None, [] o
False: sin BD la API habria dicho "no encontrado" o una lista vacia.
Las escrituras hacen rollback() antes de dejar subir el error.
"""

from mysql.connector import Error
from conexion.conexion_bd import ConexionBD, conexion_y_cursor
from modelo.mascota import Mascota


class MascotaDAO:
    """Acceso a datos para la tabla mascotas."""

    _INSERTAR = """
        INSERT INTO mascotas (id_usuario, nombre, especie, raza, sexo,
                            fecha_nacimiento, edad_aprox, color, peso,
                            foto, observaciones, estado)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    _CONSULTAR_TODOS = """
        SELECT m.id_mascota, m.id_usuario, m.nombre, m.especie, m.raza,
            m.sexo, m.fecha_nacimiento, m.edad_aprox, m.color, m.peso,
            m.foto, m.observaciones, m.estado, m.fecha_registro
        FROM mascotas m ORDER BY m.id_mascota
    """

    _CONSULTAR_POR_ID = """
        SELECT id_mascota, id_usuario, nombre, especie, raza, sexo,
            fecha_nacimiento, edad_aprox, color, peso, foto,
            observaciones, estado, fecha_registro
        FROM mascotas WHERE id_mascota = %s
    """

    _CONSULTAR_POR_USUARIO = """
        SELECT id_mascota, id_usuario, nombre, especie, raza, sexo,
            fecha_nacimiento, edad_aprox, color, peso, foto,
            observaciones, estado, fecha_registro
        FROM mascotas WHERE id_usuario = %s ORDER BY nombre
    """

    _ACTUALIZAR = """
        UPDATE mascotas
        SET nombre = %s, especie = %s, raza = %s, sexo = %s,
            fecha_nacimiento = %s, edad_aprox = %s, color = %s,
            peso = %s, foto = %s, observaciones = %s, estado = %s
        WHERE id_mascota = %s
    """

    _ELIMINAR = """
        DELETE FROM mascotas WHERE id_mascota = %s
    """

    _BUSCAR_POR_NOMBRE = """
        SELECT id_mascota, id_usuario, nombre, especie, raza, sexo,
            fecha_nacimiento, edad_aprox, color, peso, foto,
            observaciones, estado, fecha_registro
        FROM mascotas WHERE nombre LIKE %s ORDER BY nombre
    """

    def __init__(self):
        self._conexion_bd = ConexionBD()

    def _mapear_mascota(self, fila):
        """Convierte una fila del ResultSet a un objeto Mascota."""
        return Mascota(
            id_mascota=fila[0],
            id_usuario=fila[1],
            nombre=fila[2],
            especie=fila[3],
            raza=fila[4],
            sexo=fila[5],
            fecha_nacimiento=fila[6],
            edad_aprox=fila[7],
            color=fila[8],
            peso=fila[9],
            foto=fila[10],
            observaciones=fila[11],
            estado=fila[12],
            fecha_registro=fila[13]
        )

    def insertar(self, mascota):
        """Registra una nueva mascota en la base de datos."""
        with conexion_y_cursor(self._conexion_bd) as (conexion, cursor):
            valores = (
                mascota.id_usuario, mascota.nombre, mascota.especie,
                mascota.raza, mascota.sexo, mascota.fecha_nacimiento,
                mascota.edad_aprox, mascota.color, mascota.peso,
                mascota.foto, mascota.observaciones, mascota.estado
            )
            try:
                cursor.execute(self._INSERTAR, valores)
                conexion.commit()
            except Error:
                conexion.rollback()
                raise
            mascota.id_mascota = cursor.lastrowid
        return True

    def consultar_todos(self):
        """Retorna la lista de todas las mascotas registradas."""
        with conexion_y_cursor(self._conexion_bd) as (conexion, cursor):
            cursor.execute(self._CONSULTAR_TODOS)
            filas = cursor.fetchall()
            mascotas = [self._mapear_mascota(fila) for fila in filas]
        return mascotas

    def consultar_por_id(self, id_mascota):
        """Busca una mascota por su ID."""
        with conexion_y_cursor(self._conexion_bd) as (conexion, cursor):
            cursor.execute(self._CONSULTAR_POR_ID, (id_mascota,))
            fila = cursor.fetchone()
        return self._mapear_mascota(fila) if fila else None

    def consultar_por_usuario(self, id_usuario):
        """Retorna las mascotas de un usuario específico."""
        with conexion_y_cursor(self._conexion_bd) as (conexion, cursor):
            cursor.execute(self._CONSULTAR_POR_USUARIO, (id_usuario,))
            filas = cursor.fetchall()
            mascotas = [self._mapear_mascota(fila) for fila in filas]
        return mascotas

    def actualizar(self, mascota):
        """Actualiza la información de una mascota existente."""
        with conexion_y_cursor(self._conexion_bd) as (conexion, cursor):
            valores = (
                mascota.nombre, mascota.especie, mascota.raza, mascota.sexo,
                mascota.fecha_nacimiento, mascota.edad_aprox, mascota.color,
                mascota.peso, mascota.foto, mascota.observaciones,
                mascota.estado, mascota.id_mascota
            )
            try:
                cursor.execute(self._ACTUALIZAR, valores)
                conexion.commit()
            except Error:
                conexion.rollback()
                raise
            filas_afectadas = cursor.rowcount
        return filas_afectadas > 0

    def eliminar(self, id_mascota):
        """Elimina una mascota por su ID."""
        with conexion_y_cursor(self._conexion_bd) as (conexion, cursor):
            try:
                cursor.execute(self._ELIMINAR, (id_mascota,))
                conexion.commit()
            except Error:
                conexion.rollback()
                raise
            filas_afectadas = cursor.rowcount
        return filas_afectadas > 0

    def buscar_por_nombre(self, termino):
        """Busca mascotas cuyo nombre contenga el término."""
        with conexion_y_cursor(self._conexion_bd) as (conexion, cursor):
            cursor.execute(self._BUSCAR_POR_NOMBRE, (f"%{termino}%",))
            filas = cursor.fetchall()
            mascotas = [self._mapear_mascota(fila) for fila in filas]
        return mascotas
