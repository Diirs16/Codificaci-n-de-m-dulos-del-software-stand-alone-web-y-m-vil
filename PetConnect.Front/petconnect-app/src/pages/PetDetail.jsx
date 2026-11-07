import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft, Heart } from "lucide-react";
import { getMascota } from "../services/api";
import { datosMascota } from "../utils/mascota";
import FormularioSolicitud from "../components/FormularioSolicitud";
import EstadoCarga from "../components/EstadoCarga";

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

  const datos = datosMascota(pet);

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

          {/* 3.4 (A-22): solo raza, edad y sexo que vienen de la BD, ya formateados.
              Sin tamaño, vacunación ni esterilización: la BD no los tiene y un dato
              de salud no se inventa (antes todas salían con una ✗ de vacunas pendientes). */}
          {datos && <p className="text-gray-500 mb-4">{datos}</p>}

          <p className="text-gray-600 leading-relaxed mb-8">{pet.description}</p>

          {!showForm ? (
            <button
              type="button"
              onClick={() => setShowForm(true)}
              className="w-full md:w-auto min-h-11 flex items-center justify-center gap-2 bg-black text-white px-8 py-3 rounded-lg font-medium hover:bg-gray-800 transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-black"
            >
              <Heart className="w-5 h-5" aria-hidden="true" />
              Solicitar Adopción
            </button>
          ) : (
            // 3.6 (A-21): la solicitud se envía de verdad a la API (antes, en el 3.2,
            // el formulario era una demo bloqueada).
            <FormularioSolicitud tipo="adopcion" mascota={pet} onCerrar={() => setShowForm(false)} />
          )}
        </div>
      </div>
    </main>
  );
}
