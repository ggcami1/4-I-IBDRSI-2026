create table compras(
id int not null auto_increment primary key,
productos varchar(50)
);

create table compras2(
id int not null auto_increment primary key,
productos varchar(50)
);

drop table compras2;
insert into compras
(productos)
values
('Azucar'),
('Pan'),
('Jugo'),
('Refresco'), 
('Harina');

insert into 
compras2(productos)
values
('Azucar'),
('Pan'),
('mantequilla'),
('queso'),
('manzana');
 
    

  select *
  from compras
  left join compras2 on compras.productos = compras2.productos
  
  union
  
  select *
  from compras
  right join compras2 on compras.productos = compras2.productos
  where compras.productos is null;
  
 /*pero no para mi*/
 
 create table empleados(
 id int not null auto_increment primary key,
 Id_empleado int,
 Id_gerente int,
 Puesto varchar(50)
 );
 
 insert into chambiadores
 (Id_empleado, Id_gerente, Puesto)
 values
 (1001, 0, 'Presidente'),
 (2002, 1001, 'Director'),
 (3003, 1001, 'Gerente'),
 (4004, 2002, 'Ingeniero'),
 (5005, 2002, 'Contador'),
 (6006, 2002, 'Administrador');
 
 alter table chambiadores
 add nivel int;

UPDATE chambiadores SET nivel = 0 WHERE id = 1;

UPDATE chambiadores SET nivel = 1 WHERE id IN (2,3);

UPDATE chambiadores SET nivel = 2 WHERE id IN (4,5,6);

select *
from chambiadores

create table entregas(
id int not null auto_increment primary key,
Id_cliente int,
 Id_Orden int not null, 
 Estado_Destino varchar(50),
 Costo int);
 
 insert into entrega
 (Id_cliente, Id_Orden, Estado_Destino, Costo)
 values
 (1001, 1, 'JAL', 987),
(1001, 2, 'CDMX', 400),
(1001, 3, 'CDMX', 545),
(1001, 4, 'CDMX', 321),
(2002, 5, 'MTY', 324),
(3003, 6, 'JAL', 931),
(4004, 7, 'JAL', 876),
(5005, 8, 'CDMX', 567);

SELECT *
from entrega;

SELECT 
Id_cliente,
Id_Orden,
Estado_Destino,
CONCAT('$', Costo) AS Costo
FROM entrega
WHERE Estado_Destino = 'CDMX'
AND Id_cliente IN (
    SELECT Id_cliente
    FROM entrega
    WHERE Estado_Destino = 'JAL'
);