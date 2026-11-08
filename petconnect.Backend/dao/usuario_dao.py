"""
DAO (Data Access Object) para la entidad Usuario.
Implementa operaciones CRUD sobre la tabla 'usuarios'.
Equivalente al patrón DAO con PreparedStatement de JDBC.
Item 4.5 (A-11, NC-003): cada metodo pide una conexion del pool con
conexion_y_cursor y, al salir del with, cierra el cursor y la devuelve.
Si la BD falla, imprime y devuelve None, [] o False (item 4.15: propagar).
"""

from mysql.connector import Error
from conexion.conexion_bd import ConexionBD, conexion_y_cursor
from modelo.usuario import Usuario


class UsuarioDAO:
    """Acceso a datos para la tabla usuarios."""

    # NC-005 (item 3.1): la fecha y la version de la politica aceptada son la prueba
    # de la autorizacion. Se escriben al crear el usuario y, desde el item 3.5, cuando
    # una cuenta vieja (o que acepto otra version) la da al iniciar sesion. Los SELECT
    # las leen para que /api/auth/login sepa si hay que pedirla.
    _INSERTAR = """
        INSERT INTO usuarios (nombres, apellidos, correo, telefono,
                            password_hash, foto_perfil, estado, verificado, acepta_datos,
                            fecha_autorizacion_datos, version_politica_datos)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    _CONSULTAR_TODOS = """
        SELECT id_usuario, nombres, apellidos, correo, telefono,
            password_hash, foto_perfil, estado, verificado, acepta_datos,
            fecha_creacion, fecha_actualizacion,
            fecha_autorizacion_datos, version_politica_datos
        FROM usuarios ORDER BY id_usuario
    """

    _CONSULTAR_POR_ID = """
        SELECT id_usuario, nombres, apellidos, correo, telefono,
            password_hash, foto_perfil, estado, verificado, acepta_datos,
            fecha_creacion, fecha_actualizacion,
            fecha_autorizacion_datos, version_politica_datos
        FROM usuarios WHERE id_usuario = %s
    """

    _CONSULTAR_POR_CORREO = """
        SELECT id_usuario, nombres, apellidos, correo, telefono,
            password_hash, foto_perfil, estado, verificado, acepta_datos,
            fecha_creacion, fecha_actualizacion,
            fecha_autorizacion_datos, version_politica_datos
        FROM usuarios WHERE correo = %s
    """

    _ACTUALIZAR = """
        UPDATE usuarios
        SET nombres = %s, apellidos = %s, correo = %s, telefono = %s,
            foto_perfil = %s, estado = %s, verificado = %s, acepta_datos = %s
        WHERE id_usuario = %s
    """

    _ACTUALIZAR_PASSWORD = """
        UPDATE usuarios SET password_hash = %s WHERE id_usuario = %s
    """

    # Item 3.5 (A-20, R05): las tres columnas van juntas porque la regla
    # chk_autorizacion_datos de la BD no acepta un 1 sin fecha ni version.
    # Solo la llama /api/auth/login/verify, con la casilla marcada por la persona
    # y el codigo correcto: nunca se usa para "autorizar" cuentas en bloque.
    _REGISTRAR_AUTORIZACION = """
        UPDATE usuarios
        SET acepta_datos = 1, fecha_autorizacion_datos = %s, version_politica_datos = %s
        WHERE id_usuario = %s
    """

    _ELIMINAR = """
        DELETE FROM usuarios WHERE id_usuario = %s
    """

    _BUSCAR_POR_NOMBRE = """
        SELECT id_usuario, nombres, apellidos, correo, telefono,
            password_hash, foto_perfil, estado, verificado, acepta_datos,
            fecha_creacion, fecha_actualizacion,
            fecha_autorizacion_datos, version_politica_datos
        FROM usuarios WHERE nombres LIKE %s OR apellidos LIKE %s
        ORDER BY nombres
    """

    # Item 4.13 (A-03): lo unico que require_auth necesita en cada peticion. Es una
    # consulta corta por la clave primaria (solo dos columnas).
    _CONSULTAR_SESION = """
        SELECT version_sesion, estado FROM usuarios WHERE id_usuario = %s
    """

    # Sumar 1 deja sin valor todos los tokens de la cuenta. fecha_actualizacion se
    # reasigna a si misma para que su regla "on update" no la cambie: cerrar sesion no es
    # editar los datos de la persona.
    _CERRAR_SESIONES = """
        UPDATE usuarios
        SET version_sesion = version_sesion + 1, fecha_actualizacion = fecha_actualizacion
        WHERE id_usuario = %s
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
            fecha_actualizacion=fila[11],
            fecha_autorizacion_datos=fila[12],
            version_politica_datos=fila[13]
        )

    def insertar(self, usuario):
        """Registra un nuevo usuario en la base de datos."""
        try:
            with conexion_y_cursor(self._conexion_bd) as (conexion, cursor):
                valores = (
                    usuario.nombres, usuario.apellidos, usuario.correo,
                    usuario.telefono, usuario.password_hash, usuario.foto_perfil,
                    usuario.estado, usuario.verificado, usuario.acepta_datos,
                    usuario.fecha_autorizacion_datos, usuario.version_politica_datos
                )
                try:
                    cursor.execute(self._INSERTAR, valores)
                    conexion.commit()
                except Error:
                    conexion.rollback()
                    raise
                usuario.id_usuario = cursor.lastrowid
            return True
        except Error as e:
            print(f"[ERROR] Al insertar usuario: {e}")
            return False

    def consultar_todos(self):
        """Retorna la lista de todos los usuarios registrados."""
        try:
            with conexion_y_cursor(self._conexion_bd) as (conexion, cursor):
                cursor.execute(self._CONSULTAR_TODOS)
                filas = cursor.fetchall()
                usuarios = [self._mapear_usuario(fila) for fila in filas]
            return usuarios
        except Error as e:
            print(f"[ERROR] Al consultar usuarios: {e}")
            return []

    def consultar_por_id(self, id_usuario):
        """Busca un usuario por su ID."""
        try:
            with conexion_y_cursor(self._conexion_bd) as (conexion, cursor):
                cursor.execute(self._CONSULTAR_POR_ID, (id_usuario,))
                fila = cursor.fetchone()
            return self._mapear_usuario(fila) if fila else None
        except Error as e:
            print(f"[ERROR] Al consultar usuario por ID: {e}")
            return None

    def consultar_por_correo(self, correo):
        """Busca un usuario por su correo electrónico."""
        try:
            with conexion_y_cursor(self._conexion_bd) as (conexion, cursor):
                cursor.execute(self._CONSULTAR_POR_CORREO, (correo,))
                fila = cursor.fetchone()
            return self._mapear_usuario(fila) if fila else None
        except Error as e:
            print(f"[ERROR] Al consultar usuario por correo: {e}")
            return None

    def actualizar(self, usuario):
        """Actualiza la información de un usuario existente."""
        try:
            with conexion_y_cursor(self._conexion_bd) as (conexion, cursor):
                valores = (
                    usuario.nombres, usuario.apellidos, usuario.correo,
                    usuario.telefono, usuario.foto_perfil, usuario.estado,
                    usuario.verificado, usuario.acepta_datos, usuario.id_usuario
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
            print(f"[ERROR] Al actualizar usuario: {e}")
            return False

    def actualizar_password(self, id_usuario, password_hash):
        """Reemplaza el hash de la contrasena (migracion de SHA-256 a bcrypt)."""
        try:
            with conexion_y_cursor(self._conexion_bd) as (conexion, cursor):
                try:
                    cursor.execute(self._ACTUALIZAR_PASSWORD, (password_hash, id_usuario))
                    conexion.commit()
                except Error:
                    conexion.rollback()
                    raise
                filas_afectadas = cursor.rowcount
            return filas_afectadas > 0
        except Error as e:
            print(f"[ERROR] Al actualizar la contrasena: {e}")
            return False

    def registrar_autorizacion(self, id_usuario, fecha, version):
        """Guarda la autorizacion de datos que la persona dio al iniciar sesion (item 3.5)."""
        try:
            with conexion_y_cursor(self._conexion_bd) as (conexion, cursor):
                try:
                    cursor.execute(self._REGISTRAR_AUTORIZACION, (fecha, version, id_usuario))
                    conexion.commit()
                except Error:
                    conexion.rollback()
                    raise
                filas_afectadas = cursor.rowcount
            return filas_afectadas > 0
        except Error as e:
            print(f"[ERROR] Al registrar la autorizacion de datos: {e}")
            return False

    # Item 4.13: estos dos metodos NO se tragan los errores de la BD (como OtpDAO y
    # SolicitudDAO). Si devolvieran None con la BD caida, require_auth responderia
    # 401 y la web cerraria la sesion (4.7); dejandolos subir, la API responde 503.

    def consultar_sesion(self, id_usuario):
        """Devuelve (version_sesion, estado) del usuario, o None si no existe."""
        with conexion_y_cursor(self._conexion_bd) as (conexion, cursor):
            cursor.execute(self._CONSULTAR_SESION, (id_usuario,))
            fila = cursor.fetchone()
        return (int(fila[0]), fila[1]) if fila else None

    def cerrar_sesiones(self, id_usuario):
        """Suma 1 a version_sesion: cierra todas las sesiones abiertas de la cuenta."""
        with conexion_y_cursor(self._conexion_bd) as (conexion, cursor):
            try:
                cursor.execute(self._CERRAR_SESIONES, (id_usuario,))
                conexion.commit()
            except Error:
                conexion.rollback()
                raise
            filas_afectadas = cursor.rowcount
        return filas_afectadas > 0

    def eliminar(self, id_usuario):
        """Elimina un usuario por su ID."""
        try:
            with conexion_y_cursor(self._conexion_bd) as (conexion, cursor):
                try:
                    cursor.execute(self._ELIMINAR, (id_usuario,))
                    conexion.commit()
                except Error:
                    conexion.rollback()
                    raise
                filas_afectadas = cursor.rowcount
            return filas_afectadas > 0
        except Error as e:
            print(f"[ERROR] Al eliminar usuario: {e}")
            return False

    def buscar_por_nombre(self, termino):
        """Busca usuarios cuyo nombre o apellido contenga el término."""
        try:
            with conexion_y_cursor(self._conexion_bd) as (conexion, cursor):
                patron = f"%{termino}%"
                cursor.execute(self._BUSCAR_POR_NOMBRE, (patron, patron))
                filas = cursor.fetchall()
                usuarios = [self._mapear_usuario(fila) for fila in filas]
            return usuarios
        except Error as e:
            print(f"[ERROR] Al buscar usuarios: {e}")
            return []
