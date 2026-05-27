from PIL import Image, ImageDraw, ImageFont
import math

W, H  = 1400, 1000
TW    = 230
CH    = 24
HH    = 32

C_BG     = (248, 249, 252)
C_HDR_BG = (41,  70, 135)
C_HDR_FG = (255, 255, 255)
C_ROW1   = (255, 255, 255)
C_ROW2   = (237, 242, 255)
C_BORDER = (41,  70, 135)
C_PK     = (180, 100,   0)
C_FK     = (  0, 100, 180)
C_TEXT   = ( 30,  30,  50)
C_TYPE   = (130, 130, 160)
C_LINE   = (100, 130, 220)
C_SHADOW = (200, 205, 220)

img = Image.new('RGB', (W, H), C_BG)
d   = ImageDraw.Draw(img)

FONT_DIR = "/usr/share/fonts/truetype/dejavu/"
try:
    FB = ImageFont.truetype(FONT_DIR + "DejaVuSans-Bold.ttf", 14)
    FR = ImageFont.truetype(FONT_DIR + "DejaVuSans.ttf", 12)
    FT = ImageFont.truetype(FONT_DIR + "DejaVuSans-Bold.ttf", 22)
except Exception:
    FB = FR = FT = ImageFont.load_default()

def tbl_h(n):
    return HH + n * CH + 4

def draw_table(x, y, name, cols):
    h = tbl_h(len(cols))
    d.rectangle([x+4, y+4, x+TW+4, y+h+4], fill=C_SHADOW)
    d.rectangle([x, y, x+TW, y+HH], fill=C_HDR_BG)
    nw = d.textlength(name, font=FB)
    d.text((x + (TW - nw) // 2, y + 9), name, fill=C_HDR_FG, font=FB)
    for i, (cn, ct, pk, fk) in enumerate(cols):
        ry = y + HH + i * CH + 2
        d.rectangle([x, ry, x+TW, ry+CH], fill=C_ROW2 if i % 2 == 0 else C_ROW1)
        if pk:
            d.text((x+5, ry+6), "PK", fill=C_PK, font=FR)
            cx = x + 30
        elif fk:
            d.text((x+5, ry+6), "FK", fill=C_FK, font=FR)
            cx = x + 30
        else:
            cx = x + 10
        d.text((cx, ry+6), cn, fill=C_TEXT, font=FR)
        tw = d.textlength(ct, font=FR)
        d.text((x+TW-tw-5, ry+6), ct, fill=C_TYPE, font=FR)
        d.line([x, ry+CH, x+TW, ry+CH], fill=(210, 215, 230), width=1)
    d.rectangle([x, y, x+TW, y+h], outline=C_BORDER, width=2)

def cpt(tx, ty, ci, side):
    cy = ty + HH + ci * CH + CH // 2 + 2
    return (tx + (TW if side == 'r' else 0), cy)

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

COLS = {
    'user': [
        ('id','INTEGER',True,False), ('username','TEXT',False,False),
        ('email','TEXT',False,False), ('password','TEXT',False,False),
    ],
    'swift': [
        ('id','INTEGER',True,False), ('name','TEXT',False,False),
    ],
    'swift_group': [
        ('id','INTEGER',True,False), ('swift_id','INTEGER',False,True),
        ('group_id','INTEGER',False,True),
    ],
    'group': [
        ('id','INTEGER',True,False), ('name','TEXT',False,False),
    ],
    'student': [
        ('id','INTEGER',True,False), ('name','TEXT',False,False),
        ('lastname','TEXT',False,False), ('email','TEXT',False,False),
        ('semester','INTEGER',False,False), ('group_id','INTEGER',False,True),
    ],
    'class': [
        ('id','INTEGER',True,False), ('name','TEXT',False,False),
        ('semester','INTEGER',False,False),
    ],
    'student_group_class': [
        ('id','INTEGER',True,False), ('student_id','INTEGER',False,True),
        ('group_id','INTEGER',False,True), ('class_id','INTEGER',False,True),
        ('grade','INTEGER',False,False),
    ],
}

POS = {
    'user':                (40,  70),
    'swift':               (640,  70),
    'swift_group':         (640, 210),
    'group':               (640, 390),
    'student':             (40, 310),
    'class':               (980, 390),
    'student_group_class': (530, 650),
}

# Title
title = "Database Schema"
tw = d.textlength(title, font=FT)
d.text(((W - tw) // 2, 12), title, fill=C_HDR_BG, font=FT)

# Draw tables
for t, c in COLS.items():
    x, y = POS[t]
    draw_table(x, y, t, c)

# Shorthand positions
sx,  sy  = POS['swift']
sgx, sgy = POS['swift_group']
gx,  gy  = POS['group']
stx, sty = POS['student']
clx, cly = POS['class']
scx, scy = POS['student_group_class']

# 1. swift_group.swift_id → swift.id (route left of both)
line_pts(cpt(sgx,sgy,1,'l'), (605, sgy+70), (605, sy+46), cpt(sx,sy,0,'l'))

# 2. swift_group.group_id → group.id (route further left)
line_pts(cpt(sgx,sgy,2,'l'), (585, sgy+94), (585, gy+46), cpt(gx,gy,0,'l'))

# 3. student.group_id → group.id (elbow through middle)
p1 = cpt(stx, sty, 5, 'r')
p2 = cpt(gx,  gy,  0, 'l')
mx = (p1[0] + p2[0]) // 2
line_pts(p1, (mx, p1[1]), (mx, p2[1]), p2)

# 4. student_group_class.student_id → student.id (route around left margin)
st_bot_y = sty + tbl_h(len(COLS['student']))
line_pts(
    cpt(scx, scy, 1, 'l'),
    (25, scy + 70),
    (25, st_bot_y + 15),
    (stx + TW//2, st_bot_y + 15),
    (stx + TW//2, st_bot_y),
)

# 5. student_group_class.group_id → group.id (route below group table)
g_bot_y = gy + tbl_h(len(COLS['group']))
line_pts(
    cpt(scx, scy, 2, 'l'),
    (500, scy + 94),
    (500, g_bot_y + 15),
    (gx + TW//2, g_bot_y + 15),
    (gx + TW//2, g_bot_y),
)

# 6. student_group_class.class_id → class.id (route right elbow)
p1 = cpt(scx, scy, 3, 'r')
p2 = cpt(clx, cly, 0, 'l')
line_pts(p1, (890, p1[1]), (890, p2[1]), p2)

# Legend
lx, ly = 40, 920
d.rectangle([lx-5, ly-5, lx+265, ly+68], fill=(255,255,255), outline=C_BORDER, width=1)
d.text((lx+5, ly+5),  "PK  Primary Key",      fill=C_PK,   font=FR)
d.text((lx+5, ly+25), "FK  Foreign Key",      fill=C_FK,   font=FR)
d.line([(lx+5, ly+50), (lx+38, ly+50)], fill=C_LINE, width=2)
arrowhead((lx+5, ly+50), (lx+38, ly+50))
d.text((lx+44, ly+44), "Foreign Key Relation", fill=C_TEXT, font=FR)

out = '/home/gus/Documents/MyFirstAIProject/schema_diagram.png'
img.save(out)
print(f"Saved: {out}")
