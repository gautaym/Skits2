#!/usr/bin/env bash
# Runs inside the unityci/editor Docker image (see .github/workflows/unity-env-check.yml).
# Activates Unity, runs the SkitEnvCheck editor script, then checks the
# non-Unity tools a skit pipeline needs (ffmpeg, text-to-speech) by turning the
# rendered frames into an MP4 with a voice line.
set -uo pipefail

PROJECT=/project
OUT="${SKIT_OUT:-$PROJECT/Output}"
mkdir -p "$OUT"
REPORT="$OUT/report.txt"
: > "$REPORT"
FAILED=0

log()   { echo "$*" | tee -a "$REPORT"; }
check() { # check <name> <pass:0|1> <detail>
  if [ "$2" = "1" ]; then log "PASS | $1 | $3"; else log "FAIL | $1 | $3"; FAILED=1; fi
}

log "== Container tools =="
apt-get update -qq >/dev/null 2>&1
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends \
  ffmpeg espeak-ng mesa-utils libgl1-mesa-dri xvfb >/dev/null 2>&1
rc=$?
check "apt install ffmpeg espeak-ng mesa xvfb" "$([ $rc = 0 ] && echo 1 || echo 0)" "exit $rc"

GL=$(xvfb-run -a glxinfo -B 2>&1 | grep -E "OpenGL (renderer|version) string" | tr '\n' ' ')
check "OpenGL under virtual display (xvfb)" "$([ -n "$GL" ] && echo 1 || echo 0)" "${GL:-no GL context}"

# ---------- Unity licence ----------
log ""
log "== Unity licence =="
LIC_DIR=/root/.local/share/unity3d/Unity
mkdir -p "$LIC_DIR"
SERIAL_USED=0
if [ -n "${UNITY_SERIAL:-}" ]; then
  unity-editor -batchmode -nographics -quit -logFile /dev/stdout \
    -serial "$UNITY_SERIAL" -username "$UNITY_EMAIL" -password "$UNITY_PASSWORD" > "$OUT/activation.log" 2>&1
  rc=$?; SERIAL_USED=1
  check "Unity activation (serial)" "$([ $rc = 0 ] && echo 1 || echo 0)" "exit $rc"
elif [ -z "${UNITY_LICENSE:-}" ]; then
  # No licence file: sign in with the Unity account and let the Licensing
  # Client grant the Personal entitlement on this machine.
  unity-editor -batchmode -nographics -quit -logFile /dev/stdout \
    -username "$UNITY_EMAIL" -password "$UNITY_PASSWORD" > "$OUT/activation.log" 2>&1
  rc=$?; SERIAL_USED=1
  LIC_FILES=$(find /root/.local/share/unity3d /root/.config/unity3d /usr/share/unity3d \
    \( -name '*.ulf' -o -name '*Entitlement*' -o -name '*.xml' \) 2>/dev/null | grep -i licen | tr '\n' ' ')
  log "INFO | Unity activation (email + password sign-in) | exit $rc; licence files: ${LIC_FILES:-none}"
  grep -iE "licen|entitle|activation|sign.?in|login|token" "$OUT/activation.log" \
    | grep -viE "password" | head -25 | sed 's/^/  log: /' | tee -a "$REPORT"
else
  printf '%s' "$UNITY_LICENSE" | tr -d '\r' > "$LIC_DIR/Unity_lic.ulf"
  unity-editor -batchmode -nographics -quit -logFile /dev/stdout \
    -manualLicenseFile "$LIC_DIR/Unity_lic.ulf" > "$OUT/activation.log" 2>&1
  rc=$?
  # Personal licences often report a non-zero exit here even when the .ulf is
  # valid; the real test is whether the editor run below starts.
  log "INFO | Unity activation (.ulf licence file) | exit $rc (see activation.log)"
fi

# ---------- Unity editor check ----------
log ""
log "== Unity editor run (imports packages, renders test frames) =="
START=$(date +%s)
unity-editor -batchmode -logFile "$OUT/editor.log" -projectPath "$PROJECT" \
  -force-glcore -executeMethod SkitEnvCheck.Run
rc=$?
check "Unity editor run" "$([ $rc = 0 ] && echo 1 || echo 0)" "exit $rc after $(( $(date +%s) - START ))s"
if [ -f "$OUT/unity-report.txt" ]; then
  cat "$OUT/unity-report.txt" >> "$REPORT"
else
  log "FAIL | Unity report | not produced - check editor.log (licence or compile error?)"
  grep -iE "error|licen" "$OUT/editor.log" 2>/dev/null | head -20 | tee -a "$REPORT"
  FAILED=1
fi

# ---------- Video + voice pipeline ----------
log ""
log "== Video / audio pipeline =="
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

# ---------- Return serial licence seat ----------
if [ "$SERIAL_USED" = 1 ]; then
  unity-editor -batchmode -nographics -quit -logFile /dev/stdout -returnlicense \
    -username "$UNITY_EMAIL" -password "$UNITY_PASSWORD" >> "$OUT/activation.log" 2>&1
fi

log ""
if [ $FAILED = 0 ]; then log "OVERALL: READY - everything needed to make a skit works"; else log "OVERALL: NOT READY - see FAIL lines above"; fi
# Artifacts of a public repo are downloadable by anyone: scrub credentials.
for f in "$OUT"/*.log "$OUT"/*.txt; do
  [ -f "$f" ] || continue
  for s in "${UNITY_EMAIL:-}" "${UNITY_PASSWORD:-}" "${UNITY_SERIAL:-}"; do
    [ -n "$s" ] && S="$s" perl -pi -e 's/\Q$ENV{S}\E/***/g' "$f"
  done
done
chmod -R a+rwX "$OUT" 2>/dev/null
exit $FAILED
