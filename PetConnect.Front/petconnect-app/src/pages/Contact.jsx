import { useState } from "react";
import { Mail, Phone, MapPin, CheckCircle } from "lucide-react";

export default function Contact() {
  const [submitted, setSubmitted] = useState(false);
  const [form, setForm] = useState({
    name: "",
    email: "",
    message: "",
  });

  const handleChange = (e) =>
    setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = (e) => {
    e.preventDefault();
    setSubmitted(true);
  };

  if (submitted) {
    return (
      <main className="max-w-lg mx-auto px-4 py-20 text-center">
        <CheckCircle className="w-16 h-16 text-green-600 mx-auto mb-6" />
        <h1 className="text-2xl font-bold mb-3">Mensaje Enviado</h1>
        <p className="text-gray-500 mb-8">
          Gracias por contactarnos. Responderemos tu mensaje lo antes posible.
        </p>
        <button
          onClick={() => {
            setSubmitted(false);
            setForm({ name: "", email: "", message: "" });
          }}
          className="bg-black text-white px-6 py-3 rounded-lg font-medium hover:bg-gray-800 transition-colors"
        >
          Enviar otro mensaje
        </button>
      </main>
    );
  }

  return (
    <main className="page-enter max-w-5xl mx-auto px-4 py-8">
      <div className="text-center mb-10">
        <h1 className="text-2xl md:text-3xl font-bold mb-3">Contacto</h1>
        <p className="text-gray-500 max-w-xl mx-auto">
          ¿Tienes alguna pregunta o sugerencia? Escríbenos y te responderemos lo
          antes posible.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="contact-name" className="block text-sm font-medium mb-1">
              Nombre
            </label>
            <input
              id="contact-name"
              name="name"
              value={form.name}
              onChange={handleChange}
              required
              className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:border-black"
              placeholder="Tu nombre"
            />
          </div>

          <div>
            <label htmlFor="contact-email" className="block text-sm font-medium mb-1">
              Correo electrónico
            </label>
            <input
              id="contact-email"
              name="email"
              type="email"
              value={form.email}
              onChange={handleChange}
              required
              className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:border-black"
              placeholder="tu@correo.com"
            />
          </div>

          <div>
            <label htmlFor="contact-message" className="block text-sm font-medium mb-1">
              Mensaje
            </label>
            <textarea
              id="contact-message"
              name="message"
              value={form.message}
              onChange={handleChange}
              required
              rows={5}
              className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:border-black resize-none"
              placeholder="Escribe tu mensaje..."
            />
          </div>

          <button
            type="submit"
            className="btn-hover btn-ripple w-full bg-black text-white py-3 rounded-lg font-medium hover:bg-gray-800 transition-colors"
          >
            Enviar Mensaje
          </button>
        </form>

        <div className="space-y-6">
          <h2 className="text-lg font-semibold">Información de contacto</h2>

          <div className="flex items-start gap-3">
            <Mail className="w-5 h-5 text-black mt-0.5" />
            <div>
              <p className="text-sm font-medium">Correo electrónico</p>
              <p className="text-sm text-gray-500">info@petconnect.com</p>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <Phone className="w-5 h-5 text-black mt-0.5" />
            <div>
              <p className="text-sm font-medium">Teléfono</p>
              <p className="text-sm text-gray-500">+57 300 123 4567</p>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <MapPin className="w-5 h-5 text-black mt-0.5" />
            <div>
              <p className="text-sm font-medium">Ubicación</p>
              <p className="text-sm text-gray-500">Bogotá, Colombia</p>
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
