import { ChevronDown, LoaderCircle } from "lucide-react";

// Ítem 4.17 (NC-003): botón al final de un listado que se carga por páginas.
// No se muestra si ya no hay más. Mientras carga queda desactivado (un clic
// doble no pide dos veces) y, si falla, avisa sin borrar lo que ya se ve.
export default function BotonVerMas({ hayMas, cargando, error, onVerMas, texto = "Ver más" }) {
  if (!hayMas) return null;

  return (
    <div className="mt-8 flex flex-col items-center gap-3">
      {error && (
        <p role="alert" className="text-sm text-red-700">
          No pudimos cargar más. Revisa tu conexión e inténtalo de nuevo.
        </p>
      )}
      <button
        type="button"
        onClick={onVerMas}
        disabled={cargando}
        aria-busy={cargando}
        className="btn-hover inline-flex min-h-11 w-full items-center justify-center gap-2 rounded-lg border-2 border-black px-6 py-2.5 text-sm font-medium text-black transition-colors hover:bg-black hover:text-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-black disabled:cursor-wait disabled:opacity-60 disabled:hover:bg-transparent disabled:hover:text-black sm:w-auto"
      >
        {cargando ? (
          <LoaderCircle className="h-4 w-4 motion-safe:animate-spin" aria-hidden="true" />
        ) : (
          <ChevronDown className="h-4 w-4" aria-hidden="true" />
        )}
        {cargando ? "Cargando…" : texto}
      </button>
    </div>
  );
}
