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

const { getMascota, getMascotasAdopcion, getProductos } = await import(
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
