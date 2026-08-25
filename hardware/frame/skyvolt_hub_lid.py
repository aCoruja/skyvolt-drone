import FreeCAD, Part, math, os

doc = FreeCAD.newDocument("VoltHex_HubLid")

# ---------------------------------------------------------------------------
# PARAMETROS (mm) - medidos a partir de VoltHex_Hub.FCStd e VoltHex_Arm.FCStd
# (peca existente, sem script parametrico) para garantir encaixe real.
# ---------------------------------------------------------------------------
LID_VERTEX_R   = 65.0   # raio do hexagono (centro->vertice); hub real vai ate r=64.8
LID_THK        = 4.0    # espessura da tampa (nao precisa dos 6mm do hub, so fecha/trava)
LID_FILLET_R   = 6.0    # arredondamento dos 6 cantos

STANDOFF_R       = 32.0   # raio dos furos de coluna - igual ao VoltHex_Hub (medido: +-22.63,+-22.63)
STANDOFF_HOLE_D  = 3.4    # M3 folga

ARM_ANGLES       = [0, 60, 120, 180, 240, 300]  # mesmo esquema de rotacao da montagem
CLAMP_HOLE_R     = [52.0, 62.0]  # raios ao longo do eixo do braco - identico aos 2 furos da lingueta do braco
CLAMP_HOLE_D     = 3.2    # M3 folga - igual ao furo existente no VoltHex_Arm
CLAMP_CLEARANCE  = 4.0    # margem de exclusao do favo de mel ao redor de cada furo de trava

HONEYCOMB_CELL_R  = 6.0
HONEYCOMB_WALL    = 3.0
HONEYCOMB_MIN_R   = 16.0
HONEYCOMB_MARGIN  = 0.82
STANDOFF_CLEARANCE = 8.0

N_SIDES = 6

# ---------------------------------------------------------------------------
def hex_vertices(radius, cx=0.0, cy=0.0, rot_deg=0.0):
    pts = []
    for i in range(6):
        a = math.radians(60 * i + rot_deg)
        pts.append(FreeCAD.Vector(cx + radius * math.cos(a), cy + radius * math.sin(a), 0.0))
    pts.append(pts[0])
    return pts

def point_in_polygon(x, y, verts):
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

def near_any_clamp_hole(x, y, clearance, clamp_centers):
    for (hx, hy) in clamp_centers:
        if math.hypot(x - hx, y - hy) < clearance:
            return True
    return False

# ---------------------------------------------------------------------------
# 1) TAMPA - hexagono com cantos arredondados
# ---------------------------------------------------------------------------
lid_pts = hex_vertices(LID_VERTEX_R)
lid_solid = make_prism_from_pts(lid_pts, 0.0, LID_THK)

v_edges = straight_vertical_edges(lid_solid)
if v_edges:
    try:
        lid_solid = lid_solid.makeFillet(LID_FILLET_R, v_edges)
    except Exception as ex:
        FreeCAD.Console.PrintWarning("Falha no fillet da tampa: %s\n" % ex)

# ---------------------------------------------------------------------------
# 2) POSICOES DOS FUROS
# ---------------------------------------------------------------------------
standoff_centers = []
for k in range(4):
    a = math.radians(45 + 90 * k)
    standoff_centers.append((STANDOFF_R * math.cos(a), STANDOFF_R * math.sin(a)))

clamp_centers = []
for ang in ARM_ANGLES:
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    for r in CLAMP_HOLE_R:
        clamp_centers.append((ux * r, uy * r))

# ---------------------------------------------------------------------------
# 3) FAVO DE MEL (alivio de peso), evitando standoffs e furos de trava
# ---------------------------------------------------------------------------
hub_boundary = hex_vertices(LID_VERTEX_R * HONEYCOMB_MARGIN)

cell_pitch_x = (HONEYCOMB_CELL_R * math.sqrt(3)) + HONEYCOMB_WALL
cell_pitch_y = (HONEYCOMB_CELL_R * 1.5) + HONEYCOMB_WALL * math.sqrt(3) / 2.0

honeycomb_cells = []
row = 0
y = -LID_VERTEX_R
while y <= LID_VERTEX_R:
    x_offset = (cell_pitch_x / 2.0) if (row % 2) else 0.0
    x = -LID_VERTEX_R + x_offset
    while x <= LID_VERTEX_R:
        r = math.hypot(x, y)
        ok = (HONEYCOMB_MIN_R <= r) and point_in_polygon(x, y, hub_boundary)
        if ok:
            for (sx, sy) in standoff_centers:
                if math.hypot(x - sx, y - sy) < STANDOFF_CLEARANCE:
                    ok = False
                    break
            if ok and near_any_clamp_hole(x, y, CLAMP_CLEARANCE, clamp_centers):
                ok = False
        if ok:
            cell_pts = hex_vertices(HONEYCOMB_CELL_R, cx=x, cy=y, rot_deg=90)
            honeycomb_cells.append(make_prism_from_pts(cell_pts, -1.0, LID_THK + 1.0))
        x += cell_pitch_x
    y += cell_pitch_y
    row += 1

if honeycomb_cells:
    comb_tool = honeycomb_cells[0]
    for c in honeycomb_cells[1:]:
        comb_tool = comb_tool.fuse(c)
    comb_tool = comb_tool.removeSplitter()
    lid_solid = lid_solid.cut(comb_tool)

# ---------------------------------------------------------------------------
# 4) FUROS - coluna (standoff) e trava dos bracos (clamp)
# ---------------------------------------------------------------------------
hole_tools = []
for (sx, sy) in standoff_centers:
    hole_tools.append(Part.makeCylinder(STANDOFF_HOLE_D / 2.0, LID_THK + 4, FreeCAD.Vector(sx, sy, -2)))
for (hx, hy) in clamp_centers:
    hole_tools.append(Part.makeCylinder(CLAMP_HOLE_D / 2.0, LID_THK + 4, FreeCAD.Vector(hx, hy, -2)))

holes = hole_tools[0]
for t in hole_tools[1:]:
    holes = holes.fuse(t)
holes = holes.removeSplitter()
lid_solid = lid_solid.cut(holes)
lid_solid = lid_solid.removeSplitter()

# ---------------------------------------------------------------------------
# 5) SALVAR
# ---------------------------------------------------------------------------
obj = doc.addObject("Part::Feature", "VoltHex_HubLid")
obj.Shape = lid_solid
doc.recompute()

out_dir = "/home/acoruja/Documentos/Projeto_Desenvolvimento/Impressao_3D"
doc.saveAs(os.path.join(out_dir, "VoltHex_HubLid.FCStd"))
Part.export([obj], os.path.join(out_dir, "VoltHex_HubLid.stl"))
Part.export([obj], os.path.join(out_dir, "VoltHex_HubLid.step"))

print("OK - volume:", lid_solid.Volume, "mm3  bbox:", lid_solid.BoundBox)
print("clamp holes:", clamp_centers)
print("standoff holes:", standoff_centers)
