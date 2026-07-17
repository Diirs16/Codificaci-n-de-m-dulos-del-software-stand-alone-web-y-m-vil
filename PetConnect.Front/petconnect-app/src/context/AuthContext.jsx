import { createContext, useContext, useState } from "react";
import { loginUser, registerUser, verifyCode as apiVerifyCode } from "../services/api";

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

  const _setUser = (userData, token) => {
    setUser(userData);
    if (userData) saveSession(userData, token);
    else clearSession();
  };

  const login = async (email, password) => {
    setAuthError(null);
    const { token, ...userData } = await loginUser(email, password);
    _setUser(userData, token);
    setShowLogin(false);
  };

  const register = async (name, email, password) => {
    setAuthError(null);
    await registerUser(name, email, password);
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
  };

  const openLogin = () => {
    setShowRegister(false);
    setShowLogin(true);
    setAuthError(null);
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
        login,
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
