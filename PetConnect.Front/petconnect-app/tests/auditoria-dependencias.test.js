// Ítem 5.4, parte 1 (A-29): dependencias de la web sin vulnerabilidades conocidas.
// Se corre con `npm test` (node --test). No necesita internet: lee como texto el
// package-lock.json y la CI (.github/workflows/ci.yml). La consulta real a los
// avisos del día la hace `npm audit` (en tu PC y en la CI).
//
// Lo que se vigila:
// - El 10/11/2026 `npm audit` dio 6 altas: react-router / react-router-dom
//   (CSRF en modo RSC, que la app no usa), vite (fallos del servidor de
//   desarrollo, el de `npm run dev`), postcss, nanoid y source-map-js (herramientas
//   de compilación). `npm audit fix` (sin --force) las corrigió cambiando solo el
//   lock. Si alguien devuelve el lock a una versión vulnerable, esta prueba falla.
// - La CI corre `npm audit` en el trabajo "web" después de `npm ci` y falla con
//   avisos altos o críticos (nunca "fix", nunca --force, nunca continue-on-error).
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const RAIZ = fileURLToPath(new URL("..", import.meta.url));
const RAIZ_REPO = join(RAIZ, "..", "..");

// Primera versión SIN cada aviso del 10/11/2026 (sacada del rango de npm audit).
const VERSION_MINIMA = {
  "react-router": "7.18.2",
  "react-router-dom": "7.18.2",
  vite: "8.1.6",
  postcss: "8.5.23",
  nanoid: "3.3.18",
  "source-map-js": "1.2.2",
};

// "8.3.8" → [8, 3, 8]; compara número por número.
function esMenor(a, b) {
  const pa = a.split(".").map(Number);
  const pb = b.split(".").map(Number);
  for (let i = 0; i < 3; i++) {
    if (pa[i] !== pb[i]) return pa[i] < pb[i];
  }
  return false;
}

// Todas las copias de un paquete en el lock (puede haber anidadas:
// node_modules/x/node_modules/nanoid).
function copiasEnElLock(nombre) {
  const lock = JSON.parse(readFileSync(join(RAIZ, "package-lock.json"), "utf8"));
  return Object.entries(lock.packages)
    .filter(([ruta]) => ruta === `node_modules/${nombre}` || ruta.endsWith(`/node_modules/${nombre}`))
    .map(([ruta, datos]) => ({ ruta, version: datos.version }));
}

// Texto del trabajo "web" de la CI: desde "  web:" hasta el siguiente trabajo.
function trabajoWebDeLaCi() {
  const lineas = readFileSync(join(RAIZ_REPO, ".github", "workflows", "ci.yml"), "utf8").split(/\r?\n/);
  const inicio = lineas.findIndex((l) => /^ {2}web:\s*$/.test(l));
  assert.ok(inicio >= 0, "la CI no tiene el trabajo 'web'");
  const fin = lineas.findIndex((l, i) => i > inicio && /^ {2}\S/.test(l));
  return lineas.slice(inicio, fin === -1 ? undefined : fin);
}

// Pasos del trabajo: cada uno empieza con "      - "; sin comentarios.
function pasosDelTrabajoWeb() {
  const pasos = [];
  for (const linea of trabajoWebDeLaCi()) {
    if (/^\s*#/.test(linea)) continue;
    if (/^ {6}- /.test(linea)) pasos.push("");
    if (pasos.length) pasos[pasos.length - 1] += linea.trim() + "\n";
  }
  return pasos;
}

test("el lock no trae versiones con los avisos del 10/11/2026", () => {
  for (const [nombre, minima] of Object.entries(VERSION_MINIMA)) {
    const copias = copiasEnElLock(nombre);
    assert.ok(copias.length > 0, `${nombre} ya no está en el lock: revisa esta prueba`);
    for (const { ruta, version } of copias) {
      assert.ok(!esMenor(version, minima), `${ruta} está en ${version}; debe ser ${minima} o más nueva`);
    }
  }
});

test("la CI audita las dependencias de la web después de npm ci", () => {
  const pasos = pasosDelTrabajoWeb();
  const iNpmCi = pasos.findIndex((p) => /run:\s*npm ci\b/.test(p));
  const iAudit = pasos.findIndex((p) => /run:\s*npm audit\b/.test(p));
  assert.ok(iNpmCi >= 0, "falta el paso npm ci");
  assert.ok(iAudit >= 0, "falta el paso npm audit en el trabajo web");
  assert.ok(iAudit > iNpmCi, "npm audit debe ir después de npm ci");
});

test("el paso de npm audit falla con avisos altos y no arregla nada solo", () => {
  const paso = pasosDelTrabajoWeb().find((p) => /run:\s*npm audit\b/.test(p));
  assert.ok(paso, "falta el paso npm audit");
  assert.doesNotMatch(paso, /npm audit fix/, "la CI solo revisa; el arreglo se hace a mano");
  assert.doesNotMatch(paso, /--force/);
  assert.doesNotMatch(paso, /continue-on-error/, "si queda en 'solo avisar', nadie lo mira");
  assert.doesNotMatch(paso, /--omit[= ]dev/, "vite es de desarrollo y sus fallos te afectan al usar npm run dev");
  // Sin --audit-level falla desde "low"; "critical" dejaría pasar las altas.
  const nivel = paso.match(/--audit-level[= ](\w+)/);
  if (nivel) assert.match(nivel[1], /^(low|moderate|high)$/, `nivel ${nivel[1]}: debe fallar al menos con las altas`);
});
