export default function Footer() {
  return (
    <footer className="bg-gray-950 text-gray-400 mt-auto">
      <div className="max-w-7xl mx-auto px-4 py-10">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div>
            <div className="flex items-center gap-2 mb-3">
              <img src="/logo.svg" alt="Pet Connect" className="w-7 h-7" />
              <span className="text-lg font-bold">
                <span className="text-[#6dd5d8]">Pet </span>
                <span className="text-[#f5a65a]">Connect</span>
              </span>
            </div>
            <p className="text-sm leading-relaxed">
              Tu tienda de confianza para productos de mascotas y adopción
              responsable.
            </p>
          </div>

          <div>
            <h4 className="text-white font-semibold mb-3 text-sm uppercase tracking-wider">
              Enlaces
            </h4>
            <ul className="space-y-2 text-sm list-none p-0 m-0">
              <li><a href="/catalogo" className="hover:text-white transition-colors no-underline text-gray-400">Catálogo</a></li>
              <li><a href="/adopcion" className="hover:text-white transition-colors no-underline text-gray-400">Adopción</a></li>
              <li><a href="/contacto" className="hover:text-white transition-colors no-underline text-gray-400">Contacto</a></li>
            </ul>
          </div>

          <div>
            <h4 className="text-white font-semibold mb-3 text-sm uppercase tracking-wider">
              Contacto
            </h4>
            <ul className="space-y-2 text-sm list-none p-0 m-0">
              <li>info@petconnect.com</li>
              <li>+57 300 123 4567</li>
              <li>Bogotá, Colombia</li>
            </ul>
          </div>
        </div>

        <div className="border-t border-gray-800 mt-8 pt-6 text-center text-sm">
          &copy; 2025 Pet Connect. Todos los derechos reservados.
        </div>
      </div>
    </footer>
  );
}
