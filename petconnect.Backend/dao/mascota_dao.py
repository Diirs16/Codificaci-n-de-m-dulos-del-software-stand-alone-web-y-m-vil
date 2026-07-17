"""
DAO (Data Access Object) para la entidad Mascota.
Implementa operaciones CRUD sobre la tabla 'mascotas'.
"""

from mysql.connector import Error
from conexion.conexion_bd import ConexionBD
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
        conexion = self._conexion_bd.obtener_conexion()
        if conexion is None:
            return False
        try:
            cursor = conexion.cursor()
            valores = (
                mascota.id_usuario, mascota.nombre, mascota.especie,
                mascota.raza, mascota.sexo, mascota.fecha_nacimiento,
                mascota.edad_aprox, mascota.color, mascota.peso,
                mascota.foto, mascota.observaciones, mascota.estado
            )
            cursor.execute(self._INSERTAR, valores)
            self._conexion_bd.commit()
            mascota.id_mascota = cursor.lastrowid
            cursor.close()
            return True
        except Error as e:
            self._conexion_bd.rollback()
            print(f"[ERROR] Al insertar mascota: {e}")
            return False

    def consultar_todos(self):
        """Retorna la lista de todas las mascotas registradas."""
        conexion = self._conexion_bd.obtener_conexion()
        if conexion is None:
            return []
        try:
            cursor = conexion.cursor()
            cursor.execute(self._CONSULTAR_TODOS)
            filas = cursor.fetchall()
            mascotas = [self._mapear_mascota(fila) for fila in filas]
            cursor.close()
            return mascotas
        except Error as e:
            print(f"[ERROR] Al consultar mascotas: {e}")
            return []

    def consultar_por_id(self, id_mascota):
        """Busca una mascota por su ID."""
        conexion = self._conexion_bd.obtener_conexion()
        if conexion is None:
            return None
        try:
            cursor = conexion.cursor()
            cursor.execute(self._CONSULTAR_POR_ID, (id_mascota,))
            fila = cursor.fetchone()
            cursor.close()
            return self._mapear_mascota(fila) if fila else None
        except Error as e:
            print(f"[ERROR] Al consultar mascota por ID: {e}")
            return None

    def consultar_por_usuario(self, id_usuario):
        """Retorna las mascotas de un usuario específico."""
        conexion = self._conexion_bd.obtener_conexion()
        if conexion is None:
            return []
        try:
            cursor = conexion.cursor()
            cursor.execute(self._CONSULTAR_POR_USUARIO, (id_usuario,))
            filas = cursor.fetchall()
            mascotas = [self._mapear_mascota(fila) for fila in filas]
            cursor.close()
            return mascotas
        except Error as e:
            print(f"[ERROR] Al consultar mascotas por usuario: {e}")
            return []

    def actualizar(self, mascota):
        """Actualiza la información de una mascota existente."""
        conexion = self._conexion_bd.obtener_conexion()
        if conexion is None:
            return False
        try:
            cursor = conexion.cursor()
            valores = (
                mascota.nombre, mascota.especie, mascota.raza, mascota.sexo,
                mascota.fecha_nacimiento, mascota.edad_aprox, mascota.color,
                mascota.peso, mascota.foto, mascota.observaciones,
                mascota.estado, mascota.id_mascota
            )
            cursor.execute(self._ACTUALIZAR, valores)
            self._conexion_bd.commit()
            filas_afectadas = cursor.rowcount
            cursor.close()
            return filas_afectadas > 0
        except Error as e:
            self._conexion_bd.rollback()
            print(f"[ERROR] Al actualizar mascota: {e}")
            return False

    def eliminar(self, id_mascota):
        """Elimina una mascota por su ID."""
        conexion = self._conexion_bd.obtener_conexion()
        if conexion is None:
            return False
        try:
            cursor = conexion.cursor()
            cursor.execute(self._ELIMINAR, (id_mascota,))
            self._conexion_bd.commit()
            filas_afectadas = cursor.rowcount
            cursor.close()
            return filas_afectadas > 0
        except Error as e:
            self._conexion_bd.rollback()
            print(f"[ERROR] Al eliminar mascota: {e}")
            return False

    def buscar_por_nombre(self, termino):
        """Busca mascotas cuyo nombre contenga el término."""
        conexion = self._conexion_bd.obtener_conexion()
        if conexion is None:
            return []
        try:
            cursor = conexion.cursor()
            cursor.execute(self._BUSCAR_POR_NOMBRE, (f"%{termino}%",))
            filas = cursor.fetchall()
            mascotas = [self._mapear_mascota(fila) for fila in filas]
            cursor.close()
            return mascotas
        except Error as e:
            print(f"[ERROR] Al buscar mascotas: {e}")
            return []
