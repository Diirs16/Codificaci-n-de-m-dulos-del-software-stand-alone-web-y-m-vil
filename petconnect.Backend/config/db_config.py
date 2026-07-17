import os
from dotenv import load_dotenv
load_dotenv()

DB_CONFIG = {
    "host":      os.getenv("DB_HOST", "localhost"),
    "port":      int(os.getenv("DB_PORT", 3310)),
    "database":  os.getenv("DB_NAME", "petconnect"),
    "user":      os.getenv("DB_USER", "root"),
    "password":  os.getenv("DB_PASSWORD", ""),
    "charset":   "utf8mb4",
    "collation": "utf8mb4_unicode_ci",
    "autocommit": True,
}
