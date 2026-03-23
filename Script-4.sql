/* 
Implementacion de una base de datos en un sistema de informacion
2025/03/04 4-I
Camila Gonzalez Ortega
Nombre de la practica
*/

create database cami;
USE cami;

CREATE TABLE `cami`.`BOOKS` (
	`ID` INT not null auto_increment PRIMARY KEY ,
	NAME VARCHAR(50) NOT NULL,
	PRICE INT,
	CATEGORYID INT,
	AUTHORID INT
);

DROP TABLE cami.BOOKS;

CREATE TABLE `cami`.`CATEGORIES` (
ID INT NOT NULL auto_increment PRIMARY KEY,
 NAME VARCHAR(50) NOT NULL,
 CATEGORYid varchar(50)
 );

DROP TABLE cami.CATEGORIES;

CREATE TABLE `cami`.`AUTHORS` (
ID INT not null auto_increment PRIMARY KEY,
 NAME VARCHAR(50) NOT NULL,
 AUTHORSid varchar(50)
 );
 
 DROP TABLE cami.AUTHORS;

INSERT INTO
	`cami`.`CATEGORIES`(CATEGORYID,NAME)
VALUES
	(1, 'Cat-A'),
	(2, 'Cat-B'),
	(3, 'Cat-C'),
	(7, 'Cat-D'),
	(8, 'Cat-E'),
	(4, 'Cat-F'),
	(10, 'Cat-G'),
	(12, 'Cat-H'),
	(6, 'Cat-I');


INSERT INTO
	AUTHORS(AUTHORSID,NAME)
VALUES
	(1, 'Author-A'),
	(2, 'Author-B'),
	(3, 'Author-C'),
	(10, 'Author-D'),
	(12, 'Author-E');


INSERT INTO
	BOOKS(NAME,PRICE,CATEGORYID,AUTHORID)
VALUES
	('Book-A', 100, 1, 2),
	('Book-B', 200, 2, 2),
	('Book-C', 150, 3, 2),
	('Book-D', 100, 3, 1),
	('Book-E', 200, 3, 1),
	('Book-F', 150, 4, 1),
	('Book-G', 100, 5, 5),
	('Book-H', 200, 5, 6),
	('Book-I', 150, 7, 8);
	

/** Encontrar los fallos en el script, hacer las correcciones, realizar las siguientes operaciones y guardar las consultas**/
 /**--INNER JOIN
 --LEFT OUTER JOIN
 --RIGHT OUTER JOIN
 --JOIN NATURAL
 --LEFT EXCLUDING JOIN
 --LEFT EXCLUDING JOIN**/
 
   select *
  from AUTHORS, BOOKS, CATEGORIES;
  
 SELECT *
FROM BOOKS b
INNER JOIN AUTHORS a ON b.AUTHORID = a.ID
INNER JOIN CATEGORIES c ON b.CATEGORYID = c.ID;
  
SELECT *
FROM BOOKS b
LEFT JOIN AUTHORS a ON b.AUTHORID = a.ID
LEFT JOIN CATEGORIES c ON b.CATEGORYID = c.ID;

SELECT *
FROM BOOKS b
RIGHT JOIN AUTHORS a ON b.AUTHORID = a.ID;
  
  SELECT *
FROM BOOKS
NATURAL JOIN AUTHORS;

SELECT *
FROM BOOKS b
LEFT JOIN AUTHORS a ON b.AUTHORID = a.ID
WHERE a.ID IS NULL;

SELECT *
FROM BOOKS b
RIGHT JOIN AUTHORS a ON b.AUTHORID = a.ID
WHERE b.ID IS NULL;
