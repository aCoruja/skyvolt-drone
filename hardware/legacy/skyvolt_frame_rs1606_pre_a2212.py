import FreeCAD, Part, math, os

out_dir = "/home/acoruja/Documentos/Projeto_Desenvolvimento/SkyVolt/hardware/frame"

# ---------------------------------------------------------------------------
# PARAMETROS (mm) - Rev.2: motor RS1606 3300KV real, frame modular (mesa 220x220)
# ---------------------------------------------------------------------------
HUB_VERTEX_R      = 70.0
HUB_THK           = 6.0
HUB_FILLET_R      = 10.0

ARM_TIP_R         = 190.0   # centro -> centro do motor
ARM_THK           = HUB_THK
ARM_W_ROOT        = 26.0
ARM_W_TIP         = 20.0
ARM_SEGMENTS      = 14       # pontos ao longo do comprimento p/ curva suave do braco

SHOULDER_R        = HUB_VERTEX_R   # onde o braco encosta no hub (face externa)
TAB_DEPTH         = 22.0           # profundidade da lingueta dentro do hub
TAB_W             = 18.0           # largura da lingueta
TAB_BOLT_HOLE_D   = 3.2            # M3 folga
TAB_BOLT_R1       = SHOULDER_R - 8.0
TAB_BOLT_R2       = SHOULDER_R - 18.0

MOTOR_PAD_R          = 12.0    # disco de fixacao do motor RS1606 (pequeno)
MOTOR_SQUARE_HALF    = 6.0     # padrao de furacao 12x12mm (M2) - verificar contra datasheet real antes de imprimir
MOTOR_BOLT_HOLE_D    = 2.2     # M2 folga
MOTOR_CENTER_HOLE_D  = 6.0     # eixo/fios

STANDOFF_R        = 32.0
STANDOFF_HOLE_D    = 3.4

HONEYCOMB_CELL_R   = 7.0
HONEYCOMB_WALL     = 3.0
HONEYCOMB_MIN_R    = 22.0
HONEYCOMB_MARGIN   = 0.80
STANDOFF_CLEARANCE = 9.0
SLOT_CLEARANCE     = 11.0   # folga do favo de mel em torno de cada rasgo de encaixe do braco

GROOVE_W           = 8.0
GROOVE_DEPTH       = 1.2

# Servo SG90 (efetuadores) - dimensao padrao de mercado, alta confianca
SERVO_HOLE_SPACING = 32.5    # centro a centro dos furos das orelhas
SERVO_HOLE_D       = 2.2     # M2 folga
SERVO_BOSS_L       = 36.0    # ao longo do braco
SERVO_BOSS_W       = 14.0
SERVO_BOSS_H       = 3.0
EFFECTOR_POS_FRAC  = 0.62    # posicao do centro do servo ao longo do braco (0=ombro, 1=ponta)

# Bandeja de eletronica (ESP32-S3 x2 + LoRa x2) - aparafusa nos 4 furos de coluna do hub
TRAY_L             = 150.0
TRAY_W             = 80.0
TRAY_THK           = 3.0
TRAY_CHAMFER       = 8.0
ESP32_L            = 70.0    # ESP32-S3-DevKitC-1, dado oficial Espressif
ESP32_W            = 28.0
ESP32_CLEARANCE    = 0.8     # folga do trilho
RAIL_H             = 2.4
RAIL_T             = 1.6
STRAP_SLOT_W       = 2.2
STRAP_SLOT_L       = 7.0
LORA_BAY_L         = 28.0    # bandeja generica ajustavel (modulo LoRa sem furo confirmado)
LORA_BAY_W         = 20.0
LORA_NUB_D         = 3.0
LORA_NUB_H         = 1.5

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

def circle_edges(shape, z_level, radius, tol=0.05):
    edges = []
    for e in shape.Edges:
        c = e.Curve
        if not isinstance(c, Part.Circle):
            continue
        if abs(c.Center.z - z_level) < 0.5 and abs(c.Radius - radius) < tol + 0.3:
            edges.append(e)
    return edges

# =====================================================================
# HUB
# =====================================================================
def build_hub():
    hub_pts = hex_vertices(HUB_VERTEX_R)
    hub = make_prism_from_pts(hub_pts, 0.0, HUB_THK)

    v_edges = straight_vertical_edges(hub)
    if v_edges:
        try:
            hub = hub.makeFillet(HUB_FILLET_R, v_edges)
        except Exception as ex:
            FreeCAD.Console.PrintWarning("Falha no fillet do hub: %s\n" % ex)

    # favo de mel
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
                r_pt = math.hypot(x, y)
                ang_pt = math.atan2(y, x)
                for i6 in range(N_ARMS):
                    da = ang_pt - math.radians(60.0 * i6)
                    lx = r_pt * math.cos(da)
                    ly = r_pt * math.sin(da)
                    if (SHOULDER_R - TAB_DEPTH - SLOT_CLEARANCE) <= lx <= (SHOULDER_R + SLOT_CLEARANCE) and abs(ly) <= (TAB_W / 2.0 + SLOT_CLEARANCE):
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
        hub = hub.cut(comb_tool)

    # furos de coluna (stack eletronica)
    hole_tools = []
    for (sx, sy) in standoff_centers:
        hole_tools.append(Part.makeCylinder(STANDOFF_HOLE_D / 2.0, HUB_THK + 4, FreeCAD.Vector(sx, sy, -2)))

    # 6 rasgos (mortise) + furos de parafuso da lingueta
    slot_tools = []
    for i in range(N_ARMS):
        angle = 60.0 * i
        a = math.radians(angle)
        ux, uy = math.cos(a), math.sin(a)
        nx, ny = -uy, ux

        root_c = FreeCAD.Vector(ux * (SHOULDER_R - TAB_DEPTH), uy * (SHOULDER_R - TAB_DEPTH), 0.0)
        tip_c  = FreeCAD.Vector(ux * (SHOULDER_R + 2.0), uy * (SHOULDER_R + 2.0), 0.0)
        hw = TAB_W / 2.0
        p1 = root_c + FreeCAD.Vector(nx * hw, ny * hw, 0)
        p2 = root_c - FreeCAD.Vector(nx * hw, ny * hw, 0)
        p3 = tip_c  - FreeCAD.Vector(nx * hw, ny * hw, 0)
        p4 = tip_c  + FreeCAD.Vector(nx * hw, ny * hw, 0)
        slot_tools.append(make_prism_from_pts([p1, p2, p3, p4, p1], -1.0, HUB_THK + 1.0))

        for r_bolt in (TAB_BOLT_R1, TAB_BOLT_R2):
            bx, by = ux * r_bolt, uy * r_bolt
            hole_tools.append(Part.makeCylinder(TAB_BOLT_HOLE_D / 2.0, HUB_THK + 4, FreeCAD.Vector(bx, by, -2)))

    cut_tool = slot_tools[0]
    for t in slot_tools[1:]:
        cut_tool = cut_tool.fuse(t)
    for t in hole_tools:
        cut_tool = cut_tool.fuse(t)
    cut_tool = cut_tool.removeSplitter()
    hub = hub.cut(cut_tool)
    hub = hub.removeSplitter()
    return hub

# =====================================================================
# BRACO (modelado ao longo de +X, angulo 0 - pronto p/ imprimir deitado)
# =====================================================================
def build_arm():
    top_pts, bot_pts = [], []
    for i in range(ARM_SEGMENTS + 1):
        t = i / float(ARM_SEGMENTS)
        r = SHOULDER_R + t * (ARM_TIP_R - SHOULDER_R)
        w = ARM_W_TIP + (ARM_W_ROOT - ARM_W_TIP) * ((1.0 - t) ** 1.6)
        top_pts.append(FreeCAD.Vector(r, w / 2.0, 0.0))
        bot_pts.append(FreeCAD.Vector(r, -w / 2.0, 0.0))

    poly = top_pts + list(reversed(bot_pts)) + [top_pts[0]]
    body = make_prism_from_pts(poly, 0.0, ARM_THK)

    # lingueta (tenon) - entra no rasgo do hub
    hw = TAB_W / 2.0
    tab_pts = [
        FreeCAD.Vector(SHOULDER_R - TAB_DEPTH,  hw, 0.0),
        FreeCAD.Vector(SHOULDER_R - TAB_DEPTH, -hw, 0.0),
        FreeCAD.Vector(SHOULDER_R + 0.5,       -hw, 0.0),
        FreeCAD.Vector(SHOULDER_R + 0.5,        hw, 0.0),
        FreeCAD.Vector(SHOULDER_R - TAB_DEPTH,  hw, 0.0),
    ]
    tab = make_prism_from_pts(tab_pts, 0.0, ARM_THK)
    body = body.fuse(tab)
    body = body.removeSplitter()

    # pad do motor
    tip_c = FreeCAD.Vector(ARM_TIP_R, 0.0, 0.0)
    pad = Part.makeCylinder(MOTOR_PAD_R, ARM_THK, tip_c)
    body = body.fuse(pad)
    body = body.removeSplitter()

    try:
        top_circ = circle_edges(body, ARM_THK, MOTOR_PAD_R)
        if top_circ:
            body = body.makeChamfer(1.2, top_circ)
    except Exception as ex:
        FreeCAD.Console.PrintWarning("Falha no chanfro do pad: %s\n" % ex)

    # friso decorativo no topo (cosmetico) - para antes da base do servo p/ nao criar vazio interno
    servo_r_preview = SHOULDER_R + EFFECTOR_POS_FRAC * (ARM_TIP_R - SHOULDER_R)
    groove_r0 = SHOULDER_R + 12.0
    groove_r1 = min(ARM_TIP_R - MOTOR_PAD_R - 6.0, servo_r_preview - SERVO_BOSS_L / 2.0 - 5.0)
    if groove_r1 > groove_r0:
        g_pts = [
            FreeCAD.Vector(groove_r0,  GROOVE_W / 2.0, 0.0),
            FreeCAD.Vector(groove_r0, -GROOVE_W / 2.0, 0.0),
            FreeCAD.Vector(groove_r1, -GROOVE_W / 2.0, 0.0),
            FreeCAD.Vector(groove_r1,  GROOVE_W / 2.0, 0.0),
            FreeCAD.Vector(groove_r0,  GROOVE_W / 2.0, 0.0),
        ]
        groove = make_prism_from_pts(g_pts, ARM_THK - GROOVE_DEPTH, ARM_THK + 1.0)
        try:
            body = body.cut(groove)
        except Exception as ex:
            FreeCAD.Console.PrintWarning("Falha no friso: %s\n" % ex)

    # base do servo (SG90) - presente nos 6 bracos p/ manter a peca unica/intercambiavel;
    # so 3 recebem efetuador de fato (Secao 4.2 do documento), os outros ficam livres.
    servo_r = SHOULDER_R + EFFECTOR_POS_FRAC * (ARM_TIP_R - SHOULDER_R)
    boss_pts = [
        FreeCAD.Vector(servo_r - SERVO_BOSS_L / 2.0,  SERVO_BOSS_W / 2.0, 0.0),
        FreeCAD.Vector(servo_r - SERVO_BOSS_L / 2.0, -SERVO_BOSS_W / 2.0, 0.0),
        FreeCAD.Vector(servo_r + SERVO_BOSS_L / 2.0, -SERVO_BOSS_W / 2.0, 0.0),
        FreeCAD.Vector(servo_r + SERVO_BOSS_L / 2.0,  SERVO_BOSS_W / 2.0, 0.0),
        FreeCAD.Vector(servo_r - SERVO_BOSS_L / 2.0,  SERVO_BOSS_W / 2.0, 0.0),
    ]
    boss = make_prism_from_pts(boss_pts, ARM_THK, ARM_THK + SERVO_BOSS_H)
    body = body.fuse(boss)
    body = body.removeSplitter()

    # furos: motor (4x M2 padrao quadrado + centro), lingueta (2x M3) e servo (2x M2)
    hole_tools = []
    hole_tools.append(Part.makeCylinder(MOTOR_CENTER_HOLE_D / 2.0, ARM_THK + 4, tip_c + FreeCAD.Vector(0, 0, -2)))
    for sx in (-1, 1):
        for sy in (-1, 1):
            hx = tip_c.x + sx * MOTOR_SQUARE_HALF
            hy = tip_c.y + sy * MOTOR_SQUARE_HALF
            hole_tools.append(Part.makeCylinder(MOTOR_BOLT_HOLE_D / 2.0, ARM_THK + 4, FreeCAD.Vector(hx, hy, -2)))
    for r_bolt in (TAB_BOLT_R1, TAB_BOLT_R2):
        hole_tools.append(Part.makeCylinder(TAB_BOLT_HOLE_D / 2.0, ARM_THK + 4, FreeCAD.Vector(r_bolt, 0.0, -2)))
    for sgn in (-1, 1):
        hx = servo_r + sgn * SERVO_HOLE_SPACING / 2.0
        hole_tools.append(Part.makeCylinder(SERVO_HOLE_D / 2.0, ARM_THK + SERVO_BOSS_H + 4, FreeCAD.Vector(hx, 0.0, -2)))

    holes = hole_tools[0]
    for t in hole_tools[1:]:
        holes = holes.fuse(t)
    holes = holes.removeSplitter()
    body = body.cut(holes)
    body = body.removeSplitter()
    return body

# =====================================================================
# BANDEJA DE ELETRONICA (ESP32-S3 x2 + LoRa x2) - aparafusa no hub
# =====================================================================
def rounded_rect_pts(l, w, chamfer):
    hl, hw = l / 2.0, w / 2.0
    c = chamfer
    return [
        FreeCAD.Vector(-hl + c, -hw, 0), FreeCAD.Vector(hl - c, -hw, 0),
        FreeCAD.Vector(hl, -hw + c, 0),  FreeCAD.Vector(hl, hw - c, 0),
        FreeCAD.Vector(hl - c, hw, 0),   FreeCAD.Vector(-hl + c, hw, 0),
        FreeCAD.Vector(-hl, hw - c, 0),  FreeCAD.Vector(-hl, -hw + c, 0),
        FreeCAD.Vector(-hl + c, -hw, 0),
    ]

def build_rail_bay(cx, cy, board_l, board_w, clearance):
    hw = board_w / 2.0 + clearance
    hl = board_l / 2.0
    rails = []
    for sy in (-1, 1):
        r_pts = [
            FreeCAD.Vector(cx - hl, cy + sy * hw, 0),
            FreeCAD.Vector(cx + hl, cy + sy * hw, 0),
            FreeCAD.Vector(cx + hl, cy + sy * (hw + RAIL_T), 0),
            FreeCAD.Vector(cx - hl, cy + sy * (hw + RAIL_T), 0),
            FreeCAD.Vector(cx - hl, cy + sy * hw, 0),
        ]
        rails.append(make_prism_from_pts(r_pts, TRAY_THK, TRAY_THK + RAIL_H))
    # aba de fim de curso numa ponta
    stop_pts = [
        FreeCAD.Vector(cx - hl, cy - hw - RAIL_T, 0), FreeCAD.Vector(cx - hl + 2.0, cy - hw - RAIL_T, 0),
        FreeCAD.Vector(cx - hl + 2.0, cy + hw + RAIL_T, 0), FreeCAD.Vector(cx - hl, cy + hw + RAIL_T, 0),
        FreeCAD.Vector(cx - hl, cy - hw - RAIL_T, 0),
    ]
    rails.append(make_prism_from_pts(stop_pts, TRAY_THK, TRAY_THK + RAIL_H))
    fused = rails[0]
    for r in rails[1:]:
        fused = fused.fuse(r)

    slots = []
    for sx in (-1, 1):
        slots.append(Part.makeBox(STRAP_SLOT_L, STRAP_SLOT_W, TRAY_THK + 4,
                                   FreeCAD.Vector(cx + sx * (hl * 0.55) - STRAP_SLOT_L / 2.0, cy - STRAP_SLOT_W / 2.0, -2)))
    slot_tool = slots[0].fuse(slots[1])
    return fused.removeSplitter(), slot_tool.removeSplitter()

def build_lora_bay(cx, cy):
    nubs = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            nubs.append(Part.makeCylinder(LORA_NUB_D / 2.0, LORA_NUB_H,
                                           FreeCAD.Vector(cx + sx * LORA_BAY_L / 2.0, cy + sy * LORA_BAY_W / 2.0, TRAY_THK)))
    fused = nubs[0]
    for n in nubs[1:]:
        fused = fused.fuse(n)
    slots = []
    for sy in (-1, 1):
        slots.append(Part.makeBox(STRAP_SLOT_W, STRAP_SLOT_L, TRAY_THK + 4,
                                   FreeCAD.Vector(cx - STRAP_SLOT_W / 2.0, cy + sy * (LORA_BAY_W * 0.55) - STRAP_SLOT_L / 2.0, -2)))
    slot_tool = slots[0].fuse(slots[1])
    return fused.removeSplitter(), slot_tool.removeSplitter()

def build_tray():
    base_pts = rounded_rect_pts(TRAY_L, TRAY_W, TRAY_CHAMFER)
    tray = make_prism_from_pts(base_pts, 0.0, TRAY_THK)

    esp32_y = ESP32_W / 2.0 + ESP32_CLEARANCE + RAIL_T + 4.0
    rails1, slots1 = build_rail_bay(-6.0, esp32_y, ESP32_L, ESP32_W, ESP32_CLEARANCE)
    rails2, slots2 = build_rail_bay(-6.0, -esp32_y, ESP32_L, ESP32_W, ESP32_CLEARANCE)
    tray = tray.fuse(rails1).fuse(rails2)
    tray = tray.removeSplitter()

    lora_x = TRAY_L / 2.0 - LORA_BAY_L / 2.0 - 6.0
    lora1, lslots1 = build_lora_bay(lora_x, 0.0)
    lora2, lslots2 = build_lora_bay(-lora_x, 0.0)
    tray = tray.fuse(lora1).fuse(lora2)
    tray = tray.removeSplitter()

    hole_tools = [slots1, slots2, lslots1, lslots2]
    for k in range(4):
        a = math.radians(45 + 90 * k)
        hx, hy = STANDOFF_R * math.cos(a), STANDOFF_R * math.sin(a)
        hole_tools.append(Part.makeCylinder(STANDOFF_HOLE_D / 2.0, TRAY_THK + RAIL_H + 4, FreeCAD.Vector(hx, hy, -2)))
    holes = hole_tools[0]
    for t in hole_tools[1:]:
        holes = holes.fuse(t)
    holes = holes.removeSplitter()
    tray = tray.cut(holes)
    tray = tray.removeSplitter()
    return tray

# =====================================================================
# GERACAO
# =====================================================================
hub_shape = build_hub()
arm_shape = build_arm()
tray_shape = build_tray()

doc = FreeCAD.newDocument("SkyVolt_Hub")
obj = doc.addObject("Part::Feature", "SkyVolt_Hub")
obj.Shape = hub_shape
doc.recompute()
doc.saveAs(os.path.join(out_dir, "SkyVolt_Hub.FCStd"))
Part.export([obj], os.path.join(out_dir, "SkyVolt_Hub.stl"))
Part.export([obj], os.path.join(out_dir, "SkyVolt_Hub.step"))
hub_bbox = hub_shape.BoundBox
hub_vol = hub_shape.Volume
print("HUB volume mm3:", hub_vol, " bbox:", hub_bbox.XLength, hub_bbox.YLength, hub_bbox.ZLength)

doc2 = FreeCAD.newDocument("SkyVolt_Arm")
obj2 = doc2.addObject("Part::Feature", "SkyVolt_Arm")
obj2.Shape = arm_shape
doc2.recompute()
doc2.saveAs(os.path.join(out_dir, "SkyVolt_Arm.FCStd"))
Part.export([obj2], os.path.join(out_dir, "SkyVolt_Arm.stl"))
Part.export([obj2], os.path.join(out_dir, "SkyVolt_Arm.step"))
arm_bbox = arm_shape.BoundBox
arm_vol = arm_shape.Volume
print("ARM volume mm3:", arm_vol, " bbox:", arm_bbox.XLength, arm_bbox.YLength, arm_bbox.ZLength)

doc4 = FreeCAD.newDocument("SkyVolt_Tray")
obj4 = doc4.addObject("Part::Feature", "SkyVolt_Tray")
obj4.Shape = tray_shape
doc4.recompute()
doc4.saveAs(os.path.join(out_dir, "SkyVolt_Tray.FCStd"))
Part.export([obj4], os.path.join(out_dir, "SkyVolt_Tray.stl"))
Part.export([obj4], os.path.join(out_dir, "SkyVolt_Tray.step"))
tray_bbox = tray_shape.BoundBox
tray_vol = tray_shape.Volume
print("TRAY volume mm3:", tray_vol, " bbox:", tray_bbox.XLength, tray_bbox.YLength, tray_bbox.ZLength)

# preview de montagem (compound, so visual/conferencia - nao e a peca de impressao)
doc3 = FreeCAD.newDocument("SkyVolt_Assembly_Preview")
hub_obj = doc3.addObject("Part::Feature", "Hub")
hub_obj.Shape = hub_shape
arm_shapes_positioned = []
for i in range(N_ARMS):
    angle = 60.0 * i
    a_obj = doc3.addObject("Part::Feature", "Arm_%d" % i)
    rot = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), angle)
    a_obj.Shape = arm_shape.copy()
    a_obj.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), rot)
    arm_shapes_positioned.append(a_obj.Shape.copy())
    arm_shapes_positioned[-1].Placement = a_obj.Placement
STANDOFF_GAP = 12.0  # altura da coluna/standoff entre hub e bandeja (nao modelada, comprada pronta)
tray_positioned = tray_shape.copy()
tray_positioned.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, HUB_THK + STANDOFF_GAP), FreeCAD.Rotation())
tray_obj = doc3.addObject("Part::Feature", "Tray")
tray_obj.Shape = tray_positioned
doc3.recompute()
doc3.saveAs(os.path.join(out_dir, "SkyVolt_Assembly_Preview.FCStd"))

compound = Part.makeCompound([hub_shape, tray_positioned] + arm_shapes_positioned)
prev_obj = doc3.addObject("Part::Feature", "PreviewCompound")
prev_obj.Shape = compound
doc3.recompute()
Part.export([prev_obj], os.path.join(out_dir, "SkyVolt_Assembly_Preview.stl"))

total_frame_g_petg = (hub_vol + N_ARMS * arm_vol + tray_vol) / 1000.0 * 1.27
print("PESO TOTAL FRAME (100%% infill PETG) g:", total_frame_g_petg)
print("BED CHECK hub (mm):", hub_bbox.XLength, "x", hub_bbox.YLength, " <= 220x220 ?", hub_bbox.XLength <= 220 and hub_bbox.YLength <= 220)
print("BED CHECK arm (mm):", arm_bbox.XLength, "x", arm_bbox.YLength, " <= 220x220 ?", arm_bbox.XLength <= 220 and arm_bbox.YLength <= 220)
print("BED CHECK tray (mm):", tray_bbox.XLength, "x", tray_bbox.YLength, " <= 220x220 ?", tray_bbox.XLength <= 220 and tray_bbox.YLength <= 220)

print("OK")
