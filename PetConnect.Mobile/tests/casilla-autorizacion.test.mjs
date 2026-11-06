// Ítem 3.5 (A-20, R05): la casilla de autorización vive en UN solo componente
// (src/components/CasillaAutorizacion.js) que usan el registro y el inicio de
// sesión, y el inicio de sesión pide la casilla cuando la API la exige.
// Node no entiende JSX: estas pruebas leen el texto de los archivos.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readdirSync, readFileSync } from "node:fs";
import { join, relative } from "node:path";
import { fileURLToPath } from "node:url";

const SRC = fileURLToPath(new URL("../src", import.meta.url));
const leer = (ruta) => readFileSync(join(SRC, ruta), "utf8");

function archivosDeCodigo(carpeta) {
  return readdirSync(carpeta, { withFileTypes: true }).flatMap((e) => {
    const ruta = join(carpeta, e.name);
    if (e.isDirectory()) return archivosDeCodigo(ruta);
    return /\.(js|jsx)$/.test(e.name) ? [ruta] : [];
  });
}

test("el texto legal de la casilla (B.1) está solo en el componente", () => {
  const conTexto = archivosDeCodigo(SRC)
    .filter((ruta) => readFileSync(ruta, "utf8").includes("Soy mayor de 18 años"))
    .map((ruta) => relative(SRC, ruta).replaceAll("\\", "/"));
  assert.deepEqual(conTexto, ["components/CasillaAutorizacion.js"]);
});

test("el registro y el inicio de sesión usan <CasillaAutorizacion>", () => {
  for (const pantalla of ["screens/RegisterScreen.js", "screens/LoginScreen.js"]) {
    const codigo = leer(pantalla);
    assert.ok(
      codigo.includes('import CasillaAutorizacion from "../components/CasillaAutorizacion"'),
      `${pantalla} debe importar el componente`,
    );
    assert.ok(codigo.includes("<CasillaAutorizacion"), `${pantalla} debe usar el componente`);
  }
});

test("el inicio de sesión atiende el 403 de la autorización con los textos de B.3", () => {
  const codigo = leer("screens/LoginScreen.js");
  assert.ok(codigo.includes("requiereAutorizacion"), "debe reconocer el 403 que pide la casilla");
  assert.ok(codigo.includes("Autoriza el uso de tus datos"));
  assert.ok(codigo.includes("Para continuar debes autorizar el tratamiento de tus datos personales."));
  assert.ok(codigo.includes("Si no quieres autorizarlo, escríbenos a"));
  assert.ok(codigo.includes("y borraremos tu cuenta."));
  assert.ok(codigo.includes("mailto:"), "debe ofrecer escribir al correo de atención");
  assert.ok(
    codigo.includes("loginUser(email.trim(), password, true)"),
    "con la casilla marcada repite /login con true",
  );
});

test("la casilla empieza sin marcar en las dos pantallas", () => {
  for (const pantalla of ["screens/RegisterScreen.js", "screens/LoginScreen.js"]) {
    assert.ok(
      /const \[aceptaDatos, setAceptaDatos\] = useState\(false\)/.test(leer(pantalla)),
      `${pantalla}: aceptaDatos debe empezar en false`,
    );
  }
});
