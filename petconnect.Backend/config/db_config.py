import os
from dotenv import load_dotenv
load_dotenv()

# Modo estricto: la BD rechaza con error los datos invalidos en lugar de
# guardarlos vacios en silencio (NC-009). Debe coincidir con sql/schema.sql.
SQL_MODE_ESTRICTO = (
    "STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,"
    "ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION"
)

TAMANO_POOL_POR_DEFECTO = 10
TAMANO_POOL_MAXIMO = 32      # limite de mysql-connector (pooling.CNX_POOL_MAXSIZE)


def tamano_pool(texto):
    """
    Item 4.5 (A-11, NC-003): cuantas conexiones tiene el pool (DB_POOL_SIZE).
    Vacio = 10. Un valor no valido detiene el arranque con un mensaje claro en vez
    de seguir con un numero inventado. MariaDB acepta 151 conexiones por defecto:
    con varios procesos (Gunicorn, item 4.6) procesos x tamano debe quedar debajo.
    """
    texto = (texto or "").strip()
    if not texto:
        return TAMANO_POOL_POR_DEFECTO
    try:
        tamano = int(texto)
    except ValueError:
        tamano = 0
    if not 1 <= tamano <= TAMANO_POOL_MAXIMO:
        raise ValueError(
            f"DB_POOL_SIZE debe ser un numero entero entre 1 y {TAMANO_POOL_MAXIMO} "
            f"(vacio = {TAMANO_POOL_POR_DEFECTO})"
        )
    return tamano


POOL_SIZE = tamano_pool(os.getenv("DB_POOL_SIZE"))

DB_CONFIG = {
    "host":      os.getenv("DB_HOST", "localhost"),
    "port":      int(os.getenv("DB_PORT", 3310)),
    "database":  os.getenv("DB_NAME", "petconnect"),
    "user":      os.getenv("DB_USER", "root"),
    "password":  os.getenv("DB_PASSWORD", ""),
    "charset":   "utf8mb4",
    "collation": "utf8mb4_unicode_ci",
    "autocommit": True,
    "sql_mode":  SQL_MODE_ESTRICTO,
}
