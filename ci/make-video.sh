#!/usr/bin/env bash
# Runs on the GitHub runner after Unity: checks the non-Unity tools a skit
# pipeline needs by turning the rendered frames + a TTS voice line into an MP4.
set -uo pipefail
OUT="${SKIT_OUT:-Output}"
mkdir -p "$OUT"
REPORT="$OUT/report.txt"
FAILED=0
log()   { echo "$*" | tee -a "$REPORT"; }
check() { if [ "$2" = "1" ]; then log "PASS | $1 | $3"; else log "FAIL | $1 | $3"; FAILED=1; fi; }

log ""
log "== Video / audio pipeline (runner) =="
sudo apt-get update -qq > "$OUT/apt.log" 2>&1
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends ffmpeg espeak-ng >> "$OUT/apt.log" 2>&1
rc=$?
check "Install ffmpeg + espeak-ng" "$([ $rc = 0 ] && echo 1 || echo 0)" "$(ffmpeg -version 2>/dev/null | head -1)"

espeak-ng -v en-us -s 150 -w "$OUT/voice.wav" "Hey! Did you see that? This skit was rendered by Unity on GitHub." >/dev/null 2>&1
check "Text-to-speech (espeak-ng)" "$([ -s "$OUT/voice.wav" ] && echo 1 || echo 0)" "voice.wav"

if ls "$OUT"/frames/frame_*.png >/dev/null 2>&1; then
  AUDIO=(); [ -s "$OUT/voice.wav" ] && AUDIO=(-i "$OUT/voice.wav" -c:a aac)
  ffmpeg -y -loglevel error -framerate 24 -i "$OUT/frames/frame_%04d.png" \
    "${AUDIO[@]}" -c:v libx264 -pix_fmt yuv420p "$OUT/skit_test.mp4" 2>>"$OUT/ffmpeg.log"
  DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT/skit_test.mp4" 2>/dev/null)
  check "ffmpeg: frames + voice -> MP4" "$([ -s "$OUT/skit_test.mp4" ] && echo 1 || echo 0)" "skit_test.mp4 duration ${DUR:-?}s"
else
  check "ffmpeg: frames + voice -> MP4" 0 "no frames rendered by Unity"
fi

log ""
if grep -q '^FAIL' "$REPORT"; then log "OVERALL: NOT READY - see FAIL lines above"; exit 1; fi
log "OVERALL: READY - everything needed to make a skit works"
