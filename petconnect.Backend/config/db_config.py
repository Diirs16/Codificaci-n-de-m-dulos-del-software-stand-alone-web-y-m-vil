import os
from dotenv import load_dotenv
load_dotenv()

# Modo estricto: la BD rechaza con error los datos invalidos en lugar de
# guardarlos vacios en silencio (NC-009). Debe coincidir con sql/schema.sql.
SQL_MODE_ESTRICTO = (
    "STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,"
    "ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION"
)

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
