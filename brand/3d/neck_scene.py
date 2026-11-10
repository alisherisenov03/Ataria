"""ATARIA ad: side sleeper's cervical spine on a flat pillow vs on ATARIA.

Medical-3D look: real skeleton (Blender "Human Base Meshes", CC0) lying on its left side,
viewed from behind. On a flat pillow the head drops and the neck bends (red);
on ATARIA the neck continues the straight line of the spine (cool white).
    python neck_scene.py flat|ataria out.png [samples] [bend_fraction]
Needs HUMAN_BUNDLE=/path/to/human_base_meshes_bundle.blend in the environment.
"""
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

import pillow_scene as ps

BUNDLE = os.environ.get("HUMAN_BUNDLE", "human_base_meshes_bundle.blend")
CERVICAL = [f"GEO-skeletion.spine_cervical_c{i}" for i in range(1, 8)]
THORACIC = ["GEO-skeletion.spine_thoracic_t1", "GEO-skeletion.spine_thoracic_2", "GEO-skeletion.spine_thoracic_t3"] + [
    f"GEO-skeletion.spine_thoracic_{i}" for i in range(4, 11)] + ["GEO-skeletion.spine_thoracic_t11", "GEO-skeletion.spine_thoracic_t12"]
UPPER = ["GEO-skeletion.ripcage", "GEO-skeletion.clavicle.L", "GEO-skeletion.clavicle.R",
         "GEO-skeletion.shoulder_scapula.L", "GEO-skeletion.shoulder_scapula.R"]
SKULL = "GEO-skeletion.skull"

HEAD_X = -0.22     # head on the left wing of the pillow; the rest of the pillow is in front of the face
SPINE_Z = 0.19     # spine height above the mattress while lying on the side (half shoulder width)
FLESH = 0.015      # soft tissue between skull and pillow
FLAT_TOP = 0.06    # a regular pillow under the weight of a head


def load_skeleton():
    names = [SKULL] + CERVICAL + THORACIC + UPPER
    with bpy.data.libraries.load(BUNDLE) as (src, dst):
        dst.objects = [n for n in src.objects if n in names]
    objs = {}
    for o in dst.objects:
        bpy.context.collection.objects.link(o)
        objs[o.name] = o
    bpy.context.view_layer.update()
    # bake modifiers (mirror / subsurf) and world transforms so we can move bones freely
    for o in objs.values():
        o.data = o.data.copy()  # several vertebrae share one mesh in the bundle
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
    bpy.ops.object.convert(target="MESH")
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return objs


def center(o):
    vs = [v.co for v in o.data.vertices]
    return sum(vs, Vector()) / len(vs)


def transform(o, m):
    o.data.transform(m)
    o.data.update()


def lowest_z(o):
    return min(v.co.z for v in o.data.vertices)


def material(kind):
    bone = bpy.data.materials.new("bone")
    N = ps.Nodes(bone)
    out = N.n("ShaderNodeOutputMaterial")
    b = N.n("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = (0.78, 0.74, 0.66, 1)
    b.inputs["Roughness"].default_value = 0.45
    b.inputs["Subsurface Weight"].default_value = 0.25
    b.inputs["Subsurface Radius"].default_value = (0.004, 0.003, 0.002)
    N.link(b.outputs[0], out.inputs["Surface"])

    neck = bpy.data.materials.new("neck")
    N = ps.Nodes(neck)
    out = N.n("ShaderNodeOutputMaterial")
    b = N.n("ShaderNodeBsdfPrincipled")
    bad = kind != "ataria"
    b.inputs["Base Color"].default_value = (0.9, 0.25, 0.18, 1) if bad else (0.8, 0.86, 0.9, 1)
    b.inputs["Roughness"].default_value = 0.4
    b.inputs["Emission Color"].default_value = (1.0, 0.12, 0.06, 1) if bad else (0.55, 0.85, 1.0, 1)
    b.inputs["Emission Strength"].default_value = 2.5 if bad else 0.6
    N.link(b.outputs[0], out.inputs["Surface"])
    return bone, neck


def axis_line(a, b, color, strength):
    """Thin glowing guide: the line the spine should follow."""
    mat = bpy.data.materials.new("guide")
    N = ps.Nodes(mat)
    out = N.n("ShaderNodeOutputMaterial")
    e = N.n("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*color, 1)
    e.inputs["Strength"].default_value = strength
    N.link(e.outputs[0], out.inputs["Surface"])
    d = b - a
    bpy.ops.mesh.primitive_cylinder_add(radius=0.0022, depth=d.length, location=(a + b) / 2)
    o = bpy.context.object
    o.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    o.data.materials.append(mat)
    o.visible_shadow = False
    return o


def pose(objs, kind, bend_fraction=1.0):
    # standing (z up, facing -y, left = +x)  ->  lying on the left side, head towards +y, facing +x, viewed from -x
    lie = Matrix(((0, -1, 0), (0, 0, 1), (-1, 0, 0))).to_4x4()
    for o in objs.values():
        transform(o, lie)
    c7, skull = objs[CERVICAL[6]], objs[SKULL]
    base = center(c7)
    move = Matrix.Translation(Vector((HEAD_X, -0.11, SPINE_Z)) - base)
    for o in objs.values():
        transform(o, move)

    neutral_bottom = lowest_z(skull)
    if kind == "ataria":
        target = None
    else:
        target = FLAT_TOP + FLESH
    # lateral flexion: rotate the head and C1..C6 joint by joint about the world x axis (towards the mattress)
    chain = [objs[n] for n in reversed(CERVICAL)] + [skull]  # c7, c6, ..., c1, skull
    joints = [center(o) for o in chain]

    def bend(total):
        step = total / 6
        for j in range(1, len(chain) - 1 + 1):
            if j >= len(chain):
                break
            pivot = (joints[j - 1] + joints[j]) / 2
            r = Matrix.Translation(pivot) @ Matrix.Rotation(step, 4, "X") @ Matrix.Translation(-pivot)
            for o in chain[j:]:
                transform(o, r)
            joints[j:] = [r @ p for p in joints[j:]]

    if target is not None:
        # find the angle where the skull rests on the flat pillow (head drops towards -z)
        lo, hi = 0.0, math.radians(45)
        snapshot = {o.name: [v.co.copy() for v in o.data.vertices] for o in chain}
        snap_joints = [p.copy() for p in joints]
        for _ in range(18):
            mid = (lo + hi) / 2
            for o in chain:
                for v, co in zip(o.data.vertices, snapshot[o.name]):
                    v.co = co
            joints[:] = [p.copy() for p in snap_joints]
            sign = 1
            bend(sign * mid)
            if lowest_z(skull) > neutral_bottom + 0.001 and mid > 0.01:  # wrong direction: flip
                for o in chain:
                    for v, co in zip(o.data.vertices, snapshot[o.name]):
                        v.co = co
                joints[:] = [p.copy() for p in snap_joints]
                bend(-mid)
            if lowest_z(skull) > target:
                lo = mid
            else:
                hi = mid
        # final pose at the found angle (optionally only part of it, for the animation)
        for o in chain:
            for v, co in zip(o.data.vertices, snapshot[o.name]):
                v.co = co
            o.data.update()
        joints[:] = [p.copy() for p in snap_joints]
        bend(lo * bend_fraction)
        test = lowest_z(skull)
        if test > neutral_bottom:
            for o in chain:
                for v, co in zip(o.data.vertices, snapshot[o.name]):
                    v.co = co
                o.data.update()
            joints[:] = [p.copy() for p in snap_joints]
            bend(-lo * bend_fraction)
        print("bend deg", round(math.degrees(lo * bend_fraction), 1))
    return neutral_bottom


def build(kind, bend_fraction=1.0):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scn = bpy.context.scene
    scn.render.engine = "CYCLES"
    scn.cycles.device = "CPU"
    scn.cycles.use_denoising = True
    scn.view_settings.view_transform = "AgX"
    scn.view_settings.look = "AgX - Medium High Contrast"
    world = bpy.data.worlds.new("w")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.01, 0.011, 0.014, 1)
    scn.world = world

    objs = load_skeleton()
    neutral_bottom = pose(objs, kind, bend_fraction)
    bone, neck = material(kind)
    for name, o in objs.items():
        o.data.materials.clear()
        o.data.materials.append(neck if name in CERVICAL else bone)
        for p in o.data.polygons:
            p.use_smooth = True

    # bed
    bpy.ops.mesh.primitive_plane_add(size=6, location=(0, 0, 0))
    bpy.context.object.data.materials.append(ps.simple_material("sheet", (0.05, 0.048, 0.05), 0.9, 30.0, 0.05))

    if kind == "ataria":
        pil = ps.build_pillow()
        pil.data.materials.append(ps.pillow_material())
        # sit the pillow so its wing meets the head (skull + soft tissue), as the foam gives under the head
        pil.location.z = neutral_bottom - FLESH - ps.height(HEAD_X, 0.03)
    else:
        bpy.ops.mesh.primitive_cube_add(location=(0.0, 0.0, FLAT_TOP / 2))
        p = bpy.context.object
        p.scale = (0.32, 0.22, FLAT_TOP / 2)
        bpy.ops.object.transform_apply(scale=True)
        bev = p.modifiers.new("bevel", "BEVEL")
        bev.width, bev.segments = 0.025, 8
        sub = p.modifiers.new("sub", "SUBSURF")
        sub.levels = sub.render_levels = 2
        bpy.ops.object.shade_smooth()
        p.data.materials.append(ps.simple_material("plain", (0.72, 0.71, 0.69), 0.85, 400.0, 0.1))

    # the ideal line: straight continuation of the thoracic spine
    t_mid = center(objs["GEO-skeletion.spine_thoracic_4"])
    c7 = center(objs[CERVICAL[6]])
    direction = (c7 - t_mid).normalized()
    color = (0.4, 1.0, 0.6) if kind == "ataria" else (1.0, 0.85, 0.3)
    axis_line(t_mid, c7 + direction * 0.30, color, 12.0)

    ps.add_area("key", (-1.0, -0.9, 1.3), (HEAD_X, -0.1, 0.18), (1.6, 1.2), 55, (1.0, 0.9, 0.8))
    ps.add_area("rim", (0.5, 0.9, 0.7), (HEAD_X, 0.0, 0.18), (0.6, 1.0), 35, (0.7, 0.8, 1.0))
    ps.add_area("fill", (-1.2, 0.6, 0.3), (HEAD_X, 0.0, 0.15), (1.0, 1.0), 10, (0.8, 0.85, 1.0))

    cam_data = bpy.data.cameras.new("cam")
    cam_data.lens = 62
    cam_data.dof.use_dof = True
    cam_data.dof.aperture_fstop = 4.0
    cam = bpy.data.objects.new("cam", cam_data)
    bpy.context.collection.objects.link(cam)
    cam.location = (HEAD_X - 1.5, -0.16, 0.26)
    target = Vector((HEAD_X, -0.12, 0.16))
    ps.look_at(cam, target)
    cam_data.dof.focus_distance = (target - cam.location).length
    scn.camera = cam
    return scn


if __name__ == "__main__":
    kind, out = sys.argv[1], sys.argv[2]
    samples = int(sys.argv[3]) if len(sys.argv) > 3 else 128
    frac = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
    scn = build(kind, frac)
    scn.cycles.samples = samples
    scn.render.resolution_x, scn.render.resolution_y = 1080, 1350
    scn.render.filepath = out
    bpy.ops.render.render(write_still=True)
