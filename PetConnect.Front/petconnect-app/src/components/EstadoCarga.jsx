import { Inbox, LoaderCircle, RotateCw, TriangleAlert } from "lucide-react";

// Ítem 3.3 (A-23, NC-009): antes, si la API fallaba, la web mostraba mascotas y
// productos inventados. Ahora cada página muestra uno de estos tres estados:
//   - "cargando": mientras llega la respuesta (role="status": el lector de
//     pantalla lo anuncia sin interrumpir).
//   - "error": la API no respondió (role="alert") + botón "Reintentar".
//   - "vacio": la API respondió bien, pero no hay nada que mostrar.
// "accion" es opcional: un enlace extra, por ejemplo "Volver a adopción".
// "encabezado" es opcional: "h1" cuando el estado ocupa toda la página (las
// fichas), para que la página siga teniendo su título principal.
const ESTILOS = {
  cargando: "border-gray-200 bg-white text-gray-600",
  error: "border-red-200 bg-red-50 text-red-900",
  vacio: "border-gray-200 bg-gray-50 text-gray-700",
};

const ICONOS = { cargando: LoaderCircle, error: TriangleAlert, vacio: Inbox };

export default function EstadoCarga({ tipo, titulo, children, onReintentar, accion, encabezado }) {
  const Icono = ICONOS[tipo];
  const Titulo = encabezado ?? "p";

  return (
    <div
      role={tipo === "error" ? "alert" : "status"}
      className={`mx-auto flex max-w-md flex-col items-center gap-3 rounded-lg border px-5 py-10 text-center ${ESTILOS[tipo]}`}
    >
      <Icono
        className={`h-8 w-8 ${tipo === "cargando" ? "motion-safe:animate-spin" : ""}`}
        aria-hidden="true"
      />
      <Titulo className="font-semibold">{titulo}</Titulo>
      {children && <p className="text-sm">{children}</p>}
      {(onReintentar || accion) && (
        <div className="mt-2 flex flex-wrap justify-center gap-3">
          {onReintentar && (
            <button
              type="button"
              onClick={onReintentar}
              className="inline-flex min-h-11 items-center gap-2 rounded-lg bg-black px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-gray-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-black"
            >
              <RotateCw className="h-4 w-4" aria-hidden="true" />
              Reintentar
            </button>
          )}
          {accion}
        </div>
      )}
    </div>
  );
}
