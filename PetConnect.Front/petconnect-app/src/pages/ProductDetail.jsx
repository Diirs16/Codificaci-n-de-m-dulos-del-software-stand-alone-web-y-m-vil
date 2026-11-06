import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft, ShoppingCart, Check } from "lucide-react";
import { getProducto } from "../services/api";
import EstadoCarga from "../components/EstadoCarga";
import { useCart } from "../context/CartContext";
import { addRipple } from "../assets/js/rippleEffect";
import { showAddToCartToast } from "../assets/js/addToCartToast";

function formatPrice(price) {
  return new Intl.NumberFormat("es-CO", {
    style: "currency",
    currency: "COP",
    minimumFractionDigits: 0,
  }).format(price);
}

const VOLVER_CATALOGO = (
  <Link
    to="/catalogo"
    className="inline-flex min-h-11 items-center gap-1 rounded-lg border border-gray-300 px-5 py-2.5 text-sm font-medium text-black no-underline hover:bg-gray-100 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-black"
  >
    <ArrowLeft className="w-4 h-4" aria-hidden="true" />
    Volver al catálogo
  </Link>
);

export default function ProductDetail() {
  const { id } = useParams();
  const { addItem } = useCart();
  const [product, setProduct] = useState(null);
  // 3.3 (A-23): "no-encontrado" solo si la API respondió 404; cualquier otro
  // fallo es "error". Antes, si la API fallaba, se mostraba un producto
  // inventado de data/products.js que hasta se podía agregar al carrito.
  const [estado, setEstado] = useState("cargando"); // "cargando" | "no-encontrado" | "error" | "listo"
  const [intento, setIntento] = useState(0); // al sumar 1, se vuelve a pedir la ficha

  useEffect(() => {
    let vigente = true; // evita actualizar la página si el usuario ya se fue
    getProducto(id)
      .then((data) => {
        if (!vigente) return;
        setProduct(data);
        setEstado("listo");
      })
      .catch((e) => {
        if (vigente) setEstado(e.status === 404 ? "no-encontrado" : "error");
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
        {estado === "cargando" && <EstadoCarga tipo="cargando" encabezado="h1" titulo="Cargando producto…" />}
        {estado === "no-encontrado" && (
          <EstadoCarga tipo="vacio" encabezado="h1" titulo="Producto no encontrado" accion={VOLVER_CATALOGO}>
            Puede que ya no esté disponible en el catálogo.
          </EstadoCarga>
        )}
        {estado === "error" && (
          <EstadoCarga
            tipo="error"
            encabezado="h1"
            titulo="No pudimos cargar este producto"
            onReintentar={reintentar}
            accion={VOLVER_CATALOGO}
          >
            Revisa tu conexión o inténtalo de nuevo en unos minutos.
          </EstadoCarga>
        )}
      </main>
    );
  }

  return (
    <main className="page-enter max-w-7xl mx-auto px-4 py-8">
      <Link
        to="/catalogo"
        className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-black no-underline mb-6"
      >
        <ArrowLeft className="w-4 h-4" />
        Volver al catálogo
      </Link>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="relative">
          <img
            src={product.image}
            alt={product.name}
            className="w-full aspect-square object-cover rounded-lg border border-gray-200"
          />
          {product.isNew && (
            <span className="absolute top-3 left-3 bg-black text-white text-xs px-3 py-1 rounded font-medium">
              Nuevo
            </span>
          )}
          {product.discount > 0 && (
            <span className="absolute top-3 right-3 bg-red-600 text-white text-xs px-3 py-1 rounded font-medium">
              -{product.discount}%
            </span>
          )}
        </div>

        <div>
          <p className="text-sm text-gray-400 uppercase tracking-wider mb-2">
            {product.category}
          </p>
          <h1 className="text-2xl md:text-3xl font-bold mb-4">{product.name}</h1>

          <div className="flex items-baseline gap-3 mb-6">
            <span className="text-3xl font-bold">{formatPrice(product.price)}</span>
            {product.oldPrice && (
              <span className="text-lg text-gray-400 line-through">
                {formatPrice(product.oldPrice)}
              </span>
            )}
          </div>

          <p className="text-gray-600 leading-relaxed mb-6">{product.description}</p>

          <div className="flex items-center gap-2 text-sm text-gray-500 mb-6">
            <Check className="w-4 h-4 text-green-600" />
            <span>
              {product.stock > 0
                ? `${product.stock} unidades disponibles`
                : "Agotado"}
            </span>
          </div>

          <button
            onClick={(e) => {
              addRipple(e);
              addItem(product);
              showAddToCartToast(product.name);
            }}
            disabled={product.stock === 0}
            className="btn-hover btn-ripple w-full md:w-auto flex items-center justify-center gap-2 bg-black text-white px-8 py-3 rounded-lg font-medium hover:bg-gray-800 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed"
          >
            <ShoppingCart className="w-5 h-5" />
            Agregar al carrito
          </button>
        </div>
      </div>
    </main>
  );
}
