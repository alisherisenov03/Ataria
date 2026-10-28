# ATARIA AT-SM23 — model v2. Proportions measured on the owner's front photo (001.jpg), side/end views 025/030/034/035.
# 1 unit = 1 cm. X: width (bowl left, column right). Y: depth (front = -Y). Z: up.
import bpy, bmesh, math, sys, os
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = args[0] if args else "/tmp/r.png"
VIEW = args[1] if len(args) > 1 else "front34"
SAMPLES = int(args[2]) if len(args) > 2 else 64
TEX = os.path.dirname(os.path.abspath(__file__))

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

def mat(name, color, metal=0.0, rough=0.5, trans=0.0, ior=1.45, coat=0.0, bump=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    b.inputs["Transmission Weight"].default_value = trans
    b.inputs["IOR"].default_value = ior
    b.inputs["Coat Weight"].default_value = coat
    if bump:
        n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = 900; n.inputs["Detail"].default_value = 2
        bu = nt.nodes.new("ShaderNodeBump"); bu.inputs["Strength"].default_value = bump; bu.inputs["Distance"].default_value = 0.02
        nt.links.new(n.outputs["Fac"], bu.inputs["Height"]); nt.links.new(bu.outputs["Normal"], b.inputs["Normal"])
    return m

GRAPHITE = mat("graphite", (0.032, 0.032, 0.034), rough=0.58, coat=0.08, bump=0.25)
STEEL = mat("steel", (0.88, 0.88, 0.9), metal=1.0, rough=0.09)
CHROME = mat("chrome", (0.95, 0.95, 0.96), metal=1.0, rough=0.04)
CLEAR = mat("clear", (0.98, 0.99, 1.0), rough=0.03, trans=1.0, ior=1.49)
SCREEN = mat("screen", (0.006, 0.006, 0.008), rough=0.08)
DARK = mat("dark", (0.012, 0.012, 0.013), rough=0.5)

def decal(name, img, w, h, loc, rot=(math.radians(90), 0, 0)):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(os.path.join(TEX, img))
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"]); nt.links.new(t.outputs["Alpha"], b.inputs["Alpha"])
    b.inputs["Roughness"].default_value = 0.45
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object; o.name = name; o.scale = (w, h, 1); o.data.materials.append(m)
    return o

def box(name, size, loc, material=GRAPHITE):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(material)
    return o

def bevel(o, w, segs=8, angle=None):
    md = o.modifiers.new("bev", "BEVEL"); md.width = w; md.segments = segs
    md.limit_method = "ANGLE" if angle else "NONE"
    if angle: md.angle_limit = math.radians(angle)
    md.harden_normals = False
    return md

def union(a, b):
    md = a.modifiers.new("u", "BOOLEAN"); md.operation = "UNION"; md.object = b; md.solver = "EXACT"
    bpy.context.view_layer.objects.active = a; bpy.ops.object.modifier_apply(modifier=md.name)
    bpy.data.objects.remove(b)

def diff(a, b):
    md = a.modifiers.new("d", "BOOLEAN"); md.operation = "DIFFERENCE"; md.object = b; md.solver = "EXACT"
    bpy.context.view_layer.objects.active = a; bpy.ops.object.modifier_apply(modifier=md.name)
    bpy.data.objects.remove(b)

def smooth(o):
    bpy.context.view_layer.objects.active = o; o.select_set(True); bpy.ops.object.shade_smooth(); o.select_set(False)

def cyl(name, r, h, loc, rot=(0, 0, 0), material=STEEL, verts=128):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=loc, rotation=rot, vertices=verts)
    o = bpy.context.object; o.name = name; o.data.materials.append(material); smooth(o)
    return o

def lathe(name, profile, loc, material=STEEL, thick=0.22, sub=2):
    me = bpy.data.meshes.new(name); o = bpy.data.objects.new(name, me); sc.collection.objects.link(o)
    bm = bmesh.new(); vs = [bm.verts.new((r, 0, z)) for r, z in profile]
    for a, b in zip(vs, vs[1:]): bm.edges.new((a, b))
    bmesh.ops.spin(bm, geom=bm.verts[:] + bm.edges[:], cent=(0, 0, 0), axis=(0, 0, 1), angle=math.tau, steps=128)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4); bm.to_mesh(me); bm.free()
    o.location = loc; o.data.materials.append(material)
    if thick: o.modifiers.new("s", "SOLIDIFY").thickness = thick
    if sub: o.modifiers.new("sub", "SUBSURF").levels = sub
    for p in me.polygons: p.use_smooth = True
    return o


def rounded_poly(pts, radii, seg=14):
    # pts: list of (x, z); radii: per-corner fillet radius (0 = sharp). Returns dense outline.
    out = []
    n = len(pts)
    for i in range(n):
        p0, p1, p2 = Vector(pts[i - 1]), Vector(pts[i]), Vector(pts[(i + 1) % n])
        r = radii[i]
        if r <= 0: out.append(p1); continue
        a = (p0 - p1).normalized(); b = (p2 - p1).normalized()
        ang = a.angle(b); t = r / math.tan(ang / 2)
        s1 = p1 + a * t; s2 = p1 + b * t
        bis = (a + b).normalized(); c = p1 + bis * (r / math.sin(ang / 2))
        v1 = s1 - c; v2 = s2 - c
        a1 = math.atan2(v1.y, v1.x); a2 = math.atan2(v2.y, v2.x)
        da = a2 - a1
        while da > math.pi: da -= math.tau
        while da < -math.pi: da += math.tau
        for k in range(seg + 1):
            aa = a1 + da * k / seg
            out.append(c + Vector((math.cos(aa), math.sin(aa))) * r)
    return out

def extrude_profile(name, pts, radii, depth, edge, material=None):
    outline = rounded_poly(pts, radii)
    me = bpy.data.meshes.new(name); o = bpy.data.objects.new(name, me); sc.collection.objects.link(o)
    bm = bmesh.new()
    vs = [bm.verts.new((v.x, -depth / 2, v.y)) for v in outline]
    f = bm.faces.new(vs)
    r = bmesh.ops.extrude_face_region(bm, geom=[f])
    for v in [e for e in r["geom"] if isinstance(e, bmesh.types.BMVert)]: v.co.y += depth
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
    o.data.materials.append(material or GRAPHITE)
    md = o.modifiers.new("bev", "BEVEL"); md.width = edge; md.segments = 10; md.limit_method = "ANGLE"; md.angle_limit = math.radians(60)
    o.modifiers.new("wn", "WEIGHTED_NORMAL")
    for pgn in me.polygons: pgn.use_smooth = True
    return o

W = 44.0          # overall width
HD = 19.0         # head / column depth
BD = 23.0         # base depth
FY = -HD / 2      # front face of head and column

# ---- base: low slab with rounded ends ----
extrude_profile("base", [(0, 0), (W, 0), (W, 4.6), (0, 4.6)], [1.2, 1.2, 2.2, 2.2], BD, 2.0)
cyl("seat", 11.8, 0.4, (11.0, 0, 4.75), material=DARK)
# ---- body: one C-shaped piece (column + head), profile measured on the front photo ----
body = [(30.9, 4.6), (W, 4.6), (W, 44.9), (0, 44.9), (0, 30.4), (30.9, 30.4)]
extrude_profile("body", body, [0, 0, 3.8, 3.8, 3.2, 5.5], HD, 2.4)
# seams: top cap line and the tilt split across the column
box("seam_top_f", (W - 7.0, 0.05, 0.14), (W / 2, FY - 0.01, 43.7), material=DARK)
box("seam_tilt_f", (13.1 - 2.0, 0.05, 0.14), (W - 6.55, FY - 0.01, 21.6), material=DARK)
for yy in (FY - 0.01, -FY + 0.01): pass
# planetary hub under the head
cyl("hub", 6.4, 2.6, (11.0, 0, 29.4), material=GRAPHITE)
cyl("hub_ring", 5.6, 0.9, (11.0, 0, 27.7), material=DARK)
cyl("shaft", 1.0, 2.5, (11.0, 0, 26.2), material=STEEL)

# side port cover on the left end of the head (with a triangle mark)
port = box("port_cover", (0.4, 9.0, 8.0), (-0.12, 0, 37.6)); bevel(port, 1.4, 8); smooth(port)

# ---- bowl 7 L ----
lathe("bowl", [(0.01, 5.2), (6.8, 5.4), (9.8, 8.0), (11.8, 12.6), (12.6, 18.4), (12.8, 23.6), (13.4, 25.2), (13.5, 25.4)], (11.0, 0, 0))
for sgn in (-1, 1):
    bpy.ops.mesh.primitive_torus_add(major_radius=4.6, minor_radius=0.36, location=(11.0, sgn * 12.9, 21.6))
    h = bpy.context.object; h.scale = (1.0, 0.32, 1.0); h.data.materials.append(CHROME); smooth(h)
# clear splash guard lid with spout chute at the front-left
lathe("lid", [(6.6, 27.2), (10.5, 26.9), (13.6, 26.0), (13.8, 25.4)], (11.0, 0, 0), material=CLEAR, thick=0.25)
ch = box("chute", (5.4, 4.2, 2.6), (2.0, -7.5, 27.0), material=CLEAR); bevel(ch, 0.6, 4); smooth(ch)

# ---- front controls ----
fr = box("display_frame", (8.0, 0.5, 6.0), (W - 6.6, FY - 0.15, 28.8), material=CHROME); bevel(fr, 0.6, 6); smooth(fr)
sc_ = box("display", (6.9, 0.5, 4.9), (W - 6.6, FY - 0.3, 28.8), material=SCREEN); bevel(sc_, 0.4, 6); smooth(sc_)
cyl("dial_ring", 4.2, 1.2, (W - 7.6, FY - 0.5, 10.3), rot=(math.radians(90), 0, 0), material=CHROME)
cyl("dial_knurl", 3.2, 2.2, (W - 7.6, FY - 1.4, 10.3), rot=(math.radians(90), 0, 0), material=STEEL)
cyl("dial_cap", 2.9, 0.6, (W - 7.6, FY - 2.6, 10.3), rot=(math.radians(90), 0, 0), material=STEEL)
lv = box("lever", (4.0, 1.0, 1.3), (W - 8.6, FY - 0.55, 18.3), material=CHROME); bevel(lv, 0.5, 6); smooth(lv)
cyl("lever_pivot", 0.9, 1.3, (W - 10.0, FY - 0.6, 18.3), rot=(math.radians(90), 0, 0), material=CHROME)

# ---- decals cut from the real photos ----
if os.path.exists(os.path.join(TEX, "logo.png")): decal("logo", "logo.png", 8.2, 8.2 * 0.125, (21.5, FY - 0.03, 38.4))
if os.path.exists(os.path.join(TEX, "icons.png")): decal("icons", "icons.png", 7.4, 7.4 * 902 / 806, (W - 6.6, FY - 0.03, 37.6))
if os.path.exists(os.path.join(TEX, "display.png")): decal("disp", "display.png", 6.6, 6.6 * 500 / 700, (W - 6.6, FY - 0.58, 28.8))
if os.path.exists(os.path.join(TEX, "dial.png")): decal("dialface", "dial.png", 8.4, 8.4, (W - 7.6, FY - 2.95, 10.3))

# ---- studio: taupe floor, stone plinth, curved fluted wall ----
floor = box("floor", (600, 600, 1), (22, 0, -4.0), material=mat("floor", (0.40, 0.355, 0.32), rough=0.6))
cyl("plinth", 34, 3.5, (22, 0, -1.75), material=mat("stone", (0.46, 0.41, 0.37), rough=0.85, bump=0.6), verts=192)
wallm = mat("wall", (0.54, 0.48, 0.43), rough=0.92)
for i in range(70):
    a = math.radians(-80 + i * 2.3)
    cyl(f"fl{i}", 1.7, 160, (22 + 130 * math.sin(a), 110 * math.cos(a) + 20, 76), material=wallm, verts=24)

def aim(o, tgt): o.rotation_euler = (Vector(tgt) - o.location).to_track_quat("-Z", "Y").to_euler()
bpy.ops.object.light_add(type="AREA", location=(120, -70, 100)); k = bpy.context.object
k.data.energy = 420000; k.data.size = 130; k.data.color = (1.0, 0.91, 0.8); aim(k, (22, 0, 20))
bpy.ops.object.light_add(type="AREA", location=(-100, -60, 70)); f = bpy.context.object
f.data.energy = 60000; f.data.size = 160; f.data.color = (0.95, 0.96, 1.0); aim(f, (22, 0, 20))
bpy.ops.object.light_add(type="AREA", location=(10, 90, 120)); r = bpy.context.object
r.data.energy = 140000; r.data.size = 80; aim(r, (22, 0, 30))
world = bpy.data.worlds.new("w"); sc.world = world; world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.36, 0.32, 0.29, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.35

cams = {
    "front34": ((-34, -112, 46), (21, 0, 21), 55),
    "front": ((22, -135, 24), (22, 0, 22), 60),
    "side": ((-130, -10, 28), (22, 0, 21), 60),
    "close_panel": ((60, -52, 30), (W - 7, FY, 22), 70),
}
loc, tgt, lens = cams.get(VIEW, cams["front34"])
bpy.ops.object.camera_add(location=loc); cam = bpy.context.object; sc.camera = cam; aim(cam, tgt); cam.data.lens = lens

sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = SAMPLES; sc.cycles.use_denoising = True
sc.render.resolution_x = 1200; sc.render.resolution_y = 1500
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"
sc.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("rendered", OUT)
