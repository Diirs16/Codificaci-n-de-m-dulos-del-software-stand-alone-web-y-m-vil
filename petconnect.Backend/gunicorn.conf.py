"""
Configuracion de Gunicorn para la API de PetConnect (item 5.2 de la auditoria, A-30).

Gunicorn es el servidor de produccion de Python: reemplaza a app.run(), que es solo
para desarrollo. Solo funciona en Linux (dentro del contenedor de Docker); en tu
computador con Windows se sigue usando "python api.py".

Se usa asi (lo hace el Dockerfile):
    gunicorn -c gunicorn.conf.py api:app

La prueba tests/test_docker_backend.py revisa estos valores.
"""
import sys

# Escucha en todas las interfaces DENTRO del contenedor: si escuchara en 127.0.0.1
# (como app.run), nadie fuera del contenedor (ni nginx) podria llegar a la API.
# Hacia fuera solo se publica lo que diga docker-compose.yml.
bind = "0.0.0.0:5000"

# UN proceso con 8 hilos, no varios procesos. El limite de peticiones (item 2.6)
# cuenta en la memoria del proceso: con 4 procesos cada uno llevaria su cuenta y
# el limite real pasaria de 5 a 20 intentos por minuto. Los hilos comparten esa
# memoria y el pool de conexiones (10 por defecto, DB_POOL_SIZE): 8 hilos caben.
workers = 1
worker_class = "gthread"
threads = 8

# Segundos maximos por peticion antes de reiniciar el proceso (bcrypt tarda ~0,25 s).
timeout = 30

# Sin registro de accesos: cada linea traeria la IP y la ruta de cada persona
# (datos personales, Ley 1581). Los errores si se registran (salida de errores).
accesslog = None
errorlog = "-"

# Sin "socket de control" (Gunicorn 25.1+): es una puerta para manejar Gunicorn con
# la herramienta gunicornc, que no usamos. Por defecto la crea en la carpeta personal
# del usuario, y el usuario petconnect del Dockerfile no tiene una: daba
# "Permission denied: '/home/petconnect'" al arrancar. Una puerta menos abierta.
control_socket_disable = True

# Codigo de salida que Gunicorn entiende como "el proceso no pudo arrancar":
# el proceso principal se detiene en vez de reintentarlo sin fin.
# Es Arbiter.WORKER_BOOT_ERROR; se copia el numero porque gunicorn.arbiter no se
# puede importar en Windows (las pruebas corren ahi).
ERROR_DE_ARRANQUE = 3


def post_worker_init(worker):
    """
    Gunicorn no ejecuta el bloque "if __name__ == '__main__'" de api.py. Aqui, ya
    cargada la API en el proceso que atiende, se hacen las mismas revisiones que
    hace "python api.py" (BD, tabla de OTP, columna version_sesion). Si algo
    falla, el proceso termina con ERROR_DE_ARRANQUE y Gunicorn se apaga con el
    aviso en el registro, en lugar de atender peticiones que darian 500.
    """
    import api

    if not api.preparar_arranque():
        sys.exit(ERROR_DE_ARRANQUE)
