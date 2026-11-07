"""
Script de carga inicial de datos (seed) para PetConnect.
Inserta las categorías, los productos y las mascotas en adopción de ejemplo.

Requiere que las tablas ya existan: primero se carga sql/schema.sql
(ver sql/README.md). Se puede ejecutar varias veces: no duplica filas.
    python seed.py
"""

import sys
import os
import secrets
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from conexion.conexion_bd import ConexionBD
from security.passwords import hash_password

# Dueño ficticio de las mascotas en adopción (mascotas.id_usuario es obligatorio).
# Queda inactivo y con una contraseña aleatoria que nadie conoce: no se puede usar para entrar.
REFUGIO = ("Refugio PetConnect", "(cuenta de ejemplo)", "refugio@petconnect.test")

CATEGORIAS = [
    (1, "Alimentos"),
    (2, "Accesorios"),
    (3, "Juguetes"),
    (4, "Higiene"),
]

# Fotos: Unsplash (licencia Unsplash, uso libre), de ejemplo.
# REVISAR-VETERINARIO: las descripciones marcadas hablan de alimentación o salud.
PRODUCTOS = [
    # REVISAR-VETERINARIO: alimentación (fórmula, proteínas)
    (1, "Alimento Premium para Perro",
    "Alimento balanceado de alta calidad para perros adultos. Fórmula rica en proteínas con pollo y arroz. Bolsa de 15kg.",
    89900, 25, "https://images.unsplash.com/photo-1589924691995-400dc9ecc119?w=400&h=400&fit=crop", True),
    # REVISAR-VETERINARIO: beneficio ortopédico
    (2, "Cama Ortopédica para Mascota",
    "Cama ortopédica con espuma viscoelástica para mascotas medianas y grandes. Funda lavable y antideslizante.",
    129900, 12, "https://images.unsplash.com/photo-1601758228041-f3b2795255f1?w=400&h=400&fit=crop", True),
    (2, "Collar Ajustable Reflectivo",
    "Collar ajustable con material reflectivo para paseos nocturnos seguros. Disponible en varias tallas.",
    34900, 50, "https://images.unsplash.com/photo-1599839575945-a9e5af0c3fa5?w=400&h=400&fit=crop", True),
    (3, "Juguete Interactivo para Gato",
    "Juguete interactivo con plumas y cascabel para estimular el instinto de caza de tu gato.",
    45900, 30, "https://images.unsplash.com/photo-1545249390-6bdfa286032f?w=400&h=400&fit=crop", True),
    # REVISAR-VETERINARIO: piel sensible e hipoalergénico
    (4, "Shampoo Hipoalergénico",
    "Shampoo suave para pieles sensibles. Fórmula sin parabenos ni sulfatos. Aroma a lavanda.",
    28900, 40, "https://images.unsplash.com/photo-1584797011906-3a8f260a4bbb?w=400&h=400&fit=crop", True),
    (2, "Transportadora para Mascotas",
    "Transportadora rígida aprobada para viajes en avión. Ventilación superior y lateral. Tamaño mediano.",
    159900, 8, "https://images.unsplash.com/photo-1548199973-03cce0bbc87b?w=400&h=400&fit=crop", True),
    # REVISAR-VETERINARIO: alimentación
    (1, "Alimento para Gato Adulto",
    "Alimento seco premium para gatos adultos con salmón y verduras. Bolsa de 10kg.",
    67900, 20, "https://images.unsplash.com/photo-1574158622682-e40e69881006?w=400&h=400&fit=crop", True),
    (2, "Correa Retráctil 5m",
    "Correa retráctil de 5 metros con freno ergonómico. Soporta hasta 30kg.",
    54900, 35, "https://images.unsplash.com/photo-1587300003388-59208cc962cb?w=400&h=400&fit=crop", True),
    (2, "Plato Comedero Doble Acero",
    "Comedero doble de acero inoxidable con base antideslizante. Ideal para comida y agua.",
    39900, 45, "https://images.unsplash.com/photo-1601758174114-e711c0cbaa69?w=400&h=400&fit=crop", True),
    # REVISAR-VETERINARIO: salud dental y talla apta
    (3, "Hueso Dental Masticable",
    "Hueso de nylon resistente para limpieza dental. Sabor a pollo. Apto para perros medianos.",
    18900, 60, "https://images.unsplash.com/photo-1583337130417-13104dec14a3?w=400&h=400&fit=crop", True),
    (4, "Arena para Gato Premium",
    "Arena aglomerante de alta absorción con control de olores. Bolsa de 10kg.",
    32900, 55, "https://images.unsplash.com/photo-1526336024174-e58f5cdd8e13?w=400&h=400&fit=crop", True),
    (2, "Rascador Torre para Gato",
    "Torre rascador de 3 niveles con plataformas, cueva y juguete colgante. Altura: 120cm.",
    189900, 6, "https://images.unsplash.com/photo-1518791841217-8f162f1e1131?w=400&h=400&fit=crop", True),
]

# (nombre, especie, raza, sexo, edad_aprox en años, color, foto, observaciones)
# edad_aprox es un número entero: el modo estricto rechaza textos como "2 años".
# color va en None: no se sabe el color real y no se inventa. Hasta el ítem 3.4
# (A-22) aquí se guardaba el tamaño ("Tamaño Grande"). En la BD de desarrollo
# estas mascotas se cargaron por otra vía, con "Grande"/"Pequenio" en color y
# Nala con 6. La migración sql/migraciones/2026-11-06_mascotas_ejemplo.sql
# corrige las dos cosas en bases ya cargadas.
# Fotos: Unsplash (licencia Unsplash, uso libre), de ejemplo.
# REVISAR-VETERINARIO: las descripciones hablan de vacunas, esterilización,
# desparasitación y cuidados. Un veterinario debe validarlas antes de publicar.
MASCOTAS_ADOPCION = [
    # REVISAR-VETERINARIO: vacunada, esterilizada y desparasitada
    ("Luna", "Perro", "Labrador Retriever", "hembra", 2, None,
    "https://images.unsplash.com/photo-1552053831-71594a27632d?w=400&h=400&fit=crop",
    "Luna es una labradora muy cariñosa y juguetona. Le encanta correr y jugar con pelotas. Vacunada, esterilizada y desparasitada. Busca un hogar con espacio para correr."),
    # REVISAR-VETERINARIO: vacunado y esterilizado
    ("Milo", "Gato", "Mestizo", "macho", 1, None,
    "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=400&h=400&fit=crop",
    "Milo es un gato tranquilo y muy cariñoso. Le gusta dormir en el sol y que lo acaricien. Ideal para apartamentos. Vacunado y esterilizado."),
    ("Rocky", "Perro", "Bulldog Francés", "macho", 3, None,
    "https://images.unsplash.com/photo-1583511655857-d19b40a7a54e?w=400&h=400&fit=crop",
    "Rocky es un bulldog muy sociable y tranquilo. Se lleva bien con niños y otras mascotas. Perfecto compañero para la familia."),
    # REVISAR-VETERINARIO: en proceso de vacunación y edad de adopción (6 meses)
    ("Nala", "Gato", "Siamés", "hembra", 0, None,  # 6 meses: menos de 1 año
    "https://images.unsplash.com/photo-1573865526739-10659fec78a5?w=400&h=400&fit=crop",
    "Nala es una gatita siamés muy curiosa y activa. Le encanta explorar y jugar. En proceso de vacunación. Busca un hogar amoroso."),
    # REVISAR-VETERINARIO: vacunado y esterilizado
    ("Max", "Perro", "Golden Retriever", "macho", 4, None,
    "https://images.unsplash.com/photo-1633722715463-d30f4f325e24?w=400&h=400&fit=crop",
    "Max es un golden retriever noble y obediente. Entrenado en comandos básicos. Excelente con niños. Vacunado y esterilizado."),
    # REVISAR-VETERINARIO: cuidado del pelo (cepillado)
    ("Cleo", "Gato", "Persa", "hembra", 2, None,
    "https://images.unsplash.com/photo-1596854407944-bf87f6fdd49e?w=400&h=400&fit=crop",
    "Cleo es una gata persa de pelo largo. Tranquila y elegante, perfecta para personas que buscan compañía serena. Requiere cepillado regular."),
]


def seed():
    bd = ConexionBD()
    conn = bd.obtener_conexion()
    if conn is None:
        print("[ERROR] No se pudo conectar a la base de datos.")
        sys.exit(1)
    # Item 4.5 (A-11): la conexion es prestada por el pool; los finally cierran el
    # cursor y la devuelven aunque alguna insercion falle.
    try:
        cursor = conn.cursor()
        try:
            _cargar_datos(cursor)
            conn.commit()
        finally:
            cursor.close()
    finally:
        conn.close()
    print("\n✓ Seed completado exitosamente.")


def _cargar_datos(cursor):
    """Inserta categorias, productos, la cuenta del refugio y las mascotas de ejemplo."""

    # --- Categorías de producto (la tabla la crea sql/schema.sql) ---
    print("\n→ Insertando categorías...")
    for id_cat, nombre in CATEGORIAS:
        cursor.execute("""
            INSERT INTO categorias_producto (id_categoria_producto, nombre)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE nombre = VALUES(nombre)
        """, (id_cat, nombre))
    print(f"  [OK] {len(CATEGORIAS)} categorías listas.")

    # --- Productos ---
    print("→ Insertando productos...")
    insertados = 0
    for id_cat, nombre, descripcion, precio, stock, imagen_url, activo in PRODUCTOS:
        cursor.execute("""
            INSERT INTO productos (id_categoria_producto, nombre, descripcion, precio, stock, imagen_url, activo)
            SELECT %s, %s, %s, %s, %s, %s, %s
            WHERE NOT EXISTS (SELECT 1 FROM productos WHERE nombre = %s)
        """, (id_cat, nombre, descripcion, precio, stock, imagen_url, activo, nombre))
        insertados += cursor.rowcount
    print(f"  [OK] {insertados} productos insertados (los duplicados se omitieron).")

    # --- Dueño ficticio de las mascotas en adopción ---
    print("→ Creando la cuenta de ejemplo del refugio...")
    nombres, apellidos, correo = REFUGIO
    cursor.execute("""
        INSERT INTO usuarios (nombres, apellidos, correo, password_hash, estado, verificado, acepta_datos)
        SELECT %s, %s, %s, %s, 'inactivo', 0, 0
        WHERE NOT EXISTS (SELECT 1 FROM usuarios WHERE correo = %s)
    """, (nombres, apellidos, correo, hash_password(secrets.token_urlsafe(32)), correo))
    cursor.execute("SELECT id_usuario FROM usuarios WHERE correo = %s", (correo,))
    id_refugio = cursor.fetchone()[0]

    # --- Mascotas en adopción ---
    print("→ Insertando mascotas en adopción...")
    insertadas = 0
    for nombre, especie, raza, sexo, edad_aprox, color, foto, observaciones in MASCOTAS_ADOPCION:
        cursor.execute("""
            INSERT INTO mascotas (id_usuario, nombre, especie, raza, sexo, edad_aprox, color, foto, observaciones, estado)
            SELECT %s, %s, %s, %s, %s, %s, %s, %s, %s, 'en_adopcion'
            WHERE NOT EXISTS (SELECT 1 FROM mascotas WHERE nombre = %s AND estado = 'en_adopcion')
        """, (id_refugio, nombre, especie, raza, sexo, edad_aprox, color, foto, observaciones, nombre))
        insertadas += cursor.rowcount
    print(f"  [OK] {insertadas} mascotas insertadas (los duplicados se omitieron).")


if __name__ == "__main__":
    seed()
