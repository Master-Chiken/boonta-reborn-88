#!/usr/bin/env python3
"""Host tests for the minimal Dolphin GDB Remote Serial Protocol client."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from dolphin_gdb_probe import RSPClient  # noqa: E402


class FakeSocket:
    def __init__(self, incoming: bytes = b"") -> None:
        self.incoming = bytearray(incoming)
        self.sent = bytearray()
        self.recv_calls = 0
        self.timeout = None

    def settimeout(self, timeout: float) -> None:
        self.timeout = timeout

    def sendall(self, data: bytes) -> None:
        self.sent.extend(data)

    def recv(self, size: int) -> bytes:
        self.recv_calls += 1
        if not self.incoming:
            return b""
        data = bytes(self.incoming[:size])
        del self.incoming[:size]
        return data


def packet(payload: bytes) -> bytes:
    checksum = sum(payload) & 0xFF
    return b"$" + payload + b"#" + f"{checksum:02x}".encode("ascii")


class RSPClientTests(unittest.TestCase):
    def test_continue_is_asynchronous_and_does_not_wait_for_ack(self) -> None:
        sock = FakeSocket()
        client = RSPClient(sock)

        client.continue_execution()

        self.assertEqual(bytes(sock.sent), packet(b"c"))
        self.assertEqual(sock.recv_calls, 0)

    def test_interrupt_reads_stop_packet_and_acknowledges_it(self) -> None:
        stop = packet(b"T05thread:1;")
        sock = FakeSocket(stop)
        client = RSPClient(sock)

        reply = client.interrupt()

        self.assertEqual(reply, "T05thread:1;")
        self.assertEqual(bytes(sock.sent), b"\x03+")

    def test_read_packet_skips_ack_before_stop_packet(self) -> None:
        stop = packet(b"T05thread:1;")
        sock = FakeSocket(b"+" + stop)
        client = RSPClient(sock)

        reply = client.read_packet()

        self.assertEqual(reply, "T05thread:1;")
        self.assertEqual(bytes(sock.sent), b"+")

    def test_read_ack_preserves_packet_without_separate_ack(self) -> None:
        stop = packet(b"T05thread:1;")
        sock = FakeSocket(stop)
        client = RSPClient(sock)

        client.read_ack()

        self.assertEqual(client.read_packet(), "T05thread:1;")
        self.assertEqual(bytes(sock.sent), b"+")


if __name__ == "__main__":
    unittest.main()
