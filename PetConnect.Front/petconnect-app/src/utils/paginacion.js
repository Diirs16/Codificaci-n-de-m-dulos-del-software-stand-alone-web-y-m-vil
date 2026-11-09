// Ítem 4.17 (NC-003, A-11): los listados se piden por páginas.
// La API acepta ?pagina= y ?por_pagina= (20 por defecto, 50 como máximo) y
// responde una LISTA, sin el total. Por eso "hay más" se deduce así: si llegó
// una página llena, puede haber otra. Si justo no quedaban, el siguiente
// "Ver más" trae una lista vacía y el botón desaparece.

/** Cuántos pide cada pantalla. */
export const POR_PAGINA_DESTACADOS = 4; // Home: "Productos destacados"
export const POR_PAGINA_ADOPCION = 12;
export const POR_PAGINA_CATALOGO = 50; // el máximo de la API: el buscador revisa más productos

function esEnteroPositivo(valor) {
  return Number.isInteger(valor) && valor > 0;
}

/**
 * "/productos" + { pagina: 2, porPagina: 50 } → "/productos?pagina=2&por_pagina=50".
 * Sin opciones (o con valores que no son enteros positivos) la ruta queda igual
 * y la API usa sus valores por defecto. En la URL solo viajan estos números,
 * nunca datos personales (Ley 1581).
 */
export function rutaPaginada(ruta, { pagina, porPagina } = {}) {
  const parametros = new URLSearchParams();
  if (esEnteroPositivo(pagina)) parametros.set("pagina", String(pagina));
  if (esEnteroPositivo(porPagina)) parametros.set("por_pagina", String(porPagina));
  const consulta = parametros.toString();
  return consulta ? `${ruta}?${consulta}` : ruta;
}

/** true si la página llegó llena: puede haber otra después. */
export function hayMas(recibidos, porPagina) {
  return Array.isArray(recibidos) && recibidos.length >= porPagina;
}

/**
 * Agrega al final los elementos nuevos cuyo id no estaba. Si alguien publica o
 * retira una mascota entre dos "Ver más", las páginas se corren una posición
 * y podría llegar repetida: así no sale dos veces (ni choca la key de React).
 */
export function unirSinRepetir(actuales, nuevos) {
  const vistos = new Set(actuales.map((item) => item.id));
  return [...actuales, ...nuevos.filter((item) => !vistos.has(item.id))];
}
