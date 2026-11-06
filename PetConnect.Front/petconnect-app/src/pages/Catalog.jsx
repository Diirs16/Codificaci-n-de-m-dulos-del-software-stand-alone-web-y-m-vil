import { useState, useEffect } from "react";
import { Search } from "lucide-react";
import ProductCard from "../components/ProductCard";
import EstadoCarga from "../components/EstadoCarga";
import { getProductos } from "../services/api";
import { useScrollReveal } from "../assets/js/useScrollReveal";

export default function Catalog() {
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("Todos");
  // 3.3 (A-23): los productos y sus categorías salen SOLO de la API. Antes, si
  // la API fallaba o no traía nada, se quedaban los 12 productos inventados.
  const [products, setProducts] = useState([]);
  const [estado, setEstado] = useState("cargando"); // "cargando" | "error" | "listo"
  const [intento, setIntento] = useState(0); // al sumar 1, se vuelve a pedir la lista

  useScrollReveal();

  useEffect(() => {
    let vigente = true; // evita actualizar la página si el usuario ya se fue
    getProductos()
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

  const categories = ["Todos", ...new Set(products.map((p) => p.category).filter(Boolean))];

  const filtered = products.filter((p) => {
    const matchesSearch = p.name.toLowerCase().includes(search.toLowerCase());
    const matchesCategory = category === "Todos" || p.category === category;
    return matchesSearch && matchesCategory;
  });

  return (
    <main className="page-enter max-w-7xl mx-auto px-4 py-8">
      <h1 className="text-2xl md:text-3xl font-bold mb-6">Catálogo de Productos</h1>

      {estado === "cargando" && <EstadoCarga tipo="cargando" titulo="Cargando productos…" />}

      {estado === "error" && (
        <EstadoCarga
          tipo="error"
          titulo="No pudimos cargar el catálogo"
          onReintentar={reintentar}
        >
          Revisa tu conexión o inténtalo de nuevo en unos minutos.
        </EstadoCarga>
      )}

      {estado === "listo" && products.length === 0 && (
        <EstadoCarga tipo="vacio" titulo="Todavía no hay productos en el catálogo">
          Vuelve pronto: aquí aparecerán los productos disponibles.
        </EstadoCarga>
      )}

      {estado === "listo" && products.length > 0 && (
        <>
          <div className="flex flex-col md:flex-row gap-4 mb-8">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Buscar productos..."
                className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:border-black transition-shadow focus:shadow-md"
                aria-label="Buscar productos"
              />
            </div>

            <div className="flex gap-2 flex-wrap">
              {categories.map((cat) => (
                <button
                  key={cat}
                  onClick={() => setCategory(cat)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                    category === cat
                      ? "bg-black text-white scale-105"
                      : "border border-gray-300 text-gray-600 hover:bg-gray-100 hover:scale-105"
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>
          </div>

          {filtered.length === 0 ? (
            <div className="text-center py-20 text-gray-500">
              <p className="text-lg">No se encontraron productos</p>
              <p className="text-sm mt-1">Intenta con otra búsqueda o categoría</p>
            </div>
          ) : (
            <>
              <p className="text-sm text-gray-500 mb-4">
                {filtered.length} producto{filtered.length !== 1 ? "s" : ""} encontrado
                {filtered.length !== 1 ? "s" : ""}
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                {filtered.map((product, i) => (
                  <div
                    key={product.id}
                    className={`scroll-reveal stagger-${(i % 4) + 1}`}
                  >
                    <ProductCard product={product} />
                  </div>
                ))}
              </div>
            </>
          )}
        </>
      )}
    </main>
  );
}
