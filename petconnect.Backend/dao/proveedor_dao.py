"""
DAO (Data Access Object) para la entidad ProveedorServicio.
Implementa operaciones CRUD sobre la tabla 'proveedores_servicio'.
Item 4.5 (A-11, NC-003): cada metodo pide una conexion del pool con
conexion_y_cursor y, al salir del with, cierra el cursor y la devuelve.
Si la BD falla, imprime y devuelve None, [] o False (item 4.15: propagar).
"""

from mysql.connector import Error
from conexion.conexion_bd import ConexionBD, conexion_y_cursor
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
        FROM proveedores_servicio WHERE nombre LIKE %s ESCAPE '!' AND activo = TRUE
        ORDER BY nombre
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
        try:
            with conexion_y_cursor(self._conexion_bd) as (conexion, cursor):
                valores = (
                    proveedor.nombre, proveedor.tipo_documento,
                    proveedor.numero_documento, proveedor.telefono,
                    proveedor.correo, proveedor.direccion, proveedor.ciudad,
                    proveedor.descripcion, proveedor.horario,
                    proveedor.atiende_24_7, proveedor.latitud,
                    proveedor.longitud, proveedor.activo
                )
                try:
                    cursor.execute(self._INSERTAR, valores)
                    conexion.commit()
                except Error:
                    conexion.rollback()
                    raise
                proveedor.id_proveedor = cursor.lastrowid
            return True
        except Error as e:
            print(f"[ERROR] Al insertar proveedor: {e}")
            return False

    def consultar_todos(self):
        """Retorna la lista de todos los proveedores."""
        try:
            with conexion_y_cursor(self._conexion_bd) as (conexion, cursor):
                cursor.execute(self._CONSULTAR_TODOS)
                filas = cursor.fetchall()
                proveedores = [self._mapear_proveedor(fila) for fila in filas]
            return proveedores
        except Error as e:
            print(f"[ERROR] Al consultar proveedores: {e}")
            return []

    def consultar_por_id(self, id_proveedor):
        """Busca un proveedor por su ID."""
        try:
            with conexion_y_cursor(self._conexion_bd) as (conexion, cursor):
                cursor.execute(self._CONSULTAR_POR_ID, (id_proveedor,))
                fila = cursor.fetchone()
            return self._mapear_proveedor(fila) if fila else None
        except Error as e:
            print(f"[ERROR] Al consultar proveedor por ID: {e}")
            return None

    def actualizar(self, proveedor):
        """Actualiza la información de un proveedor existente."""
        try:
            with conexion_y_cursor(self._conexion_bd) as (conexion, cursor):
                valores = (
                    proveedor.nombre, proveedor.tipo_documento,
                    proveedor.numero_documento, proveedor.telefono,
                    proveedor.correo, proveedor.direccion, proveedor.ciudad,
                    proveedor.descripcion, proveedor.horario,
                    proveedor.atiende_24_7, proveedor.latitud,
                    proveedor.longitud, proveedor.activo, proveedor.id_proveedor
                )
                try:
                    cursor.execute(self._ACTUALIZAR, valores)
                    conexion.commit()
                except Error:
                    conexion.rollback()
                    raise
                filas_afectadas = cursor.rowcount
            return filas_afectadas > 0
        except Error as e:
            print(f"[ERROR] Al actualizar proveedor: {e}")
            return False

    def eliminar(self, id_proveedor):
        """Elimina un proveedor por su ID."""
        try:
            with conexion_y_cursor(self._conexion_bd) as (conexion, cursor):
                try:
                    cursor.execute(self._ELIMINAR, (id_proveedor,))
                    conexion.commit()
                except Error:
                    conexion.rollback()
                    raise
                filas_afectadas = cursor.rowcount
            return filas_afectadas > 0
        except Error as e:
            print(f"[ERROR] Al eliminar proveedor: {e}")
            return False

    @staticmethod
    def _escapar_like(termino):
        """Hace que '%' y '_' del término se busquen como letras y no como comodines.

        Se usa '!' como carácter de escape (ESCAPE '!' en la consulta) porque la
        barra invertida cambia de significado según el modo NO_BACKSLASH_ESCAPES
        de MariaDB. El '!' se escapa primero para no duplicar los que se agregan.
        """
        return termino.replace("!", "!!").replace("%", "!%").replace("_", "!_")

    def buscar_por_nombre(self, termino):
        """Busca proveedores activos cuyo nombre contenga el término (NC-011)."""
        try:
            with conexion_y_cursor(self._conexion_bd) as (conexion, cursor):
                cursor.execute(self._BUSCAR_POR_NOMBRE,
                               (f"%{self._escapar_like(termino)}%",))
                filas = cursor.fetchall()
                proveedores = [self._mapear_proveedor(fila) for fila in filas]
            return proveedores
        except Error as e:
            print(f"[ERROR] Al buscar proveedores: {e}")
            return []

    def consultar_por_ciudad(self, ciudad):
        """Retorna los proveedores activos de una ciudad."""
        try:
            with conexion_y_cursor(self._conexion_bd) as (conexion, cursor):
                cursor.execute(self._CONSULTAR_POR_CIUDAD, (ciudad,))
                filas = cursor.fetchall()
                proveedores = [self._mapear_proveedor(fila) for fila in filas]
            return proveedores
        except Error as e:
            print(f"[ERROR] Al consultar proveedores por ciudad: {e}")
            return []
