---
name: guardar-partida
description: Guarda partida en git de forma segura - revisa los cambios, corre las verificaciones del módulo tocado, busca secretos y hace un commit con mensaje en español. Úsala cuando el usuario diga "haz commit", "guarda lo que llevamos", "guardar partida" o cuando algo quedó funcionando.
argument-hint: "[mensaje opcional]"
---

# Guardar partida

## 1. Ver qué cambió
- `git status` y `git diff --stat`. Muéstrale al usuario la lista de archivos en lenguaje sencillo
  (qué se agregó, qué se modificó).
- Si hay archivos que **no** pertenecen a este cambio (por ejemplo trabajo a medias de otra cosa),
  pregunta si se incluyen o se dejan para otro commit. Nunca uses `git add -A` a ciegas: agrega por ruta.
- Si aparece un `.env`, llave o archivo pesado (videos, `node_modules`, `.venv`), **detente** y avisa.

## 2. Verificar según el módulo que cambió
- `petconnect.Backend/` → `../.venv/Scripts/python -m unittest discover -s tests -v` (desde esa carpeta).
- `PetConnect.Front/petconnect-app/` → `npm run lint` y `npm run build`.
- `PetConnect.Mobile/` → al menos que `npx expo export --platform web` o `npm start` no muestre errores
  (si es muy lento, pregunta antes).
Si algo falla, **no hagas commit**: muestra el error y propón arreglarlo primero.

## 3. Commit
- Mensaje en español, presente, una línea de máximo ~72 caracteres que diga *qué* cambia
  (ej. "Agrega filtro por especie en la página de adopción"). Si hace falta, un párrafo corto con el *por qué*.
- Si el usuario dio un mensaje (`$ARGUMENTS`), úsalo.
- El hook `revisar-commit.js` revisa secretos automáticamente; si bloquea el commit, explica qué encontró
  y cómo sacarlo a `.env`.

## 4. Después
- Muestra el hash corto y el mensaje (`git log --oneline -1`).
- **No** hagas `git push` salvo que el usuario lo pida explícitamente (pedirá confirmación).
- Recuerda: "si algo se rompe más adelante, podemos volver a este punto".
