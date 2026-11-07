import { useEffect } from "react";
import { AlertTriangle } from "lucide-react";

// NC-005 (ítem 3.1): copia publicada de la Parte A de
// Documentacion/Legal/POLITICA-TRATAMIENTO-DATOS-v1.0-BORRADOR.md (Ley 1581 de 2012).
// Si cambias este texto, cambia también el .md y sube la versión aquí y en la API
// (VERSION_POLITICA_DATOS en petconnect.Backend/api.py): la versión es la prueba
// de qué aceptó cada persona.
// BORRADOR: lo deben validar el dueño del proyecto y el instructor antes de publicarlo.
// 1.1 (07/11/2026, ítem 3.6): agrega las solicitudes de adopción y los mensajes de contacto.
// tests/solicitudes.test.js revisa que sea la misma versión de la API.
const VERSION_POLITICA = "1.1";
// Correo de atención del proyecto (decisión D.1, 06/11/2026). Es del proyecto, no de una persona.
const CORREO_DATOS = "proyectopetconnect+atencion@gmail.com";

/** Enlace al correo de datos; break-words: baja entero de línea y solo se parte si no cabe solo (375 px). */
function CorreoDatos() {
  return (
    <a
      href={`mailto:${CORREO_DATOS}`}
      className="font-medium text-black underline underline-offset-2 break-words hover:text-gray-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-black"
    >
      {CORREO_DATOS}
    </a>
  );
}

const SECCIONES = [
  { id: "responsable", titulo: "Quién es el responsable de tus datos" },
  { id: "marco-legal", titulo: "Marco legal" },
  { id: "palabras-clave", titulo: "Palabras clave" },
  { id: "datos", titulo: "Qué datos recogemos y cómo" },
  { id: "finalidades", titulo: "Para qué usamos tus datos" },
  { id: "autorizacion", titulo: "Tu autorización" },
  { id: "derechos", titulo: "Tus derechos" },
  { id: "ejercer-derechos", titulo: "Cómo ejercer tus derechos" },
  { id: "encargados", titulo: "Con quién compartimos tus datos" },
  { id: "seguridad", titulo: "Cómo protegemos tus datos" },
  { id: "conservacion", titulo: "Cuánto tiempo guardamos tus datos" },
  { id: "menores", titulo: "Niñas, niños y adolescentes" },
  { id: "cambios", titulo: "Cambios a esta política" },
  { id: "vigencia", titulo: "Vigencia" },
];

/** Dato que todavía no se ha decidido (Parte D del borrador). Nunca se inventa. */
function PorDefinir({ children }) {
  return (
    <span className="rounded bg-amber-100 px-1 text-amber-950 underline decoration-amber-600 decoration-dashed underline-offset-4">
      Por definir: {children}
    </span>
  );
}

function Seccion({ id, children }) {
  const n = SECCIONES.findIndex((s) => s.id === id);
  return (
    <section id={id} aria-labelledby={`${id}-titulo`} className="scroll-mt-24 border-t border-gray-200 pt-8 mt-10 first:mt-0 first:border-t-0 first:pt-0">
      <h2 id={`${id}-titulo`} className="text-xl font-bold leading-snug mb-4 text-gray-950">
        <span className="text-gray-500 font-semibold mr-2 tabular-nums">{n + 1}.</span>
        {SECCIONES[n].titulo}
      </h2>
      <div className="space-y-4">{children}</div>
    </section>
  );
}

function Indice() {
  return (
    <ol className="space-y-1 text-sm list-none p-0 m-0">
      {SECCIONES.map((s, i) => (
        <li key={s.id}>
          <a
            href={`#${s.id}`}
            className="flex gap-2 rounded px-2 py-1.5 text-gray-700 no-underline hover:bg-gray-100 hover:text-black focus-visible:outline-2 focus-visible:outline-black"
          >
            <span className="tabular-nums text-gray-500 w-5 shrink-0 text-right">{i + 1}.</span>
            <span>{s.titulo}</span>
          </a>
        </li>
      ))}
    </ol>
  );
}

/** Lista de pares "nombre: detalle" que en pantallas pequeñas reemplaza a una tabla. */
function Fila({ titulo, children }) {
  return (
    <li className="py-3 border-b border-gray-100 last:border-b-0">
      <p className="font-semibold text-gray-950">{titulo}</p>
      <div className="text-gray-700 mt-0.5">{children}</div>
    </li>
  );
}

export default function PoliticaDatos() {
  // Título propio en la pestaña del navegador (WCAG 2.4.2); se restaura al salir
  useEffect(() => {
    const anterior = document.title;
    document.title = "Política de datos personales | Pet Connect";
    return () => {
      document.title = anterior;
    };
  }, []);

  return (
    <main className="page-enter max-w-6xl mx-auto px-4 py-10 md:py-14">
      <div className="lg:grid lg:grid-cols-[15rem_minmax(0,1fr)] lg:gap-12">
        <aside className="hidden lg:block" aria-label="Contenido de la política">
          <nav className="sticky top-24">
            <p className="text-sm font-semibold text-gray-950 mb-2 px-2">En esta página</p>
            <Indice />
          </nav>
        </aside>

        <article className="max-w-[68ch] text-base leading-relaxed text-gray-800">
          <header className="mb-8">
            <h1 className="text-3xl md:text-4xl font-bold leading-tight text-gray-950 text-balance">
              Política de tratamiento de datos personales
            </h1>
            <p className="mt-3 text-gray-600">
              Versión {VERSION_POLITICA}. Vigente desde: <PorDefinir>fecha de publicación</PorDefinir>.
            </p>

            <div
              role="note"
              className="mt-6 flex gap-3 rounded-lg border border-amber-300 bg-amber-50 p-4 text-sm text-amber-950"
            >
              <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5 text-amber-700" aria-hidden="true" />
              <p>
                <strong>Borrador en revisión.</strong> Este texto todavía no lo ha validado el equipo del
                proyecto con su instructor. Los datos marcados como “por definir” se completarán antes de
                publicarlo.
              </p>
            </div>
          </header>

          {/* Lo primero que alguien necesita saber, en lenguaje sencillo */}
          <section aria-labelledby="resumen-titulo" className="mb-10 rounded-xl border border-[#6dd5d8]/60 bg-[#6dd5d8]/10 px-5 py-5">
            <h2 id="resumen-titulo" className="text-lg font-bold text-gray-950 mb-3">En pocas palabras</h2>
            <ul className="space-y-2 list-disc pl-5 marker:text-gray-400">
              <li>Para crear tu cuenta te pedimos tu nombre, tu correo y una contraseña que nunca guardamos tal cual.</li>
              <li>Los usamos solo para tu cuenta, para enviarte códigos de verificación y para mostrar tus mascotas.</li>
              <li>
                Si nos envías una solicitud de adopción o un mensaje de contacto, lo guardamos (con tu teléfono, si lo
                escribes) para responderte. Solo lo lee el equipo de PetConnect.
              </li>
              <li>No vendemos tus datos, no te enviamos publicidad y no usamos herramientas de seguimiento.</li>
              <li>
                Puedes pedir ver, corregir o borrar tus datos cuando quieras: te explicamos cómo en la{" "}
                <a href="#ejercer-derechos" className="font-medium text-black underline underline-offset-2">sección 8</a>.
              </li>
            </ul>
          </section>

          <details className="lg:hidden mb-10 rounded-lg border border-gray-200">
            <summary className="cursor-pointer select-none px-4 py-3 min-h-11 font-semibold text-gray-950 focus-visible:outline-2 focus-visible:outline-black">
              Contenido de la política
            </summary>
            <div className="px-2 pb-3">
              <Indice />
            </div>
          </details>

          <Seccion id="responsable">
            <p>El responsable del tratamiento de tus datos personales es:</p>
            <dl className="grid grid-cols-1 sm:grid-cols-[11rem_1fr] gap-x-4 gap-y-1 sm:gap-y-3">
              <dt className="font-semibold text-gray-950">Nombre</dt>
              {/* D.1 completa, decidida por el dueño del proyecto el 06/11/2026 */}
              <dd className="mb-3 sm:mb-0">
                PetConnect y sus asociados: Daniel Jimenez, Andrea Silva, Nelson Perez y Andrea Yasmin
              </dd>
              <dt className="font-semibold text-gray-950">Domicilio</dt>
              <dd className="mb-3 sm:mb-0">Armenia, Quindío, Colombia</dd>
              <dt className="font-semibold text-gray-950">Dirección física</dt>
              <dd className="mb-3 sm:mb-0">Cra. 6 # 17 Norte 01, Armenia, Quindío</dd>
              <dt className="font-semibold text-gray-950">Correo para temas de datos</dt>
              <dd className="mb-3 sm:mb-0"><CorreoDatos /></dd>
              <dt className="font-semibold text-gray-950">Teléfono</dt>
              <dd>
                <a
                  href="tel:+573243682078"
                  className="font-medium text-black underline underline-offset-2 hover:text-gray-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-black"
                >
                  324 368 2078
                </a>
              </dd>
            </dl>
            <p>
              PetConnect es una plataforma para personas que tienen mascotas o quieren adoptar una. Reúne adopción,
              catálogo de productos y directorio de servicios.
            </p>
          </Seccion>

          <Seccion id="marco-legal">
            <p>
              Esta política cumple la <strong>Ley Estatutaria 1581 de 2012</strong> (protección de datos personales),
              su decreto reglamentario <strong>Decreto 1377 de 2013</strong> (hoy compilado en el Decreto Único 1074
              de 2015) y el artículo 15 de la Constitución Política de Colombia (derecho al hábeas data).
            </p>
          </Seccion>

          <Seccion id="palabras-clave">
            <dl className="space-y-3">
              {[
                ["Dato personal", "cualquier información que te identifica o te puede identificar, como tu nombre o tu correo."],
                ["Titular", "tú, la persona a quien se refieren los datos."],
                ["Tratamiento", "cualquier cosa que se haga con tus datos: recogerlos, guardarlos, usarlos, enviarlos o borrarlos."],
                ["Autorización", "tu permiso previo, expreso e informado para que tratemos tus datos."],
                ["Responsable", "quien decide para qué y cómo se tratan los datos (sección 1)."],
                ["Encargado", "quien trata datos por cuenta del responsable, por ejemplo el servicio que envía nuestros correos."],
              ].map(([termino, definicion]) => (
                <div key={termino}>
                  <dt className="inline font-semibold text-gray-950">{termino}: </dt>
                  <dd className="inline">{definicion}</dd>
                </div>
              ))}
            </dl>
          </Seccion>

          <Seccion id="datos">
            <ul className="list-none p-0 m-0">
              <Fila titulo="Nombre y apellidos">Al registrarte. Obligatorio.</Fila>
              <Fila titulo="Correo electrónico">Al registrarte y al iniciar sesión. Obligatorio.</Fila>
              <Fila titulo="Contraseña">
                Al registrarte. Obligatoria. <strong>No la guardamos tal cual:</strong> guardamos solo una huella
                cifrada (hash bcrypt) de la que no se puede sacar la contraseña.
              </Fila>
              <Fila titulo="Fecha de tu autorización y versión de la política que aceptaste">
                Al registrarte. Obligatorio: es la prueba de tu autorización.
              </Fila>
              <Fila titulo="Códigos de verificación">
                Cada vez que te registras o inicias sesión; te los enviamos por correo. Obligatorios.
              </Fila>
              <Fila titulo="Datos de tus mascotas">
                Nombre, especie, raza, sexo, edad aproximada, color, foto y observaciones. Solo si registras mascotas
                en tu cuenta. Opcionales.
              </Fila>
              <Fila titulo="Mensajes que nos envías por los formularios de adopción y contacto">
                Con la fecha y la mascota. Solo si los envías, con tu sesión iniciada. Opcionales.
              </Fila>
              <Fila titulo="Teléfono">Solo si lo escribes en una solicitud de adopción. Opcional.</Fila>
              <Fila titulo="Dirección IP desde la que te conectas">En cada petición, por razones técnicas.</Fila>
            </ul>
            <p>
              <strong>No pedimos datos sensibles</strong> (salud, origen racial o étnico, orientación política,
              creencias, datos biométricos, vida sexual, etc.) y te pedimos que no los escribas en campos libres como
              las observaciones de tus mascotas. Los datos de salud de las mascotas (vacunas, por ejemplo) son de los
              animales, no tuyos, pero los tratamos con el mismo cuidado porque están asociados a tu cuenta.
            </p>
            <p>
              <strong>En tu dispositivo:</strong> para que no tengas que iniciar sesión en cada pantalla, la web guarda
              tu sesión (un token y tu nombre y correo) en el almacenamiento local del navegador, y la app la guarda en
              el almacenamiento del celular. Se borra al cerrar sesión. No usamos cookies de publicidad ni herramientas
              de analítica o seguimiento.
            </p>
          </Seccion>

          <Seccion id="finalidades">
            <ol className="list-decimal pl-6 space-y-2 marker:text-gray-500">
              <li>Crear tu cuenta y permitirte iniciar sesión.</li>
              <li>Verificar que el correo es tuyo y proteger tu cuenta con códigos que te enviamos por correo.</li>
              <li>Enviarte los correos necesarios para usar el servicio: códigos de verificación y bienvenida.</li>
              <li>
                Mostrarte y administrar tus mascotas. Las que publiques <strong>en adopción</strong> se muestran a
                cualquier visitante (nombre, especie, raza, sexo, edad, foto y descripción), <strong>sin</strong> tus
                datos personales.
              </li>
              <li>
                Proteger la plataforma: limitar los intentos de inicio de sesión y de códigos, y detectar abusos. Los
                registros técnicos del servidor no guardan tu correo ni tus códigos.
              </li>
              <li>Atender tus consultas, reclamos y solicitudes sobre tus datos.</li>
              <li>
                Gestionar tus solicitudes de adopción y responder tus mensajes de contacto. Solo los lee el equipo de
                PetConnect; no se envían a quien publicó la mascota.
              </li>
            </ol>
            <p>
              <strong>Lo que no hacemos:</strong> no vendemos ni alquilamos tus datos, no te enviamos publicidad y no
              los usamos para fines distintos a los de esta lista. Si algún día quisiéramos usarlos para otra cosa (por
              ejemplo, enviarte novedades), te pediríamos una autorización nueva y aparte, que podrías no dar sin
              perder tu cuenta.
            </p>
          </Seccion>

          <Seccion id="autorizacion">
            <p>
              Solo tratamos tus datos si nos autorizas <strong>antes</strong> de registrarte, marcando tú la casilla
              del formulario de registro. La casilla viene sin marcar y no puedes crear la cuenta sin ella (Ley 1581,
              art. 9). Guardamos la fecha y la versión de esta política que aceptaste, como prueba (Decreto 1377,
              art. 8).
            </p>
            <p>
              Los formularios de adopción y contacto no piden otra casilla: usan la autorización de tu cuenta con esta
              versión de la política, y cada solicitud guarda la versión que tenías aceptada al enviarla. Si aceptaste
              una versión anterior, te pediremos autorizar otra vez al iniciar sesión.
            </p>
            <p>
              No necesitamos tu autorización en los casos del artículo 10 de la Ley 1581, por ejemplo una orden
              judicial o un requerimiento de una entidad pública en ejercicio de sus funciones.
            </p>
          </Seccion>

          <Seccion id="derechos">
            <p>Como titular tienes derecho a (Ley 1581, art. 8):</p>
            <ul className="list-disc pl-6 space-y-2 marker:text-gray-400">
              <li><strong>Conocer, actualizar y rectificar</strong> tus datos, incluso si están incompletos o son inexactos.</li>
              <li><strong>Pedir prueba</strong> de la autorización que nos diste.</li>
              <li><strong>Saber cómo hemos usado</strong> tus datos, si nos lo preguntas.</li>
              <li>
                <strong>Revocar la autorización y pedir que borremos</strong> tus datos. No procede si tienes un deber
                legal o contractual de permanecer en la base de datos. Como no podemos prestarte el servicio sin tus
                datos, revocar la autorización implica cerrar tu cuenta.
              </li>
              <li><strong>Acceder gratis</strong> a tus datos.</li>
              <li>
                <strong>Presentar quejas</strong> ante la Superintendencia de Industria y Comercio (SIC), después de
                haber hecho tu consulta o reclamo ante nosotros (Ley 1581, art. 16).
              </li>
            </ul>
          </Seccion>

          <Seccion id="ejercer-derechos">
            <p>
              Escríbenos a <CorreoDatos /> desde el correo de tu
              cuenta, para comprobar que eres tú sin pedirte más datos. También pueden hacerlo tus causahabientes o tu
              representante, demostrando esa calidad.
            </p>

            <h3 className="text-lg font-semibold text-gray-950 pt-2">Consultas</h3>
            <p>
              Si quieres saber qué datos tenemos o cómo los usamos, te respondemos en máximo{" "}
              <strong>10 días hábiles</strong> desde que recibimos tu mensaje. Si no alcanzamos, te avisamos el motivo
              y te respondemos en máximo <strong>5 días hábiles más</strong> (Ley 1581, art. 14).
            </p>

            <h3 className="text-lg font-semibold text-gray-950 pt-2">Reclamos</h3>
            <p>
              Si quieres corregir, actualizar o borrar tus datos, revocar la autorización o denunciar un
              incumplimiento (Ley 1581, art. 15):
            </p>
            <ol className="list-decimal pl-6 space-y-2 marker:font-semibold marker:text-gray-950">
              <li>Incluye tu nombre, el correo de tu cuenta, qué pides y por qué, y los documentos que quieras aportar.</li>
              <li>
                Si falta algo, te lo pedimos dentro de los <strong>5 días</strong> siguientes. Si en{" "}
                <strong>2 meses</strong> no lo envías, entenderemos que desististe del reclamo.
              </li>
              <li>
                En máximo <strong>2 días hábiles</strong> marcamos tus datos con la nota “reclamo en trámite” hasta
                resolverlo.
              </li>
              <li>
                Te respondemos en máximo <strong>15 días hábiles</strong>. Si no alcanzamos, te avisamos el motivo y te
                respondemos en máximo <strong>8 días hábiles más</strong>.
              </li>
            </ol>
          </Seccion>

          <Seccion id="encargados">
            <p>
              No compartimos tus datos con terceros para que los usen para sus propios fines. Los usan, solo por cuenta
              nuestra y para lo descrito en la sección 5, estos encargados:
            </p>
            <ul className="list-none p-0 m-0">
              <Fila titulo="Google LLC (servicio de correo Gmail)">
                Envía tus códigos de verificación y el correo de bienvenida (recibe tu nombre y tu correo). Sus
                servidores pueden estar fuera de Colombia.
              </Fila>
              <Fila titulo={<PorDefinir>proveedor donde se alojen la API y la base de datos</PorDefinir>}>
                Guarda la base de datos y hace funcionar la plataforma. Ubicación de sus servidores:{" "}
                <PorDefinir>país</PorDefinir>.
              </Fila>
            </ul>
            <p>
              Al aceptar esta política autorizas que tus datos se transmitan a esos encargados aunque sus servidores
              estén fuera de Colombia, solo para las finalidades de la sección 5 (Ley 1581, art. 26; Decreto 1377,
              arts. 24 y 25).
            </p>
          </Seccion>

          <Seccion id="seguridad">
            <ul className="list-disc pl-6 space-y-2 marker:text-gray-400">
              <li>Las contraseñas se guardan solo como hash bcrypt: nadie del equipo puede verlas.</li>
              <li>Los códigos de verificación vencen a los 10 minutos y se bloquean después de 5 intentos fallidos.</li>
              <li>Limitamos la cantidad de intentos de inicio de sesión y de registro por minuto.</li>
              <li>Los correos se envían por una conexión cifrada que verifica la identidad del servidor de correo.</li>
              <li>Las mascotas que no están en adopción solo las puede ver su dueño.</li>
              <li>Los registros técnicos del servidor no guardan correos ni códigos.</li>
            </ul>
            <p>
              Ningún sistema es 100 % seguro. Si ocurre un incidente que afecte tus datos, te avisaremos y lo
              informaremos a la SIC como lo exige la ley.
            </p>
          </Seccion>

          <Seccion id="conservacion">
            <ul className="list-none p-0 m-0">
              <Fila titulo="Tu cuenta">
                Mientras esté activa. Si pides borrarla, eliminamos tus datos en el plazo de respuesta del reclamo
                (sección 8), salvo lo que la ley nos obligue a conservar.
              </Fila>
              <Fila titulo="Prueba de tu autorización (fecha y versión)">
                <PorDefinir>cuánto tiempo después de cerrar la cuenta</PorDefinir>.
              </Fila>
              <Fila titulo="Tus solicitudes de adopción y mensajes de contacto">
                Mientras tu cuenta exista o hasta que pidas borrarlos.
              </Fila>
              <Fila titulo="Un registro que no terminaste">
                Tus datos y el código se guardan solo en la memoria temporal del servidor, dejan de servir a los 10
                minutos y nunca llegan a la base de datos.
              </Fila>
              <Fila titulo="Cuentas inactivas">
                <PorDefinir>si se borran tras un tiempo sin uso</PorDefinir>.
              </Fila>
            </ul>
            <p>
              Solo guardamos los datos el tiempo razonable y necesario para la finalidad (Decreto 1377, art. 11).
            </p>
          </Seccion>

          <Seccion id="menores">
            <p>
              PetConnect es para <strong>mayores de 18 años</strong>. Al registrarte declaras que lo eres. Si eres
              menor de edad, pide a tu madre, padre o representante legal que use la plataforma por ti.
            </p>
          </Seccion>

          <Seccion id="cambios">
            <p>
              Si cambiamos esta política, publicaremos la versión nueva con su fecha <strong>antes</strong> de
              aplicarla y te avisaremos por correo. Si el cambio afecta para qué usamos tus datos, te pediremos de
              nuevo la autorización (Decreto 1377, art. 13).
            </p>
          </Seccion>

          <Seccion id="vigencia">
            <dl className="grid grid-cols-[9rem_1fr] gap-x-4 gap-y-2">
              <dt className="font-semibold text-gray-950">Versión</dt>
              <dd>{VERSION_POLITICA}</dd>
              <dt className="font-semibold text-gray-950">Vigente desde</dt>
              <dd><PorDefinir>fecha de publicación</PorDefinir></dd>
            </dl>
            <p>Las bases de datos estarán vigentes mientras PetConnect preste el servicio.</p>
          </Seccion>
        </article>
      </div>
    </main>
  );
}
