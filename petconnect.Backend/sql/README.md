# Base de datos de PetConnect

| Archivo | Qué hace |
|---|---|
| `schema.sql` | Crea las 32 tablas y los catálogos fijos (roles y planes). **Solo estructura, sin datos personales.** |
| `../seed.py` | Inserta datos de ejemplo: categorías, 12 productos, una cuenta ficticia de refugio y 6 mascotas en adopción. |

Motor probado: **MariaDB 10.4.32** (XAMPP) en el puerto **3310**. También sirve en MySQL 8.0.16 o superior
(necesario para que se cumplan las reglas `CHECK`).

## Orden para crear la base desde cero

Desde la carpeta `petconnect.Backend`. Si `mysql` no se reconoce, usa la ruta completa de XAMPP:
`C:\xampp\mysql\bin\mysql.exe`.

**1. Crear la base vacía** (pide la contraseña de MySQL):

```bash
mysql -u root -p -P 3310 -e "CREATE DATABASE IF NOT EXISTS petconnect CHARACTER SET utf8mb4 COLLATE utf8mb4_spanish_ci"
```

**2. Crear las tablas** (`source` funciona igual en PowerShell y en Git Bash):

```bash
mysql -u root -p -P 3310 petconnect -e "source sql/schema.sql"
```

**3. Cargar los datos de ejemplo** (con el `.venv` de la raíz y el `.env` ya configurado):

```bash
../.venv/Scripts/python seed.py
```

**4. Comprobar:** con la API encendida (`python api.py`), abre
<http://localhost:5000/api/mascotas/adopcion>. Debe devolver **6 mascotas**.

`schema.sql` usa `CREATE TABLE IF NOT EXISTS` e `INSERT IGNORE`, y `seed.py` no duplica filas, así que repetir los
pasos no borra nada.

## Reglas que pone la base de datos

- **Modo SQL estricto** (`STRICT_TRANS_TABLES`): un dato inválido produce un error en lugar de guardarse vacío
  en silencio. Se activa en `schema.sql` y en cada conexión de la API (`config/db_config.py`). Antes, el estado
  `en_adopcion` se guardaba vacío y el catálogo de adopción salía sin mascotas (NC-009).
- **`mascotas.estado`** acepta: `activa`, `en_adopcion`, `perdida`, `adoptada`, `fallecida`.
- **`aplicaciones_vacuna`**: la regla `chk_aplicacion_fechas` exige que `fecha_proxima` sea posterior a
  `fecha_aplicacion` (NC-010).

## ¿Ya tenías la base creada antes del 03/11/2026?

Tu tabla `mascotas` no tiene el estado `en_adopcion` (las mascotas en adopción quedaron con el estado vacío) y
`aplicaciones_vacuna` no tiene la regla de fechas. `schema.sql` no modifica tablas que ya existen; para eso está la
migración `migraciones/2026-11-03_estado_en_adopcion.sql`. Desde la carpeta `petconnect.Backend`:

**1. Respaldo** (fuera del repositorio: contiene datos personales y **nunca** se sube a git):

```bash
mysqldump -u root -p -P 3310 petconnect --result-file="$HOME/respaldo_petconnect_2026-11-03.sql"
```

En PowerShell cambia `$HOME` por `$env:USERPROFILE`. Se usa `--result-file` en vez de `>` porque en PowerShell `>`
guarda el archivo en otra codificación.

**2. Migración:**

```bash
mysql -u root -p -P 3310 petconnect -e "source sql/migraciones/2026-11-03_estado_en_adopcion.sql"
```

**3. Comprobar** que ninguna mascota quedó con el estado vacío (la consulta solo muestra conteos):

```bash
mysql -u root -p -P 3310 petconnect -e "SELECT estado, COUNT(*) AS total FROM mascotas GROUP BY estado"
```

No debe aparecer una fila con el estado vacío, y `en_adopcion` debe tener tus mascotas de adopción (6 si cargaste
`seed.py`).

La migración trabaja siempre en modo estricto y se puede ejecutar varias veces. Si se detiene con un error:

- **`Data truncated for column 'estado'`**: alguna mascota tiene un estado que no está en la lista nueva. Ese valor
  **no se pierde** (la columna queda como texto mientras tanto). Cámbialo por uno válido y vuelve a ejecutar el paso 2.
- **`CONSTRAINT chk_aplicacion_fechas failed`**: hay vacunas con la próxima dosis igual o anterior a la aplicación.
  Corrige esas fechas y vuelve a ejecutar el paso 2.

## Prueba automática

`tests/test_esquema.py` revisa este archivo sin conectarse a la base. Para probarlo de verdad contra MariaDB,
la prueba crea una base temporal `petconnect_prueba`, carga `schema.sql` y `seed.py`, consulta la API y al final
**borra solo esa base temporal**:

```bash
PETCONNECT_PRUEBA_BD=1 ../.venv/Scripts/python -m unittest tests.test_esquema -v
```

En PowerShell: `$env:PETCONNECT_PRUEBA_BD="1"; ../.venv/Scripts/python -m unittest tests.test_esquema -v`
