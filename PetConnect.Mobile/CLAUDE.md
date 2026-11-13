# Móvil PetConnect — reglas del módulo

Se carga además del `CLAUDE.md` de la raíz cuando Claude trabaja dentro de esta carpeta.

@AGENTS.md

## Estructura
- `App.js` → `src/navigation/AppNavigator.js` (pestañas + pila de pantallas).
- `src/screens/` — una pantalla por archivo (`XxxScreen.js`).
- `src/context/AuthContext.js` — sesión; el token se guarda en `AsyncStorage`.
- `src/services/api.js` — única puerta hacia el backend (`10.0.2.2:5000` en Android, `localhost` en web).

## Reglas
- Expo 57: antes de usar una API de Expo, revisa la documentación de esa versión exacta (ver `AGENTS.md`).
- Probar siempre en el emulador de Android además de la web.
- Mismos endpoints y mismos mensajes que el Front web: si cambia la API, avisar que los dos clientes se afectan.

## Verificar
```bash
npm start          # menú de Expo
npm run android    # build nativo en emulador
```
