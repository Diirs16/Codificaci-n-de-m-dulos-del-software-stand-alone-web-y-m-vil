"""
DAO (Data Access Object) para la entidad ProveedorServicio.
Implementa operaciones CRUD sobre la tabla 'proveedores_servicio'.
"""

from mysql.connector import Error
from conexion.conexion_bd import ConexionBD
from modelo.proveedor_servicio import ProveedorServicio


class ProveedorDAO:
    """Acceso a datos para la tabla proveedores_servicio."""

    _INSERTAR = """
        INSERT INTO proveedores_servicio (nombre, tipo_documento, numero_documento,
                                        telefono, correo, direccion, ciudad,
                                        descripcion, horario, atiende_24_7,
                                        latitud, longitud, activo)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    _CONSULTAR_TODOS = """
        SELECT id_proveedor, nombre, tipo_documento, numero_documento,
            telefono, correo, direccion, ciudad, descripcion,
            horario, atiende_24_7, latitud, longitud, activo
        FROM proveedores_servicio ORDER BY id_proveedor
    """

    _CONSULTAR_POR_ID = """
        SELECT id_proveedor, nombre, tipo_documento, numero_documento,
            telefono, correo, direccion, ciudad, descripcion,
            horario, atiende_24_7, latitud, longitud, activo
        FROM proveedores_servicio WHERE id_proveedor = %s
    """

    _ACTUALIZAR = """
        UPDATE proveedores_servicio
        SET nombre = %s, tipo_documento = %s, numero_documento = %s,
            telefono = %s, correo = %s, direccion = %s, ciudad = %s,
            descripcion = %s, horario = %s, atiende_24_7 = %s,
            latitud = %s, longitud = %s, activo = %s
        WHERE id_proveedor = %s
    """

    _ELIMINAR = """
        DELETE FROM proveedores_servicio WHERE id_proveedor = %s
    """

    _BUSCAR_POR_NOMBRE = """
        SELECT id_proveedor, nombre, tipo_documento, numero_documento,
            telefono, correo, direccion, ciudad, descripcion,
            horario, atiende_24_7, latitud, longitud, activo
        FROM proveedores_servicio WHERE nombre LIKE %s ORDER BY nombre
    """

    _CONSULTAR_POR_CIUDAD = """
        SELECT id_proveedor, nombre, tipo_documento, numero_documento,
            telefono, correo, direccion, ciudad, descripcion,
            horario, atiende_24_7, latitud, longitud, activo
        FROM proveedores_servicio WHERE ciudad = %s AND activo = TRUE
        ORDER BY nombre
    """

    def __init__(self):
        self._conexion_bd = ConexionBD()

    def _mapear_proveedor(self, fila):
        """Convierte una fila del ResultSet a un objeto ProveedorServicio."""
        return ProveedorServicio(
            id_proveedor=fila[0],
            nombre=fila[1],
            tipo_documento=fila[2],
            numero_documento=fila[3],
            telefono=fila[4],
            correo=fila[5],
            direccion=fila[6],
            ciudad=fila[7],
            descripcion=fila[8],
            horario=fila[9],
            atiende_24_7=bool(fila[10]),
            latitud=float(fila[11]) if fila[11] else None,
            longitud=float(fila[12]) if fila[12] else None,
            activo=bool(fila[13])
        )

    def insertar(self, proveedor):
        """Registra un nuevo proveedor de servicios."""
        conexion = self._conexion_bd.obtener_conexion()
        if conexion is None:
            return False
        try:
            cursor = conexion.cursor()
            valores = (
                proveedor.nombre, proveedor.tipo_documento,
                proveedor.numero_documento, proveedor.telefono,
                proveedor.correo, proveedor.direccion, proveedor.ciudad,
                proveedor.descripcion, proveedor.horario,
                proveedor.atiende_24_7, proveedor.latitud,
                proveedor.longitud, proveedor.activo
            )
            cursor.execute(self._INSERTAR, valores)
            self._conexion_bd.commit()
            proveedor.id_proveedor = cursor.lastrowid
            cursor.close()
            return True
        except Error as e:
            self._conexion_bd.rollback()
            print(f"[ERROR] Al insertar proveedor: {e}")
            return False

    def consultar_todos(self):
        """Retorna la lista de todos los proveedores."""
        conexion = self._conexion_bd.obtener_conexion()
        if conexion is None:
            return []
        try:
            cursor = conexion.cursor()
            cursor.execute(self._CONSULTAR_TODOS)
            filas = cursor.fetchall()
            proveedores = [self._mapear_proveedor(fila) for fila in filas]
            cursor.close()
            return proveedores
        except Error as e:
            print(f"[ERROR] Al consultar proveedores: {e}")
            return []

    def consultar_por_id(self, id_proveedor):
        """Busca un proveedor por su ID."""
        conexion = self._conexion_bd.obtener_conexion()
        if conexion is None:
            return None
        try:
            cursor = conexion.cursor()
            cursor.execute(self._CONSULTAR_POR_ID, (id_proveedor,))
            fila = cursor.fetchone()
            cursor.close()
            return self._mapear_proveedor(fila) if fila else None
        except Error as e:
            print(f"[ERROR] Al consultar proveedor por ID: {e}")
            return None

    def actualizar(self, proveedor):
        """Actualiza la información de un proveedor existente."""
        conexion = self._conexion_bd.obtener_conexion()
        if conexion is None:
            return False
        try:
            cursor = conexion.cursor()
            valores = (
                proveedor.nombre, proveedor.tipo_documento,
                proveedor.numero_documento, proveedor.telefono,
                proveedor.correo, proveedor.direccion, proveedor.ciudad,
                proveedor.descripcion, proveedor.horario,
                proveedor.atiende_24_7, proveedor.latitud,
                proveedor.longitud, proveedor.activo, proveedor.id_proveedor
            )
            cursor.execute(self._ACTUALIZAR, valores)
            self._conexion_bd.commit()
            filas_afectadas = cursor.rowcount
            cursor.close()
            return filas_afectadas > 0
        except Error as e:
            self._conexion_bd.rollback()
            print(f"[ERROR] Al actualizar proveedor: {e}")
            return False

    def eliminar(self, id_proveedor):
        """Elimina un proveedor por su ID."""
        conexion = self._conexion_bd.obtener_conexion()
        if conexion is None:
            return False
        try:
            cursor = conexion.cursor()
            cursor.execute(self._ELIMINAR, (id_proveedor,))
            self._conexion_bd.commit()
            filas_afectadas = cursor.rowcount
            cursor.close()
            return filas_afectadas > 0
        except Error as e:
            self._conexion_bd.rollback()
            print(f"[ERROR] Al eliminar proveedor: {e}")
            return False

    def buscar_por_nombre(self, termino):
        """Busca proveedores cuyo nombre contenga el término."""
        conexion = self._conexion_bd.obtener_conexion()
        if conexion is None:
            return []
        try:
            cursor = conexion.cursor()
            cursor.execute(self._BUSCAR_POR_NOMBRE, (f"%{termino}%",))
            filas = cursor.fetchall()
            proveedores = [self._mapear_proveedor(fila) for fila in filas]
            cursor.close()
            return proveedores
        except Error as e:
            print(f"[ERROR] Al buscar proveedores: {e}")
            return []

    def consultar_por_ciudad(self, ciudad):
        """Retorna los proveedores activos de una ciudad."""
        conexion = self._conexion_bd.obtener_conexion()
        if conexion is None:
            return []
        try:
            cursor = conexion.cursor()
            cursor.execute(self._CONSULTAR_POR_CIUDAD, (ciudad,))
            filas = cursor.fetchall()
            proveedores = [self._mapear_proveedor(fila) for fila in filas]
            cursor.close()
            return proveedores
        except Error as e:
            print(f"[ERROR] Al consultar proveedores por ciudad: {e}")
            return []
