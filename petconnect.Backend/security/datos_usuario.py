"""
Validaciones comunes de los datos de una cuenta (item 4.11, A-18).

Antes vivian dentro de api.py y la consola (vista/menu_usuarios.py) no podia
usarlas sin importar api.py, que carga el .env y arranca Flask (A-41). Ahora la
API y la consola llaman a las MISMAS funciones, asi que aceptan y rechazan
exactamente los mismos nombres y correos (como security/politica.py hace con
las contrasenas desde el 4.1).

- validar_nombre: A-05. Un nombre son palabras de letras (con tildes y n con
  virgulilla) separadas por espacios; nada de numeros, URL ni HTML.
- validar_formato_correo: formato y largo maximo. NO consulta el DNS: esa parte
  (registros MX) sigue en api.py, porque necesita red y solo la usa la API.
- validar_telefono: item 4.19. Es la regla de las solicitudes de adopcion (3.6),
  que antes vivia en api.py; ahora la usa tambien la consola al registrar y al
  actualizar un usuario.

Cada funcion devuelve el mensaje de error o None si el dato sirve. Los mensajes
de nombre y correo van sin tildes, como el resto de la API; el del telefono las
lleva porque la web y el movil lo muestran tal cual desde el 3.6. Los mensajes
nunca repiten el dato recibido (Ley 1581).
"""
import re

# A-05: dentro de una palabra se permite ' o - (O'Neil, Perez-Gil) y al final un
# punto (Ma. Jose). Sin numeros, ':', '/', '<' ni un punto pegado a otra palabra,
# asi que no cabe una URL (https://..., sitio-falso.example) ni HTML.
_PALABRA_NOMBRE = r"[^\W\d_]+(?:['\-][^\W\d_]+)*\.?"
_NOMBRE_REGEX = re.compile(rf"{_PALABRA_NOMBRE}(?: +{_PALABRA_NOMBRE})*")
NOMBRE_MIN, NOMBRE_MAX = 2, 60

_EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")
CORREO_MAX = 120     # como usuarios.correo y otp_pendientes.correo (varchar(120))

TELEFONO_MAX = 20                       # como usuarios.telefono y solicitudes.telefono
TELEFONO_DIGITOS_MIN, TELEFONO_DIGITOS_MAX = 7, 15   # 15: maximo internacional (E.164)
_TELEFONO_REGEX = re.compile(r"\+?[0-9 ]+")


def validar_nombre(nombre: str, etiqueta: str = "El nombre") -> str | None:
    """Mensaje de error si `nombre` no parece un nombre de persona; None si es valido.

    `etiqueta` solo cambia el comienzo del mensaje (la consola la usa para decir
    "Los apellidos ..."); la regla es la misma.
    """
    if not (NOMBRE_MIN <= len(nombre) <= NOMBRE_MAX) or not _NOMBRE_REGEX.fullmatch(nombre):
        return (f"{etiqueta} debe tener entre {NOMBRE_MIN} y {NOMBRE_MAX} caracteres y solo "
                "letras, espacios, guiones, apostrofos o puntos")
    return None


def validar_formato_correo(correo: str) -> str | None:
    """Mensaje de error si el correo esta vacio, mal escrito o es muy largo; None si sirve."""
    correo = (correo or "").strip()
    if not correo:
        return "El correo es requerido"
    if not _EMAIL_REGEX.match(correo):
        return "El formato del correo no es valido"
    # Item 4.6: en modo estricto un correo mas largo daria error al guardar
    if len(correo) > CORREO_MAX:
        return f"El correo no puede tener mas de {CORREO_MAX} caracteres"
    return None


def validar_telefono(telefono: str) -> str | None:
    """Vacio = no lo dio (es opcional). Solo numeros, espacios y un + al inicio."""
    if telefono == "":
        return None
    digitos = sum(c.isdigit() for c in telefono)
    if (len(telefono) > TELEFONO_MAX or not _TELEFONO_REGEX.fullmatch(telefono)
            or not (TELEFONO_DIGITOS_MIN <= digitos <= TELEFONO_DIGITOS_MAX)):
        return (f"El teléfono solo puede tener números, espacios y un + al inicio "
                f"(entre {TELEFONO_DIGITOS_MIN} y {TELEFONO_DIGITOS_MAX} dígitos)")
    return None
