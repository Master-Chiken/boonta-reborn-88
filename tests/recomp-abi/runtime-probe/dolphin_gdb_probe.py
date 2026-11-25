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
        self.sock.settimeout(10.0)

    @staticmethod
    def packet(payload: bytes) -> bytes:
        checksum = sum(payload) & 0xFF
        return b"$" + payload + b"#" + f"{checksum:02x}".encode("ascii")

    def send_packet(self, payload: str) -> None:
        self.sock.sendall(self.packet(payload.encode("ascii")))

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
                raise RuntimeError("Received a GDB packet where an ACK was expected")

    def read_packet(self) -> str:
        while True:
            value = self.sock.recv(1)
            if not value:
                raise ConnectionError("Dolphin GDB socket closed before packet")
            if value in (b"+", b"\n", b"\r"):
                continue
            if value == b"-":
                raise RuntimeError("Dolphin GDB stub sent NACK")
            if value == b"$":
                break

        payload = bytearray()
        while True:
            value = self.sock.recv(1)
            if not value:
                raise ConnectionError("Dolphin GDB socket closed inside packet")
            if value == b"#":
                break
            payload.extend(value)

        checksum = self.sock.recv(2)
        if len(checksum) != 2:
            raise ConnectionError("Incomplete GDB packet checksum")
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

    def command(self, payload: str) -> str:
        self.send_packet(payload)
        self.read_ack()
        return self.read_packet()

    def continue_execution(self) -> None:
        self.send_packet("c")
        self.read_ack()

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
    required = {"g_probe_stage", "g_probe_failure_code", "g_probe_failure_label"}
    missing = required - result.keys()
    if missing:
        raise ValueError(f"Missing symbols in {path}: {', '.join(sorted(missing))}")
    return result


def read_memory(rsp: RSPClient, address: int, size: int) -> bytes:
    reply = rsp.command(f"m{address:08x},{size:x}")
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
        "-C", f"Main.General.GDBPort={args.port}",
        "-C", "Logger.Options.WriteToFile=True",
        "-C", "Logger.Options.WriteToConsole=True",
        "-C", "Logger.Options.Verbosity=4",
        "-C", "Logger.Logs.GDB_STUB=True",
        "-C", "Logger.Logs.BOOT=True",
        "-C", "Logger.Logs.CORE=True",
        "-C", "Dolphin.Interface.UsePanicHandlers=False",
        "-C", "Dolphin.Interface.ConfirmStop=False",
    ]

    process: subprocess.Popen[bytes] | None = None
    sock: socket.socket | None = None
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
                raise TimeoutError(f"Could not connect to Dolphin GDB port: {last_error}")

            rsp = RSPClient(sock)
            supported = rsp.command("qSupported:multiprocess+;swbreak+;hwbreak+")
            print(f"GDB qSupported: {supported}", flush=True)

            rsp.continue_execution()
            time.sleep(args.run_seconds)
            stop_reply = rsp.interrupt()
            print(f"GDB stop reply: {stop_reply}", flush=True)

            pc_match = re.search(r"(?:^|;)40:([0-9a-fA-F]{8})(?:;|$)", stop_reply)
            pc = int(pc_match.group(1), 16) if pc_match else None
            if pc is not None:
                print(f"PowerPC PC at interrupt: 0x{pc:08x}", flush=True)

            stage = read_memory(rsp, symbols["g_probe_stage"], 4).decode("ascii", "replace")
            print(f"Probe stage: {stage}", flush=True)

            if stage == "FAIL":
                code_data = read_memory(rsp, symbols["g_probe_failure_code"], 4)
                label_data = read_memory(rsp, symbols["g_probe_failure_label"], 24)
                code = int.from_bytes(code_data, "big")
                label = label_data.split(b"\0", 1)[0].decode("ascii", "replace")
                print(f"Probe failure code: {code}", flush=True)
                print(f"Probe failure label: {label}", flush=True)
                return 1
            if stage != "PASS":
                raise RuntimeError(
                    f"DOL did not reach PASS (stage={stage!r}, PC={pc!r}); "
                    "the memory operations are not validated"
                )

            print("RECOMP_PPC_MEMORY_PROBE:PASS (Dolphin GDB stage marker)", flush=True)
            return 0
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
        print(f"ERROR: {error}", file=sys.stderr, flush=True)
        raise SystemExit(1)
