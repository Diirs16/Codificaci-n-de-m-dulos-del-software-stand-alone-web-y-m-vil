---
name: levantar-proyecto
description: Arranca los servidores de PetConnect (backend Flask, web Vite y/o móvil Expo) y le dice al usuario qué dirección abrir. Úsala cuando pidan "levanta el servidor", "quiero ver la página", "corre la app" o antes de revisar un cambio visual.
argument-hint: "[backend | web | movil | todo]"
---

# Levantar PetConnect

Argumento recibido: `$ARGUMENTS` (si viene vacío, pregunta qué módulo quiere ver; si dice "web" o "movil",
levanta también el backend porque ambos lo necesitan).

## Pasos

1. **Revisa qué ya está corriendo** para no duplicar procesos: puertos 5000 (API), 5173 (web), 8081 (Expo)
   y 3310 (MySQL). En Windows: `netstat -ano | findstr :5000`.
2. **MySQL** (puerto 3310): si no responde, dile al usuario que lo encienda (servicio de Windows o Workbench).
   No intentes instalar ni reconfigurar MySQL.
3. **Backend** — siempre en segundo plano:
   - Carpeta `petconnect.Backend/`, con el intérprete `../.venv/Scripts/python`.
   - Comando: `../.venv/Scripts/python api.py`.
   - Si falla por variables faltantes, compara con `.env.example` (nunca abras `.env`) y dile al usuario
     cuáles debe completar. Si faltan `JWT_SECRET`/`FERNET_KEY`, indícale que corra `python generate_keys.py`
     (desde 6.3 no borra nada: solo llena las claves que falten). Nunca lo corras tú contra su `.env`.
4. **Web** — carpeta `PetConnect.Front/petconnect-app/`: si no existe `node_modules`, pide permiso para
   `npm install`; luego `npm run dev` en segundo plano. URL: http://localhost:5173
   - Si estás en la app de escritorio, ábrela en el navegador integrado para que el usuario la vea.
5. **Móvil** — carpeta `PetConnect.Mobile/`: `npm start` (Expo) o `npm run android` si hay emulador.
   Web de Expo: http://localhost:8081

## Al terminar
Responde con una tabla corta: módulo, URL, estado (arriba / falló + motivo) y cómo detenerlo.
Recuerda al usuario: "cada cambio que haga lo verás ahí al momento; si algo se ve mal, toma captura y pégala".
