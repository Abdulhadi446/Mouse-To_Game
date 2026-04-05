# Mouse-To_Game

<p align="center">
  <img src="assets/readme/real-tool.png" alt="Mouse To WASD Controller" width="100%" />
</p>

<p align="center">
  <img alt="Linux" src="https://img.shields.io/badge/Linux-Ready-22c55e?style=for-the-badge&logo=linux&logoColor=white" />
  <img alt="Windows" src="https://img.shields.io/badge/Windows-Ready-3b82f6?style=for-the-badge&logo=windows&logoColor=white" />
  <img alt="Executable Release" src="https://img.shields.io/badge/Executable-Releases-f59e0b?style=for-the-badge&logo=github" />
</p>

This project is primarily a desktop mouse-to-key mapper for real games.
The browser game is optional and only used as a quick test/demo environment.

## Tool First Showcase

### Desktop Tool UI

![Desktop mapper interface](assets/readme/real-tool.png)

### Real Project Landing

![Project landing screenshot](assets/readme/real-landing.png)

### Demo Media

![Tool demo gif](assets/readme/demo.gif)

<video src="assets/readme/demo.mp4" controls muted loop width="100%"></video>

## What The Tool Does

- Maps mouse wheel and clicks to configurable keys.
- Works with multiple backends: auto, evdev, x11, pynput.
- Supports live key remapping from the GUI.
- Includes emergency stop and quick enable/disable flow.
- Provides executable builds for Linux and Windows.

## Quick Start (Tool)

### Run From Source

```bash
python3 -m pip install -r requirements.txt
python3 mouse_to_wasd.py
```

Debug mode:

```bash
python3 mouse_to_wasd.py --debug
```

Common key-mapping override:

```bash
python3 mouse_to_wasd.py --key-forward up --key-backward down --key-left left --key-right right
```

Wheel tuning:

```bash
python3 mouse_to_wasd.py --wheel-step 0.35 --wheel-press-threshold 1.0 --wheel-release-threshold 0.5
```

### Tool Controls

- Wheel up: increase forward charge
- Wheel down: increase backward charge
- Left mouse hold: left key
- Right mouse hold: right key
- Middle mouse hold: jump/action key
- F8: enable/disable mapper
- Esc: stop app in terminal

## Executable Distribution

### Linux Build

```bash
./build_linux.sh
```

Outputs:

- dist/mouse-to-game
- dist/input-remapper-runner

### Windows Build (Command Prompt)

```cmd
build_windows.cmd
```

PowerShell alternative:

```powershell
./build_windows.ps1
```

Outputs:

- dist/mouse-to-game.exe
- dist/input-remapper-runner.exe

## Input Remapper Runner Helper

Run with explicit values:

```bash
python3 input_remapper_runner.py --device "BT5.4 Mouse" --preset "The Gaming Setup"
```

List device keys:

```bash
input-remapper-control --list-devices
```

Runner behavior:

- Interactive device picker if device is omitted.
- Preset prompt if preset is omitted.
- Touchpad-like device safeguard by default.
- Esc or Ctrl+C to stop.

## Releases and CI

Workflow: .github/workflows/build-executables.yml

- Manual run: uploads workflow artifacts.
- Tag push (v\*): creates/updates GitHub Release and uploads binaries.

Release command:

```bash
git tag v1.0.0
git push origin v1.0.0
```

## Optional: Web Demo

The web game exists only to preview feel before using the desktop mapper.

Open game/index.html in a browser.

If needed, serve locally:

```bash
python3 -m http.server 8000
```

Then open:

http://localhost:8000/game/
