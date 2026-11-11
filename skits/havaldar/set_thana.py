"""The village thana (police outpost) set.

Layout (metres): compound wall runs along X at y=WALL_Y, gate gap between
x=GATE_X0..GATE_X1. A short return wall at x=CORNER_X comes toward camera
(Chhotu peeks round its front edge). Cameras look roughly toward +Y.
"""
import math
import random

import bmesh
import bpy
from mathutils import Vector

from common import box, collection, curve_tube, cylinder, join, mat, noise_mat, sphere, torus

D = math.radians
WALL_Y = 2.2
WALL_H = 2.4
GATE_X0, GATE_X1 = 1.0, 2.7
CORNER_X = -3.0
CORNER_FRONT_Y = 0.2
TREE_POS = (3.6, 0.6)


def wall_materials():
    green = noise_mat("wall_green", (0.36, 0.5, 0.33), (0.45, 0.6, 0.42), scale=3.0, rough=0.95, bump=0.25,
                      mix_c3=(0.3, 0.33, 0.22), scale2=1.2)
    return green


def build_ground(col):
    m = noise_mat("ground", (0.4, 0.27, 0.15), (0.55, 0.42, 0.27), scale=0.6, rough=1.0, bump=0.35,
                  mix_c3=(0.33, 0.22, 0.12), scale2=0.25)
    g = box("ground", loc=(0, 0, -0.05), size=(80, 80, 0.1), m=m, col=col)
    # scattered small stones, joined into one mesh
    rr = random.Random(4)
    stones = []
    sm = noise_mat("stone", (0.32, 0.28, 0.24), (0.5, 0.45, 0.38), scale=12, rough=0.9, bump=0.3)
    for i in range(140):
        x, y = rr.uniform(-7, 7), rr.uniform(-4, 5)
        if abs(x) < 0.7 and -0.4 < y < 1.2:  # keep Pandey's spot clear
            continue
        s = rr.uniform(0.015, 0.06)
        st = sphere(f"stone{i}", loc=(x, y, s * 0.3), radius=s, segs=8, rings=5,
                    scale=(1, rr.uniform(0.6, 1.2), rr.uniform(0.4, 0.7)), m=sm, col=col, smooth=False)
        st.rotation_euler = (0, 0, rr.uniform(0, 6.3))
        stones.append(st)
    join(stones, "stones")
    # dry grass tufts along the wall base
    gm = mat("dry_grass", (0.35, 0.3, 0.1), rough=0.9)
    tufts = []
    for i in range(40):
        x = rr.uniform(-4.4, 4.4)
        if GATE_X0 - 0.1 < x < GATE_X1 + 0.1:
            continue
        for k in range(5):
            a = rr.uniform(0, 6.3)
            h = rr.uniform(0.08, 0.2)
            b = Vector((x + rr.uniform(-0.05, 0.05), WALL_Y - 0.2 + rr.uniform(-0.05, 0.05), 0))
            tip = b + Vector((math.cos(a) * h * 0.4, math.sin(a) * h * 0.4, h))
            tufts.append(curve_tube(f"grass{i}_{k}", [b, (b + tip) / 2 + Vector((0, 0, 0.02)), tip], bevel=0.004,
                                    m=gm, col=col, taper=[1, 0.6, 0.1], resolution=4))
    return g


def build_wall(col):
    green = wall_materials()
    cap_m = noise_mat("wall_cap", (0.45, 0.55, 0.42), (0.55, 0.62, 0.5), scale=5, rough=0.9, bump=0.2)
    t = 0.3
    parts = []
    # main wall, left of gate and right of gate
    for x0, x1 in ((CORNER_X - 0.15, GATE_X0), (GATE_X1, 6.5)):
        w = x1 - x0
        parts.append(box(f"wall_{x0:.1f}", loc=((x0 + x1) / 2, WALL_Y, WALL_H / 2), size=(w, t, WALL_H),
                         m=green, col=col, bevel=0.03))
        parts.append(box(f"wallcap_{x0:.1f}", loc=((x0 + x1) / 2, WALL_Y, WALL_H + 0.04), size=(w + 0.04, t + 0.08, 0.08),
                         m=cap_m, col=col, bevel=0.02))
    # return wall toward camera (Chhotu's peeking corner)
    ly = WALL_Y - CORNER_FRONT_Y
    box("wall_return", loc=(CORNER_X, (WALL_Y + CORNER_FRONT_Y) / 2, WALL_H / 2), size=(t, ly, WALL_H),
        m=green, col=col, bevel=0.03)
    box("wall_return_cap", loc=(CORNER_X, (WALL_Y + CORNER_FRONT_Y) / 2, WALL_H + 0.04), size=(t + 0.08, ly + 0.04, 0.08),
        m=cap_m, col=col, bevel=0.02)
    # gate pillars with pyramid caps
    for x in (GATE_X0 - 0.2, GATE_X1 + 0.2):
        box(f"pillar_{x:.1f}", loc=(x, WALL_Y, 1.4), size=(0.45, 0.45, 2.8), m=green, col=col, bevel=0.03)
        box(f"pillarcap_{x:.1f}", loc=(x, WALL_Y, 2.85), size=(0.55, 0.55, 0.1), m=cap_m, col=col, bevel=0.02)
        cylinder(f"pillartop_{x:.1f}", loc=(x, WALL_Y, 3.02), r=0.2, r2=0.02, depth=0.26, segs=4, m=cap_m, col=col,
                 rot=(0, 0, D(45)), smooth=False)
    # dirty skirting band near ground
    dirt = noise_mat("wall_dirt", (0.25, 0.25, 0.16), (0.33, 0.36, 0.24), scale=6, rough=1.0, bump=0.2)
    box("wall_skirt", loc=((CORNER_X + 6.5) / 2, WALL_Y - 0.155, 0.18), size=(9.6, 0.02, 0.36), m=dirt, col=col)
    # peeling plaster patch: irregular blob showing brick + raw plaster
    build_peel(col, Vector((-1.7, WALL_Y - t / 2 - 0.004, 1.35)), 0.55, seed=3)
    build_peel(col, Vector((4.6, WALL_Y - t / 2 - 0.004, 0.75)), 0.3, seed=8)


def build_peel(col, center, size, seed):
    rr = random.Random(seed)
    brick = noise_mat("brick", (0.36, 0.12, 0.06), (0.5, 0.2, 0.1), scale=14, rough=0.95, bump=0.5)
    plaster = noise_mat("plaster", (0.62, 0.56, 0.45), (0.72, 0.66, 0.55), scale=20, rough=1.0, bump=0.3)
    for name, m, s, dy in (("peel_plaster", plaster, 1.0, 0.0), ("peel_brick", brick, 0.72, -0.003)):
        me = bpy.data.meshes.new(name)
        bm = bmesh.new()
        n = 28
        verts = []
        for i in range(n):
            a = 2 * math.pi * i / n
            r = size * s * (0.75 + 0.35 * math.sin(3 * a + seed) * rr.uniform(0.6, 1.0) + rr.uniform(-0.12, 0.12))
            verts.append(bm.verts.new((math.cos(a) * r * 1.4, 0, math.sin(a) * r)))
        bm.faces.new(verts)
        bm.to_mesh(me)
        bm.free()
        o = bpy.data.objects.new(name, me)
        col.objects.link(o)
        o.location = center + Vector((0, dy, 0))
        o.data.materials.append(m)


def build_gate(col):
    blue = noise_mat("gate_blue", (0.02, 0.09, 0.42), (0.04, 0.16, 0.55), scale=10, rough=0.45, bump=0.1,
                     mix_c3=(0.24, 0.08, 0.02), scale2=7.0)
    x0, x1 = GATE_X0 + 0.02, GATE_X1 - 0.02
    y = WALL_Y
    h0, h1 = 0.08, 2.05
    parts = []
    for z in (h0, 1.0, h1):
        parts.append(cylinder(f"gate_rail{z}", loc=((x0 + x1) / 2, y, z), r=0.035, depth=x1 - x0, segs=12,
                              rot=(0, D(90), 0), m=blue, col=col))
    n = 14
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        parts.append(cylinder(f"gate_bar{i}", loc=(x, y, (h0 + h1) / 2), r=0.016, depth=h1 - h0, segs=10,
                              m=blue, col=col))
        parts.append(cylinder(f"gate_spike{i}", loc=(x, y, h1 + 0.1), r=0.03, r2=0.0, depth=0.18, segs=8,
                              m=blue, col=col))
    for x in (x0, (x0 + x1) / 2, x1):
        parts.append(box(f"gate_stile{x:.2f}", loc=(x, y, (h0 + h1) / 2), size=(0.08, 0.06, h1 - h0), m=blue, col=col))
    # diagonal brace and a padlock
    parts.append(curve_tube("gate_brace", [(x0 + 0.05, y, h0 + 0.05), ((x0 + x1) / 2 - 0.05, y, 0.95)], bevel=0.02,
                            m=blue, col=col))
    lock = box("padlock", loc=((x0 + x1) / 2 + 0.06, y - 0.06, 1.0), size=(0.07, 0.03, 0.08),
               m=mat("lock", (0.3, 0.25, 0.1), rough=0.4, metal=0.8), col=col, bevel=0.01)
    return parts


def build_sign(col):
    """Hand-painted sign board (blank) on the wall, left of the gate."""
    board_m = noise_mat("sign_paint", (0.75, 0.72, 0.6), (0.62, 0.58, 0.45), scale=4, rough=0.9, bump=0.1)
    border_m = mat("sign_border", (0.45, 0.04, 0.03), rough=0.7)
    x, z = -0.55, 1.75
    y = WALL_Y - 0.17
    box("sign_board", loc=(x, y, z), size=(1.5, 0.04, 0.62), m=board_m, col=col, bevel=0.01, rot=(0, D(-1.5), 0))
    box("sign_border", loc=(x, y + 0.012, z), size=(1.6, 0.03, 0.72), m=border_m, col=col, bevel=0.01, rot=(0, D(-1.5), 0))
    for dx in (-0.65, 0.65):
        cylinder(f"sign_nail{dx}", loc=(x + dx, y - 0.025, z + 0.24), r=0.012, depth=0.02, rot=(D(90), 0, 0),
                 m=mat("nail", (0.2, 0.18, 0.15), metal=0.8), col=col)


def build_bench(col):
    wood = noise_mat("bench_wood", (0.22, 0.12, 0.05), (0.32, 0.19, 0.09), scale=25, rough=0.8, bump=0.15,
                     mix_c3=(0.15, 0.09, 0.05), scale2=3)
    bx, by = 3.0, 1.75
    for i, dy in enumerate((-0.12, 0.0, 0.12)):
        box(f"bench_plank{i}", loc=(bx, by + dy, 0.45), size=(1.6, 0.11, 0.04), m=wood, col=col, bevel=0.008,
            rot=(0, 0, D(0.6 * (i - 1))))
    for dx in (-0.65, 0.65):
        for dy in (-0.14, 0.14):
            box(f"bench_leg{dx}{dy}", loc=(bx + dx, by + dy, 0.22), size=(0.06, 0.06, 0.44), m=wood, col=col, bevel=0.006)
        box(f"bench_rail{dx}", loc=(bx + dx, by, 0.12), size=(0.04, 0.3, 0.04), m=wood, col=col)


def build_matka(col):
    """Earthen pot on an iron stand, with a lid and a steel tumbler."""
    clay = noise_mat("terracotta", (0.45, 0.14, 0.05), (0.55, 0.2, 0.08), scale=9, rough=0.85, bump=0.15,
                     mix_c3=(0.32, 0.12, 0.05), scale2=4)
    iron = mat("iron", (0.05, 0.05, 0.05), rough=0.5, metal=0.8)
    steel = mat("steel", (0.6, 0.6, 0.62), rough=0.15, metal=1.0)
    x, y = -2.3, 1.65
    z0 = 0.62
    torus("matka_ring", loc=(x, y, z0), R=0.17, r=0.015, m=iron, col=col)
    for i in range(3):
        a = 2 * math.pi * i / 3
        lx, ly = x + math.cos(a) * 0.2, y + math.sin(a) * 0.2
        curve_tube(f"matka_leg{i}", [(x + math.cos(a) * 0.17, y + math.sin(a) * 0.17, z0), (lx, ly, z0 * 0.5),
                                     (lx + math.cos(a) * 0.04, ly + math.sin(a) * 0.04, 0)], bevel=0.012, m=iron, col=col)
    body = sphere("matka", loc=(x, y, z0 + 0.22), radius=0.27, scale=(1, 1, 0.88), m=clay, col=col)
    torus("matka_neck", loc=(x, y, z0 + 0.45), R=0.1, r=0.035, m=clay, col=col)
    cylinder("matka_neckc", loc=(x, y, z0 + 0.42), r=0.1, depth=0.06, m=clay, col=col)
    # painted white band
    torus("matka_band", loc=(x, y, z0 + 0.3), R=0.255, r=0.008, m=mat("chalk", (0.8, 0.78, 0.7), rough=0.9), col=col,
          scale=(1, 1, 0.6))
    cylinder("matka_lid", loc=(x, y, z0 + 0.49), r=0.13, r2=0.11, depth=0.025, m=steel, col=col)
    cylinder("tumbler", loc=(x + 0.04, y - 0.02, z0 + 0.55), r=0.035, r2=0.03, depth=0.09, m=steel, col=col)


def build_tree(col):
    """Neem tree: gnarled trunk, branches, and leaf clusters that cast dappled shade."""
    bark = noise_mat("bark", (0.12, 0.09, 0.07), (0.25, 0.2, 0.15), scale=18, rough=0.95, bump=0.6)
    leaf_m = noise_mat("neem_leaves", (0.05, 0.16, 0.03), (0.12, 0.3, 0.05), scale=6, rough=0.75, bump=0.2,
                       mix_c3=(0.16, 0.3, 0.04), scale2=2)
    tx, ty = TREE_POS
    curve_tube("tree_trunk", [(tx, ty, 0), (tx + 0.1, ty, 1.0), (tx - 0.15, ty + 0.1, 2.2), (tx - 0.4, ty, 3.0)],
               bevel=0.22, m=bark, col=col, taper=[1.3, 1.0, 0.85, 0.6])
    rr = random.Random(11)
    tips = []
    for i, (dx, dy, dz) in enumerate([(-2.2, -0.3, 1.4), (-1.0, -1.2, 1.6), (1.2, 0.2, 1.5), (0.0, 1.0, 1.8),
                                      (-2.8, 0.6, 0.9), (0.8, -1.0, 1.0)]):
        start = Vector((tx - 0.3, ty, 2.7))
        end = start + Vector((dx, dy, dz))
        mid = start.lerp(end, 0.5) + Vector((0, 0, 0.3))
        curve_tube(f"tree_branch{i}", [start, mid, end], bevel=0.08, m=bark, col=col, taper=[1.0, 0.7, 0.3])
        tips.append(end)
    # leaf clusters: displaced icospheres, joined
    clusters = []
    for i, tip in enumerate(tips):
        for k in range(9):
            c = tip + Vector((rr.uniform(-0.9, 0.9), rr.uniform(-0.8, 0.8), rr.uniform(-0.4, 0.5)))
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=rr.uniform(0.35, 0.6), location=c)
            bpy.ops.object.shade_smooth()
            o = bpy.context.active_object
            o.name = f"leaves{i}_{k}"
            for c_ in o.users_collection:
                c_.objects.unlink(o)
            col.objects.link(o)
            tex = bpy.data.textures.get("leafnoise") or bpy.data.textures.new("leafnoise", "CLOUDS")
            tex.noise_scale = 0.25
            dm = o.modifiers.new("disp", "DISPLACE")
            dm.texture = tex
            dm.strength = 0.3
            o.data.materials.append(leaf_m)
            clusters.append(o)
    join(clusters, "neem_canopy")


def build_cow(col):
    """A white cow resting (legs folded) far in the background."""
    white = noise_mat("cow_white", (0.7, 0.68, 0.62), (0.6, 0.57, 0.5), scale=3, rough=0.9, bump=0.1)
    dark = mat("cow_dark", (0.05, 0.04, 0.035), rough=0.6)
    horn = mat("cow_horn", (0.35, 0.3, 0.22), rough=0.5)
    x, y = -9.0, 9.0
    root = bpy.data.objects.new("cow_root", None)
    col.objects.link(root)
    root.location = (x, y, 0)
    root.rotation_euler = (0, 0, D(-25))
    parts = [
        sphere("cow_body", loc=(0, 0, 0.42), radius=1.0, scale=(0.95, 0.45, 0.42), m=white, col=col),
        sphere("cow_hump", loc=(0.55, 0, 0.78), radius=0.22, scale=(1, 1, 0.8), m=white, col=col),
        sphere("cow_neck", loc=(0.95, -0.05, 0.65), radius=0.22, scale=(1.0, 0.8, 1.1), m=white, col=col),
        sphere("cow_head", loc=(1.25, -0.1, 0.72), radius=0.2, scale=(1.3, 0.75, 0.85), m=white, col=col),
        sphere("cow_muzzle", loc=(1.47, -0.12, 0.66), radius=0.11, scale=(0.9, 1.0, 0.8), m=dark, col=col),
    ]
    for sy in (1, -1):
        parts.append(curve_tube(f"cow_horn{sy}", [(1.2, -0.1 + sy * 0.1, 0.86), (1.15, -0.1 + sy * 0.22, 1.02),
                                                  (1.2, -0.1 + sy * 0.25, 1.1)], bevel=0.03, m=horn, col=col,
                                taper=[1.0, 0.7, 0.2]))
        parts.append(sphere(f"cow_ear{sy}", loc=(1.15, -0.1 + sy * 0.2, 0.78), radius=0.09, scale=(0.6, 1.5, 0.5),
                            m=white, col=col))
        parts.append(sphere(f"cow_leg{sy}", loc=(0.6, sy * 0.35, 0.1), radius=0.12, scale=(2.2, 0.8, 0.7),
                            m=white, col=col))
    parts.append(curve_tube("cow_tail", [(-0.9, 0, 0.5), (-1.1, 0.1, 0.25), (-1.0, 0.25, 0.05)], bevel=0.025,
                            m=white, col=col))
    for o in parts:
        o.parent = root


def build_far(col):
    """Distant trees and a hut so the horizon isn't empty above the wall."""
    rr = random.Random(21)
    leaf = noise_mat("far_trees", (0.08, 0.17, 0.05), (0.14, 0.24, 0.08), scale=2, rough=0.9, bump=0.0)
    trunk = mat("far_trunk", (0.12, 0.08, 0.05), rough=0.9)
    for i in range(14):
        x, y = rr.uniform(-25, 25), rr.uniform(14, 30)
        h = rr.uniform(3, 6)
        cylinder(f"far_trunk{i}", loc=(x, y, h * 0.3), r=0.15, depth=h * 0.6, m=trunk, col=col, segs=8)
        sphere(f"far_crown{i}", loc=(x, y, h * 0.75), radius=h * 0.35, scale=(1.3, 1.0, 0.8), m=leaf, col=col,
               segs=16, rings=8)


def build_lighting(col):
    sc = bpy.context.scene
    w = bpy.data.worlds.new("sky")
    w.use_nodes = True
    nt = w.node_tree
    sky = nt.nodes.new("ShaderNodeTexSky")
    sky.sky_type = "NISHITA"
    sky.sun_elevation = D(55)
    sky.sun_rotation = D(200)
    sky.sun_disc = False
    sky.air_density = 1.4
    sky.dust_density = 0.6
    nt.links.new(sky.outputs["Color"], nt.nodes["Background"].inputs["Color"])
    nt.nodes["Background"].inputs["Strength"].default_value = 0.6
    sc.world = w
    bpy.ops.object.light_add(type="SUN", rotation=(D(38), D(0), D(32)))
    sun = bpy.context.active_object
    sun.name = "sun"
    sun.data.energy = 5.5
    sun.data.color = (1.0, 0.93, 0.82)
    sun.data.angle = D(1.5)
    for c in sun.users_collection:
        c.objects.unlink(sun)
    col.objects.link(sun)
    return sun


def build_set():
    col = collection("set")
    build_ground(col)
    build_wall(col)
    build_gate(col)
    build_sign(col)
    build_bench(col)
    build_matka(col)
    build_tree(col)
    build_cow(col)
    build_far(col)
    build_lighting(col)
    return col
