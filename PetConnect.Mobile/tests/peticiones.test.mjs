// Ítem 3.5 (A-20, R05): piezas puras de src/services/api.js (src/utils/peticiones.js).
// Mismos casos que la web (tests/api.test.js). Correos inventados.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { errorDeApi, cuerpoLogin } from "../src/utils/peticiones.js";

const CORREO = "ana@ejemplo.test";
const CLAVE = "Clave-de-prueba-1";

test("con la casilla marcada, /login manda acepta_datos como booleano true", () => {
  assert.deepEqual(cuerpoLogin(CORREO, CLAVE, true), {
    email: CORREO,
    password: CLAVE,
    acepta_datos: true,
  });
});

test("sin la casilla, /login NO manda acepta_datos (ni con 'true' ni con 1)", () => {
  for (const valor of [undefined, false, "true", 1, null]) {
    const cuerpo = cuerpoLogin(CORREO, CLAVE, valor);
    assert.ok(!("acepta_datos" in cuerpo), `con ${String(valor)} no debe ir acepta_datos`);
    assert.deepEqual(cuerpo, { email: CORREO, password: CLAVE });
  }
});

test("el 403 que pide la autorización trae requiereAutorizacion y el status", () => {
  const mensaje = "Para seguir usando tu cuenta debes autorizar el tratamiento de tus datos personales";
  const error = errorDeApi(mensaje, 403, { error: mensaje, requiere_autorizacion: true });
  assert.ok(error instanceof Error);
  assert.equal(error.message, mensaje);
  assert.equal(error.status, 403);
  assert.equal(error.requiereAutorizacion, true);
});

test("otros errores NO piden la autorización ('Cuenta inactiva', un texto 'true' o sin cuerpo)", () => {
  const inactiva = errorDeApi("Cuenta inactiva", 403, { error: "Cuenta inactiva" });
  assert.equal(inactiva.requiereAutorizacion, false);
  assert.equal(inactiva.status, 403);

  const texto = errorDeApi("x", 403, { error: "x", requiere_autorizacion: "true" });
  assert.equal(texto.requiereAutorizacion, false);

  const sinCuerpo = errorDeApi("Error 502: respuesta inválida del servidor", 502, null);
  assert.equal(sinCuerpo.requiereAutorizacion, false);
  assert.equal(sinCuerpo.status, 502);
});

// api.js importa react-native y Node no lo puede cargar: se revisa su texto para
// asegurar que de verdad usa las piezas probadas arriba.
test("api.js usa errorDeApi y cuerpoLogin, y loginUser recibe aceptaDatos", () => {
  const codigo = readFileSync(new URL("../src/services/api.js", import.meta.url), "utf8");
  assert.ok(/throw errorDeApi\(data\.error/.test(codigo), "apiFetch debe lanzar errorDeApi con los datos de la API");
  assert.ok(!/throw new Error\(/.test(codigo), "apiFetch no debe lanzar un Error sin status");
  assert.ok(/export function loginUser\(email, password, aceptaDatos\)/.test(codigo));
  assert.ok(codigo.includes("cuerpoLogin(email, password, aceptaDatos)"));
});
