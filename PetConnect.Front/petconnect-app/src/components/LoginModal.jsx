import { useState, useRef } from "react";
import { X } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import CasillaAutorizacion from "./CasillaAutorizacion";

// Ítem 3.5 (A-20, R05): las cuentas sin autorización vigente (creadas antes del 3.1
// o que aceptaron otra versión de la política) deben marcar la casilla para entrar.
// Textos de B.3 en Documentacion/Legal/POLITICA-TRATAMIENTO-DATOS-v1.0-BORRADOR.md.
const MENSAJE_SIN_AUTORIZACION = "Para continuar debes autorizar el tratamiento de tus datos personales.";
// Correo de atención del proyecto (D.1); el mismo de PoliticaDatos.jsx y AvisoDemo.jsx
const CORREO_ATENCION = "proyectopetconnect+atencion@gmail.com";

export default function LoginModal() {
  const {
    showLogin,
    setShowLogin,
    login,
    verifyLoginCode,
    pendingLoginEmail,
    setPendingLoginEmail,
    openRegister,
    authError,
    setAuthError,
  } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);
  // Ítem 3.5: avisoAutorizacion guarda el mensaje del 403 de la API; si no está
  // vacío, el modal muestra el paso "Autoriza el uso de tus datos".
  const [avisoAutorizacion, setAvisoAutorizacion] = useState("");
  const [aceptaDatos, setAceptaDatos] = useState(false);   // empieza SIN marcar
  const aceptaRef = useRef(null);

  if (!showLogin) return null;

  // La API pidió la autorización: se muestra la casilla sin marcar. El correo y
  // la contraseña siguen en el estado para repetir el inicio de sesión con ella.
  const pedirAutorizacion = (err) => {
    setAuthError(null);
    setAceptaDatos(false);
    setAvisoAutorizacion(err.message);
  };

  // Salir del paso de la casilla sin autorizar: se olvida la contraseña escrita.
  const salirDeAutorizacion = () => {
    setAuthError(null);
    setAceptaDatos(false);
    setAvisoAutorizacion("");
    setPassword("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login(email, password);
    } catch (err) {
      if (err.requiereAutorizacion) pedirAutorizacion(err);
      else setAuthError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAutorizar = async (e) => {
    e.preventDefault();
    // Sin la casilla no se llama a la API (y la API respondería 403 igual)
    if (!aceptaDatos) {
      setAuthError(MENSAJE_SIN_AUTORIZACION);
      aceptaRef.current?.focus();
      return;
    }
    setLoading(true);
    try {
      await login(email, password, true);
      // La autorización se guarda solo cuando el código sea correcto (/login/verify)
      setAvisoAutorizacion("");
      setAceptaDatos(false);
    } catch (err) {
      setAuthError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await verifyLoginCode(pendingLoginEmail, code);
      setEmail("");
      setPassword("");
      setCode("");
    } catch (err) {
      // La versión de la política pudo cambiar mientras llegaba el código:
      // la API vuelve a pedir la casilla y no entrega el token.
      if (err.requiereAutorizacion) {
        setPendingLoginEmail(null);
        setCode("");
        pedirAutorizacion(err);
      } else {
        setAuthError(err.message);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setShowLogin(false);
    setPendingLoginEmail(null);
    setCode("");
  };

  const handleCloseAutorizacion = () => {
    salirDeAutorizacion();
    setShowLogin(false);
  };

  if (pendingLoginEmail) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div className="absolute inset-0 bg-black/40 backdrop-fade" onClick={handleClose} />
        <div className="modal-enter relative bg-white rounded-xl shadow-xl w-full max-w-sm p-6">
          <button
            onClick={handleClose}
            className="absolute top-4 right-4 p-1 hover:bg-gray-100 rounded-full"
            aria-label="Cerrar"
          >
            <X className="w-5 h-5" />
          </button>

          <h2 className="text-xl font-bold mb-2 text-center">Verificar inicio de sesión</h2>
          <p className="text-sm text-gray-500 text-center mb-6">
            Ingresa el código de 6 dígitos que enviamos a{" "}
            <span className="font-medium text-gray-800">{pendingLoginEmail}</span>
          </p>

          {authError && (
            <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2 mb-4 text-center">
              {authError}
            </p>
          )}

          <form onSubmit={handleVerify} className="space-y-4">
            <input
              type="text"
              inputMode="numeric"
              maxLength={6}
              value={code}
              onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
              required
              autoFocus
              className="w-full px-3 py-3 border border-gray-300 rounded-lg text-center text-2xl font-bold tracking-widest focus:outline-none focus:border-black"
              placeholder="------"
            />

            <button
              type="submit"
              disabled={loading || code.length !== 6}
              className="w-full bg-black text-white py-2.5 rounded-lg font-medium hover:bg-gray-800 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {loading ? "Verificando..." : "Confirmar código"}
            </button>
          </form>

          <p className="text-center text-sm text-gray-500 mt-4">
            ¿No recibiste el código?{" "}
            <button
              onClick={() => { setAuthError(null); setPendingLoginEmail(null); setCode(""); }}
              className="text-black font-medium hover:underline"
            >
              Volver e intentar de nuevo
            </button>
          </p>
        </div>
      </div>
    );
  }

  if (avisoAutorizacion) {
    return (
      // overflow-y-auto + min-h-full: a 375 px el paso es alto y debe poder desplazarse
      <div className="fixed inset-0 z-50 overflow-y-auto">
        <div className="fixed inset-0 bg-black/40 backdrop-fade" onClick={handleCloseAutorizacion} />
        <div
          className="relative flex min-h-full items-center justify-center p-4"
          onClick={(e) => e.target === e.currentTarget && handleCloseAutorizacion()}
        >
          <div className="modal-enter relative bg-white rounded-xl shadow-xl w-full max-w-sm p-6">
            <button
              onClick={handleCloseAutorizacion}
              className="absolute top-4 right-4 p-1 hover:bg-gray-100 rounded-full"
              aria-label="Cerrar"
            >
              <X className="w-5 h-5" />
            </button>

            <h2 className="text-xl font-bold mb-2 text-center">Autoriza el uso de tus datos</h2>
            {/* Mensaje del 403 de la API (B.3) */}
            <p className="text-sm text-gray-600 text-center mb-6">{avisoAutorizacion}</p>

            {authError && (
              <p role="alert" className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2 mb-4 text-center">
                {authError}
              </p>
            )}

            <form onSubmit={handleAutorizar} className="space-y-4">
              <CasillaAutorizacion
                ref={aceptaRef}
                id="login-acepta"
                name="aceptaDatos"
                checked={aceptaDatos}
                onChange={(e) => setAceptaDatos(e.target.checked)}
              />

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-black text-white py-2.5 rounded-lg font-medium hover:bg-gray-800 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                {loading ? "Enviando código..." : "Autorizar y continuar"}
              </button>
              <button
                type="button"
                onClick={salirDeAutorizacion}
                className="w-full min-h-11 border border-gray-300 bg-white text-black py-2.5 rounded-lg text-sm font-medium transition-colors hover:bg-gray-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-black"
              >
                Cancelar
              </button>
            </form>

            {/* B.3: si no autoriza, puede pedir que se borre su cuenta (proceso manual, C.8) */}
            <p className="mt-5 pt-4 border-t border-gray-100 text-sm leading-relaxed text-gray-600">
              Si no quieres autorizarlo, escríbenos a{" "}
              <a
                href={`mailto:${CORREO_ATENCION}`}
                className="break-words font-medium text-black underline underline-offset-2 hover:text-gray-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-black"
              >
                {CORREO_ATENCION}
              </a>{" "}
              y borraremos tu cuenta.
            </p>
          </div>
        </div>
      </div>
    );
  }

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
