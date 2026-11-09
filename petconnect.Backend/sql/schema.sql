-- ================================================================
-- PETCONNECT - Esquema de la base de datos (solo estructura)
--
-- Exportado de la BD de desarrollo (MariaDB 10.4.32) el 03/11/2026
-- y corregido segun la auditoria (A-01, NC-009 y NC-010).
-- No contiene datos personales: solo tablas y catalogos fijos.
--
-- Orden de uso (detalle en sql/README.md):
--   1. Crear la base "petconnect" (utf8mb4)
--   2. Cargar este archivo dentro de ella
--   3. python seed.py   (productos y mascotas de ejemplo)
--
-- Usa CREATE TABLE IF NOT EXISTS: nunca borra ni reemplaza tablas.
-- Evitar el punto y coma dentro de los comentarios: las pruebas
-- separan las sentencias por ese caracter.
-- ================================================================

-- Modo estricto: un dato invalido produce error en vez de guardarse
-- vacio en silencio (causa de NC-009). La conexion de la API activa
-- el mismo modo en config/db_config.py
SET SESSION sql_mode = 'STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';
SET NAMES utf8mb4;

-- ----------------------------------------------------------------
-- Usuarios y roles
-- ----------------------------------------------------------------

-- NC-005 (item 3.1, 05/11/2026): nadie autoriza el tratamiento de sus
-- datos por defecto (Ley 1581 art. 9). acepta_datos = 1 exige la fecha
-- y la version de la politica aceptada (regla chk_autorizacion_datos).

CREATE TABLE IF NOT EXISTS `roles` (
  `id_rol` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(50) NOT NULL,
  `descripcion` varchar(150) DEFAULT NULL,
  PRIMARY KEY (`id_rol`),
  UNIQUE KEY `nombre` (`nombre`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;

CREATE TABLE IF NOT EXISTS `usuarios` (
  `id_usuario` int(11) NOT NULL AUTO_INCREMENT,
  `nombres` varchar(100) NOT NULL,
  `apellidos` varchar(100) DEFAULT NULL,
  `correo` varchar(120) NOT NULL,
  `telefono` varchar(20) DEFAULT NULL,
  `password_hash` varchar(255) NOT NULL,
  `foto_perfil` varchar(255) DEFAULT NULL,
  `estado` enum('activo','inactivo','bloqueado') DEFAULT 'activo',
  `version_sesion` int(10) unsigned NOT NULL DEFAULT 0,
  `verificado` tinyint(1) DEFAULT 0,
  `acepta_datos` tinyint(1) NOT NULL DEFAULT 0,
  `fecha_autorizacion_datos` datetime DEFAULT NULL,
  `version_politica_datos` varchar(20) DEFAULT NULL,
  `fecha_creacion` timestamp NOT NULL DEFAULT current_timestamp(),
  `fecha_actualizacion` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id_usuario`),
  UNIQUE KEY `correo` (`correo`),
  CONSTRAINT `chk_autorizacion_datos` CHECK (`acepta_datos` = 0 OR (`fecha_autorizacion_datos` IS NOT NULL AND `version_politica_datos` IS NOT NULL))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;

CREATE TABLE IF NOT EXISTS `usuarios_roles` (
  `id_usuario` int(11) NOT NULL,
  `id_rol` int(11) NOT NULL,
  PRIMARY KEY (`id_usuario`,`id_rol`),
  KEY `fk_ur_rol` (`id_rol`),
  CONSTRAINT `fk_ur_rol` FOREIGN KEY (`id_rol`) REFERENCES `roles` (`id_rol`) ON UPDATE CASCADE,
  CONSTRAINT `fk_ur_usuario` FOREIGN KEY (`id_usuario`) REFERENCES `usuarios` (`id_usuario`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;

CREATE TABLE IF NOT EXISTS `direcciones` (
  `id_direccion` int(11) NOT NULL AUTO_INCREMENT,
  `id_usuario` int(11) NOT NULL,
  `etiqueta` varchar(50) DEFAULT NULL,
  `direccion_linea1` varchar(150) NOT NULL,
  `direccion_linea2` varchar(150) DEFAULT NULL,
  `ciudad` varchar(80) NOT NULL,
  `departamento` varchar(80) DEFAULT NULL,
  `codigo_postal` varchar(15) DEFAULT NULL,
  `pais` varchar(80) DEFAULT 'Colombia',
  `principal` tinyint(1) DEFAULT 0,
  PRIMARY KEY (`id_direccion`),
  KEY `fk_direccion_usuario` (`id_usuario`),
  CONSTRAINT `fk_direccion_usuario` FOREIGN KEY (`id_usuario`) REFERENCES `usuarios` (`id_usuario`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;

CREATE TABLE IF NOT EXISTS `metodos_pago` (
  `id_metodo_pago` int(11) NOT NULL AUTO_INCREMENT,
  `id_usuario` int(11) NOT NULL,
  `tipo` enum('tarjeta','pse','nequi','daviplata','otro') NOT NULL,
  `titular` varchar(120) DEFAULT NULL,
  `referencia_token` varchar(150) DEFAULT NULL,
  `ultimos4` varchar(4) DEFAULT NULL,
  `activo` tinyint(1) DEFAULT 1,
  `fecha_creacion` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id_metodo_pago`),
  KEY `fk_metodo_usuario` (`id_usuario`),
  CONSTRAINT `fk_metodo_usuario` FOREIGN KEY (`id_usuario`) REFERENCES `usuarios` (`id_usuario`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;

-- ----------------------------------------------------------------
-- Planes y suscripciones
-- ----------------------------------------------------------------

CREATE TABLE IF NOT EXISTS `planes` (
  `id_plan` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(50) NOT NULL,
  `precio` decimal(10,2) NOT NULL DEFAULT 0.00,
  `duracion_dias` int(11) NOT NULL,
  `descripcion` varchar(255) DEFAULT NULL,
  `activo` tinyint(1) DEFAULT 1,
  PRIMARY KEY (`id_plan`),
  UNIQUE KEY `nombre` (`nombre`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;

CREATE TABLE IF NOT EXISTS `suscripciones` (
  `id_suscripcion` int(11) NOT NULL AUTO_INCREMENT,
  `id_usuario` int(11) NOT NULL,
  `id_plan` int(11) NOT NULL,
  `fecha_inicio` date NOT NULL,
  `fecha_fin` date NOT NULL,
  `estado` enum('activa','vencida','cancelada') DEFAULT 'activa',
  `auto_renovacion` tinyint(1) DEFAULT 0,
  PRIMARY KEY (`id_suscripcion`),
  KEY `fk_suscripcion_usuario` (`id_usuario`),
  KEY `fk_suscripcion_plan` (`id_plan`),
  CONSTRAINT `fk_suscripcion_plan` FOREIGN KEY (`id_plan`) REFERENCES `planes` (`id_plan`) ON UPDATE CASCADE,
  CONSTRAINT `fk_suscripcion_usuario` FOREIGN KEY (`id_usuario`) REFERENCES `usuarios` (`id_usuario`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;

-- ----------------------------------------------------------------
-- Tienda: productos, carrito, pedidos y pagos
-- ----------------------------------------------------------------

CREATE TABLE IF NOT EXISTS `categorias_producto` (
  `id_categoria_producto` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(80) NOT NULL,
  `descripcion` varchar(150) DEFAULT NULL,
  PRIMARY KEY (`id_categoria_producto`),
  UNIQUE KEY `nombre` (`nombre`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;

-- NC-003 (item 4.17): idx_productos_activo sirve al catalogo de la API
-- (WHERE activo = TRUE ORDER BY id_producto).
CREATE TABLE IF NOT EXISTS `productos` (
  `id_producto` int(11) NOT NULL AUTO_INCREMENT,
  `id_categoria_producto` int(11) NOT NULL,
  `nombre` varchar(120) NOT NULL,
  `descripcion` text DEFAULT NULL,
  `precio` decimal(10,2) NOT NULL,
  `stock` int(11) NOT NULL DEFAULT 0,
  `imagen_url` varchar(255) DEFAULT NULL,
  `activo` tinyint(1) DEFAULT 1,
  PRIMARY KEY (`id_producto`),
  KEY `fk_producto_categoria` (`id_categoria_producto`),
  KEY `idx_productos_activo` (`activo`),
  CONSTRAINT `fk_producto_categoria` FOREIGN KEY (`id_categoria_producto`) REFERENCES `categorias_producto` (`id_categoria_producto`) ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;

CREATE TABLE IF NOT EXISTS `carritos` (
  `id_carrito` int(11) NOT NULL AUTO_INCREMENT,
  `id_usuario` int(11) NOT NULL,
  `estado` enum('activo','cerrado','abandonado') DEFAULT 'activo',
  `fecha_creacion` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id_carrito`),
  KEY `fk_carrito_usuario` (`id_usuario`),
  CONSTRAINT `fk_carrito_usuario` FOREIGN KEY (`id_usuario`) REFERENCES `usuarios` (`id_usuario`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;

CREATE TABLE IF NOT EXISTS `carrito_detalle` (
  `id_carrito_detalle` int(11) NOT NULL AUTO_INCREMENT,
  `id_carrito` int(11) NOT NULL,
  `id_producto` int(11) NOT NULL,
  `cantidad` int(11) NOT NULL DEFAULT 1,
  `precio_unitario` decimal(10,2) NOT NULL,
  PRIMARY KEY (`id_carrito_detalle`),
  KEY `fk_carrito_detalle_carrito` (`id_carrito`),
  KEY `fk_carrito_detalle_producto` (`id_producto`),
  CONSTRAINT `fk_carrito_detalle_carrito` FOREIGN KEY (`id_carrito`) REFERENCES `carritos` (`id_carrito`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_carrito_detalle_producto` FOREIGN KEY (`id_producto`) REFERENCES `productos` (`id_producto`) ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;

CREATE TABLE IF NOT EXISTS `pedidos` (
  `id_pedido` int(11) NOT NULL AUTO_INCREMENT,
  `id_usuario` int(11) NOT NULL,
  `id_direccion` int(11) DEFAULT NULL,
  `fecha_pedido` timestamp NOT NULL DEFAULT current_timestamp(),
  `estado` enum('pendiente','pagado','enviado','entregado','cancelado') DEFAULT 'pendiente',
  `subtotal` decimal(10,2) NOT NULL DEFAULT 0.00,
  `total` decimal(10,2) NOT NULL DEFAULT 0.00,
  `observaciones` text DEFAULT NULL,
  PRIMARY KEY (`id_pedido`),
  KEY `fk_pedido_usuario` (`id_usuario`),
  KEY `fk_pedido_direccion` (`id_direccion`),
  CONSTRAINT `fk_pedido_direccion` FOREIGN KEY (`id_direccion`) REFERENCES `direcciones` (`id_direccion`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_pedido_usuario` FOREIGN KEY (`id_usuario`) REFERENCES `usuarios` (`id_usuario`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;

CREATE TABLE IF NOT EXISTS `pedido_detalle` (
  `id_pedido_detalle` int(11) NOT NULL AUTO_INCREMENT,
  `id_pedido` int(11) NOT NULL,
  `id_producto` int(11) NOT NULL,
  `cantidad` int(11) NOT NULL,
  `precio_unitario` decimal(10,2) NOT NULL,
  PRIMARY KEY (`id_pedido_detalle`),
  KEY `fk_pedido_detalle_pedido` (`id_pedido`),
  KEY `fk_pedido_detalle_producto` (`id_producto`),
  CONSTRAINT `fk_pedido_detalle_pedido` FOREIGN KEY (`id_pedido`) REFERENCES `pedidos` (`id_pedido`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_pedido_detalle_producto` FOREIGN KEY (`id_producto`) REFERENCES `productos` (`id_producto`) ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;

CREATE TABLE IF NOT EXISTS `pagos` (
  `id_pago` int(11) NOT NULL AUTO_INCREMENT,
  `id_pedido` int(11) DEFAULT NULL,
  `id_suscripcion` int(11) DEFAULT NULL,
  `id_metodo_pago` int(11) DEFAULT NULL,
  `monto` decimal(10,2) NOT NULL,
  `fecha_pago` timestamp NOT NULL DEFAULT current_timestamp(),
  `estado` enum('pendiente','aprobado','rechazado') DEFAULT 'pendiente',
  `referencia` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id_pago`),
  KEY `fk_pago_pedido` (`id_pedido`),
  KEY `fk_pago_suscripcion` (`id_suscripcion`),
  KEY `fk_pago_metodo` (`id_metodo_pago`),
  CONSTRAINT `fk_pago_metodo` FOREIGN KEY (`id_metodo_pago`) REFERENCES `metodos_pago` (`id_metodo_pago`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_pago_pedido` FOREIGN KEY (`id_pedido`) REFERENCES `pedidos` (`id_pedido`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_pago_suscripcion` FOREIGN KEY (`id_suscripcion`) REFERENCES `suscripciones` (`id_suscripcion`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;

-- ----------------------------------------------------------------
-- Mascotas, adopcion y salud
-- ----------------------------------------------------------------

-- NC-009: se agrega 'en_adopcion' al enum de estado. Antes no existia
-- y MariaDB, en modo no estricto, guardaba el estado vacio.
-- NC-003 (item 4.17): idx_mascotas_estado sirve al listado de adopcion
-- (WHERE estado = 'en_adopcion' ORDER BY id_mascota).
CREATE TABLE IF NOT EXISTS `mascotas` (
  `id_mascota` int(11) NOT NULL AUTO_INCREMENT,
  `id_usuario` int(11) NOT NULL,
  `nombre` varchar(80) NOT NULL,
  `especie` varchar(50) NOT NULL,
  `raza` varchar(80) DEFAULT NULL,
  `sexo` enum('macho','hembra','no_definido') DEFAULT 'no_definido',
  `fecha_nacimiento` date DEFAULT NULL,
  `edad_aprox` int(11) DEFAULT NULL,
  `color` varchar(50) DEFAULT NULL,
  `peso` decimal(5,2) DEFAULT NULL,
  `foto` varchar(255) DEFAULT NULL,
  `observaciones` text DEFAULT NULL,
  `estado` enum('activa','en_adopcion','perdida','adoptada','fallecida') DEFAULT 'activa',
  `fecha_registro` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id_mascota`),
  KEY `fk_mascota_usuario` (`id_usuario`),
  KEY `idx_mascotas_estado` (`estado`),
  CONSTRAINT `fk_mascota_usuario` FOREIGN KEY (`id_usuario`) REFERENCES `usuarios` (`id_usuario`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;

CREATE TABLE IF NOT EXISTS `adopciones` (
  `id_adopcion` int(11) NOT NULL AUTO_INCREMENT,
  `id_usuario` int(11) NOT NULL,
  `id_mascota` int(11) DEFAULT NULL,
  `nombre_mascota` varchar(80) NOT NULL,
  `especie` varchar(50) NOT NULL,
  `raza` varchar(80) DEFAULT NULL,
  `sexo` enum('macho','hembra','no_definido') DEFAULT 'no_definido',
  `edad_aprox` int(11) DEFAULT NULL,
  `tamano` varchar(30) DEFAULT NULL,
  `descripcion` text DEFAULT NULL,
  `estado_salud` varchar(150) DEFAULT NULL,
  `vacunada` tinyint(1) DEFAULT 0,
  `esterilizada` tinyint(1) DEFAULT 0,
  `desparasitada` tinyint(1) DEFAULT 0,
  `imagen_url` varchar(255) DEFAULT NULL,
  `estado` enum('disponible','en_proceso','adoptado') DEFAULT 'disponible',
  `fecha_publicacion` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id_adopcion`),
  KEY `fk_adopcion_usuario` (`id_usuario`),
  KEY `fk_adopcion_mascota` (`id_mascota`),
  CONSTRAINT `fk_adopcion_mascota` FOREIGN KEY (`id_mascota`) REFERENCES `mascotas` (`id_mascota`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_adopcion_usuario` FOREIGN KEY (`id_usuario`) REFERENCES `usuarios` (`id_usuario`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;

-- Item 3.6 (A-21, 07/11/2026): solicitudes de adopcion y mensajes de
-- contacto que una persona envia con su sesion iniciada. NO es la tabla
-- adopciones (esa es la publicacion de una mascota). El nombre y el correo
-- salen de la cuenta y no se repiten aqui. version_politica_datos es la
-- version de la politica que la cuenta tenia aceptada al enviar (prueba de
-- la autorizacion, Ley 1581 art. 17 b). Si se borra la cuenta o la mascota,
-- se borran sus solicitudes (politica v1.1, A.11). La regla
-- chk_solicitud_tipo exige la mascota solo en adopcion y deja el telefono
-- solo para adopcion. Misma definicion en migraciones/2026-11-07_solicitudes.sql
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
  CONSTRAINT `fk_solicitud_mascota` FOREIGN KEY (`id_mascota`) REFERENCES `mascotas` (`id_mascota`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_solicitud_usuario` FOREIGN KEY (`id_usuario`) REFERENCES `usuarios` (`id_usuario`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `chk_solicitud_tipo` CHECK (`tipo` = 'adopcion' AND `id_mascota` IS NOT NULL OR `tipo` = 'contacto' AND `id_mascota` IS NULL AND `telefono` IS NULL)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;

-- Item 4.6 (A-12, NC-003, 07/11/2026): codigos de un solo uso (OTP) del
-- registro y del inicio de sesion. Antes vivian en la memoria de la API y se
-- perdian al reiniciar o con varios procesos. Una fila por correo y proposito.
-- El codigo va cifrado con Fernet (FERNET_KEY), nunca en claro. vence y
-- ultimo_envio son segundos desde 1970 (time.time() de Python). Los datos del
-- registro pendiente (nombre, hash bcrypt y prueba de la autorizacion) son
-- datos personales (Ley 1581): la API borra la fila al verificar, al
-- bloquearse con 5 fallos y al vencer (los vencidos se borran cada vez que se
-- crea un codigo y al arrancar). La regla chk_otp_proposito deja el nombre y
-- el hash solo para el registro y el usuario solo para el inicio de sesion.
-- Misma definicion en migraciones/2026-11-07_otp_pendientes.sql
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
  CONSTRAINT `fk_otp_usuario` FOREIGN KEY (`id_usuario`) REFERENCES `usuarios` (`id_usuario`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `chk_otp_proposito` CHECK (`proposito` = 'registro' AND `nombre` IS NOT NULL AND `password_hash` IS NOT NULL AND `id_usuario` IS NULL OR `proposito` = 'login' AND `id_usuario` IS NOT NULL AND `nombre` IS NULL AND `password_hash` IS NULL)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;

CREATE TABLE IF NOT EXISTS `vacunas` (
  `id_vacuna` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `descripcion` varchar(255) DEFAULT NULL,
  `especie_aplicable` varchar(50) DEFAULT NULL,
  `dosis_recomendada` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id_vacuna`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;

CREATE TABLE IF NOT EXISTS `carnets_vacunacion` (
  `id_carnet` int(11) NOT NULL AUTO_INCREMENT,
  `id_mascota` int(11) NOT NULL,
  `numero_carnet` varchar(50) DEFAULT NULL,
  `archivo_url` varchar(255) DEFAULT NULL,
  `fecha_creacion` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id_carnet`),
  KEY `fk_carnet_mascota` (`id_mascota`),
  CONSTRAINT `fk_carnet_mascota` FOREIGN KEY (`id_mascota`) REFERENCES `mascotas` (`id_mascota`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;

-- NC-010: la proxima dosis debe ser posterior a la fecha de aplicacion.
CREATE TABLE IF NOT EXISTS `aplicaciones_vacuna` (
  `id_aplicacion` int(11) NOT NULL AUTO_INCREMENT,
  `id_mascota` int(11) NOT NULL,
  `id_vacuna` int(11) NOT NULL,
  `fecha_aplicacion` date NOT NULL,
  `fecha_proxima` date DEFAULT NULL,
  `veterinario` varchar(120) DEFAULT NULL,
  `observaciones` text DEFAULT NULL,
  `soporte_url` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id_aplicacion`),
  KEY `fk_aplicacion_mascota` (`id_mascota`),
  KEY `fk_aplicacion_vacuna` (`id_vacuna`),
  CONSTRAINT `fk_aplicacion_mascota` FOREIGN KEY (`id_mascota`) REFERENCES `mascotas` (`id_mascota`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_aplicacion_vacuna` FOREIGN KEY (`id_vacuna`) REFERENCES `vacunas` (`id_vacuna`) ON UPDATE CASCADE,
  CONSTRAINT `chk_aplicacion_fechas` CHECK (`fecha_proxima` IS NULL OR `fecha_proxima` > `fecha_aplicacion`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;

CREATE TABLE IF NOT EXISTS `historial_salud` (
  `id_historial` int(11) NOT NULL AUTO_INCREMENT,
  `id_mascota` int(11) NOT NULL,
  `tipo_registro` enum('consulta','tratamiento','cirugia','alergia','peso','comportamiento','otro') NOT NULL,
  `titulo` varchar(120) NOT NULL,
  `descripcion` text NOT NULL,
  `fecha_registro` datetime NOT NULL,
  `profesional` varchar(120) DEFAULT NULL,
  `archivo_url` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id_historial`),
  KEY `fk_historial_mascota` (`id_mascota`),
  CONSTRAINT `fk_historial_mascota` FOREIGN KEY (`id_mascota`) REFERENCES `mascotas` (`id_mascota`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;

CREATE TABLE IF NOT EXISTS `gps_dispositivos` (
  `id_dispositivo` int(11) NOT NULL AUTO_INCREMENT,
  `id_mascota` int(11) NOT NULL,
  `codigo_dispositivo` varchar(100) NOT NULL,
  `marca` varchar(80) DEFAULT NULL,
  `modelo` varchar(80) DEFAULT NULL,
  `activo` tinyint(1) DEFAULT 1,
  `fecha_asignacion` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id_dispositivo`),
  UNIQUE KEY `codigo_dispositivo` (`codigo_dispositivo`),
  KEY `fk_gps_mascota` (`id_mascota`),
  CONSTRAINT `fk_gps_mascota` FOREIGN KEY (`id_mascota`) REFERENCES `mascotas` (`id_mascota`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;

CREATE TABLE IF NOT EXISTS `gps_ubicaciones` (
  `id_ubicacion` int(11) NOT NULL AUTO_INCREMENT,
  `id_dispositivo` int(11) NOT NULL,
  `latitud` decimal(10,7) NOT NULL,
  `longitud` decimal(10,7) NOT NULL,
  `precision_metros` decimal(8,2) DEFAULT NULL,
  `fecha_registro` datetime NOT NULL,
  PRIMARY KEY (`id_ubicacion`),
  KEY `fk_ubicacion_dispositivo` (`id_dispositivo`),
  CONSTRAINT `fk_ubicacion_dispositivo` FOREIGN KEY (`id_dispositivo`) REFERENCES `gps_dispositivos` (`id_dispositivo`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;

-- ----------------------------------------------------------------
-- Proveedores de servicios, resenas y citas
-- ----------------------------------------------------------------

CREATE TABLE IF NOT EXISTS `categorias_servicio` (
  `id_categoria_servicio` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(80) NOT NULL,
  `descripcion` varchar(150) DEFAULT NULL,
  PRIMARY KEY (`id_categoria_servicio`),
  UNIQUE KEY `nombre` (`nombre`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;

-- NC-003 (item 4.17): idx_proveedores_ciudad sirve a la busqueda por
-- ciudad de la consola (WHERE ciudad = ? AND activo = TRUE ORDER BY
-- nombre). La busqueda por nombre usa LIKE '%texto%', que no puede usar
-- un indice normal.
CREATE TABLE IF NOT EXISTS `proveedores_servicio` (
  `id_proveedor` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(120) NOT NULL,
  `tipo_documento` varchar(20) DEFAULT NULL,
  `numero_documento` varchar(30) DEFAULT NULL,
  `telefono` varchar(20) DEFAULT NULL,
  `correo` varchar(120) DEFAULT NULL,
  `direccion` varchar(150) DEFAULT NULL,
  `ciudad` varchar(80) DEFAULT NULL,
  `descripcion` text DEFAULT NULL,
  `horario` varchar(120) DEFAULT NULL,
  `atiende_24_7` tinyint(1) DEFAULT 0,
  `latitud` decimal(10,7) DEFAULT NULL,
  `longitud` decimal(10,7) DEFAULT NULL,
  `activo` tinyint(1) DEFAULT 1,
  PRIMARY KEY (`id_proveedor`),
  KEY `idx_proveedores_ciudad` (`ciudad`,`activo`,`nombre`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;

CREATE TABLE IF NOT EXISTS `servicios` (
  `id_servicio` int(11) NOT NULL AUTO_INCREMENT,
  `id_proveedor` int(11) NOT NULL,
  `id_categoria_servicio` int(11) NOT NULL,
  `nombre` varchar(120) NOT NULL,
  `descripcion` text DEFAULT NULL,
  `precio_base` decimal(10,2) DEFAULT NULL,
  `disponible` tinyint(1) DEFAULT 1,
  PRIMARY KEY (`id_servicio`),
  KEY `fk_servicio_proveedor` (`id_proveedor`),
  KEY `fk_servicio_categoria` (`id_categoria_servicio`),
  CONSTRAINT `fk_servicio_categoria` FOREIGN KEY (`id_categoria_servicio`) REFERENCES `categorias_servicio` (`id_categoria_servicio`) ON UPDATE CASCADE,
  CONSTRAINT `fk_servicio_proveedor` FOREIGN KEY (`id_proveedor`) REFERENCES `proveedores_servicio` (`id_proveedor`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;

CREATE TABLE IF NOT EXISTS `resenas_servicio` (
  `id_resena` int(11) NOT NULL AUTO_INCREMENT,
  `id_usuario` int(11) NOT NULL,
  `id_servicio` int(11) NOT NULL,
  `calificacion` tinyint(4) NOT NULL CHECK (`calificacion` between 1 and 5),
  `comentario` text DEFAULT NULL,
  `fecha_creacion` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id_resena`),
  KEY `fk_resena_usuario` (`id_usuario`),
  KEY `fk_resena_servicio` (`id_servicio`),
  CONSTRAINT `fk_resena_servicio` FOREIGN KEY (`id_servicio`) REFERENCES `servicios` (`id_servicio`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_resena_usuario` FOREIGN KEY (`id_usuario`) REFERENCES `usuarios` (`id_usuario`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;

CREATE TABLE IF NOT EXISTS `citas` (
  `id_cita` int(11) NOT NULL AUTO_INCREMENT,
  `id_mascota` int(11) NOT NULL,
  `id_proveedor` int(11) DEFAULT NULL,
  `tipo_cita` enum('veterinaria','peluqueria','vacunacion','estetica','emergencia','otro') NOT NULL,
  `fecha_hora` datetime NOT NULL,
  `estado` enum('pendiente','confirmada','cancelada','realizada') DEFAULT 'pendiente',
  `motivo` varchar(150) DEFAULT NULL,
  `observaciones` text DEFAULT NULL,
  PRIMARY KEY (`id_cita`),
  KEY `fk_cita_mascota` (`id_mascota`),
  KEY `fk_cita_proveedor` (`id_proveedor`),
  CONSTRAINT `fk_cita_mascota` FOREIGN KEY (`id_mascota`) REFERENCES `mascotas` (`id_mascota`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_cita_proveedor` FOREIGN KEY (`id_proveedor`) REFERENCES `proveedores_servicio` (`id_proveedor`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;

-- ----------------------------------------------------------------
-- Comunidad
-- ----------------------------------------------------------------

CREATE TABLE IF NOT EXISTS `publicaciones_comunidad` (
  `id_publicacion` int(11) NOT NULL AUTO_INCREMENT,
  `id_usuario` int(11) NOT NULL,
  `titulo` varchar(150) NOT NULL,
  `contenido` text NOT NULL,
  `imagen_url` varchar(255) DEFAULT NULL,
  `estado` enum('visible','oculta','reportada') DEFAULT 'visible',
  `fecha_creacion` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id_publicacion`),
  KEY `fk_publicacion_usuario` (`id_usuario`),
  CONSTRAINT `fk_publicacion_usuario` FOREIGN KEY (`id_usuario`) REFERENCES `usuarios` (`id_usuario`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;

CREATE TABLE IF NOT EXISTS `comentarios_publicacion` (
  `id_comentario` int(11) NOT NULL AUTO_INCREMENT,
  `id_publicacion` int(11) NOT NULL,
  `id_usuario` int(11) NOT NULL,
  `comentario` text NOT NULL,
  `fecha_creacion` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id_comentario`),
  KEY `fk_comentario_publicacion` (`id_publicacion`),
  KEY `fk_comentario_usuario` (`id_usuario`),
  CONSTRAINT `fk_comentario_publicacion` FOREIGN KEY (`id_publicacion`) REFERENCES `publicaciones_comunidad` (`id_publicacion`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_comentario_usuario` FOREIGN KEY (`id_usuario`) REFERENCES `usuarios` (`id_usuario`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;

CREATE TABLE IF NOT EXISTS `reportes_publicacion` (
  `id_reporte` int(11) NOT NULL AUTO_INCREMENT,
  `id_publicacion` int(11) NOT NULL,
  `id_usuario` int(11) NOT NULL,
  `motivo` varchar(150) NOT NULL,
  `detalle` text DEFAULT NULL,
  `fecha_reporte` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id_reporte`),
  KEY `fk_reporte_publicacion` (`id_publicacion`),
  KEY `fk_reporte_usuario` (`id_usuario`),
  CONSTRAINT `fk_reporte_publicacion` FOREIGN KEY (`id_publicacion`) REFERENCES `publicaciones_comunidad` (`id_publicacion`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_reporte_usuario` FOREIGN KEY (`id_usuario`) REFERENCES `usuarios` (`id_usuario`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;

-- ----------------------------------------------------------------
-- Notificaciones y recordatorios
-- ----------------------------------------------------------------

CREATE TABLE IF NOT EXISTS `notificaciones` (
  `id_notificacion` int(11) NOT NULL AUTO_INCREMENT,
  `id_usuario` int(11) NOT NULL,
  `tipo` enum('vacuna','cita','pedido','adopcion','comunidad','seguridad','premium','otro') NOT NULL,
  `titulo` varchar(120) NOT NULL,
  `mensaje` varchar(255) NOT NULL,
  `leida` tinyint(1) DEFAULT 0,
  `fecha_envio` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id_notificacion`),
  KEY `fk_notificacion_usuario` (`id_usuario`),
  CONSTRAINT `fk_notificacion_usuario` FOREIGN KEY (`id_usuario`) REFERENCES `usuarios` (`id_usuario`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;

CREATE TABLE IF NOT EXISTS `recordatorios` (
  `id_recordatorio` int(11) NOT NULL AUTO_INCREMENT,
  `id_usuario` int(11) NOT NULL,
  `id_mascota` int(11) DEFAULT NULL,
  `id_cita` int(11) DEFAULT NULL,
  `id_aplicacion` int(11) DEFAULT NULL,
  `titulo` varchar(120) NOT NULL,
  `mensaje` varchar(255) NOT NULL,
  `canal` enum('app','whatsapp','sms','correo') NOT NULL,
  `fecha_programada` datetime NOT NULL,
  `estado` enum('pendiente','enviado','fallido','cancelado') DEFAULT 'pendiente',
  PRIMARY KEY (`id_recordatorio`),
  KEY `fk_recordatorio_usuario` (`id_usuario`),
  KEY `fk_recordatorio_mascota` (`id_mascota`),
  KEY `fk_recordatorio_cita` (`id_cita`),
  KEY `fk_recordatorio_aplicacion` (`id_aplicacion`),
  CONSTRAINT `fk_recordatorio_aplicacion` FOREIGN KEY (`id_aplicacion`) REFERENCES `aplicaciones_vacuna` (`id_aplicacion`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_recordatorio_cita` FOREIGN KEY (`id_cita`) REFERENCES `citas` (`id_cita`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_recordatorio_mascota` FOREIGN KEY (`id_mascota`) REFERENCES `mascotas` (`id_mascota`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_recordatorio_usuario` FOREIGN KEY (`id_usuario`) REFERENCES `usuarios` (`id_usuario`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;

-- ----------------------------------------------------------------
-- Catalogos fijos (no son datos personales)
-- INSERT IGNORE: si la fila ya existe, no hace nada.
-- ----------------------------------------------------------------

INSERT IGNORE INTO `roles` (`id_rol`, `nombre`, `descripcion`) VALUES
  (1, 'admin', 'Administrador del sistema'),
  (2, 'cliente', 'Usuario final de la aplicación'),
  (3, 'proveedor', 'Proveedor de servicios o productos');

INSERT IGNORE INTO `planes` (`id_plan`, `nombre`, `precio`, `duracion_dias`, `descripcion`, `activo`) VALUES
  (1, 'Gratuito', 0.00, 30, 'Acceso básico a la plataforma', 1),
  (2, 'Premium Mensual', 19900.00, 30, 'Incluye GPS, historial avanzado y recordatorios personalizados', 1),
  (3, 'Premium Anual', 199000.00, 365, 'Incluye funciones premium por un año', 1);
