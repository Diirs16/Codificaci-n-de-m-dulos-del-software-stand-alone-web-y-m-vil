"""
DAO (Data Access Object) para la entidad Producto.
Implementa operaciones CRUD sobre la tabla 'productos'.
"""

from mysql.connector import Error
from conexion.conexion_bd import ConexionBD
from modelo.producto import Producto


class ProductoDAO:
    """Acceso a datos para la tabla productos."""

    _INSERTAR = """
        INSERT INTO productos (id_categoria_producto, nombre, descripcion,
                            precio, stock, imagen_url, activo)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """

    _CONSULTAR_TODOS = """
        SELECT p.id_producto, p.id_categoria_producto, p.nombre,
            p.descripcion, p.precio, p.stock, p.imagen_url, p.activo
        FROM productos p ORDER BY p.id_producto
    """

    _CONSULTAR_POR_ID = """
        SELECT id_producto, id_categoria_producto, nombre, descripcion,
            precio, stock, imagen_url, activo
        FROM productos WHERE id_producto = %s
    """

    _CONSULTAR_POR_CATEGORIA = """
        SELECT id_producto, id_categoria_producto, nombre, descripcion,
            precio, stock, imagen_url, activo
        FROM productos WHERE id_categoria_producto = %s ORDER BY nombre
    """

    _ACTUALIZAR = """
        UPDATE productos
        SET id_categoria_producto = %s, nombre = %s, descripcion = %s,
            precio = %s, stock = %s, imagen_url = %s, activo = %s
        WHERE id_producto = %s
    """

    _ELIMINAR = """
        DELETE FROM productos WHERE id_producto = %s
    """

    _BUSCAR_POR_NOMBRE = """
        SELECT id_producto, id_categoria_producto, nombre, descripcion,
            precio, stock, imagen_url, activo
        FROM productos WHERE nombre LIKE %s ORDER BY nombre
    """

    def __init__(self):
        self._conexion_bd = ConexionBD()

    def _mapear_producto(self, fila):
        """Convierte una fila del ResultSet a un objeto Producto."""
        return Producto(
            id_producto=fila[0],
            id_categoria_producto=fila[1],
            nombre=fila[2],
            descripcion=fila[3],
            precio=float(fila[4]) if fila[4] else 0.0,
            stock=fila[5],
            imagen_url=fila[6],
            activo=bool(fila[7])
        )

    def insertar(self, producto):
        """Registra un nuevo producto en la base de datos."""
        conexion = self._conexion_bd.obtener_conexion()
        if conexion is None:
            return False
        try:
            cursor = conexion.cursor()
            valores = (
                producto.id_categoria_producto, producto.nombre,
                producto.descripcion, producto.precio, producto.stock,
                producto.imagen_url, producto.activo
            )
            cursor.execute(self._INSERTAR, valores)
            self._conexion_bd.commit()
            producto.id_producto = cursor.lastrowid
            cursor.close()
            return True
        except Error as e:
            self._conexion_bd.rollback()
            print(f"[ERROR] Al insertar producto: {e}")
            return False

    def consultar_todos(self):
        """Retorna la lista de todos los productos."""
        conexion = self._conexion_bd.obtener_conexion()
        if conexion is None:
            return []
        try:
            cursor = conexion.cursor()
            cursor.execute(self._CONSULTAR_TODOS)
            filas = cursor.fetchall()
            productos = [self._mapear_producto(fila) for fila in filas]
            cursor.close()
            return productos
        except Error as e:
            print(f"[ERROR] Al consultar productos: {e}")
            return []

    def consultar_por_id(self, id_producto):
        """Busca un producto por su ID."""
        conexion = self._conexion_bd.obtener_conexion()
        if conexion is None:
            return None
        try:
            cursor = conexion.cursor()
            cursor.execute(self._CONSULTAR_POR_ID, (id_producto,))
            fila = cursor.fetchone()
            cursor.close()
            return self._mapear_producto(fila) if fila else None
        except Error as e:
            print(f"[ERROR] Al consultar producto por ID: {e}")
            return None

    def consultar_por_categoria(self, id_categoria):
        """Retorna los productos de una categoría específica."""
        conexion = self._conexion_bd.obtener_conexion()
        if conexion is None:
            return []
        try:
            cursor = conexion.cursor()
            cursor.execute(self._CONSULTAR_POR_CATEGORIA, (id_categoria,))
            filas = cursor.fetchall()
            productos = [self._mapear_producto(fila) for fila in filas]
            cursor.close()
            return productos
        except Error as e:
            print(f"[ERROR] Al consultar productos por categoría: {e}")
            return []

    def actualizar(self, producto):
        """Actualiza la información de un producto existente."""
        conexion = self._conexion_bd.obtener_conexion()
        if conexion is None:
            return False
        try:
            cursor = conexion.cursor()
            valores = (
                producto.id_categoria_producto, producto.nombre,
                producto.descripcion, producto.precio, producto.stock,
                producto.imagen_url, producto.activo, producto.id_producto
            )
            cursor.execute(self._ACTUALIZAR, valores)
            self._conexion_bd.commit()
            filas_afectadas = cursor.rowcount
            cursor.close()
            return filas_afectadas > 0
        except Error as e:
            self._conexion_bd.rollback()
            print(f"[ERROR] Al actualizar producto: {e}")
            return False

    def eliminar(self, id_producto):
        """Elimina un producto por su ID."""
        conexion = self._conexion_bd.obtener_conexion()
        if conexion is None:
            return False
        try:
            cursor = conexion.cursor()
            cursor.execute(self._ELIMINAR, (id_producto,))
            self._conexion_bd.commit()
            filas_afectadas = cursor.rowcount
            cursor.close()
            return filas_afectadas > 0
        except Error as e:
            self._conexion_bd.rollback()
            print(f"[ERROR] Al eliminar producto: {e}")
            return False

    def buscar_por_nombre(self, termino):
        """Busca productos cuyo nombre contenga el término."""
        conexion = self._conexion_bd.obtener_conexion()
        if conexion is None:
            return []
        try:
            cursor = conexion.cursor()
            cursor.execute(self._BUSCAR_POR_NOMBRE, (f"%{termino}%",))
            filas = cursor.fetchall()
            productos = [self._mapear_producto(fila) for fila in filas]
            cursor.close()
            return productos
        except Error as e:
            print(f"[ERROR] Al buscar productos: {e}")
            return []
