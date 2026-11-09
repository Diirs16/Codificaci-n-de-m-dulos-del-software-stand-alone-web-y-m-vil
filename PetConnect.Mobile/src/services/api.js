import AsyncStorage from "@react-native-async-storage/async-storage";
import { Platform } from "react-native";
import { errorDeApi, cuerpoLogin, cuerpoSolicitudAdopcion, cuerpoMensajeContacto } from "../utils/peticiones";
import { conLimiteDeTiempo } from "../utils/sesion";

/**
 * URL base de la API PetConnect (mismo backend Flask que usan el módulo
 * stand-alone y el módulo web). En Android emulator "localhost" apunta al
 * propio emulador, por eso se usa 10.0.2.2 para llegar al host.
 */
const HOST = Platform.select({
  android: "10.0.2.2",
  default: "localhost",
});

export const API_BASE = `http://${HOST}:5000/api`;

/**
 * NC-005 (ítem 3.1): página de la Política de tratamiento de datos personales,
 * publicada por la web (/politica-de-datos). Se abre en el navegador del celular.
 * Solo vale en desarrollo (web en el puerto 5173 del computador); al desplegar
 * debe salir de una variable de entorno, como la API (A-27, ítem 5.3).
 */
export const POLITICA_URL = `http://${HOST}:5173/politica-de-datos`;

const TOKEN_KEY = "petconnect_token";

async function apiFetch(path, options = {}) {
  const token = await AsyncStorage.getItem(TOKEN_KEY);
  const headers = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  let data;
  try {
    data = await res.json();
  } catch {
    throw errorDeApi(`Error ${res.status}: respuesta inválida del servidor`, res.status, null);
  }
  // Ítem 3.5: el error lleva status y requiereAutorizacion (src/utils/peticiones.js)
  if (!res.ok) throw errorDeApi(data.error || `Error ${res.status}`, res.status, data);
  return data;
}

export function getProductos() {
  return apiFetch("/productos");
}

export function getProducto(id) {
  return apiFetch(`/productos/${id}`);
}

export function getMascotasAdopcion() {
  return apiFetch("/mascotas/adopcion");
}

export function getMascota(id) {
  return apiFetch(`/mascotas/${id}`);
}

// Ítem 3.5: con aceptaDatos === true (casilla marcada) la API guarda la
// autorización de una cuenta que no la tenía, solo cuando el código sea correcto.
export function loginUser(email, password, aceptaDatos) {
  return apiFetch("/auth/login", {
    method: "POST",
    body: JSON.stringify(cuerpoLogin(email, password, aceptaDatos)),
  });
}

export function registerUser(name, email, password, aceptaDatos) {
  return apiFetch("/auth/register", {
    method: "POST",
    // NC-005: la API solo acepta el booleano JSON true; "=== true" evita mandar
    // un texto como "true" o un 1 (que la API rechazaría con 400).
    body: JSON.stringify({ name, email, password, acepta_datos: aceptaDatos === true }),
  });
}

export function verifyCode(email, code) {
  return apiFetch("/auth/verify", {
    method: "POST",
    body: JSON.stringify({ email, code }),
  });
}

export function verifyLoginCode(email, code) {
  return apiFetch("/auth/login/verify", {
    method: "POST",
    body: JSON.stringify({ email, code }),
  });
}

export function getPerfil() {
  return apiFetch("/auth/me");
}

// Ítem 4.13 (A-03): cierra la sesión EN LA API. La API suma 1 a version_sesion y así
// el token deja de valer en todos los aparatos de la cuenta (200). Si el token ya no
// valía responde 401. Se rinde a los TIEMPO_CIERRE_MS (8 s; error sin status, como sin
// red) para que nadie quede esperando: utils/sesion.js borra la sesión local igual.
export function cerrarSesionEnServidor() {
  return conLimiteDeTiempo((signal) => apiFetch("/auth/logout", { method: "POST", signal }));
}

// --- Solicitudes (ítem 3.6 parte 3, A-21) ---
// Necesitan la sesión iniciada: apiFetch manda el token. Si la cuenta no aceptó la
// versión vigente de la política, la API responde 403 y el error trae
// requiereAutorizacion = true. El formulario dice "enviada" solo si esto no lanza error.
export function enviarSolicitudAdopcion(idMascota, mensaje, telefono = "") {
  return apiFetch("/solicitudes/adopcion", {
    method: "POST",
    body: JSON.stringify(cuerpoSolicitudAdopcion(idMascota, mensaje, telefono)),
  });
}

export function enviarMensajeContacto(mensaje) {
  return apiFetch("/solicitudes/contacto", {
    method: "POST",
    body: JSON.stringify(cuerpoMensajeContacto(mensaje)),
  });
}

export async function saveToken(token) {
  await AsyncStorage.setItem(TOKEN_KEY, token);
}

export async function clearToken() {
  await AsyncStorage.removeItem(TOKEN_KEY);
}

export async function getToken() {
  return AsyncStorage.getItem(TOKEN_KEY);
}
