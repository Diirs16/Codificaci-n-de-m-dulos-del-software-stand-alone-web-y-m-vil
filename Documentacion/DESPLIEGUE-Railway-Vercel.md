# Publicar PetConnect: API en Railway y web en Vercel (ítem 5.5)

Guía paso a paso para el dueño del proyecto. Crear cuentas, poner tarjetas y escribir contraseñas o claves en un
servicio lo hace **el dueño**; Claude prepara los archivos y los comandos. Precios y planes consultados el
11/11/2026: pueden cambiar.

```
Navegador ──HTTPS──> Vercel (web, preview)
    │
    └──HTTPS──> Railway "api" (Gunicorn, puerto 5000) ──red privada──> Railway "db" (MariaDB 10.11 + volumen)
Celular ──HTTPS──┘
```

- La web la sirve Vercel, pero los datos los pide **directo** a la API de Railway (`VITE_API_URL`).
- La BD **no** tiene dirección pública: solo la API llega a ella, por la red privada de Railway.
- Ningún secreto va en el repositorio, en `VITE_*` ni en `EXPO_PUBLIC_*`: todo va en el panel de Railway.

---

## Parte 2 — Publicar la API en Railway

### 0. Antes de empezar

- [ ] **El código debe estar en GitHub.** Railway construye desde el repositorio de GitHub, no desde tu PC. Los
  cambios de la parte 1 (`017d14c`: `Dockerfile.bd`, `CORS_ORIGENES`, `x-real-ip`) solo existen en tu
  computador hasta que hagas `git push`.
- [ ] Python a mano para generar claves (el `.venv` de la raíz sirve).

### 1. Crear la cuenta y el proyecto

1. Entra a <https://railway.com> → **Login** con tu cuenta de GitHub. Elige la **prueba** (US$5 por 30 días,
   sin tarjeta). Al autorizar a GitHub, da acceso **solo** al repositorio de PetConnect.
2. **New Project** → **Empty Project**. Ponle de nombre `petconnect`.

### 2. Servicio de la base de datos (`db`)

1. En el proyecto: **Create** → **GitHub Repo** → elige el repositorio de PetConnect.
2. Antes de que termine el primer despliegue (si falla, no importa), abre el servicio → **Settings**:
   - **Service Name**: `db` (la API lo busca con ese nombre).
   - **Root Directory**: `/petconnect.Backend`
   - **Region**: **US East (Virginia)**.
   - En **Networking** **no** generes dominio ni TCP Proxy: la BD no se ve desde internet.
3. Pestaña **Variables** → agrega estas (los valores los generas tú, ver abajo):

   | Variable | Valor |
   |---|---|
   | `RAILWAY_DOCKERFILE_PATH` | `Dockerfile.bd` |
   | `MARIADB_ROOT_PASSWORD` | una clave nueva |
   | `MARIADB_USER` | `petconnect_app` |
   | `MARIADB_PASSWORD` | otra clave nueva, distinta |

   Para generar cada clave, en PowerShell desde la carpeta raíz `Evidecia` (una vez por clave):

   ```powershell
   .\.venv\Scripts\python -c "import secrets; print(secrets.token_urlsafe(24))"
   ```

   Cópiala directo al panel. **No la pegues en el chat** ni en ningún archivo. En Railway puedes marcar
   cada clave como *sealed* (sellada): ya no se puede volver a ver, solo reemplazar.
4. Clic derecho en el lienzo del proyecto → **Volume** → conéctalo al servicio `db` con *mount path*
   `/var/lib/mysql` (ahí guarda MariaDB los datos; sin volumen se borrarían en cada despliegue).
5. **Deploy** (o **Redeploy**). En **Deployments → View logs** debe salir algo como
   `ready for connections` y, la primera vez, que corrió `01-schema.sql`.
   - Si el registro dice que no encuentra `Dockerfile.bd`, cambia `RAILWAY_DOCKERFILE_PATH` a
     `/petconnect.Backend/Dockerfile.bd` y vuelve a desplegar.
   - Si construyó la imagen de la **API** en lugar de la BD, faltaba `RAILWAY_DOCKERFILE_PATH`: agrégala y
     vuelve a desplegar.

> El esquema solo se carga cuando el volumen está vacío (la primera vez), igual que en `docker-compose`.

### 3. Servicio de la API (`api`)

1. **Create** → **GitHub Repo** → el mismo repositorio.
2. **Settings**:
   - **Service Name**: `api`
   - **Root Directory**: `/petconnect.Backend` (usa el `Dockerfile` de la API, el del ítem 5.2).
   - **Region**: **US East (Virginia)** (la misma de la BD).
3. **Variables**:

   | Variable | Valor | Por qué |
   |---|---|---|
   | `DB_HOST` | `${{db.RAILWAY_PRIVATE_DOMAIN}}` | Dirección privada de la BD (referencia, no se copia a mano) |
   | `DB_PORT` | `3306` | Puerto de MariaDB dentro de Railway |
   | `DB_NAME` | `petconnect` | |
   | `DB_USER` | `${{db.MARIADB_USER}}` | Referencia: la toma del servicio `db` |
   | `DB_PASSWORD` | `${{db.MARIADB_PASSWORD}}` | Referencia: nunca escribes la clave dos veces |
   | `JWT_SECRET` | clave **nueva** (sellada) | `.\.venv\Scripts\python -c "import secrets; print(secrets.token_hex(32))"` |
   | `FERNET_KEY` | clave **nueva** (sellada) | `.\.venv\Scripts\python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
   | `PROXY_CONFIABLE` | `x-real-ip` | El límite de 5 intentos cuenta por la IP real de cada persona |
   | `APP_ENV` | `desarrollo` | Railway bloquea el correo SMTP: el código de verificación sale en los registros de Railway (solo el código, nunca el correo). **Solo para el preview** |
   | `EMAIL_MODE` | `gmail` | Sin `GMAIL_USER` ni `GMAIL_APP_PASSWORD`: falla al instante, sin intentar conectarse |
   | `PORT` | `5000` | Gunicorn escucha en el 5000 (`gunicorn.conf.py`) |
   | `CORS_ORIGENES` | *(vacía por ahora)* | Se llena en la parte 3 con la dirección de Vercel |

   **No** pongas `FLASK_DEBUG`, `API_HOST`, `GMAIL_*` ni `MAILTRAP_*`. No copies las claves de tu `.env`
   local: claves nuevas para un servidor nuevo.
4. **Settings → Networking → Generate Domain** → puerto **5000**. Te da algo como
   `https://api-production-xxxx.up.railway.app` (con HTTPS automático).
5. **Deploy**. En los registros debe salir que Gunicorn arrancó. Si la API arrancó antes que la BD y se
   cayó, Railway la reinicia sola; si no, **Redeploy**.

### 4. Probar (mándale a Claude las capturas)

En PowerShell, desde cualquier carpeta (cambia la dirección por la tuya):

```powershell
Invoke-RestMethod -Uri "https://TU-DOMINIO.up.railway.app/api/productos"
```

Esperado: una respuesta JSON (la lista vacía si no hay productos). **No** debe salir un error 502/503.

Límite de intentos (debe responder 400 cinco veces y 429 la sexta):

```powershell
1..6 | ForEach-Object { try { Invoke-WebRequest -Method Post -Uri "https://TU-DOMINIO.up.railway.app/api/auth/login" -ContentType "application/json" -Body "{}" -UseBasicParsing | Out-Null } catch { $_.Exception.Response.StatusCode.value__ } }
```

Captura también la pestaña **Deployments → View logs** del servicio `api` (que no aparezca ningún correo,
clave ni valor de configuración).

### Si algo falla

- **La API no llega a la BD**: revisa que el servicio se llame exactamente `db` y que las dos estén en la
  misma región y el mismo entorno (*production*).
- **`JWT_SECRET` obligatorio**: falta la variable o tiene menos de 32 bytes.
- **La prueba de 30 días se acaba**: la API se apaga hasta pasar a Hobby (US$5/mes, con tarjeta, lo hace el
  dueño). Tenlo en cuenta con la fecha de la evaluación.
