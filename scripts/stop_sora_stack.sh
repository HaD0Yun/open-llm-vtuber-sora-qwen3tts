#!/usr/bin/env bash
set -euo pipefail

pkill -f "run_qwen3_tts_bridge_server.py" || true
pkill -f "run_server.py --verbose" || true

echo "Stopped OLV and Qwen3-TTS bridge processes (if running)."
