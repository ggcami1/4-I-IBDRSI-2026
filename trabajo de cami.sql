CREATE TABLE LETRAS(
id int NOT NULL auto_increment PRIMARY KEY,
caso varchar (1)
);

INSERT INTO LETRAS(caso)
VALUES
('A'),
('B'),
('C');

SELECT t1.caso, t2.caso, t3.caso
FROM LETRAS t1
JOIN LETRAS t2 ON t1.caso <> t2.caso
JOIN LETRAS t3 
  ON t1.caso <> t3.caso
 AND t2.caso <> t3.caso
ORDER BY t1.caso, t2.caso, t3.caso;

CREATE TABLE DESARROLLOS(
id int NOT null auto_increment primary key,
Desarrollo varchar(25),
Terminacion DATE 
);

INSERT INTO DESARROLLOS (Desarrollo, Terminacion)
VALUES
('RestAPI', '2024-06-01'),
('RestAPI', '2024-06-14'),
('RestAPI', '2024-06-15'),
('Web', '2024-06-01'),
('Web', '2024-06-02'),
('Web', '2025-06-19'),
('App', '2024-06-01'),
('App', '2024-05-15'),
('App', '2024-06-30');

SELECT 
    Desarrollo,
    AVG(DAY(Terminacion)) AS Promedio
FROM 
    DESARROLLOS
GROUP BY 
    Desarrollo;

create table ALMACEN(
id int not null auto_increment primary key,
fecha DATE,
ajuste INT
);

insert INTO ALMACEN(fecha, ajuste)
values
('2025-03-01', 100),
('2025-04-01', 75),
('2025-05-01', -150),
('2025-06-01', 50),
('2025-07-01', -70);

SELECT
    DATE_FORMAT(fecha, '%m/%d/%Y') AS Fecha,
    ajuste AS Ajuste,
    SUM(ajuste) OVER (ORDER BY fecha) AS Inventario
FROM
    ALMACEN
ORDER BY
    fecha;