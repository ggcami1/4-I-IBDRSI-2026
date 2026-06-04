from PIL import Image, ImageDraw, ImageFont
import math

W, H = 1320, 980

# ── Paleta de colores ─────────────────────────────────────────────────────────
C_BG        = (245, 247, 252)

C_TITLE_BG  = (25,  50,  115)
C_TITLE_FG  = (255, 255, 255)

C_FE_BG     = (214, 234, 255)
C_FE_HDR    = (41,  100, 180)
C_FE_BORDER = (41,  100, 180)
C_FE_BOX    = (255, 255, 255)
C_FE_BOX_B  = (100, 150, 220)
C_FE_TAG    = (41,  100, 180)

C_BE_BG     = (255, 243, 220)
C_BE_HDR    = (160,  80,  10)
C_BE_BORDER = (160,  80,  10)
C_BE_BOX    = (255, 255, 255)
C_BE_BOX_B  = (200, 130,  50)
C_BE_SUB_BG = (255, 249, 235)
C_BE_SUB_B  = (210, 160,  80)
C_BE_TAG    = (160,  80,  10)

C_DB_BG     = (215, 245, 222)
C_DB_HDR    = (25,  120,  55)
C_DB_BORDER = (25,  120,  55)
C_DB_BOX    = (255, 255, 255)
C_DB_BOX_B  = (80,  180, 100)
C_DB_TAG    = (25,  120,  55)

C_ARROW     = (80,  80,  130)
C_CONN      = (100, 100, 150)
C_TEXT      = (30,  30,   50)
C_SUB       = (90,  90,  115)
C_VER       = (140, 140, 165)
C_WHITE     = (255, 255, 255)

# ── Tipografía ────────────────────────────────────────────────────────────────
FONT_DIR = "/usr/share/fonts/truetype/dejavu/"
try:
    F24B = ImageFont.truetype(FONT_DIR + "DejaVuSans-Bold.ttf",   24)
    F18B = ImageFont.truetype(FONT_DIR + "DejaVuSans-Bold.ttf",   18)
    F15B = ImageFont.truetype(FONT_DIR + "DejaVuSans-Bold.ttf",   15)
    F13B = ImageFont.truetype(FONT_DIR + "DejaVuSans-Bold.ttf",   13)
    F13  = ImageFont.truetype(FONT_DIR + "DejaVuSans.ttf",        13)
    F12  = ImageFont.truetype(FONT_DIR + "DejaVuSans.ttf",        12)
    F11  = ImageFont.truetype(FONT_DIR + "DejaVuSans.ttf",        11)
    F11B = ImageFont.truetype(FONT_DIR + "DejaVuSans-Bold.ttf",   11)
    F10  = ImageFont.truetype(FONT_DIR + "DejaVuSans.ttf",        10)
except Exception:
    F24B = F18B = F15B = F13B = F13 = F12 = F11 = F11B = F10 = ImageFont.load_default()

img = Image.new('RGB', (W, H), C_BG)
d   = ImageDraw.Draw(img)


# ── Helpers ───────────────────────────────────────────────────────────────────

def rr(x1, y1, x2, y2, r=10, fill=None, outline=None, width=2):
    d.rounded_rectangle([x1, y1, x2, y2], radius=r, fill=fill,
                        outline=outline, width=width)

def centered(text, x1, x2, y, font, color):
    tw = d.textlength(text, font=font)
    d.text(((x1 + x2 - tw) // 2, y), text, fill=color, font=font)

def arrow_down(cx, y1, y2, label='', sublabel=''):
    # Vertical double arrow (bidirectional)
    d.line([(cx, y1), (cx, y2)], fill=C_ARROW, width=3)
    # Arrowhead down
    s = 9
    d.polygon([(cx, y2), (cx-s, y2-s*1.6), (cx+s, y2-s*1.6)], fill=C_ARROW)
    # Arrowhead up
    d.polygon([(cx, y1), (cx-s, y1+s*1.6), (cx+s, y1+s*1.6)], fill=C_ARROW)
    if label:
        tw = d.textlength(label, font=F13B)
        d.text((cx - tw//2, (y1+y2)//2 - 16), label, fill=C_CONN, font=F13B)
    if sublabel:
        tw = d.textlength(sublabel, font=F11)
        d.text((cx - tw//2, (y1+y2)//2 + 2), sublabel, fill=C_SUB, font=F11)

def tech_box(x, y, w, h, title, subtitle, tag_color, r=8):
    rr(x, y, x+w, y+h, r=r, fill=C_WHITE, outline=tag_color, width=2)
    centered(title,    x, x+w, y+10, F13B, C_TEXT)
    if subtitle:
        centered(subtitle, x, x+w, y+28, F11,  C_VER)

def section_header(x1, y1, x2, y2, title, subtitle, bg, border, hdr_color, r=12):
    rr(x1, y1, x2, y2, r=r, fill=bg, outline=border, width=2)
    # Header strip
    d.rounded_rectangle([x1, y1, x2, y1+38], radius=r, fill=hdr_color)
    d.rectangle([x1, y1+18, x2, y1+38], fill=hdr_color)  # flatten bottom of header
    centered(title, x1, x2, y1+10, F15B, C_WHITE)
    if subtitle:
        centered(subtitle, x1, x2, y1+44, F12, C_SUB)


# ── Título ────────────────────────────────────────────────────────────────────

d.rectangle([0, 0, W, 56], fill=C_TITLE_BG)
centered("Arquitectura del Sistema — Control Escolar", 0, W, 14, F24B, C_TITLE_FG)

# ── CAPA 1: Frontend ──────────────────────────────────────────────────────────

FE_Y1, FE_Y2 = 66, 242
section_header(20, FE_Y1, W-20, FE_Y2,
               "CAPA DE PRESENTACIÓN  —  Frontend",
               "Renderizado en el navegador del usuario",
               C_FE_BG, C_FE_BORDER, C_FE_HDR)

BW, BH = 220, 62
BY = FE_Y1 + 72
GAP = (W - 40 - 4*BW) // 5
BXS = [20 + GAP + i*(BW + GAP) for i in range(4)]

tech_box(BXS[0], BY, BW, BH, "HTML5",          "Estructura · Formularios",     C_FE_BOX_B)
tech_box(BXS[1], BY, BW, BH, "CSS3",           "Diseño · Responsive · Flexbox", C_FE_BOX_B)
tech_box(BXS[2], BY, BW, BH, "Jinja2 Templates","Renderizado server-side",     C_FE_BOX_B)
tech_box(BXS[3], BY, BW, BH, "JavaScript ES6", "Fetch API · DOM · Async/Await", C_FE_BOX_B)

# ── Flecha HTTP ───────────────────────────────────────────────────────────────

ARROW_Y1, ARROW_Y2 = FE_Y2 + 4, FE_Y2 + 60
arrow_down(W//2, ARROW_Y1, ARROW_Y2,
           label="HTTP / HTTPS",
           sublabel="Peticiones GET/POST  ·  Respuestas HTML/JSON")

# ── CAPA 2: Backend ───────────────────────────────────────────────────────────

BE_Y1, BE_Y2 = ARROW_Y2 + 4, 750
section_header(20, BE_Y1, W-20, BE_Y2,
               "CAPA DE LÓGICA DE NEGOCIO  —  Backend",
               "Python 3.14  ·  Servidor WSGI",
               C_BE_BG, C_BE_BORDER, C_BE_HDR)

# Sub-sección: Framework & Core
SUB1_Y1 = BE_Y1 + 68
SUB1_Y2 = SUB1_Y1 + 90
rr(40, SUB1_Y1, W-40, SUB1_Y2, r=8, fill=C_BE_SUB_BG, outline=C_BE_SUB_B, width=1)
d.text((52, SUB1_Y1 + 6), "Framework & Core", fill=C_BE_TAG, font=F11B)

FW, FH = 240, 52
FY = SUB1_Y1 + 28
FG = (W - 80 - 3*FW) // 4
FXS = [40 + FG + i*(FW + FG) for i in range(3)]
tech_box(FXS[0], FY, FW, FH, "Flask 3.1.3",    "Framework web WSGI",           C_BE_BOX_B)
tech_box(FXS[1], FY, FW, FH, "Werkzeug 3.1.8", "WSGI · Hashing de contraseñas", C_BE_BOX_B)
tech_box(FXS[2], FY, FW, FH, "Jinja2",         "Motor de plantillas HTML",      C_BE_BOX_B)

# Sub-sección: Módulos de la aplicación
SUB2_Y1 = SUB1_Y2 + 14
SUB2_Y2 = SUB2_Y1 + 90
rr(40, SUB2_Y1, W-40, SUB2_Y2, r=8, fill=C_BE_SUB_BG, outline=C_BE_SUB_B, width=1)
d.text((52, SUB2_Y1 + 6), "Módulos de la Aplicación", fill=C_BE_TAG, font=F11B)

MW, MH = 220, 52
MY = SUB2_Y1 + 28
MG = (W - 80 - 4*MW) // 5
MXS = [40 + MG + i*(MW + MG) for i in range(4)]
tech_box(MXS[0], MY, MW, MH, "auth.py",     "Registro · Login · 2FA · Recuperación", C_BE_BOX_B)
tech_box(MXS[1], MY, MW, MH, "student.py",  "Alumnos · Grupos · Clases · Planeaciones", C_BE_BOX_B)
tech_box(MXS[2], MY, MW, MH, "db.py",       "Conexión SQLite · Auditoría UDF",     C_BE_BOX_B)
tech_box(MXS[3], MY, MW, MH, "__init__.py", "Fábrica de la app · Configuración",   C_BE_BOX_B)

# Sub-sección: Librerías de apoyo
SUB3_Y1 = SUB2_Y2 + 14
SUB3_Y2 = SUB3_Y1 + 90
rr(40, SUB3_Y1, W-40, SUB3_Y2, r=8, fill=C_BE_SUB_BG, outline=C_BE_SUB_B, width=1)
d.text((52, SUB3_Y1 + 6), "Librerías de Apoyo", fill=C_BE_TAG, font=F11B)

LW, LH = 200, 52
LY = SUB3_Y1 + 28
LG = (W - 80 - 4*LW) // 5
LXS = [40 + LG + i*(LW + LG) for i in range(4)]
tech_box(LXS[0], LY, LW, LH, "pyotp 2.9.0",  "Autenticación TOTP (2FA)",      C_BE_BOX_B)
tech_box(LXS[1], LY, LW, LH, "qrcode 8.2",   "Generación de códigos QR",      C_BE_BOX_B)
tech_box(LXS[2], LY, LW, LH, "Pillow 12.2.0","Procesamiento de imágenes",     C_BE_BOX_B)
tech_box(LXS[3], LY, LW, LH, "click 8.3.3",  "CLI · Comando flask init-db",   C_BE_BOX_B)

# ── Flecha DB ─────────────────────────────────────────────────────────────────

DB_ARROW_Y1 = BE_Y2 + 4
DB_ARROW_Y2 = DB_ARROW_Y1 + 52
arrow_down(W//2, DB_ARROW_Y1, DB_ARROW_Y2,
           label="sqlite3  (Python stdlib)",
           sublabel="Lectura / escritura de datos locales")

# ── CAPA 3: Base de datos ─────────────────────────────────────────────────────

DB_Y1 = DB_ARROW_Y2 + 4
DB_Y2 = H - 16
section_header(20, DB_Y1, W-20, DB_Y2,
               "CAPA DE DATOS  —  Base de Datos",
               "Almacenamiento local en archivo",
               C_DB_BG, C_DB_BORDER, C_DB_HDR)

DW, DH = 280, 66
DY = DB_Y1 + 56
DG = (W - 40 - 3*DW) // 4
DXS = [20 + DG + i*(DW + DG) for i in range(3)]

tech_box(DXS[0], DY, DW, DH, "SQLite 3",
         "instance/flaskr.sqlite", C_DB_BOX_B)

tech_box(DXS[1], DY, DW, DH, "12 Tablas · Triggers · Índices",
         "Esquema relacional completo", C_DB_BOX_B)

tech_box(DXS[2], DY, DW, DH, "Auditoría integrada",
         "login_logs · audit_logs · UDF", C_DB_BOX_B)

# ── Guardar ───────────────────────────────────────────────────────────────────

out = '/home/gus/Documents/MyFirstAIProject/flaskr/static/architecture_diagram.png'
img.save(out)
print(f"Guardado: {out}")
