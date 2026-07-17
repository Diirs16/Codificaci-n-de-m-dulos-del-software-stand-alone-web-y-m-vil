"""
DAO (Data Access Object) para la entidad Usuario.
Implementa operaciones CRUD sobre la tabla 'usuarios'.
Equivalente al patrón DAO con PreparedStatement de JDBC.
"""

from mysql.connector import Error
from conexion.conexion_bd import ConexionBD
from modelo.usuario import Usuario


class UsuarioDAO:
    """Acceso a datos para la tabla usuarios."""

    _INSERTAR = """
        INSERT INTO usuarios (nombres, apellidos, correo, telefono,
                            password_hash, foto_perfil, estado, verificado, acepta_datos)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    _CONSULTAR_TODOS = """
        SELECT id_usuario, nombres, apellidos, correo, telefono,
            password_hash, foto_perfil, estado, verificado, acepta_datos,
            fecha_creacion, fecha_actualizacion
        FROM usuarios ORDER BY id_usuario
    """

    _CONSULTAR_POR_ID = """
        SELECT id_usuario, nombres, apellidos, correo, telefono,
            password_hash, foto_perfil, estado, verificado, acepta_datos,
            fecha_creacion, fecha_actualizacion
        FROM usuarios WHERE id_usuario = %s
    """

    _CONSULTAR_POR_CORREO = """
        SELECT id_usuario, nombres, apellidos, correo, telefono,
            password_hash, foto_perfil, estado, verificado, acepta_datos,
            fecha_creacion, fecha_actualizacion
        FROM usuarios WHERE correo = %s
    """

    _ACTUALIZAR = """
        UPDATE usuarios
        SET nombres = %s, apellidos = %s, correo = %s, telefono = %s,
            foto_perfil = %s, estado = %s, verificado = %s, acepta_datos = %s
        WHERE id_usuario = %s
    """

    _ELIMINAR = """
        DELETE FROM usuarios WHERE id_usuario = %s
    """

    _BUSCAR_POR_NOMBRE = """
        SELECT id_usuario, nombres, apellidos, correo, telefono,
            password_hash, foto_perfil, estado, verificado, acepta_datos,
            fecha_creacion, fecha_actualizacion
        FROM usuarios WHERE nombres LIKE %s OR apellidos LIKE %s
        ORDER BY nombres
    """

    def __init__(self):
        self._conexion_bd = ConexionBD()

    def _mapear_usuario(self, fila):
        """Convierte una fila del ResultSet a un objeto Usuario."""
        return Usuario(
            id_usuario=fila[0],
            nombres=fila[1],
            apellidos=fila[2],
            correo=fila[3],
            telefono=fila[4],
            password_hash=fila[5],
            foto_perfil=fila[6],
            estado=fila[7],
            verificado=bool(fila[8]),
            acepta_datos=bool(fila[9]),
            fecha_creacion=fila[10],
            fecha_actualizacion=fila[11]
        )

    def insertar(self, usuario):
        """Registra un nuevo usuario en la base de datos."""
        conexion = self._conexion_bd.obtener_conexion()
        if conexion is None:
            return False
        try:
            cursor = conexion.cursor()
            valores = (
                usuario.nombres, usuario.apellidos, usuario.correo,
                usuario.telefono, usuario.password_hash, usuario.foto_perfil,
                usuario.estado, usuario.verificado, usuario.acepta_datos
            )
            cursor.execute(self._INSERTAR, valores)
            self._conexion_bd.commit()
            usuario.id_usuario = cursor.lastrowid
            cursor.close()
            return True
        except Error as e:
            self._conexion_bd.rollback()
            print(f"[ERROR] Al insertar usuario: {e}")
            return False

    def consultar_todos(self):
        """Retorna la lista de todos los usuarios registrados."""
        conexion = self._conexion_bd.obtener_conexion()
        if conexion is None:
            return []
        try:
            cursor = conexion.cursor()
            cursor.execute(self._CONSULTAR_TODOS)
            filas = cursor.fetchall()
            usuarios = [self._mapear_usuario(fila) for fila in filas]
            cursor.close()
            return usuarios
        except Error as e:
            print(f"[ERROR] Al consultar usuarios: {e}")
            return []

    def consultar_por_id(self, id_usuario):
        """Busca un usuario por su ID."""
        conexion = self._conexion_bd.obtener_conexion()
        if conexion is None:
            return None
        try:
            cursor = conexion.cursor()
            cursor.execute(self._CONSULTAR_POR_ID, (id_usuario,))
            fila = cursor.fetchone()
            cursor.close()
            return self._mapear_usuario(fila) if fila else None
        except Error as e:
            print(f"[ERROR] Al consultar usuario por ID: {e}")
            return None

    def consultar_por_correo(self, correo):
        """Busca un usuario por su correo electrónico."""
        conexion = self._conexion_bd.obtener_conexion()
        if conexion is None:
            return None
        try:
            cursor = conexion.cursor()
            cursor.execute(self._CONSULTAR_POR_CORREO, (correo,))
            fila = cursor.fetchone()
            cursor.close()
            return self._mapear_usuario(fila) if fila else None
        except Error as e:
            print(f"[ERROR] Al consultar usuario por correo: {e}")
            return None

    def actualizar(self, usuario):
        """Actualiza la información de un usuario existente."""
        conexion = self._conexion_bd.obtener_conexion()
        if conexion is None:
            return False
        try:
            cursor = conexion.cursor()
            valores = (
                usuario.nombres, usuario.apellidos, usuario.correo,
                usuario.telefono, usuario.foto_perfil, usuario.estado,
                usuario.verificado, usuario.acepta_datos, usuario.id_usuario
            )
            cursor.execute(self._ACTUALIZAR, valores)
            self._conexion_bd.commit()
            filas_afectadas = cursor.rowcount
            cursor.close()
            return filas_afectadas > 0
        except Error as e:
            self._conexion_bd.rollback()
            print(f"[ERROR] Al actualizar usuario: {e}")
            return False

    def eliminar(self, id_usuario):
        """Elimina un usuario por su ID."""
        conexion = self._conexion_bd.obtener_conexion()
        if conexion is None:
            return False
        try:
            cursor = conexion.cursor()
            cursor.execute(self._ELIMINAR, (id_usuario,))
            self._conexion_bd.commit()
            filas_afectadas = cursor.rowcount
            cursor.close()
            return filas_afectadas > 0
        except Error as e:
            self._conexion_bd.rollback()
            print(f"[ERROR] Al eliminar usuario: {e}")
            return False

    def buscar_por_nombre(self, termino):
        """Busca usuarios cuyo nombre o apellido contenga el término."""
        conexion = self._conexion_bd.obtener_conexion()
        if conexion is None:
            return []
        try:
            cursor = conexion.cursor()
            patron = f"%{termino}%"
            cursor.execute(self._BUSCAR_POR_NOMBRE, (patron, patron))
            filas = cursor.fetchall()
            usuarios = [self._mapear_usuario(fila) for fila in filas]
            cursor.close()
            return usuarios
        except Error as e:
            print(f"[ERROR] Al buscar usuarios: {e}")
            return []
