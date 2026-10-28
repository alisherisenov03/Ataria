"""ATARIA pillow #1 ("butterfly") — procedural 3D model + Bork-style studio scene.

Run with the Blender Python module (bpy) and scikit-image:
    python pillow_scene.py still   out.png  [view]
    python pillow_scene.py turn    out_dir  [frames]
Views: hero (3/4 front), front, top, macro.
Shape follows brand/ataria_pillow1_reference.jpg: 620x410 mm, wings 13 cm,
grey velvet top that runs down the centre of the front face, white
diamond-quilted sides, dark button in the head dimple.
"""
import math
import sys

import bpy
import numpy as np
from skimage import measure

W, D = 0.31, 0.205  # half width / half depth, metres
SEAM_Z = 0.016  # height of the lower side seam (label sits in it)


# ---------------------------------------------------------------- geometry
def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)


def smax(a, b, k):
    return -smin(-a, -b, k)


def outline_sdf(x, y, z=None):
    if z is not None:
        # ends flare outwards with height: X-shaped front silhouette, undercut wings
        x = x * (1 + 0.24 * np.clip(1 - z / 0.115, 0, 1) ** 1.6)
    # rounded rectangle
    r = 0.07
    qx, qy = np.abs(x) - (W - r), np.abs(y) - (D - r)
    d = np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r
    # deep concave cut-ins on the left/right sides (arm/shoulder zones)
    side = np.hypot(np.abs(x) - (W + 0.06), y) - 0.135
    d = smax(d, -side, 0.03)
    # shallow concave back edge
    back = np.hypot(x, y - (D + 0.30)) - 0.32
    d = smax(d, -back, 0.03)
    # two small notches either side of the front centre tab
    for sx in (-1, 1):
        n = np.hypot(x - sx * 0.14, y + D + 0.025) - 0.055
        d = smax(d, -n, 0.02)
    return d


def height(x, y):
    ax = np.clip(np.abs(x) / W, 0, 1.2)
    h = 0.070 + 0.062 * ax ** 2.0                    # wings rise to the ends
    h += 0.020 * np.clip(np.abs(y) / D, 0, 1.2) ** 2  # front / back rolls
    h += 0.010 * np.clip(y / D, 0, 1)                 # back roll a bit higher (13 vs 11 cm)
    h -= 0.022 * np.exp(-(x ** 2 + (y + 0.01) ** 2) / (2 * 0.075 ** 2))  # head dimple
    return h


def pillow_sdf(x, y, z):
    d = outline_sdf(x, y, z)
    # soft cover: sides bulge out a little around mid-height
    d -= 0.007 * np.exp(-((z - 0.05) / 0.035) ** 2)
    d = smax(d, z - height(x, y), 0.045)
    d = smax(d, -z, 0.022)
    return d


def smoothstep(e0, e1, v):
    t = np.clip((v - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def grey_mask(v, n):
    """1 on the grey velvet panel (top + centre band of the front/back faces), 0 on white knit."""
    top = smoothstep(0.30, 0.50, n[:, 2])
    band_w = 0.085 + 1.25 * v[:, 2]
    band = smoothstep(band_w + 0.006, band_w - 0.006, np.abs(v[:, 0])) * smoothstep(0.15, 0.35, np.abs(n[:, 1]))
    return np.maximum(top, band)


def quilt_height(v, n, p=0.026):
    """Puffy diamond quilting, triplanar so the diamonds stay square on every face."""
    w = np.abs(n) ** 4
    w /= w.sum(axis=1, keepdims=True)
    h = np.zeros(len(v))
    for axis, (i, j) in enumerate(((1, 2), (0, 2), (0, 1))):
        u, t = v[:, i], v[:, j]
        q = np.abs(np.sin(np.pi * (u + t) / p) * np.sin(np.pi * (u - t) / p)) ** 0.45
        h += w[:, axis] * q
    return h


def smooth_noise(v, cell, sigma, seed):
    """Isotropic soft noise in roughly [-1, 1]: blurred random lattice sampled at the vertices."""
    from scipy.ndimage import gaussian_filter, map_coordinates
    lo = v.min(axis=0) - 4 * cell
    shape = np.ceil((v.max(axis=0) - lo) / cell).astype(int) + 8
    g = gaussian_filter(np.random.default_rng(seed).normal(size=shape), sigma)
    g /= np.abs(g).max()
    return map_coordinates(g, ((v - lo) / cell).T, order=1)


def build_pillow(step=0.002):
    o = step * 0.37  # keep flat faces off the grid planes (avoids degenerate triangles)
    xs = np.arange(-0.42, 0.42, step) + o
    ys = np.arange(-0.25, 0.25, step) + o
    zs = np.arange(-0.01, 0.18, step) + o
    X, Y, Z = np.meshgrid(xs, ys, zs, indexing="ij")
    vol = pillow_sdf(X, Y, Z)
    verts, faces, normals, _ = measure.marching_cubes(vol, 0.0, spacing=(step, step, step))
    verts += np.array([xs[0], ys[0], zs[0]])
    normals = normals / np.linalg.norm(normals, axis=1, keepdims=True)
    if np.mean(np.sum((verts - verts.mean(axis=0)) * normals, axis=1)) < 0:
        normals = -normals  # make them point outward

    grey = grey_mask(verts, normals)
    seam = np.clip(1 - np.abs(2 * grey - 1), 0, 1) ** 2  # peaks on the grey/white seam
    # lower seam where the side band meets the bottom panel; the label is sewn into it
    side = smoothstep(0.85, 0.6, np.abs(normals[:, 2]))
    seam = np.maximum(seam, np.exp(-((verts[:, 2] - SEAM_Z) / 0.0022) ** 2) * side)
    # fabric: quilt puffs on white, slow soft ripples on the velvet, piping groove on the seam
    ripple = smooth_noise(verts, cell=0.008, sigma=2.0, seed=7)
    puff = 0.75 + 0.5 * (0.5 + 0.5 * np.sin(verts @ np.array([31.0, -23.0, 17.0])))  # uneven filling
    disp = (1 - grey) * 0.0022 * quilt_height(verts, normals) * puff
    disp += 0.0014 * ripple
    disp -= 0.0016 * seam
    verts = verts + normals * disp[:, None]

    mesh = bpy.data.meshes.new("pillow")
    mesh.from_pydata(verts.tolist(), [], faces[:, ::-1].tolist())
    for name, vals in (("grey", grey), ("seam", seam)):
        attr = mesh.attributes.new(name, "FLOAT", "POINT")
        attr.data.foreach_set("value", vals.astype(np.float32))
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=step * 0.05)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=step * 0.05)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)  # consistent outward faces
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    mesh.shade_smooth()
    obj = bpy.data.objects.new("pillow", mesh)
    bpy.context.collection.objects.link(obj)
    return obj


# ---------------------------------------------------------------- materials
class Nodes:
    def __init__(self, mat):
        mat.use_nodes = True
        self.nt = mat.node_tree
        self.nt.nodes.clear()

    def n(self, kind, **props):
        node = self.nt.nodes.new(kind)
        for k, v in props.items():
            setattr(node, k, v)
        return node

    def link(self, a, b):
        self.nt.links.new(a, b)

    def math(self, op, a, b=None, clamp=False):
        m = self.n("ShaderNodeMath", operation=op, use_clamp=clamp)
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                m.inputs[i].default_value = v
            else:
                self.link(v, m.inputs[i])
        return m.outputs[0]


def pillow_material():
    mat = bpy.data.materials.new("pillow_cover")
    N = Nodes(mat)
    out = N.n("ShaderNodeOutputMaterial")
    tex = N.n("ShaderNodeTexCoord")
    grey = N.n("ShaderNodeAttribute", attribute_name="grey").outputs["Fac"]
    seam = N.n("ShaderNodeAttribute", attribute_name="seam").outputs["Fac"]

    # knit / pile micro texture (quilting itself is real geometry)
    knit = N.n("ShaderNodeTexNoise")
    knit.inputs["Scale"].default_value = 2200.0
    knit.inputs["Detail"].default_value = 4
    N.link(tex.outputs["Object"], knit.inputs["Vector"])
    bump = N.n("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.35
    bump.inputs["Distance"].default_value = 0.0006
    N.link(knit.outputs["Fac"], bump.inputs["Height"])
    vbump = N.n("ShaderNodeBump")
    vbump.inputs["Strength"].default_value = 0.2
    vbump.inputs["Distance"].default_value = 0.0003
    N.link(knit.outputs["Fac"], vbump.inputs["Height"])

    white = N.n("ShaderNodeBsdfPrincipled")
    white.inputs["Base Color"].default_value = (0.80, 0.78, 0.74, 1)
    white.inputs["Roughness"].default_value = 0.9
    white.inputs["Sheen Weight"].default_value = 0.4
    white.inputs["Subsurface Weight"].default_value = 0.08
    white.inputs["Subsurface Radius"].default_value = (0.004, 0.004, 0.004)
    velvet = N.n("ShaderNodeBsdfPrincipled")
    velvet.inputs["Base Color"].default_value = (0.15, 0.15, 0.175, 1)
    velvet.inputs["Roughness"].default_value = 0.95
    velvet.inputs["Sheen Weight"].default_value = 1.0
    velvet.inputs["Sheen Roughness"].default_value = 0.3
    velvet.inputs["Sheen Tint"].default_value = (0.8, 0.8, 0.86, 1)
    piping = N.n("ShaderNodeBsdfPrincipled")
    piping.inputs["Base Color"].default_value = (0.55, 0.54, 0.53, 1)
    piping.inputs["Roughness"].default_value = 0.85
    N.link(bump.outputs["Normal"], white.inputs["Normal"])
    N.link(vbump.outputs["Normal"], velvet.inputs["Normal"])
    mix = N.n("ShaderNodeMixShader")
    N.link(grey, mix.inputs["Fac"])
    N.link(white.outputs[0], mix.inputs[1])
    N.link(velvet.outputs[0], mix.inputs[2])
    mix2 = N.n("ShaderNodeMixShader")
    N.link(N.math("POWER", seam, 2.0), mix2.inputs["Fac"])
    N.link(mix.outputs[0], mix2.inputs[1])
    N.link(piping.outputs[0], mix2.inputs[2])
    N.link(mix2.outputs[0], out.inputs["Surface"])
    return mat


def add_tag(pillow, podium_h):
    """Black woven ATARIA label sewn into the lower side seam, sticking out of it."""
    import bmesh
    from mathutils import Matrix, Vector
    bpy.context.view_layer.update()
    mw = pillow.matrix_world
    target = Vector((-0.235, -0.215, SEAM_Z))
    cands = [v for v in pillow.data.vertices if abs(v.co.z - SEAM_Z) < 0.003]
    best = min(cands, key=lambda v: (v.co - target).length)
    out = Vector((best.normal.x, best.normal.y, 0)).normalized()
    up = Vector((0, 0, 1))
    t = up.cross(out).normalized()               # along the seam
    e = out                                      # sticks straight out of the seam
    w, L, n = 0.032, 0.017, 8  # wide along the seam, sticks out 17 mm
    root = mw @ best.co - out * 0.002            # starts inside the seam
    bm = bmesh.new()
    rows = []
    for i in range(n + 1):
        f = i / n
        c = root + e * (L * f) - up * (0.0015 * f * f)
        rows.append([bm.verts.new(c - t * w / 2), bm.verts.new(c + t * w / 2)])
    for a, b in zip(rows, rows[1:]):
        bm.faces.new((a[0], a[1], b[1], b[0]))
    me = bpy.data.meshes.new("tag")
    bm.to_mesh(me)
    bm.free()
    tag = bpy.data.objects.new("tag", me)
    bpy.context.collection.objects.link(tag)
    solid = tag.modifiers.new("solid", "SOLIDIFY")
    solid.thickness = 0.0011                     # folded label: two layers of ribbon
    solid.offset = 0
    tag.data.materials.append(simple_material("tag", (0.025, 0.03, 0.045), 0.8, 3000.0, 0.15))
    bpy.ops.object.shade_smooth()

    face_n = e.cross(t).normalized()
    if face_n.z < 0:
        face_n = -face_n
    bpy.ops.object.text_add()
    txt = bpy.context.object
    txt.data.body = "ATARIA"
    txt.data.align_x = "CENTER"
    txt.data.align_y = "CENTER"
    txt.data.size = 0.0072
    txt.data.extrude = 0.00005
    x_ax = -t if (-t).dot(Vector((1, 0, 0))) > 0 else t  # read left-to-right from the front
    y_ax = face_n.cross(x_ax).normalized()
    rot = Matrix((x_ax, y_ax, face_n)).transposed().to_4x4()
    mid = root + e * (L * 0.55) - up * 0.0005 + face_n * 0.0009
    txt.matrix_world = Matrix.Translation(mid) @ rot
    txt.data.materials.append(simple_material("tag_text", (0.85, 0.85, 0.85), 0.6))
    return tag


def simple_material(name, color, rough=0.6, noise_scale=0.0, bump=0.0):
    mat = bpy.data.materials.new(name)
    N = Nodes(mat)
    out = N.n("ShaderNodeOutputMaterial")
    bsdf = N.n("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = rough
    if noise_scale:
        tex = N.n("ShaderNodeTexCoord")
        noise = N.n("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = noise_scale
        noise.inputs["Detail"].default_value = 8
        N.link(tex.outputs["Object"], noise.inputs["Vector"])
        b = N.n("ShaderNodeBump")
        b.inputs["Strength"].default_value = bump
        N.link(noise.outputs["Fac"], b.inputs["Height"])
        N.link(b.outputs["Normal"], bsdf.inputs["Normal"])
        ramp = N.n("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].color = (*[c * 0.92 for c in color], 1)
        ramp.color_ramp.elements[1].color = (*[min(1, c * 1.05) for c in color], 1)
        N.link(noise.outputs["Fac"], ramp.inputs["Fac"])
        N.link(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    N.link(bsdf.outputs[0], out.inputs["Surface"])
    return mat


# ---------------------------------------------------------------- scene
def add_area(name, loc, target, size, power, kelvin_rgb):
    data = bpy.data.lights.new(name, "AREA")
    data.shape = "RECTANGLE"
    data.size, data.size_y = size
    data.energy = power
    data.color = kelvin_rgb
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = loc
    look_at(obj, target)
    return obj


def look_at(obj, target):
    from mathutils import Vector
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def build_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scn = bpy.context.scene
    scn.render.engine = "CYCLES"
    scn.cycles.device = "CPU"
    scn.cycles.use_denoising = True
    scn.view_settings.view_transform = "AgX"
    scn.view_settings.look = "AgX - Medium High Contrast"

    world = bpy.data.worlds.new("w")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.06, 0.05, 0.045, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.08
    scn.world = world

    pillow = build_pillow()
    pillow.data.materials.append(pillow_material())
    podium_h = 0.10
    pillow.location.z = podium_h

    # button in the head dimple
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.008, location=(0, -0.01, podium_h + height(0, -0.01) - 0.003))
    btn = bpy.context.object
    btn.scale.z = 0.6
    bpy.ops.object.shade_smooth()
    btn.data.materials.append(simple_material("button", (0.05, 0.05, 0.06), 0.75))
    add_tag(pillow, podium_h)

    # travertine podium
    bpy.ops.mesh.primitive_cylinder_add(vertices=128, radius=0.5, depth=podium_h, location=(0, 0, podium_h / 2))
    pod = bpy.context.object
    bev = pod.modifiers.new("bevel", "BEVEL")
    bev.width, bev.segments = 0.006, 4
    bpy.ops.object.shade_smooth()
    pod.data.materials.append(simple_material("travertine", (0.45, 0.40, 0.34), 0.7, 40.0, 0.15))

    # taupe sweep: floor + wall with a curved join
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
    sweep = bpy.context.object
    sweep.scale = (8, 8, 1)
    bpy.ops.object.transform_apply(scale=True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.subdivide(number_cuts=60)
    bpy.ops.object.mode_set(mode="OBJECT")
    for v in sweep.data.vertices:
        if v.co.y > 1.2:
            t = v.co.y - 1.2
            ang = min(t / 1.0, 1) * math.pi / 2
            v.co.z = (1 - math.cos(ang)) * 1.0 + max(0, t - 1.0)
            v.co.y = 1.2 + math.sin(ang) * 1.0
    bpy.ops.object.shade_smooth()
    sweep.data.materials.append(simple_material("taupe", (0.16, 0.13, 0.11), 0.9, 6.0, 0.05))

    warm, neutral, cool = (1.0, 0.86, 0.72), (1.0, 0.95, 0.9), (0.85, 0.9, 1.0)
    add_area("key", (-1.1, -1.0, 1.4), (0, 0, 0.18), (2.4, 1.8), 75, warm)
    add_area("rim", (1.2, 1.0, 0.9), (0, 0, 0.2), (0.4, 1.2), 45, neutral)
    add_area("fill", (1.2, -1.3, 0.5), (0, 0, 0.15), (1.5, 1.5), 8, cool)
    return pillow


CAMERAS = {
    # name: (location, target, focal mm)
    "hero": ((-0.95, -1.25, 0.62), (0, 0.02, 0.17), 70),
    "front": ((0.0, -1.6, 0.30), (0, 0, 0.17), 85),
    "top": ((0.0, -0.35, 1.45), (0, 0.0, 0.15), 60),
    "macro": ((-0.34, -0.55, 0.33), (-0.235, -0.225, 0.12), 100),
}


def add_camera(view):
    loc, target, mm = CAMERAS[view]
    cam_data = bpy.data.cameras.new("cam")
    cam_data.lens = mm
    cam_data.dof.use_dof = True
    cam_data.dof.aperture_fstop = 2.8 if view == "macro" else 5.6
    cam = bpy.data.objects.new("cam", cam_data)
    bpy.context.collection.objects.link(cam)
    cam.location = loc
    look_at(cam, target)
    from mathutils import Vector
    cam_data.dof.focus_distance = (Vector(target) - Vector(loc)).length
    bpy.context.scene.camera = cam
    return cam


def render_still(path, view="hero", samples=160, res=(1080, 1350)):
    build_scene()
    add_camera(view)
    scn = bpy.context.scene
    scn.cycles.samples = samples
    scn.render.resolution_x, scn.render.resolution_y = res
    scn.render.filepath = path
    bpy.ops.render.render(write_still=True)


def render_turntable(out_dir, frames=96, samples=48, res=(720, 900)):
    """Slow 3/4 orbit around the pillow, like a premium product film."""
    build_scene()
    cam = add_camera("hero")
    scn = bpy.context.scene
    scn.cycles.samples = samples
    scn.render.resolution_x, scn.render.resolution_y = res
    loc0 = cam.location.copy()
    r = math.hypot(loc0.x, loc0.y)
    a0 = math.atan2(loc0.y, loc0.x)
    for f in range(frames):
        a = a0 + math.radians(50) * (f / (frames - 1)) - math.radians(10)
        cam.location = (r * math.cos(a), r * math.sin(a), loc0.z - 0.08 * f / frames)
        look_at(cam, (0, 0.02, 0.17))
        scn.render.filepath = f"{out_dir}/f{f:04d}.png"
        bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    mode, out = sys.argv[1], sys.argv[2]
    extra = sys.argv[3] if len(sys.argv) > 3 else None
    if mode == "still":
        render_still(out, extra or "hero")
    else:
        render_turntable(out, int(extra or 96))
