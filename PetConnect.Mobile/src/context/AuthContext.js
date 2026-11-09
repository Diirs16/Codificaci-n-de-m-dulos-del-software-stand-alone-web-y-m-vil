import { createContext, useContext, useEffect, useState } from "react";
import {
  getPerfil,
  getToken,
  saveToken,
  clearToken,
  cerrarSesionEnServidor,
  verifyLoginCode as apiVerifyLoginCode,
} from "../services/api";
import { cerrarSesion } from "../utils/sesion";

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

  // Solo borra la sesión de este celular (sin llamar a la API). Se usa cuando la API
  // ya dijo que el token no vale (401), p. ej. en FormularioSolicitud.js.
  async function cerrarSesionLocal() {
    await clearToken();
    setUser(null);
    setPendingLoginEmail(null);
  }

  // Ítem 4.13 (A-03): botón "Cerrar sesión". Cierra en la API (todos los aparatos) y
  // siempre en este celular. Devuelve "cerrada", "ya-cerrada" o "sin-confirmar"
  // (ver utils/sesion.js); con "sin-confirmar" ProfileScreen muestra un aviso.
  function logout() {
    return cerrarSesion({
      leerToken: getToken,
      cerrarEnServidor: cerrarSesionEnServidor,
      borrarLocal: cerrarSesionLocal,
    });
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
        cerrarSesionLocal,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
