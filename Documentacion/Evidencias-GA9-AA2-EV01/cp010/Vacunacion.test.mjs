// CP-010 – Prueba unitaria del recordatorio de vacunación (RF03), con el ejecutor nativo de Node.js.
// Ejecutar: node --test Documentacion/Evidencias-GA9-AA2-EV01/cp010/
import { test, describe } from "node:test";
import assert from "node:assert/strict";
import { Vacunacion } from "./Vacunacion.mjs";

const antirrabica = {
  idMascota: 15,
  nombreVacuna: "Antirrábica",
  fechaAplicacion: "2025-11-03",
  periodicidadDias: 365,
};

describe("Vacunacion.generarRecordatorio()", () => {
  test("calcula la próxima dosis y el aviso tres días antes", () => {
    const r = new Vacunacion(antirrabica).generarRecordatorio("2026-10-20");
    assert.equal(r.fechaProximaDosis, "2026-11-03");
    assert.equal(r.fechaAviso, "2026-10-31");
    assert.equal(r.estado, "PROGRAMADO");
  });

  // Análisis de valores límite alrededor de la ventana de aviso
  for (const [hoy, esperado] of [
    ["2026-10-30", "PROGRAMADO"],   // un día antes del aviso
    ["2026-10-31", "AVISO_ACTIVO"], // primer día de la ventana
    ["2026-11-03", "AVISO_ACTIVO"], // día de la dosis
    ["2026-11-04", "VENCIDA"],      // un día después de la dosis
  ]) {
    test(`el ${hoy} el estado es ${esperado}`, () => {
      assert.equal(new Vacunacion(antirrabica).generarRecordatorio(hoy).estado, esperado);
    });
  }

  test("rechaza una periodicidad no positiva (valor límite 0)", () => {
    assert.throws(() => new Vacunacion({ ...antirrabica, periodicidadDias: 0 }), RangeError);
  });
});
