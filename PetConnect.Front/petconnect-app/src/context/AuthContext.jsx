import { createContext, useContext, useEffect, useState } from "react";
import {
  getPerfil,
  loginUser,
  registerUser,
  verifyCode as apiVerifyCode,
  verifyLoginCode as apiVerifyLoginCode,
} from "../services/api";
import { revalidarSesion } from "../utils/sesion";

const AuthContext = createContext();
const SESSION_KEY = "petconnect_session";
const TOKEN_KEY   = "petconnect_token";

function saveSession(userData, token) {
  localStorage.setItem(SESSION_KEY, JSON.stringify(userData));
  if (token) localStorage.setItem(TOKEN_KEY, token);
}

function clearSession() {
  localStorage.removeItem(SESSION_KEY);
  localStorage.removeItem(TOKEN_KEY);
}

function loadSession() {
  try {
    const raw = localStorage.getItem(SESSION_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }) {
  const [user, setUser]               = useState(() => loadSession());
  const [showLogin, setShowLogin]     = useState(false);
  const [showRegister, setShowRegister] = useState(false);
  const [authError, setAuthError]     = useState(null);
  const [pendingEmail, setPendingEmail] = useState(null);
  const [pendingLoginEmail, setPendingLoginEmail] = useState(null);

  // Ítem 4.7 (A-24): la sesión guardada se muestra de inmediato, pero al abrir la
  // web se pregunta a la API (/auth/me) si el token sigue vigente. Solo un 401
  // la cierra; si la API no responde (503, red caída) la sesión no se toca.
  useEffect(() => {
    if (!loadSession()) return;
    let vigente = true; // React (StrictMode) puede montar dos veces: vale la última
    revalidarSesion({
      leerToken: () => localStorage.getItem(TOKEN_KEY),
      obtenerPerfil: getPerfil,
    }).then(({ accion, perfil }) => {
      if (!vigente) return;
      if (accion === "cerrar") {
        setUser(null);
        clearSession();
      } else if (accion === "actualizar") {
        setUser(perfil); // nombre y correo al día; el token guardado se conserva
        saveSession(perfil);
      }
    });
    return () => {
      vigente = false;
    };
  }, []);

  const _setUser = (userData, token) => {
    setUser(userData);
    if (userData) saveSession(userData, token);
    else clearSession();
  };

  // aceptaDatos: solo true cuando la persona marcó la casilla de autorización
  // (ítem 3.5, cuentas sin autorización vigente). Si no, no se manda.
  const login = async (email, password, aceptaDatos) => {
    setAuthError(null);
    await loginUser(email, password, aceptaDatos);
    setPendingLoginEmail(email);
  };

  const verifyLoginCode = async (email, code) => {
    setAuthError(null);
    const { token, ...userData } = await apiVerifyLoginCode(email, code);
    _setUser(userData, token);
    setPendingLoginEmail(null);
    setShowLogin(false);
  };

  const register = async (name, email, password, aceptaDatos) => {
    setAuthError(null);
    await registerUser(name, email, password, aceptaDatos);
    setPendingEmail(email);
  };

  const verifyCode = async (email, code) => {
    setAuthError(null);
    const { token, ...userData } = await apiVerifyCode(email, code);
    _setUser(userData, token);
    setPendingEmail(null);
    setShowRegister(false);
  };

  const logout = () => {
    _setUser(null);
    setPendingEmail(null);
    setPendingLoginEmail(null);
  };

  const openLogin = () => {
    setShowRegister(false);
    setShowLogin(true);
    setAuthError(null);
    setPendingLoginEmail(null);
  };

  const openRegister = () => {
    setShowLogin(false);
    setShowRegister(true);
    setAuthError(null);
    setPendingEmail(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        showLogin,
        showRegister,
        authError,
        setAuthError,
        setShowLogin,
        setShowRegister,
        pendingEmail,
        setPendingEmail,
        pendingLoginEmail,
        setPendingLoginEmail,
        login,
        verifyLoginCode,
        register,
        verifyCode,
        logout,
        openLogin,
        openRegister,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
