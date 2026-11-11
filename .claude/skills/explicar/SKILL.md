---
name: explicar
description: Explica como para principiante lo que se acaba de hacer, un archivo, una función o un concepto del proyecto PetConnect. Úsala cuando el usuario diga "explícame", "¿qué hace esto?", "¿por qué lo hiciste así?" o "enséñame a cambiarlo yo solo".
argument-hint: "[archivo, función, concepto o vacío para lo último que se hizo]"
---

# Explicar: $ARGUMENTS

Si `$ARGUMENTS` está vacío, explica el **último cambio** de esta conversación (o el último commit con
`git show --stat HEAD` si la conversación es nueva).

## Formato de la explicación (en español, tono cercano, sin relleno)

1. **En una frase**: qué es o qué hace.
2. **Analogía** de la vida real (una sola, corta). Ej.: "el JWT es como la manilla de un evento: te la
   ponen al entrar y con ella pasas sin volver a mostrar la boleta".
3. **Cómo funciona aquí**: recorre el flujo con los archivos reales del proyecto, citando
   `ruta/archivo:línea`. Máximo ~10 líneas de código citado; resume el resto.
4. **Por qué así y no de otra forma**: la alternativa que se descartó y la razón.
5. **Hazlo tú mismo**: un ejercicio pequeño y seguro que el usuario pueda hacer solo
   (ej. "cambia el color del botón en `src/components/ProductCard.jsx` línea X, de `bg-emerald-600` a ...")
   y cómo comprobar que funcionó.
6. **Palabras nuevas**: glosario de 1 línea por término técnico que apareció.

## Reglas
- No cambies ningún archivo en esta skill; solo explica.
- Si detectas que algo de lo que explicas está mal o es inseguro, dilo al final en "Ojo con esto".
