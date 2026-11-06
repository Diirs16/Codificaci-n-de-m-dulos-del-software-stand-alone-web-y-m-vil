// Ítem 3.4 (A-22): cómo se muestran los datos de una mascota en la web.
// La API manda lo que hay en la BD: age = edad_aprox (número entero de años,
// 0 = menos de 1 año, null = no se sabe) y gender = sexo ("macho", "hembra" o
// "no_definido"). Aquí se convierten en texto para la persona. Si un dato no
// se sabe, se devuelve null y la página no lo muestra: nunca se inventa.
// (Vacunación, esterilización y tamaño NO se muestran: la BD no los tiene.)

/** 0 → "Menos de 1 año", 1 → "1 año", 2 → "2 años"; cualquier otra cosa → null. */
export function formatearEdad(age) {
  if (!Number.isInteger(age) || age < 0) return null;
  if (age === 0) return "Menos de 1 año";
  return age === 1 ? "1 año" : `${age} años`;
}

const SEXOS = { hembra: "Hembra", macho: "Macho" };

/** "hembra" → "Hembra", "macho" → "Macho"; "no_definido" u otro valor → null. */
export function formatearSexo(gender) {
  return SEXOS[gender] ?? null;
}

/** Línea "Raza · Edad · Sexo" con solo los datos que se conocen ("" si no hay ninguno). */
export function datosMascota(pet) {
  const raza = typeof pet?.breed === "string" ? pet.breed.trim() : "";
  return [raza, formatearEdad(pet?.age), formatearSexo(pet?.gender)]
    .filter(Boolean)
    .join(" · ");
}
