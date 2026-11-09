// Ítem 4.17 (NC-003, A-11): los listados se piden por páginas.
// La API acepta ?pagina= y ?por_pagina= (20 por defecto, 50 como máximo) y
// responde una LISTA, sin el total. Por eso "hay más" se deduce así: si llegó
// una página llena, puede haber otra. Si justo no quedaban, el siguiente
// "Ver más" trae una lista vacía y el botón desaparece.
// JavaScript puro (sin react-native) para que las pruebas de Node lo carguen.
// Hace lo mismo que PetConnect.Front/petconnect-app/src/utils/paginacion.js.

/** Cuántos pide cada pantalla. */
export const POR_PAGINA_CATALOGO = 20; // HomeScreen: catálogo en 2 columnas, sin buscador
export const POR_PAGINA_ADOPCION = 12; // AdoptionScreen (igual que la web)

function esEnteroPositivo(valor) {
  return Number.isInteger(valor) && valor > 0;
}

/**
 * "/productos" + { pagina: 2, porPagina: 20 } → "/productos?pagina=2&por_pagina=20".
 * Sin opciones (o con valores que no son enteros positivos) la ruta queda igual
 * y la API usa sus valores por defecto. En la URL solo viajan estos números,
 * nunca datos personales (Ley 1581).
 */
export function rutaPaginada(ruta, { pagina, porPagina } = {}) {
  const parametros = [];
  if (esEnteroPositivo(pagina)) parametros.push(`pagina=${pagina}`);
  if (esEnteroPositivo(porPagina)) parametros.push(`por_pagina=${porPagina}`);
  return parametros.length ? `${ruta}?${parametros.join("&")}` : ruta;
}

/** true si la página llegó llena: puede haber otra después. */
export function hayMas(recibidos, porPagina) {
  return Array.isArray(recibidos) && recibidos.length >= porPagina;
}

/**
 * Agrega al final los elementos nuevos cuyo id no estaba. Si alguien publica o
 * retira una mascota entre dos "Ver más", las páginas se corren una posición
 * y podría llegar repetida: así no sale dos veces (ni choca el keyExtractor).
 */
export function unirSinRepetir(actuales, nuevos) {
  const vistos = new Set(actuales.map((item) => item.id));
  return [...actuales, ...nuevos.filter((item) => !vistos.has(item.id))];
}
