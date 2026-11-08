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

> Al cerrar 2.2 + 2.3 + 4.8 (`decrypt`) se cierra **NC-007** (cerrada el 08/11/2026) · 2.5 + 2.6 cierran **NC-006** · 2.9 cierra **NC-002**.

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
| [x] | 3.5 | A-20 | — (R05) | Pedir la autorización de datos a las cuentas existentes (`acepta_datos = 0`) y a quienes aceptaron una versión vieja de la política, al iniciar sesión (API + web + móvil); si no autorizan, ofrecer borrar la cuenta. **Nunca** con un `UPDATE` que la invente. Después de la parte 3 del 3.1. Surgió el 05/11/2026 | 🔴 | Una cuenta en 0 que inicia sesión ve la casilla y, al marcarla, queda con fecha y versión; sin marcarla no entra — *Opción (a) del dueño; si no autorizan, enlace al correo de atención para borrar la cuenta (proceso manual, C.8). Parte 1 de 3 (API + DAO) hecha el 06/11/2026: `api.py` (`_autorizacion_vigente`: `acepta_datos` = 1 y versión actual; `/login` responde 403 `"requiere_autorizacion": true` tras la contraseña y sin enviar código; con `"acepta_datos": true` la fecha y la versión van en el pendiente; `/login/verify` las escribe solo con el código correcto y sin prueba válida responde 403 sin token), `dao/usuario_dao.py` (los `SELECT` leen fecha y versión; `registrar_autorizacion`, `UPDATE` parametrizado de las tres columnas); `tests/test_login_datos.py` (12) y `test_esquema.py` (1 con MariaDB); con el `api.py` anterior fallan 5 de 9, con el DAO anterior 3 de 3. Parte 2 de 3 (web) hecha el 06/11/2026: componente `CasillaAutorizacion.jsx` (texto B.1 + B.2 en un solo lugar, lo usan el registro y el inicio de sesión); `LoginModal.jsx` muestra el paso “Autoriza el uso de tus datos” con el 403 (casilla sin marcar, “Autorizar y continuar”, “Cancelar” y `mailto` B.3 para pedir borrar la cuenta; sin marcar, mensaje B.3 y 0 peticiones; un 403 en `/login/verify` vuelve a la casilla); `api.js` (`acepta_datos` solo con `true`, error con `requiereAutorizacion`) y `AuthContext.jsx`; `tests/api.test.js` (+5) y `tests/casilla-autorizacion.test.js` (3): con el código anterior fallan 7 de 8; `npm test` 20/20, lint y build OK, 375 px con la API simulada; `/impeccable audit` 16/20. Arreglo de la auditoría del 06/11/2026: “Cancelar” desactivado mientras se envía (si no, al llegar la respuesta salía igual la pantalla del código). Probada por el dueño con la API real el 06/11/2026: la cuenta 18 (`acepta_datos = 0`) inició sesión en la web, vio “Autoriza el uso de tus datos”, marcó la casilla, escribió el código y quedó con `acepta_datos = 1` y fecha; el caso “sin marcar” quedó probado con las pruebas automáticas y la API simulada. Parte 3 de 3 (móvil) hecha el 06/11/2026: componente `src/components/CasillaAutorizacion.js` (texto B.1 + enlace aparte + B.2 en un solo lugar; lo usan `RegisterScreen.js`, sin cambio visible, y `LoginScreen.js`); `LoginScreen.js` muestra el paso “Autoriza el uso de tus datos” con el 403 (casilla sin marcar, “Autorizar y continuar”, “Cancelar” desactivado mientras se envía y que borra la contraseña, línea B.3 con enlace aparte `mailto`; sin marcar, mensaje B.3 en `aria-live` y 0 peticiones; un 403 en `/login/verify` vuelve a la casilla); `src/utils/peticiones.js` (`errorDeApi` con `status` y `requiereAutorizacion`, `cuerpoLogin` con `acepta_datos` solo con `true`) que usa `api.js`; `AuthContext.js` sin cambios. `tests/peticiones.test.mjs` (5) y `tests/casilla-autorizacion.test.mjs` (4): con el código anterior fallan las 9 nuevas (5 si se deja `peticiones.js`: pasan a propósito las 4 que solo prueban ese archivo nuevo); `npm test` 16/16; `npx expo export --platform web` OK; 375 px con la API simulada (sin marcar 0 peticiones, marcada 1 con `"acepta_datos": true`, 403 en verify → casilla, Cancelar borra la contraseña, registro igual); `/impeccable audit` 14/20. Probado por el dueño en el emulador con la API real el 07/11/2026: la cuenta 17 (`acepta_datos = 0`) vio la casilla, la marcó, escribió el código y quedó con `acepta_datos = 1` y fecha 2026-11-07 01:32:37 (consulta por `id_usuario`, sin correos; las 18 y 19 siguen en 1 con su fecha). A-20 y R05: contingencia completa* |
| [x] | 3.6 | A-21 | — | Envío real de la solicitud de adopción y del mensaje de contacto: endpoint con `@require_auth` (y limitador), tabla nueva (migración + `schema.sql`), consentimiento para esa finalidad y **política v1.1** (Parte C, “Fuera del 3.1”; subir `VERSION_POLITICA_DATOS`), web y, si se decide, móvil. Quitar el `AvisoDemo` solo del formulario que ya envíe. El checkout real va aparte (A-26). Surgió en el 3.2 (06/11/2026) | 🔴 | Una solicitud enviada queda en la BD con el usuario, la fecha y la versión de la política, y la web dice “enviada” solo si la API respondió 201 — *Decisiones del dueño (07/11/2026): adopción y contacto; solo con sesión; solo en la BD (el equipo las lee con SQL); mensaje + teléfono opcional (solo adopción); sin casilla aparte, aviso corto B.5 (vale la autorización de la cuenta con la política 1.1, cuya versión se copia a cada solicitud); `VERSION_POLITICA_DATOS` = `"1.1"` desde la parte 1; móvil como parte 3. Parte 1 de 3 (API + BD) hecha el 07/11/2026: tabla `solicitudes` (`schema.sql` + migración `2026-11-07_solicitudes.sql`, regla `chk_solicitud_tipo`, `ON DELETE CASCADE`), `dao/solicitud_dao.py`, `POST /api/solicitudes/adopcion` y `/contacto` (limitador + `@require_auth`; 400 / 403 con `requiere_autorizacion` / 404 / 201 solo si se guardó), política 1.1 en el borrador .md; `tests/test_solicitudes.py` (19) y `test_esquema.py` (+7); con el código anterior fallan 27. Parte 2 de 3 (web) hecha el 07/11/2026: componente `FormularioSolicitud.jsx` (sin sesión, “Inicia sesión para enviar”; con sesión, teléfono opcional, mensaje y aviso B.5; “enviada” solo con el 201; 401/403 → “Volver a iniciar sesión”), `utils/solicitud.js`, `api.js` (`enviarSolicitudAdopcion`, `enviarMensajeContacto`), `PetDetail.jsx` y `Contact.jsx` sin `AvisoDemo` (sigue en Checkout), `PoliticaDatos.jsx` en 1.1; `tests/solicitudes.test.js` (9; con el código anterior fallan 5), `npm test` 29/29, lint y build OK, 375 px con la API simulada; `/impeccable audit` 16/20. Migración aplicada en la BD del dueño y probado con la API real el 07/11/2026: solicitud de adopción de Luna → “Solicitud enviada… número 1” (201, cuenta ya con la 1.1). Parte 3 de 3 (móvil) hecha el 07/11/2026: Contacto como **pestaña nueva** (decisión del dueño); `FormularioSolicitud.js` (mismo comportamiento que la web) en `PetDetailScreen.js` y `ContactScreen.js`; el inicio de sesión se abre como modal `IniciarSesion` encima del formulario (no se pierde lo escrito); `utils/solicitud.js` (copia de la web, una prueba exige que sean iguales), `peticiones.js` y `api.js` con las dos funciones; `tests/solicitudes.test.mjs` (11; con el código anterior fallan 4), `npm test` 27/27, `expo export --platform web` OK, 375 px con la API simulada; `/impeccable audit` 14/20. **Fase 3 completa.** Probado por el dueño en el emulador con la API real el 07/11/2026: “Mensaje enviado… número 2” y “Solicitud enviada… número 3” (Luna)* |

---

## Fase 4 — Estabilidad, calidad y pruebas

| ✔ | # | ID | NC | Qué | Esfuerzo |
|---|---|---|---|---|---|
| [x] | 4.1 | A-17 | NC-004 | Exigir minúscula en API, web y móvil (validación en un módulo común) — *Hecho el 07/11/2026 en 3 partes: API (`240116e`, `security/politica.py`), web (`680797e`, `src/utils/contrasena.js`) y móvil (`43fcfe1`, copia de la utilidad; `RegisterScreen.js` ya valida antes de enviar). `PETCONNECT1!` se rechaza en los tres. Regresión: `test_politica.py` (17), `contrasena.test.js` (13) y `contrasena.test.mjs` (8); la contraprueba falla con el código viejo. NC-004 cerrada* | 🟢 |
| [x] | 4.2 | A-19 | NC-011 | `AND activo = TRUE` en `buscar_por_nombre` de proveedores — *Hecho el 07/11/2026 en una parte (`06a422d`, solo backend): `_BUSCAR_POR_NOMBRE` filtra `activo = TRUE` como la búsqueda por ciudad y, con el sí del dueño, escapa `!`, `%` y `_` (`ESCAPE '!'`). Regresión: `tests/test_proveedores.py` (5, BD simulada); con el DAO viejo fallan 3 y pasan a propósito 2. NC-011 cerrada; CP-013 sigue en seguimiento por el filtro por tipo, que no existe* | 🟢 |
| [x] | 4.3 | A-31 | — | GitHub Actions: `unittest` + `npm run lint` + `npm run build` en cada push — *Hecho el 07/11/2026 en una parte (`8802815`): `.github/workflows/ci.yml`, en cada push y con “Run workflow”, un job por módulo en `ubuntu-latest`: backend (Python 3.14, `unittest`), web (Node 24: `npm ci`, lint, `npm test`, build) y móvil (Node 24: `npm ci`, `npm test` y `expo export --platform web`, con el sí del dueño). `permissions: contents: read`, `persist-credentials: false`, acciones `@v7`, sin secretos. Validado en local en una copia limpia del commit (sin `.env` ni `node_modules`): backend 200 (176 + 24 omitidas), web 0 errores de lint + 42/42 + build, móvil 35/35 + export; YAML revisado y sin diferencias de mayúsculas en los imports. **La primera ejecución en GitHub queda pendiente del push** (al terminar todo). No cierra NC* | 🟡 |
| [x] | 4.4 | A-31 | todas | Pruebas de endpoints con el cliente de Flask (mascotas, productos, auth, errores) — *Hecho el 07/11/2026 en una parte (`37f8126`, solo pruebas; `api.py` sin tocar). Primero un inventario ruta × caso y NC × prueba: de 14 rutas, 6 tenían huecos (`/api/auth/me` sin ninguna prueba) y NC-001, NC-008 y NC-009 no tenían regresión por la API. `tests/test_endpoints.py` (31, BD/DNS/correo simulados, sin `.env`): inventario vivo de rutas (ruta nueva sin pruebas → falla; privadas → 401 sin token), productos, filtro de adopción, `/me` con token real, migración del hash, login, verificación del código, registro y `validar-correo`. Suite 231 (207 + 24 omitidas). Contraprueba en una copia temporal: 28 roturas, todas detectadas; cada prueba falla con al menos una. A-31 resuelto (falta ver la CI en GitHub con el push). Hallazgo → 4.16* | 🟡 |
| [x] | 4.5 | A-11 | NC-003 | Pool de conexiones + `try/finally` para cerrar cursores — *Hecho el 07/11/2026 en una parte (`9c417de`, solo backend). Decisiones del dueño: pool de 10 (`DB_POOL_SIZE`, de 1 a 32), consola y `seed.py` en el mismo pool, 4.15 aparte. `ConexionBD` presta conexiones de un `MySQLConnectionPool`; si está lleno espera hasta 5 s y luego 503; el log no trae usuario ni host. `conexion_y_cursor()` (el `try/finally` escrito una vez) en los 32 métodos de los 5 DAO y en las 4 consultas de `api.py`; `_get_conn()` (pedía y nunca devolvía) → `_verificar_bd()`. `tests/test_pool.py` (25; 3 con MariaDB): sin fugas en 32 métodos y 14 rutas × 3 escenarios. Suite 256 (229 + 27 omitidas). Contraprueba: con el código viejo fallan 20 de 22; cada archivo arreglado tiene su prueba. NC-003 sigue abierta (4.6, 4.12; paginación e índices sin ítem)* | 🟡 |
| [x] | 4.6 | A-12 | NC-003 | OTP en tabla de la BD (hash del código, intentos, expiración) o 1 worker con hilos; limpiar vencidos y acotar `_mx_cache` — *Hecho el 07/11/2026 en dos partes (solo backend): `_mx_cache` de 1.000 dominios con LRU y candado (`9ccd379`) y tabla `otp_pendientes` (`24ed52c`). Decisiones del dueño: opción A, código cifrado con Fernet (no hash: hay que reenviar el mismo código), datos del registro pendiente borrados al verificar, bloquearse o vencer. `AlmacenOTP(proposito, repositorio)` conserva las reglas y guarda en `OtpDAO` (API) o `RepositorioMemoria` (pruebas); el intento se reserva antes de comparar (un `UPDATE` atómico); crear un código y arrancar la API borran los vencidos; sin la tabla la API no arranca y lo avisa; correos de más de 120 caracteres → 400. `tests/test_otp_bd.py` (48; 16 con MariaDB). Suite 311 (268 + 43 omitidas). El 08/11/2026, con MariaDB, la carrera dio 4 != 5: `verificar()` ahora lee la fila antes de reservar el intento (prueba nueva sin MariaDB). Con MariaDB, 48/48 OK. Contraprueba: con el código viejo 20 intentos a la vez comparan 20 veces y los vencidos no se borran. **Falta del dueño: aplicar la migración (con respaldo)**; opcional: las pruebas con `PETCONNECT_PRUEBA_BD=1`. Hallazgo: A.11 de la política dice que el registro pendiente nunca llega a la BD (decisión D.7 del borrador). NC-003 sigue abierta (4.17, 4.12)* | 🟡 |
| [x] | 4.7 | A-24 | — | Web: validar sesión con `/auth/me` al iniciar y cerrar sesión ante 401 — *Hecho el 08/11/2026 en una parte (`3606c5d`, solo web). Decisión del dueño: opción A, solo el 401 cierra la sesión (503, 502, 500, 404 o red caída no la tocan). `getPerfil()` en `src/services/api.js`, `src/utils/sesion.js` decide (cerrar / mantener / actualizar / ignorar si la sesión cambió mientras llegaba la respuesta) y `AuthContext.jsx` lo llama al iniciar. Regresión: `tests/sesion.test.js` (9; `npm test` 51/51). Contraprueba: con el código viejo fallan 5 y pasan a propósito 4. Visto en el navegador a 375 px con la API real: token falso → 401 → sesión cerrada. No cierra NC* | 🟢 |
| [x] | 4.8 | A-13 | NC-007 | Fernet: usarlo para el teléfono o quitarlo; corregir comentario `api.py:400`; `decrypt` debe fallar — *Hecho el 08/11/2026 en una parte (`979cdf3`, solo backend, no toca la BD). Fernet se queda (lo usan los OTP desde el 4.6). Decisión del dueño: opción A, el teléfono sigue en texto plano y se corrige el comentario de `api.py` (cifrarlo pedía migrar columnas `varchar(20)` y, con A-16 abierto, perder la `FERNET_KEY` dejaría ilegibles los teléfonos). `decrypt()` lanza `InvalidToken` si no puede descifrar; `decrypt_estricto` se fusionó con ella; `api.py` ya no importa `encrypt/decrypt`. Regresión: `PruebasDescifrado` en `tests/test_seguridad.py` (5). Suite 314 (271 + 43 omitidas). Contraprueba: con el `crypto.py` viejo fallan 4 (3 nuevas + el OTP ilegible) y pasan a propósito 2. NC-007 cerrada* | 🟢 |
| [x] | 4.9 | A-15 | — | Decidir `autocommit` y alinear código + README — *Hecho el 08/11/2026 en una parte (`a25224d`, solo backend; no toca el esquema). Decisión del dueño: opción B, `autocommit: False` (lo que ya decía el README). Ninguna operación de los DAO tenía varios pasos (cada escritura es una sentencia con su `commit()`); la única con varios pasos en una conexión es `seed.py`, que ahora es “todo o nada”. Los DAO no cambian: sus `rollback()` ya sirven. El pool se crea con `pool_reset_session=True` explícito: al devolver la conexión se descarta lo no confirmado. README: 5.1, 5.2, 5.3 y 7.2 (pool y `commit()` sobre la conexión prestada). Regresión en `tests/test_pool.py`: 5 sin BD (inventario automático de 21 escrituras y 18 lecturas por su SQL) y 2 nuevas + 1 ajustada con MariaDB. Suite 321 (276 + 45 omitidas). Contraprueba: con el código viejo fallan 2 y pasan a propósito 3; al quitar un `commit()` a propósito, la prueba lo detecta. Opcional del dueño: las pruebas con `PETCONNECT_PRUEBA_BD=1`. No cierra NC* | 🟢 |
| [x] | 4.10 | A-14 | — | Registro con respuesta neutra (sin 409 que revele cuentas) — *Hecho el 08/11/2026 en una parte (`8668680`, solo backend; no toca el esquema). Decisión del dueño: opción A, respuesta neutra + correo de aviso al titular. Un correo con cuenta recibe lo mismo que uno nuevo (200 “Codigo enviado”) por el mismo camino: bcrypt + un correo la primera vez, nada si se repite antes de 10 min, el mismo 503 si el correo falla. Nunca crea OTP. El aviso (`enviar_aviso_cuenta_existente`, plantilla `HTML_AVISO_REGISTRO`) lleva el nombre de la cuenta y no lleva código; la memoria de avisos guarda el SHA-256 del correo. Hueco tapado: `/verify` respondía distinto sin pendiente (“No hay verificación pendiente”) que con código incorrecto; ahora un solo mensaje para sin pendiente, vencido e incorrecto. Web y móvil sin cambios. Regresión: `tests/test_registro_neutro.py` (18) + 7 pruebas viejas ajustadas. Suite 339 (294 + 45 omitidas). Contraprueba: con el `api.py` viejo dan error 52; 9 sabotajes sobre el código nuevo, todos detectados (volver al 409: fallan 11). CP-002 de la GA9 aprobado en la API. Hallazgo → 4.18 (tiempo de `/login`). Opcional del dueño: probarlo con la API real* | 🟢 |
| [x] | 4.11 | A-18 | — | Consola: `getpass`, sin `.strip()`, misma política que la API, autorización de datos — *Hecho el 08/11/2026 en una parte (`3e814e3`, solo backend; no toca el esquema). Decisiones del dueño (las recomendadas): la consola no da la autorización por el titular (Ley 1581, art. 9; política C.6): guarda `acepta_datos = False` explícito y avisa que el titular la dará al iniciar sesión (3.5); nombre, apellidos y formato del correo como la API (sin DNS); correo repetido → “Ese correo ya tiene una cuenta”, sin repetirlo ni calcular bcrypt; contraseña dos veces con `getpass` y sin `.strip()`, por `validar_contrasena`. Módulo común nuevo `security/datos_usuario.py` (sacado de `api.py`; la consola no importa `api.py`, A-41). Regresión: `tests/test_consola_registro.py` (26). Suite 365 (320 + 45 omitidas). Contraprueba: con la consola vieja fallan 13 (registraba `PETCONNECT1!`) y pasan a propósito 13; con el `api.py` viejo falla 1. No cierra NC. Hallazgo → 4.19. Opcional del dueño: probarlo con `python main.py`* | 🟢 |
| [ ] | 4.12 | — | NC-003 | Repetir la prueba de carga (CP-008/CP-017) tras 4.5, 4.6 y 4.17 (saltarlo hasta que esos estén hechos) | 🟡 |
| [ ] | 4.13 | A-03 | — | Revocar sesiones: columna `usuarios.version_sesion` dentro del token y comparada en `require_auth` (sumar 1 al cerrar sesión o cambiar la contraseña); quitar el correo del token (se puede leer); si se guardan ids de sesión, solo su hash SHA-256. **Requiere 4.5** (hecho el 07/11/2026). No reemplaza 2.2 — *Parte 1 de 3 (API y BD) hecha el 08/11/2026 (`3c039ec`). Decisiones del dueño (las recomendadas): ruta `POST /api/auth/logout` y botones por partes (cierra la sesión en todos los aparatos: un contador por cuenta); `require_auth` rechaza con 401 las cuentas con estado distinto de `activo`; los tokens viejos sin versión no valen. Columna `usuarios.version_sesion` (migración `2026-11-08_version_sesion.sql`), token con `sub`, `ver`, `iat` y `exp` (sin correo), `require_auth` consulta la sesión en cada petición (BD caída → 503), la API no arranca sin la columna. `tests/test_sesiones.py` (26; 5 con MariaDB). Suite 395 (345 + 50 omitidas). Contraprueba: fallan las 21 nuevas sin BD. **Falta del dueño: aplicar la migración (con respaldo).** Faltan la parte 2 (web: “Cerrar sesión” llama a la ruta) y la 3 (móvil)* | 🟡 |
| [ ] | 4.14 | A-41 | — | `tests/test_seguridad.py` importa `api.py`, que carga el `.env` real con `load_dotenv()` (no imprime nada, pero choca con la regla): desactivarlo como en `tests/test_correo.py` | 🟢 |
| [ ] | 4.15 | — | — | Mover el SQL de productos y mascotas de `api.py` a `dao/` (regla de `petconnect.Backend/CLAUDE.md`). Antes, que los DAO **propaguen** los errores de la BD (hoy los imprimen y devuelven `None`/`[]`), o el 503 del 2.3 se volvería 404 o lista vacía. Surgió en el 2.9. *El 07/11/2026 el dueño decidió hacerlo aparte del 4.5. Ya existe `conexion_y_cursor()` (4.5): basta quitar el `try/except Error` + `print` de cada método (el `print` muestra el mensaje de MySQL, que puede traer un correo: Ley 1581) y, en `api.py`, `_verificar_bd()` deja de hacer falta. Modelo: `dao/solicitud_dao.py`* | 🟡 |
| [ ] | 4.16 | — | — | `GET /api/productos/<id>` no filtra `activo = TRUE`: un producto descontinuado se ve (y se puede agregar al carrito) si se escribe su URL. Agregar el filtro para que responda el 404 “Producto no encontrado” de siempre y su prueba en `tests/test_endpoints.py` (`PruebasProductos` ya tiene la nota). Sin datos personales. Surgió en el 4.4 (07/11/2026); el dueño decidió no tocar `api.py` en ese ítem. Se puede hacer junto con 4.15 | 🟢 |
| [ ] | 4.17 | A-11 | NC-003 | Paginación e índices (la otra mitad de la acción correctiva de NC-003). **Paginación:** `GET /api/productos` y `GET /api/mascotas/adopcion` devuelven todas las filas sin `LIMIT`; la web y el móvil las consumen (`src/services/api.js` en ambos), así que cambiar la forma de la respuesta toca los 3 módulos: decidir antes si se usan parámetros opcionales (`?pagina=&por_pagina=` con un máximo fijo, parametrizados) que mantengan la lista de hoy o un objeto con `total`, y hacerlo por partes (API, web, móvil). **Índices:** `mascotas` solo tiene la clave primaria y `id_usuario` (falta `estado`), `productos` no tiene índice en `activo` y `proveedores_servicio` solo la clave primaria (`ciudad`, `activo`, `nombre`); el `LIKE '%texto%'` no usa índice. Va en `sql/schema.sql` y en una migración de `sql/migraciones/` con su prueba en `tests/test_esquema.py` (toca la BD: plan primero, respaldo y que el dueño la aplique). Agregado el 07/11/2026 con el sí del dueño, al cerrar el 4.5. Hacerlo antes del 4.12 | 🟡 |
| [ ] | 4.18 | A-14 | — | `/api/auth/login` revela cuentas por **tiempo**: si el correo no existe responde enseguida (`usuario is None` corta antes de bcrypt) y si existe calcula bcrypt (~0,3 s) aunque la contraseña sea mala. Arreglo: comparar contra un hash bcrypt fijo de relleno cuando no hay usuario (mismo costo 12), responder el mismo 401 y una prueba que cuente las llamadas a `verificar_password`/bcrypt en los dos casos. Solo backend. Surgió en el 4.10 (08/11/2026) | 🟢 |
| [ ] | 4.19 | A-18 | — | Consola, “6. Actualizar usuario” (`vista/menu_usuarios.py`, `_actualizar_usuario`): cambia nombres, apellidos y correo **sin validar** (acepta una URL como nombre o `x` como correo) y un correo que ya tiene otra cuenta hace fallar el `UPDATE`, cuyo `print` muestra el mensaje de MySQL con el correo (Ley 1581). Arreglo: usar `validar_nombre` y `validar_formato_correo` de `security/datos_usuario.py` (ya comunes desde el 4.11) y avisar “ese correo ya tiene una cuenta” como el registro; prueba en `tests/test_consola_registro.py` o una nueva. Solo backend. Surgió en el 4.11 (08/11/2026) | 🟢 |

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

*Versión del 08/11/2026, actualizada al terminar la parte 1 del 4.13 (A-03: `usuarios.version_sesion` en el token y
comparada en `require_auth`, ruta `POST /api/auth/logout`, token sin correo; solo backend; no cierra NC). Lo próximo es
la parte 2 del 4.13 (web: el botón “Cerrar sesión” llama a la ruta). El 4.12 se salta hasta tener el 4.17.
Salta los ítems de “Por actualizar” y pide actualizar este prompt al terminar cada ítem o cada parte.*

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
- git log --oneline -12 y git status -sb (qué se hizo en sesiones anteriores).
  PUSH: el 07/11/2026, al cerrar la Fase 3 y con el sí del dueño, se subió a
  origin/main TODO hasta el commit que actualiza este prompt (incluye 3.1 a
  3.6; los últimos: 2b8bc59, 3.6 parte 3 móvil, y e978419, prueba del móvil
  en el emulador). Desde ahí los commits nuevos quedan en local. Decisión
  del dueño del 07/11/2026, al cerrar el 4.1: el push se hace cuando TODO
  esté hecho. NO hagas push ni lo preguntes al cerrar cada ítem; solo al
  marcar el último [ ] de este archivo, recuerda los commits pendientes y
  pregunta (push normal, nunca --force). Sin subir todavía: desde 240116e
  (4.1) en adelante.

Estado conocido (8/11/2026; si el git log muestra más ítems hechos, manda el git log):
- 4.13 PARTE 1 de 3 HECHA el 08/11/2026 (A-03; commit 3c039ec, solo
  backend; TOCA EL ESQUEMA; no cierra NC). Decisiones del dueño (las
  recomendadas): (1) ruta POST /api/auth/logout + botones por partes
  (API → web → móvil); un solo contador por cuenta, así que cerrar
  sesión cierra en TODOS los aparatos (tabla de sesiones por aparato
  descartada); (2) require_auth rechaza con 401 (no 403) las cuentas con
  estado != "activo" (la web solo cierra la sesión con 401, 4.7); (3) los
  tokens viejos sin "ver" no valen (todos inician sesión otra vez).
  Columna usuarios.version_sesion int(10) unsigned NOT NULL DEFAULT 0
  (schema.sql + sql/migraciones/2026-11-08_version_sesion.sql, ADD
  COLUMN IF NOT EXISTS de MariaDB; pasos en sql/README.md).
  jwt_helper.generate_token(user_id, version_sesion): token con sub,
  ver, iat y exp (sin correo); ver entero >= 0 (True no vale).
  UsuarioDAO.consultar_sesion(id) -> (version, estado) o None y
  cerrar_sesiones(id) (suma 1; fecha_actualizacion = fecha_actualizacion
  para no cambiarla); ambos dejan subir los errores (503). api.py:
  _datos_del_token(); require_auth consulta la sesión en cada petición,
  mismo 401 _MENSAJE_SESION_INVALIDA para todo; ya no existe
  request.current_user_email; /login/verify firma con la versión de la
  BD (consultar_sesion) y /register/verify con VERSION_SESION_INICIAL =
  0; POST /api/auth/logout (@require_auth, sin limitador) → 200
  {"message": "Sesion cerrada"}; _preparar_sesiones() al arrancar
  (errno 1054 → aviso y no arranca). _cuenta_que_envia() sigue como 2.ª
  barrera. tests/test_sesiones.py (26: 21 sin BD, 5 con
  PETCONNECT_PRUEBA_BD=1 en petconnect_prueba_sesion y
  petconnect_prueba_sesion_migracion); test_esquema +3; ajustadas las
  pruebas que fabricaban tokens con el correo (test_endpoints: /me con
  usuario borrado → 401; test_esquema con BD crea 2 cuentas activas
  porque el refugio de la semilla está inactivo); test_pool 41 métodos
  (22 escrituras, 19 lecturas); RUTAS_PRIVADAS incluye logout. Suite 395
  (345 + 50 omitidas). Contraprueba (git stash de api.py, jwt_helper.py
  y usuario_dao.py): fallan las 21 nuevas sin BD (37 resultados con
  subcasos), ninguna pasa a propósito. PENDIENTE DEL DUEÑO: aplicar la
  migración con respaldo (sin ella la API nueva no arranca) y, opcional,
  test_sesiones y test_esquema con PETCONNECT_PRUEBA_BD=1. Nota: la
  Figura 4 de la GA9 (ejemplo de CP-012) usa generate_token(2, correo),
  la firma vieja. No existe "cambiar contraseña": cuando exista, debe
  llamar a cerrar_sesiones().
- 4.11 HECHO el 08/11/2026 (A-18; commit 3e814e3, solo backend; no toca
  el esquema; no cierra NC). Decisiones del dueño (las recomendadas):
  (1) la consola NO da la autorización por el titular (Ley 1581 art. 9,
  política C.6): acepta_datos = False explícito, sin fecha ni versión, y
  avisa (AVISO_SIN_AUTORIZACION) que el titular autoriza al iniciar
  sesión (3.5); (2) nombre, apellidos y formato del correo como la API,
  sin DNS; (3) correo repetido → "Ese correo ya tiene una cuenta" sin
  repetirlo, sin bcrypt ni INSERT, y sin pedir la contraseña; (4) la
  contraseña se pide 2 veces. vista/menu_usuarios.py _registrar_usuario:
  getpass (from getpass import getpass), sin .strip(), validar_contrasena;
  valida en orden nombre → apellidos (opcionales) → correo → ¿existe? →
  teléfono → contraseña ×2; cualquier error vuelve al menú sin guardar.
  Módulo común nuevo security/datos_usuario.py: validar_nombre(nombre,
  etiqueta="El nombre") y validar_formato_correo(correo) (vacío, formato,
  máximo 120), sacados de api.py; la consola no importa api.py (A-41).
  api.py: _validar_nombre = validar_nombre (alias) y _validar_correo usa
  validar_formato_correo y luego el DNS; NOMBRE_MIN/MAX, CORREO_MAX y los
  regex ya no están en api.py. tests/test_consola_registro.py (26; simula
  input, getpass, UsuarioDAO y hash_password; desactiva load_dotenv al
  importar). Suite 365 (320 + 45 omitidas). Contraprueba (git stash de
  menu_usuarios.py): fallan 13 (registraba PETCONNECT1! y Abc12!x, input
  visible, quitaba espacios, sin aviso de autorización ni de correo
  repetido), pasan a propósito 13; git stash de api.py: falla 1. Política:
  nota "Fuera del 3.1" (no cambia la Parte A ni la versión). Queda: un
  INSERT simultáneo del mismo correo aún imprime el mensaje de MySQL
  (4.15). Hallazgo → 4.19. Opcional del dueño: probarlo con python
  main.py (usa su .env).
- 4.10 HECHO el 08/11/2026 (A-14; commit 8668680, solo backend; no toca
  el esquema; no cierra NC; CP-002 de la GA9 aprobado en la API).
  Decisión del dueño: opción A (respuesta neutra + aviso al titular); la B
  dejaba el camino de la cuenta existente mucho más rápido. api.py:
  _registro_con_cuenta_existente() responde 200 {"message": "Codigo
  enviado", "email"} como un registro nuevo: la 1.ª vez hash_password()
  (descartado) + enviar_aviso_cuenta_existente(correo de la cuenta,
  primer nombre de la cuenta); antes de AVISO_REGISTRO_ESPERA (600 s) no
  calcula ni envía nada (como el pendiente vigente de A-09); si el aviso
  falla: _liberar_aviso() y el mismo 503 (200 con APP_ENV=desarrollo).
  Nunca crea OTP. _avisos_registro: OrderedDict con el SHA-256 del correo
  en minúsculas, AVISOS_MAXIMO = 1000, candado, reloj _reloj_avisos()
  (time.monotonic, las pruebas lo simulan); en memoria del proceso.
  _RESPUESTA_REGISTRO = "Codigo enviado". verify(): no_pendiente, expirado
  e incorrecto → 400 _MENSAJE_CODIGO_REGISTRO ("Codigo incorrecto o
  vencido. Si pasaron mas de 10 minutos, vuelve a registrarte");
  bloqueado sigue en 429; /login/verify no cambió. correo/: plantilla
  HTML_AVISO_REGISTRO, enviar_aviso_cuenta_existente(to_email, name)
  (escapa el nombre, sin código; remite a proyectopetconnect+atencion@
  gmail.com porque no hay recuperar contraseña). Web y móvil sin cambios
  (muestran data.error; no miraban el 409). Política B.3: 2 filas nuevas
  (el aviso y el mensaje de /verify; no cambia la Parte A ni la versión).
  tests/test_registro_neutro.py (18); ajustadas 7 viejas (test_endpoints
  409 → neutro + parche enviar_aviso + _liberar_aviso en setUp; mensajes
  de /verify en test_endpoints, test_otp y test_registro). Suite 339 (294
  + 45 omitidas). Contraprueba: git stash de api.py → 52 errores (no
  existen las funciones nuevas); en una copia del scratchpad, 9
  sabotajes del código nuevo, todos detectados (409 → 11 fallan; mensajes
  viejos de /verify → 5; sin bcrypt → 2; sin límite → 4; nombre escrito
  → 2; sin 503 → 1; sin liberar → 1; correo en claro → 1; crear OTP → 3).
  Riesgos abiertos anotados en A-14: tiempo de /register/resend pasados
  60 s, el 429 tras 6 códigos malos solo con pendiente real y tiempos no
  idénticos al milisegundo (taparlos: correos en segundo plano, que
  cambia el 503 del 2.8). Hallazgo → 4.18 (/login por tiempo).
  Opcional del dueño: probarlo con la API real (registrarse con un
  correo que ya tiene cuenta → "Codigo enviado" y llega el aviso).
- 4.9 HECHO el 08/11/2026 (A-15; commit a25224d, solo backend; no toca
  el esquema; no cierra NC). Decisión del dueño: opción B, autocommit
  False en config/db_config.py (lo que ya decía el README). Búsqueda de
  operaciones de varios pasos: cada escritura de los DAO es una sentencia
  con su commit(); el UPDATE atómico de OtpDAO no cambió; /register/verify
  y /login/verify usan conexiones distintas (el autocommit no los toca);
  la única con varios pasos en una conexión es seed.py, que ahora es
  "todo o nada". Los DAO no cambiaron (sus rollback() ya sirven).
  conexion/conexion_bd.py: MySQLConnectionPool(..., pool_reset_session=
  True) explícito; al devolver la conexión, reset_session() descarta lo
  no confirmado y reaplica autocommit y sql_mode (mysql-connector 9.1.0).
  README: 5.1, 5.2, 5.3 y 7.2 (pool, commit() sobre la conexión
  prestada). tests/test_pool.py: PruebasTransacciones (4) + 1 en
  PruebasConexionBD (pool_reset_session); el inventario clasifica cada
  método por el SQL que manda (21 escrituras, 18 lecturas). Con MariaDB:
  autocommit = 0 (antes 1) y 2 nuevas (lo no confirmado se descarta;
  rollback deshace los dos pasos). Las conexiones auxiliares de
  PruebasPoolEnBD y PruebasEsquemaEnBD fijan autocommit = True. Suite 321
  (276 + 45 omitidas). Contraprueba (git stash de db_config.py y
  conexion_bd.py): fallan 2, pasan a propósito 3 (las de los DAO); al
  quitar a propósito el commit() de ProductoDAO.actualizar, la prueba lo
  detecta. Opcional del dueño: test_pool, test_esquema y test_otp_bd con
  PETCONNECT_PRUEBA_BD=1.
- 4.8 HECHO el 08/11/2026 (A-13; commit 979cdf3, solo backend; no toca
  la BD; CIERRA NC-007). Decisión del dueño: opción A, el teléfono sigue
  en texto plano (usuarios.telefono lo llena solo la consola;
  solicitudes.telefono, el de adopción, nadie lo lee aún) y se corrigió
  el comentario de api.py. Opción B (cifrarlo) descartada por ahora:
  varchar(20) no alcanza (~120 caracteres cifrado), migrar filas y, con
  A-16 abierto, perder la FERNET_KEY dejaría ilegibles los teléfonos.
  security/crypto.py: decrypt() lanza InvalidToken si no puede descifrar
  ("" y None se devuelven igual); decrypt_estricto ya no existe (los OTP
  usan decrypt en otp/servicio.py). api.py ya no importa encrypt/decrypt.
  tests/test_seguridad.py: PruebasDescifrado (5); las 2 de
  decrypt_estricto de test_otp_bd.py se movieron ahí. Suite 314 (271 +
  43 omitidas). Contraprueba (git stash de crypto.py): fallan 4 (texto
  no Fernet, token alterado, otra clave y
  test_codigo_ilegible_se_borra_y_no_se_reenvia del OTP), pasan a
  propósito 2 (ida y vuelta, vacío/None).
- 4.7 HECHO el 08/11/2026 (A-24; commit 3606c5d, solo web; no toca API
  ni BD; no cierra NC). Decisión del dueño: opción A, solo el 401 cierra
  la sesión (404 "Usuario no encontrado" no: puede venir de una API mal
  desplegada y el token vence en 24 h). getPerfil() en src/services/api.js
  (GET /auth/me); src/utils/sesion.js: revalidarSesion({ leerToken,
  obtenerPerfil }) → "cerrar" (401 o datos sin token), "mantener" (503,
  502, 500, 404, red caída), "actualizar" con el perfil (200) o "ignorar"
  si el token cambió mientras llegaba la respuesta. AuthContext.jsx la
  llama en un useEffect al iniciar (con bandera "vigente" por StrictMode,
  que monta dos veces en desarrollo: se ven 2 llamadas a /auth/me) y
  muestra la sesión guardada mientras tanto. El 401 a mitad de sesión lo
  sigue tratando FormularioSolicitud.jsx (no se cerró sesión ante
  cualquier 401 para no perder su mensaje). tests/sesion.test.js (9);
  npm test 51/51, lint 0 errores (2 avisos viejos de only-export-
  components), build OK. Contraprueba (git stash de api.js y
  AuthContext.jsx): fallan 5, pasan a propósito 4. Navegador a 375 px
  con la API del dueño: token falso → 401 → sesión borrada.
- 4.6 CORREGIDO el 08/11/2026 (d040676 y f2214e6): verificar() lee la
  fila antes de reservar el intento; el dueño corrió test_otp_bd.py con
  MariaDB: 48/48. Sigue pendiente confirmar que aplicó la migración
  otp_pendientes en su BD real (sin ella la API nueva no arranca).
- 4.6 HECHO el 07/11/2026 (A-12; commits 9ccd379 y 24ed52c, solo
  backend; NC-003 sigue abierta hasta el 4.17 y el 4.12). Decisiones del
  dueño: opción A (tabla otp_pendientes), código cifrado con Fernet (con
  hash no se podría reenviar el mismo código, A-09), datos del registro
  pendiente borrados al verificar, al bloquearse y al vencer, _mx_cache
  de 1.000 dominios (MX_CACHE_MAXIMO, LRU con candado).
  otp/servicio.py: AlmacenOTP(proposito, repositorio) tiene las reglas;
  OtpDAO (dao/otp_dao.py, 7 métodos, deja subir errores) en la API y
  RepositorioMemoria (candado) en las pruebas: _importar_api() de
  test_errores.py pasa los almacenes de la API a un RepositorioMemoria
  compartido (las pruebas de rutas simulan la BD). test_errores.py pone
  FERNET_KEY y JWT_SECRET de prueba al importarse. El intento se reserva
  antes de comparar (UPDATE ... intentos < 5) y se devuelve si acierta;
  crear un código borra todos los vencidos; api._preparar_otp() al
  arrancar los borra y, sin la tabla (errno 1146), avisa y no arranca.
  decrypt_estricto nuevo en security/crypto.py (el 4.8 ya no puede
  "quitar Fernet": lo usan los OTP). CORREO_MAX = 120 en _validar_correo.
  /register/resend ahora usa la BD (sin BD, 503). tests/test_otp_bd.py
  (47; 16 con PETCONNECT_PRUEBA_BD=1 en petconnect_prueba_otp y
  petconnect_prueba_otp_migracion); test_esquema 34 tablas; test_pool
  39 métodos de DAO. Suite 310 (267 + 43 omitidas). Contraprueba en el
  scratchpad (git archive + pruebas nuevas): todo viejo → 20 != 5 en la
  carrera y 100 vencidos sin borrar; solo api.py viejo → 5 fallan;
  _mx_cache viejo → 1.500 != 1.000. PENDIENTE DEL DUEÑO: aplicar
  sql/migraciones/2026-11-07_otp_pendientes.sql con respaldo (sin eso la
  API nueva no arranca) y, opcional, las pruebas con MariaDB. Hallazgo:
  la política (A.11) dice que el registro pendiente "nunca llega a la
  base de datos"; corregirla obliga a subir la versión (C.9): decisión
  D.7 del borrador, pendiente del dueño.
  CORRECCIÓN 08/11/2026: el dueño corrió test_otp_bd.py con MariaDB y
  la carrera de 20 intentos dio 4 != 5. Causa: quien ganaba un intento
  leía la fila DESPUÉS y un 6.º intento (bloqueado) ya la había borrado
  → "no_pendiente" sin comparar (aunque trajera el código correcto).
  verificar() ahora lee la fila ANTES de reservar. Prueba nueva sin
  MariaDB (test_quien_gana_un_intento_compara_aunque_otro_borre_la_fila,
  los ganadores se demoran 0,2 s); con el código anterior da 0 != 5.
  test_otp_bd.py: 48. Suite 311 (268 + 43 omitidas). Repetida por el
  dueño con PETCONNECT_PRUEBA_BD=1: 48/48 OK (08/11/2026).
- 4.5 HECHO el 07/11/2026 (A-11; commit 9c417de, solo backend; NC-003
  sigue abierta). Decisiones del dueño: pool de 10 (DB_POOL_SIZE en
  .env.example, vacío = 10, de 1 a 32; otro valor detiene el arranque),
  consola y seed.py en el mismo pool, 4.15 aparte. ConexionBD (sigue
  Singleton) presta conexiones de un MySQLConnectionPool creado una sola
  vez; si está lleno espera hasta 5 s (ESPERA_MAXIMA_SEGUNDOS) y devuelve
  None → 503; el log solo trae tipo y errno. conexion_y_cursor(conexion_bd,
  dictionary=False) es el try/finally: cierra cursor y devuelve la
  conexión aunque haya error; sin BD lanza InterfaceError (503). La usan
  los 32 métodos de los DAO (commit/rollback sobre la conexión prestada;
  ConexionBD.commit/rollback ya no existen) y las 4 consultas de api.py.
  _get_conn() → _verificar_bd() (pide y devuelve enseguida). El punto de
  parche de las pruebas sigue siendo _conexion_bd.obtener_conexion.
  tests/test_pool.py (25; 3 con PETCONNECT_PRUEBA_BD=1, base temporal
  petconnect_prueba_pool): PETICIONES debe cubrir TODA ruta del inventario
  (ruta nueva → agregarla ahí y "test_pool.py" en RUTAS_PUBLICAS/PRIVADAS
  de test_endpoints.py) y cada DAO nuevo entra solo en la revisión de
  fugas (ojo: el número de métodos está fijo en 32). Suite 256 (229 + 27
  omitidas). Contraprueba en el scratchpad (copia con tar + git archive):
  viejo → fallan 20 de 22; solo api.py viejo → 36 subcasos; solo DAO
  viejos → 96 + 21; seed/main viejos → su prueba. PENDIENTE DEL DUEÑO
  (opcional): correr las 27 de MariaDB con PETCONNECT_PRUEBA_BD=1.
  Hallazgo: paginación e índices de NC-003 no tenían ítem → 4.17
  (agregado con el sí del dueño; el 4.12 espera a 4.6 y 4.17).
- 4.4 HECHO el 07/11/2026 (A-31 segunda parte; A-31 RESUELTO; commit
  37f8126, solo tests/test_endpoints.py; api.py sin tocar). Inventario
  ruta x caso y NC x prueba antes de escribir: huecos en /api/auth/me (sin
  ninguna prueba), productos (200 y 404), filtro de la lista de adopción
  sin MariaDB, login (vacíos, correo inexistente = contraseña mala,
  migración del hash NC-001), login/verify y verify (sin pendiente,
  vencido, 404, 503 sin gastar el código, 500 al crear), register (vacíos,
  409, 503) y validar-correo. 31 pruebas con BD, DNS y correo simulados
  (_BaseEndpoints: parchea _conexion_bd.obtener_conexion, api.UsuarioDAO,
  enviar_codigo y enviar_bienvenida). Inventario vivo: RUTAS_PUBLICAS y
  RUTAS_PRIVADAS deben ser iguales a app.url_map (/api/...), cada ruta debe
  aparecer en el código (ast, sin docstrings ni comentarios) de los
  archivos de pruebas anotados, y las privadas responden 401 sin token. OJO:
  TODA RUTA NUEVA debe anotarse ahí con sus pruebas o la CI falla.
  Suite 231 (207 + 24 omitidas). Contraprueba: script en el scratchpad que
  copia el backend con git archive y aplica 28 roturas de a una (todas
  detectadas). NC-001, NC-008 y NC-009 con nota de regresión en la GA9
  (siguen cerradas). Hallazgo: /api/productos/<id> no filtra activo →
  ítem 4.16 (decisión del dueño: no tocar api.py en el 4.4). Para correr
  un solo archivo: python -m unittest discover -s tests -p "test_x.py"
  (con "python -m unittest tests.test_x" no encuentra test_errores).
- 4.3 HECHO el 07/11/2026 (A-31, primera parte; commit 8802815; no cierra
  NC). .github/workflows/ci.yml: on push (cualquier rama) + workflow_dispatch;
  permissions: contents: read; 3 jobs en ubuntu-latest con timeout-minutes: 10
  y working-directory propio: backend (setup-python@v7, "3.14", cache pip;
  python -m pip install -r requirements.txt; python -m unittest discover -s
  tests -v), web y movil (setup-node@v7, "24", cache npm con el
  package-lock.json de cada uno; npm ci + lint + test + build en la web;
  npm ci + test + npx expo export --platform web en el móvil). checkout@v7
  con persist-credentials: false. Sin secretos ni .env. Se eligió v7 (y no
  v4/v5 de la nota anterior) porque las v4/v5 usan Node 20, que GitHub retira;
  las v7 salieron en junio-julio de 2026 sin cambios que afecten. Validado sin
  push: YAML leído con el paquete yaml de PetConnect.Mobile/node_modules y
  comandos corridos en una copia de git archive HEAD fuera del repo (venv
  nuevo, npm ci desde cero): backend 200 (176 + 24 omitidas), web lint 0
  errores (2 avisos only-export-components de siempre) + 42/42 + build, móvil
  35/35 + export (~10 s). Los package-lock ya traen los binarios linux-x64
  (oxlint, rolldown, tailwind, lightningcss). Revisión de mayúsculas de los
  imports (JS relativos y Python locales): sin problemas. FALTA: la primera
  ejecución real en GitHub, al hacer el push final; si falla, revisar la
  pestaña Actions del repositorio (cada job dice qué paso falló). OJO: el hook
  de secretos bloquea cualquier comando que contenga el texto ".env" (A-40);
  para buscar esos archivos usar el patrón ".e*".
- 4.2 HECHO el 07/11/2026 (A-19, NC-011 CERRADA; commit 06a422d, solo
  backend). dao/proveedor_dao.py: _BUSCAR_POR_NOMBRE lleva
  "nombre LIKE %s ESCAPE '!' AND activo = TRUE" y buscar_por_nombre escapa
  !, % y _ con _escapar_like (se eligió '!' y no '\' por el modo
  NO_BACKSLASH_ESCAPES de MariaDB). tests/test_proveedores.py (5) simula la
  conexión (dao._conexion_bd = MagicMock) tras _importar_api(), así config/
  no carga el .env. Suite backend: 200 pruebas (176 correctas, 24 omitidas
  sin MariaDB). CP-013 sigue "en seguimiento": el filtro por tipo no existe
  (ni columna ni rutas de proveedores en la API). Los otros DAO
  (mascota, producto, usuario) también usan LIKE f"%{termino}%" sin escapar:
  pendiente sin ítem, de baja prioridad (preguntar al dueño).
- 4.1 HECHO el 07/11/2026 (A-17, NC-004 CERRADA, CP-003 aprobado). La
  política de contraseñas vive en petconnect.Backend/security/politica.py:
  validar_contrasena(password) -> mensaje | None, con LARGO_MIN = 8,
  LARGO_MAX = 64 (y 72 bytes), mayúscula A-Z, minúscula a-z, número y un
  especial de CARACTERES_ESPECIALES = '@ # ! " $ & ? ¡ - _ * .' (mensajes sin
  tildes). api.py la importa; _validate_password queda como alias porque lo
  llama Documentacion/Evidencias-GA9-AA2-EV01/pruebas_aa2.py. Importar
  security/ exige FERNET_KEY y JWT_SECRET (crypto.py y jwt_helper.py):
  tests/test_politica.py pone claves de prueba antes. La consola (4.11) debe
  usar esta misma función. Web: src/utils/contrasena.js (REGLAS_CONTRASENA
  {id, label, mensaje, test} y validarContrasena); RegisterModal.jsx muestra
  6 reglas. Móvil: copia en src/utils/contrasena.js (la prueba exige que sea
  igual a la de la web y compara límites con politica.py); RegisterScreen.js
  valida antes de registerUser y muestra la pista bajo el campo. Las utilidades
  JS cuentan con [...p].length (un emoji = 1, como Python) y usan TextEncoder
  para los bytes (Hermes lo trae desde RN 0.74). Revisado a 375 px en la web
  y en el export web del móvil; con la API real y en el emulador es opcional.
- Hechos: 0.1, 1.1, 1.2, toda la fase 2 (2.1 a 2.9), el 3.1 (3 partes: API +
  BD, web y móvil; ver git log), el 3.2, el 3.3 y el 3.4 (3 partes: backend,
  web y móvil; A-22 resuelto). NC-005 y NC-009 cerradas el 06/11/2026.
  El 3.5 está HECHO (3 partes el 06/11/2026: API + DAO, web y móvil; A-20 y
  R05 con la contingencia completa). La web la probó el dueño con la API
  real (cuenta 18) y el móvil en el emulador (cuenta 17, 07/11/2026). El
  3.6 está HECHO (3 partes el 07/11/2026: API + BD, web y móvil) y con él
  TODA la Fase 3. Cuentas 17, 18 y 19 del dueño: las tres en
  acepta_datos = 1 con fecha, pero con la versión 1.0: desde que el dueño
  reinicie la API con el código del 3.6, TODAS las cuentas deben autorizar
  otra vez (1.1) al iniciar sesión. Eso es lo esperado, no un error.
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
  tests/sin-salud-inventada.test.js, tests/casilla-autorizacion.test.js y,
  desde el 3.6, tests/solicitudes.test.js: 29 pruebas). La web para revisar con la API
  apagada: el proxy de Vite responde 502 sin cuerpo.
- Pruebas móvil (desde el 3.4 parte 3): npm test en PetConnect.Mobile
  ("node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON --test", sin
  dependencias; 27 pruebas en tests/*.test.mjs desde el 3.6 parte 3). Las pruebas son .mjs y el
  package.json NO tiene "type": "module" (cambiarlo puede romper Expo/Metro);
  Node 24 importa los .js de src/ con import y la bandera calla el aviso.
  Solo sirven para código JS puro (src/utils/) o para leer el texto de las
  pantallas: Node no entiende JSX.
- Formularios demo (3.2, A-21, hecho el 06/11/2026, solo web; desde el 3.6
  parte 2 solo el CHECKOUT sigue en demo: PetDetail y Contacto envían de
  verdad con FormularioSolicitud.jsx): componente
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
  antes en RegisterModal.jsx), y en el móvil CasillaAutorizacion.js y
  LoginScreen.js (desde el 3.5; antes en RegisterScreen.js), y el borrador .md.
- "Por actualizar" está vacía.
- Pruebas: 179 (155 OK + 24 omitidas que necesitan MariaDB), desde el 3.6 parte 1.
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
  en CasillaAutorizacion.js del móvil y de la web (desde el 3.5), PoliticaDatos.jsx
  y el borrador .md)
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
- Pendientes que dejó el 3.1 (fuera de NC-005): el 3.5 (hecho el 06/11/2026);
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
- NC-007 cerrada el 08/11/2026 (4.8, decrypt() que falla). NC-006 cerrada el
  04/11/2026. NC-002 cerrada el 05/11/2026.
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
  Si cambia el texto legal: este componente, CasillaAutorizacion.js del móvil,
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

3.5 parte 3 (móvil, A-20, R05, hecha el 06/11/2026):
- src/components/CasillaAutorizacion.js (props marcada, onCambiar, pista =
  accessibilityHint, onErrorEnlace(mensaje)): ÚNICO lugar del móvil con el
  texto B.1, el enlace aparte "Leer los términos y condiciones que aceptas:
  ..." (Linking.openURL(POLITICA_URL)) y el aviso B.2 con el correo de
  atención. Lo usan RegisterScreen.js (sin cambio visible) y LoginScreen.js.
  Primer archivo de src/components/ del móvil.
- src/utils/peticiones.js (JS puro, para que Node lo pruebe: api.js importa
  react-native y Node falla con "Unexpected token 'typeof'"):
  errorDeApi(mensaje, status, data) → Error con status y
  requiereAutorizacion (solo data.requiere_autorizacion === true);
  cuerpoLogin(email, password, aceptaDatos) → acepta_datos: true solo con
  true. api.js los usa (apiFetch y loginUser(email, password, aceptaDatos)).
  AuthContext.js NO cambió: LoginScreen llama a loginUser directamente y
  luego a iniciarLogin(email); el error de verificarLogin llega tal cual.
- LoginScreen.js: estados avisoAutorizacion (mensaje del 403) y aceptaDatos
  (false). Paso "Autoriza el uso de tus datos" en un ScrollView: casilla,
  zona aria-live con el error, "Autorizar y continuar" (Pressable; repite
  loginUser(email.trim(), password, true) e iniciarLogin), "Cancelar"
  (desactivado mientras se envía; borra la contraseña) y la línea B.3 "Si no
  quieres autorizarlo, escríbenos a ... y borraremos tu cuenta." con un
  enlace aparte "Escribir al correo de atención" (mailto). Sin marcar:
  MENSAJE_SIN_AUTORIZACION y 0 peticiones. 403 en /login/verify → borra el
  código, cancelarLogin() y vuelve a la casilla sin marcar. Orden: código
  (pendingLoginEmail) > casilla > formulario.
- Pruebas: tests/peticiones.test.mjs (5) y tests/casilla-autorizacion.test.mjs
  (4, leen el texto). Contraprueba (git stash de api.js y las 2 pantallas +
  sin el componente): fallan 5 de 9 dejando peticiones.js (pasan a propósito
  las 4 que solo prueban ese archivo nuevo); sin peticiones.js fallan todas.
  npm test 16/16; npx expo export --platform web OK.
- Revisado a 375 px con la API simulada (window.fetch reemplazado, correo
  inventado ana@ejemplo.test). OJO: el puerto 8090 lo tenía un http.server
  de otra sesión (10:37) sirviendo la misma carpeta dist; se usó ese en
  http://127.0.0.1:8090 (preview_start le asignó 8091 al nuevo, pero python
  igual pedía el 8090 y no arrancó). /impeccable audit 14/20 (pulido
  opcional: el mensaje del 403 en gris #64748b sobre #f2f2f2 ≈ 4,3:1; enlaces
  de 44 px y no 48 dp; sin android_ripple; colores fijos sin modo oscuro, como
  toda la app).
- Prueba con la API real en el emulador Pixel_7 (dueño, 07/11/2026, API de
  las 13:14:48 del 06/11, la única, posterior a api.py 11:15:50): la cuenta 17
  (acepta_datos = 0) inició sesión, vio la casilla, la marcó ("Cancelar" se
  vio gris mientras se enviaba), escribió el código y quedó con
  acepta_datos = 1 y fecha 2026-11-07 01:32:37 (SELECT id_usuario,
  acepta_datos, fecha_autorizacion_datos FROM usuarios WHERE id_usuario >= 17:
  17, 18 y 19 en 1 con fecha). El caso "sin marcar" con la API real no se
  capturó: lo cubren las pruebas y la API simulada.

3.6 parte 1 (API + BD, A-21, hecha el 07/11/2026; plan de 3 partes aprobado
por el dueño: API + BD, web, móvil):
- Decisiones del dueño (07/11/2026): adopción Y contacto; solo con sesión
  iniciada (nombre y correo salen de la cuenta, no se guardan otra vez);
  solo en la BD (el equipo las lee con SQL; ni correo ni pantalla del dueño
  de la mascota: las 6 mascotas son del usuario 5, de correo ajeno); mensaje
  + teléfono OPCIONAL (solo adopción); SIN casilla aparte: aviso corto B.5
  (vale la autorización de la cuenta con la política 1.1); textos v1.1 de
  A.4, A.5 punto 7 y A.11 aprobados; VERSION_POLITICA_DATOS = "1.1" desde
  esta parte; móvil como parte 3.
- BD: tabla `solicitudes` (id_solicitud, id_usuario, tipo enum
  adopcion/contacto, id_mascota NULL, telefono varchar(20) NULL, mensaje
  varchar(1000), version_politica_datos NOT NULL, fecha_envio datetime) con
  chk_solicitud_tipo (adopción exige mascota; contacto sin mascota ni
  teléfono) y ON DELETE CASCADE desde usuarios y mascotas. En schema.sql
  (33 tablas) y en sql/migraciones/2026-11-07_solicitudes.sql (solo el
  CREATE TABLE IF NOT EXISTS, misma definición; lo revisa test_esquema).
  sql/README.md explica cómo aplicarla y cómo leer las solicitudes.
- dao/solicitud_dao.py: dueno_de_mascota_en_adopcion(id) (id_usuario o
  None; solo estado en_adopcion) e insertar(id_usuario, tipo, id_mascota,
  telefono, mensaje, version, fecha) → id. NO se traga los errores (los
  deja subir: 503/500 de los manejadores globales); sin conexión lanza
  InterfaceError (→ 503). Modelo para el 4.15.
- api.py: VERSION_POLITICA_DATOS = "1.1"; MENSAJE_MIN/MAX = 10/1000;
  teléfono: números, espacios y un + al inicio, 7 a 15 dígitos, máx. 20;
  _cuenta_que_envia() (UsuarioDAO.consultar_por_id del token: 404 si no
  existe, 403 "Cuenta inactiva o bloqueada", 403 con
  "requiere_autorizacion": true y el mensaje "Para enviar tu solicitud
  debes autorizar la versión vigente de la política de datos. Cierra sesión
  y vuelve a iniciarla" si no tiene la 1.1). POST /api/solicitudes/adopcion
  {id_mascota (int, no bool), mensaje, telefono opcional} y POST
  /api/solicitudes/contacto {mensaje} (ignora mascota y teléfono). Orden:
  limitador (LIMITE_AUTH, 5/min por IP) → @require_auth → validar cuerpo
  (400) → cuenta → mascota en adopción (404 "Mascota no encontrada") y no
  propia (400) → insertar → 201 {"message": "Solicitud enviada" | "Mensaje
  enviado", "id"}. Los mensajes nuevos llevan tildes.
- Pruebas: tests/test_solicitudes.py (15 de rutas con UsuarioDAO y
  SolicitudDAO simulados y token de api.generate_token; 4 del DAO con
  conexión simulada); test_esquema.py: tabla (sin BD), migración (sin BD,
  3) y con MariaDB test_solicitudes_con_la_base_real (PruebasEsquemaEnBD) y
  PruebasMigracionSolicitudesEnBD (2, base "petconnect_prueba_solicitudes");
  test_limite.py con las 2 rutas; test_login_datos.py y
  test_registro_datos.py con VERSION = "1.1" (y el caso "versión 1.0" debe
  autorizar otra vez); test_logs.py lee api.VERSION_POLITICA_DATOS.
  Contraprueba (git stash de api.py y schema.sql): fallan 27; pasan a
  propósito las 4 del DAO y 2 de la migración (archivos nuevos).
- Borrador de la política en 1.1 (mismo nombre de archivo ...v1.0-BORRADOR
  .md, para no romper enlaces): A.4 (mensajes + teléfono), A.5 punto 7,
  A.6 (sin casilla aparte), A.11, A.14, B.3 (+2 filas), B.5 (avisos de
  adopción y contacto), C.12 a C.15 y una fila en la Parte E.
- BD real del dueño (07/11/2026): migración APLICADA (SHOW COLUMNS FROM
  solicitudes: las 8 columnas como schema.sql) y respaldo
  petconnect-2026-11-07-3.6.sql en C:\Users\goku8\Respaldos\ (hecho justo
  después de la migración). Las clases con MariaDB
  (PETCONNECT_PRUEBA_BD=1: tests.test_esquema.PruebasEsquemaEnBD y
  tests.test_esquema.PruebasMigracionSolicitudesEnBD) no se corrieron:
  opcional.
- TROPIEZO (07/11/2026), igual al del 3.5: tras reiniciar la API, el
  puerto 5000 lo seguía atendiendo una API VIEJA del 06/11 13:14 (PID
  45052 → 39180, sin las rutas del 3.6) junto a la nueva (04:14): la ruta
  respondía 404 "Recurso no encontrado". El dueño la cerró con
  Stop-Process -Id 45052,39180. Antes de cada prueba con la API real:
  Get-NetTCPConnection -LocalPort 5000 -State Listen (un solo proceso) y un
  POST sin token a /api/solicitudes/contacto debe responder 401 (no 404).
  Cada API sale como dos procesos (el python del .venv lanza un hijo).
- La GA9 no tiene una NC para A-21: no se tocó.

3.6 parte 2 (web, A-21, hecha el 07/11/2026):
- src/components/FormularioSolicitud.jsx (props tipo "adopcion" |
  "contacto", mascota {id, name} solo adopción, onCerrar opcional): ÚNICO
  formulario de solicitudes de la web y único lugar con el aviso B.5. Sin
  sesión NO muestra campos: texto + "Inicia sesión para enviar" (openLogin)
  y "Crear cuenta" (openRegister). Con sesión: "Envías como {nombre}
  ({correo})" (de la cuenta, solo para leer), teléfono opcional (solo
  adopción; type="tel", autoComplete="tel"), mensaje (textarea con contador
  n/1000 y ayuda "Entre 10 y 1000 caracteres"), aviso B.5 (enlace a
  /politica-de-datos en pestaña nueva y mailto) y "Enviar solicitud" /
  "Enviar mensaje" ("Enviando…" y desactivado mientras se envía). Valida
  primero en el navegador (0 peticiones si falla: foco al campo y
  aria-invalid). Estado "enviada" SOLO tras la respuesta ok (201): recuadro
  verde role="status", foco al título, "Tu solicitud quedó guardada con el
  número N...". Error de la API: role="alert" con foco (en el celular
  quedaba fuera de la pantalla), sin borrar lo escrito; 401 → "Tu sesión
  venció..." y 403 con requiereAutorizacion → mensaje de la API; los dos con
  "Volver a iniciar sesión" (logout + openLogin; lo escrito se conserva
  mientras la página siga abierta).
- src/utils/solicitud.js: validarMensaje y validarTelefono (mismas reglas
  que api.py; JS puro para que Node lo pruebe; COPIARLO al móvil).
- api.js: enviarSolicitudAdopcion(idMascota, mensaje, telefono) →
  {id_mascota: Number, mensaje, telefono} y enviarMensajeContacto(mensaje)
  → {mensaje}; el token lo pone apiFetch.
- PetDetail.jsx: "Solicitar Adopción" abre <FormularioSolicitud
  tipo="adopcion" mascota={pet} onCerrar>. Contact.jsx: <FormularioSolicitud
  tipo="contacto" /> en la columna izquierda. Ninguna importa AvisoDemo
  (sigue solo en Checkout.jsx, A-26).
- PoliticaDatos.jsx: VERSION_POLITICA = "1.1"; resumen, A.4 (mensajes y
  teléfono), A.5 punto 7, A.6 (sin casilla aparte) y A.11 como el .md.
- tests/solicitudes.test.js (9): validación, las dos funciones (token,
  cuerpo sin nombre ni correo, 403/401/404), páginas sin demo y checkout en
  demo, "enviada" solo tras el await, aviso B.5, y la MISMA versión en
  PoliticaDatos.jsx, api.py y el borrador .md (si se sube una, la prueba
  obliga a subir las tres). Contraprueba (git stash de api.js, PetDetail,
  Contact y PoliticaDatos): fallan 5 de 9; pasan a propósito las 2 de
  validación y 2 que leen FormularioSolicitud.jsx (archivos nuevos).
  npm test 29/29, lint 0 errores (los 2 avisos de siempre), build OK.
- Revisado a 375 px con la API simulada (window.fetch reemplazado, sesión
  inventada ana@ejemplo.test, mascota inventada): sin sesión, vacío (0
  peticiones), teléfono con guiones (0 peticiones), 403 (mensaje + botón,
  nada "enviada", texto conservado), 201 (recuadro verde con el número),
  401 en Contacto → "Volver a iniciar sesión" cierra sesión y abre el login;
  /politica-de-datos dice 1.1; sin desplazamiento horizontal.
  /impeccable audit 16/20 (detector sin hallazgos; pulido opcional: al abrir
  o cerrar el formulario de adopción el foco cae en body, ya anotado en el
  3.2; colores fijos sin modo oscuro ni tokens; el correo de atención
  repetido en 7 archivos de la web).
- Probado por el dueño con la API real (07/11/2026, API de las 04:14, la
  única tras cerrar la vieja): con su sesión en la web abrió Luna
  (/adopcion/3), escribió teléfono y mensaje y vio "Solicitud enviada... con
  el número 1". Como la API solo responde 201 después de guardar la fila y
  exige la autorización 1.1, eso confirma la fila en la BD y que la cuenta
  ya tiene la 1.1 (primera prueba real del cambio de versión, C.9). El
  mensaje de contacto y el conteo con SELECT tipo, COUNT(*) no se
  capturaron (opcional; lo cubren las pruebas y la API simulada). La ficha
  de Luna (BD del dueño) dice "Vacunada, esterilizada y desparasitada":
  sigue pendiente de validación veterinaria (3.4). El pie de la web sigue
  con el contacto inventado (pendiente sin ítem).

3.6 parte 3 (móvil, A-21, hecha el 07/11/2026):
- Decisión del dueño (07/11/2026): Contacto como PESTAÑA NUEVA. Pestañas:
  Catalogo (Tienda), Adopcion, Contacto y Perfil.
- src/components/FormularioSolicitud.js (props tipo "adopcion" | "contacto",
  mascota {id, name} solo adopción, onCerrar opcional): ÚNICO formulario de
  solicitudes del móvil y único lugar con el aviso B.5 (una prueba lo exige).
  Sin sesión: texto + "Inicia sesión para enviar" y "Crear cuenta". Con
  sesión: "Envías como {nombre} ({correo})", teléfono opcional (solo
  adopción, phone-pad, máx. 20), mensaje multiline con contador n/1000,
  aviso B.5 y dos filas de enlace aparte (política con
  Linking.openURL(POLITICA_URL) y mailto al correo de atención). Valida con
  utils/solicitud.js antes de llamar a la API (0 peticiones si falla; borde
  rojo en el campo). "enviada" SOLO tras el 201 (recuadro verde con el
  número). 401 → "Tu sesión venció..." y 403 con requiereAutorizacion →
  mensaje de la API; los dos con "Volver a iniciar sesión" (logout y abre el
  modal). Sin status (fetch falló) → mensaje en español. Nunca borra lo
  escrito. Botones de 48 px; error en aria-live="polite" con role="alert".
- AppNavigator.js: pestaña Contacto (ContactScreen.js) y pantalla
  "IniciarSesion" en el Stack raíz con presentation "modal": muestra el
  mismo LoginStack (Login + Register) ENCIMA de la ficha o de Contacto y se
  cierra sola (goBack) cuando hay user. Mandar a la pestaña Perfil se
  descartó: cerraba la ficha de la mascota y se perdía lo escrito.
- utils/solicitud.js = COPIA de la web (tests/solicitudes.test.mjs compara
  el código sin los comentarios //: si cambia una regla, cambiar api.py, la
  web y el móvil). utils/peticiones.js: cuerpoSolicitudAdopcion y
  cuerpoMensajeContacto (sin nombre ni correo). api.js:
  enviarSolicitudAdopcion y enviarMensajeContacto (token desde AsyncStorage
  en apiFetch).
- tests/solicitudes.test.mjs (11): validación, copia igual a la web,
  cuerpos, api.js, "enviada" solo tras el await, el catch no borra campos,
  401/403 y modal (no navega a Perfil ni a Main), B.5 completo y sin
  casilla, B.5 solo en el componente, ficha/Contacto/navegador lo usan.
  Contraprueba (git stash de api.js, peticiones.js, PetDetailScreen.js y
  AppNavigator.js): fallan 4; pasan a propósito 7 (archivos nuevos). npm
  test 27/27. npx expo export --platform web OK.
- Revisado a 375 px con la API simulada (http.server de launch.json
  "movil-web-export", puerto 8090; window.fetch reemplazado DESPUÉS de
  cargar, sesión inventada ana@ejemplo.test por el modal): sin sesión,
  vacío, teléfono con guiones (0 peticiones), 401 en Contacto → modal y el
  texto conservado, 403 en adopción (mensaje + botón, nada "enviada"), 201
  en las dos; sin desplazamiento horizontal. En la web exportada el enlace
  a la política abrió en la MISMA pestaña del panel (se pierde el estado de
  la app): solo afecta la web; en Android abre el navegador.
  /impeccable audit 14/20 (pulido opcional, igual que el resto del móvil:
  colores fijos sin modo oscuro, iconos emoji en las pestañas, enlaces de
  44 px y no 48 dp, sin android_ripple).
- Probado por el dueño con la API real en el emulador Pixel_7 (07/11/2026,
  tras reiniciar el PC: la RAM estaba llena, 0,6 GB libres, y el emulador
  del día anterior estaba congelado; npm run android no avanzaba). POST sin
  token → 401 (una sola API). Contacto: vacío → aviso rojo; enviado →
  "Mensaje enviado... número 2". Luna: 6 letras → aviso rojo; válido con
  teléfono → "Solicitud enviada... número 3". 401/403 reales y el SELECT no
  se capturaron (opcional).
- Pendiente sin ítem (visto en la prueba, web y móvil): el aviso rojo de
  validación queda visible mientras se corrige el campo, hasta volver a
  tocar "Enviar". Mejora sugerida: borrarlo al editar ese campo, en
  FormularioSolicitud.jsx y FormularioSolicitud.js a la vez. Preguntar al
  dueño antes.

Contexto del próximo paso (4.13 parte 2 de 3, A-03: web; no toca la BD):
- La API ya tiene POST /api/auth/logout (con @require_auth): suma 1 a
  usuarios.version_sesion y responde 200 {"message": "Sesion cerrada"};
  con un token que ya no vale responde 401. Cierra la sesión en TODOS
  los aparatos de la cuenta.
- Web hoy: AuthContext.jsx tiene logout() síncrono que solo borra el
  token y el usuario del navegador. Lo usan Header.jsx (botón "Cerrar
  sesión", líneas ~68 y ~117: escritorio y menú móvil) y
  FormularioSolicitud.jsx (~101, tras un 401: ahí el token ya no vale,
  así que NO debe llamar a la API; conviene un cierre "solo local").
- Plan sugerido: logoutEnServidor() en src/services/api.js (POST
  /auth/logout con el token); el botón llama a la API y SIEMPRE borra la
  sesión local, aunque la API responda 401, 503 o no haya red (que el
  usuario nunca quede "atrapado"). Decidir con el dueño si se avisa
  cuando la API no pudo cerrar la sesión en el servidor (p. ej. 503) y
  si el botón se desactiva mientras se envía. Prueba en tests/ (npm
  test) + contraprueba con git stash; npm run lint y npm run build;
  revisión a 375 px con /impeccable audit si cambia la interfaz.
- Para verlo con la API real, el dueño debe haber aplicado la migración
  2026-11-08_version_sesion.sql (sin ella python api.py no arranca).
- Después: parte 3 (móvil: ProfileScreen.js y FormularioSolicitud.js,
  logout() de src/context/AuthContext.js). Al terminarla, marcar [x] el
  4.13. Luego sigue el 4.14 (el 4.12 se salta hasta tener el 4.17). El
  4.18 y el 4.19 se pueden adelantar si el dueño quiere.

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

**Próximo ítem: 4.13, parte 2 de 3 (web)** (A-03): el botón “Cerrar sesión” de la web llama a `POST /api/auth/logout` y siempre borra la sesión local. La parte 1 (API y BD) quedó hecha el 08/11/2026 (`3c039ec`: `usuarios.version_sesion` en el token y comparada en `require_auth`, token sin correo, cuentas no activas → 401, la API no arranca sin la columna). Después, la parte 3 (móvil). El 4.12 se salta hasta tener el 4.17. Hallazgos abiertos: 4.18 (`/login` revela cuentas por tiempo) y 4.19 (consola: “Actualizar usuario” sin validar). **Pendiente del dueño:** aplicar las migraciones `2026-11-07_otp_pendientes.sql` (sin confirmar) y `2026-11-08_version_sesion.sql` con respaldo, y la decisión D.7 de la política. NC-003 sigue abierta hasta el 4.17 y la medición del 4.12.
