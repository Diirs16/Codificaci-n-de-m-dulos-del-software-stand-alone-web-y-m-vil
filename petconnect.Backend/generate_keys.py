"""
Genera las claves de seguridad de PetConnect (JWT_SECRET y FERNET_KEY) SIN borrar nada
(item 6.3 de PRIORIDADES, A-16).

- Si el archivo .env de esta carpeta NO existe: lo crea copiando .env.example y llena
  las dos claves. Despues completa tu DB_PASSWORD y el correo.
- Si YA existe: solo llena las claves que falten (linea vacia como "JWT_SECRET=" o sin
  linea). Todo lo demas (contrasena de la BD, correo, comentarios) queda igual, byte a
  byte. Si las dos claves ya tienen valor, el archivo no se toca.

Se puede correr las veces que quieras y desde cualquier carpeta: siempre usa el .env de
la carpeta del backend (la misma que lee api.py).

Nunca imprime el valor de una clave, ni siquiera una parte.

Uso:
    python generate_keys.py
"""
import codecs
import os
import re
import secrets
import tempfile
from pathlib import Path

from cryptography.fernet import Fernet

CARPETA = Path(__file__).resolve().parent
RUTA_ENV = CARPETA / ".env"
RUTA_PLANTILLA = CARPETA / ".env.example"

# Como se crea cada clave. JWT_SECRET: 32 bytes al azar en hexadecimal (64 caracteres),
# lo mismo que recomienda .env.example. FERNET_KEY: el formato que exige Fernet.
GENERADORES = {
    "JWT_SECRET": lambda: secrets.token_hex(32),
    "FERNET_KEY": lambda: Fernet.generate_key().decode(),
}

CREADA = "creada"
YA_ESTABA = "ya estaba"


def _patron(nombre):
    # "NOMBRE=valor", con espacios opcionales y "export " opcional. Una linea que empieza
    # con "#" es un comentario y no coincide: una clave comentada no cuenta.
    return re.compile(r"^(\s*(?:export\s+)?" + re.escape(nombre) + r"\s*=)(.*)$")


def _separar_comentario(resto):
    """Separa "valor  # comentario" en ("valor", "  # comentario")."""
    comentario = re.search(r"\s+#.*$", resto)
    if comentario:
        return resto[:comentario.start()], comentario.group(0)
    return resto, ""


def _esta_vacio(valor):
    return valor.strip() in ("", '""', "''")


def completar_texto(texto):
    """
    Recibe el contenido de un archivo de entorno y devuelve (texto_nuevo, estado).
    estado dice, para cada clave, si se creo o si ya estaba. No toca ninguna otra linea.
    """
    lineas = texto.splitlines(keepends=True)
    fin_de_linea = "\r\n" if "\r\n" in texto else "\n"
    estado = {}
    faltantes = []

    for nombre, generar_valor in GENERADORES.items():
        patron = _patron(nombre)
        ultima_vacia = None
        tiene_valor = False
        for i, linea in enumerate(lineas):
            cuerpo = linea.rstrip("\r\n")
            m = patron.match(cuerpo)
            if not m:
                continue
            valor, _ = _separar_comentario(m.group(2))
            if _esta_vacio(valor):
                ultima_vacia = i
            else:
                tiene_valor = True

        if tiene_valor:
            estado[nombre] = YA_ESTABA
        elif ultima_vacia is not None:
            # Se llena la ULTIMA linea vacia: si la clave se repite, python-dotenv usa
            # la ultima. Se conserva el comentario de la misma linea, si lo hay.
            linea = lineas[ultima_vacia]
            cuerpo = linea.rstrip("\r\n")
            fin = linea[len(cuerpo):]
            m = _patron(nombre).match(cuerpo)
            _, comentario = _separar_comentario(m.group(2))
            lineas[ultima_vacia] = m.group(1) + generar_valor() + comentario + fin
            estado[nombre] = CREADA
        else:
            faltantes.append(f"{nombre}={generar_valor()}")
            estado[nombre] = CREADA

    if faltantes:
        if lineas and not lineas[-1].endswith(("\n", "\r")):
            lineas[-1] += fin_de_linea
        if lineas:
            lineas.append(fin_de_linea)
        lineas.append("# Claves de seguridad (agregadas por generate_keys.py - NUNCA compartir)"
                      + fin_de_linea)
        lineas.extend(linea + fin_de_linea for linea in faltantes)

    return "".join(lineas), estado


def _escribir_seguro(ruta, datos):
    """
    Escribe primero en un archivo temporal de la misma carpeta y luego lo pone en lugar
    del original (os.replace). Si algo falla a mitad, el archivo original queda entero.
    """
    descriptor, temporal = tempfile.mkstemp(dir=ruta.parent, prefix=".generate_keys-",
                                            suffix=".tmp")
    try:
        with os.fdopen(descriptor, "wb") as archivo:
            archivo.write(datos)
        os.replace(temporal, ruta)
    except BaseException:
        if os.path.exists(temporal):
            os.remove(temporal)
        raise


def generar(ruta_env=RUTA_ENV, ruta_plantilla=RUTA_PLANTILLA):
    """
    Completa (o crea) el archivo de entorno. Devuelve (estado, nuevo):
    estado = {"JWT_SECRET": "creada" | "ya estaba", "FERNET_KEY": ...}
    nuevo = True si el archivo no existia y se creo desde la plantilla.
    """
    ruta_env = Path(ruta_env)
    ruta_plantilla = Path(ruta_plantilla)
    nuevo = not ruta_env.exists()

    if nuevo:
        datos = ruta_plantilla.read_bytes() if ruta_plantilla.exists() else b""
    else:
        datos = ruta_env.read_bytes()

    bom = codecs.BOM_UTF8 if datos.startswith(codecs.BOM_UTF8) else b""
    try:
        texto = datos[len(bom):].decode("utf-8")
    except UnicodeDecodeError:
        raise SystemExit(
            f"[ERROR] {ruta_env.name} no esta guardado en UTF-8. No se toco nada: "
            "guardalo como UTF-8 (Bloc de notas > Guardar como > Codificacion) y vuelve a correrlo."
        )

    texto_nuevo, estado = completar_texto(texto)

    if nuevo or texto_nuevo != texto:
        _escribir_seguro(ruta_env, bom + texto_nuevo.encode("utf-8"))
    return estado, nuevo


def main(ruta_env=RUTA_ENV, ruta_plantilla=RUTA_PLANTILLA):
    estado, nuevo = generar(ruta_env, ruta_plantilla)
    nombre = Path(ruta_env).name
    if nuevo:
        print(f"[OK] {nombre} creado a partir de {Path(ruta_plantilla).name}.")
    else:
        print(f"[OK] {nombre} revisado. Las demas variables no se tocaron.")
    for clave, resultado in estado.items():
        if resultado == CREADA:
            print(f"     {clave}: creada")
        else:
            print(f"     {clave}: ya tenia valor, no se cambio")
    if nuevo:
        print()
        print(f"Ahora abre {nombre} y completa DB_PASSWORD (y el correo, si lo usas).")
    print()
    print(f"IMPORTANTE: Nunca subas {nombre} a GitHub ni compartas sus claves.")


if __name__ == "__main__":
    main()
