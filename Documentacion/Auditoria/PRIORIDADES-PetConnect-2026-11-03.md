# Lista de prioridades — qué arreglar primero

Basada en [AUDITORIA-PetConnect-2026-11-03.md](AUDITORIA-PetConnect-2026-11-03.md). Los IDs (`A-xx`) remiten a ese
reporte; la columna **NC** a la bitácora del plan de pruebas GA9.

**Criterio de orden:** (1) lo que impide correr o evaluar el proyecto, (2) lo que un atacante puede explotar hoy,
(3) datos personales y honestidad con el usuario, (4) estabilidad y pruebas, (5) despliegue, (6) orden.
Dentro de cada fase van primero los arreglos más rápidos.

**Esfuerzo:** 🟢 < 30 min · 🟡 1–3 h · 🔴 medio día o más.

**Regla para cada ítem:** un commit por ítem, con **su prueba de regresión**, y actualizar la bitácora de NC
(estado “Cerrada el dd/mm/2026” y la evidencia). Así el repositorio cuenta la misma historia que el plan.

---

## Fase 0 — Hoy, antes que nada (10 minutos)

- [x] **0.1 Rotar `JWT_SECRET`** (incidente §5 del reporte) · 🟢 — *Hecho el 03/11/2026 (evidencia en §5 del reporte).*
  Genera uno nuevo con `python -c "import secrets; print(secrets.token_hex(32))"` y reemplaza **solo esa línea** en
  `petconnect.Backend/.env`, a mano. **No** corras `generate_keys.py` (borra el resto del archivo).
  *Listo cuando:* la API arranca y un token viejo devuelve 401 en `/api/auth/me`.

---

## Fase 1 — Que el proyecto se pueda correr y evaluar (bloqueante)

| ✔ | # | ID | NC | Qué | Esfuerzo | Listo cuando |
|---|---|---|---|---|---|---|
| [x] | 1.1 | A-01 | NC-009, NC-010 | Subir `petconnect.Backend/sql/schema.sql` (sin datos reales) con el enum de `mascotas.estado` que incluya `en_adopcion`, `CHECK` de fechas en `aplicaciones_vacuna` y `SET SESSION sql_mode='STRICT_TRANS_TABLES,...'`; documentar el orden `schema.sql → seed.py` | 🟡 | Una BD vacía se crea solo con el repo y `/api/mascotas/adopcion` devuelve las 6 mascotas |
| [x] | 1.2 | A-01 | NC-009 | Script de corrección para la BD existente (`UPDATE mascotas SET estado='en_adopcion' WHERE estado=''`) | 🟢 | Ninguna mascota queda con estado vacío — *Hecho el 03/11/2026: `sql/migraciones/2026-11-03_estado_en_adopcion.sql`, aplicada a la BD de desarrollo (6 de 6 en `en_adopcion`)* |

---

## Fase 2 — Seguridad que se puede explotar hoy

| ✔ | # | ID | NC | Qué | Esfuerzo | Prueba de regresión |
|---|---|---|---|---|---|---|
| [x] | 2.1 | A-06 | — | `s.starttls(context=ssl.create_default_context())` en `correo/servicio.py:45` | 🟢 | Prueba que verifique que `starttls` recibe un contexto con `verify_mode == CERT_REQUIRED` (con *mock*) — *Hecho el 03/11/2026: `tests/test_correo.py` (falla con el código viejo, pasa con el nuevo)* |
| [x] | 2.2 | A-03 | NC-007 | `JWT_SECRET` obligatorio (≥ 32 bytes) o la API no arranca | 🟢 | Importar sin `JWT_SECRET` lanza error — *Hecho el 03/11/2026: `tests/test_seguridad.py`, `PruebasSecretoObligatorio` (falla con el código viejo, pasa con el nuevo)* |
| [x] | 2.3 | A-08 | NC-007 | `debug` por variable de entorno (falso por defecto); `HTTPException` con su código real; 500 con mensaje genérico; validar que `email`, `code`, `password`, `name` sean texto; 503 si no hay BD | 🟡 | `/api/no-existe` → 404; `code` numérico → 400; BD caída → 503 sin detalles internos — *Hecho el 03/11/2026: `tests/test_errores.py` (falla con el código viejo, pasa con el nuevo)* |
| [x] | 2.4 | A-05 | — | `html.escape()` de `name` (y todo dato del usuario) en `correo/servicio.py` | 🟢 | El HTML generado no contiene `<a href` cuando el nombre lo trae — *Hecho el 03/11/2026: escape en `correo/servicio.py` + nombre validado en `/register` (`api.py`); `tests/test_correo.py` y `tests/test_errores.py` (fallan con el código viejo, pasan con el nuevo)* |
| [x] | 2.5 | A-04 | NC-006 | Máximo 5 intentos por OTP (luego se invalida) + `hmac.compare_digest` | 🟢 | El 6.º intento devuelve “código bloqueado” aunque sea el correcto — *Hecho el 04/11/2026: `otp/servicio.py` + `api.py` (429 “Demasiados intentos fallidos”); `tests/test_otp.py` (falla con el código viejo, pasa con el nuevo)* |
| [x] | 2.6 | A-04, A-05 | NC-006 | Flask-Limiter (versión fijada) en `login`, `login/verify`, `register`, `verify`, `utils/validar-correo` (ej. 5/min por IP) | 🟡 | La 6.ª petición en un minuto → 429 — *Hecho el 04/11/2026: Flask-Limiter 4.1.1 + `limits` 5.8.0, 5/min por IP; `tests/test_limite.py` (falla con el código viejo, pasa con el nuevo). NC-006 cerrada* |
| [x] | 2.7 | A-09 | — | No sobrescribir un registro pendiente vigente + ruta de reenvío del mismo código (junto con el botón web “Reenviar código”) | 🟢 | Segundo `/register` con el mismo correo → no cambia el hash pendiente — *Hecho el 05/11/2026: `otp/servicio.py` (`vigente`, `para_reenviar`) + `api.py` (`/register` no toca el pendiente vigente; `POST /api/auth/register/resend`: mismo código, 60 s entre correos, máx. 3 reenvíos, sin alargar el vencimiento, respuesta neutra); `tests/test_registro.py` (falla con el código viejo, pasa con el nuevo). Botón web en `RegisterModal.jsx`* |
| [x] | 2.8 | A-10 | — | Imprimir el OTP solo si `APP_ENV=desarrollo`; nunca el correo en logs de producción | 🟢 | Con `APP_ENV` distinto, la salida no contiene el código — *Hecho el 04/11/2026: `api.py` (`_es_desarrollo`, `_avisar_fallo_envio`; fuera de desarrollo, 503 y se descarta el código) + `.env.example`; `tests/test_logs.py` (falla con el código viejo, pasa con el nuevo)* |
| [x] | 2.9 | A-07 | NC-002 | `/api/mascotas/<id>` solo devuelve `en_adopcion` (404 si no); ruta privada con `@require_auth` + dueño | 🟡 | Sin token y mascota no en adopción → 404 — *Hecho el 05/11/2026: `api.py` (filtro en SQL + revisión en Python; ruta privada `GET /api/usuarios/me/mascotas/<id>`, ajena → mismo 404); `tests/test_mascotas.py` (falla con el código viejo, pasa con el nuevo) + `test_esquema.py` con MariaDB temporal. NC-002 cerrada* |

> Al cerrar 2.2 + 2.3 se cierra **NC-007** · 2.5 + 2.6 cierran **NC-006** · 2.9 cierra **NC-002**.

---

## Por actualizar

Ítems revisados pero en pausa porque su arreglo depende de algo que se va a construir primero. Cuando se retome,
se borra de aquí y se marca `[x]` en su fase.

*Ninguno por ahora.* El 2.7 (A-09) estuvo aquí del 04/11 al 05/11/2026 y quedó hecho junto con el botón web
“Reenviar código” (decisiones, evidencia y riesgos que siguen abiertos en el “Estado” de A-09 de la
[AUDITORÍA](AUDITORIA-PetConnect-2026-11-03.md)).

---

## Fase 3 — Datos personales y honestidad con el usuario

| ✔ | # | ID | NC | Qué | Esfuerzo | Listo cuando |
|---|---|---|---|---|---|---|
| [ ] | 3.1 | A-20 | NC-005 | Casilla de autorización **sin marcar** + enlace a política en web y móvil; la API rechaza sin ella; guardar fecha y versión; quitar `acepta_datos=True` por defecto | 🟡 | Registro sin casilla → 400; con casilla → `acepta_datos=1` y fecha guardada — *Parte 1 de 3 (API + BD) hecha el 05/11/2026: `api.py` (`VERSION_POLITICA_DATOS = "1.0"`, 400 sin `"acepta_datos": true`, fecha y versión en el pendiente y en el usuario), modelo y DAO, `schema.sql` + migración `2026-11-05_autorizacion_datos.sql` (aplicada por el dueño); `tests/test_registro_datos.py` y `test_esquema.py` (fallan con el código viejo, pasan con el nuevo). Borrador de la política en `Documentacion/Legal/`. Parte 2 de 3 (web) hecha el 05/11/2026: casilla sin marcar con +18 y enlace a la política en pestaña nueva, aviso corto, mensaje sin llamar a la API (`RegisterModal.jsx`), `acepta_datos` booleano (`api.js`), página `/politica-de-datos` (`PoliticaDatos.jsx`, borrador con “Por definir”) y enlace en el pie; probada por el dueño con la API real (conteo `0 \| 10 \| 0` y `1 \| 1 \| 1`). Falta la parte 3 (móvil); NC-005 se cierra con ella* |
| [ ] | 3.2 | A-21 | — | Formularios de adopción, contacto y checkout: implementar el envío **o** rotular “Demo — no se envía” y deshabilitar | 🟢 (rotular) / 🔴 (implementar) | Ningún formulario dice “enviado” si no envió nada |
| [ ] | 3.3 | A-23 | NC-009 | Web: estados de carga/vacío/error en Catálogo, Adopción, detalles y Home; `data/*.js` solo para pruebas | 🟡 | Con la API apagada, la web muestra un error, no perritos falsos |
| [ ] | 3.4 | A-22 | — | Datos reales de vacunación/esterilización/tamaño (o no mostrarlos); corregir `seed.py` (tamaño en `color`); `/revision-contenido-mascotas` | 🟡 | La ficha no contradice la descripción; textos marcados `REVISAR-VETERINARIO` |
| [ ] | 3.5 | A-20 | — (R05) | Pedir la autorización de datos a las cuentas existentes (`acepta_datos = 0`) y a quienes aceptaron una versión vieja de la política, al iniciar sesión (API + web + móvil); si no autorizan, ofrecer borrar la cuenta. **Nunca** con un `UPDATE` que la invente. Después de la parte 3 del 3.1. Surgió el 05/11/2026 | 🔴 | Una cuenta en 0 que inicia sesión ve la casilla y, al marcarla, queda con fecha y versión; sin marcarla no entra |

---

## Fase 4 — Estabilidad, calidad y pruebas

| ✔ | # | ID | NC | Qué | Esfuerzo |
|---|---|---|---|---|---|
| [ ] | 4.1 | A-17 | NC-004 | Exigir minúscula en API, web y móvil (validación en un módulo común) | 🟢 |
| [ ] | 4.2 | A-19 | NC-011 | `AND activo = TRUE` en `buscar_por_nombre` de proveedores | 🟢 |
| [ ] | 4.3 | A-31 | — | GitHub Actions: `unittest` + `npm run lint` + `npm run build` en cada push | 🟡 |
| [ ] | 4.4 | A-31 | todas | Pruebas de endpoints con el cliente de Flask (mascotas, productos, auth, errores) | 🟡 |
| [ ] | 4.5 | A-11 | NC-003 | Pool de conexiones + `try/finally` para cerrar cursores | 🟡 |
| [ ] | 4.6 | A-12 | NC-003 | OTP en tabla de la BD (hash del código, intentos, expiración) o 1 worker con hilos; limpiar vencidos y acotar `_mx_cache` | 🟡 |
| [ ] | 4.7 | A-24 | — | Web: validar sesión con `/auth/me` al iniciar y cerrar sesión ante 401 | 🟢 |
| [ ] | 4.8 | A-13 | — | Fernet: usarlo para el teléfono o quitarlo; corregir comentario `api.py:400`; `decrypt` debe fallar | 🟢 |
| [ ] | 4.9 | A-15 | — | Decidir `autocommit` y alinear código + README | 🟢 |
| [ ] | 4.10 | A-14 | — | Registro con respuesta neutra (sin 409 que revele cuentas) | 🟢 |
| [ ] | 4.11 | A-18 | — | Consola: `getpass`, sin `.strip()`, misma política que la API, autorización de datos | 🟢 |
| [ ] | 4.12 | — | NC-003 | Repetir la prueba de carga (CP-008/CP-017) tras 4.5 y 4.6 | 🟡 |
| [ ] | 4.13 | A-03 | — | Revocar sesiones: columna `usuarios.version_sesion` dentro del token y comparada en `require_auth` (sumar 1 al cerrar sesión o cambiar la contraseña); quitar el correo del token (se puede leer); si se guardan ids de sesión, solo su hash SHA-256. **Requiere 4.5.** No reemplaza 2.2 | 🟡 |
| [ ] | 4.14 | A-41 | — | `tests/test_seguridad.py` importa `api.py`, que carga el `.env` real con `load_dotenv()` (no imprime nada, pero choca con la regla): desactivarlo como en `tests/test_correo.py` | 🟢 |
| [ ] | 4.15 | — | — | Mover el SQL de productos y mascotas de `api.py` a `dao/` (regla de `petconnect.Backend/CLAUDE.md`). Antes, que los DAO **propaguen** los errores de la BD (hoy los imprimen y devuelven `None`/`[]`), o el 503 del 2.3 se volvería 404 o lista vacía. Hacerlo junto con 4.5 (pool y `try/finally`). Surgió en el 2.9 | 🟡 |

---

## Fase 5 — Despliegue

| ✔ | # | ID | Qué | Esfuerzo |
|---|---|---|---|---|
| [ ] | 5.1 | A-30 | `.dockerignore` en cada módulo (excluir `.env`, `node_modules`, `.venv`, `__pycache__`, `dist`) **antes** de construir cualquier imagen | 🟢 |
| [ ] | 5.2 | A-30 | `docker-compose.yml` en la raíz: BD con `schema.sql`, secretos por `env_file`, API con Gunicorn en `0.0.0.0`, web compilada (no `npm run dev`) | 🔴 |
| [ ] | 5.3 | A-27 | Móvil: `EXPO_PUBLIC_API_URL` y HTTPS; `expo-secure-store` para el token (A-28) | 🟡 |
| [ ] | 5.4 | A-29 | `npm audit fix` en la web; planear actualización de Expo; `pip-audit` en CI | 🟡 |
| [ ] | 5.5 | — | Antes de Vercel: la API debe estar alojada aparte (ver `CLAUDE.md`, “Sobre publicar en Vercel”) | — |

---

## Fase 6 — Orden y documentación

- [ ] **6.1** README: MariaDB 10.4, `autocommit`, versión del conector y cómo levantar API, web y móvil (A-32) · 🟡
- [ ] **6.2** Plan GA9: `unittest` vs `pytest`/`.env.test` (A-33); actualizar la bitácora con cada NC cerrada · 🟢
- [ ] **6.3** `generate_keys.py` no debe sobrescribir un `.env` existente (A-16) · 🟢
- [ ] **6.4** `addToCartToast.js`: `textContent` en lugar de `innerHTML` (A-25) · 🟢
- [ ] **6.5** Quitar la LICENSE de Expo del móvil o poner la propia (A-34) · 🟢
- [ ] **6.6** Una sola colección de Postman, sin `postman/postman/` (A-35) · 🟢
- [ ] **6.7** Rutas genéricas en `EJECUCION.md` (A-36) · 🟢
- [ ] **6.8** `.gitignore`: agregar `~$*` (A-38); borrar `.github/modernize/` local (A-39) · 🟢
- [ ] **6.9** Hooks de Claude: corregir falsos positivos (A-40) y regla de scripts que importan la API (A-41) · 🟢
- [ ] **6.10** Renombrar el repositorio en GitHub sin acentos rotos (A-37) · 🟢
- [ ] **6.11** Decidir qué hacer con los Dockerfile sin commit (se rehacen en 5.2) · 🟢

---

## Si solo hay una semana

1. **Fase 0** (rotar `JWT_SECRET`)
2. **1.1** esquema SQL + enum + modo estricto
3. **2.1 → 2.5** (todos 🟢: TLS, JWT obligatorio, errores, escape, intentos OTP)
4. **2.9** NC-002
5. **2.6 – 2.8** limitador, registro pisado, logs
6. **3.1** autorización de datos y **3.2** rotular formularios demo
7. **3.3** la web muestra errores
8. **4.1, 4.2, 4.3** (NC-004, NC-011 y CI: rápidos y suman mucho ante el instructor)

Con eso quedan cerradas **NC-002, NC-004, NC-005, NC-006, NC-007, NC-009, NC-010 y NC-011**, y hay CI.

---

## Prompt para empezar a corregir

Pega esto en Claude Code, dentro de la carpeta del proyecto. Sirve para **cada sesión**: siempre toma el siguiente
ítem pendiente, en orden de prioridad (fase 0 → 6), y lo tacha con `[x]` al terminar. Un ítem por vez, no "todo de
una": así cada commit tiene su prueba y, si algo falla, se sabe qué lo causó.

*Versión del 05/11/2026, actualizada al terminar la parte 2 del 3.1 (web): estado conocido al día y contexto de
la parte 3 (móvil) del 3.1, que cierra NC-005. Salta los ítems de “Por actualizar” y pide actualizar este prompt al terminar cada
ítem o cada parte.*

```text
Vamos a seguir corrigiendo PetConnect con la auditoría del 3/11/2026.

Lee primero:
- Documentacion/Auditoria/PRIORIDADES-PetConnect-2026-11-03.md (lista con casillas
  y "Próximo ítem")
- Documentacion/Auditoria/AUDITORIA-PetConnect-2026-11-03.md (detalle del A-xx)
- Documentacion/GA9-220501096-AA1-EV02-PetConnect.md (bitácora de NC)
- Documentacion/Legal/POLITICA-TRATAMIENTO-DATOS-v1.0-BORRADOR.md (borrador de la
  política: Parte B = textos de la casilla, el aviso y los mensajes; Parte C =
  especificación; Parte D = decisiones pendientes)
- git log --oneline -12 (qué se hizo en sesiones anteriores; revisa con
  git status -sb si hay commits sin push; el 05/11/2026 se subió todo hasta el
  botón web del 2.7, 6e0bbc5; los commits de las partes 1 y 2 del 3.1 quedaron
  sin push)

Estado conocido (5/11/2026; si el git log muestra más ítems hechos, manda el git log):
- Hechos: 0.1, 1.1, 1.2 y toda la fase 2 (2.1 a 2.9; ver git log). Fase 3: el
  3.1 va por partes: la parte 1 (API + BD) y la parte 2 (web) están hechas;
  sigue la parte 3 (móvil), que cierra NC-005.
- "Por actualizar" está vacía.
- Pruebas: 125 (110 OK + 15 omitidas que necesitan MariaDB).
- Autorización de datos (3.1 parte 1, NC-005 en corrección): api.py tiene
  VERSION_POLITICA_DATOS = "1.0" y _MENSAJE_SIN_AUTORIZACION. /register exige
  "acepta_datos": true (solo el booleano JSON, con `is True`) justo después de
  revisar los campos obligatorios, antes del nombre, el DNS, la BD, la revisión
  del pendiente vigente (2.7) y el correo; si no, 400 "Debes autorizar el
  tratamiento de tus datos personales para registrarte". El pendiente guarda
  fecha_autorizacion_datos (datetime de /register, sin microsegundos) y
  version_politica_datos; /verify las pasa al Usuario y, si faltan, responde ese
  400 y descarta el pendiente (doble barrera). Usuario(acepta_datos=False por
  defecto, fecha_autorizacion_datos, version_politica_datos); el INSERT de
  UsuarioDAO las escribe (los SELECT no las leen). BD: acepta_datos NOT NULL
  DEFAULT 0, regla chk_autorizacion_datos; migración
  sql/migraciones/2026-11-05_autorizacion_datos.sql YA aplicada a la BD del
  dueño (10 usuarios en 0, sin fecha). Toda prueba que se registre debe mandar
  "acepta_datos": true. Pruebas: tests/test_registro_datos.py y test_esquema.py
  (PruebasMigracionDatosSinBD / PruebasMigracionDatosEnBD).
- Web (3.1 parte 2, hecha el 05/11/2026): RegisterModal.jsx tiene FORM_VACIO
  (aceptaDatos: false), la casilla id="reg-acepta" sin marcar antes del botón
  ("Soy mayor de 18 años, he leído la Política de tratamiento de datos
  personales y autorizo...", D.4 decidido: la edad va en la misma casilla), el
  enlace a /politica-de-datos con target="_blank" y el aviso corto B.2 debajo
  (aria-describedby). Sin marcar: MENSAJE_SIN_AUTORIZACION en el cuadro rojo
  (role="alert"), foco en la casilla y NINGUNA llamada a la API. api.js:
  registerUser(name, email, password, aceptaDatos) manda
  acepta_datos: aceptaDatos === true. Página src/pages/PoliticaDatos.jsx (copia
  en JSX de la Parte A del borrador; VERSION_POLITICA = "1.0"; los datos de D.1,
  D.3 y D.5 salen como "Por definir"; si cambias el texto, cambia también el .md
  y sube la versión aquí y en la API). Ruta en App.jsx y enlace en Footer.jsx.
  Probada por el dueño con la API real: conteo 0 | 10 | 0 y 1 | 1 | 1.
- La API NO tiene recargador: después de cambiar el backend hay que reiniciarla
  (Ctrl+C y ..\.venv\Scripts\python api.py desde petconnect.Backend). Para saber
  si corre el código nuevo: CreationDate del proceso (Get-CimInstance
  Win32_Process, CommandLine con api.py) más reciente que LastWriteTime de
  api.py, o un POST /api/auth/register sin acepta_datos que responda 400
  "Debes autorizar...".
- Pendientes que dejó el 3.1 (fuera de NC-005): el 3.5 (pedir la autorización a
  las cuentas existentes y a quienes aceptaron una versión vieja, al iniciar
  sesión; nunca con un UPDATE que la invente); botón "borrar mi cuenta"
  (supresión, C.8) y llenar las decisiones D.1 a D.3, D.5 y D.6 de la política
  (no bloquean el cierre técnico, sí la publicación).
- Registro (2.7, A-09): AlmacenOTP tiene vigente(clave) (borra el pendiente si
  venció) y para_reenviar(clave) (60 s entre correos, máximo 3 reenvíos, no
  alarga los 10 minutos, no reenvía un código con 5 fallos). /register NO toca
  un pendiente vigente (vale la primera contraseña) y responde igual que
  siempre. POST /api/auth/register/resend reenvía el MISMO código, con respuesta
  neutra haya o no pendiente; si falla el correo, 503 sin borrar el pendiente.
  Web: RegisterModal.jsx tiene el botón "Reenviar código" (cuenta regresiva,
  aria-live, aria-disabled) y "Cambiar correo"; api.js tiene resendRegisterCode.
  Prueba modelo para registro: tests/test_registro.py (reloj de otp/servicio.py
  simulado con mock.patch.object(servicio, "time", ...)).
- Pendientes que dejó el 2.7 (sin ítem todavía, preguntar al dueño): botón igual
  en LoginModal.jsx y en el móvil; que /verify vuelva a pedir la contraseña
  (otra persona puede borrar el pendiente con 6 códigos falsos y registrarse);
  la caja del código sin aria-label/autoComplete="one-time-code" y los modales
  sin role="dialog" (/impeccable audit, 17/20); el código vencido no se avisa
  (registrarse otra vez con un código vigente no manda otro y los 10 minutos
  siguen desde el primero; tras vencer, "Reenviar código" no envía nada y la
  web no dice que venció; ver A-09 de la AUDITORÍA).
- NC-007 solo espera decrypt() (4.8). NC-006 cerrada el 04/11/2026. NC-002
  cerrada el 05/11/2026.
- Mascotas (2.9): GET /api/mascotas/<id> pública solo devuelve en_adopcion (SQL
  + revisión en Python); si no, 404 "Mascota no encontrada". Ruta privada
  GET /api/usuarios/me/mascotas/<id> con @require_auth (ajena → mismo 404). En
  api.py: _consultar_mascota(sql, params) y _mascota_no_encontrada(). El SQL de
  productos y mascotas sigue en api.py: moverlo a dao/ es el 4.15 (MascotaDAO
  se traga los errores de la BD; hacerlo con el pool, 4.5).
- tests/test_mascotas.py es el modelo para rutas con @require_auth: tokens con
  api.generate_token(id, correo_inventado) dentro de la prueba (nunca impresos)
  y una BD simulada cuyo cursor devuelve la fila que la prueba elige.
- Pruebas con MariaDB (PETCONNECT_PRUEBA_BD=1) las corre el DUEÑO, porque usan
  las credenciales del .env. El MySQL de XAMPP es el servicio de Windows "mysql"
  (puerto 3310); si está apagado da error 2002 (10061) y se enciende con
  Start-Service mysql en una PowerShell de administrador. Los comandos van desde
  petconnect.Backend (..\.venv\Scripts\python solo funciona ahí). Para que el
  resultado quepa en una captura, correr solo las clases que tocan el ítem (ej.
  tests.test_esquema.PruebasEsquemaEnBD tests.test_esquema.PruebasMigracionDatosEnBD).
  Respaldo: C:\Users\goku8\Respaldos\.
- OTP (2.5): AlmacenOTP cuenta fallos (MAX_INTENTOS = 5); el 6.º intento borra el
  código y devuelve "bloqueado"; las rutas de verificación responden 429
  "Demasiados intentos fallidos...". Compara con hmac.compare_digest sobre bytes.
  Sin threading.Lock (decisión: lo más simple). AlmacenOTP tiene crear(),
  verificar(), descartar() y tiene_pendiente().
- Limitador (2.6): api.limiter (Flask-Limiter 4.1.1), LIMITE_AUTH = "5 per minute"
  por IP en las 5 rutas de auth; 429 "Demasiadas peticiones. Espera un minuto...".
  _importar_api() lo deja APAGADO (limiter.enabled = False); una prueba que lo
  necesite lo enciende en setUp y lo reinicia (modelo: tests/test_limite.py).
- Correo que falla (2.8): APP_ENV (nueva, vacía en .env.example) es aparte de
  FLASK_DEBUG; _es_desarrollo() solo acepta "desarrollo" (.strip().lower()).
  _avisar_fallo_envio(e, codigo=None) registra con app.logger.warning solo
  "Fallo de envio de correo en <ruta>: <tipo>" (nunca el correo ni str(e)); en
  desarrollo imprime SOLO el código y devuelve True. Fuera de desarrollo /login y
  /register descartan el pendiente y responden 503 "No pudimos enviar el código a
  tu correo..."; la bienvenida de /verify sigue en 201. La reutilizará la ruta de
  reenvío del 2.7.
- api.py ya tiene manejadores de error: 404/405 reales, 500 genérico con id_error
  (_registrar_error: registra con app.logger tipo y pila, sin el mensaje), 503 si
  no hay BD (BDNoDisponible), y _cuerpo_json()/_texto() para validar que los
  campos sean texto. Reutilízalos. /register valida el nombre con
  _validar_nombre() antes del DNS y la BD (2.4). _modo_debug() lee FLASK_DEBUG.
  require_auth deja request.current_user_id (int) y responde 401 sin token.
- tests/test_errores.py es el modelo para probar rutas: test_client, BD simulada
  con mock, sin enviar correos (mock de api.enviar_codigo y, si hace falta,
  de api._validar_correo para no consultar el DNS). Su función _importar_api()
  importa api.py sin cargar el .env real (tests/test_otp.py y tests/test_logs.py
  la reutilizan con from test_errores import _importar_api; por eso se corren con
  discover -s tests, no como tests.test_x). tests/test_logs.py es el modelo para
  simular una BD "encendida" (obtener_conexion -> MagicMock) con UsuarioDAO falso.
  tests/test_esquema.py tiene las pruebas con MariaDB real (PETCONNECT_PRUEBA_BD=1,
  solo bases temporales). Pendiente 4.14 para test_seguridad.py.
- Las rutas de prueba se registran al importar el archivo, no en setUpClass
  (Flask prohíbe registrar rutas después de la primera petición).
- La web (src/services/api.js:20) y el móvil (src/services/api.js:34) muestran
  data.error con cualquier respuesta que no sea ok.

Contexto del próximo paso (3.1 parte 3 de 3: MÓVIL, A-20, NC-005). Solo
PetConnect.Mobile; no tocar backend ni web (regla 3). Si el plan ya fue
aprobado en la sesión anterior, revisa si hay cambios sin commit en
PetConnect.Mobile antes de tocar nada.
- Hoy el registro del móvil recibe 400 "Debes autorizar el tratamiento de tus
  datos personales para registrarte": la API ya lo exige (parte 1) y el móvil
  no manda la casilla.
- Móvil: src/screens/RegisterScreen.js (estados ~línea 15, handleRegister ~23
  con registerUser en la 27, formulario ~71, botón "Registrarme" ~94; hoy no
  tiene casilla ni enlace) y src/services/api.js:61 registerUser(name, email,
  password), que debe mandar acepta_datos: aceptaDatos === true (igual que la
  web). No hay componente de casilla ni expo-web-browser instalados: la casilla
  se arma con Pressable + accessibilityRole="checkbox" +
  accessibilityState={{ checked }} (sin librería nueva) y la política se abre
  con Linking.openURL de react-native en el navegador del celular. Ojo: en el
  emulador la web está en http://10.0.2.2:5173/politica-de-datos (misma lógica
  que HOST en api.js); solo vale en desarrollo (A-27, 5.3).
- Qué hacer (Parte B y C del borrador): los mismos textos B.1 (con +18), B.2 y
  B.3 de la web; casilla SIN marcar, antes del botón; sin marcar → mensaje B.3
  sin llamar a la API; área táctil de 44 px; leer bien en TalkBack.
- Prueba: el móvil no tiene pruebas automáticas ni linter (package.json solo
  tiene start, android, ios y web); revisión en el emulador Android. El dueño prueba
  con la API real: sin marcar → mensaje sin petición; el enlace abre la
  política; marcada → código → cuenta creada; conteo → la fila de 1 sube a 2.
  Usar vercel-react-native-skills y /impeccable audit al final.
- Al terminar: NC-005 "Cerrada el dd/mm/2026" en GA9 (fila ~708, H-08 ~167,
  CP-001 ~672), "Estado" de A-20 en la AUDITORÍA y [x] en el 3.1.

Luego:
1. Toma el PRIMER ítem sin marcar ([ ]) en orden de fases, saltando los que
   estén en la sección "Por actualizar" (hoy ninguno). Si el ítem va por partes,
   sigue con la parte pendiente. Si dos seguidos son 🟢 y tocan el mismo
   archivo, puedes agruparlos (dímelo).
2. Antes de tocar código explícame en lenguaje sencillo qué está mal, el riesgo
   y tu plan (archivos, cambio, prueba de regresión), con opciones y pros/contras
   si hay varias. Si hay cambios sin commit relacionados, revísalos primero.
   Espera mi aprobación.
3. Implementa solo ese ítem respetando CLAUDE.md (secretos, SQL parametrizado,
   español, Ley 1581). No leas ni imprimas el .env. Si necesita una dependencia
   nueva, pídeme permiso y fija la versión en requirements.txt.
4. Agrega la prueba de regresión y corre:
   - Backend: ../.venv/Scripts/python -m unittest discover -s tests -v
     (deben seguir pasando todas las anteriores más las nuevas)
   - Si toca la BD: también con PETCONNECT_PRUEBA_BD=1 (solo bases temporales)
   - Web (si cambió): npm run lint y luego npm run build
   Comprueba que la prueba nueva FALLA con el código viejo (contraprueba con
   git stash solo del archivo corregido) y dime cuántas fallan y cuáles pasan
   a propósito.
5. Si hay que tocar mi BD real, arrancar la API con mi .env o algo con
   contraseña, NO lo hagas tú: dame los comandos para Windows PowerShell 5.1
   (sin &&, un comando por bloque, indicando desde qué carpeta; MySQL está en
   C:\xampp\mysql\bin\), con respaldo previo fuera del repo, y espera mi captura.
6. Actualiza la fila de la NC en la bitácora GA9 (fecha y evidencia, incluida la
   contraprueba) y el "Estado" bajo el A-xx en la AUDITORÍA. Si con este ítem se
   completa una NC, cambia su estado a "Cerrada el dd/mm/2026".
7. Marca [x] en PRIORIDADES (si el ítem va por partes, solo al terminar la
   última; mientras tanto anota el avance en su fila), actualiza "Próximo ítem"
   y el prompt de PRIORIDADES (estado conocido + contexto del siguiente paso).
8. Commit con /guardar-partida: un commit por ítem, agregando archivos por ruta.
   No incluyas .gitignore, CLAUDE.md ni archivos sin seguimiento ajenos al ítem.
   No hagas push.
9. Explícame qué cambió (estilo /explicar), cómo verlo funcionando y déjame el
   prompt listo para el siguiente ítem, pegado completo en el chat.
```

**Próximo ítem: 3.1, parte 3 de 3 (móvil)** (A-20, NC-005). Las partes 1 (API + BD) y 2 (web) quedaron hechas el
05/11/2026; la web se probó con la API real. Hasta terminar la parte 3, el registro del móvil responde 400 porque
todavía no manda la casilla. Con la parte 3 se cierra NC-005. Después: 3.2, y el 3.5 (autorización de las cuentas
existentes) cuando toque.
