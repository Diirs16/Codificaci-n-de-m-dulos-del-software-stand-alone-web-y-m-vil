# Política de tratamiento de datos personales de PetConnect — versión 1.1 (BORRADOR)

> **Estado: BORRADOR para validar. No publicar todavía.**
> Lo redactó Claude Code el 05/11/2026 para el ítem 3.1 (A-20, NC-005). Es contenido legal: puede *sonar* bien y
> tener errores. Antes de publicarlo deben revisarlo el dueño del proyecto y el instructor (o un abogado), y hay que
> llenar todos los `[PENDIENTE: …]`. Las citas de artículos se deben comparar con el texto oficial.
>
> **Para qué sirve este archivo:**
> - **Parte A**: el texto de la política que se publica en la web (`/politica-de-datos`, parte 2 del 3.1) y al que
>   enlazará el móvil (parte 3). La copia publicada está en
>   `PetConnect.Front/petconnect-app/src/pages/PoliticaDatos.jsx`: **si cambias uno, cambia el otro** y sube la
>   versión allí y en `VERSION_POLITICA_DATOS` de la API.
> - **Parte B**: los textos cortos de la interfaz (casilla, aviso y mensajes).
> - **Parte C**: lo que el sistema debe hacer para cumplir. Es la especificación de las 3 partes del 3.1.
> - **Parte D**: las decisiones que faltan. **Parte E**: la revisión de datos personales.
>
> **Prueba de la autorización:** la versión `1.1` es la que guarda el servidor en `VERSION_POLITICA_DATOS`. El texto
> exacto de cada versión queda en el historial de git de este archivo. Así se puede mostrar qué aceptó cada persona.
> Si el texto cambia, cambia la versión (ver A.13).
>
> **Versiones:**
> - **1.0** (05/11/2026, ítem 3.1): cuenta, códigos, mascotas y protección de la plataforma.
> - **1.1** (07/11/2026, ítem 3.6, A-21): agrega las solicitudes de adopción y los mensajes de contacto (A.4, A.5
>   punto 7, A.6, A.11 y A.14; Partes B.3, B.5 y C.12 a C.15). Al subir la versión, quien aceptó la 1.0 debe
>   autorizar otra vez al iniciar sesión (C.9). El archivo conserva el nombre `...v1.0-BORRADOR.md` para no romper
>   los enlaces de los demás documentos.

---

## Parte A — Texto de la política (para publicar)

### A.1 Quién es el responsable de tus datos

El responsable del tratamiento de tus datos personales es:

| Dato | Valor |
|---|---|
| Nombre | PetConnect y sus asociados: Daniel Jimenez, Andrea Silva, Nelson Perez y Andrea Yasmin |
| Domicilio | Armenia, Quindío, Colombia |
| Dirección física | Cra. 6 # 17 Norte 01, Armenia, Quindío |
| Correo para temas de datos personales | proyectopetconnect+atencion@gmail.com |
| Teléfono | 324 368 2078 |

(Datos de A.1 decididos por el dueño del proyecto el 06/11/2026, D.1.)

PetConnect es una plataforma para personas que tienen mascotas o quieren adoptar una. Reúne adopción, catálogo de
productos y directorio de servicios. [PENDIENTE: decidir si se aclara que es un proyecto formativo del SENA, ficha
220501096.]

### A.2 Marco legal

Esta política cumple la **Ley Estatutaria 1581 de 2012** (protección de datos personales), su decreto reglamentario
**Decreto 1377 de 2013** (hoy compilado en el **Decreto Único 1074 de 2015**) y el artículo 15 de la Constitución
Política de Colombia (derecho al hábeas data).

### A.3 Palabras clave

- **Dato personal:** cualquier información que te identifica o te puede identificar, como tu nombre o tu correo.
- **Titular:** tú, la persona a quien se refieren los datos.
- **Tratamiento:** cualquier cosa que se haga con tus datos: recogerlos, guardarlos, usarlos, enviarlos o borrarlos.
- **Autorización:** tu permiso previo, expreso e informado para que tratemos tus datos.
- **Responsable:** quien decide para qué y cómo se tratan los datos (ver A.1).
- **Encargado:** quien trata datos por cuenta del responsable, por ejemplo el servicio que envía nuestros correos.

### A.4 Qué datos recogemos y cómo

| Dato | Cuándo lo recogemos | Obligatorio |
|---|---|---|
| Nombre y apellidos | Al registrarte | Sí |
| Correo electrónico | Al registrarte y al iniciar sesión | Sí |
| Contraseña | Al registrarte. **No la guardamos tal cual:** guardamos solo una huella cifrada (hash bcrypt) de la que no se puede sacar la contraseña | Sí |
| Fecha en que autorizaste y versión de la política que aceptaste | Al registrarte | Sí (es la prueba de tu autorización) |
| Códigos de verificación | Cada vez que te registras o inicias sesión; te los enviamos por correo | Sí |
| Datos de tus mascotas (nombre, especie, raza, sexo, edad aproximada, color, foto y observaciones) | Solo si registras mascotas en tu cuenta | No |
| Mensajes que nos envías por los formularios de adopción y contacto (con la fecha y la mascota) | Solo si los envías, con tu sesión iniciada | No |
| Teléfono | Solo si lo escribes en una solicitud de adopción | No |
| Dirección IP desde la que te conectas | En cada petición | Técnico |

**No pedimos datos sensibles** (salud, origen racial o étnico, orientación política, creencias, datos biométricos,
vida sexual, etc.) y te pedimos que no los escribas en campos libres como las observaciones de tus mascotas.
Los datos de salud de las mascotas (vacunas, por ejemplo) son de los animales, no tuyos, pero los tratamos con el
mismo cuidado porque están asociados a tu cuenta.

**En tu dispositivo:** para que no tengas que iniciar sesión en cada pantalla, la web guarda tu sesión (un token y tu
nombre y correo) en el almacenamiento local del navegador, y la app la guarda en el almacenamiento del celular. Se
borra al cerrar sesión. **No usamos cookies de publicidad ni herramientas de analítica o seguimiento.**

### A.5 Para qué usamos tus datos

1. Crear tu cuenta y permitirte iniciar sesión.
2. Verificar que el correo es tuyo y proteger tu cuenta con códigos que te enviamos por correo.
3. Enviarte los correos necesarios para usar el servicio: códigos de verificación y bienvenida.
4. Mostrarte y administrar tus mascotas. Las mascotas que publiques **en adopción** se muestran a cualquier visitante
   (nombre, especie, raza, sexo, edad, foto y descripción), **sin** tus datos personales.
5. Proteger la plataforma: limitar los intentos de inicio de sesión y de códigos, y detectar abusos. Los registros
   técnicos del servidor no guardan tu correo ni tus códigos.
6. Atender tus consultas, reclamos y solicitudes sobre tus datos.
7. Gestionar tus solicitudes de adopción y responder tus mensajes de contacto. Solo los lee el equipo de PetConnect;
   no se envían a quien publicó la mascota.

**Lo que no hacemos:** no vendemos ni alquilamos tus datos, no te enviamos publicidad y no los usamos para fines
distintos a los de esta lista. Si algún día quisiéramos usarlos para otra cosa (por ejemplo, enviarte novedades), te
pediríamos una autorización nueva y aparte, que podrías no dar sin perder tu cuenta.

### A.6 Tu autorización

Solo tratamos tus datos si nos autorizas **antes** de registrarte, marcando tú mismo la casilla del formulario de
registro. La casilla viene **sin marcar** y no puedes crear la cuenta sin ella (Ley 1581, art. 9). Guardamos la fecha
y la versión de esta política que aceptaste, como prueba (Decreto 1377, art. 8).

Los formularios de adopción y contacto no piden otra casilla: usan la autorización de tu cuenta con esta versión de
la política, y cada solicitud guarda la versión que tenías aceptada al enviarla. Si aceptaste una versión anterior, te
pediremos autorizar otra vez al iniciar sesión.

No necesitamos tu autorización en los casos del artículo 10 de la Ley 1581 (por ejemplo, una orden judicial o un
requerimiento de una entidad pública en ejercicio de sus funciones).

### A.7 Tus derechos

Como titular tienes derecho a (Ley 1581, art. 8):

- **Conocer, actualizar y rectificar** tus datos, incluso si están incompletos o son inexactos.
- **Pedir prueba** de la autorización que nos diste.
- **Saber cómo hemos usado** tus datos, si nos lo preguntas.
- **Revocar la autorización y pedir que borremos** tus datos (supresión). No procede si tienes un deber legal o
  contractual de permanecer en la base de datos. Como no podemos prestarte el servicio sin tus datos, revocar la
  autorización implica cerrar tu cuenta.
- **Acceder gratis** a tus datos.
- **Presentar quejas** ante la Superintendencia de Industria y Comercio (SIC), después de haber hecho tu consulta o
  reclamo ante nosotros (Ley 1581, art. 16).

### A.8 Cómo ejercer tus derechos

Escríbenos a **proyectopetconnect+atencion@gmail.com** desde el correo de tu cuenta, para que podamos comprobar que
eres tú sin pedirte más datos. También pueden hacerlo tus causahabientes o tu representante, demostrando esa calidad.

**Consultas** (quieres saber qué datos tenemos o cómo los usamos): te respondemos en máximo **10 días hábiles**
desde que recibimos tu mensaje. Si no alcanzamos, te avisamos el motivo y te respondemos en máximo **5 días hábiles
más** (Ley 1581, art. 14).

**Reclamos** (quieres corregir, actualizar o borrar tus datos, revocar la autorización o denunciar un incumplimiento)
(Ley 1581, art. 15):

1. Incluye tu nombre, el correo de tu cuenta, qué pides y por qué, y los documentos que quieras aportar.
2. Si falta algo, te lo pedimos dentro de los **5 días** siguientes. Si en **2 meses** no lo envías, entenderemos
   que desististe del reclamo.
3. En máximo **2 días hábiles** marcamos tus datos con la nota “reclamo en trámite” hasta resolverlo.
4. Te respondemos en máximo **15 días hábiles**. Si no alcanzamos, te avisamos el motivo y te respondemos en máximo
   **8 días hábiles más**.

### A.9 Con quién compartimos tus datos

No compartimos tus datos con terceros para que los usen para sus propios fines. Los usan, solo por cuenta nuestra y
para lo descrito en A.5, estos encargados:

| Encargado | Para qué | Dónde están sus servidores |
|---|---|---|
| Google LLC (servicio de correo Gmail) | Enviarte los códigos de verificación y el correo de bienvenida (recibe tu nombre y tu correo) | Pueden estar fuera de Colombia |
| [PENDIENTE: proveedor donde se aloje la API y la base de datos] | Guardar la base de datos y hacer funcionar la plataforma | [PENDIENTE] |

Al aceptar esta política autorizas que tus datos se transmitan a esos encargados aunque sus servidores estén fuera de
Colombia, solo para las finalidades de A.5 (Ley 1581, art. 26; Decreto 1377, arts. 24 y 25).

### A.10 Cómo protegemos tus datos

- Las contraseñas se guardan solo como hash bcrypt; nadie del equipo puede verlas.
- Los códigos de verificación vencen a los 10 minutos y se bloquean después de 5 intentos fallidos.
- Limitamos la cantidad de intentos de inicio de sesión y de registro por minuto.
- Los correos se envían por una conexión cifrada que verifica la identidad del servidor de correo.
- Las mascotas que no están en adopción solo las puede ver su dueño.
- Los registros técnicos del servidor no guardan correos ni códigos.

Ningún sistema es 100 % seguro. Si ocurre un incidente que afecte tus datos, te avisaremos y lo informaremos a la SIC
como lo exige la ley.

### A.11 Cuánto tiempo guardamos tus datos

- **Tu cuenta:** mientras esté activa. Si pides borrarla, eliminamos tus datos en el plazo de respuesta del reclamo
  (A.8), salvo lo que la ley nos obligue a conservar.
- **Prueba de tu autorización** (fecha y versión): [PENDIENTE: cuánto tiempo después de cerrar la cuenta].
- **Tus solicitudes de adopción y mensajes de contacto:** se guardan mientras tu cuenta exista o hasta que pidas
  borrarlos.
- **Un registro que no terminaste:** tus datos y el código se guardan solo en la memoria temporal del servidor, dejan
  de servir a los 10 minutos y nunca llegan a la base de datos.
- **Cuentas inactivas:** [PENDIENTE: decidir si se borran tras un tiempo sin uso].

Solo guardamos los datos el tiempo razonable y necesario para la finalidad (Decreto 1377, art. 11).

### A.12 Niñas, niños y adolescentes

PetConnect es para **mayores de 18 años**. Al registrarte declaras que lo eres. Si eres menor de edad, pide a tu
madre, padre o representante legal que use la plataforma por ti. (Decidido por el dueño del proyecto el 05/11/2026,
D.4.)

### A.13 Cambios a esta política

Si cambiamos esta política, publicaremos la versión nueva con su fecha **antes** de aplicarla y te avisaremos por
correo. Si el cambio afecta para qué usamos tus datos, te pediremos de nuevo la autorización (Decreto 1377, art. 13).

### A.14 Vigencia

- Versión: **1.1**
- Vigente desde: [PENDIENTE: fecha de publicación].
- Las bases de datos estarán vigentes mientras PetConnect preste el servicio.

---

## Parte B — Textos para la interfaz (web y móvil)

**B.1 Casilla** (sin marcar al abrir el formulario, obligatoria, al final del formulario y antes del botón):

> ☐ Soy mayor de 18 años, he leído la **[Política de tratamiento de datos personales]** y autorizo a PetConnect a
> tratar mis datos para crear y usar mi cuenta.

La declaración de edad va en la misma casilla (D.4). La API no la recibe aparte: solo `"acepta_datos": true`.

El texto entre corchetes es un enlace a la política. En la web se abre en una pestaña nueva para no perder lo escrito
en el formulario; en el móvil abre la misma página.

**B.2 Aviso corto** (letra pequeña, debajo de la casilla; cumple el deber de informar del art. 12 de la Ley 1581):

> Usaremos tu nombre y tu correo para crear tu cuenta y enviarte códigos de verificación. Puedes conocer, actualizar,
> rectificar o borrar tus datos y revocar este permiso escribiendo a proyectopetconnect+atencion@gmail.com.

(El 05/11/2026 se quitó el correo porque aún estaba “por definir”; el 06/11/2026, con el correo decidido (D.1), el
dueño del proyecto pidió volver a mostrarlo en el aviso. El correo también está en la política, secciones A.1 y A.8.)

**B.3 Mensajes:**

| Situación | Dónde | Texto |
|---|---|---|
| Se intenta enviar el formulario sin marcar la casilla | Web y móvil, antes de llamar a la API | “Para crear tu cuenta debes autorizar el tratamiento de tus datos personales.” |
| La API recibe un registro sin autorización válida | API, respuesta 400 | “Debes autorizar el tratamiento de tus datos personales para registrarte” |
| Pie de página o menú | Web | Enlace “Política de datos personales” a `/politica-de-datos` |
| Inicio de sesión de una cuenta sin autorización vigente (creada antes del 3.1 o que aceptó otra versión), sin la casilla | API, respuesta 403 con `"requiere_autorizacion": true` (ítem 3.5) | “Para seguir usando tu cuenta debes autorizar el tratamiento de tus datos personales” |
| Se intenta continuar el inicio de sesión sin marcar la casilla | Web y móvil, antes de llamar a la API (ítem 3.5) | “Para continuar debes autorizar el tratamiento de tus datos personales.” |
| Debajo de la casilla del inicio de sesión | Web y móvil (ítem 3.5) | “Si no quieres autorizarlo, escríbenos a proyectopetconnect+atencion@gmail.com y borraremos tu cuenta.” (enlace `mailto`, proceso manual de C.8) |
| Se envía una solicitud o un mensaje con una cuenta sin la autorización de la versión vigente (por ejemplo, un token de antes de la 1.1) | API, respuesta 403 con `"requiere_autorizacion": true` (ítem 3.6) | “Para enviar tu solicitud debes autorizar la versión vigente de la política de datos. Cierra sesión y vuelve a iniciarla” |
| Formulario de adopción o contacto sin sesión iniciada | Web y móvil (ítem 3.6, partes 2 y 3) | El botón dice “Inicia sesión para enviar” y no se puede escribir en el formulario |
| Alguien intenta registrarse con un correo que ya tiene cuenta | API: misma respuesta que un registro nuevo (“Codigo enviado”), sin crear código. Correo al titular, como mucho uno cada 10 minutos (ítem 4.10, A-14) | Asunto “PetConnect - Intento de registro con tu correo”. “Hola {nombre de la cuenta}: alguien intentó crear una cuenta en PetConnect con este correo, pero ya tienes una. Si fuiste tú, no necesitas registrarte: inicia sesión con tu correo y tu contraseña. Si no fuiste tú, puedes ignorar este mensaje: no se creó ninguna cuenta ni cambió tu contraseña. ¿Olvidaste tu contraseña? Escríbenos a proyectopetconnect+atencion@gmail.com.” No cambia la Parte A (no sube la versión) |
| Código del registro incorrecto, vencido o sin registro pendiente | API, respuesta 400 (ítem 4.10, A-14: un solo mensaje para no revelar cuentas) | “Codigo incorrecto o vencido. Si pasaron mas de 10 minutos, vuelve a registrarte” |

**B.4 Accesibilidad:** la casilla debe tener su etiqueta asociada (`<label htmlFor>` en la web,
`accessibilityRole="checkbox"` y `accessibilityState={{ checked }}` en el móvil), un área táctil de al menos
44 × 44 px y un contraste suficiente. El error debe leerse con el lector de pantalla.

**B.5 Aviso de los formularios de adopción y contacto** (versión 1.1, ítem 3.6; letra pequeña, encima del botón
“Enviar”; cumple el deber de informar del art. 12 de la Ley 1581). Decisión del dueño del proyecto (07/11/2026): **sin
casilla aparte**, porque la cuenta ya autorizó la versión 1.1, que nombra esta finalidad (A.5 punto 7).

> Adopción: Al enviar, usaremos tu nombre, tu correo, tu teléfono (si lo escribes) y este mensaje para gestionar tu
> solicitud de adopción de {nombre de la mascota}, según la **[Política de tratamiento de datos personales]**. Solo el
> equipo de PetConnect lee tu mensaje. No escribas datos sensibles (salud, creencias…). Puedes pedir que lo borremos
> escribiendo a proyectopetconnect+atencion@gmail.com.

> Contacto: Al enviar, usaremos tu nombre, tu correo y este mensaje para responder tu consulta, según la
> **[Política de tratamiento de datos personales]**. Solo el equipo de PetConnect lee tu mensaje. No escribas datos
> sensibles (salud, creencias…). Puedes pedir que lo borremos escribiendo a proyectopetconnect+atencion@gmail.com.

El nombre y el correo se muestran solo para leer (salen de la cuenta). La web y el móvil dicen “enviada” **solo** si la
API respondió 201.

---

## Parte C — Qué debe hacer el sistema (especificación para implementar)

| # | Requisito legal | Norma | Qué hace PetConnect | Parte del 3.1 |
|---|---|---|---|---|
| C.1 | Autorización previa: se pide antes de recoger los datos | Ley 1581, art. 9 | `/api/auth/register` exige la autorización antes de validar el nombre, consultar el DNS, consultar la BD o enviar un correo | 1 (API) |
| C.2 | Autorización expresa: una conducta inequívoca, nunca el silencio ni una casilla premarcada | Ley 1581, art. 9; Decreto 1377, art. 7 | La casilla empieza sin marcar. La API acepta solo `"acepta_datos": true` (booleano JSON); `"true"`, `1`, `"si"`, `null` o la ausencia del campo → 400 | 1 (API), 2 (web), 3 (móvil) |
| C.3 | Autorización informada: se informa la finalidad, los derechos y quién es el responsable | Ley 1581, art. 12 | Enlace a la política (Parte A) y aviso corto (B.2) visibles antes del botón | 2 y 3 |
| C.4 | Rechazar el registro sin autorización | Acción correctiva de NC-005 | 400 sin código enviado ni registro pendiente creado | 1 |
| C.5 | Conservar la prueba de la autorización | Ley 1581, art. 17 b; Decreto 1377, art. 8 | Columnas `usuarios.fecha_autorizacion_datos` (DATETIME) y `usuarios.version_politica_datos` (VARCHAR); la fecha es la de `/register` y la versión sale de `VERSION_POLITICA_DATOS = "1.0"` en el servidor | 1 (API + BD) |
| C.6 | No afirmar una autorización que no existe | Ley 1581, arts. 4 y 9 | `acepta_datos` sin `DEFAULT 1` (pasa a `NOT NULL DEFAULT 0`); `Usuario()` trae `False`; regla `CHECK`: `acepta_datos = 0` o fecha y versión presentes; los usuarios existentes sin fecha pasan a `0` en la migración | 1 (BD) |
| C.7 | Política publicada y disponible | Decreto 1377, art. 13 | Página web `/politica-de-datos` con la Parte A, enlazada desde el registro y el pie de página | 2 |
| C.8 | Canal para consultas y reclamos | Ley 1581, arts. 14 y 15 | Correo de A.8, `proyectopetconnect+atencion@gmail.com` (decidido el 06/11/2026; proceso manual). Un botón de “borrar mi cuenta” queda para un ítem futuro | Fuera del 3.1 |
| C.9 | Cambios en la política | Decreto 1377, art. 13 | Cambiar el texto obliga a subir `VERSION_POLITICA_DATOS`; al iniciar sesión, quien aceptó otra versión debe autorizar otra vez (casilla + código; ítem 3.5, hecho el 06/11/2026 en la API, la web y el móvil) | 3.5 |
| C.10 | Usuarios sin autorización registrada | Riesgo R05 del plan GA9 (contingencia) | Quedan con `acepta_datos = 0` (nunca un `UPDATE` que la invente); al iniciar sesión deben marcar la casilla y la autorización se guarda con el código correcto (ítem 3.5, hecho el 06/11/2026 en la API, la web y el móvil) | 3.5 |
| C.11 | Datos personales fuera de los registros técnicos | Ley 1581, art. 4 (seguridad y confidencialidad) | Ya cumplido en el 2.8: los registros no llevan correos ni códigos | Hecho |
| C.12 | Finalidad nueva: solicitudes de adopción y mensajes de contacto | Ley 1581, arts. 4 b y 12; Decreto 1377, art. 13 | La política pasa a la versión 1.1 (A.4, A.5 punto 7, A.11) y `VERSION_POLITICA_DATOS = "1.1"`: quien aceptó la 1.0 autoriza otra vez al iniciar sesión (C.9). Las rutas `POST /api/solicitudes/adopcion` y `/contacto` exigen sesión (`@require_auth`) y una cuenta activa con la autorización de la versión vigente; si no, 403 con `"requiere_autorizacion": true` (B.3) | 3.6 (parte 1, API) |
| C.13 | Conservar la prueba de la autorización de cada solicitud | Ley 1581, art. 17 b; Decreto 1377, art. 8 | Tabla `solicitudes`: `id_usuario` (del token, nunca del cuerpo), `version_politica_datos` (la que aceptó la cuenta) y `fecha_envio`. La API responde 201 solo si la fila se guardó | 3.6 (parte 1, API + BD) |
| C.14 | Minimización y confidencialidad | Ley 1581, art. 4 (finalidad, seguridad, confidencialidad) | La tabla no repite el nombre ni el correo (salen de la cuenta). Teléfono opcional y solo en adopción; un mensaje de contacto no guarda mascota ni teléfono (regla `chk_solicitud_tipo`). Mensaje de 10 a 1000 caracteres. Los registros técnicos no llevan el mensaje ni el teléfono. Límite de 5 envíos por minuto por IP | 3.6 (parte 1) |
| C.15 | Conservación | Decreto 1377, art. 11 | Si se borra la cuenta o la mascota, se borran sus solicitudes (`ON DELETE CASCADE`); A.11 | 3.6 (parte 1, BD) |

**Fuera del 3.1** (no mezclar): la consola (`vista/menu_usuarios.py`) es el 4.11. Desde el 3.1 guardará
`acepta_datos = 0` por el nuevo valor por defecto del modelo, que es lo honesto. *Hecho el 08/11/2026 (4.11): la
consola no pide la casilla, porque quien escribe es el administrador y no el titular (C.6); guarda `acepta_datos = 0`
explícito, sin fecha ni versión, y avisa que el titular autorizará al iniciar sesión (C.10, ítem 3.5). No cambia la
Parte A ni la versión.* Los formularios de adopción y contacto
se rotularon como demo en el 3.2 y envían datos desde el 3.6, con esta política en su versión 1.1 (C.12 a C.15).

---

## Parte D — Decisiones pendientes del dueño del proyecto

| # | Decisión | Recomendación |
|---|---|---|
| D.1 | Quién figura como responsable (A.1) y con qué correo de contacto | **Decidido el 06/11/2026:** PetConnect y sus asociados: Daniel Jimenez, Andrea Silva, Nelson Perez y Andrea Yasmin; Armenia, Quindío; Cra. 6 # 17 Norte 01; `proyectopetconnect+atencion@gmail.com`; 324 368 2078 |
| D.2 | Si se dice que es un proyecto formativo del SENA | Sí, mientras no sea un servicio real |
| D.3 | Dónde se alojará la API y la BD (A.9) | Llenarlo antes de publicar en internet (ítem 5.5) |
| D.4 | Solo mayores de 18 años (A.12) | **Decidido el 05/11/2026: sí**, declarado en la misma casilla (B.1) |
| D.5 | Cuánto se conserva la prueba de la autorización y si se borran las cuentas inactivas (A.11) | Pedir criterio al instructor |
| D.6 | Registro Nacional de Bases de Datos (RNBD) de la SIC | Según el Decreto 090 de 2018, hoy solo obliga a sociedades y entidades sin ánimo de lucro con activos de más de 100.000 UVT y a entidades públicas. **Verificar con el instructor** |
| D.7 | A.11 dice que un registro sin terminar “nunca llega a la base de datos”. Desde el ítem 4.6 (07/11/2026) sí llega: el nombre, el hash de la contraseña y la prueba de la autorización se guardan en la tabla `otp_pendientes` (el código va cifrado) y se borran al verificar, al bloquearse con 5 fallos o al vencer (10 minutos; los vencidos se borran cada vez que se pide un código y al arrancar la API). Corregir A.11 cambia el texto, y por C.9 eso obliga a subir `VERSION_POLITICA_DATOS` (todas las cuentas autorizan otra vez) | **Pendiente del dueño.** Texto sugerido: “Un registro que no terminaste: tus datos y el código se guardan en la base de datos hasta 10 minutos, el código cifrado, y se borran al terminar el registro, al vencer o tras 5 intentos fallidos”. Recomendación: hacerlo junto con el próximo cambio de la política (una sola subida de versión) y antes de publicarla |

---

## Parte E — Revisión de contenido (skill `/revision-contenido-mascotas`, 05/11/2026)

| Categoría | Archivo / sección | Hallazgo | Gravedad | Acción sugerida |
|---|---|---|---|---|
| Datos personales | Este archivo, A.1 | Desde el 06/11/2026 A.1 publica a propósito los nombres de los integrantes, una dirección y un teléfono (lo exige el Decreto 1377, art. 13). Cada integrante debe estar de acuerdo con que su nombre salga en la web, y conviene que el teléfono y la dirección sean del proyecto o del centro, no personales | Media | Confirmarlo con el equipo y el instructor antes de publicar |
| Datos personales | A.9 | La transmisión a Google (Gmail) y al futuro alojamiento debe revisarla un profesional | Media | Validar con el instructor; llenar D.3 |
| Datos personales | A.10 | Hoy la web y el móvil hablan con la API por HTTP sin cifrar en desarrollo (A-27), y el token del móvil está en AsyncStorage sin cifrar (A-28). A.10 no promete HTTPS a propósito | Media | Hacer el 5.3 antes de publicar en internet y entonces agregar “conexión cifrada (HTTPS)” a A.10 |
| Datos personales | A.11 | Hasta el 07/11/2026 los registros pendientes vencidos no se limpiaban de la memoria (A-12). El ítem 4.6 los pasó a la tabla `otp_pendientes` y los borra al vencer, pero A.11 todavía dice que “nunca llegan a la base de datos” | Media | Decidir D.7 (corregir A.11 con subida de versión) antes de publicar |
| Datos personales | Todo el archivo | Fuera de A.1 no hay datos de personas: solo marcadores `[PENDIENTE]` | — | Ninguna |
| Datos personales | A.4, A.5 punto 7, B.5 (versión 1.1, 07/11/2026) | Los mensajes son texto libre: alguien puede escribir datos sensibles o datos de otra persona. El aviso B.5 pide no hacerlo, pero no lo impide. Las solicitudes no llegan a quien publicó la mascota: el equipo hace de intermediario a mano | Media | Validar con el instructor que la autorización de la cuenta (sin casilla aparte, decisión del 07/11/2026) basta para esta finalidad |
| Salud animal | A.4 | Solo nombra que existen datos de vacunas; no da información veterinaria | — | No necesita `REVISAR-VETERINARIO` |
| Imágenes | — | No hay imágenes | — | Ninguna |
| Legal | Todo el archivo | Lo redactó una IA; las citas (Ley 1581 arts. 3, 8, 9, 10, 12, 14, 15, 16, 17, 26; Decreto 1377 arts. 7, 8, 11, 13, 24, 25; Decreto 090 de 2018) se deben comparar con el texto oficial | Alta | Validación del dueño y del instructor |

**Veredicto: pendiente de** llenar D.2, D.3, D.5 y D.6 (D.1 y D.4 ya están decididos), validar el texto legal con el instructor y hacer el 5.3 (HTTPS) antes de
publicar en internet. Para desarrollo y para la evidencia GA9, el borrador sirve para implementar las 3 partes del 3.1.
