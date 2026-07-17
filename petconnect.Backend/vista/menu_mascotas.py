"""
Vista del módulo de Mascotas.
Interfaz de consola para gestionar las operaciones CRUD de mascotas.
"""

from dao.mascota_dao import MascotaDAO
from dao.usuario_dao import UsuarioDAO
from modelo.mascota import Mascota


class MenuMascotas:
    """Menú interactivo para la gestión de mascotas."""

    def __init__(self):
        self._mascota_dao = MascotaDAO()
        self._usuario_dao = UsuarioDAO()

    def mostrar_menu(self):
        """Muestra el submenú de gestión de mascotas."""
        while True:
            print("\n" + "=" * 55)
            print("       GESTION DE MASCOTAS - PetConnect")
            print("=" * 55)
            print("  1. Registrar mascota")
            print("  2. Consultar todas las mascotas")
            print("  3. Buscar mascota por ID")
            print("  4. Buscar mascotas por dueno (ID usuario)")
            print("  5. Buscar mascotas por nombre")
            print("  6. Actualizar mascota")
            print("  7. Eliminar mascota")
            print("  0. Volver al menu principal")
            print("-" * 55)

            opcion = input("  Seleccione una opcion: ").strip()

            if opcion == "1":
                self._registrar_mascota()
            elif opcion == "2":
                self._consultar_todas()
            elif opcion == "3":
                self._buscar_por_id()
            elif opcion == "4":
                self._buscar_por_usuario()
            elif opcion == "5":
                self._buscar_por_nombre()
            elif opcion == "6":
                self._actualizar_mascota()
            elif opcion == "7":
                self._eliminar_mascota()
            elif opcion == "0":
                break
            else:
                print("  [!] Opcion no valida.")

    def _registrar_mascota(self):
        """Solicita datos y registra una nueva mascota."""
        print("\n--- Registro de nueva mascota ---")
        try:
            id_usuario = int(input("  ID del dueno (usuario): ").strip())
        except ValueError:
            print("  [!] ID debe ser un numero entero.")
            return

        usuario = self._usuario_dao.consultar_por_id(id_usuario)
        if not usuario:
            print(f"  [!] No existe usuario con ID {id_usuario}.")
            return

        print(f"  Dueno: {usuario.nombres} {usuario.apellidos}")

        nombre = input("  Nombre de la mascota: ").strip()
        especie = input("  Especie (perro/gato/ave/otro): ").strip()
        raza = input("  Raza: ").strip()
        sexo = input("  Sexo (macho/hembra/no_definido): ").strip()
        color = input("  Color: ").strip()
        peso_txt = input("  Peso (kg, dejar vacio si no sabe): ").strip()
        edad_txt = input("  Edad aproximada (anos, dejar vacio si no sabe): ").strip()
        observaciones = input("  Observaciones: ").strip()

        if not nombre or not especie:
            print("  [!] Nombre y especie son obligatorios.")
            return

        if sexo not in ("macho", "hembra", "no_definido"):
            sexo = "no_definido"

        peso = float(peso_txt) if peso_txt else None
        edad_aprox = int(edad_txt) if edad_txt else None

        mascota = Mascota(
            id_usuario=id_usuario,
            nombre=nombre,
            especie=especie,
            raza=raza,
            sexo=sexo,
            color=color,
            peso=peso,
            edad_aprox=edad_aprox,
            observaciones=observaciones
        )

        if self._mascota_dao.insertar(mascota):
            print(f"  [OK] Mascota registrada con ID: {mascota.id_mascota}")
        else:
            print("  [!] No se pudo registrar la mascota.")

    def _consultar_todas(self):
        """Muestra todas las mascotas registradas."""
        print("\n--- Lista de mascotas ---")
        mascotas = self._mascota_dao.consultar_todos()
        if not mascotas:
            print("  No hay mascotas registradas.")
            return
        for mascota in mascotas:
            print(f"  {mascota}")
        print(f"\n  Total: {len(mascotas)} mascota(s)")

    def _buscar_por_id(self):
        """Busca y muestra una mascota por su ID."""
        print("\n--- Buscar mascota por ID ---")
        try:
            id_mascota = int(input("  ID de la mascota: ").strip())
        except ValueError:
            print("  [!] ID debe ser un numero entero.")
            return

        mascota = self._mascota_dao.consultar_por_id(id_mascota)
        if mascota:
            print(f"  {mascota}")
            print(f"  Color: {mascota.color} | Observaciones: {mascota.observaciones}")
            print(f"  Fecha registro: {mascota.fecha_registro}")
        else:
            print(f"  [!] No se encontro mascota con ID {id_mascota}.")

    def _buscar_por_usuario(self):
        """Muestra las mascotas de un usuario específico."""
        print("\n--- Mascotas por dueno ---")
        try:
            id_usuario = int(input("  ID del usuario: ").strip())
        except ValueError:
            print("  [!] ID debe ser un numero entero.")
            return

        mascotas = self._mascota_dao.consultar_por_usuario(id_usuario)
        if not mascotas:
            print(f"  No se encontraron mascotas para el usuario {id_usuario}.")
            return
        for mascota in mascotas:
            print(f"  {mascota}")
        print(f"\n  Total: {len(mascotas)} mascota(s)")

    def _buscar_por_nombre(self):
        """Busca mascotas por nombre."""
        print("\n--- Buscar mascotas por nombre ---")
        termino = input("  Nombre a buscar: ").strip()

        mascotas = self._mascota_dao.buscar_por_nombre(termino)
        if not mascotas:
            print(f"  No se encontraron mascotas con '{termino}'.")
            return
        for mascota in mascotas:
            print(f"  {mascota}")
        print(f"\n  Encontradas: {len(mascotas)} mascota(s)")

    def _actualizar_mascota(self):
        """Actualiza la información de una mascota existente."""
        print("\n--- Actualizar mascota ---")
        try:
            id_mascota = int(input("  ID de la mascota a actualizar: ").strip())
        except ValueError:
            print("  [!] ID debe ser un numero entero.")
            return

        mascota = self._mascota_dao.consultar_por_id(id_mascota)
        if not mascota:
            print(f"  [!] No se encontro mascota con ID {id_mascota}.")
            return

        print(f"  Mascota actual: {mascota}")
        print("  (Deje vacio para mantener el valor actual)\n")

        nombre = input(f"  Nombre [{mascota.nombre}]: ").strip()
        especie = input(f"  Especie [{mascota.especie}]: ").strip()
        raza = input(f"  Raza [{mascota.raza}]: ").strip()
        color = input(f"  Color [{mascota.color}]: ").strip()
        peso_txt = input(f"  Peso [{mascota.peso}]: ").strip()
        estado = input(f"  Estado (activa/perdida/adoptada/fallecida) [{mascota.estado}]: ").strip()
        observaciones = input(f"  Observaciones [{mascota.observaciones}]: ").strip()

        if nombre:
            mascota.nombre = nombre
        if especie:
            mascota.especie = especie
        if raza:
            mascota.raza = raza
        if color:
            mascota.color = color
        if peso_txt:
            mascota.peso = float(peso_txt)
        if estado in ("activa", "perdida", "adoptada", "fallecida"):
            mascota.estado = estado
        if observaciones:
            mascota.observaciones = observaciones

        if self._mascota_dao.actualizar(mascota):
            print("  [OK] Mascota actualizada correctamente.")
        else:
            print("  [!] No se pudo actualizar la mascota.")

    def _eliminar_mascota(self):
        """Elimina una mascota previa confirmación."""
        print("\n--- Eliminar mascota ---")
        try:
            id_mascota = int(input("  ID de la mascota a eliminar: ").strip())
        except ValueError:
            print("  [!] ID debe ser un numero entero.")
            return

        mascota = self._mascota_dao.consultar_por_id(id_mascota)
        if not mascota:
            print(f"  [!] No se encontro mascota con ID {id_mascota}.")
            return

        print(f"  Mascota: {mascota}")
        confirmacion = input("  Esta seguro de eliminar? (s/n): ").strip().lower()

        if confirmacion == "s":
            if self._mascota_dao.eliminar(id_mascota):
                print("  [OK] Mascota eliminada correctamente.")
            else:
                print("  [!] No se pudo eliminar la mascota.")
        else:
            print("  Operacion cancelada.")
