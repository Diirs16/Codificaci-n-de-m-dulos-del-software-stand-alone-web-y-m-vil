# PetConnect — Guía completa de verificación

Guía de referencia para las evidencias GA7-220501096-AA3-EV01 (Codificación de módulos) y GA8-220501096-AA1-EV02 (Módulos integrados). Todos los pasos, en orden, para levantar y probar los tres módulos desde cero (stand-alone, web y móvil), verificar la API con Postman de punta a punta, y el registro de cada problema que salió durante la puesta en marcha con su solución.

**3 módulos · 9 endpoints · 9 problemas resueltos**

## Índice

1. [Requisitos previos](#1-requisitos-previos)
2. [Módulo Stand-Alone](#2-módulo-stand-alone)
3. [Módulo Web](#3-módulo-web)
4. [Módulo Móvil](#4-módulo-móvil)
5. [Postman — inicio rápido](#5-postman--inicio-rápido)
6. [Referencia de los 9 endpoints](#6-referencia-de-los-9-endpoints)
7. [Flujo de autenticación con doble verificación por correo](#7-flujo-de-autenticación-con-doble-verificación-por-correo)
8. [Registro de problemas de esta sesión](#8-registro-de-problemas-de-esta-sesión)
9. [Checklist final](#9-checklist-final)

---

## 1. Requisitos previos

> El entorno virtual de Python (`.venv`) **no se sube a GitHub** (está en `.gitignore`, junto con `node_modules`). Si acabas de clonar el repositorio, no vas a tener esa carpeta todavía — hay que crearla la primera vez. Si ya la tienes (por ejemplo en tu propia máquina), sáltate el paso 2 y solo actívala.

Antes de correr cualquier módulo, confirma esto una sola vez:

1. **MySQL corriendo** — servidor local en el puerto `3310`, con la base de datos `petconnect` ya creada (ejecutar el script de la base de datos si es la primera vez).

2. **Crear el entorno virtual de Python** (solo la primera vez, después de clonar el repo). Desde la raíz `Evidecia`:

   ```powershell
   python -m venv .venv
   ```

3. **Activarlo** — hay que repetir este paso cada vez que abras una terminal nueva para correr `main.py` o `api.py`:

   ```powershell
   (Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned)
   .\.venv\Scripts\Activate.ps1
   ```

   El prompt debe quedar así: `(.venv) PS ...\Evidecia>`.

4. **Instalar las dependencias** (solo la primera vez, con el entorno ya activado):

   ```powershell
   pip install -r petconnect.Backend\requirements.txt
   ```

5. **Configurar las variables de entorno** — copia la plantilla y complétala con tus propios datos de MySQL:

   ```powershell
   cd petconnect.Backend
   copy .env.example .env
   ```

   Abre `.env` y pon tu `DB_HOST`, `DB_PORT`, `DB_USER` y `DB_PASSWORD` reales. Luego genera las claves de seguridad (una sola vez):

   ```powershell
   python generate_keys.py
   ```

   Esto completa automáticamente `JWT_SECRET` y `FERNET_KEY` en el `.env`. El envío de correo es opcional — si lo dejas vacío o falla, el código de verificación simplemente se imprime en la consola del servidor en vez de llegar por correo (ver sección 7). Para que el correo llegue de verdad, configura Gmail:

   ```
   EMAIL_MODE=gmail
   GMAIL_USER=tucorreo@gmail.com
   GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
   ```

   `GMAIL_APP_PASSWORD` es una **contraseña de aplicación** de 16 caracteres (no tu contraseña normal), generada en `myaccount.google.com/apppasswords` — requiere verificación en dos pasos activada en la cuenta de Gmail.

6. **Node.js instalado** — necesario para el frontend web y la app móvil (no hace falta entorno virtual, cada carpeta usa `npm install` por su cuenta, la primera vez que se corre).

### Organización del código de autenticación

Toda la lógica de correo y de códigos de un solo uso (OTP) vive en dos módulos separados dentro de `petconnect.Backend`, no mezclada con las rutas de `api.py`:

```
petconnect.Backend/
  correo/
    plantillas.py   → diseño HTML del correo (código y bienvenida)
    servicio.py       → envío real (Gmail / SMTP / Mailtrap)
  otp/
    servicio.py        → generar, guardar, expirar y verificar códigos (AlmacenOTP)
```

## 2. Módulo Stand-Alone

App de consola en Python. No depende del navegador ni de ningún servidor web.

**`petconnect.Backend/main.py`**

1. Con el entorno virtual activado, entra a la carpeta:
   ```powershell
   cd petconnect.Backend
   ```
2. Ejecuta la app:
   ```powershell
   python main.py
   ```
3. Navega el menú: escribe `2` (Gestión de Mascotas) → `2` (Consultar todas las mascotas). Debe listar las mascotas reales de la base de datos.

> ✅ **Se ve bien si...** dice `[OK] Conexion establecida exitosamente.` y luego muestra la lista de mascotas con ID, nombre, especie y raza.

## 3. Módulo Web

Dos partes que corren juntas, en dos terminales distintas: el backend (API) y el frontend (interfaz).

### Backend — `petconnect.Backend/api.py` (`http://localhost:5000`)

1. Con el entorno virtual activado:
   ```powershell
   cd petconnect.Backend
   python api.py
   ```

> ✅ **Se ve bien si...** la terminal dice `[OK] API PetConnect corriendo en http://localhost:5000` y se queda corriendo (no se cierra sola). Déjala abierta.

### Frontend — `PetConnect.Front/petconnect-app` (`http://localhost:5173`)

1. Abre una **segunda** terminal (no cierres la de la API):
   ```powershell
   cd PetConnect.Front\petconnect-app
   npm install   # solo la primera vez
   npm run dev
   ```
2. Abre en el navegador: `http://localhost:5173`

> ✅ **Se ve bien si...** la página carga el catálogo de productos con imágenes y precios reales.

## 4. Módulo Móvil

App en React Native con Expo. Necesita que el backend del paso anterior siga corriendo, porque consume la misma API.

**`PetConnect.Mobile`** (`http://localhost:8081`)

1. Abre una **tercera** terminal:
   ```powershell
   cd PetConnect.Mobile
   npm install   # solo la primera vez
   npx expo start --web
   ```
2. Abre en el navegador y prueba las 3 pestañas: Tienda (catálogo), Adopción, Perfil (login). Todas deben cargar datos reales de la misma API del puerto 5000.

> ✅ **Se ve bien si...** la pestaña Tienda muestra los mismos productos que en la web, y en Perfil, al iniciar sesión con contraseña correcta, la app pide un **código de 6 dígitos** enviado al correo (igual que en la web) antes de entregar la sesión — ver sección 7.2.

## 5. Postman — inicio rápido

Con el backend corriendo (sección 3), sigue estos pasos en orden:

1. **Importa la colección** — atajo `Ctrl + O` (o botón Import) → pestaña File → selecciona:
   ```
   petconnect.Backend/postman/PetConnect.postman_collection.json
   ```
2. **Si quedó duplicada**, borra la copia extra: clic derecho sobre una de las dos "PetConnect API" → Delete.
3. **Prueba primero lo que no pide login** — carpeta Productos → *Listar productos* → Send. Debe responder `200 OK`. Repite con Mascotas.
4. **Revisa el Body antes de enviar peticiones POST** — en *Registrar usuario*, *Verificar código* e *Iniciar sesión*, la pestaña Body debe tener marcado **raw** y el dropdown en **JSON** (no "form-data", no "Text"). Si aparece en form-data, la API responde que faltan datos aunque los veas llenos.

## 6. Referencia de los 9 endpoints

Todas las rutas van después de `http://localhost:5000`. Las de método **GET** también se pueden probar pegando la URL directo en el navegador — las de **POST** no, esas necesitan Postman.

| Método | Ruta | Acceso | Qué esperar |
|---|---|---|---|
| GET | `/api/productos` | Libre | 200 OK — lista de 14 productos |
| GET | `/api/productos/13` | Libre | 200 OK — detalle de un producto (o 404 si el ID no existe) |
| GET | `/api/mascotas/adopcion` | Libre | 200 OK — hoy devuelve `[]`: normal, ninguna mascota está marcada "en adopción" en la BD |
| GET | `/api/mascotas/3` | Libre | 200 OK — detalle de "Luna" (o 404 si el ID no existe) |
| POST | `/api/utils/validar-correo` | Libre | 200 OK — `{"valido": true/false, "mensaje": ...}`. Valida formato + dominio (MX). Body: `email` |
| POST | `/api/auth/register` | Libre | 200 OK — "Codigo enviado". Body: `name`, `email`, `password` |
| POST | `/api/auth/verify` | Libre | 201 — crea el usuario, manda el correo de bienvenida y devuelve `token`. Body: `email`, `code` |
| POST | `/api/auth/login` | Libre | 200 OK — **ya no da el token directo**: valida usuario/contraseña y manda un código de verificación al correo. Body: `email`, `password` |
| POST | `/api/auth/login/verify` | Libre | 200 OK — con el código correcto, entrega el `token` JWT (válido 24h). Body: `email`, `code` |
| GET | `/api/auth/me` | Con token | 401 sin `Authorization: Bearer <token>`; 200 con token válido |

### Rutas que NO existen (para no perder tiempo buscándolas)

| Ruta | Resultado |
|---|---|
| `GET /api/mascota/adopcion` | 404 — falta la "s" de "mascotas" |
| `GET /api/mascotas` | 404 — no existe listado sin filtro en la API web (sí existe en la app de consola) |
| `GET /api/auth/` | 404 — esa ruta sola no existe |

## 7. Flujo de autenticación con doble verificación por correo

Tanto el **registro** como el **login** piden un código de 6 dígitos enviado al correo antes de entregar la sesión — es el mismo mecanismo (`otp.AlmacenOTP`) reutilizado en los dos flujos. Si el correo no está configurado (sección 1) o el envío falla, el código se imprime en la consola del servidor en vez de perderse — esto es intencional, no un error, y permite probar todo sin depender de un servicio externo. Con Gmail configurado, el correo llega de verdad (código + un correo de bienvenida aparte al completar el registro).

### 7.1 Registro (crea la cuenta)

1. **Registrar usuario** — carpeta Autenticación → *Registrar usuario* → Send, con Body en raw + JSON:
   ```json
   {
     "name": "Daniel Test",
     "email": "dtest@example.com",
     "password": "Password123!"
   }
   ```
   Debe responder `200 OK` con `"message": "Codigo enviado"`.

2. **Consigue el código** — o bien llega al correo (si Gmail está configurado), o bien queda impreso en la terminal donde corre `python api.py`:
   ```
   [DEV] No se pudo enviar el correo (...). Codigo para dtest@example.com: 483920
   ```

3. **Verificar código** — carpeta Autenticación → *Verificar código de registro* → Body raw + JSON con el mismo email y el código:
   ```json
   {
     "email": "dtest@example.com",
     "code": "483920"
   }
   ```
   Debe responder `201` con un `token`. En este momento se crea la cuenta en la base de datos **y llega el correo de bienvenida** ("¡Bienvenido a la familia PetConnect!").

### 7.2 Login (ya con la cuenta creada)

4. **Iniciar sesión (paso 1)** — con el mismo email/password del registro → Send. Debe responder `200` con `"message": "Codigo enviado"` — **ya no entrega el token en este paso**, solo manda un código nuevo al correo (asunto "Código de inicio de sesión", para diferenciarlo del de registro).

5. **Verificar código de inicio de sesión (paso 2)** — Body raw + JSON con el email y el código recibido. Debe responder `200` con `token` — la colección lo guarda automático en la variable `token`.

6. **Perfil autenticado** — *Perfil autenticado* → Send (ya usa `{{token}}` solo). Debe responder `200` con tus datos de usuario.

> ✅ **Confirmado en esta sesión**: se probó el flujo completo (registro → código → verificación → correo de bienvenida → login → código → verificación → perfil) con Gmail real configurado, y los correos llegaron correctamente a la bandeja de entrada.

### 7.3 Este mismo flujo, en la app móvil

`PetConnect.Mobile` usa la misma API, así que el login ahí también pide el código en dos pasos:

1. Pestaña **Perfil** → escribe correo y contraseña → **Ingresar**. La pantalla cambia a "Verificar inicio de sesión".
2. Escribe el código de 6 dígitos (correo real o consola del backend) → **Confirmar código**.
3. Si el código es incorrecto, se muestra "Codigo incorrecto" sin romper la app; con el código correcto, entra con sesión activa.

> ⚠️ Este flujo se agregó **después** de construir el módulo móvil por primera vez — hubo que actualizar `AuthContext.js` y `LoginScreen.js` para que dejaran de esperar el token directo (ver problema #9 en la sección 8).

## 8. Registro de problemas de esta sesión

Todo lo que se atascó mientras se probaban los módulos, en orden real, con la causa y la solución exacta.

| # | Síntoma | Causa | Solución |
|---|---|---|---|
| 1 | El preview del frontend falló: `Port 5173 is in use` | Había quedado corriendo un servidor Vite de una sesión anterior que nunca se cerró | Se cerró el proceso viejo. El puerto se mantuvo fijo en 5173 (sin "autoPort") porque el backend solo permite ese origen en su CORS |
| 2 | `preview_start` seguía fallando: `spawn cmd.exe ENOENT` | Falla del entorno de la herramienta de vista previa al invocar npm, no del proyecto | Se levantó el servidor manualmente (`npm run dev`) y se abrió la URL directa en el navegador |
| 3 | `python api.py` → `ModuleNotFoundError: No module named 'dotenv'` | Se ejecutó con el Python del sistema, sin las dependencias (solo están en `.venv`) | Activar el entorno antes de correr la API (ver sección 1) |
| 4 | Dos procesos de Python escuchando el puerto 5000 a la vez | Un backend de una sesión anterior seguía activo cuando se levantó uno nuevo | Se cerró el proceso viejo con `Stop-Process`, dejando solo el que el usuario controla |
| 5 | `http://localhost:5000` (sin ruta) responde `404 Not Found` | No es un error: la API no define ninguna ruta en la raíz `/`, solo bajo `/api/...` | Usar una ruta real, por ejemplo `/api/productos` |
| 6 | `/api/mascota/adopcion` (singular) → 404; y probar rutas POST desde el navegador | Error de tipeo (falta la "s"); y los navegadores solo mandan GET al pegar una URL, por eso las rutas POST siempre dan 405 así | Usar `/api/mascotas/adopcion` con "s"; probar las rutas POST solo desde Postman |
| 7 | En Postman, el Body de *Registrar usuario* tenía datos pero la API respondía "Nombre, correo y contrasena son requeridos" | El modo del Body estaba en **form-data** en vez de **raw + JSON**. Flask solo lee JSON crudo | Cambiar el Body a raw con el dropdown en JSON |
| 8 | Con el Body ya corregido, *Registrar usuario* respondía `500`: "No se pudo enviar el correo: Connection unexpectedly closed" | El `.env` solo tenía `MAILTRAP_API_TOKEN`, pero el modo por defecto de envío es SMTP, que necesita usuario/contraseña SMTP no configurados | Se modificó `api.py` para que, si el envío de correo falla, el registro no se bloquee: el código queda impreso en la consola del servidor y el flujo completo funciona sin depender de Mailtrap |
| 9 | Al agregar el código OTP al login web, el login de la app móvil quedó roto (intentaba guardar un token que ya no llega en el primer paso) | `AuthContext.js` y `LoginScreen.js` de `PetConnect.Mobile` no se habían actualizado cuando se cambió `/api/auth/login` en el backend | Se actualizaron para el mismo flujo de dos pasos que la web (`iniciarLogin` / `verificarLogin`), y se agregó `establecerSesion` para no romper el registro, que sí sigue recibiendo el token directo |

## 9. Checklist final

- [x] **Módulo Stand-Alone corre y conecta a MySQL** — `python petconnect.Backend/main.py`, menú → 2 → 2
- [x] **Módulo Web: backend responde** — `python petconnect.Backend/api.py` (con `.venv` activado) → probar `/api/productos`
- [x] **Módulo Web: frontend carga datos reales** — `npm run dev` en `PetConnect.Front/petconnect-app` → `http://localhost:5173`
- [x] **Módulo Móvil corre y consume la misma API** — `npx expo start --web` en `PetConnect.Mobile` → `http://localhost:8081`
- [x] **Colección Postman importada y probada** — `petconnect.Backend/postman/PetConnect.postman_collection.json` (9 endpoints)
- [x] **Registro con verificación por correo probado** — código → verificación → correo de bienvenida
- [x] **Login en dos pasos probado** — password → código por correo → verificación → token (24h)
- [x] **Envío real de correo por Gmail configurado y confirmado** — `EMAIL_MODE=gmail` en `.env`
- [x] **Código organizado en módulos separados** — `correo/` (plantillas + envío) y `otp/` (códigos de un solo uso), fuera de `api.py`
- [x] **Login en dos pasos también funciona en la app móvil** — corregido y probado tras encontrarlo roto (ver problema #9)
- [x] **Documentos de la evidencia GA7 completos** — `GA7-220501096-AA3-EV01-PetConnect.docx` y `petconnect.Backend/DOCUMENTACION_PETCONNECT.docx`
- [x] **Documento de la evidencia GA8 (Módulos integrados) completo** — `GA8-220501096-AA1-EV02-PetConnect.docx` (tabla de módulos, integración con evidencia real, acta de pruebas con 9 casos)
