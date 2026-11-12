"""Synthesise every sound effect and music cue for the skit (original, royalty-free).
python synth.py  -> writes audio/sfx/*.wav and audio/music/*.wav   (needs numpy + scipy)"""
import os

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, lfilter, sosfilt

SR = 48000
HERE = os.path.dirname(os.path.abspath(__file__))
rng = np.random.default_rng(7)


# ---------------------------------------------------------------- helpers --

def t_(d):
    return np.arange(int(d * SR)) / SR


def noise(d):
    return rng.uniform(-1, 1, int(d * SR))


def lp(x, fc, order=2):
    return sosfilt(butter(order, fc, "low", fs=SR, output="sos"), x)


def hp(x, fc, order=2):
    return sosfilt(butter(order, fc, "high", fs=SR, output="sos"), x)


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], "band", fs=SR, output="sos"), x)


def env(n, a=0.005, r=0.1, total=None):
    n = int(n)
    e = np.ones(n)
    na, nr = min(n, int(a * SR)), min(n, int(r * SR))
    if na:
        e[:na] = np.linspace(0, 1, na)
    if nr:
        e[-nr:] *= np.linspace(1, 0, nr)
    return e


def decay(d, tau):
    return np.exp(-t_(d) / tau)


def mix(total, *parts):
    out = np.zeros(int(total * SR))
    for start, sig in parts:
        i = int(start * SR)
        j = min(len(out), i + len(sig))
        out[i:j] += sig[: j - i]
    return out


def osc_phase(freq):
    """freq: array of Hz per sample -> phase in radians."""
    return 2 * np.pi * np.cumsum(freq) / SR


def saw(ph):
    return 2 * ((ph / (2 * np.pi)) % 1.0) - 1


def square(ph, duty=0.5):
    return np.where((ph / (2 * np.pi)) % 1.0 < duty, 1.0, -1.0)


def note_hz(n):
    """MIDI note -> Hz."""
    return 440.0 * 2 ** ((n - 69) / 12)


def save(rel, x, gain_db=-1.0):
    x = np.asarray(x, dtype=float)
    peak = np.max(np.abs(x)) or 1.0
    x = x / peak * 10 ** (gain_db / 20)
    path = os.path.join(HERE, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    wavfile.write(path, SR, (x * 32767).astype(np.int16))
    print(f"{rel:32s} {len(x) / SR:5.2f}s")


def echo(x, delay, fb=0.35, n=3):
    out = np.concatenate([x, np.zeros(int(delay * SR * n))])
    for k in range(1, n + 1):
        i = int(delay * SR * k)
        out[i:i + len(x)] += x * fb ** k
    return out


# ------------------------------------------------------------- instruments --

def kick_dhol(d=0.5, f0=130, f1=55):
    f = f1 + (f0 - f1) * np.exp(-t_(d) / 0.04)
    body = np.sin(osc_phase(f)) * decay(d, 0.18)
    slap = hp(noise(d), 1500) * decay(d, 0.012) * 0.6
    return body + slap


def dhol_high(d=0.25):
    tone = np.sin(osc_phase(np.full(int(d * SR), 420.0))) * decay(d, 0.05)
    return tone * 0.5 + bp(noise(d), 1800, 6000) * decay(d, 0.03)


def brass(n, d, vib=5.5, bright=2500, detune=0.0, glide_to=None):
    tt = t_(d)
    f = np.full(len(tt), note_hz(n)) * 2 ** (detune / 1200)
    if glide_to is not None:
        f = f * (note_hz(glide_to) / note_hz(n)) ** np.clip((tt - d * 0.4) / (d * 0.6), 0, 1)
    f = f * (1 + 0.006 * np.sin(2 * np.pi * vib * tt) * np.clip(tt / 0.25, 0, 1))
    ph = osc_phase(f)
    x = saw(ph) + 0.5 * saw(ph * 2.0)
    cutoff_env = np.clip(tt / 0.06, 0, 1)
    x = lp(x, bright) * (0.4 + 0.6 * cutoff_env)
    return x * env(len(tt), 0.02, 0.06)


def kazoo(n, d, detune=-25, glide_to=None):
    tt = t_(d)
    f = np.full(len(tt), note_hz(n)) * 2 ** (detune / 1200)
    if glide_to is not None:
        f = f * (note_hz(glide_to) / note_hz(n)) ** np.clip((tt - d * 0.3) / (d * 0.7), 0, 1)
    f *= 1 + 0.02 * np.sin(2 * np.pi * 6.5 * tt)
    x = saw(osc_phase(f))
    x = x + 0.6 * np.sign(x) * (np.abs(x) ** 0.3)  # buzz
    x = bp(x, 500, 1600) * 1.5 + bp(x, 2200, 3200) * 0.6 + 0.08 * bp(noise(d), 1500, 4000)
    return x * env(len(tt), 0.02, 0.05)


def pluck(n, d=0.5):
    """Karplus-Strong pizzicato."""
    f = note_hz(n)
    N = int(SR / f)
    buf = rng.uniform(-1, 1, N)
    out = np.zeros(int(d * SR))
    for i in range(len(out)):
        out[i] = buf[i % N]
        buf[i % N] = 0.5 * (buf[i % N] + buf[(i + 1) % N]) * 0.994
    return out * decay(d, 0.12)


def bassoon(n, d):
    tt = t_(d)
    ph = osc_phase(np.full(len(tt), note_hz(n)))
    x = lp(square(ph, 0.3) + 0.4 * saw(ph), 900)
    return x * env(len(tt), 0.015, 0.05)


def shehnai(n, d, detune=35, bend=0.0):
    tt = t_(d)
    f = note_hz(n) * 2 ** ((detune + bend * np.clip(tt / d, 0, 1)) / 1200)
    f = f * (1 + 0.012 * np.sin(2 * np.pi * 5.0 * tt) * np.clip(tt / 0.3, 0, 1))
    ph = osc_phase(np.full(len(tt), 1.0) * f)
    x = sum((1 / k) * np.sin(ph * k) for k in (1, 3, 5, 7, 9)) + 0.4 * saw(ph)
    x = bp(x, 700, 3500) * 1.4 + 0.03 * bp(noise(d), 2000, 6000)
    return x * env(len(tt), 0.04, 0.12)


# ------------------------------------------------------------------- music --

HERO = [  # (midi note, beats): heroic minor-key fanfare "TAAA-DAAA"
    (62, 1.5), (69, 2.5),                       # TAAA - DAAA
    (69, 0.5), (69, 0.5), (74, 1.0), (72, 0.5), (70, 0.5), (69, 2.0),
    (67, 0.5), (69, 0.5), (70, 1.0), (69, 0.5), (67, 0.5), (74, 3.0),
]


def hero_theme(bpm=84, total=7.5):
    beat = 60 / bpm
    out = np.zeros(int(total * SR))
    t = 0.0
    for n, b in HERO:
        d = b * beat
        if t >= total:
            break
        seg = brass(n, d * 0.95) + 0.6 * brass(n - 12, d * 0.95, bright=1500)
        out = out + mix(total, (t, seg))
        t += d
    drums = []
    tt = 0.0
    k = 0
    while tt < total:
        drums.append((tt, kick_dhol() * (1.2 if k % 4 == 0 else 0.8)))
        drums.append((tt + beat * 0.5, dhol_high() * 0.7))
        if k % 2:
            drums.append((tt + beat * 0.75, dhol_high() * 0.5))
        tt += beat
        k += 1
    out += mix(total, *drums) * 0.9
    # swell of low strings underneath
    pad = sum(lp(saw(osc_phase(np.full(int(total * SR), note_hz(m)))), 800) for m in (38, 45, 50))
    out += pad * 0.12 * np.clip(t_(total) / 1.0, 0, 1)
    return out * env(len(out), 0.01, 0.4)


def hero_kazoo(bpm=96, total=4.2):
    beat = 60 / bpm
    out = np.zeros(int(total * SR))
    t = 0.0
    notes = HERO[:2] + HERO[2:8]
    for i, (n, b) in enumerate(notes):
        d = b * beat
        last = i == len(notes) - 1
        seg = kazoo(n, d * (1.6 if last else 0.92), glide_to=(n - 7 if last else None))
        out = out + mix(total, (t, seg))
        t += d
        if t > total:
            break
    return out * env(len(out), 0.01, 0.3)


def sneaky(bpm=132, total=6.0):
    beat = 60 / bpm
    pattern = [(57, 1.0), (None, 1.0), (60, 1.0), (None, 1.0), (57, 0.5), (59, 0.5), (60, 0.5), (None, 1.5)]
    parts = []
    t, k = 0.0, 0
    while t < total:
        n, b = pattern[k % len(pattern)]
        if n:
            parts.append((t, pluck(n + 12, 0.4)))
        if k % len(pattern) in (0, 2, 4):
            parts.append((t, bassoon(n - 24 if n else 33, beat * 0.45) * 0.7))
        t += b * beat
        k += 1
    return mix(total, *parts)


def shehnai_lazy(total=4.0):
    # Sa re Ga ... re (Bhairav-ish), lazy and slightly off-key
    return mix(total, (0.0, shehnai(62, 0.9)), (0.85, shehnai(63, 0.7, detune=50)),
               (1.5, shehnai(66, 1.0, detune=20)), (2.45, shehnai(63, 1.5, detune=40, bend=-80)))


def village_ambience(total=50.0):
    breeze = lp(noise(total), 500) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.07 * t_(total)))
    parts = [(0, breeze * 0.5)]
    t = 1.0
    while t < total - 1:
        d = rng.uniform(0.08, 0.18)
        f0 = rng.uniform(2500, 4200)
        f = f0 + rng.uniform(-900, 900) * np.linspace(0, 1, int(d * SR))
        chirp = np.sin(osc_phase(f)) * env(int(d * SR), 0.01, 0.05) * 0.25
        for r in range(rng.integers(1, 4)):
            parts.append((t + r * (d + 0.05), chirp))
        t += rng.uniform(1.2, 3.5)
    # one distant cow moo
    md = 1.6
    mf = 110 + 40 * np.sin(np.pi * np.clip(t_(md) / md, 0, 1))
    moo = lp(saw(osc_phase(mf)), 700) * env(int(md * SR), 0.2, 0.4) * 0.15
    parts.append((total * 0.55, moo))
    return mix(total, *parts)


# ----------------------------------------------------------------- effects --

def thunder_crash(d=2.5):
    crack = hp(noise(0.3), 800) * decay(0.3, 0.05)
    rumble = lp(noise(d), 180, 4) * (decay(d, 0.8) * (0.7 + 0.3 * np.sin(2 * np.pi * 3 * t_(d))))
    return mix(d, (0, crack * 0.8), (0.02, rumble * 3.0))


def belly_pat_dhab():
    d = 0.4
    f = 50 + 60 * np.exp(-t_(d) / 0.03)
    thump = np.sin(osc_phase(f)) * decay(d, 0.09)
    slap = bp(noise(d), 600, 4000) * decay(d, 0.015)
    return echo(thump + slap * 0.7, 0.16, fb=0.35, n=3)


def record_scratch(d=0.55):
    tt = t_(d)
    wob = np.sin(2 * np.pi * (4 + 10 * tt / d) * tt)
    x = noise(d)
    out = np.zeros_like(x)
    seg = int(0.01 * SR)
    for i in range(0, len(x), seg):
        c = 1500 + 1200 * wob[i]
        out[i:i + seg] = bp(x[i:i + seg + 200], max(200, c * 0.6), c * 1.4)[:len(out[i:i + seg])]
    tone = np.sin(osc_phase(300 + 250 * wob)) * 0.4
    return (out + tone) * env(len(tt), 0.005, 0.08)


def balloon_squeak(d=0.7):
    tt = t_(d)
    f = 650 + 450 * (tt / d) + 80 * np.sin(2 * np.pi * 28 * tt)
    ph = osc_phase(f)
    x = np.sin(ph) + 0.5 * np.sin(2 * ph) + 0.3 * square(ph) * 0.3
    return lp(x, 4000) * env(len(tt), 0.03, 0.12) * (0.6 + 0.4 * np.sin(2 * np.pi * 11 * tt) ** 2)


def crickets(d=2.0):
    parts = []
    for base, start, rate in ((4600, 0.0, 0.42), (5200, 0.21, 0.55)):
        t = start
        while t < d:
            for k in range(3):
                cd = 0.035
                c = np.sin(osc_phase(np.full(int(cd * SR), base))) * np.sin(np.pi * t_(cd) / cd)
                parts.append((t + k * 0.05, c * 0.5))
            t += rate
    return mix(d, *parts)


def snare(d=0.12):
    return (bp(noise(d), 1500, 7000) * 0.8 + np.sin(osc_phase(np.full(int(d * SR), 190.0))) * 0.3) * decay(d, 0.04)


def drumroll(d=3.0):
    parts = []
    t = 0.0
    while t < d:
        p = t / d
        parts.append((t, snare() * (0.3 + 0.7 * p)))
        t += 1 / (12 + 16 * p)
    return mix(d, *parts)


def dhaam_pop(d=3.2):
    """Big cartoon blast: clipped crack, sub drop, rumbling body, debris crackle, long reverb tail."""
    from scipy.signal import fftconvolve
    n = int(d * SR)
    tt = t_(d)
    crack = lp(noise(0.06), 9000) * decay(0.06, 0.012) * 4.0
    sub_f = 26 + 70 * np.exp(-tt / 0.12)
    sub = np.sin(osc_phase(sub_f)) * decay(d, 0.55) * 2.2
    brown = np.cumsum(noise(d))
    brown = hp(brown / (np.max(np.abs(brown)) or 1), 25)
    body = lp(brown, 700, 4) * decay(d, 0.7) * (1 + 0.5 * lp(noise(d), 12)) * 6.0
    mid = bp(noise(d), 300, 2500) * decay(d, 0.25) * 1.5
    crackle = np.zeros(n)
    idx = rng.integers(int(0.03 * SR), int(1.4 * SR), 260)
    crackle[idx] = rng.uniform(-1, 1, len(idx)) * np.exp(-idx / SR / 0.5)
    crackle = bp(crackle, 1500, 7000) * 12
    dry = mix(d, (0, crack), (0.002, sub), (0.004, body), (0.004, mid), (0, crackle))
    ir = noise(2.2) * np.exp(-t_(2.2) / 0.55)
    wet = fftconvolve(lp(dry, 4000), ir)[:n]
    wet = wet / (np.max(np.abs(wet)) or 1) * np.max(np.abs(dry)) * 0.5
    x = dry + wet
    return np.tanh(1.8 * x / (np.max(np.abs(x)) or 1)) * env(n, 0.001, 0.6)


def balloon_pop(d=0.6):
    """Sharp rubber balloon burst: bright crack + rubber twang + tiny room tail, clearly not an explosion."""
    n = int(d * SR)
    crack = hp(noise(0.03), 1200, 4) * decay(0.03, 0.004) * 3.0
    click = np.zeros(n)
    click[0] = 1.0
    click = bp(click, 2000, 9000) * 40
    twang = np.sin(osc_phase(np.full(int(0.08 * SR), 950.0))) * decay(0.08, 0.018) * 0.5
    snap_low = np.sin(osc_phase(180 + 300 * np.exp(-t_(0.08) / 0.01))) * decay(0.08, 0.02) * 0.6
    tail = bp(noise(d), 800, 6000) * decay(d, 0.07) * 0.25
    return mix(d, (0, click), (0, crack), (0.001, twang), (0, snap_low), (0.004, tail))


def boing(d=1.0):
    tt = t_(d)
    f = 140 * (1 + 0.6 * np.exp(-tt / 0.25) * np.sin(2 * np.pi * 9 * tt)) * (1 + 0.8 * tt / d)
    ph = osc_phase(f)
    return (np.sin(ph) + 0.3 * np.sin(2 * ph)) * decay(d, 0.35) * env(len(tt), 0.005, 0.1)


def dhapp_land(d=0.9):
    f = 40 + 70 * np.exp(-t_(d) / 0.03)
    thud = np.tanh(2 * np.sin(osc_phase(f)) * decay(d, 0.15))
    dust = lp(noise(d), 2500) * decay(d, 0.25) * 0.3
    return thud + dust


def frantic_pat(d=4.0):
    parts = []
    t = 0.0
    while t < d:
        pd = 0.06
        slap = bp(noise(pd), rng.uniform(500, 900), 3500) * decay(pd, 0.012)
        parts.append((t, slap * rng.uniform(0.6, 1.0)))
        t += rng.uniform(0.09, 0.15)
    return mix(d, *parts)


def whoosh_away(d=0.9):
    tt = t_(d)
    x = noise(d)
    out = np.zeros_like(x)
    seg = int(0.01 * SR)
    for i in range(0, len(x), seg):
        c = 4000 * (1 - i / len(x)) + 400
        out[i:i + seg] = bp(x[i:i + seg + 200], c * 0.5, min(c * 1.6, 20000))[:len(out[i:i + seg])]
    return out * np.sin(np.pi * tt / d) ** 2


def paan_chew(d=4.5):
    parts = []
    t = 0.1
    while t < d - 0.3:
        cd = rng.uniform(0.12, 0.2)
        squelch = lp(noise(cd), 1400) * np.sin(np.pi * t_(cd) / cd) ** 2
        parts.append((t, squelch * rng.uniform(0.5, 1.0)))
        t += rng.uniform(0.32, 0.45)
    return mix(d, *parts)


def sad_trombone(d=3.0):
    notes = [(55, 0.0, 0.42), (54, 0.45, 0.42), (53, 0.9, 0.42), (52, 1.35, 1.6)]
    parts = []
    for n, s, nd in notes:
        b = brass(n, nd, vib=7 if nd > 1 else 0.1, bright=1400)
        if nd > 1:
            b *= 1 + 0.5 * np.sin(2 * np.pi * 4.5 * t_(nd))  # wah-wah
        parts.append((s, b))
    return mix(d, *parts)


def main():
    save("music/hero_theme.wav", hero_theme())
    save("music/hero_kazoo.wav", hero_kazoo())
    save("music/sneaky_strings.wav", sneaky())
    save("music/sneaky_strings_fast.wav", sneaky(bpm=190, total=4.0))
    save("music/shehnai_lazy.wav", shehnai_lazy())
    save("music/village_ambience.wav", village_ambience())
    save("sfx/thunder_crash.wav", thunder_crash())
    save("sfx/belly_pat_dhab.wav", belly_pat_dhab())
    save("sfx/record_scratch.wav", record_scratch())
    save("sfx/balloon_squeak.wav", balloon_squeak())
    save("sfx/crickets.wav", crickets())
    save("sfx/drumroll.wav", drumroll())
    save("sfx/dhaam_pop.wav", dhaam_pop())
    save("sfx/balloon_pop.wav", balloon_pop(), gain_db=0.0)
    save("sfx/boing.wav", boing())
    save("sfx/dhapp_land.wav", dhapp_land())
    save("sfx/frantic_pat.wav", frantic_pat())
    save("sfx/whoosh_away.wav", whoosh_away())
    save("sfx/paan_chew.wav", paan_chew())
    save("sfx/sad_trombone.wav", sad_trombone())


if __name__ == "__main__":
    main()
