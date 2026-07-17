"""
PetConnect - Sistema de Gestión para Mascotas
Punto de entrada principal de la aplicación.

Módulos:
    - Gestión de Usuarios (CRUD)
    - Gestión de Mascotas (CRUD)
    - Gestión de Productos / Tienda (CRUD)
    - Gestión de Proveedores de Servicio (CRUD)

Tecnologías:
    - Python 3.x
    - MySQL 8.x (conexión vía mysql-connector-python)
    - Patrón DAO (Data Access Object)
    - Arquitectura por capas (Modelo - DAO - Vista)

Autor: Daniel Santiago
Fecha: Junio 2026
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from conexion.conexion_bd import ConexionBD
from vista.menu_principal import MenuPrincipal


def main():
    """Función principal que inicia la aplicación PetConnect."""
    print("\n  Conectando a la base de datos PetConnect...")

    conexion_bd = ConexionBD()
    conexion = conexion_bd.obtener_conexion()

    if conexion is None:
        print("  [ERROR] No se pudo establecer conexion con la base de datos.")
        print("  Verifique que MySQL este ejecutandose y los datos")
        print("  de conexion en config/db_config.py sean correctos.")
        sys.exit(1)

    print("  [OK] Conexion establecida exitosamente.\n")

    try:
        menu = MenuPrincipal()
        menu.iniciar()
    except KeyboardInterrupt:
        print("\n\n  Aplicacion interrumpida por el usuario.")
    finally:
        conexion_bd.cerrar_conexion()
        print("  [OK] Conexion a la base de datos cerrada.")


if __name__ == "__main__":
    main()
