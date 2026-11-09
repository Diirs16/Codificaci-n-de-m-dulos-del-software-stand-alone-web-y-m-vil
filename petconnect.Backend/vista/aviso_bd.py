"""
Aviso de la consola cuando la base de datos falla (item 4.15 de PRIORIDADES).

Desde el 4.15, MascotaDAO y ProductoDAO ya no se tragan los errores de la BD: los
dejan subir. Cada menu los atrapa en su ciclo y llama a avisar_error_bd(), asi la
consola no se cierra con una traza y vuelve al menu.

Solo se muestra el numero del error de MySQL (por ejemplo 1452 = el dueno o la
categoria no existe). NUNCA el mensaje: puede traer datos personales, como
"Duplicate entry 'correo@...'" (Ley 1581).
"""


def avisar_error_bd(error):
    """Imprime un aviso corto sin el mensaje de MySQL."""
    codigo = getattr(error, "errno", None)
    if codigo is None or codigo < 0:
        # Sin numero: no hubo conexion (conexion_y_cursor lanza InterfaceError)
        print("  [!] La base de datos no respondio. Verifique que MySQL este "
              "ejecutandose e intente de nuevo.")
    else:
        print(f"  [!] No se pudo completar la operacion con la base de datos "
              f"(codigo MySQL {codigo}). Revise los datos e intente de nuevo.")
