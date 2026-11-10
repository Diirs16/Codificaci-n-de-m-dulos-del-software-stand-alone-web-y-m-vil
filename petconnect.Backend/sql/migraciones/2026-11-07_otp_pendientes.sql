-- ================================================================
-- PETCONNECT - Migracion del 07/11/2026 (PRIORIDADES 4.6, A-12, NC-003)
--
-- Para bases creadas antes del 07/11/2026 (item 4.6). Una base nueva no
-- la necesita: schema.sql ya trae la tabla.
-- Como ejecutarla (con respaldo previo): sql/README.md
--
-- Crea la tabla otp_pendientes, donde la API guarda los codigos de
-- verificacion del registro y del inicio de sesion (antes vivian en la
-- memoria de la API). La definicion es la misma de schema.sql (lo revisa
-- tests/test_esquema.py).
--
-- No cambia ni borra ninguna tabla ni ningun dato. Usa CREATE TABLE
-- IF NOT EXISTS, asi que se puede ejecutar varias veces sin danar nada.
-- Necesita la tabla usuarios (clave foranea).
-- Hay que ejecutarla ANTES de arrancar la API con el codigo del 4.6.
-- 10/11/2026 (item 5.2): la clave foranea de id_usuario pasa a ON UPDATE
-- RESTRICT, igual que en schema.sql, porque MariaDB 10.11 no acepta la
-- regla CHECK con ON UPDATE CASCADE. Si ya habias aplicado esta
-- migracion, aplica tambien 2026-11-10_llaves_sin_cascada_update.sql.
-- Evitar el punto y coma dentro de los comentarios: las pruebas
-- separan las sentencias por ese caracter.
-- ================================================================

SET SESSION sql_mode = 'STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

CREATE TABLE IF NOT EXISTS `otp_pendientes` (
  `correo` varchar(120) NOT NULL,
  `proposito` enum('registro','login') NOT NULL,
  `codigo_cifrado` varchar(255) NOT NULL,
  `intentos` tinyint(3) unsigned NOT NULL DEFAULT 0,
  `reenvios` tinyint(3) unsigned NOT NULL DEFAULT 0,
  `vence` double NOT NULL,
  `ultimo_envio` double NOT NULL,
  `nombre` varchar(60) DEFAULT NULL,
  `password_hash` varchar(255) DEFAULT NULL,
  `id_usuario` int(11) DEFAULT NULL,
  `fecha_autorizacion_datos` datetime DEFAULT NULL,
  `version_politica_datos` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`correo`,`proposito`),
  KEY `idx_otp_vence` (`vence`),
  KEY `fk_otp_usuario` (`id_usuario`),
  CONSTRAINT `fk_otp_usuario` FOREIGN KEY (`id_usuario`) REFERENCES `usuarios` (`id_usuario`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `chk_otp_proposito` CHECK (`proposito` = 'registro' AND `nombre` IS NOT NULL AND `password_hash` IS NOT NULL AND `id_usuario` IS NULL OR `proposito` = 'login' AND `id_usuario` IS NOT NULL AND `nombre` IS NULL AND `password_hash` IS NULL)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;
