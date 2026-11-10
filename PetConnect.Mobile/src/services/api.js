import AsyncStorage from "@react-native-async-storage/async-storage";
import { Platform } from "react-native";
import { errorDeApi, cuerpoLogin, cuerpoSolicitudAdopcion, cuerpoMensajeContacto } from "../utils/peticiones";
import { conLimiteDeTiempo } from "../utils/sesion";
import { rutaPaginada } from "../utils/paginacion";
import { resolverUrlApi, resolverUrlPolitica } from "../utils/configApi";

// Ítem 5.3, parte 1 (A-27): las direcciones salen de EXPO_PUBLIC_API_URL y
// EXPO_PUBLIC_WEB_URL (plantilla: PetConnect.Mobile/.env.example). Vacías = el
// computador de desarrollo de siempre (10.0.2.2 en el emulador de Android,
// localhost en web). Fuera de desarrollo se exige https:// salvo hacia el propio
// computador (reglas en src/utils/configApi.js). Expo copia estos valores dentro
// de la app al compilar: se escriben como process.env.EXPO_PUBLIC_X (con punto),
// si no, quedan vacíos. Nunca va un secreto en una variable EXPO_PUBLIC_.
const PLATAFORMA = { plataforma: Platform.OS, esDesarrollo: __DEV__ };
const CONFIG_API = resolverUrlApi(process.env.EXPO_PUBLIC_API_URL, PLATAFORMA);
const CONFIG_POLITICA = resolverUrlPolitica(process.env.EXPO_PUBLIC_WEB_URL, PLATAFORMA);

// El motivo se muestra solo a quien programa (consola de Metro); no lleva datos personales.
if (CONFIG_API.error) console.warn(`Configuración de la API: ${CONFIG_API.error}`);
if (CONFIG_POLITICA.error) console.warn(`Configuración de la web: ${CONFIG_POLITICA.error}`);

/**
 * URL base de la API PetConnect (mismo backend Flask que usan el módulo
 * stand-alone y el módulo web). null si EXPO_PUBLIC_API_URL no es segura: entonces
 * apiFetch no manda nada.
 */
export const API_BASE = CONFIG_API.url;

/**
 * NC-005 (ítem 3.1): página de la Política de tratamiento de datos personales,
 * publicada por la web (/politica-de-datos). Se abre en el navegador del celular.
 * null si EXPO_PUBLIC_WEB_URL no es segura: Linking.openURL falla y la pantalla
 * muestra "No se pudo abrir la política en el navegador".
 */
export const POLITICA_URL = CONFIG_POLITICA.url;

const TOKEN_KEY = "petconnect_token";

async function apiFetch(path, options = {}) {
  // Sin status, como un error de red: no cierra la sesión ni se confunde con un 401.
  if (!API_BASE) throw errorDeApi("la app no tiene configurada una dirección segura (https) del servidor", undefined, null);

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

// Ítem 4.17 (NC-003): los listados van por páginas. Opcional:
// { pagina, porPagina } → ?pagina=&por_pagina= (sin opciones, la API manda la
// primera página de 20; nunca más de 50). La respuesta sigue siendo una lista.
export function getProductos(opciones) {
  return apiFetch(rutaPaginada("/productos", opciones));
}

export function getProducto(id) {
  return apiFetch(`/productos/${id}`);
}

export function getMascotasAdopcion(opciones) {
  return apiFetch(rutaPaginada("/mascotas/adopcion", opciones));
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
