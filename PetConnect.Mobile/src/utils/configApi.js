// Ítem 5.3, parte 1 (A-27): de dónde sale la dirección de la API y de la web.
// JavaScript puro (sin React Native) para que `npm test` lo pruebe con Node
// (tests/config-api.test.mjs). Lo usa src/services/api.js.
//
// Antes la dirección estaba fija en el código (http://10.0.2.2:5000 o
// http://localhost:5000): solo servía en el emulador y siempre por HTTP sin
// cifrar. Ahora se puede dar con EXPO_PUBLIC_API_URL y EXPO_PUBLIC_WEB_URL
// (plantilla en PetConnect.Mobile/.env.example).
//
// OJO: Expo copia el valor de toda variable EXPO_PUBLIC_ dentro de la app al
// compilarla. Cualquiera que tenga la app puede leerlo: ahí va solo una
// dirección pública, NUNCA una clave, un token ni una contraseña.

// Direcciones que no salen del computador o del emulador: por eso aceptan HTTP
// sin cifrar aunque la app esté compilada (p. ej. el `npx expo export` local).
// 10.0.2.2 es el computador visto desde el emulador de Android.
export const HOSTS_LOCALES = ["localhost", "127.0.0.1", "10.0.2.2", "[::1]"];

/** Computador de desarrollo visto desde la app (lo que se usaba antes del 5.3). */
export function hostDeDesarrollo(plataforma) {
  return plataforma === "android" ? "10.0.2.2" : "localhost";
}

// protocolo://servidor[:puerto][/ruta], sin ?consulta ni #ancla. Se usa una
// expresión regular y no `new URL()` porque en React Native URL no siempre trae
// hostname completo.
const FORMA_URL = /^(https?):\/\/([^/?#\s]+)(\/[^?#\s]*)?$/i;

/** Quita las barras del final: "https://a.com/api/" → "https://a.com/api". */
function sinBarraFinal(texto) {
  return texto.replace(/\/+$/, "");
}

/** Nombre del servidor sin el puerto: "api.ejemplo.com:8443" → "api.ejemplo.com". */
function nombreDelServidor(autoridad) {
  if (autoridad.startsWith("[")) return autoridad.slice(0, autoridad.indexOf("]") + 1);
  return autoridad.split(":")[0];
}

/**
 * Revisa una dirección escrita en una variable EXPO_PUBLIC_.
 * Devuelve { url } con la dirección limpia o { error } con el motivo.
 *   - Solo http:// o https://, sin usuario ni contraseña dentro (quedarían a la vista).
 *   - https:// obligatorio, salvo hacia HOSTS_LOCALES o en modo desarrollo
 *     (esDesarrollo = __DEV__, para probar con la IP del PC en un celular real).
 */
export function revisarUrl(valor, { esDesarrollo }) {
  const texto = sinBarraFinal(String(valor ?? "").trim());
  const partes = FORMA_URL.exec(texto);
  if (!partes) return { error: "no es una dirección http:// o https:// válida" };

  const [, protocolo, autoridad] = partes;
  if (autoridad.includes("@")) return { error: "no debe llevar usuario ni contraseña" };

  const servidor = nombreDelServidor(autoridad).toLowerCase();
  if (!servidor) return { error: "no es una dirección http:// o https:// válida" };
  const local = HOSTS_LOCALES.includes(servidor);
  if (protocolo.toLowerCase() === "http" && !local && !esDesarrollo) {
    return { error: "debe usar https:// (HTTP sin cifrar solo en desarrollo)" };
  }
  return { url: texto };
}

/**
 * Dirección base de la API (termina en /api).
 *   - Variable vacía → la de desarrollo de siempre: http://10.0.2.2:5000/api en
 *     Android y http://localhost:5000/api en web.
 *   - Con valor (p. ej. https://api.ejemplo.com) → se le agrega /api si no lo trae.
 * Si el valor no sirve devuelve { url: null, error } y la app NO lo usa: las
 * peticiones fallan con un mensaje (ver apiFetch) en vez de mandar datos sin cifrar.
 */
export function resolverUrlApi(valor, { plataforma, esDesarrollo }) {
  if (!String(valor ?? "").trim()) {
    return { url: `http://${hostDeDesarrollo(plataforma)}:5000/api`, error: null };
  }
  const { url, error } = revisarUrl(valor, { esDesarrollo });
  if (error) return { url: null, error: `EXPO_PUBLIC_API_URL ${error}` };
  return { url: url.endsWith("/api") ? url : `${url}/api`, error: null };
}

/**
 * Página de la Política de tratamiento de datos (NC-005, ítem 3.1), que publica la web.
 *   - Variable vacía → http://10.0.2.2:5173 o http://localhost:5173 (Vite en desarrollo).
 *   - Con valor (p. ej. https://petconnect.ejemplo.com) → se le agrega /politica-de-datos.
 */
export function resolverUrlPolitica(valor, { plataforma, esDesarrollo }) {
  if (!String(valor ?? "").trim()) {
    return { url: `http://${hostDeDesarrollo(plataforma)}:5173/politica-de-datos`, error: null };
  }
  const { url, error } = revisarUrl(valor, { esDesarrollo });
  if (error) return { url: null, error: `EXPO_PUBLIC_WEB_URL ${error}` };
  return { url: `${url}/politica-de-datos`, error: null };
}
