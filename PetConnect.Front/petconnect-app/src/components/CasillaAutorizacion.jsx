import { ExternalLink } from "lucide-react";

// Casilla de autorización de datos (Ley 1581, arts. 9 y 12; ítems 3.1 y 3.5).
// Textos B.1 (casilla) y B.2 (aviso corto) de
// Documentacion/Legal/POLITICA-TRATAMIENTO-DATOS-v1.0-BORRADOR.md.
// Es el ÚNICO lugar de la web con este texto legal: lo usan el registro
// (RegisterModal.jsx) y el inicio de sesión de cuentas sin autorización vigente
// (LoginModal.jsx). Si cambia el texto, cambia también el .md y sube la versión
// de la política (PoliticaDatos.jsx y VERSION_POLITICA_DATOS en api.py).
//
// La casilla la controla quien la usa (checked + onChange) y debe empezar SIN
// marcar. `ref` permite mover el foco a la casilla cuando falta marcarla.
export default function CasillaAutorizacion({ id, name, checked, onChange, ref }) {
  const idAviso = `${id}-aviso`;
  return (
    <div>
      <div className="flex items-start gap-3">
        <input
          ref={ref}
          id={id}
          name={name}
          type="checkbox"
          checked={checked}
          onChange={onChange}
          aria-describedby={idAviso}
          className="mt-0.5 h-5 w-5 shrink-0 cursor-pointer accent-black focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-black"
        />
        <label htmlFor={id} className="min-h-11 text-sm leading-snug cursor-pointer">
          Soy mayor de 18 años, he leído la{" "}
          <a
            href="/politica-de-datos"
            target="_blank"
            rel="noopener noreferrer"
            className="font-medium text-black underline underline-offset-2 hover:text-gray-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-black"
          >
            Política de tratamiento de datos personales
            <ExternalLink className="inline w-3.5 h-3.5 ml-0.5 -mt-0.5" aria-hidden="true" />
            <span className="sr-only"> (se abre en una pestaña nueva)</span>
          </a>{" "}
          y autorizo a PetConnect a tratar mis datos para crear y usar mi cuenta.
        </label>
      </div>
      <p id={idAviso} className="mt-2 pl-8 text-xs leading-relaxed text-gray-600">
        Usaremos tu nombre y tu correo para crear tu cuenta y enviarte códigos de verificación.
        Puedes conocer, actualizar, rectificar o borrar tus datos y revocar este permiso
        escribiendo a{" "}
        {/* Correo de atención del proyecto (D.1, 06/11/2026); el mismo de PoliticaDatos.jsx */}
        <span className="break-words font-medium text-gray-800">proyectopetconnect+atencion@gmail.com.</span>
      </p>
    </div>
  );
}
