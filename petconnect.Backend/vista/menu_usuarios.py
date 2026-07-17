"""
Vista del módulo de Usuarios.
Interfaz de consola para gestionar las operaciones CRUD de usuarios.
"""

import hashlib
from dao.usuario_dao import UsuarioDAO
from modelo.usuario import Usuario


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
        """Solicita datos y registra un nuevo usuario."""
        print("\n--- Registro de nuevo usuario ---")
        nombres = input("  Nombres: ").strip()
        apellidos = input("  Apellidos: ").strip()
        correo = input("  Correo electronico: ").strip()
        telefono = input("  Telefono: ").strip()
        contrasena = input("  Contrasena: ").strip()

        if not nombres or not correo or not contrasena:
            print("  [!] Nombres, correo y contrasena son obligatorios.")
            return

        password_hash = hashlib.sha256(contrasena.encode()).hexdigest()

        usuario = Usuario(
            nombres=nombres,
            apellidos=apellidos,
            correo=correo,
            telefono=telefono,
            password_hash=password_hash
        )

        if self._usuario_dao.insertar(usuario):
            print(f"  [OK] Usuario registrado con ID: {usuario.id_usuario}")
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
