-- ================================================================
-- PETCONNECT - Migracion del 06/11/2026 (PRIORIDADES 3.4, A-22)
--
-- Solo para bases que ya tienen las 6 mascotas de ejemplo en adopcion
-- (Luna, Milo, Rocky, Nala, Max y Cleo). Una base nueva no la necesita:
-- seed.py ya las crea con los datos corregidos.
-- Como ejecutarla (con respaldo previo): sql/README.md
--
-- Corrige dos datos que contradecian la ficha de esas mascotas:
--   1. El tamano guardado en la columna color. Segun como se cargaron,
--      dice "Grande", "Mediano", "Pequenio", "Pequeno" o "Tamano ...".
--      Ninguno es un color. Queda en NULL (sin dato), porque el color
--      real no se conoce y no se inventa.
--   2. La edad de Nala. Su descripcion dice "gatita" y seed.py le pone
--      0 (6 meses, menos de 1 anio), pero en algunas bases quedo en 6,
--      que la ficha muestra como 6 anios. Se corrige a 0 solo si sigue en 6.
--
-- Como reconoce las mascotas de ejemplo: por su nombre Y su especie,
-- y solo si estan en adopcion. No usa el id ni el dueno, porque cambian
-- de una base a otra (en la base de desarrollo del 06/11/2026 no son de
-- la cuenta del refugio de seed.py). Una mascota con el mismo nombre
-- pero otra especie, u otro estado, queda igual.
--
-- Los patrones usan _ (un caracter cualquiera) en lugar de la enie,
-- para que funcionen aunque la consola use otra codificacion.
--
-- No cambia la estructura de ninguna tabla. Se puede ejecutar varias
-- veces sin danar nada: la segunda vez no encuentra filas.
-- Evitar el punto y coma dentro de los comentarios: las pruebas
-- separan las sentencias por ese caracter.
-- ================================================================

SET SESSION sql_mode = 'STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- Paso 1: el tamano sale de la columna color
UPDATE `mascotas` SET `color` = NULL
  WHERE (`color` LIKE 'Tama_o %' OR `color` IN ('Grande', 'Mediano', 'Pequenio') OR `color` LIKE 'Peque_o')
    AND `estado` = 'en_adopcion'
    AND (`nombre`, `especie`) IN (('Luna', 'Perro'), ('Milo', 'Gato'), ('Rocky', 'Perro'), ('Nala', 'Gato'), ('Max', 'Perro'), ('Cleo', 'Gato'));

-- Paso 2: Nala tiene 6 meses, no 6 anios
UPDATE `mascotas` SET `edad_aprox` = 0
  WHERE `nombre` = 'Nala' AND `especie` = 'Gato' AND `edad_aprox` = 6
    AND `estado` = 'en_adopcion';
