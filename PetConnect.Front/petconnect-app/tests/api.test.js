// Pruebas de src/services/api.js (ítem 3.3, A-23, NC-009).
// Se corren con `npm test` (node --test, que viene con Node: sin dependencias nuevas).
//
// La web ya no muestra datos falsos cuando la API falla: muestra un error. Para
// eso cada error que lanza api.js lleva `status` (el número de respuesta HTTP),
// y así la ficha distingue "no encontrada" (404) de "no pudimos cargar" (503, 502
// o 0 si el servidor ni siquiera respondió).
//
// Aquí no se llama a ninguna API real: `fetch` se reemplaza por uno falso que
// devuelve la respuesta que cada prueba elige.
import { test, beforeEach, afterEach } from "node:test";
import assert from "node:assert/strict";

// api.js lee el token de localStorage, que en Node no existe como en el navegador.
Object.defineProperty(globalThis, "localStorage", {
  value: { getItem: () => null },
  configurable: true,
  writable: true,
});

const { getMascota, getMascotasAdopcion, getProductos, loginUser, verifyLoginCode } = await import(
  "../src/services/api.js"
);

const fetchOriginal = globalThis.fetch;

// Respuesta falsa: `cuerpo` es un objeto (se manda como JSON) o un texto.
function responder(status, cuerpo) {
  globalThis.fetch = async () =>
    new Response(typeof cuerpo === "string" ? cuerpo : JSON.stringify(cuerpo), {
      status,
      headers: { "Content-Type": "application/json" },
    });
}

beforeEach(() => {
  globalThis.fetch = fetchOriginal;
});

afterEach(() => {
  globalThis.fetch = fetchOriginal;
});

test("404 de una mascota: el error trae status 404 y el mensaje de la API", async () => {
  responder(404, { error: "Mascota no encontrada" });
  await assert.rejects(getMascota(99), (e) => {
    assert.equal(e.status, 404);
    assert.equal(e.message, "Mascota no encontrada");
    return true;
  });
});

test("503 (BD caída): el error trae status 503, no es un 'no encontrada'", async () => {
  responder(503, { error: "Servicio no disponible" });
  await assert.rejects(getMascotasAdopcion(), (e) => {
    assert.equal(e.status, 503);
    return true;
  });
});

test("502 sin cuerpo (proxy de Vite con la API apagada): status 502", async () => {
  responder(502, "");
  await assert.rejects(getProductos(), (e) => {
    assert.equal(e.status, 502);
    return true;
  });
});

test("el servidor no responde (fetch falla): status 0 y mensaje en español", async () => {
  globalThis.fetch = async () => {
    throw new TypeError("Failed to fetch");
  };
  await assert.rejects(getMascota(1), (e) => {
    assert.equal(e.status, 0);
    assert.match(e.message, /conectar/);
    return true;
  });
});

test("respuesta correcta: devuelve los datos tal cual (lista vacía incluida)", async () => {
  responder(200, []);
  assert.deepEqual(await getMascotasAdopcion(), []);
});

// --- Ítem 3.5 (A-20, R05): autorización de datos al iniciar sesión ---
// La API responde 403 con "requiere_autorizacion": true a las cuentas sin
// autorización vigente. La web debe reconocerlo (para mostrar la casilla) y
// mandar "acepta_datos": true SOLO cuando la persona marcó la casilla.
// Los correos y contraseñas de estas pruebas son inventados.

// fetch falso que guarda el cuerpo enviado para revisarlo después.
function capturarCuerpo(status, respuesta) {
  const enviados = [];
  globalThis.fetch = async (_url, opciones) => {
    enviados.push(JSON.parse(opciones.body));
    return new Response(JSON.stringify(respuesta), {
      status,
      headers: { "Content-Type": "application/json" },
    });
  };
  return enviados;
}

test("loginUser con la casilla marcada manda acepta_datos como booleano true", async () => {
  const enviados = capturarCuerpo(200, { message: "Codigo enviado" });
  await loginUser("ana@ejemplo.test", "Clave@123", true);
  assert.equal(enviados.length, 1);
  assert.equal(enviados[0].acepta_datos, true);
});

test("loginUser sin la casilla NO manda acepta_datos (ni con valores parecidos a true)", async () => {
  const enviados = capturarCuerpo(200, { message: "Codigo enviado" });
  await loginUser("ana@ejemplo.test", "Clave@123");
  await loginUser("ana@ejemplo.test", "Clave@123", "true");
  await loginUser("ana@ejemplo.test", "Clave@123", 1);
  for (const cuerpo of enviados) {
    assert.deepEqual(Object.keys(cuerpo).sort(), ["email", "password"]);
  }
});

test("403 con requiere_autorizacion: el error trae requiereAutorizacion y el mensaje", async () => {
  responder(403, {
    error: "Para seguir usando tu cuenta debes autorizar el tratamiento de tus datos personales",
    requiere_autorizacion: true,
  });
  await assert.rejects(loginUser("ana@ejemplo.test", "Clave@123"), (e) => {
    assert.equal(e.status, 403);
    assert.equal(e.requiereAutorizacion, true);
    assert.match(e.message, /autorizar el tratamiento/);
    return true;
  });
});

test("403 de /login/verify con requiere_autorizacion también lo trae", async () => {
  responder(403, { error: "Para seguir usando tu cuenta...", requiere_autorizacion: true });
  await assert.rejects(verifyLoginCode("ana@ejemplo.test", "123456"), (e) => {
    assert.equal(e.requiereAutorizacion, true);
    return true;
  });
});

test("otro 403 (cuenta inactiva) NO pide la casilla", async () => {
  responder(403, { error: "Cuenta inactiva o bloqueada" });
  await assert.rejects(loginUser("ana@ejemplo.test", "Clave@123"), (e) => {
    assert.equal(e.status, 403);
    assert.equal(e.requiereAutorizacion, false);
    return true;
  });
});
