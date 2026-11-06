// Ítem 3.4 (A-22): la tabla mascotas no tiene vacunación, esterilización ni
// tamaño, y desde la parte 1 la API ya no los manda. Antes el móvil mostraba
// "Talla undefined" y las insignias "Vacunada: No / Esterilizada: No" en TODAS
// las fichas (un dato de salud inventado). Esta prueba impide que vuelvan a
// src/. Igual que la de la web, también cuenta los comentarios.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readdirSync, readFileSync } from "node:fs";
import { join, relative } from "node:path";
import { fileURLToPath } from "node:url";

const SRC = fileURLToPath(new URL("../src", import.meta.url));
const PROHIBIDO = /\bvaccinated\b|\bsterilized\b|\.size\b|\bTalla\b|\bVacunad[ao]\b|\bEsterilizad[ao]\b/;

function archivosDeCodigo(carpeta) {
  return readdirSync(carpeta, { withFileTypes: true }).flatMap((e) => {
    const ruta = join(carpeta, e.name);
    if (e.isDirectory()) return archivosDeCodigo(ruta);
    return /\.(js|jsx)$/.test(e.name) ? [ruta] : [];
  });
}

test("ningún archivo de src/ muestra vacunación, esterilización ni tamaño inventados", () => {
  const culpables = archivosDeCodigo(SRC)
    .filter((ruta) => PROHIBIDO.test(readFileSync(ruta, "utf8")))
    .map((ruta) => relative(SRC, ruta));
  assert.deepEqual(culpables, []);
});
