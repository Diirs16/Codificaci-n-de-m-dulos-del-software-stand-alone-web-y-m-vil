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
| [x] | 3.1 | A-20 | NC-005 | Casilla de autorización **sin marcar** + enlace a política en web y móvil; la API rechaza sin ella; guardar fecha y versión; quitar `acepta_datos=True` por defecto | 🟡 | Registro sin casilla → 400; con casilla → `acepta_datos=1` y fecha guardada — *Parte 1 de 3 (API + BD) hecha el 05/11/2026: `api.py` (`VERSION_POLITICA_DATOS = "1.0"`, 400 sin `"acepta_datos": true`, fecha y versión en el pendiente y en el usuario), modelo y DAO, `schema.sql` + migración `2026-11-05_autorizacion_datos.sql` (aplicada por el dueño); `tests/test_registro_datos.py` y `test_esquema.py` (fallan con el código viejo, pasan con el nuevo). Borrador de la política en `Documentacion/Legal/`. Parte 2 de 3 (web) hecha el 05/11/2026: casilla sin marcar con +18 y enlace a la política en pestaña nueva, aviso corto, mensaje sin llamar a la API (`RegisterModal.jsx`), `acepta_datos` booleano (`api.js`), página `/politica-de-datos` (`PoliticaDatos.jsx`, borrador con “Por definir”) y enlace en el pie; probada por el dueño con la API real (conteo `0 \| 10 \| 0` y `1 \| 1 \| 1`). Parte 3 de 3 (móvil) hecha el 06/11/2026: casilla sin marcar con +18, enlace aparte “Leer los términos y condiciones que aceptas: Política…” (`Linking.openURL`), aviso corto y mensaje sin llamar a la API (`RegisterScreen.js`), `acepta_datos` booleano y `POLITICA_URL` (`api.js`); `npx expo export --platform web` OK y revisión a 375 px con la API simulada; probada por el dueño en el emulador con la API real (conteo `0 \| 5 \| 0` y `1 \| 1 \| 1`). NC-005 cerrada el 06/11/2026* |
| [x] | 3.2 | A-21 | — | Formularios de adopción, contacto y checkout: implementar el envío **o** rotular “Demo — no se envía” y deshabilitar | 🟢 (rotular) / 🔴 (implementar) | Ningún formulario dice “enviado” si no envió nada — *Hecho el 06/11/2026 (camino “rotular”, solo web): componente `AvisoDemo.jsx`; en `PetDetail.jsx`, `Contact.jsx` y `Checkout.jsx` aviso “Demo — …”, campos en `<fieldset disabled>`, botón deshabilitado y sin pantallas de “enviado”; el checkout ya no vacía el carrito; `Confirmation.jsx` y la ruta `/confirmacion` borradas; Contacto muestra el correo de atención y Armenia (D.1) en lugar de datos inventados. Lint 0 errores, build OK, 375 px sin desbordes y 0 `POST` a `/api`; búsqueda de textos engañosos: 7 con el código viejo, 0 con el nuevo; `/impeccable audit` 16/20. El envío real es el 3.6* |
| [x] | 3.3 | A-23 | NC-009 | Web: estados de carga/vacío/error en Catálogo, Adopción, detalles y Home; `data/*.js` solo para pruebas | 🟡 | Con la API apagada, la web muestra un error, no perritos falsos — *Hecho el 06/11/2026 (solo web): `api.js` (cada error trae `status`; 0 sin conexión), componente `EstadoCarga.jsx` (cargando / error con “Reintentar” / vacío), `Adoption.jsx`, `Catalog.jsx`, `PetDetail.jsx` (404 → “no encontrada”, otro fallo → error; nunca la ficha falsa), `ProductDetail.jsx` y `Home.jsx` (“Productos destacados” de la API en lugar de ofertas/nuevos inventados); `src/data/pets.js` y `products.js` borrados. Pruebas nuevas `npm test` (`node --test`, sin dependencias): `tests/api.test.js` y `tests/sin-datos-falsos.test.js` (fallan 5 de 6 con el código viejo, pasan 6 de 6 con el nuevo). Lint 0 errores, build OK, 375 px con la API apagada: error en las 5 páginas (contraprueba: el código viejo mostraba las 6 mascotas falsas); `/impeccable audit` 17/20. Probado por el dueño con la API real: 6 mascotas de la BD, `/adopcion/99999` → “Mascota no encontrada”, Home con productos reales. NC-009 cerrada* |
| [x] | 3.4 | A-22 | — | Datos reales de vacunación/esterilización/tamaño (o no mostrarlos); corregir `seed.py` (tamaño en `color`); `/revision-contenido-mascotas` | 🟡 | La ficha no contradice la descripción; textos marcados `REVISAR-VETERINARIO` — *Opción (a) del dueño: no mostrar vacunación, esterilización ni tamaño. Parte 1 de 3 (backend) hecha el 06/11/2026: `api.py` ya no inventa `vaccinated`/`sterilized`/`size`; `seed.py` con `color` en `None` y 10 textos `# REVISAR-VETERINARIO`; migración `2026-11-06_mascotas_ejemplo.sql` (color con tamaño → `NULL`, Nala 6 → 0; reconoce las 6 de ejemplo por nombre + especie + `en_adopcion`), aplicada por el dueño; `tests/test_ficha_mascota.py` y `test_esquema.py` (fallan con el código viejo, pasan con el nuevo). Parte 2 de 3 (web) hecha el 06/11/2026: `src/utils/mascota.js` (edad “2 años” / “Menos de 1 año”, sexo “Hembra”/“Macho”, línea sin datos desconocidos); `PetDetail.jsx` sin el bloque ✓/✗ ni la talla y `Adoption.jsx` sin la talla; `tests/mascota.test.js` y `tests/sin-salud-inventada.test.js` (con las páginas viejas falla 1 de 12, que nombra las dos páginas; pasan 12 de 12 con las nuevas); lint 0 errores, build OK, 375 px con la API real; `/impeccable audit` 16/20. Parte 3 de 3 (móvil) hecha el 06/11/2026: `src/utils/mascota.js` (copia de la web); `PetDetailScreen.js` sin las insignias Vacunada/Esterilizada, sin `Badge` y sin “Talla undefined”; `AdoptionScreen.js` con la misma línea “Raza · Edad · Sexo”; fotos con `role="img"` y `aria-label`; `tests/mascota.test.mjs` y `tests/sin-salud-inventada.test.mjs` (`npm test` del móvil, `node --test`; con las pantallas viejas fallan 2 de 7, pasan 7 de 7 con las nuevas); `npx expo export --platform web` OK y 375 px con la API simulada; probado por el dueño en el emulador con la API real (6 mascotas, Nala “Menos de 1 año”); `/impeccable audit` 14/20. A-22 resuelto. Falta la validación veterinaria de los textos marcados antes de publicar* |
| [ ] | 3.5 | A-20 | — (R05) | Pedir la autorización de datos a las cuentas existentes (`acepta_datos = 0`) y a quienes aceptaron una versión vieja de la política, al iniciar sesión (API + web + móvil); si no autorizan, ofrecer borrar la cuenta. **Nunca** con un `UPDATE` que la invente. Después de la parte 3 del 3.1. Surgió el 05/11/2026 | 🔴 | Una cuenta en 0 que inicia sesión ve la casilla y, al marcarla, queda con fecha y versión; sin marcarla no entra — *Opción (a) del dueño; si no autorizan, enlace al correo de atención para borrar la cuenta (proceso manual, C.8). Parte 1 de 3 (API + DAO) hecha el 06/11/2026: `api.py` (`_autorizacion_vigente`: `acepta_datos` = 1 y versión actual; `/login` responde 403 `"requiere_autorizacion": true` tras la contraseña y sin enviar código; con `"acepta_datos": true` la fecha y la versión van en el pendiente; `/login/verify` las escribe solo con el código correcto y sin prueba válida responde 403 sin token), `dao/usuario_dao.py` (los `SELECT` leen fecha y versión; `registrar_autorizacion`, `UPDATE` parametrizado de las tres columnas); `tests/test_login_datos.py` (12) y `test_esquema.py` (1 con MariaDB); con el `api.py` anterior fallan 5 de 9, con el DAO anterior 3 de 3. Parte 2 de 3 (web) hecha el 06/11/2026: componente `CasillaAutorizacion.jsx` (texto B.1 + B.2 en un solo lugar, lo usan el registro y el inicio de sesión); `LoginModal.jsx` muestra el paso “Autoriza el uso de tus datos” con el 403 (casilla sin marcar, “Autorizar y continuar”, “Cancelar” y `mailto` B.3 para pedir borrar la cuenta; sin marcar, mensaje B.3 y 0 peticiones; un 403 en `/login/verify` vuelve a la casilla); `api.js` (`acepta_datos` solo con `true`, error con `requiereAutorizacion`) y `AuthContext.jsx`; `tests/api.test.js` (+5) y `tests/casilla-autorizacion.test.js` (3): con el código anterior fallan 7 de 8; `npm test` 20/20, lint y build OK, 375 px con la API simulada; `/impeccable audit` 16/20. Arreglo de la auditoría del 06/11/2026: “Cancelar” desactivado mientras se envía (si no, al llegar la respuesta salía igual la pantalla del código). Probada por el dueño con la API real el 06/11/2026: la cuenta 18 (`acepta_datos = 0`) inició sesión en la web, vio “Autoriza el uso de tus datos”, marcó la casilla, escribió el código y quedó con `acepta_datos = 1` y fecha; el caso “sin marcar” quedó probado con las pruebas automáticas y la API simulada. Falta el móvil (parte 3)* |
| [ ] | 3.6 | A-21 | — | Envío real de la solicitud de adopción y del mensaje de contacto: endpoint con `@require_auth` (y limitador), tabla nueva (migración + `schema.sql`), consentimiento para esa finalidad y **política v1.1** (Parte C, “Fuera del 3.1”; subir `VERSION_POLITICA_DATOS`), web y, si se decide, móvil. Quitar el `AvisoDemo` solo del formulario que ya envíe. El checkout real va aparte (A-26). Surgió en el 3.2 (06/11/2026) | 🔴 | Una solicitud enviada queda en la BD con el usuario, la fecha y la versión de la política, y la web dice “enviada” solo si la API respondió 201 |

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

*Versión del 06/11/2026, actualizada al terminar el 3.5 parte 2 de 3 (web: el inicio de sesión muestra la casilla
cuando la API la pide): estado conocido al día y contexto de la parte 3 (móvil). Sin push hasta terminar toda la Fase 3. Salta los ítems de “Por actualizar” y pide actualizar este prompt al terminar cada ítem o cada parte.*

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
- git log --oneline -12 y git status -sb (qué se hizo en sesiones anteriores;
  el 05/11/2026 se subió todo hasta el botón web del 2.7, 6e0bbc5; desde ahí
  todo queda en local: 3.1 (31f005c, fa1dda3, 6f0bdc9), 0a5e1dd, b8d5ec2,
  f40af07, 57e05c4 (3.2), 6c9c0bf (3.3), 47ae96d, b398126 y f441696 (3.4,
  3 partes), 03925c5 (3.5 parte 1, API + DAO) y el commit del 3.5 parte 2
  (web).
  REGLA DEL DUEÑO (06/11/2026): NO
  se hace push hasta terminar TODA la Fase 3 (3.1 a 3.6). No preguntes por el
  push antes; al marcar el último ítem de la fase, recuérdalo y pregunta)

Estado conocido (6/11/2026; si el git log muestra más ítems hechos, manda el git log):
- Hechos: 0.1, 1.1, 1.2, toda la fase 2 (2.1 a 2.9), el 3.1 (3 partes: API +
  BD, web y móvil; ver git log), el 3.2, el 3.3 y el 3.4 (3 partes: backend,
  web y móvil; A-22 resuelto). NC-005 y NC-009 cerradas el 06/11/2026.
  El 3.5 va por partes: parte 1 (API + DAO) y parte 2 (web) hechas el
  06/11/2026; sigue la parte 3 (móvil). La parte 2 ya la probó el dueño con
  la API real (cuenta 18; ver "Avance de esa prueba").
- Web sin datos falsos (3.3, A-23, hecho el 06/11/2026, solo web):
  src/data/pets.js y products.js BORRADOS; la prueba
  tests/sin-datos-falsos.test.js falla si algo de src/ vuelve a importar data/.
  api.js: cada error trae status (código HTTP; 0 si el servidor no respondió;
  502 = proxy de Vite con la API apagada). Componente src/components/
  EstadoCarga.jsx (props tipo "cargando" | "error" | "vacio", titulo,
  children, onReintentar, accion, encabezado; role="status" o "alert"; con
  encabezado="h1" en las fichas). Patrón en cada página: estado
  "cargando" | "error" | "listo", intento (sumar 1 = reintentar) y la bandera
  vigente en el useEffect. Adoption.jsx y Catalog.jsx empiezan vacías; con 0
  resultados muestran el estado vacío; las categorías salen de la API.
  PetDetail.jsx y ProductDetail.jsx: 404 → "no encontrada", otro fallo → error
  con "Reintentar" y "Volver". Home.jsx: "Productos destacados" = los 4
  primeros productos de la API (se quitaron "Ofertas" y "Nuevos": la BD no
  tiene descuento ni "nuevo"). Quedan sin uso las etiquetas Nuevo/-x%/oldPrice
  de ProductCard.jsx y ProductDetail.jsx, y Home sigue prometiendo "Envío en
  24-48 horas" y "garantía de devolución" (pendiente sin ítem: preguntar al
  dueño). /impeccable audit 17/20 (pulido opcional: el foco se va al body
  cuando "Reintentar" desaparece). Probado por el dueño con la API real el
  06/11/2026 (6 mascotas, 404 y productos reales). OJO: el pie (Footer.jsx)
  todavía muestra contacto inventado (info@petconnect.com, +57 300 123 4567,
  Bogotá) que contradice la D.1 (correo de atención y Armenia): pendiente sin
  ítem, preguntar al dueño.
- Pruebas web: npm test (node --test, sin dependencias; tests/api.test.js,
  tests/sin-datos-falsos.test.js, tests/mascota.test.js,
  tests/sin-salud-inventada.test.js y tests/casilla-autorizacion.test.js,
  20 pruebas). La web para revisar con la API
  apagada: el proxy de Vite responde 502 sin cuerpo.
- Pruebas móvil (desde el 3.4 parte 3): npm test en PetConnect.Mobile
  ("node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON --test", sin
  dependencias; 7 pruebas en tests/*.test.mjs). Las pruebas son .mjs y el
  package.json NO tiene "type": "module" (cambiarlo puede romper Expo/Metro);
  Node 24 importa los .js de src/ con import y la bandera calla el aviso.
  Solo sirven para código JS puro (src/utils/) o para leer el texto de las
  pantallas: Node no entiende JSX.
- Formularios demo (3.2, A-21, hecho el 06/11/2026, solo web): componente
  src/components/AvisoDemo.jsx (props id, titulo, children, invitacion; recuadro
  ámbar role="note"; con invitacion agrega el mailto al correo de atención).
  PetDetail.jsx, Contact.jsx y Checkout.jsx: aviso "Demo — ...", campos en
  <fieldset disabled aria-describedby>, botón submit deshabilitado y
  onSubmit={(e) => e.preventDefault()}; sin estado del formulario ni pantallas
  de "enviado". Checkout ya no vacía el carrito. Confirmation.jsx y la ruta
  /confirmacion se BORRARON (App.jsx). Contact.jsx muestra el correo de
  atención (mailto) y Armenia, Quindío (D.1), sin teléfono (el dueño puede
  decidir agregar 324 368 2078); el horario de atención sigue inventado. El
  envío real es el 3.6 (API + tabla + consentimiento + política v1.1); el
  checkout real va con A-26. /impeccable audit 16/20 (foco a body al abrir el
  formulario de adopción, sin modo oscuro ni tokens: pulido opcional).
  El correo de atención está ahora en AvisoDemo.jsx, Contact.jsx,
  PoliticaDatos.jsx, CasillaAutorizacion.jsx y LoginModal.jsx (desde el 3.5;
  antes en RegisterModal.jsx), RegisterScreen.js y el borrador .md.
- "Por actualizar" está vacía.
- Pruebas: 153 (132 OK + 21 omitidas que necesitan MariaDB).
- Autorización de datos (3.1 parte 1, NC-005 cerrada): api.py tiene
  VERSION_POLITICA_DATOS = "1.0" y _MENSAJE_SIN_AUTORIZACION. /register exige
  "acepta_datos": true (solo el booleano JSON, con `is True`) justo después de
  revisar los campos obligatorios, antes del nombre, el DNS, la BD, la revisión
  del pendiente vigente (2.7) y el correo; si no, 400 "Debes autorizar el
  tratamiento de tus datos personales para registrarte". El pendiente guarda
  fecha_autorizacion_datos (datetime de /register, sin microsegundos) y
  version_politica_datos; /verify las pasa al Usuario y, si faltan, responde ese
  400 y descarta el pendiente (doble barrera). Usuario(acepta_datos=False por
  defecto, fecha_autorizacion_datos, version_politica_datos); el INSERT de
  UsuarioDAO las escribe (desde el 3.5 los SELECT también las leen). BD: acepta_datos NOT NULL
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
  (aria-describedby), que desde el 06/11/2026 termina con el correo de atención
  proyectopetconnect+atencion@gmail.com (D.1). Sin marcar: MENSAJE_SIN_AUTORIZACION en el cuadro rojo
  (role="alert"), foco en la casilla y NINGUNA llamada a la API. api.js:
  registerUser(name, email, password, aceptaDatos) manda
  acepta_datos: aceptaDatos === true. Página src/pages/PoliticaDatos.jsx (copia
  en JSX de la Parte A del borrador; VERSION_POLITICA = "1.0"; CORREO_DATOS y
  <CorreoDatos /> (mailto) en las secciones 1 y 8; D.1 completa desde el
  06/11/2026 (responsable, Armenia, dirección y teléfono en la sección 1); D.3
  y D.5 salen como "Por definir"; si cambias el texto, cambia también el .md
  y sube la versión aquí y en la API). Ruta en App.jsx y enlace en Footer.jsx.
  Probada por el dueño con la API real: conteo 0 | 10 | 0 y 1 | 1 | 1.
- Móvil (3.1 parte 3, hecha el 06/11/2026): RegisterScreen.js tiene la casilla
  sin marcar (Pressable con role="checkbox" y aria-checked; se usan role/aria-*
  porque react-native-web no traduce accessibilityState), el enlace en su propia
  línea "Leer los términos y condiciones que aceptas: Política de tratamiento
  de datos personales" (decisión del dueño; Linking.openURL(POLITICA_URL)), el
  aviso B.2 (desde el 06/11/2026 con el correo de atención
  proyectopetconnect+atencion@gmail.com, igual que la web; si cambia, cambiarlo
  en RegisterScreen.js, RegisterModal.jsx, PoliticaDatos.jsx y el borrador .md)
  y el error en una zona aria-live="polite". Sin marcar: mensaje B.3
  y ninguna petición. ScrollView + KeyboardAvoidingView (behavior="padding",
  offset con measureInWindow: en Expo 57 Android no encoge la ventana con el
  teclado). api.js: registerUser(..., aceptaDatos) manda acepta_datos:
  aceptaDatos === true y exporta POLITICA_URL (http://${HOST}:5173/
  politica-de-datos; solo desarrollo, 5.3). Probado por el dueño en el
  emulador: conteo 0 | 5 | 0 y 1 | 1 | 1 (el dueño borró sus cuentas de prueba
  viejas el 06/11/2026). OJO: en la BD del dueño las 6 mascotas en adopción
  son del USUARIO 5, no de la cuenta del refugio de seed.py (comprobado el
  06/11/2026 con un conteo, sin mostrar correos): NO borrar la cuenta 5, ON
  DELETE CASCADE borraría las mascotas. Esas 6 filas no salieron de ningún
  seed.py del repositorio (textos sin tildes, ids 3 a 8).
  /impeccable audit 15/20 (foco a la casilla tras el error, android_ripple,
  48 dp en el enlace: pulido opcional).
- Emulador Android (PC del dueño): AVD Pixel_7. Encenderlo sin depender de una
  terminal: Start-Process "$env:LOCALAPPDATA\Android\Sdk\emulator\emulator.exe"
  -ArgumentList "-avd","Pixel_7". ANDROID_HOME está vacía: se creó
  PetConnect.Mobile/android/local.properties con sdk.dir (android/ está en
  .gitignore). Antes de npm run android, en ESA terminal:
  $env:JAVA_HOME = "C:\Program Files\Android\Android Studio\jbr" (Java 21; con
  el Java 25 del sistema falla configureCMakeDebug). La terminal de Metro no
  sirve para escribir comandos (cada letra es un atajo: j abre DevTools, r
  recarga). La web para el emulador: npm run dev -- --host 127.0.0.1.
- La API NO tiene recargador: después de cambiar el backend hay que reiniciarla
  (Ctrl+C y ..\.venv\Scripts\python api.py desde petconnect.Backend). Para saber
  si corre el código nuevo: CreationDate del proceso (Get-CimInstance
  Win32_Process, CommandLine con api.py) más reciente que LastWriteTime de
  api.py, o un POST /api/auth/register sin acepta_datos que responda 400
  "Debes autorizar...".
- Pendientes que dejó el 3.1 (fuera de NC-005): el 3.5 (en curso, ver abajo);
  botón "borrar mi cuenta"
  (supresión, C.8) y llenar las decisiones D.2, D.3, D.5 y D.6 de la política
  (D.1 y D.4 decididas)
  (no bloquean el cierre técnico, sí la publicación). El móvil tampoco tiene
  "Reenviar código" en "Verifica tu correo" (pendiente del 2.7).
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

3.4 parte 1 (backend, A-22, hecha el 06/11/2026; opción (a) del dueño: NO
mostrar vacunación, esterilización ni tamaño, porque la tabla mascotas no
tiene esas columnas y un dato de salud no se inventa):
- api.py: _mascota_to_dict(row) solo hace _row_to_dict(row). Las 3 rutas de
  mascotas devuelven exactamente id, name, species, breed, gender, age, image,
  description, estado. Ya NO existen vaccinated, sterilized ni size.
- seed.py: color en None en las 6 mascotas; 10 textos con la línea
  "# REVISAR-VETERINARIO: motivo" justo encima de su tupla (Luna, Milo, Nala,
  Max, Cleo; Alimento Premium, Cama Ortopédica, Shampoo Hipoalergénico,
  Alimento para Gato, Hueso Dental); fotos anotadas como Unsplash. Pendiente
  de validación veterinaria antes de publicar (avisado al dueño).
- Migración sql/migraciones/2026-11-06_mascotas_ejemplo.sql (YA aplicada a la
  BD del dueño): color con tamaño ("Grande", "Mediano", "Pequenio",
  "Peque_o", "Tama_o %") → NULL y Nala (Gato, edad 6) → 0, solo en las 6
  mascotas de ejemplo reconocidas por (nombre, especie) + estado en_adopcion,
  sin usar id ni dueño. Resultado en la BD: 6 con color NULL, Nala con 0; la
  API devuelve Nala con age 0. Explicada en sql/README.md.
- Pruebas: tests/test_ficha_mascota.py (API con BD simulada; seed.py leído
  con ast, sin importarlo, para no cargar el .env) y en test_esquema.py
  PruebasMigracionEjemploSinBD / PruebasMigracionEjemploEnBD (base temporal
  petconnect_prueba_ejemplo) y test_seed_no_guarda_el_tamano_en_color.
- Pendiente sin ítem: la BD del dueño tiene descripciones distintas de
  seed.py (solo la de Luna habla de vacunas); también deben pasar por un
  veterinario antes de publicar.

3.4 parte 2 (web, A-22, hecha el 06/11/2026):
- src/utils/mascota.js: formatearEdad(age) (0 → "Menos de 1 año", 1 →
  "1 año", n → "n años"; null, negativo o no entero → null),
  formatearSexo(gender) ("hembra" → "Hembra", "macho" → "Macho";
  "no_definido" u otro → null) y datosMascota(pet) ("Raza · Edad · Sexo" solo
  con lo conocido, "" si nada). La usan PetDetail.jsx y Adoption.jsx.
- Pruebas: tests/mascota.test.js y tests/sin-salud-inventada.test.js (OJO:
  también cuenta los comentarios).

3.4 parte 3 (móvil, A-22, hecha el 06/11/2026):
- PetConnect.Mobile/src/utils/mascota.js = COPIA de la de la web (no hay
  paquete compartido): si cambias una, cambia la otra.
- PetDetailScreen.js: especie en su línea y debajo datosMascota (no se pinta
  si está vacía); sin Badge, sin Vacunada/Esterilizada y sin Talla.
  AdoptionScreen.js: la misma línea. Las <Image> de las dos tienen
  role="img" y aria-label={nombre}: sin el rol, react-native-web deja la
  etiqueta en un div que el lector de pantalla ignora.
- Pruebas: tests/mascota.test.mjs (formato + las dos pantallas usan
  datosMascota) y tests/sin-salud-inventada.test.mjs (falla si src/ menciona
  vaccinated, sterilized, .size, Talla, Vacunada/o o Esterilizada/o; cuenta
  los comentarios). Contraprueba: con las pantallas viejas fallan 2 de 7.
- Revisado con npx expo export --platform web (config "movil-web-export",
  puerto 8090) a 375 px con una API simulada en el navegador (window.fetch
  reemplazado, datos inventados): desde el puerto 8090 la API real falla por
  CORS. Probado por el dueño en el emulador con la API real: lista de
  Adopción con las 6 mascotas bien formateadas. Si el emulador muestra
  "Unable to load script": Metro no estaba o el emulador no llegaba a él;
  adb reverse tcp:8081 tcp:8081 (y tcp:5000) y RELOAD. Si npx expo start
  dice que el 8081 está ocupado, ya hay un Metro (el de npm run android):
  contestar n.
  /impeccable audit 14/20, todo ya existía (pendiente sin ítem, preguntar al
  dueño): texto gris #64748b sobre el fondo #f2f2f2 de la ficha ≈ 4,3:1
  (< 4,5:1); la ficha y la lista muestran el error crudo sin "Reintentar" ni
  "no encontrada" (lo que la web ganó en el 3.3); colores fijos sin modo
  oscuro; miniaturas de 70 px que bajan la foto completa. Las fotos de
  HomeScreen.js:56 y ProductDetailScreen.js:19 siguen sin texto alternativo.
- Sigue pendiente la validación veterinaria de los textos marcados
  REVISAR-VETERINARIO (seed.py) y de las descripciones de la BD del dueño.

3.5 parte 1 (API + DAO, A-20, R05, hecha el 06/11/2026; opción (a) del
dueño):
- api.py: _MENSAJE_LOGIN_SIN_AUTORIZACION ("Para seguir usando tu cuenta debes
  autorizar el tratamiento de tus datos personales"), _autorizacion_vigente(u)
  (u.acepta_datos is True y u.version_politica_datos == VERSION_POLITICA_DATOS)
  y _pedir_autorizacion() → 403 {"error": ..., "requiere_autorizacion": true}.
  /login: después de la contraseña, la migración del hash y el estado; si no
  está vigente y el cuerpo no trae "acepta_datos": true (is True) → 403 sin
  código; con la casilla, el pendiente del OTP lleva id_usuario,
  fecha_autorizacion_datos (now sin microsegundos) y version_politica_datos.
  Si ya está vigente, "acepta_datos" se ignora y el pendiente solo lleva
  id_usuario. /login/verify: tras el código correcto y consultar el usuario,
  si no está vigente exige en el pendiente fecha, la versión ACTUAL y el mismo
  id_usuario (si no → el mismo 403; el pendiente ya se descartó) y llama
  dao.registrar_autorizacion(id, fecha, version) (False → 500 sin token).
- dao/usuario_dao.py: los 4 SELECT terminan en fecha_autorizacion_datos,
  version_politica_datos (fila[12], fila[13] en _mapear_usuario);
  registrar_autorizacion(id_usuario, fecha, version) = UPDATE parametrizado
  de acepta_datos = 1 + las dos columnas (juntas por chk_autorizacion_datos).
  UsuarioDAO.actualizar (consola) sigue pudiendo poner acepta_datos = 1 sin
  fecha y la BD lo rechazaría: es del 4.11.
- Pruebas: tests/test_login_datos.py (12, BD simulada, usuario SimpleNamespace
  con acepta_datos/fecha/version) y en test_esquema.py
  PruebasEsquemaEnBD.test_autorizacion_al_iniciar_sesion_con_la_base_real (la
  corre el dueño con PETCONNECT_PRUEBA_BD=1). test_logs.py usa un usuario con
  autorización 1.0. Contraprueba: api.py viejo → fallan 5 de 9; DAO viejo → 3
  de 3. Toda prueba nueva que haga /login con un usuario falso debe darle
  acepta_datos=True y version_politica_datos="1.0" (o esperar el 403).
- Borrador de la política: B.3 tiene 3 filas nuevas (403 de la API; mensaje
  del cliente sin casilla: "Para continuar debes autorizar el tratamiento de
  tus datos personales."; texto del mailto: "Si no quieres autorizarlo,
  escríbenos a proyectopetconnect+atencion@gmail.com y borraremos tu
  cuenta."); C.9 y C.10 apuntan al 3.5. La Parte A no cambió (sigue 1.0).
- Riesgos que siguen: un token viejo vale hasta 24 h (require_auth no consulta
  la BD; 4.13); la consola no pide la autorización (4.11).
- La API del dueño debe reiniciarse para correr este código (sin recargador).

3.5 parte 2 (web, A-20, R05, hecha el 06/11/2026):
- src/components/CasillaAutorizacion.jsx (props id, name, checked, onChange,
  ref; el aviso tiene id `${id}-aviso` y la casilla aria-describedby): ÚNICO
  lugar de la web con el texto B.1 (+18, enlace a /politica-de-datos en
  pestaña nueva) y B.2 (con el correo de atención). Lo usan RegisterModal.jsx
  (id "reg-acepta", sin cambio visible) y LoginModal.jsx (id "login-acepta").
  Si cambia el texto legal: este componente, RegisterScreen.js del móvil,
  PoliticaDatos.jsx (si es la Parte A) y el borrador .md.
- api.js: errorDeApi(mensaje, status, data) pone requiereAutorizacion = true
  solo si data.requiere_autorizacion === true (el 403 "Cuenta inactiva" no lo
  trae); loginUser(email, password, aceptaDatos) agrega acepta_datos: true
  solo si aceptaDatos === true. AuthContext.jsx: login(email, password,
  aceptaDatos).
- LoginModal.jsx: estado avisoAutorizacion (mensaje del 403; si no está
  vacío se muestra el paso "Autoriza el uso de tus datos"), aceptaDatos (sin
  marcar) y aceptaRef. "Autorizar y continuar" repite login(email, password,
  true) con lo que sigue en el estado; sin marcar: MENSAJE_SIN_AUTORIZACION
  ("Para continuar debes autorizar el tratamiento de tus datos personales.")
  en role="alert", foco en la casilla y ninguna petición. "Cancelar" vuelve
  al formulario y borra la contraseña (también al cerrar ese paso); está
  desactivado mientras se envía (disabled={loading}, arreglo del 06/11/2026:
  cancelar a mitad de la petición llevaba igual al código). Línea B.3
  con mailto al correo de atención. Si /login/verify responde el 403, vuelve
  al paso de la casilla (sin marcar). Orden de pantallas: código
  (pendingLoginEmail) > casilla > formulario.
- Pruebas: tests/api.test.js (+5: con true manda el booleano; sin él, ni con
  "true" ni 1, no lo manda; 403 de /login y de /login/verify traen
  requiereAutorizacion; "Cuenta inactiva" no) y tests/casilla-autorizacion
  .test.js (3, leen el texto: "Soy mayor de 18 años" solo en el componente,
  los dos modales usan <CasillaAutorizacion>, LoginModal tiene
  requiereAutorizacion y los mensajes B.3). Contraprueba: fallan 7 de 8; pasa
  a propósito "sin la casilla NO manda acepta_datos".
- Revisado a 375 px con la config "web" de .claude/launch.json (Vite tomó el
  puerto 5175 porque el 5173 estaba ocupado) y window.fetch reemplazado en el
  navegador (datos inventados). /impeccable audit 16/20 (detector sin
  hallazgos; pulido opcional: el foco queda en body al cambiar de paso; los
  modales sin role="dialog", ya anotado en el 2.7).
- Prueba con la API real (la hace el dueño, con la API reiniciada; si no la
  ha mandado, pídela antes de seguir): respaldo; conteo antes; iniciar
  sesión en la web con una cuenta vieja (acepta_datos = 0): sale el paso de
  la casilla; "Autorizar y continuar" sin marcar → mensaje; marcar → código
  → sesión iniciada; conteo después con SELECT acepta_datos, COUNT(*),
  COUNT(fecha_autorizacion_datos) FROM usuarios GROUP BY acepta_datos (sin
  mostrar correos): debe pasar una cuenta de 0 a 1, con fecha. OJO: la
  cuenta 5 es dueña de las 6 mascotas; autorizarla está bien, borrarla NO.
  Con la captura: anotar el resultado en la fila del 3.5, en el "Estado" de
  A-20 de la AUDITORÍA y en el R05 de la GA9 (hoy dicen "pendiente del dueño").
- Avance de esa prueba (06/11/2026, tarde): respaldo
  C:\Users\goku8\Respaldos\petconnect-2026-11-06-antes-3.5-web.sql hecho.
  Las cuentas viejas en 0 (5, 9, 11, 12, 13) NO sirven para probar: 9, 11,
  12 y 13 son @example.com (no reciben el código) y la 5 (refugio) tiene un
  correo de un dominio ajeno al dueño (no iniciar sesión con ella: el código
  iría a un buzón ajeno). Por eso el dueño les quitó la autorización a dos
  cuentas SUYAS con UPDATE usuarios SET acepta_datos = 0,
  fecha_autorizacion_datos = NULL, version_politica_datos = NULL WHERE
  id_usuario = N (una fila cada vez; quitarla no la inventa): la 17 (alias
  de prueba) y la 18 (creada hoy desde la web con la casilla del registro:
  eso confirmó que RegisterModal + CasillaAutorizacion funcionan con la API
  real, quedó con fecha). Conteo antes: 0 | 7 | 0 y 1 | 1 | 1.
  Tropiezos: la API del puerto 5000 resultó ser un proceso VIEJO de las 10:43
  (anterior a api.py, 11:15) que se quedó con el puerto al cerrarse la de las
  12:34; el dueño cerró las API viejas y arrancó una nueva a las 13:14 (antes
  de cada prueba, revisar con Get-NetTCPConnection -LocalPort 5000 -State
  Listen qué proceso tiene el puerto y su hora de arranque). Además, el alias
  "+18" del correo es de la cuenta 19, no de la 18: identificar las cuentas
  por id_usuario, no por el alias.
  RESULTADO (06/11/2026, dueño, API de las 13:14): la cuenta 18 inició sesión
  en la web, vio "Autoriza el uso de tus datos", marcó la casilla, escribió el
  código y quedó con acepta_datos = 1 y fecha 2026-11-06 13:21:05. La cuenta
  19 se creó a las 13:09:21 desde el registro web con la casilla (otra
  confirmación del registro). La 17 sigue en 0 (se usará para el móvil).
  Conteo esperado 0 | 6 | 0 y 1 | 3 | 3 (deducido; no se corrió el GROUP BY
  final). El caso "sin marcar" con la API real NO se capturó: está probado con
  las pruebas automáticas y la API simulada. Pendiente sin ítem: decidir si se
  borran las cuentas @example.com 9, 11, 12 y 13 (NO la 5).

Contexto del próximo paso (3.5 parte 3 de 3: móvil; regla 3, solo móvil):
- Hoy el móvil muestra el 403 de /login como un error cualquiera.
  PetConnect.Mobile/src/services/api.js: apiFetch lanza new Error(data.error)
  sin status ni requiere_autorizacion (líneas 40 y 42); loginUser(email,
  password) (línea 62) no manda acepta_datos. src/context/AuthContext.js:
  login. src/screens/LoginScreen.js (127 líneas): correo + contraseña y
  código. El móvil no tiene componente de casilla: está dentro de
  RegisterScreen.js (Pressable con role="checkbox", aria-checked, enlace
  aparte con Linking.openURL(POLITICA_URL), aviso B.2, error en zona
  aria-live="polite", ScrollView + KeyboardAvoidingView).
- Plan propuesto (pedir aprobación): igual que la web. Sacar la casilla de
  RegisterScreen.js a src/components/CasillaAutorizacion.js (mismo texto,
  incluido el enlace "Leer los términos y condiciones que aceptas: ...") y
  usarla en el registro y en un paso nuevo de LoginScreen.js ("Autoriza el
  uso de tus datos": casilla sin marcar, "Autorizar y continuar",
  "Cancelar", y el texto B.3 con Linking.openURL("mailto:...")). Sin marcar:
  mensaje B.3 del cliente y ninguna petición. api.js: el error lleva
  requiereAutorizacion (y quizá status) y loginUser(email, password,
  aceptaDatos) manda acepta_datos solo con true. Si /login/verify responde
  el 403, volver a la casilla.
- Prueba: ampliar las pruebas .mjs del móvil (npm test): una prueba de
  api.js con fetch simulado (OJO: api.js del móvil puede importar cosas de
  React Native o Expo que Node no carga; si es así, probar leyendo el texto
  del archivo, como mascota.test.mjs) y otra que lea el texto: la frase
  "Soy mayor de 18 años" solo en el componente, las dos pantallas lo usan.
  Contraprueba con el código viejo. npx expo export --platform web y 375 px
  con la API simulada (config "movil-web-export", puerto 8090; sin marcar:
  0 peticiones). Prueba en el emulador con la API real (la hace el dueño):
  una cuenta vieja, casilla, código y conteo.
- Al terminar la parte 3: marcar [x] el 3.5 y seguir con el 3.6 (último de
  la Fase 3; después, recordar el push y preguntar).

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
   - Web (si cambió): npm run lint, npm test y luego npm run build
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

**Próximo ítem: 3.5, parte 3 de 3 (móvil)** (A-20, R05): la API ya pide la autorización al iniciar sesión (parte 1) y
la web ya muestra la casilla (parte 2, 06/11/2026; probada por el dueño con la API real); falta que
`LoginScreen.js` haga lo mismo en el móvil. Después: el 3.6. Sin push hasta terminar toda la Fase 3.
