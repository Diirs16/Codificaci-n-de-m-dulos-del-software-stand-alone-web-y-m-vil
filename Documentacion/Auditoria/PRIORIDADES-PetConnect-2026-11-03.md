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
| [ ] | 2.7 | A-09 | — | No sobrescribir un registro pendiente vigente — **⏸ Por actualizar** (ver [sección](#por-actualizar)): se hace junto con el botón web “Reenviar código” | 🟢 | Segundo `/register` con el mismo correo → no cambia el hash pendiente |
| [ ] | 2.8 | A-10 | — | Imprimir el OTP solo si `APP_ENV=desarrollo`; nunca el correo en logs de producción | 🟢 | Con `APP_ENV` distinto, la salida no contiene el código |
| [ ] | 2.9 | A-07 | NC-002 | `/api/mascotas/<id>` solo devuelve `en_adopcion` (404 si no); ruta privada con `@require_auth` + dueño | 🟡 | Sin token y mascota no en adopción → 404 |

> Al cerrar 2.2 + 2.3 se cierra **NC-007** · 2.5 + 2.6 cierran **NC-006** · 2.9 cierra **NC-002**.

---

## Por actualizar

Ítems revisados pero en pausa porque su arreglo depende de algo que se va a construir primero. Cuando se retome,
se borra de aquí y se marca `[x]` en su fase.

### 2.7 · A-09 · Un segundo registro pisa la contraseña del primero — en pausa desde el 04/11/2026

**Por qué está en pausa:** el dueño del proyecto decidió crear un **botón web “Reenviar código”** en la verificación
del registro. Eso cambia la decisión del 2.7: si el reenvío tiene su propio botón, `/register` ya no necesita
reenviar nada y basta con no tocar el pendiente (la opción más simple).

**Lo que ya se revisó (sin tocar código):**
- `api.py`, `/api/auth/register`: `_otp_registro.crear(email, {...})` reemplaza sin preguntar el nombre, el hash de la
  contraseña, el código y el contador de intentos del registro pendiente. Si otra persona registra el correo de la
  víctima después de ella, la cuenta se crea con la contraseña de esa persona cuando la víctima usa el código nuevo.
  (El login pide código por correo, así que no entra sin el buzón de la víctima, pero ya tiene uno de los dos
  factores y la víctima queda con una contraseña que no conoce.)
- Arreglo propuesto: `AlmacenOTP.vigente(clave)` en `otp/servicio.py` (devuelve el pendiente si no venció; si venció,
  lo borra para que se pueda reemplazar). En `/register`, si hay un pendiente vigente, no se toca: ni el hash, ni el
  contador de intentos, ni el vencimiento. La respuesta es siempre la misma, `"Codigo enviado"`, para no revelar
  que alguien se está registrando con ese correo (A-14). Si alguien se registra dos veces seguidas, vale la
  **primera** contraseña.
- Opciones descartadas: responder 409 “revisa tu correo” (revela el registro en curso) y borrar el pendiente para
  crear uno nuevo (deja el problema igual).

**Cómo encaja el botón “Reenviar código”:**
- **Backend:** ruta nueva (nombre propuesto `POST /api/auth/register/resend`) que recibe solo `email`. Si hay pendiente
  vigente, reenvía **el mismo código** con el nombre del primer registro, sin reiniciar el contador de intentos.
  Si no hay pendiente, responde lo mismo (respuesta neutra). Con `@limiter.limit(LIMITE_AUTH)`.
- **Web:** `src/components/RegisterModal.jsx`, en el paso de verificación, junto a “¿No recibiste el código?”. Hoy
  ese enlace dice “Volver e intentar de nuevo” y manda a registrarse otra vez, cosa que con el 2.7 ya no cambiaría
  los datos. Función nueva en `src/services/api.js`, espera entre clics (ej. 60 s) y aviso de “Te reenviamos el código”.
- **Login:** `src/components/LoginModal.jsx` tiene el mismo enlace; decidir si el botón va también allí (otra parte).
- **Móvil:** después, en su propia parte (regla 3 de `CLAUDE.md`).

**Orden propuesto (una parte a la vez, con `/nueva-funcionalidad`):** (1) backend: 2.7 + ruta de reenvío + pruebas
(`tests/test_registro.py`: dos `/register` con contraseñas distintas → queda el hash del primero; reenviar no da
intentos nuevos; un pendiente vencido sí se reemplaza; el reenvío manda el mismo código); (2) web: el botón;
(3) móvil, si se quiere.

**Decisiones pendientes del dueño:** nombre de la ruta, cuánto esperar entre reenvíos, si reenviar alarga los
10 minutos de vencimiento y si el botón va también en el login.

**Riesgo que sigue abierto aunque se haga el 2.7:** otra persona puede mandar 6 códigos falsos a `/verify` con el
correo de la víctima; el bloqueo del 2.5 borra el pendiente y entonces sí puede registrarse con su contraseña. Es
más difícil (tiene que hacerlo en el par de minutos entre el registro y la verificación). Arreglo definitivo, sin
ítem todavía: que `/verify` vuelva a pedir la contraseña y la compare con el hash pendiente (toca web y móvil).

---

## Fase 3 — Datos personales y honestidad con el usuario

| ✔ | # | ID | NC | Qué | Esfuerzo | Listo cuando |
|---|---|---|---|---|---|---|
| [ ] | 3.1 | A-20 | NC-005 | Casilla de autorización **sin marcar** + enlace a política en web y móvil; la API rechaza sin ella; guardar fecha y versión; quitar `acepta_datos=True` por defecto | 🟡 | Registro sin casilla → 400; con casilla → `acepta_datos=1` y fecha guardada |
| [ ] | 3.2 | A-21 | — | Formularios de adopción, contacto y checkout: implementar el envío **o** rotular “Demo — no se envía” y deshabilitar | 🟢 (rotular) / 🔴 (implementar) | Ningún formulario dice “enviado” si no envió nada |
| [ ] | 3.3 | A-23 | NC-009 | Web: estados de carga/vacío/error en Catálogo, Adopción, detalles y Home; `data/*.js` solo para pruebas | 🟡 | Con la API apagada, la web muestra un error, no perritos falsos |
| [ ] | 3.4 | A-22 | — | Datos reales de vacunación/esterilización/tamaño (o no mostrarlos); corregir `seed.py` (tamaño en `color`); `/revision-contenido-mascotas` | 🟡 | La ficha no contradice la descripción; textos marcados `REVISAR-VETERINARIO` |

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

*Versión del 04/11/2026, ajustada después de poner en pausa el 2.7: salta los ítems de “Por actualizar”, agrega el
contexto del 2.8 y pide actualizar este prompt al terminar cada ítem.*

```text
Vamos a seguir corrigiendo PetConnect con la auditoría del 3/11/2026.

Lee primero:
- Documentacion/Auditoria/PRIORIDADES-PetConnect-2026-11-03.md (lista con casillas
  y "Próximo ítem")
- Documentacion/Auditoria/AUDITORIA-PetConnect-2026-11-03.md (detalle del A-xx)
- Documentacion/GA9-220501096-AA1-EV02-PetConnect.md (bitácora de NC)
- git log --oneline -12 (qué se hizo en sesiones anteriores; revisa con
  git status -sb si hay commits sin push)

Estado conocido (4/11/2026; si el git log muestra más ítems hechos, manda el git log):
- Hechos: 0.1, 1.1, 1.2, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6 (ver git log).
- En pausa: 2.7 (A-09), en la sección "Por actualizar" de PRIORIDADES. Se hará
  junto con un botón web "Reenviar código"; no lo tomes salvo que te lo pida.
- Pruebas: 71 (61 OK + 10 omitidas que necesitan MariaDB).
- NC-007 solo espera decrypt() (4.8). NC-006 cerrada el 04/11/2026.
- OTP (2.5): AlmacenOTP cuenta fallos (MAX_INTENTOS = 5); el 6.º intento borra el
  código y devuelve "bloqueado"; las rutas de verificación responden 429
  "Demasiados intentos fallidos..." (decisión del dueño). Compara con
  hmac.compare_digest sobre bytes. Sin threading.Lock (decisión: lo más simple).
- Limitador (2.6): api.limiter (Flask-Limiter 4.1.1), LIMITE_AUTH = "5 per minute"
  por IP en las 5 rutas de auth; 429 "Demasiadas peticiones. Espera un minuto...".
  _importar_api() lo deja APAGADO (limiter.enabled = False); una prueba que lo
  necesite lo enciende en setUp y lo reinicia (modelo: tests/test_limite.py).
- api.py ya tiene manejadores de error: 404/405 reales, 500 genérico con id_error
  (registra tipo y pila, sin el mensaje), 503 si no hay BD (BDNoDisponible), y
  _cuerpo_json()/_texto() para validar que los campos sean texto. Reutilízalos.
  /register valida el nombre con _validar_nombre() antes del DNS y la BD (2.4).
- tests/test_errores.py es el modelo para probar rutas: test_client, BD simulada
  apagada con mock, sin enviar correos (mock de api.enviar_codigo y, si hace falta,
  de api._validar_correo para no consultar el DNS). Su función _importar_api()
  importa api.py sin cargar el .env real (tests/test_otp.py la reutiliza con
  from test_errores import _importar_api). tests/test_correo.py es el modelo
  para el correo (mock de smtplib). Pendiente 4.14 para test_seguridad.py.
- Las rutas de prueba se registran al importar el archivo, no en setUpClass
  (Flask prohíbe registrar rutas después de la primera petición).

Contexto del próximo ítem (2.8, A-10, sin NC):
- api.py tiene 3 print() que se ejecutan cuando falla el envío del correo:
  /api/auth/login (~línea 429) imprime el código de inicio de sesión y el correo;
  /api/auth/register (~512) imprime el código de registro y el correo;
  /api/auth/verify (~560, bienvenida) imprime el correo. Los 3 incluyen además
  ({e}), el mensaje de la excepción, que puede traer la dirección (Ley 1581).
  Quien lea la consola o los logs ve códigos válidos y correos de usuarios.
- Meta: el código solo se muestra si APP_ENV=desarrollo (variable nueva,
  documentada en .env.example y vacía por defecto = no es desarrollo). Nunca
  el correo ni str(e): registrar con app.logger solo "fallo de envío" + ruta +
  type(e).__name__, como hace el manejador de 500.
- Decidir (con pros/contras): (a) APP_ENV nueva o reutilizar FLASK_DEBUG=1;
  (b) si en desarrollo se imprime también el correo o solo el código; (c) qué
  responde la API al cliente si el correo falla fuera de desarrollo (hoy dice
  "Codigo enviado" aunque no llegó nada: ¿503 "No pudimos enviar el código,
  intenta de nuevo"?). En /login ese mensaje sale después de comprobar la
  contraseña, así que no revela cuentas; en /register revisar A-14.
- Una función común (ej. _avisar_fallo_envio) evita repetir la lógica 3 veces y
  la reutilizará la ruta de reenvío del 2.7 cuando se haga.
- Prueba (archivo nuevo, ej. tests/test_logs.py): mock de api.enviar_codigo /
  api.enviar_bienvenida que lance una excepción cuyo mensaje traiga el correo;
  mock.patch.dict(os.environ) para APP_ENV; capturar stdout con
  contextlib.redirect_stdout y los logs con assertLogs. Sin APP_ENV (o con
  "produccion") ni la salida ni los logs contienen el código ni el correo; con
  APP_ENV=desarrollo aparece el código. /login necesita mock de UsuarioDAO con
  un usuario inventado y de la comprobación de contraseña. Sin BD, sin
  correos, sin DNS, limitador apagado (_importar_api).
- Como no tiene NC, en GA9 no hay fila que cambiar: solo el "Estado" bajo A-10
  en la AUDITORÍA.

Luego:
1. Toma el PRIMER ítem sin marcar ([ ]) en orden de fases, saltando los que
   estén en la sección "Por actualizar" (hoy el 2.7). Si dos seguidos son 🟢 y
   tocan el mismo archivo, puedes agruparlos (dímelo).
2. Antes de tocar código explícame en lenguaje sencillo qué está mal, el riesgo
   y tu plan (archivos, cambio, prueba de regresión), con opciones y pros/contras
   si hay varias. Si hay cambios sin commit relacionados, revísalos primero.
   Espera mi aprobación.
3. Implementa solo ese ítem respetando CLAUDE.md (secretos, SQL parametrizado,
   español, Ley 1581). No leas ni imprimas el .env. Si necesita una dependencia
   nueva (ej. Flask-Limiter en 2.6), pídeme permiso y fija la versión en
   requirements.txt.
4. Agrega la prueba de regresión y corre:
   - Backend: ../.venv/Scripts/python -m unittest discover -s tests -v
     (deben seguir pasando todas las anteriores más las nuevas)
   - Si toca la BD: también con PETCONNECT_PRUEBA_BD=1 (solo bases temporales)
   - Web (si cambió): npm run lint y luego npm run build
   Comprueba que la prueba nueva FALLA con el código viejo (contraprueba con
   git stash solo del archivo corregido) y dime cuántas fallan.
5. Si hay que tocar mi BD real, arrancar la API con mi .env o algo con
   contraseña, NO lo hagas tú: dame los comandos para Windows PowerShell 5.1
   (sin &&, un comando por bloque, indicando desde qué carpeta; MySQL está en
   C:\xampp\mysql\bin\), con respaldo previo fuera del repo, y espera mi captura.
6. Actualiza la fila de la NC en la bitácora GA9 (fecha y evidencia, incluida la
   contraprueba) y el "Estado" bajo el A-xx en la AUDITORÍA. Si con este ítem se
   completa una NC, cambia su estado a "Cerrada el dd/mm/2026".
7. Marca [x] en PRIORIDADES, actualiza "Próximo ítem" y el prompt de PRIORIDADES
   (estado conocido + contexto del siguiente ítem).
8. Commit con /guardar-partida: un commit por ítem, agregando archivos por ruta.
   No incluyas .gitignore, CLAUDE.md ni archivos sin seguimiento ajenos al ítem.
   No hagas push.
9. Explícame qué cambió (estilo /explicar), cómo verlo funcionando y déjame el
   prompt listo para el siguiente ítem, pegado completo en el chat.
```

**Próximo ítem: 2.8** (el 2.7 está ⏸ por actualizar: se retoma junto con el botón web “Reenviar código”; ver
[Por actualizar](#por-actualizar))
