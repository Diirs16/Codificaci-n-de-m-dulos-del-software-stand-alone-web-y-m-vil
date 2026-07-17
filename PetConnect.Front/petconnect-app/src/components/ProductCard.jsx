import { ShoppingCart } from "lucide-react";
import { Link } from "react-router-dom";
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

export default function ProductCard({ product }) {
  const { addItem } = useCart();

  const handleAdd = (e) => {
    addRipple(e);
    addItem(product);
    showAddToCartToast(product.name);
  };

  return (
    <div className="card-hover border border-gray-200 rounded-lg overflow-hidden bg-white">
      <Link to={`/producto/${product.id}`} className="block img-zoom">
        <div className="relative">
          <img
            src={product.image}
            alt={product.name}
            className="w-full h-48 object-cover"
            loading="lazy"
          />
          {product.isNew && (
            <span className="absolute top-2 left-2 bg-black text-white text-xs px-2 py-1 rounded font-medium cart-badge">
              Nuevo
            </span>
          )}
          {product.discount > 0 && (
            <span className="absolute top-2 right-2 bg-red-600 text-white text-xs px-2 py-1 rounded font-medium cart-badge">
              -{product.discount}%
            </span>
          )}
        </div>
      </Link>

      <div className="p-3">
        <Link
          to={`/producto/${product.id}`}
          className="link-animate text-sm font-medium text-black no-underline line-clamp-2"
        >
          {product.name}
        </Link>

        <div className="flex items-center gap-2 mt-2">
          <span className="font-bold text-black">
            {formatPrice(product.price)}
          </span>
          {product.oldPrice && (
            <span className="text-sm text-gray-400 line-through">
              {formatPrice(product.oldPrice)}
            </span>
          )}
        </div>

        <button
          onClick={handleAdd}
          className="btn-ripple w-full mt-3 flex items-center justify-center gap-2 bg-black text-white py-2 rounded-lg text-sm font-medium hover:bg-gray-800 transition-colors"
        >
          <ShoppingCart className="w-4 h-4" />
          Agregar al carrito
        </button>
      </div>
    </div>
  );
}
