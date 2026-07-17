import { useState, useEffect } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { ArrowLeft, Check, X as XIcon, Heart } from "lucide-react";
import { pets as staticPets } from "../data/pets";
import { getMascota } from "../services/api";

export default function PetDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [pet, setPet] = useState(null);
  const [notFound, setNotFound] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [form, setForm] = useState({
    name: "",
    email: "",
    phone: "",
    message: "",
  });

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

  const handleChange = (e) =>
    setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = (e) => {
    e.preventDefault();
    setSubmitted(true);
    setShowForm(false);
  };

  if (submitted) {
    return (
      <main className="max-w-lg mx-auto px-4 py-20 text-center">
        <Heart className="w-16 h-16 text-black mx-auto mb-6" />
        <h1 className="text-2xl font-bold mb-3">Solicitud Enviada</h1>
        <p className="text-gray-500 mb-8">
          Tu solicitud de adopción para <strong>{pet.name}</strong> ha sido
          enviada. Nos pondremos en contacto contigo pronto.
        </p>
        <button
          onClick={() => navigate("/adopcion")}
          className="bg-black text-white px-6 py-3 rounded-lg font-medium hover:bg-gray-800 transition-colors"
        >
          Ver más mascotas
        </button>
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
              onSubmit={handleSubmit}
              className="space-y-4 border border-gray-200 rounded-lg p-4"
            >
              <h3 className="font-semibold">Formulario de Adopción</h3>
              <div>
                <label htmlFor="adopt-name" className="block text-sm font-medium mb-1">
                  Nombre completo
                </label>
                <input
                  id="adopt-name"
                  name="name"
                  value={form.name}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:border-black"
                />
              </div>
              <div>
                <label htmlFor="adopt-email" className="block text-sm font-medium mb-1">
                  Correo electrónico
                </label>
                <input
                  id="adopt-email"
                  name="email"
                  type="email"
                  value={form.email}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:border-black"
                />
              </div>
              <div>
                <label htmlFor="adopt-phone" className="block text-sm font-medium mb-1">
                  Teléfono
                </label>
                <input
                  id="adopt-phone"
                  name="phone"
                  type="tel"
                  value={form.phone}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:border-black"
                />
              </div>
              <div>
                <label htmlFor="adopt-message" className="block text-sm font-medium mb-1">
                  ¿Por qué quieres adoptar a {pet.name}?
                </label>
                <textarea
                  id="adopt-message"
                  name="message"
                  value={form.message}
                  onChange={handleChange}
                  required
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:border-black resize-none"
                />
              </div>
              <div className="flex gap-3">
                <button
                  type="submit"
                  className="flex-1 bg-black text-white py-2.5 rounded-lg font-medium hover:bg-gray-800 transition-colors"
                >
                  Enviar Solicitud
                </button>
                <button
                  type="button"
                  onClick={() => setShowForm(false)}
                  className="px-4 py-2.5 border border-gray-300 rounded-lg text-sm hover:bg-gray-100 transition-colors"
                >
                  Cancelar
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </main>
  );
}
