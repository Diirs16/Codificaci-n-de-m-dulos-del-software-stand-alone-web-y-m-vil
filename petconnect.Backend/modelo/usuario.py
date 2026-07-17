"""Entidad Usuario - Representa la tabla 'usuarios' de la base de datos."""


class Usuario:
    """Modelo de datos para un usuario del sistema PetConnect."""

    def __init__(self, id_usuario=None, nombres="", apellidos="",
                correo="", telefono="", password_hash="",
                foto_perfil=None, estado="activo", verificado=False,
                acepta_datos=True, fecha_creacion=None, fecha_actualizacion=None):
        self.id_usuario = id_usuario
        self.nombres = nombres
        self.apellidos = apellidos
        self.correo = correo
        self.telefono = telefono
        self.password_hash = password_hash
        self.foto_perfil = foto_perfil
        self.estado = estado
        self.verificado = verificado
        self.acepta_datos = acepta_datos
        self.fecha_creacion = fecha_creacion
        self.fecha_actualizacion = fecha_actualizacion

    def __str__(self):
        estado_txt = f"[{self.estado.upper()}]"
        return (f"ID: {self.id_usuario} | {self.nombres} {self.apellidos} "
                f"| {self.correo} | Tel: {self.telefono} | {estado_txt}")

    def __repr__(self):
        return f"Usuario(id={self.id_usuario}, correo='{self.correo}')"
