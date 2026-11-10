-- ================================================================
-- PETCONNECT - Migracion del 10/11/2026 (PRIORIDADES 5.2, A-30)
--
-- Para bases creadas antes del 10/11/2026. Una base nueva no la
-- necesita: schema.sql ya trae las claves asi.
-- Como ejecutarla (con respaldo previo): sql/README.md
--
-- Cambia dos claves foraneas de ON UPDATE CASCADE a ON UPDATE RESTRICT:
--   fk_solicitud_mascota  solicitudes.id_mascota  -> mascotas
--   fk_otp_usuario        otp_pendientes.id_usuario -> usuarios
-- Esas columnas tambien estan en una regla CHECK (chk_solicitud_tipo y
-- chk_otp_proposito). MariaDB 10.5 en adelante (Docker usa 10.11) no
-- acepta una regla CHECK sobre una columna que una clave foranea
-- cambiaria sola: error 1901 al crear la tabla. MariaDB 10.4 si lo
-- acepta, por eso esta base funciona hoy. Con esta migracion queda
-- igual que schema.sql y lista para una version nueva de MariaDB.
--
-- Nada cambia en la practica: los id se crean solos (AUTO_INCREMENT) y
-- el codigo nunca los modifica. ON DELETE CASCADE se queda: borrar una
-- mascota o una cuenta sigue borrando sus solicitudes y codigos.
--
-- No cambia ni borra ningun dato, columna ni tabla. Usa DROP FOREIGN
-- KEY IF EXISTS (existe en MariaDB, no en MySQL), asi que se puede
-- ejecutar varias veces sin danar nada. Las mismas definiciones de
-- schema.sql (lo revisa tests/test_esquema.py).
-- Evitar el punto y coma dentro de los comentarios: las pruebas
-- separan las sentencias por ese caracter.
-- ================================================================

SET SESSION sql_mode = 'STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

ALTER TABLE `solicitudes` DROP FOREIGN KEY IF EXISTS `fk_solicitud_mascota`;

ALTER TABLE `solicitudes`
  ADD CONSTRAINT `fk_solicitud_mascota` FOREIGN KEY (`id_mascota`) REFERENCES `mascotas` (`id_mascota`) ON DELETE CASCADE ON UPDATE RESTRICT;

ALTER TABLE `otp_pendientes` DROP FOREIGN KEY IF EXISTS `fk_otp_usuario`;

ALTER TABLE `otp_pendientes`
  ADD CONSTRAINT `fk_otp_usuario` FOREIGN KEY (`id_usuario`) REFERENCES `usuarios` (`id_usuario`) ON DELETE CASCADE ON UPDATE RESTRICT;
