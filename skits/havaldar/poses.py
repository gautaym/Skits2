"""Named poses (joint rotations in degrees) and helpers to key them."""
from common import key

# Joint names are rig keys; values are XYZ euler degrees.
PANDEY = {
    "rest": {},
    # leaning back on the rifle, arms folded on top of the belly, chin up
    "lean_folded": {
        "root": (-6, 0, 0), "chest": (-10, 0, 0), "neck": (-6, 0, 0), "head": (-8, 0, 0),
        "shoulder_L": (-52, -40, 0), "elbow_L": (-62, 0, -48), "wrist_L": (-20, 0, -10),
        "shoulder_R": (-50, 40, 0), "elbow_R": (-66, 0, 50), "wrist_R": (-20, 0, 10),
        "hip_L": (4, 0, 4), "hip_R": (4, 0, -4), "knee_L": (-4, 0, 0), "knee_R": (-4, 0, 0),
        "ankle_L": (7, 0, 0), "ankle_R": (7, 0, 0),
    },
    # belly pat (right hand out, slapping the belly)
    "pat_up": {"shoulder_R": (-20, 0, -10), "elbow_R": (-75, 0, -20), "wrist_R": (20, 0, 0)},
    "pat_down": {"shoulder_R": (-32, 0, -8), "elbow_R": (-40, 0, -10), "wrist_R": (-10, 0, 0)},
    # ear twitch / suspicious: head tilts
    "suspicious": {"head": (-4, 0, 12), "neck": (-4, 0, 0)},
    # rocketing up: arms flung, legs kicked, hands to bottom
    "launch": {
        "root": (0, 0, 0), "chest": (10, 0, 0), "head": (-15, 0, 0),
        "shoulder_L": (20, 0, 20), "elbow_L": (-40, 0, 0), "shoulder_R": (20, 0, -20), "elbow_R": (-40, 0, 0),
        "hip_L": (-35, 0, 15), "hip_R": (-25, 0, -15), "knee_L": (60, 0, 0), "knee_R": (50, 0, 0),
    },
    # sitting on the ground, legs out, hands patting backside
    "sit_pat": {
        "root": (0, 0, 0), "chest": (12, 0, 0), "head": (8, 0, 0),
        "hip_L": (-82, 0, 18), "hip_R": (-82, 0, -18), "knee_L": (8, 0, 0), "knee_R": (8, 0, 0),
        "ankle_L": (-20, 0, 0), "ankle_R": (-20, 0, 0),
        "shoulder_L": (25, 0, 30), "elbow_L": (-20, 0, 0), "shoulder_R": (25, 0, -30), "elbow_R": (-20, 0, 0),
    },
    "fist_shake": {"shoulder_R": (-120, 0, -20), "elbow_R": (-40, 0, 0), "wrist_R": (0, 0, 0),
                   "head": (-8, 0, 0)},
}

CHHOTU = {
    "rest": {},
    # peeking: leaning sideways round the corner, balloon raised, finger on lips
    "peek": {"root": (0, 0, 0), "hips": (0, -14, 0), "chest": (0, -12, 0), "head": (0, -10, 0),
             "shoulder_R": (-70, 0, 15), "elbow_R": (-60, 0, 0),
             "shoulder_L": (-55, 0, -35), "elbow_L": (-120, 0, -30)},
    # exaggerated tiptoe: high knee, arms out, balloon forward
    "tiptoe_a": {"chest": (8, 0, 0), "hip_L": (-70, 0, 0), "knee_L": (95, 0, 0), "ankle_L": (40, 0, 0),
                 "hip_R": (15, 0, 0), "knee_R": (10, 0, 0), "ankle_R": (35, 0, 0),
                 "shoulder_R": (-75, 0, 10), "elbow_R": (-20, 0, 0), "shoulder_L": (-20, 0, 55), "elbow_L": (-40, 0, 0)},
    "tiptoe_b": {"chest": (8, 0, 0), "hip_R": (-70, 0, 0), "knee_R": (95, 0, 0), "ankle_R": (40, 0, 0),
                 "hip_L": (15, 0, 0), "knee_L": (10, 0, 0), "ankle_L": (35, 0, 0),
                 "shoulder_R": (-75, 0, 10), "elbow_R": (-20, 0, 0), "shoulder_L": (-20, 0, 55), "elbow_L": (-40, 0, 0)},
    # holding the balloon out behind the havaldar
    "aim": {"chest": (15, 0, 0), "head": (-5, 0, 0), "shoulder_R": (-80, 0, 0), "elbow_R": (-10, 0, 0),
            "shoulder_L": (-80, 0, -10), "elbow_L": (-60, 0, 0), "hip_L": (-20, 0, 0), "knee_L": (30, 0, 0),
            "hip_R": (10, 0, 0)},
    "run_a": {"chest": (18, 0, 0), "hip_L": (-60, 0, 0), "knee_L": (70, 0, 0), "hip_R": (35, 0, 0), "knee_R": (60, 0, 0),
              "shoulder_L": (45, 0, 10), "elbow_L": (-70, 0, 0), "shoulder_R": (-50, 0, -10), "elbow_R": (-70, 0, 0)},
    "run_b": {"chest": (18, 0, 0), "hip_R": (-60, 0, 0), "knee_R": (70, 0, 0), "hip_L": (35, 0, 0), "knee_L": (60, 0, 0),
              "shoulder_R": (45, 0, -10), "elbow_R": (-70, 0, 0), "shoulder_L": (-50, 0, 10), "elbow_L": (-70, 0, 0)},
}

BABA = {
    "rest": {},
    # leaning on the stick, slightly stooped, amused
    "lean_stick": {"chest": (12, 0, 0), "neck": (8, 0, 0), "head": (14, 0, 6),
                   "shoulder_R": (-30, 0, 0), "elbow_R": (-45, 0, 0), "wrist_R": (-15, 0, 0),
                   "shoulder_L": (10, 0, 15), "elbow_L": (-60, 0, -40)},
}

ALL = {"pandey": PANDEY, "chhotu": CHHOTU, "baba": BABA}

JOINT_KEYS = ["root", "hips", "chest", "neck", "head", "belly",
              "shoulder_L", "elbow_L", "wrist_L", "shoulder_R", "elbow_R", "wrist_R",
              "hip_L", "knee_L", "ankle_L", "hip_R", "knee_R", "ankle_R"]


def pose(rig, frame, name_or_dict, base=None, keep_root=True):
    """Key every joint of rig at frame: base pose overlaid with the named pose.

    Joints not mentioned go to zero, so poses are absolute and repeatable.
    The root's rotation is keyed only if the pose mentions it (its location
    is animated separately).
    """
    table = ALL[rig["name"]]
    p = {}
    for layer in (base, name_or_dict):
        if layer is None:
            continue
        p.update(table[layer] if isinstance(layer, str) else layer)
    for j in JOINT_KEYS:
        if j not in rig:
            continue
        if j == "root" and "root" not in p and keep_root:
            continue
        key(rig[j], frame, rot=p.get(j, (0, 0, 0)))


def face(rig, frame, lids=None, brows=None, mouth=None, look=None, lidlo=None):
    """Key facial controls. lids: degrees (-42 open, 0 half, 80 shut).
    brows: (raise_m, tilt_deg) applied to both (tilt mirrored); mouth: open 0..1."""
    import math
    if lids is not None:
        for s in ("L", "R"):
            v = lids[s] if isinstance(lids, dict) else lids
            key(rig[f"lid_{s}"], frame, rot=(v, 0, 0))
    if lidlo is not None:
        for s in ("L", "R"):
            key(rig[f"lidlo_{s}"], frame, rot=(lidlo, 0, 0))
    if brows is not None:
        up, tilt = brows if not isinstance(brows, dict) else (0, 0)
        for s, sx in (("L", 1), ("R", -1)):
            b = rig[f"brow_{s}"]
            if not hasattr(b, "_rest"):
                pass
            bu, bt = (brows[s] if isinstance(brows, dict) else (up, tilt))
            base = b.get("rest_z")
            if base is None:
                b["rest_z"] = b.location.z
                base = b.location.z
            b.location.z = base + bu
            b.keyframe_insert("location", index=2, frame=frame)
            b.rotation_euler = (0, sx * math.radians(bt), 0)
            b.keyframe_insert("rotation_euler", frame=frame)
    if mouth is not None:
        m = rig["mouth"]
        m.scale = (1.0, 1.0, 0.25 + 0.95 * mouth)
        m.keyframe_insert("scale", frame=frame)
    if look is not None:
        for s in ("L", "R"):
            key(rig[f"look_{s}"], frame, rot=(look[0], 0, look[1]))
