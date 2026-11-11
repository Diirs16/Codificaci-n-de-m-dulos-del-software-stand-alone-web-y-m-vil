// Ítem 5.5, parte 3: de dónde saca la web la dirección de la API.
// JavaScript puro (sin React ni Vite) para que `npm test` lo pruebe con Node
// (tests/config-api.test.js). Lo usa src/services/api.js.
//
// En tu computador (npm run dev) y en Docker la web llama a "/api" y Vite o
// nginx se lo pasan a la API. En Vercel no hay quien haga eso: ahí la web llama
// directo a la API de Railway con la dirección que dice VITE_API_URL.
//
// OJO: Vite copia el valor de toda variable VITE_ dentro de la página al
// compilarla. Cualquiera puede leerlo en el navegador: ahí va solo una
// dirección pública, NUNCA una clave, un token ni una contraseña.

// Direcciones que no salen del computador: por eso aceptan HTTP sin cifrar
// (p. ej. `npm run preview` contra la API local).
export const HOSTS_LOCALES = ["localhost", "127.0.0.1", "[::1]"];

// La de siempre: el proxy de Vite (vite.config.js) o nginx (nginx.conf).
export const BASE_LOCAL = "/api";

// protocolo://servidor[:puerto][/ruta], sin ?consulta ni #ancla
const FORMA_URL = /^(https?):\/\/([^/?#\s]+)(\/[^?#\s]*)?$/i;

/** Nombre del servidor sin el puerto: "api.ejemplo.com:8443" → "api.ejemplo.com". */
function nombreDelServidor(autoridad) {
  if (autoridad.startsWith("[")) return autoridad.slice(0, autoridad.indexOf("]") + 1);
  return autoridad.split(":")[0];
}

/**
 * Dirección base de la API (termina en /api) a partir de VITE_API_URL.
 *   - Vacía o sin definir → "/api" (desarrollo y Docker, como antes).
 *   - https://dominio[:puerto][/ruta] → se le agrega /api si no lo trae.
 *   - http:// solo hacia HOSTS_LOCALES (afuera iría sin cifrar).
 *   - Sin usuario:clave@, sin ?consulta ni #ancla.
 * Si el valor no sirve devuelve { base: null, error } y la web NO lo usa: las
 * peticiones fallan con "No se pudo conectar" en vez de mandar datos sin cifrar
 * o a una dirección rara.
 */
export function resolverBaseApi(valor) {
  const texto = String(valor ?? "").trim().replace(/\/+$/, "");
  if (!texto) return { base: BASE_LOCAL, error: null };

  const partes = FORMA_URL.exec(texto);
  if (!partes) return { base: null, error: "VITE_API_URL no es una dirección http:// o https:// válida" };

  const [, protocolo, autoridad] = partes;
  if (autoridad.includes("@")) return { base: null, error: "VITE_API_URL no debe llevar usuario ni contraseña" };

  const servidor = nombreDelServidor(autoridad).toLowerCase();
  if (!servidor) return { base: null, error: "VITE_API_URL no es una dirección http:// o https:// válida" };
  if (protocolo.toLowerCase() === "http" && !HOSTS_LOCALES.includes(servidor)) {
    return { base: null, error: "VITE_API_URL debe usar https:// (http:// solo hacia este computador)" };
  }
  return { base: texto.endsWith("/api") ? texto : `${texto}/api`, error: null };
}
