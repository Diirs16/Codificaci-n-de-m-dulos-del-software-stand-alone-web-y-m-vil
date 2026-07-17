"""
Menú principal de la aplicación PetConnect.
Punto de entrada a los diferentes módulos del sistema.
"""

from vista.menu_usuarios import MenuUsuarios
from vista.menu_mascotas import MenuMascotas
from vista.menu_productos import MenuProductos
from vista.menu_proveedores import MenuProveedores


class MenuPrincipal:
    """Controlador del menú principal de PetConnect."""

    def __init__(self):
        self._menu_usuarios = MenuUsuarios()
        self._menu_mascotas = MenuMascotas()
        self._menu_productos = MenuProductos()
        self._menu_proveedores = MenuProveedores()

    def iniciar(self):
        """Ejecuta el bucle principal del menú."""
        while True:
            print("\n" + "=" * 55)
            print("  ____       _    ____                            _   ")
            print(" |  _ \\ ___ | |_ / ___|___  _ __  _ __   ___  ___| |_ ")
            print(" | |_) / _ \\| __| |   / _ \\| '_ \\| '_ \\ / _ \\/ __| __|")
            print(" |  __/  __/| |_| |__| (_) | | | | | | |  __/ (__| |_ ")
            print(" |_|   \\___| \\__|\\____\\___/|_| |_|_| |_|\\___|\\___|\\__|")
            print()
            print("        Sistema de Gestion - PetConnect v1.0")
            print("=" * 55)
            print("  1. Gestion de Usuarios")
            print("  2. Gestion de Mascotas")
            print("  3. Gestion de Productos (Tienda)")
            print("  4. Gestion de Proveedores de Servicio")
            print("  0. Salir del sistema")
            print("-" * 55)

            opcion = input("  Seleccione un modulo: ").strip()

            if opcion == "1":
                self._menu_usuarios.mostrar_menu()
            elif opcion == "2":
                self._menu_mascotas.mostrar_menu()
            elif opcion == "3":
                self._menu_productos.mostrar_menu()
            elif opcion == "4":
                self._menu_proveedores.mostrar_menu()
            elif opcion == "0":
                print("\n  Gracias por usar PetConnect. Hasta pronto!")
                break
            else:
                print("  [!] Opcion no valida. Intente nuevamente.")
