# Nuevas prácticas de trabajo con Claude Code — PetConnect

**Fecha:** 3 de noviembre de 2026
**Proyecto:** PetConnect (Backend Flask + Web React/Vite + Móvil Expo)
**Origen:** guía de buenas prácticas para trabajar con Claude Code, adaptada a este proyecto.

Este documento explica **todo lo nuevo** que se agregó al repositorio: qué es, en qué nos ayuda, cómo se
implementó y cómo cambia el flujo de trabajo. Las prácticas se aplicaron de tres formas:

| Forma | Qué significa | Dónde vive |
|---|---|---|
| **Regla estricta** | Claude la lee siempre y debe cumplirla; algunas además están **bloqueadas por configuración** (no dependen de que Claude “se acuerde”) | `CLAUDE.md` (raíz y por módulo), `.claude/settings.json`, `.claude/hooks/` |
| **Skill** | Un procedimiento paso a paso que se invoca con `/nombre` o que Claude activa solo cuando aplica | `.claude/skills/<nombre>/SKILL.md` |
| **Instalado** | Skills externas descargadas de sus repositorios oficiales | `.claude/skills/` + `PROCEDENCIA.md` |
| **Hábito** | Cosas que haces tú en la interfaz (teclas, comandos); quedan documentadas aquí | Este documento |

---

## Índice

1. [Mapa: de la guía a lo implementado](#1-mapa-de-la-guía-a-lo-implementado)
2. [CLAUDE.md: la memoria del proyecto](#2-claudemd-la-memoria-del-proyecto)
3. [Permisos: lo que Claude puede, debe preguntar o no puede hacer](#3-permisos)
4. [Hooks: reglas que se cumplen solas](#4-hooks-reglas-que-se-cumplen-solas)
5. [Skills propias del proyecto](#5-skills-propias-del-proyecto)
6. [Skills externas instaladas](#6-skills-externas-instaladas)
7. [Protección de secretos y archivos locales](#7-protección-de-secretos-y-archivos-locales)
8. [Hábitos: teclas y comandos de Claude Code](#8-hábitos-teclas-y-comandos)
9. [El nuevo flujo de trabajo, de punta a punta](#9-el-nuevo-flujo-de-trabajo)
10. [Inventario de archivos nuevos o modificados](#10-inventario-de-archivos)
11. [Cómo se verificó](#11-cómo-se-verificó)
12. [Pendientes y advertencias](#12-pendientes-y-advertencias)

---

## 1. Mapa: de la guía a lo implementado

| Sección de la guía | Cómo quedó en PetConnect | Tipo |
|---|---|---|
| 1. Qué es Claude Code | Contexto en `CLAUDE.md`: Claude sabe qué módulos hay, cómo se levantan y cómo se prueban | Regla |
| 2. Git como “guardar partida” | Ya existía git; se agregó la skill `/guardar-partida` y el hook que revisa secretos antes de cada commit | Skill + Hook |
| 3. Dar contexto en el primer mensaje | La skill `/nueva-funcionalidad` hace las preguntas de contexto por ti si la petición es corta | Skill |
| 4. Modo plan | Regla 2 del `CLAUDE.md`: cambios grandes → plan primero y esperar aprobación | Regla + Hábito |
| 5. Ir por partes y ver en el navegador | Regla 3 del `CLAUDE.md` + skill `/levantar-proyecto` | Regla + Skill |
| 6. Pedir cambios específicos / capturas | Documentado en la sección 8; la skill `/nueva-funcionalidad` pide capturas de referencia | Hábito + Skill |
| 7. Que te explique para aprender | Regla 1 del `CLAUDE.md` (explicar siempre) + skill `/explicar` | Regla + Skill |
| 8. Leer los permisos antes de aceptar | `.claude/settings.json`: lista de lo permitido, lo que pregunta y lo prohibido | Configuración |
| 9. Cuando algo falla | Skill `/reportar-error` con la ficha qué hice / qué esperaba / qué pasó / error completo | Skill |
| 10. Skills frontend-design, impeccable, vercel | Descargadas e instaladas en `.claude/skills/` | Instalado |
| 11. CLAUDE.md | Creado en la raíz y uno por módulo (Backend, Web, Móvil) | Regla |
| 12. Comandos y teclas | Documentado en la sección 8 | Hábito |
| 13. Ideas para el sitio | No aplica directamente (PetConnect no es un sitio de veterinaria); quedan como referencia para futuras funcionalidades usando `/nueva-funcionalidad` | — |
| 14. Cosas que hay que cuidar | Reglas 4–7 del `CLAUDE.md`, hooks de secretos, permisos `deny`, skill `/revision-contenido-mascotas` | Regla + Hook + Skill |

---

## 2. CLAUDE.md: la memoria del proyecto

### Qué es
Claude no recuerda conversaciones anteriores. `CLAUDE.md` es un archivo que Claude Code **lee automáticamente
al abrir cada sesión** en esta carpeta. Es como el manual de inducción que se le da a un desarrollador nuevo.
Además, cuando Claude trabaja dentro de una subcarpeta que tiene su propio `CLAUDE.md`, también lo carga.

### Cómo se implementó
| Archivo | Contenido |
|---|---|
| `CLAUDE.md` (raíz) | Qué es PetConnect, tabla de módulos/puertos, comandos de verificación y las **10 reglas estrictas** |
| `petconnect.Backend/CLAUDE.md` | Arquitectura por capas + DAO, SQL solo en `dao/` y parametrizado, formato de errores, `@require_auth`, cómo correr las pruebas |
| `PetConnect.Front/petconnect-app/CLAUDE.md` | Estructura de `src/`, todas las llamadas HTTP por `services/api.js`, mobile first, accesibilidad, peligro de los `VITE_*` |
| `PetConnect.Mobile/CLAUDE.md` | Importa el `AGENTS.md` existente (documentación de Expo 57), estructura de pantallas, `10.0.2.2` vs `localhost` |

### Las 10 reglas estrictas (resumen)
1. **Español y explicar siempre** qué se hizo, por qué y en qué archivo, en lenguaje sencillo.
2. **Plan primero** para cambios grandes (funcionalidad nueva, rediseño, base de datos, seguridad o más de 3 archivos).
3. **Una parte a la vez**, sin mezclar módulos, y decir cómo verla funcionando.
4. **Secretos:** nunca leer/mostrar `.env` ni llaves, nunca quemar claves en el código, bcrypt para contraseñas, SQL parametrizado.
5. **Datos personales (Ley 1581 de 2012):** no en logs, URLs ni mensajes de error; datos de prueba ficticios.
6. **Contenido veterinario:** marcarlo con `REVISAR-VETERINARIO` y avisar que lo valide un profesional.
7. **Imágenes:** solo propias o con licencia libre.
8. **Git:** commit cuando algo funciona, mensajes en español; `push --force` prohibido; acciones destructivas con confirmación.
9. **Diseño:** `frontend-design` + `/impeccable audit`, mobile first a 375 px, respetar componentes existentes.
10. **Errores:** no adivinar; reproducir, encontrar la causa y luego corregir.

### En qué nos ayuda
- No hay que repetir en cada conversación “estoy aprendiendo, explícame”, “todo en español”, “no toques el `.env`”.
- Claude sabe de entrada que el backend usa el puerto 5000, MySQL el 3310 y que las pruebas se corren con `unittest`,
  así que no inventa comandos.
- Las reglas de seguridad que ya se habían corregido en el proyecto (NC-001 bcrypt, NC-008 JWT) quedan protegidas
  para que no se reintroduzcan.

### Cómo transforma el flujo
**Antes:** cada sesión empezaba de cero y había que volver a explicar el proyecto.
**Ahora:** Claude arranca sabiendo qué es PetConnect, cómo se prueba y qué no puede hacer. Si quieres agregar una
regla nueva (por ejemplo los colores de la marca), la escribes en `CLAUDE.md` y queda para siempre.

---

## 3. Permisos

### Qué es
`.claude/settings.json` define qué acciones Claude puede hacer **sin preguntar**, cuáles **siempre debe preguntar** y
cuáles **tiene prohibidas**. Es la versión automática de “lee antes de aceptar”: las cosas peligrosas ni siquiera
dependen de que tú las leas a tiempo.

### Cómo se implementó
| Lista | Reglas | Por qué |
|---|---|---|
| `allow` (sin preguntar) | `git status/diff/log/show`, `git branch`, `npm run lint`, `npm run build`, pruebas `unittest` del backend | Son de solo lectura o verificación; preguntar por ellas solo genera ruido |
| `ask` (siempre pregunta) | `git push`, `git reset --hard`, `git clean`, `git branch -D`, `git checkout -- …`, `rm -rf`, `npm install`, `pip install`, `Remove-Item` | Publican, borran o instalan cosas: tú decides cada vez |
| `deny` (prohibido) | Leer o editar `.env`, `.env.local`, `.env.*.local`, `*.pem`, `*.key`; `git push --force` / `-f` | Exponer secretos o reescribir el historial remoto no tiene marcha atrás |

### En qué nos ayuda
- Menos ventanas de permiso para cosas inofensivas → puedes concentrarte en las que importan.
- Las acciones irreversibles siempre te las va a preguntar, aunque estés en un modo más automático.

### Cómo transforma el flujo
Cuando Claude te pida permiso, ya sabes que es algo que vale la pena leer (publicar, borrar, instalar).
Si no entiendes el comando, respóndele: *“no, primero explícame qué hace ese comando”*.

---

## 4. Hooks: reglas que se cumplen solas

### Qué es
Un **hook** es un programa pequeño que Claude Code ejecuta automáticamente antes o después de cada acción de Claude.
A diferencia de una regla escrita (que Claude podría olvidar), un hook **se ejecuta siempre**.
Los tres hooks están escritos en JavaScript (Node.js, que ya está instalado) para que funcionen igual en Windows.

### Cómo se implementó
| Hook | Cuándo corre | Qué hace |
|---|---|---|
| `.claude/hooks/proteger-secretos.js` | **Antes** de leer, editar, escribir o correr un comando | Bloquea abrir/editar `.env` y llaves; bloquea `cat`/`Get-Content`/`copy` de esos archivos en la terminal; bloquea `git add -f` y `git add .env`; si Claude va a escribir algo como `password = "…"` en el código, **te pregunta** antes |
| `.claude/hooks/revisar-commit.js` | **Antes** de cualquier `git commit` | Revisa lo que está preparado (*staged*): si hay un `.env`, una llave privada, una variable de `.env` con valor real o una clave escrita en el código, **bloquea el commit** y explica cómo sacarla a `.env` |
| `.claude/hooks/lint-front.js` | **Después** de editar un `.js`/`.jsx` de `PetConnect.Front/petconnect-app/src/` | Corre `oxlint` solo sobre ese archivo y le pasa los avisos a Claude para que los corrija en el momento |

Los archivos de pruebas (`tests/`, `*.test.*`) y los `.md` se excluyen de la detección de claves, porque ahí es
normal tener valores de ejemplo.

### En qué nos ayuda
- Es la defensa más fuerte para el punto 14 de la guía (*“nunca subas contraseñas a GitHub”*): aunque alguien
  se equivoque, el commit no pasa.
- Los errores de estilo del Front se corrigen en el mismo paso en que se escriben, no días después.

### Cómo transforma el flujo
No tienes que hacer nada: funcionan en segundo plano. Solo los vas a notar cuando bloqueen algo; en ese caso el
mensaje dice qué encontró y cómo arreglarlo. Si algún día un hook estorba, se puede desactivar quitándolo de
`.claude/settings.json`.

---

## 5. Skills propias del proyecto

### Qué es una skill
Una skill es una **receta guardada**: instrucciones paso a paso que Claude sigue cuando la llamas con `/nombre`
(o cuando él detecta que aplica). Convierte un buen hábito en algo repetible que no depende de la memoria.

### Las seis skills creadas

#### `/levantar-proyecto [backend | web | movil | todo]`
- **Ayuda en:** sección 5 de la guía (“levanta el servidor para ver la página”).
- **Cómo funciona:** revisa qué puertos ya están ocupados (5000, 5173, 8081, 3310), avisa si MySQL está apagado,
  arranca el backend con el `.venv` de la raíz, la web con `npm run dev` y/o Expo, y termina con una tabla de
  módulo → URL → estado. Si faltan variables, compara con `.env.example` sin abrir el `.env`.
- **Transforma el flujo:** ya no hay que recordar en qué carpeta y con qué comando arranca cada parte.

#### `/nueva-funcionalidad <qué quieres construir>`
- **Ayuda en:** secciones 3, 4 y 5 (contexto, modo plan, ir por partes).
- **Cómo funciona:** 4 fases obligatorias: (1) contexto — hasta 5 preguntas concretas; (2) plan con archivos,
  partes, riesgos, y **espera tu aprobación**; (3) construir parte por parte, verificando y explicando cada una;
  (4) cierre con `/impeccable audit`, revisión de contenido y `/guardar-partida`.
- **Transforma el flujo:** pasas de “hazme X” → resultado genérico, a una conversación guiada donde ves y apruebas
  cada pedazo.

#### `/explicar [archivo | función | concepto]`
- **Ayuda en:** sección 7 (aprender mientras construyes).
- **Cómo funciona:** responde siempre con el mismo formato: una frase, una analogía, cómo funciona *en este proyecto*
  (con archivo:línea), por qué así y no de otra forma, un **ejercicio para hacerlo tú solo** y un glosario. No modifica
  archivos. Sin argumento explica el último cambio.
- **Transforma el flujo:** cada cambio se puede convertir en una mini-clase sobre tu propio código.

#### `/reportar-error [descripción]`
- **Ayuda en:** sección 9 (cuando algo falla).
- **Cómo funciona:** arma la ficha (módulo, qué hice, qué esperaba, qué pasó, error completo, desde cuándo), pide lo
  que falte en un solo mensaje, reproduce el error, sigue el flujo interfaz → `api.js` → `api.py` → `dao/` → MySQL,
  enuncia la causa **antes** de tocar código, corrige y agrega una prueba si es del backend. Trae una lista de los
  errores típicos de PetConnect (MySQL apagado, `.env` incompleto, token vencido, `10.0.2.2`, proxy de Vite).
- **Transforma el flujo:** “no funciona” se convierte en un diagnóstico ordenado y un arreglo de la causa real.

#### `/guardar-partida [mensaje]`
- **Ayuda en:** secciones 2 y 12 (“haz un commit con lo que llevamos”).
- **Cómo funciona:** muestra qué cambió, agrega archivos **por ruta** (nunca `git add -A` a ciegas), corre las
  verificaciones del módulo tocado (pruebas, lint, build), y si todo pasa hace el commit en español. El hook de
  secretos actúa como segunda revisión. **No hace push** salvo que lo pidas.
- **Transforma el flujo:** cada commit es un punto seguro: probado y sin secretos.

#### `/revision-contenido-mascotas [archivo o carpeta]`
- **Ayuda en:** sección 14 (información médica, fotos, datos de clientes).
- **Cómo funciona:** revisa los cambios buscando textos de salud animal (vacunas, dosis, enfermedades…) y los marca
  con `REVISAR-VETERINARIO`; lista imágenes nuevas y su origen/licencia y si tienen texto alternativo; revisa datos
  personales según la Ley 1581 de 2012 (logs, URLs, `@require_auth`, aviso de tratamiento de datos). Termina con una
  tabla de hallazgos y un veredicto.
- **Transforma el flujo:** antes de publicar hay un control de calidad del contenido, no solo del código.

---

## 6. Skills externas instaladas

Se descargaron de sus repositorios oficiales en GitHub (con tu autorización), se revisó su contenido y se copiaron
sin modificar a `.claude/skills/`. El commit exacto de cada una quedó en `.claude/skills/PROCEDENCIA.md`.
Al estar dentro del proyecto, **cualquiera que clone el repositorio las tiene**; no hay que instalarlas por máquina.

| Skill | Origen | Licencia | Para qué |
|---|---|---|---|
| `frontend-design` | anthropics/skills | ver `LICENSE.txt` | Se activa sola al diseñar interfaces: obliga a definir paleta, tipografía y layout propios del tema antes de codificar, y evita el “look de plantilla” |
| `impeccable` (v4.8.0) | pbakaus/impeccable | Apache 2.0 | Caja de herramientas de diseño que llamas tú |
| `deploy-to-vercel` | vercel-labs/agent-skills | MIT | Guía para publicar la web en Vercel; por defecto despliega como *preview* |
| `vercel-react-best-practices` | vercel-labs/agent-skills | MIT | Reglas de rendimiento para React (se aplican en el Front web) |
| `vercel-react-native-skills` | vercel-labs/agent-skills | MIT | Buenas prácticas de React Native / Expo (se aplican en el Móvil) |

> No se instaló `web-design-guidelines` (también de Vercel) porque descarga sus reglas de internet en cada uso y
> se solapa con `/impeccable audit`.

### Comandos más útiles de impeccable
| Comando | Qué hace |
|---|---|
| `/impeccable audit [página]` | Revisa accesibilidad, rendimiento, adaptación a celular y jerarquía visual |
| `/impeccable critique [página]` | Revisión de experiencia de usuario con puntaje |
| `/impeccable polish [página]` | Pulida final antes de entregar |
| `/impeccable adapt [página]` | Que se vea bien en celular y otros tamaños |
| `/impeccable delight [página]` | Detalles con personalidad (animaciones sutiles, huellitas…) |
| `/impeccable clarify [página]` | Mejora textos de botones, etiquetas y mensajes de error |
| `/impeccable init` | Crea `PRODUCT.md` con el contexto del producto para futuras sesiones de diseño |
| `/impeccable` (sin nada) | Muestra el menú según el estado del proyecto |

**Ojo:** algunos comandos de impeccable ejecutan su motor (`scripts/impeccable.cmd`), que la primera vez descarga
`impeccable-windows-x64.exe` desde los *releases* oficiales de GitHub y verifica su huella (checksum) antes de
usarlo. Claude te pedirá permiso antes. Si no lo autorizas, la skill sigue funcionando leyendo sus guías.
Impeccable solo instala su propio hook si tú corres `/impeccable hooks on`.

### Publicar en Vercel: advertencia importante
Vercel sirve para la **web** (`PetConnect.Front/petconnect-app` como *Root Directory*). El backend Flask y MySQL
**no** corren ahí. En desarrollo, Vite redirige `/api` a `localhost:5000`; en Vercel esa redirección no existe, así
que la página cargaría **sin datos**. Antes de publicar hay que alojar la API en otro servicio y apuntar el Front
a esa dirección. Esta advertencia quedó escrita en el `CLAUDE.md`.

### Cómo transforma el flujo
Diseñar deja de ser “ponle colores bonitos”: hay una dirección de diseño pensada (frontend-design), una revisión
objetiva (impeccable audit) y una pulida final (impeccable polish). Publicar pasa a ser un paso guiado.

---

## 7. Protección de secretos y archivos locales

Ya existía un buen `.gitignore` (ignoraba `.env`, `.venv`, `node_modules`, llaves). Se agregó:

```gitignore
# Claude Code: se comparten CLAUDE.md, .claude/settings.json, hooks y skills;
# lo personal o temporal de cada máquina NO se sube
.claude/settings.local.json
.claude/worktrees/
.claude/scheduled_tasks.lock
CLAUDE.local.md
.impeccable/config.local.json
.vercel/
```

| Archivo | Se sube a GitHub | Para qué |
|---|---|---|
| `CLAUDE.md`, `.claude/settings.json`, `.claude/hooks/`, `.claude/skills/` | Sí | Reglas y herramientas compartidas del equipo |
| `.claude/settings.local.json`, `CLAUDE.local.md` | No | Preferencias personales tuyas que no deben imponerse a otros |
| `.env` | **Nunca** | Contraseñas y claves reales (la plantilla es `.env.example`) |

En resumen, los secretos quedan protegidos en **cuatro capas**: `.gitignore` → permisos `deny` → hook
`proteger-secretos.js` → hook `revisar-commit.js`.

---

## 8. Hábitos: teclas y comandos

Esto no se puede configurar en archivos: son cosas que haces tú.

| Acción | Cómo | Cuándo usarlo |
|---|---|---|
| Modo plan | `Shift + Tab` hasta que diga *plan mode* | Antes de cualquier cambio grande; Claude solo investiga y propone |
| Detener a Claude | `Esc` | Si va por mal camino |
| Volver a un mensaje anterior | `Esc` dos veces | Para corregir lo que pediste |
| Empezar de cero | `/clear` | Al cambiar de tema (de diseño a base de datos, por ejemplo) |
| Ayuda | `/help` | — |
| Pegar capturas | `Ctrl + V` o arrastrar la imagen | Para mostrar algo que se ve mal o una referencia (“quiero algo con esta vibra”) |
| Regenerar el CLAUDE.md | `/init` | Ya no hace falta: se escribió a mano y más completo |

**Pedir cambios específicos:**
- ❌ “no me gusta, cámbialo”
- ✅ “en la página de adopción el botón *Adoptar* casi no se ve; hazlo más grande, verde, y que en celular quede fijo abajo”

**Reportar un error:** usa `/reportar-error` y pega el error **completo** (terminal o F12 → Console).

---

## 9. El nuevo flujo de trabajo

```
 1. Abres Claude en la carpeta Evidecia
        └─ Claude lee CLAUDE.md (raíz + módulo) → ya conoce el proyecto y las reglas
 2. /nueva-funcionalidad "lo que quieres"   (o Shift+Tab → modo plan)
        └─ Preguntas de contexto → plan → TÚ apruebas
 3. Claude construye UNA parte
        ├─ hook proteger-secretos: no toca .env ni quema claves
        ├─ hook lint-front: corrige avisos del Front al instante
        └─ frontend-design: diseño con identidad (si es interfaz)
 4. /levantar-proyecto → miras el resultado en el navegador / emulador
        └─ ¿Algo raro? captura + /reportar-error
 5. /explicar → entiendes lo que se hizo (y haces el ejercicio)
 6. Repetir 3–5 por cada parte
 7. /impeccable audit → /impeccable polish   (si hubo interfaz)
 8. /revision-contenido-mascotas            (si hay textos de salud, fotos o datos personales)
 9. /guardar-partida
        ├─ pruebas + lint + build
        └─ hook revisar-commit: bloquea si hay secretos
10. (Cuando toque publicar) /deploy-to-vercel → preview primero
```

**Comparación rápida**

| Antes | Ahora |
|---|---|
| Cada sesión había que re-explicar el proyecto | `CLAUDE.md` lo explica solo |
| Pedidos sueltos → resultados genéricos | Contexto → plan aprobado → partes pequeñas |
| La seguridad dependía de acordarse | Permisos + hooks la hacen cumplir |
| Commits sin verificar | Commit = pruebas pasadas + sin secretos |
| Diseño “a ojo” | Dirección de diseño + auditoría + pulida |
| Aceptar sin entender | Explicación y ejercicio después de cada cambio |
| Textos de salud sin revisar | Marcados para revisión veterinaria |

---

## 10. Inventario de archivos

**Nuevos**
```
CLAUDE.md
petconnect.Backend/CLAUDE.md
PetConnect.Front/petconnect-app/CLAUDE.md
PetConnect.Mobile/CLAUDE.md
.claude/settings.json
.claude/hooks/proteger-secretos.js
.claude/hooks/revisar-commit.js
.claude/hooks/lint-front.js
.claude/skills/PROCEDENCIA.md
.claude/skills/levantar-proyecto/SKILL.md
.claude/skills/nueva-funcionalidad/SKILL.md
.claude/skills/explicar/SKILL.md
.claude/skills/reportar-error/SKILL.md
.claude/skills/guardar-partida/SKILL.md
.claude/skills/revision-contenido-mascotas/SKILL.md
.claude/skills/frontend-design/            (externa, 2 archivos)
.claude/skills/impeccable/                 (externa, 58 archivos)
.claude/skills/deploy-to-vercel/           (externa, 1 archivo)
.claude/skills/vercel-react-best-practices/ (externa, 76 archivos)
.claude/skills/vercel-react-native-skills/  (externa, 42 archivos)
Documentacion/NUEVAS-PRACTICAS-CLAUDE-CODE.md   (este documento)
```

**Modificados**
```
.gitignore   (bloque de Claude Code, .impeccable y .vercel)
```

No se modificó **ningún** archivo de código de la aplicación (Backend, Web ni Móvil).

---

## 11. Cómo se verificó

| Qué | Resultado |
|---|---|
| Hook `proteger-secretos.js`: 14 casos (leer/editar `.env`, `.env.local`, `.pem`; `cat`/`Get-Content` de `.env`; `git add -f`; clave quemada; y casos que deben pasar: `.env.example`, `api.py`, `ls`, archivos de prueba, entrada inválida) | 14/14 correctos |
| Hook `lint-front.js`: archivo con `debugger` y variable sin usar / archivo limpio / archivo del backend | Reporta, pasa, ignora (correcto) |
| Hook `revisar-commit.js` en un repositorio de prueba con un `.env` y un `config.py` con clave | Bloqueó ambos; con solo un archivo limpio dejó pasar |
| Hook activo en la sesión real (`cat no-existe/.env`) | Bloqueado por la regla de PetConnect |
| `settings.json` válido y con los 3 hooks registrados | Correcto |
| Skills externas: archivos descargados vs. repositorio original (conteo y huella de cada archivo) | Idénticos |
| Nombre de cada skill = nombre de su carpeta | 11/11 |
| Ningún archivo de las skills queda excluido por `.gitignore` | Correcto |
| Pruebas del backend (`unittest`, 13 pruebas) antes de empezar | OK |

---

## 12. Pendientes y advertencias

1. **Nada está en un commit todavía.** Cuando revises todo, guarda partida (`/guardar-partida`).
2. Si alguna skill nueva no aparece al escribir `/`, cierra y vuelve a abrir la sesión de Claude Code.
3. **Vercel:** antes de publicar la web hay que alojar el backend en otro servicio (ver sección 6).
4. **impeccable** puede pedir permiso para descargar su motor la primera vez que lo uses.
5. Los `Dockerfile` y `docker-compose.yml` que estaban sin seguimiento en git **no se tocaron**. Ojo: el
   `docker-compose.yml` está dentro de `petconnect.Backend/` pero sus rutas (`./petconnect.Backend`,
   `./PetConnect.Front/...`) solo funcionan si se ejecuta desde la raíz del repositorio, y aún tiene secciones
   incompletas (`# ...`).
6. Los textos de salud animal que ya existen en `src/data/pets.js` y en las pantallas no se han revisado todavía;
   se puede correr `/revision-contenido-mascotas PetConnect.Front/petconnect-app/src` cuando quieras.
