---
name: reportar-error
description: Ordena un error de PetConnect en un reporte claro (qué hice, qué esperaba, qué pasó, error completo) y lo depura paso a paso hasta la causa raíz. Úsala cuando el usuario diga "no funciona", "salió un error", "se rompió" o pegue una traza o captura de un fallo.
argument-hint: "[descripción del problema]"
---

# Reporte y depuración: $ARGUMENTS

## 1. Completar el reporte
Arma esta ficha con lo que el usuario dio. Si falta algo importante, pídelo **todo en un solo mensaje**:

| Campo | Contenido |
|---|---|
| Módulo | Backend / Web / Móvil |
| Qué hice | pasos exactos |
| Qué esperaba | resultado esperado |
| Qué pasó | resultado real |
| Error completo | texto de la terminal o de la consola del navegador (F12 → Console) o captura |
| ¿Desde cuándo? | ¿funcionaba antes? ¿qué cambió? (`git log --oneline -5`, `git diff`) |

Pista para el usuario: el error se copia completo, no solo la última línea; en el navegador también sirve
la pestaña **Network** (F12) para ver qué respondió la API.

## 2. Reproducir
Intenta reproducir el error tú mismo (correr pruebas, llamar al endpoint, levantar el módulo).
Si no se puede reproducir, dilo y explica qué información falta.

## 3. Aislar y encontrar la causa
- Sigue el flujo: interfaz → `services/api.js` → ruta en `api.py` → `dao/` → MySQL.
- Errores frecuentes en este proyecto: MySQL apagado (puerto 3310), `.env` incompleto
  (comparar con `.env.example`, sin abrir `.env`), token JWT vencido o ausente (401),
  CORS, backend no corriendo (el proxy de Vite responde 500/502), `10.0.2.2` vs `localhost` en el móvil.
- Formula la causa en una frase **antes** de cambiar código.

## 4. Corregir y probar
- Cambio mínimo que arregle la causa, no el síntoma.
- Si es del backend, agrega una prueba en `tests/` que habría detectado el error.
- Vuelve a correr la reproducción y confirma que ya no falla.

## 5. Explicar
Resume: causa, arreglo, cómo evitarlo la próxima vez. Propón `/guardar-partida`.
