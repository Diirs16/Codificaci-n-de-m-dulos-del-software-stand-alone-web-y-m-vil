// Pruebas del ítem 5.5, parte 3: la web en Vercel llama a la API de Railway.
// Se corren con `npm test` (node --test). No llaman a ninguna API real.
//
// Revisan:
// - resolverBaseApi (src/utils/configApi.js): VITE_API_URL vacía = "/api" como
//   antes; con valor exige https:// (salvo localhost), agrega /api y rechaza
//   usuario:clave@, ?consulta y #ancla.
// - api.js: usa esa función con import.meta.env.VITE_API_URL y, si la
//   dirección no sirve, falla sin llamar a fetch.
// - vercel.json: recargar /catalogo no da 404 y no reenvía /api a ningún lado
//   (con un rewrite todos los visitantes llegarían a la API con la IP de Vercel
//   y compartirían el límite de 5 intentos por minuto).
// - .env.example: solo VITE_API_URL, vacía.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

import { resolverBaseApi, BASE_LOCAL } from "../src/utils/configApi.js";

const leer = (ruta) => readFileSync(new URL(`../${ruta}`, import.meta.url), "utf8");
const RAILWAY = "https://api-production-ejemplo.up.railway.app";   // inventada

test("vacía o sin definir: /api, como en desarrollo y Docker", () => {
  for (const valor of [undefined, null, "", "   "]) {
    assert.deepEqual(resolverBaseApi(valor), { base: BASE_LOCAL, error: null });
  }
  assert.equal(BASE_LOCAL, "/api");
});

test("https: agrega /api y quita las barras del final", () => {
  assert.equal(resolverBaseApi(RAILWAY).base, `${RAILWAY}/api`);
  assert.equal(resolverBaseApi(`${RAILWAY}/`).base, `${RAILWAY}/api`);
  assert.equal(resolverBaseApi(`${RAILWAY}/api`).base, `${RAILWAY}/api`);
  assert.equal(resolverBaseApi(`  ${RAILWAY}/api/  `).base, `${RAILWAY}/api`);
  assert.equal(resolverBaseApi("https://api.ejemplo.test:8443").base, "https://api.ejemplo.test:8443/api");
});

test("http solo hacia este computador", () => {
  assert.equal(resolverBaseApi("http://localhost:5000").base, "http://localhost:5000/api");
  assert.equal(resolverBaseApi("http://127.0.0.1:5000").base, "http://127.0.0.1:5000/api");
  assert.equal(resolverBaseApi("http://[::1]:5000").base, "http://[::1]:5000/api");
  for (const valor of ["http://api-production-ejemplo.up.railway.app", "http://localhost.ejemplo.test",
    "HTTP://api.ejemplo.test"]) {
    const r = resolverBaseApi(valor);
    assert.equal(r.base, null, valor);
    assert.match(r.error, /https/);
  }
});

test("rechaza direcciones mal escritas o con datos a la vista", () => {
  const malas = [
    "api.ejemplo.test",                          // sin protocolo
    "ftp://api.ejemplo.test",
    "https://usuario:clave@api.ejemplo.test",    // la clave quedaría en la página
    "https://api.ejemplo.test/?token=abc",
    "https://api.ejemplo.test/#x",
    "https://api ejemplo.test",
    "https://",
    "javascript:alert(1)",
  ];
  for (const valor of malas) {
    const r = resolverBaseApi(valor);
    assert.equal(r.base, null, valor);
    assert.match(r.error, /^VITE_API_URL /);
    assert.ok(!r.error.includes("clave@"), "el error no repite el valor");
  }
});

test("api.js usa VITE_API_URL y no llama a fetch si la dirección no sirve", () => {
  const codigo = leer("src/services/api.js");
  assert.match(codigo, /import \{ resolverBaseApi \} from "\.\.\/utils\/configApi\.js"/);
  assert.match(codigo, /resolverBaseApi\(import\.meta\.env\?\.VITE_API_URL\)/);
  assert.doesNotMatch(codigo, /const API_BASE = "\/api"/, "la dirección ya no va fija");
  const guardia = codigo.indexOf("if (!API_BASE)");
  const llamada = codigo.indexOf("await fetch(");
  assert.ok(guardia > -1 && guardia < llamada, "la revisión va antes de fetch");
});

test("vercel.json: las rutas de React van a index.html y /api no se reenvía", () => {
  const config = JSON.parse(leer("vercel.json"));
  assert.deepEqual(config.rewrites, [{ source: "/(.*)", destination: "/index.html" }]);
  const texto = JSON.stringify(config);
  assert.doesNotMatch(texto, /railway|https?:\/\/(?!openapi\.vercel\.sh)/i, "sin direcciones de afuera");
  assert.equal(config.env, undefined, "las variables van en el panel de Vercel");
  assert.equal(config.build, undefined);
});

test(".env.example: solo VITE_API_URL y vacía", () => {
  const variables = leer(".env" + ".example")
    .split(/\r?\n/)
    .map((l) => l.trim())
    .filter((l) => l && !l.startsWith("#"));
  assert.deepEqual(variables, ["VITE_API_URL="]);
});
