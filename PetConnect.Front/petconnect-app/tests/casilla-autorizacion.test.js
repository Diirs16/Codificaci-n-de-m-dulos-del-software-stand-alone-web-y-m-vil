// Ítem 3.5 (A-20, R05): el texto legal de la casilla (B.1 y B.2 del borrador de la
// política) vive SOLO en src/components/CasillaAutorizacion.jsx, y lo usan el
// registro y el inicio de sesión. Así, si cambia la política, se cambia una vez.
// Node no entiende JSX: esta prueba lee el texto de los archivos.
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

test("el texto de la casilla (B.1) solo está en CasillaAutorizacion.jsx", () => {
  const conTexto = archivosDeCodigo(SRC)
    .filter((ruta) => readFileSync(ruta, "utf8").includes("Soy mayor de 18 años"))
    .map((ruta) => relative(SRC, ruta).replaceAll("\\", "/"));
  assert.deepEqual(conTexto, ["components/CasillaAutorizacion.jsx"]);
});

test("el registro y el inicio de sesión usan el componente de la casilla", () => {
  for (const archivo of ["components/RegisterModal.jsx", "components/LoginModal.jsx"]) {
    assert.match(leer(archivo), /<CasillaAutorizacion\b/, `${archivo} no usa <CasillaAutorizacion>`);
  }
});

test("el inicio de sesión reconoce el 403 y tiene los mensajes de B.3", () => {
  const login = leer("components/LoginModal.jsx");
  assert.match(login, /requiereAutorizacion/);
  assert.match(login, /Para continuar debes autorizar el tratamiento de tus datos personales\./);
  assert.match(login, /Si no quieres autorizarlo, escríbenos a/);
  assert.match(login, /mailto:/);
});
