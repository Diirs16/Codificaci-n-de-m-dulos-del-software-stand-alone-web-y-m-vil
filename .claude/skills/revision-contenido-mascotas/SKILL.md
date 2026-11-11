---
name: revision-contenido-mascotas
description: Revisa contenido de PetConnect antes de publicarlo - textos de salud animal (vacunas, dosis, enfermedades, alimentación), imágenes y su licencia, y manejo de datos personales de dueños (Ley 1581 de 2012). Úsala antes de publicar, al agregar textos de cuidados o fichas de mascotas, o cuando se guarden datos de usuarios.
argument-hint: "[archivo o carpeta a revisar; vacío = cambios sin commit]"
---

# Revisión de contenido: $ARGUMENTS

Alcance: si `$ARGUMENTS` está vacío, revisa los archivos de `git diff` y `git diff --cached`.
Esta skill **no modifica** archivos salvo para agregar marcas `REVISAR-VETERINARIO` si el usuario lo aprueba.

## 1. Contenido veterinario y de salud
Busca textos sobre: vacunas, desparasitación, dosis, medicamentos, enfermedades, síntomas, esterilización,
alimentación, edades de adopción, cuidados post-operatorios.
Por cada hallazgo indica: archivo:línea, la frase, y el riesgo (dato que puede ser incorrecto o peligroso).
- Marca cada uno con `<!-- REVISAR-VETERINARIO -->` (JSX/HTML) o `# REVISAR-VETERINARIO` (Python).
- Nunca inventes dosis ni calendarios de vacunación; usa frases como "consulta a tu veterinario".
- Recuérdale al usuario: **un veterinario debe validar estos textos antes de publicarlos**.

## 2. Imágenes y recursos
- Lista imágenes nuevas (`src/assets/`, `public/`, `PetConnect.Mobile/assets/`) y URLs externas de imágenes.
- Pregunta o anota el origen: propia, licencia libre (Unsplash/Pexels), generada, o desconocida.
- Las de origen desconocido se marcan como "reemplazar antes de publicar".
- Verifica que tengan texto alternativo (`alt` / `accessibilityLabel`).

## 3. Datos personales (Habeas Data, Ley 1581 de 2012)
- ¿Se piden, guardan o muestran correo, teléfono, dirección, documento o datos del dueño?
- Comprueba: no aparecen en logs (`print`, `console.log`), ni en URLs, ni en mensajes de error al usuario.
- Comprueba que las rutas que devuelven datos de un usuario usen `@require_auth` y solo devuelvan los suyos.
- Si es un formulario nuevo que recoge datos: debe haber aviso de tratamiento de datos / autorización.
- Los datos de prueba deben ser ficticios.

## 4. Informe
Tabla final con: categoría, archivo:línea, hallazgo, gravedad (alta / media / baja), acción sugerida.
Termina con un veredicto: "listo para publicar" o "pendiente de: ...".
