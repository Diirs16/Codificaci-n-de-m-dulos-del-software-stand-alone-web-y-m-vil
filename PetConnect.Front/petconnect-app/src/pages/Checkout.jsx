import { useState } from "react";
import { useCart } from "../context/CartContext";
import { useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";

function formatPrice(price) {
  return new Intl.NumberFormat("es-CO", {
    style: "currency",
    currency: "COP",
    minimumFractionDigits: 0,
  }).format(price);
}

export default function Checkout() {
  const { items, totalPrice, clearCart } = useCart();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    name: "",
    address: "",
    city: "",
    phone: "",
  });

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

  const handleChange = (e) =>
    setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = (e) => {
    e.preventDefault();
    clearCart();
    navigate("/confirmacion");
  };

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
        <form onSubmit={handleSubmit} className="space-y-4">
          <h2 className="text-lg font-semibold mb-2">Datos de envío</h2>

          <div>
            <label htmlFor="checkout-name" className="block text-sm font-medium mb-1">
              Nombre completo
            </label>
            <input
              id="checkout-name"
              name="name"
              value={form.name}
              onChange={handleChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:border-black"
            />
          </div>

          <div>
            <label htmlFor="checkout-address" className="block text-sm font-medium mb-1">
              Dirección
            </label>
            <input
              id="checkout-address"
              name="address"
              value={form.address}
              onChange={handleChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:border-black"
            />
          </div>

          <div>
            <label htmlFor="checkout-city" className="block text-sm font-medium mb-1">
              Ciudad
            </label>
            <input
              id="checkout-city"
              name="city"
              value={form.city}
              onChange={handleChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:border-black"
            />
          </div>

          <div>
            <label htmlFor="checkout-phone" className="block text-sm font-medium mb-1">
              Teléfono
            </label>
            <input
              id="checkout-phone"
              name="phone"
              type="tel"
              value={form.phone}
              onChange={handleChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:border-black"
            />
          </div>

          <button
            type="submit"
            className="btn-hover btn-ripple w-full bg-black text-white py-3 rounded-lg font-medium hover:bg-gray-800 transition-colors mt-4"
          >
            Confirmar Pedido
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
