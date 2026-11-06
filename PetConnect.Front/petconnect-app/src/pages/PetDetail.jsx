import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft, Check, X as XIcon, Heart } from "lucide-react";
import { getMascota } from "../services/api";
import AvisoDemo from "../components/AvisoDemo";
import EstadoCarga from "../components/EstadoCarga";

// Clases de los campos bloqueados del formulario demo (3.2): no se puede escribir en ellos.
const CAMPO_DEMO =
  "w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-gray-50 cursor-not-allowed";

const VOLVER_ADOPCION = (
  <Link
    to="/adopcion"
    className="inline-flex min-h-11 items-center gap-1 rounded-lg border border-gray-300 px-5 py-2.5 text-sm font-medium text-black no-underline hover:bg-gray-100 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-black"
  >
    <ArrowLeft className="w-4 h-4" aria-hidden="true" />
    Volver a adopción
  </Link>
);

export default function PetDetail() {
  const { id } = useParams();
  const [pet, setPet] = useState(null);
  // 3.3 (A-23): "no-encontrada" solo si la API respondió 404 (no existe o no
  // está en adopción, ítem 2.9). Cualquier otro fallo (503 BD caída, 502 API
  // apagada, 0 sin conexión) es "error". Antes, si la API fallaba, se mostraba
  // una mascota inventada de data/pets.js con su formulario de adopción.
  const [estado, setEstado] = useState("cargando"); // "cargando" | "no-encontrada" | "error" | "listo"
  const [intento, setIntento] = useState(0); // al sumar 1, se vuelve a pedir la ficha
  const [showForm, setShowForm] = useState(false);

  useEffect(() => {
    let vigente = true; // evita actualizar la página si el usuario ya se fue
    getMascota(id)
      .then((data) => {
        if (!vigente) return;
        setPet(data);
        setEstado("listo");
      })
      .catch((e) => {
        if (vigente) setEstado(e.status === 404 ? "no-encontrada" : "error");
      });
    return () => {
      vigente = false;
    };
  }, [id, intento]);

  function reintentar() {
    setEstado("cargando");
    setIntento((n) => n + 1);
  }

  if (estado !== "listo") {
    return (
      <main className="max-w-7xl mx-auto px-4 py-16">
        {estado === "cargando" && (
          <EstadoCarga tipo="cargando" encabezado="h1" titulo="Cargando información de la mascota…" />
        )}
        {estado === "no-encontrada" && (
          <EstadoCarga tipo="vacio" encabezado="h1" titulo="Mascota no encontrada" accion={VOLVER_ADOPCION}>
            Puede que ya haya sido adoptada o que ya no esté disponible.
          </EstadoCarga>
        )}
        {estado === "error" && (
          <EstadoCarga
            tipo="error"
            encabezado="h1"
            titulo="No pudimos cargar la información de esta mascota"
            onReintentar={reintentar}
            accion={VOLVER_ADOPCION}
          >
            Revisa tu conexión o inténtalo de nuevo en unos minutos.
          </EstadoCarga>
        )}
      </main>
    );
  }

  return (
    <main className="page-enter max-w-7xl mx-auto px-4 py-8">
      <Link
        to="/adopcion"
        className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-black no-underline mb-6"
      >
        <ArrowLeft className="w-4 h-4" />
        Volver a adopción
      </Link>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <img
          src={pet.image}
          alt={pet.name}
          className="w-full aspect-square object-cover rounded-lg border border-gray-200"
        />

        <div>
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-2xl md:text-3xl font-bold">{pet.name}</h1>
            <span className="text-sm bg-gray-100 text-gray-600 px-3 py-1 rounded">
              {pet.species}
            </span>
          </div>

          <p className="text-gray-500 mb-4">
            {pet.breed} &middot; {pet.age} &middot; {pet.gender} &middot;{" "}
            {pet.size}
          </p>

          <p className="text-gray-600 leading-relaxed mb-6">{pet.description}</p>

          <div className="space-y-2 mb-8">
            <div className="flex items-center gap-2 text-sm">
              {pet.vaccinated ? (
                <Check className="w-4 h-4 text-green-600" />
              ) : (
                <XIcon className="w-4 h-4 text-red-500" />
              )}
              <span>{pet.vaccinated ? "Vacunado/a" : "Pendiente de vacunación"}</span>
            </div>
            <div className="flex items-center gap-2 text-sm">
              {pet.sterilized ? (
                <Check className="w-4 h-4 text-green-600" />
              ) : (
                <XIcon className="w-4 h-4 text-red-500" />
              )}
              <span>
                {pet.sterilized ? "Esterilizado/a" : "Pendiente de esterilización"}
              </span>
            </div>
          </div>

          {!showForm ? (
            <button
              onClick={() => setShowForm(true)}
              className="w-full md:w-auto flex items-center justify-center gap-2 bg-black text-white px-8 py-3 rounded-lg font-medium hover:bg-gray-800 transition-colors"
            >
              <Heart className="w-5 h-5" />
              Solicitar Adopción
            </button>
          ) : (
            <form
              onSubmit={(e) => e.preventDefault()}
              className="space-y-4 border border-gray-200 rounded-lg p-4"
            >
              <h3 className="font-semibold">Formulario de Adopción</h3>
              {/* 3.2 (A-21): las solicitudes todavía no se envían a la API. Los campos van
                  bloqueados para no recoger datos personales que nadie recibe. */}
              <AvisoDemo
                id="adopt-demo"
                titulo="Demo — la solicitud no se envía"
                invitacion={`Si te interesa adoptar a ${pet.name}, escríbenos a`}
              >
                Por ahora las solicitudes de adopción no están disponibles: este
                formulario es una muestra y no se puede llenar.
              </AvisoDemo>
              <fieldset disabled aria-describedby="adopt-demo" className="min-w-0 space-y-4">
                <div>
                  <label htmlFor="adopt-name" className="block text-sm font-medium mb-1">
                    Nombre completo
                  </label>
                  <input id="adopt-name" name="name" className={CAMPO_DEMO} />
                </div>
                <div>
                  <label htmlFor="adopt-email" className="block text-sm font-medium mb-1">
                    Correo electrónico
                  </label>
                  <input id="adopt-email" name="email" type="email" className={CAMPO_DEMO} />
                </div>
                <div>
                  <label htmlFor="adopt-phone" className="block text-sm font-medium mb-1">
                    Teléfono
                  </label>
                  <input id="adopt-phone" name="phone" type="tel" className={CAMPO_DEMO} />
                </div>
                <div>
                  <label htmlFor="adopt-message" className="block text-sm font-medium mb-1">
                    ¿Por qué quieres adoptar a {pet.name}?
                  </label>
                  <textarea
                    id="adopt-message"
                    name="message"
                    rows={3}
                    className={`${CAMPO_DEMO} resize-none`}
                  />
                </div>
              </fieldset>
              <div className="flex flex-wrap gap-3">
                <button
                  type="submit"
                  disabled
                  className="flex-1 min-h-11 bg-gray-200 text-gray-700 py-2.5 px-4 rounded-lg font-medium cursor-not-allowed"
                >
                  No disponible (demo)
                </button>
                <button
                  type="button"
                  onClick={() => setShowForm(false)}
                  className="min-h-11 px-4 py-2.5 border border-gray-300 rounded-lg text-sm hover:bg-gray-100 transition-colors"
                >
                  Cerrar
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </main>
  );
}
