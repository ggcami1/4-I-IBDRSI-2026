

CREATE TABLE jugadores (
    Id_jugador INT PRIMARY KEY,
    Marcador INT
);

INSERT INTO jugadores VALUES
(1001,2343),
(2002,9432),
(3003,6548),
(4004,1054),
(5005,6832);

SELECT 
    CASE 
        WHEN NTILE(2) OVER (ORDER BY Marcador DESC) = 1 THEN 1
        ELSE 2
    END AS Categoria,
    Id_jugador,
    Marcador
FROM jugadores
ORDER BY Categoria, Marcador DESC;


-- =========================================
-- EJERCICIO 2 – Paginación
-- =========================================



CREATE TABLE ordenes (
    Id_orden INT PRIMARY KEY,
    Id_cliente INT,
    Fecha DATE,
    Cantidad INT,
    Estado VARCHAR(10)
);

INSERT INTO ordenes VALUES
(1,1001,'2025-01-01',100,'JAL'),
(2,3003,'2025-01-01',100,'COL'),
(3,1001,'2025-01-03',100,'JAL'),
(4,2002,'2025-01-02',150,'JAL'),
(5,1001,'2025-01-02',100,'JAL'),
(6,4004,'2025-01-05',50,'COL'),
(7,1001,'2025-01-01',150,'JAL'),
(8,3003,'2025-01-03',100,'COL'),
(9,4004,'2025-01-04',100,'COL'),
(10,1001,'2025-01-01',75,'JAL'),
(11,2002,'2025-01-02',75,'JAL'),
(12,3003,'2025-01-02',100,'COL'),
(13,4004,'2025-01-05',100,'COL');

SELECT *
FROM ordenes
ORDER BY Id_orden
LIMIT 5 OFFSET 4;


-- =========================================
-- EJERCICIO 3 – Proveedores principales
-- =========================================



CREATE TABLE pedidos (
    Id_orden INT PRIMARY KEY,
    Id_cliente INT,
    Cantidad INT,
    Proveedor VARCHAR(50)
);

INSERT INTO pedidos VALUES
(1,1001,12,'IBM'),
(2,1001,54,'IBM'),
(3,1001,32,'Amazon'),
(4,2002,7,'Amazon'),
(5,2002,16,'Amazon'),
(6,2002,5,'IBM');

SELECT Id_cliente, Proveedor
FROM (
    SELECT 
        Id_cliente,
        Proveedor,
        COUNT(*) AS total_pedidos,
        ROW_NUMBER() OVER (PARTITION BY Id_cliente ORDER BY COUNT(*) DESC) AS rn
    FROM pedidos
    GROUP BY Id_cliente, Proveedor
) t
WHERE rn = 1;