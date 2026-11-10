// Pruebas del ítem 5.3, parte 2 (A-28): el token del móvil va cifrado en
// expo-secure-store y el que quedó en AsyncStorage se pasa ahí y se borra.
// src/services/api.js importa react-native y Node no lo puede cargar: se prueba
// la lógica pura (src/utils/almacenToken.js) con almacenes falsos y se lee el
// texto de api.js. Los tokens son inventados.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { CLAVE_TOKEN, crearAlmacenToken, tieneAlmacenSeguro } from "../src/utils/almacenToken.js";

function leer(ruta) {
  return readFileSync(new URL(`../${ruta}`, import.meta.url), "utf8");
}

// AsyncStorage falso (texto plano), en memoria y con promesas como el real.
// `fallar` hace que esa operación rechace.
function almacenViejo(inicial = {}, fallar = {}) {
  const datos = new Map(Object.entries(inicial));
  return {
    datos,
    getItem: async (clave) => (datos.has(clave) ? datos.get(clave) : null),
    setItem: async (clave, valor) => {
      if (fallar.setItem) throw new Error("disco lleno");
      datos.set(clave, valor);
    },
    removeItem: async (clave) => void datos.delete(clave),
  };
}

// SecureStore falso, con los mismos nombres que expo-secure-store. `fallar` hace
// que esa operación rechace, como cuando el Keystore no acepta el valor.
function almacenSeguro(inicial = {}, fallar = {}) {
  const datos = new Map(Object.entries(inicial));
  return {
    datos,
    getItemAsync: async (clave) => {
      if (fallar.getItemAsync) throw new Error("Keystore no disponible");
      return datos.has(clave) ? datos.get(clave) : null;
    },
    setItemAsync: async (clave, valor) => {
      if (fallar.setItemAsync) throw new Error("Keystore no acepta el valor");
      datos.set(clave, valor);
    },
    deleteItemAsync: async (clave) => {
      if (fallar.deleteItemAsync) throw new Error("no se pudo borrar");
      datos.delete(clave);
    },
  };
}

// Guarda los avisos para revisar que existen y que nunca llevan el token.
function crear({ seguro, viejo }) {
  const avisos = [];
  const almacen = crearAlmacenToken({ seguro, viejo, avisar: (texto) => avisos.push(texto) });
  return { almacen, avisos };
}

test("la clave del token es la misma de antes (así se encuentra el token viejo)", () => {
  assert.equal(CLAVE_TOKEN, "petconnect_token");
  // SecureStore solo acepta letras, números, ".", "-" y "_"
  assert.match(CLAVE_TOKEN, /^[A-Za-z0-9._-]+$/);
});

test("SecureStore solo se usa en Android e iOS (en web el módulo viene vacío)", () => {
  assert.equal(tieneAlmacenSeguro("android"), true);
  assert.equal(tieneAlmacenSeguro("ios"), true);
  assert.equal(tieneAlmacenSeguro("web"), false);
  assert.equal(tieneAlmacenSeguro(undefined), false);
});

// --- Con SecureStore (Android e iOS) ---

test("guardar pone el token en SecureStore y NO en AsyncStorage", async () => {
  const seguro = almacenSeguro();
  const viejo = almacenViejo();
  const { almacen, avisos } = crear({ seguro, viejo });
  await almacen.guardar("token-nuevo");
  assert.equal(seguro.datos.get(CLAVE_TOKEN), "token-nuevo");
  assert.equal(viejo.datos.has(CLAVE_TOKEN), false);
  assert.equal(await almacen.leer(), "token-nuevo");
  assert.deepEqual(avisos, []);
});

test("guardar también borra un token viejo que hubiera quedado en AsyncStorage", async () => {
  const seguro = almacenSeguro();
  const viejo = almacenViejo({ [CLAVE_TOKEN]: "token-de-antes" });
  await crear({ seguro, viejo }).almacen.guardar("token-nuevo");
  assert.equal(viejo.datos.has(CLAVE_TOKEN), false);
});

test("leer pasa el token de AsyncStorage a SecureStore y lo borra de AsyncStorage", async () => {
  const seguro = almacenSeguro();
  const viejo = almacenViejo({ [CLAVE_TOKEN]: "token-de-antes" });
  const { almacen } = crear({ seguro, viejo });
  assert.equal(await almacen.leer(), "token-de-antes", "la sesión no se pierde al actualizar");
  assert.equal(seguro.datos.get(CLAVE_TOKEN), "token-de-antes");
  assert.equal(viejo.datos.has(CLAVE_TOKEN), false, "no queda copia en texto plano");
  assert.equal(await almacen.leer(), "token-de-antes");
});

test("si ya hay token en SecureStore, se usa ese y se ignora AsyncStorage", async () => {
  const seguro = almacenSeguro({ [CLAVE_TOKEN]: "token-seguro" });
  const viejo = almacenViejo({ [CLAVE_TOKEN]: "token-de-antes" });
  assert.equal(await crear({ seguro, viejo }).almacen.leer(), "token-seguro");
});

test("sin token en ningún lado, leer da null", async () => {
  assert.equal(await crear({ seguro: almacenSeguro(), viejo: almacenViejo() }).almacen.leer(), null);
});

test("si SecureStore no acepta el token viejo, se sigue usando y NO se borra (se reintenta luego)", async () => {
  const seguro = almacenSeguro({}, { setItemAsync: true });
  const viejo = almacenViejo({ [CLAVE_TOKEN]: "token-de-antes" });
  const { almacen, avisos } = crear({ seguro, viejo });
  assert.equal(await almacen.leer(), "token-de-antes");
  assert.equal(viejo.datos.get(CLAVE_TOKEN), "token-de-antes", "no se pierde la sesión");
  assert.equal(avisos.length, 1);
});

test("si SecureStore no puede guardar, la sesión dura en memoria y NO se guarda en texto plano", async () => {
  const seguro = almacenSeguro({}, { setItemAsync: true });
  const viejo = almacenViejo();
  const { almacen, avisos } = crear({ seguro, viejo });
  await almacen.guardar("token-nuevo"); // no lanza: el inicio de sesión sigue
  assert.equal(await almacen.leer(), "token-nuevo", "sirve mientras la app esté abierta");
  assert.equal(viejo.datos.has(CLAVE_TOKEN), false, "nunca en AsyncStorage");
  assert.equal(seguro.datos.has(CLAVE_TOKEN), false);
  assert.equal(avisos.length, 1);
  // Al cerrar la app (almacén nuevo, sin memoria) hay que volver a iniciar sesión
  assert.equal(await crear({ seguro, viejo }).almacen.leer(), null);
});

test("si SecureStore no deja leer, no se rompe: busca en AsyncStorage y avisa", async () => {
  const seguro = almacenSeguro({}, { getItemAsync: true });
  const { almacen, avisos } = crear({ seguro, viejo: almacenViejo() });
  assert.equal(await almacen.leer(), null);
  assert.ok(avisos.length >= 1);
});

test("borrar quita el token de SecureStore, de AsyncStorage y de la memoria", async () => {
  const seguro = almacenSeguro({ [CLAVE_TOKEN]: "token-seguro" });
  const viejo = almacenViejo({ [CLAVE_TOKEN]: "token-de-antes" });
  const { almacen } = crear({ seguro, viejo });
  await almacen.borrar();
  assert.equal(seguro.datos.has(CLAVE_TOKEN), false);
  assert.equal(viejo.datos.has(CLAVE_TOKEN), false);
  assert.equal(await almacen.leer(), null);

  // También el token que solo estaba en memoria
  const sinGuardar = crear({ seguro: almacenSeguro({}, { setItemAsync: true }), viejo: almacenViejo() });
  await sinGuardar.almacen.guardar("token-en-memoria");
  await sinGuardar.almacen.borrar();
  assert.equal(await sinGuardar.almacen.leer(), null);
});

test("si SecureStore falla al borrar, igual borra AsyncStorage, no lanza y avisa", async () => {
  const seguro = almacenSeguro({ [CLAVE_TOKEN]: "token-seguro" }, { deleteItemAsync: true });
  const viejo = almacenViejo({ [CLAVE_TOKEN]: "token-de-antes" });
  const { almacen, avisos } = crear({ seguro, viejo });
  await almacen.borrar();
  assert.equal(viejo.datos.has(CLAVE_TOKEN), false);
  assert.equal(avisos.length, 1);
});

test("los avisos nunca llevan el token", async () => {
  const avisos = [];
  for (const fallar of [{ setItemAsync: true }, { getItemAsync: true }, { deleteItemAsync: true }]) {
    const seguro = almacenSeguro({}, fallar);
    const viejo = almacenViejo({ [CLAVE_TOKEN]: "token-secreto-123" });
    const almacen = crearAlmacenToken({ seguro, viejo, avisar: (t) => avisos.push(t) });
    await almacen.leer();
    await almacen.guardar("token-secreto-456");
    await almacen.borrar();
  }
  assert.ok(avisos.length > 0);
  for (const aviso of avisos) assert.doesNotMatch(aviso, /token-secreto/);
});

// --- Sin SecureStore (export web) ---

test("en web (seguro = null) usa AsyncStorage, como la web React con localStorage", async () => {
  const viejo = almacenViejo();
  const { almacen } = crear({ seguro: null, viejo });
  await almacen.guardar("token-web");
  assert.equal(viejo.datos.get(CLAVE_TOKEN), "token-web");
  assert.equal(await almacen.leer(), "token-web");
  await almacen.borrar();
  assert.equal(viejo.datos.has(CLAVE_TOKEN), false);
});

test("en web, si no se puede guardar, la sesión dura hasta cerrar la página", async () => {
  const viejo = almacenViejo({}, { setItem: true });
  const { almacen, avisos } = crear({ seguro: null, viejo });
  await almacen.guardar("token-web");
  assert.equal(await almacen.leer(), "token-web");
  assert.equal(avisos.length, 1);
});

// --- api.js, app.json y package.json (se revisa su texto) ---

test("api.js usa SecureStore fuera de web y ya no toca AsyncStorage directo", () => {
  const codigo = leer("src/services/api.js");
  assert.match(codigo, /import \* as SecureStore from "expo-secure-store";/);
  assert.match(codigo, /import \{ crearAlmacenToken, tieneAlmacenSeguro \} from "\.\.\/utils\/almacenToken";/);
  assert.match(codigo, /seguro: tieneAlmacenSeguro\(Platform\.OS\) \? SecureStore : null,/);
  assert.match(codigo, /viejo: AsyncStorage,/);
  assert.match(codigo, /avisar: \(aviso\) => console\.warn\(/);
  // El token solo pasa por el almacén: ni getItem/setItem/removeItem sueltos
  assert.doesNotMatch(codigo, /AsyncStorage\.(getItem|setItem|removeItem)/);
  assert.doesNotMatch(codigo, /SecureStore\.\w+Async/);
  const apiFetch = codigo.slice(codigo.indexOf("async function apiFetch"));
  assert.match(apiFetch, /const token = await almacenToken\.leer\(\);/);
  assert.match(codigo, /export async function saveToken\(token\) \{\s*await almacenToken\.guardar\(token\);/);
  assert.match(codigo, /export async function clearToken\(\) \{\s*await almacenToken\.borrar\(\);/);
  assert.match(codigo, /export async function getToken\(\) \{\s*return almacenToken\.leer\(\);/);
});

test("expo-secure-store queda en package.json con la versión de Expo 57 y su plugin en app.json", () => {
  const paquete = JSON.parse(leer("package.json"));
  assert.match(paquete.dependencies["expo-secure-store"], /^~57\.0\.\d+$/);
  const bloqueo = JSON.parse(leer("package-lock.json"));
  assert.match(bloqueo.packages["node_modules/expo-secure-store"].version, /^57\.0\.\d+$/);
  // El plugin saca los datos de SecureStore de las copias de seguridad de Android
  // (al restaurarlas en otro celular no se podrían descifrar).
  const app = JSON.parse(leer("app.json"));
  assert.ok(app.expo.plugins.includes("expo-secure-store"));
});
