CREATE TABLE `jona`.`persona`(
id int NOT NULL PRIMARY KEY,
Customer_ID int,
Type_Phone varchar(25),
Phone_Number varchar(20)
);

INSERT into jona.persona
(id, Customer_ID, Type_Phone, Phone_Number)
VALUES
(1, 1001, 'Celular', '333-897-5421'),
(2, 1001, 'Trabajo', '333-897-6542'),
(3, 1001, 'Casa', '333-698-9874'),
(4, 2002, 'Celular', '333-963-6544'),
(5, 2002, 'Trabajo', '333-812-9856'),
(6, 3003, 'Celular', '333-987-6541');

SELECT 
    Customer_ID,
    MAX(CASE WHEN Type_Phone = 'Celular' THEN Phone_Number END) AS Celular,
    MAX(CASE WHEN Type_Phone = 'Trabajo' THEN Phone_Number END) AS Trabajo,
    MAX(CASE WHEN Type_Phone = 'Casa' THEN Phone_Number END) AS Casa
FROM persona
GROUP BY Customer_ID;

create table Desarrollos(
id int not null primary key,
Desarrollo varchar(25),
Etapa int,
Finalizado date NULL
);

insert INTO Desarrollos(id, Desarrollo, Etapa, Finalizado)
values 
(1, 'RestAPI', 1, '2024/02/01'),
(2, 'RestAPI', 2, '2024/05/30'),
(3, 'RestAPI', 3, '2024/06/29'),
(4, 'Web', 1, '2024/10/28'),
(5, 'Web', 2, '2024/11/20'),
(6, 'Web', 3, null),
(7, 'App', 1, '2024/01/30'),
(8, 'App', 2, null);

select DISTINCT *
FROM Desarrollos
WHERE Finalizado is NULL 

create TABLE Requisitos(
id int not null primary key,
Decripcion varchar(25)
);

insert into Requisitos(id, Decripcion)
values
(1, 'geologo'),
(2, 'astronomo'),
(3, 'tecnico');

create TABLE candidatos(
id int not null primary key,
ID_candidato int,
descripcion varchar(25)
);

insert into candidatos (id, ID_candidato, descripcion)
VALUES 
(1, 1001, 'Geólogo'),
(2, 1001, 'Astrónomo'),
(3, 1001, 'Bioquímico'),
(4, 1001, 'Técnico'),
(5, 2002, 'Cirujano'),
(6, 2002, 'Mecánico'),
(7, 2002, 'Geólogo'),
(8, 3003, 'Geólogo'),
(9, 3003, 'Astrónomo'),
(10, 4004, 'Ingeniero');

SELECT c.ID_candidato
FROM candidatos c
JOIN Requisitos r ON c.descripcion = r.decripcion
GROUP BY c.ID_candidato
HAVING COUNT(DISTINCT c.descripcion) = (SELECT COUNT(*) FROM Requisitos);