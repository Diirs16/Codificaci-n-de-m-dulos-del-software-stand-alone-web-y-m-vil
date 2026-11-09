"""
DAO (Data Access Object) para la entidad Producto.
Implementa operaciones CRUD sobre la tabla 'productos'.
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
        with conexion_y_cursor(self._conexion_bd) as (conexion, cursor):
            valores = (
                producto.id_categoria_producto, producto.nombre,
                producto.descripcion, producto.precio, producto.stock,
                producto.imagen_url, producto.activo
            )
            try:
                cursor.execute(self._INSERTAR, valores)
                conexion.commit()
            except Error:
                conexion.rollback()
                raise
            producto.id_producto = cursor.lastrowid
        return True

    def consultar_todos(self):
        """Retorna la lista de todos los productos."""
        with conexion_y_cursor(self._conexion_bd) as (conexion, cursor):
            cursor.execute(self._CONSULTAR_TODOS)
            filas = cursor.fetchall()
            productos = [self._mapear_producto(fila) for fila in filas]
        return productos

    def consultar_por_id(self, id_producto):
        """Busca un producto por su ID."""
        with conexion_y_cursor(self._conexion_bd) as (conexion, cursor):
            cursor.execute(self._CONSULTAR_POR_ID, (id_producto,))
            fila = cursor.fetchone()
        return self._mapear_producto(fila) if fila else None

    def consultar_por_categoria(self, id_categoria):
        """Retorna los productos de una categoría específica."""
        with conexion_y_cursor(self._conexion_bd) as (conexion, cursor):
            cursor.execute(self._CONSULTAR_POR_CATEGORIA, (id_categoria,))
            filas = cursor.fetchall()
            productos = [self._mapear_producto(fila) for fila in filas]
        return productos

    def actualizar(self, producto):
        """Actualiza la información de un producto existente."""
        with conexion_y_cursor(self._conexion_bd) as (conexion, cursor):
            valores = (
                producto.id_categoria_producto, producto.nombre,
                producto.descripcion, producto.precio, producto.stock,
                producto.imagen_url, producto.activo, producto.id_producto
            )
            try:
                cursor.execute(self._ACTUALIZAR, valores)
                conexion.commit()
            except Error:
                conexion.rollback()
                raise
            filas_afectadas = cursor.rowcount
        return filas_afectadas > 0

    def eliminar(self, id_producto):
        """Elimina un producto por su ID."""
        with conexion_y_cursor(self._conexion_bd) as (conexion, cursor):
            try:
                cursor.execute(self._ELIMINAR, (id_producto,))
                conexion.commit()
            except Error:
                conexion.rollback()
                raise
            filas_afectadas = cursor.rowcount
        return filas_afectadas > 0

    def buscar_por_nombre(self, termino):
        """Busca productos cuyo nombre contenga el término."""
        with conexion_y_cursor(self._conexion_bd) as (conexion, cursor):
            cursor.execute(self._BUSCAR_POR_NOMBRE, (f"%{termino}%",))
            filas = cursor.fetchall()
            productos = [self._mapear_producto(fila) for fila in filas]
        return productos
