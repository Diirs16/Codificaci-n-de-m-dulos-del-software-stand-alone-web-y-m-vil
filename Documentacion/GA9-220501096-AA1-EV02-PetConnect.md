> **Fuente en Markdown del plan de pruebas.** La versión para entregar es `GA9-220501096-AA1-EV02-PetConnect.docx`, que ya aplica el formato APA 7 (Times New Roman 12, interlineado doble, texto alineado a la izquierda, sangría de 1,27 cm, número de página arriba a la derecha y títulos de nivel 1 a 3). En este archivo, `##` = Nivel 1, `###` = Nivel 2 y `####` = Nivel 3.

# Plan de Pruebas de Software para la Aplicación PetConnect

Camilo Esteban Orjuela Bonilla, Jazmín Andrea Bautista Oyuela, Yuli Andrea Silva Segura, Valentina Lobo Mccausland y Daniel Santiago Jiménez Guzmán

Tecnología en Análisis y Desarrollo de Software (ADSO) – Ficha 3235905

Servicio Nacional de Aprendizaje (SENA)

GA9-220501096-AA1-EV02: Realiza plan de pruebas de software

Ing. Miguel Andrés Arévalo Vela

Octubre de 2026

---

**Tabla 1**

*Información de control del documento*

| Campo | Valor |
|---|---|
| Identificador del plan | PP-PETCONNECT-2026-01 |
| Versión | 2.2 – Revisión técnica integral, alineación con la ERS y resultados de la primera ejecución de casos |
| Versiones anteriores | 1.0 – Borrador del equipo; 2.0 – Revisión técnica contra el código; 2.1 – Alineación con la ERS |
| Línea base de requerimientos | Especificación de los requerimientos funcionales y no funcionales del software (ERS) del proyecto: RF01–RF11, RNF01–RNF07, RIU01–RIU03, RS01–RS03, RR01–RR02 y RM01–RM02 |
| Base de código revisada | Repositorio del proyecto (carpeta `Evidecia`), rama `main`, commit `c4310dc` |
| Metodología | Scrum, seleccionada en la evidencia GA1-220501092-AA5-EV02 |
| Fecha de la revisión | 2 de octubre de 2026 (revisión técnica); 5 de octubre de 2026 (actualización con la ejecución) |
| Primera ejecución de casos | 5 de octubre de 2026: casos CP-001 a CP-012 de la evidencia GA9-220501096-AA2-EV01, con evidencias en `Documentacion/Evidencias-GA9-AA2-EV01` |
| Norma de documentación | ISO/IEC/IEEE 29119-3:2021 |
| Modelo de calidad | ISO/IEC 25010:2023 |
| Aprobación | Líder de pruebas y Scrum Master: Daniel Santiago Jiménez Guzmán |

## Introducción

PetConnect es una aplicación móvil integral para el cuidado de mascotas, dirigida a propietarios, fundaciones de adopción y proveedores de servicios veterinarios. Según su especificación de requerimientos (ERS), el sistema debe permitir el registro de usuarios y de una o varias mascotas, almacenar el carné de vacunación, mostrar un directorio de servicios veterinarios, ofrecer una comunidad de dueños, llevar un diario de salud y comportamiento, y publicar y adoptar mascotas; el GPS en tiempo real y la tienda virtual completan la versión premium. La solución se compone de una aplicación móvil híbrida construida con React Native sobre Expo, un cliente web en React con Vite, una API REST y una base de datos relacional compatible con MySQL (MariaDB 10.4 en el entorno local y MySQL 8 como objetivo del staging); el entorno de staging objetivo es una infraestructura de contenedores Docker sobre Amazon Web Services (AWS).

Este documento es la versión oficial del plan de pruebas. Integra el trabajo del equipo con una revisión técnica que contrastó los requerimientos de la ERS con el código fuente del repositorio. Esa comprobación arrojó dos conclusiones que condicionan todo el plan. La primera es que la API REST está implementada en Python 3 con Flask 3.1 y no en Node.js con Express, como se había asumido en el borrador; por eso el plan adopta la arquitectura verificada y ajusta las herramientas de prueba del servidor, conservando Jest para la capa JavaScript (móvil y web). La segunda es que el código confirma la no conformidad NC-001 (contraseñas almacenadas con SHA-256, tal como lo indica RS03) y presenta otros defectos de seguridad, desempeño y protección de datos, entre ellos uno que deja inutilizables los endpoints protegidos; todos se registran en la bitácora de no conformidades. La revisión del entorno mostró además que el servidor de base de datos local es MariaDB 10.4.32 y no MySQL 8, como indica el README. Por último, la primera ejecución de casos, el 5 de octubre de 2026 (evidencia GA9-220501096-AA2-EV01), confirmó varias de esas no conformidades y agregó tres nuevas (NC-009 a NC-011).

El plan se fundamenta en el modelo de calidad de producto ISO/IEC 25010, cuya edición de 2023 organiza la calidad en nueve características (International Organization for Standardization [ISO], 2023), y sigue la estructura documental de ISO/IEC/IEEE 29119-3 para planes, casos y reportes de prueba (ISO, 2021). La ejecución se orienta por los siete principios del proceso de pruebas analizados por Mera Paz (2016), en especial el de pruebas tempranas, que justifica la revisión estática de la ERS y del código realizada antes de construir las nuevas funcionalidades. La automatización se distribuye según la pirámide de pruebas de Cohn (2009), que privilegia las pruebas unitarias rápidas y económicas sobre las de interfaz, y las funcionalidades nuevas se construyen con desarrollo guiado por pruebas (TDD) en el ciclo rojo, verde y refactorizar descrito por Beck (2002), integrado en los sprints de Scrum (Schwaber y Sutherland, 2020), la metodología que el equipo seleccionó para el proyecto.

Dado que PetConnect trata datos personales de los propietarios, el plan concreta el requerimiento RNF06 en la Ley Estatutaria 1581 de 2012 de protección de datos personales (Congreso de la República de Colombia, 2012) y adopta como marco de verificación de seguridad el OWASP Top 10:2025 (OWASP Foundation, 2025).

## Objetivos

### Objetivo General

Planificar, organizar y controlar las actividades de verificación y validación de la aplicación PetConnect durante los Sprints 1 a 3 (octubre y noviembre de 2026), para evidenciar antes de su liberación el cumplimiento de los requerimientos de la ERS bajo el modelo de calidad ISO/IEC 25010.

### Objetivos Específicos

1. Analizar mediante pruebas estáticas los requerimientos de la ERS y contrastarlos con el código fuente, para detectar ambigüedades e inconsistencias antes de construir las nuevas funcionalidades.
2. Definir la estrategia, los niveles y las técnicas de prueba según la pirámide de Cohn (70 % unitarias, 20 % integración y 10 % extremo a extremo) y el ciclo TDD integrado en Scrum.
3. Diseñar los casos de prueba CP-001 a CP-019 y trazarlos hacia los requerimientos y las historias de usuario del proyecto.
4. Verificar los mecanismos de seguridad (RS01 a RS03 y RNF03) frente al OWASP Top 10:2025 y el cumplimiento de la Ley 1581 de 2012 (RNF06).
5. Evaluar el desempeño (RNF04, RR01 y RR02) con 500 usuarios de carga normal, 1000 de carga pico y estrés hasta 1500, la usabilidad (RNF02) con el cuestionario SUS y la compatibilidad, la accesibilidad y el SEO de la versión web (RNF05) con Lighthouse.
6. Establecer los criterios de entrada, salida, suspensión y reanudación, el procedimiento, las métricas, la bitácora de no conformidades y la matriz de riesgos que soportan la decisión de liberación.

## Descripción y Análisis Técnico del Sistema Bajo Prueba

### Arquitectura del Sistema Bajo Prueba

La ERS no fija la tecnología de implementación. La Tabla 2 contrasta la arquitectura que asumía el borrador con la verificada en el repositorio; la última columna explica cómo cada diferencia modifica la estrategia de pruebas.

**Tabla 2**

*Arquitectura del sistema bajo prueba: asumida frente a verificada*

| Capa | Asumido en el borrador | Verificado en el repositorio | Estado | Implicación para las pruebas |
|---|---|---|---|---|
| Aplicación móvil | React Native | React Native 0.86 sobre Expo SDK 57, React Navigation 7 y AsyncStorage (`PetConnect.Mobile`); Expo permite compilar para Android e iOS | Conforme | Jest con `jest-expo` y React Native Testing Library; Maestro para E2E |
| Versión web | React | React 19 con Vite 8 y Tailwind CSS 4 (`PetConnect.Front`) | Conforme | Jest o Vitest con Testing Library; Cypress para E2E; Lighthouse |
| API REST | Node.js con Express | Python 3.14 con Flask 3.1.3 y Flask-CORS (`petconnect.Backend/api.py`) | Inconsistencia IN-01, corregida en este plan | pytest y el cliente de pruebas de Flask cumplen el rol de Supertest; Postman y Newman con las colecciones existentes |
| Seguridad | JWT y bcrypt | JWT HS256 con PyJWT (vigencia de 24 h), OTP de 6 dígitos (vigencia de 10 min) y cifrado Fernet; contraseñas con SHA-256 sin sal; el `sub` del JWT se emite como entero y PyJWT 2.13 lo rechaza | No conforme (NC-001 y NC-008) | Pruebas de seguridad prioritarias; bcrypt y la validación del token son criterios de salida |
| Datos | MySQL 8 | MariaDB 10.4.32 (XAMPP, compatible con MySQL) en el puerto 3310, con modo SQL no estricto; `mysql-connector-python` 9.1, patrón DAO y conexión única Singleton | Diferencia de motor (IN-02) | Integración contra MariaDB local y contra MySQL 8 en Docker y staging; el modo no estricto guarda vacíos los valores inválidos (NC-009); la conexión única compartida limita la concurrencia y el escalado (NC-003, RM02); MariaDB 10.4 dejó de recibir soporte en junio de 2024 |
| Infraestructura | Docker en AWS | No existen `Dockerfile` ni `docker-compose.yml`; la API corre con el servidor de desarrollo de Flask y `debug=True` | Pendiente | La provisión del staging es criterio de entrada para las pruebas no funcionales |

*Nota.* Elaboración propia a partir de la revisión del repositorio (commit `c4310dc`, 2 de octubre de 2026). El repositorio no contiene pruebas automatizadas; la suite descrita en este plan se construye desde cero.

Según el diagrama de clases del proyecto, las entidades principales son `Usuario`, `Mascota`, `Vacunacion`, `Servicios` y `PublicacionAdopcion`. La Tabla 3 las relaciona con su estado en el código y con el enfoque de prueba que les corresponde: las clases existentes reciben pruebas de regresión y las nuevas se construyen con TDD.

**Tabla 3**

*Mapeo de clases principales del dominio*

| Clase | Estado en el repositorio | Atributos clave | Requerimientos | Enfoque de prueba |
|---|---|---|---|---|
| `Usuario` | Existe (`modelo/usuario.py`, `dao/usuario_dao.py`) | `id_usuario`, `correo`, `password_hash`, `estado`, `verificado`, `acepta_datos` | RF01, RIU01, RS01, RS03, RNF06 | Regresión, seguridad y cumplimiento de la Ley 1581 |
| `Mascota` | Existe (`modelo/mascota.py`, `dao/mascota_dao.py`) | `id_mascota`, `id_usuario` (propietario), `nombre`, `especie`, `raza`, `edad_aprox`, `foto`, `estado` | RF02, RF04, RIU02 | Regresión y control de acceso por propietario |
| `Servicios` (`ProveedorServicio`) | Existe el modelo y el DAO; aún no hay endpoint REST | `nombre`, `ciudad`, `horario`, `atiende_24_7`, `latitud`, `longitud` | RF06 | Regresión y desempeño de la búsqueda |
| `Vacunacion` | Nueva | `idMascota`, `nombreVacuna`, `fechaAplicacion`, `periodicidadDias`, `lote`, `veterinario` | RF03, RS02 | TDD, integración y E2E |
| `PublicacionAdopcion` | Nueva | `idPublicacion`, `idMascota`, `idPublicador`, `estado` (Disponible, En proceso, Adoptado) | RF09 | TDD, transición de estados y E2E |

*Nota.* La comunidad (RF07) y el diario de salud (RF08) introducen además las clases nuevas `Publicacion`, `Comentario` y `EntradaDiario`, que siguen el mismo enfoque que `Vacunacion`.

### Análisis de Requerimientos y Detección de Inconsistencias

Las pruebas estáticas se aplicaron antes de cualquier ejecución dinámica, en coherencia con el principio de pruebas tempranas: un defecto detectado en el requisito o en la revisión de código cuesta menos que uno detectado en producción (Mera Paz, 2016). El análisis revisó cada requerimiento de la ERS en busca de ambigüedad, contradicción y falta de criterio medible, e inspeccionó el código existente para comprobar si lo implementado coincide con lo especificado. A cada requerimiento funcional se le asignó una prioridad y un nivel de riesgo según el impacto que tendría una falla sobre el usuario, sus datos o su mascota.

**Tabla 4**

*Requerimientos funcionales de la ERS priorizados por nivel de riesgo*

| ID | Requerimiento funcional (ERS) | Clasificación | Prioridad | Riesgo | Justificación del riesgo |
|---|---|---|---|---|---|
| RF01 | Permitir al usuario registrarse mediante un formulario | Existente | Alta | Alto | Puerta de entrada al sistema; maneja credenciales y datos personales |
| RF02 | Permitir ingresar los datos de una mascota | Existente | Alta | Medio | Base del carné, el diario y la adopción |
| RF03 | Almacenar el carné de vacunación de cada mascota registrada | Nueva | Alta | Alto | Información vinculada al propietario (RS02); el recordatorio de dosis depende de un cálculo de fechas |
| RF04 | Permitir al usuario registrar más de una mascota | Existente | Alta | Medio | Relación de uno a muchos; riesgo de mezclar datos entre mascotas |
| RF05 | Ofrecer opciones para explorar después del registro | Existente | Media | Bajo | Navegación; impacto acotado |
| RF06 | Mostrar un directorio de servicios veterinarios y relacionados | Existente | Alta | Medio | Búsqueda con riesgo de latencia (NC-003) |
| RF07 | Permitir acceder a una comunidad de dueños de mascotas | Nueva | Media | Medio | Contenido generado por usuarios: XSS almacenado y contenido inapropiado |
| RF08 | Permitir llevar un diario de salud y comportamiento | Nueva | Media | Medio | Información sensible para el propietario; exige integridad y autenticación (RS01) |
| RF09 | Permitir publicar y adoptar mascotas | Nueva (la consulta del catálogo ya existe) | Alta | Medio | Flujo con estados y dos actores; riesgo de publicaciones falsas |
| RF10 | Ofrecer GPS en tiempo real para localizar mascotas | Fuera de alcance (premium) | Baja | Alto | Solo revisión estática en este ciclo |
| RF11 | Permitir compras en una tienda virtual integrada | Fuera de alcance (premium) | Baja | Alto | Solo revisión estática; ya existen `/api/productos` y el carrito web |

La Tabla 5 reúne los requerimientos no funcionales, de interfaz, de seguridad, de rendimiento y de mantenimiento. Varios están redactados en la ERS sin un umbral verificable; para cada uno se adopta un criterio medible, porque un requisito sin umbral no se puede aprobar ni rechazar de forma objetiva.

**Tabla 5**

*Requerimientos no funcionales de la ERS y criterio medible adoptado*

| ID | Requerimiento (ERS) | Criterio medible adoptado en el plan | Verificación |
|---|---|---|---|
| RNF01 | Disponibilidad 24/7 de al menos 99 % | Disponibilidad mensual ≥ 99 % en staging (máximo 7,3 h de caída al mes) | Monitoreo con Amazon CloudWatch |
| RNF02 | Interfaz intuitiva para usuarios no técnicos | Puntaje SUS ≥ 68 y ≥ 90 % de éxito en las tareas críticas sin ayuda, con al menos un participante adulto mayor | CP-018 |
| RNF03 | Información protegida mediante autenticación y cifrado | Se concreta en RS01 a RS03; HTTPS con TLS 1.2 o superior; cifrado Fernet de datos personales sensibles en reposo | Pruebas de seguridad, OWASP ZAP |
| RNF04 | Tiempo de respuesta ≤ 2 s por acción | Percentil 95 ≤ 2 s por acción con carga normal (500 usuarios concurrentes, 50 % de RR01) | CP-017 (JMeter) |
| RNF05 | Compatibilidad con móviles y navegadores modernos | Android 10 o superior, iOS 15 o superior y las dos últimas versiones de Chrome, Edge y Firefox; versión web con Lighthouse ≥ 90 en Accesibilidad, Buenas prácticas y SEO | CP-019, Lighthouse |
| RNF06 | Cumplir la ley de protección de datos personales vigente | Ley 1581 de 2012: autorización previa, expresa e informada, registrada con fecha y versión de la política; derechos a conocer, actualizar, rectificar y suprimir; solo datos sintéticos en pruebas | CP-001, lista de chequeo |
| RNF07 | Respaldos diarios de usuarios y mascotas | Respaldo automático diario; restauración completa verificada una vez por sprint con pérdida máxima de 24 h de datos | Prueba de respaldo y restauración |
| RIU01 | Registro con campos de nombre, correo y contraseña | Campos presentes, obligatorios y validados en el cliente y en el servidor | CP-001, CP-003 |
| RIU02 | Formulario de mascota con nombre, especie, raza, edad y foto | Campos presentes; edad válida entre 0 y 30 años | CP-007, CP-008 |
| RIU03 | Menú principal con íconos de comunidad, tienda, GPS, diario, etc. | Todos los íconos visibles; tienda y GPS muestran un aviso de versión premium sin errores | CP-007, revisión de interfaz |
| RS01 | Exigir autenticación para funciones como el diario o el registro de mascotas | Toda ruta privada exige un JWT válido (401 sin token); inicio de sesión en dos pasos con OTP de 6 dígitos, vigencia de 10 min y máximo 5 intentos; secreto JWT obligatorio y vigencia de 24 h | CP-005, CP-006 |
| RS02 | Carné de vacunación visible solo por el usuario dueño | Autorización por objeto: cualquier otro usuario recibe 403 o 404, sin datos del carné en la respuesta | CP-012 |
| RS03 | Encriptar las contraseñas con un algoritmo estándar (ej. SHA-256) | bcrypt con sal aleatoria y factor de costo 12. Política: mínimo 8 caracteres con al menos una mayúscula, una minúscula y un número; máximo 64 | CP-003, CP-004 |
| RR01 | Soportar hasta 1000 usuarios activos simultáneos | Error < 1 % y percentil 95 ≤ 5 s con 1000 usuarios; estrés hasta 1500 con recuperación ≤ 5 min | CP-017 |
| RR02 | Tiempo de carga de cada módulo ≤ 5 minutos | Corregido a ≤ 5 s por módulo, también en la carga pico de RR01 | CP-017, Lighthouse |
| RM01 | Agregar módulos sin afectar los existentes | Regresión automatizada en verde después de cada módulo nuevo; cobertura ≥ 80 % en dominio y 100 % en funciones de seguridad | Integración continua |
| RM02 | Base de datos escalable horizontalmente | Pool de conexiones y despliegue compatible con réplicas de lectura de Amazon RDS | Revisión de arquitectura; NC-003 |

*Nota.* Los requerimientos de rendimiento (RR) de la ERS corresponden a la característica de eficiencia de desempeño de ISO/IEC 25010.

#### Verificación de Hallazgos

La revisión estática de la ERS y de las historias de usuario identificó inconsistencias que deben aclararse con el Product Owner. Al contrastar con el código se agregaron los hallazgos de implementación. La Tabla 6 resume ambos grupos.

**Tabla 6**

*Hallazgos de la revisión de la ERS y del código*

| ID | Hallazgo | Corrección acordada | Verificación en el código | Estado |
|---|---|---|---|---|
| H-01 | RS03 pide "encriptar" las contraseñas con SHA-256. SHA-256 es una función de resumen rápida y sin sal, y una contraseña no se cifra (proceso reversible) sino que se transforma con una función de derivación irreversible | Almacenar con bcrypt (sal aleatoria y costo 12) y corregir la redacción de RS03 | `api.py` (función `_hash_password`, líneas 66–67) y `vista/menu_usuarios.py` (línea 67) usan `hashlib.sha256`; `bcrypt` no figura en `requirements.txt` | Abierto como NC-001 (bloqueante) |
| H-02 | RR02 fija "5 minutos" de carga por módulo, valor incompatible con RNF04 (2 s por acción) | RNF04: ≤ 2 s por acción; RR02: ≤ 5 s por módulo | Los listados no se paginan y la conexión a la base de datos es única y compartida, por lo que se anticipa incumplimiento | Requisito corregido; riesgo abierto como NC-003 |
| H-03 | La historia de usuario de RF01 indica "máximo 8 caracteres" para la contraseña, mientras que la seguridad exige una longitud mínima | Mínimo 8 caracteres con mayúscula, minúscula y número; máximo 64 (RS03) | `_validate_password` (`api.py`, líneas 70–79) exige longitud, mayúscula, número y carácter especial, pero no verifica la minúscula: acepta `PETCONNECT1!` | Abierto como NC-004 |
| H-04 | RF03 solo exige "almacenar" el carné; el diagrama de clases incluye `generarRecordatorio()`, pero la ERS no define recordatorios ni su anticipación | Incorporar a RF03 el recordatorio de la próxima dosis con una anticipación de 3 días, valor por confirmar con el Product Owner | Funcionalidad nueva, aún no implementada | Requisito a actualizar por control de cambios |
| H-05 | RF10 y RF11 son premium, pero RIU03 exige sus íconos en el menú principal | Los íconos se muestran con un aviso de versión premium | — | Criterio agregado a RIU03 |
| H-06 | El borrador asumía una API en Node.js con Express | Documentar la arquitectura real | La API está implementada en Flask (Python) | Corregido en este plan (IN-01) |
| H-07 | El borrador asumía Docker en AWS | Provisionar el staging antes del Sprint 3 | No hay artefactos de contenedores ni de infraestructura | Criterio de entrada; riesgo R06 |
| H-08 | RNF06 exige cumplir la ley de protección de datos | Capturar la autorización expresa del titular | `/api/auth/verify` crea el usuario con `acepta_datos=True` fijo (`api.py`, línea 401) y los formularios de registro no muestran casilla de autorización | Abierto como NC-005 |
| H-09 | RS01 depende de que el token emitido sea aceptado | El token debe validarse en los endpoints protegidos | Prueba dinámica temprana con PyJWT 2.13.0: un token con `sub` entero, como el que emite `generate_token()`, se rechaza con `InvalidSubjectError: Subject must be a string` | Abierto como NC-008 |
| H-10 | El README y el borrador indicaban MySQL 8 como base de datos | Documentar el motor real; probar en MariaDB local y en MySQL 8 (Docker y staging) con modo SQL estricto; planear la migración del entorno local a una versión con soporte | `SELECT VERSION()` devuelve `10.4.32-MariaDB` y el `sql_mode` del servidor no incluye `STRICT_TRANS_TABLES` | Corregido en este plan (IN-02); el modo no estricto origina NC-009 |

*Nota.* H-01 a H-05 provienen de la revisión estática de la ERS y de las historias de usuario; H-06 a H-10, del contraste con el código y el entorno del repositorio.

El hallazgo H-01 merece una explicación adicional, porque es la principal amenaza a la confidencialidad del sistema. SHA-256 está diseñado para ser rápido: una GPU moderna calcula miles de millones de resúmenes por segundo, lo que hace viables los ataques de diccionario y de fuerza bruta si la base de datos se filtra. Además, al no usar sal, dos usuarios con la misma contraseña obtienen el mismo resumen, lo que habilita las tablas precalculadas (*rainbow tables*). bcrypt, en cambio, incorpora una sal aleatoria en cada resumen y un factor de costo adaptativo: con costo 12 se ejecutan 2^12 rondas de expansión de clave, lo que lleva el cálculo de un solo resumen al orden de cientos de milisegundos. La guía de OWASP recomienda bcrypt con un factor de trabajo de 10 o superior cuando no se dispone de Argon2id (OWASP Foundation, s.f.).

La corrección introduce tres condiciones que el plan prueba explícitamente. Primera, bcrypt solo procesa los primeros 72 bytes de la contraseña, por lo que se fija una longitud máxima de 64 caracteres y se prueba ese valor límite. Segunda, los usuarios ya registrados tienen resúmenes SHA-256, de modo que se requiere una migración: al siguiente inicio de sesión exitoso se valida el resumen heredado y se reemplaza por uno bcrypt (CP-004). Tercera, el costo de bcrypt consume CPU en cada inicio de sesión, así que el escenario de autenticación se mide por separado en la prueba de carga.

### Clasificación de Funcionalidades Existentes y Nuevas

Las funcionalidades existentes ya se desarrollaron en sprints anteriores y requieren pruebas de regresión para confirmar que los cambios nuevos no las dañan. Las funcionalidades nuevas reciben el ciclo completo de pruebas.

**Tabla 7**

*Clasificación de funcionalidades y tipo de prueba aplicable*

| Funcionalidad | Clasificación | Evidencia en el repositorio | Tipo de prueba | Herramientas |
|---|---|---|---|---|
| Registro e inicio de sesión (RF01, RIU01, RS01) | Existente | Endpoints `/api/auth/*`; pantallas `LoginScreen` y `RegisterScreen` | Humo, regresión y seguridad | pytest, Newman, Maestro |
| Registro de una o varias mascotas (RF02, RF04, RIU02) | Existente | `Mascota`, `MascotaDAO`, menú de consola | Humo y regresión | pytest |
| Menú de exploración (RF05, RIU03) | Existente | `HomeScreen` y navegación por pestañas | Humo y regresión | Maestro |
| Directorio de servicios (RF06) | Existente | `ProveedorServicio`, `ProveedorDAO` | Humo, regresión y desempeño | pytest, Newman, JMeter |
| Carné de vacunación con recordatorios (RF03, RS02) | Nueva | No existe | TDD, integración y E2E | Jest, pytest, Maestro |
| Comunidad (RF07) | Nueva | No existe | TDD, integración y seguridad (XSS) | Jest, pytest, OWASP ZAP |
| Diario de salud y comportamiento (RF08) | Nueva | No existe | TDD e integración | Jest, pytest |
| Publicación y adopción (RF09) | Nueva | Solo existe la consulta (`GET /api/mascotas/adopcion` y `AdoptionScreen`), que hoy devuelve una lista vacía (NC-009) | TDD, transición de estados, integración y E2E | Jest, pytest, Maestro, Cypress |
| GPS en tiempo real (RF10) | Fuera de alcance (premium) | `ProveedorServicio` guarda coordenadas estáticas, sin seguimiento en vivo | Solo revisión estática | — |
| Tienda virtual (RF11) | Fuera de alcance (premium) | Existen `/api/productos` y el carrito del módulo web | Solo revisión estática; los defectos incidentales van al backlog | — |

*Nota.* También quedan fuera del alcance las pasarelas de pago reales, la integración con WhatsApp y los dispositivos GPS físicos; cuando una prueba los necesite, se reemplazarán por servicios simulados.

### Estrategia y Niveles de Prueba

#### Evaluación con el Modelo ISO/IEC 25010

La estrategia asigna una prioridad a cada característica del modelo según el contexto de PetConnect: una aplicación móvil que trata datos personales, con picos de uso y usuarios sin formación técnica.

**Tabla 8**

*Evaluación de PetConnect con el modelo de calidad ISO/IEC 25010:2023*

| Característica | Subcaracterísticas priorizadas | Requerimientos | Métrica o umbral | Prioridad |
|---|---|---|---|---|
| Adecuación funcional | Completitud, corrección y pertinencia funcional | RF01–RF09 | 100 % de casos de prioridad alta aprobados | Alta |
| Eficiencia de desempeño | Comportamiento temporal, utilización de recursos y capacidad | RNF04, RR01, RR02 | p95 ≤ 2 s (500 usuarios) y ≤ 5 s (1000 usuarios); error < 1 % | Alta |
| Compatibilidad | Coexistencia e interoperabilidad | RNF05 | Matriz de dispositivos y navegadores sin fallos bloqueantes | Media |
| Capacidad de interacción | Aprendizaje, operabilidad, protección frente a errores e inclusividad | RNF02, RIU01–RIU03, RNF05 | SUS ≥ 68; Lighthouse Accesibilidad ≥ 90 | Alta |
| Fiabilidad | Disponibilidad y recuperabilidad | RNF01, RNF07 | Disponibilidad ≥ 99 %; restauración diaria verificada | Media |
| Seguridad | Confidencialidad, integridad, autenticidad, responsabilidad y resistencia | RNF03, RNF06, RS01–RS03 | Cero no conformidades críticas o altas abiertas | Crítica |
| Mantenibilidad | Modularidad, analizabilidad y capacidad de prueba | RM01 | Cobertura ≥ 80 % en dominio y 100 % en seguridad | Media |
| Flexibilidad | Escalabilidad e instalabilidad | RM02, RR01 | Escalado horizontal de la API y de la base de datos | Media |
| Protección (*safety*) | Advertencia de peligros | RF08 | El diario advierte que no reemplaza la consulta veterinaria | Baja |

*Nota.* La característica "capacidad de interacción" corresponde a la antigua "usabilidad" de ISO/IEC 25010:2011, renombrada en la edición de 2023 (ISO, 2023).

#### Aplicación de los Siete Principios de las Pruebas

Mera Paz (2016) recoge siete principios que orientan cualquier proceso de pruebas. La Tabla 9 muestra cómo se aplica cada uno en PetConnect.

**Tabla 9**

*Aplicación de los siete principios de las pruebas en PetConnect*

| Principio | Aplicación concreta en PetConnect |
|---|---|
| 1. Las pruebas muestran la presencia de defectos, no su ausencia | Un ciclo sin fallas se reporta como "sin defectos encontrados con los casos ejecutados"; los criterios de salida se basan en riesgo residual aceptado |
| 2. Las pruebas exhaustivas son imposibles | Se prioriza por riesgo (Tabla 4) y se usan partición de equivalencia y valores límite: contraseña de 7, 8, 9, 64 y 65 caracteres; edad de mascota de −1, 0, 30 y 31 años |
| 3. Pruebas tempranas | La revisión del 2 de octubre detectó cinco inconsistencias en la ERS y ocho no conformidades en el código antes de escribir código nuevo; la primera ejecución, el 5 de octubre, agregó tres más (NC-009 a NC-011) |
| 4. Agrupamiento de defectos | La mayoría de las no conformidades se concentran en `api.py` y en sus módulos de seguridad; autenticación y carné reciben la mayor densidad de casos |
| 5. Paradoja del pesticida | Los datos de prueba se rotan en cada sprint, cada no conformidad genera un caso de regresión nuevo y se programan sesiones de prueba exploratoria |
| 6. Las pruebas dependen del contexto | Aplicación con datos personales y de salud animal: seguridad y privacidad (RNF03, RNF06) pesan más que en una aplicación informativa |
| 7. Falacia de la ausencia de errores | Además de verificar, se valida con usuarios reales que la aplicación resuelve su necesidad (SUS ≥ 68) y con el Product Owner en cada Sprint Review |

#### Pirámide de Pruebas

Cohn (2009) propone concentrar la automatización en la base de la pirámide, porque las pruebas unitarias son rápidas, estables y localizan el defecto con precisión, mientras que las de interfaz son lentas y frágiles. Los porcentajes de la Tabla 10 se refieren al número de casos automatizados, no al esfuerzo.

**Tabla 10**

*Distribución de la pirámide de pruebas de PetConnect*

| Nivel | Proporción | Técnica | Herramientas | Alcance | Responsable |
|---|---|---|---|---|---|
| Unitarias | 70 % | Caja blanca: cobertura de sentencias y ramas, partición de equivalencia y valores límite | Jest, `jest-expo` y React Native Testing Library (móvil); Jest o Vitest (web); pytest y pytest-cov (API en Python) | Clases de dominio (`Vacunacion`, `PublicacionAdopcion`), validadores y DAO con dobles de prueba | Cada desarrollador; revisión de Daniel Jiménez |
| Integración | 20 % | Caja gris: contratos de la API, autenticación JWT y persistencia | pytest con el cliente de pruebas de Flask (equivalente a Supertest); MariaDB 10.4 local y MySQL 8 en Docker; Postman y Newman | Endpoints REST, autorización por objeto y transacciones | Camilo Orjuela |
| Extremo a extremo (E2E) | 10 % | Caja negra sobre flujos completos | Maestro (Android e iOS) y Cypress (web) | Registro → OTP → mascota → vacuna → carné; publicación y adopción | Yuli Silva (móvil) y Daniel Jiménez (web) |

*Nota.* Supertest es una librería exclusiva de Node.js; al estar la API en Flask, su función la cumple `app.test_client()`, que ejecuta solicitudes HTTP contra la aplicación sin levantar un servidor.

#### Técnicas de Caja Blanca y Caja Negra

Las pruebas de caja blanca se diseñan conociendo el código fuente y buscan recorrer sus caminos lógicos (Myers et al., 2011). En PetConnect se exige una cobertura mínima del 80 % de sentencias y ramas en la lógica de dominio, medida con pytest-cov en la API y con Jest en los módulos móvil y web, y del 100 % en las funciones de seguridad (hash, validación de contraseña, emisión y verificación del token). Las pruebas de caja negra se diseñan a partir de la especificación y aplican tres técnicas. La partición de equivalencia divide, por ejemplo, la edad de la mascota (RIU02) en una clase válida (0 a 30 años) y clases inválidas (negativa, texto y mayor de 30). El análisis de valores límite prueba los bordes de cada clase, como las longitudes de contraseña de 7, 8 y 9 caracteres y de 64 y 65 caracteres. La prueba de transición de estados se aplica a la publicación de adopción (RF09), cuyas reglas resume la Tabla 11.

**Tabla 11**

*Transiciones de estado de una publicación de adopción (RF09)*

| Estado actual | Evento | Estado siguiente | Resultado esperado |
|---|---|---|---|
| Disponible | El publicador acepta una solicitud de adopción para revisión | En proceso | Transición válida |
| En proceso | El publicador aprueba la adopción | Adoptado | Transición válida; la mascota sale del catálogo |
| En proceso | El publicador rechaza la solicitud | Disponible | Transición válida; la mascota vuelve al catálogo |
| Disponible | Se intenta marcar como Adoptado sin solicitud en proceso | Sin cambio | Transición inválida: error 409 |
| Adoptado | Cualquier evento | Sin cambio | Estado final: toda transición se rechaza |

*Nota.* Las reglas de las dos últimas filas son una propuesta del equipo de pruebas y deben confirmarse con el Product Owner en el Sprint Planning del Sprint 3.

#### Pruebas No Funcionales

**Desempeño y estrés.** Se ejecutan con Apache JMeter desde una instancia independiente de la API, para que el generador de carga no compita por recursos con el sistema medido. La carga normal se fija en 500 usuarios (50 % de RR01) y la carga pico en los 1000 usuarios que exige RR01. Las solicitudes que envían correo usan el modo `smtp` (sandbox de Mailtrap) y nunca Gmail, para no despachar mensajes reales ni agotar los límites diarios de envío de la cuenta.

**Tabla 12**

*Escenarios de prueba de desempeño y estrés*

| Escenario | Perfil de carga | Mezcla de transacciones | Criterio de aprobación |
|---|---|---|---|
| Carga normal (RNF04) | 500 usuarios concurrentes durante 15 min | 40 % catálogo de adopción, 25 % directorio, 25 % carné y diario, 10 % inicio de sesión | p95 ≤ 2 s por acción; error < 1 % |
| Carga pico (RR01, RR02) | Rampa de 0 a 1000 usuarios en 10 min y meseta de 30 min, con pausas aleatorias de 3 a 7 s | Igual a la carga normal | p95 ≤ 5 s; carga de módulo ≤ 5 s; error < 1 %; CPU < 80 % |
| Estrés | Escalones de 250 usuarios cada 5 min desde 1000 hasta 1500, o hasta que el error supere el 5 % | Igual a la carga normal | Identificar el punto de quiebre; recuperación ≤ 5 min al retirar la carga |
| Autenticación aislada | Inicio de sesión creciente hasta saturar la CPU | 100 % inicio de sesión con bcrypt costo 12 | Documentar la capacidad máxima de inicios de sesión por segundo |

**Usabilidad.** Se aplica el System Usability Scale (SUS), un cuestionario de diez afirmaciones con escala de cinco puntos (Brooke, 1996). A cada ítem impar se le resta 1 a la respuesta; a cada ítem par, la respuesta se resta de 5; la suma se multiplica por 2,5 y se obtiene un puntaje de 0 a 100. El umbral de 68 corresponde al promedio de referencia de la escala (Sauro, 2011). Participan ocho usuarios representativos, entre ellos al menos un adulto mayor, en sesiones moderadas con el APK instalado en un dispositivo físico. Las tareas son: registrarse e iniciar sesión, registrar una mascota, registrar una vacuna y consultar el carné, crear una entrada del diario y publicar o solicitar una adopción.

**Seguridad.** La verificación toma como marco el OWASP Top 10:2025 (OWASP Foundation, 2025) y combina análisis dinámico con OWASP ZAP, auditoría de dependencias e inspección manual. La Tabla 13 relaciona cada categoría con los hallazgos y controles de PetConnect.

**Tabla 13**

*Verificación de seguridad frente al OWASP Top 10:2025*

| Categoría OWASP Top 10:2025 | Aplicación en PetConnect | Hallazgo o caso | Técnica |
|---|---|---|---|
| A01 Control de acceso roto | Manipulación del identificador en la URL del carné y de las mascotas (RS02) | NC-002; CP-012 | Pruebas negativas, ZAP |
| A02 Configuración de seguridad incorrecta | `debug=True`, secreto JWT por defecto, CORS y cabeceras de seguridad; modo SQL no estricto de MariaDB, que guarda vacíos los valores inválidos | NC-007, NC-009 | ZAP baseline, revisión de configuración |
| A03 Fallas en la cadena de suministro de software | `requirements.txt` no fija versiones de `PyJWT`, `cryptography`, `mailtrap`, `python-dotenv` y `dnspython`; la actualización no controlada de PyJWT ya rompió la validación de tokens | NC-008 | pip-audit, npm audit, fijación de versiones |
| A04 Fallas criptográficas | SHA-256 sin sal (RS03); API servida por HTTP; token guardado en AsyncStorage sin cifrar | NC-001; CP-004 | Inspección; migrar el token a `expo-secure-store` |
| A05 Inyección | Las consultas actuales usan parámetros (`%s`), lo cual es conforme; riesgo de XSS almacenado en la comunidad | CP-014 | Cargas maliciosas, escaneo activo de ZAP |
| A06 Diseño inseguro | Abuso del flujo de adopción (publicaciones falsas o masivas) | CP-016 | Modelado de amenazas en el Sprint Planning |
| A07 Fallas de autenticación | OTP sin límite de intentos; sin limitación de tasa en el inicio de sesión; enumeración de correos (respuesta 409 en el registro) | NC-006; CP-002, CP-005 | Fuerza bruta controlada |
| A08 Fallas de integridad de software o datos | Token JWT con firma alterada o algoritmo `none`; firma del APK | CP-006 | Pruebas de manipulación del token |
| A09 Fallas de registro y alertas de seguridad | Los errores se imprimen en consola y no existe registro de auditoría de accesos denegados | CP-012 (paso 7) | Inspección de registros |
| A10 Manejo incorrecto de condiciones excepcionales | El manejador global devuelve `str(e)` al cliente y convierte en HTTP 500 hasta las rutas inexistentes (404); `decrypt()` devuelve el valor original si el descifrado falla | NC-007 | Inyección de fallas (base de datos caída, token corrupto) |

**Compatibilidad, accesibilidad y SEO.** La matriz de compatibilidad (RNF05) cubre dos teléfonos Android físicos (uno de gama media con Android 10 y otro con Android 14), un iPhone con iOS 15 o superior (o el simulador de iOS en macOS) y las dos últimas versiones de Chrome, Edge y Firefox. Lighthouse se ejecuta sobre la versión de producción del módulo web (`npm run build` y `npm run preview`) en modo móvil emulado, con metas de Rendimiento ≥ 80 y de Accesibilidad, Buenas prácticas y SEO ≥ 90. Como Lighthouse no audita aplicaciones nativas, el APK se evalúa con Accessibility Scanner de Android y con el lector de pantalla TalkBack.

**Disponibilidad y respaldos.** La disponibilidad (RNF01) se mide con Amazon CloudWatch durante todo el Sprint 3. Para RNF07 se verifica que exista un respaldo automático diario y, una vez por sprint, se restaura el último respaldo en una base de datos limpia y se comparan los conteos de usuarios, mascotas y vacunas con el origen.

#### Criterios de Entrada, Salida, Suspensión y Reanudación

**Tabla 14**

*Criterios de control del proceso de pruebas*

| Tipo | Criterios |
|---|---|
| Entrada | (a) Historias de usuario con criterios de aceptación aprobados (Definition of Ready); (b) código integrado en la rama de desarrollo con build exitoso; (c) entorno desplegado con datos semilla sintéticos; (d) casos de prueba revisados por pares; (e) prueba de humo aprobada. Para las pruebas no funcionales, además: (f) staging en AWS con Docker y Gunicorn, sin el servidor de desarrollo de Flask y con `debug` desactivado; (g) HTTPS activo; (h) NC-001 corregida antes de la ronda final de seguridad |
| Salida | (a) 100 % de los casos de prioridad alta ejecutados; (b) ≥ 95 % del total de casos aprobados; (c) cero no conformidades críticas o altas abiertas; (d) cobertura ≥ 80 % en dominio y 100 % en seguridad; (e) RNF04, RR01 y RR02 cumplidos; (f) SUS ≥ 68; (g) umbrales de Lighthouse cumplidos; (h) ZAP sin alertas de riesgo alto; (i) restauración de respaldo verificada; (j) informe de finalización aprobado en la Sprint Review |
| Suspensión | (a) Falla de la prueba de humo o de más del 40 % de sus casos; (b) entorno caído por más de 4 horas; (c) defecto bloqueante que impide ejecutar ≥ 30 % de los casos; (d) build roto por más de un día hábil; (e) detección de datos personales reales en el entorno de pruebas; (f) cambio sustancial de requisitos a mitad del sprint |
| Reanudación | (a) Causa corregida y verificada con una prueba de confirmación; (b) prueba de humo aprobada al 100 %; (c) entorno restaurado y datos reiniciados; (d) autorización del líder de pruebas; (e) reejecución completa de los casos afectados |

### Entornos, Herramientas y Metodología

#### Entornos de Hardware y Software

Se definen tres entornos para separar el trabajo diario de la validación final. El entorno local lo usa cada integrante mientras desarrolla; el entorno virtualizado reproduce el servidor con contenedores Docker para que todos prueben con las mismas versiones; y el staging en la nube se usa para las pruebas de extremo a extremo y no funcionales.

**Tabla 15**

*Entornos de prueba*

| Entorno | Propósito | Hardware | Software y configuración | Datos |
|---|---|---|---|---|
| Local (desarrollo) | Pruebas unitarias, TDD y exploratorias | Computador con Windows 11, procesador Core i5 o Ryzen 5, 8 GB de RAM (16 GB recomendados para el emulador) y disco SSD; dos teléfonos Android (10 y 14) y un iPhone con iOS 15 o superior | Python 3.14 con entorno virtual, Flask 3.1.3, MariaDB 10.4.32 (XAMPP) en el puerto 3310, Node.js LTS, Expo SDK 57, emulador de Android Studio (host `10.0.2.2`), Visual Studio Code, Postman | Datos sintéticos; correos con dominio `@petconnect.test` |
| Docker virtualizado (integración continua) | Pruebas de integración, regresión y humo automatizadas | Runner de GitHub Actions (`ubuntu-latest`) y Docker Desktop local | `docker compose` con los servicios `api` (`python:3.14-slim` y Gunicorn) y `db` (`mysql:8.0` en modo SQL estricto, igual que el staging, con el script del esquema); variables en `.env.test`; `EMAIL_MODE=smtp` | Base de datos efímera recreada en cada ejecución |
| Staging en AWS | Pruebas E2E, de desempeño, de seguridad y de aceptación | Propuesta de referencia: Amazon EC2 t3.medium (2 vCPU, 4 GB) para la API detrás de un Application Load Balancer con certificado de AWS Certificate Manager; Amazon RDS for MySQL 8.0 con respaldo diario; instancia EC2 separada para JMeter | Imagen Docker versionada desde la integración continua; HTTPS obligatorio; monitoreo con Amazon CloudWatch | Volumen sintético: 10 000 usuarios, 25 000 mascotas y 60 000 registros de vacunación |

*Nota.* El script `seed.py` carga categorías, productos y mascotas de ejemplo sin propietario; en el Sprint 1 se amplía con usuarios, mascotas con propietario y vacunas sintéticos. No se usan datos personales reales, en cumplimiento de la Ley 1581 de 2012 (Congreso de la República de Colombia, 2012). El motor local (MariaDB 10.4, en modo no estricto) difiere del objetivo (MySQL 8 en modo estricto), por lo que la regresión se ejecuta en ambos hasta que el equipo migre el entorno local a MySQL 8 o a una versión de MariaDB con soporte. Las pruebas que escriben datos usan una base aislada (`petconnect_qa`) que se crea y se elimina en cada ejecución.

**Tabla 16**

*Herramientas de prueba*

| Herramienta | Nivel | Propósito |
|---|---|---|
| Jest, `jest-expo` y React Native Testing Library | Unitario | Lógica de dominio y componentes del módulo móvil |
| Jest o Vitest con Testing Library | Unitario | Componentes y utilidades del módulo web |
| pytest y pytest-cov | Unitario e integración | Lógica de la API en Python y medición de cobertura |
| Cliente de pruebas de Flask | Integración | Solicitudes HTTP contra la API sin servidor (rol de Supertest) |
| Postman y Newman | Integración y regresión | Colecciones existentes en `PetConnect.Mobile/postman` y `petconnect.Backend/postman`, ejecutadas en la integración continua |
| Maestro | E2E | Flujos del APK y de la app de iOS en emulador, simulador y dispositivo físico |
| Cypress | E2E | Flujos del módulo web |
| Apache JMeter 5.6 | No funcional | Carga, estrés y capacidad |
| OWASP ZAP | Seguridad | Análisis dinámico (baseline y escaneo activo) |
| pip-audit y npm audit | Seguridad | Vulnerabilidades conocidas en dependencias |
| SonarLint y SonarQube | Análisis estático | Código duplicado, errores y problemas de seguridad |
| Lighthouse | No funcional | Rendimiento, accesibilidad, buenas prácticas y SEO del módulo web |
| Accessibility Scanner y TalkBack | No funcional | Accesibilidad del APK |
| Formulario SUS | No funcional | Medición de la usabilidad percibida |
| Docker y docker-compose | Entorno | Entornos idénticos para todo el equipo |
| GitHub Actions y GitHub Projects | Gestión | Integración continua y tablero de defectos y no conformidades |

#### Ciclo TDD Integrado con Scrum

El equipo trabaja con Scrum, por lo que las pruebas forman parte de cada sprint y no se dejan para el final (Schwaber y Sutherland, 2020). En el Sprint Planning, cada criterio de aceptación de una historia de usuario nueva se traduce en al menos una prueba que falla y se estiman también las tareas de prueba; en el Daily Scrum se informan los bloqueos causados por no conformidades; en la Sprint Review se presentan los resultados de las pruebas; y en la retrospectiva se analizan los defectos más frecuentes. La Definition of Done exige pruebas en verde, cobertura dentro del umbral y revisión de código por un par. Dentro del sprint, cada incremento sigue el ciclo de Beck (2002): rojo (escribir una prueba que falla), verde (escribir el código mínimo para aprobarla) y refactorizar (mejorar el diseño sin cambiar el comportamiento, con las pruebas como red de seguridad).

El ejemplo corresponde al recordatorio de vacunación de RF03 (hallazgo H-04): el sistema debe generar un aviso tres días antes de la próxima dosis. El método `generarRecordatorio()` de la clase `Vacunacion` se ubica en la capa de dominio del módulo móvil, porque alimenta las notificaciones locales del dispositivo. La próxima dosis se calcula a partir de la fecha de aplicación y de la periodicidad de la vacuna. Las fechas se manejan como cadenas `AAAA-MM-DD` interpretadas en UTC: si se usara la hora local del dispositivo (UTC−5 en Colombia), el cálculo podría correrse un día, un defecto clásico que las pruebas de valores límite detectan.

**Figura 1**

*Fase roja: prueba unitaria escrita antes del código*

```javascript
// PetConnect.Mobile/src/domain/__tests__/Vacunacion.test.js
import { Vacunacion } from "../Vacunacion";

const antirrabica = {
  idMascota: 15,
  nombreVacuna: "Antirrábica",
  fechaAplicacion: "2025-11-03",
  periodicidadDias: 365,
};

describe("Vacunacion.generarRecordatorio()", () => {
  test("calcula la próxima dosis y el aviso tres días antes", () => {
    const r = new Vacunacion(antirrabica).generarRecordatorio("2026-10-20");
    expect(r.fechaProximaDosis).toBe("2026-11-03");
    expect(r.fechaAviso).toBe("2026-10-31");
    expect(r.estado).toBe("PROGRAMADO");
  });

  // Análisis de valores límite alrededor de la ventana de aviso
  test.each([
    ["2026-10-30", "PROGRAMADO"],   // un día antes del aviso
    ["2026-10-31", "AVISO_ACTIVO"], // primer día de la ventana
    ["2026-11-03", "AVISO_ACTIVO"], // día de la dosis
    ["2026-11-04", "VENCIDA"],      // un día después de la dosis
  ])("el %s el estado es %s", (hoy, esperado) => {
    const r = new Vacunacion(antirrabica).generarRecordatorio(hoy);
    expect(r.estado).toBe(esperado);
  });

  test("rechaza una periodicidad no positiva (valor límite 0)", () => {
    const datos = { ...antirrabica, periodicidadDias: 0 };
    expect(() => new Vacunacion(datos).generarRecordatorio("2026-10-20"))
      .toThrow(RangeError);
  });
});
```

*Nota.* Al ejecutar `npx jest src/domain`, la suite falla con el mensaje "Cannot find module '../Vacunacion'", porque la clase aún no existe. Ese fallo es el resultado esperado de la fase roja.

**Figura 2**

*Fase verde: implementación mínima que aprueba las pruebas*

```javascript
// PetConnect.Mobile/src/domain/Vacunacion.js (versión mínima)
export class Vacunacion {
  constructor(datos) {
    Object.assign(this, datos);
  }

  generarRecordatorio(hoy) {
    if (!(this.periodicidadDias > 0)) throw new RangeError("periodicidad inválida");
    const dia = 24 * 60 * 60 * 1000;
    const aplicacion = Date.parse(this.fechaAplicacion);
    const proxima = new Date(aplicacion + this.periodicidadDias * dia);
    const aviso = new Date(proxima.getTime() - 3 * dia);
    const actual = new Date(Date.parse(hoy));
    let estado = "PROGRAMADO";
    if (actual > proxima) estado = "VENCIDA";
    else if (actual >= aviso) estado = "AVISO_ACTIVO";
    return {
      fechaProximaDosis: proxima.toISOString().slice(0, 10),
      fechaAviso: aviso.toISOString().slice(0, 10),
      estado,
    };
  }
}
```

*Nota.* Las seis pruebas pasan a verde. El código funciona, pero mezcla validación, aritmética de fechas y reglas de negocio en un solo método y usa valores sin nombre (3, `"VENCIDA"`).

**Figura 3**

*Fase de refactorización: diseño mejorado con las pruebas en verde*

```javascript
// PetConnect.Mobile/src/domain/Vacunacion.js (versión refactorizada)
const MS_POR_DIA = 24 * 60 * 60 * 1000;
export const DIAS_ANTICIPACION_AVISO = 3;

export const EstadoRecordatorio = Object.freeze({
  PROGRAMADO: "PROGRAMADO",
  AVISO_ACTIVO: "AVISO_ACTIVO",
  VENCIDA: "VENCIDA",
});

// Fechas "AAAA-MM-DD" en UTC para evitar corrimientos por la zona horaria
const aFecha = (iso) => new Date(`${iso}T00:00:00Z`);
const aIso = (fecha) => fecha.toISOString().slice(0, 10);
const sumarDias = (fecha, dias) => new Date(fecha.getTime() + dias * MS_POR_DIA);

export class Vacunacion {
  constructor({ idMascota, nombreVacuna, fechaAplicacion, periodicidadDias }) {
    if (!Number.isInteger(periodicidadDias) || periodicidadDias <= 0) {
      throw new RangeError("La periodicidad debe ser un entero positivo de días");
    }
    this.idMascota = idMascota;
    this.nombreVacuna = nombreVacuna;
    this.fechaAplicacion = fechaAplicacion;
    this.periodicidadDias = periodicidadDias;
  }

  calcularProximaDosis() {
    return sumarDias(aFecha(this.fechaAplicacion), this.periodicidadDias);
  }

  generarRecordatorio(hoyIso) {
    const proxima = this.calcularProximaDosis();
    const aviso = sumarDias(proxima, -DIAS_ANTICIPACION_AVISO);
    const hoy = aFecha(hoyIso);

    let estado = EstadoRecordatorio.PROGRAMADO;
    if (hoy > proxima) estado = EstadoRecordatorio.VENCIDA;
    else if (hoy >= aviso) estado = EstadoRecordatorio.AVISO_ACTIVO;

    return {
      idMascota: this.idMascota,
      vacuna: this.nombreVacuna,
      fechaProximaDosis: aIso(proxima),
      fechaAviso: aIso(aviso),
      estado,
    };
  }
}
```

*Nota.* La validación pasa al constructor (un objeto inválido no llega a existir), las constantes reciben nombre y la aritmética de fechas se aísla en funciones puras reutilizables. Las seis pruebas siguen en verde, lo que demuestra que la refactorización no alteró el comportamiento. Si el Product Owner fija otra anticipación, solo cambia `DIAS_ANTICIPACION_AVISO` y los valores esperados de las pruebas.

En el nivel de integración, el mismo enfoque se aplica a la API en Flask. La Figura 4 muestra la prueba automatizada de CP-012, que cumple el papel que tendría Supertest en un servidor Express.

**Figura 4**

*Prueba de integración de CP-012 con pytest y el cliente de pruebas de Flask*

```python
# petconnect.Backend/tests/integracion/test_cp012_carne_acceso.py
import pytest
from api import app
from security.jwt_helper import generate_token

@pytest.fixture
def cliente():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c

@pytest.fixture
def token_usuario_b():
    # El usuario B (id 2) no tiene relación con la mascota 15
    return generate_token(2, "usuario.b@petconnect.test")

def test_cp012_no_expone_carne_de_mascota_ajena(cliente, token_usuario_b):
    resp = cliente.get("/api/mascotas/15/vacunas",
                       headers={"Authorization": f"Bearer {token_usuario_b}"})
    assert resp.status_code in (403, 404)
    assert "vacunas" not in (resp.get_json() or {})

def test_cp012_exige_token(cliente):
    resp = cliente.get("/api/mascotas/15/vacunas")
    assert resp.status_code == 401
```

*Nota.* Se ejecuta con `pytest -q` dentro de `petconnect.Backend`, con las variables de `.env.test` (`JWT_SECRET`, `FERNET_KEY` y la conexión a la base de datos del contenedor) cargadas en el entorno antes de importar la aplicación. Mientras NC-008 siga abierta, el primer caso falla con HTTP 401 en lugar de 403 o 404, porque el token de prueba se rechaza: la prueba detecta el defecto.

#### Procedimiento de Ejecución

Cada ciclo de pruebas sigue estos pasos: (a) se seleccionan las historias del sprint y se diseñan o actualizan sus casos de prueba; (b) se preparan el entorno y los datos de prueba; (c) se ejecuta la prueba de humo; (d) se ejecutan los casos y se registran los resultados en el formato de la Tabla 21; (e) cada falla se documenta en la bitácora de no conformidades; (f) el desarrollador corrige y el analista vuelve a probar el caso fallido (prueba de confirmación); (g) se ejecuta la regresión automatizada; y (h) se actualizan las métricas y se reporta el estado en la Sprint Review.

#### Cronograma por Sprint

Los sprints duran dos semanas. El cronograma descuenta los festivos nacionales del 12 de octubre, el 2 de noviembre y el 16 de noviembre de 2026.

**Tabla 17**

*Cronograma de actividades de prueba por sprint*

| Sprint | Fechas | Objetivo de prueba | Actividades principales | Entregables |
|---|---|---|---|---|
| Sprint 1 | 5 al 16 de octubre de 2026 (festivo: 12 de octubre) | Pruebas estáticas y base de regresión | Aprobación del plan; aclaración de H-01 a H-05 con el Product Owner; matriz de trazabilidad; corrección y prueba de confirmación de NC-001, NC-004, NC-005, NC-008, NC-009 y NC-011; `docker compose` e integración continua; humo y regresión de registro, mascotas, exploración y directorio; TDD de `Vacunacion` (CP-010 y CP-011) | Plan aprobado, ERS actualizada, matriz v1, suite de regresión automatizada, informe de humo |
| Sprint 2 | 19 al 30 de octubre de 2026 | Funcionalidades nuevas de salud y comunidad | TDD e integración del carné, el diario y la comunidad; CP-012 sobre el endpoint nuevo y prueba de confirmación de NC-002; corrección de NC-006, NC-007 y NC-010; ZAP baseline; primera medición con Lighthouse | Incremento probado, reporte de cobertura, reporte ZAP v1 |
| Sprint 3 | 3 al 13 de noviembre de 2026 (festivo: 2 de noviembre) | Adopciones, E2E y no funcionales | TDD de adopciones; E2E con Maestro y Cypress; provisión del staging en AWS; JMeter con 500 y 1000 usuarios y estrés hasta 1500 (CP-017; prueba de confirmación de NC-003); sesiones SUS (CP-018); compatibilidad (CP-019); restauración de respaldo; regresión completa | Reportes de JMeter, SUS, Lighthouse y compatibilidad; reporte ZAP v2 |
| Cierre | 17 al 20 de noviembre de 2026 (festivo: 16 de noviembre) | Decisión de liberación | Prueba de confirmación final de las no conformidades; informe de finalización según ISO/IEC/IEEE 29119-3; retrospectiva; decisión de liberación en la Sprint Review | Informe de finalización, acta de liberación |

#### Roles y Responsabilidades

**Tabla 18**

*Roles y responsabilidades del equipo de pruebas*

| Integrante | Rol | Responsabilidades principales |
|---|---|---|
| Daniel Santiago Jiménez Guzmán | Líder de pruebas y Scrum Master | Coordina el plan, facilita las ceremonias, prioriza por riesgo, controla el cronograma, aprueba la suspensión y la reanudación, consolida las métricas y elabora el informe de finalización; ejecuta las pruebas E2E del módulo web |
| Jazmín Andrea Bautista Oyuela | Analista de requerimientos | Revisión estática y actualización de la ERS, criterios de aceptación, matriz de trazabilidad, diseño de casos a partir de las historias de usuario y cumplimiento de la Ley 1581 |
| Camilo Esteban Orjuela Bonilla | Probador del servidor y la API | Pruebas unitarias con TDD e integración de la API en Flask, colecciones de Newman y corrección de NC-001, NC-002, NC-003, NC-006 a NC-011 |
| Yuli Andrea Silva Segura | Probadora de la aplicación | Pruebas unitarias del dominio móvil, E2E con Maestro, compatibilidad en móviles y navegadores y accesibilidad del APK |
| Valentina Lobo Mccausland | Probadora no funcional | Desempeño y estrés con JMeter, usabilidad con SUS, Lighthouse, escaneos con OWASP ZAP y prueba de respaldos |

**Tabla 19**

*Matriz RACI de las actividades de prueba*

| Actividad | Daniel | Jazmín | Camilo | Yuli | Valentina |
|---|---|---|---|---|---|
| Plan y estrategia de pruebas | A/R | C | C | C | C |
| Revisión de la ERS y trazabilidad | A | R | C | C | I |
| Pruebas unitarias e integración de la API | A | I | R | I | I |
| Pruebas unitarias y E2E móviles | A | I | C | R | I |
| Pruebas E2E web | A/R | I | C | C | I |
| Pruebas no funcionales y de seguridad | A | I | C | C | R |
| Gestión de no conformidades | A/R | C | R | R | R |
| Informe de finalización y liberación | A/R | C | C | C | C |

*Nota.* R = responsable de ejecutar; A = aprueba y rinde cuentas; C = consultado; I = informado.

### Artefactos de Registro e Instrumentos de QA

#### Matriz de Trazabilidad

La matriz relaciona cada requerimiento con sus historias de usuario y sus casos de prueba. Permite comprobar que ningún requerimiento quede sin probar y conocer qué requerimiento se ve afectado cuando un caso falla.

**Tabla 20**

*Matriz de trazabilidad entre requerimientos, historias de usuario y casos de prueba*

| Requerimientos | Historia de usuario | Clase o módulo | Criterio de aceptación clave | Casos de prueba | Sprint |
|---|---|---|---|---|---|
| RF01, RIU01, RNF06 | Nuevo usuario del sistema | `Usuario` | El usuario se crea solo con datos válidos y autorización expresa de tratamiento de datos | CP-001, CP-002 | 1 |
| RS03, RNF03 | Nuevo usuario del sistema | `Usuario` | Contraseña con la política de RS03, almacenada con bcrypt | CP-003, CP-004 | 1 |
| RS01 | Nuevo usuario del sistema | Autenticación (JWT) | Las rutas privadas exigen un token válido emitido tras el segundo factor | CP-005, CP-006 | 1 |
| RF02, RF04, RF05, RIU02, RIU03 | Registro mascota | `Mascota` | Cada mascota queda asociada a su propietario; el menú muestra todas las opciones | CP-007, CP-008, CP-009 | 1 |
| RF03, RS02 | Registro mascota | `Vacunacion` | Solo el dueño consulta el carné; el aviso se genera tres días antes de la dosis | CP-010, CP-011, CP-012 | 1–2 |
| RF06 | Servicios veterinarios | `Servicios` | La búsqueda por palabra clave y tipo devuelve solo coincidencias | CP-013 | 1 |
| RF07, RF08 | Apoyo e interacción | Comunidad y Diario | Publicaciones saneadas; entradas del diario fechadas y privadas | CP-014, CP-015 | 2 |
| RF09 | Adopción | `PublicacionAdopcion` | Solo se permiten las transiciones de la Tabla 11 | CP-016 | 3 |
| RNF04, RR01, RR02 | Todas | Sistema completo | p95 ≤ 2 s con 500 usuarios y ≤ 5 s con 1000 | CP-017 | 3 |
| RNF02 | Todas | Sistema completo | SUS ≥ 68 | CP-018 | 3 |
| RNF05 | Todas | Sistema completo | Sin fallos bloqueantes en la matriz de compatibilidad | CP-019 | 3 |

*Nota.* RNF01, RNF07, RM01 y RM02 se verifican mediante monitoreo, prueba de respaldo y restauración, regresión automatizada y revisión de arquitectura, sin un caso de prueba funcional asociado.

#### Formato de Caso de Prueba Diligenciado: CP-012

El formato sigue los campos de especificación de casos de prueba de ISO/IEC/IEEE 29119-3 (ISO, 2021). Como el carné de vacunación todavía no existe, la primera ejecución se hizo de forma temprana sobre el endpoint de mascotas que el carné va a reutilizar.

**Tabla 21**

*Especificación del caso de prueba CP-012*

| Campo | Contenido |
|---|---|
| Identificador | CP-012 |
| Nombre | Control de acceso al carné de vacunación |
| Requerimientos | RS02, RF03, RNF06 |
| Historia de usuario | Registro mascota |
| Característica ISO/IEC 25010 | Seguridad: confidencialidad y autenticidad |
| Riesgo y categoría OWASP | R02 (nivel 20, crítico); A01:2025 Control de acceso roto |
| Nivel y tipo | Integración (API) y E2E (móvil); caja gris; prueba negativa |
| Técnica de diseño | Partición de equivalencia sobre el actor: dueño, otro usuario autenticado, usuario anónimo, token expirado y token con firma alterada |
| Prioridad | Alta |
| Precondiciones | 1. Entorno Docker con datos semilla sintéticos. 2. Usuario A (id 1), dueño de la mascota 15, con dos vacunas registradas. 3. Usuario B (id 2), sin relación con esa mascota. 4. API con `debug` desactivado. |
| Datos de prueba | `usuario.a@petconnect.test` y `usuario.b@petconnect.test`; mascota 15; token con `exp` en el pasado; token con la firma alterada |
| Postcondiciones | Ningún dato se modifica; las sesiones se cierran |
| Responsables | Camilo Orjuela (pasos 1 a 5 y 7) y Yuli Silva (paso 6) |
| Evidencias | Reporte de pytest, ejecución de Newman, video de Maestro y extracto del registro de auditoría |

**Tabla 22**

*Pasos, resultados esperados y ejecuciones de CP-012*

| Paso | Acción | Resultado esperado |
|---|---|---|
| 1 | Iniciar sesión como usuario B (credenciales y OTP) | HTTP 200 con un token JWT válido |
| 2 | `GET /api/mascotas/15/vacunas` con el token de B | HTTP 403 o 404; el cuerpo no contiene datos del carné |
| 3 | `GET /api/mascotas/15/vacunas` sin cabecera `Authorization` | HTTP 401 |
| 4 | Repetir el paso 2 con el token expirado y con el token de firma alterada | HTTP 401 en ambos casos |
| 5 | `GET /api/mascotas/15/vacunas` con el token del usuario A, dueño de la mascota | HTTP 200; solo se listan las vacunas de la mascota 15 |
| 6 | En la app, como usuario B, abrir un enlace profundo al carné de la mascota 15 | Mensaje "No tienes acceso a este carné"; ningún dato visible |
| 7 | Revisar el registro de auditoría | El intento denegado queda registrado con fecha, usuario y recurso, sin datos sensibles |
| **Ejecución 1** | Prueba temprana por inspección de código, 2 de octubre de 2026. Objeto: `GET /api/mascotas/{id}` (`api.py`, líneas 232–243), patrón que el carné va a reutilizar | **Resultado obtenido:** el endpoint no aplica `@require_auth`, no verifica el dueño y la consulta no filtra por estado; un usuario anónimo que cambia el identificador en la URL obtiene cualquier mascota registrada, aunque no esté en adopción. **Estado: Fallido. Defecto: NC-002** |
| **Ejecución 1b** | Prueba dinámica, 5 de octubre de 2026 (AA2, CP-006), sobre el mismo endpoint en la base aislada `petconnect_qa` | **Resultado obtenido:** HTTP 200 sin token y con el token de un usuario que no es el dueño, con todos los datos de la mascota, incluidas sus observaciones de salud. **Estado: Fallido. Defecto: NC-002 confirmada** |
| **Ejecución 2** | Programada en el Sprint 2 (26 al 30 de octubre de 2026) sobre el endpoint nuevo `/api/mascotas/{id}/vacunas` | Pendiente; se ejecuta después de corregir NC-002 |

#### Resumen de la Suite de Casos de Prueba

**Tabla 23**

*Suite de casos de prueba CP-001 a CP-019*

| ID | Descripción | Requerimientos | Nivel | Tipo | Prioridad | Sprint | Estado al 5 de octubre de 2026 |
|---|---|---|---|---|---|---|---|
| CP-001 | Registro de usuario con datos válidos, verificación por OTP y autorización de datos | RF01, RIU01, RNF06 | Integración, E2E | Positiva | Alta | 1 | Fallido por inspección (NC-005); el registro con OTP se aprobó el 5/10 (AA2, CP-001) |
| CP-002 | Registro rechazado por correo ya existente, sin revelar qué correos están registrados | RF01 | Integración | Negativa | Alta | 1 | En seguimiento: el 5/10 rechazó el duplicado con HTTP 409, pero el mensaje revela que el correo existe (A07; AA2, CP-002) |
| CP-003 | Contraseña de 7, 8, 9, 64 y 65 caracteres y composición exigida (valores límite) | RS03, RIU01 | Unitario | Negativa | Alta | 1 | Fallido; confirmado el 5/10 (NC-004; AA2, CP-002) |
| CP-004 | Contraseña almacenada con bcrypt costo 12, nunca en texto plano, con migración de resúmenes SHA-256 | RS03, RNF03 | Unitario | Positiva | Alta | 1 | Fallido; confirmado el 5/10 (NC-001; AA2, CP-007) |
| CP-005 | Inicio de sesión en dos pasos que devuelve un JWT con expiración, aceptado por un endpoint protegido; bloqueo tras 5 OTP incorrectos | RS01 | Integración | Positiva y negativa | Alta | 1 | Fallido en prueba temprana (NC-008, NC-006) |
| CP-006 | Acceso a rutas privadas sin token, con token expirado o con firma alterada devuelve 401 | RS01 | Integración | Negativa | Alta | 1 | Diseñado |
| CP-007 | Registro de mascota con nombre, especie, raza, edad y foto desde el menú principal | RF02, RF05, RIU02, RIU03 | E2E | Positiva | Alta | 1 | Diseñado |
| CP-008 | Registro de mascota con campos obligatorios vacíos o edad inválida | RF02, RIU02 | Unitario | Negativa | Media | 1 | Diseñado |
| CP-009 | Registro de una segunda mascota con el mismo usuario | RF04 | Integración | Positiva | Alta | 1 | Aprobado el 5/10 en el módulo stand-alone (AA2, CP-003) |
| CP-010 | Agregar una vacuna al carné con datos válidos | RF03 | Unitario, integración | Positiva | Alta | 2 | En seguimiento: el 5/10 la BD guardó el carné, pero aceptó fechas inconsistentes (NC-010; AA2, CP-004) |
| CP-011 | Generación del recordatorio tres días antes de la próxima dosis (TDD) | RF03 | Unitario | Positiva y límites | Alta | 1–2 | Aprobado el 5/10: 6 de 6 pruebas (AA2, CP-010) |
| CP-012 | Otro usuario no puede ver el carné de una mascota ajena | RS02, RF03 | Integración, E2E | Negativa | Alta | 2 | Fallido; confirmado dinámicamente el 5/10 (NC-002; AA2, CP-006) |
| CP-013 | Búsqueda de servicios por palabra clave y filtro por tipo | RF06 | Integración | Positiva | Media | 1 | En seguimiento: el 5/10 la búsqueda por nombre devolvió proveedores inactivos (NC-011; AA2, CP-005) |
| CP-014 | Crear y responder una publicación en la comunidad, con carga XSS saneada | RF07 | E2E, seguridad | Positiva y negativa | Media | 2 | Diseñado |
| CP-015 | Registrar una entrada en el diario de salud, visible solo para el dueño | RF08, RS01 | Integración | Positiva | Media | 2 | Diseñado |
| CP-016 | Publicar una mascota en adopción y recorrer sus transiciones de estado | RF09 | E2E | Positiva y negativa | Alta | 3 | Fallido el 5/10: el catálogo de adopción está vacío (NC-009; AA2, CP-012) |
| CP-017 | Tiempo de respuesta con 500 y 1000 usuarios y estrés hasta 1500 | RNF04, RR01, RR02 | No funcional | Desempeño | Alta | 3 | Fallido el 5/10 con 500 usuarios en el entorno local: p95 de 30 s y 56 % de errores (NC-003; AA2, CP-008) |
| CP-018 | Prueba de usabilidad SUS con ocho participantes | RNF02 | No funcional | Usabilidad | Media | 3 | Diseñado |
| CP-019 | Compatibilidad en Android, iOS y navegadores | RNF05 | No funcional | Compatibilidad | Media | 3 | Diseñado |

*Nota.* Los estados del 5 de octubre provienen de la ejecución de la evidencia GA9-220501096-AA2-EV01, cuyos casos tienen numeración propia (se indica como "AA2, CP-0XX"). Esa ejecución se hizo sobre la API, los DAO y la base de datos en el entorno local; las ejecuciones en Docker, staging e interfaz siguen el cronograma de la Tabla 17.

#### Bitácora de No Conformidades

Cuando el resultado de una revisión o de un caso difiere del esperado, se registra una no conformidad (NC). La severidad indica el impacto técnico: crítica cuando bloquea el sistema o expone datos, alta cuando impide usar una funcionalidad principal o compromete la seguridad, media cuando existe una alternativa de uso y baja cuando es estética. El estado sigue el ciclo abierta, en corrección, en verificación y cerrada.

**Tabla 24**

*Bitácora de no conformidades*

| ID | Detección | Descripción y evidencia | Severidad | Requisito / OWASP | Acción correctiva | Responsable | Estado |
|---|---|---|---|---|---|---|---|
| NC-001 | 2/10/2026, revisión estática de la ERS y del código | Algoritmo de hashing: RS03 indica SHA-256 y el código lo implementa sin sal (`api.py`, líneas 66–67; `vista/menu_usuarios.py`, línea 67). `bcrypt` no figura en `requirements.txt` | Crítica | RS03, RNF03 / A04:2025 | Reemplazar por bcrypt con costo 12 en la API y en la consola; comparar con `bcrypt.checkpw`; migrar los resúmenes heredados al siguiente inicio de sesión; longitud máxima de 64; corregir la redacción de RS03 | Camilo Orjuela y Jazmín Bautista; confirmación: Daniel Jiménez | Abierta, bloquea la liberación; confirmada el 5/10/2026 (AA2, CP-007) |
| NC-002 | 2/10/2026, CP-012 (ejecución 1) | Elusión de la autorización por manipulación de la URL: `GET /api/mascotas/{id}` no exige autenticación ni verifica dueño ni estado; al cambiar el identificador se obtienen mascotas que no están en adopción, incluidas sus observaciones de salud | Alta (crítica si se replica en el carné) | RS02, RS01 / A01:2025 | Limitar el endpoint público a las mascotas en adopción (con el estado que defina la corrección de NC-009); endpoints privados con `@require_auth` y verificación de que `id_usuario` coincide con el usuario del token; responder 404 para no revelar existencia | Camilo Orjuela | Abierta; confirmada dinámicamente el 5/10/2026 (AA2, CP-006) |
| NC-003 | 2/10/2026, revisión estática de desempeño | Latencia en la búsqueda: los listados no se paginan ni se filtran en el servidor; una única conexión a la base de datos (Singleton en `conexion/conexion_bd.py`) se comparte entre los hilos de Flask; la API usa el servidor de desarrollo. El 5/10/2026, con 500 usuarios, el p95 fue de 30 s y falló el 56 % de las solicitudes ('MySQL Connection not available', 'bytearray index out of range') | Alta | RNF04, RR01, RR02, RM02 | Paginación y filtros parametrizados; índices sobre `mascotas(estado)` y los campos de búsqueda del directorio; pool de conexiones (`mysql.connector.pooling`); despliegue con Gunicorn | Camilo Orjuela; medición: Valentina Lobo | Abierta; confirmada el 5/10/2026 (AA2, CP-008) |
| NC-004 | 2/10/2026, revisión estática | La política de contraseña no verifica la minúscula (`_validate_password` acepta `PETCONNECT1!`) y exige un carácter especial que RS03 no documenta | Media | RS03, RIU01 | Agregar la verificación de minúscula; documentar el carácter especial como control adicional; alinear la validación de los módulos web y móvil | Camilo Orjuela y Yuli Silva | Abierta; confirmada el 5/10/2026 (AA2, CP-002) |
| NC-005 | 2/10/2026, revisión estática | El usuario se crea con `acepta_datos=True` fijo (`api.py`, línea 401) sin que el titular otorgue la autorización en el formulario | Alta | RNF06 / Ley 1581, art. 9 | Casilla no premarcada con enlace a la política de tratamiento; persistir la fecha y la versión aceptada; rechazar el registro sin autorización | Jazmín Bautista, Yuli Silva y Camilo Orjuela | Abierta |
| NC-006 | 2/10/2026, revisión estática | `AlmacenOTP.verificar()` (`otp/servicio.py`) no cuenta intentos fallidos y `/api/auth/login` no limita la tasa de solicitudes: el código de 6 dígitos es atacable por fuerza bruta durante sus 10 minutos de vigencia | Alta | RS01 / A07:2025 | Máximo 5 intentos por código y bloqueo temporal; limitación de tasa por IP y por cuenta; registro de intentos fallidos | Camilo Orjuela | Abierta |
| NC-007 | 2/10/2026, revisión estática | Configuración insegura: `app.run(debug=True)`; el manejador global devuelve `str(e)` al cliente y, como comprobó la ejecución del 5/10/2026, convierte en HTTP 500 hasta las rutas inexistentes (404); `JWT_SECRET` tiene el valor por defecto `"dev-secret-inseguro"`; `decrypt()` devuelve el valor original si el descifrado falla | Alta | RNF03, RS01 / A02:2025, A10:2025 | Desactivar `debug` fuera del entorno local; mensajes genéricos con identificador de correlación; impedir el arranque sin `JWT_SECRET`; registrar y propagar los errores de descifrado | Camilo Orjuela | Abierta |
| NC-008 | 2/10/2026, prueba dinámica temprana (CP-005) | `generate_token()` (`security/jwt_helper.py`) emite el claim `sub` como entero; PyJWT 2.13.0, instalado porque `requirements.txt` no fija versión, exige que `sub` sea texto y `verify_token()` devuelve `None`. Todo endpoint con `@require_auth` (hoy `/api/auth/me`) responde 401 aunque el token se acabe de emitir | Crítica | RS01 / A03:2025 | Emitir `"sub": str(user_id)` y convertirlo a entero en `require_auth`; fijar las versiones de `requirements.txt`; agregar una prueba de ida y vuelta (emitir y validar) a la regresión | Camilo Orjuela | Abierta, bloquea las funcionalidades que requieren autenticación (RS01) |
| NC-009 | 5/10/2026, ejecución (AA2, CP-012) | Catálogo de adopción siempre vacío: `seed.py` y la API usan el estado `'en_adopcion'`, que no existe en el enum de `mascotas.estado`; MariaDB, en modo no estricto, lo guarda vacío (advertencia 1265). Las 6 mascotas de la BD de desarrollo tienen estado vacío, y la web lo oculta mostrando las mascotas fijas de `src/data/pets.js` | Alta | RF09 / A02:2025 | Definir un único modelo de adopción (agregar el estado al enum o usar la tabla `adopciones`), corregir los registros existentes, activar el modo SQL estricto y mostrar un estado vacío en la web en lugar de datos fijos | Camilo Orjuela | Abierta |
| NC-010 | 5/10/2026, ejecución (AA2, CP-004) | El carné acepta una próxima dosis anterior a la fecha de aplicación: `aplicaciones_vacuna` no tiene ninguna validación de fechas | Media | RF03 | Validar las fechas en la capa de servicio del carné y agregar una restricción CHECK en la base de datos | Camilo Orjuela y Yuli Silva | Abierta |
| NC-011 | 5/10/2026, ejecución (AA2, CP-005) | `buscar_por_nombre()` del directorio devuelve proveedores inactivos, a diferencia de `consultar_por_ciudad()` | Baja | RF06 | Agregar `AND activo = TRUE` a la consulta y un caso de regresión | Camilo Orjuela | Abierta |

*Nota.* NC-001 a NC-003 corresponden a los hallazgos previos del equipo, confirmados contra el código. NC-004 a NC-008 son hallazgos nuevos de la revisión técnica. NC-009 a NC-011 surgieron de la primera ejecución de casos, el 5 de octubre de 2026 (evidencia GA9-220501096-AA2-EV01). Todas tienen un caso de regresión asociado para evitar su reaparición.

#### Métricas de Seguimiento

Al final de cada sprint, el líder de pruebas reporta las métricas de la Tabla 25 en la Sprint Review.

**Tabla 25**

*Métricas de seguimiento del proceso de pruebas*

| Métrica | Cálculo | Meta | Frecuencia |
|---|---|---|---|
| Avance de ejecución | Casos ejecutados / casos planificados × 100 | 100 % de los casos de prioridad alta | Por sprint |
| Tasa de aprobación | Casos aprobados / casos ejecutados × 100 | ≥ 95 % | Por sprint |
| No conformidades abiertas por severidad | Conteo por severidad en el tablero | Cero críticas o altas al cierre | Diaria |
| Densidad de defectos por módulo | No conformidades del módulo / casos del módulo | Tendencia decreciente | Por sprint |
| Cobertura de código | Sentencias y ramas cubiertas por las pruebas unitarias | ≥ 80 % en dominio y 100 % en seguridad | En cada ejecución de la integración continua |
| Tiempo medio de corrección | Promedio de días entre la detección y el cierre | ≤ 3 días hábiles para las críticas | Por sprint |
| Detección temprana | No conformidades detectadas antes de la ejecución formal / total | Al 5 de octubre de 2026: 8 de 11 (siete por revisión estática y una por prueba dinámica temprana; NC-009 a NC-011 surgieron en la primera ejecución) | Al cierre |

### Matriz de Riesgos y Contingencias

El nivel de cada riesgo se calcula como Nivel = Probabilidad × Impacto, ambos en una escala de 1 a 5. Los rangos son: 1 a 5, bajo; 6 a 10, medio; 12 a 16, alto; y 20 a 25, crítico. Los riesgos críticos y altos tienen acciones obligatorias dentro del cronograma y se revisan en cada Daily Scrum.

**Tabla 26**

*Matriz de riesgos y contingencias*

| ID | Riesgo | Causa o evidencia | P | I | Nivel | Mitigación preventiva | Contingencia | Responsable |
|---|---|---|---|---|---|---|---|---|
| R01 | Inseguridad de contraseñas | SHA-256 sin sal, tal como indica RS03 (NC-001) | 4 | 5 | 20 – Crítico | bcrypt costo 12 en el Sprint 1; CP-004 en la regresión | Restablecimiento forzado de contraseñas; aviso a los titulares y a la autoridad de protección de datos | Camilo Orjuela |
| R02 | Exposición del carné de vacunación | Patrón de acceso sin autorización por objeto (NC-002) | 4 | 5 | 20 – Crítico | Autorización por dueño desde el diseño; CP-012 automatizado en la integración continua | Desactivar el endpoint del carné y retirar la versión afectada | Camilo Orjuela |
| R03 | Degradación del desempeño bajo carga | Conexión única, sin paginación, servidor de desarrollo (NC-003); materializado el 5/10 con 500 usuarios (56 % de errores) | 5 | 4 | 20 – Crítico | Pool de conexiones, paginación, índices y Gunicorn antes del Sprint 3 | Escalar horizontalmente la API en AWS; limitar temporalmente funciones costosas | Valentina Lobo |
| R04 | Autenticación débil o inutilizable | OTP sin límite de intentos, secreto JWT por defecto y token rechazado (NC-006, NC-007, NC-008) | 3 | 5 | 15 – Alto | Límite de intentos y de tasa; secreto obligatorio; prueba de ida y vuelta del token | Bloqueo de cuentas afectadas y rotación del secreto JWT | Camilo Orjuela |
| R05 | Incumplimiento de la Ley 1581 de 2012 | Autorización no capturada (NC-005) o datos reales en las pruebas | 3 | 5 | 15 – Alto | Casilla de autorización y política publicada en el Sprint 1; solo datos sintéticos | Solicitar la autorización a los usuarios existentes; suspender las pruebas y depurar los datos | Jazmín Bautista |
| R06 | Retraso en la provisión del staging (Docker y AWS) | No existen artefactos de infraestructura en el repositorio; el motor local (MariaDB 10.4) difiere del objetivo (MySQL 8) | 3 | 4 | 12 – Alto | `docker compose` en el Sprint 1 y staging listo al inicio del Sprint 3 | Ejecutar JMeter en el entorno Docker local con carga reducida y extrapolar con cautela | Daniel Jiménez |
| R07 | Dependencia de servicios externos | Correo para el OTP, notificaciones push y mapas | 3 | 3 | 9 – Medio | Modo `smtp` (sandbox) y servicios simulados en las pruebas | Proveedor alterno; código impreso en la consola solo en el entorno local | Camilo Orjuela |
| R08 | Fragmentación de dispositivos y falta de iPhone físico | Diversidad de versiones de Android; compilar para iOS requiere macOS | 3 | 3 | 9 – Medio | Matriz de dispositivos con emulador, simulador y equipos físicos | Préstamo de equipos o servicio de dispositivos en la nube | Yuli Silva |
| R09 | Menor tiempo disponible para las pruebas | Retrasos del desarrollo, carga académica y festivos (12 de octubre, 2 y 16 de noviembre) | 3 | 3 | 9 – Medio | Cronograma con festivos descontados; tablero visible | Repriorizar por riesgo y mover los casos de prioridad baja al siguiente ciclo | Daniel Jiménez |
| R10 | Requerimientos ambiguos o contradictorios | Hallazgos H-01 a H-05 de la ERS | 3 | 3 | 9 – Medio | Aclaración con el Product Owner en el Sprint 1 y control de cambios sobre la ERS | Congelar el alcance del sprint y documentar los supuestos en el plan | Jazmín Bautista |

Los riesgos R01 y R02 son críticos porque combinan una vulnerabilidad ya confirmada en el código con un impacto máximo sobre la confidencialidad. Si se filtrara la base de datos, R01 permitiría recuperar por fuerza bruta la mayoría de las contraseñas, que los usuarios suelen reutilizar en otros servicios; el daño excedería a PetConnect. R02 expondría información de las mascotas vinculada a su dueño con solo cambiar un número en la URL, un ataque que no requiere conocimientos técnicos y que viola directamente RS02. En ambos casos, la Ley 1581 obliga al responsable del tratamiento a garantizar la seguridad de la información y a informar a la autoridad de protección de datos cuando se presenten violaciones a los códigos de seguridad (Congreso de la República de Colombia, 2012, art. 17). Por esa razón, NC-001 y NC-002 son criterios de salida bloqueantes: sin su corrección y su prueba de confirmación aprobada no hay liberación, cualquiera sea el resultado del resto de la suite. R03 pasó de alto a crítico después de la ejecución del 5 de octubre, porque el riesgo dejó de ser una hipótesis: con 500 usuarios falló más de la mitad de las solicitudes. Su corrección (pool de conexiones y Gunicorn) es requisito para la prueba de carga del Sprint 3.

## Conclusiones

La elaboración del plan de pruebas permitió encontrar defectos antes de ejecutar una sola prueba formal. La revisión estática de la ERS reveló un algoritmo inadecuado para las contraseñas (RS03), un tiempo de carga incoherente (RR02), una regla de longitud de contraseña mal planteada en la historia de usuario de RF01, un recordatorio de vacunación que el diseño contempla pero la ERS no especifica, y una tensión entre el menú de RIU03 y el alcance premium. El contraste con el código confirmó NC-001, materializó el riesgo de elusión de autorización de NC-002 en un endpoint existente, anticipó la latencia de NC-003 a partir de su causa técnica y reveló cinco no conformidades nuevas: la política de contraseñas incompleta, la ausencia de autorización conforme a la Ley 1581, el OTP sin límite de intentos, una configuración insegura del servidor y, mediante una prueba dinámica de pocas líneas, un token JWT que la propia API rechaza por una actualización no controlada de dependencias.

La primera ejecución de casos, el 5 de octubre de 2026 (evidencia GA9-220501096-AA2-EV01), llevó el plan a la práctica: de 12 casos, 5 se aprobaron, 3 quedaron en seguimiento y 4 se rechazaron. La ejecución confirmó con pruebas dinámicas NC-001, NC-002, NC-003 y NC-004, y reveló tres no conformidades nuevas: el catálogo de adopción siempre vacío por un estado que no existe en la base de datos (NC-009), el carné sin validación de fechas (NC-010) y la búsqueda del directorio que muestra proveedores inactivos (NC-011).

Validar el plan contra el repositorio también corrigió su base técnica. La API está construida en Flask y no en Express, de modo que las pruebas de integración se apoyan en pytest y en el cliente de pruebas de Flask, mientras que Jest se conserva donde corresponde: en la capa JavaScript de los módulos móvil y web. Del mismo modo, la base de datos local es MariaDB 10.4 en modo no estricto y no MySQL 8, una diferencia que explica NC-009 y que obliga a probar en ambos motores. Un plan de pruebas que describe una arquitectura distinta de la real no puede verificarla.

Priorizar por riesgo hace viable el proceso dentro de tres sprints. El registro, la autenticación y el carné de vacunación concentran la mayor cantidad de casos porque manejan datos personales e información de salud, mientras que el GPS y la tienda virtual se dejan para un plan posterior, en coherencia con el modelo de la versión premium. La combinación de ISO/IEC 25010, la pirámide de Cohn y TDD dentro de Scrum convierte la calidad en una tarea de cada sprint y no en una fase final; el ejemplo de `generarRecordatorio()` muestra cómo el análisis de valores límite convierte un criterio de aceptación en una prueba ejecutable y protege contra defectos sutiles, como el corrimiento de fechas por zona horaria.

La calidad antes de la liberación queda respaldada por criterios objetivos y verificables: cero no conformidades críticas o altas abiertas, cobertura mínima, percentil 95 del tiempo de respuesta dentro de 2 y 5 segundos, puntaje SUS de al menos 68, umbrales de Lighthouse, respaldo restaurable y ausencia de alertas altas en el análisis de seguridad. La matriz de trazabilidad y la bitácora de no conformidades permiten demostrar qué se probó, qué falló y cómo se corrigió, información necesaria para decidir con evidencia si PetConnect está listo para sus usuarios.

## Referencias

Beck, K. (2002). *Test-driven development: By example*. Addison-Wesley.

Brooke, J. (1996). SUS: A "quick and dirty" usability scale. En P. W. Jordan, B. Thomas, B. A. Weerdmeester y I. L. McClelland (Eds.), *Usability evaluation in industry* (pp. 189–194). Taylor & Francis.

Cohn, M. (2009). *Succeeding with agile: Software development using Scrum*. Addison-Wesley.

Congreso de la República de Colombia. (2012, 17 de octubre). *Ley Estatutaria 1581 de 2012, por la cual se dictan disposiciones generales para la protección de datos personales*. Diario Oficial No. 48.587.

International Organization for Standardization. (2021). *Software and systems engineering — Software testing — Part 3: Test documentation* (ISO/IEC/IEEE Standard No. 29119-3:2021). ISO.

International Organization for Standardization. (2023). *Systems and software engineering — Systems and software Quality Requirements and Evaluation (SQuaRE) — Product quality model* (ISO/IEC Standard No. 25010:2023). ISO.

Mera Paz, J. A. (2016). Análisis del proceso de pruebas de calidad de software. *Ingeniería Solidaria, 12*(20), 163–176. https://doi.org/10.16925/in.v12i20.1482

Myers, G. J., Sandler, C. y Badgett, T. (2011). *The art of software testing* (3.ª ed.). John Wiley & Sons.

OWASP Foundation. (s.f.). *Password storage cheat sheet*. OWASP Cheat Sheet Series. https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html

OWASP Foundation. (2025). *OWASP Top 10:2025*. https://owasp.org/Top10/2025/

Sauro, J. (2011). *A practical guide to the System Usability Scale: Background, benchmarks & best practices*. Measuring Usability LLC.

Schwaber, K. y Sutherland, J. (2020). *La guía de Scrum: La guía definitiva de Scrum: Las reglas del juego*. https://scrumguides.org
