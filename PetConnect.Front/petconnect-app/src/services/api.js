const API_BASE = "/api";
const TOKEN_KEY = "petconnect_token";

// Ítem 3.3 (A-23): cada error lleva `status`, el número de respuesta HTTP
// (404 = no existe, 503 = BD caída, 502 = el proxy de Vite no encontró la API).
// Vale 0 si el servidor ni siquiera respondió. Así las páginas distinguen
// "no encontrada" de "no pudimos cargar" sin comparar textos.
function errorDeApi(mensaje, status) {
  const error = new Error(mensaje);
  error.status = status;
  return error;
}

async function apiFetch(path, options = {}) {
  const token = localStorage.getItem(TOKEN_KEY);
  const headers = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

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
  if (!res.ok) throw errorDeApi(data.error || `Error ${res.status}`, res.status);
  return data;
}

// --- Auth ---
export function loginUser(email, password) {
  return apiFetch("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
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

export function validarCorreo(email) {
  return apiFetch("/utils/validar-correo", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}

// --- Productos ---
export function getProductos() { return apiFetch("/productos"); }
export function getProducto(id) { return apiFetch(`/productos/${id}`); }

// --- Mascotas ---
export function getMascotasAdopcion() { return apiFetch("/mascotas/adopcion"); }
export function getMascota(id) { return apiFetch(`/mascotas/${id}`); }
