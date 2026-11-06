import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { getMascotasAdopcion } from "../services/api";
import { Heart } from "lucide-react";
import { useScrollReveal } from "../assets/js/useScrollReveal";
import EstadoCarga from "../components/EstadoCarga";

export default function Adoption() {
  // 3.3 (A-23, NC-009): la lista sale SOLO de la API. Antes empezaba con 6
  // mascotas inventadas y, si la API fallaba o no traía nada, las dejaba en
  // pantalla (así se ocultó NC-009).
  const [pets, setPets] = useState([]);
  const [estado, setEstado] = useState("cargando"); // "cargando" | "error" | "listo"
  const [intento, setIntento] = useState(0); // al sumar 1, se vuelve a pedir la lista

  useScrollReveal();

  useEffect(() => {
    let vigente = true; // evita actualizar la página si el usuario ya se fue
    getMascotasAdopcion()
      .then((data) => {
        if (!vigente) return;
        setPets(data);
        setEstado("listo");
      })
      .catch(() => {
        if (vigente) setEstado("error");
      });
    return () => {
      vigente = false;
    };
  }, [intento]);

  function reintentar() {
    setEstado("cargando");
    setIntento((n) => n + 1);
  }

  return (
    <main className="page-enter max-w-7xl mx-auto px-4 py-8">
      <div className="text-center mb-10">
        <h1 className="hero-title text-2xl md:text-3xl font-bold mb-3">
          Mascotas en Adopción
        </h1>
        <p className="hero-subtitle text-gray-500 max-w-xl mx-auto">
          Conoce a las mascotas que buscan un hogar lleno de amor. Cada una de
          ellas merece una familia.
        </p>
      </div>

      {estado === "cargando" && (
        <EstadoCarga tipo="cargando" titulo="Cargando mascotas en adopción…" />
      )}

      {estado === "error" && (
        <EstadoCarga
          tipo="error"
          titulo="No pudimos cargar las mascotas en adopción"
          onReintentar={reintentar}
        >
          Revisa tu conexión o inténtalo de nuevo en unos minutos.
        </EstadoCarga>
      )}

      {estado === "listo" && pets.length === 0 && (
        <EstadoCarga tipo="vacio" titulo="Por ahora no hay mascotas en adopción">
          Vuelve pronto: cuando un refugio publique una mascota, aparecerá aquí.
        </EstadoCarga>
      )}

      {estado === "listo" && pets.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {pets.map((pet, i) => (
            <div
              key={pet.id}
              className={`scroll-reveal stagger-${(i % 3) + 1} card-hover border border-gray-200 rounded-lg overflow-hidden bg-white`}
            >
              <Link to={`/adopcion/${pet.id}`} className="block img-zoom">
                <img
                  src={pet.image}
                  alt={pet.name}
                  className="w-full h-56 object-cover"
                  loading="lazy"
                />
              </Link>
              <div className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <Link
                    to={`/adopcion/${pet.id}`}
                    className="link-animate text-lg font-bold text-black no-underline"
                  >
                    {pet.name}
                  </Link>
                  <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                    {pet.species}
                  </span>
                </div>
                <p className="text-sm text-gray-500 mb-1">
                  {pet.breed} &middot; {pet.age} &middot; {pet.gender}
                </p>
                <p className="text-sm text-gray-500 mb-3">{pet.size}</p>
                <Link
                  to={`/adopcion/${pet.id}`}
                  className="btn-hover w-full flex items-center justify-center gap-2 border-2 border-black text-black py-2 rounded-lg text-sm font-medium hover:bg-black hover:text-white transition-colors no-underline"
                >
                  <Heart className="w-4 h-4" />
                  Conocer más
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </main>
  );
}
