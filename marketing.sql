CREATE TABLE precios(
id int NOT NULL auto_increment primary key,
Id_producto int,
Fecha date,
Precio decimal(4,2)
);
DROP table precios;
insert INTO precios(Id_producto, Fecha, Precio)
values
(1001, '2025-01-01', 19.99),
(1001, '2025-04-15', 59.99),
(1001, '2025-06-08', 79.99),
(2002, '2025-04-17', 39.99),
(2002, '2025-05-19', 59.99);

SELECT Id_producto, Fecha, Precio
FROM (
    SELECT 
        Id_producto,
        Fecha,
        Precio,
        ROW_NUMBER() OVER (PARTITION BY Id_producto ORDER BY Fecha DESC) AS rn
    FROM precios
) AS t
WHERE rn = 1;


CREATE TABLE VENTAS (
    Id_orden INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    Id_cliente INT,
    Fecha DATE,
    Total DECIMAL(10,2),
    Estado VARCHAR(50)
);

INSERT INTO VENTAS (Id_orden, Id_cliente, Fecha, Total, Estado)
VALUES
(1, 1001, '2025-01-01', 100, 'JAL'),
(2, 1001, '2025-01-01', 150, 'JAL'),
(3, 1001, '2025-01-01', 75, 'JAL'),
(4, 1001, '2025-02-01', 100, 'JAL'),
(5, 1001, '2025-03-01', 100, 'JAL'),
(6, 2002, '2025-02-01', 75, 'JAL'),
(7, 2002, '2025-02-01', 150, 'JAL'),
(8, 3003, '2025-01-01', 100, 'CDMX'),
(9, 3003, '2025-02-01', 100, 'CDMX'),
(10, 3003, '2025-03-01', 100, 'CDMX'),
(11, 4004, '2025-04-01', 100, 'CDMX'),
(12, 4004, '2025-05-01', 50, 'CDMX'),
(13, 4004, '2025-05-01', 100, 'CDMX');

SELECT Estado
FROM (
    -- Calcula el promedio mensual por cliente
    SELECT 
        Id_cliente,
        Estado,
        YEAR(Fecha) AS anio,
        MONTH(Fecha) AS mes,
        AVG(Total) AS promedio_mensual
    FROM VENTAS
    GROUP BY Id_cliente, Estado, YEAR(Fecha), MONTH(Fecha)
) AS promedios
GROUP BY Estado
HAVING MIN(promedio_mensual) > 99;

CREATE TABLE ocurrencias1 (
    Proceso VARCHAR(50),
    Mensaje VARCHAR(100),
    Ocurrencia INT,
    PRIMARY KEY (Proceso, Mensaje)
);

INSERT INTO ocurrencias1 (Proceso, Mensaje, Ocurrencia) VALUES
('Web', 'Error: No se puede dividir por 0', 3),
('RestAPI', 'Error: Fallo la conversión', 5),
('App', 'Error: Fallo la conversión', 7),
('RestAPI', 'Error: Error sin identificar', 9),
('Web', 'Error: Error sin identificar', 1),
('App', 'Error: Error sin identificar', 10),
('Web', 'Estado Completado', 8),
('RestAPI', 'Estado Completado', 6);

SELECT Proceso, Mensaje, Ocurrencia
FROM   ocurrencias1 as el
where  Ocurrencia > all( SELECT    e2.Ocurrencia
                          FROM    ocurrencias1 as e2
                          WHERE   e2.Mensaje = el.Mensaje AND
                                  e2.Proceso <> el.Proceso
);