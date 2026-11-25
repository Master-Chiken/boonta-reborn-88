#!/usr/bin/env python3
"""Run a GameCube DOL in Dolphin and inspect its stage through Dolphin's GDB stub."""

from __future__ import annotations

import argparse
import re
import socket
import subprocess
import sys
import time
from pathlib import Path


class RSPClient:
    def __init__(self, sock: socket.socket) -> None:
        self.sock = sock
        self.sock.settimeout(60.0)
        self.pending_packet: str | None = None

    @staticmethod
    def packet(payload: bytes) -> bytes:
        checksum = sum(payload) & 0xFF
        return b"$" + payload + b"#" + f"{checksum:02x}".encode("ascii")

    def send_packet(self, payload: str) -> None:
        self.sock.sendall(self.packet(payload.encode("ascii")))

    def read_exact(self, size: int, description: str) -> bytes:
        data = bytearray()
        while len(data) < size:
            chunk = self.sock.recv(size - len(data))
            if not chunk:
                raise ConnectionError(f"Dolphin GDB socket closed while reading {description}")
            data.extend(chunk)
        return bytes(data)

    def read_packet_body(self) -> str:
        payload = bytearray()
        while True:
            value = self.sock.recv(1)
            if not value:
                raise ConnectionError("Dolphin GDB socket closed inside packet")
            if value == b"#":
                break
            payload.extend(value)

        checksum = self.read_exact(2, "packet checksum")
        expected = sum(payload) & 0xFF
        try:
            received = int(checksum.decode("ascii"), 16)
        except ValueError as exc:
            raise RuntimeError(f"Invalid GDB checksum field: {checksum!r}") from exc
        if received != expected:
            raise RuntimeError(
                f"GDB packet checksum mismatch: received {received:02x}, expected {expected:02x}"
            )
        self.sock.sendall(b"+")
        return payload.decode("ascii", errors="replace")

    def read_ack(self) -> None:
        while True:
            value = self.sock.recv(1)
            if not value:
                raise ConnectionError("Dolphin GDB socket closed before ACK")
            if value == b"+":
                return
            if value == b"-":
                raise RuntimeError("Dolphin GDB stub rejected the command (NACK)")
            if value == b"$":
                # Accept a reply packet sent without a separate '+' ACK, and
                # preserve it for the caller waiting for the command response.
                self.pending_packet = self.read_packet_body()
                return

    def read_packet(self) -> str:
        if self.pending_packet is not None:
            packet = self.pending_packet
            self.pending_packet = None
            return packet

        while True:
            value = self.sock.recv(1)
            if not value:
                raise ConnectionError("Dolphin GDB socket closed before packet")
            if value in (b"+", b"\\n", b"\\r"):
                continue
            if value == b"-":
                raise RuntimeError("Dolphin GDB stub sent NACK")
            if value == b"$":
                return self.read_packet_body()

    def command(self, payload: str) -> str:
        self.send_packet(payload)
        self.read_ack()
        return self.read_packet()

    def continue_execution(self) -> None:
        # The RSP "c" command is asynchronous: the stub replies with a stop
        # packet only after the target halts, not with an ordinary ACK.
        # read_packet() handles an optional ACK before that stop packet.
        self.send_packet("c")

    def interrupt(self) -> str:
        self.sock.sendall(b"\x03")
        return self.read_packet()


def load_symbols(path: Path) -> dict[str, int]:
    result: dict[str, int] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) != 2:
            continue
        name, address = parts
        result[name] = int(address, 16)
    required = {
        "g_probe_stage",
        "g_probe_failure_code",
        "g_probe_failure_label",
        "g_probe_failure_actual",
        "g_probe_failure_expected",
    }
    missing = required - result.keys()
    if missing:
        raise ValueError(f"Missing symbols in {path}: {', '.join(sorted(missing))}")
    return result


def read_memory(rsp: RSPClient, address: int, size: int) -> bytes:
    reply = rsp.command(f"m{address:08x},{size:x}")
    print(f"GDB memory reply at 0x{address:08x}: {reply!r}", flush=True)
    if reply.startswith("E"):
        raise RuntimeError(f"Dolphin GDB memory read failed at 0x{address:08x}: {reply}")
    try:
        data = bytes.fromhex(reply)
    except ValueError as exc:
        raise RuntimeError(f"Invalid memory reply for 0x{address:08x}: {reply!r}") from exc
    if len(data) != size:
        raise RuntimeError(
            f"Short memory reply at 0x{address:08x}: {len(data)} bytes, expected {size}"
        )
    return data


def nearest_text_symbol(symbols: dict[str, int], address: int) -> tuple[str, int] | None:
    candidates = [
        (symbol_address, name)
        for name, symbol_address in symbols.items()
        if not name.startswith("g_probe_") and symbol_address <= address
    ]
    if not candidates:
        return None
    symbol_address, name = max(candidates)
    return name, address - symbol_address


def tail_file(path: Path, line_count: int = 40) -> str:
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return ""
    return "\n".join(lines[-line_count:])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dolphin", default="dolphin-emu-nogui")
    parser.add_argument("--dol", type=Path, required=True)
    parser.add_argument("--symbols", type=Path, required=True)
    parser.add_argument("--user-dir", type=Path, required=True)
    parser.add_argument("--stdout-log", type=Path, required=True)
    parser.add_argument("--port", type=int, default=55000)
    parser.add_argument("--run-seconds", type=float, default=1.5)
    parser.add_argument("--connect-timeout", type=float, default=30.0)
    args = parser.parse_args()

    symbols = load_symbols(args.symbols)
    args.user_dir.mkdir(parents=True, exist_ok=True)
    args.stdout_log.parent.mkdir(parents=True, exist_ok=True)

    command = [
        args.dolphin,
        "--platform=headless",
        "--video_backend=Null",
        f"--exec={args.dol.resolve()}",
        f"--user={args.user_dir.resolve()}",
        "-C", f"Dolphin.General.GDBPort={args.port}",
        "-C", "Logger.Options.WriteToFile=True",
        "-C", "Logger.Options.WriteToConsole=True",
        "-C", "Logger.Options.Verbosity=4",
        "-C", "Logger.Logs.GDB_STUB=True",
        "-C", "Logger.Logs.BOOT=True",
        "-C", "Logger.Logs.CORE=True",
        "-C", "Dolphin.Interface.DebugModeEnabled=True",
        "-C", "Dolphin.Interface.UsePanicHandlers=False",
        "-C", "Dolphin.Interface.ConfirmStop=False",
    ]

    process: subprocess.Popen[bytes] | None = None
    sock: socket.socket | None = None
    phase = "starting Dolphin"
    try:
        with args.stdout_log.open("wb") as output:
            process = subprocess.Popen(
                command,
                stdout=output,
                stderr=subprocess.STDOUT,
                close_fds=True,
            )

            deadline = time.monotonic() + args.connect_timeout
            last_error: Exception | None = None
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise RuntimeError(
                        f"Dolphin exited before opening GDB port (status {process.returncode})"
                    )
                try:
                    sock = socket.create_connection(("127.0.0.1", args.port), timeout=1.0)
                    break
                except OSError as exc:
                    last_error = exc
                    time.sleep(0.1)
            if sock is None:
                stdout_tail = tail_file(args.stdout_log)
                dolphin_log_tail = tail_file(args.user_dir / "Logs" / "dolphin.log")
                diagnostics = "\n".join(
                    part for part in (
                        "Dolphin stdout/stderr tail:\n" + stdout_tail if stdout_tail else "",
                        "Dolphin log tail:\n" + dolphin_log_tail if dolphin_log_tail else "",
                    ) if part
                )
                raise TimeoutError(
                    f"Could not connect to Dolphin GDB port {args.port}: {last_error}\n{diagnostics}"
                )

            phase = "GDB qSupported request"
            print("GDB: sending qSupported", flush=True)
            rsp = RSPClient(sock)
            supported = rsp.command("qSupported:multiprocess+;swbreak+;hwbreak+")
            print(f"GDB qSupported: {supported}", flush=True)

            phase = "running the PowerPC memory probe"
            print(f"GDB: resuming DOL for up to {args.run_seconds * 5:.1f}s", flush=True)
            rsp.continue_execution()

            stage = ""
            stop_reply = ""
            pc = None
            for attempt in range(5):
                time.sleep(args.run_seconds)
                phase = "interrupting Dolphin and reading guest state"
                stop_reply = rsp.interrupt()
                print(f"GDB stop reply: {stop_reply}", flush=True)
                pc_match = re.search(r"40:([0-9a-fA-F]{8})", stop_reply)
                pc = int(pc_match.group(1), 16) if pc_match else None
                stage = read_memory(rsp, symbols["g_probe_stage"], 4).decode(
                    "ascii", errors="replace"
                )
                print(f"RECOMP_PPC_MEMORY_PROBE:STAGE {stage!r}", flush=True)

                if stage in ("PASS", "FAIL"):
                    break
                if stage != "STAR":
                    location = nearest_text_symbol(symbols, pc) if pc is not None else None
                    detail = (
                        f"{location[0]}+0x{location[1]:x}" if location else "unknown location"
                    )
                    raise RuntimeError(
                        f"DOL did not reach main/probe execution: stage={stage!r}, "
                        f"PC={f'0x{pc:08x}' if pc is not None else 'unknown'} ({detail})"
                    )
                if attempt < 4:
                    print(
                        f"Probe still running; resuming for another {args.run_seconds:.1f}s",
                        flush=True,
                    )
                    rsp.continue_execution()

            if stage == "PASS":
                print("RECOMP_PPC_MEMORY_PROBE:PASS (guest memory tests completed)", flush=True)
                return 0

            if stage == "FAIL":
                failure_code = int.from_bytes(
                    read_memory(rsp, symbols["g_probe_failure_code"], 4), "big"
                )
                label = read_memory(rsp, symbols["g_probe_failure_label"], 24)
                label_text = label.split(b"\0", 1)[0].decode("ascii", errors="replace")
                actual = int.from_bytes(
                    read_memory(rsp, symbols["g_probe_failure_actual"], 8), "big"
                )
                expected = int.from_bytes(
                    read_memory(rsp, symbols["g_probe_failure_expected"], 8), "big"
                )
                print(
                    "RECOMP_PPC_MEMORY_PROBE:FAIL "
                    f"code={failure_code} label={label_text!r} "
                    f"actual=0x{actual:016x} expected=0x{expected:016x}",
                    flush=True,
                )
                return 1

            raise RuntimeError(
                f"Probe did not finish within {args.run_seconds * 5:.1f}s; last stage={stage!r}"
            )
    finally:
        if sock is not None:
            try:
                sock.close()
            except OSError:
                pass
        if process is not None:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"ERROR during {locals().get('phase', 'initialization')}: {error}", file=sys.stderr, flush=True)
        raise SystemExit(1)
