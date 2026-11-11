"""Shared helpers for building the skit procedurally in Blender."""
import math
import random

import bmesh
import bpy
from mathutils import Euler, Vector

# ------------------------------------------------------------ collections --

def collection(name, parent=None):
    col = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    parent = parent or bpy.context.scene.collection
    if col.name not in [c.name for c in parent.children]:
        parent.children.link(col)
    return col


def link(obj, col):
    for c in obj.users_collection:
        c.objects.unlink(obj)
    col.objects.link(obj)
    return obj


# -------------------------------------------------------------- materials --

_mats = {}


def mat(name, color, rough=0.6, metal=0.0, sss=0.0, spec=0.3, emission=None, coat=0.0):
    """Principled material, cached by name."""
    if name in _mats:
        return _mats[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Specular IOR Level"].default_value = spec
    b.inputs["Coat Weight"].default_value = coat
    if sss:
        b.inputs["Subsurface Weight"].default_value = sss
        b.inputs["Subsurface Radius"].default_value = (0.9, 0.35, 0.2)
        b.inputs["Subsurface Scale"].default_value = 0.02
    if emission:
        b.inputs["Emission Color"].default_value = (*emission[0], 1)
        b.inputs["Emission Strength"].default_value = emission[1]
    m.diffuse_color = (*color, 1)
    _mats[name] = m
    return m


def noise_mat(name, c1, c2, scale=8.0, rough=0.8, detail=6.0, bump=0.2, mix_c3=None, scale2=2.0):
    """Material mixing two (or three) colours with noise, plus bump: walls, ground, wood."""
    if name in _mats:
        return _mats[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    n, l = nt.nodes, nt.links
    b = n["Principled BSDF"]
    b.inputs["Roughness"].default_value = rough
    b.inputs["Specular IOR Level"].default_value = 0.2
    tc = n.new("ShaderNodeTexCoord")
    nz = n.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = scale
    nz.inputs["Detail"].default_value = detail
    l.new(tc.outputs["Object"], nz.inputs["Vector"])
    ramp = n.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*c1, 1)
    ramp.color_ramp.elements[1].color = (*c2, 1)
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[1].position = 0.7
    l.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    col_out = ramp.outputs["Color"]
    if mix_c3:
        nz2 = n.new("ShaderNodeTexNoise")
        nz2.inputs["Scale"].default_value = scale2
        l.new(tc.outputs["Object"], nz2.inputs["Vector"])
        r2 = n.new("ShaderNodeValToRGB")
        r2.color_ramp.elements[0].position = 0.55
        r2.color_ramp.elements[1].position = 0.6
        mix = n.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        l.new(nz2.outputs["Fac"], r2.inputs["Fac"])
        l.new(r2.outputs["Color"], mix.inputs["Factor"])
        l.new(col_out, mix.inputs["A"])
        mix.inputs["B"].default_value = (*mix_c3, 1)
        col_out = mix.outputs["Result"]
    l.new(col_out, b.inputs["Base Color"])
    if bump:
        bp = n.new("ShaderNodeBump")
        bp.inputs["Strength"].default_value = bump
        l.new(nz.outputs["Fac"], bp.inputs["Height"])
        l.new(bp.outputs["Normal"], b.inputs["Normal"])
    m.diffuse_color = (*c1, 1)
    _mats[name] = m
    return m


def set_mat(obj, m):
    obj.data.materials.clear()
    obj.data.materials.append(m)
    return obj


# ------------------------------------------------------------- primitives --

def _new_obj(name, mesh, col):
    o = bpy.data.objects.new(name, mesh)
    (col or bpy.context.scene.collection).objects.link(o)
    return o


def sphere(name, loc=(0, 0, 0), scale=(1, 1, 1), radius=1.0, m=None, col=None, segs=32, rings=16,
           smooth=True, subsurf=0):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=rings, radius=radius)
    bm.to_mesh(me)
    bm.free()
    o = _new_obj(name, me, col)
    o.location, o.scale = loc, scale
    finish(o, m, smooth, subsurf)
    return o


def hemisphere(name, radius=1.0, m=None, col=None, keep="top"):
    """Half sphere shell, e.g. eyelids (rotate to open/close)."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=radius)
    kill = [v for v in bm.verts if (v.co.z < -1e-4 if keep == "top" else v.co.z > 1e-4)]
    bmesh.ops.delete(bm, geom=kill, context="VERTS")
    bm.to_mesh(me)
    bm.free()
    o = _new_obj(name, me, col)
    sol = o.modifiers.new("thick", "SOLIDIFY")
    sol.thickness = radius * 0.08
    finish(o, m, True)
    return o


def box(name, loc=(0, 0, 0), size=(1, 1, 1), m=None, col=None, bevel=0.0, rot=(0, 0, 0)):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bm.to_mesh(me)
    bm.free()
    o = _new_obj(name, me, col)
    o.location, o.scale, o.rotation_euler = loc, size, rot
    if bevel:
        bv = o.modifiers.new("bevel", "BEVEL")
        bv.width = bevel
        bv.segments = 3
        bv.use_clamp_overlap = True
        bv.affect = "EDGES"
        # bevel width is in local space: keep it uniform under non-uniform scale
        bpy.context.view_layer.objects.active = o
    finish(o, m, smooth=False)
    if bevel:
        apply_scale(o)
    return o


def cylinder(name, loc=(0, 0, 0), r=0.1, depth=1.0, r2=None, m=None, col=None, segs=32, rot=(0, 0, 0),
             smooth=True, cap=True):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=cap, segments=segs, radius1=r, radius2=r if r2 is None else r2,
                          depth=depth)
    bm.to_mesh(me)
    bm.free()
    o = _new_obj(name, me, col)
    o.location, o.rotation_euler = loc, rot
    finish(o, m, smooth)
    return o


def torus(name, loc=(0, 0, 0), R=0.5, r=0.1, m=None, col=None, rot=(0, 0, 0), scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, major_segments=48, minor_segments=16,
                                     location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    o.scale = scale
    if col:
        link(o, col)
    finish(o, m, True)
    return o


def capsule(name, a, b, r, r2=None, m=None, col=None):
    """Rounded limb between points a and b (radius r at a, r2 at b)."""
    a, b = Vector(a), Vector(b)
    r2 = r if r2 is None else r2
    d = b - a
    o = cylinder(name, loc=(a + b) / 2, r=r, r2=r2, depth=d.length, m=m, col=col, cap=False)
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d)
    e1 = sphere(name + "_a", loc=a, radius=r, m=m, col=col, segs=24, rings=12)
    e2 = sphere(name + "_b", loc=b, radius=r2, m=m, col=col, segs=24, rings=12)
    o = join([o, e1, e2], name)
    # fuse into one closed surface: no internal faces, so no stray outline dashes
    rm = o.modifiers.new("fuse", "REMESH")
    rm.mode = "VOXEL"
    rm.voxel_size = max(min(r, r2) / 5.0, 0.0025)
    apply_mods(o)
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def curve_tube(name, pts, bevel=0.02, m=None, col=None, taper=None, resolution=12, cyclic=False):
    """Smooth bezier tube through pts. taper: list of radii per point."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = bevel
    cu.bevel_resolution = 6
    cu.resolution_u = resolution
    cu.use_fill_caps = True
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        bp = sp.bezier_points[i]
        bp.co = p
        bp.handle_left_type = bp.handle_right_type = "AUTO"
        if taper:
            bp.radius = taper[i]
    sp.use_cyclic_u = cyclic
    o = _new_obj(name, cu, col)
    if m:
        cu.materials.append(m)
    return o


def finish(o, m=None, smooth=True, subsurf=0):
    if m:
        set_mat(o, m)
    if smooth and o.type == "MESH":
        for p in o.data.polygons:
            p.use_smooth = True
    if subsurf:
        s = o.modifiers.new("subsurf", "SUBSURF")
        s.levels = s.render_levels = subsurf
    return o


def select_only(objs):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]


def apply_scale(o):
    select_only([o])
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)


def apply_mods(o):
    select_only([o])
    for md in list(o.modifiers):
        bpy.ops.object.modifier_apply(modifier=md.name)


def join(objs, name):
    for o in objs:
        if o.modifiers:
            apply_mods(o)
    select_only(objs)
    bpy.ops.object.join()
    o = bpy.context.active_object
    o.name = name
    return o


def to_mesh(o):
    select_only([o])
    bpy.ops.object.convert(target="MESH")
    return bpy.context.active_object


# ------------------------------------------------------------ rig helpers --

def joint(name, parent=None, loc=(0, 0, 0), col=None):
    """An empty used as an FK joint; children follow it."""
    e = bpy.data.objects.new(name, None)
    e.empty_display_size = 0.05
    e.rotation_mode = "XYZ"
    (col or bpy.context.scene.collection).objects.link(e)
    if parent:
        e.parent = parent
    e.location = loc
    return e


def attach(child, parent):
    """Parent keeping world transform."""
    mw = child.matrix_world.copy()
    child.parent = parent
    child.matrix_parent_inverse = parent.matrix_world.inverted()
    child.matrix_world = mw
    return child


def key(obj, frame, loc=None, rot=None, scale=None, interp=None):
    """Keyframe object transforms. rot in degrees."""
    if loc is not None:
        obj.location = loc
        obj.keyframe_insert("location", frame=frame)
    if rot is not None:
        obj.rotation_euler = Euler([math.radians(a) for a in rot], "XYZ")
        obj.keyframe_insert("rotation_euler", frame=frame)
    if scale is not None:
        obj.scale = scale if not isinstance(scale, (int, float)) else (scale,) * 3
        obj.keyframe_insert("scale", frame=frame)
    if interp and obj.animation_data and obj.animation_data.action:
        for fc in _fcurves(obj):
            for kp in fc.keyframe_points:
                if int(round(kp.co.x)) == frame:
                    kp.interpolation = interp


def _fcurves(obj):
    act = obj.animation_data.action
    if hasattr(act, "fcurves") and len(act.fcurves):
        return act.fcurves
    # Blender 4.4+ layered actions
    out = []
    for layer in getattr(act, "layers", []):
        for strip in layer.strips:
            for bag in strip.channelbags:
                out.extend(bag.fcurves)
    return out


def set_interp(obj, interp="CONSTANT"):
    if obj.animation_data and obj.animation_data.action:
        for fc in _fcurves(obj):
            for kp in fc.keyframe_points:
                kp.interpolation = interp


def rng(seed):
    return random.Random(seed)
