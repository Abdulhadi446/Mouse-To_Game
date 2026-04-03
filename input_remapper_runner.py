#!/usr/bin/env python3
"""Start an Input Remapper preset and stop it with terminal ESC.

This is a lightweight controller around `input-remapper-control`.
It does not create mappings; it starts/stops an existing preset.
"""

from __future__ import annotations

import argparse
import select
import subprocess
import sys

try:
    import termios
    import tty
except ImportError:  # pragma: no cover - Windows
    termios = None
    tty = None

try:
    import msvcrt
except ImportError:  # pragma: no cover - non-Windows
    msvcrt = None


def looks_like_touchpad(name: str) -> bool:
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


def run_control(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["input-remapper-control", *args],
        check=False,
        capture_output=True,
        text=True,
    )


def list_device_keys() -> list[str]:
    result = run_control(["--list-devices"])
    if result.returncode != 0:
        return []

    keys = []
    for line in result.stdout.splitlines():
        entry = line.strip()
        if not entry:
            continue
        keys.append(entry)
    return keys


def start_preset(device: str, preset: str) -> None:
    result = run_control(["--command", "start", "--device", device, "--preset", preset])
    if result.returncode != 0:
        msg = result.stderr.strip() or result.stdout.strip() or "unknown error"
        raise SystemExit(f"[remapper] Failed to start preset: {msg}")


def stop_all() -> None:
    run_control(["--command", "stop-all"])


def esc_wait_loop() -> None:
    if not sys.stdin.isatty():
        # Non-interactive mode: block until interrupted.
        try:
            while True:
                select.select([], [], [], 1.0)
        except KeyboardInterrupt:
            return

    if msvcrt is not None:
        while True:
            if msvcrt.kbhit():
                if msvcrt.getch() == b"\x1b":
                    return
            select.select([], [], [], 0.05)
        return

    if termios is None or tty is None:
        return

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        while True:
            ready, _, _ = select.select([sys.stdin], [], [], 0.1)
            if not ready:
                continue
            ch = sys.stdin.read(1)
            if ch == "\x1b":
                return
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run Input Remapper preset and stop on ESC"
    )
    parser.add_argument("--device", help="Device key as used by Input Remapper")
    parser.add_argument("--preset", help="Preset name without .json")
    parser.add_argument(
        "--allow-touchpad",
        action="store_true",
        help="Override safety check and allow touchpad-like device names",
    )
    args = parser.parse_args()

    if not args.device:
        devices = list_device_keys()
        if devices and sys.stdin.isatty():
            print("[remapper] Available device keys:")
            for index, device in enumerate(devices, start=1):
                print(f"  {index}. {device}")
            choice = input("[remapper] Pick a device number or type a key: ").strip()
            if choice.isdigit():
                selection = int(choice)
                if 1 <= selection <= len(devices):
                    args.device = devices[selection - 1]
            elif choice:
                args.device = choice

        if sys.stdin.isatty():
            if not args.device:
                args.device = input("[remapper] Device key: ").strip()
        if not args.device:
            raise SystemExit(
                "[remapper] Missing --device. Run `input-remapper-control --list-devices` to see available keys."
            )

    if not args.preset:
        if sys.stdin.isatty():
            args.preset = input("[remapper] Preset name: ").strip()
        if not args.preset:
            raise SystemExit("[remapper] Missing --preset")

    if looks_like_touchpad(args.device) and not args.allow_touchpad:
        raise SystemExit(
            "[remapper] Refusing touchpad-like device. "
            "Use a mouse device key, or pass --allow-touchpad to override."
        )

    print(f"[remapper] Starting preset '{args.preset}' on '{args.device}'")
    start_preset(args.device, args.preset)
    print("[remapper] Running. Press ESC in this terminal to stop.")

    try:
        esc_wait_loop()
    except KeyboardInterrupt:
        pass
    finally:
        print("[remapper] Stopping all injections")
        stop_all()


if __name__ == "__main__":
    main()
