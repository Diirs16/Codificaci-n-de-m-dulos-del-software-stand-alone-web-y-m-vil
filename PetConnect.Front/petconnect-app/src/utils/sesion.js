// Ítem 4.7 (A-24): al abrir la web se revisa con la API si la sesión guardada
// en localStorage sigue sirviendo. Antes se daba por buena siempre, aunque el
// token (24 h) hubiera vencido.
// JS puro (sin React) para que `npm test` lo pueda probar con Node; lo usa
// src/context/AuthContext.jsx.
//
// Devuelve qué hacer con la sesión:
//   { accion: "cerrar" }               → token vencido o falso (401), o datos sin token
//   { accion: "actualizar", perfil }   → token vigente: se guardan nombre y correo al día
//   { accion: "mantener" }             → la API no respondió bien (503, 502, 500, red caída):
//                                         eso NO es un token malo, la sesión no se toca
//   { accion: "ignorar" }              → mientras se esperaba la respuesta la sesión cambió
//                                         (cerró sesión o entró con otra cuenta)
//
// Decisión del dueño (08/11/2026, opción A): solo el 401 cierra la sesión. Un 404
// ("Usuario no encontrado") se trata como "mantener": el token vence en 24 h.
export async function revalidarSesion({ leerToken, obtenerPerfil }) {
  const token = leerToken();
  if (!token) return { accion: "cerrar" };

  let resultado;
  try {
    const perfil = await obtenerPerfil();
    resultado = { accion: "actualizar", perfil };
  } catch (error) {
    resultado = { accion: error?.status === 401 ? "cerrar" : "mantener" };
  }

  // Una respuesta atrasada no puede cerrar (ni pisar) una sesión nueva
  if (leerToken() !== token) return { accion: "ignorar" };
  return resultado;
}

// Ítem 4.13 (A-03): botón "Cerrar sesión". Pide a la API que cierre la sesión
// (POST /auth/logout, todos los aparatos) y SIEMPRE borra la sesión de este
// navegador, responda lo que responda: nadie queda "atrapado" con la sesión abierta.
// Lo usa src/context/AuthContext.jsx (logout).
//
// Devuelve cómo quedó la sesión en el servidor:
//   "cerrada"        → 200: el token ya no vale en ningún aparato
//   "ya-cerrada"     → 401 (el token ya no valía) o no había token: no se avisa nada
//   "sin-confirmar"  → 503, 502, 500, sin red o tiempo agotado: este navegador sí
//                      cerró, pero los otros aparatos podrían seguir con la sesión
//                      (decisión del dueño, A1: se muestra un aviso)
export async function cerrarSesion({ leerToken, cerrarEnServidor, borrarLocal }) {
  const token = leerToken();
  if (!token) {
    borrarLocal(); // sin token no hay nada que cerrar en la API
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
  const tokenAhora = leerToken();
  if (!tokenAhora || tokenAhora === token) borrarLocal();
  return resultado;
}
