#!/usr/bin/env python3
"""Generate a small, deterministic Dolphin DTM movie for the clean-room GameCube demo.

The file follows Dolphin's 256-byte DTMHeader and its packed 8-byte GameCube
ControllerState records. It contains only synthetic button inputs; no game
assets or proprietary data are embedded.
"""
from __future__ import annotations

import argparse
import struct
from pathlib import Path

HEADER_SIZE = 256
CONTROLLER_STATE_SIZE = 8
DEFAULT_FRAMES = 3600
MAX_FRAMES = 12000

# Dolphin's packed Movie::ControllerState: first-byte buttons.
START = 1 << 0
A = 1 << 1
B = 1 << 2
X = 1 << 3
Y = 1 << 4

# Second byte controller state flags / D-pad directions.
DPAD_LEFT = 1 << 0
DPAD_RIGHT = 1 << 1
IS_CONNECTED = 1 << 6


def _controller_state(frame: int) -> bytes:
    """Return one packed state matching Dolphin's current 8-byte GC record."""
    buttons = A
    if frame == 0:
        # Reset the prototype to a known start state.
        buttons |= Y
    if 1 <= frame < 80:
        buttons |= X
    if 100 <= frame < 140:
        buttons |= B
    if frame in (220, 280):
        # Toggle pause, then resume. Each press lasts exactly one poll.
        buttons |= START

    flags = IS_CONNECTED
    if frame < 2000:
        flags |= DPAD_RIGHT
    elif frame < 2800:
        flags |= DPAD_LEFT

    # Trigger and analog axes are neutral. The D-pad provides the deterministic
    # left/right steering signal, avoiding host-controller calibration issues.
    return bytes((buttons, flags, 0, 0, 0, 0, 0, 0))


def build_dtm(frame_count: int = DEFAULT_FRAMES) -> bytes:
    """Build a boot-from-DOL movie with one GameCube controller input per frame."""
    if not isinstance(frame_count, int) or isinstance(frame_count, bool):
        raise ValueError("frame_count must be an integer")
    if frame_count < 1 or frame_count > MAX_FRAMES:
        raise ValueError(f"frame_count must be between 1 and {MAX_FRAMES}")

    header = bytearray(HEADER_SIZE)
    header[0:4] = b"DTM\x1a"
    # This clean-room demo boots from a .dol, not a retail disc; its game ID
    # and disc hash are intentionally empty. bWii=0, port 1 connected, no savestate.
    header[0x0B] = 0x01
    struct.pack_into("<QQQQ", header, 0x0D, frame_count, frame_count, 0, 0)
    struct.pack_into("<I", header, 0x2D, 0)
    header[0x31:0x31 + len(b"Boonta CI")] = b"Boonta CI"
    # bSaveConfig remains false, so this synthetic movie cannot override the
    # runner's display, input or emulator settings.
    data = bytearray(header)
    for frame in range(frame_count):
        data.extend(_controller_state(frame))
    return bytes(data)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path, help="destination .dtm path")
    parser.add_argument("--frames", type=int, default=DEFAULT_FRAMES,
                        help=f"movie input polls (1..{MAX_FRAMES}; default {DEFAULT_FRAMES})")
    args = parser.parse_args()
    payload = build_dtm(args.frames)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(payload)
    print(f"Wrote {args.output}: {args.frames} controller polls, {len(payload)} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
