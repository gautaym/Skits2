"""Procedural cartoon characters: Havaldar Pandey, Chhotu, Baba.

Every character is a hierarchy of joints (empties) with smooth mesh parts
parented to them, so shots are animated by keyframing joint rotations.
Characters are built at the origin facing -Y; place them via rig["root"].
"""
import math

from mathutils import Vector

from common import (attach, box, capsule, curve_tube, cylinder, hemisphere, joint, mat, noise_mat,
                    sphere, torus)

D = math.radians


# ------------------------------------------------------------------ face --

def build_face(rig, head, R, skin, col, eye_r=None, eye_sep=0.36, eye_h=0.18, iris=(0.12, 0.06, 0.02),
               brow_col=(0.02, 0.015, 0.01), brow_thick=1.0, nose=1.0, lips=None, mouth_w=0.45,
               mouth_h=-0.38, ears=True, prefix=""):
    """Eyes with lids, brows, nose, ears and a mouth on a head of radius R."""
    eye_r = eye_r or R * 0.2
    white = mat("eye_white", (0.9, 0.88, 0.85), rough=0.15, spec=0.6)
    iris_m = mat(prefix + "iris", iris, rough=0.2)
    pupil_m = mat("pupil", (0.0, 0.0, 0.0), rough=0.1)
    glint = mat("glint", (1, 1, 1), emission=((1, 1, 1), 3.0))
    lid_m = skin
    for side, sx in (("L", 1), ("R", -1)):
        pos = Vector((sx * R * eye_sep, -R * 0.86, R * eye_h))
        ej = joint(f"{prefix}eye_{side}", head, pos, col)
        ball = sphere(f"{prefix}eyeball_{side}", radius=eye_r, m=white, col=col)
        ball.parent = ej
        aim = joint(f"{prefix}look_{side}", ej, (0, 0, 0), col)  # rotate to look around
        ir = sphere(f"{prefix}iris_{side}", loc=(0, -eye_r * 0.82, 0), radius=eye_r * 0.55,
                    scale=(1, 0.35, 1), m=iris_m, col=col)
        pu = sphere(f"{prefix}pupil_{side}", loc=(0, -eye_r * 0.97, 0), radius=eye_r * 0.27,
                    scale=(1, 0.3, 1), m=pupil_m, col=col)
        gl = sphere(f"{prefix}glint_{side}", loc=(eye_r * 0.22, -eye_r * 1.02, eye_r * 0.25),
                    radius=eye_r * 0.1, m=glint, col=col, segs=12, rings=6)
        for o in (ir, pu, gl):
            o.parent = aim
        lid_up = hemisphere(f"{prefix}lid_up_{side}", radius=eye_r * 1.1, m=lid_m, col=col)
        lid_up.parent = ej
        lid_up.rotation_euler = (D(-42), 0, 0)
        lid_lo = hemisphere(f"{prefix}lid_lo_{side}", radius=eye_r * 1.08, m=lid_m, col=col, keep="bottom")
        lid_lo.parent = ej
        lid_lo.rotation_euler = (D(48), 0, 0)
        rig[f"lid_{side}"] = lid_up
        rig[f"lidlo_{side}"] = lid_lo
        rig[f"look_{side}"] = aim
        # brow: chunky tapered tube above the eye
        bj = joint(f"{prefix}brow_{side}", head, pos + Vector((0, -eye_r * 0.15, eye_r * 1.55)), col)
        bw = eye_r * 1.25
        brow = curve_tube(f"{prefix}browc_{side}",
                          [(-sx * bw, 0, -eye_r * 0.15), (0, -eye_r * 0.1, eye_r * 0.12), (sx * bw, 0, 0)],
                          bevel=eye_r * 0.22 * brow_thick, m=mat(prefix + "brow", brow_col, rough=0.9), col=col,
                          taper=[0.7, 1.0, 0.55])
        brow.parent = bj
        rig[f"brow_{side}"] = bj
        if ears:
            ear = sphere(f"{prefix}ear_{side}", loc=(sx * R * 0.97, 0.02, R * 0.02), radius=R * 0.22,
                         scale=(0.45, 0.8, 1.0), m=skin, col=col)
            ear.parent = head
            rig[f"ear_{side}"] = ear
    # nose
    ns = sphere(prefix + "nose", loc=(0, -R * 1.02, -R * 0.05), radius=R * 0.2 * nose,
                scale=(1.0, 1.0, 0.95), m=skin, col=col)
    ns.parent = head
    for sx in (1, -1):
        nos = sphere(prefix + f"nostril{sx}", loc=(sx * R * 0.13 * nose, -R * 0.98, -R * 0.12), radius=R * 0.09 * nose,
                     m=skin, col=col)
        nos.parent = head
    rig["nose"] = ns
    # mouth: dark interior + optional lips; animate rig["mouth"].scale.z to talk
    mj = joint(prefix + "mouth", head, (0, -R * 0.86, R * mouth_h), col)
    inner = sphere(prefix + "mouth_in", radius=R * mouth_w, scale=(1.0, 0.25, 0.32),
                   m=mat("mouth_dark", (0.12, 0.01, 0.01), rough=0.5), col=col)
    inner.parent = mj
    teeth = sphere(prefix + "teeth", loc=(0, -R * 0.02, R * mouth_w * 0.18), radius=R * mouth_w * 0.8,
                   scale=(1.0, 0.25, 0.12), m=mat("teeth", (0.85, 0.8, 0.7), rough=0.3), col=col)
    teeth.parent = mj
    if lips:
        lp = torus(prefix + "lips", R=R * mouth_w * 0.95, r=R * 0.05, m=mat(prefix + "lips", lips, rough=0.35),
                   col=col, rot=(D(90), 0, 0), scale=(1.0, 1.0, 0.38))
        lp.parent = mj
    mj.scale = (1, 1, 0.25)
    rig["mouth"] = mj


# ----------------------------------------------------------- limbs/body --

def arm(rig, side, sx, chest, shoulder, upper, fore, r_up, r_fore, sleeve_m, skin, col, prefix, hand_r,
        sleeve_len=1.0):
    sh = joint(f"{prefix}shoulder_{side}", chest, shoulder, col)
    up_m = sleeve_m
    up = capsule(f"{prefix}upperarm_{side}", (0, 0, 0), (0, 0, -upper), r_up, r_up * 0.85, m=up_m, col=col)
    up.parent = sh
    el = joint(f"{prefix}elbow_{side}", sh, (0, 0, -upper), col)
    fa_m = sleeve_m if sleeve_len > 1.0 else skin
    fa = capsule(f"{prefix}forearm_{side}", (0, 0, 0), (0, 0, -fore), r_fore, r_fore * 0.8, m=fa_m, col=col)
    fa.parent = el
    wr = joint(f"{prefix}wrist_{side}", el, (0, 0, -fore), col)
    palm = sphere(f"{prefix}hand_{side}", loc=(0, 0, -hand_r * 0.9), radius=hand_r, scale=(0.8, 0.55, 1.1),
                  m=skin, col=col)
    palm.parent = wr
    thumb = capsule(f"{prefix}thumb_{side}", (sx * -hand_r * 0.45, -hand_r * 0.3, -hand_r * 0.4),
                    (sx * -hand_r * 0.75, -hand_r * 0.55, -hand_r * 1.1), hand_r * 0.28, m=skin, col=col)
    thumb.parent = wr
    for i in range(4):
        fx = (i - 1.5) * hand_r * 0.36
        f = capsule(f"{prefix}finger{i}_{side}", (fx, 0, -hand_r * 1.6), (fx, -hand_r * 0.15, -hand_r * 2.3),
                    hand_r * 0.17, hand_r * 0.15, m=skin, col=col)
        f.parent = wr
    rig[f"shoulder_{side}"], rig[f"elbow_{side}"], rig[f"wrist_{side}"] = sh, el, wr
    return sh, el, wr


def leg(rig, side, sx, hips, hip, thigh, shin, r_th, r_sh, pants_m, skin_or_shoe, col, prefix, foot_len,
        foot_m=None, shorts=False, foot_r=None):
    hj = joint(f"{prefix}hip_{side}", hips, hip, col)
    th = capsule(f"{prefix}thigh_{side}", (0, 0, 0), (0, 0, -thigh), r_th, r_th * 0.85, m=pants_m, col=col)
    th.parent = hj
    kn = joint(f"{prefix}knee_{side}", hj, (0, 0, -thigh), col)
    sh_m = skin_or_shoe if shorts else pants_m
    sh = capsule(f"{prefix}shin_{side}", (0, 0, 0), (0, 0, -shin), r_sh, r_sh * 0.8, m=sh_m, col=col)
    sh.parent = kn
    an = joint(f"{prefix}ankle_{side}", kn, (0, 0, -shin), col)
    fr = foot_r or r_sh * 1.1
    ft = sphere(f"{prefix}foot_{side}", loc=(0, -foot_len * 0.3, -fr * 0.45), radius=1.0,
                scale=(fr * 1.1, foot_len * 0.6, fr * 0.75), m=foot_m or skin_or_shoe, col=col)
    ft.parent = an
    rig[f"hip_{side}"], rig[f"knee_{side}"], rig[f"ankle_{side}"] = hj, kn, an
    return hj, kn, an


# --------------------------------------------------------------- PANDEY --

def build_pandey(col):
    rig = {"name": "pandey"}
    p = "pd_"
    skin = mat("pd_skin", (0.36, 0.2, 0.12), rough=0.5, sss=0.15)
    khaki = noise_mat("khaki", (0.36, 0.27, 0.12), (0.42, 0.32, 0.15), scale=60, rough=0.85, bump=0.05)
    dark = mat("black_leather", (0.015, 0.012, 0.01), rough=0.35, spec=0.6, coat=0.3)
    beret_m = noise_mat("beret", (0.012, 0.012, 0.014), (0.03, 0.03, 0.035), scale=120, rough=0.95, bump=0.1)
    hair_m = mat("pd_hair", (0.01, 0.008, 0.006), rough=0.7)
    trousers = noise_mat("khaki_trousers", (0.24, 0.17, 0.07), (0.29, 0.21, 0.09), scale=60, rough=0.85, bump=0.05)
    brass = mat("brass", (0.8, 0.55, 0.18), rough=0.25, metal=1.0)
    belt_m = mat("belt", (0.08, 0.04, 0.015), rough=0.4)

    root = joint("pandey_root", None, (0, 0, 0), col)
    hips = joint(p + "hips", root, (0, 0, 0.92), col)
    rig["root"], rig["hips"] = root, hips

    # pot belly (the star of the show), torso and belt
    belly_j = joint(p + "belly", hips, (0, -0.1, 0.2), col)
    belly = sphere(p + "belly_m", radius=1.0, scale=(0.42, 0.46, 0.38), m=khaki, col=col)
    belly.parent = belly_j
    rig["belly"] = belly_j
    chest = joint(p + "chest", hips, (0, 0.06, 0.55), col)
    rig["chest"] = chest
    ch = sphere(p + "chest_m", radius=1.0, scale=(0.34, 0.27, 0.32), m=khaki, col=col)
    back = sphere(p + "back_m", loc=(0, 0.04, -0.25), radius=1.0, scale=(0.36, 0.3, 0.3), m=khaki, col=col)
    back.parent = chest
    ch.parent = chest
    pel = sphere(p + "pelvis_m", loc=(0, 0.02, -0.04), radius=1.0, scale=(0.34, 0.32, 0.22), m=trousers, col=col)
    pel.parent = hips
    belt_j = joint(p + "belt", hips, (0, -0.1, 0.0), col)
    belt_j.rotation_euler = (D(-8), 0, 0)  # front dips slightly under the belly
    belt = torus(p + "belt_m", R=1.0, r=0.06, m=dark, col=col, scale=(0.385, 0.42, 0.7))
    belt.parent = belt_j
    buckle = box(p + "buckle", loc=(0, -0.47, 0.0), size=(0.13, 0.04, 0.1), m=brass, col=col, bevel=0.012)
    buckle.parent = belt_j
    holster = box(p + "holster", loc=(0.4, 0.16, -0.12), size=(0.07, 0.14, 0.2), m=dark, col=col, bevel=0.025,
                  rot=(D(14), 0, 0))
    holster.parent = belt_j
    flap = box(p + "holster_flap", loc=(0.405, 0.15, -0.02), size=(0.08, 0.15, 0.05), m=dark, col=col, bevel=0.02,
               rot=(D(14), 0, 0))
    flap.parent = belt_j
    # straining shirt buttons down the belly
    BY, BZ = 0.46, 0.38  # belly ellipsoid semi-axes (y, z) at x=0

    def on_belly(z, lift=0.0):
        """Point on the belly's front surface at height z, and the surface tilt (deg about X)."""
        y = -BY * math.sqrt(max(0.0, 1 - (z / BZ) ** 2))
        n = Vector((0, y / BY ** 2, z / BZ ** 2)).normalized()  # outward normal
        pos = Vector((0, y, z)) + n * lift
        return pos, math.degrees(math.atan2(-n.z, -n.y))

    for i, z in enumerate((0.24, 0.1, -0.04, -0.18)):
        pos, tilt = on_belly(z, lift=0.008)
        b = cylinder(p + f"button{i}", loc=pos, r=0.02, depth=0.012, m=brass, col=col, rot=(D(90 + tilt), 0, 0))
        b.parent = belly_j
    placket = curve_tube(p + "placket", [on_belly(z, lift=0.002)[0] for z in (0.33, 0.2, 0.06, -0.08, -0.22)],
                         bevel=0.006, m=mat("khaki_dark", (0.27, 0.2, 0.09), rough=0.9), col=col)
    placket.parent = belly_j
    for sx in (1, -1):  # chest pockets + epaulettes
        pk = box(p + f"pocket{sx}", loc=(sx * 0.15, -0.255, 0.04), size=(0.12, 0.02, 0.1),
                 m=mat("khaki_dark", (0.27, 0.2, 0.09)), col=col, bevel=0.01, rot=(D(-12), 0, sx * D(-14)))
        pk.parent = chest
        ep = box(p + f"epaulette{sx}", loc=(sx * 0.27, 0.0, 0.25), size=(0.14, 0.09, 0.02), m=khaki, col=col,
                 bevel=0.01, rot=(0, sx * D(-18), 0))
        ep.parent = chest
    badge = box(p + "nameplate", loc=(-0.15, -0.27, 0.13), size=(0.09, 0.01, 0.025),
                m=mat("nameplate", (0.02, 0.05, 0.25), rough=0.3), col=col, bevel=0.003, rot=(D(-12), 0, D(14)))
    badge.parent = chest

    # head
    neck = joint(p + "neck", chest, (0, 0.0, 0.26), col)
    nk = cylinder(p + "neck_m", loc=(0, 0, 0.04), r=0.1, depth=0.14, m=skin, col=col)
    nk.parent = neck
    head = joint(p + "head", neck, (0, 0.0, 0.27), col)
    rig["neck"], rig["head"] = neck, head
    R = 0.25
    hd = sphere(p + "head_m", radius=R, scale=(1.0, 0.95, 1.08), m=skin, col=col)
    hd.parent = head
    jowl = sphere(p + "jowls", loc=(0, -0.03, -R * 0.55), radius=R * 0.8, scale=(1.08, 0.9, 0.6), m=skin, col=col)
    jowl.parent = head
    build_face(rig, head, R, skin, col, eye_r=R * 0.25, eye_sep=0.38, eye_h=0.16, brow_thick=1.5, nose=1.3,
               mouth_w=0.36, mouth_h=-0.42, prefix=p)
    # big curled moustache: two tapered bezier curls
    must_m = mat("moustache", (0.012, 0.009, 0.007), rough=0.8)
    must = joint(p + "moustache", head, (0, -R * 0.98, -R * 0.3), col)
    rig["moustache"] = must
    for sx in (1, -1):
        c = curve_tube(p + f"must{sx}", [
            (sx * 0.005, -0.02, 0.0), (sx * 0.09, -0.005, -0.025), (sx * 0.16, 0.025, -0.01),
            (sx * 0.19, 0.04, 0.035), (sx * 0.165, 0.04, 0.06), (sx * 0.145, 0.03, 0.04)],
            bevel=0.038, m=must_m, col=col, taper=[1.0, 1.0, 0.75, 0.45, 0.3, 0.2])
        c.scale = (1.2, 1.2, 1.2)
        mj = joint(p + f"must_j{sx}", must, (0, 0, 0), col)
        c.parent = mj
        rig[f"must_{'L' if sx > 0 else 'R'}"] = mj
    # sideburns / hair under the beret
    for sx in (1, -1):
        sb = sphere(p + f"sideburn{sx}", loc=(sx * R * 0.92, 0.02, R * 0.25), radius=R * 0.3,
                    scale=(0.35, 0.8, 1.0), m=hair_m, col=col)
        sb.parent = head
    back = sphere(p + "hair_back", loc=(0, R * 0.25, R * 0.25), radius=R * 0.98, scale=(1.02, 0.85, 0.8),
                  m=hair_m, col=col)
    back.parent = head
    # beret, tilted to one side, with brass badge
    beret = joint(p + "beret", head, (0, 0.02, R * 0.88), col)
    rig["beret"] = beret
    cap = sphere(p + "beret_m", loc=(R * 0.18, 0.0, 0.03), radius=1.0, scale=(R * 1.22, R * 1.12, R * 0.38),
                 m=beret_m, col=col)
    cap.rotation_euler = (0, D(-14), 0)
    cap.parent = beret
    band = torus(p + "beret_band", R=R * 0.98, r=0.018, m=dark, col=col, scale=(1.0, 0.98, 1.0))
    band.parent = beret
    bdg = cylinder(p + "beret_badge", loc=(-R * 0.45, -R * 0.83, 0.05), r=0.035, depth=0.012, m=brass, col=col,
                   rot=(D(80), 0, D(-25)))
    bdg.parent = beret

    # arms (khaki short sleeves) and legs (khaki trousers, black boots)
    for side, sx in (("L", 1), ("R", -1)):
        arm(rig, side, sx, chest, (sx * 0.33, 0.0, 0.16), 0.3, 0.27, 0.085, 0.07, khaki, skin, col, p, 0.065)
        leg(rig, side, sx, hips, (sx * 0.16, 0.0, -0.05), 0.42, 0.4, 0.15, 0.12, trousers, dark, col, p,
            foot_len=0.34, foot_m=dark, foot_r=0.11)
        bt = cylinder(p + f"boot_top{side}", loc=(0, 0, -0.3), r=0.115, r2=0.105, depth=0.2, m=dark, col=col)
        bt.parent = rig[f"knee_{side}"]
    return rig


def build_rifle(col):
    """Old bolt-action .303-style rifle; origin at the butt (rests on the ground). ~1.3 m long."""
    wood = noise_mat("rifle_wood", (0.42, 0.17, 0.05), (0.55, 0.24, 0.08), scale=30, rough=0.4, bump=0.05)
    steel = mat("gunmetal", (0.02, 0.022, 0.025), rough=0.3, metal=0.9, coat=0.3)
    root = joint("rifle_root", None, (0, 0, 0), col)
    parts = [
        box("rifle_butt", loc=(0, 0, 0.17), size=(0.07, 0.17, 0.34), m=wood, col=col, bevel=0.025),
        box("rifle_wrist", loc=(0, 0.02, 0.43), size=(0.06, 0.08, 0.24), m=wood, col=col, bevel=0.02),
        box("rifle_fore", loc=(0, 0.0, 0.83), size=(0.065, 0.075, 0.62), m=wood, col=col, bevel=0.02),
        box("rifle_buttplate", loc=(0, 0, 0.012), size=(0.075, 0.175, 0.025), m=steel, col=col, bevel=0.006),
        cylinder("rifle_barrel", loc=(0, 0.0, 1.02), r=0.022, depth=0.62, m=steel, col=col),
        cylinder("rifle_muzzle", loc=(0, 0.0, 1.33), r=0.028, depth=0.04, m=steel, col=col),
        box("rifle_receiver", loc=(0, 0.0, 0.6), size=(0.07, 0.085, 0.16), m=steel, col=col, bevel=0.01),
        box("rifle_mag", loc=(0, 0.06, 0.6), size=(0.05, 0.06, 0.12), m=steel, col=col, bevel=0.008),
        cylinder("rifle_bolt", loc=(0.06, 0.0, 0.64), r=0.014, depth=0.1, m=steel, col=col, rot=(0, D(90), 0)),
        sphere("rifle_knob", loc=(0.115, 0.0, 0.64), radius=0.025, m=steel, col=col),
        curve_tube("rifle_trigger_guard", [(0, 0.04, 0.5), (0, 0.1, 0.53), (0, 0.06, 0.58)], bevel=0.008,
                   m=steel, col=col),
        curve_tube("rifle_sling", [(0, 0.09, 0.3), (0, 0.17, 0.65), (0, 0.06, 1.05)], bevel=0.012,
                   m=mat("sling", (0.22, 0.14, 0.05), rough=0.8), col=col),
    ]
    for z in (0.62, 0.95, 1.12):
        parts.append(cylinder(f"rifle_band{z}", loc=(0, 0, z), r=0.045, depth=0.03, m=steel, col=col))
    for o in parts:
        o.parent = root
    return {"root": root}


# --------------------------------------------------------------- CHHOTU --

def build_chhotu(col):
    rig = {"name": "chhotu"}
    p = "ch_"
    skin = mat("ch_skin", (0.4, 0.23, 0.13), rough=0.5, sss=0.15)
    red = noise_mat("tshirt_red", (0.62, 0.02, 0.02), (0.72, 0.04, 0.03), scale=80, rough=0.85, bump=0.03)
    shorts_m = noise_mat("shorts", (0.33, 0.27, 0.15), (0.4, 0.33, 0.19), scale=60, rough=0.9, bump=0.05)
    hair_m = mat("ch_hair", (0.008, 0.006, 0.005), rough=0.6)

    root = joint("chhotu_root", None, (0, 0, 0), col)
    hips = joint(p + "hips", root, (0, 0, 0.56), col)
    rig["root"], rig["hips"] = root, hips
    chest = joint(p + "chest", hips, (0, 0, 0.2), col)
    rig["chest"] = chest
    torso = sphere(p + "torso", loc=(0, 0, 0.0), radius=1.0, scale=(0.16, 0.12, 0.22), m=red, col=col)
    torso.parent = chest
    collar = torus(p + "collar", loc=(0, 0, 0.19), R=0.065, r=0.015, m=red, col=col)
    collar.parent = chest
    pel = sphere(p + "shorts_m", radius=1.0, scale=(0.165, 0.125, 0.11), m=shorts_m, col=col)
    pel.parent = hips
    neck = joint(p + "neck", chest, (0, 0, 0.2), col)
    nk = cylinder(p + "neck_m", loc=(0, 0, 0.03), r=0.04, depth=0.08, m=skin, col=col)
    nk.parent = neck
    head = joint(p + "head", neck, (0, 0, 0.17), col)
    rig["neck"], rig["head"] = neck, head
    R = 0.17
    hd = sphere(p + "head_m", radius=R, scale=(1.0, 0.95, 1.02), m=skin, col=col)
    hd.parent = head
    chin = sphere(p + "chin", loc=(0, -0.03, -R * 0.45), radius=R * 0.65, scale=(1.0, 0.9, 0.7), m=skin, col=col)
    chin.parent = head
    # big mischievous eyes
    build_face(rig, head, R, skin, col, eye_r=R * 0.32, eye_sep=0.38, eye_h=0.12, iris=(0.09, 0.04, 0.015),
               brow_thick=0.8, nose=0.8, mouth_w=0.33, mouth_h=-0.45, lips=(0.35, 0.12, 0.1), prefix=p)
    # short messy hair: a cap plus random spiky tufts
    cap = sphere(p + "hair_cap", loc=(0, R * 0.14, R * 0.42), radius=R * 1.02, scale=(1.0, 1.0, 0.7),
                 m=hair_m, col=col)
    cap.parent = head
    import random
    rr = random.Random(9)
    for i in range(22):
        a = rr.uniform(0, 2 * math.pi)
        el = rr.uniform(D(15), D(80))
        if math.sin(a) < -0.55 and el < D(55):  # keep the forehead clear
            continue
        d = Vector((math.cos(a) * math.cos(el), math.sin(a) * math.cos(el), math.sin(el)))
        base = d * R * 0.9 + Vector((0, R * 0.12, R * 0.3))
        tip = base + d * R * rr.uniform(0.25, 0.45) + Vector((rr.uniform(-0.03, 0.03), 0, 0.02))
        t = capsule(p + f"tuft{i}", base, tip, R * 0.13, R * 0.03, m=hair_m, col=col)
        t.parent = head
    for side, sx in (("L", 1), ("R", -1)):
        arm(rig, side, sx, chest, (sx * 0.15, 0.0, 0.13), 0.2, 0.19, 0.045, 0.035, red, skin, col, p, 0.04)
        leg(rig, side, sx, hips, (sx * 0.075, 0.0, -0.03), 0.27, 0.26, 0.06, 0.04, shorts_m, skin, col, p,
            foot_len=0.2, shorts=True, foot_r=0.045)
    # sleeves end short: re-colour forearms as skin (arm() used sleeve on upper only)
    # balloon held in right hand
    bal = joint(p + "balloon", rig["wrist_R"], (0, -0.02, -0.08), col)
    rig["balloon"] = bal
    yellow = mat("balloon", (0.95, 0.62, 0.0), rough=0.12, spec=0.8, coat=0.6, sss=0.1)
    ball = sphere(p + "balloon_m", loc=(0, -0.05, 0.42), radius=1.0, scale=(0.21, 0.21, 0.26), m=yellow, col=col)
    ball.parent = bal
    knot = sphere(p + "balloon_knot", loc=(0, -0.05, 0.155), radius=0.025, scale=(1, 1, 1.3), m=yellow, col=col)
    knot.parent = bal
    string = curve_tube(p + "balloon_str", [(0, -0.05, 0.14), (0.01, -0.03, 0.07), (0, 0, 0.0)], bevel=0.003,
                        m=mat("string", (0.8, 0.8, 0.75), rough=0.9), col=col)
    string.parent = bal
    rig["balloon_mesh"] = [ball, knot, string]
    return rig


# ----------------------------------------------------------------- BABA --

def build_baba(col):
    rig = {"name": "baba"}
    p = "bb_"
    skin = mat("bb_skin", (0.32, 0.18, 0.1), rough=0.6, sss=0.12)
    white = noise_mat("cotton_white", (0.72, 0.7, 0.64), (0.8, 0.78, 0.72), scale=50, rough=0.95, bump=0.08)
    turban_m = noise_mat("turban", (0.78, 0.76, 0.7), (0.66, 0.64, 0.58), scale=20, rough=0.95, bump=0.15)
    wood = noise_mat("stick", (0.15, 0.07, 0.025), (0.24, 0.12, 0.05), scale=30, rough=0.6, bump=0.1)
    gold = mat("glasses", (0.6, 0.45, 0.2), rough=0.3, metal=1.0)

    root = joint("baba_root", None, (0, 0, 0), col)
    hips = joint(p + "hips", root, (0, 0, 0.86), col)
    rig["root"], rig["hips"] = root, hips
    chest = joint(p + "chest", hips, (0, 0.02, 0.36), col)
    rig["chest"] = chest
    # long kurta: tapered cone from shoulders to knees, slightly stooped
    kurta = cylinder(p + "kurta", loc=(0, 0, -0.32), r=0.17, r2=0.25, depth=0.95, m=white, col=col, segs=40)
    kurta.rotation_euler = (math.pi, 0, 0)
    kurta.parent = chest
    sh = sphere(p + "shoulders", loc=(0, 0, 0.12), radius=1.0, scale=(0.21, 0.13, 0.12), m=white, col=col)
    sh.parent = chest
    neck = joint(p + "neck", chest, (0, -0.02, 0.18), col)
    nk = cylinder(p + "neck_m", loc=(0, 0, 0.05), r=0.045, depth=0.12, m=skin, col=col)
    nk.parent = neck
    head = joint(p + "head", neck, (0, -0.02, 0.18), col)
    rig["neck"], rig["head"] = neck, head
    R = 0.15
    hd = sphere(p + "head_m", radius=R, scale=(0.95, 0.95, 1.1), m=skin, col=col)
    hd.parent = head
    build_face(rig, head, R, skin, col, eye_r=R * 0.16, eye_sep=0.36, eye_h=0.16, iris=(0.12, 0.08, 0.04),
               brow_col=(0.75, 0.74, 0.7), brow_thick=1.2, nose=1.2, mouth_w=0.34, mouth_h=-0.48,
               lips=(0.5, 0.02, 0.02), prefix=p)
    # cheeks bulging with paan
    for sx in (1, -1):
        ck = sphere(p + f"cheek{sx}", loc=(sx * R * 0.45, -R * 0.6, -R * 0.36), radius=R * 0.3, scale=(1.0, 0.9, 0.85),
                    m=skin, col=col)
        ck.parent = head
        rig[f"cheek_{'L' if sx > 0 else 'R'}"] = ck
    stub = sphere(p + "stubble", loc=(0, -0.01, -R * 0.55), radius=R * 0.75, scale=(1.05, 0.95, 0.6),
                  m=noise_mat("stubble", (0.5, 0.48, 0.45), (0.3, 0.2, 0.14), scale=300, rough=0.9, bump=0.0),
                  col=col)
    stub.parent = head
    # small white turban: stacked wraps
    tj = joint(p + "turban", head, (0, 0.01, R * 0.62), col)
    for i, (z, rr, sc) in enumerate([(0.0, R * 0.95, 1.0), (0.05, R * 0.9, 0.95), (0.1, R * 0.75, 0.9)]):
        t = torus(p + f"turban{i}", loc=(0, 0, z), R=rr, r=R * 0.22, m=turban_m, col=col,
                  rot=(D(6 * (i - 1)), D(-5 * i), 0), scale=(1, 1.02, sc))
        t.parent = tj
    top = sphere(p + "turban_top", loc=(0, 0, 0.1), radius=R * 0.75, scale=(1, 1, 0.5), m=turban_m, col=col)
    top.parent = tj
    # round glasses
    gj = joint(p + "glasses", head, (0, -R * 1.02, R * 0.16), col)
    for sx in (1, -1):
        rim = torus(p + f"rim{sx}", loc=(sx * R * 0.36, 0, 0), R=R * 0.24, r=0.004, m=gold, col=col,
                    rot=(D(90), 0, 0))
        rim.parent = gj
        temple = curve_tube(p + f"temple{sx}", [(sx * R * 0.6, 0, 0), (sx * R * 0.95, R * 0.6, 0.0),
                                                (sx * R * 0.95, R * 1.0, -0.02)], bevel=0.003, m=gold, col=col)
        temple.parent = gj
    bridge = curve_tube(p + "bridge", [(-R * 0.13, 0, 0), (0, -0.005, 0.01), (R * 0.13, 0, 0)], bevel=0.003,
                        m=gold, col=col)
    bridge.parent = gj
    for side, sx in (("L", 1), ("R", -1)):
        arm(rig, side, sx, chest, (sx * 0.2, 0.0, 0.08), 0.26, 0.24, 0.05, 0.035, white, skin, col, p, 0.04,
            sleeve_len=1.2)
        leg(rig, side, sx, hips, (sx * 0.09, 0.0, -0.04), 0.4, 0.4, 0.075, 0.065, white, skin, col, p,
            foot_len=0.22, foot_m=mat("chappal", (0.12, 0.05, 0.02), rough=0.7), foot_r=0.045)
    # walking stick in right hand
    stick = joint(p + "stick", rig["wrist_R"], (0, -0.02, -0.07), col)
    sk = cylinder(p + "stick_m", loc=(0, 0, -0.42), r=0.016, depth=0.95, m=wood, col=col, segs=12)
    sk.parent = stick
    hook = curve_tube(p + "stick_hook", [(0, 0, 0.05), (0, 0, 0.1), (0, -0.06, 0.12), (0, -0.09, 0.07)],
                      bevel=0.016, m=wood, col=col)
    hook.parent = stick
    rig["stick"] = stick
    return rig
