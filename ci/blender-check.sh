#!/usr/bin/env bash
# Runs on the GitHub runner. Expects Blender at $BLENDER and xvfb, espeak-ng,
# ffmpeg installed (see .github/workflows/blender-env-check.yml).
# Writes Output/report.txt; exits non-zero unless a skit MP4 was produced.
set -uo pipefail
OUT="${SKIT_OUT:-Output}"
mkdir -p "$OUT"
REPORT="$OUT/report.txt"
: > "$REPORT"
log()   { echo "$*" | tee -a "$REPORT"; }
check() { if [ "$2" = "1" ]; then log "PASS | $1 | $3"; else log "FAIL | $1 | $3"; fi; }

run_blender() { # run_blender <report-name> <script args...>
  local name=$1; shift
  xvfb-run -a -s "-screen 0 1280x1024x24" \
    "$BLENDER" -b --factory-startup --python-exit-code 1 \
    --python ci/blender_check.py -- --out "$OUT" --report "$name" "$@" \
    >> "$OUT/blender.log" 2>&1
}

log "== Tools =="
check "Blender binary" "$("$BLENDER" -b --factory-startup --version >/dev/null 2>&1 && echo 1 || echo 0)" \
  "$("$BLENDER" -b --factory-startup --version 2>/dev/null | head -1)"
check "ffmpeg" "$(command -v ffmpeg >/dev/null && echo 1 || echo 0)" "$(ffmpeg -version 2>/dev/null | head -1 | cut -c1-40)"
GL=$(xvfb-run -a glxinfo -B 2>/dev/null | grep -E "OpenGL (renderer|core profile version)" | sed 's/.*string: //' | tr '\n' ' ')
check "OpenGL on virtual display" "$([ -n "$GL" ] && echo 1 || echo 0)" "${GL:-none}"

espeak-ng -v en-us -s 150 -w "$OUT/voice.wav" \
  "Hey! Did you see that? This skit was rendered by Blender on GitHub." >/dev/null 2>&1
check "Text-to-speech (espeak-ng)" "$([ -s "$OUT/voice.wav" ] && echo 1 || echo 0)" "voice.wav"
log ""

# OpenGL engines can abort Blender outright, so probe each in its own process.
ENGINES="Cycles"
for eng in EEVEE Workbench; do
  if run_blender "probe-$eng.txt" --engines "$eng" --skip-mp4 && grep -q "^PASS | $eng" "$OUT/probe-$eng.txt"; then
    ENGINES="$eng,$ENGINES"
  else
    log "FAIL | $eng still render | crashed or blank (needs OpenGL); see blender.log"
  fi
done

# Main run: every engine that works, then the full MP4 with the best one.
run_blender "blender-report.txt" --engines "$ENGINES" --voice "$OUT/voice.wav"
log "(exit $?)"
cat "$OUT/blender-report.txt" >> "$REPORT" 2>/dev/null || log "FAIL | Blender check | no report; see blender.log"

if [ -s "$OUT/skit_test.mp4" ]; then
  INFO=$(ffprobe -v error -show_entries stream=codec_name,width,height:format=duration -of compact=p=0 "$OUT/skit_test.mp4" | tr '\n' ' ')
  check "MP4 playable (ffprobe)" 1 "$INFO"
else
  check "MP4 playable (ffprobe)" 0 "skit_test.mp4 missing"
fi

log ""
if grep -q "^PASS | Render .*MP4" "$REPORT" && grep -q "^PASS | MP4 playable" "$REPORT"; then
  log "OVERALL: READY - Blender can render skits here (engines: $ENGINES)"
  exit 0
fi
log "OVERALL: NOT READY - see FAIL lines above"
exit 1
