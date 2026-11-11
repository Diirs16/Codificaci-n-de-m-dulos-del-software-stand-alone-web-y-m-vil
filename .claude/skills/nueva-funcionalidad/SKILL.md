---
name: nueva-funcionalidad
description: Flujo guiado para construir algo nuevo en PetConnect (una página, pantalla, endpoint o módulo) de forma ordenada - reunir contexto, proponer plan, construir por partes, probar y guardar partida. Úsala cuando el usuario pida agregar o crear una funcionalidad, sección o pantalla nueva.
argument-hint: "<qué quieres construir>"
---

# Nueva funcionalidad: $ARGUMENTS

Sigue estas fases **en orden**. No saltes a escribir código antes de la fase 3.

## Fase 1 — Contexto (como si fueras un desarrollador recién contratado)
Si la petición es corta o ambigua, haz como máximo 5 preguntas concretas, por ejemplo:
- ¿Para quién es? (adoptante, dueño de mascota, proveedor, administrador)
- ¿En qué módulo? (web, móvil, backend o varios)
- ¿Qué datos muestra o guarda? ¿Ya existen en la base de datos?
- ¿Cómo debe sentirse? (puedes pedir una captura de referencia: "quiero algo con esta vibra")
- ¿Qué NO debe hacer?
Lee el código relacionado antes de preguntar lo que ya puedes averiguar tú.

## Fase 2 — Plan (esperar aprobación)
Presenta el plan en lenguaje sencillo:
1. Qué se va a construir y qué no.
2. Archivos que se crean / modifican, agrupados por módulo.
3. Partes en las que se va a dividir (cada parte debe poder verse funcionando sola).
4. Tecnología o librería nueva, si hace falta, y **por qué** (preferir lo que ya usa el proyecto).
5. Riesgos: seguridad, datos personales, contenido veterinario.
Termina con: "¿Apruebas el plan o quieres cambiar algo?" y **espera**.

## Fase 3 — Construir por partes
Por cada parte del plan:
1. Implementa solo esa parte, respetando el `CLAUDE.md` del módulo.
2. Si es interfaz: aplica la skill `frontend-design`; diseño mobile first.
3. Verifica: backend → pruebas `unittest`; web → `npm run lint` y `npm run build`.
4. Dile al usuario cómo verlo (usa `/levantar-proyecto` si no está corriendo).
5. Explica en 3–5 líneas qué hiciste y por qué (estilo `/explicar`).
6. Pregunta si sigue con la próxima parte o quiere ajustes.

## Fase 4 — Cierre
1. Si hay interfaz nueva: sugiere `/impeccable audit` y luego `/impeccable polish`.
2. Si hay textos de salud animal, imágenes o datos personales: corre `/revision-contenido-mascotas`.
3. Propón guardar partida con `/guardar-partida`.
4. Si cambió la API, recuerda actualizar la colección de Postman y que el Front y el Móvil la consumen.
