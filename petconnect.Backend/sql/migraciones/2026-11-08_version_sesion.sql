-- ================================================================
-- PETCONNECT - Migracion del 08/11/2026 (PRIORIDADES 4.13, A-03)
--
-- Para bases creadas antes del 08/11/2026 (item 4.13). Una base nueva no
-- la necesita: schema.sql ya trae la columna.
-- Como ejecutarla (con respaldo previo): sql/README.md
--
-- Agrega a usuarios la columna version_sesion (empieza en 0). El token de
-- la API lleva ese numero y require_auth lo compara con la BD en cada
-- peticion: sumarle 1 (POST /api/auth/logout) cierra todas las sesiones
-- abiertas de esa cuenta, en todos los aparatos.
--
-- No cambia ni borra ningun dato: las filas que ya existen quedan con 0.
-- Agregar la columna no toca fecha_actualizacion.
-- Usa ADD COLUMN IF NOT EXISTS (existe en MariaDB, no en MySQL), asi que
-- se puede ejecutar varias veces sin danar nada.
-- Hay que ejecutarla ANTES de arrancar la API con el codigo del 4.13.
-- Evitar el punto y coma dentro de los comentarios: las pruebas
-- separan las sentencias por ese caracter.
-- ================================================================

SET SESSION sql_mode = 'STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

ALTER TABLE `usuarios`
  ADD COLUMN IF NOT EXISTS `version_sesion` int(10) unsigned NOT NULL DEFAULT 0 AFTER `estado`;
