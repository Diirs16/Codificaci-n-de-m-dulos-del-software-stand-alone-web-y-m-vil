# PetConnect — Guía completa de verificación

Evidencia GA7-220501096-AA3-EV01. Todos los pasos, en orden, para levantar y probar los tres módulos desde cero (stand-alone, web y móvil), verificar la API con Postman de punta a punta, y el registro de cada problema que salió durante la puesta en marcha con su solución.

**3 módulos · 8 endpoints · 8 problemas resueltos**

## Índice

1. [Requisitos previos](#1-requisitos-previos)
2. [Módulo Stand-Alone](#2-módulo-stand-alone)
3. [Módulo Web](#3-módulo-web)
4. [Módulo Móvil](#4-módulo-móvil)
5. [Postman — inicio rápido](#5-postman--inicio-rápido)
6. [Referencia de los 8 endpoints](#6-referencia-de-los-8-endpoints)
7. [Flujo de autenticación completo](#7-flujo-de-autenticación-completo-de-punta-a-punta)
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

   Esto completa automáticamente `JWT_SECRET` y `FERNET_KEY` en el `.env`. El campo de Mailtrap se puede dejar vacío — si no está configurado, el código de verificación de registro simplemente se imprime en la consola del servidor en vez de llegar por correo (ver sección 7).

6. **Node.js instalado** — necesario para el frontend web y la app móvil (no hace falta entorno virtual, cada carpeta usa `npm install` por su cuenta, la primera vez que se corre).

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

> ✅ **Se ve bien si...** la pestaña Tienda muestra los mismos productos que en la web, y la pestaña Perfil te deja escribir un correo/contraseña e intentar iniciar sesión.

## 5. Postman — inicio rápido

Con el backend corriendo (sección 3), sigue estos pasos en orden:

1. **Importa la colección** — atajo `Ctrl + O` (o botón Import) → pestaña File → selecciona:
   ```
   petconnect.Backend/postman/PetConnect.postman_collection.json
   ```
2. **Si quedó duplicada**, borra la copia extra: clic derecho sobre una de las dos "PetConnect API" → Delete.
3. **Prueba primero lo que no pide login** — carpeta Productos → *Listar productos* → Send. Debe responder `200 OK`. Repite con Mascotas.
4. **Revisa el Body antes de enviar peticiones POST** — en *Registrar usuario*, *Verificar código* e *Iniciar sesión*, la pestaña Body debe tener marcado **raw** y el dropdown en **JSON** (no "form-data", no "Text"). Si aparece en form-data, la API responde que faltan datos aunque los veas llenos.

## 6. Referencia de los 8 endpoints

Todas las rutas van después de `http://localhost:5000`. Las de método **GET** también se pueden probar pegando la URL directo en el navegador — las de **POST** no, esas necesitan Postman.

| Método | Ruta | Acceso | Qué esperar |
|---|---|---|---|
| GET | `/api/productos` | Libre | 200 OK — lista de 14 productos |
| GET | `/api/productos/13` | Libre | 200 OK — detalle de un producto (o 404 si el ID no existe) |
| GET | `/api/mascotas/adopcion` | Libre | 200 OK — hoy devuelve `[]`: normal, ninguna mascota está marcada "en adopción" en la BD |
| GET | `/api/mascotas/3` | Libre | 200 OK — detalle de "Luna" (o 404 si el ID no existe) |
| POST | `/api/auth/register` | Libre | 200 OK — "Codigo enviado". Body: `name`, `email`, `password` |
| POST | `/api/auth/verify` | Libre | 201 — crea el usuario y devuelve `token`. Body: `email`, `code` |
| POST | `/api/auth/login` | Libre | 200 OK — devuelve `token` JWT. Body: `email`, `password` |
| GET | `/api/auth/me` | Con token | 401 sin `Authorization: Bearer <token>`; 200 con token válido |

### Rutas que NO existen (para no perder tiempo buscándolas)

| Ruta | Resultado |
|---|---|
| `GET /api/mascota/adopcion` | 404 — falta la "s" de "mascotas" |
| `GET /api/mascotas` | 404 — no existe listado sin filtro en la API web (sí existe en la app de consola) |
| `GET /api/auth/` | 404 — esa ruta sola no existe |

## 7. Flujo de autenticación completo, de punta a punta

Registro → código → verificación → login → perfil. El envío de correo real (Mailtrap) no está configurado con usuario/contraseña SMTP, así que el código de verificación se imprime en la consola del servidor en vez de llegar por correo — esto es intencional, no un error, y permite probar todo el flujo sin depender de un servicio externo.

1. **Registrar usuario** — carpeta Autenticación → *Registrar usuario* → Send, con Body en raw + JSON:
   ```json
   {
     "name": "Daniel Test",
     "email": "dtest@example.com",
     "password": "Password123!"
   }
   ```
   Debe responder `200 OK` con `"message": "Codigo enviado"`.

2. **Copia el código desde la terminal del backend** — en la terminal donde corre `python api.py`, busca una línea como:
   ```
   [DEV] No se pudo enviar el correo (...). Codigo para dtest@example.com: 483920
   ```
   Ese número de 6 dígitos es el código.

3. **Verificar código** — carpeta Autenticación → *Verificar código* → Body raw + JSON con el mismo email y el código copiado:
   ```json
   {
     "email": "dtest@example.com",
     "code": "483920"
   }
   ```
   Debe responder `201` con un `token`.

4. **Iniciar sesión** — con el mismo email/password del paso 1 → Send. Debe responder `200` con `token` — la colección lo guarda automático en la variable `token`.

5. **Perfil autenticado** — *Perfil autenticado* → Send (ya usa `{{token}}` solo). Debe responder `200` con tus datos de usuario.

> ✅ **Confirmado en esta sesión**: se probó *Registrar usuario* con un correo nuevo y respondió `200 OK` sin depender de Mailtrap, gracias al fallback agregado en `api.py`.

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

## 9. Checklist final

- [x] **Módulo Stand-Alone corre y conecta a MySQL** — `python petconnect.Backend/main.py`, menú → 2 → 2
- [x] **Módulo Web: backend responde** — `python petconnect.Backend/api.py` (con `.venv` activado) → probar `/api/productos`
- [x] **Módulo Web: frontend carga datos reales** — `npm run dev` en `PetConnect.Front/petconnect-app` → `http://localhost:5173`
- [x] **Módulo Móvil corre y consume la misma API** — `npx expo start --web` en `PetConnect.Mobile` → `http://localhost:8081`
- [x] **Colección Postman importada y probada** — `petconnect.Backend/postman/PetConnect.postman_collection.json`
- [x] **Flujo de autenticación completo probado** — registro → código en consola → verificación → login → perfil, sin depender de Mailtrap
- [x] **Documentos de la evidencia completos** — `GA7-220501096-AA3-EV01-PetConnect.docx` y `petconnect.Backend/DOCUMENTACION_PETCONNECT.docx`
