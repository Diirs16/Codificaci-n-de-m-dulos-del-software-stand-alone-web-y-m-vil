// Pruebas del ítem 4.17 (NC-003, A-11): el móvil pide los listados por páginas.
// Mismos casos que la web (PetConnect.Front/petconnect-app/tests/paginacion.test.js).
// src/services/api.js importa react-native y Node no lo puede cargar: por eso se
// prueba la lógica pura (src/utils/paginacion.js) y se lee el código de las pantallas.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  POR_PAGINA_ADOPCION,
  POR_PAGINA_CATALOGO,
  hayMas,
  rutaPaginada,
  unirSinRepetir,
} from "../src/utils/paginacion.js";

function leer(ruta) {
  return readFileSync(new URL(`../src/${ruta}`, import.meta.url), "utf8");
}

// --- rutaPaginada ---

test("rutaPaginada agrega pagina y por_pagina a la ruta", () => {
  assert.equal(rutaPaginada("/productos", { pagina: 2, porPagina: 20 }), "/productos?pagina=2&por_pagina=20");
  assert.equal(rutaPaginada("/mascotas/adopcion", { pagina: 1 }), "/mascotas/adopcion?pagina=1");
  assert.equal(rutaPaginada("/productos", { porPagina: 12 }), "/productos?por_pagina=12");
});

test("rutaPaginada sin opciones deja la ruta igual (la API usa sus valores por defecto)", () => {
  assert.equal(rutaPaginada("/productos"), "/productos");
  assert.equal(rutaPaginada("/productos", {}), "/productos");
});

test("rutaPaginada ignora lo que no es un entero positivo (nunca manda basura a la API)", () => {
  for (const malo of [0, -1, 1.5, NaN, "2", null, undefined, Infinity]) {
    assert.equal(rutaPaginada("/productos", { pagina: malo, porPagina: malo }), "/productos", String(malo));
  }
});

// --- hayMas y unirSinRepetir ---

test("hayMas: una página llena puede tener otra después; una incompleta es la última", () => {
  assert.equal(hayMas(new Array(12).fill({}), 12), true);
  assert.equal(hayMas(new Array(11).fill({}), 12), false);
  assert.equal(hayMas([], 12), false);
  assert.equal(hayMas(undefined, 12), false);
});

test("unirSinRepetir agrega al final sin repetir ids y sin cambiar el orden", () => {
  const actuales = [{ id: 1 }, { id: 2 }];
  const nuevos = [{ id: 2 }, { id: 3 }, { id: 4 }];
  assert.deepEqual(unirSinRepetir(actuales, nuevos), [{ id: 1 }, { id: 2 }, { id: 3 }, { id: 4 }]);
  assert.deepEqual(actuales, [{ id: 1 }, { id: 2 }]); // no modifica la lista de antes
  assert.deepEqual(unirSinRepetir([], []), []);
});

test("los tamaños de página respetan el máximo de la API (50)", () => {
  for (const tamano of [POR_PAGINA_CATALOGO, POR_PAGINA_ADOPCION]) {
    assert.ok(Number.isInteger(tamano) && tamano > 0 && tamano <= 50, String(tamano));
  }
});

// --- api.js y pantallas (se lee el código, no se ejecuta React Native) ---

test("api.js arma la ruta de los dos listados con rutaPaginada", () => {
  const api = leer("services/api.js");
  assert.match(api, /export function getProductos\(opciones\)\s*\{\s*return apiFetch\(rutaPaginada\("\/productos", opciones\)\)/);
  assert.match(
    api,
    /export function getMascotasAdopcion\(opciones\)\s*\{\s*return apiFetch\(rutaPaginada\("\/mascotas\/adopcion", opciones\)\)/,
  );
});

test("el catálogo y la adopción cargan por páginas con 'Ver más' al pie de la lista", () => {
  const casos = [
    ["screens/HomeScreen.js", /useListaPaginada\(\s*getProductos,\s*POR_PAGINA_CATALOGO\s*\)/],
    ["screens/AdoptionScreen.js", /useListaPaginada\(\s*getMascotasAdopcion,\s*POR_PAGINA_ADOPCION\s*\)/],
  ];
  for (const [ruta, usaPaginacion] of casos) {
    const codigo = leer(ruta);
    assert.match(codigo, usaPaginacion, ruta);
    assert.match(codigo, /ListFooterComponent=\{\s*<BotonVerMas\b/, ruta);
  }
});
