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
   | `EMAIL_MODE` | `brevo` | Railway Hobby bloquea SMTP; Brevo envía por HTTPS (ver [Correo con Brevo](#correo-con-brevo-ítem-612)) |
   | `BREVO_API_KEY` | clave **nueva** (sellada) | Se genera en Brevo y la pone el dueño (nunca en el chat ni con `Read-Host`; ver [Correo con Brevo](#correo-con-brevo-ítem-612)) |
   | `BREVO_SENDER` | remitente validado en Brevo | El Gmail del proyecto, el mismo que aparece como verificado en Brevo → *Remitentes* |
   | `PORT` | `5000` | Gunicorn escucha en el 5000 (`gunicorn.conf.py`) |
   | `CORS_ORIGENES` | *(vacía por ahora)* | Se llena en la parte 3 con la dirección de Vercel |

   **No** pongas `FLASK_DEBUG`, `API_HOST`, `GMAIL_*` ni `MAILTRAP_*`. No copies las claves de tu `.env`
   local: claves nuevas para un servidor nuevo. Tampoco `APP_ENV`: se usó con `desarrollo` mientras el
   correo no llegaba (el código salía en los registros) y se quitó el 13/11/2026 al cerrar el ítem 6.12.
   Sin ella, si el correo falla la API responde 503 y el código no queda en ningún registro.
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
- **"Invalid service name"** al elegir el repositorio: el nombre del repositorio era demasiado largo. Se
  renombró a `PETCONNECT-PROYECTO` (o crea un *Empty Service* y conecta el repositorio después).
- **El despliegue falla sin construir nada** y en sus datos dice *"Your plan can only deploy to a single
  region"*: el servicio quedó con dos regiones. Deja una sola (US East).
- **No le des "Deploy" a cambios viejos** de la barra "Apply N changes" si no sabes qué traen: ábrelos con
  **Details** y, si sobran, descártalos (⋮ → *Discard*).

### Cómo se hizo de verdad (11/11/2026): con el CLI de Railway

Los clics del panel resultaron confusos, así que se usó el CLI oficial (`npm install -g @railway/cli@5.71.0`).
El dueño hizo `railway login` y generó las claves con comandos que las guardan **sin mostrarlas**. Desde
la carpeta raíz del proyecto (`Evidecia`, la que tiene la carpeta `.venv`), uno por línea:

```powershell
$p = .\.venv\Scripts\python -c "import secrets; print(secrets.token_urlsafe(24))"; railway variable set "MARIADB_PASSWORD=$p" --service db --skip-deploys | Out-Null; $p = $null
```

(Igual para `MARIADB_ROOT_PASSWORD`; `JWT_SECRET` con `secrets.token_hex(32)` y `FERNET_KEY` con
`Fernet.generate_key().decode()`, los dos con `--service api`.) Lo demás (nombres, carpeta, variables que no
son secretas, volumen, región, dominio y despliegues) lo configuró Claude por CLI, revisando las variables
solo por nombre.

- Dirección de la API: `https://api-production-d8fdc68b.up.railway.app`
- Ver los registros: `railway logs --service api` (o `--service db`)
- Ver los despliegues: `railway deployment list --service api`

### Correo con Brevo (ítem 6.12)

**Por qué:** el plan Hobby de Railway bloquea el correo SMTP (Gmail, Mailtrap), pero no HTTPS. Brevo tiene
una API por HTTPS (puerto 443), así que la API manda el código de verificación por ahí
(`EMAIL_MODE=brevo`, función `_enviar_brevo` de `correo/servicio.py`). No usa dependencias nuevas.

1. **Cuenta**: crear una cuenta gratuita en Brevo con el Gmail del proyecto.
2. **Remitente**: en Brevo → *Remitentes*, agregar el Gmail del proyecto con el nombre `PetConnect` y
   validarlo con el enlace que llega a esa bandeja. Ese mismo correo va en `BREVO_SENDER`.
3. **Clave de API restringida**: Brevo → *SMTP y API* → *Claves de API* → *Generar una nueva clave*, con
   permisos **restringidos** y solo *Emails transaccionales → Todos*. Si alguien la roba, solo puede enviar
   correos, no leer contactos ni cambiar la cuenta. Brevo la muestra **una sola vez**.
4. **Ponerla en Railway** (la pone el dueño, nunca Claude). Dos formas:
   - **Panel web**: servicio `api` → **Variables** → `BREVO_API_KEY` → ⋮ → **Edit** → pegar → ✓ y luego
     **Deploy** en la barra *"Apply N changes"*. Antes de desplegar abre **Details**: el 13/11/2026 había
     2 cambios en espera en `db` (quitarle el repositorio y la rama) que nadie pidió; se descartaron
     solo esos. Ojo: si descartas todo, también se pierde la clave.
   - **CLI con el portapapeles** (lo que funcionó el 13/11/2026): un script que **espera** a que copies el
     valor en Brevo y lo pasa con `| railway variable set BREVO_API_KEY --stdin --service api --skip-deploys`
     (Railway quita el salto de línea final). El valor no se ve en pantalla ni queda en el historial.
     `Get-Clipboard | railway ...` a secas **no** sirve si copias el comando desde el chat: el portapapeles
     queda con el comando y eso es lo que se guarda.
   - **Nunca** `Read-Host "..."`: tres veces la clave terminó pegada dentro del texto entre comillas y quedó
     visible en capturas (y en el historial de PowerShell, `ConsoleHost_history.txt`). Si una clave se ve
     en una captura, bórrala en Brevo y genera otra.
5. **Las variables que no son secretas** (`EMAIL_MODE=brevo` y `BREVO_SENDER`) se ponen igual. Comprueba
   después solo con sí/no (que el remitente tenga forma de correo, que la clave empiece por `xkeysib-`),
   nunca mostrando el valor. **No** copies el "Iniciar sesión" de la pestaña SMTP de Brevo: tiene forma de
   correo, pero es el usuario SMTP, no el remitente.
6. **Desplegar**: una variable puesta con `--skip-deploys` o borrada no redespliega sola:
   `railway redeploy --service api --yes`.
7. **Probar** con un registro **nuevo** desde la web de Vercel y revisar la bandeja **y la carpeta de spam**.
   "Reenviar código" no sirve para probar si el registro ya venció (10 min): la API responde 200 igual,
   a propósito (A-14), pero no envía nada.
8. **Al terminar**: quitar `APP_ENV` y redesplegar. Sin esa variable, si el correo falla la API responde 503
   ("No pudimos enviar el código…") y el código se descarta; no queda en ningún registro.

**Avisos:**

- **Spam**: Brevo no puede autenticar un remitente de Gmail (es un dominio gratuito), así que lo cambia por
  una dirección `@brevosend.com`. Por eso el correo puede caer en spam. Con un dominio propio verificado
  en Brevo esto se arregla.
- **La clave vence**: Brevo desactiva una clave de API que pasa **90 días sin usarse**, y además cada clave
  trae fecha de vencimiento (la del 13/11/2026 vence el 13/11/2027; se ve en *SMTP y API* → *Claves API*).
  Si la demo queda quieta mucho tiempo, genera otra y cámbiala en Railway.
- **Error 401 por "IP autorizadas"** (pasó el 13/11/2026): Brevo bloquea por defecto las llamadas desde IP
  que no conoce y manda al correo de la cuenta un aviso **"Verificar una nueva IP"**. No autorices esa IP
  suelta: en el plan Hobby la IP de salida de Railway puede cambiar. En Brevo → *Settings* → **Seguridad**
  → **IP autorizadas** (o el enlace "Haz clic aquí" del aviso morado de *Claves API y MCP*) pulsa
  **"Desactivar para claves API"** y deja **Activado** el de claves SMTP (PetConnect no usa SMTP). Es
  aceptable porque la única clave está sellada en Railway y restringida a enviar correos.

**Leer los registros** (desde cualquier carpeta, con la sesión de `railway login`):

```powershell
railway logs --service api
```

Busca la línea `Brevo rechazo el correo: HTTP ...`. El registro solo muestra el código HTTP, nunca el correo
ni la clave:

| Código | Qué significa | Qué revisar |
|---|---|---|
| 401 | Brevo no acepta la clave | La lista de IP autorizadas (lo más común) y que `BREVO_API_KEY` sea la clave nueva y activa |
| 400 | Brevo no acepta el mensaje | Que `BREVO_SENDER` sea exactamente el remitente validado en Brevo |
| Sin esa línea, y el correo no llega | Falta una variable o `EMAIL_MODE` está mal escrito | Que estén `EMAIL_MODE=brevo`, `BREVO_API_KEY` y `BREVO_SENDER` |
