"""
Vista del módulo de Productos (Tienda/Marketplace).
Interfaz de consola para gestionar las operaciones CRUD de productos.
"""

from dao.producto_dao import ProductoDAO
from modelo.producto import Producto


class MenuProductos:
    """Menú interactivo para la gestión de productos."""

    def __init__(self):
        self._producto_dao = ProductoDAO()

    def mostrar_menu(self):
        """Muestra el submenú de gestión de productos."""
        while True:
            print("\n" + "=" * 55)
            print("       GESTION DE PRODUCTOS - PetConnect")
            print("=" * 55)
            print("  1. Registrar producto")
            print("  2. Consultar todos los productos")
            print("  3. Buscar producto por ID")
            print("  4. Buscar productos por categoria")
            print("  5. Buscar productos por nombre")
            print("  6. Actualizar producto")
            print("  7. Eliminar producto")
            print("  0. Volver al menu principal")
            print("-" * 55)

            opcion = input("  Seleccione una opcion: ").strip()

            if opcion == "1":
                self._registrar_producto()
            elif opcion == "2":
                self._consultar_todos()
            elif opcion == "3":
                self._buscar_por_id()
            elif opcion == "4":
                self._buscar_por_categoria()
            elif opcion == "5":
                self._buscar_por_nombre()
            elif opcion == "6":
                self._actualizar_producto()
            elif opcion == "7":
                self._eliminar_producto()
            elif opcion == "0":
                break
            else:
                print("  [!] Opcion no valida.")

    def _registrar_producto(self):
        """Solicita datos y registra un nuevo producto."""
        print("\n--- Registro de nuevo producto ---")
        try:
            id_categoria = int(input("  ID de la categoria: ").strip())
        except ValueError:
            print("  [!] ID debe ser un numero entero.")
            return

        nombre = input("  Nombre del producto: ").strip()
        descripcion = input("  Descripcion: ").strip()

        try:
            precio = float(input("  Precio: ").strip())
        except ValueError:
            print("  [!] Precio debe ser un valor numerico.")
            return

        try:
            stock = int(input("  Stock disponible: ").strip())
        except ValueError:
            print("  [!] Stock debe ser un numero entero.")
            return

        imagen_url = input("  URL de imagen (opcional): ").strip() or None

        if not nombre:
            print("  [!] El nombre del producto es obligatorio.")
            return

        producto = Producto(
            id_categoria_producto=id_categoria,
            nombre=nombre,
            descripcion=descripcion,
            precio=precio,
            stock=stock,
            imagen_url=imagen_url
        )

        if self._producto_dao.insertar(producto):
            print(f"  [OK] Producto registrado con ID: {producto.id_producto}")
        else:
            print("  [!] No se pudo registrar el producto.")

    def _consultar_todos(self):
        """Muestra todos los productos registrados."""
        print("\n--- Lista de productos ---")
        productos = self._producto_dao.consultar_todos()
        if not productos:
            print("  No hay productos registrados.")
            return
        for producto in productos:
            print(f"  {producto}")
        print(f"\n  Total: {len(productos)} producto(s)")

    def _buscar_por_id(self):
        """Busca y muestra un producto por su ID."""
        print("\n--- Buscar producto por ID ---")
        try:
            id_producto = int(input("  ID del producto: ").strip())
        except ValueError:
            print("  [!] ID debe ser un numero entero.")
            return

        producto = self._producto_dao.consultar_por_id(id_producto)
        if producto:
            print(f"  {producto}")
            print(f"  Descripcion: {producto.descripcion}")
        else:
            print(f"  [!] No se encontro producto con ID {id_producto}.")

    def _buscar_por_categoria(self):
        """Muestra los productos de una categoría."""
        print("\n--- Productos por categoria ---")
        try:
            id_categoria = int(input("  ID de la categoria: ").strip())
        except ValueError:
            print("  [!] ID debe ser un numero entero.")
            return

        productos = self._producto_dao.consultar_por_categoria(id_categoria)
        if not productos:
            print(f"  No se encontraron productos en la categoria {id_categoria}.")
            return
        for producto in productos:
            print(f"  {producto}")
        print(f"\n  Total: {len(productos)} producto(s)")

    def _buscar_por_nombre(self):
        """Busca productos por nombre."""
        print("\n--- Buscar productos por nombre ---")
        termino = input("  Nombre a buscar: ").strip()

        productos = self._producto_dao.buscar_por_nombre(termino)
        if not productos:
            print(f"  No se encontraron productos con '{termino}'.")
            return
        for producto in productos:
            print(f"  {producto}")
        print(f"\n  Encontrados: {len(productos)} producto(s)")

    def _actualizar_producto(self):
        """Actualiza la información de un producto existente."""
        print("\n--- Actualizar producto ---")
        try:
            id_producto = int(input("  ID del producto a actualizar: ").strip())
        except ValueError:
            print("  [!] ID debe ser un numero entero.")
            return

        producto = self._producto_dao.consultar_por_id(id_producto)
        if not producto:
            print(f"  [!] No se encontro producto con ID {id_producto}.")
            return

        print(f"  Producto actual: {producto}")
        print("  (Deje vacio para mantener el valor actual)\n")

        nombre = input(f"  Nombre [{producto.nombre}]: ").strip()
        descripcion = input(f"  Descripcion [{producto.descripcion}]: ").strip()
        precio_txt = input(f"  Precio [{producto.precio}]: ").strip()
        stock_txt = input(f"  Stock [{producto.stock}]: ").strip()
        activo_txt = input(f"  Activo (s/n) [{'s' if producto.activo else 'n'}]: ").strip().lower()

        if nombre:
            producto.nombre = nombre
        if descripcion:
            producto.descripcion = descripcion
        if precio_txt:
            producto.precio = float(precio_txt)
        if stock_txt:
            producto.stock = int(stock_txt)
        if activo_txt in ("s", "n"):
            producto.activo = activo_txt == "s"

        if self._producto_dao.actualizar(producto):
            print("  [OK] Producto actualizado correctamente.")
        else:
            print("  [!] No se pudo actualizar el producto.")

    def _eliminar_producto(self):
        """Elimina un producto previa confirmación."""
        print("\n--- Eliminar producto ---")
        try:
            id_producto = int(input("  ID del producto a eliminar: ").strip())
        except ValueError:
            print("  [!] ID debe ser un numero entero.")
            return

        producto = self._producto_dao.consultar_por_id(id_producto)
        if not producto:
            print(f"  [!] No se encontro producto con ID {id_producto}.")
            return

        print(f"  Producto: {producto}")
        confirmacion = input("  Esta seguro de eliminar? (s/n): ").strip().lower()

        if confirmacion == "s":
            if self._producto_dao.eliminar(id_producto):
                print("  [OK] Producto eliminado correctamente.")
            else:
                print("  [!] No se pudo eliminar el producto.")
        else:
            print("  Operacion cancelada.")
