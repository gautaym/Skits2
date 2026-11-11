"""Single source of truth for timing (seconds). Used by the Blender build
(animation, lip-sync, cuts) and by the audio mix."""
import os

FPS = 24
HERE = os.path.dirname(os.path.abspath(__file__))
AUDIO = os.path.join(HERE, "audio")

# Beat start times (seconds). Each beat is also a camera cut.
T = {
    "hook": 0.0,       # SHOT 1 wide, slow-mo push-in, moustache in the wind
    "hook_low": 2.6,   # hero low angle, belly pat "DHAB"
    "peek": 5.2,       # record scratch -> SHOT 2 Chhotu peeks
    "sneak": 8.2,      # SHOT 3 giant tiptoe steps
    "kaun": 10.8,      # balloon squeak, music dies, CU "कौन है बे?"
    "freeze": 11.9,    # SHOT 4 comic freeze, crickets
    "hawa": 13.4,      # "हुंह... हवा है"
    "setup": 15.6,     # SHOT 5 CU balloon behind backside, drumroll
    "bang": 18.4,      # SHOT 6 DHAAAM
    "ground": 19.8,    # SHOT 7 wide on the ground
    "frantic": 24.0,   # medium, frantic patting; Chhotu runs off
    "baba": 28.9,      # SHOT 8 low angle Baba
    "nose": 31.6,      # CU balloon shred on nose
    "end": 34.6,       # fist shake, sad trombone, kazoo reprise
    "out": 37.6,
}

# Voice lines: (file in audio/vo, speaker, start seconds, fallback duration)
VO = [
    ("h1_naam_pandey.mp3", "pandey", 0.35, 4.2),
    ("c1_bhaukal_nikalte.mp3", "chhotu", 5.7, 2.8),
    ("h2_kaun_hai_be.mp3", "pandey", 10.95, 0.9),
    ("h3_hawa_hai.mp3", "pandey", 13.5, 2.6),
    ("c2_jai_bajrangbali.mp3", "chhotu", 16.9, 1.3),
    ("h4_baap_re.mp3", "pandey", 18.75, 4.8),
    ("h5_sab_hai_na.mp3", "pandey", 24.1, 4.75),
    ("c3_bhaukal_fuss.mp3", "chhotu", 25.0, 2.0),
    ("b1_gubbara_phoota.mp3", "baba", 29.1, 3.6),
    ("b2_beizzati.mp3", "baba", 31.7, 3.6),
    ("h6_chhotua.mp3", "pandey", 35.0, 2.0),
]


def f(t):
    """Seconds -> frame number (1-based)."""
    return int(round(t * FPS)) + 1


def vo_path(name):
    return os.path.join(AUDIO, "vo", name)
