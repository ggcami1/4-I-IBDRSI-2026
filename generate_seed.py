#!/usr/bin/env python3
"""Regenerate seed data section of flaskr/schema.sql.

Produces:
  - 10 periodos  (2017-2026)
  - 18 classes   (3 per semester, semesters 1-6)
  - 912 students (4 per group × 4 groups × 6 sems × 9 years, plus 2026 sems 2/4/6)
  - 2736 grade records (3 per student)
Preserves original 2026 student names and grades.
"""
import os
import random
import unicodedata

random.seed(42)


def norm(text):
    """Strip accents and lowercase — used for email generation."""
    nfkd = unicodedata.normalize('NFKD', text)
    return ''.join(c for c in nfkd if not unicodedata.combining(c)).lower()


def esc(text):
    return text.replace("'", "''")


# ── Name pools ────────────────────────────────────────────────────────────────

MALE = [
    'Miguel','Carlos','Eduardo','Ricardo','Alejandro','Diego','José','Juan',
    'Héctor','Roberto','Sergio','Andrés','Raúl','Javier','Guillermo','Mario',
    'Omar','Arturo','Ernesto','Iván','Enrique','Ramón','Salvador','Gerardo',
    'Luis','Fernando','Antonio','Marcos','Pedro','Rodrigo','Adrián','Francisco',
    'Gabriel','Emilio','Óscar','Víctor','Daniel','Pablo','Alfredo','Rubén',
    'Hugo','Jaime','Ignacio','Manuel','Rafael','Tomás','Armando','Joaquín',
]

FEMALE = [
    'Ana','María','Sofía','Alejandra','Gabriela','Natalia','Patricia','Verónica',
    'Adriana','Carmen','Paola','Leticia','Claudia','Irene','Lucía','Valentina',
    'Isabella','Camila','Mónica','Perla','Diana','Araceli','Laura','Mariana',
    'Elizabeth','Sandra','Gloria','Fernanda','Andrea','Daniela','Karla','Rocío',
    'Norma','Silvia','Angélica','Rosa','Liliana','Alicia','Beatriz','Elena',
    'Rebeca','Alma','Cecilia','Susana','Nadia','Lorena','Ximena','Miriam',
]

LAST = [
    'García','Martínez','López','González','Hernández','Pérez','Sánchez','Ramírez',
    'Torres','Flores','Reyes','Cruz','Morales','Gutiérrez','Ortiz','Vargas',
    'Castillo','Mendoza','Ramos','Aguilar','Jiménez','Álvarez','Romero','Navarro',
    'Silva','Ruiz','Guerrero','Méndez','Suárez','Castro','Ortega','Delgado',
    'Vega','Soto','Campos','Espinoza','Luna','Mora','Peña','Ríos',
    'Serrano','Núñez','Ibarra','Montes','Carrillo','Domínguez','Medina','Herrera',
    'Chávez','Rojas','Rivera','Muñoz','Contreras','Ávila','Fuentes','Acosta',
    'Lara','Miranda','Bravo','Cortez','Gallegos','Salinas','Velázquez','Blanco',
    'Aguirre','Ponce','Valdez','Cabrera','Cervantes','Sandoval','Vázquez','Robles',
]

# ── Classes ───────────────────────────────────────────────────────────────────
# IDs assigned sequentially: 1-3 sem1, 4-6 sem2, 7-9 sem3, 10-12 sem4,
#                            13-15 sem5, 16-18 sem6

CLASS_DEFS = [
    # Semester 1 – new
    ('Fundamentos de Programación',           1),
    ('Matemáticas Discretas',                 1),
    ('Introducción a Sistemas Computacionales',1),
    # Semester 2 – existing
    ('Introducción a la Programación',         2),
    ('Algoritmos y Estructuras de Datos',      2),
    ('Programación Orientada a Objetos',       2),
    # Semester 3 – new
    ('Estructuras de Datos Avanzadas',         3),
    ('Paradigmas de Programación',             3),
    ('Sistemas Digitales',                     3),
    # Semester 4 – existing
    ('Bases de Datos',                         4),
    ('Desarrollo Web',                         4),
    ('Redes y Comunicaciones',                 4),
    # Semester 5 – new
    ('Compiladores',                           5),
    ('Seguridad Informática',                  5),
    ('Arquitectura de Computadoras',           5),
    # Semester 6 – existing
    ('Sistemas Operativos',                    6),
    ('Inteligencia Artificial',                6),
    ('Desarrollo de Aplicaciones Móviles',     6),
]

CLASSES_BY_SEM = {
    1: [1,  2,  3 ],
    2: [4,  5,  6 ],
    3: [7,  8,  9 ],
    4: [10, 11, 12],
    5: [13, 14, 15],
    6: [16, 17, 18],
}

# ── Preserved 2026 students ───────────────────────────────────────────────────
# Grade keys use NEW class IDs (old→new: 1→4,2→5,5→6 / 3→10,4→11,6→12 / 7→16,8→17,9→18)

FIXED_2026 = {
    (2,1): [('Miguel','García',    {4:8, 5:9, 6:7}),  ('Ana','Martínez',     {4:9, 5:7, 6:10}),
            ('Carlos','López',     {4:7, 5:8, 6:6}),  ('María','González',   {4:10,5:6, 6:8}) ],
    (2,2): [('José','Hernández',   {4:6, 5:9, 6:8}),  ('Laura','Pérez',      {4:8, 5:5, 6:9}),
            ('Juan','Sánchez',     {4:5, 5:8, 6:7}),  ('Sofía','Ramírez',    {4:9, 5:10,6:6}) ],
    (2,3): [('Eduardo','Reyes',    {4:9, 5:7, 6:8}),  ('Mariana','Cruz',     {4:7, 5:10,6:9}),
            ('Ricardo','Morales',  {4:5, 5:8, 6:6}),  ('Alejandra','Gutiérrez',{4:10,5:6,6:7})],
    (2,4): [('Alejandro','Ortiz',  {4:6, 5:8, 6:9}),  ('Gabriela','Vargas',  {4:8, 5:9, 6:7}),
            ('Diego','Castillo',   {4:9, 5:7, 6:5}),  ('Natalia','Mendoza',  {4:7, 5:5, 6:10})],
    (4,1): [('Héctor','Ramos',     {10:8, 11:10,12:7}),('Patricia','Aguilar', {10:10,11:7, 12:9}),
            ('Roberto','Jiménez',  {10:7, 11:9, 12:8}),('Verónica','Álvarez', {10:9, 11:8, 12:6})],
    (4,2): [('Sergio','Romero',    {10:5, 11:8, 12:9}),('Adriana','Navarro',  {10:8, 11:6, 12:10}),
            ('Andrés','Torres',    {10:6, 11:9, 12:7}),('Carmen','Silva',      {10:10,11:7, 12:8})],
    (4,3): [('Raúl','Ruiz',        {10:10,11:6, 12:9}),('Paola','Guerrero',   {10:6, 11:9, 12:7}),
            ('Javier','Méndez',    {10:9, 11:7, 12:5}),('Leticia','Suárez',   {10:7, 11:5, 12:10})],
    (4,4): [('Guillermo','Castro', {10:5, 11:8, 12:10}),('Claudia','Ortega',  {10:8, 11:10,12:6}),
            ('Mario','Delgado',    {10:10,11:6, 12:8}),('Irene','Vega',        {10:6, 11:8, 12:9})],
    (6,1): [('Omar','Soto',        {16:9, 17:7, 18:8}),('Lucía','Campos',     {16:7, 17:10,18:9}),
            ('Arturo','Espinoza',  {16:8, 17:9, 18:6}),('Valentina','Reyes',  {16:10,17:6, 18:7})],
    (6,2): [('Ernesto','Luna',     {16:5, 17:9, 18:8}),('Isabella','Mora',    {16:9, 17:7, 18:6}),
            ('Iván','Peña',        {16:7, 17:8, 18:10}),('Camila','Ríos',     {16:8, 17:5, 18:9})],
    (6,3): [('Enrique','Delgado',  {16:8, 17:7, 18:9}),('Mónica','Serrano',   {16:7, 17:9, 18:8}),
            ('Ramón','Guerrero',   {16:6, 17:8, 18:7}),('Perla','Núñez',      {16:10,17:6, 18:5})],
    (6,4): [('Salvador','Ibarra',  {16:9, 17:5, 18:8}),('Diana','Montes',     {16:5, 17:8, 18:10}),
            ('Gerardo','Carrillo', {16:8, 17:10,18:7}),('Araceli','Domínguez',{16:7, 17:9, 18:6})],
}


def rand_students(sem):
    result = []
    for i in range(4):
        name = random.choice(MALE if i % 2 == 0 else FEMALE)
        grades = {c: random.randint(5, 10) for c in CLASSES_BY_SEM[sem]}
        result.append((name, random.choice(LAST), grades))
    return result


# ── Build SQL ─────────────────────────────────────────────────────────────────

YEARS = list(range(2017, 2027))
parts = []

# periodos
rows = [f"    ('Periodo {y}', {y})" for y in YEARS]
parts.append("INSERT INTO periodo (name, year) VALUES\n" + ',\n'.join(rows) + ";\n")

# groups
parts.append("INSERT INTO \"group\" (name) VALUES\n    ('a'), ('b'), ('i'), ('j');\n")

# swifts
parts.append("INSERT INTO swift (name, hora_inicio, hora_fin) VALUES\n"
             "    ('MATUTINO',   '07:00', '13:00'),\n"
             "    ('VESPERTINO', '14:00', '20:00');\n")

# swift_group  a,b → MATUTINO(1)  i,j → VESPERTINO(2)
parts.append("INSERT INTO swift_group (swift_id, group_id) VALUES\n"
             "    (1, 1),\n    (1, 2),\n    (2, 3),\n    (2, 4);\n")

# classes
rows = [f"    ('{esc(name)}', {sem})" for name, sem in CLASS_DEFS]
parts.append("INSERT INTO class (name, semester) VALUES\n" + ',\n'.join(rows) + ";\n")

# students + grades
student_rows, grade_rows = [], []
sid = 1

for yi, year in enumerate(YEARS):
    pid = yi + 1                                  # periodo_id
    sems = [2, 4, 6] if year == 2026 else range(1, 7)
    for sem in sems:
        for gid in [1, 2, 3, 4]:
            students = FIXED_2026.get((sem, gid)) if year == 2026 else rand_students(sem)
            for name, lastname, grades in students:
                email = f"{norm(name)}.{norm(lastname)}"
                student_rows.append(
                    f"    ('{esc(name)}', '{esc(lastname)}', '{email}', {sem}, {gid}, {pid})"
                )
                for cid in sorted(grades):
                    grade_rows.append(f"    ({sid}, {gid}, {cid}, {grades[cid]})")
                sid += 1

parts.append("INSERT INTO student (name, lastname, email, semester, group_id, periodo_id) VALUES\n"
             + ',\n'.join(student_rows) + ";\n")
parts.append("INSERT INTO student_group_class (student_id, group_id, class_id, grade) VALUES\n"
             + ',\n'.join(grade_rows) + ";\n")

seed_sql = '\n'.join(parts)

# ── Patch schema.sql ──────────────────────────────────────────────────────────

schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flaskr', 'schema.sql')
with open(schema_path, 'r', encoding='utf-8') as f:
    content = f.read()

insert_pos = content.find('\nINSERT INTO')
content = (content[:insert_pos] if insert_pos != -1 else content.rstrip()) + '\n\n' + seed_sql

with open(schema_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"✓ {sid - 1} students  |  {len(grade_rows)} grade records  →  flaskr/schema.sql")
