"""Entidad ProveedorServicio - Representa la tabla 'proveedores_servicio'."""


class ProveedorServicio:
    """Modelo de datos para un proveedor de servicios en PetConnect."""

    def __init__(self, id_proveedor=None, nombre="", tipo_documento="",
                numero_documento="", telefono="", correo="",
                direccion="", ciudad="", descripcion="",
                horario="", atiende_24_7=False, latitud=None,
                longitud=None, activo=True):
        self.id_proveedor = id_proveedor
        self.nombre = nombre
        self.tipo_documento = tipo_documento
        self.numero_documento = numero_documento
        self.telefono = telefono
        self.correo = correo
        self.direccion = direccion
        self.ciudad = ciudad
        self.descripcion = descripcion
        self.horario = horario
        self.atiende_24_7 = atiende_24_7
        self.latitud = latitud
        self.longitud = longitud
        self.activo = activo

    def __str__(self):
        h24 = "24/7" if self.atiende_24_7 else self.horario
        estado_txt = "Activo" if self.activo else "Inactivo"
        return (f"ID: {self.id_proveedor} | {self.nombre} | {self.ciudad} "
                f"| Tel: {self.telefono} | Horario: {h24} | {estado_txt}")

    def __repr__(self):
        return f"ProveedorServicio(id={self.id_proveedor}, nombre='{self.nombre}')"
