// Validación de formato de correo, 100% en el navegador (instantánea, sin red).
// No puede confirmar que el correo "exista" de verdad: eso requiere consultar
// el dominio (ver services/api.js -> validarCorreo, que sí llama al backend).
const EMAIL_REGEX = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;

export function esFormatoCorreoValido(email) {
  return EMAIL_REGEX.test((email || "").trim());
}
