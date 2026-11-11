// Ítem 5.4, parte 3 (A-29): dependencias del móvil sin vulnerabilidades altas ni críticas.
// Se corre con `npm test` (node --test). No necesita internet: lee como texto el
// package.json, el package-lock.json y la CI (.github/workflows/ci.yml). La consulta
// real a los avisos del día la hace `npm audit` (en tu PC y en la CI).
//
// Lo que se vigila:
// - El 10/11/2026 `npm audit` dio 27 (1 crítica, 14 altas, 11 moderadas, 1 baja), casi
//   todas en herramientas de Expo y Metro. Se arreglaron SIN subir de versión mayor:
//   los parches que el SDK 57 espera (`npx expo install --check`) puestos a mano en el
//   package.json y luego `npm audit fix` (sin --force). Quedan 4 moderadas en
//   @expo/fingerprint (glob y minimatch), herramienta de compilación que Expo 58
//   tampoco arregla. Si alguien vuelve a una versión vulnerable, esta prueba falla.
// - La CI corre `npm audit` en el trabajo "movil" después de `npm ci` y falla con
//   avisos altos o críticos (nunca "fix", --force ni continue-on-error).
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const RAIZ = fileURLToPath(new URL("..", import.meta.url));
const RAIZ_REPO = join(RAIZ, "..");
const leerJson = (nombre) => JSON.parse(readFileSync(join(RAIZ, nombre), "utf8"));

// Parches del SDK 57 que pedía `npx expo install --check` el 11/11/2026.
const PAQUETE_MINIMO = {
  expo: "57.0.32",
  "@expo/metro-runtime": "57.0.18",
  "react-native": "0.86.3",
  "react-native-screens": "4.26.0",
};

// Primera versión SIN los avisos altos o críticos del 10/11/2026 (rango de npm audit).
// "puedeFaltar": el paquete desapareció con el arreglo (nadie lo pide ya); si vuelve,
// debe venir corregido.
const LOCK_MINIMO = {
  "shell-quote": { minima: "1.11.0" }, // la crítica (react-devtools-core)
  "node-forge": { minima: "1.4.3" },
  compression: { minima: "1.8.2" },
  "js-yaml": { minima: "4.3.1" },
  browserslist: { minima: "4.28.7" },
  nanoid: { minima: "3.3.18" },
  "source-map-js": { minima: "1.2.2" },
  metro: { minima: "0.84.5" }, // desde aquí Metro ya no usa image-size
  "image-size": { minima: "2.0.3", puedeFaltar: true },
  zod: { minima: "4.6.6", puedeFaltar: true },
  "decode-uri-component": { minima: "0.5.1", puedeFaltar: true },
};

// "~57.0.32" o "0.86.3" → [57, 0, 32]
const numeros = (version) => version.replace(/^[~^]/, "").split(".").map(Number);
function esMenor(a, b) {
  const [pa, pb] = [numeros(a), numeros(b)];
  for (let i = 0; i < 3; i++) if (pa[i] !== pb[i]) return pa[i] < pb[i];
  return false;
}

function copiasEnElLock(nombre) {
  const lock = leerJson("package-lock.json");
  return Object.entries(lock.packages)
    .filter(([ruta]) => ruta === `node_modules/${nombre}` || ruta.endsWith(`/node_modules/${nombre}`))
    .map(([ruta, datos]) => ({ ruta, version: datos.version }));
}

// Pasos del trabajo "movil" de la CI, sin comentarios.
function pasosDelTrabajoMovil() {
  const lineas = readFileSync(join(RAIZ_REPO, ".github", "workflows", "ci.yml"), "utf8").split(/\r?\n/);
  const inicio = lineas.findIndex((l) => /^ {2}movil:\s*$/.test(l));
  assert.ok(inicio >= 0, "la CI no tiene el trabajo 'movil'");
  const fin = lineas.findIndex((l, i) => i > inicio && /^ {2}\S/.test(l));
  const pasos = [];
  for (const linea of lineas.slice(inicio, fin === -1 ? undefined : fin)) {
    if (/^\s*#/.test(linea)) continue;
    if (/^ {6}- /.test(linea)) pasos.push("");
    if (pasos.length) pasos[pasos.length - 1] += linea.trim() + "\n";
  }
  return pasos;
}

test("el package.json pide los parches del SDK 57 que corrigen los avisos", () => {
  const { dependencies } = leerJson("package.json");
  for (const [nombre, minima] of Object.entries(PAQUETE_MINIMO)) {
    assert.ok(dependencies[nombre], `falta ${nombre} en package.json`);
    assert.ok(!esMenor(dependencies[nombre], minima), `${nombre} ${dependencies[nombre]}: debe ser ${minima} o más nueva`);
  }
});

test("el lock no trae versiones con los avisos altos o críticos del 10/11/2026", () => {
  for (const [nombre, { minima, puedeFaltar }] of Object.entries(LOCK_MINIMO)) {
    const copias = copiasEnElLock(nombre);
    if (!puedeFaltar) assert.ok(copias.length > 0, `${nombre} ya no está en el lock: revisa esta prueba`);
    for (const { ruta, version } of copias) {
      assert.ok(!esMenor(version, minima), `${ruta} está en ${version}; debe ser ${minima} o más nueva`);
    }
  }
});

test("la CI audita las dependencias del móvil después de npm ci", () => {
  const pasos = pasosDelTrabajoMovil();
  const iNpmCi = pasos.findIndex((p) => /run:\s*npm ci\b/.test(p));
  const iAudit = pasos.findIndex((p) => /run:\s*npm audit\b/.test(p));
  assert.ok(iNpmCi >= 0, "falta el paso npm ci");
  assert.ok(iAudit >= 0, "falta el paso npm audit en el trabajo movil");
  assert.ok(iAudit > iNpmCi, "npm audit debe ir después de npm ci");
});

test("el paso de npm audit falla con avisos altos y no arregla nada solo", () => {
  const paso = pasosDelTrabajoMovil().find((p) => /run:\s*npm audit\b/.test(p));
  assert.ok(paso, "falta el paso npm audit");
  assert.doesNotMatch(paso, /npm audit fix/, "la CI solo revisa; el arreglo se hace a mano");
  assert.doesNotMatch(paso, /--force/);
  assert.doesNotMatch(paso, /continue-on-error/, "si queda en 'solo avisar', nadie lo mira");
  assert.doesNotMatch(paso, /\|\|\s*true/);
  // Sin --audit-level falla desde "low"; "critical" dejaría pasar las altas.
  const nivel = paso.match(/--audit-level[= ](\w+)/);
  if (nivel) assert.match(nivel[1], /^(low|moderate|high)$/, `nivel ${nivel[1]}: debe fallar al menos con las altas`);
});
