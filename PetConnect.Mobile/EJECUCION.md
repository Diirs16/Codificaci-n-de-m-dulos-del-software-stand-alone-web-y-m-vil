# Ejecución del módulo móvil (PetConnect.Mobile) — Android

Guía operativa con los comandos reales usados para generar el APK, levantar el
ambiente completo y diagnosticar los problemas más comunes en Windows.
Complementa la evidencia `Documentacion/GA8-220501096-AA2-EV02-PetConnect.docx`.

## 1. Requisitos previos (ya instalados en este equipo)

| Herramienta | Ubicación |
|---|---|
| Entorno virtual Python (backend) | `Evidecia\.venv` |
| Android SDK | `C:\Users\<usuario>\AppData\Local\Android\Sdk` |
| JDK (Android Studio) | `C:\Program Files\Android\Android Studio\jbr` |
| Emulador configurado | AVD `Pixel_7` |

## 2. Generar el proyecto Android nativo y el APK (solo la primera vez, o si cambia el código nativo)

```bash
cd PetConnect.Mobile
npx expo prebuild -p android --no-install
cd android
./gradlew assembleDebug
```

APK resultante: `PetConnect.Mobile/android/app/build/outputs/apk/debug/app-debug.apk`

> La variante `assembleRelease` falla en este equipo con
> `ninja: error: ... Filename longer than 260 characters` porque la ruta del
> proyecto (dentro de OneDrive) supera el límite clásico de rutas de Windows.
> Se documenta como limitación conocida; se usa la variante `debug` + Metro.

## 3. Arrancar todo para usar/probar la app (cada vez)

Se necesitan **3 procesos corriendo al mismo tiempo**, cada uno en su propia
terminal:

**Terminal 1 — Backend Flask** (usar el Python del entorno virtual, no el global):

```powershell
cd Evidecia
.\.venv\Scripts\Activate.ps1
cd petconnect.Backend
python api.py
```

Debe mostrar: `[OK] API PetConnect corriendo en http://localhost:5000`

**Terminal 2 — Metro (bundler de JavaScript)**:

```bash
cd PetConnect.Mobile
npx expo start
```

Debe mostrar: `Waiting on http://localhost:8081`

**Terminal 3 — Emulador y conexión**:

```powershell
& "C:\Users\goku8\AppData\Local\Android\Sdk\emulator\emulator.exe" -avd Pixel_7
```

Esperar a que encienda por completo, luego:

```powershell
& "C:\Users\goku8\AppData\Local\Android\Sdk\platform-tools\adb.exe" reverse tcp:8081 tcp:8081
& "C:\Users\goku8\AppData\Local\Android\Sdk\platform-tools\adb.exe" install -r "PetConnect.Mobile\android\app\build\outputs\apk\debug\app-debug.apk"
```

Abrir la app en el emulador (o si ya estaba abierta con error, forzar recarga):

```powershell
& "C:\Users\goku8\AppData\Local\Android\Sdk\platform-tools\adb.exe" shell am force-stop com.petconnect.mobile
& "C:\Users\goku8\AppData\Local\Android\Sdk\platform-tools\adb.exe" shell monkey -p com.petconnect.mobile -c android.intent.category.LAUNCHER 1
```

## 4. Comandos de diagnóstico

Verificar que el backend responde:

```bash
curl http://127.0.0.1:5000/api/productos
```

Verificar que el emulador está conectado:

```powershell
& "C:\Users\goku8\AppData\Local\Android\Sdk\platform-tools\adb.exe" devices
```

Verificar que Metro está vivo y sirviendo el proyecto correcto (sin necesidad
de la app, directo desde la terminal):

```bash
curl http://127.0.0.1:8081/status
# debe responder: packager-status:running

curl "http://127.0.0.1:8081/index.bundle?platform=android&dev=true" -o bundle.js
# debe descargar varios MB de JavaScript válido, sin errores
```

## 5. Problemas encontrados y solución

| Síntoma | Causa | Solución |
|---|---|---|
| `ModuleNotFoundError: No module named 'dotenv'` al correr `python api.py` | Se ejecutó con el Python global de Windows, no con el del entorno virtual | Activar `.venv` (`.\.venv\Scripts\Activate.ps1`) o llamar directo a `.venv\Scripts\python.exe api.py` |
| Pantalla roja **"Unable to load script"** en la app | El APK debug no trae el JavaScript empacado: necesita Metro corriendo y el puerto reenviado | Levantar `npx expo start` y ejecutar `adb reverse tcp:8081 tcp:8081`, luego recargar la app |
| `adb: no devices/emulators found` | El emulador no está encendido, se cerró o aún no termina de arrancar | Encender el AVD desde Android Studio o `emulator -avd Pixel_7`, esperar a que cargue por completo y confirmar con `adb devices` |
| `adb` no se reconoce como comando | `platform-tools` no está en el PATH de la terminal actual | Usar la ruta completa a `adb.exe`, o agregar `platform-tools` al `PATH` de la sesión |
| `./gradlew assembleRelease` falla con `Filename longer than 260 characters` | Límite de rutas de Windows, agravado por la ruta larga dentro de OneDrive | Usar la variante `assembleDebug` + Metro (ver sección 2); la solución de fondo (rutas largas de Windows o mover el proyecto) queda fuera del alcance de esta evidencia |
| `Port 8081 is being used by another process` al correr `npx expo start` | Ya había un Metro corriendo de un intento anterior | Verificar con `curl http://127.0.0.1:8081/status` antes de abrir uno nuevo; si ya responde `running`, no hace falta otro |
