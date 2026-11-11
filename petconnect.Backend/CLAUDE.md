# Backend PetConnect — reglas del módulo

Se carga además del `CLAUDE.md` de la raíz cuando Claude trabaja dentro de esta carpeta.

## Estructura (arquitectura por capas + DAO)
- `api.py` — API REST Flask (rutas `/api/...`, puerto 5000). Rutas protegidas usan `@require_auth`.
- `main.py` + `vista/` — módulo de consola (menús).
- `dao/` — acceso a datos. **Único lugar donde se escribe SQL.**
- `modelo/` — entidades (Usuario, Mascota, Producto, ProveedorServicio).
- `conexion/conexion_bd.py` — pool de conexiones MySQL (`ConexionBD`, Singleton) y `conexion_y_cursor()`. `config/` lee el `.env`.
- `security/` — `passwords.py` (bcrypt), `jwt_helper.py` (tokens), `crypto.py` (Fernet).
- `correo/`, `otp/` — envío de códigos de verificación.
- `tests/` — pruebas con `unittest` (no requieren base de datos).

## Reglas
- SQL solo en `dao/` y siempre parametrizado: `cursor.execute(sql, (valor,))`.
- Toda consulta usa `with conexion_y_cursor(self._conexion_bd) as (conexion, cursor):` (ítem 4.5): devuelve la
  conexión al pool aunque haya error. Nunca pedir `obtener_conexion()` sin devolverla con `close()` en un `finally`.
- Respuestas de error de la API: `jsonify({"error": "mensaje en español"})` con el código HTTP correcto.
  Nunca devolver trazas (`traceback`) ni datos internos al cliente.
- Toda ruta que use datos del usuario logueado lleva `@require_auth`.
- Variables nuevas de configuración: agrégalas a `.env.example` (con valor vacío) y léelas con `os.getenv`.
- Dependencias nuevas: agrégalas a `requirements.txt` con versión fija (`paquete==x.y.z`).
- Si cambias algo de `security/`, corre las pruebas y agrega una prueba nueva en `tests/`.

## Verificar
```bash
../.venv/Scripts/python -m unittest discover -s tests -v
```
