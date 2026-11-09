// Ítem 4.13, parte 3 (A-03): botón "Cerrar sesión" del móvil.
// JavaScript puro (sin React Native) para que `npm test` lo pruebe con Node
// (tests/cerrar-sesion.test.mjs). Hace lo mismo que cerrarSesion de la web
// (PetConnect.Front/petconnect-app/src/utils/sesion.js), pero con await porque
// AsyncStorage (donde el móvil guarda el token) es asíncrono.

// Si la API no contesta en este tiempo, se deja de esperar (cuenta como sin red).
export const TIEMPO_CIERRE_MS = 8000;

/**
 * Llama a hacerPeticion(signal) y la corta si pasan `ms` milisegundos sin respuesta.
 * Se usa AbortController + setTimeout (no AbortSignal.timeout, que puede no existir en
 * React Native). Al cortarla, fetch lanza un AbortError SIN status: cerrarSesion lo
 * trata como "sin-confirmar". El temporizador se limpia siempre (no queda colgado).
 */
export async function conLimiteDeTiempo(hacerPeticion, ms = TIEMPO_CIERRE_MS) {
  const control = new AbortController();
  const temporizador = setTimeout(() => control.abort(), ms);
  try {
    return await hacerPeticion(control.signal);
  } finally {
    clearTimeout(temporizador);
  }
}

/**
 * Pide a la API que cierre la sesión (POST /auth/logout: deja de valer en TODOS los
 * aparatos de la cuenta) y SIEMPRE borra la sesión de este celular, responda lo que
 * responda: nadie queda "atrapado" con la sesión abierta.
 *
 * Devuelve cómo quedó la sesión en el servidor:
 *   "cerrada"        → 200: el token ya no vale en ningún aparato
 *   "ya-cerrada"     → 401 (el token ya no valía) o no había token: no se avisa nada
 *   "sin-confirmar"  → 503, 502, 500, sin red o tiempo agotado (error sin status):
 *                      este celular sí cerró, pero los otros aparatos podrían seguir
 *                      con la sesión (decisión del dueño, A1: se muestra un aviso)
 */
export async function cerrarSesion({ leerToken, cerrarEnServidor, borrarLocal }) {
  const token = await leerToken();
  if (!token) {
    await borrarLocal(); // sin token no hay nada que cerrar en la API
    return "ya-cerrada";
  }

  let resultado;
  try {
    await cerrarEnServidor();
    resultado = "cerrada";
  } catch (error) {
    resultado = error?.status === 401 ? "ya-cerrada" : "sin-confirmar";
  }

  // Se borra siempre, salvo que mientras se esperaba entrara OTRA cuenta
  // (un token distinto): esa sesión nueva no se toca.
  const tokenAhora = await leerToken();
  if (!tokenAhora || tokenAhora === token) await borrarLocal();
  return resultado;
}
