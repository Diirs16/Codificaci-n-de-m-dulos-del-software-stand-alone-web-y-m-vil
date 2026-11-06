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
- **`usuarios`**: `acepta_datos` vale 0 por defecto y la regla `chk_autorizacion_datos` exige que un 1 tenga
  `fecha_autorizacion_datos` y `version_politica_datos` (NC-005, Ley 1581).

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

## ¿Ya tenías la base creada antes del 05/11/2026? (autorización de datos, NC-005)

Antes, `usuarios.acepta_datos` valía 1 por defecto y la API lo ponía en 1 fijo, sin preguntar (Ley 1581, art. 9).
Ahora quien se registra marca una casilla y la base guarda **cuándo** autorizó y **qué versión** de la política
aceptó. La migración `migraciones/2026-11-05_autorizacion_datos.sql`:

- agrega `fecha_autorizacion_datos` y `version_politica_datos`;
- deja en `acepta_datos = 0` a los usuarios que no tienen esa prueba, es decir, a todos los que se registraron antes.
  Pueden seguir entrando, y no se les inventa una fecha;
- cambia el valor por defecto a 0 y agrega la regla `chk_autorizacion_datos` (un 1 sin fecha ni versión da error).

**Hazlo antes de arrancar la API nueva:** sin las columnas nuevas, crear una cuenta falla con 500. Desde la carpeta
`petconnect.Backend`, con un respaldo nuevo como el del paso 1 de arriba (cambia la fecha del nombre del archivo):

```bash
mysql -u root -p -P 3310 petconnect -e "source sql/migraciones/2026-11-05_autorizacion_datos.sql"
```

**Comprobar** (solo muestra conteos, no datos personales):

```bash
mysql -u root -p -P 3310 petconnect -e "SELECT acepta_datos, COUNT(*) AS total, COUNT(fecha_autorizacion_datos) AS con_fecha FROM usuarios GROUP BY acepta_datos"
```

Antes de la primera cuenta nueva, todas las filas deben estar en `acepta_datos = 0` con `con_fecha = 0`. La
migración se puede ejecutar varias veces: quien autorizó después conserva su 1.

## ¿Ya tenías las mascotas de ejemplo antes del 06/11/2026? (tamaño en `color` y edad de Nala, A-22)

Las 6 mascotas de ejemplo (Luna, Milo, Rocky, Nala, Max y Cleo) tenían el **tamaño** guardado en la columna `color`:
`seed.py` ponía “Tamaño Grande”, “Tamaño Mediano”…, y en la base de desarrollo, cargada por otra vía, dice “Grande”,
“Mediano” o “Pequenio”. Además ahí **Nala** (una gatita de 6 meses) quedó con `edad_aprox = 6`, que la ficha muestra
como 6 años. La migración `migraciones/2026-11-06_mascotas_ejemplo.sql`:

- deja ese `color` en `NULL` (sin dato: el color real no se conoce y no se inventa);
- cambia la edad de Nala de 6 a 0 (menos de 1 año), solo si sigue en 6.

Reconoce las mascotas de ejemplo por **nombre y especie**, y solo si están en adopción. No usa el id ni el dueño,
porque cambian de una base a otra. Una mascota con el mismo nombre pero otra especie u otro estado queda igual.
No cambia la estructura de ninguna tabla y se puede ejecutar varias veces.

Desde la carpeta `petconnect.Backend`, con un respaldo nuevo como el del paso 1 de arriba:

```bash
mysql -u root -p -P 3310 petconnect -e "source sql/migraciones/2026-11-06_mascotas_ejemplo.sql"
```

**Comprobar** (solo muestra datos de las mascotas, no de personas). Después de migrar, `color` debe salir `NULL` en
las 6 y Nala con `edad_aprox = 0`:

```bash
mysql -u root -p -P 3310 petconnect -e "SELECT id_mascota, nombre, edad_aprox, color FROM mascotas WHERE estado = 'en_adopcion'"
```

## Prueba automática

`tests/test_esquema.py` revisa este archivo sin conectarse a la base. Para probarlo de verdad contra MariaDB,
la prueba crea una base temporal `petconnect_prueba`, carga `schema.sql` y `seed.py`, consulta la API y al final
**borra solo esa base temporal**:

```bash
PETCONNECT_PRUEBA_BD=1 ../.venv/Scripts/python -m unittest tests.test_esquema -v
```

En PowerShell: `$env:PETCONNECT_PRUEBA_BD="1"; ../.venv/Scripts/python -m unittest tests.test_esquema -v`
