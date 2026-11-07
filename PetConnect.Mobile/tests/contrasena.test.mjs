// Ítem 4.1 parte 3 (A-17, NC-004): el móvil exige la misma política de contraseña
// que la API (petconnect.Backend/security/politica.py, RS03, caso CP-003) y la web.
// Antes RegisterScreen.js no revisaba la contraseña: solo la API. Contraseñas inventadas.
// - src/utils/contrasena.js es JS puro: se ejecuta de verdad con los casos de CP-003.
// - Es la MISMA copia que la de la web, y sus límites son los de politica.py.
// - RegisterScreen.js tiene JSX y Node no lo entiende: se lee su texto.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
// Con "* as" la falta de algo hace fallar solo su prueba (no todo el archivo).
import * as politica from "../src/utils/contrasena.js";

const leer = (ruta) => readFileSync(new URL(ruta, import.meta.url), "utf8");
const PANTALLA = leer("../src/screens/RegisterScreen.js");
const POLITICA_PY = leer("../../petconnect.Backend/security/politica.py");

const validar = (p) => politica.validarContrasena(p);

test("A-17: PETCONNECT1! se rechaza por no tener minúscula; Petconnect1! se acepta", () => {
  assert.equal(validar("PETCONNECT1!"), "La contraseña debe tener al menos una minúscula");
  assert.equal(validar("Petconnect1!"), null);
});

test("CP-003: 7 se rechaza; 8, 9 y 64 se aceptan; 65 se rechaza", () => {
  assert.match(validar("Abc12!x"), /al menos 8/);
  assert.equal(validar("Abc1234!"), null);
  assert.equal(validar("Abc12345!"), null);
  assert.equal(validar("Aa1!" + "b".repeat(60)), null);
  assert.match(validar("Aa1!" + "b".repeat(61)), /máximo 64/);
});

test("CP-003: 72 bytes se acepta y 73 se rechaza; un emoji cuenta como 1 carácter", () => {
  assert.equal(validar("Aa1!" + "🐶".repeat(17)), null);
  assert.match(validar("Aa1!b" + "🐶".repeat(17)), /máximo 64/);
  assert.equal(validar("Aa1!" + "b".repeat(55) + "🐶".repeat(3)), null);
});

test("sin mayúscula, sin número, sin especial o vacía se rechaza", () => {
  assert.match(validar("petconnect1!"), /mayúscula/);
  assert.match(validar("Petconnect!!"), /número/);
  assert.match(validar("Petconnect12"), /carácter especial/);
  assert.match(validar(""), /al menos 8/);
  assert.match(validar("PETCONNECTÑÁ1!"), /minúscula/);
});

test("src/utils/contrasena.js es la MISMA copia que la de la web (sin contar los comentarios //)", () => {
  const sinComentarios = (texto) =>
    texto
      .replaceAll("\r\n", "\n")
      .split("\n")
      .filter((linea) => !linea.startsWith("//"))
      .join("\n")
      .trim();
  const movil = leer("../src/utils/contrasena.js");
  const web = leer("../../PetConnect.Front/petconnect-app/src/utils/contrasena.js");
  assert.equal(sinComentarios(movil), sinComentarios(web), "si cambia una regla, cambiarla en politica.py, la web y el móvil");
});

test("los límites y los caracteres especiales son los de politica.py", () => {
  assert.match(POLITICA_PY, new RegExp(`^LARGO_MIN = ${politica.LARGO_MIN}$`, "m"));
  assert.match(POLITICA_PY, new RegExp(`^LARGO_MAX = ${politica.LARGO_MAX}$`, "m"));
  assert.ok(POLITICA_PY.includes(`CARACTERES_ESPECIALES = '${politica.CARACTERES_ESPECIALES}'`));
});

test("RegisterScreen valida la contraseña ANTES de llamar a la API", () => {
  assert.match(PANTALLA, /import \{[^}]*validarContrasena[^}]*\} from "\.\.\/utils\/contrasena"/);
  const valida = PANTALLA.indexOf("validarContrasena(password)");
  const envia = PANTALLA.indexOf("await registerUser(");
  assert.ok(valida > 0, "no llama a validarContrasena(password)");
  assert.ok(valida < envia, "debe validar antes de registerUser");
});

test("RegisterScreen muestra la pista de la contraseña con la minúscula", () => {
  assert.match(PANTALLA, /<Text style=\{styles\.pista\}>\{PISTA_CONTRASENA\}<\/Text>/);
  assert.match(PANTALLA, /con mayúscula, minúscula, número/);
});
