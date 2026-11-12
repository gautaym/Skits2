"""Single source of truth for timing (seconds), built from the real (tightened) voice-line lengths.
Used by the Blender build (animation, lip-sync, cuts) and by the audio mix. Fast-paced: every beat
starts as soon as the previous line ends; only the comic freeze is held."""
import json
import os

FPS = 24
HERE = os.path.dirname(os.path.abspath(__file__))
AUDIO = os.path.join(HERE, "audio")
_DUR_FILE = os.path.join(AUDIO, "vo_fast", "durations.json")
_FALLBACK = {"h1_naam_pandey.mp3": 4.2, "c1_bhaukal_nikalte.mp3": 2.6, "h2_kaun_hai_be.mp3": 1.0,
             "h3_hawa_hai.mp3": 2.6, "c2_jai_bajrangbali.mp3": 1.2, "h4_baap_re.mp3": 4.8,
             "h5_sab_hai_na.mp3": 4.6, "c3_bhaukal_fuss.mp3": 1.7, "b1_gubbara_phoota.mp3": 4.0,
             "b2_beizzati.mp3": 4.5, "h6_chhotua.mp3": 1.8}
DUR = dict(_FALLBACK)
if os.path.exists(_DUR_FILE):
    DUR.update(json.load(open(_DUR_FILE)))

SPEAKER = {"h": "pandey", "c": "chhotu", "b": "baba"}


def _build():
    T, starts = {}, {}

    def line(name, at):
        starts[name] = at
        return at + DUR[name]

    T["hook"] = 0.0
    h1_end = line("h1_naam_pandey.mp3", 0.2)
    T["hook_low"] = round(0.2 + DUR["h1_naam_pandey.mp3"] * 0.5, 2)   # cut mid-line to the hero low angle
    T["pat"] = h1_end + 0.05                                           # belly pat DHAB
    T["peek"] = T["pat"] + 0.45                                        # record scratch -> Chhotu peeks
    c1_end = line("c1_bhaukal_nikalte.mp3", T["peek"] + 0.2)
    T["sneak"] = c1_end + 0.15
    T["kaun"] = T["sneak"] + 2.0                                       # squeak, music dies
    h2_end = line("h2_kaun_hai_be.mp3", T["kaun"] + 0.05)
    T["freeze"] = h2_end + 0.05                                        # crickets (the one held beat)
    T["hawa"] = T["freeze"] + 1.2
    h3_end = line("h3_hawa_hai.mp3", T["hawa"] + 0.05)
    T["setup"] = max(h3_end + 0.3, T["hawa"] + 2.4)                    # balloon behind the backside
    c2_end = line("c2_jai_bajrangbali.mp3", T["setup"] + 0.8)
    T["bang"] = c2_end + 0.3                                           # DHAAAM
    h4_end = line("h4_baap_re.mp3", T["bang"] + 0.3)
    T["ground"] = T["bang"] + 1.4
    T["frantic"] = h4_end + 0.05
    h5_end = line("h5_sab_hai_na.mp3", T["frantic"] + 0.05)
    c3_end = line("c3_bhaukal_fuss.mp3", h5_end + 0.05)                # Chhotu giggles and zooms off
    T["run"] = h5_end
    T["baba"] = c3_end + 0.25
    b1_end = line("b1_gubbara_phoota.mp3", T["baba"] + 0.1)
    T["nose"] = b1_end + 0.1                                           # shred on the nose
    b2_end = line("b2_beizzati.mp3", T["nose"] + 0.05)
    T["end"] = b2_end + 0.1                                            # sad trombone, fist shake
    h6_end = line("h6_chhotua.mp3", T["end"] + 0.25)
    T["kazoo"] = h6_end + 0.05
    T["out"] = T["kazoo"] + 2.2
    T = {k: round(v, 3) for k, v in T.items()}
    vo = [(n, SPEAKER[n[0]], round(s, 3), DUR[n]) for n, s in starts.items()]
    return T, vo


T, VO = _build()

# Sound effects and music: (path under audio/, start seconds, gain, max seconds or None)
SFX = [
    ("music/village_ambience.wav", 0.0, 0.22, T["out"]),
    ("music/hero_theme.wav", 0.0, 0.55, T["peek"] - 0.05),
    ("sfx/thunder_crash.wav", 0.0, 0.8, None),
    ("sfx/belly_pat_dhab.wav", T["pat"], 1.0, None),
    ("sfx/record_scratch.wav", T["peek"] - 0.12, 0.9, None),
    ("music/sneaky_strings.wav", T["sneak"], 0.5, T["kaun"] - 0.15 - T["sneak"]),
    ("sfx/balloon_squeak.wav", T["kaun"] - 0.15, 0.9, None),
    ("sfx/crickets.wav", T["freeze"], 0.8, T["hawa"] - T["freeze"]),
    ("music/sneaky_strings_fast.wav", T["hawa"] + 1.3, 0.4, T["setup"] - T["hawa"] - 1.3),
    ("sfx/drumroll.wav", T["setup"], 0.6, T["bang"] - T["setup"]),
    ("sfx/dhaam_pop.wav", T["bang"], 1.0, None),
    ("sfx/boing.wav", T["bang"] + 0.15, 0.8, None),
    ("sfx/dhapp_land.wav", T["bang"] + 1.1, 1.0, None),
    ("sfx/frantic_pat.wav", T["ground"] + 0.1, 0.55, None),
    ("sfx/frantic_pat.wav", T["frantic"] + 0.3, 0.45, None),
    ("sfx/whoosh_away.wav", T["run"] + 0.6, 0.8, None),
    ("music/shehnai_lazy.wav", T["baba"], 0.5, None),
    ("sfx/paan_chew.wav", T["baba"], 0.55, None),
    ("sfx/sad_trombone.wav", T["end"] - 0.05, 0.75, None),
    ("music/hero_kazoo.wav", T["kazoo"], 0.6, None),
]


def f(t):
    """Seconds -> frame number (1-based)."""
    return int(round(t * FPS)) + 1


def vo_path(name):
    """Prefer the tightened line; fall back to the original upload."""
    fast = os.path.join(AUDIO, "vo_fast", name.replace(".mp3", ".wav"))
    return fast if os.path.exists(fast) else os.path.join(AUDIO, "vo", name)


# Rifle placement relative to Pandey (his local space: +Y is behind him).
RIFLE_LOCAL = {"loc": (0.06, 1.02, 0.0), "rot_x_deg": 44, "scale": 0.82}


def rifle_ground_lift(rot_x_deg=44, scale=0.82, heel_v=0.058):
    """Lift so the butt's heel corner sits exactly on the ground instead of sinking in."""
    import math
    return heel_v * math.sin(math.radians(rot_x_deg)) * scale


if __name__ == "__main__":
    for k, v in sorted(T.items(), key=lambda kv: kv[1]):
        print(f"{k:9s} {v:6.2f}")
    for n, who, s, d in VO:
        print(f"  {n:26s} {s:6.2f} -> {s + d:6.2f}")
