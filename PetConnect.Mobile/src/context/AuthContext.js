import { createContext, useContext, useEffect, useState } from "react";
import {
  getPerfil,
  getToken,
  saveToken,
  clearToken,
  verifyLoginCode as apiVerifyLoginCode,
} from "../services/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [pendingLoginEmail, setPendingLoginEmail] = useState(null);

  useEffect(() => {
    (async () => {
      const token = await getToken();
      if (token) {
        try {
          const me = await getPerfil();
          setUser(me);
        } catch {
          await clearToken();
        }
      }
      setLoading(false);
    })();
  }, []);

  // Guarda la sesion cuando ya se tiene un token real (usado tras verificar
  // el codigo de registro, que si entrega el token directamente).
  async function establecerSesion(token, userData) {
    await saveToken(token);
    setUser(userData);
  }

  // Paso 1 del login ya no entrega token: solo confirma que se mando el
  // codigo al correo y deja pendiente la verificacion.
  function iniciarLogin(email) {
    setPendingLoginEmail(email);
  }

  // Paso 2: con el codigo correcto, la API entrega el token real.
  async function verificarLogin(code) {
    const { token, ...userData } = await apiVerifyLoginCode(pendingLoginEmail, code);
    await saveToken(token);
    setUser(userData);
    setPendingLoginEmail(null);
  }

  function cancelarLogin() {
    setPendingLoginEmail(null);
  }

  async function logout() {
    await clearToken();
    setUser(null);
    setPendingLoginEmail(null);
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        pendingLoginEmail,
        establecerSesion,
        iniciarLogin,
        verificarLogin,
        cancelarLogin,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
