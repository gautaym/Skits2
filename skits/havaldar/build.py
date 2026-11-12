"""Build and (optionally) render "हवलदार का भौकाल".

Blender binary:  blender -b --factory-startup --python build.py -- [options]
bpy module:      python build.py [options]

Options:
  --out DIR            output folder (default: Output)
  --frames A-B         render this frame range to DIR/frames/####.png
  --stills a,b,...     render stills at these times (seconds) to DIR/still_<t>.png
  --res 1080           output width (height = 16:9 vertical); default 1080
  --samples 32         Cycles samples
  --save file.blend    save the built scene
"""
import argparse
import math
import os
import random
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import characters as C  # noqa: E402
import poses as P  # noqa: E402
import set_thana as S  # noqa: E402
import timeline as TL  # noqa: E402
from common import _fcurves as TL_fcurves  # noqa: E402
from common import collection, joint, key, mat, set_interp, sphere  # noqa: E402

T, f, FPS = TL.T, TL.f, TL.FPS
D = math.radians

P0 = Vector((0.4, 1.0, 0.0))      # Pandey stands here, facing +X (back to the wall end)
PL = Vector((0.7, 1.0, 0.0))      # ...and lands here, sitting
BALLOON_AT = Vector((-0.08, 0.78, 0.62))  # balloon right behind his backside
BABA_AT = Vector((1.75, 0.3, 0.0))


# ------------------------------------------------------------------- utils --

def place(name, loc, rot_z_deg, col):
    e = joint(name, None, loc, col)
    e.rotation_euler = (0, 0, D(rot_z_deg))
    return e


def hold(obj, frames, attr="location"):
    for fr in frames:
        obj.keyframe_insert(attr, frame=fr)


def evaluate(frame):
    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()


def world_center(objs):
    pts = [o.matrix_world.translation for o in objs]
    return sum(pts, Vector()) / len(pts)


def hide_until(objs, frame_show, frame_hide=None):
    """Scale 0 -> 1 visibility toggle (robust across engines, keyed CONSTANT)."""
    for o in objs:
        s0 = o.scale.copy()
        o.scale = (0, 0, 0)
        o.keyframe_insert("scale", frame=1)
        o.scale = s0
        o.keyframe_insert("scale", frame=frame_show)
        if frame_hide:
            o.scale = (0, 0, 0)
            o.keyframe_insert("scale", frame=frame_hide)
        set_interp(o, "CONSTANT")


# --------------------------------------------------------------- lip-sync --

def envelope(path, start_t):
    """Per-frame loudness 0..1 of an audio file, via ffmpeg. None if missing."""
    if not os.path.exists(path):
        return None
    try:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", "8000", "-f", "s16le", "-"],
                             capture_output=True, check=True).stdout
    except Exception:
        return None
    import array
    a = array.array("h", raw)
    hop = 8000 // FPS
    vals = []
    for i in range(0, len(a), hop):
        seg = a[i:i + hop]
        vals.append(math.sqrt(sum(x * x for x in seg) / max(1, len(seg))))
    peak = max(vals) or 1
    return [min(1.0, v / peak * 1.3) for v in vals]


def lipsync(rig, start_t, fname, dur, seed=0):
    env = envelope(TL.vo_path(fname), start_t)
    if env is None:  # placeholder chatter until the voice line exists
        rr = random.Random(seed)
        n = int(dur * FPS)
        env = []
        for i in range(n):
            syl = abs(math.sin(i * math.pi / rr.choice([3, 4, 5])))
            env.append(syl * rr.uniform(0.5, 1.0) if i < n - 2 else 0)
    f0 = f(start_t)
    last = None
    for i, v in enumerate(env + [0, 0]):
        v = round(v * 4) / 4
        if v != last:
            P.face(rig, f0 + i, mouth=v)
            last = v


# --------------------------------------------------------------- effects --

def star_burst(col, at, fb):
    """Cartoon POP star + DHAAAM! text, facing the bang camera."""
    import bmesh
    me = bpy.data.meshes.new("pop_star")
    bm = bmesh.new()
    pts = []
    for i in range(24):
        r = 0.55 if i % 2 == 0 else 0.25
        a = 2 * math.pi * i / 24
        pts.append(bm.verts.new((math.cos(a) * r, 0, math.sin(a) * r)))
    bm.faces.new(pts)
    bm.to_mesh(me)
    bm.free()
    star = bpy.data.objects.new("pop_star", me)
    col.objects.link(star)
    star.location = at + Vector((0, -0.15, 0))
    star.data.materials.append(mat("pop_yellow", (1.0, 0.75, 0.05), emission=((1.0, 0.7, 0.05), 6.0)))
    inner = sphere("pop_core", loc=(0, 0.01, 0), radius=0.2, scale=(1, 0.05, 1), m=mat("pop_white", (1, 1, 1),
                   emission=((1, 1, 0.9), 10.0)), col=col)
    inner.parent = star
    bpy.ops.object.text_add(location=at + Vector((0.45, -0.2, 0.62)), rotation=(D(90), 0, 0))
    txt = bpy.context.active_object
    txt.name = "dhaam_text"
    for c in txt.users_collection:
        c.objects.unlink(txt)
    col.objects.link(txt)
    txt.data.body = "DHAAAM!"
    txt.data.align_x = "CENTER"
    txt.data.size = 0.32
    txt.data.extrude = 0.03
    txt.data.offset = 0.012
    txt.data.materials.append(mat("pop_red", (0.9, 0.05, 0.02), emission=((1.0, 0.1, 0.02), 1.5)))
    for o, sc in ((star, 1.0), (txt, 1.0)):
        o.scale = (0, 0, 0)
        o.keyframe_insert("scale", frame=fb - 1)
        o.scale = (0.3 * sc,) * 3
        o.keyframe_insert("scale", frame=fb)
        o.scale = (1.15 * sc,) * 3
        o.keyframe_insert("scale", frame=fb + 3)
        o.scale = (1.0 * sc,) * 3
        o.keyframe_insert("scale", frame=fb + 9)
        o.scale = (0, 0, 0)
        o.keyframe_insert("scale", frame=fb + 13)
    key(star, fb, rot=(0, 0, 0))
    key(star, fb + 12, rot=(0, 25, 0))
    return star


def shreds(col, at, fb, n=14):
    """Yellow balloon shreds flying out and settling on the ground."""
    m = mat("balloon", (0.95, 0.62, 0.0))
    rr = random.Random(5)
    out = []
    for i in range(n):
        bpy.ops.mesh.primitive_plane_add(size=0.07, location=at)
        o = bpy.context.active_object
        o.name = f"shred{i}"
        for c in o.users_collection:
            c.objects.unlink(o)
        col.objects.link(o)
        o.data.materials.append(m)
        o.modifiers.new("thick", "SOLIDIFY").thickness = 0.004
        o.scale = (rr.uniform(0.6, 1.4), rr.uniform(0.4, 1.0), 1)
        s_full = o.scale.copy()
        a = rr.uniform(0, 2 * math.pi)
        d = rr.uniform(0.4, 1.4)
        land = at + Vector((math.cos(a) * d, math.sin(a) * d * 0.6, 0))
        land.z = 0.004
        peak = at.lerp(land, 0.4) + Vector((0, 0, rr.uniform(0.3, 0.8)))
        o.scale = (0, 0, 0)
        o.keyframe_insert("scale", frame=fb - 1)
        o.scale = s_full
        o.keyframe_insert("scale", frame=fb)
        key(o, fb, loc=at, rot=(0, 0, 0))
        key(o, fb + 5, loc=peak, rot=(rr.uniform(-400, 400), rr.uniform(-400, 400), rr.uniform(-200, 200)))
        key(o, fb + 16, loc=land, rot=(0, 0, rr.uniform(0, 360)))
        out.append(o)
    return out


def flies(col, around, f0, f1):
    """Three flies buzzing in circles over the havaldar's head."""
    body_m = mat("fly", (0.01, 0.01, 0.01), rough=0.3)
    wing_m = mat("fly_wing", (0.85, 0.9, 1.0), rough=0.1, emission=((0.6, 0.7, 0.8), 0.3))
    for k in range(3):
        fl = sphere(f"fly{k}", radius=0.018, scale=(1.4, 1, 1), m=body_m, col=col, segs=10, rings=6)
        for sx in (1, -1):
            w = sphere(f"fly{k}_w{sx}", loc=(0, sx * 0.02, 0.012), radius=0.02, scale=(1.2, 0.6, 0.12), m=wing_m,
                       col=col, segs=8, rings=4)
            w.parent = fl
        r = 0.35 + 0.1 * k
        for fr in range(f0, f1 + 1, 2):
            a = fr * (0.35 + 0.07 * k) + k * 2.1
            p = around + Vector((math.cos(a) * r, math.sin(a) * r * 0.7, 0.15 * math.sin(fr * 0.5 + k)))
            fl.location = p
            fl.keyframe_insert("location", frame=fr)
            fl.rotation_euler = (0, 0, a + math.pi / 2)
            fl.keyframe_insert("rotation_euler", frame=fr)
        hide_until([fl], 1, f1 + 1)


# --------------------------------------------------------------- cameras --

CAMS = []


def camera(name, loc, target, lens, t0, end_loc=None, t_end=None, col=None, shake=None):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_fit = "VERTICAL"
    cd.sensor_height = 24
    cam = bpy.data.objects.new(name, cd)
    col.objects.link(cam)
    cam.location = loc
    if isinstance(target, bpy.types.Object):
        tgt = target
    else:
        tgt = joint(name + "_target", None, target, col)
    c = cam.constraints.new("TRACK_TO")
    c.target = tgt
    c.track_axis = "TRACK_NEGATIVE_Z"
    c.up_axis = "UP_Y"
    if end_loc is not None:
        key(cam, f(t0), loc=loc)
        key(cam, f(t_end), loc=end_loc)
    if shake:
        fs, fe, amp = shake
        rr = random.Random(7)
        key(cam, fs - 1, loc=cam.location.copy())
        base = cam.location.copy()
        for fr in range(fs, fe):
            k = amp * (1 - (fr - fs) / (fe - fs))
            key(cam, fr, loc=base + Vector((rr.uniform(-k, k), rr.uniform(-k, k) * 0.3, rr.uniform(-k, k))))
        key(cam, fe, loc=base)
    m = bpy.context.scene.timeline_markers.new(name, frame=f(t0))
    m.camera = cam
    CAMS.append(cam)
    return cam


# ------------------------------------------------------------------- build --

def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = FPS
    sc.frame_start = 1
    sc.frame_end = f(T["out"]) - 1

    S.build_set()
    col = collection("cast")
    fx = collection("fx")
    cams = collection("cameras")

    pd = C.build_pandey(col)
    ch = C.build_chhotu(col)
    bb = C.build_baba(col)
    rifle = C.build_rifle(col)

    # world placement empties (roots stay free for pose leans / hops)
    pd_place = place("pandey_place", P0, 90, col)
    pd["root"].parent = pd_place
    ch_place = place("chhotu_place", (-2.75, 2.6, 0), 0, col)
    ch["root"].parent = ch_place
    bb_place = place("baba_place", (9, 0, 0), -110, col)
    bb["root"].parent = bb_place

    rl = TL.RIFLE_LOCAL
    rifle_space = place("rifle_space", P0, 90, col)
    rifle["root"].parent = rifle_space
    rifle["root"].location = (rl["loc"][0], rl["loc"][1], TL.rifle_ground_lift(rl["rot_x_deg"], rl["scale"]))
    rifle["root"].scale = (rl["scale"],) * 3
    key(rifle["root"], 1, rot=(rl["rot_x_deg"], 0, 0))

    fb, fl = f(T["bang"]), f(T["bang"] + 1.1)  # bang, landing

    animate_pandey(pd, pd_place, rifle, fb, fl, fx)
    animate_chhotu(ch, ch_place, fb)
    animate_baba(bb, bb_place)

    star_burst(fx, BALLOON_AT, fb)
    shreds(fx, BALLOON_AT, fb)
    flies(fx, P0 + Vector((0.05, 0, 2.25)), 1, f(T["setup"]))

    build_cameras(pd, ch, bb, cams, fb)
    return pd, ch, bb


def animate_pandey(pd, pd_place, rifle, fb, fl, fx):
    F = f
    # ---- smug lean, proud, half-lidded, breathing
    for t in (0, T["pat"] - 0.3, T["peek"], T["kaun"], T["hawa"], T["setup"]):
        P.pose(pd, F(t), "lean_folded")
    P.pose(pd, F(T["hook_low"] - 1.0), {"head": (-14, 0, 0)}, base="lean_folded")  # chin up during the hero intro
    P.face(pd, 1, lids=24, lidlo=48, brows=(0.012, 8), look=(8, 0))
    P.face(pd, F(10.75), lids=24, brows=(0.012, 8))
    for i, t in enumerate([x * 1.4 for x in range(int(T["bang"] / 1.4))]):
        key(pd["belly"], F(t), scale=(1.0, 1.0, 1.0))
        key(pd["belly"], F(t + 0.7), scale=(1.025, 1.035, 1.01))
    # moustache flutter in the "wind" during the hook
    for fr in range(1, F(T["hook_low"]), 3):
        a = 6 * math.sin(fr * 0.9)
        key(pd["must_L"], fr, rot=(0, a, a * 0.5))
        key(pd["must_R"], fr, rot=(0, -a, -a * 0.5))
    key(pd["must_L"], F(T["hook_low"]), rot=(0, 0, 0))
    key(pd["must_R"], F(T["hook_low"]), rot=(0, 0, 0))
    # belly pat "DHAB"
    tp = T["pat"]
    P.pose(pd, F(tp - 0.2), "pat_up", base="lean_folded")
    P.pose(pd, F(tp), "pat_down", base="lean_folded")
    P.pose(pd, F(tp + 0.2), "pat_up", base="lean_folded")
    P.pose(pd, F(tp + 0.45), "lean_folded")
    key(pd["belly"], F(tp), scale=(1.06, 1.08, 0.95))
    key(pd["belly"], F(tp + 0.15), scale=(1.0, 1.0, 1.0))
    # ---- "कौन है बे?" : head tilts, ear twitches, eyes stay half shut
    P.pose(pd, F(T["kaun"] + 0.15), "suspicious", base="lean_folded")
    for i in range(3):
        t = T["kaun"] + 0.2 + i * 0.18
        key(pd["ear_R"], F(t), scale=(0.45, 0.8, 1.0))
        key(pd["ear_R"], F(t + 0.08), scale=(0.6, 1.05, 1.25))
    key(pd["ear_R"], F(T["kaun"] + 0.9), scale=(0.45, 0.8, 1.0))
    P.face(pd, F(T["kaun"] + 0.1), lids=40, brows=(0.0, -12))
    # freeze: hold
    P.pose(pd, F(T["hawa"] - 0.05), "suspicious", base="lean_folded")
    # "हुंह... हवा है": snort, back to smug
    P.pose(pd, F(T["hawa"] + 0.35), {"head": (-18, 0, 0)}, base="lean_folded")
    P.pose(pd, F(T["hawa"] + 1.2), "lean_folded")
    P.face(pd, F(T["hawa"] + 0.3), lids=24, brows=(0.015, 10))
    P.pose(pd, fb - 4, "lean_folded")
    P.face(pd, fb - 1, lids=24, lidlo=48, brows=(0.015, 10))
    # ---- BANG: squash, rocket up, flail, fall, land sitting
    key(pd_place, 1, loc=P0)
    key(pd_place, fb, loc=P0)
    key(pd["root"], fb, loc=(0, 0, 0))
    key(pd["root"], fb + 2, loc=(0, 0, -0.08))
    P.pose(pd, fb + 3, "launch")
    key(pd["root"], fb + 9, loc=(0, -0.1, 1.5))
    P.pose(pd, fb + 9, "launch", base={"head": (-30, 0, 0)})
    key(pd["root"], fb + 14, loc=(0, -0.2, 1.35))
    key(pd_place, fl, loc=PL)
    P.pose(pd, fl - 4, "launch")
    key(pd["root"], fl, loc=(0, 0, -0.66))
    P.pose(pd, fl, "sit_pat")
    key(pd["root"], fl + 2, loc=(0, 0, -0.7))
    key(pd["root"], fl + 5, loc=(0, 0, -0.66))
    key(pd["belly"], fl, scale=(1.12, 1.12, 0.85))
    key(pd["belly"], fl + 4, scale=(0.96, 0.96, 1.06))
    key(pd["belly"], fl + 8, scale=(1.0, 1.0, 1.0))
    P.face(pd, fb + 1, lids=-75, lidlo=60, brows=(0.045, -15), look=(0, 0))
    # beret: rides the head (Child Of) until the bang, then flies free in world space and lands
    beret = pd["beret"]
    evaluate(1)
    local = beret.matrix_local.copy()
    beret.parent = None
    beret.matrix_world = local  # values now interpreted relative to the constraint
    co = beret.constraints.new("CHILD_OF")
    co.target = pd["head"]
    co.inverse_matrix.identity()
    co.influence = 1.0
    co.keyframe_insert("influence", frame=1)
    co.keyframe_insert("influence", frame=fb)
    evaluate(fb)
    w0 = beret.matrix_world.copy()
    co.influence = 0.0
    co.keyframe_insert("influence", frame=fb + 1)
    for fc in TL_fcurves(beret):
        for kp in fc.keyframe_points:
            kp.interpolation = "CONSTANT"
    p0 = w0.translation.copy()
    key(beret, fb, loc=local.translation, rot=tuple(math.degrees(a) for a in local.to_euler()))
    key(beret, fb + 1, loc=p0, rot=tuple(math.degrees(a) for a in w0.to_euler()))
    key(beret, fb + 8, loc=p0 + Vector((0.2, -0.3, 0.8)), rot=(180, 0, 540))
    key(beret, fb + 16, loc=p0 + Vector((0.5, -0.6, 0.9)), rot=(300, 40, 900))
    key(beret, fl + 6, loc=Vector((PL.x + 0.75, PL.y - 0.55, 0.035)), rot=(360, 0, 1100))
    # rifle loses its seat and topples
    rl = TL.RIFLE_LOCAL["rot_x_deg"]
    key(rifle["root"], fb + 1, rot=(rl, 0, 0))
    key(rifle["root"], fb + 11, rot=(88, 0, 0))
    key(rifle["root"], fb + 14, rot=(80, 0, 0))
    key(rifle["root"], fb + 17, rot=(88, 0, 0))
    # ---- on the ground: frantic patting, looking around
    t = T["bang"] + 1.2
    i = 0
    while t < T["baba"] - 0.2:
        alt = {"shoulder_L": (38 if i % 2 else 18, -38, 0), "elbow_L": (-35 if i % 2 else -10, 0, 0),
               "shoulder_R": (18 if i % 2 else 38, 38, 0), "elbow_R": (-10 if i % 2 else -35, 0, 0),
               "head": (10, 0, 25 if (i // 4) % 2 else -25)}
        P.pose(pd, F(t), alt, base="sit_pat")
        t += 0.2
        i += 1
    P.face(pd, fl + 1, lids=-70, lidlo=55, brows=(0.04, -18))
    # ---- Baba arrives: look up at him, sheepish; then fist shake at the end
    look_baba = {"head": (-22, 0, 45), "chest": (4, 0, 15)}
    P.pose(pd, F(T["baba"]), look_baba, base="sit_pat")
    P.pose(pd, F(T["end"] - 0.1), look_baba, base="sit_pat")
    P.face(pd, F(T["baba"]), lids=10, lidlo=50, brows=(0.02, -20))
    P.face(pd, F(T["nose"]), lids=-20, lidlo=50, brows=(0.035, -25), look=(0, -10))
    for i in range(6):
        t = T["end"] + 0.25 + i * 0.22
        shake = {"shoulder_R": (-5, 145 + (8 if i % 2 else -8), 0), "elbow_R": (-5 if i % 2 else -25, 0, 0),
                 "head": (-14, 0, -55), "chest": (0, 0, -25)}
        P.pose(pd, F(t), shake, base="sit_pat")
    P.face(pd, F(T["end"]), lids=0, brows=(-0.01, 28))  # angry: brows down & in
    # balloon shred stuck on his nose from the landing on
    shred = bpy.data.objects.new("nose_shred", bpy.data.meshes.new("nose_shred"))
    import bmesh
    bm = bmesh.new()
    vs = [bm.verts.new(v) for v in ((-0.04, 0, -0.02), (0.035, 0, -0.03), (0.045, 0, 0.025), (-0.01, 0, 0.04),
                                     (-0.05, 0, 0.01))]
    bm.faces.new(vs)
    bm.to_mesh(shred.data)
    bm.free()
    fx.objects.link(shred)
    shred.data.materials.append(mat("balloon", (0.95, 0.62, 0.0)))
    shred.modifiers.new("thick", "SOLIDIFY").thickness = 0.004
    shred.parent = pd["nose"]
    shred.location = (0.0, -0.075, 0.01)
    shred.rotation_euler = (D(-10), 0, D(12))
    hide_until([shred], fl)
    # lip-sync (placeholder chatter until the voice files exist)
    for fname, who, start, dur in TL.VO:
        if who == "pandey":
            lipsync(pd, start, fname, dur, seed=sum(map(ord, fname)))


def animate_chhotu(ch, ch_place, fb):
    F = f
    # balloon follows the hand's position only (never its rotation), floating upright above the fist
    bal, wr = ch["balloon"], ch["wrist_R"]
    bal.parent = None
    co = bal.constraints.new("CHILD_OF")
    co.target = wr
    co.use_rotation_x = co.use_rotation_y = co.use_rotation_z = False
    co.use_scale_x = co.use_scale_y = co.use_scale_z = False
    co.inverse_matrix.identity()
    key(bal, 1, loc=(0, 0, 0.04), rot=(0, 0, 0))
    # hidden behind the wall
    key(ch_place, 1, loc=(-2.75, 2.6, 0), rot=(0, 0, 0))
    P.pose(ch, 1, "rest")
    P.face(ch, 1, lids=-42, lidlo=48, brows=(0, 0), mouth=0)
    # ---- peek round the wall end: lean out to his right (-X)
    key(ch_place, F(T["peek"]) - 1, loc=(-2.75, 2.6, 0))
    key(ch_place, F(T["peek"]), loc=(-2.92, 2.62, 0), rot=(0, 0, 20))
    peek = {"root": (0, -18, 0), "chest": (0, -14, 0), "head": (0, 26, -20),
            "shoulder_R": (-150, 0, -15), "elbow_R": (-30, 0, 0),
            "shoulder_L": (-60, 0, -30), "elbow_L": (-125, 0, -20)}
    P.pose(ch, F(T["peek"]), peek)
    P.pose(ch, F(T["sneak"]) - 1, peek)
    key(ch_place, F(T["sneak"]) - 1, loc=(-2.92, 2.62, 0), rot=(0, 0, 20))
    P.face(ch, F(T["peek"]), lids=-30, brows={"L": (0.03, 15), "R": (-0.005, -10)}, look=(0, -25))
    P.face(ch, F(T["peek"] + 0.4), look=(0, -35))
    # ---- sneak: giant tiptoe steps round the corner toward Pandey's back
    path = [(T["sneak"], (-3.55, 2.3), 0), (T["sneak"] + 0.7, (-3.6, 1.35), 40),
            (T["sneak"] + 1.5, (-2.7, 0.95), 90), (T["kaun"] - 0.15, (-1.5, 0.85), 90)]
    P.pose(ch, F(T["sneak"]), "tiptoe_a")
    for t, (x, y), rz in path:
        key(ch_place, F(t), loc=(x, y, 0), rot=(0, 0, rz))
    t, i = T["sneak"], 0
    while t < T["kaun"] - 0.2:
        P.pose(ch, F(t), "tiptoe_a" if i % 2 == 0 else "tiptoe_b")
        key(ch["root"], F(t), loc=(0, 0, 0.0))
        key(ch["root"], F(t + 0.3), loc=(0, 0, 0.09))
        t += 0.6
        i += 1
    P.face(ch, F(T["sneak"]), lids=-20, brows=(0.02, -10), look=(0, 0))
    # ---- squeak + freeze on one leg, eyes wide
    P.pose(ch, F(T["kaun"] - 0.15), "tiptoe_a")
    key(ch["root"], F(T["kaun"] - 0.15), loc=(0, 0, 0.05))
    P.pose(ch, F(T["hawa"] + 1.2), "tiptoe_a")
    key(ch["root"], F(T["hawa"] + 1.2), loc=(0, 0, 0.05))
    P.face(ch, F(T["kaun"]), lids=-70, lidlo=65, brows=(0.04, 0), look=(10, 0))
    P.face(ch, F(T["hawa"] + 1.0), lids=-70, brows=(0.04, 0))
    # relief, then quick steps to the target
    P.face(ch, F(T["hawa"] + 1.4), lids=-30, brows=(0.02, -15))
    ch_target_t = T["setup"] - 0.05
    t, i = T["hawa"] + 1.3, 0
    while t < ch_target_t:
        P.pose(ch, F(t), "tiptoe_a" if i % 2 == 0 else "tiptoe_b")
        t += 0.3
        i += 1
    # ---- aim the balloon right behind the backside: solve placement so the balloon lands there
    P.pose(ch, F(T["setup"]), "aim")
    key(ch["root"], F(T["setup"]), loc=(0, 0, 0))
    # bring the balloon down into his hands, held out in front of him (world-axis offset from the wrist)
    fwd = Vector((math.sin(D(55)), -math.cos(D(55)), 0))
    key(bal, F(T["hawa"] + 1.3), loc=(0, 0, 0.04))
    key(bal, F(T["setup"]), loc=fwd * 0.17 + Vector((0, 0.05, -0.43)))
    key(ch_place, F(T["setup"]), loc=(-0.65, 0.78, 0), rot=(0, 0, 55))
    evaluate(F(T["setup"]))
    off = BALLOON_AT - world_center([o for o in ch["balloon_mesh"][:1]])
    off.z = 0
    final = Vector((-0.65, 0.78, 0)) + off
    key(ch_place, F(T["setup"]), loc=final, rot=(0, 0, 55))
    key(ch_place, F(T["hawa"] + 1.3), loc=(-1.5, 0.85, 0), rot=(0, 0, 90))
    P.pose(ch, fb - 1, "aim")
    key(ch_place, fb - 1, loc=final, rot=(0, 0, 55))
    # the gleam: eyes squint, glints flare
    P.face(ch, F(T["setup"] + 1.0), lids=5, lidlo=40, brows=(-0.01, 22))
    for s in ("L", "R"):
        g = bpy.data.objects[f"ch_glint_{s}"]
        key(g, F(T["setup"] + 1.0), scale=(1, 1, 1))
        key(g, F(T["setup"] + 1.4), scale=(2.6, 2.6, 2.6))
        key(g, fb - 1, scale=(2.6, 2.6, 2.6))
        key(g, fb, scale=(1, 1, 1))
    # ---- POP: balloon gone, Chhotu recoils, then laughs, then runs off
    hide_until(ch["balloon_mesh"], 1, fb)
    P.pose(ch, fb + 2, {"root": (-14, 0, 0), "shoulder_R": (-120, 0, 30), "shoulder_L": (-120, 0, -30),
                        "elbow_R": (-30, 0, 0), "elbow_L": (-30, 0, 0)})
    P.face(ch, fb + 1, lids=-70, brows=(0.04, 0), mouth=1.0)
    key(ch_place, fb + 12, loc=final + Vector((-0.5, -0.3, 0)), rot=(0, 0, 60))
    t, i = T["bang"] + 0.8, 0
    while t < T["run"]:
        P.pose(ch, F(t), {"chest": (18 if i % 2 else 8, 0, 0), "head": (-10 if i % 2 else 5, 0, 0),
                          "shoulder_L": (-40, 0, -50), "elbow_L": (-90, 0, -40),
                          "shoulder_R": (-40, 0, 50), "elbow_R": (-90, 0, 40)})
        P.face(ch, F(t), lids=60, lidlo=60, mouth=0.9 if i % 2 else 0.5, brows=(0.02, 15))
        t += 0.15
        i += 1
    run0, run1 = T["run"], T["run"] + 1.6
    key(ch_place, F(run0), loc=final + Vector((-0.5, -0.3, 0)), rot=(0, 0, -90))
    key(ch_place, F(run1), loc=(-5.5, 0.3, 0), rot=(0, 0, -90))
    t, i = run0, 0
    while t < run1:
        P.pose(ch, F(t), "run_a" if i % 2 == 0 else "run_b")
        t += 0.17
        i += 1
    for fname, who, start, dur in TL.VO:
        if who == "chhotu":
            lipsync(ch, start, fname, dur, seed=sum(map(ord, fname)))


def animate_baba(bb, bb_place):
    F = f
    key(bb_place, 1, loc=(9, 0, 0), rot=(0, 0, -110))
    key(bb_place, F(T["baba"]) - 1, loc=(9, 0, 0))
    key(bb_place, F(T["baba"]), loc=BABA_AT, rot=(0, 0, -123))
    set_interp(bb_place, "CONSTANT")
    P.pose(bb, F(T["baba"]), "lean_stick")
    tip = joint("baba_stick_tip", bb_place, (-0.28, -0.3, 0.0))
    dt = bb["stick"].constraints.new("DAMPED_TRACK")
    dt.target = tip
    dt.track_axis = "TRACK_NEGATIVE_Z"
    P.face(bb, F(T["baba"]), lids=18, lidlo=40, brows=(0.01, -10), look=(15, 0))
    # paan chewing: cheeks and mouth working between lines
    for fr in range(F(T["baba"]), F(T["out"]), 10):
        for s in ("L", "R"):
            ck = bb[f"cheek_{s}"]
            key(ck, fr, scale=(1.0, 0.9, 0.85))
            key(ck, fr + 5, scale=(1.18, 1.0, 0.95))
    # chuckle: "हें हें हें"
    for i in range(4):
        t = T["end"] - 0.9 + i * 0.18
        P.pose(bb, F(t), {"head": (8 if i % 2 else 18, 0, 6), "chest": (8 if i % 2 else 14, 0, 0)}, base="lean_stick")
    for fname, who, start, dur in TL.VO:
        if who == "baba":
            lipsync(bb, start, fname, dur, seed=sum(map(ord, fname)))


def build_cameras(pd, ch, bb, col, fb):
    h = pd["head"]
    camera("cam_hook", (2.5, -4.6, 0.95), (0.5, 1.0, 1.25), 30, T["hook"], end_loc=(1.55, -3.0, 1.1),
           t_end=T["hook_low"], col=col)
    camera("cam_hero_low", (2.5, -0.9, 0.75), (0.55, 1.0, 1.85), 24, T["hook_low"], col=col)
    camera("cam_peek", (-3.3, -1.7, 1.05), (-3.35, 2.4, 0.95), 48, T["peek"], col=col)
    sneak = camera("cam_sneak", (-1.4, -6.0, 1.5), (-1.4, 1.2, 0.9), 20, T["sneak"], col=col)
    camera("cam_kaun", (1.7, -0.1, 2.0), h, 38, T["kaun"], col=col)
    m = bpy.context.scene.timeline_markers.new("cam_freeze", frame=f(T["freeze"]))
    m.camera = sneak
    camera("cam_hawa", (1.95, -1.05, 1.45), h, 32, T["hawa"], col=col)
    camera("cam_setup", (0.3, -1.15, 1.2), BALLOON_AT + Vector((-0.25, 0, 0.2)), 26, T["setup"],
           end_loc=(0.25, -0.9, 1.15), t_end=T["bang"], col=col)
    camera("cam_bang", (0.5, -3.7, 1.35), (0.45, 1.0, 1.55), 24, T["bang"], col=col, shake=(fb, fb + 12, 0.08))
    camera("cam_ground", (0.9, -3.4, 0.85), (0.6, 1.0, 0.55), 26, T["ground"], col=col)
    camera("cam_frantic", (2.0, -1.25, 0.8), h, 30, T["frantic"], col=col)
    camera("cam_baba", (0.25, -0.55, 0.28), bb["head"], 22, T["baba"], col=col)
    camera("cam_nose", (1.95, 1.7, 1.25), h, 32, T["nose"], col=col)
    camera("cam_end", (0.5, -2.3, 1.0), h, 28, T["end"], col=col)
    # extra cuts for a fast-paced reel (nothing held longer than ~3 s except the freeze)
    camera("cam_pat", (1.7, -1.3, 1.35), pd["belly"], 30, T["pat"] - 0.8, col=col)
    camera("cam_ground_face", (2.5, 0.75, 1.1), h, 26, T["ground"] + 2.0, col=col)
    run_m = bpy.context.scene.timeline_markers.new("cam_run", frame=f(T["run"]))
    run_m.camera = bpy.data.objects["cam_ground"]
    camera("cam_baba_cu", (0.95, 0.95, 1.45), bb["head"], 26, T["baba"] + 2.4, col=col)
    camera("cam_two_shot", (0.5, -2.6, 1.1), (1.2, 0.7, 1.0), 28, T["nose"] + 2.8, col=col)
    bpy.context.scene.camera = CAMS[0]


# ------------------------------------------------------------------ render --

def setup_render(res=1080, samples=32):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 4
    sc.cycles.diffuse_bounces = 2
    sc.cycles.glossy_bounces = 2
    sc.cycles.transmission_bounces = 2
    sc.render.resolution_x = res
    sc.render.resolution_y = int(res * 16 / 9)
    sc.render.resolution_percentage = 100
    sc.view_settings.view_transform = "AgX"
    try:
        sc.view_settings.look = "AgX - Punchy"
    except TypeError:
        pass
    sc.render.use_freestyle = True
    sc.render.line_thickness_mode = "ABSOLUTE"
    sc.render.line_thickness = 2.0 * res / 1080
    vl = sc.view_layers[0]
    ls = vl.freestyle_settings.linesets[0]
    ls.select_by_visibility = True
    ls.select_by_edge_types = True
    ls.select_silhouette = True
    ls.select_border = True
    ls.select_crease = False
    ls.linestyle = ls.linestyle or bpy.data.linestyles.new("ink")
    ls.linestyle.color = (0.05, 0.03, 0.02)
    sc.render.image_settings.file_format = "PNG"


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="Output")
    ap.add_argument("--frames", default="")
    ap.add_argument("--stills", default="")
    ap.add_argument("--res", type=int, default=1080)
    ap.add_argument("--samples", type=int, default=32)
    ap.add_argument("--save", default="")
    a = ap.parse_args(argv)
    build()
    setup_render(a.res, a.samples)
    sc = bpy.context.scene
    os.makedirs(a.out, exist_ok=True)
    if a.save:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.save))
    if a.stills:
        for t in a.stills.split(","):
            fr = f(float(t))
            sc.frame_set(fr)
            sc.render.filepath = os.path.join(os.path.abspath(a.out), f"still_{float(t):05.2f}.png")
            bpy.ops.render.render(write_still=True)
    if a.frames:
        s, e = (int(x) for x in a.frames.split("-"))
        sc.frame_start, sc.frame_end = s, min(e, sc.frame_end)
        sc.render.filepath = os.path.join(os.path.abspath(a.out), "frames", "")
        bpy.ops.render.render(animation=True)


if __name__ == "__main__":
    main()
