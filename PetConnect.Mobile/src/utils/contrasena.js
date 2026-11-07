// Ítem 4.1 parte 3 (A-17, NC-004): COPIA de PetConnect.Front/petconnect-app/src/utils/contrasena.js.
// Las MISMAS reglas, en el mismo orden, que petconnect.Backend/security/politica.py
// (validar_contrasena). Se revisan aquí primero para avisar sin llamar a la API;
// la API las vuelve a revisar.
// tests/contrasena.test.mjs compara este código con el de la web y los límites con
// politica.py: si cambia una regla, cambiarla en politica.py, en la web y aquí.
// JS puro (sin React Native) para que `npm test` lo pueda probar con Node.
// TextEncoder: Hermes lo trae desde React Native 0.74 (aquí 0.86).

export const LARGO_MIN = 8;
export const LARGO_MAX = 64;
const MAX_BYTES_BCRYPT = 72; // bcrypt solo procesa 72 bytes; un emoji ocupa 4
export const CARACTERES_ESPECIALES = '@ # ! " $ & ? ¡ - _ * .';

// Python cuenta un emoji como 1 carácter y JavaScript (p.length) como 2.
// [...p] separa por carácter real, así los dos lados cuentan igual.
const largo = (p) => [...p].length;
const bytes = (p) => new TextEncoder().encode(p).length;

// Mayúscula y minúscula: solo A-Z y a-z (sin tildes ni ñ), igual que la API.
// label = texto de la lista de requisitos; mensaje = aviso cuando falla.
export const REGLAS_CONTRASENA = [
  {
    id: "len",
    label: `Mínimo ${LARGO_MIN} caracteres`,
    mensaje: `La contraseña debe tener al menos ${LARGO_MIN} caracteres`,
    test: (p) => largo(p) >= LARGO_MIN,
  },
  {
    id: "max",
    label: `Máximo ${LARGO_MAX} caracteres`,
    mensaje: `La contraseña debe tener máximo ${LARGO_MAX} caracteres`,
    test: (p) => largo(p) <= LARGO_MAX && bytes(p) <= MAX_BYTES_BCRYPT,
  },
  {
    id: "upper",
    label: "Al menos una mayúscula",
    mensaje: "La contraseña debe tener al menos una mayúscula",
    test: (p) => /[A-Z]/.test(p),
  },
  {
    id: "lower",
    label: "Al menos una minúscula",
    mensaje: "La contraseña debe tener al menos una minúscula",
    test: (p) => /[a-z]/.test(p),
  },
  {
    id: "number",
    label: "Al menos un número",
    mensaje: "La contraseña debe tener al menos un número",
    test: (p) => /[0-9]/.test(p),
  },
  {
    id: "special",
    label: `Al menos un carácter especial: ${CARACTERES_ESPECIALES}`,
    mensaje: `La contraseña debe tener al menos un carácter especial: ${CARACTERES_ESPECIALES}`,
    test: (p) => /[@#!"$&?¡\-_*.]/.test(p),
  },
];

/** Mensaje de la primera regla que no se cumple; null si la contraseña sirve. */
export function validarContrasena(password) {
  const p = password ?? "";
  const fallida = REGLAS_CONTRASENA.find((regla) => !regla.test(p));
  return fallida ? fallida.mensaje : null;
}
