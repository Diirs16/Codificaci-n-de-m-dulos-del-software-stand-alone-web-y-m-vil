// Pruebas del ítem 4.13, parte 3 (A-03): el botón "Cerrar sesión" del móvil.
// Mismas reglas que la web (tests/cerrar-sesion.test.js del Front). Se corren con
// `npm test` (node --test, sin dependencias nuevas). No llaman a la API real. Tokens
// y nombres inventados.
//
// Antes, logout() solo borraba el token del celular (AsyncStorage): si alguien lo
// había copiado, o la cuenta seguía abierta en otro aparato, seguía valiendo hasta 24 h.
// Ahora:
// - Se llama a POST /api/auth/logout (la API suma 1 a version_sesion y el token deja
//   de valer en TODOS los aparatos), con un límite de 8 s.
// - La sesión local se borra SIEMPRE: 200, 401, 503, 502, 500, sin red o tiempo agotado.
// - Si el servidor no pudo confirmar el cierre, se avisa con Alert.alert (A1).
// - El botón queda desactivado mientras se espera (B1).
// - FormularioSolicitud, tras un 401, solo cierra en local (no llama a la API).
//
// api.js, AuthContext.js y las pantallas importan react-native y Node no lo puede
// cargar: la lógica está en src/utils/sesion.js (se ejecuta de verdad) y del resto
// se revisa el texto.
import { test, beforeEach } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { errorDeApi } from "../src/utils/peticiones.js";
// Con "* as" la falta de una función hace fallar solo su prueba (no todo el archivo).
import * as sesion from "../src/utils/sesion.js";

const TOKEN = "token-de-prueba"; // inventado
const leer = (ruta) => readFileSync(new URL(ruta, import.meta.url), "utf8");

// AsyncStorage falso: guarda el token en memoria y responde con promesas, como el real
let tokenGuardado;
let borrados;
let llamadasApi;

const leerToken = async () => tokenGuardado;
const borrarLocal = async () => {
  borrados += 1;
  tokenGuardado = null;
};

function cerrar(cerrarEnServidor) {
  assert.equal(typeof sesion.cerrarSesion, "function", "falta cerrarSesion en src/utils/sesion.js");
  return sesion.cerrarSesion({
    leerToken,
    cerrarEnServidor: async () => {
      llamadasApi += 1;
      return cerrarEnServidor();
    },
    borrarLocal,
  });
}

// Lo que lanza apiFetch con una respuesta que no fue ok (status HTTP incluido)
const respuestaConError = (status, mensaje = `Error ${status}`) => () => {
  throw errorDeApi(mensaje, status, { error: mensaje });
};

beforeEach(() => {
  tokenGuardado = TOKEN;
  borrados = 0;
  llamadasApi = 0;
});

// --- Qué pasa con cada respuesta ---

test("200: se cierra en el servidor y en el celular", async () => {
  assert.equal(await cerrar(async () => ({ message: "Sesion cerrada" })), "cerrada");
  assert.equal(llamadasApi, 1);
  assert.equal(borrados, 1);
  assert.equal(tokenGuardado, null);
});

test("401 (el token ya no valía): se borra lo local sin aviso", async () => {
  const resultado = await cerrar(
    respuestaConError(401, "Token invalido o sesion expirada. Inicia sesion de nuevo"),
  );
  assert.equal(resultado, "ya-cerrada");
  assert.equal(borrados, 1);
});

test("503, 502 y 500: la sesión local SE BORRA igual y se avisa", async () => {
  for (const status of [503, 502, 500]) {
    tokenGuardado = TOKEN;
    borrados = 0;
    assert.equal(await cerrar(respuestaConError(status)), "sin-confirmar", `status ${status}`);
    assert.equal(borrados, 1, `status ${status}: la sesión local debe borrarse`);
  }
});

test("sin red o tiempo agotado (error sin status): la sesión local SE BORRA igual y se avisa", async () => {
  // apiFetch no atrapa el fallo de fetch: llega el error de React Native tal cual
  const sinRed = new TypeError("Network request failed");
  const tiempoAgotado = new Error("Aborted");
  tiempoAgotado.name = "AbortError"; // lo que lanza fetch al cortarlo con AbortController
  for (const falla of [sinRed, tiempoAgotado]) {
    tokenGuardado = TOKEN;
    borrados = 0;
    const resultado = await cerrar(() => {
      throw falla;
    });
    assert.equal(resultado, "sin-confirmar", falla.name);
    assert.equal(borrados, 1, `${falla.name}: la sesión local debe borrarse`);
  }
});

test("sin token guardado: no se llama a la API y se borra lo local", async () => {
  tokenGuardado = null;
  assert.equal(await cerrar(async () => ({ message: "Sesion cerrada" })), "ya-cerrada");
  assert.equal(llamadasApi, 0);
  assert.equal(borrados, 1);
});

test("si mientras se espera entra OTRA cuenta, su sesión nueva no se borra", async () => {
  const resultado = await cerrar(async () => {
    tokenGuardado = "token-de-otra-cuenta";
    return { message: "Sesion cerrada" };
  });
  assert.equal(resultado, "cerrada");
  assert.equal(borrados, 0);
  assert.equal(tokenGuardado, "token-de-otra-cuenta");
});

// --- Límite de tiempo (apiFetch no tiene uno propio) ---

test("conLimiteDeTiempo corta la petición que no responde (error sin status)", async () => {
  assert.equal(typeof sesion.conLimiteDeTiempo, "function", "falta conLimiteDeTiempo en src/utils/sesion.js");
  assert.equal(sesion.TIEMPO_CIERRE_MS, 8000, "mismo límite que la web (8 s)");
  // Petición falsa que nunca contesta: solo termina si la cortan (como fetch con signal)
  const peticionColgada = (signal) =>
    new Promise((_, rechazar) => {
      signal.addEventListener("abort", () => {
        const error = new Error("Aborted");
        error.name = "AbortError";
        rechazar(error);
      });
    });
  const inicio = Date.now();
  await assert.rejects(sesion.conLimiteDeTiempo(peticionColgada, 30), (error) => {
    assert.equal(error.name, "AbortError");
    assert.equal(error.status, undefined, "sin status: cerrarSesion lo cuenta como sin-confirmar");
    return true;
  });
  assert.ok(Date.now() - inicio < 2000, "debe cortarse a los 30 ms, no quedarse esperando");
});

test("conLimiteDeTiempo: si responde a tiempo devuelve la respuesta y limpia el temporizador", async () => {
  assert.equal(typeof sesion.conLimiteDeTiempo, "function", "falta conLimiteDeTiempo en src/utils/sesion.js");
  let senal;
  const respuesta = await sesion.conLimiteDeTiempo(async (signal) => {
    senal = signal;
    return { message: "Sesion cerrada" };
  }, 30);
  assert.deepEqual(respuesta, { message: "Sesion cerrada" });
  // Si el temporizador quedara activo, a los 30 ms cortaría una petición que ya terminó
  await new Promise((listo) => setTimeout(listo, 60));
  assert.equal(senal.aborted, false, "el temporizador debe limpiarse al terminar");
});

// --- Archivos con React Native (se revisa su texto) ---

test("api.js: cerrarSesionEnServidor hace POST /auth/logout con el límite de tiempo", () => {
  const codigo = leer("../src/services/api.js");
  assert.match(codigo, /import \{[^}]*\bconLimiteDeTiempo\b[^}]*\} from "\.\.\/utils\/sesion"/);
  assert.match(
    codigo,
    /export function cerrarSesionEnServidor\(\) \{\s*return conLimiteDeTiempo\(\(signal\) =>\s*apiFetch\("\/auth\/logout", \{ method: "POST", signal \}\)/,
  );
  // apiFetch pasa el signal a fetch (lo lleva dentro de options)
  assert.match(codigo, /fetch\(`\$\{API_BASE\}\$\{path\}`, \{ \.\.\.options, headers \}\)/);
});

test("AuthContext: logout llama a la API con cerrarSesion y existe un cierre solo local", () => {
  const contexto = leer("../src/context/AuthContext.js");
  assert.match(contexto, /import \{ cerrarSesion \} from "\.\.\/utils\/sesion"/);
  assert.match(contexto, /function logout\(\) \{\s*return cerrarSesion\(\{/);
  assert.match(contexto, /cerrarEnServidor: cerrarSesionEnServidor/);
  assert.match(contexto, /borrarLocal: cerrarSesionLocal/);
  assert.match(contexto, /async function cerrarSesionLocal\(\) \{\s*await clearToken\(\);\s*setUser\(null\);/);
  assert.match(contexto, /value=\{\{[\s\S]*\bcerrarSesionLocal\b[\s\S]*\}\}/);
});

test("FormularioSolicitud: tras un 401 solo cierra en local (no llama a la API)", () => {
  const formulario = leer("../src/components/FormularioSolicitud.js");
  assert.match(
    formulario,
    /async function volverAIniciarSesion\(\) \{[\s\S]*await cerrarSesionLocal\(\);[\s\S]*iniciarSesion\(\);/,
  );
  assert.doesNotMatch(formulario, /\blogout\b/);
});

test("ProfileScreen: el botón espera desactivado y avisa con Alert si no se confirmó", () => {
  const perfil = leer("../src/screens/ProfileScreen.js");
  assert.match(perfil, /onPress=\{salir\}/);
  assert.match(perfil, /disabled=\{cerrando\}/);
  assert.match(perfil, /accessibilityState=\{\{ disabled: cerrando, busy: cerrando \}\}/);
  assert.match(perfil, /cerrando \? "Cerrando sesión…" : "Cerrar sesión"/);
  assert.match(perfil, /if \(cerrando\) return;/);
  assert.match(perfil, /await logout\(\)/);
  assert.match(perfil, /resultado === "sin-confirmar"/);
  assert.match(perfil, /Alert\.alert\(AVISO_CIERRE_TITULO, AVISO_CIERRE_TEXTO/);
  // El mismo mensaje de la web (cambia "navegador" por "celular")
  assert.match(perfil, /pero no pudimos confirmarlo con el servidor\. /);
  assert.match(perfil, /Si usas PetConnect en otro aparato, cierra sesión también allí\./);
});
