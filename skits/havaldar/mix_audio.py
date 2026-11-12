"""Mix every available voice line (and later SFX/music) at its timeline position.

python mix_audio.py OUT.wav   -> writes a stereo 48 kHz mix, or exits 2 if no audio exists yet.
Needs ffmpeg on PATH (or FFMPEG env var).
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import timeline as TL  # noqa: E402

FFMPEG = os.environ.get("FFMPEG", "ffmpeg")


def clips():
    out = []
    for fname, _who, start, _dur in TL.VO:
        p = TL.vo_path(fname)
        if os.path.exists(p):
            out.append((p, start, 1.0, None))
    for sub in ("sfx", "music"):
        cue = os.path.join(TL.AUDIO, sub, "cues.txt")  # lines: file start_seconds [gain] [max_seconds]
        if os.path.exists(cue):
            for line in open(cue):
                parts = line.split()
                if len(parts) >= 2 and not line.startswith("#"):
                    p = os.path.join(TL.AUDIO, sub, parts[0])
                    if os.path.exists(p):
                        out.append((p, float(parts[1]), float(parts[2]) if len(parts) > 2 else 1.0,
                                    float(parts[3]) if len(parts) > 3 else None))
    return out


def main(out):
    cs = clips()
    if not cs:
        print("no audio yet")
        sys.exit(2)
    dur = TL.T["out"]
    args = [FFMPEG, "-y", "-v", "error", "-f", "lavfi", "-t", str(dur), "-i", "anullsrc=r=48000:cl=stereo"]
    filt = []
    for i, (p, start, gain, maxlen) in enumerate(cs, 1):
        args += ["-i", p]
        ms = int(start * 1000)
        trim = f"atrim=0:{maxlen},afade=t=out:st={max(0.0, maxlen - 0.08)}:d=0.08," if maxlen else ""
        filt.append(f"[{i}:a]{trim}aresample=48000,aformat=channel_layouts=stereo,volume={gain},"
                    f"adelay={ms}|{ms}[a{i}]")
    mix_in = "[0:a]" + "".join(f"[a{i}]" for i in range(1, len(cs) + 1))
    filt.append(f"{mix_in}amix=inputs={len(cs) + 1}:normalize=0:duration=first,alimiter=limit=0.95[out]")
    args += ["-filter_complex", ";".join(filt), "-map", "[out]", "-t", str(dur), out]
    subprocess.run(args, check=True)
    print(f"mixed {len(cs)} clips -> {out}")


if __name__ == "__main__":
    main(sys.argv[1])
