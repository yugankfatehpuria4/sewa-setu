#!/usr/bin/env bash
# Transcribe the DC briefing with timestamps (needs internet to fetch the model once).
# Usage: ./scripts/transcribe_briefing.sh path/to/dc-briefing.mp3 > docs/evidence/dc-briefing-transcript.md
set -euo pipefail
pip install -q faster-whisper
python3 - "$1" <<'PY'
import sys
from faster_whisper import WhisperModel
m = WhisperModel("small", device="cpu", compute_type="int8")
segs, info = m.transcribe(sys.argv[1], vad_filter=True)
print("# DC briefing transcript (faster-whisper small, lang=%s)\n" % info.language)
for s in segs:
    print("- [%02d:%02d] %s" % (int(s.start)//60, int(s.start)%60, s.text.strip()))
PY
