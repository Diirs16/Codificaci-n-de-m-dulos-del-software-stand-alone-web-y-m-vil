# PetConnect

Plataforma para mascotas: **adopción**, **tienda de productos** y **directorio de proveedores de servicios**. Es
un proyecto formativo del SENA (ficha 3235905) con **cuatro formas de usarse**, que comparten la misma base de
datos y la misma API REST:

| Módulo | Carpeta | Tecnología | Para qué |
|---|---|---|---|
| API (backend) | `petconnect.Backend/` | Python + Flask | Servicio REST que usan la web y el móvil |
| Consola (stand-alone) | `petconnect.Backend/` (`main.py`) | Python | Menús de texto para administrar usuarios, mascotas, productos y proveedores |
| Web | `PetConnect.Front/petconnect-app/` | React + Vite + Tailwind | Página para el navegador |
| Móvil | `PetConnect.Mobile/` | React Native + Expo | App para Android |

Este README es la **puerta de entrada**: qué hace el proyecto, qué necesita, cómo instalarlo y dónde están las
guías largas.

## Contenido

1. [Qué se puede hacer](#1-qué-se-puede-hacer)
2. [Cómo se conecta todo](#2-cómo-se-conecta-todo)
3. [Tecnologías y dependencias](#3-tecnologías-y-dependencias)
4. [Estructura del repositorio](#4-estructura-del-repositorio)
5. [Instalación paso a paso](#5-instalación-paso-a-paso)
6. [Variables de entorno](#6-variables-de-entorno)
7. [Endpoints de la API](#7-endpoints-de-la-api)
8. [Pruebas e integración continua](#8-pruebas-e-integración-continua)
9. [Despliegue](#9-despliegue)
10. [Base de datos](#10-base-de-datos)
11. [El backend por dentro](#11-el-backend-por-dentro)
12. [Más documentación](#12-más-documentación)
13. [Licencia](#13-licencia)

## 1. Qué se puede hacer

| Funcionalidad | Web | Móvil | Consola |
|---|---|---|---|
| Ver el catálogo de productos y el detalle de cada uno | Inicio, `/catalogo`, `/producto/:id` | Pestaña **Tienda** | Menú de productos |
| Agregar productos al carrito y ver el resumen de compra | Carrito y `/checkout` (*demo*: no cobra ni guarda pedidos) | — | — |
| Ver mascotas en adopción y su ficha | `/adopcion`, `/adopcion/:id` | Pestaña **Adopción** | Menú de mascotas |
| Pedir la adopción de una mascota (con sesión iniciada) | Formulario en la ficha | Formulario en la ficha | — |
| Escribir a PetConnect (con sesión iniciada) | `/contacto` | Pestaña **Contacto** | — |
| Crear cuenta con código de verificación por correo | Ventana **Registrarse** | Pestaña **Perfil** | — |
| Iniciar sesión en dos pasos (contraseña + código por correo) | Ventana **Iniciar sesión** | Pestaña **Perfil** | — |
| Cerrar sesión en todos los dispositivos (y ver el perfil en el móvil) | Botón **Cerrar sesión** del encabezado | Pestaña **Perfil** | — |
| Leer la política de tratamiento de datos (Ley 1581 de 2012) | `/politica-de-datos` | Enlace a la web | — |
| Registrar, consultar, buscar, actualizar y eliminar usuarios, mascotas, productos y proveedores | — | — | Menú principal |

Para crear cuenta o iniciar sesión, la persona debe marcar la casilla de **autorización de datos personales**: sin
ella no se manda el código.

## 2. Cómo se conecta todo

```
   Navegador                   Celular Android
 ┌────────────────┐          ┌──────────────────┐
 │  Web (React)   │          │  Móvil (Expo)    │
 │  :5173         │          │  emulador        │
 └───────┬────────┘          └────────┬─────────┘
         │  /api (proxy de Vite)      │  10.0.2.2:5000 (emulador)
         └──────────────┬─────────────┘
                        ▼
              ┌───────────────────┐        ┌──────────────────────┐
              │  API Flask :5000  │ ─────▶ │  Correo (Gmail,      │
              │  JWT · bcrypt     │        │  Mailtrap o Brevo)   │
              └─────────┬─────────┘        └──────────────────────┘
                        │  SQL parametrizado
                        ▼
              ┌───────────────────┐        ┌──────────────────────┐
              │  MariaDB :3310    │ ◀───── │  Consola (main.py)   │
              │  base petconnect  │        │  usa los mismos DAO  │
              └───────────────────┘        └──────────────────────┘
```

| Qué | Dirección en el PC |
|---|---|
| Web | <http://localhost:5173> |
| API | <http://localhost:5000> (prueba: <http://localhost:5000/api/productos>) |
| Base de datos | `localhost`, puerto `3310`, base `petconnect` |
| Móvil (emulador de Android) | llega a la API por `10.0.2.2:5000` |
| Todo con Docker | <http://localhost:8080> |

## 3. Tecnologías y dependencias

### 3.1 Herramientas base

| Tecnología | Versión | Dónde se fija |
|---|---|---|
| Python | 3.14 | `.venv` de la raíz, la CI y el `Dockerfile` de la API |
| MariaDB (base de datos) | 10.4.32 en el PC (XAMPP, puerto 3310); 10.11 en Docker y Railway | `docker-compose.yml`, `petconnect.Backend/Dockerfile.bd` |
| Node.js (con `npm`) | 24 | la CI y el `Dockerfile` de la web |
| Android Studio | con emulador (Pixel 7) y su JDK (`jbr`) | solo para el móvil, ver `PetConnect.Mobile/EJECUCION.md` |
| Docker Desktop | opcional | solo para la sección 5.7 |

**MariaDB** es una base de datos "prima" de MySQL: usa el mismo lenguaje SQL y el mismo conector
(`mysql-connector-python`). Por eso en el código y en algunos comandos se lee "MySQL", pero el motor real es
MariaDB. El esquema **no** se ha probado en MySQL 8 (ver `petconnect.Backend/sql/README.md`).

### 3.2 Backend (API y consola)

Fijadas con versión exacta en `petconnect.Backend/requirements.txt` (se instalan con `pip`, sección 5.3).

| Paquete | Versión | Para qué sirve |
|---|---|---|
| flask | 3.1.3 | El servidor web de la API (rutas, peticiones y respuestas JSON) |
| flask-cors | 6.0.5 | Decide qué páginas pueden llamar a la API desde el navegador (CORS) |
| Flask-Limiter / limits | 4.1.1 / 5.8.0 | Límite de intentos por IP (frena a quien prueba contraseñas sin parar) |
| mysql-connector-python | 9.1.0 | Conector con MariaDB, con pool de conexiones |
| bcrypt | 5.0.0 | Guarda las contraseñas de forma segura (nunca en texto plano) |
| PyJWT | 2.15.1 | Crea y revisa el token de sesión (JWT) |
| cryptography | 50.0.2 | Cifra datos sensibles con `FERNET_KEY` |
| python-dotenv | 1.2.2 | Lee las variables del archivo `.env` |
| dnspython | 2.9.2 | Revisa que el dominio de un correo exista (registros MX) |
| mailtrap | 2.6.0 | Envío del código por la API de Mailtrap |
| gunicorn | 26.2.0 | Servidor de producción de la API (en Docker y Railway) |

### 3.3 Web

Declaradas en `PetConnect.Front/petconnect-app/package.json` (se instalan con `npm ci`, sección 5.5).

| Paquete | Versión | Para qué sirve |
|---|---|---|
| react / react-dom | ^19.2.7 / ^19.2.7 | La librería con la que se arma la interfaz |
| react-router-dom | ^7.18.1 | Las páginas y sus direcciones (`/catalogo`, `/adopcion`…) |
| lucide-react | ^1.22.0 | Íconos |
| vite / @vitejs/plugin-react | ^8.1.0 / ^6.0.2 | Servidor de desarrollo y armado (*build*) de la página |
| tailwindcss / @tailwindcss/vite | ^4.3.2 / ^4.3.2 | Estilos con clases utilitarias |
| oxlint | ^1.69.0 | Linter: revisa el código en busca de errores comunes |
| @types/react / @types/react-dom | ^19.2.17 / ^19.2.3 | Ayudas de autocompletado para el editor |

### 3.4 Móvil

Declaradas en `PetConnect.Mobile/package.json` (se instalan con `npm ci`, sección 5.6).

| Paquete | Versión | Para qué sirve |
|---|---|---|
| expo | ~57.0.32 | La plataforma que compila y ejecuta la app |
| react-native / react | 0.86.3 / 19.2.3 | La librería con la que se arma la interfaz móvil |
| @react-navigation/native, native-stack, bottom-tabs | ^7.3.10, ^7.18.2, ^7.18.10 | Navegación entre pantallas y pestañas de abajo |
| react-native-screens / react-native-safe-area-context | ~4.26.0 / ~5.7.0 | Pantallas nativas y respeto del borde del celular (*notch*) |
| expo-secure-store | ~57.0.4 | Guarda el token de sesión cifrado en el celular |
| @react-native-async-storage/async-storage | 2.2.0 | Guarda datos simples en el celular |
| expo-status-bar | ~57.0.1 | Barra de estado del celular |
| react-native-web / react-dom / @expo/metro-runtime | ^0.21.2 / 19.2.3 / ~57.0.18 | Permiten armar la app también para web (lo usa la CI) |

## 4. Estructura del repositorio

```
Evidecia/
├── petconnect.Backend/        # API Flask + consola (Python)
│   ├── api.py                 # API REST (puerto 5000)
│   ├── main.py                # Consola stand-alone
│   ├── seed.py                # Datos de ejemplo (inventados)
│   ├── generate_keys.py       # Crea JWT_SECRET y FERNET_KEY en el .env
│   ├── config/  conexion/  modelo/  dao/  vista/   # Capas (ver sección 11)
│   ├── security/  otp/  correo/                    # Contraseñas, JWT, cifrado, códigos y correo
│   ├── sql/                   # schema.sql, migraciones y su README
│   ├── tests/                 # Pruebas (unittest)
│   ├── requirements.txt       # Dependencias de Python
│   ├── Dockerfile  Dockerfile.bd  gunicorn.conf.py
│   └── .env.example           # Plantilla de variables (sin valores reales)
├── PetConnect.Front/petconnect-app/   # Web React + Vite
│   ├── src/pages/             # Páginas (Home, Catalog, Adoption, Checkout, Contact…)
│   ├── src/components/        # Header, Footer, carrito, ventanas de login y registro…
│   ├── src/context/           # Sesión (AuthContext) y carrito (CartContext)
│   ├── src/services/api.js    # Llamadas a la API
│   ├── src/hooks/  src/utils/ # Paginación, validaciones y ayudas
│   ├── tests/                 # Pruebas (node --test)
│   └── package.json  vite.config.js  Dockerfile
├── PetConnect.Mobile/                 # App Expo
│   ├── App.js                 # Punto de entrada
│   ├── src/screens/           # Pantallas (Home, Adoption, Login, Register, Profile…)
│   ├── src/navigation/        # Pestañas y pilas de pantallas
│   ├── src/context/  src/services/  src/components/  src/hooks/  src/utils/
│   ├── tests/                 # Pruebas (node --test)
│   └── EJECUCION.md           # Emulador, APK y problemas comunes
├── docker/                    # Plantillas de variables para docker compose
├── docker-compose.yml         # BD + API + web en contenedores
├── .github/workflows/ci.yml   # Integración continua (GitHub Actions)
├── Documentacion/             # Evidencias GA7/GA8/GA9, auditoría y guía de despliegue
├── VERIFICACION.md            # Guía de verificación del sistema
└── CLAUDE.md                  # Reglas para trabajar con Claude Code
```

## 5. Instalación paso a paso

Los comandos son para **Windows PowerShell 5.1**: van uno por bloque (ahí `&&` no existe) y cada bloque dice desde
qué carpeta se corre. El orden recomendado es: base de datos → API → web y/o móvil.

### 5.1 Clonar el proyecto

```powershell
git clone https://github.com/Diirs16/PETCONNECT-PROYECTO.git Evidecia
```

```powershell
cd Evidecia
```

Revisa que tengas las herramientas de la sección 3.1 (`python --version`, `node --version`).

### 5.2 Base de datos

1. Enciende MariaDB en XAMPP (puerto **3310**).
2. Crea la base `petconnect` y carga `petconnect.Backend/sql/schema.sql` (34 tablas, sin datos personales).
3. Después de instalar la API (5.3), carga los datos de ejemplo con `seed.py`.

Los comandos exactos, las migraciones para quien ya tenía la base y cómo comprobar que quedó bien están en
[`petconnect.Backend/sql/README.md`](petconnect.Backend/sql/README.md).

### 5.3 API (backend)

La primera vez, crea el entorno virtual. Desde la raíz `Evidecia`:

```powershell
python -m venv .venv
```

Instala las dependencias de la sección 3.2. Desde `Evidecia\petconnect.Backend`:

```powershell
..\.venv\Scripts\python -m pip install -r requirements.txt
```

Crea el `.env` con las claves `JWT_SECRET` y `FERNET_KEY` ya generadas (copia `.env.example` y no muestra los
valores). Desde `Evidecia\petconnect.Backend`:

```powershell
..\.venv\Scripts\python generate_keys.py
```

Abre `petconnect.Backend/.env` y llena lo que falte (base de datos y correo, sección 6). Nunca subas el `.env` a Git.

Carga los datos de ejemplo (inventados). Desde `Evidecia\petconnect.Backend`:

```powershell
..\.venv\Scripts\python seed.py
```

Arranca la API. Desde `Evidecia\petconnect.Backend`:

```powershell
..\.venv\Scripts\python api.py
```

Debe mostrar `[OK] Conexion a la base de datos establecida.` y `[OK] API PetConnect corriendo en
http://127.0.0.1:5000`. Prueba en el navegador: <http://localhost:5000/api/productos>.

> La API no se recarga sola: si cambias código del backend, deténla con `Ctrl + C` y vuelve a arrancarla.

### 5.4 Consola (stand-alone)

Usa la misma base de datos y el mismo `.env` que la API. Desde `Evidecia\petconnect.Backend`:

```powershell
..\.venv\Scripts\python main.py
```

Abre el menú principal (usuarios, mascotas, productos y proveedores) con las opciones de registrar, consultar,
buscar, actualizar y eliminar.

### 5.5 Web

La primera vez, instala las dependencias de la sección 3.3. Desde `Evidecia\PetConnect.Front\petconnect-app`:

```powershell
npm ci
```

Arranca el servidor de desarrollo (con la API de la sección 5.3 encendida). Desde la misma carpeta:

```powershell
npm run dev
```

Abre <http://localhost:5173>. En desarrollo, Vite manda las llamadas a `/api` hacia `http://localhost:5000`
(ver `vite.config.js`), así que no hace falta configurar nada más.

### 5.6 Móvil

La primera vez, instala las dependencias de la sección 3.4. Desde `Evidecia\PetConnect.Mobile`:

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

### 5.7 Todo con Docker (opcional)

Levanta la base de datos (MariaDB 10.11), la API (con Gunicorn) y la web (con nginx) en contenedores, sin instalar
Python ni MariaDB en el PC.

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
| | `EMAIL_MODE` | Por dónde sale el código de verificación: `gmail`, `smtp` (sandbox de Mailtrap), `sdk` (API de Mailtrap) o `brevo` |
| | `GMAIL_USER`, `GMAIL_APP_PASSWORD` | Correo por Gmail |
| | `MAILTRAP_API_TOKEN`, `MAILTRAP_SENDER` | Correo por Mailtrap |
| | `BREVO_API_KEY`, `BREVO_SENDER` | Correo por la API HTTPS de Brevo (el que se usa en Railway) |
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

## 7. Endpoints de la API

Todas las rutas empiezan por `/api` y responden JSON. Las marcadas con 🔒 piden el token de sesión
(`Authorization: Bearer <token>`). Las de inicio de sesión, registro y solicitudes tienen límite de intentos por IP.

| Método | Ruta | Qué hace |
|---|---|---|
| GET | `/api/productos` | Lista el catálogo (paginado) |
| GET | `/api/productos/<id>` | Detalle de un producto |
| GET | `/api/mascotas/adopcion` | Lista las mascotas en adopción (paginado) |
| GET | `/api/mascotas/<id>` | Ficha de una mascota en adopción |
| GET 🔒 | `/api/usuarios/me/mascotas/<id>` | Ficha de una mascota propia |
| POST | `/api/utils/validar-correo` | Revisa el formato y el dominio de un correo, sin crear nada |
| POST | `/api/auth/register` | Registro: guarda la solicitud y manda un código al correo |
| POST | `/api/auth/register/resend` | Reenvía el código de un registro pendiente |
| POST | `/api/auth/verify` | Confirma el código del registro y crea la cuenta |
| POST | `/api/auth/login` | Paso 1 del inicio de sesión: revisa la contraseña y manda un código al correo |
| POST | `/api/auth/login/verify` | Paso 2: confirma el código y entrega el token |
| GET 🔒 | `/api/auth/me` | Datos de la cuenta con sesión iniciada |
| POST 🔒 | `/api/auth/logout` | Cierra la sesión en todos los dispositivos |
| POST 🔒 | `/api/solicitudes/adopcion` | Envía una solicitud para adoptar una mascota |
| POST 🔒 | `/api/solicitudes/contacto` | Envía un mensaje de contacto |

Ejemplos de cada petición (con Postman) en [`VERIFICACION.md`](VERIFICACION.md).

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

## 9. Despliegue

- **API y base de datos:** en Railway, con HTTPS. La BD no tiene dirección pública: solo la API llega a ella.
- **Web:** en un *preview* protegido de Vercel, que llama directo a la API de Railway con `VITE_API_URL`.
- **Móvil:** apunta a los dos con `EXPO_PUBLIC_API_URL` y `EXPO_PUBLIC_WEB_URL`.
- **Correo:** en Railway sale por la API de Brevo, porque su plan Hobby bloquea SMTP.

El paso a paso, las variables de cada servicio y los problemas encontrados están en
[`Documentacion/DESPLIEGUE-Railway-Vercel.md`](Documentacion/DESPLIEGUE-Railway-Vercel.md). Las claves del servidor
se ponen en el panel de Railway, nunca en el repositorio.

## 10. Base de datos

| Propiedad | Valor |
|---|---|
| Nombre | `petconnect` |
| Motor | MariaDB (InnoDB), compatible con MySQL |
| Charset / collation de las tablas | `utf8mb4` / `utf8mb4_spanish_ci` |
| Tablas | 34 (`petconnect.Backend/sql/schema.sql`) |
| Transacciones | autocommit `False`: nada queda guardado hasta `commit()` |

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

El esquema trae tablas para funciones que todavía no tienen pantalla (citas, comunidad, GPS, pagos…): quedan
listas para crecer.

## 11. El backend por dentro

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

Las contraseñas se guardan solo con **bcrypt** y todas las consultas SQL van **parametrizadas** (con marcadores
`%s`, nunca pegando el dato en el texto), lo que evita la inyección SQL.

<details>
<summary><strong>Ver el detalle técnico: conexión, pool, consultas, DAO y convenciones</strong></summary>

### 11.1 Conexión a la base de datos

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

### 11.2 Consultas parametrizadas

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

### 11.3 Operaciones de los DAO de la consola

| DAO | Insertar | Consultar | Buscar | Actualizar | Eliminar |
|---|---|---|---|---|---|
| UsuarioDAO | `insertar()` | `consultar_todos()`, `consultar_por_id()` | `consultar_por_correo()`, `buscar_por_nombre()` | `actualizar()` | `eliminar()` |
| MascotaDAO | `insertar()` | `consultar_todos()`, `consultar_por_id()` | `consultar_por_usuario()`, `buscar_por_nombre()` | `actualizar()` | `eliminar()` |
| ProductoDAO | `insertar()` | `consultar_todos()`, `consultar_por_id()` | `consultar_por_categoria()`, `buscar_por_nombre()` | `actualizar()` | `eliminar()` |
| ProveedorDAO | `insertar()` | `consultar_todos()`, `consultar_por_id()` | `consultar_por_ciudad()`, `buscar_por_nombre()` | `actualizar()` | `eliminar()` |

Cada submenú de la consola ofrece 7 opciones: registrar, consultar todos, buscar por ID, búsqueda específica,
buscar por nombre, actualizar y eliminar.

### 11.4 Contraseñas

Se guardan solo con **bcrypt** (sal aleatoria y factor de costo 12) en `security/passwords.py`. Las cuentas
antiguas con SHA-256 se reconocen con `hashlib` y pasan a bcrypt en su siguiente inicio de sesión.

### 11.5 Convenciones de código (PEP 8)

| Elemento | Convención | Ejemplos |
|---|---|---|
| Variables y métodos | snake_case (métodos con verbo) | `id_usuario`, `consultar_por_id()` |
| Clases | PascalCase | `Usuario`, `MascotaDAO`, `ConexionBD` |
| Paquetes | minúsculas | `config`, `conexion`, `modelo`, `dao`, `vista` |
| Constantes | UPPER_SNAKE_CASE | `DB_CONFIG`, `_INSERTAR` |
| Métodos privados | prefijo `_` | `_mapear_usuario()` |

</details>

## 12. Más documentación

| Documento | Qué tiene |
|---|---|
| [`PetConnect.Mobile/EJECUCION.md`](PetConnect.Mobile/EJECUCION.md) | Emulador, APK y problemas comunes del móvil |
| [`VERIFICACION.md`](VERIFICACION.md) | Guía para verificar el sistema completo, endpoints y Postman |
| [`petconnect.Backend/sql/README.md`](petconnect.Backend/sql/README.md) | Crear la base, migraciones y reglas de la BD |
| [`Documentacion/DESPLIEGUE-Railway-Vercel.md`](Documentacion/DESPLIEGUE-Railway-Vercel.md) | Publicar la API en Railway y la web en Vercel |
| [`Documentacion/Auditoria/`](Documentacion/Auditoria/) | Auditoría del 03/11/2026 y lista de prioridades |
| `Documentacion/` | Evidencias de las guías GA7, GA8 y GA9 |
| [`CLAUDE.md`](CLAUDE.md) | Reglas del proyecto para trabajar con Claude Code |

## 13. Licencia

**Todos los derechos reservados.** PetConnect es un proyecto formativo del SENA (ficha 3235905) y su código no
tiene una licencia abierta. Que se pueda ver (por ejemplo, en GitHub) no da permiso de copiarlo, modificarlo ni
redistribuirlo sin autorización de sus autores.

- Hasta el 12/11/2026, `PetConnect.Mobile/` traía el archivo `LICENSE` de la plantilla de Expo (una licencia MIT a
  nombre de Expo), que no correspondía a este código. Se quitó (hallazgo A-34 de la auditoría).
- Las librerías de terceros (React, Expo, Flask y las demás dependencias) conservan cada una su propia licencia, que
  viene dentro del paquete (`node_modules/` o el entorno de Python).
- Si más adelante se elige una licencia abierta (por ejemplo, MIT), se agrega un archivo `LICENSE` en la raíz y se
  actualiza esta sección. Antes conviene consultarlo con el instructor.
