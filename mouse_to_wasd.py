#!/usr/bin/env python3
"""Wayland-friendly Mouse -> WASD mapper for Linux desktop games.

This version uses low-level Linux input devices (evdev) for capture and uinput
for virtual key emission, which is much more reliable on GNOME Wayland than a
pure global-hook approach.

Mappings:
- Scroll up       -> tap W
- Scroll down     -> tap S
- Hold left click -> hold A
- Hold right click -> hold D

Stop / controls:
- Esc in the terminal running this app -> stop
- Ctrl+C -> stop

Notes:
- On Wayland, global keyboard hooks are restricted by design.
- You may need permission to read /dev/input/event* and write /dev/uinput.
- If needed, run with sudo or add udev rules / input group access.
"""

from __future__ import annotations

import argparse
import os
import queue
import select
import signal
import sys
import termios
import threading
import time
import tty
from dataclasses import dataclass
from typing import Iterable, Optional

try:
    import tkinter as tk
    from tkinter import ttk
except ImportError:  # pragma: no cover - optional GUI
    tk = None
    ttk = None

try:
    from evdev import InputDevice, UInput, ecodes, list_devices
except ImportError as exc:  # pragma: no cover - import-time failure is user-facing
    raise SystemExit(
        "[mouse2wasd] Missing dependency: evdev. Install with:\n"
        "  python3 -m pip install -r requirements.txt"
    ) from exc

try:
    from pynput import keyboard as pynput_keyboard
    from pynput import mouse as pynput_mouse
except ImportError:  # pragma: no cover - optional fallback
    pynput_keyboard = None
    pynput_mouse = None

try:
    from Xlib import XK, X
    from Xlib import display as xdisplay
    from Xlib.ext import xtest
except ImportError:  # pragma: no cover - optional X11 backend
    xdisplay = None
    XK = None
    X = None
    xtest = None


@dataclass
class Config:
    pulse_ms: float = 90.0
    wheel_step: float = 0.35
    wheel_press_threshold: float = 1.0
    wheel_release_threshold: float = 0.5
    backend: str = "auto"
    device_match_hint: str = "mouse"
    debug: bool = False
    gui: bool = True
    key_forward: str = "w"
    key_backward: str = "s"
    key_left: str = "a"
    key_right: str = "d"
    key_jump: str = "space"


class MouseToWasd:
    def __init__(self, config: Config):
        self.config = config
        self.enabled = True
        self.running = True
        self.lock = threading.Lock()
        self.device_threads: list[threading.Thread] = []
        self.device: Optional[InputDevice] = None
        self.ui: Optional[UInput] = None
        self.display = None
        self.x11_kbd = None
        self.backend = "evdev"
        self.mouse_listener = None
        self.key_listener = None
        self.status_callback = None
        self.log = print

        self.held = {}
        self.wheel_counter = 0.0

        self._select_backend()
        self._init_held_keys()

    def _init_held_keys(self) -> None:
        self.held = {
            self.config.key_forward: False,
            self.config.key_backward: False,
            self.config.key_left: False,
            self.config.key_right: False,
            self.config.key_jump: False,
        }

    @staticmethod
    def _looks_like_touchpad(name: str) -> bool:
        lowered = name.lower()
        markers = (
            "touchpad",
            "trackpad",
            "synaptics",
            "elan",
            "bcm5974",
            "alps",
            "track point",
            "trackpoint",
        )
        return any(marker in lowered for marker in markers)

    def _select_backend(self) -> None:
        requested = self.config.backend.lower().strip()
        if requested not in {"auto", "evdev", "x11", "pynput"}:
            raise SystemExit(
                "[mouse2wasd] Invalid backend. Use one of: auto, evdev, x11, pynput"
            )

        if requested in {"auto", "evdev"}:
            try:
                self._setup_uinput()
                self._select_mouse_device()
                self.backend = "evdev"
                return
            except Exception as exc:
                if requested == "evdev":
                    raise SystemExit(f"[mouse2wasd] evdev backend failed: {exc}")
                print(f"[mouse2wasd] evdev/uinput unavailable: {exc}")

        if requested in {"auto", "x11"} and self._setup_x11_backend():
            self.backend = "x11"
            return

        if requested in {"auto", "pynput"} and self._setup_pynput_backend():
            self.backend = "pynput"
            return

        raise SystemExit("[mouse2wasd] No usable backend found for current settings.")

    def _debug(self, message: str) -> None:
        if self.config.debug:
            self.log(f"[mouse2wasd][debug] {message}")

    def set_logger(self, logger) -> None:
        self.log = logger

    def set_status_callback(self, callback) -> None:
        self.status_callback = callback

    def _status(self, key: str, value: str) -> None:
        if self.status_callback is not None:
            try:
                self.status_callback(key, value)
            except Exception:
                pass

    def _clamp01(self, value: float) -> float:
        return max(0.0, min(1.0, value))

    def _supported_key_names(self) -> list[str]:
        return [
            "a",
            "b",
            "c",
            "d",
            "e",
            "f",
            "g",
            "h",
            "i",
            "j",
            "k",
            "l",
            "m",
            "n",
            "o",
            "p",
            "q",
            "r",
            "s",
            "t",
            "u",
            "v",
            "w",
            "x",
            "y",
            "z",
            "0",
            "1",
            "2",
            "3",
            "4",
            "5",
            "6",
            "7",
            "8",
            "9",
            "space",
            "tab",
            "enter",
            "esc",
            "backspace",
            "delete",
            "insert",
            "home",
            "end",
            "pageup",
            "pagedown",
            "up",
            "down",
            "left",
            "right",
            "shift",
            "ctrl",
            "alt",
            "meta",
        ]

    def _uinput_supported_key_codes(self) -> list[int]:
        codes: list[int] = []
        for name in self._supported_key_names():
            code = self._key_code_for_uinput(name)
            if code is not None and code not in codes:
                codes.append(code)
        return codes

    @staticmethod
    def _key_attr(name: str):
        if pynput_keyboard is None:
            return None

        attr_map = {
            "space": "space",
            "tab": "tab",
            "enter": "enter",
            "esc": "esc",
            "backspace": "backspace",
            "delete": "delete",
            "insert": "insert",
            "home": "home",
            "end": "end",
            "pageup": "page_up",
            "pagedown": "page_down",
            "up": "up",
            "down": "down",
            "left": "left",
            "right": "right",
            "shift": "shift",
            "ctrl": "ctrl",
            "alt": "alt",
            "meta": "cmd",
        }
        attr_name = attr_map.get(name)
        if attr_name is None:
            return None
        return getattr(pynput_keyboard.Key, attr_name, None)

    def _controller_key_value(self, name: str):
        if pynput_keyboard is None:
            return None

        name = self._normalize_key_name(name)
        if len(name) == 1:
            return name
        return self._key_attr(name)

    def _key_code_for_uinput(self, name: str) -> Optional[int]:
        name = self._normalize_key_name(name)
        mapping = {
            "w": ecodes.KEY_W,
            "a": ecodes.KEY_A,
            "s": ecodes.KEY_S,
            "d": ecodes.KEY_D,
            "e": ecodes.KEY_E,
            "q": ecodes.KEY_Q,
            "space": ecodes.KEY_SPACE,
            "tab": getattr(ecodes, "KEY_TAB", None),
            "enter": getattr(ecodes, "KEY_ENTER", None),
            "esc": getattr(ecodes, "KEY_ESC", None),
            "backspace": getattr(ecodes, "KEY_BACKSPACE", None),
            "delete": getattr(ecodes, "KEY_DELETE", None),
            "insert": getattr(ecodes, "KEY_INSERT", None),
            "home": getattr(ecodes, "KEY_HOME", None),
            "end": getattr(ecodes, "KEY_END", None),
            "pageup": getattr(ecodes, "KEY_PAGEUP", None),
            "pagedown": getattr(ecodes, "KEY_PAGEDOWN", None),
            "shift": getattr(ecodes, "KEY_LEFTSHIFT", None),
            "ctrl": getattr(ecodes, "KEY_LEFTCTRL", None),
            "alt": getattr(ecodes, "KEY_LEFTALT", None),
            "meta": getattr(ecodes, "KEY_LEFTMETA", None),
            "up": getattr(ecodes, "KEY_UP", None),
            "down": getattr(ecodes, "KEY_DOWN", None),
            "left": getattr(ecodes, "KEY_LEFT", None),
            "right": getattr(ecodes, "KEY_RIGHT", None),
        }
        if name in mapping and mapping[name] is not None:
            return mapping[name]
        if len(name) == 1:
            return getattr(ecodes, f"KEY_{name.upper()}", None)
        return None

    def _normalize_key_name(self, key: str) -> str:
        key_lower = key.lower().strip()
        aliases = {
            "escape": "esc",
            "return": "enter",
            "spacebar": "space",
            "page up": "pageup",
            "page down": "pagedown",
            "arrow up": "up",
            "arrow down": "down",
            "arrow left": "left",
            "arrow right": "right",
            "super": "meta",
            "cmd": "meta",
            "windows": "meta",
            "control": "ctrl",
            "option": "alt",
        }
        return aliases.get(key_lower, key_lower)

    def _supported_key_names(self) -> list[str]:
        return [
            "a",
            "b",
            "c",
            "d",
            "e",
            "f",
            "g",
            "h",
            "i",
            "j",
            "k",
            "l",
            "m",
            "n",
            "o",
            "p",
            "q",
            "r",
            "s",
            "t",
            "u",
            "v",
            "w",
            "x",
            "y",
            "z",
            "0",
            "1",
            "2",
            "3",
            "4",
            "5",
            "6",
            "7",
            "8",
            "9",
            "space",
            "tab",
            "enter",
            "esc",
            "backspace",
            "delete",
            "insert",
            "home",
            "end",
            "pageup",
            "pagedown",
            "up",
            "down",
            "left",
            "right",
            "shift",
            "ctrl",
            "alt",
            "meta",
        ]

    def _set_wheel_counter(self, value: float) -> None:
        self.wheel_counter = max(-1.0, min(1.0, value))
        self._status("counter", f"counter: {self.wheel_counter:.2f}")

    def _apply_wheel_notch(self, direction: int, magnitude: float = 1.0) -> None:
        if not self.enabled or not self.running:
            return

        step = self.config.wheel_step * max(0.0, magnitude)
        with self.lock:
            if direction > 0:
                self._set_wheel_counter(self.wheel_counter + step)
            elif direction < 0:
                self._set_wheel_counter(self.wheel_counter - step)
            self._update_wheel_key_state_locked()

    def _get_key_name(self, key_type: str) -> str:
        mapping = {
            "forward": self.config.key_forward,
            "backward": self.config.key_backward,
            "left": self.config.key_left,
            "right": self.config.key_right,
            "jump": self.config.key_jump,
        }
        return mapping.get(key_type, "w")

    def _update_wheel_key_state_locked(self) -> None:
        press_t = self.config.wheel_press_threshold
        release_t = self.config.wheel_release_threshold
        fw = self._get_key_name("forward")
        bw = self._get_key_name("backward")

        # Hysteresis: press at high threshold, release below lower threshold.
        if self.wheel_counter >= press_t:
            self._press(fw)
            self._release(bw)
        elif self.held[fw] and self.wheel_counter <= release_t:
            self._release(fw)

        if self.wheel_counter <= -press_t:
            self._press(bw)
            self._release(fw)
        elif self.held[bw] and self.wheel_counter >= -release_t:
            self._release(bw)

    def _setup_x11_backend(self) -> bool:
        if (
            pynput_keyboard is None
            or pynput_mouse is None
            or xdisplay is None
            or XK is None
            or X is None
            or xtest is None
        ):
            return False

        try:
            self.display = xdisplay.Display()
            self.x11_kbd = pynput_keyboard.Controller()
        except Exception:
            return False

        self.mouse_listener = pynput_mouse.Listener(
            on_scroll=self._pynput_on_scroll,
            on_click=self._pynput_on_click,
        )
        self.key_listener = pynput_keyboard.Listener(on_press=self._pynput_on_key)
        return True

    def _setup_pynput_backend(self) -> bool:
        if pynput_keyboard is None or pynput_mouse is None:
            return False

        self.mouse_listener = pynput_mouse.Listener(
            on_scroll=self._pynput_on_scroll,
            on_click=self._pynput_on_click,
        )
        self.key_listener = pynput_keyboard.Listener(on_press=self._pynput_on_key)
        return True

    def _pynput_on_scroll(self, _x: int, _y: int, _dx: int, dy: int) -> None:
        if not self.enabled or not self.running:
            return
        self._debug(f"scroll dy={dy}")
        if dy > 0:
            self._apply_wheel_notch(1, abs(float(dy)))
        elif dy < 0:
            self._apply_wheel_notch(-1, abs(float(dy)))

    def _pynput_on_click(self, _x: int, _y: int, button, pressed: bool) -> None:
        if not self.enabled or not self.running:
            return

        self._debug(f"click button={button} action={'press' if pressed else 'release'}")

        if button == pynput_mouse.Button.left:
            if pressed:
                self._press(self._get_key_name("left"))
            else:
                self._release(self._get_key_name("left"))

        if button == pynput_mouse.Button.right:
            if pressed:
                self._press(self._get_key_name("right"))
            else:
                self._release(self._get_key_name("right"))

        if button == pynput_mouse.Button.middle:
            self._debug(
                f"click button=middle action={'press' if pressed else 'release'}"
            )
            if pressed:
                self._press(self._get_key_name("jump"))
            else:
                self._release(self._get_key_name("jump"))

    def _pynput_on_key(self, key):
        if key == pynput_keyboard.Key.f8:
            self.enabled = not self.enabled
            status = "ENABLED" if self.enabled else "DISABLED"
            self.log(f"[mouse2wasd] {status}")
            self._status("enabled", f"enabled: {'yes' if self.enabled else 'no'}")
            if not self.enabled:
                self.release_all()

        if key == pynput_keyboard.Key.esc:
            self.stop("ESC")
            return False

        return True

    def _setup_uinput(self) -> None:
        capabilities = {ecodes.EV_KEY: self._uinput_supported_key_codes()}
        self.ui = UInput(capabilities, name="mouse2wasd-virtual-keyboard")

    def _select_mouse_device(self) -> None:
        device_paths = list_devices()
        candidates: list[InputDevice] = []
        skipped_touchpads: list[str] = []

        for path in device_paths:
            try:
                device = InputDevice(path)
            except OSError:
                continue

            caps = device.capabilities(verbose=False)
            rel_codes = set(caps.get(ecodes.EV_REL, []))
            key_codes = set(caps.get(ecodes.EV_KEY, []))

            has_buttons = ecodes.BTN_LEFT in key_codes and ecodes.BTN_RIGHT in key_codes
            has_wheel = ecodes.REL_WHEEL in rel_codes
            is_hint_match = self.config.device_match_hint.lower() in device.name.lower()
            is_touchpad = self._looks_like_touchpad(device.name)

            if is_touchpad:
                skipped_touchpads.append(f"{path}: {device.name}")
                continue

            if has_buttons and has_wheel:
                if is_hint_match:
                    self.device = device
                    return
                candidates.append(device)

        if candidates:
            self.device = candidates[0]
            return

        available = []
        for path in device_paths:
            try:
                device = InputDevice(path)
                available.append(f"{path}: {device.name}")
            except OSError:
                continue

        raise SystemExit(
            "[mouse2wasd] No suitable mouse device found.\n"
            "Need a non-touchpad device that provides BTN_LEFT, BTN_RIGHT and REL_WHEEL.\n"
            "Available devices:\n"
            + (
                "\n".join(f"  - {line}" for line in available)
                if available
                else "  (none)"
            )
            + (
                "\nSkipped touchpad-like devices:\n"
                + "\n".join(f"  - {line}" for line in skipped_touchpads)
                if skipped_touchpads
                else ""
            )
        )

    def _write_key(self, key: str, key_code: int, value: int) -> None:
        key_name = key.upper()
        normalized_key = self._normalize_key_name(key)

        if self.backend == "x11" and self.x11_kbd is not None:
            key_value = self._controller_key_value(normalized_key)
            if key_value is not None:
                self._debug(
                    f"emit {key_name} {'down' if value else 'up'} via x11-controller"
                )
                if value:
                    self.x11_kbd.press(key_value)
                else:
                    self.x11_kbd.release(key_value)
                self._status(
                    "last",
                    f"emit {key_name} {'down' if value else 'up'} via x11-controller",
                )
                return

        if (
            self.backend == "x11"
            and self.display is not None
            and X is not None
            and xtest is not None
        ):
            event_type = X.KeyPress if value else X.KeyRelease
            self._debug(f"emit {key_name} {'down' if value else 'up'} via x11-xtest")
            xtest.fake_input(self.display, event_type, key_code)
            self.display.sync()
            self._status(
                "last", f"emit {key_name} {'down' if value else 'up'} via x11-xtest"
            )
            return

        if self.ui is None:
            return
        self._debug(f"emit {key_name} {'down' if value else 'up'} via evdev/uinput")
        self.ui.write(ecodes.EV_KEY, key_code, value)
        self.ui.syn()
        self._status(
            "last", f"emit {key_name} {'down' if value else 'up'} via evdev/uinput"
        )

    def _press(self, key: str) -> None:
        if not self.held[key]:
            self._write_key(key, self._key_code(key), 1)
            self.held[key] = True

    def _release(self, key: str) -> None:
        if self.held[key]:
            self._write_key(key, self._key_code(key), 0)
            self.held[key] = False

    def _pulse(self, key: str, duration_ms: Optional[float] = None) -> None:
        with self.lock:
            if not self.enabled or not self.running:
                return
            self._press(key)

        hold_ms = self.config.pulse_ms if duration_ms is None else duration_ms

        def release_later() -> None:
            if not self.running:
                return
            self._release(key)

        timer = threading.Timer(hold_ms / 1000.0, release_later)
        timer.daemon = True
        timer.start()

    def _key_code(self, key: str) -> int:
        key_name = self._normalize_key_name(key)
        if self.backend == "x11" and self.display is not None and XK is not None:
            x11_aliases = {
                "esc": "Escape",
                "enter": "Return",
                "space": "space",
                "tab": "Tab",
                "backspace": "BackSpace",
                "delete": "Delete",
                "insert": "Insert",
                "home": "Home",
                "end": "End",
                "pageup": "Page_Up",
                "pagedown": "Page_Down",
                "up": "Up",
                "down": "Down",
                "left": "Left",
                "right": "Right",
                "shift": "Shift_L",
                "ctrl": "Control_L",
                "alt": "Alt_L",
                "meta": "Super_L",
            }
            x11_name = x11_aliases.get(key_name, key_name)
            keysym = XK.string_to_keysym(x11_name)
            if keysym == 0 and len(key_name) == 1:
                keysym = XK.string_to_keysym(key_name)
            if keysym == 0:
                self.log(
                    f"[mouse2wasd] Unknown key '{key}'. Supported: {', '.join(self._supported_key_names())}"
                )
                return -1
            return self.display.keysym_to_keycode(keysym)

        mapping = {
            "w": ecodes.KEY_W,
            "a": ecodes.KEY_A,
            "s": ecodes.KEY_S,
            "d": ecodes.KEY_D,
            "e": ecodes.KEY_E,
            "q": ecodes.KEY_Q,
            "space": ecodes.KEY_SPACE,
            "tab": getattr(ecodes, "KEY_TAB", None),
            "enter": getattr(ecodes, "KEY_ENTER", None),
            "esc": getattr(ecodes, "KEY_ESC", None),
            "backspace": getattr(ecodes, "KEY_BACKSPACE", None),
            "delete": getattr(ecodes, "KEY_DELETE", None),
            "insert": getattr(ecodes, "KEY_INSERT", None),
            "home": getattr(ecodes, "KEY_HOME", None),
            "end": getattr(ecodes, "KEY_END", None),
            "pageup": getattr(ecodes, "KEY_PAGEUP", None),
            "pagedown": getattr(ecodes, "KEY_PAGEDOWN", None),
            "shift": ecodes.KEY_LEFTSHIFT,
            "ctrl": ecodes.KEY_LEFTCTRL,
            "alt": ecodes.KEY_LEFTALT,
            "meta": getattr(ecodes, "KEY_LEFTMETA", None),
            "up": ecodes.KEY_UP,
            "down": ecodes.KEY_DOWN,
            "left": ecodes.KEY_LEFT,
            "right": ecodes.KEY_RIGHT,
        }
        if key_name in mapping and mapping[key_name] is not None:
            return mapping[key_name]

        if len(key_name) == 1:
            key_code = getattr(ecodes, f"KEY_{key_name.upper()}", None)
            if key_code is not None:
                return key_code

        if key_name.startswith("f") and key_name[1:].isdigit():
            key_code = getattr(ecodes, f"KEY_F{key_name[1:]}", None)
            if key_code is not None:
                return key_code

        self.log(
            f"[mouse2wasd] Unknown key '{key}'. Supported: {', '.join(self._supported_key_names())}"
        )
        return -1  # Invalid key code

    def _handle_mouse_event(self, event) -> None:
        if not self.enabled or not self.running:
            return

        self._debug(f"event type={event.type} code={event.code} value={event.value}")
        self._status(
            "last", f"event type={event.type} code={event.code} value={event.value}"
        )

        if event.type == ecodes.EV_REL and event.code == ecodes.REL_WHEEL:
            if event.value > 0:
                self._apply_wheel_notch(1, abs(float(event.value)))
            elif event.value < 0:
                self._apply_wheel_notch(-1, abs(float(event.value)))
            return

        if event.type == ecodes.EV_KEY:
            if event.code == ecodes.BTN_LEFT:
                self._debug(
                    f"click button=left action={'press' if event.value == 1 else 'release'}"
                )
                if event.value == 1:
                    self._press(self._get_key_name("left"))
                elif event.value == 0:
                    self._release(self._get_key_name("left"))
            elif event.code == ecodes.BTN_RIGHT:
                self._debug(
                    f"click button=right action={'press' if event.value == 1 else 'release'}"
                )
                if event.value == 1:
                    self._press(self._get_key_name("right"))
                elif event.value == 0:
                    self._release(self._get_key_name("right"))
            elif event.code == ecodes.BTN_MIDDLE:
                self._debug(
                    f"click button=middle action={'press' if event.value == 1 else 'release'}"
                )
                if event.value == 1:
                    self._press(self._get_key_name("jump"))
                elif event.value == 0:
                    self._release(self._get_key_name("jump"))

    def run_device_loop(self) -> None:
        if self.device is None:
            return

        self.log(f"[mouse2wasd] Using device: {self.device.path} ({self.device.name})")

        try:
            self.device.grab()
        except Exception:
            # Non-fatal: continue without exclusive grab if not permitted.
            pass

        try:
            for event in self.device.read_loop():
                if not self.running:
                    break
                self._handle_mouse_event(event)
        except OSError:
            # Device disconnected or permission issue; stop cleanly.
            self.stop("DEVICE_ERROR")
        finally:
            try:
                self.device.ungrab()
            except Exception:
                pass

    def release_all(self) -> None:
        for key in [
            self._get_key_name("left"),
            self._get_key_name("right"),
            self._get_key_name("forward"),
            self._get_key_name("backward"),
            self._get_key_name("jump"),
        ]:
            self._release(key)

    def stop(self, reason: str = "STOP") -> None:
        if not self.running:
            return
        self.log(f"[mouse2wasd] EXIT ({reason})")
        self.running = False
        self.release_all()
        if self.ui is not None:
            try:
                self.ui.close()
            except Exception:
                pass
        if self.mouse_listener is not None:
            try:
                self.mouse_listener.stop()
            except Exception:
                pass
        if self.key_listener is not None:
            try:
                self.key_listener.stop()
            except Exception:
                pass
        if self.display is not None:
            try:
                self.display.close()
            except Exception:
                pass

    def start_pynput_backend(self) -> None:
        if self.mouse_listener is None or self.key_listener is None:
            return
        self.mouse_listener.start()
        self.key_listener.start()

    def wait_pynput_backend(self) -> None:
        if self.key_listener is not None:
            self.key_listener.join()


def terminal_esc_watcher(mapper: MouseToWasd) -> None:
    """Press Esc in the terminal to stop the app.

    This works even when GNOME Wayland blocks global keyboard listeners.
    """
    if not sys.stdin.isatty():
        return

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        while mapper.running:
            ready, _, _ = select.select([sys.stdin], [], [], 0.1)
            if not ready:
                continue

            ch = sys.stdin.read(1)
            if ch == "\x1b":
                mapper.stop("TERMINAL_ESC")
                return
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


class LogWindow:
    def __init__(self, title: str = "Mouse To WASD Logs", mapper=None):
        if tk is None:
            raise RuntimeError("Tkinter is not available")

        self.mapper = mapper
        self.settings_visible = False
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry("860x620")
        self.root.minsize(740, 520)

        self.counter_overlay = tk.Toplevel(self.root)
        self.counter_overlay.overrideredirect(True)
        self.counter_overlay.attributes("-topmost", True)
        self.counter_overlay.configure(bg="#0b1220")
        self.counter_overlay.attributes("-alpha", 0.62)

        screen_w = self.root.winfo_screenwidth()
        overlay_w = 150
        overlay_h = 32
        overlay_x = screen_w - overlay_w
        overlay_y = 0
        self.counter_overlay.geometry(
            f"{overlay_w}x{overlay_h}+{overlay_x}+{overlay_y}"
        )

        self.overlay_counter_var = tk.StringVar(value="counter 0.00")
        overlay_label = tk.Label(
            self.counter_overlay,
            textvariable=self.overlay_counter_var,
            bg="#0b1220",
            fg="#e2e8f0",
            font=("DejaVu Sans", 11, "bold"),
            padx=4,
            pady=2,
        )
        overlay_label.pack(fill="both", expand=True)

        self.queue: queue.Queue[str] = queue.Queue()
        self.status_queue: queue.Queue[tuple[str, str]] = queue.Queue()
        self.status_vars = {
            "backend": tk.StringVar(value="backend: ?"),
            "session": tk.StringVar(value="session: ?"),
            "enabled": tk.StringVar(value="enabled: yes"),
            "device": tk.StringVar(value="device: ?"),
            "last": tk.StringVar(value="last event: none"),
            "counter": tk.StringVar(value="counter: 0.00"),
        }

        self.key_choices = (
            mapper._supported_key_names() if mapper else ["w", "a", "s", "d", "space"]
        )

        self.key_input_vars = {
            "forward": tk.StringVar(
                value=mapper.config.key_forward
                if mapper and mapper.config.key_forward in self.key_choices
                else "w"
            ),
            "backward": tk.StringVar(
                value=mapper.config.key_backward
                if mapper and mapper.config.key_backward in self.key_choices
                else "s"
            ),
            "left": tk.StringVar(
                value=mapper.config.key_left
                if mapper and mapper.config.key_left in self.key_choices
                else "a"
            ),
            "right": tk.StringVar(
                value=mapper.config.key_right
                if mapper and mapper.config.key_right in self.key_choices
                else "d"
            ),
            "jump": tk.StringVar(
                value=mapper.config.key_jump
                if mapper and mapper.config.key_jump in self.key_choices
                else "space"
            ),
        }

        self._build_ui()
        self.root.after(50, self._drain)

    def _build_ui(self) -> None:
        container = ttk.Frame(self.root, padding=12)
        container.pack(fill="both", expand=True)

        top = ttk.Frame(container)
        top.pack(fill="x", pady=(0, 10))

        for key in ("backend", "session", "enabled", "device", "last"):
            ttk.Label(top, textvariable=self.status_vars[key]).pack(anchor="w")

        self.settings_frame = ttk.LabelFrame(container, text="Key Settings", padding=8)
        self.settings_frame.pack_forget()

        key_labels = [
            ("Forward (W)", "forward"),
            ("Backward (S)", "backward"),
            ("Left (A)", "left"),
            ("Right (D)", "right"),
            ("Jump (Space)", "jump"),
        ]

        for label_text, key_type in key_labels:
            frame = ttk.Frame(self.settings_frame)
            frame.pack(fill="x", pady=2)
            ttk.Label(frame, text=label_text, width=15).pack(side="left")
            entry = ttk.Combobox(
                frame,
                textvariable=self.key_input_vars[key_type],
                values=self.key_choices,
                width=12,
                state="readonly",
            )
            entry.pack(side="left", padx=4)
            entry.bind(
                "<<ComboboxSelected>>",
                lambda _event, kt=key_type: self._apply_key_setting(kt),
            )
            ttk.Button(
                frame,
                text="Apply",
                width=6,
                command=lambda kt=key_type: self._apply_key_setting(kt),
            ).pack(side="left")

        bars = ttk.Frame(container)
        bars.pack(fill="x", pady=(0, 8))

        ttk.Label(bars, text="Scroll Counter Magnitude").pack(anchor="w")
        self.counter_bar = ttk.Progressbar(
            bars, orient="horizontal", mode="determinate", maximum=1.0
        )
        self.counter_bar.pack(fill="x")
        ttk.Label(bars, textvariable=self.status_vars["counter"]).pack(anchor="w")

        self.text = tk.Text(
            container, wrap="word", height=22, bg="#0f172a", fg="#e2e8f0"
        )
        self.text.pack(fill="both", expand=True, side="left")
        self.text.configure(state="disabled", takefocus=0)
        for sequence in ("<Button-2>", "<ButtonRelease-2>", "<<Paste>>"):
            self.text.bind(sequence, lambda _event: "break")

        scroll = ttk.Scrollbar(container, command=self.text.yview)
        scroll.pack(fill="y", side="right")
        self.text.configure(yscrollcommand=scroll.set)

        bottom = ttk.Frame(container)
        bottom.pack(fill="x", pady=(10, 0))
        ttk.Button(bottom, text="Clear", command=self.clear).pack(side="left")
        ttk.Button(bottom, text="Settings", command=self._toggle_settings).pack(
            side="left", padx=4
        )
        ttk.Button(bottom, text="Quit", command=self.root.quit).pack(side="right")

        def close_windows() -> None:
            try:
                self.counter_overlay.destroy()
            except Exception:
                pass
            self.root.quit()

        self.root.protocol("WM_DELETE_WINDOW", close_windows)

    def log(self, message: str) -> None:
        self.queue.put(message)

    def set_status(self, key: str, value: str) -> None:
        self.status_queue.put((key, value))

    def set_enabled(self, enabled: bool) -> None:
        self.set_status("enabled", f"enabled: {'yes' if enabled else 'no'}")

    def set_last(self, value: str) -> None:
        self.set_status("last", f"last event: {value}")

    def _toggle_settings(self) -> None:
        self.settings_visible = not self.settings_visible
        if self.settings_visible:
            self.settings_frame.pack(
                fill="x", pady=(8, 0), after=self.text.master.winfo_children()[0]
            )
        else:
            self.settings_frame.pack_forget()

    def _apply_key_setting(self, key_type: str) -> None:
        if not self.mapper:
            return

        new_key = self.key_input_vars[key_type].get().lower().strip()
        if not new_key:
            self.log(f"[settings] Empty key for {key_type}")
            return

        if self.mapper._key_code(new_key) < 0:
            self.log(f"[settings] Unsupported key for {key_type}: {new_key}")
            self.key_input_vars[key_type].set(self.mapper._get_key_name(key_type))
            return

        try:
            # Update config
            if key_type == "forward":
                self.mapper.config.key_forward = new_key
            elif key_type == "backward":
                self.mapper.config.key_backward = new_key
            elif key_type == "left":
                self.mapper.config.key_left = new_key
            elif key_type == "right":
                self.mapper.config.key_right = new_key
            elif key_type == "jump":
                self.mapper.config.key_jump = new_key

            self.mapper._init_held_keys()
            self.log(f"[settings] Updated {key_type} -> {new_key}")
        except Exception as e:
            self.log(f"[settings] Error updating {key_type}: {e}")

    def clear(self) -> None:
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.configure(state="disabled")

    def _drain(self) -> None:
        try:
            while True:
                message = self.queue.get_nowait()
                self.text.configure(state="normal")
                self.text.insert("end", message + "\n")
                self.text.see("end")
                self.text.configure(state="disabled")
        except queue.Empty:
            pass

        try:
            while True:
                key, value = self.status_queue.get_nowait()
                if key in self.status_vars:
                    self.status_vars[key].set(value)
                if key == "counter":
                    try:
                        counter_value = float(value.split(":", 1)[1].strip())
                        self.counter_bar["value"] = abs(counter_value)
                        self.overlay_counter_var.set(f"counter {counter_value:+.2f}")
                    except Exception:
                        pass
        except queue.Empty:
            pass
        self.root.after(50, self._drain)

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    parser = argparse.ArgumentParser(description="Mouse to WASD mapper")
    parser.add_argument(
        "--debug", action="store_true", help="Print mouse and key events"
    )
    parser.add_argument(
        "--pulse-ms", type=float, default=90.0, help="W/S tap duration in ms"
    )
    parser.add_argument(
        "--wheel-step",
        type=float,
        default=0.35,
        help="Charge added per wheel notch (0..1)",
    )
    parser.add_argument(
        "--wheel-press-threshold",
        type=float,
        default=1.0,
        help="Press W/S when charge reaches this value",
    )
    parser.add_argument(
        "--wheel-release-threshold",
        type=float,
        default=0.5,
        help="Release W/S when charge drops to this value",
    )
    parser.add_argument(
        "--no-gui",
        action="store_true",
        help="Disable the log window GUI",
    )
    parser.add_argument(
        "--backend",
        choices=["auto", "evdev", "x11", "pynput"],
        default="auto",
        help="Input capture backend (auto tries evdev first)",
    )
    parser.add_argument(
        "--key-forward",
        type=str,
        default="w",
        help="Key for forward (e.g. w, up)",
    )
    parser.add_argument(
        "--key-backward",
        type=str,
        default="s",
        help="Key for backward (e.g. s, down)",
    )
    parser.add_argument(
        "--key-left",
        type=str,
        default="a",
        help="Key for left turn (e.g. a, left)",
    )
    parser.add_argument(
        "--key-right",
        type=str,
        default="d",
        help="Key for right turn (e.g. d, right)",
    )
    parser.add_argument(
        "--key-jump",
        type=str,
        default="space",
        help="Key for jump/action (e.g. space, w)",
    )
    args = parser.parse_args()

    mapper = MouseToWasd(
        Config(
            pulse_ms=args.pulse_ms,
            wheel_step=args.wheel_step,
            wheel_press_threshold=args.wheel_press_threshold,
            wheel_release_threshold=args.wheel_release_threshold,
            backend=args.backend,
            debug=args.debug,
            gui=not args.no_gui,
            key_forward=args.key_forward,
            key_backward=args.key_backward,
            key_left=args.key_left,
            key_right=args.key_right,
            key_jump=args.key_jump,
        )
    )

    if args.wheel_release_threshold > args.wheel_press_threshold:
        raise SystemExit(
            "[mouse2wasd] wheel-release-threshold must be <= wheel-press-threshold"
        )

    log_window = None
    gui_enabled = mapper.config.gui and tk is not None and ttk is not None
    if gui_enabled:
        try:
            log_window = LogWindow(mapper=mapper)

            def gui_log(message: str) -> None:
                print(message)
                log_window.log(message)

            mapper.set_logger(gui_log)
            mapper.set_status_callback(log_window.set_status)
        except Exception as exc:
            print(f"[mouse2wasd] GUI unavailable: {exc}")
            log_window = None

    if log_window is None:
        mapper.set_logger(print)

    session_type = os.environ.get("XDG_SESSION_TYPE", "unknown")
    desktop = os.environ.get("XDG_CURRENT_DESKTOP", "unknown")

    def handle_signal(_sig, _frame):
        mapper.stop("SIGNAL")
        raise SystemExit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    mapper.log("[mouse2wasd] Running")
    mapper.log(f"[mouse2wasd] Session: {session_type} ({desktop})")
    mapper.log(
        f"[mouse2wasd] Scroll up/down -> {args.key_forward.upper()}/{args.key_backward.upper()}"
    )
    mapper.log("[mouse2wasd] Touchpad devices are ignored (mouse-only mapping)")
    mapper.log(
        f"[mouse2wasd] Hold left/right mouse -> {args.key_left.upper()}/{args.key_right.upper()}"
    )
    mapper.log(f"[mouse2wasd] Hold middle mouse -> {args.key_jump.upper()}")
    mapper.log("[mouse2wasd] Press Esc in this terminal to stop")
    mapper.log("[mouse2wasd] Ctrl+C also stops the app")
    mapper.log(
        "[mouse2wasd] Wheel thresholds: "
        f"press={args.wheel_press_threshold:.2f}, release={args.wheel_release_threshold:.2f}"
    )
    mapper.log(f"[mouse2wasd] Wheel step={args.wheel_step:.2f}")
    mapper.log("[mouse2wasd] Single counter mode (up increases, down decreases)")
    mapper.log("[mouse2wasd] Counter changes only on manual scroll")
    if args.debug:
        mapper.log("[mouse2wasd] Debug mode enabled")
    if mapper.backend == "x11":
        mapper.log("[mouse2wasd] Using X11 keyboard controller backend")
    elif mapper.backend == "pynput":
        mapper.log("[mouse2wasd] Using pynput hook backend")
    else:
        mapper.log("[mouse2wasd] Using evdev/uinput backend")
    mapper.log(f"[mouse2wasd] Backend request: {args.backend}")

    if log_window is not None:
        log_window.set_status("backend", f"backend: {mapper.backend}")
        log_window.set_status("session", f"session: {session_type} ({desktop})")
        log_window.set_enabled(mapper.enabled)
        if mapper.backend == "evdev" and mapper.device is not None:
            log_window.set_status(
                "device", f"device: {mapper.device.name} ({mapper.device.path})"
            )
        elif mapper.backend == "x11":
            log_window.set_status("device", "device: X11 virtual keyboard")
        elif mapper.backend == "pynput":
            log_window.set_status("device", "device: global mouse hooks")
        log_window.set_status("counter", "counter: 0.00")
        log_window.set_last("startup")

    esc_thread = threading.Thread(
        target=terminal_esc_watcher, args=(mapper,), daemon=True
    )
    esc_thread.start()

    if mapper.backend == "pynput":
        mapper.start_pynput_backend()
    else:
        device_thread = threading.Thread(target=mapper.run_device_loop, daemon=True)
        device_thread.start()

    def monitor_stop() -> None:
        while mapper.running:
            time.sleep(0.1)
        if log_window is not None:
            try:
                log_window.root.after(0, log_window.root.quit)
            except Exception:
                pass

    monitor_thread = threading.Thread(target=monitor_stop, daemon=True)
    monitor_thread.start()

    try:
        if log_window is not None:
            log_window.run()
        else:
            while mapper.running:
                time.sleep(0.05)
    finally:
        mapper.release_all()
        mapper.stop("EXIT")


if __name__ == "__main__":
    main()
