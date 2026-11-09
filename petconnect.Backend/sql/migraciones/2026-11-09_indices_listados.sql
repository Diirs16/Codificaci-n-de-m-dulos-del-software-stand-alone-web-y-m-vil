-- ================================================================
-- PETCONNECT - Migracion del 09/11/2026 (PRIORIDADES 4.17, A-11, NC-003)
--
-- Para bases creadas antes del 09/11/2026. Una base nueva no la
-- necesita: schema.sql ya trae los indices.
-- Como ejecutarla (con respaldo previo): sql/README.md
--
-- Agrega tres indices para que la base no revise la tabla entera en
-- cada listado:
--   idx_mascotas_estado     listado de adopcion de la API
--   idx_productos_activo    catalogo de productos de la API
--   idx_proveedores_ciudad  busqueda por ciudad de la consola
-- Son los mismos de schema.sql (lo revisa tests/test_esquema.py).
--
-- No cambia ni borra ningun dato ni ninguna columna.
-- Usa CREATE INDEX IF NOT EXISTS (existe en MariaDB, no en MySQL), asi
-- que se puede ejecutar varias veces sin danar nada.
-- Se puede ejecutar antes o despues de arrancar la API: sin los
-- indices todo funciona igual, solo que mas lento con muchas filas.
-- Evitar el punto y coma dentro de los comentarios: las pruebas
-- separan las sentencias por ese caracter.
-- ================================================================

SET SESSION sql_mode = 'STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

CREATE INDEX IF NOT EXISTS `idx_mascotas_estado` ON `mascotas` (`estado`);

CREATE INDEX IF NOT EXISTS `idx_productos_activo` ON `productos` (`activo`);

CREATE INDEX IF NOT EXISTS `idx_proveedores_ciudad` ON `proveedores_servicio` (`ciudad`,`activo`,`nombre`);
