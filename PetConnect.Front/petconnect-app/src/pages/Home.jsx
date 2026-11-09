import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, Heart, Truck, Shield } from "lucide-react";
import ProductCard from "../components/ProductCard";
import EstadoCarga from "../components/EstadoCarga";
import { getProductos } from "../services/api";
import { useScrollReveal } from "../assets/js/useScrollReveal";
// Cuántos productos de la API se muestran en "Productos destacados".
import { POR_PAGINA_DESTACADOS } from "../utils/paginacion";

export default function Home() {
  // 3.3 (A-23): antes Home SIEMPRE usaba productos inventados de
  // data/products.js, con "descuento" y "nuevo", datos que la BD no tiene.
  // Ahora muestra los primeros productos reales de la API, en una sola sección.
  const [products, setProducts] = useState([]);
  const [estado, setEstado] = useState("cargando"); // "cargando" | "error" | "listo"
  const [intento, setIntento] = useState(0); // al sumar 1, se vuelve a pedir la lista

  useScrollReveal();

  useEffect(() => {
    let vigente = true; // evita actualizar la página si el usuario ya se fue
    // 4.17 (NC-003): pide solo los 4 que muestra. Antes pedía el catálogo entero
    // y se quedaba con los 4 primeros.
    getProductos({ pagina: 1, porPagina: POR_PAGINA_DESTACADOS })
      .then((data) => {
        if (!vigente) return;
        setProducts(data);
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
    <main className="page-enter">
      {/* Hero */}
      <section className="bg-gray-50 border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-16 md:py-24 text-center">
          <h1 className="hero-title text-3xl md:text-5xl font-bold text-black leading-tight mb-4">
            Todo para tu mascota en un solo lugar
          </h1>
          <p className="hero-subtitle text-gray-500 text-lg mb-8 max-w-2xl mx-auto">
            Encuentra los mejores productos para el cuidado de tu mascota y dale
            un hogar a quien más lo necesita con nuestro programa de adopción.
          </p>
          <div className="hero-buttons flex flex-col sm:flex-row gap-3 justify-center">
            <Link
              to="/catalogo"
              className="btn-hover btn-ripple inline-flex items-center justify-center gap-2 bg-black text-white px-6 py-3 rounded-lg font-medium hover:bg-gray-800 transition-colors no-underline"
            >
              Ver catálogo
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link
              to="/adopcion"
              className="btn-hover inline-flex items-center justify-center gap-2 border-2 border-black text-black px-6 py-3 rounded-lg font-medium hover:bg-black hover:text-white transition-colors no-underline"
            >
              Adoptar mascota
              <Heart className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="max-w-7xl mx-auto px-4 py-12">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="scroll-reveal stagger-1 card-hover flex items-start gap-4 p-5 border border-gray-200 rounded-lg">
            <Truck className="w-8 h-8 text-black flex-shrink-0" />
            <div>
              <h3 className="font-semibold text-sm mb-1">Envío rápido</h3>
              <p className="text-sm text-gray-500">
                Entrega en 24-48 horas en las principales ciudades.
              </p>
            </div>
          </div>
          <div className="scroll-reveal stagger-2 card-hover flex items-start gap-4 p-5 border border-gray-200 rounded-lg">
            <Shield className="w-8 h-8 text-black flex-shrink-0" />
            <div>
              <h3 className="font-semibold text-sm mb-1">Compra segura</h3>
              <p className="text-sm text-gray-500">
                Pagos protegidos y garantía de devolución.
              </p>
            </div>
          </div>
          <div className="scroll-reveal stagger-3 card-hover flex items-start gap-4 p-5 border border-gray-200 rounded-lg">
            <Heart className="w-8 h-8 text-black flex-shrink-0" />
            <div>
              <h3 className="font-semibold text-sm mb-1">Adopción responsable</h3>
              <p className="text-sm text-gray-500">
                Conectamos mascotas con familias amorosas.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Productos destacados (de la API; 3.3) */}
      <section className="max-w-7xl mx-auto px-4 py-10">
        <div className="scroll-reveal flex items-center justify-between mb-6">
          <h2 className="text-xl md:text-2xl font-bold">Productos destacados</h2>
          <Link
            to="/catalogo"
            className="link-animate text-sm text-gray-500 hover:text-black no-underline flex items-center gap-1"
          >
            Ver todo <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
        {estado === "cargando" && <EstadoCarga tipo="cargando" titulo="Cargando productos…" />}
        {estado === "error" && (
          <EstadoCarga
            tipo="error"
            titulo="No pudimos cargar los productos"
            onReintentar={reintentar}
          >
            Revisa tu conexión o inténtalo de nuevo en unos minutos.
          </EstadoCarga>
        )}
        {estado === "listo" && products.length === 0 && (
          <EstadoCarga tipo="vacio" titulo="Todavía no hay productos en el catálogo" />
        )}
        {estado === "listo" && products.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {products.map((product, i) => (
              <div key={product.id} className={`scroll-reveal stagger-${i + 1}`}>
                <ProductCard product={product} />
              </div>
            ))}
          </div>
        )}
      </section>

      {/* CTA Adoption */}
      <section className="max-w-7xl mx-auto px-4 py-10 mb-8">
        <div className="scroll-reveal-scale bg-gray-50 border border-gray-200 rounded-xl p-8 md:p-12 text-center">
          <h2 className="text-2xl md:text-3xl font-bold mb-3">
            Dale un hogar a quien más lo necesita
          </h2>
          <p className="text-gray-500 mb-6 max-w-lg mx-auto">
            Conoce las mascotas disponibles para adopción y cambia una vida
            para siempre.
          </p>
          <Link
            to="/adopcion"
            className="btn-hover btn-ripple inline-flex items-center gap-2 bg-black text-white px-6 py-3 rounded-lg font-medium hover:bg-gray-800 transition-colors no-underline"
          >
            Ver mascotas en adopción
            <Heart className="w-4 h-4" />
          </Link>
        </div>
      </section>
    </main>
  );
}
