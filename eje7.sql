create table cbtis.DATOS(
id int not null auto_increment primary key,
producto varchar(25),
cantidad int
);

insert into cbtis.DATOS(producto, cantidad)
values 
('Lápiz', 3),
('Borrador', 4),
('Cuaderno', 2);

with recursive numeros as (
	select 1 as n
    union all
    select n + 1
    from numeros
    where n < 10
)
select t.producto, 1 as cantidad
from cbtis.DATOS t
join numeros n on n.n <= t.cantidad;

CREATE TABLE cbtis.asientos(
num_asiento INTEGER primary key
);

INSERT INTO cbtis.asientos VALUES 
(7),
(13),
(14),
(15),
(27),
(28),
(29),
(30),
(31),
(32),
(33),
(34),
(35),
(52),
(53),
(54);
use cbtis;
WITH ordenados AS (
    SELECT num_asiento,
           LAG(num_asiento) OVER (ORDER BY num_asiento) AS anterior
    FROM asientos
)
SELECT 
    COALESCE(anterior + 1, 1) AS espacio_inicio,
    num_asiento - 1 AS espacio_final
FROM ordenados
WHERE num_asiento - COALESCE(anterior, 0) > 1;

SELECT 
    (MAX(num_asiento) - MIN(num_asiento) + 1) - COUNT(*) AS disponibles
FROM asientos;

SELECT 
    CASE 
        WHEN num_asiento % 2 = 0 THEN 'pares'
        ELSE 'impares'
    END AS tipo,
    COUNT(*) AS total
FROM asientos
GROUP BY tipo;

create table periodos(
id int not null auto_increment primary key,
inicio date,
final date
);

insert into periodos(inicio, final)
values 
('2025-01-01', '2025-01-05'),
('2025-01-03', '2025-01-09'),
('2025-01-10', '2025-01-11'),
('2025-01-12', '2025-01-16'),
('2025-01-15', '2025-01-19');

with ordenados as (
	select
		inicio,
        final,
        lag(final) over (order by inicio) as fin_anterior
	from periodos
),
grupos as (
	select *,
		case
			when inicio <= fin_anterior then 0
            else 1
		end as nuevo_grupo
	from ordenados
),
acumulado as (
	select *,
		sum(nuevo_grupo) over(order by inicio) as grupo
	from grupos
)
select
	min(inicio) as inicio,
    max(final) as final
from acumulado
group by grupo
order by inicio;