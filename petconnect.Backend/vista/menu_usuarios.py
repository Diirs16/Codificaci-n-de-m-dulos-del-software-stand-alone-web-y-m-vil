"""
Vista del módulo de Usuarios.
Interfaz de consola para gestionar las operaciones CRUD de usuarios.
"""

from getpass import getpass

from dao.usuario_dao import UsuarioDAO
from modelo.usuario import Usuario
from security.datos_usuario import validar_formato_correo, validar_nombre
from security.passwords import hash_password
from security.politica import validar_contrasena

# Item 4.11 (A-18): la consola no puede dar la autorizacion de datos en nombre del
# titular (Ley 1581, art. 9; politica C.6 y C.10). La cuenta queda en
# acepta_datos = 0 y el titular la da al iniciar sesion (item 3.5).
AVISO_SIN_AUTORIZACION = (
    "  [i] La cuenta queda SIN autorizacion de tratamiento de datos. El titular\n"
    "      debe darla al iniciar sesion por la web o el movil (casilla + codigo)."
)


class MenuUsuarios:
    """Menú interactivo para la gestión de usuarios."""

    def __init__(self):
        self._usuario_dao = UsuarioDAO()

    def mostrar_menu(self):
        """Muestra el submenú de gestión de usuarios."""
        while True:
            print("\n" + "=" * 55)
            print("       GESTION DE USUARIOS - PetConnect")
            print("=" * 55)
            print("  1. Registrar usuario")
            print("  2. Consultar todos los usuarios")
            print("  3. Buscar usuario por ID")
            print("  4. Buscar usuario por correo")
            print("  5. Buscar usuarios por nombre")
            print("  6. Actualizar usuario")
            print("  7. Eliminar usuario")
            print("  0. Volver al menu principal")
            print("-" * 55)

            opcion = input("  Seleccione una opcion: ").strip()

            if opcion == "1":
                self._registrar_usuario()
            elif opcion == "2":
                self._consultar_todos()
            elif opcion == "3":
                self._buscar_por_id()
            elif opcion == "4":
                self._buscar_por_correo()
            elif opcion == "5":
                self._buscar_por_nombre()
            elif opcion == "6":
                self._actualizar_usuario()
            elif opcion == "7":
                self._eliminar_usuario()
            elif opcion == "0":
                break
            else:
                print("  [!] Opcion no valida.")

    def _registrar_usuario(self):
        """Solicita datos y registra un nuevo usuario con las mismas reglas que la API.

        Item 4.11 (A-18): nombre, correo y contrasena pasan por las mismas
        funciones que /api/auth/register (security/datos_usuario.py y
        security/politica.py). La contrasena se escribe sin verse (getpass), dos
        veces, y se guarda tal cual (sin .strip(), como la API). Ante cualquier
        error se vuelve al menu sin guardar nada.
        """
        print("\n--- Registro de nuevo usuario ---")
        nombres = input("  Nombres: ").strip()
        if not nombres:
            print("  [!] Nombres, correo y contrasena son obligatorios.")
            return
        error = validar_nombre(nombres, "El nombre")
        if error:
            print(f"  [!] {error}")
            return

        apellidos = input("  Apellidos (opcional): ").strip()
        if apellidos:
            error = validar_nombre(apellidos, "Los apellidos")
            if error:
                print(f"  [!] {error}")
                return

        correo = input("  Correo electronico: ").strip()
        error = validar_formato_correo(correo)
        if error:
            print(f"  [!] {error}")
            return
        # La consola es del administrador: puede decir que el correo ya existe
        # (en la API publica no, A-14). El mensaje no repite el correo (Ley 1581).
        if self._usuario_dao.consultar_por_correo(correo) is not None:
            print("  [!] Ese correo ya tiene una cuenta. No se registro nada.")
            return

        telefono = input("  Telefono (opcional): ").strip()

        contrasena = getpass("  Contrasena (no se vera al escribir): ")
        if not contrasena:
            print("  [!] Nombres, correo y contrasena son obligatorios.")
            return
        error = validar_contrasena(contrasena)
        if error:
            print(f"  [!] {error}")
            return
        if getpass("  Repita la contrasena: ") != contrasena:
            print("  [!] Las contrasenas no coinciden. No se registro nada.")
            return

        usuario = Usuario(
            nombres=nombres,
            apellidos=apellidos,
            correo=correo,
            telefono=telefono,
            password_hash=hash_password(contrasena),
            acepta_datos=False,     # explicito: ver AVISO_SIN_AUTORIZACION
        )

        if self._usuario_dao.insertar(usuario):
            print(f"  [OK] Usuario registrado con ID: {usuario.id_usuario}")
            print(AVISO_SIN_AUTORIZACION)
        else:
            print("  [!] No se pudo registrar el usuario.")

    def _consultar_todos(self):
        """Muestra todos los usuarios registrados."""
        print("\n--- Lista de usuarios ---")
        usuarios = self._usuario_dao.consultar_todos()
        if not usuarios:
            print("  No hay usuarios registrados.")
            return
        for usuario in usuarios:
            print(f"  {usuario}")
        print(f"\n  Total: {len(usuarios)} usuario(s)")

    def _buscar_por_id(self):
        """Busca y muestra un usuario por su ID."""
        print("\n--- Buscar usuario por ID ---")
        try:
            id_usuario = int(input("  ID del usuario: ").strip())
        except ValueError:
            print("  [!] ID debe ser un numero entero.")
            return

        usuario = self._usuario_dao.consultar_por_id(id_usuario)
        if usuario:
            print(f"  {usuario}")
            print(f"  Verificado: {'Si' if usuario.verificado else 'No'}")
            print(f"  Fecha registro: {usuario.fecha_creacion}")
        else:
            print(f"  [!] No se encontro usuario con ID {id_usuario}.")

    def _buscar_por_correo(self):
        """Busca y muestra un usuario por su correo."""
        print("\n--- Buscar usuario por correo ---")
        correo = input("  Correo electronico: ").strip()

        usuario = self._usuario_dao.consultar_por_correo(correo)
        if usuario:
            print(f"  {usuario}")
        else:
            print(f"  [!] No se encontro usuario con correo '{correo}'.")

    def _buscar_por_nombre(self):
        """Busca usuarios cuyo nombre o apellido contenga el término."""
        print("\n--- Buscar usuarios por nombre ---")
        termino = input("  Termino de busqueda: ").strip()

        usuarios = self._usuario_dao.buscar_por_nombre(termino)
        if not usuarios:
            print(f"  No se encontraron usuarios con '{termino}'.")
            return
        for usuario in usuarios:
            print(f"  {usuario}")
        print(f"\n  Encontrados: {len(usuarios)} usuario(s)")

    def _actualizar_usuario(self):
        """Actualiza la información de un usuario existente."""
        print("\n--- Actualizar usuario ---")
        try:
            id_usuario = int(input("  ID del usuario a actualizar: ").strip())
        except ValueError:
            print("  [!] ID debe ser un numero entero.")
            return

        usuario = self._usuario_dao.consultar_por_id(id_usuario)
        if not usuario:
            print(f"  [!] No se encontro usuario con ID {id_usuario}.")
            return

        print(f"  Usuario actual: {usuario}")
        print("  (Deje vacio para mantener el valor actual)\n")

        nombres = input(f"  Nombres [{usuario.nombres}]: ").strip()
        apellidos = input(f"  Apellidos [{usuario.apellidos}]: ").strip()
        correo = input(f"  Correo [{usuario.correo}]: ").strip()
        telefono = input(f"  Telefono [{usuario.telefono}]: ").strip()
        estado = input(f"  Estado (activo/inactivo/bloqueado) [{usuario.estado}]: ").strip()

        if nombres:
            usuario.nombres = nombres
        if apellidos:
            usuario.apellidos = apellidos
        if correo:
            usuario.correo = correo
        if telefono:
            usuario.telefono = telefono
        if estado in ("activo", "inactivo", "bloqueado"):
            usuario.estado = estado

        if self._usuario_dao.actualizar(usuario):
            print("  [OK] Usuario actualizado correctamente.")
        else:
            print("  [!] No se pudo actualizar el usuario.")

    def _eliminar_usuario(self):
        """Elimina un usuario previa confirmación."""
        print("\n--- Eliminar usuario ---")
        try:
            id_usuario = int(input("  ID del usuario a eliminar: ").strip())
        except ValueError:
            print("  [!] ID debe ser un numero entero.")
            return

        usuario = self._usuario_dao.consultar_por_id(id_usuario)
        if not usuario:
            print(f"  [!] No se encontro usuario con ID {id_usuario}.")
            return

        print(f"  Usuario: {usuario}")
        confirmacion = input("  Esta seguro de eliminar? (s/n): ").strip().lower()

        if confirmacion == "s":
            if self._usuario_dao.eliminar(id_usuario):
                print("  [OK] Usuario eliminado correctamente.")
            else:
                print("  [!] No se pudo eliminar el usuario.")
        else:
            print("  Operacion cancelada.")
