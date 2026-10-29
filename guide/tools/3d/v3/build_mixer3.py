# ATARIA AT-SM23 — model v3, measured on the owner's straight front photo (ref-front.jpg: 44 cm = 895 px).
# 1 unit = 1 cm. X: width (bowl left, column right). Y: depth (front = -Y). Z: up.
# Usage: python build_mixer3.py -- OUT VIEW [SAMPLES]
#   VIEW = front | front34 | back34 | end | side | top | dial | glb | blend
import bpy, bmesh, math, sys, os
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = args[0] if args else "/tmp/r.png"
VIEW = args[1] if len(args) > 1 else "front34"
SAMPLES = int(args[2]) if len(args) > 2 else 48
TEX = os.path.dirname(os.path.abspath(__file__))

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
prod = bpy.data.collections.new("product"); sc.collection.children.link(prod)
studio = bpy.data.collections.new("studio"); sc.collection.children.link(studio)
COL = [prod]

def link(o):
    for c in o.users_collection: c.objects.unlink(o)
    COL[0].objects.link(o)
    return o

# ---------- materials ----------
def mat(name, color, metal=0.0, rough=0.5, trans=0.0, ior=1.45, coat=0.0, emit=None, alpha=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    b.inputs["Transmission Weight"].default_value = trans
    b.inputs["IOR"].default_value = ior
    b.inputs["Coat Weight"].default_value = coat
    if alpha < 1: b.inputs["Alpha"].default_value = alpha; m.blend_method = "BLEND"
    if emit: b.inputs["Emission Color"].default_value = (*emit, 1); b.inputs["Emission Strength"].default_value = 1.0
    return m

GRAPHITE = mat("graphite", (0.045, 0.045, 0.048), rough=0.55, coat=0.05)
DARK = mat("dark", (0.012, 0.012, 0.013), rough=0.6)
STEEL = mat("steel", (0.9, 0.9, 0.91), metal=1.0, rough=0.1)
CHROME = mat("chrome", (0.96, 0.96, 0.97), metal=1.0, rough=0.035)
SATIN = mat("satin", (0.62, 0.63, 0.64), metal=1.0, rough=0.38)  # matte-silver display frame
CLEAR = mat("clear", (0.97, 0.98, 1.0), rough=0.02, trans=1.0, ior=1.49)
GLASS = mat("glass", (0.004, 0.004, 0.006), rough=0.05, coat=1.0)

def tex_mat(name, img, rough=0.45, metal=0.0, emit=False, alpha=True):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(os.path.join(TEX, img))
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    if alpha: nt.links.new(t.outputs["Alpha"], b.inputs["Alpha"]); m.blend_method = "BLEND"
    if emit:
        nt.links.new(t.outputs["Color"], b.inputs["Emission Color"]); b.inputs["Emission Strength"].default_value = 1.6
    b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal
    return m

def smooth(o):
    for p in o.data.polygons: p.use_smooth = True

def decal(name, img, w, h, loc, rot=(math.radians(90), 0, 0), **kw):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object; o.name = name; o.scale = (w, h, 1)
    bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(tex_mat(name, img, **kw))
    return link(o)

def cyl(name, r, h, loc, rot=(0, 0, 0), material=STEEL, verts=128, bev=0.0):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=loc, rotation=rot, vertices=verts)
    o = bpy.context.object; o.name = name; o.data.materials.append(material); smooth(o)
    if bev:
        md = o.modifiers.new("b", "BEVEL"); md.width = bev; md.segments = 4; md.limit_method = "ANGLE"
    return link(o)

def box(name, size, loc, material=GRAPHITE, bev=0.0, segs=6):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(material)
    if bev:
        md = o.modifiers.new("b", "BEVEL"); md.width = bev; md.segments = segs; smooth(o)
    return link(o)

def rounded_poly(pts, radii, seg=14):
    out = []; n = len(pts)
    for i in range(n):
        p0, p1, p2 = Vector(pts[i - 1]), Vector(pts[i]), Vector(pts[(i + 1) % n]); r = radii[i]
        if r <= 0: out.append(p1); continue
        a = (p0 - p1).normalized(); b = (p2 - p1).normalized(); ang = a.angle(b)
        t = r / math.tan(ang / 2); s1 = p1 + a * t; s2 = p1 + b * t
        c = p1 + (a + b).normalized() * (r / math.sin(ang / 2))
        a1 = math.atan2((s1 - c).y, (s1 - c).x); a2 = math.atan2((s2 - c).y, (s2 - c).x); da = a2 - a1
        while da > math.pi: da -= math.tau
        while da < -math.pi: da += math.tau
        for k in range(seg + 1):
            aa = a1 + da * k / seg; out.append(c + Vector((math.cos(aa), math.sin(aa))) * r)
    return out

def slab(name, outline, z0, z1, edge, material=GRAPHITE, plane="xy", y0=None, y1=None):
    # outline: list of 2D points. plane "xy": extrude along Z from z0 to z1. plane "xz": extrude along Y from y0 to y1.
    me = bpy.data.meshes.new(name); o = bpy.data.objects.new(name, me); sc.collection.objects.link(o)
    bm = bmesh.new()
    if plane == "xy": vs = [bm.verts.new((v[0], v[1], z0)) for v in outline]
    else: vs = [bm.verts.new((v[0], y0, v[1])) for v in outline]
    f = bm.faces.new(vs)
    r = bmesh.ops.extrude_face_region(bm, geom=[f])
    for v in [e for e in r["geom"] if isinstance(e, bmesh.types.BMVert)]:
        if plane == "xy": v.co.z = z1
        else: v.co.y = y1
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    o.data.materials.append(material)
    if edge:
        md = o.modifiers.new("bev", "BEVEL"); md.width = edge; md.segments = 8; md.limit_method = "ANGLE"; md.angle_limit = math.radians(50)
    o.modifiers.new("wn", "WEIGHTED_NORMAL"); smooth(o)
    return link(o)

def plan_rect(x0, x1, y0, y1, r):
    return rounded_poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], r if isinstance(r, (list, tuple)) else [r] * 4)

def lathe(name, profile, loc, material=STEEL, thick=0.22, sub=2):
    me = bpy.data.meshes.new(name); o = bpy.data.objects.new(name, me); sc.collection.objects.link(o)
    bm = bmesh.new(); vs = [bm.verts.new((r, 0, z)) for r, z in profile]
    for a, b in zip(vs, vs[1:]): bm.edges.new((a, b))
    bmesh.ops.spin(bm, geom=bm.verts[:] + bm.edges[:], cent=(0, 0, 0), axis=(0, 0, 1), angle=math.tau, steps=160)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4); bm.to_mesh(me); bm.free()
    o.location = loc; o.data.materials.append(material)
    if thick: o.modifiers.new("s", "SOLIDIFY").thickness = thick
    if sub: o.modifiers.new("sub", "SUBSURF").levels = sub
    smooth(o)
    return link(o)

def tube(name, pts, r, material=CHROME):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = r; cu.bevel_resolution = 6
    sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1)
    for p, q in zip(sp.points, pts): p.co = (*q, 1)
    o = bpy.data.objects.new(name, cu); sc.collection.objects.link(o); o.data.materials.append(material)
    bpy.context.view_layer.objects.active = o; o.select_set(True); bpy.ops.object.convert(target="MESH"); o.select_set(False)
    smooth(o)
    return link(o)

def fillet_xz(name, cx, cz, r, quadrant, y0, y1):
    # concave fillet block in the XZ plane: square r x r at corner (cx, cz) minus a quarter circle; quadrant = (sx, sz)
    sx, sz = quadrant; pts = [(cx, cz)]
    for k in range(17):
        a = math.pi / 2 * k / 16
        pts.append((cx + sx * r - sx * r * math.sin(a), cz + sz * r - sz * r * math.cos(a)))
    return slab(name, pts, 0, 0, 0, plane="xz", y0=y0, y1=y1)

# ---------- dimensions (cm) ----------
W = 44.0                 # base width
HD = 19.0                # head and column depth
FY = -HD / 2             # front face
BX = 10.8                # bowl / hub axis
CX0, CX1 = 25.6, 42.4    # column left / right
HZ0, HZ1 = 32.5, 42.4    # head underside / top of head body (cap above)

# base: rounded plan, soft edges; raised seat ring for the bowl
slab("base", plan_rect(0, W, -11.6, 11.6, 4.5), 0, 4.7, 1.9)
cyl("base_foot", 1.0, 0.25, (4, -8, 0.0), material=DARK, verts=32)
lathe("seat", [(7.0, 4.65), (9.8, 4.7), (10.3, 5.0), (9.9, 5.3), (7.4, 5.35)], (BX, 0, 0), material=GRAPHITE, thick=0, sub=1)

# body: column + head as one piece. Side profile (XZ) intersected with the plan shape (XY): rounded ends like photo 035.
prof = [(CX0, 4.6), (CX1, 4.6), (CX1, 31.4), (43.6, 32.8), (43.6, 44.6), (0.7, 44.6), (0.7, HZ0), (CX0, HZ0)]
body = slab("body", rounded_poly(prof, [0, 0, 1.0, 1.0, 1.4, 1.4, 1.6, 4.0]), 0, 0, 0, plane="xz", y0=-HD / 2, y1=HD / 2)
body.modifiers.clear()
plan = slab("plan", rounded_poly([(0.7, -HD / 2), (43.6, -HD / 2), (43.6, HD / 2), (0.7, HD / 2)], [6.0, 3.2, 3.2, 6.0]), 0, 50, 0)
plan.modifiers.clear()
md = body.modifiers.new("i", "BOOLEAN"); md.operation = "INTERSECT"; md.object = plan; md.solver = "EXACT"
bpy.context.view_layer.objects.active = body; bpy.ops.object.modifier_apply(modifier=md.name); bpy.data.objects.remove(plan)
md = body.modifiers.new("bev", "BEVEL"); md.width = 1.3; md.segments = 8; md.limit_method = "ANGLE"; md.angle_limit = math.radians(40)
body.modifiers.new("wn", "WEIGHTED_NORMAL"); smooth(body)
fb = fillet_xz("fillet_base", CX0 + 0.02, 4.55, 4.5, (-1, 1), -HD / 2 + 0.5, HD / 2 - 0.5)
md = fb.modifiers.new("bev", "BEVEL"); md.width = 0.8; md.segments = 6; md.limit_method = "ANGLE"; md.angle_limit = math.radians(40)
# tilt seam around the column and the cap seam
slab("seam_tilt", rounded_poly([(CX0 + 0.3, -HD / 2 - 0.03), (CX1 + 0.03, -HD / 2 - 0.03), (CX1 + 0.03, HD / 2 + 0.03), (CX0 + 0.3, HD / 2 + 0.03)], [0, 3.2, 3.2, 0]), 21.5, 21.68, 0, material=DARK)
# top cap is flush with the body: only a thin seam runs round the head at z 42.4 (photos 034/035)
slab("seam_cap", rounded_poly([(0.68, -HD / 2 - 0.02), (43.62, -HD / 2 - 0.02), (43.62, HD / 2 + 0.02), (0.68, HD / 2 + 0.02)], [6.0, 3.2, 3.2, 6.0]), HZ1 - 0.08, HZ1 + 0.08, 0, material=DARK)
# separate rear lid over the column: flush, seen only as a seam across the top
# rear top lid = cover of the blender socket (owner's photo 019): the whole rear part of the top cap from x 25 to the end,
# flush with the cap; seen only as a seam across the top that runs down both sides to the cap seam
RLX = 26.2
box("seam_rear", (0.14, HD + 0.06, 44.66 - HZ1), (RLX, 0, (44.66 + HZ1) / 2), material=DARK)
# the port cover reaches over the top edge: short seams on the top surface at the bowl end
box("seam_port_c", (0.14, 8.4, 0.04), (2.3, 0, 44.6), material=DARK)
for yy in (-4.2, 4.2): box(f"seam_port_{yy}", (1.6, 0.14, 0.04), (1.5, yy, 44.6), material=DARK)

# planetary hub under the head
cyl("hub", 7.4, 2.3, (BX, 0, HZ0 - 1.1), material=GRAPHITE, bev=0.5)
cyl("hub_ring", 6.3, 0.8, (BX, 0, 29.9), material=DARK)
cyl("shaft", 1.0, 2.2, (BX, 0, 28.6), material=STEEL, verts=48)

# port cover on the bowl end of the head (photo 034/041): U outline, two lines and a triangle
decal("port", "port.png", 8.4, 7.8, (0.7 - 0.03, 0, 38.9), rot=(math.radians(90), 0, math.radians(-90)), rough=0.5)

# ---------- bowl 7 L: r 13.5, from z 5.5 to 28, sticks out past the head end ----------
lathe("bowl", [(0.01, 5.6), (7.6, 5.8), (10.9, 8.6), (12.9, 13.0), (13.5, 18.5), (13.5, 24.2), (13.7, 27.3), (14.05, 27.85), (14.05, 28.05)], (BX, 0, 0), thick=0.18)
lathe("bowl_foot", [(7.0, 4.9), (8.4, 5.0), (8.8, 6.2), (7.4, 6.4)], (BX, 0, 0), material=DARK, thick=0, sub=1)
# riveted handles front and back: wide arcs (+-45 deg) standing 1.6 cm off the wall at z 23.5
for side in (-1, 1):
    pts = []
    for k in range(41):
        t = -1 + 2 * k / 40; a = math.radians(45) * t
        rr = 13.75 + 1.65 * (1 - abs(t) ** 6) ** 0.5
        zz = 23.5 + 0.15 * (1 - t * t)
        pts.append((BX + rr * math.sin(a), side * rr * math.cos(a), zz))
    tube(f"handle{side}", pts, 0.42)
    for t in (-1, 1):
        a = math.radians(45) * t; rr = 13.6
        p = box(f"rivet{side}{t}", (1.4, 0.45, 2.4), (BX + rr * math.sin(a), side * rr * math.cos(a), 23.5), material=CHROME, bev=0.15)
        p.rotation_euler = (0, 0, -a if side > 0 else a)
        for dz in (-0.6, 0.6):
            cyl(f"rv{side}{t}{dz}", 0.18, 0.2, (BX + (rr + 0.25) * math.sin(a), side * (rr + 0.25) * math.cos(a), 23.5 + dz), rot=(math.radians(90), 0, -a if side > 0 else a), material=STEEL, verts=16)

# clear splash guard with feed chute at front-left
lathe("lid", [(7.7, 30.25), (10.2, 29.95), (12.9, 29.25), (14.25, 28.45), (14.35, 27.85)], (BX, 0, 0), material=CLEAR, thick=0.25)
# feed chute faces the bowl end of the machine (photo 035): an open trapezoid frame on the lid edge
cpts = [(8.5, -6.6), (15.4, -5.6), (16.3, -4.0), (16.3, 4.0), (15.4, 5.6), (8.5, 6.6)]
ch = slab("chute", [(BX - u, v) for u, v in reversed(cpts)], 28.2, 31.0, 0, material=CLEAR)
inner = slab("chute_in", [(BX - u, v) for u, v in reversed([(8.1, -6.2), (15.0, -5.25), (15.9, -3.7), (15.9, 3.7), (15.0, 5.25), (8.1, 6.2)])], 27.0, 32.0, 0, material=CLEAR)
ch.modifiers.clear(); inner.modifiers.clear()
md = ch.modifiers.new("d", "BOOLEAN"); md.operation = "DIFFERENCE"; md.object = inner; md.solver = "EXACT"
bpy.context.view_layer.objects.active = ch; bpy.ops.object.modifier_apply(modifier=md.name); bpy.data.objects.remove(inner)
md = ch.modifiers.new("bev", "BEVEL"); md.width = 0.12; md.segments = 3

# ---------- controls on the column front ----------
DXc = 36.1
fr = box("display_frame", (7.6, 0.55, 5.6), (DXc, FY - 0.2, 28.8), material=SATIN, bev=0.7, segs=8)
gl = box("display_glass", (6.7, 0.5, 4.7), (DXc, FY - 0.35, 28.8), material=GLASS, bev=0.35)
decal("display", "display3.png", 6.5, 6.5 * 1000 / 1400, (DXc, FY - 0.62, 28.8), rough=0.1, emit=True, alpha=False)

# lever: chrome "comma" with a ring pivot, open-padlock mark below (photo 037)
LX, LZ = 33.0, 18.3
cyl("lever_ring", 1.05, 0.9, (LX, FY - 0.45, LZ), rot=(math.radians(90), 0, 0), material=CHROME, verts=64, bev=0.25)
cyl("lever_hole", 0.62, 0.4, (LX, FY - 0.95, LZ), rot=(math.radians(90), 0, 0), material=DARK, verts=48)
arm = [(LX + 0.6, LZ + 0.95), (LX + 2.6, LZ + 0.55), (LX + 3.8, LZ - 0.3), (LX + 4.1, LZ - 1.35), (LX + 3.7, LZ - 1.4), (LX + 2.6, LZ - 0.55), (LX + 0.6, LZ - 0.9)]
slab("lever_arm", rounded_poly(arm, [0.3, 1.5, 1.0, 0.35, 0.3, 1.2, 0.3], seg=8), 0, 0, 0.25, material=CHROME, plane="xz", y0=FY - 0.15, y1=FY - 0.85)
decal("lock", "lock.png", 3.2, 3.2 * 400 / 700, (LX + 0.9, FY - 0.02, LZ - 2.6), rough=0.5)

# speed dial: satin-chrome dish with the real number ring, knurled knob, brushed cap (photos 006/037)
DX, DZ = 35.6, 10.3
cyl("dial_dish", 4.15, 0.7, (DX, FY - 0.3, DZ), rot=(math.radians(90), 0, 0), material=CHROME, verts=160, bev=0.3)
decal("dial_ring", "dial_ring.png", 8.1, 8.1, (DX, FY - 0.67, DZ), rough=0.15, metal=0.0)
teeth = []
for k in range(180):
    a = math.tau * k / 180; rr = 2.95 if k % 2 == 0 else 2.78
    teeth.append((DX + rr * math.cos(a), DZ + rr * math.sin(a)))
slab("dial_knurl", teeth, 0, 0, 0.0, material=CHROME, plane="xz", y0=FY - 0.6, y1=FY - 2.7)
cyl("dial_cap", 3.0, 0.45, (DX, FY - 2.85, DZ), rot=(math.radians(90), 0, 0), material=STEEL, verts=160, bev=0.15)
decal("dial_face", "dial_cap.png", 5.9, 5.9, (DX, FY - 3.09, DZ), rough=0.2, metal=0.0)

# ---------- head decals: logo and the three speed pills ----------
decal("logo", "logo.png", 8.1, 8.1 * 297 / 2367, (21.5, FY - 0.02, 38.2), rough=0.4)
decal("icons", "icons.png", 5.2, 5.2 * 902 / 806, (36.3, FY - 0.02, 36.45), rough=0.4)

# ---------- attachment scenes ----------
if VIEW in ("tools", "blender", "grinder"):
    exec(open(os.path.join(TEX, "attachments.py")).read())
if VIEW == "tools":
    # hook, whisk and beater standing on the plinth in front of the machine, collars up
    # stand each tool upside down on its collar, like the factory photos 053-055
    for fn, (x, y), turn in ((make_hook, (-9.0, -25.0), 30), (make_whisk, (3.5, -30.0), 0), (make_beater, (16.5, -26.0), -25)):
        objs = fn(x, y, 0.0)
        e = bpy.data.objects.new("stand", None); prod.objects.link(e); e.location = (x, y, 0.0); bpy.context.view_layer.update()
        for o in objs:
            o.parent = e; o.matrix_parent_inverse = e.matrix_world.inverted()
        e.rotation_euler = (math.radians(180), 0, math.radians(turn))
if VIEW == "blender":
    # rear lid removed: open well with the drive socket, jar seated in it
    b = bpy.data.objects["body"]
    cut = slab("well_cut", rounded_poly([(RLX + 0.5, -HD / 2 + 0.7), (42.9, -HD / 2 + 0.7), (42.9, HD / 2 - 0.7), (RLX + 0.5, HD / 2 - 0.7)], [0.4, 2.6, 2.6, 0.4]), 43.0, 47.0, 0)
    cut.modifiers.clear()
    md = b.modifiers.new("well", "BOOLEAN"); md.operation = "DIFFERENCE"; md.object = cut; md.solver = "EXACT"
    b.modifiers.move(len(b.modifiers) - 1, 0)
    cut.hide_render = True; cut.hide_viewport = True
    bpy.data.objects["seam_rear"].hide_render = True
    cyl("socket_ring", 6.4, 0.6, (35.0, 0, 43.3), material=DARK, verts=96)
    cyl("socket_drive", 1.1, 0.9, (35.0, 0, 43.6), material=STEEL, verts=12)
    make_blender(35.0, 0, 43.0)
if VIEW == "grinder":
    bpy.data.objects["port"].hide_render = True
    cyl("port_socket", 2.2, 0.6, (0.5, 0, 38.9), rot=(0, math.radians(90), 0), material=DARK, verts=64)
    make_grinder(0.6, 38.9)

# ---------- "work" animation: head lowers, dial turns to speed 2, dough hook spins (owner's product video) ----------
if VIEW == "work":
    def apply_all(o):
        bpy.context.view_layer.objects.active = o
        for m in list(o.modifiers): bpy.ops.object.modifier_apply(modifier=m.name)
    # split the one-piece body along the tilt seam: the upper part (head + top of the column) tilts
    b = bpy.data.objects["body"]; apply_all(b)
    up = b.copy(); up.data = b.data.copy(); up.name = "body_up"; prod.objects.link(up)
    for o, keep_up in ((b, False), (up, True)):
        bm = bmesh.new(); bm.from_mesh(o.data)
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, 21.6), plane_no=(0, 0, 1), clear_inner=keep_up, clear_outer=not keep_up)
        bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary])
        bm.to_mesh(o.data); bm.free()
    HX, HZ = CX1 - 1.2, 21.6       # hinge at the back of the tilt seam
    hinge = bpy.data.objects.new("hinge", None); prod.objects.link(hinge); hinge.location = (HX, 0, HZ); bpy.context.view_layer.update()
    lower = {"body", "base", "base_foot", "seat", "fillet_base", "seam_tilt", "bowl", "bowl_foot", "lever_ring", "lever_hole", "lever_arm", "lock",
             "dial_dish", "dial_ring", "dial_knurl", "dial_cap", "dial_face"}
    lower |= {o.name for o in prod.objects if o.name.startswith(("handle", "rivet", "rv"))}
    # dough hook: collar with a guard disc, bar out and down in an S, flat tip (photo 055, in working position)
    hk = []
    for k in range(31):
        t = k / 30
        x = 2.2 * math.sin(math.pi * t * 0.9) + 0.8 * t; z = 27.6 - 15.5 * t; yv = 0.6 * math.sin(math.pi * t)
        hk.append((BX + 1.6 + x, yv, z))
    hk += [(hk[-1][0] + 1.2, 0.2, hk[-1][2] - 0.5), (hk[-1][0] + 2.6, 0.0, hk[-1][2] - 0.4)]
    COL[0] = prod
    hook = tube("hook", hk, 0.55, material=STEEL)
    cyl("hook_collar", 1.25, 2.0, (BX + 1.6, 0, 28.4), material=STEEL, verts=48)
    cyl("hook_disc", 3.6, 0.15, (BX + 1.6, 0, 27.5), material=STEEL, verts=96)
    spin = bpy.data.objects.new("spin", None); prod.objects.link(spin); spin.location = (BX + 1.6, 0, 27.5); bpy.context.view_layer.update()
    for n in ("hook", "hook_collar", "hook_disc"):
        o = bpy.data.objects[n]; o.parent = spin; o.matrix_parent_inverse = spin.matrix_world.inverted()
    orbit = bpy.data.objects.new("planet", None); prod.objects.link(orbit); orbit.location = (BX, 0, 27.5); bpy.context.view_layer.update()
    spin.parent = orbit; spin.matrix_parent_inverse = orbit.matrix_world.inverted()
    orbit.parent = hinge; orbit.matrix_parent_inverse = hinge.matrix_world.inverted(); bpy.context.view_layer.update()
    for o in list(prod.objects):
        if o.type in ("MESH",) and o.name not in lower and o.parent is None:
            o.parent = hinge; o.matrix_parent_inverse = hinge.matrix_world.inverted()
    # knob rotates about its own axis (Y); pointer steps P(-36) 0(0) 1(36) 2(72) deg clockwise
    knob = bpy.data.objects.new("knob", None); prod.objects.link(knob); knob.location = (DX, FY, DZ); bpy.context.view_layer.update()
    for n in ("dial_knurl", "dial_cap", "dial_face"):
        o = bpy.data.objects[n]; o.parent = knob; o.matrix_parent_inverse = knob.matrix_world.inverted()
    def key(o, prop, frame, val, interp="BEZIER"):
        setattr(o, prop, val); o.keyframe_insert(prop, frame=frame)
    key(hinge, "rotation_euler", 1, (0, math.radians(44), 0)); key(hinge, "rotation_euler", 18, (0, math.radians(44), 0))
    key(hinge, "rotation_euler", 52, (0, 0, 0))
    key(knob, "rotation_euler", 1, (0, 0, 0)); key(knob, "rotation_euler", 62, (0, 0, 0)); key(knob, "rotation_euler", 82, (0, math.radians(72), 0))
    key(orbit, "rotation_euler", 84, (0, 0, 0)); key(orbit, "rotation_euler", 168, (0, 0, math.radians(-300)))
    key(spin, "rotation_euler", 84, (0, 0, 0)); key(spin, "rotation_euler", 168, (0, 0, math.radians(900)))
    for o in (orbit, spin):
        for fc in o.animation_data.action.fcurves:
            kp = fc.keyframe_points; kp[0].interpolation = "BEZIER"; kp[0].easing = "EASE_IN"
            kp[0].handle_right_type = "AUTO"
    for o in (hinge, knob):
        for fc in o.animation_data.action.fcurves:
            for kp in fc.keyframe_points: kp.interpolation = "SINE"; kp.easing = "EASE_IN_OUT"

# ---------- export / studio ----------
if VIEW == "glb":
    # glTF is in metres: scale the product from cm, centred on the base footprint
    bpy.ops.object.select_all(action="DESELECT")
    for o in prod.all_objects: o.select_set(True)
    bpy.context.view_layer.objects.active = prod.all_objects[0]
    bpy.ops.object.convert(target="MESH")  # bake bevels/solidify/subsurf at cm scale first
    for o in prod.all_objects: o.location.x -= W / 2
    sc.cursor.location = (0, 0, 0)
    bpy.ops.transform.resize(value=(0.01, 0.01, 0.01), center_override=(0, 0, 0))
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", use_selection=True, export_apply=True,
                              export_yup=True, export_image_format="AUTO")
    print("exported", OUT); sys.exit(0)

COL[0] = studio
floor = box("floor", (800, 800, 1), (22, 0, -4.0), material=mat("floor", (0.40, 0.355, 0.32), rough=0.6))
cyl("plinth", 36, 3.5, (22, 0, -1.75), material=mat("stone", (0.46, 0.41, 0.37), rough=0.85), verts=192)
wallm = mat("wall", (0.54, 0.48, 0.43), rough=0.92)
for i in range(150):
    a = math.radians(-180 + i * 2.4)
    cyl(f"fl{i}", 1.7, 170, (22 + 140 * math.sin(a), 140 * math.cos(a), 80), material=wallm, verts=20)
# solid backing behind the flutes so nothing shows through the gaps
bk = lathe("wall_back", [(143.5, -4), (143.5, 170)], (22, 0, 0), material=wallm, thick=0, sub=0)

def aim(o, tgt): o.rotation_euler = (Vector(tgt) - o.location).to_track_quat("-Z", "Y").to_euler()
def light(loc, e, size, col=(1, 1, 1), tgt=(22, 0, 22)):
    bpy.ops.object.light_add(type="AREA", location=loc); l = bpy.context.object
    l.data.energy = e; l.data.size = size; l.data.color = col; aim(l, tgt); return l
light((-60, -110, 90), 300000, 120, (1.0, 0.93, 0.84))
light((120, -60, 60), 120000, 140, (0.96, 0.97, 1.0))
light((20, 90, 120), 120000, 90)
world = bpy.data.worlds.new("w"); sc.world = world; world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.36, 0.32, 0.29, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.35

cams = {
    "front": ((22.9, -300, 27.6), (22.9, 0, 27.6), 0),       # orthographic, matched to ref-front.jpg
    "front34": ((-30, -105, 45), (22, 0, 22), 50),
    "back34": ((80, 95, 50), (22, 0, 22), 50),
    "end": ((-120, 0, 26), (22, 0, 24), 60),
    "side": ((140, -8, 26), (22, 0, 24), 60),
    "top": ((22, -0.01, 150), (22, 0, 20), 45),
    "dial": ((44, -38, 16), (DX, FY, 12), 85),
    "tools": ((-10, -110, 40), (12, -10, 22), 45),
    "blender": ((-30, -100, 62), (24, 0, 36), 45),
    "grinder": ((-60, -95, 50), (8, 0, 30), 45),
}
loc, tgt, lens = cams.get(VIEW, cams["front34"])
bpy.ops.object.camera_add(location=loc); cam = bpy.context.object; sc.camera = cam; aim(cam, tgt)
sc.render.resolution_x, sc.render.resolution_y = 1200, 1500
if VIEW == "front":
    cam.data.type = "ORTHO"; cam.data.ortho_scale = 1600 / 20.34; sc.render.resolution_x, sc.render.resolution_y = 1200, 1600
    for o in studio.objects: o.hide_render = o.name.startswith("fl") or o.name == "plinth"
else:
    cam.data.lens = lens
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = SAMPLES; sc.cycles.use_denoising = True
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"
# ---------- photoreal pass (REAL=1): studio HDRI, micro-surface materials, depth of field, motion blur ----------
REAL = os.environ.get("REAL") == "1"
def node_noise(nt, scale, detail=4, coord="Object"):
    tc = nt.nodes.new("ShaderNodeTexCoord"); n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = scale; n.inputs["Detail"].default_value = detail
    nt.links.new(tc.outputs[coord], n.inputs["Vector"]); return n
def add_bump(m, scale, strength, dist=0.02):
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]; n = node_noise(nt, scale, 6)
    bu = nt.nodes.new("ShaderNodeBump"); bu.inputs["Strength"].default_value = strength; bu.inputs["Distance"].default_value = dist
    nt.links.new(n.outputs["Fac"], bu.inputs["Height"]); nt.links.new(bu.outputs["Normal"], b.inputs["Normal"])
def vary_rough(m, scale, lo, hi):
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]; n = node_noise(nt, scale, 3)
    mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["To Min"].default_value = lo; mr.inputs["To Max"].default_value = hi
    nt.links.new(n.outputs["Fac"], mr.inputs["Value"]); nt.links.new(mr.outputs["Result"], b.inputs["Roughness"])
def vary_color(m, scale, c1, c2):
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]; n = node_noise(nt, scale, 5)
    cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (*c1, 1); cr.color_ramp.elements[1].color = (*c2, 1)
    nt.links.new(n.outputs["Fac"], cr.inputs["Fac"]); nt.links.new(cr.outputs["Color"], b.inputs["Base Color"])
if REAL and os.environ.get("HALF"): sc.render.resolution_percentage = 50
if REAL:
    # warm taupe studio, as on the site
    for name, col in (("wall", (0.56, 0.48, 0.41)), ("stone", (0.44, 0.375, 0.32)), ("floor", (0.30, 0.255, 0.22))):
        m = bpy.data.materials.get(name)
        if m: m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*col, 1)
    # soft-touch graphite: fine grain + gentle roughness drift; dark trims slightly glossier
    add_bump(GRAPHITE, 70, 0.08, 0.003); vary_rough(GRAPHITE, 0.35, 0.46, 0.54)
    GRAPHITE.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.034, 0.034, 0.036, 1)
    vary_rough(STEEL, 0.25, 0.045, 0.11)            # polished steel with faint smudges
    vary_rough(CHROME, 0.3, 0.02, 0.06)
    sb = SATIN.node_tree.nodes["Principled BSDF"]; sb.inputs["Anisotropic"].default_value = 0.6; add_bump(SATIN, 400, 0.05, 0.002)
    cb = CLEAR.node_tree.nodes["Principled BSDF"]; cb.inputs["Base Color"].default_value = (0.93, 0.95, 0.96, 1); cb.inputs["Roughness"].default_value = 0.008
    for name, sc_, st in (("wall", 3.0, 0.35), ("floor", 1.2, 0.15)):
        m = bpy.data.materials.get(name)
        if m: add_bump(m, sc_, st, 0.05); vary_color(m, 0.08, tuple(v * 0.93 for v in m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value[:3]), tuple(v * 1.05 for v in m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value[:3]))
    st_ = bpy.data.materials.get("stone")
    if st_:
        add_bump(st_, 9.0, 0.45, 0.04); vary_color(st_, 0.5, (0.44, 0.37, 0.31), (0.53, 0.46, 0.39)); vary_rough(st_, 2.0, 0.7, 0.92)
    # studio HDRI drives reflections; area lights stay as soft key/fill
    hdr = os.path.join(TEX, "hdri", os.environ.get("HDRI", "studio_small_09") + ".hdr")
    wn = world.node_tree; env = wn.nodes.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(hdr)
    mp = wn.nodes.new("ShaderNodeMapping"); tc = wn.nodes.new("ShaderNodeTexCoord"); mp.inputs["Rotation"].default_value[2] = math.radians(float(os.environ.get("HDRI_ROT", "35")))
    wn.links.new(tc.outputs["Generated"], mp.inputs["Vector"]); wn.links.new(mp.outputs["Vector"], env.inputs["Vector"])
    wn.links.new(env.outputs["Color"], wn.nodes["Background"].inputs["Color"]); wn.nodes["Background"].inputs["Strength"].default_value = float(os.environ.get("HDRI_STR", "0.35"))
    lights = [o for o in sc.objects if o.type == "LIGHT"]
    lights[0].data.energy *= 1.1; lights[0].data.size = 70      # warm key from front-left: smaller = more shape
    lights[1].data.energy *= 0.35                                # cool fill from the right
    lights[2].data.energy *= 0.9                                 # rim from behind
    # product-photo strip softboxes: seen in reflections only, they draw crisp highlights on steel and soft-touch
    def strip(name, loc, size, power, tgt=(22, 0, 22), col=(1, 0.97, 0.92)):
        # softbox with a soft gradient falloff along its length: smooth, premium highlights without hard edges
        bpy.ops.mesh.primitive_plane_add(size=1, location=loc); p = bpy.context.object; p.name = name; p.scale = size
        em = bpy.data.materials.new(name); em.use_nodes = True; nt = em.node_tree
        for nd in list(nt.nodes):
            if nd.type == "BSDF_PRINCIPLED": nt.nodes.remove(nd)
        tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["UV"], sep.inputs["Vector"])
        # bell-shaped profile across the short side (x) and the long side (y)
        def bell(sock):
            m1 = nt.nodes.new("ShaderNodeMath"); m1.operation = "SUBTRACT"; m1.inputs[1].default_value = 0.5; nt.links.new(sock, m1.inputs[0])
            m2 = nt.nodes.new("ShaderNodeMath"); m2.operation = "MULTIPLY"; nt.links.new(m1.outputs[0], m2.inputs[0]); nt.links.new(m1.outputs[0], m2.inputs[1])
            m3 = nt.nodes.new("ShaderNodeMath"); m3.operation = "MULTIPLY"; m3.inputs[1].default_value = -8.0; nt.links.new(m2.outputs[0], m3.inputs[0])
            m4 = nt.nodes.new("ShaderNodeMath"); m4.operation = "EXPONENT"; nt.links.new(m3.outputs[0], m4.inputs[0]); return m4.outputs[0]
        bx, by = bell(sep.outputs["X"]), bell(sep.outputs["Y"])
        mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; nt.links.new(bx, mul.inputs[0]); nt.links.new(by, mul.inputs[1])
        st = nt.nodes.new("ShaderNodeMath"); st.operation = "MULTIPLY"; st.inputs[1].default_value = power; nt.links.new(mul.outputs[0], st.inputs[0])
        e = nt.nodes.new("ShaderNodeEmission"); e.inputs["Color"].default_value = (*col, 1); nt.links.new(st.outputs[0], e.inputs["Strength"])
        nt.links.new(e.outputs["Emission"], nt.nodes["Material Output"].inputs["Surface"])
        p.data.materials.append(em); aim(p, tgt); p.rotation_euler.rotate_axis("X", math.radians(180))
        p.visible_camera = False; p.visible_shadow = False
        for c in p.users_collection: c.objects.unlink(p)
        studio.objects.link(p)
    strip("soft_L", (-75, -55, 42), (22, 100, 1), 14.0)
    strip("soft_R", (100, -70, 46), (22, 100, 1), 7.0, col=(0.95, 0.97, 1.0))
    strip("soft_T", (20, -15, 125), (90, 40, 1), 5.0)
    strip("rim_B", (30, 110, 60), (60, 18, 1), 10.0)
    # soft pool of light on the fluted wall behind the machine, darker towards the edges
    bpy.ops.object.light_add(type="SPOT", location=(22, -60, 150)); wl = bpy.context.object
    wl.data.energy = 420000; wl.data.spot_size = math.radians(60); wl.data.spot_blend = 1.0; wl.data.shadow_soft_size = 25; wl.data.color = (1.0, 0.9, 0.78)
    aim(wl, (22, 120, 50))
    for c in wl.users_collection: c.objects.unlink(wl)
    studio.objects.link(wl)
    # camera: depth of field on the machine, motion blur, more light bounces through the clear lid
    foc = bpy.data.objects.new("focus", None); studio.objects.link(foc); foc.location = (24, -6, 24)
    cam.data.dof.use_dof = True; cam.data.dof.focus_object = foc; cam.data.dof.aperture_fstop = float(os.environ.get("FSTOP", "4.0"))
    sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = 0.4
    sc.cycles.max_bounces = 10; sc.cycles.transmission_bounces = 10; sc.cycles.glossy_bounces = 6
    sc.cycles.adaptive_threshold = 0.015; sc.cycles.denoiser = "OPENIMAGEDENOISE"
    sc.render.filter_size = 1.2
    sc.view_settings.look = "AgX - Medium High Contrast"; sc.view_settings.exposure = float(os.environ.get("EXPO", "0.0"))

if VIEW == "blend":
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True); print("saved", OUT); sys.exit(0)
if VIEW == "work":
    # 7 s: slow push-in at three quarters while the head lowers, the dial clicks to 2 and the hook starts
    sc.render.resolution_x, sc.render.resolution_y = 1280, 720
    cam.data.lens = 30; cam.data.keyframe_insert("lens", frame=1)
    cam.location = (-26, -108, 54); aim(cam, (22, 0, 26)); cam.keyframe_insert("location", frame=1)
    cam.data.lens = 38; cam.data.keyframe_insert("lens", frame=168)
    cam.location = (-22, -84, 50); cam.keyframe_insert("location", frame=168)
    tr = cam.constraints.new("TRACK_TO"); tgt = bpy.data.objects.new("look", None); studio.objects.link(tgt); tgt.location = (22, 0, 23)
    tr.target = tgt; tr.track_axis = "TRACK_NEGATIVE_Z"; tr.up_axis = "UP_Y"
    sc.frame_start, sc.frame_end = 1, 168; sc.render.fps = 24
    sc.render.filepath = OUT.rstrip("/") + "/f_"
    sc.render.image_settings.file_format = "JPEG"; sc.render.image_settings.quality = 93
    if len(args) > 3:  # preview selected frames only
        for fr in map(int, args[3].split(",")):
            sc.frame_set(fr); sc.render.filepath = OUT.rstrip("/") + f"/p_{fr:04d}.jpg"; bpy.ops.render.render(write_still=True)
        sys.exit(0)
    bpy.ops.render.render(animation=True); print("rendered animation", OUT); sys.exit(0)
if VIEW == "orbit":
    # 5 s at 24 fps, 16:9: slow 100-degree orbit from the bowl end to the controls
    sc.render.resolution_x, sc.render.resolution_y = 1280, 720
    bpy.ops.object.empty_add(location=(22, 0, 23)); pivot = bpy.context.object
    cam.parent = pivot; cam.location = (0, -128, 21); cam.rotation_euler = (math.radians(82), 0, 0); cam.data.lens = 38
    sc.frame_start, sc.frame_end = 1, 120
    pivot.rotation_euler = (0, 0, math.radians(-60)); pivot.keyframe_insert("rotation_euler", frame=1)
    pivot.rotation_euler = (0, 0, math.radians(40)); pivot.keyframe_insert("rotation_euler", frame=120)
    for fc in pivot.animation_data.action.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = "SINE"
    sc.render.fps = 24
    sc.render.filepath = OUT.rstrip("/") + "/f_"
    sc.render.image_settings.file_format = "JPEG"; sc.render.image_settings.quality = 93
    bpy.ops.render.render(animation=True); print("rendered animation", OUT); sys.exit(0)
sc.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("rendered", OUT)
