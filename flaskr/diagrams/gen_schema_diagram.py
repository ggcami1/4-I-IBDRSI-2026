from PIL import Image, ImageDraw, ImageFont
import math

W, H  = 1820, 1260
TW    = 240
CH    = 24
HH    = 34

C_BG      = (248, 249, 252)
C_HDR_BG  = (41,  70, 135)
C_HDR_FG  = (255, 255, 255)
C_ROW1    = (255, 255, 255)
C_ROW2    = (237, 242, 255)
C_BORDER  = (41,  70, 135)
C_PK      = (180, 100,   0)
C_FK      = (  0, 100, 180)
C_TEXT    = ( 30,  30,  50)
C_TYPE    = (130, 130, 160)
C_LINE    = (100, 130, 220)
C_SHADOW  = (200, 205, 220)
C_SEC     = (220, 230, 250)

img = Image.new('RGB', (W, H), C_BG)
d   = ImageDraw.Draw(img)

FONT_DIR = "/usr/share/fonts/truetype/dejavu/"
try:
    FB = ImageFont.truetype(FONT_DIR + "DejaVuSans-Bold.ttf", 14)
    FR = ImageFont.truetype(FONT_DIR + "DejaVuSans.ttf",      12)
    FT = ImageFont.truetype(FONT_DIR + "DejaVuSans-Bold.ttf", 24)
    FS = ImageFont.truetype(FONT_DIR + "DejaVuSans.ttf",      10)
    FL = ImageFont.truetype(FONT_DIR + "DejaVuSans-Bold.ttf", 11)
except Exception:
    FB = FR = FT = FS = FL = ImageFont.load_default()


def tbl_h(n):
    return HH + n * CH + 4


def draw_table(x, y, name, cols):
    h = tbl_h(len(cols))
    d.rectangle([x+4, y+4, x+TW+4, y+h+4], fill=C_SHADOW)
    d.rectangle([x, y, x+TW, y+HH], fill=C_HDR_BG)
    nw = d.textlength(name, font=FB)
    d.text((x + (TW - nw) // 2, y + 10), name, fill=C_HDR_FG, font=FB)
    for i, (cn, ct, pk, fk) in enumerate(cols):
        ry = y + HH + i * CH + 2
        d.rectangle([x, ry, x+TW, ry+CH], fill=C_ROW2 if i % 2 == 0 else C_ROW1)
        if pk:
            d.text((x+5, ry+6), "PK", fill=C_PK, font=FS)
            cx = x + 28
        elif fk:
            d.text((x+5, ry+6), "FK", fill=C_FK, font=FS)
            cx = x + 28
        else:
            cx = x + 10
        d.text((cx, ry+6), cn, fill=C_TEXT, font=FR)
        tw_len = d.textlength(ct, font=FR)
        d.text((x+TW-tw_len-5, ry+6), ct, fill=C_TYPE, font=FR)
        d.line([x, ry+CH, x+TW, ry+CH], fill=(210, 215, 230), width=1)
    d.rectangle([x, y, x+TW, y+h], outline=C_BORDER, width=2)


def row_y(ty, ci):
    return ty + HH + ci * CH + CH // 2 + 2


def cpt(tx, ty, ci, side):
    y = row_y(ty, ci)
    return (tx + (TW if side == 'r' else 0), y)


def arrowhead(prev, tip):
    dx, dy = tip[0]-prev[0], tip[1]-prev[1]
    ln = math.hypot(dx, dy)
    if not ln:
        return
    ux, uy = dx/ln, dy/ln
    s = 9
    d.polygon([tip,
               (int(tip[0]-s*ux+s*.4*(-uy)), int(tip[1]-s*uy+s*.4*ux)),
               (int(tip[0]-s*ux-s*.4*(-uy)), int(tip[1]-s*uy-s*.4*ux))],
              fill=C_LINE)


def line_pts(*pts):
    for i in range(len(pts)-1):
        d.line([pts[i], pts[i+1]], fill=C_LINE, width=2)
    arrowhead(pts[-2], pts[-1])


# ── Tabla de columnas ─────────────────────────────────────────────────────────

COLS = {
    'periodo': [
        ('id',   'INTEGER', True,  False),
        ('name', 'TEXT',    False, False),
        ('year', 'INTEGER', False, False),
    ],
    'user': [
        ('id',       'INTEGER', True,  False),
        ('username', 'TEXT',    False, False),
        ('nombre',   'TEXT',    False, False),
        ('apellido', 'TEXT',    False, False),
        ('email',    'TEXT',    False, False),
        ('rol',      'TEXT',    False, False),
        ('activo',   'INTEGER', False, False),
    ],
    'backup_code': [
        ('id',      'INTEGER', True,  False),
        ('user_id', 'INTEGER', False, True),
        ('code',    'TEXT',    False, False),
        ('used',    'INTEGER', False, False),
    ],
    'swift': [
        ('id',          'INTEGER', True,  False),
        ('name',        'TEXT',    False, False),
        ('hora_inicio', 'TEXT',    False, False),
        ('hora_fin',    'TEXT',    False, False),
    ],
    'swift_group': [
        ('id',       'INTEGER', True,  False),
        ('swift_id', 'INTEGER', False, True),
        ('group_id', 'INTEGER', False, True),
    ],
    'group': [
        ('id',   'INTEGER', True,  False),
        ('name', 'TEXT',    False, False),
    ],
    'class': [
        ('id',       'INTEGER', True,  False),
        ('name',     'TEXT',    False, False),
        ('semester', 'INTEGER', False, False),
    ],
    'student': [
        ('id',         'INTEGER', True,  False),
        ('name',       'TEXT',    False, False),
        ('lastname',   'TEXT',    False, False),
        ('email',      'TEXT',    False, False),
        ('semester',   'INTEGER', False, False),
        ('group_id',   'INTEGER', False, True),
        ('periodo_id', 'INTEGER', False, True),
    ],
    'planeaciones': [
        ('id',              'INTEGER', True,  False),
        ('id_grupo',        'INTEGER', False, True),
        ('id_materia',      'INTEGER', False, True),
        ('id_docente',      'INTEGER', False, True),
        ('dia_semana',      'TEXT',    False, False),
        ('hora_inicio',     'TEXT',    False, False),
        ('hora_fin',        'TEXT',    False, False),
        ('aula',            'TEXT',    False, False),
        ('periodo_escolar', 'INTEGER', False, True),
        ('observaciones',   'TEXT',    False, False),
    ],
    'student_group_class': [
        ('id',         'INTEGER', True,  False),
        ('student_id', 'INTEGER', False, True),
        ('group_id',   'INTEGER', False, True),
        ('class_id',   'INTEGER', False, True),
        ('grade',      'INTEGER', False, False),
    ],
    'login_logs': [
        ('id',      'INTEGER', True,  False),
        ('usuario', 'TEXT',    False, False),
        ('user_id', 'INTEGER', False, False),
        ('evento',  'TEXT',    False, False),
        ('ip',      'TEXT',    False, False),
        ('fecha',   'TEXT',    False, False),
    ],
    'audit_logs': [
        ('id',               'INTEGER', True,  False),
        ('tabla_afectada',   'TEXT',    False, False),
        ('registro_id',      'INTEGER', False, False),
        ('accion',           'TEXT',    False, False),
        ('datos_anteriores', 'TEXT',    False, False),
        ('datos_nuevos',     'TEXT',    False, False),
        ('usuario',          'TEXT',    False, False),
        ('fecha',            'TEXT',    False, False),
    ],
}

POS = {
    'periodo':             (40,   70),
    'user':                (1500,  70),
    'backup_code':         (1500, 350),
    'swift':               (40,  260),
    'swift_group':         (350, 260),
    'group':               (660, 260),
    'class':               (1060, 260),
    'student':             (40,  480),
    'planeaciones':        (660, 480),
    'student_group_class': (350, 790),
    'login_logs':          (40,  1010),
    'audit_logs':          (660, 1010),
}

# ── Título ────────────────────────────────────────────────────────────────────

title = "Sistema de Control Escolar — Esquema de Base de Datos"
tw_title = d.textlength(title, font=FT)
d.text(((W - tw_title) // 2, 14), title, fill=C_HDR_BG, font=FT)

# ── Secciones (fondos) ────────────────────────────────────────────────────────

def section(x1, y1, x2, y2, label):
    d.rectangle([x1, y1, x2, y2], fill=C_SEC, outline=(180, 195, 230), width=1)
    d.text((x1+8, y1+4), label, fill=(60, 80, 140), font=FL)

section(20,  55, 310, 200,  "Periodo")
section(1480, 55, 1800, 500, "Autenticación")
section(20,  245, 1440, 760, "Académico")
section(20,  995, 1440, 1210, "Auditoría")

# ── Tablas ────────────────────────────────────────────────────────────────────

for name, cols in COLS.items():
    x, y = POS[name]
    draw_table(x, y, name, cols)

# ── Relaciones (FK → PK, la punta de flecha apunta al PK) ────────────────────

px,  py  = POS['periodo']
ux,  uy  = POS['user']
bx,  by  = POS['backup_code']
swx, swy = POS['swift']
sgx, sgy = POS['swift_group']
gx,  gy  = POS['group']
clx, cly = POS['class']
stx, sty = POS['student']
plx, ply = POS['planeaciones']
scx, scy = POS['student_group_class']

# 1. backup_code.user_id → user.id (ambas tablas en x=1500; ruta por la derecha)
line_pts(
    cpt(bx, by, 1, 'r'),
    (1775, row_y(by, 1)),
    (1775, row_y(uy, 0)),
    cpt(ux, uy, 0, 'r'),
)

# 2. swift_group.swift_id → swift.id (codo izquierdo)
line_pts(
    cpt(sgx, sgy, 1, 'l'),
    (318, row_y(sgy, 1)),
    (318, row_y(swy, 0)),
    cpt(swx, swy, 0, 'r'),
)

# 3. swift_group.group_id → group.id (codo derecho corto)
line_pts(
    cpt(sgx, sgy, 2, 'r'),
    (625, row_y(sgy, 2)),
    (625, row_y(gy, 0)),
    cpt(gx, gy, 0, 'l'),
)

# 4. student.group_id → group.id (sube por x=330, entre swift y swift_group)
line_pts(
    cpt(stx, sty, 5, 'r'),
    (330, row_y(sty, 4)),
    (330, 235),
    (gx + TW//2, 235),
    (gx + TW//2, gy),
)

# 5. student.periodo_id → periodo.id (sube por la izquierda, x=12)
line_pts(
    cpt(stx, sty, 6, 'l'),
    (12, row_y(sty, 5)),
    (12, row_y(py, 0)),
    cpt(px, py, 0, 'l'),
)

# 6. student_group_class.student_id → student.id (codo izquierdo)
line_pts(
    cpt(scx, scy, 1, 'l'),
    (308, row_y(scy, 1)),
    (308, row_y(sty, 0)),
    cpt(stx, sty, 0, 'r'),
)

# 7. student_group_class.group_id → group.id (sube por x=912, derecha del group)
line_pts(
    cpt(scx, scy, 2, 'r'),
    (912, row_y(scy, 2)),
    (912, row_y(gy, 0)),
    cpt(gx, gy, 0, 'r'),
)

# 8. student_group_class.class_id → class.id (sube por x=950)
line_pts(
    cpt(scx, scy, 3, 'r'),
    (950, row_y(scy, 3)),
    (950, row_y(cly, 0)),
    cpt(clx, cly, 0, 'l'),
)

# 9. planeaciones.id_grupo → group.id (sube verticalmente por x=628)
line_pts(
    cpt(plx, ply, 1, 'l'),
    (628, row_y(ply, 1)),
    (628, row_y(gy, 0)),
    cpt(gx, gy, 0, 'l'),
)

# 10. planeaciones.id_materia → class.id (sube por x=982)
line_pts(
    cpt(plx, ply, 2, 'r'),
    (982, row_y(ply, 2)),
    (982, row_y(cly, 0)),
    cpt(clx, cly, 0, 'l'),
)

# 11. planeaciones.id_docente → user.id (sube por x=1480)
line_pts(
    cpt(plx, ply, 3, 'r'),
    (1478, row_y(ply, 3)),
    (1478, row_y(uy, 0)),
    cpt(ux, uy, 0, 'l'),
)

# 12. planeaciones.periodo_escolar → periodo.id (sube por x=22, extremo izquierdo)
line_pts(
    cpt(plx, ply, 8, 'l'),
    (22, row_y(ply, 8)),
    (22, row_y(py, 0)),
    cpt(px, py, 0, 'l'),
)

# ── Leyenda ───────────────────────────────────────────────────────────────────

lx, ly = 1500, 1010
d.rectangle([lx, ly, lx+280, ly+110], fill=(255, 255, 255), outline=C_BORDER, width=1)
lbl = "Leyenda"
lw = d.textlength(lbl, font=FB)
d.text((lx + (280 - lw)//2, ly+6), lbl, fill=C_HDR_BG, font=FB)
d.text((lx+10, ly+30), "PK  Llave primaria",    fill=C_PK,   font=FR)
d.text((lx+10, ly+52), "FK  Llave foránea",     fill=C_FK,   font=FR)
d.line([(lx+10, ly+82), (lx+50, ly+82)], fill=C_LINE, width=2)
arrowhead((lx+10, ly+82), (lx+50, ly+82))
d.text((lx+58, ly+76), "Relación FK → PK", fill=C_TEXT, font=FR)

# ── Guardar ───────────────────────────────────────────────────────────────────

out = '/home/gus/Documents/MyFirstAIProject/flaskr/static/schema_diagram.png'
img.save(out)
print(f"Guardado: {out}")
