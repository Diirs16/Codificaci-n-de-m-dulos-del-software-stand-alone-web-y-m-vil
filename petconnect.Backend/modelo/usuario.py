"""Entidad Usuario - Representa la tabla 'usuarios' de la base de datos."""


class Usuario:
    """Modelo de datos para un usuario del sistema PetConnect."""

    def __init__(self, id_usuario=None, nombres="", apellidos="",
                correo="", telefono="", password_hash="",
                foto_perfil=None, estado="activo", verificado=False,
                acepta_datos=False, fecha_creacion=None, fecha_actualizacion=None,
                fecha_autorizacion_datos=None, version_politica_datos=None):
        # NC-005 (item 3.1): por defecto NADIE autorizo el tratamiento de sus datos.
        # acepta_datos=True solo con la fecha y la version de la politica aceptada
        # (Ley 1581, art. 9). La base lo exige con la regla chk_autorizacion_datos.
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
        self.fecha_autorizacion_datos = fecha_autorizacion_datos
        self.version_politica_datos = version_politica_datos

    def __str__(self):
        estado_txt = f"[{self.estado.upper()}]"
        return (f"ID: {self.id_usuario} | {self.nombres} {self.apellidos} "
                f"| {self.correo} | Tel: {self.telefono} | {estado_txt}")

    def __repr__(self):
        return f"Usuario(id={self.id_usuario}, correo='{self.correo}')"
