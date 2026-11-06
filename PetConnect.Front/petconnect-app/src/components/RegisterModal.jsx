import { useState, useMemo, useEffect, useRef } from "react";
import { X, Check, AlertCircle, Loader2, RotateCw, MailCheck, ExternalLink } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { esFormatoCorreoValido } from "../utils/validarCorreo";
import { validarCorreo, resendRegisterCode } from "../services/api";

// Mismas reglas que el servidor (otp/servicio.py, ítem 2.7): 60 s entre correos
// y máximo 3 reenvíos por código. El servidor las aplica igual aunque esto se salte.
const ESPERA_REENVIO_MS = 60_000;
const MAX_REENVIOS = 3;

const RULES = [
  { id: "len",     label: "Mínimo 8 caracteres",               test: (p) => p.length >= 8 },
  { id: "upper",   label: "Al menos una mayúscula",             test: (p) => /[A-Z]/.test(p) },
  { id: "number",  label: "Al menos un número",                 test: (p) => /[0-9]/.test(p) },
  { id: "special", label: 'Al menos un carácter especial: @ # ! " $ & ? ¡', test: (p) => /[@#!"$&?¡\-_*.]/.test(p) },
];

// NC-005 (ítem 3.1): la casilla de autorización empieza SIN marcar (Ley 1581, art. 9).
// Textos de la Parte B de Documentacion/Legal/POLITICA-TRATAMIENTO-DATOS-v1.0-BORRADOR.md
const FORM_VACIO = {
  name: "",
  email: "",
  password: "",
  confirmPassword: "",
  aceptaDatos: false,
};
const MENSAJE_SIN_AUTORIZACION = "Para crear tu cuenta debes autorizar el tratamiento de tus datos personales.";

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

  const [form, setForm] = useState(FORM_VACIO);
  const aceptaRef = useRef(null);
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

  // --- Reenviar código (ítem 2.7) ---
  // reenviarDesde: hora (ms) a partir de la cual se puede volver a pedir el código.
  // ahora: se actualiza cada segundo solo mientras dura la espera (cuenta regresiva).
  const [reenviarDesde, setReenviarDesde] = useState(0);
  const [ahora, setAhora] = useState(0);
  const [reenvios, setReenvios] = useState(0);
  const [reenviando, setReenviando] = useState(false);
  const [avisoReenvio, setAvisoReenvio] = useState("");

  useEffect(() => {
    if (reenviarDesde <= ahora) return;
    const id = setTimeout(() => setAhora(Date.now()), 1000);
    return () => clearTimeout(id);
  }, [reenviarDesde, ahora]);

  const segundosRestantes = Math.max(0, Math.ceil((reenviarDesde - ahora) / 1000));
  const sinReenvios = reenvios >= MAX_REENVIOS;
  const reenvioBloqueado = reenviando || segundosRestantes > 0 || sinReenvios;

  if (!showRegister) return null;

  const iniciarEspera = () => {
    const t = Date.now();
    setAhora(t);
    setReenviarDesde(t + ESPERA_REENVIO_MS);
  };

  const reiniciarReenvio = () => {
    setReenviarDesde(0);
    setAhora(0);
    setReenvios(0);
    setAvisoReenvio("");
  };

  const handleChange = (e) => {
    const { name, type, checked, value } = e.target;
    setForm({ ...form, [name]: type === "checkbox" ? checked : value });
  };

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
    // Sin la casilla no se llama a la API (y la API lo rechazaría igual con 400)
    if (!form.aceptaDatos) {
      setAuthError(MENSAJE_SIN_AUTORIZACION);
      aceptaRef.current?.focus();
      return;
    }
    setLoading(true);
    try {
      await register(form.name, form.email, form.password, form.aceptaDatos);
      setForm(FORM_VACIO);
      reiniciarReenvio();
      iniciarEspera();   // la espera arranca también con el primer código
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

  const handleResend = async () => {
    if (reenvioBloqueado) return;   // aria-disabled no bloquea el clic por sí solo
    setReenviando(true);
    setAuthError(null);
    setAvisoReenvio("");
    try {
      await resendRegisterCode(pendingEmail);
      setReenvios((n) => n + 1);
      // Aviso neutro: no confirma que el correo tenga un registro en curso
      setAvisoReenvio("Si hay un registro pendiente, te reenviamos el código. Revisa también la carpeta de spam.");
      iniciarEspera();
    } catch (err) {
      setAuthError(err.message);   // 429, 503 u otro error de la API, como en el resto del modal
    } finally {
      setReenviando(false);
    }
  };

  const handleChangeEmail = () => {
    setAuthError(null);
    setPendingEmail(null);
    setCode("");
    reiniciarReenvio();
  };

  const handleClose = () => {
    setShowRegister(false);
    setCode("");
    setForm(FORM_VACIO);
    reiniciarReenvio();
  };

  return (
    // overflow-y-auto + min-h-full: si el formulario es más alto que la pantalla
    // (celular de 375 × 812 con la casilla de datos), se desplaza en vez de cortarse.
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div
        className="fixed inset-0 bg-black/40 backdrop-fade"
        onClick={handleClose}
      />
      <div
        className="relative flex min-h-full items-center justify-center p-4"
        onClick={(e) => e.target === e.currentTarget && handleClose()}   // clic fuera del modal
      >
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
              <p role="alert" className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2 mb-4 text-center">
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

              {/* NC-005: autorización previa, expresa e informada (Ley 1581, arts. 9 y 12) */}
              <div>
                <div className="flex items-start gap-3">
                  <input
                    ref={aceptaRef}
                    id="reg-acepta"
                    name="aceptaDatos"
                    type="checkbox"
                    checked={form.aceptaDatos}
                    onChange={handleChange}
                    aria-describedby="reg-acepta-aviso"
                    className="mt-0.5 h-5 w-5 shrink-0 cursor-pointer accent-black focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-black"
                  />
                  <label htmlFor="reg-acepta" className="min-h-11 text-sm leading-snug cursor-pointer">
                    Soy mayor de 18 años, he leído la{" "}
                    <a
                      href="/politica-de-datos"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="font-medium text-black underline underline-offset-2 hover:text-gray-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-black"
                    >
                      Política de tratamiento de datos personales
                      <ExternalLink className="inline w-3.5 h-3.5 ml-0.5 -mt-0.5" aria-hidden="true" />
                      <span className="sr-only"> (se abre en una pestaña nueva)</span>
                    </a>{" "}
                    y autorizo a PetConnect a tratar mis datos para crear y usar mi cuenta.
                  </label>
                </div>
                <p id="reg-acepta-aviso" className="mt-2 pl-8 text-xs leading-relaxed text-gray-600">
                  Usaremos tu nombre y tu correo para crear tu cuenta y enviarte códigos de verificación.
                  Puedes conocer, actualizar, rectificar o borrar tus datos y revocar este permiso
                  escribiendo a{" "}
                  {/* Correo de atención del proyecto (D.1, 06/11/2026); el mismo de PoliticaDatos.jsx */}
                  <span className="break-words font-medium text-gray-800">proyectopetconnect+atencion@gmail.com.</span>
                </p>
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
              <p role="alert" className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2 mb-4 text-center">
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

            <div className="mt-5 pt-4 border-t border-gray-100">
              <p className="text-center text-sm text-gray-500 mb-2">¿No recibiste el código?</p>
              <button
                type="button"
                onClick={handleResend}
                aria-disabled={reenvioBloqueado}
                className="w-full min-h-11 inline-flex items-center justify-center gap-2 border border-gray-300 bg-white text-black py-2.5 rounded-lg text-sm font-medium transition-colors hover:bg-gray-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-black aria-disabled:bg-gray-50 aria-disabled:text-gray-600 aria-disabled:cursor-not-allowed"
              >
                <RotateCw className={`w-4 h-4 shrink-0 ${reenviando ? "animate-spin" : ""}`} aria-hidden="true" />
                <span className="tabular-nums">
                  {reenviando
                    ? "Reenviando..."
                    : sinReenvios
                    ? "Ya no se puede reenviar más"
                    : segundosRestantes > 0
                    ? `Reenviar en ${segundosRestantes} s`
                    : "Reenviar código"}
                </span>
              </button>

              {/* Siempre en el DOM para que los lectores de pantalla anuncien el cambio */}
              <div role="status" aria-live="polite">
                {avisoReenvio && (
                  <p className="mt-3 flex items-start gap-2 text-sm text-green-800 bg-green-50 border border-green-200 rounded-lg px-3 py-2">
                    <MailCheck className="w-4 h-4 shrink-0 mt-0.5" aria-hidden="true" />
                    <span>
                      {avisoReenvio}
                      {sinReenvios && " Ya usaste los reenvíos de este código; si no llega, revisa que el correo esté bien escrito."}
                    </span>
                  </p>
                )}
              </div>

              <p className="text-center text-sm text-gray-500 mt-4">
                ¿Escribiste mal tu correo?{" "}
                <button
                  type="button"
                  onClick={handleChangeEmail}
                  className="text-black font-medium underline-offset-2 hover:underline focus-visible:underline"
                >
                  Cambiar correo
                </button>
              </p>
            </div>
          </>
        )}
      </div>
      </div>
    </div>
  );
}
