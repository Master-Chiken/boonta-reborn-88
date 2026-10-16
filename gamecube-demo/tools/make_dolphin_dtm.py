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
RESET_PRESS_FRAME = 120  # Build non-default gameplay state before testing Y reset.
RESET_HOLD_FRAMES = 6  # Approx. 100 ms at 60 Hz; avoids an unrealistically short button tap.
RESET_BOOST_END_FRAME = 60
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


def _controller_state(frame: int, steering: str = "right",
                      scenario: str = "control-smoke",
                      steering_source: str = "dpad") -> bytes:
    """Return one packed controller poll with one explicit steering source."""
    if scenario == "reset-check":
        # First create a state that differs visibly from reset: accelerate, boost,
        # and steer. Y is pressed alone at frame 240; every later poll is neutral.
        if frame < RESET_PRESS_FRAME:
            buttons = A
            if 1 <= frame < RESET_BOOST_END_FRAME:
                buttons |= X
        elif RESET_PRESS_FRAME <= frame < RESET_PRESS_FRAME + RESET_HOLD_FRAMES:
            buttons = Y
        else:
            buttons = 0
    else:
        buttons = A  # Hold accelerator for the normal control/race scenarios.
        if frame == 0:
            buttons |= Y  # Reset to a deterministic starting position.
        if 1 <= frame < 80:
            buttons |= X  # Boost near the start.
    if scenario == "control-smoke":
        if 100 <= frame < 140:
            buttons |= B  # Exercise a short brake pulse.
        if frame in (220, 280):
            buttons |= START  # Pause, then resume with one-frame presses.

    flags = IS_CONNECTED
    stick_x = NEUTRAL_AXIS
    # Control-smoke movies exercise exactly one steering source at a time. A full
    # race stays centered so it tests lap progression rather than steering response.
    if ((scenario == "control-smoke" and frame < STEERING_HOLD_FRAMES)
            or (scenario == "reset-check" and frame < RESET_PRESS_FRAME)):
        if steering_source == "dpad":
            if steering == "right":
                flags |= DPAD_RIGHT
            elif steering == "left":
                flags |= DPAD_LEFT
        elif steering_source == "stick":
            if steering == "right":
                stick_x = 255
            elif steering == "left":
                stick_x = 0

    # DTM ControllerState packs digital buttons first, then analog trigger bytes,
    # then main-stick and C-stick axes. Neutral unsigned axes are centered at 128;
    # 0 and 255 deliberately represent full-left and full-right for the main stick.
    return bytes((buttons, flags, 0, 0, stick_x, NEUTRAL_AXIS,
                  NEUTRAL_AXIS, NEUTRAL_AXIS))


def build_dtm(frame_count: int = DEFAULT_FRAMES, game_id: str = DEFAULT_GAME_ID,
              steering: str = "right", scenario: str = "control-smoke",
              steering_source: str = "dpad") -> bytes:
    """Build a boot-from-DOL movie whose ID matches the selected homebrew DOL."""
    if not isinstance(frame_count, int) or isinstance(frame_count, bool):
        raise ValueError("frame_count must be an integer")
    if frame_count < 1 or frame_count > MAX_FRAMES:
        raise ValueError(f"frame_count must be between 1 and {MAX_FRAMES}")
    if not isinstance(game_id, str) or len(game_id.encode("ascii", errors="strict")) != 6:
        raise ValueError("game_id must be exactly six ASCII bytes")
    if steering not in ("none", "left", "right"):
        raise ValueError("steering must be one of: none, left, right")
    if scenario not in ("control-smoke", "full-race", "reset-check"):
        raise ValueError("scenario must be one of: control-smoke, full-race, reset-check")
    if steering_source not in ("dpad", "stick"):
        raise ValueError("steering_source must be one of: dpad, stick")
    if scenario == "full-race" and steering != "none":
        raise ValueError("full-race scenario requires --steering none")

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
        data.extend(_controller_state(frame, steering, scenario, steering_source))
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
    parser.add_argument("--scenario", choices=("control-smoke", "full-race", "reset-check"),
                        default="control-smoke",
                        help="short control validation, full race, or neutral Y-reset check")
    parser.add_argument("--steering-source", choices=("dpad", "stick"), default="dpad",
                        help="send steering with the D-pad or analog main stick")
    args = parser.parse_args()
    payload = build_dtm(args.frames, args.game_id, args.steering, args.scenario,
                        args.steering_source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(payload)
    print(f"Wrote {args.output}: {args.frames} controller polls, game ID {args.game_id!r}, "
          f"steering={args.steering}, source={args.steering_source}, scenario={args.scenario}, "
          f"{len(payload)} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
