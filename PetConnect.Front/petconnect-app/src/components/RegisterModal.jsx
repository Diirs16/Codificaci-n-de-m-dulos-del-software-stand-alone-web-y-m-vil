import { useState, useMemo, useEffect } from "react";
import { X, Check, AlertCircle, Loader2 } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { esFormatoCorreoValido } from "../utils/validarCorreo";
import { validarCorreo } from "../services/api";

const RULES = [
  { id: "len",     label: "Mínimo 8 caracteres",               test: (p) => p.length >= 8 },
  { id: "upper",   label: "Al menos una mayúscula",             test: (p) => /[A-Z]/.test(p) },
  { id: "number",  label: "Al menos un número",                 test: (p) => /[0-9]/.test(p) },
  { id: "special", label: 'Al menos un carácter especial: @ # ! " $ & ? ¡', test: (p) => /[@#!"$&?¡\-_*.]/.test(p) },
];

export default function RegisterModal() {
  const {
    showRegister,
    setShowRegister,
    register,
    verifyCode,
    openLogin,
    authError,
    setAuthError,
    pendingEmail,
    setPendingEmail,
  } = useAuth();

  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
  });
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [showRules, setShowRules] = useState(false);

  const ruleResults = useMemo(
    () => RULES.map((r) => ({ ...r, ok: r.test(form.password) })),
    [form.password]
  );
  const allRulesOk = ruleResults.every((r) => r.ok);

  // Estado del correo: "vacio" | "formato_invalido" | "verificando" | "valido" | "invalido" | "sin_verificar"
  const [emailStatus, setEmailStatus] = useState({ estado: "vacio", mensaje: "" });

  useEffect(() => {
    const email = form.email.trim();

    if (!email) {
      setEmailStatus({ estado: "vacio", mensaje: "" });
      return;
    }
    // 1. Formato: instantáneo, 100% en el navegador.
    if (!esFormatoCorreoValido(email)) {
      setEmailStatus({ estado: "formato_invalido", mensaje: "El formato del correo no es válido" });
      return;
    }
    // 2. Dominio: se confirma con el backend (consulta registros MX),
    //    con un pequeño retraso para no llamar la API en cada tecla.
    setEmailStatus({ estado: "verificando", mensaje: "Verificando dominio..." });
    const timeoutId = setTimeout(async () => {
      try {
        const res = await validarCorreo(email);
        setEmailStatus({ estado: res.valido ? "valido" : "invalido", mensaje: res.mensaje });
      } catch {
        setEmailStatus({ estado: "sin_verificar", mensaje: "No se pudo verificar el dominio ahora mismo" });
      }
    }, 600);

    return () => clearTimeout(timeoutId);
  }, [form.email]);

  const emailBloqueaEnvio = emailStatus.estado === "formato_invalido" || emailStatus.estado === "invalido";

  if (!showRegister) return null;

  const handleChange = (e) =>
    setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (emailBloqueaEnvio) {
      setAuthError(emailStatus.mensaje || "El correo no es válido");
      return;
    }
    if (!allRulesOk) {
      setAuthError("La contraseña no cumple todos los requisitos");
      setShowRules(true);
      return;
    }
    if (form.password !== form.confirmPassword) {
      setAuthError("Las contraseñas no coinciden");
      return;
    }
    setLoading(true);
    try {
      await register(form.name, form.email, form.password);
      setForm({ name: "", email: "", password: "", confirmPassword: "" });
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
      await verifyCode(pendingEmail, code);
    } catch (err) {
      setAuthError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setShowRegister(false);
    setCode("");
    setForm({ name: "", email: "", password: "", confirmPassword: "" });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div
        className="absolute inset-0 bg-black/40 backdrop-fade"
        onClick={handleClose}
      />
      <div className="modal-enter relative bg-white rounded-xl shadow-xl w-full max-w-sm p-6">
        <button
          onClick={handleClose}
          className="absolute top-4 right-4 p-1 hover:bg-gray-100 rounded-full"
          aria-label="Cerrar"
        >
          <X className="w-5 h-5" />
        </button>

        {!pendingEmail ? (
          <>
            <h2 className="text-xl font-bold mb-6 text-center">Crear Cuenta</h2>

            {authError && (
              <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2 mb-4 text-center">
                {authError}
              </p>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label htmlFor="reg-name" className="block text-sm font-medium mb-1">
                  Nombre completo
                </label>
                <input
                  id="reg-name"
                  name="name"
                  type="text"
                  value={form.name}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:border-black"
                  placeholder="Tu nombre"
                />
              </div>

              <div>
                <label htmlFor="reg-email" className="block text-sm font-medium mb-1">
                  Correo electrónico
                </label>
                <input
                  id="reg-email"
                  name="email"
                  type="email"
                  value={form.email}
                  onChange={handleChange}
                  required
                  className={`w-full px-3 py-2 border rounded-lg text-sm focus:outline-none ${
                    emailBloqueaEnvio
                      ? "border-red-400 focus:border-red-500"
                      : "border-gray-300 focus:border-black"
                  }`}
                  placeholder="tu@correo.com"
                />
                {emailStatus.estado !== "vacio" && (
                  <p
                    className={`mt-1.5 flex items-center gap-1.5 text-xs ${
                      emailStatus.estado === "valido"
                        ? "text-green-600"
                        : emailStatus.estado === "verificando"
                        ? "text-gray-400"
                        : emailStatus.estado === "sin_verificar"
                        ? "text-amber-600"
                        : "text-red-600"
                    }`}
                  >
                    {emailStatus.estado === "verificando" ? (
                      <Loader2 className="w-3.5 h-3.5 shrink-0 animate-spin" />
                    ) : emailStatus.estado === "valido" ? (
                      <Check className="w-3.5 h-3.5 shrink-0" />
                    ) : (
                      <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                    )}
                    {emailStatus.mensaje}
                  </p>
                )}
              </div>

              <div>
                <label htmlFor="reg-password" className="block text-sm font-medium mb-1">
                  Contraseña
                </label>
                <input
                  id="reg-password"
                  name="password"
                  type="password"
                  value={form.password}
                  onChange={handleChange}
                  onFocus={() => setShowRules(true)}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:border-black"
                  placeholder='Ej: MiPerro@2025'
                />
                {showRules && (
                  <ul className="mt-2 space-y-1">
                    {ruleResults.map((r) => (
                      <li key={r.id} className={`flex items-center gap-1.5 text-xs ${r.ok ? "text-green-600" : "text-gray-400"}`}>
                        {r.ok
                          ? <Check className="w-3.5 h-3.5 shrink-0" />
                          : <AlertCircle className="w-3.5 h-3.5 shrink-0" />}
                        {r.label}
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              <div>
                <label htmlFor="reg-confirm" className="block text-sm font-medium mb-1">
                  Confirmar contraseña
                </label>
                <input
                  id="reg-confirm"
                  name="confirmPassword"
                  type="password"
                  value={form.confirmPassword}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:border-black"
                  placeholder="Repite tu contraseña"
                />
              </div>

              <button
                type="submit"
                disabled={loading || emailBloqueaEnvio || !allRulesOk || form.password !== form.confirmPassword}
                className="w-full bg-black text-white py-2.5 rounded-lg font-medium hover:bg-gray-800 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                {loading ? "Enviando código..." : "Registrarse"}
              </button>
            </form>

            <p className="text-center text-sm text-gray-500 mt-4">
              ¿Ya tienes cuenta?{" "}
              <button
                onClick={openLogin}
                className="text-black font-medium hover:underline"
              >
                Inicia sesión
              </button>
            </p>
          </>
        ) : (
          <>
            <h2 className="text-xl font-bold mb-2 text-center">Verificar correo</h2>
            <p className="text-sm text-gray-500 text-center mb-6">
              Ingresa el código de 6 dígitos que enviamos a{" "}
              <span className="font-medium text-gray-800">{pendingEmail}</span>
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
                onClick={() => { setAuthError(null); setPendingEmail(null); setCode(""); }}
                className="text-black font-medium hover:underline"
              >
                Volver e intentar de nuevo
              </button>
            </p>
          </>
        )}
      </div>
    </div>
  );
}
