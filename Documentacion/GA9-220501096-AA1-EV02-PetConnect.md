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
| Versión | 2.3 – Revisión técnica integral, alineación con la ERS, resultados de la primera ejecución y cierre de NC-001 y NC-008 |
| Versiones anteriores | 1.0 – Borrador del equipo; 2.0 – Revisión técnica contra el código; 2.1 – Alineación con la ERS; 2.2 – Resultados de la primera ejecución (versión entregada) |
| Línea base de requerimientos | Especificación de los requerimientos funcionales y no funcionales del software (ERS) del proyecto: RF01–RF11, RNF01–RNF07, RIU01–RIU03, RS01–RS03, RR01–RR02 y RM01–RM02 |
| Base de código revisada | Repositorio del proyecto (carpeta `Evidecia`), rama `main`, commit `c4310dc` |
| Metodología | Scrum, seleccionada en la evidencia GA1-220501092-AA5-EV02 |
| Fecha de la revisión | 2 de octubre de 2026 (revisión técnica); 5 de octubre de 2026 (actualización con la ejecución); 15 de octubre de 2026 (cierre de NC-001 y NC-008) |
| Primera ejecución de casos | 5 de octubre de 2026: casos CP-001 a CP-012 de la evidencia GA9-220501096-AA2-EV01, con evidencias en `Documentacion/Evidencias-GA9-AA2-EV01` |
| Prueba de confirmación | 15 de octubre de 2026: NC-001 y NC-008 corregidas y confirmadas (4 de 4 verificaciones aprobadas), con evidencias en `Documentacion/Evidencias-Confirmacion-NC-001-NC-008` y pruebas de regresión en `petconnect.Backend/tests` |
| Norma de documentación | ISO/IEC/IEEE 29119-3:2021 |
| Modelo de calidad | ISO/IEC 25010:2023 |
| Aprobación | Líder de pruebas y Scrum Master: Daniel Santiago Jiménez Guzmán |

## Introducción

PetConnect es una aplicación móvil integral para el cuidado de mascotas, dirigida a propietarios, fundaciones de adopción y proveedores de servicios veterinarios. Según su especificación de requerimientos (ERS), el sistema debe permitir el registro de usuarios y de una o varias mascotas, almacenar el carné de vacunación, mostrar un directorio de servicios veterinarios, ofrecer una comunidad de dueños, llevar un diario de salud y comportamiento, y publicar y adoptar mascotas; el GPS en tiempo real y la tienda virtual completan la versión premium. La solución se compone de una aplicación móvil híbrida construida con React Native sobre Expo, un cliente web en React con Vite, una API REST y una base de datos relacional compatible con MySQL (MariaDB 10.4 en el entorno local y MySQL 8 como objetivo del staging); el entorno de staging objetivo es una infraestructura de contenedores Docker sobre Amazon Web Services (AWS).

Este documento es la versión oficial del plan de pruebas. Integra el trabajo del equipo con una revisión técnica que contrastó los requerimientos de la ERS con el código fuente del repositorio. Esa comprobación arrojó dos conclusiones que condicionan todo el plan. La primera es que la API REST está implementada en Python 3 con Flask 3.1 y no en Node.js con Express, como se había asumido en el borrador; por eso el plan adopta la arquitectura verificada y ajusta las herramientas de prueba del servidor, conservando Jest para la capa JavaScript (móvil y web). La segunda es que el código confirma la no conformidad NC-001 (contraseñas almacenadas con SHA-256, tal como lo indica RS03) y presenta otros defectos de seguridad, desempeño y protección de datos, entre ellos uno que deja inutilizables los endpoints protegidos; todos se registran en la bitácora de no conformidades. La revisión del entorno mostró además que el servidor de base de datos local es MariaDB 10.4.32 y no MySQL 8, como indica el README. Por último, la primera ejecución de casos, el 5 de octubre de 2026 (evidencia GA9-220501096-AA2-EV01), confirmó varias de esas no conformidades y agregó tres nuevas (NC-009 a NC-011). El 15 de octubre, dentro del Sprint 1 y atendiendo la retroalimentación del instructor, se corrigieron NC-001 y NC-008, y su prueba de confirmación fue aprobada.

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
| Seguridad | JWT y bcrypt | JWT HS256 con PyJWT 2.13 (vigencia de 24 h; `sub` emitido como texto desde el 15/10/2026), OTP de 6 dígitos (vigencia de 10 min) y cifrado Fernet; contraseñas con bcrypt costo 12 desde el 15/10/2026, con migración automática de los hashes SHA-256 antiguos | Conforme desde el 15/10/2026 (NC-001 y NC-008 cerradas) | Pruebas de seguridad prioritarias; `tests/test_seguridad.py` protege ambas correcciones en la regresión |
| Datos | MySQL 8 | MariaDB 10.4.32 (XAMPP, compatible con MySQL) en el puerto 3310, con modo SQL no estricto; `mysql-connector-python` 9.1, patrón DAO y conexión única Singleton | Diferencia de motor (IN-02) | Integración contra MariaDB local y contra MySQL 8 en Docker y staging; el modo no estricto guarda vacíos los valores inválidos (NC-009); la conexión única compartida limita la concurrencia y el escalado (NC-003, RM02); MariaDB 10.4 dejó de recibir soporte en junio de 2024 |
| Infraestructura | Docker en AWS | No existen `Dockerfile` ni `docker-compose.yml`; la API corre con el servidor de desarrollo de Flask y `debug=True` | Pendiente | La provisión del staging es criterio de entrada para las pruebas no funcionales |

*Nota.* Elaboración propia a partir de la revisión del repositorio (commit `c4310dc`, 2 de octubre de 2026), actualizada el 15 de octubre con las correcciones de NC-001 y NC-008. Hasta esa fecha el repositorio no tenía pruebas automatizadas; ese día se agregaron las primeras pruebas de regresión (`petconnect.Backend/tests`).

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
| RS03 | Encriptar las contraseñas con un algoritmo estándar (ej. SHA-256) | bcrypt con sal aleatoria y factor de costo 12. Política: mínimo 8 caracteres con al menos una mayúscula, una minúscula y un número; máximo 64. Control adicional del proyecto (NC-004): al menos un carácter especial de `@ # ! " $ & ? ¡ - _ * .` | CP-003, CP-004 |
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
| H-01 | RS03 pide "encriptar" las contraseñas con SHA-256. SHA-256 es una función de resumen rápida y sin sal, y una contraseña no se cifra (proceso reversible) sino que se transforma con una función de derivación irreversible | Almacenar con bcrypt (sal aleatoria y costo 12) y corregir la redacción de RS03 | `api.py` (función `_hash_password`, líneas 66–67) y `vista/menu_usuarios.py` (línea 67) usan `hashlib.sha256`; `bcrypt` no figura en `requirements.txt`. Corregido el 15/10/2026 (`security/passwords.py`) | NC-001 cerrada el 15/10/2026 |
| H-02 | RR02 fija "5 minutos" de carga por módulo, valor incompatible con RNF04 (2 s por acción) | RNF04: ≤ 2 s por acción; RR02: ≤ 5 s por módulo | Los listados no se paginan y la conexión a la base de datos es única y compartida, por lo que se anticipa incumplimiento | Requisito corregido; riesgo abierto como NC-003 |
| H-03 | La historia de usuario de RF01 indica "máximo 8 caracteres" para la contraseña, mientras que la seguridad exige una longitud mínima | Mínimo 8 caracteres con mayúscula, minúscula y número; máximo 64 (RS03) | `_validate_password` (`api.py`, líneas 70–79) exige longitud, mayúscula, número y carácter especial, pero no verifica la minúscula: acepta `PETCONNECT1!` | Corregido el 07/11/2026 con el cierre de NC-004: la API (`security/politica.py`), la web y el móvil exigen la minúscula y rechazan `PETCONNECT1!` |
| H-04 | RF03 solo exige "almacenar" el carné; el diagrama de clases incluye `generarRecordatorio()`, pero la ERS no define recordatorios ni su anticipación | Incorporar a RF03 el recordatorio de la próxima dosis con una anticipación de 3 días, valor por confirmar con el Product Owner | Funcionalidad nueva, aún no implementada | Requisito a actualizar por control de cambios |
| H-05 | RF10 y RF11 son premium, pero RIU03 exige sus íconos en el menú principal | Los íconos se muestran con un aviso de versión premium | — | Criterio agregado a RIU03 |
| H-06 | El borrador asumía una API en Node.js con Express | Documentar la arquitectura real | La API está implementada en Flask (Python) | Corregido en este plan (IN-01) |
| H-07 | El borrador asumía Docker en AWS | Provisionar el staging antes del Sprint 3 | No hay artefactos de contenedores ni de infraestructura | Criterio de entrada; riesgo R06 |
| H-08 | RNF06 exige cumplir la ley de protección de datos | Capturar la autorización expresa del titular | `/api/auth/verify` crea el usuario con `acepta_datos=True` fijo (`api.py`, línea 401) y los formularios de registro no muestran casilla de autorización | Corregido el 06/11/2026 con el cierre de NC-005: la API exige la autorización y guarda fecha y versión, y la web y el móvil muestran la casilla sin marcar con el enlace a la política |
| H-09 | RS01 depende de que el token emitido sea aceptado | El token debe validarse en los endpoints protegidos | Prueba dinámica temprana con PyJWT 2.13.0: un token con `sub` entero, como el que emite `generate_token()`, se rechaza con `InvalidSubjectError: Subject must be a string`. Corregido el 15/10/2026: el `sub` se emite como texto | NC-008 cerrada el 15/10/2026 |
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
| A03 Fallas en la cadena de suministro de software | `requirements.txt` no fija versiones de `PyJWT`, `cryptography`, `mailtrap`, `python-dotenv` y `dnspython`; la actualización no controlada de PyJWT rompió la validación de tokens; desde el 15/10/2026 las versiones están fijadas | NC-008 (cerrada) | pip-audit, npm audit, fijación de versiones |
| A04 Fallas criptográficas | SHA-256 sin sal (RS03), reemplazado por bcrypt el 15/10/2026; API servida por HTTP; token guardado en AsyncStorage sin cifrar | NC-001 (cerrada); CP-004 | Inspección; migrar el token a `expo-secure-store` |
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
| Entrada | (a) Historias de usuario con criterios de aceptación aprobados (Definition of Ready); (b) código integrado en la rama de desarrollo con build exitoso; (c) entorno desplegado con datos semilla sintéticos; (d) casos de prueba revisados por pares; (e) prueba de humo aprobada. Para las pruebas no funcionales, además: (f) staging en AWS con Docker y Gunicorn, sin el servidor de desarrollo de Flask y con `debug` desactivado; (g) HTTPS activo; (h) NC-001 corregida antes de la ronda final de seguridad (cumplido el 15/10/2026) |
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
| Docker virtualizado (integración continua) | Pruebas de integración, regresión y humo automatizadas | Runner de GitHub Actions (`ubuntu-latest`) y Docker Desktop local | `docker compose` con los servicios `api` (`python:3.14-slim` y Gunicorn) y `db` (`mysql:8.0` en modo SQL estricto, igual que el staging, con el script del esquema); variables en `.env.test`; `EMAIL_MODE=smtp`. Estado al 07/11/2026: la integración continua ya corre en `ubuntu-latest` sin Docker ni base de datos (`.github/workflows/ci.yml`), y las pruebas que requieren MariaDB se omiten allí; `docker compose` y `.env.test` siguen pendientes | Base de datos efímera recreada en cada ejecución |
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
| GitHub Actions y GitHub Projects | Gestión | Integración continua y tablero de defectos y no conformidades. Desde el 07/11/2026, `.github/workflows/ci.yml` corre en cada push un job por módulo: backend (`unittest` con Python 3.14), web (lint, `npm test` y build con Node 24) y móvil (`npm test` y `expo export` con Node 24), sin secretos; en local pasaron backend 200 pruebas (24 omitidas que requieren MariaDB), web 42 y móvil 35 |

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
| Sprint 1 | 5 al 16 de octubre de 2026 (festivo: 12 de octubre) | Pruebas estáticas y base de regresión | Aprobación del plan; aclaración de H-01 a H-05 con el Product Owner; matriz de trazabilidad; corrección y prueba de confirmación de NC-001 y NC-008 (cerradas el 15/10/2026), NC-004, NC-005, NC-009 y NC-011; `docker compose` e integración continua (la integración continua se creó el 07/11/2026 con GitHub Actions, `.github/workflows/ci.yml`, y su primera ejecución en GitHub queda pendiente del siguiente push; `docker compose` sigue pendiente); humo y regresión de registro, mascotas, exploración y directorio; TDD de `Vacunacion` (CP-010 y CP-011) | Plan aprobado, ERS actualizada, matriz v1, suite de regresión automatizada, informe de humo |
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
| **Ejecución 1c** | Prueba de regresión automatizada, 5 de noviembre de 2026 (PRIORIDADES 2.9), sobre el patrón corregido: `GET /api/mascotas/{id}` (pública) y la ruta privada nueva `GET /api/usuarios/me/mascotas/{id}`; `tests/test_mascotas.py` con el cliente de Flask y BD simulada | **Resultado obtenido:** la ruta pública responde 404 “Mascota no encontrada”, sin datos, a toda mascota que no esté en adopción, igual que a una inexistente; la privada responde 401 sin token o con un token inválido, el mismo 404 con el token de otro usuario y 200 solo con el token del dueño (pasos 2, 3, 4 y 5 aplicados al patrón). Con el código anterior, 9 de 11 pruebas fallan. Con MariaDB temporal (`test_esquema.py`, `test_mascota_privada_solo_la_ve_su_dueno`) el filtro del SQL real da el mismo resultado. **Estado: Aprobado para el patrón; NC-002 cerrada el 05/11/2026.** Los pasos 6 y 7 (app y registro de auditoría) no aplican todavía |
| **Ejecución 2** | Programada en el Sprint 2 (26 al 30 de octubre de 2026) sobre el endpoint nuevo `/api/mascotas/{id}/vacunas` | Pendiente: el endpoint del carné todavía no existe. Cuando se construya debe colgar de la ruta privada (por ejemplo `/api/usuarios/me/mascotas/{id}/vacunas`, con `@require_auth` y el mismo filtro por dueño) y reutilizar `tests/test_mascotas.py` como modelo |

#### Resumen de la Suite de Casos de Prueba

**Tabla 23**

*Suite de casos de prueba CP-001 a CP-019*

| ID | Descripción | Requerimientos | Nivel | Tipo | Prioridad | Sprint | Estado al 15 de octubre de 2026 |
|---|---|---|---|---|---|---|---|
| CP-001 | Registro de usuario con datos válidos, verificación por OTP y autorización de datos | RF01, RIU01, RNF06 | Integración, E2E | Positiva | Alta | 1 | Aprobado el 06/11/2026 en API, web y móvil (NC-005 cerrada). Antes: fallido por inspección (NC-005); el registro con OTP se aprobó el 5/10 (AA2, CP-001). El 05/11/2026 la API ya rechaza el registro sin autorización y guarda fecha y versión (`tests/test_registro_datos.py`). Web aprobada el 05/11/2026 con la API real (ejecutada por el dueño del proyecto): sin la casilla, la API responde 400 “Debes autorizar…” y el formulario muestra el mensaje sin enviar la petición; con la casilla marcada, el código OTP crea la cuenta y el conteo de la BD pasa a `acepta_datos = 1` con fecha (`1 \| 1 \| 1`). Móvil aprobado el 06/11/2026 en el emulador Android con la API real (ejecutado por el dueño del proyecto): el enlace abrió la política en el navegador del emulador; con la casilla marcada, el código OTP creó la cuenta y la app quedó con la sesión iniciada; conteo `0 \| 5 \| 0` y `1 \| 1 \| 1` (la cuenta del móvil, con fecha). Sin marcar, la app muestra el mensaje y no envía la petición (verificado con el mismo código en la compilación web, 0 peticiones) |
| CP-002 | Registro rechazado por correo ya existente, sin revelar qué correos están registrados | RF01 | Integración | Negativa | Alta | 1 | En seguimiento: el 5/10 rechazó el duplicado con HTTP 409, pero el mensaje revela que el correo existe (A07; AA2, CP-002) |
| CP-003 | Contraseña de 7, 8, 9, 64 y 65 caracteres y composición exigida (valores límite) | RS03, RIU01 | Unitario | Negativa | Alta | 1 | Aprobado el 07/11/2026 en API, web y móvil (NC-004 cerrada): 7 y 65 caracteres y 73 bytes se rechazan; 8, 9 y 64 caracteres y 72 bytes se aceptan; sin mayúscula, minúscula, número o carácter especial se rechaza (`tests/test_politica.py`, `contrasena.test.js` y `contrasena.test.mjs`). Había fallado el 5/10 (NC-004; AA2, CP-002) |
| CP-004 | Contraseña almacenada con bcrypt costo 12, nunca en texto plano, con migración de resúmenes SHA-256 | RS03, RNF03 | Unitario | Positiva | Alta | 1 | Aprobado el 15/10 en la prueba de confirmación de NC-001 (CONF-NC-001); había fallado el 5/10 (AA2, CP-007) |
| CP-005 | Inicio de sesión en dos pasos que devuelve un JWT con expiración, aceptado por un endpoint protegido; bloqueo tras 5 OTP incorrectos | RS01 | Integración | Positiva y negativa | Alta | 1 | En seguimiento: desde el 15/10 el token se acepta en las rutas protegidas (NC-008 cerrada, CONF-NC-008); desde el 4/11 el 6.º intento de OTP responde 429 “Demasiados intentos fallidos” aunque traiga el código correcto, sin entregar token (`tests/test_otp.py`, PRIORIDADES 2.5), y desde el mismo día la 6.ª petición en un minuto desde la misma IP responde 429 (`tests/test_limite.py`, 2.6). NC-006 cerrada el 04/11/2026 |
| CP-006 | Acceso a rutas privadas sin token, con token expirado o con firma alterada devuelve 401 | RS01 | Integración | Negativa | Alta | 1 | Diseñado |
| CP-007 | Registro de mascota con nombre, especie, raza, edad y foto desde el menú principal | RF02, RF05, RIU02, RIU03 | E2E | Positiva | Alta | 1 | Diseñado |
| CP-008 | Registro de mascota con campos obligatorios vacíos o edad inválida | RF02, RIU02 | Unitario | Negativa | Media | 1 | Diseñado |
| CP-009 | Registro de una segunda mascota con el mismo usuario | RF04 | Integración | Positiva | Alta | 1 | Aprobado el 5/10 en el módulo stand-alone (AA2, CP-003) |
| CP-010 | Agregar una vacuna al carné con datos válidos | RF03 | Unitario, integración | Positiva | Alta | 2 | En seguimiento: el 5/10 la BD guardó el carné, pero aceptó fechas inconsistentes (NC-010; AA2, CP-004) |
| CP-011 | Generación del recordatorio tres días antes de la próxima dosis (TDD) | RF03 | Unitario | Positiva y límites | Alta | 1–2 | Aprobado el 5/10: 6 de 6 pruebas (AA2, CP-010) |
| CP-012 | Otro usuario no puede ver el carné de una mascota ajena | RS02, RF03 | Integración, E2E | Negativa | Alta | 2 | Fallido el 5/10 (NC-002; AA2, CP-006); patrón corregido y NC-002 cerrada el 05/11/2026 (Ejecución 1c, `tests/test_mascotas.py`); Ejecución 2 pendiente hasta que exista el endpoint del carné |
| CP-013 | Búsqueda de servicios por palabra clave y filtro por tipo | RF06 | Integración | Positiva | Media | 1 | En seguimiento. La parte de palabra clave quedó corregida el 07/11/2026 (NC-011 cerrada): la búsqueda por nombre devuelve solo proveedores activos y toma `%` y `_` como letras (`tests/test_proveedores.py`). Falta el filtro por tipo: `proveedores_servicio` no tiene esa columna y la API todavía no tiene rutas de proveedores. El 5/10 la búsqueda por nombre había devuelto proveedores inactivos (NC-011; AA2, CP-005) |
| CP-014 | Crear y responder una publicación en la comunidad, con carga XSS saneada | RF07 | E2E, seguridad | Positiva y negativa | Media | 2 | Diseñado |
| CP-015 | Registrar una entrada en el diario de salud, visible solo para el dueño | RF08, RS01 | Integración | Positiva | Media | 2 | Diseñado |
| CP-016 | Publicar una mascota en adopción y recorrer sus transiciones de estado | RF09 | E2E | Positiva y negativa | Alta | 3 | Fallido el 5/10: el catálogo de adopción está vacío (NC-009; AA2, CP-012). NC-009 cerrada el 06/11/2026: la API devuelve las 6 mascotas en adopción y la web muestra un estado vacío o de error en lugar de datos fijos; la publicación y las transiciones de estado siguen sin implementar, así que el caso queda pendiente de reejecutar |
| CP-017 | Tiempo de respuesta con 500 y 1000 usuarios y estrés hasta 1500 | RNF04, RR01, RR02 | No funcional | Desempeño | Alta | 3 | Fallido el 5/10 con 500 usuarios en el entorno local: p95 de 30 s y 56 % de errores (NC-003; AA2, CP-008) |
| CP-018 | Prueba de usabilidad SUS con ocho participantes | RNF02 | No funcional | Usabilidad | Media | 3 | Diseñado |
| CP-019 | Compatibilidad en Android, iOS y navegadores | RNF05 | No funcional | Compatibilidad | Media | 3 | Diseñado |

*Nota.* Los estados del 5 de octubre provienen de la ejecución de la evidencia GA9-220501096-AA2-EV01, cuyos casos tienen numeración propia (se indica como "AA2, CP-0XX"). Esa ejecución se hizo sobre la API, los DAO y la base de datos en el entorno local; las ejecuciones en Docker, staging e interfaz siguen el cronograma de la Tabla 17. Los estados del 15 de octubre provienen de la prueba de confirmación de NC-001 y NC-008 (`Documentacion/Evidencias-Confirmacion-NC-001-NC-008`).

#### Bitácora de No Conformidades

Cuando el resultado de una revisión o de un caso difiere del esperado, se registra una no conformidad (NC). La severidad indica el impacto técnico: crítica cuando bloquea el sistema o expone datos, alta cuando impide usar una funcionalidad principal o compromete la seguridad, media cuando existe una alternativa de uso y baja cuando es estética. El estado sigue el ciclo abierta, en corrección, en verificación y cerrada.

**Tabla 24**

*Bitácora de no conformidades*

| ID | Detección | Descripción y evidencia | Severidad | Requisito / OWASP | Acción correctiva | Responsable | Estado |
|---|---|---|---|---|---|---|---|
| NC-001 | 2/10/2026, revisión estática de la ERS y del código | Algoritmo de hashing: RS03 indica SHA-256 y el código lo implementa sin sal (`api.py`, líneas 66–67; `vista/menu_usuarios.py`, línea 67). `bcrypt` no figura en `requirements.txt` | Crítica | RS03, RNF03 / A04:2025 | Reemplazar por bcrypt con costo 12 en la API y en la consola; comparar con `bcrypt.checkpw`; migrar los resúmenes heredados al siguiente inicio de sesión; longitud máxima de 64; corregir la redacción de RS03 | Camilo Orjuela y Jazmín Bautista; confirmación: Daniel Jiménez | Cerrada el 15/10/2026: bcrypt (costo 12) en la API y la consola, migración automática de los hashes SHA-256 y longitud máxima de 64; prueba de confirmación aprobada (CONF-NC-001, CONF-NC-001-MIG y CONF-NC-001-CON). Regresión por la API agregada el 07/11/2026 (PRIORIDADES 4.4, A-31, commit `37f8126`): `tests/test_endpoints.py`, `PruebasLogin` (cliente de Flask, BD y correo simulados, sin `.env`): un inicio de sesión correcto con un hash SHA-256 heredado lo reemplaza por un bcrypt de costo 12 (`$2b$12$`) que valida la contraseña y no la contiene; con un hash bcrypt no se reescribe nada, y con la contraseña equivocada no se migra. Antes la migración solo se probaba en `security/passwords.py`, y las pruebas de login la dejaban apagada. Contraprueba en una copia temporal: quitar la migración, guardar la contraseña en texto plano, reescribir también los bcrypt o migrar antes de revisar la contraseña hace fallar al menos una de las 3 pruebas |
| NC-002 | 2/10/2026, CP-012 (ejecución 1) | Elusión de la autorización por manipulación de la URL: `GET /api/mascotas/{id}` no exige autenticación ni verifica dueño ni estado; al cambiar el identificador se obtienen mascotas que no están en adopción, incluidas sus observaciones de salud | Alta (crítica si se replica en el carné) | RS02, RS01 / A01:2025 | Limitar el endpoint público a las mascotas en adopción (con el estado que defina la corrección de NC-009); endpoints privados con `@require_auth` y verificación de que `id_usuario` coincide con el usuario del token; responder 404 para no revelar existencia | Camilo Orjuela | Cerrada el 05/11/2026 (PRIORIDADES 2.9; confirmada dinámicamente el 5/10/2026, AA2, CP-006). `api.py`: `GET /api/mascotas/{id}` sigue siendo pública, pero solo devuelve mascotas con `estado = 'en_adopcion'`: el filtro va en el SQL (parametrizado) y se revisa otra vez en Python (doble barrera, por si alguien cambia la consulta). Si la mascota no existe o tiene otro estado (`activa`, `perdida`, `adoptada`, `fallecida`), responde el mismo 404 `{"error": "Mascota no encontrada"}` sin ningún dato, así que no se puede saber si existe. Ruta privada nueva `GET /api/usuarios/me/mascotas/{id}` con `@require_auth`: el SQL filtra por `id_mascota` y por el `id_usuario` del token, y Python vuelve a comparar el dueño; sin token o con un token inválido responde 401 sin consultar la BD; una mascota ajena da el mismo 404 (no 403, para no revelar que existe); el dueño la ve en cualquier estado y la respuesta no incluye `id_usuario`. Es el patrón que debe reutilizar el carné (CP-012, Ejecución 2). La web (`PetDetail.jsx`) y el móvil (`PetDetailScreen.js`) solo abren mascotas en adopción y no cambiaron. Regresión en `tests/test_mascotas.py` (11 pruebas con el cliente de Flask, BD simulada que devuelve la fila sin aplicar el `WHERE`, sin correos ni `.env`): las 11 pasan con el código corregido. Contraprueba con el `api.py` anterior (`git stash` solo de ese archivo): fallan 9 de 11 (16 casos contando los subcasos): la ruta pública devolvía 200 con los 4 estados privados y su SQL no filtraba por estado, y la ruta privada no existía (404 genérico en lugar de 401, 200 o el 404 propio); pasan con ambos, a propósito, `test_mascota_en_adopcion_responde_200_sin_token` (el caso normal nunca falló) y `test_mascota_inexistente_responde_el_mismo_404` (una mascota inexistente siempre dio 404). Suite: 89 pruebas, 78 OK y 11 omitidas que requieren MariaDB. Prueba con MariaDB temporal, ejecutada por el dueño del proyecto el 05/11/2026 con `PETCONNECT_PRUEBA_BD=1` (base desechable `petconnect_prueba` creada desde `schema.sql` + `seed.py` y borrada al final; respaldo previo de la BD de desarrollo fuera del repositorio): `tests/test_esquema.py`, `PruebasEsquemaEnBD`, 6 de 6 OK, sin omitidas, incluida `test_mascota_privada_solo_la_ve_su_dueno`, que con el SQL real comprueba que una mascota `activa` responde 404 en la ruta pública y con el token de otro usuario, y 200 con el token de su dueño |
| NC-003 | 2/10/2026, revisión estática de desempeño | Latencia en la búsqueda: los listados no se paginan ni se filtran en el servidor; una única conexión a la base de datos (Singleton en `conexion/conexion_bd.py`) se comparte entre los hilos de Flask; la API usa el servidor de desarrollo. El 5/10/2026, con 500 usuarios, el p95 fue de 30 s y falló el 56 % de las solicitudes ('MySQL Connection not available', 'bytearray index out of range') | Alta | RNF04, RR01, RR02, RM02 | Paginación y filtros parametrizados; índices sobre `mascotas(estado)` y los campos de búsqueda del directorio; pool de conexiones (`mysql.connector.pooling`); despliegue con Gunicorn | Camilo Orjuela; medición: Valentina Lobo | Abierta; confirmada el 5/10/2026 (AA2, CP-008). En corrección desde el 07/11/2026: pool de conexiones (PRIORIDADES 4.5, A-11, commit `9c417de`). `conexion/conexion_bd.py` ya no comparte una conexión entre hilos: presta conexiones de un `MySQLConnectionPool` de 10 (`DB_POOL_SIZE`, de 1 a 32), y `conexion_y_cursor()` cierra el cursor y devuelve la conexión aunque haya error. La usan los 5 DAO, `api.py`, la consola y `seed.py`. `_get_conn()`, que pedía una conexión solo para saber si había BD y nunca la devolvía, pasó a `_verificar_bd()`, que la devuelve enseguida. Con el pool lleno se espera hasta 5 s y luego responde 503, sin colgarse. El log de conexión ya no trae usuario ni host. Regresión: `petconnect.Backend/tests/test_pool.py` (25 pruebas, 3 con MariaDB real en una base temporal): pool falso con 20 hilos, espera y 503, los 32 métodos de los DAO y las 14 rutas de la API devuelven toda conexión y cierran todo cursor (con la BD vacía, con error de MySQL y con error inesperado), 30 hilos reales sin respuestas cruzadas y el modo estricto (NC-009) tras reutilizar cada conexión. Contraprueba en una copia temporal: con el código anterior fallan 20 de las 22 pruebas sin MariaDB; archivo por archivo (`api.py`, DAO, `main.py`, `seed.py`), cada arreglo tiene la suya. El 07/11/2026 también se sacaron los códigos OTP de la memoria del proceso (PRIORIDADES 4.6, A-12, commits `9ccd379` y `24ed52c`), requisito para usar Gunicorn con varios procesos: los códigos se guardan cifrados con Fernet en la tabla nueva `otp_pendientes` (`dao/otp_dao.py`), así cualquier proceso verifica el código que otro envió y no se pierden al reiniciar. Cada intento se reserva antes de comparar con un solo `UPDATE` (nunca más de 5 aunque lleguen a la vez), crear un código borra todos los vencidos (los datos del registro pendiente no se acumulan, Ley 1581) y `_mx_cache` quedó en 1.000 dominios como máximo. Se mantienen las reglas de antes (10 minutos, 5 fallos → 429, comparación en tiempo constante, reenvío del mismo código con 60 s y máximo 3). Para la base existente hay que aplicar `sql/migraciones/2026-11-07_otp_pendientes.sql` con respaldo; sin la tabla, la API no arranca y lo avisa. Regresión: `petconnect.Backend/tests/test_otp_bd.py` (47 pruebas, 16 con MariaDB en bases temporales), más `test_esquema.py`, `test_pool.py` y `test_endpoints.py`; suite de 310 (267 correctas y 43 omitidas que requieren MariaDB). Contraprueba en una copia temporal: con el código anterior, 20 intentos simultáneos comparan 20 veces en vez de 5 y 100 códigos vencidos nunca se borran; con solo el `api.py` anterior fallan 5 pruebas; con el `_mx_cache` anterior quedan 1.500 dominios en vez de 1.000. Corrección del 08/11/2026: con MariaDB, la prueba de 20 intentos dio 4 en vez de 5. Quien ganaba un intento leía la fila después, y un 6.º intento ya la había borrado al bloquearla: respondía “no hay pendiente” sin comparar, aunque trajera el código correcto. Ahora `verificar()` lee la fila antes de reservar el intento. Prueba sin MariaDB que lo fuerza siempre (los 5 que ganan se demoran 0,2 s); con el código anterior da `0 != 5`. Suite tras la corrección: 311 (268 correctas y 43 omitidas). Falta para cerrarla: paginación e índices (PRIORIDADES 4.17) y repetir CP-008/CP-017 (PRIORIDADES 4.12) |
| NC-004 | 2/10/2026, revisión estática | La política de contraseña no verifica la minúscula (`_validate_password` acepta `PETCONNECT1!`) y exige un carácter especial que RS03 no documenta | Media | RS03, RIU01 | Agregar la verificación de minúscula; documentar el carácter especial como control adicional; alinear la validación de los módulos web y móvil | Camilo Orjuela y Yuli Silva | Cerrada el 07/11/2026 (PRIORIDADES 4.1, en tres partes: API, web y móvil; confirmada dinámicamente el 5/10/2026, AA2, CP-002). API: la política pasó de `_validate_password` (`api.py`) a `validar_contrasena` en `petconnect.Backend/security/politica.py`, un módulo común que también usará la consola (PRIORIDADES 4.11, A-18). Exige, en este orden: 8 a 64 caracteres y máximo 72 bytes (bcrypt), mayúscula, **minúscula** (nueva), número y carácter especial; mayúscula y minúscula son solo `A-Z` y `a-z`, para que Python y JavaScript den el mismo resultado. El carácter especial queda documentado en RS03 como control adicional del proyecto, y el mensaje ahora nombra los 12 aceptados (`@ # ! " $ & ? ¡ - _ * .`; antes omitía los 4 últimos). `/api/auth/register` responde 400 “La contrasena debe tener al menos una minuscula” a `PETCONNECT1!` antes de consultar la BD, calcular el hash o enviar el correo. Web: `RegisterModal.jsx` toma la lista de requisitos de `src/utils/contrasena.js` (agrega “Al menos una minúscula” y “Máximo 64 caracteres”); móvil: `RegisterScreen.js`, que antes no revisaba la contraseña, usa la copia `src/utils/contrasena.js`, avisa sin llamar a la API y muestra los requisitos bajo el campo. Las dos utilidades cuentan los caracteres como Python (un emoji = 1). Regresión: `tests/test_politica.py` del backend (17 pruebas: los valores límite de CP-003, 7, 8, 9, 64 y 65 caracteres y 72 y 73 bytes; la composición, y la ruta con el cliente de Flask, BD simulada, sin correos, DNS ni `.env`), `tests/contrasena.test.js` de la web (13) y `tests/contrasena.test.mjs` del móvil (8, que también comprueba que la copia es igual a la de la web); las dos de JavaScript comparan los límites y los caracteres con `politica.py`. Todas pasan. Suites completas: backend 195 pruebas (171 correctas y 24 omitidas que requieren MariaDB), web 42 de 42 y móvil 35 de 35; `npm run lint` sin errores, `npm run build` y `npx expo export --platform web` correctos. Contraprueba con `git stash`: con el `api.py` anterior fallan 2 (`test_rechaza_contrasena_sin_minuscula_antes_de_la_bd`, porque la API vieja dejaba pasar `PETCONNECT1!`, y `test_la_api_usa_la_politica_comun`); pasan a propósito las 14 del módulo nuevo, que sigue presente, y `test_acepta_contrasena_que_cumple_la_politica` (no rechazar de más); sin `politica.py` el archivo de pruebas no carga. Con el `RegisterModal.jsx` anterior falla 1 y pasan a propósito las 12 de la utilidad; con el `RegisterScreen.js` anterior fallan 2 (no validaba antes de enviar ni mostraba los requisitos) y pasan a propósito las 6 de la utilidad; sin la utilidad, cada archivo de pruebas falla al cargar. Revisión visual a 375 px el 07/11/2026: en la web, con `PETCONNECT1!` solo “Al menos una minúscula” queda sin cumplir; en el export web del móvil, “Registrarme” muestra el aviso de la minúscula sin llamar a la API. La prueba con la API real es opcional |
| NC-005 | 2/10/2026, revisión estática | El usuario se crea con `acepta_datos=True` fijo (`api.py`, línea 401) sin que el titular otorgue la autorización en el formulario | Alta | RNF06 / Ley 1581, art. 9 | Casilla no premarcada con enlace a la política de tratamiento; persistir la fecha y la versión aceptada; rechazar el registro sin autorización | Jazmín Bautista, Yuli Silva y Camilo Orjuela | Cerrada el 06/11/2026 (PRIORIDADES 3.1, en tres partes: API y base de datos, web y móvil; prueba de confirmación con la API real en la web, el 05/11/2026, y en el móvil, el 06/11/2026, ejecutadas por el dueño del proyecto). Borrador de la política de tratamiento v1.0 en `Documentacion/Legal/POLITICA-TRATAMIENTO-DATOS-v1.0-BORRADOR.md` (Ley 1581 y Decreto 1377): texto de la política, textos de la casilla y del aviso, especificación para implementar y decisiones pendientes; lo deben validar el dueño del proyecto y el instructor antes de publicarlo. `api.py`: `/api/auth/register` exige `"acepta_datos": true` (solo el booleano JSON; sin el campo, `false`, `"true"`, `1`, `"si"` o `null` → 400 “Debes autorizar el tratamiento de tus datos personales para registrarte”), antes del DNS, de la BD y del correo, así que no se envía código ni queda registro pendiente. La versión la fija el servidor (`VERSION_POLITICA_DATOS = "1.0"`); la fecha de la autorización (la de `/register`) y la versión viajan en el pendiente y `/api/auth/verify` las escribe al crear el usuario; si el pendiente no las trae, no crea la cuenta (doble barrera). `modelo/usuario.py`: `acepta_datos=False` por defecto (la consola, ítem 4.11, ya no guarda una autorización que nadie dio). `dao/usuario_dao.py`: el `INSERT` guarda la fecha y la versión (parametrizado). `sql/schema.sql`: `acepta_datos tinyint(1) NOT NULL DEFAULT 0`, columnas `fecha_autorizacion_datos DATETIME` y `version_politica_datos VARCHAR(20)` y regla `chk_autorizacion_datos` (`acepta_datos = 0` o fecha y versión presentes). Migración `sql/migraciones/2026-11-05_autorizacion_datos.sql`: agrega las columnas, deja en `acepta_datos = 0` a los usuarios sin prueba de autorización (no se inventa una fecha; siguen pudiendo entrar), quita el `DEFAULT 1` y agrega la regla; se puede ejecutar varias veces. Regresión: `tests/test_registro_datos.py` (7 pruebas, BD simulada, sin correos, DNS ni `.env`) y `tests/test_esquema.py` (7 sin BD y 4 con MariaDB); las pruebas anteriores que se registran ahora envían `"acepta_datos": true`. Suite: 125 pruebas, 110 OK y 15 omitidas que requieren MariaDB. Contraprueba con `git stash` de un archivo a la vez: con el `api.py` anterior fallan 5 de las 7 pruebas nuevas (9 casos con los subcasos: aceptaba el registro sin autorización y creaba la cuenta sin fecha ni versión); con el `modelo/usuario.py` y el `dao/usuario_dao.py` anteriores fallan 3 de 7 (el modelo autorizaba por defecto y el `INSERT` no guardaba la prueba); con el `schema.sql` anterior fallan 4 (6 casos: `DEFAULT 1` y sin la regla). Pasan con ambos códigos, a propósito, las que solo dependen del otro archivo y las 3 que leen únicamente la migración (modo estricto, orden de los pasos y que no inventa fechas). Ejecutado por el dueño del proyecto el 05/11/2026, con respaldo previo de la BD de desarrollo fuera del repositorio: `PETCONNECT_PRUEBA_BD=1`, `PruebasEsquemaEnBD` + `PruebasMigracionDatosEnBD`, 10 de 10 OK (bases temporales, borradas al final), incluidas `test_autorizacion_de_datos_solo_con_fecha_y_version` (con la BD real, un 1 sin fecha o sin versión da error y `UsuarioDAO` guarda la prueba) y `test_los_usuarios_viejos_quedan_sin_autorizacion`; migración aplicada a la BD de desarrollo: los 10 usuarios quedaron con `acepta_datos = 0` y sin fecha (conteo sin datos personales). Parte 2 (web), 05/11/2026: `src/components/RegisterModal.jsx` muestra antes del botón una casilla **sin marcar** con el texto “Soy mayor de 18 años, he leído la Política de tratamiento de datos personales y autorizo a PetConnect a tratar mis datos para crear y usar mi cuenta” (la declaración de edad es la decisión D.4 del borrador). El nombre de la política es un enlace a `/politica-de-datos` que se abre en una pestaña nueva, para no perder lo escrito, y debajo va el aviso corto que informa la finalidad y los derechos (Ley 1581, art. 12). Si se envía sin marcar, el formulario muestra “Para crear tu cuenta debes autorizar el tratamiento de tus datos personales.” (`role="alert"`), lleva el foco a la casilla y **no** llama a la API. `src/services/api.js` envía `acepta_datos` solo como booleano (`=== true`). Página nueva `src/pages/PoliticaDatos.jsx` (ruta en `src/App.jsx` y enlace “Política de datos personales” en `src/components/Footer.jsx`) con el texto de la Parte A del borrador, rotulada “Borrador en revisión” y con los datos que faltan (alojamiento, conservación) marcados “Por definir”, sin inventarlos. El 06/11/2026 el dueño del proyecto completó los datos del responsable (decisión D.1: nombre, domicilio, dirección y teléfono, en la sección 1 de la política) y decidió el correo de atención para temas de datos (`proyectopetconnect+atencion@gmail.com`, decisión D.1): aparece en la política (secciones 1 y 8, como enlace `mailto:`) y en el aviso corto bajo la casilla, como pide el art. 12 de la Ley 1581. Verificación: `npm run lint` (0 errores, los 2 avisos de siempre) y `npm run build` correctos; revisión a 375 y 1280 px con respuestas simuladas (sin marcar: 0 peticiones a la API; marcada: el cuerpo lleva `"acepta_datos": true`); `/impeccable audit` 17/20. La web no tiene pruebas automáticas, así que la regresión de esta parte es manual. Prueba con la API real, ejecutada por el dueño del proyecto el 05/11/2026 después de reiniciar la API con el código de la parte 1 (un intento anterior dio 500 en `/verify` porque la API seguía con el código viejo, sin recargador): `POST /api/auth/register` sin el campo responde 400 “Debes autorizar el tratamiento de tus datos personales para registrarte”; el enlace abrió la política en otra pestaña con el formulario aún abierto; registro desde la web con la casilla marcada y un alias del correo del dueño, verificado con el código dentro de los 10 minutos; conteo sin datos personales (`SELECT acepta_datos, COUNT(*), COUNT(fecha_autorizacion_datos) FROM usuarios GROUP BY acepta_datos`): `0 \| 10 \| 0` (los usuarios de antes, sin autorización inventada) y `1 \| 1 \| 1` (la cuenta nueva, con fecha). Parte 3 (móvil), 05 y 06/11/2026: `PetConnect.Mobile/src/screens/RegisterScreen.js` muestra antes del botón “Registrarme” una casilla **sin marcar** (`Pressable` con `role="checkbox"` y `aria-checked`, que TalkBack anuncia como casilla marcada o sin marcar; área táctil de más de 44 px) con el mismo texto de la web, incluida la mayoría de edad. Debajo, en su propia línea, va el enlace “Leer los términos y condiciones que aceptas: Política de tratamiento de datos personales”, que abre `/politica-de-datos` en el navegador del celular con `Linking.openURL`; la pantalla de registro sigue abierta detrás, así que lo escrito no se pierde. Va aparte y no dentro de la frase porque TalkBack lee la casilla como un solo elemento y no podría activar un enlace metido en ella; la mención de “términos y condiciones” es decisión del dueño del proyecto. Después va el aviso corto (Ley 1581, art. 12). Sin marcar, la app muestra “Para crear tu cuenta debes autorizar el tratamiento de tus datos personales.” en una zona `aria-live="polite"` (TalkBack la lee sola) y **no** llama a la API. El formulario va en un `ScrollView` dentro de un `KeyboardAvoidingView`, porque en Expo 57 la ventana de Android no se encoge con el teclado. `src/services/api.js`: `registerUser(name, email, password, aceptaDatos)` envía `acepta_datos: aceptaDatos === true` (solo el booleano) y `POLITICA_URL` apunta a la web en el puerto 5173 (`10.0.2.2` en el emulador; solo vale en desarrollo, PRIORIDADES 5.3). El móvil no tiene pruebas automáticas ni linter, así que la regresión de esta parte es manual: `npx expo export --platform web` sin errores y revisión a 375 px con la API simulada (sin marcar: el mensaje aparece y hay 0 peticiones a `/api/auth/`; marcada: 1 petición cuyo cuerpo lleva `"acepta_datos": true` como booleano y la app pasa a “Verifica tu correo”); `/impeccable audit` 15/20, sin hallazgos que bloqueen la NC. Prueba en el emulador Android (Pixel 7) con la API real, ejecutada por el dueño del proyecto el 06/11/2026: el enlace abrió la política en el navegador del emulador; registro con la casilla marcada y un correo del dueño, código recibido por correo y cuenta creada (la app quedó con la sesión iniciada en Perfil); conteo sin datos personales, hecho después de que el dueño borró sus cuentas de prueba anteriores: `0 \| 5 \| 0` (cuentas sin autorización y sin fecha inventada) y `1 \| 1 \| 1` (la cuenta creada desde el móvil, con fecha). El caso “sin marcar” no se capturó en el emulador; se comprobó con el mismo código en la compilación web y, si llegara a la API, esta lo rechaza con 400 (parte 1). Fuera de esta NC: pedir la autorización a los usuarios existentes al iniciar sesión (contingencia del R05; nunca con un `UPDATE` que la invente) y volver a pedirla cuando cambie la versión (PRIORIDADES 3.5) |
| NC-006 | 2/10/2026, revisión estática | `AlmacenOTP.verificar()` (`otp/servicio.py`) no cuenta intentos fallidos y `/api/auth/login` no limita la tasa de solicitudes: el código de 6 dígitos es atacable por fuerza bruta durante sus 10 minutos de vigencia | Alta | RS01 / A07:2025 | Máximo 5 intentos por código y bloqueo temporal; limitación de tasa por IP y por cuenta; registro de intentos fallidos | Camilo Orjuela | Cerrada el 04/11/2026 (PRIORIDADES 2.5 y 2.6). Límite de intentos (2.5): `AlmacenOTP` (`otp/servicio.py`) cuenta los fallos de cada código (`MAX_INTENTOS = 5`); tras 5 fallos, el 6.º intento borra el código y responde `"bloqueado"` aunque traiga el código correcto, y hay que pedir otro (pedir uno nuevo reinicia el contador). La comparación pasó de `!=` a `hmac.compare_digest` sobre bytes (tiempo constante; con texto no ASCII como `'１２３４５６'` no lanza `TypeError`). `/api/auth/login/verify` y `/api/auth/verify` responden **429** “Demasiados intentos fallidos…” sin entregar token ni crear el usuario; los fallos 1 a 5 siguen en 400 “Codigo incorrecto”. Regresión en `tests/test_otp.py` (9 pruebas: 7 del almacén solo y 2 de las rutas con el cliente de Flask, BD simulada apagada, sin enviar correos ni leer `.env`): las 9 pasan. Contraprueba con `git stash` de un archivo a la vez: con el `otp/servicio.py` anterior fallan 5 (`test_cinco_fallos_y_luego_el_correcto_queda_bloqueado`, `test_el_bloqueo_borra_el_codigo`, `test_se_compara_con_compare_digest` y las 2 de rutas, que respondían 503 porque el 6.º intento seguía hasta la BD); con el `api.py` anterior fallan las 2 de rutas (503 en el login y 500 `TypeError` en el registro, porque no conocía el motivo `"bloqueado"`). Pasan con ambos códigos, a propósito: 4 fallos y luego el correcto entra, pedir otro código reinicia el contador, los dígitos de ancho completo son incorrectos y el código vencido sigue diciendo “expirado” (protegen contra bloquear de más o romper lo que ya funcionaba). Suite completa: 66 pruebas, 56 correctas y 10 omitidas que requieren MariaDB. Limitación de tasa (2.6, mismo día): Flask-Limiter 4.1.1 (con `limits` 5.8.0, versiones fijadas en `requirements.txt`) limita a **5 peticiones por minuto por IP** `/api/auth/login`, `/api/auth/login/verify`, `/api/auth/register`, `/api/auth/verify` y `/api/utils/validar-correo`; la 6.ª responde 429 “Demasiadas peticiones. Espera un minuto e intenta de nuevo” con la cabecera `Retry-After`. Cada ruta lleva su propia cuenta (gastar el login no impide verificar el código) y las rutas públicas no tienen límite. El contador vive en memoria, como los OTP (PRIORIDADES 4.6). Esto también frena el envío de correos sin fin desde `/register` (A-05). Regresión en `tests/test_limite.py` (5 pruebas, con IP de documentación RFC 5737, BD simulada apagada, sin correos ni DNS): las 5 pasan; las pruebas anteriores apagan el limitador porque mandan muchas peticiones seguidas. Contraprueba con el `api.py` anterior: fallan 3 (`test_la_sexta_peticion_en_un_minuto_responde_429` en las 5 rutas, `test_otra_ip_no_queda_bloqueada` y `test_el_correo_que_se_envia_queda_limitado`: nunca respondía 429); pasan con ambos, a propósito, `test_cada_ruta_lleva_su_propia_cuenta` y `test_las_rutas_publicas_no_tienen_limite` (no limitar de más). Suite completa: 71 pruebas, 61 correctas y 10 omitidas que requieren MariaDB. Mejoras posteriores sin fecha, fuera de lo que cierra esta NC: el límite es por IP y no por cuenta (el límite de 5 fallos por código cubre el OTP, pero no la contraseña del login); los intentos fallidos no se registran en el log; detrás de un proxy hará falta `ProxyFix` para leer la IP real (5.2) |
| NC-007 | 2/10/2026, revisión estática | Configuración insegura: `app.run(debug=True)`; el manejador global devuelve `str(e)` al cliente y, como comprobó la ejecución del 5/10/2026, convierte en HTTP 500 hasta las rutas inexistentes (404); `JWT_SECRET` tiene el valor por defecto `"dev-secret-inseguro"`; `decrypt()` devuelve el valor original si el descifrado falla | Alta | RNF03, RS01 / A02:2025, A10:2025 | Desactivar `debug` fuera del entorno local; mensajes genéricos con identificador de correlación; impedir el arranque sin `JWT_SECRET`; registrar y propagar los errores de descifrado | Camilo Orjuela | En corrección desde el 3/11/2026: `security/jwt_helper.py` ya no tiene valor por defecto; si `JWT_SECRET` falta o mide menos de 32 bytes, lanza `RuntimeError` al importarse y la API, la consola y `seed.py` no arrancan (el mensaje no muestra el valor recibido); `.env.example` lo documenta como obligatorio. Regresión en `tests/test_seguridad.py` (`PruebasSecretoObligatorio`, cada caso en un proceso aparte con entorno mínimo, sin leer `.env`): sin clave, con `"dev-secret-inseguro"` y con 31 bytes no arranca; con 64 caracteres sí. Las 4 pasan con el código corregido. Contraprueba con el código anterior (valor por defecto `"dev-secret-inseguro"`), hecha a propósito para demostrar que la prueba detecta el defecto: fallan `test_sin_jwt_secret_no_arranca`, `test_secreto_publico_de_ejemplo_no_arranca` y `test_secreto_de_31_bytes_no_arranca`, porque el código viejo arrancaba en los tres casos; `test_secreto_de_64_caracteres_importa_bien` pasa con ambos, porque una clave válida nunca fue el problema. El 3/11/2026 se corrigieron también `debug` y los errores (PRIORIDADES 2.3, `api.py`): el depurador solo se enciende con `FLASK_DEBUG=1` (apagado por defecto; documentado en `.env.example`); 404 y 405 responden con su código real y un mensaje en español (antes salían como 500); cualquier otro error responde 500 con un mensaje genérico y un `id_error` de correlación, y el servidor registra el id, la ruta, el tipo de error y la pila, pero no el mensaje de la excepción, que puede traer correos (Ley 1581); si la BD no responde, 503 genérico (antes 500 `'NoneType' object has no attribute 'cursor'`, y el login respondía 401 “credenciales incorrectas”); `email`, `code`, `password` y `name` deben ser texto (antes `"code": 123456` daba 500 `'int' object has no attribute 'strip'`, ahora 400). Regresión en `tests/test_errores.py` (10 pruebas con el cliente de Flask, BD simulada apagada, sin enviar correos ni leer `.env` por su cuenta): las 10 pasan con el código corregido y las 10 fallan con el anterior (contraprueba). Suite completa: 51 pruebas, 41 correctas y 10 omitidas que requieren MariaDB (`PETCONNECT_PRUEBA_BD=1`). Solo falta `decrypt()` (4.8). Mejora posterior sin fecha: revocar sesiones consultando la BD y quitar el correo del token (4.13) |
| NC-008 | 2/10/2026, prueba dinámica temprana (CP-005) | `generate_token()` (`security/jwt_helper.py`) emite el claim `sub` como entero; PyJWT 2.13.0, instalado porque `requirements.txt` no fija versión, exige que `sub` sea texto y `verify_token()` devuelve `None`. Todo endpoint con `@require_auth` (hoy `/api/auth/me`) responde 401 aunque el token se acabe de emitir | Crítica | RS01 / A03:2025 | Emitir `"sub": str(user_id)` y convertirlo a entero en `require_auth`; fijar las versiones de `requirements.txt`; agregar una prueba de ida y vuelta (emitir y validar) a la regresión | Camilo Orjuela | Cerrada el 15/10/2026: `sub` emitido como texto, conversión a entero en `require_auth` y versiones fijadas; prueba de confirmación aprobada (CONF-NC-008). Regresión con la ruta real agregada el 07/11/2026 (PRIORIDADES 4.4, A-31, commit `37f8126`): hasta entonces la prueba de ida y vuelta usaba una ruta falsa (`/_prueba/protegida`, en `tests/test_seguridad.py`) y ninguna prueba llamaba a `GET /api/auth/me`. `tests/test_endpoints.py`, `PruebasAuthMe` (cliente de Flask, BD simulada, token emitido por `generate_token` con la clave de pruebas, sin `.env`): con el token recién emitido responde 200 con `id`, `name` y `email` (sin el hash) y busca al usuario por el `id` entero del token; un token inventado, vencido, firmado con otra clave o con `sub` no numérico responde 401 sin tocar la BD; un usuario borrado, 404, y sin BD, 503. Contraprueba en una copia temporal: con `"sub": user_id` (el defecto original) fallan 3 pruebas; sin `@require_auth` en `/me`, 4 |
| NC-009 | 5/10/2026, ejecución (AA2, CP-012) | Catálogo de adopción siempre vacío: `seed.py` y la API usan el estado `'en_adopcion'`, que no existe en el enum de `mascotas.estado`; MariaDB, en modo no estricto, lo guarda vacío (advertencia 1265). Las 6 mascotas de la BD de desarrollo tienen estado vacío, y la web lo oculta mostrando las mascotas fijas de `src/data/pets.js` | Alta | RF09 / A02:2025 | Definir un único modelo de adopción (agregar el estado al enum o usar la tabla `adopciones`), corregir los registros existentes, activar el modo SQL estricto y mostrar un estado vacío en la web en lugar de datos fijos | Camilo Orjuela | Cerrada el 06/11/2026 (PRIORIDADES 1.1, 1.2 y 3.3; prueba de confirmación con la API real ejecutada por el dueño del proyecto). Desde el 3/11/2026: `petconnect.Backend/sql/schema.sql` agrega `en_adopcion` al enum y activa el modo SQL estricto (también en cada conexión, `config/db_config.py`); una BD creada desde el repositorio devuelve las 6 mascotas en adopción (regresión en `tests/test_esquema.py`). El 3/11/2026 se agregó la migración `petconnect.Backend/sql/migraciones/2026-11-03_estado_en_adopcion.sql`, que corrige las BD existentes (las mascotas con estado vacío pasan a `en_adopcion`) sin apagar el modo estricto: si encuentra un estado desconocido se detiene y lo conserva; probada contra MariaDB en `tests/test_esquema.py` (`PruebasMigracionEnBD`). Aplicada a la BD de desarrollo el 3/11/2026, con respaldo previo: antes, 6 mascotas con estado vacío; después, 6 en `en_adopcion` y ninguna vacía. El 06/11/2026 (PRIORIDADES 3.3, A-23) la web dejó de ocultar los fallos con datos fijos: se borraron `src/data/pets.js` y `src/data/products.js`; Adopción, Catálogo, Inicio y las fichas muestran estados de carga, vacío (“Por ahora no hay mascotas en adopción”) y error con “Reintentar” (componente `src/components/EstadoCarga.jsx`), y la ficha distingue “no encontrada” (404) de “no pudimos cargar” (503, 502 o sin conexión) gracias al `status` que ahora trae cada error de `src/services/api.js`. Regresión automatizada en la web (`npm test`, `node --test`): `tests/api.test.js` y `tests/sin-datos-falsos.test.js`; con el código anterior fallan 5 de 6 (pasa a propósito la de la respuesta correcta) y con el nuevo pasan 6 de 6; lint sin errores y build correcto. Contraprueba visual a 375 px con la API apagada: el código anterior mostraba las 6 mascotas fijas y la ficha de “Luna”; el nuevo muestra “No pudimos cargar las mascotas en adopción”. Con una lista vacía simulada se ve el estado vacío, que es lo que habría revelado NC-009 el 5/10/2026. Prueba de confirmación con la API real, ejecutada por el dueño del proyecto el 06/11/2026: `/adopcion` muestra las 6 mascotas de la BD de desarrollo, `/adopcion/99999` muestra “Mascota no encontrada” y el inicio muestra los productos de la BD; el registro de la API marca `GET /api/mascotas/adopcion` 200, `GET /api/mascotas/99999` 404 y `GET /api/productos` 200. Regresión sin MariaDB agregada el 07/11/2026 (PRIORIDADES 4.4, A-31, commit `37f8126`): el filtro de la lista de adopción solo se probaba con MariaDB (`PETCONNECT_PRUEBA_BD=1`), que la integración continua omite; `tests/test_endpoints.py`, `PruebasListaAdopcion`, comprueba con la BD simulada que `GET /api/mascotas/adopcion` consulta `WHERE estado = 'en_adopcion'` y que una lista vacía responde 200 `[]`. Contraprueba en una copia temporal: sin el filtro, la prueba falla |
| NC-010 | 5/10/2026, ejecución (AA2, CP-004) | El carné acepta una próxima dosis anterior a la fecha de aplicación: `aplicaciones_vacuna` no tiene ninguna validación de fechas | Media | RF03 | Validar las fechas en la capa de servicio del carné y agregar una restricción CHECK en la base de datos | Camilo Orjuela y Yuli Silva | En corrección desde el 3/11/2026: restricción `chk_aplicacion_fechas` en `aplicaciones_vacuna` (la próxima dosis debe ser posterior a la aplicación), probada contra MariaDB en `tests/test_esquema.py`. Desde el 3/11/2026 la misma restricción llega a las BD existentes con la migración `sql/migraciones/2026-11-03_estado_en_adopcion.sql` (probada en `tests/test_esquema.py`). Falta la validación en la capa de servicio cuando se implemente el carné |
| NC-011 | 5/10/2026, ejecución (AA2, CP-005) | `buscar_por_nombre()` del directorio devuelve proveedores inactivos, a diferencia de `consultar_por_ciudad()` | Baja | RF06 | Agregar `AND activo = TRUE` a la consulta y un caso de regresión | Camilo Orjuela | Cerrada el 07/11/2026 (PRIORIDADES 4.2, commit `06a422d`; confirmada dinámicamente el 5/10/2026, AA2, CP-005). `petconnect.Backend/dao/proveedor_dao.py`: `_BUSCAR_POR_NOMBRE` pasó de `WHERE nombre LIKE %s` a `WHERE nombre LIKE %s ESCAPE '!' AND activo = TRUE`, la misma regla de `_CONSULTAR_POR_CIUDAD`. Además, `buscar_por_nombre` escapa `!`, `%` y `_` del término (`_escapar_like`): antes, buscar `_` mostraba todos los proveedores. No era inyección SQL, porque la consulta ya iba parametrizada. Se usa `!` como carácter de escape porque la barra invertida cambia de significado con el modo `NO_BACKSLASH_ESCAPES` de MariaDB. Solo la usa la consola (`vista/menu_proveedores.py`, opción 5); la API no tiene rutas de proveedores, así que la web y el móvil no cambian. El administrador sigue viendo los inactivos con “Consultar todos” y “Buscar por ID”. Regresión: `tests/test_proveedores.py` (5 pruebas, conexión simulada, sin BD real ni `.env`), que revisan el SQL enviado a `cursor.execute`. Suite completa: 200 pruebas (176 correctas y 24 omitidas que requieren MariaDB). Contraprueba con `git stash` del DAO: con el código anterior fallan 3 de 5 (`test_busqueda_por_nombre_solo_trae_activos`, `test_misma_regla_que_la_busqueda_por_ciudad` y `test_escapa_comodines`, con sus 3 subcasos: 5 fallos en total). Pasan a propósito `test_busqueda_sigue_parametrizada` y `test_devuelve_proveedores_mapeados`, que prueban lo que no debía romperse. La prueba manual en la consola con la BD real es opcional |

*Nota.* NC-001 a NC-003 corresponden a los hallazgos previos del equipo, confirmados contra el código. NC-004 a NC-008 son hallazgos nuevos de la revisión técnica. NC-009 a NC-011 surgieron de la primera ejecución de casos, el 5 de octubre de 2026 (evidencia GA9-220501096-AA2-EV01). NC-001 y NC-008 se cerraron el 15 de octubre de 2026, después de aprobar su prueba de confirmación; su prueba de regresión está en `petconnect.Backend/tests/test_seguridad.py`. Todas tienen un caso de regresión asociado para evitar su reaparición.

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
| R01 | Inseguridad de contraseñas | SHA-256 sin sal, tal como indicaba RS03 (NC-001); corregido el 15/10 con bcrypt. Riesgo residual: cuentas antiguas que aún no inician sesión | 2 | 5 | 10 – Medio | bcrypt costo 12 y migración automática al iniciar sesión; CP-004 y `tests/test_seguridad.py` en la regresión | Restablecimiento forzado de las contraseñas sin migrar; aviso a los titulares y a la autoridad de protección de datos | Camilo Orjuela |
| R02 | Exposición del carné de vacunación | Patrón de acceso sin autorización por objeto (NC-002) | 4 | 5 | 20 – Crítico | Autorización por dueño desde el diseño; CP-012 automatizado en la integración continua | Desactivar el endpoint del carné y retirar la versión afectada | Camilo Orjuela |
| R03 | Degradación del desempeño bajo carga | Conexión única, sin paginación, servidor de desarrollo (NC-003); materializado el 5/10 con 500 usuarios (56 % de errores) | 5 | 4 | 20 – Crítico | Pool de conexiones, paginación, índices y Gunicorn antes del Sprint 3 | Escalar horizontalmente la API en AWS; limitar temporalmente funciones costosas | Valentina Lobo |
| R04 | Autenticación débil o inutilizable | OTP sin límite de intentos y secreto JWT por defecto (NC-006, NC-007); el token rechazado (NC-008) se corrigió el 15/10 | 3 | 5 | 15 – Alto | Límite de intentos y de tasa; secreto obligatorio; la prueba de ida y vuelta del token ya está en la regresión | Bloqueo de cuentas afectadas y rotación del secreto JWT | Camilo Orjuela |
| R05 | Incumplimiento de la Ley 1581 de 2012 | Autorización no capturada (NC-005) o datos reales en las pruebas | 3 | 5 | 15 – Alto | Casilla de autorización y política publicada en el Sprint 1; solo datos sintéticos | Solicitar la autorización a los usuarios existentes; suspender las pruebas y depurar los datos. Contingencia en curso (PRIORIDADES 3.5, A-20): parte 1 (API y DAO) hecha el 06/11/2026: `/api/auth/login` responde 403 `"requiere_autorizacion": true` (solo con la contraseña correcta, sin enviar código) a las cuentas con `acepta_datos = 0` o con otra versión de la política, y `/api/auth/login/verify` guarda la fecha y la versión solo con la casilla marcada y el código correcto (nunca un `UPDATE` que la invente; sin prueba válida, 403 sin token). Regresión: `tests/test_login_datos.py` (12) y `test_esquema.py` con MariaDB temporal (1). Contraprueba con `git stash`: con el `api.py` anterior fallan 5 de 9 pruebas de la API (23 casos); con el `dao/usuario_dao.py` anterior, las 3 del DAO; pasan a propósito las 4 que ya funcionaban (contraseña mala, cuenta inactiva, cuenta autorizada, código incorrecto). Suite: 153 pruebas, 132 OK y 21 omitidas que requieren MariaDB. Parte 2 (web) hecha el 06/11/2026: cuando `/login` responde ese 403, `LoginModal.jsx` muestra la casilla sin marcar (componente `CasillaAutorizacion.jsx`, el mismo del registro), “Autorizar y continuar” repite el inicio de sesión con `"acepta_datos": true`, “Cancelar” vuelve atrás y un enlace al correo de atención permite pedir que se borre la cuenta; sin marcar no se llama a la API. Regresión web: `tests/api.test.js` (5 nuevas) y `tests/casilla-autorizacion.test.js` (3); contraprueba con `git stash`: fallan 7 de las 8 nuevas y pasa a propósito la que comprueba que sin casilla no se manda `acepta_datos`. `npm test` 20/20, lint y build correctos, revisión a 375 px con la API simulada (sin marcar: 0 peticiones). “Cancelar” queda desactivado mientras se envía la petición (arreglo de una revisión del 06/11/2026). Prueba con la API real, ejecutada por el dueño del proyecto el 06/11/2026: una cuenta con `acepta_datos = 0` inició sesión en la web, vio la casilla, la marcó, escribió el código y quedó con `acepta_datos = 1` y la fecha de la autorización; otra cuenta creada ese día desde el registro web con la casilla también quedó autorizada (conteo esperado `0 \| 6 \| 0` y `1 \| 3 \| 3`, deducido). El caso “sin marcar” lo cubren las pruebas automáticas y la API simulada. Parte 3 (móvil) hecha el 06/11/2026, con la que la contingencia queda completa en API, web y móvil: `LoginScreen.js` muestra la misma casilla del registro (componente nuevo `src/components/CasillaAutorizacion.js`) cuando la API la pide, con “Autorizar y continuar”, “Cancelar” y el enlace al correo de atención para pedir que se borre la cuenta; sin marcar no se llama a la API. Regresión móvil: `tests/peticiones.test.mjs` (5) y `tests/casilla-autorizacion.test.mjs` (4); contraprueba con `git stash`: fallan 5 de las 9 nuevas y pasan a propósito las 4 que solo prueban el archivo nuevo `src/utils/peticiones.js`. `npm test` 16/16, exportación web correcta y revisión a 375 px con la API simulada (sin marcar: 0 peticiones; marcada: 1 con `"acepta_datos": true`). Prueba en el emulador Android con la API real, ejecutada por el dueño del proyecto el 07/11/2026: una cuenta con `acepta_datos = 0` inició sesión desde el móvil, vio la casilla, la marcó, escribió el código y quedó con `acepta_datos = 1` y la fecha de la autorización (consulta sin datos personales). El caso “sin marcar” lo cubren las pruebas automáticas y la API simulada | Jazmín Bautista |
| R06 | Retraso en la provisión del staging (Docker y AWS) | No existen artefactos de infraestructura en el repositorio; el motor local (MariaDB 10.4) difiere del objetivo (MySQL 8) | 3 | 4 | 12 – Alto | `docker compose` en el Sprint 1 y staging listo al inicio del Sprint 3 | Ejecutar JMeter en el entorno Docker local con carga reducida y extrapolar con cautela | Daniel Jiménez |
| R07 | Dependencia de servicios externos | Correo para el OTP, notificaciones push y mapas | 3 | 3 | 9 – Medio | Modo `smtp` (sandbox) y servicios simulados en las pruebas | Proveedor alterno; código impreso en la consola solo en el entorno local | Camilo Orjuela |
| R08 | Fragmentación de dispositivos y falta de iPhone físico | Diversidad de versiones de Android; compilar para iOS requiere macOS | 3 | 3 | 9 – Medio | Matriz de dispositivos con emulador, simulador y equipos físicos | Préstamo de equipos o servicio de dispositivos en la nube | Yuli Silva |
| R09 | Menor tiempo disponible para las pruebas | Retrasos del desarrollo, carga académica y festivos (12 de octubre, 2 y 16 de noviembre) | 3 | 3 | 9 – Medio | Cronograma con festivos descontados; tablero visible | Repriorizar por riesgo y mover los casos de prioridad baja al siguiente ciclo | Daniel Jiménez |
| R10 | Requerimientos ambiguos o contradictorios | Hallazgos H-01 a H-05 de la ERS | 3 | 3 | 9 – Medio | Aclaración con el Product Owner en el Sprint 1 y control de cambios sobre la ERS | Congelar el alcance del sprint y documentar los supuestos en el plan | Jazmín Bautista |

Los riesgos R01 y R02 nacieron críticos porque combinaban una vulnerabilidad confirmada en el código con un impacto máximo sobre la confidencialidad. Si se filtrara la base de datos, R01 permitiría recuperar por fuerza bruta la mayoría de las contraseñas, que los usuarios suelen reutilizar en otros servicios; el daño excedería a PetConnect. R02 expone información de las mascotas vinculada a su dueño con solo cambiar un número en la URL, un ataque que no requiere conocimientos técnicos y que viola directamente RS02. En ambos casos, la Ley 1581 obliga al responsable del tratamiento a garantizar la seguridad de la información y a informar a la autoridad de protección de datos cuando se presenten violaciones a los códigos de seguridad (Congreso de la República de Colombia, 2012, art. 17). Por esa razón, NC-001 y NC-002 se definieron como criterios de salida bloqueantes: sin su corrección y su prueba de confirmación aprobada no hay liberación, cualquiera sea el resultado del resto de la suite. El 15 de octubre de 2026 se corrigió NC-001 y su prueba de confirmación fue aprobada, por lo que R01 bajó a nivel medio: el riesgo residual son las cuentas antiguas que todavía no han iniciado sesión y conservan el hash SHA-256. NC-002 sigue abierta y continúa bloqueando la liberación. R03 pasó de alto a crítico después de la ejecución del 5 de octubre, porque el riesgo dejó de ser una hipótesis: con 500 usuarios falló más de la mitad de las solicitudes. Su corrección (pool de conexiones y Gunicorn) es requisito para la prueba de carga del Sprint 3.

## Conclusiones

La elaboración del plan de pruebas permitió encontrar defectos antes de ejecutar una sola prueba formal. La revisión estática de la ERS reveló un algoritmo inadecuado para las contraseñas (RS03), un tiempo de carga incoherente (RR02), una regla de longitud de contraseña mal planteada en la historia de usuario de RF01, un recordatorio de vacunación que el diseño contempla pero la ERS no especifica, y una tensión entre el menú de RIU03 y el alcance premium. El contraste con el código confirmó NC-001, materializó el riesgo de elusión de autorización de NC-002 en un endpoint existente, anticipó la latencia de NC-003 a partir de su causa técnica y reveló cinco no conformidades nuevas: la política de contraseñas incompleta, la ausencia de autorización conforme a la Ley 1581, el OTP sin límite de intentos, una configuración insegura del servidor y, mediante una prueba dinámica de pocas líneas, un token JWT que la propia API rechaza por una actualización no controlada de dependencias.

La primera ejecución de casos, el 5 de octubre de 2026 (evidencia GA9-220501096-AA2-EV01), llevó el plan a la práctica: de 12 casos, 5 se aprobaron, 3 quedaron en seguimiento y 4 se rechazaron. La ejecución confirmó con pruebas dinámicas NC-001, NC-002, NC-003 y NC-004, y reveló tres no conformidades nuevas: el catálogo de adopción siempre vacío por un estado que no existe en la base de datos (NC-009), el carné sin validación de fechas (NC-010) y la búsqueda del directorio que muestra proveedores inactivos (NC-011).

El 15 de octubre, atendiendo la retroalimentación del instructor, el equipo corrigió las dos no conformidades que bloqueaban la autenticación y la protección de credenciales. NC-008 se resolvió emitiendo el identificador del usuario como texto, como exige el estándar JWT, y fijando las versiones de las dependencias; NC-001, guardando las contraseñas con bcrypt y migrando automáticamente las cuentas antiguas en su siguiente inicio de sesión. Ambas se cerraron tras aprobar su prueba de confirmación, y 13 pruebas de regresión impiden que reaparezcan. Con la autenticación funcionando quedan habilitados los casos que dependen de ella, como los del carné de vacunación, cuya protección por dueño depende ahora de corregir NC-002.

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
