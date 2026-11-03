-- ================================================================
-- PETCONNECT - Migracion del 03/11/2026 (PRIORIDADES 1.2, NC-009 y NC-010)
--
-- Solo para bases creadas ANTES de sql/schema.sql. Una base nueva ya
-- trae estos cambios y no necesita este archivo.
-- Como ejecutarla (con respaldo previo): sql/README.md
--
-- Que hace:
--   1. Agrega 'en_adopcion' al estado de mascotas.
--   2. Corrige las mascotas que quedaron con estado vacio. Ese vacio
--      lo dejo MariaDB al recibir 'en_adopcion' cuando no existia.
--   3. Agrega la regla de fechas de vacunas (chk_aplicacion_fechas).
--
-- Todo corre en modo estricto: si algo no encaja, MariaDB da un error
-- y no cambia el dato en silencio. Corrige lo que indique el error y
-- vuelve a ejecutar el archivo.
--
-- Se puede ejecutar varias veces sin danar nada. Usa DROP CONSTRAINT
-- IF EXISTS, que existe en MariaDB pero no en MySQL.
-- Evitar el punto y coma dentro de los comentarios: las pruebas
-- separan las sentencias por ese caracter.
-- ================================================================

SET SESSION sql_mode = 'STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- Paso 1a: el estado pasa a texto libre. Cada valor se copia igual,
-- incluido el vacio, asi que aqui no se pierde nada.
ALTER TABLE `mascotas`
  MODIFY `estado` varchar(20) DEFAULT 'activa';

-- Paso 1b (NC-009): el unico valor que pudo quedar vacio era 'en_adopcion'
UPDATE `mascotas` SET `estado` = 'en_adopcion' WHERE `estado` = '';

-- Paso 1c: vuelve a la lista cerrada, igual a sql/schema.sql. Si alguna
-- mascota tiene un estado que no esta en la lista, este paso falla y
-- ese valor se conserva. Corrigelo y vuelve a ejecutar el archivo.
ALTER TABLE `mascotas`
  MODIFY `estado` enum('activa','en_adopcion','perdida','adoptada','fallecida') DEFAULT 'activa';

-- Paso 2 (NC-010): si ya hay vacunas con fechas invertidas, este paso
-- falla y avisa. Corrigelas primero y vuelve a ejecutar el archivo.
ALTER TABLE `aplicaciones_vacuna` DROP CONSTRAINT IF EXISTS `chk_aplicacion_fechas`;

ALTER TABLE `aplicaciones_vacuna`
  ADD CONSTRAINT `chk_aplicacion_fechas` CHECK (`fecha_proxima` IS NULL OR `fecha_proxima` > `fecha_aplicacion`);
