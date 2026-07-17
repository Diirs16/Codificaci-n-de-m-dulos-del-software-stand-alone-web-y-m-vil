import { useState } from "react";
import { X } from "lucide-react";
import { useAuth } from "../context/AuthContext";

export default function LoginModal() {
  const { showLogin, setShowLogin, login, openRegister, authError, setAuthError } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  if (!showLogin) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login(email, password);
      setEmail("");
      setPassword("");
    } catch (err) {
      setAuthError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div
        className="absolute inset-0 bg-black/40 backdrop-fade"
        onClick={() => setShowLogin(false)}
      />
      <div className="modal-enter relative bg-white rounded-xl shadow-xl w-full max-w-sm p-6">
        <button
          onClick={() => setShowLogin(false)}
          className="absolute top-4 right-4 p-1 hover:bg-gray-100 rounded-full"
          aria-label="Cerrar"
        >
          <X className="w-5 h-5" />
        </button>

        <h2 className="text-xl font-bold mb-6 text-center">Iniciar Sesión</h2>

        {authError && (
          <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2 mb-4 text-center">
            {authError}
          </p>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="login-email" className="block text-sm font-medium mb-1">
              Correo electrónico
            </label>
            <input
              id="login-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:border-black"
              placeholder="tu@correo.com"
            />
          </div>

          <div>
            <label htmlFor="login-password" className="block text-sm font-medium mb-1">
              Contraseña
            </label>
            <input
              id="login-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:border-black"
              placeholder="Tu contraseña"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="btn-hover btn-ripple w-full bg-black text-white py-2.5 rounded-lg font-medium hover:bg-gray-800 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {loading ? "Iniciando sesión..." : "Iniciar Sesión"}
          </button>
        </form>

        <p className="text-center text-sm text-gray-500 mt-4">
          ¿No tienes cuenta?{" "}
          <button
            onClick={openRegister}
            className="text-black font-medium hover:underline"
          >
            Regístrate
          </button>
        </p>
      </div>
    </div>
  );
}
