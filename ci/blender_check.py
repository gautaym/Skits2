"""Headless Blender environment check for making video skits.

Run with the Blender binary:
    blender -b --factory-startup --python ci/blender_check.py -- --out Output [--voice Output/voice.wav]
or with the `bpy` Python module:
    python ci/blender_check.py --out Output

Builds a tiny two-character scene (keyframed walk, head bobs, camera dolly,
3D caption, optional voice track), renders test stills with each available
engine, renders the full clip to MP4 and writes Output/blender-report.txt.
"""
import argparse
import math
import os
import platform
import sys
import time

import bpy

W, H, FPS, SECONDS = 720, 1280, 24, 3  # vertical 9:16 for Shorts/Reels
FRAMES = FPS * SECONDS

lines = []


def log(s=""):
    lines.append(s)
    print("[blender-check] " + s, flush=True)


def check(name, ok, detail=""):
    log(f"{'PASS' if ok else 'FAIL'} | {name} | {detail}")
    return ok


def info(name, detail):
    log(f"INFO | {name} | {detail}")


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="Output")
    p.add_argument("--voice", default="")
    p.add_argument("--engines", default="EEVEE,Cycles,Workbench",
                   help="comma list; EEVEE/Workbench need OpenGL and abort Blender without it")
    p.add_argument("--skip-mp4", action="store_true")
    p.add_argument("--report", default="blender-report.txt")
    return p.parse_args(argv)


# ---------------------------------------------------------------- scene ----

def mat(name, rgb):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*rgb, 1)
    bsdf.inputs["Roughness"].default_value = 0.6
    return m


def add(obj_op, name, material, **kw):
    obj_op(**kw)
    o = bpy.context.active_object
    o.name = name
    if material:
        o.data.materials.append(material)
    return o


def make_character(name, rgb, x):
    root = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(root)
    root.location = (x, 0, 0)
    body = add(bpy.ops.mesh.primitive_cylinder_add, name + " body", mat(name + " body", rgb),
               radius=0.45, depth=1.6, location=(0, 0, 0.8))
    head = add(bpy.ops.mesh.primitive_uv_sphere_add, name + " head", mat(name + " skin", (1.0, 0.8, 0.65)),
               radius=0.4, location=(0, 0, 2.0))
    bpy.ops.object.shade_smooth()
    for part in (body, head):
        part.parent = root
    return root, head


def build_scene(voice):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = W, H
    sc.render.fps = FPS
    sc.frame_start, sc.frame_end = 1, FRAMES

    world = bpy.data.worlds.new("World")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.05, 0.06, 0.1, 1)
    sc.world = world

    add(bpy.ops.mesh.primitive_plane_add, "Ground", mat("Ground", (0.25, 0.5, 0.25)), size=30)

    bpy.ops.object.light_add(type="SUN", rotation=(0.8, 0.2, 0.6))
    bpy.context.active_object.data.energy = 4

    a_root, a_head = make_character("Actor A", (0.85, 0.2, 0.2), -2.5)
    b_root, b_head = make_character("Actor B", (0.2, 0.35, 0.9), 2.5)

    bpy.ops.object.text_add(location=(0, 0, 3.4), rotation=(1.5708, 0, 0))
    cap = bpy.context.active_object
    cap.data.body = "Skits2 render test"
    cap.data.align_x = "CENTER"
    cap.data.size = 0.45
    cap.data.extrude = 0.03
    cap.data.materials.append(mat("Caption", (1, 1, 1)))

    bpy.ops.object.camera_add()
    cam = bpy.context.active_object
    sc.camera = cam
    target = bpy.data.objects.new("CamTarget", None)
    sc.collection.objects.link(target)
    target.location = (0, 0, 1.7)
    cons = cam.constraints.new("TRACK_TO")
    cons.target = target

    # Keyframes: actors walk toward each other, heads bob like talking, camera dollies in.
    for f in range(1, FRAMES + 1):
        t = (f - 1) / FPS
        k = min(t / 2.0, 1.0)
        a_root.location.x = -2.5 + 1.6 * k
        b_root.location.x = 2.5 - 1.6 * k
        a_root.keyframe_insert("location", frame=f)
        b_root.keyframe_insert("location", frame=f)
        if f % 2 == 1:
            a_head.location.z = 2.0 + abs(math.sin(t * 12)) * 0.08
            b_head.location.z = 2.0 + abs(math.sin(t * 9 + 1)) * 0.08
            a_head.keyframe_insert("location", frame=f)
            b_head.keyframe_insert("location", frame=f)
    cam.location = (0, -12, 2.4)
    cam.keyframe_insert("location", frame=1)
    cam.location = (1.2, -8.5, 2.2)
    cam.keyframe_insert("location", frame=FRAMES)

    if voice and os.path.exists(voice):
        sc.sequence_editor_create()
        sc.sequence_editor.sequences.new_sound("voice", voice, channel=1, frame_start=1)
        info("Voice track", f"added {os.path.basename(voice)} to the sequencer")
    return sc


# ---------------------------------------------------------------- checks ---

def set_engine(sc, candidates):
    for e in candidates:
        try:
            sc.render.engine = e
            return e
        except TypeError:
            continue
    return None


def image_has_content(path):
    img = bpy.data.images.load(path)
    px = list(img.pixels[:])
    bpy.data.images.remove(img)
    lum = [0.3 * px[i] + 0.59 * px[i + 1] + 0.11 * px[i + 2] for i in range(0, len(px), 4 * 97)]
    mean = sum(lum) / len(lum)
    var = sum((v - mean) ** 2 for v in lum) / len(lum)
    return var > 0.002, f"luminance mean {mean:.2f}, variance {var:.4f}"


def render_still(sc, engine_ids, label, out):
    eng = set_engine(sc, engine_ids)
    if not eng:
        return check(f"{label} engine available", False, "/".join(engine_ids) + " not found"), None
    if eng == "CYCLES":
        sc.cycles.device = "CPU"
        sc.cycles.samples = 16
        sc.cycles.use_denoising = False
    path = os.path.join(out, f"still_{label.lower()}.png")
    sc.frame_set(FRAMES // 2)
    sc.render.image_settings.file_format = "PNG"
    sc.render.filepath = path
    t0 = time.time()
    try:
        bpy.ops.render.render(write_still=True)
    except Exception as e:  # EEVEE fails without an OpenGL context
        return check(f"{label} still render", False, str(e).splitlines()[0]), None
    secs = time.time() - t0
    ok, detail = image_has_content(path) if os.path.exists(path) else (False, "no file written")
    check(f"{label} still render ({eng})", ok, f"{secs:.1f}s/frame at {W}x{H}; {detail}")
    return ok, (eng, secs)


def main():
    args = parse_args()
    out = os.path.abspath(args.out)
    os.makedirs(out, exist_ok=True)
    voice = os.path.abspath(args.voice) if args.voice else ""

    log("== System ==")
    info("Blender", bpy.app.version_string)
    info("Python", platform.python_version())
    info("Machine", f"{platform.platform()}, {os.cpu_count()} CPUs")
    log("")
    log("== Checks ==")

    sc = build_scene(voice)
    check("Build scene (meshes, materials, 3D text, keyframes)", True,
          f"{len(bpy.data.objects)} objects, {FRAMES} frames @ {FPS}fps")

    import addon_utils
    for mod, why in (("io_scene_fbx", "import Mixamo/FBX characters"),
                     ("io_scene_gltf2", "import glTF characters")):
        found = any(m.__name__ == mod for m in addon_utils.modules())
        info(f"Add-on {mod}", ("available" if found else "not bundled") + f" ({why})")

    engine_ids = {"EEVEE": ["BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"],
                  "Cycles": ["CYCLES"], "Workbench": ["BLENDER_WORKBENCH"]}
    results = {}
    for label in [e.strip() for e in args.engines.split(",") if e.strip()]:
        ok, r = render_still(sc, engine_ids[label], label, out)
        if ok:
            results[label] = r
    if args.skip_mp4:
        pick = None
    else:
        # Full clip with the best engine that produced a real image (prefer EEVEE: fastest).
        pick = next((k for k in ("EEVEE", "Cycles", "Workbench") if k in results), None)
    if args.skip_mp4:
        pass
    elif pick:
        eng, _ = results[pick]
        set_engine(sc, [eng])
        r = sc.render
        r.image_settings.file_format = "FFMPEG"
        r.ffmpeg.format = "MPEG4"
        r.ffmpeg.codec = "H264"
        r.ffmpeg.constant_rate_factor = "MEDIUM"
        r.ffmpeg.audio_codec = "AAC" if voice else "NONE"
        mp4 = os.path.join(out, "skit_test.mp4")
        r.filepath = mp4
        t0 = time.time()
        bpy.ops.render.render(animation=True)
        secs = time.time() - t0
        size = os.path.getsize(mp4) if os.path.exists(mp4) else 0
        check(f"Render {FRAMES}-frame MP4 with {pick}" + (" + voice" if voice else ""), size > 10_000,
              f"{size // 1024} KB in {secs:.0f}s ({secs / FRAMES:.2f}s/frame)")
    else:
        check("Render MP4", False, "no engine produced a usable image")

    path = os.path.join(out, args.report)
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
