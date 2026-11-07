// Pruebas del ítem 3.6 (A-21): los formularios de adopción y contacto envían de verdad.
// Se corren con `npm test` (node --test, sin dependencias nuevas). No llaman a la API
// real: `fetch` se reemplaza por uno falso. Node no entiende JSX, así que las páginas
// se revisan leyendo su texto.
//
// - src/utils/solicitud.js valida igual que la API (mensaje 10 a 1000, teléfono opcional).
// - api.js manda el token, la mascota como número y nunca el nombre ni el correo.
// - PetDetail y Contacto ya no son demo; el checkout sí (A-26).
// - El aviso B.5 está en el formulario y "enviada" solo sale después de la respuesta ok.
// - La página de la política tiene la misma versión que la API (1.1).
import { test, beforeEach, afterEach } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

const TOKEN = "token-de-prueba"; // inventado

Object.defineProperty(globalThis, "localStorage", {
  value: { getItem: (clave) => (clave === "petconnect_token" ? TOKEN : null) },
  configurable: true,
  writable: true,
});

// Import como objeto: si falta una función, falla su prueba y no todo el archivo.
const api = await import("../src/services/api.js");
const { validarMensaje, validarTelefono } = await import("../src/utils/solicitud.js");

const leer = (ruta) => readFileSync(fileURLToPath(new URL(ruta, import.meta.url)), "utf8");
const fetchOriginal = globalThis.fetch;
let peticiones = [];

function responder(status, cuerpo) {
  globalThis.fetch = async (url, opciones) => {
    peticiones.push({ url, opciones });
    return new Response(JSON.stringify(cuerpo), {
      status,
      headers: { "Content-Type": "application/json" },
    });
  };
}

beforeEach(() => {
  peticiones = [];
});

afterEach(() => {
  globalThis.fetch = fetchOriginal;
});

// --- Validación en el navegador (mismas reglas que api.py) ---

test("mensaje: entre 10 y 1000 caracteres sin contar los espacios de los extremos", () => {
  for (const valido of ["a".repeat(10), "a".repeat(1000), `   ${"a".repeat(10)}\n`]) {
    assert.equal(validarMensaje(valido), null);
  }
  for (const invalido of ["", " ".repeat(20), "Hola", "a".repeat(1001), undefined, null]) {
    assert.match(validarMensaje(invalido), /entre 10 y 1000/);
  }
});

test("teléfono: opcional; solo números, espacios y un + al inicio, de 7 a 15 dígitos", () => {
  for (const valido of ["", "   ", "3000000000", "+57 300 000 0000", "1234567", undefined]) {
    assert.equal(validarTelefono(valido), null, String(valido));
  }
  for (const invalido of ["300-000-0000", "abc0000000", "123456", "1".repeat(16), "57+3000000000",
    "++573000000000", "+57 300 000 0000 0000"]) {
    assert.match(validarTelefono(invalido), /teléfono/, invalido);
  }
});

// --- api.js ---

test("enviarSolicitudAdopcion: POST con token, mascota como número y sin nombre ni correo", async () => {
  responder(201, { message: "Solicitud enviada", id: 42 });
  const respuesta = await api.enviarSolicitudAdopcion("3", "Quiero conocer a Luna pronto", "3000000000");
  assert.deepEqual(respuesta, { message: "Solicitud enviada", id: 42 });
  assert.equal(peticiones.length, 1);
  const { url, opciones } = peticiones[0];
  assert.equal(url, "/api/solicitudes/adopcion");
  assert.equal(opciones.method, "POST");
  assert.equal(opciones.headers.Authorization, `Bearer ${TOKEN}`);
  assert.deepEqual(JSON.parse(opciones.body), {
    id_mascota: 3, mensaje: "Quiero conocer a Luna pronto", telefono: "3000000000",
  });
});

test("enviarMensajeContacto: POST con token y solo el mensaje", async () => {
  responder(201, { message: "Mensaje enviado", id: 43 });
  await api.enviarMensajeContacto("Hola, tengo una pregunta");
  const { url, opciones } = peticiones[0];
  assert.equal(url, "/api/solicitudes/contacto");
  assert.equal(opciones.headers.Authorization, `Bearer ${TOKEN}`);
  assert.deepEqual(JSON.parse(opciones.body), { mensaje: "Hola, tengo una pregunta" });
});

test("403 de autorización: el error trae requiereAutorizacion; 401 y 404 no", async () => {
  responder(403, { error: "Para enviar tu solicitud debes autorizar...", requiere_autorizacion: true });
  await assert.rejects(api.enviarMensajeContacto("Hola, tengo una pregunta"), (e) => {
    assert.equal(e.status, 403);
    assert.equal(e.requiereAutorizacion, true);
    return true;
  });
  for (const [status, error] of [[401, "Autenticacion requerida"], [404, "Mascota no encontrada"]]) {
    responder(status, { error });
    await assert.rejects(api.enviarSolicitudAdopcion(3, "Quiero conocer a Luna pronto"), (e) => {
      assert.equal(e.status, status);
      assert.equal(e.message, error);
      assert.equal(e.requiereAutorizacion, false);
      return true;
    });
  }
});

// --- Páginas (texto) ---

test("adopción y contacto usan el formulario real; el checkout sigue en demo (A-26)", () => {
  for (const pagina of ["../src/pages/PetDetail.jsx", "../src/pages/Contact.jsx"]) {
    const texto = leer(pagina);
    assert.doesNotMatch(texto, /import AvisoDemo|<AvisoDemo\b|<fieldset disabled|\(demo\)/,
      `${pagina} sigue siendo demo`);
    assert.match(texto, /<FormularioSolicitud\b/, `${pagina} no usa <FormularioSolicitud>`);
  }
  assert.match(leer("../src/pages/Checkout.jsx"), /<AvisoDemo\b/);
});

test("el formulario dice 'enviada' solo después de la respuesta de la API", () => {
  const formulario = leer("../src/components/FormularioSolicitud.jsx");
  assert.equal(formulario.match(/setEstado\("enviada"\)/g)?.length, 1);
  assert.match(
    formulario,
    /await enviarSolicitudAdopcion\([\s\S]*?await enviarMensajeContacto\([\s\S]*?setEstado\("enviada"\)[\s\S]*?catch/,
  );
  assert.match(formulario, /requiereAutorizacion/);
});

test("el formulario tiene el aviso B.5 y enlaza la política", () => {
  const formulario = leer("../src/components/FormularioSolicitud.jsx");
  for (const frase of ["Al enviar, usaremos tu nombre, tu correo", "Solo el equipo de PetConnect lee tu mensaje",
    "No escribas datos sensibles", "Puedes", "pedir que lo borremos"]) {
    assert.ok(formulario.includes(frase), `falta "${frase}"`);
  }
  assert.match(formulario, /to="\/politica-de-datos"/);
  assert.match(formulario, /mailto:/);
});

test("la página de la política, el borrador y la API tienen la misma versión", () => {
  const web = leer("../src/pages/PoliticaDatos.jsx").match(/const VERSION_POLITICA = "([^"]+)"/)?.[1];
  const apiPy = leer("../../../petconnect.Backend/api.py").match(/^VERSION_POLITICA_DATOS = "([^"]+)"/m)?.[1];
  const borrador = leer("../../../Documentacion/Legal/POLITICA-TRATAMIENTO-DATOS-v1.0-BORRADOR.md")
    .match(/versión (\d+\.\d+) \(BORRADOR\)/)?.[1];
  assert.equal(apiPy, "1.1");
  assert.equal(web, apiPy);
  assert.equal(borrador, apiPy);
});
