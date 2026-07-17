import AsyncStorage from "@react-native-async-storage/async-storage";
import { Platform } from "react-native";

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
    throw new Error(`Error ${res.status}: respuesta inválida del servidor`);
  }
  if (!res.ok) throw new Error(data.error || `Error ${res.status}`);
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

export function getPerfil() {
  return apiFetch("/auth/me");
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
