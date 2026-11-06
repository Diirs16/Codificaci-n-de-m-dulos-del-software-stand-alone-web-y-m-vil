// Ítem 3.3 (A-23, NC-009): la web escondía los fallos de la API mostrando
// mascotas y productos inventados de src/data/pets.js y src/data/products.js.
// Esta prueba impide que vuelvan: ningún archivo de src/ puede importar una
// carpeta data/ (los datos salen solo de la API).
import { test } from "node:test";
import assert from "node:assert/strict";
import { readdirSync, readFileSync } from "node:fs";
import { join, relative } from "node:path";
import { fileURLToPath } from "node:url";

const SRC = fileURLToPath(new URL("../src", import.meta.url));
const IMPORTA_DATA = /from\s+["'][^"']*\/data\/[^"']*["']/;

function archivosDeCodigo(carpeta) {
  return readdirSync(carpeta, { withFileTypes: true }).flatMap((e) => {
    const ruta = join(carpeta, e.name);
    if (e.isDirectory()) return archivosDeCodigo(ruta);
    return /\.(js|jsx)$/.test(e.name) ? [ruta] : [];
  });
}

test("ningún archivo de src/ importa datos falsos de data/", () => {
  const culpables = archivosDeCodigo(SRC)
    .filter((ruta) => IMPORTA_DATA.test(readFileSync(ruta, "utf8")))
    .map((ruta) => relative(SRC, ruta));
  assert.deepEqual(culpables, []);
});
