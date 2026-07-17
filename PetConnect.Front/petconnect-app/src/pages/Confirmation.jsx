import { Link } from "react-router-dom";
import { CheckCircle } from "lucide-react";

export default function Confirmation() {
  return (
    <main className="max-w-lg mx-auto px-4 py-20 text-center">
      <CheckCircle className="w-16 h-16 text-green-600 mx-auto mb-6" />
      <h1 className="text-2xl font-bold mb-3">Pedido Confirmado</h1>
      <p className="text-gray-500 mb-8">
        Tu pedido ha sido procesado exitosamente. Recibirás un correo
        electrónico con los detalles de tu compra y la información de envío.
      </p>
      <Link
        to="/"
        className="inline-flex items-center justify-center bg-black text-white px-6 py-3 rounded-lg font-medium hover:bg-gray-800 transition-colors no-underline"
      >
        Volver al inicio
      </Link>
    </main>
  );
}
