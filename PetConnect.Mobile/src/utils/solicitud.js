// Ítem 3.6 parte 3 (A-21): COPIA de PetConnect.Front/petconnect-app/src/utils/solicitud.js.
// Las mismas reglas que valida la API en petconnect.Backend/api.py
// (_validar_mensaje y _validar_telefono). Se revisan aquí primero para avisar sin
// llamar a la API; la API las vuelve a revisar.
// tests/solicitudes.test.mjs compara este código con el de la web: si cambia una
// regla, cambiarla en api.py, en la web y aquí.
// JS puro (sin React Native) para que `npm test` lo pueda probar con Node.

export const MENSAJE_MIN = 10;
export const MENSAJE_MAX = 1000;
const TELEFONO_MAX = 20;
const TELEFONO_DIGITOS_MIN = 7;
const TELEFONO_DIGITOS_MAX = 15;

/** Mensaje de error si el mensaje no sirve; null si está bien. Cuenta sin los espacios de los extremos. */
export function validarMensaje(mensaje) {
  const largo = (mensaje ?? "").trim().length;
  if (largo < MENSAJE_MIN || largo > MENSAJE_MAX) {
    return `El mensaje debe tener entre ${MENSAJE_MIN} y ${MENSAJE_MAX} caracteres.`;
  }
  return null;
}

/** El teléfono es opcional: vacío está bien. Solo números, espacios y un + al inicio. */
export function validarTelefono(telefono) {
  const valor = (telefono ?? "").trim();
  if (valor === "") return null;
  const digitos = (valor.match(/[0-9]/g) ?? []).length;
  if (
    valor.length > TELEFONO_MAX ||
    !/^\+?[0-9 ]+$/.test(valor) ||
    digitos < TELEFONO_DIGITOS_MIN ||
    digitos > TELEFONO_DIGITOS_MAX
  ) {
    return `El teléfono solo puede tener números, espacios y un + al inicio (entre ${TELEFONO_DIGITOS_MIN} y ${TELEFONO_DIGITOS_MAX} dígitos).`;
  }
  return null;
}
