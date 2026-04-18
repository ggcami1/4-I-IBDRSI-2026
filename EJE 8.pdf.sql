

-- EJERCICIO 1: Ventas


CREATE TABLE ventas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    Año INT,
    Cantidad INT
);

INSERT INTO ventas (Año, Cantidad) VALUES
(2025,352645),
(2024,165565),
(2024,254654),
(2023,159521),
(2023,251696),
(2023,111894);

SELECT 
    SUM(CASE WHEN Año = 2025 THEN Cantidad END) AS '2025',
    SUM(CASE WHEN Año = 2024 THEN Cantidad END) AS '2024',
    SUM(CASE WHEN Año = 2023 THEN Cantidad END) AS '2023'
FROM ventas;



-- EJERCICIO 2: Duplicados


CREATE TABLE muestra (
    id INT AUTO_INCREMENT PRIMARY KEY,
    valor INT
);

INSERT INTO muestra (valor) VALUES
(1),(1),(2),(3),(3),(4);

SELECT DISTINCT valor
FROM muestra;



-- EJERCICIO 3: Llenar huecos


CREATE TABLE datos (
    Fila INT PRIMARY KEY,
    Aplicacion VARCHAR(20),
    Estado VARCHAR(20)
);

INSERT INTO datos VALUES
(1,'Web','Aprobado'),
(2,NULL,'Fallo'),
(3,NULL,'Fallo'),
(4,NULL,'Fallo'),
(5,'App','Aprobado'),
(6,NULL,'Fallo'),
(7,NULL,'Fallo'),
(8,NULL,'Aprobado'),
(9,NULL,'Aprobado'),
(10,'RESTAPI','Fallo'),
(11,NULL,'Fallo'),
(12,NULL,'Fallo');

-- Consulta para MySQL 8+
SELECT 
    Fila,
    COALESCE(
        Aplicacion,
        MAX(Aplicacion) OVER (
            ORDER BY Fila 
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        )
    ) AS Aplicacion,
    Estado
FROM datos;