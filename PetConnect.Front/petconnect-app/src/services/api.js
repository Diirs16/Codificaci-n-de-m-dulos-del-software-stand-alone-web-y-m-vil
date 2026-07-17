const API_BASE = "/api";
const TOKEN_KEY = "petconnect_token";

async function apiFetch(path, options = {}) {
  const token = localStorage.getItem(TOKEN_KEY);
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
    throw new Error(`Error ${res.status}: respuesta inválida del servidor`);
  }
  if (!res.ok) throw new Error(data.error || `Error ${res.status}`);
  return data;
}

// --- Auth ---
export function loginUser(email, password) {
  return apiFetch("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export function registerUser(name, email, password) {
  return apiFetch("/auth/register", {
    method: "POST",
    body: JSON.stringify({ name, email, password }),
  });
}

export function verifyCode(email, code) {
  return apiFetch("/auth/verify", {
    method: "POST",
    body: JSON.stringify({ email, code }),
  });
}

// --- Productos ---
export function getProductos() { return apiFetch("/productos"); }
export function getProducto(id) { return apiFetch(`/productos/${id}`); }

// --- Mascotas ---
export function getMascotasAdopcion() { return apiFetch("/mascotas/adopcion"); }
export function getMascota(id) { return apiFetch(`/mascotas/${id}`); }
