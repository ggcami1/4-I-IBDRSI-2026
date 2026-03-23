DESC detalle_horarios;
DESC horarios;
DESC plantilla_detalle_horarios;

SELECT horario_id, hora_salida, hora_entrada, codigo_incapacidad
FROM defaultdb.detalle_horarios;

SELECT horario_id, plantilla_id
FROM defaultdb.horarios;

SELECT plantilla_id, dia, codigo_incapacidad, turno
FROM defaultdb.plantilla_detalle_horarios;

INSERT INTO defaultdb.detalle_horarios
(horario_id, hora_salida, hora_entrada, codigo_incapacidad)
VALUES(0, '2026-02-18 09:00:00', '2026-02-18 17:00:00', '0');

CREATE TABLE usuarios (
  id int NOT NULL,
  nombres varchar(25) NOT NULL,
  apellidos varchar(25) DEFAULT NULL,
  departamento varchar(25) DEFAULT NULL,
  PRIMARY KEY (id, nombres)
);
 

SELECT id, nombres, apellidos, departamento
FROM defaultdb.usuarios;

INSERT INTO defaultdb.usuarios
(id, nombres, apellidos, departamento)
VALUES
(1, 'Camila', 'Gonzalez Ortega', 'Mantenimiento'),
(2, 'Emmanuel', 'Parra Almado', 'Informatica'),
(3, 'Jonathan', 'Mrtinez Segura', 'Limpieza'),
(4, 'Christian Fernando', 'Quiriz LOpez', 'Mantenimiento'),
(5, 'Juan Antonio', 'Ortega Sandoval', 'Infromatica'),
(6, 'Angel Gadiel', 'Mejia Lopez', 'Secretaria'),
(7, 'Lizbeth Estefania', 'Sanchez Ortiz', 'Diseño'),
(8, 'Joel Alejandro', 'Sandoval Camacho', 'Mantenimiento'),
(9, 'Yamile Isabela', 'Montaño Hernandez', 'Secretaria'),
(10, 'Carlos Eduardo', 'Bayardo Fregoso', 'Informatica');