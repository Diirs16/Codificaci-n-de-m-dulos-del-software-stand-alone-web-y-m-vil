import { useState } from "react";
import { Info, Search } from "lucide-react";
import ProductCard from "../components/ProductCard";
import EstadoCarga from "../components/EstadoCarga";
import BotonVerMas from "../components/BotonVerMas";
import { useListaPaginada } from "../hooks/useListaPaginada";
import { getProductos } from "../services/api";
import { useScrollReveal } from "../assets/js/useScrollReveal";
import { POR_PAGINA_CATALOGO } from "../utils/paginacion";

export default function Catalog() {
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("Todos");
  // 3.3 (A-23): los productos y sus categorías salen SOLO de la API. Antes, si
  // la API fallaba o no traía nada, se quedaban los 12 productos inventados.
  // 4.17 (NC-003): se piden de 50 en 50 (el máximo de la API). El buscador y las
  // categorías filtran los productos YA cargados; si quedan más, un aviso lo dice.
  const {
    items: products,
    estado,
    reintentar,
    hayMas,
    verMas,
    cargandoMas,
    errorMas,
  } = useListaPaginada(getProductos, POR_PAGINA_CATALOGO);

  useScrollReveal();

  const filtrando = search.trim() !== "" || category !== "Todos";

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

          {hayMas && filtrando && (
            <p className="mt-8 flex items-start justify-center gap-2 text-center text-sm text-gray-600">
              <Info className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
              <span>
                La búsqueda revisa los {products.length} productos cargados. Pulsa «Ver más
                productos» para buscar también en el resto.
              </span>
            </p>
          )}

          <BotonVerMas
            hayMas={hayMas}
            cargando={cargandoMas}
            error={errorMas}
            onVerMas={verMas}
            texto="Ver más productos"
          />
        </>
      )}
    </main>
  );
}
