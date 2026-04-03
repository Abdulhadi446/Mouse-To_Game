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
import termios
import tty


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
    parser.add_argument(
        "--device", required=True, help="Device key as used by Input Remapper"
    )
    parser.add_argument("--preset", required=True, help="Preset name without .json")
    parser.add_argument(
        "--allow-touchpad",
        action="store_true",
        help="Override safety check and allow touchpad-like device names",
    )
    args = parser.parse_args()

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
