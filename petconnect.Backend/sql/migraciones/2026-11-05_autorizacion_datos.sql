-- ================================================================
-- PETCONNECT - Migracion del 05/11/2026 (PRIORIDADES 3.1, NC-005)
--
-- Solo para bases creadas ANTES de este cambio en sql/schema.sql.
-- Una base nueva ya trae estos cambios y no necesita este archivo.
-- Como ejecutarla (con respaldo previo): sql/README.md
--
-- Que hace (Ley 1581 de 2012, art. 9: autorizacion previa y expresa):
--   1. Agrega las columnas de la prueba de la autorizacion: la fecha
--      y la version de la politica de datos que acepto cada usuario.
--   2. Los usuarios que no tienen esa prueba quedan con acepta_datos = 0,
--      porque nadie les pidio la autorizacion (antes se guardaba 1 fijo).
--      No se inventa una fecha. Pueden seguir iniciando sesion.
--   3. acepta_datos deja de valer 1 por defecto (ahora NOT NULL DEFAULT 0).
--   4. Agrega la regla chk_autorizacion_datos: acepta_datos = 1 exige
--      fecha y version.
--
-- El paso 2 actualiza fecha_actualizacion de las filas que cambian.
--
-- Todo corre en modo estricto. Se puede ejecutar varias veces sin
-- danar nada: los usuarios que autorizaron despues de la primera vez
-- (con fecha y version) conservan su autorizacion. Usa ADD COLUMN IF
-- NOT EXISTS y DROP CONSTRAINT IF EXISTS, que existen en MariaDB pero
-- no en MySQL.
-- Evitar el punto y coma dentro de los comentarios: las pruebas
-- separan las sentencias por ese caracter.
-- ================================================================

SET SESSION sql_mode = 'STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- Paso 1: columnas de la prueba de la autorizacion (Decreto 1377, art. 8)
ALTER TABLE `usuarios`
  ADD COLUMN IF NOT EXISTS `fecha_autorizacion_datos` datetime DEFAULT NULL AFTER `acepta_datos`;

ALTER TABLE `usuarios`
  ADD COLUMN IF NOT EXISTS `version_politica_datos` varchar(20) DEFAULT NULL AFTER `fecha_autorizacion_datos`;

-- Paso 2: sin prueba no hay autorizacion
UPDATE `usuarios` SET `acepta_datos` = 0
  WHERE `acepta_datos` IS NULL
     OR `fecha_autorizacion_datos` IS NULL
     OR `version_politica_datos` IS NULL;

-- Paso 3: por defecto nadie autoriza
ALTER TABLE `usuarios`
  MODIFY `acepta_datos` tinyint(1) NOT NULL DEFAULT 0;

-- Paso 4: la misma regla de sql/schema.sql
ALTER TABLE `usuarios` DROP CONSTRAINT IF EXISTS `chk_autorizacion_datos`;

ALTER TABLE `usuarios`
  ADD CONSTRAINT `chk_autorizacion_datos` CHECK (`acepta_datos` = 0 OR (`fecha_autorizacion_datos` IS NOT NULL AND `version_politica_datos` IS NOT NULL));
