// Pruebas del ítem 5.3, parte 3 (A-28): qué pasa con la sesión guardada al ABRIR la app.
// Se corren con `npm test` (node --test, sin dependencias nuevas). No llaman a la API
// real. Mensajes inventados.
//
// Antes, AuthContext.js llamaba a GET /auth/me al abrir la app y, si fallaba por
// CUALQUIER motivo (sin red, API apagada, 503, 500), borraba el token: quien abría la
// app sin internet perdía la sesión y tenía que volver a iniciarla.
// Ahora la sesión se borra SOLO si la API responde 401 (el token ya no vale: vencido,
// sesión cerrada en otro aparato o cuenta bloqueada; ver require_auth en api.py).
// Con cualquier otro error el token se queda: la app abre sin perfil y, al reabrirla
// con internet, la sesión vuelve sola. /auth/me no responde 403 (una cuenta bloqueada
// da 401) y el 404 solo pasaría si borran la cuenta en ese mismo instante: tampoco
// borran (la próxima vez que se abra la app la API ya responde 401).
//
// AuthContext.js importa react-native y Node no lo puede cargar: la decisión está en
// src/utils/sesion.js (se ejecuta de verdad) y de AuthContext se revisa el texto.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { errorDeApi } from "../src/utils/peticiones.js";
// Con "* as" la falta de la función hace fallar solo sus pruebas (no todo el archivo).
import * as sesion from "../src/utils/sesion.js";

const leer = (ruta) => readFileSync(new URL(ruta, import.meta.url), "utf8");

function debeBorrar(error) {
  assert.equal(typeof sesion.debeBorrarSesion, "function", "falta debeBorrarSesion en src/utils/sesion.js");
  return sesion.debeBorrarSesion(error);
}

// Lo que lanza apiFetch cuando la API responde con un error (status HTTP incluido)
const respuestaConError = (status, mensaje = `Error ${status}`) => errorDeApi(mensaje, status, { error: mensaje });

test("401 (el token ya no vale): SE BORRA la sesión", () => {
  assert.equal(debeBorrar(respuestaConError(401, "Token invalido o sesion expirada. Inicia sesion de nuevo")), true);
  assert.equal(debeBorrar(respuestaConError(401, "Autenticacion requerida")), true);
});

test("503, 500 y 502 (la API o la BD fallan): la sesión SE QUEDA", () => {
  for (const status of [503, 500, 502]) {
    assert.equal(debeBorrar(respuestaConError(status)), false, `status ${status}`);
  }
});

test("403, 404 y 429: la sesión SE QUEDA (solo el 401 dice que el token no vale)", () => {
  for (const status of [403, 404, 429]) {
    assert.equal(debeBorrar(respuestaConError(status)), false, `status ${status}`);
  }
});

test("sin red, tiempo agotado o dirección insegura (error sin status): la sesión SE QUEDA", () => {
  const sinRed = new TypeError("Network request failed"); // lo que lanza fetch en React Native
  const tiempoAgotado = new Error("Aborted");
  tiempoAgotado.name = "AbortError";
  // Lo que lanza apiFetch si EXPO_PUBLIC_API_URL no es segura (parte 1): sin status
  const direccionInsegura = errorDeApi(
    "la app no tiene configurada una dirección segura (https) del servidor",
    undefined,
    null,
  );
  // apiFetch con una respuesta que no es JSON lleva status: un 502 de un proxy, p. ej.
  const respuestaInvalida = errorDeApi("Error 502: respuesta inválida del servidor", 502, null);
  for (const falla of [sinRed, tiempoAgotado, direccionInsegura, respuestaInvalida]) {
    assert.equal(debeBorrar(falla), false, falla.message);
  }
});

test("errores raros (null, sin objeto, status como texto): la sesión SE QUEDA", () => {
  for (const falla of [null, undefined, "401", 401, {}, { status: "401" }]) {
    assert.equal(debeBorrar(falla), false, JSON.stringify(falla) ?? "undefined");
  }
});

// --- AuthContext.js (importa react-native: se revisa su texto) ---

test("AuthContext: al abrir la app solo borra el token si debeBorrarSesion lo dice", () => {
  const contexto = leer("../src/context/AuthContext.js");
  assert.match(contexto, /import \{[^}]*\bdebeBorrarSesion\b[^}]*\} from "\.\.\/utils\/sesion"/);
  // El catch de getPerfil() recibe el error y pregunta antes de borrar
  assert.match(
    contexto,
    /const me = await getPerfil\(\);\s*setUser\(me\);\s*\} catch \((\w+)\) \{\s*if \(debeBorrarSesion\(\1\)\) await clearToken\(\);\s*\}/,
  );
  // Ya no queda el catch que borraba ante cualquier error
  assert.doesNotMatch(contexto, /catch\s*\{\s*await clearToken\(\);/);
  // Pase lo que pase, la app deja de cargar (no se queda en la pantalla de carga)
  assert.match(contexto, /\}\s*setLoading\(false\);\s*\}\)\(\);/);
});
