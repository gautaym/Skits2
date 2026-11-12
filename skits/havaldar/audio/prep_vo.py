"""Tighten voice lines for a fast-paced reel: trim edges, shorten long pauses, speed up (pitch kept).
Writes audio/vo_fast/<name>.wav and audio/vo_fast/durations.json."""
import json
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
SRC, DST = os.path.join(HERE, "vo"), os.path.join(HERE, "vo_fast")
SPEED = {"h": 1.15, "c": 1.12, "b": 1.1}  # by speaker prefix; Baba keeps a bit of his drawl
CUT = {"h5_sab_hai_na.mp3": 2.95}  # keep only the first N seconds (after speed-up): drops "अरे कोई गिनो रे"

os.makedirs(DST, exist_ok=True)
durs = {}
for f in sorted(os.listdir(SRC)):
    if not f.endswith(".mp3"):
        continue
    out = os.path.join(DST, f.replace(".mp3", ".wav"))
    af = ("silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.03,"
          "areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.06,areverse,"
          "silenceremove=stop_periods=-1:stop_duration=0.22:stop_threshold=-42dB:stop_silence=0.18,"
          f"atempo={SPEED[f[0]]},aresample=48000")
    if f in CUT:
        af += f",atrim=0:{CUT[f]},afade=t=out:st={CUT[f] - 0.1}:d=0.1"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", os.path.join(SRC, f), "-af", af, "-ac", "1", out], check=True)
    d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", out],
                             capture_output=True, text=True).stdout)
    durs[f] = round(d, 3)
    print(f"{f:26s} {d:5.2f}s")
json.dump(durs, open(os.path.join(DST, "durations.json"), "w"), indent=1)
