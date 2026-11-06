import { Info } from "lucide-react";

// Correo de atención de la política de datos (D.1). Si cambia, cambiarlo también en
// PoliticaDatos.jsx, RegisterModal.jsx, Contact.jsx, el móvil y el borrador .md.
const CORREO_ATENCION = "proyectopetconnect+atencion@gmail.com";

/**
 * Aviso para los formularios que todavía NO envían nada (ítem 3.2, A-21).
 * La página debe bloquear sus campos (<fieldset disabled>) y enlazar este aviso
 * con aria-describedby={id}, para que el lector de pantalla lo lea con el formulario.
 * Si recibe "invitacion", agrega una línea con el correo de atención como alternativa real.
 */
export default function AvisoDemo({ id, titulo, children, invitacion }) {
  return (
    <div
      id={id}
      role="note"
      className="flex gap-3 rounded-lg border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900"
    >
      <Info className="mt-0.5 h-5 w-5 shrink-0" aria-hidden="true" />
      <div className="min-w-0 space-y-1">
        <p className="font-semibold">{titulo}</p>
        <p>{children}</p>
        {invitacion && (
          <p>
            {invitacion}{" "}
            <a
              href={`mailto:${CORREO_ATENCION}`}
              className="break-all font-medium text-amber-900 underline hover:no-underline"
            >
              {CORREO_ATENCION}
            </a>
            .
          </p>
        )}
      </div>
    </div>
  );
}
