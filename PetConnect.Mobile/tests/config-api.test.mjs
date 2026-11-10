// Pruebas del ítem 5.3, parte 1 (A-27): la dirección de la API y de la web sale
// de EXPO_PUBLIC_API_URL / EXPO_PUBLIC_WEB_URL y exige https:// fuera de
// desarrollo. src/services/api.js importa react-native y Node no lo puede cargar:
// se prueba la lógica pura (src/utils/configApi.js) y se lee el texto de api.js.
// Las direcciones son inventadas (ejemplo.com está reservado para pruebas).
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  HOSTS_LOCALES,
  hostDeDesarrollo,
  resolverUrlApi,
  resolverUrlPolitica,
  revisarUrl,
} from "../src/utils/configApi.js";

function leer(ruta) {
  return readFileSync(new URL(`../${ruta}`, import.meta.url), "utf8");
}

const COMPILADA = { plataforma: "android", esDesarrollo: false };
const DESARROLLO = { plataforma: "android", esDesarrollo: true };

// --- Sin variable: lo de siempre ---

test("sin variable usa el computador de desarrollo de antes (10.0.2.2 o localhost, puerto 5000)", () => {
  assert.equal(hostDeDesarrollo("android"), "10.0.2.2");
  assert.equal(hostDeDesarrollo("web"), "localhost");
  assert.equal(hostDeDesarrollo("ios"), "localhost");
  for (const vacio of [undefined, null, "", "   "]) {
    assert.deepEqual(resolverUrlApi(vacio, COMPILADA), { url: "http://10.0.2.2:5000/api", error: null });
    assert.deepEqual(resolverUrlApi(vacio, { plataforma: "web", esDesarrollo: false }), {
      url: "http://localhost:5000/api",
      error: null,
    });
  }
});

test("sin variable la política es la de Vite en el 5173", () => {
  assert.equal(resolverUrlPolitica(undefined, COMPILADA).url, "http://10.0.2.2:5173/politica-de-datos");
  assert.equal(
    resolverUrlPolitica("", { plataforma: "web", esDesarrollo: true }).url,
    "http://localhost:5173/politica-de-datos",
  );
});

// --- Con variable ---

test("con https agrega /api una sola vez y quita espacios y barras del final", () => {
  assert.equal(resolverUrlApi("https://api.ejemplo.com", COMPILADA).url, "https://api.ejemplo.com/api");
  assert.equal(resolverUrlApi("  https://api.ejemplo.com/ ", COMPILADA).url, "https://api.ejemplo.com/api");
  assert.equal(resolverUrlApi("https://api.ejemplo.com/api", COMPILADA).url, "https://api.ejemplo.com/api");
  assert.equal(resolverUrlApi("https://api.ejemplo.com/api//", COMPILADA).url, "https://api.ejemplo.com/api");
  assert.equal(
    resolverUrlApi("https://ejemplo.com:8443/petconnect", COMPILADA).url,
    "https://ejemplo.com:8443/petconnect/api",
  );
});

test("con https la política queda en /politica-de-datos de la web", () => {
  assert.deepEqual(resolverUrlPolitica("https://petconnect.ejemplo.com/", COMPILADA), {
    url: "https://petconnect.ejemplo.com/politica-de-datos",
    error: null,
  });
});

test("HTTP sin cifrar hacia otro servidor se rechaza en la app compilada", () => {
  for (const valor of ["http://api.ejemplo.com", "http://192.168.1.20:5000", "HTTP://api.ejemplo.com"]) {
    const resultado = resolverUrlApi(valor, COMPILADA);
    assert.equal(resultado.url, null, valor);
    assert.match(resultado.error, /^EXPO_PUBLIC_API_URL debe usar https:\/\//, valor);
  }
  const politica = resolverUrlPolitica("http://petconnect.ejemplo.com", COMPILADA);
  assert.equal(politica.url, null);
  assert.match(politica.error, /^EXPO_PUBLIC_WEB_URL debe usar https:\/\//);
});

test("HTTP hacia el propio computador o el emulador sí vale (export web local)", () => {
  assert.deepEqual(HOSTS_LOCALES, ["localhost", "127.0.0.1", "10.0.2.2", "[::1]"]);
  for (const valor of [
    "http://localhost:5000",
    "http://LOCALHOST:5000",
    "http://127.0.0.1:5000",
    "http://10.0.2.2:5000",
    "http://[::1]:5000",
  ]) {
    assert.equal(resolverUrlApi(valor, COMPILADA).error, null, valor);
  }
  assert.equal(resolverUrlApi("http://localhost:5000", COMPILADA).url, "http://localhost:5000/api");
});

test("un nombre que solo EMPIEZA como uno local no cuenta como local", () => {
  for (const valor of ["http://localhost.ejemplo.com", "http://10.0.2.2.ejemplo.com", "http://127.0.0.10"]) {
    assert.equal(resolverUrlApi(valor, COMPILADA).url, null, valor);
  }
});

test("en modo desarrollo (__DEV__) HTTP vale hacia la IP del PC (celular físico)", () => {
  assert.deepEqual(resolverUrlApi("http://192.168.1.20:5000", DESARROLLO), {
    url: "http://192.168.1.20:5000/api",
    error: null,
  });
});

test("rechaza lo que no es una dirección http o https", () => {
  for (const valor of [
    "api.ejemplo.com",
    "ftp://api.ejemplo.com",
    "javascript:alert(1)",
    "https://",
    "https://:5000",
    "https://api.ejemplo.com/?x=1",
    "https://api.ejemplo.com/#a",
    "https://api ejemplo.com",
  ]) {
    assert.equal(resolverUrlApi(valor, DESARROLLO).url, null, valor);
    assert.equal(revisarUrl(valor, { esDesarrollo: true }).url, undefined, valor);
  }
});

test("rechaza usuario o contraseña dentro de la dirección (quedarían a la vista en la app)", () => {
  const resultado = resolverUrlApi("https://usuario:clave@api.ejemplo.com", DESARROLLO);
  assert.equal(resultado.url, null);
  assert.equal(resultado.error, "EXPO_PUBLIC_API_URL no debe llevar usuario ni contraseña");
});

// --- api.js (se revisa su texto) ---

test("api.js lee las variables EXPO_PUBLIC_ como Expo exige (process.env.NOMBRE, con punto)", () => {
  const codigo = leer("src/services/api.js");
  // Expo solo reemplaza process.env.EXPO_PUBLIC_X escrito así; con corchetes o
  // desestructurando queda vacío al compilar.
  assert.match(codigo, /resolverUrlApi\(process\.env\.EXPO_PUBLIC_API_URL, /);
  assert.match(codigo, /resolverUrlPolitica\(process\.env\.EXPO_PUBLIC_WEB_URL, /);
  assert.doesNotMatch(codigo, /process\.env\[/);
  assert.doesNotMatch(codigo, /\}\s*=\s*process\.env/);
  // Ya no hay direcciones http:// escritas a mano
  assert.doesNotMatch(codigo, /http:\/\//);
  assert.doesNotMatch(codigo, /Platform\.select/);
});

test("api.js no llama a fetch si la dirección no es segura", () => {
  const codigo = leer("src/services/api.js");
  const apiFetch = codigo.slice(codigo.indexOf("async function apiFetch"));
  const revisa = apiFetch.indexOf("if (!API_BASE)");
  assert.ok(revisa > -1, "apiFetch debe revisar API_BASE");
  assert.ok(revisa < apiFetch.indexOf("fetch(`"), "la revisión va antes de fetch");
  assert.match(apiFetch, /if \(!API_BASE\) throw errorDeApi\(/);
});

test("la plantilla .env.example del móvil existe y no trae valores", () => {
  const plantilla = leer(".env.example");
  const lineas = plantilla.split(/\r?\n/).filter((l) => l.trim() && !l.trim().startsWith("#"));
  assert.deepEqual(lineas.map((l) => l.trim()), ["EXPO_PUBLIC_API_URL=", "EXPO_PUBLIC_WEB_URL="]);
  assert.match(plantilla, /visible/i, "debe avisar que todo lo EXPO_PUBLIC_ queda a la vista");
});
