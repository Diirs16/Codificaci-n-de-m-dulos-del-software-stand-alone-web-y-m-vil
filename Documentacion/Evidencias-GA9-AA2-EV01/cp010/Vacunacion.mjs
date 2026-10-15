// Implementación de referencia de la clase Vacunacion (plan de pruebas GA9-AA1-EV02, Figura 3).
const MS_POR_DIA = 24 * 60 * 60 * 1000;
export const DIAS_ANTICIPACION_AVISO = 3;

export const EstadoRecordatorio = Object.freeze({
  PROGRAMADO: "PROGRAMADO",
  AVISO_ACTIVO: "AVISO_ACTIVO",
  VENCIDA: "VENCIDA",
});

// Fechas "AAAA-MM-DD" en UTC para evitar corrimientos por la zona horaria
const aFecha = (iso) => new Date(`${iso}T00:00:00Z`);
const aIso = (fecha) => fecha.toISOString().slice(0, 10);
const sumarDias = (fecha, dias) => new Date(fecha.getTime() + dias * MS_POR_DIA);

export class Vacunacion {
  constructor({ idMascota, nombreVacuna, fechaAplicacion, periodicidadDias }) {
    if (!Number.isInteger(periodicidadDias) || periodicidadDias <= 0) {
      throw new RangeError("La periodicidad debe ser un entero positivo de días");
    }
    this.idMascota = idMascota;
    this.nombreVacuna = nombreVacuna;
    this.fechaAplicacion = fechaAplicacion;
    this.periodicidadDias = periodicidadDias;
  }

  calcularProximaDosis() {
    return sumarDias(aFecha(this.fechaAplicacion), this.periodicidadDias);
  }

  generarRecordatorio(hoyIso) {
    const proxima = this.calcularProximaDosis();
    const aviso = sumarDias(proxima, -DIAS_ANTICIPACION_AVISO);
    const hoy = aFecha(hoyIso);

    let estado = EstadoRecordatorio.PROGRAMADO;
    if (hoy > proxima) estado = EstadoRecordatorio.VENCIDA;
    else if (hoy >= aviso) estado = EstadoRecordatorio.AVISO_ACTIVO;

    return {
      idMascota: this.idMascota,
      vacuna: this.nombreVacuna,
      fechaProximaDosis: aIso(proxima),
      fechaAviso: aIso(aviso),
      estado,
    };
  }
}
