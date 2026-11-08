// Pruebas del ítem 4.7 (A-24): la web revalida la sesión con /auth/me al iniciar.
// Se corren con `npm test` (node --test, sin dependencias nuevas). No llaman a la
// API real: `fetch` se reemplaza por uno falso. Los tokens son inventados.
//
// Antes, AuthContext.jsx leía la sesión de localStorage y la daba por buena
// siempre, aunque el token (24 h) hubiera vencido. Ahora:
// - 401 (token vencido o falso) → se cierra la sesión.
// - 503, 502, 500, red caída o 404 → la sesión NO se toca (decisión del dueño,
//   opción A: solo el 401 la cierra).
// - 200 → se actualizan nombre y correo.
// - Si la sesión cambió mientras se esperaba la respuesta, la respuesta se ignora.
import { test, beforeEach, afterEach } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

// localStorage falso (en Node no existe como en el navegador)
const guardado = new Map();
Object.defineProperty(globalThis, "localStorage", {
  value: {
    getItem: (clave) => (guardado.has(clave) ? guardado.get(clave) : null),
    setItem: (clave, valor) => guardado.set(clave, String(valor)),
    removeItem: (clave) => guardado.delete(clave),
  },
  configurable: true,
  writable: true,
});

// Import como objeto: si falta una función, falla su prueba y no todo el archivo.
const api = await import("../src/services/api.js");
const { revalidarSesion } = await import("../src/utils/sesion.js");

const TOKEN_KEY = "petconnect_token";
const TOKEN = "token-de-prueba"; // inventado
const PERFIL = { id: 7, name: "Ana Prueba", email: "ana@ejemplo.test" }; // inventado
const leer = (ruta) => readFileSync(fileURLToPath(new URL(ruta, import.meta.url)), "utf8");
const fetchOriginal = globalThis.fetch;
let peticiones = [];

function responder(status, cuerpo) {
  globalThis.fetch = async (url, opciones) => {
    peticiones.push({ url, opciones });
    return new Response(typeof cuerpo === "string" ? cuerpo : JSON.stringify(cuerpo), {
      status,
      headers: { "Content-Type": "application/json" },
    });
  };
}

// Lo mismo que hace AuthContext.jsx: lee el token guardado y llama a la API real (api.js)
const revalidar = () =>
  revalidarSesion({ leerToken: () => localStorage.getItem(TOKEN_KEY), obtenerPerfil: api.getPerfil });

beforeEach(() => {
  peticiones = [];
  guardado.clear();
  guardado.set(TOKEN_KEY, TOKEN);
});

afterEach(() => {
  globalThis.fetch = fetchOriginal;
});

// --- api.js ---

test("getPerfil llama a GET /api/auth/me con el token guardado", async () => {
  assert.equal(typeof api.getPerfil, "function", "falta getPerfil en src/services/api.js");
  responder(200, PERFIL);
  assert.deepEqual(await api.getPerfil(), PERFIL);
  assert.equal(peticiones.length, 1);
  assert.equal(peticiones[0].url, "/api/auth/me");
  assert.equal(peticiones[0].opciones.method ?? "GET", "GET");
  assert.equal(peticiones[0].opciones.headers.Authorization, `Bearer ${TOKEN}`);
});

// --- Qué se decide con cada respuesta ---

test("token vencido o falso (401): se cierra la sesión", async () => {
  responder(401, { error: "Token invalido o sesion expirada. Inicia sesion de nuevo" });
  assert.deepEqual(await revalidar(), { accion: "cerrar" });
});

test("la API no responde bien (503, 502, 500): la sesión NO se cierra", async () => {
  for (const [status, cuerpo] of [
    [503, { error: "Servicio no disponible" }],
    [502, ""], // proxy de Vite con la API apagada
    [500, { error: "Error interno" }],
  ]) {
    responder(status, cuerpo);
    assert.deepEqual(await revalidar(), { accion: "mantener" }, `status ${status}`);
  }
});

test("sin red (fetch falla, status 0): la sesión NO se cierra", async () => {
  globalThis.fetch = async () => {
    throw new TypeError("Failed to fetch");
  };
  assert.deepEqual(await revalidar(), { accion: "mantener" });
});

test("404 'Usuario no encontrado' no cierra la sesión (opción A del dueño)", async () => {
  responder(404, { error: "Usuario no encontrado" });
  assert.deepEqual(await revalidar(), { accion: "mantener" });
});

test("token vigente (200): se actualizan nombre y correo", async () => {
  responder(200, PERFIL);
  assert.deepEqual(await revalidar(), { accion: "actualizar", perfil: PERFIL });
});

test("datos guardados sin token: se cierra la sesión sin llamar a la API", async () => {
  guardado.clear();
  responder(200, PERFIL);
  assert.deepEqual(await revalidar(), { accion: "cerrar" });
  assert.equal(peticiones.length, 0);
});

test("si la sesión cambia mientras se espera (cerrar sesión u otra cuenta), se ignora", async () => {
  // La persona cierra sesión justo mientras /auth/me responde 401
  globalThis.fetch = async () => {
    guardado.delete(TOKEN_KEY);
    return new Response(JSON.stringify({ error: "Token invalido" }), { status: 401 });
  };
  assert.deepEqual(await revalidar(), { accion: "ignorar" });

  // Otra cuenta entra mientras llega la respuesta vieja
  guardado.set(TOKEN_KEY, TOKEN);
  globalThis.fetch = async () => {
    guardado.set(TOKEN_KEY, "token-de-otra-cuenta");
    return new Response(JSON.stringify({ error: "Token invalido" }), { status: 401 });
  };
  assert.deepEqual(await revalidar(), { accion: "ignorar" });
  assert.equal(guardado.get(TOKEN_KEY), "token-de-otra-cuenta");
});

// --- AuthContext.jsx (Node no entiende JSX: se revisa el texto) ---

test("AuthContext revalida al iniciar con revalidarSesion y getPerfil", () => {
  const contexto = leer("../src/context/AuthContext.jsx");
  assert.match(contexto, /import \{ revalidarSesion \} from "\.\.\/utils\/sesion"/);
  assert.match(contexto, /\bgetPerfil\b/);
  assert.match(contexto, /useEffect\(\(\) => \{[\s\S]*revalidarSesion\(/);
  // Cierra solo con "cerrar" y conserva el token al actualizar
  assert.match(contexto, /accion === "cerrar"[\s\S]*clearSession\(\)/);
  assert.match(contexto, /accion === "actualizar"[\s\S]*saveSession\(perfil\)/);
});
