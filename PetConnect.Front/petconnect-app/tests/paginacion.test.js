// Pruebas del ítem 4.17 (NC-003, A-11): la web pide los listados por páginas.
// Se corren con `npm test` (node --test). No se llama a ninguna API real:
// `fetch` se reemplaza por uno falso que guarda la ruta que se pidió.
import { test, beforeEach, afterEach } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

import {
  POR_PAGINA_ADOPCION,
  POR_PAGINA_CATALOGO,
  POR_PAGINA_DESTACADOS,
  hayMas,
  rutaPaginada,
  unirSinRepetir,
} from "../src/utils/paginacion.js";

// api.js lee el token de localStorage, que en Node no existe como en el navegador.
Object.defineProperty(globalThis, "localStorage", {
  value: { getItem: () => null },
  configurable: true,
  writable: true,
});

const { getMascotasAdopcion, getProductos } = await import("../src/services/api.js");

const fetchOriginal = globalThis.fetch;
let rutasPedidas;

beforeEach(() => {
  rutasPedidas = [];
  globalThis.fetch = async (url) => {
    rutasPedidas.push(url);
    return new Response("[]", { status: 200, headers: { "Content-Type": "application/json" } });
  };
});

afterEach(() => {
  globalThis.fetch = fetchOriginal;
});

// --- rutaPaginada ---

test("rutaPaginada agrega pagina y por_pagina a la ruta", () => {
  assert.equal(rutaPaginada("/productos", { pagina: 2, porPagina: 50 }), "/productos?pagina=2&por_pagina=50");
  assert.equal(rutaPaginada("/mascotas/adopcion", { pagina: 1 }), "/mascotas/adopcion?pagina=1");
  assert.equal(rutaPaginada("/productos", { porPagina: 4 }), "/productos?por_pagina=4");
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

// --- hayMas ---

test("hayMas: una página llena puede tener otra después; una incompleta es la última", () => {
  assert.equal(hayMas(new Array(12).fill({}), 12), true);
  assert.equal(hayMas(new Array(11).fill({}), 12), false);
  assert.equal(hayMas([], 12), false);
  assert.equal(hayMas(undefined, 12), false);
});

// --- unirSinRepetir ---

test("unirSinRepetir agrega al final sin repetir ids y sin cambiar el orden", () => {
  const actuales = [{ id: 1 }, { id: 2 }];
  const nuevos = [{ id: 2 }, { id: 3 }, { id: 4 }];
  assert.deepEqual(unirSinRepetir(actuales, nuevos), [{ id: 1 }, { id: 2 }, { id: 3 }, { id: 4 }]);
  assert.deepEqual(actuales, [{ id: 1 }, { id: 2 }]); // no modifica la lista de antes
  assert.deepEqual(unirSinRepetir([], []), []);
});

// --- api.js ---

test("getProductos y getMascotasAdopcion piden la página indicada", async () => {
  await getProductos({ pagina: 3, porPagina: POR_PAGINA_CATALOGO });
  await getMascotasAdopcion({ pagina: 2, porPagina: POR_PAGINA_ADOPCION });
  assert.deepEqual(rutasPedidas, [
    "/api/productos?pagina=3&por_pagina=50",
    "/api/mascotas/adopcion?pagina=2&por_pagina=12",
  ]);
});

test("sin opciones siguen pidiendo la ruta de siempre", async () => {
  await getProductos();
  await getMascotasAdopcion();
  assert.deepEqual(rutasPedidas, ["/api/productos", "/api/mascotas/adopcion"]);
});

// --- Las páginas usan la paginación (se lee el código, no se ejecuta React) ---

function leer(ruta) {
  return readFileSync(new URL(`../src/${ruta}`, import.meta.url), "utf8");
}

test("los tamaños de página respetan el máximo de la API (50)", () => {
  for (const tamano of [POR_PAGINA_DESTACADOS, POR_PAGINA_ADOPCION, POR_PAGINA_CATALOGO]) {
    assert.ok(Number.isInteger(tamano) && tamano > 0 && tamano <= 50, String(tamano));
  }
});

test("Home pide solo los productos destacados (antes pedía todos y recortaba)", () => {
  const home = leer("pages/Home.jsx");
  assert.match(home, /getProductos\(\{\s*pagina:\s*1,\s*porPagina:\s*POR_PAGINA_DESTACADOS\s*\}\)/);
  assert.doesNotMatch(home, /\.slice\(/);
});

test("Adopción y Catálogo cargan por páginas con 'Ver más'", () => {
  const casos = [
    ["pages/Adoption.jsx", /useListaPaginada\(\s*getMascotasAdopcion,\s*POR_PAGINA_ADOPCION\s*\)/],
    ["pages/Catalog.jsx", /useListaPaginada\(\s*getProductos,\s*POR_PAGINA_CATALOGO\s*\)/],
  ];
  for (const [ruta, usaPaginacion] of casos) {
    const codigo = leer(ruta);
    assert.match(codigo, usaPaginacion, ruta);
    assert.match(codigo, /<BotonVerMas\b/, ruta);
  }
});
