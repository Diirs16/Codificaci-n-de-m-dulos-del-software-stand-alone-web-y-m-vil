// Pruebas del ítem 4.13, parte 2 (A-03): el botón "Cerrar sesión" de la web.
// Se corren con `npm test` (node --test, sin dependencias nuevas). No llaman a la
// API real: `fetch` se reemplaza por uno falso. Los tokens son inventados.
//
// Antes, logout() solo borraba el token de este navegador: si alguien lo había
// copiado, o la cuenta seguía abierta en otro aparato, seguía valiendo hasta 24 h.
// Ahora:
// - Se llama a POST /api/auth/logout (la API suma 1 a version_sesion y el token
//   deja de valer en TODOS los aparatos).
// - La sesión local se borra SIEMPRE: 200, 401, 503, 502, 500, sin red o tiempo agotado.
// - Si el servidor no pudo confirmar el cierre, se avisa (decisión A1 del dueño).
// - El botón queda desactivado mientras se espera (decisión B1).
// - FormularioSolicitud, tras un 401, solo cierra en local (no llama a la API).
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
const sesion = await import("../src/utils/sesion.js");

const TOKEN_KEY = "petconnect_token";
const SESSION_KEY = "petconnect_session";
const TOKEN = "token-de-prueba"; // inventado
const leer = (ruta) => readFileSync(fileURLToPath(new URL(ruta, import.meta.url)), "utf8");
const fetchOriginal = globalThis.fetch;
let peticiones = [];
let borrados = 0;

function responder(status, cuerpo) {
  globalThis.fetch = async (url, opciones) => {
    peticiones.push({ url, opciones });
    return new Response(typeof cuerpo === "string" ? cuerpo : JSON.stringify(cuerpo), {
      status,
      headers: { "Content-Type": "application/json" },
    });
  };
}

// Lo mismo que hace AuthContext.jsx: token guardado + API real (api.js) + borrado local
const borrarLocal = () => {
  borrados += 1;
  guardado.delete(TOKEN_KEY);
  guardado.delete(SESSION_KEY);
};
const cerrar = () => {
  assert.equal(typeof sesion.cerrarSesion, "function", "falta cerrarSesion en src/utils/sesion.js");
  assert.equal(
    typeof api.cerrarSesionEnServidor,
    "function",
    "falta cerrarSesionEnServidor en src/services/api.js",
  );
  return sesion.cerrarSesion({
    leerToken: () => localStorage.getItem(TOKEN_KEY),
    cerrarEnServidor: api.cerrarSesionEnServidor,
    borrarLocal,
  });
};
const sesionBorrada = () => !guardado.has(TOKEN_KEY) && !guardado.has(SESSION_KEY);

beforeEach(() => {
  peticiones = [];
  borrados = 0;
  guardado.clear();
  guardado.set(TOKEN_KEY, TOKEN);
  guardado.set(SESSION_KEY, JSON.stringify({ id: 7, name: "Ana Prueba" })); // inventado
});

afterEach(() => {
  globalThis.fetch = fetchOriginal;
});

// --- api.js ---

test("cerrarSesionEnServidor hace POST /api/auth/logout con el token y límite de tiempo", async () => {
  assert.equal(
    typeof api.cerrarSesionEnServidor,
    "function",
    "falta cerrarSesionEnServidor en src/services/api.js",
  );
  responder(200, { message: "Sesion cerrada" });
  assert.deepEqual(await api.cerrarSesionEnServidor(), { message: "Sesion cerrada" });
  assert.equal(peticiones.length, 1);
  assert.equal(peticiones[0].url, "/api/auth/logout");
  assert.equal(peticiones[0].opciones.method, "POST");
  assert.equal(peticiones[0].opciones.headers.Authorization, `Bearer ${TOKEN}`);
  // Con límite de tiempo: si la API no contesta, nadie queda esperando
  assert.ok(peticiones[0].opciones.signal instanceof AbortSignal, "falta el límite de tiempo (signal)");
  assert.ok(api.TIEMPO_CIERRE_MS > 0 && api.TIEMPO_CIERRE_MS <= 10000);
});

// --- Qué pasa con cada respuesta ---

test("200: se cierra en el servidor y en el navegador", async () => {
  responder(200, { message: "Sesion cerrada" });
  assert.equal(await cerrar(), "cerrada");
  assert.ok(sesionBorrada());
  assert.equal(borrados, 1);
});

test("401 (el token ya no valía): se borra lo local sin aviso", async () => {
  responder(401, { error: "Token invalido o sesion expirada. Inicia sesion de nuevo" });
  assert.equal(await cerrar(), "ya-cerrada");
  assert.ok(sesionBorrada());
});

test("503, 502 y 500: la sesión local SE BORRA igual y se avisa", async () => {
  for (const [status, cuerpo] of [
    [503, { error: "Servicio no disponible" }],
    [502, ""], // proxy de Vite con la API apagada
    [500, { error: "Error interno" }],
  ]) {
    guardado.set(TOKEN_KEY, TOKEN);
    guardado.set(SESSION_KEY, "{}");
    responder(status, cuerpo);
    assert.equal(await cerrar(), "sin-confirmar", `status ${status}`);
    assert.ok(sesionBorrada(), `status ${status}: la sesión local debe borrarse`);
  }
});

test("sin red o tiempo agotado: la sesión local SE BORRA igual y se avisa", async () => {
  for (const falla of [
    new TypeError("Failed to fetch"),
    new DOMException("The operation timed out.", "TimeoutError"), // lo que lanza AbortSignal.timeout
  ]) {
    guardado.set(TOKEN_KEY, TOKEN);
    guardado.set(SESSION_KEY, "{}");
    globalThis.fetch = async () => {
      throw falla;
    };
    assert.equal(await cerrar(), "sin-confirmar", falla.name);
    assert.ok(sesionBorrada(), `${falla.name}: la sesión local debe borrarse`);
  }
});

test("sin token guardado: no se llama a la API y se borra lo local", async () => {
  guardado.delete(TOKEN_KEY);
  responder(200, { message: "Sesion cerrada" });
  assert.equal(await cerrar(), "ya-cerrada");
  assert.equal(peticiones.length, 0);
  assert.ok(sesionBorrada());
});

test("si mientras se espera entra OTRA cuenta, su sesión nueva no se borra", async () => {
  globalThis.fetch = async () => {
    guardado.set(TOKEN_KEY, "token-de-otra-cuenta");
    return new Response(JSON.stringify({ message: "Sesion cerrada" }), { status: 200 });
  };
  assert.equal(await cerrar(), "cerrada");
  assert.equal(borrados, 0);
  assert.equal(guardado.get(TOKEN_KEY), "token-de-otra-cuenta");
});

// --- Componentes (Node no entiende JSX: se revisa el texto) ---

test("AuthContext: logout llama a la API con cerrarSesion y existe un cierre solo local", () => {
  const contexto = leer("../src/context/AuthContext.jsx");
  assert.match(contexto, /import \{[^}]*\bcerrarSesion\b[^}]*\} from "\.\.\/utils\/sesion"/);
  assert.match(contexto, /\bcerrarSesionEnServidor\b/);
  assert.match(contexto, /const logout = \(\) =>\s*cerrarSesion\(/);
  assert.match(contexto, /const cerrarSesionLocal = \(\) =>/);
  assert.match(contexto, /value=\{\{[\s\S]*\bcerrarSesionLocal\b[\s\S]*\}\}/);
});

test("FormularioSolicitud: tras un 401 solo cierra en local (no llama a la API)", () => {
  const formulario = leer("../src/components/FormularioSolicitud.jsx");
  assert.match(formulario, /function volverAIniciarSesion\(\) \{[\s\S]*cerrarSesionLocal\(\);[\s\S]*openLogin\(\);/);
  assert.doesNotMatch(formulario, /\blogout\b/);
});

test("Header: los dos botones esperan la API desactivados y avisan si no se confirmó", () => {
  const header = leer("../src/components/Header.jsx");
  // Escritorio y menú móvil usan la misma función y se desactivan mientras envían
  assert.equal(header.match(/onClick=\{salir\}/g)?.length, 2, "los dos botones deben usar salir");
  assert.equal(header.match(/disabled=\{cerrando\}/g)?.length, 2, "los dos botones deben desactivarse");
  assert.match(header, /await logout\(\)/);
  assert.match(header, /resultado === "sin-confirmar"/);
  // El aviso va en una zona role="status" y se puede cerrar
  assert.match(header, /role="status"/);
  assert.match(header, /no pudimos confirmarlo con el\s+servidor/);
  assert.match(header, /aria-label="Cerrar aviso"/);
});
