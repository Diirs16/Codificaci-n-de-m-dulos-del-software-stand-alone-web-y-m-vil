"""
Politica de contrasenas de PetConnect (requisito RS03; item 4.1, A-17, NC-004).

Una sola funcion para todo el backend: la API (/api/auth/register) y, desde el
item 4.11 (A-18), la consola (vista/menu_usuarios.py), para que las dos acepten
y rechacen exactamente las mismas contrasenas.

Reglas, en este orden (se devuelve el mensaje de la PRIMERA que falla):
  1. Minimo 8 caracteres.
  2. Maximo 64 caracteres y 72 bytes (bcrypt solo procesa 72; un emoji ocupa 4).
  3. Al menos una mayuscula (A-Z).
  4. Al menos una minuscula (a-z).  <- nueva en el 4.1: antes se aceptaba PETCONNECT1!
  5. Al menos un numero (0-9).
  6. Al menos un caracter especial de CARACTERES_ESPECIALES. RS03 no lo pide:
     es un control adicional del proyecto (documentado en NC-004).

Mayuscula y minuscula son solo A-Z y a-z (sin tildes ni n con virgulilla) para que
la web y el movil (src/utils/contrasena.js) den exactamente el mismo resultado.
Si cambia una regla, cambiarla aqui, en la web y en el movil.

Los mensajes van sin tildes, como el resto de la API, y la consola de Windows
los muestra sin simbolos raros.
"""
import re

from security.passwords import MAX_BYTES_BCRYPT

LARGO_MIN = 8
LARGO_MAX = 64
CARACTERES_ESPECIALES = '@ # ! " $ & ? ¡ - _ * .'

_MAYUSCULA = re.compile(r"[A-Z]")
_MINUSCULA = re.compile(r"[a-z]")
_NUMERO = re.compile(r"[0-9]")
_ESPECIAL = re.compile(r'[@#!"$&?¡\-_*.]')


def validar_contrasena(password: str) -> str | None:
    """Devuelve el mensaje de la primera regla que no se cumple, o None si la contrasena sirve."""
    if len(password) < LARGO_MIN:
        return f"La contrasena debe tener al menos {LARGO_MIN} caracteres"
    if len(password) > LARGO_MAX or len(password.encode("utf-8")) > MAX_BYTES_BCRYPT:
        return f"La contrasena debe tener maximo {LARGO_MAX} caracteres"
    if not _MAYUSCULA.search(password):
        return "La contrasena debe tener al menos una mayuscula"
    if not _MINUSCULA.search(password):
        return "La contrasena debe tener al menos una minuscula"
    if not _NUMERO.search(password):
        return "La contrasena debe tener al menos un numero"
    if not _ESPECIAL.search(password):
        return f"La contrasena debe tener al menos un caracter especial: {CARACTERES_ESPECIALES}"
    return None
