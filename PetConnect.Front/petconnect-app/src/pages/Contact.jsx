import { Mail, MapPin } from "lucide-react";
import AvisoDemo from "../components/AvisoDemo";

// Correo de atención de la política de datos (D.1). Si cambia, cambiarlo también en
// AvisoDemo.jsx, PoliticaDatos.jsx, RegisterModal.jsx, el móvil y el borrador .md.
const CORREO_ATENCION = "proyectopetconnect+atencion@gmail.com";

// Clases de los campos bloqueados del formulario demo (3.2): no se puede escribir en ellos.
const CAMPO_DEMO =
  "w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm bg-gray-50 cursor-not-allowed";

export default function Contact() {
  return (
    <main className="page-enter max-w-5xl mx-auto px-4 py-8">
      <div className="text-center mb-10">
        <h1 className="text-2xl md:text-3xl font-bold mb-3">Contacto</h1>
        <p className="text-gray-500 max-w-xl mx-auto">
          ¿Tienes alguna pregunta o sugerencia? Escríbenos a nuestro correo de
          atención.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
        {/* 3.2 (A-21): el formulario todavía no envía nada a la API. Los campos van
            bloqueados para no recoger datos personales que nadie recibe. */}
        <form onSubmit={(e) => e.preventDefault()} className="space-y-4 min-w-0">
          <AvisoDemo
            id="contact-demo"
            titulo="Demo — el mensaje no se envía"
            invitacion="Para escribirnos, usa el correo"
          >
            Este formulario es una muestra y no se puede llenar.
          </AvisoDemo>

          <fieldset disabled aria-describedby="contact-demo" className="min-w-0 space-y-4">
            <div>
              <label htmlFor="contact-name" className="block text-sm font-medium mb-1">
                Nombre
              </label>
              <input
                id="contact-name"
                name="name"
                className={CAMPO_DEMO}
                placeholder="Tu nombre"
              />
            </div>

            <div>
              <label htmlFor="contact-email" className="block text-sm font-medium mb-1">
                Correo electrónico
              </label>
              <input
                id="contact-email"
                name="email"
                type="email"
                className={CAMPO_DEMO}
                placeholder="tu@correo.com"
              />
            </div>

            <div>
              <label htmlFor="contact-message" className="block text-sm font-medium mb-1">
                Mensaje
              </label>
              <textarea
                id="contact-message"
                name="message"
                rows={5}
                className={`${CAMPO_DEMO} resize-none`}
                placeholder="Escribe tu mensaje..."
              />
            </div>
          </fieldset>

          <button
            type="submit"
            disabled
            className="w-full min-h-11 bg-gray-200 text-gray-700 py-3 rounded-lg font-medium cursor-not-allowed"
          >
            Envío no disponible (demo)
          </button>
        </form>

        <div className="space-y-6 min-w-0">
          <h2 className="text-lg font-semibold">Información de contacto</h2>

          <div className="flex items-start gap-3">
            <Mail className="w-5 h-5 text-black mt-0.5 shrink-0" aria-hidden="true" />
            <div className="min-w-0">
              <p className="text-sm font-medium">Correo de atención</p>
              <a
                href={`mailto:${CORREO_ATENCION}`}
                className="text-sm text-gray-700 underline hover:no-underline break-all"
              >
                {CORREO_ATENCION}
              </a>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <MapPin className="w-5 h-5 text-black mt-0.5 shrink-0" aria-hidden="true" />
            <div>
              <p className="text-sm font-medium">Ubicación</p>
              <p className="text-sm text-gray-500">Armenia, Quindío, Colombia</p>
            </div>
          </div>

          <div className="mt-6 p-5 bg-gray-50 border border-gray-200 rounded-lg">
            <h3 className="text-sm font-semibold mb-2">Horario de atención</h3>
            <p className="text-sm text-gray-500">
              Lunes a Viernes: 8:00 AM - 6:00 PM
            </p>
            <p className="text-sm text-gray-500">
              Sábados: 9:00 AM - 2:00 PM
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}
