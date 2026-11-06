import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft, Check, X as XIcon, Heart } from "lucide-react";
import { pets as staticPets } from "../data/pets";
import { getMascota } from "../services/api";
import AvisoDemo from "../components/AvisoDemo";

// Clases de los campos bloqueados del formulario demo (3.2): no se puede escribir en ellos.
const CAMPO_DEMO =
  "w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-gray-50 cursor-not-allowed";

export default function PetDetail() {
  const { id } = useParams();
  const [pet, setPet] = useState(null);
  const [notFound, setNotFound] = useState(false);
  const [showForm, setShowForm] = useState(false);

  useEffect(() => {
    getMascota(id)
      .then(setPet)
      .catch(() => {
        const fallback = staticPets.find((p) => p.id === Number(id));
        if (fallback) {
          setPet(fallback);
        } else {
          setNotFound(true);
        }
      });
  }, [id]);

  if (notFound) {
    return (
      <main className="max-w-7xl mx-auto px-4 py-20 text-center">
        <h1 className="text-2xl font-bold mb-4">Mascota no encontrada</h1>
        <Link to="/adopcion" className="text-black underline hover:no-underline">
          Volver a adopción
        </Link>
      </main>
    );
  }

  if (!pet) {
    return (
      <main className="max-w-7xl mx-auto px-4 py-20 text-center text-gray-400">
        Cargando información de la mascota...
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
