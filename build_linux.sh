#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

python3 -m pip install -r requirements.txt -r requirements-build.txt

python3 -m PyInstaller \
  --noconfirm \
  --clean \
  --onefile \
  --windowed \
  --collect-all pynput \
  --collect-all Xlib \
  --collect-all evdev \
  --name mouse-to-game \
  mouse_to_wasd.py

python3 -m PyInstaller \
  --noconfirm \
  --clean \
  --onefile \
  --collect-all pynput \
  --collect-all Xlib \
  --collect-all evdev \
  --name input-remapper-runner \
  input_remapper_runner.py

echo "Build complete. Binaries are in dist/"
ls -lh dist/
