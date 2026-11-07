// Ítem 3.5 (A-20, R05): piezas de JavaScript puro que usa src/services/api.js.
// Están aparte porque api.js importa react-native y Node no lo puede cargar:
// así las pruebas (tests/peticiones.test.mjs) las ejecutan de verdad.
// Hacen lo mismo que errorDeApi y loginUser de la web (src/services/api.js).

/**
 * Error de una respuesta que no fue ok. Lleva:
 * - status: código HTTP (ej. 403).
 * - requiereAutorizacion: true SOLO si la API mandó "requiere_autorizacion": true
 *   (el 403 "Cuenta inactiva" no lo trae, y un texto "true" tampoco cuenta).
 */
export function errorDeApi(mensaje, status, data) {
  const error = new Error(mensaje);
  error.status = status;
  error.requiereAutorizacion = data?.requiere_autorizacion === true;
  return error;
}

/**
 * Cuerpo de POST /auth/login. "acepta_datos" va solo si la persona marcó la
 * casilla (aceptaDatos === true, el booleano): un texto "true" o un 1 no
 * cuentan. Sin la casilla el campo no se manda.
 */
export function cuerpoLogin(email, password, aceptaDatos) {
  const cuerpo = { email, password };
  if (aceptaDatos === true) cuerpo.acepta_datos = true;
  return cuerpo;
}

// --- Solicitudes (ítem 3.6 parte 3, A-21): los mismos cuerpos que manda la web ---
// El nombre y el correo NO viajan: la API los toma de la cuenta del token (C.13, C.14).

/** Cuerpo de POST /solicitudes/adopcion. La mascota va como número; el teléfono es opcional. */
export function cuerpoSolicitudAdopcion(idMascota, mensaje, telefono = "") {
  return { id_mascota: Number(idMascota), mensaje, telefono };
}

/** Cuerpo de POST /solicitudes/contacto: solo el mensaje (sin mascota ni teléfono). */
export function cuerpoMensajeContacto(mensaje) {
  return { mensaje };
}
