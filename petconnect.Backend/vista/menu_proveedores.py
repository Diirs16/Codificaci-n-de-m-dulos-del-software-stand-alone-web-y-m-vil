"""
Vista del módulo de Proveedores de Servicio.
Interfaz de consola para gestionar las operaciones CRUD de proveedores.
"""

from dao.proveedor_dao import ProveedorDAO
from modelo.proveedor_servicio import ProveedorServicio


class MenuProveedores:
    """Menú interactivo para la gestión de proveedores de servicio."""

    def __init__(self):
        self._proveedor_dao = ProveedorDAO()

    def mostrar_menu(self):
        """Muestra el submenú de gestión de proveedores."""
        while True:
            print("\n" + "=" * 55)
            print("     GESTION DE PROVEEDORES - PetConnect")
            print("=" * 55)
            print("  1. Registrar proveedor")
            print("  2. Consultar todos los proveedores")
            print("  3. Buscar proveedor por ID")
            print("  4. Buscar proveedores por ciudad")
            print("  5. Buscar proveedores por nombre")
            print("  6. Actualizar proveedor")
            print("  7. Eliminar proveedor")
            print("  0. Volver al menu principal")
            print("-" * 55)

            opcion = input("  Seleccione una opcion: ").strip()

            if opcion == "1":
                self._registrar_proveedor()
            elif opcion == "2":
                self._consultar_todos()
            elif opcion == "3":
                self._buscar_por_id()
            elif opcion == "4":
                self._buscar_por_ciudad()
            elif opcion == "5":
                self._buscar_por_nombre()
            elif opcion == "6":
                self._actualizar_proveedor()
            elif opcion == "7":
                self._eliminar_proveedor()
            elif opcion == "0":
                break
            else:
                print("  [!] Opcion no valida.")

    def _registrar_proveedor(self):
        """Solicita datos y registra un nuevo proveedor."""
        print("\n--- Registro de nuevo proveedor ---")
        nombre = input("  Nombre del proveedor: ").strip()
        tipo_documento = input("  Tipo de documento (CC/NIT/CE): ").strip()
        numero_documento = input("  Numero de documento: ").strip()
        telefono = input("  Telefono: ").strip()
        correo = input("  Correo electronico: ").strip()
        direccion = input("  Direccion: ").strip()
        ciudad = input("  Ciudad: ").strip()
        descripcion = input("  Descripcion del servicio: ").strip()
        horario = input("  Horario (ej: Lun-Vie 8:00-18:00): ").strip()
        atiende_24_7_txt = input("  Atiende 24/7? (s/n): ").strip().lower()

        if not nombre:
            print("  [!] El nombre del proveedor es obligatorio.")
            return

        proveedor = ProveedorServicio(
            nombre=nombre,
            tipo_documento=tipo_documento,
            numero_documento=numero_documento,
            telefono=telefono,
            correo=correo,
            direccion=direccion,
            ciudad=ciudad,
            descripcion=descripcion,
            horario=horario,
            atiende_24_7=(atiende_24_7_txt == "s")
        )

        if self._proveedor_dao.insertar(proveedor):
            print(f"  [OK] Proveedor registrado con ID: {proveedor.id_proveedor}")
        else:
            print("  [!] No se pudo registrar el proveedor.")

    def _consultar_todos(self):
        """Muestra todos los proveedores registrados."""
        print("\n--- Lista de proveedores ---")
        proveedores = self._proveedor_dao.consultar_todos()
        if not proveedores:
            print("  No hay proveedores registrados.")
            return
        for proveedor in proveedores:
            print(f"  {proveedor}")
        print(f"\n  Total: {len(proveedores)} proveedor(es)")

    def _buscar_por_id(self):
        """Busca y muestra un proveedor por su ID."""
        print("\n--- Buscar proveedor por ID ---")
        try:
            id_proveedor = int(input("  ID del proveedor: ").strip())
        except ValueError:
            print("  [!] ID debe ser un numero entero.")
            return

        proveedor = self._proveedor_dao.consultar_por_id(id_proveedor)
        if proveedor:
            print(f"  {proveedor}")
            print(f"  Correo: {proveedor.correo}")
            print(f"  Direccion: {proveedor.direccion}")
            print(f"  Descripcion: {proveedor.descripcion}")
        else:
            print(f"  [!] No se encontro proveedor con ID {id_proveedor}.")

    def _buscar_por_ciudad(self):
        """Muestra los proveedores activos de una ciudad."""
        print("\n--- Proveedores por ciudad ---")
        ciudad = input("  Ciudad: ").strip()

        proveedores = self._proveedor_dao.consultar_por_ciudad(ciudad)
        if not proveedores:
            print(f"  No se encontraron proveedores en '{ciudad}'.")
            return
        for proveedor in proveedores:
            print(f"  {proveedor}")
        print(f"\n  Total: {len(proveedores)} proveedor(es)")

    def _buscar_por_nombre(self):
        """Busca proveedores por nombre."""
        print("\n--- Buscar proveedores por nombre ---")
        termino = input("  Nombre a buscar: ").strip()

        proveedores = self._proveedor_dao.buscar_por_nombre(termino)
        if not proveedores:
            print(f"  No se encontraron proveedores con '{termino}'.")
            return
        for proveedor in proveedores:
            print(f"  {proveedor}")
        print(f"\n  Encontrados: {len(proveedores)} proveedor(es)")

    def _actualizar_proveedor(self):
        """Actualiza la información de un proveedor existente."""
        print("\n--- Actualizar proveedor ---")
        try:
            id_proveedor = int(input("  ID del proveedor a actualizar: ").strip())
        except ValueError:
            print("  [!] ID debe ser un numero entero.")
            return

        proveedor = self._proveedor_dao.consultar_por_id(id_proveedor)
        if not proveedor:
            print(f"  [!] No se encontro proveedor con ID {id_proveedor}.")
            return

        print(f"  Proveedor actual: {proveedor}")
        print("  (Deje vacio para mantener el valor actual)\n")

        nombre = input(f"  Nombre [{proveedor.nombre}]: ").strip()
        telefono = input(f"  Telefono [{proveedor.telefono}]: ").strip()
        correo = input(f"  Correo [{proveedor.correo}]: ").strip()
        direccion = input(f"  Direccion [{proveedor.direccion}]: ").strip()
        ciudad = input(f"  Ciudad [{proveedor.ciudad}]: ").strip()
        horario = input(f"  Horario [{proveedor.horario}]: ").strip()
        activo_txt = input(f"  Activo (s/n) [{'s' if proveedor.activo else 'n'}]: ").strip().lower()

        if nombre:
            proveedor.nombre = nombre
        if telefono:
            proveedor.telefono = telefono
        if correo:
            proveedor.correo = correo
        if direccion:
            proveedor.direccion = direccion
        if ciudad:
            proveedor.ciudad = ciudad
        if horario:
            proveedor.horario = horario
        if activo_txt in ("s", "n"):
            proveedor.activo = activo_txt == "s"

        if self._proveedor_dao.actualizar(proveedor):
            print("  [OK] Proveedor actualizado correctamente.")
        else:
            print("  [!] No se pudo actualizar el proveedor.")

    def _eliminar_proveedor(self):
        """Elimina un proveedor previa confirmación."""
        print("\n--- Eliminar proveedor ---")
        try:
            id_proveedor = int(input("  ID del proveedor a eliminar: ").strip())
        except ValueError:
            print("  [!] ID debe ser un numero entero.")
            return

        proveedor = self._proveedor_dao.consultar_por_id(id_proveedor)
        if not proveedor:
            print(f"  [!] No se encontro proveedor con ID {id_proveedor}.")
            return

        print(f"  Proveedor: {proveedor}")
        confirmacion = input("  Esta seguro de eliminar? (s/n): ").strip().lower()

        if confirmacion == "s":
            if self._proveedor_dao.eliminar(id_proveedor):
                print("  [OK] Proveedor eliminado correctamente.")
            else:
                print("  [!] No se pudo eliminar el proveedor.")
        else:
            print("  Operacion cancelada.")
