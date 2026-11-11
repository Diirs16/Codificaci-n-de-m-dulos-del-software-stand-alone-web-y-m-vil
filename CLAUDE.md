# PetConnect — Instrucciones para Claude Code

Este archivo lo lee Claude Code automáticamente cada vez que se abre una sesión en esta carpeta.
Aquí viven las **reglas estrictas** del proyecto. Si una petición choca con una regla, Claude debe
decirlo antes de actuar, no ignorarla en silencio.

## Qué es el proyecto

PetConnect es una plataforma para mascotas (adopción, catálogo de productos, proveedores de servicios)
hecha como proyecto formativo SENA (ficha 220501096). Tiene tres módulos que comparten la misma API:

| Módulo | Carpeta | Tecnología | Cómo se levanta | Puerto |
|---|---|---|---|---|
| Backend (API + consola) | `petconnect.Backend/` | Python 3.14, Flask, MySQL, bcrypt, JWT | `python api.py` (con el `.venv` de la raíz activo) | 5000 |
| Web | `PetConnect.Front/petconnect-app/` | React 19 + Vite 8 + Tailwind 4 | `npm run dev` | 5173 |
| Móvil | `PetConnect.Mobile/` | Expo 57 + React Native 0.86 | `npm start` / `npm run android` | 8081 |

- MySQL corre en el puerto **3310**, base `petconnect`. La configuración sale de `petconnect.Backend/.env`.
- El Front llama a `/api` y Vite lo redirige a `http://localhost:5000` (ver `vite.config.js`).
- El Móvil usa `10.0.2.2:5000` en el emulador de Android.
- La documentación y evidencias de las guías (GA7, GA8, GA9) están en `Documentacion/`.

## Comandos de verificación

```bash
# Backend: pruebas de seguridad (no necesitan base de datos)
cd petconnect.Backend && ../.venv/Scripts/python -m unittest discover -s tests -v

# Front: linter y build
cd PetConnect.Front/petconnect-app && npm run lint && npm run build
```

En la terminal del usuario (Windows PowerShell 5.1) `&&` no existe. Desde la raíz `Evidecia`, un comando por línea
(si ya estás dentro de la carpeta, salta el `cd`; `cd ..\..` vuelve a la raíz):

```powershell
# Backend
cd petconnect.Backend
..\.venv\Scripts\python -m unittest discover -s tests -v
cd ..

# Front (si el lint falla, no sigas con el build)
cd PetConnect.Front\petconnect-app
npm run lint
npm run build
cd ..\..
```

## Reglas estrictas (obligatorias)

### 1. Idioma y forma de explicar
- Todo en **español** (respuestas, comentarios de código, mensajes de commit, textos de la interfaz).
- El dueño del proyecto está aprendiendo. Después de cada cambio, explica **qué** hiciste, **por qué**
  y **qué archivo** tocaste, en lenguaje sencillo. Si usas un término técnico nuevo, defínelo en una línea.
- Si existe una forma más simple de hacer algo, usa la simple y di cuál descartaste.

### 2. Primero el plan, luego el código
- Para cambios grandes (una funcionalidad nueva, un módulo, un rediseño, tocar la base de datos,
  tocar seguridad o más de 3 archivos) **propón un plan primero** y espera aprobación.
  El usuario activa el *modo plan* con `Shift + Tab`.
- Para cambios pequeños y concretos (un texto, un color, un bug localizado) se puede actuar directo.

### 3. Una parte a la vez
- Trabaja **una sección o pantalla a la vez**. No mezcles en un mismo cambio Front, Móvil y Backend
  salvo que el plan aprobado lo diga.
- Al terminar cada parte, di cómo verla funcionando (comando y URL) antes de seguir con la siguiente.

### 4. Secretos y datos sensibles (NUNCA se negocia)
- **Nunca** leas, muestres, copies ni subas el contenido de archivos `.env`, `*.pem`, `*.key` o similares.
  Para saber qué variables existen, usa `.env.example`.
- **Nunca** escribas contraseñas, tokens, `JWT_SECRET`, `FERNET_KEY` ni contraseñas de aplicación
  directamente en el código. Van en `.env` y se leen con `os.getenv` / `import.meta.env`.
- Si el usuario pega una clave en el chat, avísale que debe cambiarla (rotarla) y no la repitas.
- Las contraseñas de usuarios se guardan **solo con bcrypt** (`security/passwords.py`). Nada de SHA-256,
  MD5 ni texto plano.
- Toda consulta SQL va **parametrizada** (`cursor.execute(sql, params)`), nunca con f-strings ni `+`.

### 5. Datos personales (Ley 1581 de 2012 — Habeas Data)
- Correos, teléfonos, direcciones y datos de dueños de mascotas son datos personales.
- No los imprimas en logs, no los pongas en URLs ni en mensajes de error que vea el usuario final.
- Los datos de prueba deben ser inventados (nunca datos reales de personas).

### 6. Información veterinaria y de salud animal
- Claude puede escribir textos de salud que *suenan* bien pero están mal. Cualquier contenido sobre
  vacunas, dosis, medicamentos, enfermedades, cuidados o alimentación se marca con el comentario
  `<!-- REVISAR-VETERINARIO -->` (HTML/JSX) o `# REVISAR-VETERINARIO` (Python) y se avisa al usuario
  que debe validarlo con un profesional antes de publicarlo. Usa la skill `/revision-contenido-mascotas`.

### 7. Imágenes y recursos
- Solo imágenes propias, con licencia libre (Unsplash, Pexels, etc.) o generadas. Nunca imágenes de Google
  sin permiso. Si usas una de ejemplo, déjalo anotado.

### 8. Git: guardar partida
- Cada vez que algo quede funcionando, propón un commit (skill `/guardar-partida`).
- Mensajes de commit en español, en presente y describiendo el *qué* (ej. "Agrega filtro por especie
  en adopción").
- `git push --force` está **prohibido** (bloqueado en `.claude/settings.json`). `git push`, `git reset --hard`,
  `git clean`, borrar ramas y `rm -rf` siempre piden confirmación.
- Antes de hacer commit, corre las verificaciones del módulo que cambió.

### 9. Diseño de interfaz
- Para pantallas nuevas o rediseños usa la skill `frontend-design` (se activa sola) y después
  `/impeccable audit` para revisar accesibilidad, móvil y jerarquía visual.
- Todo debe verse bien en celular (ancho 375 px) y tener contraste suficiente.
- Respeta los componentes y estilos existentes (`src/components/`, Tailwind, `lucide-react`) antes de
  inventar nuevos.

### 10. Cuando algo falla
- No adivines. Pide (o busca) el error completo, reprodúcelo, encuentra la causa y luego corrige.
  Usa la skill `/reportar-error` para ordenar la información.

## Skills del proyecto (en `.claude/skills/`)

| Skill | Para qué |
|---|---|
| `/levantar-proyecto` | Arranca backend, web y/o móvil y dice qué URL abrir |
| `/nueva-funcionalidad` | Flujo guiado: contexto → plan → construir por partes → probar → commit |
| `/explicar` | Explica lo último que se hizo como para principiante |
| `/reportar-error` | Ordena un error (qué hice, qué esperaba, qué pasó, error completo) y lo depura |
| `/guardar-partida` | Revisa cambios, corre pruebas, busca secretos y hace commit |
| `/revision-contenido-mascotas` | Revisa textos de salud animal, imágenes y datos personales antes de publicar |
| `frontend-design` | (externa, Anthropic) Diseño de interfaces con identidad propia; se activa sola al diseñar |
| `/impeccable` | (externa) `audit`, `polish`, `adapt`, `delight` y más para pulir la interfaz |
| `/deploy-to-vercel` | (externa, Vercel) Publicar la web en Vercel (siempre *preview* salvo que se pida producción) |
| `vercel-react-best-practices` | (externa, Vercel) Buenas prácticas de rendimiento en React (Front web) |
| `vercel-react-native-skills` | (externa, Vercel) Buenas prácticas de React Native / Expo (Móvil) |

Origen y versión de las skills externas: `.claude/skills/PROCEDENCIA.md`.

### Sobre publicar en Vercel
- Solo se publica la **web** (`PetConnect.Front/petconnect-app`, que en Vercel se configura como *Root Directory*).
- El backend Flask + MySQL **no** corre en Vercel. En desarrollo el proxy de Vite manda `/api` a
  `localhost:5000`, pero en Vercel ese proxy no existe: antes de publicar hay que alojar la API en otro
  servicio y apuntar el Front a esa URL. Si no, la página carga pero sin datos. Avísalo antes de publicar.
- Nunca subir variables secretas como `VITE_*` (quedan visibles en el navegador).

Más detalle sobre todo esto en `Documentacion/NUEVAS-PRACTICAS-CLAUDE-CODE.md`.
