# ================================================================
# PETCONNECT Backend — imagen de la API (item 5.2 de la auditoria, A-30)
#
# Construir (desde la carpeta raiz Evidecia):
#   docker build -t petconnect-api petconnect.Backend
#
# NO lleva secretos: el .dockerignore deja fuera el .env y las claves, y la
# configuracion (DB_*, JWT_SECRET, FERNET_KEY, correo) entra al arrancar por
# variables de entorno (env_file en docker-compose.yml). Nunca escribas aqui
# un ENV o ARG con una contrasena o clave: quedaria guardado en la imagen.
# La prueba tests/test_docker_backend.py revisa este archivo.
# ================================================================

# Python 3.14 (el mismo de la CI y del .venv) en su version "slim": Debian sin
# compiladores ni extras. Todas las dependencias traen paquetes ya compilados.
FROM python:3.14-slim

# Sin archivos .pyc, los print salen al momento en "docker logs" y pip sin cache
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Primero solo requirements.txt: si el codigo cambia pero las dependencias no,
# Docker reutiliza esta capa y no reinstala todo.
COPY requirements.txt .
RUN pip install -r requirements.txt

# El resto del codigo (lo que el .dockerignore deja pasar: sin .env, sin tests/,
# sin __pycache__). Los archivos quedan del administrador y solo de lectura para
# el usuario de la API: si alguien la vulnera, no puede cambiar el codigo.
COPY . .

# Usuario sin permisos de administrador (no root) para correr la API
RUN useradd --no-create-home --uid 10001 petconnect
USER petconnect

EXPOSE 5000

# Gunicorn con gunicorn.conf.py: 0.0.0.0:5000, 1 proceso con 8 hilos y las
# revisiones de arranque de la API (preparar_arranque)
CMD ["gunicorn", "-c", "gunicorn.conf.py", "api:app"]
