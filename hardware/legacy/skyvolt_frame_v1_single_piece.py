import FreeCAD, Part, math, os

doc = FreeCAD.newDocument("SkyVolt_Frame")

# ---------------------------------------------------------------------------
# PARAMETROS (mm) - ajuste aqui conforme o motor/servo/parafusos reais
# ---------------------------------------------------------------------------
HUB_VERTEX_R      = 58.0   # raio do hub (centro -> vertice), hexagono "ponta para fora"
HUB_THK           = 6.0    # espessura do hub e dos bracos
HUB_FILLET_R      = 9.0    # arredondamento dos 6 cantos do hub

ARM_TIP_R         = 148.0  # distancia do centro ao centro do motor
ARM_W_ROOT        = 26.0   # largura do braco junto ao hub
ARM_W_TIP         = 20.0   # largura do braco junto ao motor

MOTOR_PAD_R       = 17.0   # raio do disco de fixacao do motor
MOTOR_BOLT_CIRCLE = 16.0   # diametro do circulo de furos do motor
MOTOR_BOLT_HOLE_D = 3.0    # diametro dos furos de fixacao do motor (M3)
MOTOR_CENTER_HOLE_D = 8.0  # furo central p/ eixo/fios do motor

STANDOFF_R        = 32.0   # raio do circulo dos furos de coluna (stack eletronica)
STANDOFF_HOLE_D    = 3.4   # furo para parafuso/coluna M3

EFFECTOR_ARMS      = [0, 2, 4]  # indices dos bracos (0..5) que recebem base de efetuador
EFFECTOR_POS_FRAC  = 0.62        # posicao da base ao longo do braco (0=hub, 1=motor)
EFFECTOR_W, EFFECTOR_L, EFFECTOR_H = 20.0, 15.0, 3.0
EFFECTOR_HOLE_D    = 2.2
EFFECTOR_HOLE_DX   = 12.0  # espacamento entre os 2 furos

HONEYCOMB_CELL_R   = 7.0   # raio (vertice) de cada celula hexagonal
HONEYCOMB_WALL     = 3.0   # parede entre celulas
HONEYCOMB_MIN_R    = 18.0  # nao gerar celulas mais perto do centro que isso
HONEYCOMB_MARGIN   = 0.80  # fracao do HUB_VERTEX_R ate onde o favo pode chegar
STANDOFF_CLEARANCE = 9.0   # nao gerar celula muito perto de um furo de coluna

GLOBAL_EASE_R      = 1.0   # arredondamento leve em todas as arestas (acabamento)

N_ARMS = 6

# ---------------------------------------------------------------------------
def hex_vertices(radius, cx=0.0, cy=0.0, rot_deg=0.0):
    pts = []
    for i in range(6):
        a = math.radians(60 * i + rot_deg)
        pts.append(FreeCAD.Vector(cx + radius * math.cos(a), cy + radius * math.sin(a), 0.0))
    pts.append(pts[0])
    return pts

def point_in_polygon(x, y, verts):
    # ray casting; verts is closed list (first==last), 2D via .x/.y
    inside = False
    n = len(verts) - 1
    j = n - 1
    for i in range(n):
        xi, yi = verts[i].x, verts[i].y
        xj, yj = verts[j].x, verts[j].y
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside

def make_prism_from_pts(pts, z0, z1):
    wire = Part.makePolygon(pts)
    face = Part.Face(wire)
    return face.extrude(FreeCAD.Vector(0, 0, z1 - z0)).translate(FreeCAD.Vector(0, 0, z0))

def straight_vertical_edges(shape):
    edges = []
    for e in shape.Edges:
        if len(e.Vertexes) != 2:
            continue
        c = e.Curve
        if not isinstance(c, Part.Line):
            continue
        v0, v1 = e.Vertexes[0].Point, e.Vertexes[1].Point
        dz = abs(v1.z - v0.z)
        dxy = math.hypot(v1.x - v0.x, v1.y - v0.y)
        if dz > 0.01 and dxy < 0.01:
            edges.append(e)
    return edges

# ---------------------------------------------------------------------------
# 1) HUB - hexagono com cantos arredondados
# ---------------------------------------------------------------------------
hub_pts = hex_vertices(HUB_VERTEX_R)
hub_solid = make_prism_from_pts(hub_pts, 0.0, HUB_THK)

v_edges = straight_vertical_edges(hub_solid)
if v_edges:
    try:
        hub_solid = hub_solid.makeFillet(HUB_FILLET_R, v_edges)
    except Exception as ex:
        FreeCAD.Console.PrintWarning("Falha no fillet do hub: %s\n" % ex)

# ---------------------------------------------------------------------------
# 2) BRACOS + PAD DO MOTOR (+ base de efetuador em 3 deles)
# ---------------------------------------------------------------------------
def build_arm(angle_deg, with_effector):
    a = math.radians(angle_deg)
    ux, uy = math.cos(a), math.sin(a)   # direcao radial
    nx, ny = -uy, ux                    # normal (perpendicular)

    root_c = FreeCAD.Vector(ux * (HUB_VERTEX_R * 0.55), uy * (HUB_VERTEX_R * 0.55), 0.0)
    tip_c  = FreeCAD.Vector(ux * ARM_TIP_R, uy * ARM_TIP_R, 0.0)

    hw_r, hw_t = ARM_W_ROOT / 2.0, ARM_W_TIP / 2.0
    p1 = root_c + FreeCAD.Vector(nx * hw_r, ny * hw_r, 0)
    p2 = root_c - FreeCAD.Vector(nx * hw_r, ny * hw_r, 0)
    p3 = tip_c  - FreeCAD.Vector(nx * hw_t, ny * hw_t, 0)
    p4 = tip_c  + FreeCAD.Vector(nx * hw_t, ny * hw_t, 0)
    arm_solid = make_prism_from_pts([p1, p2, p3, p4, p1], 0.0, HUB_THK)

    pad = Part.makeCylinder(MOTOR_PAD_R, HUB_THK, tip_c)
    arm_solid = arm_solid.fuse(pad)

    if with_effector:
        pos_c = root_c + (tip_c - root_c) * EFFECTOR_POS_FRAC
        bx = FreeCAD.Vector(ux, uy, 0) * (EFFECTOR_L / 2.0)
        by = FreeCAD.Vector(nx, ny, 0) * (EFFECTOR_W / 2.0)
        e1 = pos_c - bx - by
        e2 = pos_c + bx - by
        e3 = pos_c + bx + by
        e4 = pos_c - bx + by
        boss = make_prism_from_pts([e1, e2, e3, e4, e1], HUB_THK, HUB_THK + EFFECTOR_H)
        ve = straight_vertical_edges(boss)
        try:
            boss = boss.makeFillet(2.5, ve)
        except Exception:
            pass
        arm_solid = arm_solid.fuse(boss)

    return arm_solid, tip_c, ux, uy, nx, ny

arm_shapes = []
motor_centers = []
effector_centers = []

for i in range(N_ARMS):
    angle = 60.0 * i
    with_fx = i in EFFECTOR_ARMS
    shp, tip_c, ux, uy, nx, ny = build_arm(angle, with_fx)
    arm_shapes.append(shp)
    motor_centers.append(tip_c)
    if with_fx:
        root_c = FreeCAD.Vector(ux * (HUB_VERTEX_R * 0.55), uy * (HUB_VERTEX_R * 0.55), 0.0)
        pos_c = root_c + (tip_c - root_c) * EFFECTOR_POS_FRAC
        effector_centers.append((pos_c, ux, uy, nx, ny))

base = hub_solid
for shp in arm_shapes:
    base = base.fuse(shp)
base = base.removeSplitter()

# ---------------------------------------------------------------------------
# 3) FAVO DE MEL (alivio de peso) no hub
# ---------------------------------------------------------------------------
hub_boundary = hex_vertices(HUB_VERTEX_R * HONEYCOMB_MARGIN)
standoff_centers = []
for k in range(4):
    a = math.radians(45 + 90 * k)
    standoff_centers.append((STANDOFF_R * math.cos(a), STANDOFF_R * math.sin(a)))

cell_pitch_x = (HONEYCOMB_CELL_R * math.sqrt(3)) + HONEYCOMB_WALL
cell_pitch_y = (HONEYCOMB_CELL_R * 1.5) + HONEYCOMB_WALL * math.sqrt(3) / 2.0

honeycomb_cells = []
row = 0
y = -HUB_VERTEX_R
while y <= HUB_VERTEX_R:
    x_offset = (cell_pitch_x / 2.0) if (row % 2) else 0.0
    x = -HUB_VERTEX_R + x_offset
    while x <= HUB_VERTEX_R:
        r = math.hypot(x, y)
        ok = HONEYCOMB_MIN_R <= r
        if ok and point_in_polygon(x, y, hub_boundary):
            for (sx, sy) in standoff_centers:
                if math.hypot(x - sx, y - sy) < STANDOFF_CLEARANCE:
                    ok = False
                    break
        if ok:
            cell_pts = hex_vertices(HONEYCOMB_CELL_R, cx=x, cy=y, rot_deg=90)
            honeycomb_cells.append(make_prism_from_pts(cell_pts, -1.0, HUB_THK + 1.0))
        x += cell_pitch_x
    y += cell_pitch_y
    row += 1

if honeycomb_cells:
    comb_tool = honeycomb_cells[0]
    for c in honeycomb_cells[1:]:
        comb_tool = comb_tool.fuse(c)
    comb_tool = comb_tool.removeSplitter()
    base = base.cut(comb_tool)

# ---------------------------------------------------------------------------
# 4) FUROS - motor, coluna (standoff) e efetuador
# ---------------------------------------------------------------------------
hole_tools = []

for tip_c in motor_centers:
    hole_tools.append(Part.makeCylinder(MOTOR_CENTER_HOLE_D / 2.0, HUB_THK + 4, tip_c + FreeCAD.Vector(0, 0, -2)))
    for k in range(4):
        a = math.radians(45 + 90 * k)
        hx = tip_c.x + (MOTOR_BOLT_CIRCLE / 2.0) * math.cos(a)
        hy = tip_c.y + (MOTOR_BOLT_CIRCLE / 2.0) * math.sin(a)
        hole_tools.append(Part.makeCylinder(MOTOR_BOLT_HOLE_D / 2.0, HUB_THK + 4, FreeCAD.Vector(hx, hy, -2)))

for (sx, sy) in standoff_centers:
    hole_tools.append(Part.makeCylinder(STANDOFF_HOLE_D / 2.0, HUB_THK + 4, FreeCAD.Vector(sx, sy, -2)))

for (pos_c, ux, uy, nx, ny) in effector_centers:
    for sgn in (-1, 1):
        hx = pos_c.x + ux * (EFFECTOR_HOLE_DX / 2.0) * sgn
        hy = pos_c.y + uy * (EFFECTOR_HOLE_DX / 2.0) * sgn
        hole_tools.append(Part.makeCylinder(EFFECTOR_HOLE_D / 2.0, HUB_THK + EFFECTOR_H + 4, FreeCAD.Vector(hx, hy, -2)))

holes = hole_tools[0]
for t in hole_tools[1:]:
    holes = holes.fuse(t)
holes = holes.removeSplitter()
base = base.cut(holes)
base = base.removeSplitter()

# ---------------------------------------------------------------------------
# 5) ACABAMENTO - o hub ja tem cantos arredondados (HUB_FILLET_R), os pads de
#    motor e a base dos efetuadores ja sao arredondados na sua construcao.
#    Um "ease" global de todas as arestas foi tentado mas conflita com os
#    furos/favo de mel (muito proximos entre si); optou-se por nao aplicar
#    para manter o boolean robusto. Arestas de contorno seguem vivas (90),
#    o que e normal e resistente para pecas FDM.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# 6) SALVAR
# ---------------------------------------------------------------------------
obj = doc.addObject("Part::Feature", "SkyVolt_Frame")
obj.Shape = base
doc.recompute()

out_dir = "/home/acoruja/Documentos/Projeto_Desenvolvimento/Impressao_3D"
doc.saveAs(os.path.join(out_dir, "SkyVolt_Frame.FCStd"))
Part.export([obj], os.path.join(out_dir, "SkyVolt_Frame.stl"))
Part.export([obj], os.path.join(out_dir, "SkyVolt_Frame.step"))

print("OK - volume:", base.Volume, "mm3  bbox:", base.BoundBox)
