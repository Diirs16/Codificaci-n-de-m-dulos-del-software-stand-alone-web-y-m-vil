import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { AlertTriangle, Menu, X, ShoppingCart, User } from "lucide-react";
import { useCart } from "../context/CartContext";
import { useAuth } from "../context/AuthContext";

export default function Header() {
  const [menuOpen, setMenuOpen] = useState(false);
  const { totalItems, setIsOpen } = useCart();
  const { user, logout, openLogin } = useAuth();
  const location = useLocation();
  // Ítem 4.13 (A-03): mientras la API responde, el botón queda desactivado
  // (decisión B1) y, si no pudo confirmar el cierre, se avisa (decisión A1).
  const [cerrando, setCerrando] = useState(false);
  const [avisoCierre, setAvisoCierre] = useState(false);

  async function salir() {
    if (cerrando) return;
    setCerrando(true);
    try {
      const resultado = await logout();
      setAvisoCierre(resultado === "sin-confirmar");
    } finally {
      setCerrando(false);
      setMenuOpen(false);
    }
  }

  const navLinks = [
    { to: "/", label: "Inicio" },
    { to: "/catalogo", label: "Catálogo" },
    { to: "/adopcion", label: "Adopción" },
    { to: "/contacto", label: "Contacto" },
  ];

  const isActive = (path) => location.pathname === path;

  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="flex items-center gap-2 no-underline">
            <img src="/logo.svg" alt="Pet Connect" className="w-9 h-9" />
            <span className="text-xl font-bold tracking-tight">
              <span className="text-[#2a7d8a]">Pet </span>
              <span className="text-[#e8733a]">Connect</span>
            </span>
          </Link>

          <nav className="hidden md:flex items-center gap-8">
            {navLinks.map((link) => (
              <Link
                key={link.to}
                to={link.to}
                className={`text-sm font-medium no-underline transition-colors pb-1 ${
                  isActive(link.to)
                    ? "text-black border-b-2 border-black"
                    : "text-gray-500 hover:text-black"
                }`}
              >
                {link.label}
              </Link>
            ))}
          </nav>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setIsOpen(true)}
              className="relative p-2 hover:bg-gray-100 rounded-full transition-colors"
              aria-label="Ver carrito"
            >
              <ShoppingCart className="w-5 h-5 text-black" />
              {totalItems > 0 && (
                <span className="cart-badge absolute -top-1 -right-1 bg-black text-white text-xs w-5 h-5 rounded-full flex items-center justify-center font-medium">
                  {totalItems}
                </span>
              )}
            </button>

            {user ? (
              <div className="hidden md:flex items-center gap-2">
                <span className="text-sm text-gray-600">{user.name.replace(/\b\w/g, c => c.toUpperCase())}</span>
                <button
                  type="button"
                  onClick={salir}
                  disabled={cerrando}
                  className="text-sm text-gray-500 hover:text-black transition-colors disabled:cursor-wait disabled:hover:text-gray-500"
                >
                  {cerrando ? "Cerrando sesión…" : "Salir"}
                </button>
              </div>
            ) : (
              <button
                onClick={openLogin}
                className="hidden md:flex items-center gap-1 p-2 hover:bg-gray-100 rounded-full transition-colors"
                aria-label="Iniciar sesión"
              >
                <User className="w-5 h-5 text-black" />
              </button>
            )}

            <button
              onClick={() => setMenuOpen(!menuOpen)}
              className="md:hidden p-2 hover:bg-gray-100 rounded-full transition-colors"
              aria-label="Menú"
            >
              {menuOpen ? (
                <X className="w-5 h-5" />
              ) : (
                <Menu className="w-5 h-5" />
              )}
            </button>
          </div>
        </div>
      </div>

      {menuOpen && (
        <div className="md:hidden border-t border-gray-200 bg-white mobile-menu-enter">
          <nav className="flex flex-col px-4 py-2">
            {navLinks.map((link) => (
              <Link
                key={link.to}
                to={link.to}
                onClick={() => setMenuOpen(false)}
                className={`mobile-menu-item py-3 text-sm font-medium no-underline border-b border-gray-100 ${
                  isActive(link.to) ? "text-black" : "text-gray-500"
                }`}
              >
                {link.label}
              </Link>
            ))}
            {user ? (
              <button
                type="button"
                onClick={salir}
                disabled={cerrando}
                className="py-3 text-sm text-left text-gray-500 hover:text-black disabled:cursor-wait disabled:hover:text-gray-500"
              >
                {cerrando ? "Cerrando sesión…" : `Cerrar sesión (${user.name})`}
              </button>
            ) : (
              <button
                onClick={() => {
                  openLogin();
                  setMenuOpen(false);
                }}
                className="py-3 text-sm text-left text-gray-500 hover:text-black"
              >
                Iniciar sesión
              </button>
            )}
          </nav>
        </div>
      )}

      {/* Aviso del ítem 4.13: la zona role="status" existe siempre para que los
          lectores de pantalla lean el mensaje cuando aparece. Se oculta solo con la
          X o al volver a iniciar sesión. */}
      <div
        role="status"
        className="pointer-events-none fixed inset-x-4 top-20 z-[60] flex justify-end sm:left-auto sm:right-5"
      >
        {avisoCierre && !user && (
          <div className="toast-enter pointer-events-auto flex w-full max-w-sm items-start gap-3 rounded-lg bg-[#111] px-4 py-3 text-sm text-white shadow-lg">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-300" aria-hidden="true" />
            <p className="flex-1">
              Cerraste sesión en este navegador, pero no pudimos confirmarlo con el
              servidor. Si usas PetConnect en otro aparato, cierra sesión también allí.
            </p>
            <button
              type="button"
              onClick={() => setAvisoCierre(false)}
              className="-my-2.5 -mr-2.5 inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-full hover:bg-white/10 focus-visible:outline-2 focus-visible:outline-white"
              aria-label="Cerrar aviso"
            >
              <X className="h-4 w-4" aria-hidden="true" />
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
