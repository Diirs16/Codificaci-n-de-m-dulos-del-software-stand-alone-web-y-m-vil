// Pruebas del ítem 4.1 (A-17, NC-004): la web exige la misma política de contraseña
// que la API (petconnect.Backend/security/politica.py, RS03, caso CP-003).
// Se corren con `npm test` (node --test, sin dependencias nuevas). Contraseñas inventadas.
//
// - src/utils/contrasena.js es JS puro: se ejecuta de verdad con los mismos casos
//   que tests/test_politica.py del backend (límites 7/8/9/64/65 y 72/73 bytes).
// - Los límites y los caracteres especiales se comparan con el texto de politica.py.
// - RegisterModal.jsx tiene JSX y Node no lo entiende: se lee su texto.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
// Con "* as" la falta de algo hace fallar solo su prueba (no todo el archivo).
import * as politica from "../src/utils/contrasena.js";

const leer = (ruta) => readFileSync(new URL(ruta, import.meta.url), "utf8");
const MODAL = leer("../src/components/RegisterModal.jsx");
const POLITICA_PY = leer("../../../petconnect.Backend/security/politica.py");

const SIN_MINUSCULA = "PETCONNECT1!"; // la evidencia de A-17
const VALIDA = "Petconnect1!";
const validar = (p) => politica.validarContrasena(p);

test("A-17: PETCONNECT1! se rechaza por no tener minúscula", () => {
  assert.equal(validar(SIN_MINUSCULA), "La contraseña debe tener al menos una minúscula");
});

test("una contraseña que cumple todo se acepta", () => {
  assert.equal(validar(VALIDA), null);
});

test("CP-003: 7 caracteres se rechaza; 8 y 9 se aceptan", () => {
  assert.match(validar("Abc12!x"), /al menos 8/);
  assert.equal(validar("Abc1234!"), null);
  assert.equal(validar("Abc12345!"), null);
});

test("CP-003: 64 caracteres se acepta y 65 se rechaza", () => {
  assert.equal(validar("Aa1!" + "b".repeat(60)), null);
  assert.match(validar("Aa1!" + "b".repeat(61)), /máximo 64/);
});

test("CP-003: 72 bytes se acepta y 73 se rechaza (bcrypt)", () => {
  assert.equal(validar("Aa1!" + "🐶".repeat(17)), null);
  assert.match(validar("Aa1!b" + "🐶".repeat(17)), /máximo 64/);
});

test("un emoji cuenta como 1 carácter, igual que en Python", () => {
  // 59 + 3 emojis = 62 caracteres y 71 bytes: la API la acepta; con p.length serían 65
  assert.equal(validar("Aa1!" + "b".repeat(55) + "🐶".repeat(3)), null);
});

test("vacía (o sin valor) pide la longitud", () => {
  assert.match(validar(""), /al menos 8/);
  assert.match(validar(undefined), /al menos 8/);
});

test("sin mayúscula, sin número o sin carácter especial se rechaza", () => {
  assert.match(validar("petconnect1!"), /mayúscula/);
  assert.match(validar("Petconnect!!"), /número/);
  assert.match(validar("Petconnect12"), /carácter especial/);
});

test("letras con tilde o ñ no cuentan como minúscula (igual que la API)", () => {
  assert.match(validar("PETCONNECTÑÁ1!"), /minúscula/);
});

test("cada carácter especial del mensaje se acepta", () => {
  for (const caracter of politica.CARACTERES_ESPECIALES.split(" ")) {
    assert.equal(validar("Petconnect1" + caracter), null, caracter);
  }
});

test("las reglas van en el mismo orden que en la API", () => {
  assert.deepEqual(
    politica.REGLAS_CONTRASENA.map((r) => r.id),
    ["len", "max", "upper", "lower", "number", "special"],
  );
});

test("los límites y los caracteres especiales son los de politica.py", () => {
  assert.match(POLITICA_PY, new RegExp(`^LARGO_MIN = ${politica.LARGO_MIN}$`, "m"));
  assert.match(POLITICA_PY, new RegExp(`^LARGO_MAX = ${politica.LARGO_MAX}$`, "m"));
  assert.ok(
    POLITICA_PY.includes(`CARACTERES_ESPECIALES = '${politica.CARACTERES_ESPECIALES}'`),
    "CARACTERES_ESPECIALES distinto en politica.py",
  );
});

test("RegisterModal usa la utilidad común y ya no tiene su propia lista", () => {
  assert.match(MODAL, /import \{ REGLAS_CONTRASENA \} from "\.\.\/utils\/contrasena"/);
  assert.doesNotMatch(MODAL, /const RULES\s*=/);
  assert.doesNotMatch(MODAL, /\/\[A-Z\]\/\.test/);
});
