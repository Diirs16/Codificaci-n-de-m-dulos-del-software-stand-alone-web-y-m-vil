# Auditoría técnica completa — PetConnect

| Dato | Valor |
|---|---|
| Fecha | 3 de noviembre de 2026 (inicio del Sprint 3 según el plan de pruebas) |
| Commit auditado | `910c7cd` (rama `main`, 15/10/2026) + archivos sin commit en el directorio de trabajo |
| Alcance | Backend Flask (API, consola, DAO, seguridad, correo, OTP), Web React/Vite, Móvil Expo, documentación y no conformidades (NC), historial de git, dependencias, Docker y configuración de Claude Code |
| Método | Revisión estática del código, pruebas dinámicas de la API con el cliente de pruebas de Flask (sin base de datos real y con claves de prueba), pruebas automáticas, linter, build, `npm audit` y revisión del historial de git |
| Guía usada | Auditoría previa de un compañero, **verificada punto por punto** (sección 4) |
| Documento complementario | [PRIORIDADES-PetConnect-2026-11-03.md](PRIORIDADES-PetConnect-2026-11-03.md): qué arreglar primero |

---

## 1. Resumen ejecutivo

**La base del proyecto es buena:** arquitectura por capas clara, SQL 100 % parametrizado, contraseñas con bcrypt
(costo 12) con migración automática, códigos OTP generados con `secrets`, dependencias de Python fijadas y un
historial de git **sin secretos**. El plan de pruebas del equipo es serio y ya había detectado la mayoría de los
problemas graves.

**El problema de fondo:** *el código va muy por detrás del plan.* Hoy empieza el Sprint 3 y, de lo que el cronograma
prometía para los Sprints 1 y 2, en el repositorio solo están NC-001 y NC-008. Siguen abiertas NC-002, NC-003,
NC-004, NC-005, NC-006, NC-007, NC-009, NC-010 y NC-011, y no existen ni `docker compose` funcional ni
integración continua. Además, **nadie puede levantar el proyecto desde el repositorio** porque el script de la base de
datos nunca se subió.

Esta auditoría **confirmó 12 de los 13 puntos principales** de la auditoría del compañero (el restante, NC-009,
no se puede verificar porque falta el esquema SQL), encontró **15 hallazgos nuevos** y amplió otros 4. Los más serios:

1. El correo se envía por TLS **sin verificar el certificado**: la contraseña de aplicación de Gmail puede ser interceptada.
2. Los formularios de **solicitud de adopción y de contacto** dicen “enviado” pero **no envían nada** (y recogen datos personales)
   *(resuelto el 06/11/2026, ítem 3.2: rotulados como demo y bloqueados; ver A-21)*.
3. Los códigos OTP y los correos de los usuarios se **imprimen en la consola** del servidor cuando el correo falla
   *(resuelto el 04/11/2026, ítem 2.8: ver A-10)*.
4. La ficha de la mascota muestra **“Pendiente de vacunación”** a mascotas cuya descripción dice “Vacunada”: información de salud contradictoria.
5. Los `Dockerfile` copiarían el `.env` **dentro de la imagen** (no hay `.dockerignore`) y la API no sería accesible desde el contenedor.
6. Mover la API a Gunicorn (la solución de NC-003) **romperá los OTP**, porque se guardan en la memoria de cada proceso.

### Conteo por severidad

| Severidad | Cantidad | Significado |
|---|---|---|
| 🔴 Crítica | 5 | Explotable hoy o impide usar/evaluar el proyecto |
| 🟠 Alta | 12 | Riesgo serio de seguridad, de datos personales o de credibilidad ante el instructor |
| 🟡 Media | 11 | Defectos reales con impacto acotado |
| ⚪ Baja | 13 | Orden, documentación y buenas prácticas |
| **Total** | **41** | |

---

## 2. Lo que está bien (no tocar)

| Aspecto | Evidencia |
|---|---|
| Arquitectura por capas | `modelo/`, `dao/`, `vista/`, `conexion/`, `config/`, `security/` bien separados |
| SQL parametrizado | Todas las consultas de `dao/` y `api.py` usan `%s`; no se encontró concatenación de SQL |
| Contraseñas | bcrypt costo 12 + migración de SHA-256 (`security/passwords.py`); comparación de SHA-256 con `hmac.compare_digest` |
| OTP | `secrets.randbelow` (`otp/servicio.py:19`) |
| Historial de git | Se revisaron los 10 commits: **ningún `.env`, llave ni contraseña** se ha subido; solo `.env.example` |
| Dependencias Python | Versiones fijadas en `requirements.txt` |
| Pruebas | 13 pruebas de regresión de NC-001/NC-008: **13/13 OK** |
| Web | `npm run build` OK; `npm run lint` sin errores (2 avisos menores); `lang="es"`; todas las imágenes tienen `alt` |
| Móvil | Valida la sesión al abrir (`/auth/me`) y muestra los errores de la API en pantalla (no esconde fallos) |
| CORS | Restringido a los orígenes locales conocidos |
| Plan de pruebas | Completo, honesto y con trazabilidad NC ↔ casos de prueba |

---

## 3. Hallazgos

Formato: **ID · Severidad · Título** — Dónde — Qué pasa — Evidencia — Cómo arreglarlo.
Las columnas **NC** relacionan el hallazgo con la bitácora oficial del plan de pruebas; **[A]** = estaba en la
auditoría del compañero; **[N]** = hallazgo nuevo de esta auditoría.

### 3.1 Bloqueantes de entrega

#### A-01 · 🔴 Crítica · El script de la base de datos no existe en el repositorio [A]
- **Dónde:** `README.md:279, 300, 321` menciona `PetConnect.sql`.
- **Qué pasa:** ese archivo **nunca** se subió (se revisó todo el historial: 0 archivos `.sql`). `seed.py` solo crea
  `categorias_producto`; las tablas `usuarios`, `mascotas`, `productos`, `proveedores_servicio`, `aplicaciones_vacuna`
  no se pueden crear. El instructor o un compañero que clone el repositorio **no puede ejecutarlo**.
- **Además:** sin el esquema no se puede verificar NC-009 (enum de `mascotas.estado`), NC-010 (fechas de vacunas)
  ni armar Docker.
- **Arreglo:** exportar el esquema (`mysqldump --no-data petconnect > petconnect.Backend/sql/schema.sql`), corregir el
  enum de `estado` para incluir `en_adopcion`, agregar `CHECK` de fechas para NC-010 y un `sql/README` con el orden
  (`schema.sql` → `seed.py`). **Sin datos personales reales.**

#### A-02 · 🟠 Alta · El cronograma no coincide con el código [A]
- Sprint 1 (5–16 oct) prometía: NC-004, NC-005, NC-009, NC-011, `docker compose` e integración continua. **Nada está en el repo.**
- Sprint 2 (19–30 oct) prometía: NC-002, NC-006, NC-007, NC-010, ZAP. **Nada está en el repo.**
- Último commit: 15/10/2026. No existe `.github/workflows/`.
- **Arreglo:** cerrar las NC en el orden de [PRIORIDADES](PRIORIDADES-PetConnect-2026-11-03.md), **un commit por NC con su
  prueba**, y actualizar la bitácora (Tabla de NC) con la fecha real de cierre.

### 3.2 Seguridad del backend

#### A-03 · 🔴 Crítica · Secreto JWT por defecto: cualquiera puede fabricar sesiones — NC-007 [A]
- **Dónde:** `security/jwt_helper.py:9` → `os.environ.get("JWT_SECRET", "dev-secret-inseguro")`.
- **Evidencia dinámica:** sin `JWT_SECRET`, un token firmado con `"dev-secret-inseguro"` **es aceptado** por `verify_token()`.
- **Arreglo:** igual que con `FERNET_KEY`: si falta (o tiene menos de 32 bytes), la API **no arranca**.
- **Estado: resuelto el 03/11/2026 (ítem 2.2 de PRIORIDADES).** `jwt_helper.py` lanza `RuntimeError` al importarse
  si `JWT_SECRET` falta o mide menos de 32 bytes (HS256, RFC 7518 §3.2), sin mostrar el valor; `.env.example` lo marca
  como obligatorio. Prueba de regresión: `tests/test_seguridad.py` (`PruebasSecretoObligatorio`), cada caso en un
  proceso aparte con entorno mínimo. Con el código nuevo pasan los 4 casos. Con el código viejo fallan 3 a propósito
  (`test_sin_jwt_secret_no_arranca`, `test_secreto_publico_de_ejemplo_no_arranca`, `test_secreto_de_31_bytes_no_arranca`:
  el código viejo arrancaba igual) y `test_secreto_de_64_caracteres_importa_bien` pasa con ambos (una clave válida
  nunca fue el problema). NC-007 sigue en corrección (2.3 y 4.8).
- **Estado del ítem 4.13 (revocar sesiones): resuelto el 08/11/2026 en tres partes: API y BD (commit `3c039ec`), web
  (commit `aeb6e99`) y móvil (commit `383beb0`).**
  Decisiones del dueño (las recomendadas): (1) ruta `POST /api/auth/logout` y botones por partes (API → web → móvil);
  como hay un solo contador por cuenta, cerrar sesión cierra **en todos los aparatos**; descartada la tabla de sesiones
  por aparato (más tabla, limpieza y pruebas); (2) `require_auth` también rechaza cuentas con estado distinto de
  `activo`, con **401** (la web solo cierra la sesión ante un 401, 4.7); (3) los tokens viejos sin versión **no valen**
  (todos inician sesión una vez más). Cambios: columna `usuarios.version_sesion int(10) unsigned NOT NULL DEFAULT 0`
  (`sql/schema.sql` y la migración `sql/migraciones/2026-11-08_version_sesion.sql`, `ADD COLUMN IF NOT EXISTS`, propia
  de MariaDB; pasos en `sql/README.md`). `security/jwt_helper.py`: `generate_token(user_id, version_sesion)`; el token
  lleva solo `sub`, `ver`, `iat` y `exp` (**sin el correo**); `ver` debe ser un entero ≥ 0 (`True` no vale).
  `dao/usuario_dao.py`: `consultar_sesion(id)` (`SELECT version_sesion, estado`) y `cerrar_sesiones(id)` (suma 1 y
  reasigna `fecha_actualizacion` a sí misma para que su regla *on update* no la cambie); ambos dejan subir los errores
  de la BD. `api.py`: `require_auth` consulta la sesión en cada petición y responde el mismo 401 si la cuenta no
  existe, no está `activo` o la versión no coincide (y sin consultar la BD si el token no trae `ver`); si la BD no
  responde, **503** (nunca 401: una caída no saca a nadie); ya no existe `request.current_user_email` (nadie lo usaba).
  `/login/verify` firma con la versión de la BD y `/register/verify` con `VERSION_SESION_INICIAL = 0` (DEFAULT de la
  columna). Ruta nueva `POST /api/auth/logout` (`@require_auth`): 200 `{"message": "Sesion cerrada"}`. Al arrancar,
  `_preparar_sesiones()` comprueba la columna (errno 1054) y, sin ella, avisa qué migración falta y no arranca.
  `_cuenta_que_envia()` de las solicitudes se mantiene como segunda barrera. Regresión: `tests/test_sesiones.py`
  (26: 21 sin BD y 5 con `PETCONNECT_PRUEBA_BD=1` en las bases temporales `petconnect_prueba_sesion` y
  `petconnect_prueba_sesion_migracion`); `tests/test_esquema.py` +3 (la columna y la migración); ajustadas las pruebas
  que fabricaban tokens con el correo (`test_endpoints`, `test_solicitudes`, `test_mascotas`, `test_ficha_mascota`,
  `test_pool`, `test_seguridad`, y `test_esquema` con BD, que ahora crea dos cuentas activas porque el refugio de la
  semilla está inactivo); `/me` con un usuario borrado pasa de 404 a 401. `test_pool`: 41 métodos de DAO (22
  escrituras, 19 lecturas). Suite 395 (345 + 50 omitidas). Contraprueba (`git stash` de `api.py`, `jwt_helper.py` y
  `usuario_dao.py`): fallan las 21 pruebas nuevas sin BD de `test_sesiones.py` (37 resultados contando subcasos: 28
  fallos y 9 errores) y 45 resultados en toda la suite; ninguna pasa a propósito (todas prueban comportamiento nuevo). **Falta del dueño:** aplicar la
  migración con respaldo (sin ella la API nueva no arranca) y, opcional, las pruebas con MariaDB. Fuera de alcance:
  no existe “cambiar contraseña”; cuando exista, debe llamar a `cerrar_sesiones()`.
  **Parte 2 (web, 08/11/2026, commit `aeb6e99`).** Antes, el botón “Cerrar sesión” solo borraba el token del
  navegador: un token copiado, o la sesión en otro aparato, seguía valiendo hasta 24 h. Decisiones del dueño (las
  recomendadas): **A1**, avisar cuando el servidor no pudo confirmar el cierre, y **B1**, desactivar el botón mientras
  espera. Cambios en `PetConnect.Front/petconnect-app`: `src/services/api.js` `cerrarSesionEnServidor()`
  (`POST /auth/logout` con el token y `AbortSignal.timeout(TIEMPO_CIERRE_MS = 8000)`: si la API no contesta, cuenta
  como sin red); `src/utils/sesion.js` `cerrarSesion({ leerToken, cerrarEnServidor, borrarLocal })` (JS puro) llama a
  la API y **siempre** borra la sesión local; devuelve `"cerrada"` (200), `"ya-cerrada"` (401 o sin token: no llama a
  la API) o `"sin-confirmar"` (503, 502, 500, sin red o tiempo agotado); no borra si mientras esperaba entró otra
  cuenta (otro token). `src/context/AuthContext.jsx`: `logout()` usa `cerrarSesion` y nuevo `cerrarSesionLocal()`.
  `src/components/Header.jsx`: los dos botones (escritorio “Salir” y menú móvil) usan `salir()`, quedan
  desactivados con el texto “Cerrando sesión…” y, con `"sin-confirmar"`, muestran un aviso dentro de una zona
  `role="status"`, con botón “Cerrar aviso” de 44×44 px (desaparece al cerrarlo o al volver a entrar).
  `src/components/FormularioSolicitud.jsx`: tras un 401 usa `cerrarSesionLocal()` (ese token ya no vale; no se llama
  a la API). Regresión: `tests/cerrar-sesion.test.js` (10); `tests/sesion.test.js` acepta que el import de
  `utils/sesion` traiga también `cerrarSesion`. `npm test` 61 (51 + 10), `npm run lint` sin errores (los 2 avisos de
  antes) y `npm run build` correctos. Contraprueba (`git stash` de los 5 archivos de `src/`): fallan las 10 nuevas y
  pasan las 51 anteriores; ninguna nueva pasa a propósito. Revisión en el navegador a 375 px y en escritorio, con
  respuestas de la API simuladas dentro de la página (sesión inventada): el botón cambia a “Cerrando sesión…” y se
  desactiva; con 503 aparece el aviso y con 401 no; en ambos casos se borran el token y los datos; sin scroll
  horizontal. `/impeccable audit`: detector sin hallazgos; pendientes menores fuera del ítem: al cerrar sesión el
  foco del teclado vuelve al inicio de la página (el botón desaparece) y la web no tiene alternativa
  `prefers-reduced-motion` para sus animaciones (también la del aviso).
  **Parte 3 (móvil, 08/11/2026, commit `383beb0`).** Antes, “Cerrar sesión” en Perfil solo borraba el token de
  `AsyncStorage`. Ahora sigue las mismas reglas que la web (A1, B1, la sesión local se borra siempre y tras un 401 solo
  se cierra en local). Decisión del dueño para el aviso: **opción A, `Alert.alert`** (ventana nativa que TalkBack lee
  sola). Se descartó un texto con `accessibilityLiveRegion` porque, al borrarse la sesión, `AppNavigator.js` cambia
  `ProfileScreen` por la pantalla de inicio de sesión y el aviso tendría que vivir en `AuthContext` y mostrarse en
  `LoginScreen` (más estado y un archivo más). Contra: en `react-native-web` `Alert.alert` no hace nada, así que el
  aviso solo se ve en Android. Cambios en `PetConnect.Mobile`: `src/utils/sesion.js` (nuevo, JS puro):
  `cerrarSesion({ leerToken, cerrarEnServidor, borrarLocal })`, como la de la web pero con `await` (AsyncStorage);
  un error sin `status` (sin red: `apiFetch` no atrapa el fallo de `fetch`, o tiempo agotado) cuenta como
  `"sin-confirmar"`; y `conLimiteDeTiempo(hacerPeticion, ms)` con `AbortController` + `setTimeout`
  (`TIEMPO_CIERRE_MS = 8000`; no se usó `AbortSignal.timeout` porque puede no existir en React Native).
  `src/services/api.js`: `cerrarSesionEnServidor()` (`POST /auth/logout`; `apiFetch` no cambió y ya pasaba el
  `signal`). `src/context/AuthContext.js`: `cerrarSesionLocal()` nuevo; `logout()` devuelve el resultado.
  `src/screens/ProfileScreen.js`: `salir()`, botón desactivado con “Cerrando sesión…”,
  `accessibilityState={{ disabled, busy }}`, alto mínimo 48 y rojo más oscuro mientras espera (no transparencia, que
  bajaría el contraste del texto blanco); con `"sin-confirmar"`, `Alert.alert` con el mismo texto de la web
  (“celular” en vez de “navegador”). `src/components/FormularioSolicitud.js`: tras un 401 usa `cerrarSesionLocal()`.
  Regresión: `tests/cerrar-sesion.test.mjs` (12: 8 ejecutan la lógica, incluidos el corte a los 30 ms y la limpieza
  del temporizador, y 4 revisan el texto de los archivos con React Native). `npm test` 47 (35 + 12) y
  `npx expo export --platform web` sin errores. Contraprueba (`git stash` de los 4 archivos y `sesion.js` vacío):
  fallan las 12 nuevas y pasan las 35 anteriores; ninguna nueva pasa a propósito. Sin revisión en el emulador
  (opcional del dueño, con la migración `2026-11-08_version_sesion.sql` aplicada). Hallazgo fuera del ítem: al abrir
  la app, `AuthContext.js` del móvil borra el token ante cualquier error de `/auth/me` (también sin red); la web lo
  corrigió en el 4.7, el móvil no.
- **Pendiente relacionado (ítem 4.13, texto original del 03/11/2026):** hoy `require_auth` acepta el token solo por su firma, sin
  consultar la BD, así que una sesión no se puede cerrar antes de 24 h (ni al cambiar la contraseña). Además el token
  lleva el **correo**, y el contenido de un JWT se puede leer (base64, no cifrado). Propuesta: columna
  `usuarios.version_sesion` dentro del token y comparada en `require_auth` (sumar 1 cierra todas las sesiones) y
  quitar el correo del token. Si algún día se guardan identificadores de sesión en la BD, guardar su hash SHA-256,
  no el valor. Esto **no reemplaza** el secreto obligatorio: con el secreto público se podría falsificar también la
  versión. Hacerlo después del pool de conexiones (4.5), porque suma una consulta por petición.

#### A-04 · 🔴 Crítica · Códigos OTP atacables por fuerza bruta — NC-006 [A parcial]
- **Dónde:** `otp/servicio.py:42-63` (no cuenta intentos), rutas `/api/auth/login/verify` y `/api/auth/verify` sin límite de tasa.
- **Evidencia dinámica:** **2000 intentos fallidos seguidos aceptados** y el código seguía vigente. Con 10 minutos de
  vigencia y sin límite, un código de 6 dígitos se adivina con un script. Como el login exige primero la contraseña,
  el riesgo mayor está en `/api/auth/verify` (registro).
- **Arreglo:** máximo 5 intentos por código (luego se invalida) + Flask-Limiter por IP en `login`, `login/verify`,
  `register`, `verify` y `utils/validar-correo`; comparar con `hmac.compare_digest`.
- **Estado: resuelto el 04/11/2026 (ítems 2.5 y 2.6 de PRIORIDADES).** Límite de intentos (2.5):
  `otp/servicio.py`: `MAX_INTENTOS = 5`; cada código cuenta sus fallos y, tras 5, el 6.º intento **borra** el código y devuelve
  `"bloqueado"` aunque traiga el correcto (después responde “no hay verificación pendiente”); pedir otro código reinicia el
  contador. La comparación usa `hmac.compare_digest` sobre bytes (con `str` no ASCII, como `'１２３４５６'`, lanzaría `TypeError`).
  `api.py`: `/api/auth/login/verify` y `/api/auth/verify` responden **429** “Demasiados intentos fallidos. Vuelve a … para recibir
  otro codigo”, sin token ni usuario creado; los fallos 1 a 5 siguen en 400 “Codigo incorrecto” (sin decir cuántos quedan).
  Decisiones del dueño del proyecto: 429 en lugar de 400; borrar la entrada completa en lugar de dejar una marca; sin
  `threading.Lock` (con peticiones en paralelo el límite podría pasarse un poco; lo frena el limitador del 2.6). La web y el móvil
  muestran `data.error` en cualquier código de error, así que no se tocaron. Prueba de regresión: `tests/test_otp.py` (9 pruebas,
  sin BD ni correos). Contraprueba: con el `servicio.py` anterior fallan 5 y con el `api.py` anterior fallan 2 (las de rutas: 503 y
  500 `TypeError`); 4 pasan con ambos a propósito (no bloquear de más, reiniciar el contador, ancho completo y expirado).
  Limitador (2.6): Flask-Limiter 4.1.1 (`limits` 5.8.0, fijados en `requirements.txt`) con `LIMITE_AUTH = "5 per minute"` por
  IP (`request.remote_addr`) en `login`, `login/verify`, `register`, `verify` y `utils/validar-correo`; la 6.ª petición responde 429
  “Demasiadas peticiones. Espera un minuto e intenta de nuevo” con `Retry-After` (por el manejador de `HTTPException` del 2.3).
  Cada ruta cuenta aparte; contador en memoria (como los OTP, 4.6); sin `ProxyFix` (si la API va detrás de un proxy, 5.2).
  En `login/verify` actúan las dos capas: el limitador corta al 6.º intento dentro del minuto y el bloqueo del OTP corta al 6.º
  intento aunque pasen varios minutos. Prueba de regresión: `tests/test_limite.py` (5 pruebas); las pruebas anteriores apagan el
  limitador en `_importar_api()`. Contraprueba con el `api.py` anterior: fallan 3 de 5 (nunca respondía 429); pasan 2 a propósito
  (cada ruta cuenta aparte y las rutas públicas no se limitan). Suite: 71 pruebas, 61 OK y 10 omitidas que requieren MariaDB.
  Queda por mejorar, sin ítem propio: límite por cuenta (además de por IP) para la contraseña del login y registrar los intentos
  fallidos en el log sin datos personales.

#### A-05 · 🔴 Crítica · El correo de PetConnect se puede usar para phishing/spam [A]
- **Dónde:** `correo/plantillas.py:42` y `:99` insertan `{name}` sin escapar; `correo/servicio.py:66,72` usa `.format(name=...)`.
- **Evidencia dinámica:** con `name = '<a href="https://sitio-falso.example">Reclama tu premio</a>'` el HTML del correo
  **contiene el enlace**. `/api/auth/register` lo envía a **cualquier** dirección y sin límite de peticiones.
- **Impacto:** correos fraudulentos saliendo de la cuenta Gmail del proyecto → Google bloquea la cuenta.
- **Arreglo:** `html.escape(name)` (y de cualquier dato del usuario) antes de la plantilla + limitador de A-04.
- **Estado: resuelto el 03/11/2026 (ítem 2.4 de PRIORIDADES); el limitador se agregó el 04/11/2026 (ítem 2.6: `/register`
  acepta 5 peticiones por minuto por IP, ver A-04).** Dos capas:
  (1) `correo/servicio.py` aplica `html.escape()` a `name`, `code` y `proposito` antes de las dos plantillas, así que
  `<a href=...>` llega como texto (`&lt;a href=...`); el texto plano no se escapa (ahí no se dibujan etiquetas).
  (2) `/api/auth/register` valida el nombre **antes** del DNS y de la BD (`_validar_nombre` en `api.py`): de 2 a 60
  caracteres, palabras de letras (con tildes y ñ) separadas por espacios, con `'` o `-` dentro de la palabra y un punto
  al final (`Ma. José`); si no, 400. Esto corta también las URL sueltas (`https://...`, `sitio-falso.example`), que
  Gmail convierte en enlace aunque estén escapadas. Además se comprobó que en las cabeceras no se puede inyectar un salto
  de línea: el asunto es fijo en el código, el destinatario pasa por la expresión regular del correo y Python 3.14 se
  niega a armar un mensaje con una cabecera escondida (`email.errors.MessageError`).
  Pruebas de regresión: `tests/test_correo.py` (`PruebasEscapeHTML`, 3; `PruebasCabeceras`, 1) y `tests/test_errores.py`
  (`PruebasNombreRegistro`, 2), sin enviar correos ni consultar el DNS. Contraprueba: con el `servicio.py` anterior fallan
  `test_el_html_no_trae_el_enlace_del_nombre` (4 casos: código y bienvenida, con y sin espacios) y
  `test_nombre_con_simbolos_se_ve_bien`; con el `api.py` anterior falla `test_nombre_con_html_o_url_responde_400_sin_enviar_correo`
  (11 casos). Pasan con ambos códigos, a propósito: `test_la_plantilla_propia_sigue_siendo_html` (el botón propio de la
  plantilla), `test_salto_de_linea_en_cabeceras_no_envia_nada` (la protección es de Python) y
  `test_nombres_de_persona_pasan_el_filtro` (un nombre normal nunca fue el problema). Suite: 57 pruebas, 47 OK y 10
  omitidas que requieren MariaDB.

#### A-06 · 🔴 Crítica · El correo viaja con TLS sin verificar el certificado [N]
- **Dónde:** `correo/servicio.py:45` → `s.starttls()` sin `context`.
- **Evidencia:** en Python 3.14, `smtplib.starttls()` sin contexto usa `ssl._create_stdlib_context`, que es
  `_create_unverified_context` (`verify_mode=0`, `check_hostname=False`, comprobado en el `.venv`).
- **Impacto:** en una red insegura (wifi pública, SENA), alguien en el medio puede hacerse pasar por `smtp.gmail.com`
  y **robar `GMAIL_USER` y la contraseña de aplicación**.
- **Arreglo (1 línea):** `s.starttls(context=ssl.create_default_context())`.
- **Estado: resuelto el 03/11/2026 (ítem 2.1 de PRIORIDADES).** `starttls` recibe un contexto con
  `verify_mode=CERT_REQUIRED` y `check_hostname=True`. Prueba de regresión: `tests/test_correo.py` (con *mock* de
  `smtplib.SMTP`, sin enviar correos), que también comprueba que el cifrado se activa antes de `login`.

#### A-07 · 🟠 Alta · Cualquiera ve cualquier mascota, incluidos datos de salud — NC-002 [A]
- **Dónde:** `api.py:207-212` (consulta sin filtro de estado) y `api.py:235-246` (sin `@require_auth`).
- **Qué pasa:** cambiando el número en `/api/mascotas/<id>` se obtiene cualquier mascota registrada, con sus observaciones.
  Confirmado por el equipo el 5/10 (AA2, CP-006).
- **Arreglo:** la ruta pública solo devuelve `estado = 'en_adopcion'` (404 si no); las mascotas privadas van por una
  ruta con `@require_auth` que compare `id_usuario` con el del token. Prueba de regresión: sin token → 404.
- **Estado: resuelto el 05/11/2026 (ítem 2.9 de PRIORIDADES). NC-002 cerrada.** `api.py`: la ruta pública
  `GET /api/mascotas/<id>` filtra `estado = 'en_adopcion'` en el SQL y lo vuelve a revisar en Python (doble barrera);
  cualquier otro estado o una mascota inexistente responde el **mismo** 404 “Mascota no encontrada”, sin datos.
  Ruta privada nueva `GET /api/usuarios/me/mascotas/<id>` con `@require_auth`: SQL filtrado por `id_mascota` e
  `id_usuario` del token y comparación del dueño en Python; sin token o con un token inválido → 401 (sin consultar la BD);
  mascota ajena → el mismo 404 (no 403: no revela que existe); el dueño la ve en cualquier estado y la respuesta no trae
  `id_usuario`. Hoy no la consume nadie; es el patrón para el carné de vacunas. Web y móvil no cambiaron (solo abren
  mascotas en adopción). Decisiones del dueño del proyecto: crear ya la ruta privada (la pide la acción correctiva de
  NC-002), 404 en lugar de 403 y dejar el SQL en `api.py` por ahora: `MascotaDAO` se traga los errores de la BD y
  devuelve `None`, así que usarlo convertiría el 503 del 2.3 en un 404; moverlo queda como ítem 4.15, junto con el pool (4.5).
  Prueba de regresión: `tests/test_mascotas.py` (11 pruebas; BD simulada que devuelve la fila sin aplicar el `WHERE`,
  así que también prueba la segunda barrera). Contraprueba con el `api.py` anterior: fallan 9 de 11 (16 casos con los
  subcasos); pasan con ambos, a propósito, la mascota en adopción (200) y la inexistente (404). Suite: 89 pruebas, 78 OK y
  11 omitidas que requieren MariaDB. Con MariaDB temporal (`PETCONNECT_PRUEBA_BD=1`, ejecutada por el dueño del proyecto
  con respaldo previo): `test_esquema.PruebasEsquemaEnBD` 6 de 6 OK, incluida `test_mascota_privada_solo_la_ve_su_dueno`
  (una mascota `activa` → 404 en la ruta pública y con el token de otro usuario, 200 con el del dueño, con el SQL real).
- **Actualización 09/11/2026 (ítem 4.15, commits `d03871b` y `400061f`, solo backend; no toca el esquema).** El SQL
  de productos y mascotas salió de `api.py` a `dao/`. Parte 1: `MascotaDAO` y `ProductoDAO` ya no atrapan los errores
  de la BD ni imprimen el mensaje de MySQL (Ley 1581): los dejan subir, como `SolicitudDAO` y `OtpDAO`, y la consola
  los atrapa en el ciclo de cada menú con un aviso que solo trae el número del error (`vista/aviso_bd.py`). Parte 2:
  las 5 consultas pasan, copiadas tal cual, a `ProductoDAO.consultar_catalogo` / `consultar_catalogo_por_id` y
  `MascotaDAO.consultar_en_adopcion` / `consultar_en_adopcion_por_id` / `consultar_del_dueno`, que devuelven
  diccionarios con los mismos alias (el JSON no cambia); la doble barrera sigue en `api.py`. `_verificar_bd()` se
  queda solo para `UsuarioDAO`, que todavía se traga los errores (igual que `ProveedorDAO`). Regresión:
  `tests/test_dao_errores.py` (9: los métodos de 4 DAO dejan subir el error sin imprimir, la consola avisa sin el
  mensaje y `api.py` no tiene SQL) + su caso en `test_sin_env_real.py`; `test_mascotas.py`, `test_endpoints.py` y
  `test_errores.py` (503 con BD caída) pasan sin cambios. Contraprueba: con los DAO viejos fallan 2 (28 casos), con
  los menús viejos 4 y con el `api.py` viejo 2 (3 casos). Hallazgo → 4.21 (`UsuarioDAO` y `ProveedorDAO`).

#### A-08 · 🟠 Alta · Configuración insegura y errores internos expuestos — NC-007 [A + N]
- `api.py:458` → `app.run(debug=True)`: el depurador de Werkzeug permite ejecutar código si se expone. [A]
- `api.py:39-41` → el manejador global devuelve `str(e)` al cliente. [A]
- **Evidencia dinámica [N]:**

  | Petición | Respuesta actual | Debería ser |
  |---|---|---|
  | `GET /api/no-existe` | **500** `"404 Not Found: ..."` | 404 |
  | `POST /api/productos` | **500** `"405 Method Not Allowed..."` | 405 |
  | `GET /api/mascotas/1` con la BD caída | **500** `"'NoneType' object has no attribute 'cursor'"` | 503 con mensaje genérico |
  | `POST /api/auth/login/verify` con `"code": 123456` (número) | **500** `"'int' object has no attribute 'strip'"` | 400 |
  | `POST /api/auth/login` con `"email": 5` | **500** `"'int' object has no attribute 'strip'"` | 400 |

- **Arreglo:** `debug` desde variable de entorno (falso por defecto); manejar `HTTPException` aparte; mensaje genérico
  para 500 (registrando el detalle en el servidor); validar tipos de entrada (`isinstance(x, str)`); si
  `_get_conn()` devuelve `None`, responder 503.
- **Estado: resuelto el 03/11/2026 (ítem 2.3 de PRIORIDADES).** `api.py`: `debug` solo con `FLASK_DEBUG=1` (apagado por
  defecto, en `.env.example`); manejador de `HTTPException` con el código real (404, 405 con cabecera `Allow`); 500
  genérico con `id_error`, registrando en el servidor el id, la ruta, el tipo de error y la pila **sin** el mensaje de la
  excepción (Ley 1581); `BDNoDisponible`, `InterfaceError` y `OperationalError` → 503 genérico, también en las rutas de
  usuario (el login ya no dice “credenciales incorrectas” con la BD caída); las rutas de catálogo ya no devuelven el
  mensaje de MySQL; `email`, `code`, `password` y `name` deben ser texto (400) y el cuerpo debe ser un objeto JSON.
  Las 5 filas de la tabla quedan en 404, 405, 503, 400 y 400. Prueba de regresión: `tests/test_errores.py` (10 pruebas;
  las 10 fallan con el código viejo). NC-007 sigue en corrección solo por `decrypt()` (4.8).

#### A-09 · 🟠 Alta · Un segundo registro pisa la contraseña del primero [A]
- **Dónde:** `api.py:362-365` + `otp/servicio.py:35` (sobrescribe sin preguntar).
- **Evidencia dinámica:** tras dos `/register` con el mismo correo, el hash pendiente es **el del segundo**. Si la
  víctima luego verifica con su código, la cuenta queda con la contraseña del atacante.
- **Arreglo:** si ya hay un registro pendiente y vigente, no sobrescribirlo (responder 409 “revisa tu correo” o reenviar
  el mismo código).
- **Estado: resuelto el 05/11/2026 (ítem 2.7 de PRIORIDADES).** Estuvo en pausa desde el 04/11/2026 hasta crear el
  botón web “Reenviar código”. `otp/servicio.py`: `AlmacenOTP.vigente(clave)` devuelve el pendiente si no venció (si
  venció lo borra y devuelve `None`) y `para_reenviar(clave)` aplica las reglas del reenvío. `api.py`: si hay un
  pendiente vigente, `/api/auth/register` **no lo toca** (ni nombre, ni hash, ni código, ni intentos, ni vencimiento),
  no envía nada y responde lo mismo de siempre (“Codigo enviado”, sin un 409 que revele el registro en curso, A-14):
  vale la **primera** contraseña. Ruta nueva `POST /api/auth/register/resend` (solo `email`, con
  `@limiter.limit(LIMITE_AUTH)`, sin consultar la BD ni el DNS): reenvía **el mismo código** con el nombre del primer
  registro y responde siempre “Si hay un registro pendiente para este correo, te reenviamos el codigo”, haya o no
  pendiente. Si el envío falla, usa `_avisar_fallo_envio` del 2.8 (en el log solo la ruta y el tipo de error; en
  desarrollo imprime solo el código) y fuera de desarrollo responde 503 **sin borrar** el pendiente, porque el primer
  correo pudo llegar.
  Decisiones del dueño del proyecto (05/11/2026): (a) nombre `/api/auth/register/resend`; (b) 60 s entre correos del
  mismo código, controlados también en el servidor (`ultimo_envio`), con la misma respuesta neutra si se pide antes;
  (c) máximo 3 reenvíos por código (4 correos en total); (d) reenviar **no** alarga los 10 minutos; (e) un código con
  5 fallos no se reenvía (ya no sirve); (f) si falla el envío del reenvío, 503 sin borrar el pendiente (solo revela
  un registro en curso cuando falla Gmail, cosa que el atacante no controla). Ni registrarse otra vez ni reenviar
  reinician el contador de intentos del 2.5.
  Prueba de regresión: `tests/test_registro.py` (18 pruebas, sin BD, sin correos, sin DNS, con el reloj de
  `otp/servicio.py` simulado; correos inventados `@ejemplo.test`). Cubre: dos registros con contraseñas distintas
  (queda el hash del primero y `/verify` crea la cuenta con él; respuestas idénticas); 5 fallos + reenvío + registro
  + código correcto → 429; 4 fallos + reenvío + 1 fallo → 429; pendiente vencido sí se reemplaza; el reenvío manda el
  mismo código; sin pendiente, misma respuesta y nada enviado; `vigente()` solo; 6.ª petición de reenvío en un
  minuto → 429; reglas (b) a (f). `tests/test_logs.py` se ajustó: su prueba de desarrollo registraba dos veces el
  mismo correo y esperaba un segundo envío, que ahora ya no ocurre (A-09). Contraprueba con `git stash` de un archivo
  a la vez: con el `api.py` anterior **fallan 13 de 18** (16 fallos con los subcasos; pasan a propósito las 4 de
  `vigente()`, que solo usan `servicio.py`, y `test_pendiente_vencido_se_reemplaza`, porque el código viejo también
  reemplazaba un pendiente vencido); con el `servicio.py` anterior **fallan 17 de 18** (pasa a propósito
  `test_reenviar_sin_correo_o_con_numero_responde_400`, porque el 400 sale antes de tocar el almacén; en la suite
  completa fallan además otras 6 pruebas de registro porque el `api.py` nuevo llama a `vigente()`, que no existe en
  el viejo). Suite: 107 pruebas, 96 OK y 11 omitidas que requieren MariaDB.
  **Web (parte 2):** `src/services/api.js` tiene `resendRegisterCode(email)`. En `RegisterModal.jsx`, el paso “Verificar
  correo” tiene un botón “Reenviar código” con cuenta regresiva (“Reenviar en 60 s”), que arranca también con el
  primer código, y que se queda sin reenvíos tras 3, como el servidor. Muestra el aviso neutro “Si hay un registro
  pendiente, te reenviamos el código…” en una zona `role="status"`/`aria-live="polite"` y los errores de la API (429,
  503) en el cuadro rojo, ahora con `role="alert"`. Usa `aria-disabled` en lugar de `disabled` para no perder el foco
  del teclado y mide 44 px de alto. “Volver e intentar de nuevo” pasó a “¿Escribiste mal tu correo? Cambiar correo”.
  `npm run lint` sin errores (solo los 2 avisos de los contextos) y `npm run build` OK. Revisado a 375 px con
  respuestas simuladas y probado por el dueño del proyecto con la API real (el correo del primer registro llegó; un
  segundo registro no envió otro). `/impeccable audit`: 17/20. Lo que encontró ya existía antes del 2.7: la caja del
  código sin etiqueta (`aria-label`, `autoComplete="one-time-code"`) y los modales sin `role="dialog"`, sin Esc y sin
  retener el foco.
  **Riesgos que siguen abiertos:** (1) otra persona puede mandar 6 códigos falsos a `/verify` con el correo de la
  víctima; el bloqueo del 2.5 borra el pendiente y entonces sí puede registrarse con su contraseña (más difícil:
  tiene que hacerlo en los minutos entre el registro y la verificación). Arreglo definitivo: que `/verify` vuelva a
  pedir la contraseña y la compare con el hash pendiente. (2) Un `/register` con pendiente vigente responde más
  rápido (no calcula bcrypt ni envía correo): midiendo el tiempo se podría saber que hay un registro en curso. Taparlo
  exige enviar los correos en segundo plano; el 409 de A-14 (4.10) revela aún más.
  **Mejora pendiente, sin ítem todavía (hallada por el dueño en la prueba del 3.1 parte 2, 05/11/2026):** el código
  vencido no se avisa. Si alguien se registra otra vez con un correo que tiene un código vigente, `/register` responde
  “Codigo enviado” pero no manda uno nuevo (correcto según A-09) y los 10 minutos siguen contando desde el primero; cuando
  vence, “Reenviar código” tampoco envía nada (respuesta neutra) y la web no dice que el código venció. Hace falta un
  camino claro para pedir un código nuevo tras el vencimiento (por ejemplo, que la web cuente los 10 minutos y, al
  vencer, ofrezca “Volver a registrarme”, que sí reemplaza un pendiente vencido) sin revelar registros en curso (A-14).

#### A-10 · 🟠 Alta · Códigos OTP y correos impresos en la consola [N]
- **Dónde:** `api.py:305`, `:377`, `:421` → `print(f"[DEV] ... Codigo ... para {email}: {code}")`.
- **Qué pasa:** si el correo falla, el **código de inicio de sesión** de cualquier usuario y su correo quedan en los logs.
  Quien lea los logs puede entrar a cualquier cuenta (tras la contraseña) y se viola la regla de datos personales
  (Ley 1581).
- **Arreglo:** imprimir el código solo si `APP_ENV=desarrollo` explícito; en otro caso, registrar solo “fallo de envío”
  y responder al cliente que reintente.
- **Estado: resuelto el 04/11/2026 (ítem 2.8 de PRIORIDADES).** `api.py`: variable nueva `APP_ENV` (`_es_desarrollo()`:
  solo vale `desarrollo`, sin importar espacios ni mayúsculas; vacía, `produccion` o cualquier otro valor = no es
  desarrollo). Es aparte de `FLASK_DEBUG`, para que ver códigos no exija encender el depurador de Werkzeug. Los 3
  `print()` se reemplazaron por `_avisar_fallo_envio(e, codigo=None)`, que registra con `app.logger.warning` solo
  “Fallo de envio de correo en <ruta>: <tipo de error>”, **nunca** el correo ni `str(e)` (el mensaje de SMTP puede
  traer la dirección, Ley 1581). Con `APP_ENV=desarrollo` imprime **solo el código** (`[DEV] Codigo de verificacion …`)
  y `/login` y `/register` responden “Codigo enviado” como antes. Fuera de desarrollo se descarta el código pendiente
  (`_otp_login.descartar` / `_otp_registro.descartar`) y se responde **503** “No pudimos enviar el código a tu correo.
  Intenta de nuevo en unos minutos”. No revela cuentas (A-14): en `/login` ese 503 sale después de comprobar la
  contraseña y en `/register` después del 409 que ya existía. La bienvenida de `/verify` sigue respondiendo 201 (la
  cuenta ya se creó); solo se registra el fallo. Al arrancar, la API avisa si `APP_ENV=desarrollo`. `.env.example`
  documenta `APP_ENV=` (vacía) y ya no dice que el código “se imprime en la consola” siempre. La web y el móvil
  muestran `data.error` con cualquier respuesta que no sea ok, así que el 503 nuevo no exigió tocarlos.
  Prueba de regresión: `tests/test_logs.py` (6 pruebas, sin BD, sin correos, sin DNS; correo inventado
  `persona.prueba@ejemplo.test`; el correo simulado falla con un mensaje que trae la dirección, como uno real de SMTP).
  Comprueba con `redirect_stdout` y `assertLogs` que, sin `APP_ENV` y con `""`, `produccion` y `dev`, ni la consola ni
  los logs traen el código ni el correo, la respuesta es 503 y el pendiente ya no existe; que con `desarrollo` y
  `"  Desarrollo  "` la consola trae el código y no el correo; y que la bienvenida fallida responde 201 sin el correo.
  Contraprueba con el `api.py` anterior (`git stash` solo de ese archivo): **fallan 5 de 6** (14 subcasos), todas
  porque la consola mostraba el correo (`[DEV] No se pudo enviar el correo (550 …: persona.prueba@ejemplo.test).
  Codigo de inicio de sesion para persona.prueba@ejemplo.test: 740041`). Pasa con ambos, a propósito,
  `test_correo_enviado_no_imprime_ni_registra` (si el correo sí sale, no se imprime ni se registra nada: el camino
  normal no cambió). Suite: 77 pruebas, 67 OK y 10 omitidas que requieren MariaDB. Sin NC asociada (GA9 no cambia).

#### A-11 · 🟠 Alta · Una sola conexión a la BD compartida entre hilos — NC-003 [A]
- **Dónde:** `conexion/conexion_bd.py:17-31` (Singleton con una conexión). El equipo midió 56 % de errores con 500 usuarios.
- **Arreglo:** `mysql.connector.pooling.MySQLConnectionPool`, pedir y devolver una conexión por petición (con
  `try/finally`), cerrar cursores siempre.
- **Estado: resuelto en el código el 07/11/2026 (ítem 4.5 de PRIORIDADES, commit `9c417de`; solo backend). NC-003
  sigue abierta** hasta el 4.6 (OTP fuera de la memoria, A-12) y la nueva medición de carga (4.12); la paginación y
  los índices que también pide NC-003 quedaron como ítem 4.17. Decisiones del dueño: pool de 10, la consola y
  `seed.py` usan el mismo pool, y el 4.15 va aparte. `conexion/conexion_bd.py`: `ConexionBD` (sigue siendo
  Singleton) presta conexiones de un `MySQLConnectionPool` creado la primera vez que se necesita, una sola vez
  aunque lo pidan varios hilos; tamaño en `DB_POOL_SIZE` (`config/db_config.py`, `.env.example`; vacío = 10, de 1 a
  32, otro valor detiene el arranque). El pool de la librería no espera: si está lleno, `obtener_conexion()`
  reintenta hasta 5 s y luego devuelve `None` (503). El log de conexión guarda solo el tipo y el número del error,
  no el mensaje (traía usuario y host). `conexion_y_cursor()` es el `try/finally` escrito una vez: cierra el cursor
  y devuelve la conexión al pool aunque haya error. La usan los 32 métodos de los 5 DAO (el `commit`/`rollback`
  pasa a la conexión prestada; `ConexionBD.commit()` y `rollback()` desaparecen) y las 4 consultas directas de
  `api.py`. Hallazgo de la revisión: `_get_conn()` se usaba 7 veces solo para preguntar si había BD y nunca
  devolvía la conexión; con un pool, eso lo habría agotado en 10 peticiones. Ahora es `_verificar_bd()`, que la
  devuelve enseguida. `main.py` devuelve la conexión de prueba y cierra el pool al salir; `seed.py` devuelve la
  suya. Se comprobó en el código de mysql-connector 9.1 que, al devolver una conexión, la limpieza de sesión
  vuelve a aplicar el modo estricto (NC-009), el juego de caracteres y `autocommit`. Los DAO viejos siguen
  devolviendo `None`/`[]` ante errores de la BD (eso es el 4.15). Regresión: `tests/test_pool.py` (25 pruebas; 3
  con MariaDB real): tamaño del pool, pool falso con 20 hilos, espera y 503, log sin datos, `conexion_y_cursor` con
  y sin error, los 32 métodos de los DAO y las 14 rutas del inventario de `tests/test_endpoints.py` (anotadas ahí)
  devuelven toda conexión y cierran todo cursor con la BD vacía, con error de MySQL y con error inesperado; lo
  mismo la consola y `seed.py`. Con `PETCONNECT_PRUEBA_BD=1`, en una base temporal: 30 hilos a la vez sin
  respuestas cruzadas, modo estricto tras reutilizar cada conexión y 30 consultas de un DAO sin agotar el pool.
  Suite: 256 pruebas (229 correctas y 27 omitidas que requieren MariaDB). Contraprueba en una copia temporal fuera
  del repositorio: con el backend anterior fallan 20 de las 22 pruebas sin MariaDB (las 2 que pasan solo revisan
  que las listas de métodos y rutas estén completas); con solo el `api.py` anterior fallan las 12 rutas que usan
  la BD en los 3 escenarios; con solo los DAO anteriores, los 32 métodos; con solo el `seed.py` o el `main.py`
  anterior, su prueba.
- **Ítem 4.17 (paginación e índices, NC-003): hecho el 09/11/2026 en 4 partes** (`ea95ed5`, `d5502a8`, `55fa8bf`, `a42a038`). Decisiones del dueño: parámetros
  opcionales `?pagina=&por_pagina=` (20 por defecto, máximo 50) que mantienen la respuesta como lista; catálogo web
  con “Ver más” y búsqueda sobre lo cargado; móvil con botón “Ver más”. **Parte 1 hecha (índices, commit
  `ea95ed5`):** `sql/schema.sql` y la migración `sql/migraciones/2026-11-09_indices_listados.sql` crean
  `idx_mascotas_estado`, `idx_productos_activo` e `idx_proveedores_ciudad` (`ciudad`, `activo`, `nombre`). La
  migración usa `CREATE INDEX IF NOT EXISTS` (MariaDB, no MySQL), no toca datos y se puede repetir; **el dueño la
  aplicó con respaldo el 09/11/2026**. La búsqueda por nombre de proveedores (`LIKE '%texto%'`) no puede usar un índice
  normal y queda sin él. Regresión en `tests/test_esquema.py`: 3 pruebas sin BD (los índices están en el esquema; la
  migración solo crea esos índices y no apaga el modo estricto) y 2 con MariaDB en la base temporal
  `petconnect_prueba_indices` (sin índices, aplicar la migración dos veces los crea con las columnas en orden y sin
  tocar filas; `EXPLAIN` de las consultas de los DAO los lista en `possible_keys`). Contraprueba: con el `schema.sql`
  anterior fallan los 3 casos de índices; sin la migración falla su clase. Suite: 414 (362 correctas y 52
  omitidas). **Parte 2 hecha (API, commit `d5502a8`; no toca la BD):** `ProductoDAO.consultar_catalogo` y
  `MascotaDAO.consultar_en_adopcion` reciben `(limite, desplazamiento)` y terminan en `ORDER BY` id
  `LIMIT %s OFFSET %s`, parametrizado. `api.py` (sin SQL) los lee de `?pagina=&por_pagina=`: 20 por defecto, más de 50
  se recorta a 50; texto, 0, negativos, decimales o `pagina` > 10.000 responden 400 en español sin tocar la BD (solo
  dígitos ASCII; un número de miles de cifras no da 500). La respuesta sigue siendo una lista. Hallazgo de la prueba:
  `000` daba 500 antes de publicar el cambio; corregido. Regresión: `tests/test_paginacion.py` (8 pruebas) y, con
  MariaDB, 6 mascotas de 4 en 4 dan 4 + 2 + 0 sin repetir ni saltar. Contraprueba: con el código anterior fallan 7 de
  8 (pasa a propósito la que revisa que sigue siendo una lista); solo con el `api.py` anterior, 7; solo con los DAO
  anteriores, 6. Suite: 423 (370 correctas y 53 omitidas). **Parte 3 hecha (web, commit `55fa8bf`):** Home pide
  solo los 4 destacados (antes todo el catálogo y recortaba), Adopción carga de 12 en 12 y Catálogo de 50 en 50 con
  un botón “Ver más” (`src/components/BotonVerMas.jsx`); el buscador y las categorías del catálogo filtran lo ya
  cargado y un aviso lo dice si quedan más. La lógica está en `src/utils/paginacion.js` y el hook
  `src/hooks/useListaPaginada.js`: un error al pedir más no borra lo cargado y un clic doble no pide dos veces.
  Regresión: `tests/paginacion.test.js` (10); contraprueba: con el código anterior fallan 3. Probado en el navegador
  a 375 px con la API real (tamaños bajados solo para la prueba): sin repetir, una petición por “Ver más” y el botón
  desaparece al final. **Parte 4 hecha (móvil, commit `a42a038`):** el catálogo (`HomeScreen`) se pide de 20 en 20
  y la adopción de 12 en 12, con “Ver más” al pie de la `FlatList` (`src/components/BotonVerMas.js`); misma lógica
  que la web en `src/utils/paginacion.js` y `src/hooks/useListaPaginada.js`. Regresión: `tests/paginacion.test.mjs`
  (8); contraprueba: con el código anterior fallan 2. Probado en el export web a 375 px con la API real (servido en
  el puerto 8081: el 8090 no está en el CORS de la API). **NC-003 sigue abierta** hasta repetir la prueba de carga
  (4.12).

#### A-12 · 🟠 Alta · Pasar a Gunicorn romperá los OTP [N]
- **Dónde:** `api.py:44-45` (`AlmacenOTP()` en memoria), `otp/servicio.py`.
- **Qué pasa:** NC-003 propone Gunicorn. Con varios *workers* (procesos), el código se guarda en un proceso y la
  verificación puede llegar a otro → “No hay verificación pendiente”. Además los códigos se pierden al reiniciar,
  el diccionario no es seguro entre hilos y **nunca se limpian los vencidos** (crece sin límite si alguien hace spam;
  igual `_mx_cache` en `api.py:81`).
- **Arreglo:** guardar los OTP en una tabla de la BD (`otp_pendientes` con hash del código, intentos y expiración) o
  usar 1 worker con hilos mientras tanto; limpiar vencidos.
- **Estado: resuelto en el código el 07/11/2026 (ítem 4.6 de PRIORIDADES, en dos partes; solo backend). NC-003 sigue
  abierta** hasta el 4.17 (paginación e índices) y la medición del 4.12. **Migración aplicada (confirmado el 09/11/2026: la API pasa su revisión de la tabla al arrancar)**
  en su BD (`sql/migraciones/2026-11-07_otp_pendientes.sql`, con respaldo): sin ella la API nueva no arranca y lo
  avisa. Decisiones del dueño: opción A (tabla), el código **cifrado con Fernet** y no con hash (con un hash no se
  podría reenviar el mismo código, regla del A-09), borrar los datos del registro pendiente al terminar (Ley 1581) y
  `_mx_cache` de 1.000 dominios.
  - **Parte 1 (`9ccd379`):** `_mx_cache` (`api.py`) guarda como mucho 1.000 dominios (`MX_CACHE_MAXIMO`) y olvida el
    que lleva más tiempo sin usarse (LRU, con `OrderedDict`), con un candado entre hilos.
  - **Parte 2 (`24ed52c`):** tabla `otp_pendientes` (`sql/schema.sql` y migración): una fila por correo y propósito
    (`registro`/`login`), código cifrado, intentos, reenvíos, vencimiento, y los datos del pendiente (nombre, hash
    bcrypt, `id_usuario`, prueba de la autorización); la regla `chk_otp_proposito` y la clave foránea a `usuarios`
    (`ON DELETE CASCADE`). `otp/servicio.py`: `AlmacenOTP(proposito, repositorio)` conserva las reglas (10 min, 5
    fallos → 429, `compare_digest`, reenvío del mismo código con 60 s y máximo 3, código nuevo reinicia contadores)
    y guarda en `OtpDAO` (`dao/otp_dao.py`, la API) o en `RepositorioMemoria` (con candado; las pruebas). Cada intento
    se **reserva antes de comparar** con un solo `UPDATE ... WHERE intentos < 5` (atómico): ni 20 peticiones a la vez
    ni varios procesos pasan de 5. Crear un código borra **todos** los vencidos y la API los borra también al arrancar
    (`_preparar_otp()`, que además se detiene con un aviso claro si falta la tabla). Un código ilegible (cambió la
    `FERNET_KEY`) se borra y se pide otro (`decrypt_estricto` nuevo en `security/crypto.py`). Correos de más de 120
    caracteres se rechazan (antes daban 500 al guardar). `/register/resend` ahora usa la BD (sin BD, 503). El correo
    usa la intercalación `utf8mb4_spanish_ci`: mayúsculas y minúsculas comparten pendiente.
  - **Regresión:** `tests/test_otp_bd.py` (48; 16 con MariaDB en bases temporales): 20 hilos con código malo solo
    comparan 5 veces, crear borra 100 vencidos de otros correos, código cifrado, las reglas con un repositorio
    compartido (dos “procesos”), SQL parametrizado y errores que suben, la API crea los almacenes con `OtpDAO`, sin
    BD las rutas de código responden 503, otro proceso completa el registro y no queda nada del pendiente,
    arranque con y sin tabla; con `PETCONNECT_PRUEBA_BD=1` las mismas reglas con la tabla real, la regla CHECK, la
    clave foránea y la migración dos veces. `test_esquema.py` (34 tablas, la tabla igual en el esquema y la
    migración), `test_pool.py` (`OtpDAO` entra en la revisión de fugas: 39 métodos) y 2 pruebas de `_mx_cache` en
    `test_endpoints.py`. Las pruebas de rutas usan un `RepositorioMemoria` (`_importar_api`). Suite: 310 (267 + 43
    omitidas). Contraprueba en copias fuera del repositorio: con el código anterior, 20 intentos comparan 20 veces
    (`20 != 5`) y los 100 vencidos nunca se borran; con solo el `api.py` anterior fallan 5 (los almacenes en memoria,
    los 120 caracteres y el arranque); con el `_mx_cache` anterior, 1.500 entradas en vez de 1.000. Corrección del 08/11/2026: con MariaDB, la prueba de 20 intentos dio 4 en vez de 5. Quien ganaba un intento leía la fila después, y un 6.º intento ya la había borrado al bloquearla: respondía “no hay pendiente” sin comparar, aunque trajera el código correcto. Ahora `verificar()` lee la fila antes de reservar el intento. Prueba sin MariaDB que lo fuerza siempre (los 5 que ganan se demoran 0,2 s); con el código anterior da `0 != 5`. Suite: 311 (268 + 43 omitidas). El dueño corrió `test_otp_bd.py` con `PETCONNECT_PRUEBA_BD=1` tras la corrección: 48 de 48 correctas, incluidas las 16 con MariaDB (08/11/2026).
  - **Hallazgo:** el borrador de la política (A.11) dice que un registro sin terminar “nunca llega a la base de
    datos”: ya no es cierto. Corregirlo obliga a subir la versión (C.9): decisión D.7 del borrador.

#### A-13 · 🟡 Media · El cifrado Fernet no se usa pero es obligatorio para arrancar [A]
- `api.py:29` importa `encrypt/decrypt` y el comentario de `api.py:400-401` dice que el teléfono se guarda cifrado:
  **no se cifra nada**. `security/crypto.py:14-18` impide arrancar sin `FERNET_KEY`; **comprobado**: hasta importar
  `security.jwt_helper` falla sin esa clave. `decrypt()` (`:30-37`) se traga cualquier error y devuelve el texto cifrado.
- **Arreglo:** usarlo de verdad (teléfono) o quitarlo; corregir el comentario; que `decrypt` lance error.
- **Estado: resuelto el 08/11/2026 (ítem 4.8 de PRIORIDADES, commit `979cdf3`, solo backend; no toca la BD). Cierra
  NC-007.** Fernet ya no se puede quitar: desde el 4.6 cifra los códigos OTP. Decisión del dueño: **opción A**, el
  teléfono sigue en texto plano y se corrige el comentario. Se descartó la opción B (cifrarlo): las columnas
  `varchar(20)` no alcanzan (un teléfono cifrado ocupa unos 120 caracteres), habría que migrar las filas existentes y,
  mientras `generate_keys.py` pueda sobrescribir el `.env` (A-16), cambiar la `FERNET_KEY` dejaría ilegibles todos los
  teléfonos; además, hoy ninguna pantalla los lee. Retomarla cuando A-16 esté corregido y exista una vista que los use.
  Cambios: `decrypt()` lanza `InvalidToken` si no puede descifrar (vacío o `None` se devuelven igual);
  `decrypt_estricto` se fusionó con ella y `otp/servicio.py` usa `decrypt`; `api.py` ya no importa
  `encrypt/decrypt` (no los usaba) y su comentario dice la verdad: el registro no pide teléfono y el de las solicitudes
  de adopción va en claro. La política no prometía cifrar el teléfono (revisado). Regresión: `PruebasDescifrado` en
  `tests/test_seguridad.py` (5); las 2 de `decrypt_estricto` de `test_otp_bd.py` pasaron ahí. Suite: 314 (271 + 43
  omitidas). Contraprueba con el `crypto.py` anterior: fallan las 3 de texto ilegible y
  `test_codigo_ilegible_se_borra_y_no_se_reenvia` (con un `decrypt` permisivo, el OTP compararía el texto cifrado);
  pasan a propósito la ida y vuelta y la de vacío o `None`.

#### A-14 · 🟡 Media · Enumeración de correos en el registro [N, ya en el plan A07]
- `api.py:359-360` responde **409 “El correo ya está registrado”**: permite saber quién tiene cuenta.
- **Arreglo:** respuesta neutra (“Si el correo es válido te enviamos un código”) y avisar por correo al titular.
- **Estado: resuelto el 08/11/2026 (ítem 4.10 de PRIORIDADES, en una parte, `8668680`; solo backend; no toca el esquema ni cierra
  NC; el caso CP-002 de la GA9 pasa a aprobado en la API).** Decisión del dueño: **opción A**, respuesta neutra + correo
  de aviso al titular (la B, sin correo, dejaba el camino de la cuenta existente mucho más rápido: el tiempo seguía
  delatándola). `api.py`: si el correo ya tiene cuenta, `register()` llama a `_registro_con_cuenta_existente()`, que
  responde **exactamente** lo mismo que un registro nuevo (200 `{"message": "Codigo enviado", "email": ...}`) y por el
  mismo camino: la primera vez calcula bcrypt (y lo descarta) y envía un correo; un segundo intento antes de 10 minutos
  no calcula ni envía nada (como un registro nuevo con su código vigente, A-09); si el correo falla, el mismo 503 fuera
  de desarrollo y el mismo 200 con `APP_ENV=desarrollo`. **Nunca crea un OTP** para una cuenta que ya existe. El aviso
  (`enviar_aviso_cuenta_existente` en `correo/servicio.py`, plantilla `HTML_AVISO_REGISTRO`, asunto “PetConnect -
  Intento de registro con tu correo”) lleva el nombre **de la cuenta**, no el que se escribió en el formulario (A-05), no
  lleva código y remite a `proyectopetconnect+atencion@gmail.com` si olvidó la contraseña (no hay recuperación). La
  memoria de avisos recientes guarda el SHA-256 del correo en minúsculas (no el correo), como mucho 1.000, con candado,
  y olvida el aviso si no salió para que el siguiente intento lo envíe. Está en la memoria del proceso: con varios
  procesos, en el peor caso un aviso por proceso cada 10 minutos. **Hueco encontrado al revisar:** tras un `/register`
  neutro, bastaba probar un código en `/api/auth/verify`: “No hay verificación pendiente” delataba la cuenta y “Código
  incorrecto”, no. Ahora “sin pendiente”, “vencido” e “incorrecto” responden el mismo 400 “Codigo incorrecto o vencido.
  Si pasaron mas de 10 minutos, vuelve a registrarte” (`/login/verify` no cambia: exige la contraseña antes). La web y el
  móvil no cambian: no miraban el 409 (muestran `data.error`) y con el 200 pasan al paso del código.
  Regresión: `tests/test_registro_neutro.py` (18, BD/DNS/correo y relojes simulados, correos `@ejemplo.test`): misma
  respuesta para correo nuevo y con cuenta (también inactiva o bloqueada), sin OTP ni código enviado, aviso con el
  nombre de la cuenta, bcrypt calculado, segundo intento igual que uno nuevo, de nuevo tras 10 minutos, mayúsculas,
  503/200 igual que uno nuevo sin el correo en el log, memoria con hash y con tope; `/verify` igual sin pendiente,
  vencido e incorrecto; el código correcto sigue creando la cuenta; la plantilla escapa el nombre y no lleva código.
  Se ajustaron 6 pruebas viejas que comparaban los mensajes de `/verify` (`test_endpoints.py`, `test_otp.py`,
  `test_registro.py`; la de “no alarga el vencimiento” ahora comprueba que el pendiente se borró) y la del 409 de
  `test_endpoints.py`. Suite 339 (294 + 45 omitidas). Contraprueba: con el `api.py` anterior (`git stash`) dan error
  52 (las funciones nuevas no existen), así que se hizo además en una copia con un sabotaje a la vez sobre el código
  nuevo, y los 9 se detectan: volver al 409 → fallan 11 (10 de las 18 nuevas + la de `test_endpoints.py`; pasan a
  propósito la de “sin OTP”, porque el 409 tampoco lo creaba, la del tope, las 3 de la plantilla y las 3 de `/verify`,
  que prueban otras partes); mensajes viejos de `/verify` → 5;
  sin bcrypt → 2; sin límite de avisos → 4; aviso con el nombre escrito → 2; sin el 503 → 1; sin olvidar el aviso
  fallido → 1; correo en claro en la memoria → 1; crear un OTP para la cuenta → 3.
  **Riesgos que siguen abiertos (anotados, no son de este ítem):** (1) `/register/resend` pasados 60 s tarda más si hay
  pendiente (envía correo) que para una cuenta existente (nunca tiene pendiente); (2) con 6 códigos malos, solo un
  pendiente real llega al 429 de bloqueo; (3) los tiempos de bcrypt + correo no son idénticos al milisegundo. Taparlos
  del todo exige enviar los correos en segundo plano, lo que cambia el 503 del 2.8 (A-10). Exigen más trabajo y le
  mandan correos al titular, que así se entera. **Hallazgo → ítem 4.18:** `/api/auth/login` revela cuentas por
  tiempo: con un correo sin cuenta responde enseguida y con uno que sí existe calcula bcrypt (~0,3 s) aunque la
  contraseña sea mala. `/api/utils/validar-correo` no revela cuentas (no consulta la BD).

#### A-15 · 🟡 Media · `autocommit=True` vuelve inútiles los `rollback()` [N]
- `config/db_config.py:13` → `autocommit: True`; los DAO llaman `commit()/rollback()` como si hubiera transacciones.
  Una operación de varios pasos no es atómica. El README (`README.md:116,128`) dice `False`.
- **Arreglo:** decidir: `False` + `commit` explícito (lo que documenta el README) o dejar `True` y quitar los `rollback`.
- **Estado: resuelto el 08/11/2026 (ítem 4.9 de PRIORIDADES, en una parte, `a25224d`, solo backend; no toca el esquema ni cierra
  NC).** Antes se buscaron operaciones de varios pasos: cada escritura de los DAO es una sola sentencia con su
  `commit()`, y el `UPDATE ... intentos < 5` de `OtpDAO` es una sola sentencia (no cambia). Los flujos de
  `/register/verify` (crear usuario y luego borrar el OTP) y `/login/verify` usan conexiones distintas, así que el
  autocommit no los afecta, y el orden ya es seguro. La única operación de varios pasos en una conexión es `seed.py`
  (un solo `commit()` al final). Decisión del dueño: **opción B**, `autocommit: False`, que es lo que ya documentaba el
  README. Los DAO no cambian porque ya confirmaban cada escritura; ahora sus `rollback()` sí deshacen y `seed.py` es
  "todo o nada". `conexion/conexion_bd.py` crea el pool con `pool_reset_session=True` explícito: al devolver una
  conexión, la librería (mysql-connector 9.1.0) hace `reset_session()`, que descarta lo no confirmado (incluida la
  transacción que abre un SELECT) y vuelve a aplicar autocommit y `sql_mode`. README: tabla de `DB_CONFIG`, 5.2
  (pool y `commit()`/`rollback()` sobre la conexión prestada), 5.3 (flujo) y el ejemplo de 7.2. Regresión en
  `tests/test_pool.py`, sin BD (5): autocommit apagado; pool con `pool_reset_session=True`; inventario automático por
  el SQL que manda cada método (21 escrituras y 18 lecturas); cada escritura hace `commit()` una vez y las lecturas no;
  con error de la BD no hay `commit()` y la escritura hace `rollback()`. Con MariaDB (2 nuevas + 1 ajustada):
  autocommit = 0 tras devolver la conexión, un INSERT sin `commit()` se descarta al devolverla y `rollback()` deshace
  los dos pasos de una operación. Las conexiones auxiliares de `PruebasPoolEnBD` y `PruebasEsquemaEnBD` fijan
  `autocommit = True` para leer siempre lo último guardado. Suite 321 (276 + 45 omitidas). Contraprueba con
  `git stash` de `db_config.py` y `conexion_bd.py`: fallan 2 (autocommit y `pool_reset_session`) y pasan a propósito
  las 3 de los DAO (protegen los cambios futuros). Además, al quitar a propósito el `commit()` de
  `ProductoDAO.actualizar`, la prueba lo detecta. Las pruebas con MariaDB quedan para que las corra el dueño.

#### A-16 · 🟡 Media · `generate_keys.py` borra el `.env` existente sin preguntar [N]
- `generate_keys.py:41` abre el archivo de entorno en modo `"w"`: si se corre dos veces, **borra** la contraseña de la
  BD y las credenciales de Gmail, y cambia `JWT_SECRET` (cierra todas las sesiones).
- **Arreglo:** si el archivo existe, solo agregar las claves que falten o pedir confirmación.

#### A-17 · 🟡 Media · Política de contraseña sin minúscula — NC-004 [A]
- `api.py:66-77` y `RegisterModal.jsx:8-11`. **Evidencia:** `PETCONNECT1!` es aceptada.
- **Arreglo:** `re.search(r'[a-z]', ...)` en API, web y móvil.
- **Estado: resuelto el 07/11/2026 (ítem 4.1 de PRIORIDADES, en tres partes). NC-004 cerrada.** API (`240116e`): la
  política vive en `security/politica.py` (`validar_contrasena`, un módulo común que la consola podrá usar en el 4.11,
  A-18) y exige la minúscula; `api.py` la importa (el nombre `_validate_password` queda como alias porque lo usa la
  evidencia del AA2) y `/register` responde 400 a `PETCONNECT1!` antes de la BD, el hash y el correo. El mensaje del
  carácter especial ahora nombra los 12 aceptados (antes omitía `- _ * .`). Web (`680797e`): `RegisterModal.jsx` usa
  `src/utils/contrasena.js` (agrega minúscula y máximo 64). Móvil (`43fcfe1`): `RegisterScreen.js` valida con la copia
  `src/utils/contrasena.js` antes de enviar y muestra los requisitos. Mayúscula y minúscula son solo `A-Z`/`a-z`, y las
  utilidades JS cuentan los emojis como Python. Regresión: `tests/test_politica.py` (17), `contrasena.test.js` (13) y
  `contrasena.test.mjs` (8). Contraprueba con `git stash`: con el código anterior fallan 2 en la API, 1 en la web y 2
  en el móvil; las de la utilidad pasan a propósito. Detalle en la GA9 (NC-004).

#### A-18 · 🟡 Media · La consola registra usuarios saltándose las reglas [N]
- `vista/menu_usuarios.py:61` usa `input()` para la contraseña (**se ve en pantalla**; usar `getpass`), le hace
  `.strip()` (la API no, así que la misma contraseña puede no coincidir) y **no aplica** `_validate_password` ni pide
  autorización de datos.
- **Arreglo:** mover la validación a un módulo común (`security/politica.py`) y usarlo en API y consola.
- **Estado: resuelto el 08/11/2026 (ítem 4.11 de PRIORIDADES, commit `3e814e3`; solo backend, no toca el esquema;
  no cierra NC).**
  Decisiones del dueño (las recomendadas): (1) la consola **no** da la autorización de datos en nombre del titular
  (Ley 1581, art. 9; política C.6 y C.10): guarda `acepta_datos = False` explícito, sin fecha ni versión, y avisa que el
  titular la dará al iniciar sesión (3.5); (2) nombre, apellidos y formato del correo con las reglas de la API, sin
  DNS; (3) correo repetido: “Ese correo ya tiene una cuenta”, sin repetir el correo; (4) la contraseña se pide dos
  veces. `vista/menu_usuarios.py`, `_registrar_usuario()`: contraseña con `getpass` (no se ve) y sin `.strip()`, pasa
  por `validar_contrasena` (`security/politica.py`); valida antes de la BD y busca el correo antes de pedir la
  contraseña (sin bcrypt ni `INSERT` si ya existe); ante cualquier error vuelve al menú sin guardar. Módulo común nuevo
  `security/datos_usuario.py` (`validar_nombre`, `validar_formato_correo`, sacados de `api.py`): la consola no importa
  `api.py` (A-41); `api.py` lo importa (`_validar_nombre` queda como alias y `_validar_correo` hace el formato con la
  función común y luego el DNS). Regresión: `tests/test_consola_registro.py` (26, sin BD, sin `.env`, sin DNS).
  Suite 365 (320 + 45 omitidas). Contraprueba con `git stash`: con la consola anterior fallan 13 (registraba
  `PETCONNECT1!` y `Abc12!x`, pedía la contraseña con `input()`, le quitaba los espacios, no avisaba de la autorización
  ni del correo repetido) y pasan a propósito 13 (módulo común, valores que el código viejo ya guardaba bien); con el
  `api.py` anterior falla 1 (la API no usaba la función común). Queda: un `INSERT` simultáneo del mismo correo aún
  imprime el mensaje de MySQL desde el DAO (4.15). Hallazgo → 4.19 (“6. Actualizar usuario” no valida nombre ni correo).

#### A-19 · ⚪ Baja · Búsqueda de proveedores devuelve inactivos — NC-011
- `dao/proveedor_dao.py:49-54` (falta `AND activo = TRUE`, que sí tiene `:56-62`). Una línea.
- **Estado: resuelto el 07/11/2026 (ítem 4.2 de PRIORIDADES, commit `06a422d`; solo backend). NC-011 cerrada.**
  `_BUSCAR_POR_NOMBRE` filtra `activo = TRUE`, como la búsqueda por ciudad. Mejora aprobada por el dueño:
  `buscar_por_nombre` escapa `!`, `%` y `_` (`ESCAPE '!'`), así que `%` y `_` ya no actúan como comodines.
  Regresión: `tests/test_proveedores.py` (5 pruebas, BD simulada); con el DAO anterior fallan 3 y pasan a propósito
  2 (consulta parametrizada y mapeo de filas). Solo la usa la consola; la web y el móvil no cambian.

### 3.3 Datos personales (Ley 1581) y contenido

#### A-20 · 🟠 Alta · Autorización de datos falsa — NC-005 [A]
- `api.py:409` crea el usuario con `acepta_datos=True` fijo; `modelo/usuario.py:10` también lo trae en `True` por
  defecto. Ni la web ni el móvil tienen casilla.
- **Arreglo:** casilla **sin marcar** con enlace a la política; la API rechaza el registro sin ella; guardar fecha y versión.
- **Estado: resuelto el 06/11/2026 (ítem 3.1 de PRIORIDADES, en 3 partes: API + BD, web y móvil). NC-005 cerrada.**
  Borrador de la política v1.0: [POLITICA-TRATAMIENTO-DATOS-v1.0-BORRADOR.md](../Legal/POLITICA-TRATAMIENTO-DATOS-v1.0-BORRADOR.md)
  (texto para publicar, textos de la casilla y del aviso, especificación y decisiones pendientes: responsable, correo
  de contacto, alojamiento y mayoría de edad). Lo deben validar el dueño y el instructor antes de publicarlo.
  `api.py`: `/register` exige `"acepta_datos": true` (solo el booleano JSON) antes del DNS, la BD y el correo; si no,
  400 “Debes autorizar el tratamiento de tus datos personales para registrarte” sin código ni pendiente. La versión la
  fija el servidor (`VERSION_POLITICA_DATOS = "1.0"`); la fecha (la de `/register`) y la versión viajan en el pendiente
  y `/verify` las escribe; un pendiente sin ellas no se vuelve cuenta (doble barrera). Como `/register` no toca un
  pendiente vigente (2.7), la validación va antes de esa revisión. `modelo/usuario.py`: `acepta_datos=False` por
  defecto. `dao/usuario_dao.py`: el `INSERT` guarda la prueba. `sql/schema.sql`: `acepta_datos NOT NULL DEFAULT 0`,
  `fecha_autorizacion_datos`, `version_politica_datos` y regla `chk_autorizacion_datos`. Migración
  `sql/migraciones/2026-11-05_autorizacion_datos.sql` (aplicada por el dueño con respaldo previo: los 10 usuarios de
  la BD de desarrollo quedaron en `acepta_datos = 0` sin fecha; no se inventó ninguna autorización).
  Decisiones del dueño: tres partes (API + BD, web, móvil), el cliente manda solo el booleano, los usuarios existentes
  quedan en 0 y pedirles la autorización queda para después (contingencia del R05 del plan GA9). Prueba de regresión:
  `tests/test_registro_datos.py` (7) y `tests/test_esquema.py` (7 sin BD, 4 con MariaDB). Contraprueba: con el `api.py`
  anterior fallan 5 de 7 (9 casos); con el modelo y el DAO anteriores, 3 de 7; con el `schema.sql` anterior, 4 (6 casos);
  pasan a propósito las que dependen de otro archivo y las 3 que solo leen la migración. Con MariaDB temporal: 10 de 10
  OK. Suite: 125 pruebas, 110 OK y 15 omitidas que requieren MariaDB.
  **Web (parte 2, 05/11/2026):** `RegisterModal.jsx` tiene, antes del botón, la casilla **sin marcar** “Soy mayor de 18
  años, he leído la Política de tratamiento de datos personales y autorizo…” (D.4: la edad va en la misma casilla), con
  el enlace a `/politica-de-datos` en una pestaña nueva y el aviso corto B.2 debajo. Sin marcar: mensaje B.3 con
  `role="alert"`, foco en la casilla y **ninguna** petición a la API. `src/services/api.js` manda `acepta_datos` solo como
  booleano (`=== true`). Página nueva `src/pages/PoliticaDatos.jsx` (ruta en `App.jsx`, enlace en `Footer.jsx`) con la
  Parte A, rotulada “Borrador en revisión” y con los datos de D.3 y D.5 como “Por definir” (D.1 se completó el 06/11/2026). El modal se desplaza si
  no cabe a 375 px. Decisiones de la parte 2: página propia en JSX (no leer el `.md`, que exigiría una librería nueva), los
  pendientes visibles como “Por definir”. El 06/11/2026 el dueño decidió el correo de atención (`proyectopetconnect+atencion@gmail.com`, D.1),
  que ya aparece en la política (secciones 1 y 8) y en el aviso B.2.
  `npm run lint` 0 errores (2 avisos de siempre), `npm run build` OK, revisión a 375 y 1280 px con respuestas simuladas,
  `/impeccable audit` 17/20. La web no tiene pruebas automáticas (regresión manual). Prueba con la API real (dueño,
  05/11/2026, tras reiniciar la API: el 500 de `/verify` del intento anterior era la API corriendo con el código viejo):
  sin la casilla → 400; el enlace abre la política en otra pestaña; con la casilla → código → cuenta creada; conteo
  `0 | 10 | 0` y `1 | 1 | 1`.
  **Móvil (parte 3, 05 y 06/11/2026):** `src/screens/RegisterScreen.js` tiene, antes de “Registrarme”, la casilla **sin
  marcar** (`Pressable` con `role="checkbox"` y `aria-checked`, más de 44 px de alto) con el texto B.1 (+18), el enlace
  en su propia línea “Leer los términos y condiciones que aceptas: Política de tratamiento de datos personales” (abre
  `/politica-de-datos` en el navegador del celular con `Linking.openURL`) y el aviso B.2. Sin marcar: mensaje B.3 en una
  zona `aria-live="polite"` y **ninguna** petición. `src/services/api.js`: `acepta_datos: aceptaDatos === true` y
  `POLITICA_URL` (`http://${HOST}:5173/politica-de-datos`; solo desarrollo, A-27). El formulario va en `ScrollView` +
  `KeyboardAvoidingView` (`behavior="padding"`, desplazamiento medido con `measureInWindow`), porque en Expo 57 la ventana
  de Android no se encoge con el teclado. Decisiones del dueño: enlace aparte (dentro de la casilla, TalkBack lo leería
  como un solo elemento y no podría abrirlo) y que el enlace mencione “términos y condiciones” además del nombre de la
  política; sin librerías nuevas (`expo-web-browser`, casillas) ni copia de la política dentro de la app. Se usan
  `role`/`aria-*` en lugar de `accessibilityRole`/`accessibilityState` porque `react-native-web` no traduce
  `accessibilityState` y en React Native 0.86 hacen lo mismo en Android. El móvil no tiene pruebas automáticas ni linter
  (regresión manual): `npx expo export --platform web` sin errores; a 375 px con la API simulada, sin marcar → mensaje y
  0 peticiones a `/api/auth/`, marcada → 1 petición con `"acepta_datos": true` (booleano). `/impeccable audit` 15/20:
  foco a la casilla tras el error, colores fijos y solo modo claro (de toda la app), sin `android_ripple` y enlace de
  44 px (Material pide 48 dp); ninguno bloquea la NC. Prueba con la API real en el emulador Android (Pixel 7), ejecutada
  por el dueño el 06/11/2026: el enlace abrió la política; registro con la casilla marcada → código → cuenta creada y
  sesión iniciada; conteo tras borrar el dueño sus cuentas de prueba anteriores: `0 | 5 | 0` y `1 | 1 | 1`. El caso “sin
  marcar” se verificó en la compilación web (mismo código), no en el emulador.
  Entorno del emulador (solo en el PC del dueño, nada en git): `android/local.properties` con `sdk.dir` (faltaba
  `ANDROID_HOME`) y `JAVA_HOME` apuntando al Java 21 de Android Studio (`jbr`) en la terminal de `npm run android`: con
  el Java 25 del sistema falla `configureCMakeDebug`.
  Pendiente fuera de la NC: pedir la autorización a las cuentas existentes al iniciar sesión (ítem 3.5); nunca con un
  `UPDATE` que la invente.
  **Ítem 3.5, parte 1 de 3 (API + DAO, 06/11/2026; riesgo R05; opción (a) aprobada por el dueño):** `/api/auth/login`,
  después de comprobar la contraseña y el estado de la cuenta (así el 403 no revela si la cuenta existe), revisa si la
  autorización está vigente (`acepta_datos` = 1 **y** `version_politica_datos` = `VERSION_POLITICA_DATOS`). Si no lo
  está y el cuerpo no trae `"acepta_datos": true` (solo el booleano), responde 403 `{"error": "Para seguir usando tu
  cuenta debes autorizar el tratamiento de tus datos personales", "requiere_autorizacion": true}` sin enviar código. Con
  la casilla, la fecha (la de `/login`) y la versión viajan en el pendiente del OTP; `/api/auth/login/verify` las
  escribe con `UsuarioDAO.registrar_autorizacion` (un `UPDATE` parametrizado de las tres columnas juntas) **solo** con
  el código correcto, y sin una prueba válida (sin fecha, de otra versión o de otro usuario) responde el mismo 403 sin
  token (doble barrera); si no se puede guardar, 500 sin token. Una cuenta ya autorizada entra igual que antes y su
  fecha original no se toca. Los `SELECT` de `UsuarioDAO` ahora leen la fecha y la versión. Nunca se “autoriza” una
  cuenta en bloque. Prueba de regresión: `tests/test_login_datos.py` (12) y en `test_esquema.py`
  `test_autorizacion_al_iniciar_sesion_con_la_base_real` (MariaDB temporal). Contraprueba con `git stash` de un
  archivo a la vez: con el `api.py` anterior fallan 5 de las 9 pruebas de la API (23 casos con los subcasos); con el
  `dao/usuario_dao.py` anterior fallan las 3 del DAO; pasan con ambos códigos, a propósito, la contraseña mala (401),
  la cuenta inactiva, la cuenta ya autorizada y el código incorrecto, que ya funcionaban. Suite: 153 pruebas, 132 OK y
  21 omitidas que requieren MariaDB. `tests/test_logs.py` usa ahora un usuario falso con la autorización 1.0. Riesgos
  que siguen: un token entregado antes del cambio vale hasta 24 h (4.13) y la consola no la pide (4.11). Faltan la web
  (parte 2) y el móvil (parte 3); si la persona no autoriza, la app le ofrecerá escribir al correo de atención para
  borrar su cuenta (proceso manual, C.8; decisión del dueño).
  **Ítem 3.5, parte 2 de 3 (web, 06/11/2026):** la casilla del registro (texto B.1 con +18, enlace a la política en
  pestaña nueva y aviso B.2) pasó a un componente propio, `src/components/CasillaAutorizacion.jsx`, que usan
  `RegisterModal.jsx` (sin cambio visible) y `LoginModal.jsx`: el texto legal vive en un solo archivo. Cuando
  `/login` responde 403 con `requiere_autorizacion`, el modal muestra el paso “Autoriza el uso de tus datos” con el
  mensaje de la API, la casilla **sin marcar**, “Autorizar y continuar” (repite `/login` con el mismo correo y
  contraseña y `"acepta_datos": true`), “Cancelar” (vuelve al formulario y borra la contraseña escrita) y la línea B.3
  “Si no quieres autorizarlo, escríbenos a … y borraremos tu cuenta” con enlace `mailto:`. Sin marcar: “Para continuar
  debes autorizar el tratamiento de tus datos personales.” (`role="alert"`), foco en la casilla y **ninguna**
  petición. Si `/login/verify` responde ese 403 (la versión cambió mientras llegaba el código), vuelve al paso de la
  casilla. `src/services/api.js`: `loginUser(email, password, aceptaDatos)` manda `acepta_datos` solo si
  `aceptaDatos === true`, y el error lleva `requiereAutorizacion` solo si la API mandó `requiere_autorizacion: true`
  (el 403 “Cuenta inactiva” no lo trae). `AuthContext.jsx`: `login(email, password, aceptaDatos)`. Regresión:
  `tests/api.test.js` (5 pruebas nuevas, `fetch` simulado) y `tests/casilla-autorizacion.test.js` (3, leen el texto de
  los archivos: la frase “Soy mayor de 18 años” solo en el componente, los dos modales lo usan y el inicio de sesión
  tiene los mensajes de B.3). Contraprueba con `git stash` de los 4 archivos y sin el componente: fallan 7 de las 8
  nuevas; pasa a propósito “sin la casilla NO manda acepta_datos” (el código viejo nunca lo mandaba; la prueba impide
  que se empiece a mandar siempre). `npm test` 20 de 20, lint 0 errores (los 2 avisos de siempre), build OK; revisión
  a 375 px con la API simulada en el navegador: sin marcar, 0 peticiones nuevas; marcada, 1 petición con
  `"acepta_datos": true` y paso al código; 403 en `/login/verify` → vuelve a la casilla sin marcar; “Cancelar” deja la
  contraseña vacía; el registro conserva su casilla sin marcar; sin desborde horizontal. `/impeccable audit` 16/20
  (detector sin hallazgos; pulido opcional: al cambiar de paso el foco queda en `body` y los modales no tienen
  `role="dialog"`, como ya se anotó en el 2.7; colores fijos sin modo oscuro, como toda la web). Arreglo de una
  revisión del 06/11/2026: “Cancelar” queda desactivado mientras se envía la petición (si se cancelaba a mitad, al
  llegar la respuesta salía igual la pantalla del código). Prueba con la API real, ejecutada por el dueño el 06/11/2026
  con una API recién arrancada (la que ocupaba el puerto 5000 era un proceso viejo, anterior al cambio de `api.py`): la
  cuenta 18 (`acepta_datos = 0`) inició sesión en la web, vio “Autoriza el uso de tus datos”, marcó la casilla, escribió
  el código y quedó con `acepta_datos = 1` y su fecha; la cuenta 19, creada desde el registro web con la casilla, quedó
  autorizada; la 17 sigue en 0. Conteo esperado `0 | 6 | 0` y `1 | 3 | 3` (deducido, no se corrió la consulta final).
  El caso “sin marcar” no se capturó con la API real: lo cubren las pruebas automáticas y la API simulada.
  **Ítem 3.5, parte 3 de 3 (móvil, 06/11/2026) — con ella el 3.5 queda hecho y la contingencia del R05 completa en
  API, web y móvil.** La casilla del registro pasó a `src/components/CasillaAutorizacion.js` (texto B.1, enlace aparte a
  la política y aviso B.2 en un solo archivo), que usan `RegisterScreen.js` (sin cambio visible) y `LoginScreen.js`.
  Cuando `/login` responde 403 con `requiere_autorizacion`, la pantalla muestra el paso “Autoriza el uso de tus datos”
  con el mensaje de la API, la casilla **sin marcar**, “Autorizar y continuar” (repite `/login` con `"acepta_datos":
  true`), “Cancelar” (vuelve al formulario y borra la contraseña; desactivado mientras se envía) y la línea B.3 con un
  enlace aparte que abre el correo (`mailto:`) para pedir que se borre la cuenta. Sin marcar: el mensaje B.3 en una
  zona `aria-live` y **ninguna** petición. Si `/login/verify` responde el 403, vuelve a la casilla sin marcar. Como
  `api.js` importa `react-native` y Node no puede cargarlo, las piezas que se prueban pasaron a JavaScript puro en
  `src/utils/peticiones.js`: `errorDeApi` (el error lleva `status` y `requiereAutorizacion` solo si la API mandó
  `requiere_autorizacion: true`; el 403 “Cuenta inactiva” no) y `cuerpoLogin` (`acepta_datos` solo con `true`).
  `AuthContext.js` no cambió. Regresión: `tests/peticiones.test.mjs` (5) y `tests/casilla-autorizacion.test.mjs` (4,
  leen el texto: “Soy mayor de 18 años” solo en el componente, las dos pantallas lo usan, la casilla empieza sin marcar
  y el inicio de sesión tiene `requiereAutorizacion` y los textos de B.3). Contraprueba con `git stash` de `api.js` y
  las dos pantallas y sin el componente: fallan 5 de las 9 nuevas; pasan a propósito las 4 que solo prueban el archivo
  nuevo `peticiones.js` (sin él, fallan todas). `npm test` 16 de 16; `npx expo export --platform web` sin errores;
  revisión a 375 px con la API simulada: sin marcar, 0 peticiones nuevas; marcada, 1 petición con `"acepta_datos":
  true` y paso al código; 403 en `/login/verify` → casilla sin marcar; “Cancelar” deja la contraseña vacía; código
  correcto → sesión iniciada; el registro conserva su casilla; sin desborde horizontal. `/impeccable audit` 14/20
  (pulido opcional: el mensaje del 403 en gris sobre el fondo gris ≈ 4,3:1, enlaces de 44 px y no 48 dp, sin
  `android_ripple`, colores fijos sin modo oscuro como toda la app). Prueba en el emulador Android (Pixel 7) con la API real,
  ejecutada por el dueño el 07/11/2026: la cuenta 17 (`acepta_datos = 0`) inició sesión, vio la casilla, la marcó
  (“Cancelar” quedó gris mientras se enviaba), escribió el código y quedó con `acepta_datos = 1` y su fecha
  (2026-11-07 01:32:37; consulta por `id_usuario`, sin correos). El caso “sin marcar” no se capturó con la API real:
  lo cubren las pruebas automáticas y la API simulada.

#### A-21 · 🟠 Alta · Formularios que fingen enviar datos personales [N]
- **Solicitud de adopción** (`PetDetail.jsx:56-60`) y **Contacto** (`Contact.jsx:15-17`) piden nombre, correo, teléfono y
  mensaje y muestran *“Solicitud enviada. Nos pondremos en contacto contigo pronto”*… **sin enviar nada**.
  Lo mismo el **checkout** (`Checkout.jsx:41-45`) [A].
- **Impacto:** una persona que quiere adoptar cree que ya aplicó; además se recogen datos sin aviso de privacidad.
- **Arreglo:** o se implementa el endpoint (con consentimiento y `@require_auth`), o se rotula claramente **“Demo — no
  se envía”** y se deshabilita el botón.
- **Estado: resuelto el 06/11/2026 (ítem 3.2 de PRIORIDADES) con el camino “rotular”; solo web.** Decisión del dueño:
  rotular y bloquear ahora, sin recoger datos, y dejar el envío real para el ítem futuro 3.6 (API + tabla +
  consentimiento + política v1.1). Componente nuevo `src/components/AvisoDemo.jsx` (recuadro `role="note"` con el título
  “Demo — …”, el motivo y, si se pide, una línea con el correo de atención de la D.1 como alternativa real).
  `PetDetail.jsx`: el botón “Solicitar Adopción” abre el formulario con el aviso “Demo — la solicitud no se envía” y la
  invitación “Si te interesa adoptar a {nombre}, escríbenos a proyectopetconnect+atencion@gmail.com”; los 4 campos van
  dentro de `<fieldset disabled aria-describedby>` (no se puede escribir ni enviar), el botón queda deshabilitado
  (“No disponible (demo)”) y se quitaron el estado `submitted`, el estado del formulario y la pantalla “Solicitud
  Enviada… Nos pondremos en contacto contigo pronto”. `Contact.jsx`: igual (“Demo — el mensaje no se envía”), sin la
  pantalla “Mensaje Enviado… Responderemos”, y la columna de contacto cambió los datos inventados
  (`info@petconnect.com`, `+57 300 123 4567`, Bogotá: un dominio ajeno al proyecto) por el correo de atención (enlace
  `mailto`) y Armenia, Quindío (D.1). El teléfono de la D.1 no se puso en la página (expone menos; se puede agregar si el
  dueño lo decide). `Checkout.jsx`: aviso “Demo — no se procesan pedidos”, campos bloqueados, botón “Pedido no
  disponible (demo)” y el carrito **ya no se vacía**. `Confirmation.jsx` (“Pedido Confirmado… Recibirás un correo”) se
  borró junto con su ruta `/confirmacion` en `App.jsx`. Los envíos tienen además `onSubmit` con `preventDefault()`
  (segunda barrera). Nada de lo escrito se guarda en `localStorage` (no se puede escribir, y antes tampoco se guardaba).
  Verificación (la web no tiene pruebas automáticas): `npm run lint` 0 errores (los 2 avisos de siempre) y
  `npm run build` OK. Búsqueda de textos engañosos (`enviad[ao]`, `recibimos`, `recibirás`, `nos pondremos en
  contacto`, `responderemos`, `pedido confirmado`, `procesado exitosamente`) en `src/`: con el código viejo (HEAD) 7
  coincidencias en `PetDetail`, `Contact` y `Confirmation`; con el nuevo, ninguna en los formularios (queda una en
  `PoliticaDatos.jsx`, correcta: habla del correo de atención, que sí existe). Revisión a 375 px y a escritorio en el
  navegador: sin desplazamiento horizontal, todos los campos y botones `:disabled`, aun forzando `click()` y
  `requestSubmit()` el checkout sigue en `/checkout` con el carrito intacto, y ninguna petición `POST` a `/api`;
  `/confirmacion` ya no muestra nada. `/impeccable audit` 16/20 (detector sin hallazgos); queda como pulido, ya
  existente antes: al abrir el formulario de adopción el foco cae en `body`, el horario de atención de `Contact.jsx` es
  inventado y la web no tiene modo oscuro ni tokens de color.
- **Envío real (ítem 3.6, hecho y probado con la API real el 07/11/2026; 3 partes: API + BD, web y móvil).** Decisiones del dueño (07/11/2026): adopción
  **y** contacto; solo con sesión iniciada (el nombre y el correo salen de la cuenta); las solicitudes solo se guardan
  en la BD y el equipo las lee con SQL (no van por correo ni a quien publicó la mascota); mensaje y **teléfono
  opcional** (solo adopción); **sin casilla aparte**, con un aviso corto (B.5), porque vale la autorización de la
  cuenta con la política **1.1**, que nombra esta finalidad; `VERSION_POLITICA_DATOS` sube a `"1.1"` en la parte 1
  (toda cuenta que aceptó la 1.0 autoriza otra vez al iniciar sesión, ítem 3.5); el móvil entra como parte 3.
  **Parte 1 de 3 (API + BD), hecha el 07/11/2026:** tabla nueva `solicitudes` (`id_usuario`, `tipo`
  adopcion/contacto, `id_mascota`, `telefono`, `mensaje` de máximo 1000, `version_politica_datos`, `fecha_envio`;
  regla `chk_solicitud_tipo`; `ON DELETE CASCADE` desde la cuenta y la mascota; no repite nombre ni correo) en
  `sql/schema.sql` y en la migración `sql/migraciones/2026-11-07_solicitudes.sql` (solo crea la tabla), explicada en
  `sql/README.md`. `dao/solicitud_dao.py` (SQL parametrizado; a diferencia de los DAO viejos deja subir los errores de
  la BD, como pide el 4.15). `api.py`: `POST /api/solicitudes/adopcion` (`id_mascota`, `mensaje`, `telefono`
  opcional) y `POST /api/solicitudes/contacto` (`mensaje`), con el limitador (5 por minuto por IP) y `@require_auth`;
  validan el mensaje (10 a 1000 caracteres), la mascota (entero) y el teléfono (números, espacios y un `+` al inicio,
  7 a 15 dígitos) antes de tocar la BD; después revisan la cuenta en la BD (activa y con la autorización de la versión
  vigente: un token de antes de la 1.1 vale 24 h; si no, 403 con `"requiere_autorizacion": true`), que la mascota esté
  en adopción (si no, el mismo 404 de la ficha) y que no sea la propia (400). Responden 201 solo si la fila se guardó,
  con el usuario del token (nunca del cuerpo), la versión que aceptó la cuenta y la fecha; contacto no guarda mascota
  ni teléfono. Los registros técnicos no llevan el mensaje ni el teléfono. Borrador de la política en versión 1.1
  (A.4, A.5 punto 7, A.6, A.11, A.14, B.3, B.5, C.12 a C.15 y una fila en la Parte E). Pruebas: `tests/test_solicitudes.py`
  (19: 15 de las rutas con la BD simulada y 4 del DAO), `test_esquema.py` (+7: tabla y migración sin BD, y 3 con
  MariaDB que corre el dueño), `test_limite.py` (las 2 rutas nuevas) y las de los ítems 3.1 y 3.5 ajustadas a la 1.1
  (en `test_login_datos.py`, una cuenta que aceptó la 1.0 ahora debe autorizar otra vez). Suite: 179 pruebas, 155
  correctas y 24 omitidas que necesitan MariaDB. Contraprueba (`git stash` de `api.py` y `schema.sql`): fallan 27
  (las 15 de las rutas, 4 del esquema, el límite, 4 del login y 3 del registro por la versión); pasan a propósito las
  4 del DAO y 2 de la migración, que prueban archivos nuevos que no se guardaron en el stash.
  **Parte 2 de 3 (web), hecha el 07/11/2026:** componente nuevo `src/components/FormularioSolicitud.jsx`, el único
  formulario de solicitudes de la web, que usan `PetDetail.jsx` (adopción, con teléfono opcional) y `Contact.jsx`
  (contacto). Sin sesión no muestra campos: pide iniciar sesión o crear cuenta. Con sesión muestra “Envías como
  {nombre} ({correo})”, el mensaje con contador, el aviso B.5 (enlace a la política y al correo de atención) y valida
  en el navegador con `src/utils/solicitud.js` (las mismas reglas de la API) antes de llamar a `api.js`
  (`enviarSolicitudAdopcion`, `enviarMensajeContacto`). Dice “Solicitud enviada” / “Mensaje enviado” **solo** tras la
  respuesta 201; con un error lo muestra en `role="alert"` (con foco) sin borrar lo escrito, y con 401 o con el 403 de
  autorización ofrece “Volver a iniciar sesión”. `AvisoDemo` queda solo en el checkout (A-26). `PoliticaDatos.jsx` pasa
  a la versión 1.1 con los textos nuevos. Pruebas: `tests/solicitudes.test.js` (9), que también exige la misma versión
  en la página, en `api.py` y en el borrador; con el código anterior fallan 5 (pasan a propósito 4 que prueban archivos
  nuevos). `npm test` 29/29, lint 0 errores, build OK. Revisado a 375 px con la API simulada y datos inventados (vacío y
  teléfono inválido → 0 peticiones; 403 → mensaje y botón, nada “enviada”; 201 → recuadro verde; 401 → cierra sesión y
  abre el inicio de sesión) y sin desplazamiento horizontal. `/impeccable audit` 16/20 (pulido opcional: el foco cae
  en `body` al abrir o cerrar el formulario de adopción, colores fijos sin modo oscuro).
  **Prueba con la API real (dueño, 07/11/2026):** migración aplicada en su BD (`SHOW COLUMNS FROM solicitudes`: las 8
  columnas de `schema.sql`) y respaldo hecho. Al principio la ruta respondía 404: seguía viva una API del 06/11 sin el
  código nuevo y atendía el puerto 5000; al cerrarla, la ruta sin token respondió 401. Luego, con su sesión, envió una
  solicitud de adopción para Luna y la web mostró “Solicitud enviada… número 1”. Como la API solo responde 201 tras
  guardar la fila y con la autorización 1.1, eso confirma la fila y el cambio de versión (C.9) con datos reales. El
  mensaje de contacto y el conteo no se capturaron (lo cubren las pruebas automáticas).
  **Parte 3 de 3 (móvil), hecha el 07/11/2026:** el dueño eligió poner Contacto como **pestaña nueva** (Tienda,
  Adopción, Contacto, Perfil). Componente nuevo `src/components/FormularioSolicitud.js`, el único formulario de
  solicitudes del móvil y el único lugar con el aviso B.5, que usan `PetDetailScreen.js` (botón “Solicitar adopción”,
  con teléfono opcional) y la pantalla nueva `ContactScreen.js`. Hace lo mismo que el de la web: sin sesión no muestra
  campos (“Inicia sesión para enviar” / “Crear cuenta”); con sesión, “Envías como {nombre} ({correo})”, contador del
  mensaje, aviso B.5 con la política (`Linking.openURL(POLITICA_URL)`) y el correo de atención en filas aparte (para
  que TalkBack los active solos); valida antes con `src/utils/solicitud.js`, **copia** de la web; dice “enviada” solo
  tras el 201; con 401 o con el 403 de autorización ofrece “Volver a iniciar sesión”, y sin conexión muestra un
  mensaje en español (no el “Network request failed” de React Native). Para no perder lo escrito, el inicio de sesión
  se abre como **modal** encima de la ficha o de Contacto (pantalla `IniciarSesion` en `AppNavigator.js`, con el mismo
  Login y Registro) y se cierra solo al entrar; mandar a la pestaña Perfil habría cerrado la ficha de la mascota.
  `api.js` y `utils/peticiones.js`: `enviarSolicitudAdopcion` / `enviarMensajeContacto` con los mismos cuerpos que la
  web (sin nombre ni correo; el token lo pone `apiFetch`). Pruebas: `tests/solicitudes.test.mjs` (11; `npm test`
  27/27), una de ellas exige que la copia de `solicitud.js` sea igual a la de la web. Contraprueba (`git stash` de
  `api.js`, `peticiones.js`, `PetDetailScreen.js` y `AppNavigator.js`): fallan 4; pasan a propósito 7 que prueban
  archivos nuevos. `npx expo export --platform web` OK. Revisado a 375 px con la API simulada y datos inventados: sin
  sesión, vacío y teléfono con guiones (0 peticiones), 401 → “Volver a iniciar sesión” abre el modal y, al entrar, el
  texto sigue ahí; 403 → mensaje y botón, nada “enviada”; 201 → recuadro verde con el número, en adopción y contacto;
  sin desplazamiento horizontal. `/impeccable audit` 14/20 (pulido opcional, como el resto del móvil: colores fijos sin
  modo oscuro, iconos emoji en las pestañas, enlaces de 44 px y no 48 dp, sin `android_ripple`).
  **Prueba con la API real en el emulador Pixel_7 (dueño, 07/11/2026):** la API respondió 401 a un POST sin token
  (una sola API en el puerto 5000) y la app mostró las 4 pestañas. Con la sesión de la cuenta del dueño: en Contacto,
  enviar vacío → aviso rojo y nada enviado; con texto → “Mensaje enviado… número 2”. En la ficha de Luna, un mensaje
  de 6 letras → aviso rojo; con un mensaje válido y teléfono → “Solicitud enviada… número 3”. Los números vienen de la
  BD (el 1 fue la prueba web), así que las dos filas quedaron guardadas. El 401/403 con la API real y el conteo con
  `SELECT` no se capturaron (lo cubren las pruebas y la API simulada). Detalle de uso visto en la prueba (web y
  móvil): el aviso rojo de validación sigue visible mientras se corrige el campo, hasta volver a tocar “Enviar”.

#### A-22 · 🟡 Media · Información de salud contradictoria en la ficha de la mascota [N]
- La API pone siempre `vaccinated=False`, `sterilized=False`, `size="Mediano"` (`api.py:215-220`), así que
  `PetDetail.jsx:115-129` muestra **“Pendiente de vacunación / esterilización”** a Luna, Milo y Max, cuyas
  descripciones dicen “Vacunada, esterilizada…”.
- Además `seed.py:61-79` guarda “Tamaño Grande/Mediano/Pequeño” **en la columna `color`** (el comentario de
  `seed.py:59` no coincide con las tuplas).
- **Arreglo:** columnas reales (`vacunada`, `esterilizada`, `tamano`) o no mostrar el dato; corregir la semilla;
  pasar los textos por `/revision-contenido-mascotas` (regla 6: validación veterinaria).
- **Estado: resuelto el 06/11/2026 (ítem 3.4 de PRIORIDADES, en 3 partes). Parte 1 de 3 (backend) hecha el 06/11/2026.** Decisión del dueño:
  opción (a), **no mostrar** vacunación, esterilización ni tamaño (descartadas: columnas nuevas, que obligan a validar
  cada dato de salud y nadie las llenaría, y solo `tamano`, que cambia la estructura y deja la API rota en una BD sin
  migrar). `api.py`: `_mascota_to_dict` ya no agrega `vaccinated`, `sterilized` ni `size`; las 3 rutas de mascotas
  devuelven solo los 9 campos de la consulta. `seed.py`: `color` en `None` (no se inventa el color) y 10 textos marcados
  `# REVISAR-VETERINARIO` (Luna, Milo, Nala, Max y Cleo; los dos alimentos, la cama “ortopédica”, el shampoo
  hipoalergénico y el hueso dental); fotos anotadas como Unsplash. `/revision-contenido-mascotas`: sin datos personales
  expuestos; **pendiente de validación veterinaria** antes de publicar. Hallazgo al aplicar: en la BD de desarrollo las 6
  mascotas no venían de ningún `seed.py` del repositorio (textos sin tildes, `color` “Grande/Mediano/Pequenio”, Nala con
  `edad_aprox = 6` siendo una gatita de 6 meses) y su dueño es el usuario 5, no la cuenta del refugio. Migración
  `sql/migraciones/2026-11-06_mascotas_ejemplo.sql`: `color` → `NULL` y Nala 6 → 0, reconociendo las 6 mascotas de
  ejemplo por nombre + especie + `en_adopcion` (no por id ni dueño); aplicada por el dueño con respaldo previo: 6 de 6
  con `color` `NULL` y Nala en 0; la API devuelve `Nala, 0` y ningún campo inventado. Pruebas: `tests/test_ficha_mascota.py`
  (3 rutas sin campos inventados, semilla sin tamaño en `color` y textos de salud marcados) y `tests/test_esquema.py`
  (`PruebasMigracionEjemploSinBD`, `PruebasMigracionEjemploEnBD` con MariaDB temporal y
  `test_seed_no_guarda_el_tamano_en_color`). Total 140 (120 OK + 20 omitidas sin MariaDB); con MariaDB, corridas por el
dueño: `PruebasEsquemaEnBD` + `PruebasMigracionEjemploEnBD`, 12 de 12 OK. Contraprueba: con el `api.py`
  y el `seed.py` viejos fallan las 6 pruebas nuevas de `test_ficha_mascota.py` (28 subcasos); sin el archivo de la
  migración fallan sus pruebas.
  **Parte 2 de 3 (web) hecha el 06/11/2026:** función nueva `src/utils/mascota.js` (`formatearEdad`: 0 → “Menos de 1
  año”, 1 → “1 año”, 2 → “2 años”, null/negativo/no entero → no se muestra; `formatearSexo`: “Hembra”/“Macho”,
  `no_definido` → no se muestra; `datosMascota`: “Raza · Edad · Sexo” solo con lo que se conoce, sin separadores
  sueltos). `PetDetail.jsx`: se quitó el bloque ✓/✗ (“Pendiente de vacunación / esterilización” que salía en **todas**
  las fichas) y la talla, y los íconos `Check`/`XIcon`; `Adoption.jsx`: se quitó la línea de la talla. Pruebas nuevas
  (`npm test`, 12 en total): `tests/mascota.test.js` (5, formato) y `tests/sin-salud-inventada.test.js` (falla si
  `src/` vuelve a mencionar `vaccinated`, `sterilized`, `pet.size` o “Pendiente de vacunación/esterilización”).
  Contraprueba con `git stash` de las dos páginas: falla 1 de 12 (la de regresión, que nombra `Adoption.jsx` y
  `PetDetail.jsx`); las 11 restantes pasan a propósito (5 de `api.js`, 5 del formato, que es un archivo nuevo, y la de
  `data/`). Lint 0 errores, build OK. Revisión a 375 px con la API real: 6 tarjetas (“Labrador Retriever · 2 años ·
  Hembra”… “Siames · Menos de 1 año · Hembra”), sin desborde horizontal, y la ficha de Luna ya no contradice su
  descripción. Detector de `/impeccable` sin hallazgos; `/impeccable audit` 16/20 (sin tokens ni modo oscuro y el botón
  “Conocer más” de ~36 px: ya existían).
  **Parte 3 de 3 (móvil) hecha el 06/11/2026:** `src/utils/mascota.js` del móvil (copia de la de la web: no hay paquete
  compartido). `PetDetailScreen.js`: se quitaron las insignias “Vacunada”/“Esterilizada” (desde la parte 1 decían “No” en
  **todas** las fichas), el componente `Badge` y la “Talla undefined”; la especie va en su línea y debajo “Raza · Edad ·
  Sexo” (no se pinta si no hay datos). `AdoptionScreen.js`: la misma línea (antes Nala, con edad 0, salía sin edad y el
  sexo en minúscula). Las fotos de las dos pantallas tienen `role="img"` y `aria-label` con el nombre de la mascota
  (hallazgo de `/revision-contenido-mascotas`; sin el rol, react-native-web deja la etiqueta en un `div` que el lector de
  pantalla ignora). Pruebas nuevas del móvil (`npm test`, `node --test`, sin dependencias; 7 en total):
  `tests/mascota.test.mjs` (las 5 del formato de la web + que las dos pantallas usen `datosMascota`) y
  `tests/sin-salud-inventada.test.mjs` (falla si `src/` menciona `vaccinated`, `sterilized`, `.size`, “Talla”,
  “Vacunada/o” o “Esterilizada/o”). Las pruebas son `.mjs` y el script usa
  `--disable-warning=MODULE_TYPELESS_PACKAGE_JSON` para no poner `"type": "module"` en el `package.json` de Expo.
  Contraprueba con `git stash` de las dos pantallas: fallan 2 de 7 (la de regresión, que nombra `PetDetailScreen.js`, y
  la del uso de `datosMascota`, que nombra `AdoptionScreen.js`); las 5 del formato pasan a propósito (la utilidad es un
  archivo nuevo). `npx expo export --platform web` OK; revisión a 375 px con la API simulada (datos inventados): “Labrador
  Retriever · 2 años · Hembra”, “Siames · Menos de 1 año · Hembra” y, sin raza ni sexo definido, solo la especie; ficha
  sin talla ni insignias y sin desborde horizontal. Probado por el dueño en el emulador (Pixel 7) con la API real: las 6
  mascotas de la BD con “Labrador Retriever · 2 años · Hembra”, “Siames · Menos de 1 año · Hembra”, etc., sin talla.
  `/impeccable audit` 14/20 (ya existían: texto gris `#64748b` sobre el
  fondo `#f2f2f2` de la ficha ≈ 4,3:1, por debajo de 4,5:1; error sin “Reintentar”; colores fijos sin modo oscuro;
  miniaturas con la foto completa). Sigue pendiente la validación veterinaria de los textos marcados (regla 6).

### 3.4 Web (React)

#### A-23 · 🟠 Alta · La web esconde los fallos de la API con datos falsos [A]
- `Catalog.jsx:16-25`, `Adoption.jsx:9-18` (si la API devuelve **0** mascotas, también muestra las falsas),
  `PetDetail.jsx:21-31`, `ProductDetail.jsx:24-30` → `.catch(() => {})` o *fallback* a `data/*.js`.
- `Home.jsx:4,8-9` **siempre** usa `data/products.js` (campos `discount`/`isNew` que la BD no tiene) [N].
- Así se ocultó NC-009. **Arreglo:** estados de carga / vacío / error como en el móvil; usar `data/*.js` solo en pruebas.
- **Estado: resuelto el 06/11/2026 (ítem 3.3 de PRIORIDADES); solo web. NC-009 cerrada.** Decisiones del dueño: Home
  muestra los productos reales de la API y se borran `src/data/pets.js` y `src/data/products.js` (git conserva la
  historia). `src/services/api.js`: cada error lleva `status` (código HTTP; `0` si el servidor no respondió), así las
  páginas distinguen “no encontrada” (404) de “no pudimos cargar” (503 BD caída, 502 proxy de Vite sin API, 0 sin
  conexión). Componente nuevo `src/components/EstadoCarga.jsx`: estados “cargando” (`role="status"`), “error”
  (`role="alert"` + botón “Reintentar”) y “vacío”; con `encabezado="h1"` en las fichas para que la página no pierda su
  título. `Adoption.jsx` y `Catalog.jsx` empiezan vacíos y en “cargando” (ya no con 6 mascotas / 12 productos
  inventados); con 0 resultados muestran “Por ahora no hay mascotas en adopción” / “Todavía no hay productos”; las
  categorías del catálogo salen de la API. `PetDetail.jsx` y `ProductDetail.jsx`: 404 → “no encontrada”; otro error →
  “No pudimos cargar…” con “Reintentar” y “Volver”; nunca la ficha falsa ni el formulario demo del 3.2. `Home.jsx`: las
  secciones “Ofertas destacadas” y “Nuevos productos” (descuento y “nuevo” que la BD no tiene) se cambian por
  “Productos destacados”: los 4 primeros productos de la API, con los mismos estados.
  Prueba de regresión: la web no tenía pruebas; se agregó `npm test` (`node --test`, incluido en Node, sin dependencias
  nuevas): `tests/api.test.js` (404, 503, 502 sin cuerpo, servidor que no responde y respuesta correcta, con `fetch`
  simulado) y `tests/sin-datos-falsos.test.js` (ningún archivo de `src/` importa `data/`). Con el código viejo fallan
  5 de 6 (pasa a propósito la de la respuesta correcta, que comprueba que no se rompió lo que funcionaba); con el nuevo
  pasan 6 de 6. Lint 0 errores, build OK. Revisión a 375 px con la API apagada: Adopción, Catálogo, Home y las dos
  fichas muestran el error (ningún perrito ni producto), sin desborde horizontal; con `fetch` simulado en el navegador:
  404 → “Mascota no encontrada”, lista vacía → estado vacío, “Reintentar” con datos → tarjetas. Contraprueba visual con
  el código viejo y la API apagada: las 6 mascotas falsas, la ficha falsa de “Luna” con “Solicitar Adopción” y las
  “Ofertas destacadas”. Probado por el dueño con la API real el 06/11/2026: Adopción con las 6 mascotas de la BD,
  `/adopcion/99999` → “Mascota no encontrada”, Home con productos reales (API: 200, 404 y 200). `/impeccable audit` 17/20 (detector sin hallazgos; pendiente opcional: el foco se va al
  `body` cuando “Reintentar” desaparece; sin modo oscuro ni tokens, como el resto de la web).
  Fuera de este ítem: las etiquetas “Nuevo” / “-x%” y el precio anterior de `ProductCard.jsx` y `ProductDetail.jsx`
  quedan sin uso (la API no manda esos campos) y Home sigue prometiendo “Envío en 24-48 horas” y “garantía de
  devolución”, que la demo no ofrece (anotado como pendiente). En la prueba del dueño se vio además que el pie
  (`Footer.jsx`) muestra un contacto inventado (`info@petconnect.com`, `+57 300 123 4567`, Bogotá) que contradice la
  D.1 de la política (correo de atención y Armenia): pendiente sin ítem.

#### A-24 · 🟡 Media · La sesión web nunca se revalida [A]
- `AuthContext.jsx:23-33` carga el usuario de `localStorage` y lo da por bueno siempre, aunque el token (24 h) venza.
- **Arreglo:** llamar a `/auth/me` al iniciar (como el móvil) y cerrar sesión ante un 401.
- **Estado: resuelto el 08/11/2026 (ítem 4.7 de PRIORIDADES, `3606c5d`); solo web, sin tocar la API ni la BD.**
  Decisión del dueño: opción A, **solo el 401 cierra la sesión** (un 404 “Usuario no encontrado” no, porque también
  puede venir de una API mal desplegada; el token vence en 24 h). `getPerfil()` nuevo en `src/services/api.js`;
  `src/utils/sesion.js` (JS puro) decide: 401 o datos sin token → cerrar; 503, 502, 500, 404 o red caída → mantener;
  200 → actualizar nombre y correo; si el token cambió mientras llegaba la respuesta → ignorar (una respuesta
  atrasada no cierra una sesión nueva). `AuthContext.jsx` lo llama en un `useEffect` al iniciar y sigue mostrando la
  sesión guardada mientras tanto (sin pantalla de carga). El 401 a mitad de sesión lo sigue tratando
  `FormularioSolicitud.jsx`. Prueba: `tests/sesion.test.js` (9; `npm test` 51/51, lint sin errores, build OK).
  Contraprueba (`git stash` de `api.js` y `AuthContext.jsx`): fallan 5; pasan a propósito 4 (503/502/500, red caída,
  404 y datos sin token: con el código viejo no hay llamada y “mantener” coincide). En el navegador del panel a 375 px,
  con la API del dueño en :5000: sesión inventada con token falso → `/auth/me` 401 → sesión borrada y botón “Iniciar
  sesión”, sin desplazamiento horizontal.

#### A-25 · ⚪ Baja · `innerHTML` con el nombre del producto [A]
- `assets/js/addToCartToast.js:23-28`. Hoy el nombre viene de la BD, pero es XSS en potencia. Usar `textContent`.

#### A-26 · ⚪ Baja · Precio calculado en el navegador [A]
- `CartContext.jsx:37`. Aceptable mientras el checkout sea demo; si se implementa, el servidor recalcula precio y stock.
- Desde el 06/11/2026 (3.2, A-21) el checkout está rotulado como demo y bloqueado. Un checkout real (sin ítem todavía)
  exige: tabla de pedidos, endpoint con `@require_auth`, precio y stock recalculados en el servidor y una versión nueva de
  la política (dirección y teléfono de envío son datos personales).

### 3.5 Móvil (Expo)

#### A-27 · 🟡 Media · La app solo funciona en el emulador [A]
- `src/services/api.js:9-14`: `10.0.2.2` (Android) o `localhost`, por HTTP. HTTP sin cifrar solo está permitido en
  los manifiestos *debug* (`usesCleartextTraffic`), así que el APK *release* no conectaría.
- **Arreglo:** `EXPO_PUBLIC_API_URL` y HTTPS al desplegar.

#### A-28 · ⚪ Baja · Token en AsyncStorage sin cifrar y cierre de sesión ante cualquier error
- `src/services/api.js:87` (el plan ya propone `expo-secure-store`). `AuthContext.js:22-25` borra el token ante
  **cualquier** error (también sin internet), no solo ante 401.

### 3.6 Dependencias

#### A-29 · 🟡 Media · Vulnerabilidades conocidas en dependencias [N]
| Módulo | Resultado `npm audit` | Lectura |
|---|---|---|
| Web | 2 **altas** (`react-router` / `react-router-dom` ≤ 7.18.1, CSRF en modo RSC) | La app no usa RSC → impacto real bajo; se arregla con `npm audit fix` |
| Móvil | 30 (1 crítica `shell-quote`, 14 altas, 13 moderadas, 2 bajas) | Casi todas en herramientas de Expo/compilación, no en la app instalada; arreglo completo exige subir de versión mayor de Expo |
| Backend | **No se pudo auditar** (`pip-audit` no está instalado; instalarlo requiere permiso) | Recomendado en CI |

### 3.7 Docker, CI y pruebas

#### A-30 · 🟠 Alta · Los archivos de Docker no funcionan y filtrarían secretos [N]
Archivos **sin commit**: `petconnect.Backend/Dockerfile`, `docker-compose.yml`, `PetConnect.Front/.../Dockerfile`,
`PetConnect.Mobile/Dockerfile`.
- **No hay `.dockerignore`** → `COPY . .` mete el **`.env` real**, `node_modules` y `__pycache__` en la imagen.
- `docker-compose.yml` está dentro de `petconnect.Backend/` pero sus rutas (`./petconnect.Backend`, `./PetConnect.Front/...`)
  solo funcionan desde la raíz; el servicio `db` no tiene variables, volumen ni script inicial (`# ...`).
- `api.py:458` → `app.run(...)` escucha en `127.0.0.1`: **dentro del contenedor la API no es accesible**.
- El Front corre el servidor de **desarrollo** y su proxy apunta a `localhost:5000` (dentro del contenedor no es el backend).
- El Móvil usa `--localhost`: no se ve desde fuera del contenedor.
- **Arreglo:** `.dockerignore` por módulo, compose en la raíz, `host="0.0.0.0"` controlado por variable, MySQL/MariaDB
  con `schema.sql` en `docker-entrypoint-initdb.d`, secretos vía `env_file` (nunca en la imagen), Gunicorn.

#### A-31 · 🟠 Alta · No hay integración continua y las pruebas cubren poco [A]
- No existe `.github/workflows/`. Solo 13 pruebas (seguridad); **ninguna** prueba endpoints de mascotas, productos,
  OTP ni errores.
- **Arreglo:** GitHub Actions con `unittest` + `npm run lint` + `npm run build`; pruebas de regresión para cada NC
  (p. ej. `/api/mascotas/<id>` sin token → 404; 6.º intento OTP → bloqueado; ruta inexistente → 404).
- **Estado: resuelto el 07/11/2026 (ítems 4.3 y 4.4 de PRIORIDADES; solo falta ver la primera ejecución de la CI
  en GitHub, que llega con el push final).**
- **Pruebas de endpoints (ítem 4.4, commit `37f8126`):** antes de escribir pruebas se hizo un inventario de las 14
  rutas de `api.py` × caso (éxito, 400, 401, 403, 404, 503 sin BD) y de cada NC × la prueba que la cubre. Ya había
  15 archivos de pruebas con el cliente de Flask (mascotas, solicitudes, login, registro, OTP, límite, errores);
  faltaban `GET /api/auth/me` completa, el éxito y el 404 de productos, el filtro de la lista de adopción sin
  MariaDB, campos vacíos, correo inexistente, 409, 503 de login/verify, verify y registro, el código vencido o sin
  pendiente por la API, y la respuesta normal de `validar-correo`. También faltaba probar por la API la migración
  del hash de NC-001 y la ruta real de NC-008 (solo había una ruta falsa). `tests/test_endpoints.py` (31 pruebas,
  BD, DNS y correo simulados, tokens firmados con la clave de pruebas, correos `@ejemplo.test`, sin `.env`) cubre
  esos huecos y agrega un **inventario vivo**: la lista de rutas de la API debe ser la anotada en la prueba, cada
  ruta debe aparecer en el código (no en comentarios) de sus archivos de pruebas y toda ruta privada responde 401
  sin token y sin tocar la BD. Si alguien agrega una ruta sin pruebas, la CI falla. Suite: 231 pruebas (207
  correctas y 24 omitidas que requieren MariaDB). Contraprueba en una copia temporal fuera del repositorio: 28
  roturas a propósito (quitar `@require_auth` de `/me`, `sub` entero, quitar los filtros `activo` y
  `en_adopcion`, quitar o estropear la migración del hash, revelar si un correo existe, gastar el código antes de
  revisar la BD, quitar el 409, aceptar dominios sin MX, agregar una ruta sin pruebas, etc.): las 28 detectadas y
  cada una de las 31 pruebas falla con al menos una. Hallazgo nuevo: `GET /api/productos/<id>` no filtra
  `activo = TRUE` (un producto descontinuado se ve por su URL); por decisión del dueño no se tocó `api.py` y quedó
  como ítem 4.16.
  **Resuelto el 09/11/2026 (ítem 4.16, commit `4b5d18e`):** `ProductoDAO.consultar_catalogo_por_id` filtra
  `activo = TRUE` y `api.py` lo vuelve a revisar (doble barrera); un producto descontinuado responde el 404
  “Producto no encontrado” de siempre (web y móvil ya lo muestran). Regresión: 2 pruebas en
  `PruebasProductos`; contraprueba: sin el filtro del DAO falla 1, sin la revisión de `api.py` fallan 2 casos.
- **Integración continua (ítem 4.3, commit `8802815`):** `.github/workflows/ci.yml` corre en GitHub Actions
  (`ubuntu-latest`) en cada push y con el botón “Run workflow”, con un job por módulo: backend (Python 3.14,
  `pip install -r requirements.txt` y `unittest`), web (Node 24: `npm ci`, `npm run lint`, `npm test` y
  `npm run build`) y móvil (Node 24: `npm ci`, `npm test` y `npx expo export --platform web`). Solo lectura del
  repositorio (`permissions: contents: read`, `persist-credentials: false`), acciones oficiales `@v7` y ningún
  secreto: las pruebas ponen sus propias claves de prueba. Validado en local sin push: YAML revisado y los mismos
  comandos corridos en una copia limpia del último commit (`git archive`, sin `.env` ni `node_modules`): backend
  200 pruebas (176 correctas y 24 omitidas que requieren MariaDB), web lint sin errores + 42/42 + build, móvil
  35/35 + export. Sin diferencias de mayúsculas en los imports (Linux las distingue). La primera ejecución en
  GitHub queda pendiente del push, que se hace al terminar todo el plan.

### 3.8 Documentación y orden

| ID | Sev. | Hallazgo | Dónde |
|---|---|---|---|
| A-32 | ⚪ | README desactualizado: dice MySQL 8 (es MariaDB 10.4), `autocommit False` (es `True`), `mysql-connector 9.7.0` (es `9.1.0`) y solo explica la consola | `README.md:16,116,128` [A] |
| A-33 | ⚪ | El plan dice que las pruebas se corren con `pytest` y `.env.test`; el repo usa `unittest` y no hay `.env.test` | Plan GA9, nota de la tabla de pruebas de la API |
| A-34 | ⚪ | `PetConnect.Mobile/LICENSE` es la licencia de Expo (“650 Industries”) | [A] |
| A-35 | ⚪ | Colecciones de Postman duplicadas (“PetConnect API” y “PetConnect API Copy”) y carpeta anidada `postman/postman/` | `PetConnect.Mobile/postman/` [A] |
| A-36 | ⚪ | Rutas personales de Windows (`C:\Users\goku8\...`) en la guía | `PetConnect.Mobile/EJECUCION.md:60-74` [A] |
| A-37 | ⚪ | Nombre del repositorio con acentos rotos (`Codificaci-n-de-m-dulos-...`) | GitHub [A] |
| A-38 | ⚪ | Se llegó a subir un archivo temporal de Word (`~$9-220501096-AA3-EV02-PetConnect.docx`); falta `~$*` en `.gitignore` | historial de `Documentacion/GA9/` [N] |
| A-39 | ⚪ | Carpeta local `.github/modernize/java-upgrade/` (restos de una extensión de Java, sin seguimiento): no aplica a este proyecto | raíz [N] |

### 3.9 Configuración de Claude Code (instalada hoy)

#### A-40 · ⚪ Baja · El hook de secretos bloquea búsquedas legítimas [N]
- `proteger-secretos.js` bloqueó **3 comandos de esta auditoría** que solo *contenían el texto* `.env` dentro de una
  búsqueda (`grep`), sin leer el archivo.
- **Arreglo:** que el patrón exija que `.env` sea una ruta argumento (no parte de una expresión regular entre comillas).

#### A-41 · 🟡 Media · Los hooks no detectan lecturas indirectas de secretos [N] — ver incidente §5
- Un script que **importa `api.py`** carga el `.env` real mediante `load_dotenv()`; ningún hook lo puede ver.
- **Arreglo:** regla nueva en `CLAUDE.md`: los scripts de prueba que importen la API deben desactivar `load_dotenv`
  o usar variables de prueba explícitas, y **nunca imprimir** valores de configuración.
- **Estado: resuelto el 09/11/2026 (ítem 4.14 de PRIORIDADES, commit `08e61ec`; la regla de `CLAUDE.md` ya existía).** Con un “espía”
  (`load_dotenv` cambiado por una función que no carga nada y solo cuenta llamadas) se vio que `tests/test_seguridad.py`
  cargaba el `.env` real también en la suite completa (era el primer archivo en importar `api.py`) y que
  `tests/test_esquema.py`, corrido solo, lo cargaba en `PruebasEsquemaSinBD` (`config.db_config` y `seed.py`). Los dos
  usan ahora `_importar_api()` de `tests/test_errores.py`; las pruebas con BD de `test_esquema.py` lo leen a propósito
  (solo con `PETCONNECT_PRUEBA_BD=1`, para conectarse a MariaDB). Regresión: `tests/test_sin_env_real.py` (2) corre cada
  archivo en un Python aparte con el espía y exige 0 llamadas. Suite 397 (347 + 50 omitidas); el espía sobre la suite
  completa: 0 llamadas (antes 1). Contraprueba con los archivos viejos: fallan 2 de 2. Ningún valor de configuración se
  leyó ni se imprimió. Los hooks siguen sin ver lecturas indirectas: la protección es la regla y esta prueba.

---

## 4. Verificación de la auditoría del compañero

| # | Afirmación del compañero | Veredicto | Nota |
|---|---|---|---|
| Bien | Arquitectura, SQL parametrizado, bcrypt, historial limpio, OTP con `secrets`, versiones fijadas | ✅ Cierto | Confirmado |
| Fondo | La documentación va por delante del código | ✅ Cierto | Ver A-02 |
| 1 | `PetConnect.sql` nunca se subió | ✅ Cierto | 0 archivos `.sql` en todo el historial (A-01) |
| 2 | NC-002 en `api.py:235` | ✅ Cierto | A-07 |
| 3 | Correo para phishing (`plantillas.py:42`) y sin límite | ✅ Cierto, **probado** | También la plantilla de bienvenida (`:99`). El límite de tasa **sí** estaba en NC-006; la inyección HTML no (A-05) |
| 4 | Singleton de una conexión (NC-003) | ✅ Cierto | A-11; ojo con A-12 al pasar a Gunicorn |
| 5 | `debug=True` (`:458`), `str(e)`, secreto JWT por defecto (`jwt_helper.py:9`) | ✅ Cierto, **probado** | Además 404/405 se vuelven 500 (A-08) |
| 6 | `acepta_datos=True` fijo (NC-005) | ✅ Cierto | Hoy está en `api.py:409` (el plan cita la 401) |
| 7 | La web esconde errores con datos falsos | ✅ Cierto | Y `Home` siempre usa datos fijos (A-23; resuelto el 06/11/2026, ítem 3.3) |
| 8 | Checkout falso (`Checkout.jsx:41`) | ✅ Cierto | También adopción y contacto (A-21) |
| 9 | NC-009, enum sin `en_adopcion` | ⚠️ No verificable en el repo | No hay esquema SQL; se acepta por la evidencia del equipo (AA2, CP-012) |
| 10 | Móvil fijo a `10.0.2.2` (`api.js:14`) | ✅ Cierto con matiz | En web usa `localhost`; HTTP solo permitido en *debug* (A-27) |
| 11 | La web no revalida la sesión | ✅ Cierto | A-24 |
| 12 | Registro pisado (`api.py:362`) | ✅ Cierto, **probado** | A-09 |
| 13 | Cifrado no usado, `decrypt()` traga errores | ✅ Cierto, **probado** | A-13 |
| — | README, LICENSE, Postman, EJECUCION, `innerHTML`, NC-004, pruebas/CI, nombre del repo | ✅ Ciertos | A-25, A-31, A-32 a A-37 |
| — | “Quitar `AGENTS.md`, es de la plantilla” | ❌ No recomendado | Sí viene de la plantilla, pero sirve (pide leer la documentación de Expo 57) y ahora lo usa `PetConnect.Mobile/CLAUDE.md` |

**Conclusión:** la auditoría del compañero es **precisa y sirve como guía**. Le faltaron sobre todo: TLS sin verificar
(A-06), OTP en logs (A-10), el choque OTP-en-memoria/Gunicorn (A-12), formularios falsos de adopción y contacto (A-21),
la información de salud contradictoria (A-22), Docker (A-30) y las dependencias (A-29).

---

## 5. Incidente durante la auditoría (transparencia)

Durante las pruebas dinámicas, un script importó `api.py` para probarlo sin base de datos. `api.py` ejecuta
`load_dotenv()` y cargó el `.env` real; el script imprimió el valor de **`JWT_SECRET`** en la conversación con Claude.
El valor **no** quedó en ningún archivo del repositorio ni en git.

**Acción requerida:** rotar `JWT_SECRET`, es decir, generar uno nuevo (por ejemplo, `python -c "import secrets; print(secrets.token_hex(32))"`)
y pegarlo a mano en `petconnect.Backend/.env`, **sin** correr `generate_keys.py`, porque borraría el resto del archivo (A-16).
Efecto: todas las sesiones abiertas se cierran. Prevención: A-41.

**Estado: resuelto el 03/11/2026 (ítem 0.1 de PRIORIDADES).** El dueño del proyecto generó un `JWT_SECRET` nuevo
(`secrets.token_hex(32)`) en su propia terminal y reemplazó a mano solo esa línea del `.env`; el valor no pasó por la
conversación. Verificación: la API arranca y se conecta a la BD; `GET /api/auth/me` responde **401** sin token, con
un token inventado y con el token que la web tenía guardado de antes de la rotación. Pruebas `unittest`: 13 de 13 OK.

---

## 6. Qué NO se pudo auditar

| Tema | Motivo | Cómo cubrirlo |
|---|---|---|
| Esquema de la BD, NC-009, NC-010 | No hay `.sql` en el repo | Subir el esquema (A-01) |
| Pruebas contra MariaDB real y carga (NC-003) | No se levantó la BD en esta auditoría | Tras A-01, repetir CP-008 / JMeter |
| `pip-audit` del backend | No instalado (instalar requiere permiso) | Agregarlo a CI |
| Revisión visual / accesibilidad con la app corriendo | Requiere backend + BD | `/levantar-proyecto` y luego `/impeccable audit` |
| Escaneo ZAP | Fuera del alcance de una revisión local | Sprint 3 del plan |

---

## 7. Comandos ejecutados y resultados

| Comando | Resultado |
|---|---|
| `python -m unittest discover -s tests` | 13/13 OK |
| `npm run lint` (web) | 0 errores, 2 avisos (`only-export-components` en los contextos) |
| `npm run build` (web) | OK, 293.9 kB JS (88.2 kB gzip) |
| `npm audit` (web) | 2 altas |
| `npm audit` (móvil) | 30 (1 crítica, 14 altas) |
| Sondeo dinámico de la API (cliente de pruebas de Flask, BD caída a propósito) | Tabla de A-08; A-04, A-05, A-09, A-17 confirmados |
| Revisión de los 10 commits | 0 secretos, 0 `.sql`, 0 `.env` |
