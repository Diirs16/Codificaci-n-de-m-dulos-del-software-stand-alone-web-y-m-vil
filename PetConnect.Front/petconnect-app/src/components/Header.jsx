import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { Menu, X, ShoppingCart, User } from "lucide-react";
import { useCart } from "../context/CartContext";
import { useAuth } from "../context/AuthContext";

export default function Header() {
  const [menuOpen, setMenuOpen] = useState(false);
  const { totalItems, setIsOpen } = useCart();
  const { user, logout, openLogin } = useAuth();
  const location = useLocation();

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
                  onClick={logout}
                  className="text-sm text-gray-500 hover:text-black transition-colors"
                >
                  Salir
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
                onClick={() => {
                  logout();
                  setMenuOpen(false);
                }}
                className="py-3 text-sm text-left text-gray-500 hover:text-black"
              >
                Cerrar sesión ({user.name})
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
    </header>
  );
}
