"""Entidad Producto - Representa la tabla 'productos' de la base de datos."""


class Producto:
    """Modelo de datos para un producto de la tienda PetConnect."""

    def __init__(self, id_producto=None, id_categoria_producto=None,
                nombre="", descripcion="", precio=0.0, stock=0,
                imagen_url=None, activo=True):
        self.id_producto = id_producto
        self.id_categoria_producto = id_categoria_producto
        self.nombre = nombre
        self.descripcion = descripcion
        self.precio = precio
        self.stock = stock
        self.imagen_url = imagen_url
        self.activo = activo

    def __str__(self):
        estado_txt = "Activo" if self.activo else "Inactivo"
        return (f"ID: {self.id_producto} | {self.nombre} "
                f"| ${self.precio:,.2f} | Stock: {self.stock} | {estado_txt}")

    def __repr__(self):
        return f"Producto(id={self.id_producto}, nombre='{self.nombre}')"
