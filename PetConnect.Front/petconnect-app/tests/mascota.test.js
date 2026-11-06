// Ítem 3.4 (A-22): formato de los datos de una mascota (src/utils/mascota.js).
// Lo que no se sabe no se muestra: la función devuelve null o lo salta.
import { test } from "node:test";
import assert from "node:assert/strict";
import { formatearEdad, formatearSexo, datosMascota } from "../src/utils/mascota.js";

test("la edad se escribe en años y 0 es 'Menos de 1 año'", () => {
  assert.equal(formatearEdad(0), "Menos de 1 año");
  assert.equal(formatearEdad(1), "1 año");
  assert.equal(formatearEdad(2), "2 años");
  assert.equal(formatearEdad(12), "12 años");
});

test("una edad desconocida o inválida no se muestra", () => {
  for (const valor of [null, undefined, -1, 1.5, "2", NaN]) {
    assert.equal(formatearEdad(valor), null, `edad ${String(valor)}`);
  }
});

test("el sexo empieza en mayúscula y 'no_definido' no se muestra", () => {
  assert.equal(formatearSexo("hembra"), "Hembra");
  assert.equal(formatearSexo("macho"), "Macho");
  for (const valor of ["no_definido", "", null, undefined, "otro"]) {
    assert.equal(formatearSexo(valor), null, `sexo ${String(valor)}`);
  }
});

test("la línea de datos junta solo lo que se conoce", () => {
  assert.equal(
    datosMascota({ breed: "Labrador", age: 2, gender: "hembra" }),
    "Labrador · 2 años · Hembra",
  );
  assert.equal(datosMascota({ breed: "Siamés", age: 0, gender: "macho" }), "Siamés · Menos de 1 año · Macho");
  // Sin raza ni sexo definido: no quedan separadores sueltos.
  assert.equal(datosMascota({ breed: null, age: 3, gender: "no_definido" }), "3 años");
  assert.equal(datosMascota({ breed: "  ", age: null, gender: "no_definido" }), "");
  assert.equal(datosMascota(null), "");
});

test("la línea de datos no incluye tamaño, vacunación ni esterilización", () => {
  const texto = datosMascota({
    breed: "Mestizo",
    age: 4,
    gender: "macho",
    size: "Grande",
    vaccinated: true,
    sterilized: false,
  });
  assert.equal(texto, "Mestizo · 4 años · Macho");
});
