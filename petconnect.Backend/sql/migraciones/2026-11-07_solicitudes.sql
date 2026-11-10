-- ================================================================
-- PETCONNECT - Migracion del 07/11/2026 (PRIORIDADES 3.6, A-21)
--
-- Para bases creadas antes del 07/11/2026. Una base nueva no la
-- necesita: schema.sql ya trae la tabla.
-- Como ejecutarla (con respaldo previo): sql/README.md
--
-- Crea la tabla solicitudes, donde la API guarda las solicitudes de
-- adopcion y los mensajes de contacto que se envian con la sesion
-- iniciada. La definicion es la misma de schema.sql (lo revisa
-- tests/test_esquema.py).
--
-- No cambia ni borra ninguna tabla ni ningun dato. Usa CREATE TABLE
-- IF NOT EXISTS, asi que se puede ejecutar varias veces sin danar nada.
-- Necesita las tablas usuarios y mascotas (claves foraneas).
-- 10/11/2026 (item 5.2): la clave foranea de id_mascota pasa a ON UPDATE
-- RESTRICT, igual que en schema.sql, porque MariaDB 10.11 no acepta la
-- regla CHECK con ON UPDATE CASCADE. Si ya habias aplicado esta
-- migracion, aplica tambien 2026-11-10_llaves_sin_cascada_update.sql.
-- Evitar el punto y coma dentro de los comentarios: las pruebas
-- separan las sentencias por ese caracter.
-- ================================================================

SET SESSION sql_mode = 'STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

CREATE TABLE IF NOT EXISTS `solicitudes` (
  `id_solicitud` int(11) NOT NULL AUTO_INCREMENT,
  `id_usuario` int(11) NOT NULL,
  `tipo` enum('adopcion','contacto') NOT NULL,
  `id_mascota` int(11) DEFAULT NULL,
  `telefono` varchar(20) DEFAULT NULL,
  `mensaje` varchar(1000) NOT NULL,
  `version_politica_datos` varchar(20) NOT NULL,
  `fecha_envio` datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id_solicitud`),
  KEY `fk_solicitud_usuario` (`id_usuario`),
  KEY `fk_solicitud_mascota` (`id_mascota`),
  CONSTRAINT `fk_solicitud_mascota` FOREIGN KEY (`id_mascota`) REFERENCES `mascotas` (`id_mascota`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `fk_solicitud_usuario` FOREIGN KEY (`id_usuario`) REFERENCES `usuarios` (`id_usuario`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `chk_solicitud_tipo` CHECK (`tipo` = 'adopcion' AND `id_mascota` IS NOT NULL OR `tipo` = 'contacto' AND `id_mascota` IS NULL AND `telefono` IS NULL)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;
