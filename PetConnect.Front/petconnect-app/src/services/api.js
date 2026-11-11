import { rutaPaginada } from "../utils/paginacion.js";
import { resolverBaseApi } from "../utils/configApi.js";

// Ítem 5.5: "/api" en desarrollo y Docker; en Vercel, la API de Railway
// (VITE_API_URL, que Vite escribe en la página al compilar). Si la dirección no
// sirve, API_BASE queda null y apiFetch no llama a nada (ver configApi.js).
// `?.` porque en las pruebas (Node) import.meta.env no existe.
const CONFIG_API = resolverBaseApi(import.meta.env?.VITE_API_URL);
const API_BASE = CONFIG_API.base;
if (CONFIG_API.error) console.warn(`[PetConnect] ${CONFIG_API.error}: la web no llamará a la API`);
const TOKEN_KEY = "petconnect_token";

// Ítem 3.3 (A-23): cada error lleva `status`, el número de respuesta HTTP
// (404 = no existe, 503 = BD caída, 502 = el proxy de Vite no encontró la API).
// Vale 0 si el servidor ni siquiera respondió. Así las páginas distinguen
// "no encontrada" de "no pudimos cargar" sin comparar textos.
//
// Ítem 3.5 (A-20, R05): si la API manda "requiere_autorizacion": true (403 de
// /auth/login o /auth/login/verify), el error lleva requiereAutorizacion = true
// y el inicio de sesión muestra la casilla. Otro 403 (cuenta inactiva) no lo trae.
function errorDeApi(mensaje, status, data) {
  const error = new Error(mensaje);
  error.status = status;
  error.requiereAutorizacion = data?.requiere_autorizacion === true;
  return error;
}

async function apiFetch(path, options = {}) {
  const token = localStorage.getItem(TOKEN_KEY);
  const headers = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  // Dirección mal configurada: se falla como "sin conexión" sin mandar nada
  if (!API_BASE) throw errorDeApi("No se pudo conectar con el servidor", 0);

  let res;
  try {
    res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  } catch {
    throw errorDeApi("No se pudo conectar con el servidor", 0);
  }

  let data;
  try {
    data = await res.json();
  } catch {
    throw errorDeApi(`Error ${res.status}: respuesta inválida del servidor`, res.status);
  }
  if (!res.ok) throw errorDeApi(data.error || `Error ${res.status}`, res.status, data);
  return data;
}

// --- Auth ---
// Ítem 3.5: `acepta_datos` solo viaja cuando la persona marcó la casilla
// (aceptaDatos === true) y siempre como booleano. Una cuenta que ya autorizó
// inicia sesión sin mandarlo.
export function loginUser(email, password, aceptaDatos) {
  const cuerpo = { email, password };
  if (aceptaDatos === true) cuerpo.acepta_datos = true;
  return apiFetch("/auth/login", {
    method: "POST",
    body: JSON.stringify(cuerpo),
  });
}

// NC-005 (ítem 3.1): la API solo acepta el booleano true como autorización de
// datos (Ley 1581, art. 9); nunca se manda como texto.
export function registerUser(name, email, password, aceptaDatos) {
  return apiFetch("/auth/register", {
    method: "POST",
    body: JSON.stringify({ name, email, password, acepta_datos: aceptaDatos === true }),
  });
}

export function verifyCode(email, code) {
  return apiFetch("/auth/verify", {
    method: "POST",
    body: JSON.stringify({ email, code }),
  });
}

// Reenvía el MISMO código del registro pendiente (ítem 2.7). La respuesta es
// siempre neutra: no dice si ese correo tiene un registro en curso.
export function resendRegisterCode(email) {
  return apiFetch("/auth/register/resend", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}

export function verifyLoginCode(email, code) {
  return apiFetch("/auth/login/verify", {
    method: "POST",
    body: JSON.stringify({ email, code }),
  });
}

// Ítem 4.7 (A-24): pregunta a la API si el token guardado sigue vigente.
// 200 → datos de la cuenta (id, name, email); 401 → token vencido o falso.
export function getPerfil() {
  return apiFetch("/auth/me");
}

// Ítem 4.13 (A-03): cierra la sesión EN LA API. La API suma 1 a version_sesion y
// así el token deja de valer en todos los aparatos de la cuenta (200). Si el token ya
// no valía responde 401. Se rinde a los TIEMPO_CIERRE_MS (status 0, como sin red)
// para que nadie quede esperando: utils/sesion.js borra la sesión local de todos modos.
export const TIEMPO_CIERRE_MS = 8000;

export function cerrarSesionEnServidor() {
  return apiFetch("/auth/logout", {
    method: "POST",
    signal: AbortSignal.timeout(TIEMPO_CIERRE_MS),
  });
}

export function validarCorreo(email) {
  return apiFetch("/utils/validar-correo", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}

// --- Productos ---
// Ítem 4.17 (NC-003): los listados van por páginas. Opcional:
// { pagina, porPagina } → ?pagina=&por_pagina= (sin opciones, la API manda la
// primera página de 20; nunca más de 50). La respuesta sigue siendo una lista.
export function getProductos(opciones) { return apiFetch(rutaPaginada("/productos", opciones)); }
export function getProducto(id) { return apiFetch(`/productos/${id}`); }

// --- Mascotas ---
export function getMascotasAdopcion(opciones) {
  return apiFetch(rutaPaginada("/mascotas/adopcion", opciones));
}
export function getMascota(id) { return apiFetch(`/mascotas/${id}`); }

// --- Solicitudes (ítem 3.6, A-21) ---
// Necesitan la sesión iniciada: apiFetch manda el token. El nombre y el correo
// NO viajan: la API los toma de la cuenta. Si la cuenta no aceptó la versión
// vigente de la política, la API responde 403 y el error trae
// requiereAutorizacion = true. La página dice "enviada" solo si esto no lanza error.
export function enviarSolicitudAdopcion(idMascota, mensaje, telefono = "") {
  return apiFetch("/solicitudes/adopcion", {
    method: "POST",
    body: JSON.stringify({ id_mascota: Number(idMascota), mensaje, telefono }),
  });
}

export function enviarMensajeContacto(mensaje) {
  return apiFetch("/solicitudes/contacto", {
    method: "POST",
    body: JSON.stringify({ mensaje }),
  });
}
