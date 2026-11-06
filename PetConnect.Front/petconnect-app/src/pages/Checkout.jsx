import { useCart } from "../context/CartContext";
import { useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import AvisoDemo from "../components/AvisoDemo";

// Clases de los campos bloqueados del formulario demo (3.2): no se puede escribir en ellos.
const CAMPO_DEMO =
  "w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-gray-50 cursor-not-allowed";

function formatPrice(price) {
  return new Intl.NumberFormat("es-CO", {
    style: "currency",
    currency: "COP",
    minimumFractionDigits: 0,
  }).format(price);
}

export default function Checkout() {
  const { items, totalPrice } = useCart();
  const navigate = useNavigate();

  if (items.length === 0) {
    return (
      <main className="max-w-2xl mx-auto px-4 py-20 text-center">
        <h1 className="text-2xl font-bold mb-4">No hay productos en el carrito</h1>
        <button
          onClick={() => navigate("/catalogo")}
          className="text-black underline hover:no-underline"
        >
          Ir al catálogo
        </button>
      </main>
    );
  }

  return (
    <main className="page-enter max-w-3xl mx-auto px-4 py-8">
      <button
        onClick={() => navigate(-1)}
        className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-black mb-6"
      >
        <ArrowLeft className="w-4 h-4" />
        Volver
      </button>

      <h1 className="text-2xl font-bold mb-8">Checkout</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* 3.2 (A-21): no hay pedidos ni pagos en la API. Los campos van bloqueados para
            no recoger datos de envío que nadie recibe, y el carrito no se vacía. */}
        <form onSubmit={(e) => e.preventDefault()} className="space-y-4 min-w-0">
          <h2 className="text-lg font-semibold mb-2">Datos de envío</h2>

          <AvisoDemo id="checkout-demo" titulo="Demo — no se procesan pedidos">
            Esta tienda es una muestra: no se crean pedidos, no se cobra nada y
            este formulario no se puede llenar. Tu carrito se conserva.
          </AvisoDemo>

          <fieldset disabled aria-describedby="checkout-demo" className="min-w-0 space-y-4">
            <div>
              <label htmlFor="checkout-name" className="block text-sm font-medium mb-1">
                Nombre completo
              </label>
              <input id="checkout-name" name="name" className={CAMPO_DEMO} />
            </div>
            <div>
              <label htmlFor="checkout-address" className="block text-sm font-medium mb-1">
                Dirección
              </label>
              <input id="checkout-address" name="address" className={CAMPO_DEMO} />
            </div>
            <div>
              <label htmlFor="checkout-city" className="block text-sm font-medium mb-1">
                Ciudad
              </label>
              <input id="checkout-city" name="city" className={CAMPO_DEMO} />
            </div>
            <div>
              <label htmlFor="checkout-phone" className="block text-sm font-medium mb-1">
                Teléfono
              </label>
              <input id="checkout-phone" name="phone" type="tel" className={CAMPO_DEMO} />
            </div>
          </fieldset>

          <button
            type="submit"
            disabled
            className="w-full min-h-11 bg-gray-200 text-gray-700 py-3 rounded-lg font-medium cursor-not-allowed mt-4"
          >
            Pedido no disponible (demo)
          </button>
        </form>

        <div>
          <h2 className="text-lg font-semibold mb-4">Resumen del pedido</h2>
          <div className="border border-gray-200 rounded-lg p-4 space-y-3">
            {items.map((item) => (
              <div key={item.id} className="flex justify-between text-sm">
                <span className="text-gray-600">
                  {item.name} x{item.quantity}
                </span>
                <span className="font-medium">
                  {formatPrice(item.price * item.quantity)}
                </span>
              </div>
            ))}
            <div className="border-t border-gray-200 pt-3 flex justify-between">
              <span className="font-semibold">Total</span>
              <span className="text-lg font-bold">{formatPrice(totalPrice)}</span>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
