# PetConnect

Plataforma para mascotas (adopción, tienda de productos y directorio de proveedores de servicios) hecha como
proyecto formativo del SENA (ficha 3235905). Tiene **cuatro formas de usarse** que comparten la misma base de
datos y la misma API REST:

| Módulo | Carpeta | Para qué |
|---|---|---|
| API (backend) | `petconnect.Backend/` | Servicio REST en Flask que usan la web y el móvil |
| Consola (stand-alone) | `petconnect.Backend/` (`main.py`) | Menús de texto para administrar usuarios, mascotas, productos y proveedores |
| Web | `PetConnect.Front/petconnect-app/` | Página en React para el navegador |
| Móvil | `PetConnect.Mobile/` | App en React Native + Expo (Android) |

Este README es la **puerta de entrada**: explica cómo levantar cada parte y enlaza las guías largas.

## 1. Tecnologías y versiones

| Tecnología | Versión | Dónde se fija |
|---|---|---|
| Python | 3.14 | `.venv` de la raíz, la CI y el `Dockerfile` de la API |
| Flask | 3.1.3 | `petconnect.Backend/requirements.txt` |
| mysql-connector-python | 9.1.0 | `petconnect.Backend/requirements.txt` |
| bcrypt / PyJWT / cryptography | 5.0.0 / 2.15.1 / 50.0.2 | `petconnect.Backend/requirements.txt` |
| Gunicorn (servidor de la API en Docker y Railway) | 26.2.0 | `petconnect.Backend/requirements.txt` |
| MariaDB (base de datos) | 10.4.32 en el PC (XAMPP, puerto 3310); 10.11 en Docker y Railway | `docker-compose.yml`, `petconnect.Backend/Dockerfile.bd` |
| Node.js | 24 | la CI y el `Dockerfile` de la web |
| React + Vite + Tailwind | 19 / 8 / 4 | `PetConnect.Front/petconnect-app/package.json` |
| Expo + React Native | 57 / 0.86 | `PetConnect.Mobile/package.json` |

**MariaDB** es una base de datos "prima" de MySQL: usa el mismo lenguaje SQL y el mismo conector
(`mysql-connector-python`). Por eso en el código y en algunos comandos se lee "MySQL", pero el motor real es
MariaDB. El esquema **no** se ha probado en MySQL 8 (ver `petconnect.Backend/sql/README.md`).

## 2. Estructura del repositorio

```
Evidecia/
├── petconnect.Backend/        # API Flask + consola (Python)
│   ├── api.py                 # API REST (puerto 5000)
│   ├── main.py                # Consola stand-alone
│   ├── seed.py                # Datos de ejemplo
│   ├── config/  conexion/  modelo/  dao/  vista/   # Capas (ver sección 9)
│   ├── security/  otp/  correo/                    # Contraseñas, JWT, cifrado, códigos y correo
│   ├── sql/                   # schema.sql, migraciones y su README
│   ├── tests/                 # Pruebas (unittest)
│   ├── Dockerfile  Dockerfile.bd  gunicorn.conf.py
│   └── .env.example           # Plantilla de variables (sin valores reales)
├── PetConnect.Front/petconnect-app/   # Web React + Vite
├── PetConnect.Mobile/                 # App Expo (con EJECUCION.md)
├── docker/                    # Plantillas de variables para docker compose
├── docker-compose.yml         # BD + API + web en contenedores
├── .github/workflows/ci.yml   # Integración continua (GitHub Actions)
├── Documentacion/             # Evidencias GA7/GA8/GA9, auditoría y guía de despliegue
├── VERIFICACION.md            # Guía de verificación del sistema
└── CLAUDE.md                  # Reglas para trabajar con Claude Code
```

## 3. Requisitos previos

- **Python 3.14** y un entorno virtual en la raíz (`Evidecia\.venv`).
- **MariaDB** escuchando en el puerto **3310** (XAMPP en el PC).
- **Node.js 24** (con `npm`) para la web y el móvil.
- **Android Studio** con el emulador (solo para el móvil; detalles en `PetConnect.Mobile/EJECUCION.md`).
- **Docker Desktop** (opcional, solo para la sección 5.5).

Los comandos de este README son para **Windows PowerShell 5.1**: van uno por bloque (ahí `&&` no existe) y cada
bloque dice desde qué carpeta se corre.

## 4. Crear la base de datos

Los pasos completos (crear la base, cargar `sql/schema.sql`, correr `seed.py` y comprobar) están en
[`petconnect.Backend/sql/README.md`](petconnect.Backend/sql/README.md), junto con las migraciones para quien ya
tenía la base creada. En resumen: primero `schema.sql` (34 tablas, sin datos personales) y luego `seed.py` (datos
de ejemplo inventados).

## 5. Cómo levantar cada módulo

### 5.1 API (backend)

La primera vez, crea el entorno virtual. Desde la raíz `Evidecia`:

```powershell
python -m venv .venv
```

Instala las dependencias. Desde `Evidecia\petconnect.Backend`:

```powershell
..\.venv\Scripts\python -m pip install -r requirements.txt
```

Crea tu `.env` a partir de `.env.example` y llena los valores (sección 6). Nunca subas el `.env` a Git.

Arranca la API. Desde `Evidecia\petconnect.Backend`:

```powershell
..\.venv\Scripts\python api.py
```

Debe mostrar `[OK] Conexion a la base de datos establecida.` y `[OK] API PetConnect corriendo en
http://127.0.0.1:5000`. Prueba en el navegador: <http://localhost:5000/api/productos>.

> La API no se recarga sola: si cambias código del backend, deténla con `Ctrl + C` y vuelve a arrancarla.

### 5.2 Consola (stand-alone)

Usa la misma base de datos y el mismo `.env` que la API. Desde `Evidecia\petconnect.Backend`:

```powershell
..\.venv\Scripts\python main.py
```

Abre el menú principal (usuarios, mascotas, productos y proveedores) con las opciones de registrar, consultar,
buscar, actualizar y eliminar.

### 5.3 Web

La primera vez, instala las dependencias. Desde `Evidecia\PetConnect.Front\petconnect-app`:

```powershell
npm ci
```

Arranca el servidor de desarrollo (con la API de la sección 5.1 encendida). Desde la misma carpeta:

```powershell
npm run dev
```

Abre <http://localhost:5173>. En desarrollo, Vite manda las llamadas a `/api` hacia `http://localhost:5000`
(ver `vite.config.js`), así que no hace falta configurar nada más.

### 5.4 Móvil

La primera vez, instala las dependencias. Desde `Evidecia\PetConnect.Mobile`:

```powershell
npm ci
```

Arranca Metro (el servidor que entrega el JavaScript a la app). Desde la misma carpeta:

```powershell
npm start
```

O compila e instala la app en el emulador de Android. Desde la misma carpeta:

```powershell
npm run android
```

En el emulador, la app llega a la API de tu PC por `10.0.2.2:5000`. El emulador, el APK, `JAVA_HOME` y los
problemas comunes están en [`PetConnect.Mobile/EJECUCION.md`](PetConnect.Mobile/EJECUCION.md).

### 5.5 Todo con Docker

Levanta la base de datos (MariaDB 10.11), la API (con Gunicorn) y la web (con nginx) en contenedores.

1. Copia `docker/bd.env.example` como `docker/bd.env` y `docker/api.env.example` como `docker/api.env`, y
   llénalos siguiendo las instrucciones de cada archivo (no se suben a Git).
2. Desde la raíz `Evidecia`:

   ```powershell
   docker compose up --build
   ```

3. Abre <http://localhost:8080>. Solo la web publica un puerto: la API y la BD quedan dentro de la red de Docker.
4. (Opcional) Datos de ejemplo. Desde la raíz `Evidecia`, con los contenedores encendidos:

   ```powershell
   docker compose exec api python seed.py
   ```

El esquema solo se carga la primera vez (con el volumen vacío). Más detalle en los comentarios de
`docker-compose.yml`.

## 6. Variables de entorno

Aquí van **solo los nombres**. Cada plantilla `.env.example` explica qué poner y cómo generar las claves; los
archivos `.env` reales nunca se suben a Git ni se pegan en un chat.

| Plantilla | Variables | Para qué |
|---|---|---|
| `petconnect.Backend/.env.example` | `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_POOL_SIZE` | Conexión a la base de datos y tamaño del pool |
| | `JWT_SECRET`, `FERNET_KEY` | Firmar las sesiones (JWT) y cifrar datos. `JWT_SECRET` es obligatorio |
| | `EMAIL_MODE`, `MAILTRAP_API_TOKEN`, `MAILTRAP_SENDER`, `GMAIL_USER`, `GMAIL_APP_PASSWORD` | Envío del código de verificación por correo |
| | `APP_ENV`, `FLASK_DEBUG`, `API_HOST` | Modo de desarrollo, depurador y dirección donde escucha `python api.py` |
| | `PROXY_CONFIABLE`, `CORS_ORIGENES` | Proxy de confianza (límite de intentos por IP real) y páginas que pueden llamar a la API |
| `docker/api.env.example` | `DB_USER`, `DB_PASSWORD`, `DB_POOL_SIZE`, `JWT_SECRET`, `FERNET_KEY`, `APP_ENV`, `CORS_ORIGENES` y las de correo | API dentro de Docker (la dirección de la BD y el proxy los pone el compose) |
| `docker/bd.env.example` | `MARIADB_ROOT_PASSWORD`, `MARIADB_USER`, `MARIADB_PASSWORD` | Usuarios de la BD dentro de Docker |
| `PetConnect.Front/petconnect-app/.env.example` | `VITE_API_URL` | Dirección de la API publicada. Vacía = `/api` (desarrollo) |
| `PetConnect.Mobile/.env.example` | `EXPO_PUBLIC_API_URL`, `EXPO_PUBLIC_WEB_URL` | Direcciones de la API y de la web. Vacías = emulador o `localhost` |

> **Ojo:** todo lo que empieza por `VITE_` o `EXPO_PUBLIC_` queda **dentro de la página o de la app** y
> cualquiera puede leerlo. Ahí solo van direcciones públicas, nunca contraseñas ni claves.

> `python generate_keys.py` (desde cualquier carpeta) crea `JWT_SECRET` y `FERNET_KEY` en `petconnect.Backend/.env`
> **sin borrar nada**: si el archivo no existe, lo crea copiando `.env.example`; si existe, solo llena las claves que
> falten y deja igual todo lo demás. No muestra el valor de las claves.

## 7. Despliegue

- **API y base de datos:** en Railway, con HTTPS. La BD no tiene dirección pública: solo la API llega a ella.
- **Web:** en un *preview* protegido de Vercel, que llama directo a la API de Railway con `VITE_API_URL`.
- **Móvil:** apunta a los dos con `EXPO_PUBLIC_API_URL` y `EXPO_PUBLIC_WEB_URL`.

El paso a paso, las variables de cada servicio y los problemas encontrados están en
[`Documentacion/DESPLIEGUE-Railway-Vercel.md`](Documentacion/DESPLIEGUE-Railway-Vercel.md). Las claves del servidor
se ponen en el panel de Railway, nunca en el repositorio.

## 8. Pruebas e integración continua

Backend (no necesita base de datos). Desde `Evidecia\petconnect.Backend`:

```powershell
..\.venv\Scripts\python -m unittest discover -s tests -v
```

Las pruebas que sí necesitan MariaDB se omiten solas; para correrlas, pon `PETCONNECT_PRUEBA_BD=1` (crean y borran
bases temporales, nunca tocan `petconnect`).

Web. Desde `Evidecia\PetConnect.Front\petconnect-app`, uno por uno (si el lint falla, no sigas):

```powershell
npm run lint
```

```powershell
npm test
```

```powershell
npm run build
```

Móvil. Desde `Evidecia\PetConnect.Mobile`:

```powershell
npm test
```

**Integración continua (CI):** en cada `git push`, GitHub Actions (`.github/workflows/ci.yml`) corre tres trabajos
en un computador limpio con Linux, sin secretos:

| Trabajo | Qué revisa |
|---|---|
| Backend | `pip-audit` (dependencias con fallas conocidas) y `unittest` |
| Web | `npm audit`, lint, `npm test` y `npm run build` |
| Móvil | `npm audit`, `npm test` y `npx expo export --platform web` (que la app se arme) |

## 9. El backend por dentro

### 9.1 Arquitectura por capas

La consola y la API comparten las capas de acceso a datos. El patrón **DAO** (*Data Access Object*) separa las
consultas SQL de los menús y de los endpoints.

| Capa | Carpeta | Responsabilidad |
|---|---|---|
| Vista (consola) | `vista/` | Menús de texto (`menu_principal.py`, `menu_usuarios.py`, `menu_mascotas.py`, `menu_productos.py`, `menu_proveedores.py`) |
| API | `api.py` | Endpoints REST, validación de datos, JWT y límite de intentos |
| DAO | `dao/` | Consultas SQL parametrizadas (`usuario_dao.py`, `mascota_dao.py`, `producto_dao.py`, `proveedor_dao.py`, `solicitud_dao.py`, `otp_dao.py`) |
| Modelo | `modelo/` | Clases que representan las tablas (`usuario.py`, `mascota.py`, `producto.py`, `proveedor_servicio.py`) |
| Conexión | `conexion/` | `ConexionBD` (Singleton con pool de conexiones) |
| Configuración | `config/` | Lee las variables `DB_*` del `.env` (`db_config.py`) |
| Seguridad | `security/` | Contraseñas con bcrypt, JWT, cifrado, validación de datos y versión de la política |

### 9.2 Conexión a la base de datos

`config/db_config.py` arma la configuración con `os.getenv` (los valores salen del `.env`, nunca del código):

| Parámetro | Origen | Notas |
|---|---|---|
| host, port, database, user, password | `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` | Por defecto `localhost`, `3310`, `petconnect` |
| charset | fijo | `utf8mb4` (soporta tildes, ñ y emojis) |
| sql_mode | fijo | Modo estricto: un dato inválido da error en vez de guardarse vacío |
| autocommit | fijo, `False` | Nada queda guardado hasta llamar `commit()`; si algo falla, `rollback()` deshace la operación completa ("todo o nada") |

`ConexionBD` (`conexion/conexion_bd.py`) es un **Singleton** (un solo objeto por proceso) que administra un
**pool**: un "estante" de conexiones abiertas (10 por defecto, `DB_POOL_SIZE`) que presta una conexión distinta a
cada operación. Equivale a un `DataSource` con pool en Java.

| Método | Descripción |
|---|---|
| `obtener_conexion()` | Presta una conexión del pool. Si están todas ocupadas espera hasta 5 s; si la BD no responde devuelve `None` (la API contesta 503). |
| `cerrar_conexion()` | Cierra las conexiones libres del pool (la consola lo llama al salir). |
| `conexion_y_cursor(bd)` | Bloque `with` que presta conexión y cursor y los devuelve al terminar, aunque haya error. |
| `conexion.commit()` / `conexion.rollback()` | Confirman o deshacen los cambios de esa operación (sobre la conexión prestada). |

Al volver al pool, la conexión se limpia (`pool_reset_session=True`): lo que haya quedado sin `commit()` se
descarta y nunca le llega a otra petición.

### 9.3 Consultas parametrizadas

Todas las consultas usan marcadores `%s` en lugar de pegar los valores en el texto del SQL. Así se evita la
**inyección SQL** (que alguien meta comandos SQL dentro de un dato). Equivale a `PreparedStatement` en JDBC.

```python
_INSERTAR = """
    INSERT INTO usuarios (nombres, apellidos, correo, telefono, password_hash)
    VALUES (%s, %s, %s, %s, %s)
"""

with conexion_y_cursor(self._conexion_bd) as (conexion, cursor):
    try:
        cursor.execute(self._INSERTAR, (usuario.nombres, usuario.apellidos,
                       usuario.correo, usuario.telefono, usuario.password_hash))
        conexion.commit()    # Confirmar: sin esto el cambio se descarta
    except Error:
        conexion.rollback()  # Deshacer lo que no se confirmó
        raise
```

| Concepto | JDBC (Java) | mysql-connector (Python) |
|---|---|---|
| Conexión | `DriverManager.getConnection()` | `mysql.connector.connect()` / pool |
| Consulta preparada | `PreparedStatement` | `cursor.execute(sql, params)` |
| Resultado | `ResultSet` | `cursor.fetchall()` / `fetchone()` |
| Transacciones | `commit()` / `rollback()` | `commit()` / `rollback()` |

### 9.4 Operaciones de los DAO de la consola

| DAO | Insertar | Consultar | Buscar | Actualizar | Eliminar |
|---|---|---|---|---|---|
| UsuarioDAO | `insertar()` | `consultar_todos()`, `consultar_por_id()` | `consultar_por_correo()`, `buscar_por_nombre()` | `actualizar()` | `eliminar()` |
| MascotaDAO | `insertar()` | `consultar_todos()`, `consultar_por_id()` | `consultar_por_usuario()`, `buscar_por_nombre()` | `actualizar()` | `eliminar()` |
| ProductoDAO | `insertar()` | `consultar_todos()`, `consultar_por_id()` | `consultar_por_categoria()`, `buscar_por_nombre()` | `actualizar()` | `eliminar()` |
| ProveedorDAO | `insertar()` | `consultar_todos()`, `consultar_por_id()` | `consultar_por_ciudad()`, `buscar_por_nombre()` | `actualizar()` | `eliminar()` |

Cada submenú de la consola ofrece 7 opciones: registrar, consultar todos, buscar por ID, búsqueda específica,
buscar por nombre, actualizar y eliminar.

### 9.5 Contraseñas

Se guardan solo con **bcrypt** (sal aleatoria y factor de costo 12) en `security/passwords.py`. Las cuentas
antiguas con SHA-256 se reconocen con `hashlib` y pasan a bcrypt en su siguiente inicio de sesión.

### 9.6 Convenciones de código (PEP 8)

| Elemento | Convención | Ejemplos |
|---|---|---|
| Variables y métodos | snake_case (métodos con verbo) | `id_usuario`, `consultar_por_id()` |
| Clases | PascalCase | `Usuario`, `MascotaDAO`, `ConexionBD` |
| Paquetes | minúsculas | `config`, `conexion`, `modelo`, `dao`, `vista` |
| Constantes | UPPER_SNAKE_CASE | `DB_CONFIG`, `_INSERTAR` |
| Métodos privados | prefijo `_` | `_mapear_usuario()` |

## 10. Base de datos

| Propiedad | Valor |
|---|---|
| Nombre | `petconnect` |
| Motor | MariaDB (InnoDB), compatible con MySQL |
| Charset / collation de las tablas | `utf8mb4` / `utf8mb4_spanish_ci` |
| Tablas | 34 (`petconnect.Backend/sql/schema.sql`) |

| Módulo | Tablas |
|---|---|
| Seguridad | usuarios, roles, usuarios_roles, direcciones, metodos_pago, planes, suscripciones, otp_pendientes (códigos de verificación) |
| Mascotas | mascotas, carnets_vacunacion, vacunas, aplicaciones_vacuna, historial_salud, citas, recordatorios |
| Servicios | categorias_servicio, proveedores_servicio, servicios, resenas_servicio |
| Comunidad | publicaciones_comunidad, comentarios_publicacion, reportes_publicacion |
| Adopciones | adopciones, solicitudes |
| Tienda | categorias_producto, productos, carritos, carrito_detalle, pedidos, pedido_detalle, pagos |
| GPS | gps_dispositivos, gps_ubicaciones |
| Notificaciones | notificaciones |

## 11. Más documentación

| Documento | Qué tiene |
|---|---|
| [`PetConnect.Mobile/EJECUCION.md`](PetConnect.Mobile/EJECUCION.md) | Emulador, APK y problemas comunes del móvil |
| [`VERIFICACION.md`](VERIFICACION.md) | Guía para verificar el sistema completo, endpoints y Postman |
| [`petconnect.Backend/sql/README.md`](petconnect.Backend/sql/README.md) | Crear la base, migraciones y reglas de la BD |
| [`Documentacion/DESPLIEGUE-Railway-Vercel.md`](Documentacion/DESPLIEGUE-Railway-Vercel.md) | Publicar la API en Railway y la web en Vercel |
| [`Documentacion/Auditoria/`](Documentacion/Auditoria/) | Auditoría del 03/11/2026 y lista de prioridades |
| `Documentacion/` | Evidencias de las guías GA7, GA8 y GA9 |
| [`CLAUDE.md`](CLAUDE.md) | Reglas del proyecto para trabajar con Claude Code |

## 12. Licencia

**Todos los derechos reservados.** PetConnect es un proyecto formativo del SENA (ficha 3235905) y su código no
tiene una licencia abierta. Que se pueda ver (por ejemplo, en GitHub) no da permiso de copiarlo, modificarlo ni
redistribuirlo sin autorización de sus autores.

- Hasta el 12/11/2026, `PetConnect.Mobile/` traía el archivo `LICENSE` de la plantilla de Expo (una licencia MIT a
  nombre de Expo), que no correspondía a este código. Se quitó (hallazgo A-34 de la auditoría).
- Las librerías de terceros (React, Expo, Flask y las demás dependencias) conservan cada una su propia licencia, que
  viene dentro del paquete (`node_modules/` o el entorno de Python).
- Si más adelante se elige una licencia abierta (por ejemplo, MIT), se agrega un archivo `LICENSE` en la raíz y se
  actualiza esta sección. Antes conviene consultarlo con el instructor.
