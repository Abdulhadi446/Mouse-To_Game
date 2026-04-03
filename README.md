# Mouse Drive 3D (Rebuilt from scratch)

This is a fresh 3D driving game built from zero with plain HTML, CSS, and JavaScript using Three.js.

## Files

- game/index.html: App shell and HUD layout
- game/styles.css: UI styling and overlay layout
- game/game.js: 3D world, car logic, controls, lap logic, minimap

## Controls

- Mouse wheel up: increase forward charge (tool-style)
- Mouse wheel down: increase backward charge (tool-style)
- Left mouse button hold: steer left
- Right mouse button hold: steer right
- Middle mouse button: emergency stop
- F8: toggle mapper enabled/disabled
- R: reset car position

## Gameplay

- Drive around an oval track
- Race against 3 AI cars
- Complete laps to track lap count
- Current lap time and best lap are shown in HUD
- Minimap shows player and AI positions
- Boost pads on the track for speed bursts and score
- Tool-style wheel counter and action state shown in HUD

## Run

Open game/index.html in a browser.

If your browser blocks module/CDN access for local files, run a local server:

python3 -m http.server 8000

Then open http://localhost:8000/game/

## Global Mouse-to-WASD App (works across games)

If you want mouse controls converted to WASD globally (outside this web game), use the helper app:

- Script: mouse_to_wasd.py
- Dependencies: evdev + pynput + python-xlib

Install and run:

python3 -m pip install -r requirements.txt
python3 mouse_to_wasd.py

GUI log window:

python3 mouse_to_wasd.py --debug

The GUI shows:

- backend selection
- session type
- enabled/disabled state
- selected device/backend
- last event/action
- live log output

Wheel threshold mode (new):

- There is one counter only.
- Scroll up increases the counter toward +1.0.
- Scroll down decreases the counter toward -1.0.
- W is pressed when counter reaches +1.0.
- S is pressed when counter reaches -1.0.
- Key is released when manual opposite scroll brings counter back past release threshold.
- Counter does not change automatically.

Tune threshold behavior:

python3 mouse_to_wasd.py --wheel-step 0.35 --wheel-press-threshold 1.0 --wheel-release-threshold 0.5

Debug mode:

python3 mouse_to_wasd.py --debug

GUI settings:

Click the "Settings" button in the log window to toggle key remapping options. You can change any key in real-time and press Apply.

If scroll is not detected on your setup, force raw mouse backend:

python3 mouse_to_wasd.py --debug --backend evdev

Backend options:

- auto (default): try evdev first, then x11, then pynput
- evdev: raw Linux input events (best for wheel detection)
- x11: X11 global hooks
- pynput: fallback global hooks

Mappings:

- Scroll up: increase forward charge (press W at threshold)
- Scroll down: increase backward charge (press S at threshold)
- Hold left mouse: A
- Hold right mouse: D
- Hold middle mouse: Space

Hotkeys:

- Esc: stop app from the terminal running the script
- Debug: `--debug` prints mouse events and emitted actions
- The GUI log window is enabled by default; use `--no-gui` to disable it

Custom key mapping (for games with arrow keys or other layouts):

If a game only supports arrow keys instead of WASD, use:

python3 mouse_to_wasd.py --key-forward up --key-backward down --key-left left --key-right right

Or mix and match:

python3 mouse_to_wasd.py --key-forward up --key-backward down --key-left a --key-right d

Available key names: w, a, s, d, space, up, down, left, right (plus any supported OS key name)

Notes:

- On GNOME Wayland it prefers evdev/uinput when permitted.
- On X11 it uses a keyboard controller backend first, with XTest as fallback.
- If evdev/uinput is blocked, it can still fall back to X11 hooks when available.
- You may still need permission to read `/dev/input/event*` and write `/dev/uinput` for the evdev backend.
- Press Esc in the terminal running the script to stop it cleanly.
- Touchpad-like devices are skipped automatically (mouse-only mapping).

## Control Input Remapper From Terminal

You can control an existing Input Remapper preset without opening GTK:

python3 input_remapper_runner.py --device "BT5.4 Mouse" --preset "The Gaming Setup"

Behavior:

- Starts the selected Input Remapper preset
- Waits in terminal
- Press Esc in that terminal to stop all active injections
- Touchpad-like device names are blocked by default for safety
