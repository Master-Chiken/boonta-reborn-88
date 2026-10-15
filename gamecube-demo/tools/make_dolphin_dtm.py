#!/usr/bin/env python3
"""Generate a deterministic Dolphin DTM movie for the clean-room GameCube demo.

Uses Dolphin's 256-byte DTMHeader and packed 8-byte GameCube ControllerState
records. Only synthetic controller inputs are stored; no game assets or
proprietary data are embedded.
"""
from __future__ import annotations

import argparse
import struct
from pathlib import Path

HEADER_SIZE = 256
CONTROLLER_STATE_SIZE = 8
DEFAULT_FRAMES = 3600
MAX_FRAMES = 12000
STEERING_HOLD_FRAMES = 600  # Long enough to measure response, short enough to avoid driving off-frame.
DEFAULT_GAME_ID = "ID-boo"  # Dolphin's MakeGameID("boonta_gc_demo.dol") prefix.

# First byte: Start, A, B, X, Y, Z, D-pad up, D-pad down.
START = 1 << 0
A = 1 << 1
B = 1 << 2
X = 1 << 3
Y = 1 << 4

# Second byte: D-pad left/right, L/R, disc, reset, connected, origin.
DPAD_LEFT = 1 << 0
DPAD_RIGHT = 1 << 1
IS_CONNECTED = 1 << 6
NEUTRAL_AXIS = 128


def _controller_state(frame: int, steering: str = "right") -> bytes:
    """Return one packed controller poll with neutral analog axes."""
    buttons = A  # Hold accelerator for the whole run.
    if frame == 0:
        buttons |= Y  # Reset to a deterministic starting position.
    if 1 <= frame < 80:
        buttons |= X  # Boost near the start.
    if 100 <= frame < 140:
        buttons |= B  # Brake pulse.
    if frame in (220, 280):
        buttons |= START  # Pause, then resume with one-frame presses.

    flags = IS_CONNECTED
    # Keep the requested direction held during the slow software-renderer capture.
    if steering == "right" and frame < STEERING_HOLD_FRAMES:
        flags |= DPAD_RIGHT
    elif steering == "left" and frame < STEERING_HOLD_FRAMES:
        flags |= DPAD_LEFT

    # DTM stores Dolphin's controller axes as unsigned bytes (0..255), centered at
    # 128. The emulated controller layer converts that center to libogc's signed 0;
    # writing 0 here would encode full-left/full-down, not a neutral baseline.
    return bytes((buttons, flags, 0, 0, NEUTRAL_AXIS, NEUTRAL_AXIS,
                  NEUTRAL_AXIS, NEUTRAL_AXIS))


def build_dtm(frame_count: int = DEFAULT_FRAMES, game_id: str = DEFAULT_GAME_ID,
              steering: str = "right") -> bytes:
    """Build a boot-from-DOL movie whose ID matches the selected homebrew DOL."""
    if not isinstance(frame_count, int) or isinstance(frame_count, bool):
        raise ValueError("frame_count must be an integer")
    if frame_count < 1 or frame_count > MAX_FRAMES:
        raise ValueError(f"frame_count must be between 1 and {MAX_FRAMES}")
    if not isinstance(game_id, str) or len(game_id.encode("ascii", errors="strict")) != 6:
        raise ValueError("game_id must be exactly six ASCII bytes")
    if steering not in ("none", "left", "right"):
        raise ValueError("steering must be one of: none, left, right")

    header = bytearray(HEADER_SIZE)
    header[0:4] = b"DTM\x1a"
    header[4:10] = game_id.encode("ascii")
    header[0x0A] = 0  # bWii=False (GameCube demo).
    header[0x0B] = 0x01  # controller port 1 is a GameCube pad.
    header[0x0C] = 0  # bFromSaveState=False; starts from boot.
    struct.pack_into("<QQQQ", header, 0x0D, frame_count, frame_count, 0, 0)
    struct.pack_into("<I", header, 0x2D, 0)  # numRerecords
    # Dolphin stops movie playback once emulated ticks exceed DTMHeader.tickCount.
    # The demo's test movie boots an executable, so use a conservative PAL-safe
    # tick budget (486 MHz / 50 Hz = 9.72M ticks per frame); input bytes still
    # end playback exactly at frame_count.
    struct.pack_into("<Q", header, 0xED, frame_count * 10_000_000)
    author = b"Boonta CI"
    header[0x31:0x31 + len(author)] = author
    header[0x89] = 0  # bSaveConfig=False; do not override emulator settings.

    data = bytearray(header)
    for frame in range(frame_count):
        data.extend(_controller_state(frame, steering))
    return bytes(data)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path, help="destination .dtm path")
    parser.add_argument("--frames", type=int, default=DEFAULT_FRAMES,
                        help=f"controller polls (1..{MAX_FRAMES}; default {DEFAULT_FRAMES})")
    parser.add_argument("--game-id", default=DEFAULT_GAME_ID,
                        help="six-byte Dolphin executable ID; default matches boonta_gc_demo.dol")
    parser.add_argument("--steering", choices=("none", "left", "right"), default="right",
                        help="directional pulse to encode; use none for a neutral baseline")
    args = parser.parse_args()
    payload = build_dtm(args.frames, args.game_id, args.steering)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(payload)
    print(f"Wrote {args.output}: {args.frames} controller polls, game ID {args.game_id!r}, steering={args.steering}, {len(payload)} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
