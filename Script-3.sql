CREATE TABLE defaultdb.a (
	id INT auto_increment NOT NULL,
	pilotos varchar(100) NOT NULL,
	CONSTRAINT a_pk PRIMARY KEY (id)
)
ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE defaultdb.b (
	id INT auto_increment NOT NULL,
	pilotos varchar(100) NOT NULL,
	CONSTRAINT b_pk PRIMARY KEY (id)
)
ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_0900_ai_ci;

INSERT INTO defaultdb.a
(id, pilotos)
VALUES 
(1, 'S. Perez'),
(2, 'M. Botas'),
(3, 'M. Verstappen'),
(4, 'I. Hadjar'),
(5, 'C. Leclerk'),
(6, 'L. Hamilton'),
(7, 'L. Norris');

INSERT INTO defaultdb.b
(id, pilotos)
VALUES 
(1, 'G. Russell'),
(2, 'K. Antonelli'),
(3, 'S. Perez'),
(4, 'F. Alonso'),
(5, 'M. Verstappen'),
(6, 'L. Lawson'),
(7, 'L. Hamilton'); 


SELECT *
FROM a
INNER JOIN b
ON a.pilotos  = b.pilotos ;


SELECT *
FROM a
LEFT OUTER JOIN b
ON a.pilotos = b.pilotos 
UNION ALL
SELECT *
FROM a
RIGHT OUTER JOIN b
ON a.pilotos = b.pilotos ;


SELECT *
FROM a
LEFT OUTER JOIN b
ON a.pilotos = b.pilotos ;


SELECT *
FROM a
RIGHT OUTER JOIN b
ON a.pilotos = b.pilotos 

SELECT *
FROM a
LEFT JOIN b
 ON a.pilotos  = b.pilotos 
WHERE b.pilotos  IS NULL
UNION ALL 
SELECT *
FROM a 
RIGHT JOIN b 
 ON a.pilotos = b.pilotos 
WHERE a.pilotos  IS NULL

SELECT *
FROM a
LEFT JOIN b
 ON a.pilotos  = b.pilotos 
WHERE b.pilotos  IS NULL

SELECT *
FROM a 
RIGHT JOIN b 
 ON a.pilotos = b.pilotos 
WHERE a.pilotos  IS NULL

