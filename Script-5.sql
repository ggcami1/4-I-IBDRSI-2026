/* 
Implementacion de una base de datos en un sistema de informacion
2026/03/04 4-I
Camila Gonzalez Ortega
Nombre de la practica 
*/

-- Crear tabla departamentos
CREATE TABLE departamentos (
  id INT NOT NULL,
  name VARCHAR(25) NOT NULL,
  location DATE NOT NULL,
  PRIMARY KEY (id, name)
);

-- Crear tabla empleados
CREATE TABLE empleados (
  id INT PRIMARY KEY,
  nombre VARCHAR(50),
  edad INT,
  salario DECIMAL(10,2)
);

-- Insertar 5 registros en empleados
INSERT INTO empleados (id, nombre, edad, salario) VALUES
(1, 'Camila Gonzalez', 25, 8000.50),
(2, 'Emmanuel Parra', 30, 9500.75),
(3, 'Estefania Sanchez', 28, 8700.00),
(4, 'Jonathan Martinez', 35, 12000.25),
(5, 'Angel Mejia', 22, 7000.00);

-- Agregar columna departamento
ALTER TABLE empleados
ADD departamento VARCHAR(50);

-- Cambiar tipo de dato de salario a INTEGER
ALTER TABLE empleados
ALTER COLUMN salario  INT;

-- Eliminar columna departamento
ALTER TABLE empleados
DROP COLUMN departamentos;

-- Eliminar tabla departamentos permanentemente
DROP TABLE departamentos;

-- Eliminar todos los registros de empleados pero mantener la tabla
TRUNCATE TABLE empleados;

-- Renombrar tabla empleados a staff
ALTER TABLE empleados
RENAME TO staff;

-- Definir 0 como valor predeterminado en la columna salario
ALTER TABLE staff
ALTER COLUMN salario SET DEFAULT 0;

-- Crear nuevo esquema llamado rh_db
CREATE SCHEMA rh_db;

-- Mover tabla staff al esquema rh_db
ALTER TABLE staff
SET SCHEMA rh_db;