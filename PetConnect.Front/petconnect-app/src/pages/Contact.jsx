import { Mail, MapPin } from "lucide-react";
import FormularioSolicitud from "../components/FormularioSolicitud";

// Correo de atención de la política de datos (D.1). Si cambia, cambiarlo también en
// AvisoDemo.jsx, FormularioSolicitud.jsx, PoliticaDatos.jsx, CasillaAutorizacion.jsx, el móvil y el borrador .md.
const CORREO_ATENCION = "proyectopetconnect+atencion@gmail.com";

export default function Contact() {
  return (
    <main className="page-enter max-w-5xl mx-auto px-4 py-8">
      <div className="text-center mb-10">
        <h1 className="text-2xl md:text-3xl font-bold mb-3">Contacto</h1>
        <p className="text-gray-500 max-w-xl mx-auto">
          ¿Tienes alguna pregunta o sugerencia? Escríbenos con este formulario o a
          nuestro correo de atención.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
        {/* 3.6 (A-21): el mensaje se envía de verdad a la API, con la sesión iniciada
            (antes, en el 3.2, era una demo bloqueada). */}
        <div className="min-w-0">
          <FormularioSolicitud tipo="contacto" />
        </div>

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
