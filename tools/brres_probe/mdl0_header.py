"""Synthetic-only validator for the fixed MDL0 v11 subfile prefix."""
from dataclasses import dataclass
import struct

MAGIC = b"MDL0"
SUPPORTED_VERSION = 11
SECTION_COUNT_V11 = 14
FIXED_HEADER_SIZE_V11 = 0x4C


class MDL0HeaderError(ValueError):
    """Raised when a synthetic MDL0 header violates checked bounds."""


@dataclass(frozen=True)
class MDL0Header:
    start: int
    length: int
    version: int
    brres_relative_offset: int
    brres_target: int
    section_offsets: tuple[int, ...]
    name_relative_offset: int
    name_target: int


def _need(data: bytes, start: int, size: int, what: str) -> None:
    if start < 0 or size < 0 or start > len(data) or size > len(data) - start:
        raise MDL0HeaderError(f"{what} is truncated or outside the supplied buffer")


def _i32(data: bytes, offset: int) -> int:
    return struct.unpack_from(">i", data, offset)[0]


def validate_mdl0_v11(data: bytes, mdl0_start: int, brres_start: int | None = None) -> MDL0Header:
    """Validate a fixed v11 prefix inside a synthetic containing byte buffer.

    All MDL0 header offsets are relative to mdl0_start. The signed BRRES
    back-reference is resolved against that start; negative values are valid
    when they point to the supplied outer BRRES location. Section offsets are
    either zero (absent) or point inside the declared MDL0 subfile. The name
    offset is resolved against the complete containing buffer because the
    string pool is shared by BRRES subfiles.
    """
    if not isinstance(data, (bytes, bytearray, memoryview)):
        raise MDL0HeaderError("data must be bytes-like")
    data = bytes(data)
    _need(data, mdl0_start, FIXED_HEADER_SIZE_V11, "fixed MDL0 v11 header")
    if data[mdl0_start:mdl0_start + 4] != MAGIC:
        raise MDL0HeaderError("wrong MDL0 magic")

    length, version = struct.unpack_from(">II", data, mdl0_start + 4)
    if version != SUPPORTED_VERSION:
        raise MDL0HeaderError(f"unsupported MDL0 version: {version}")
    if length < FIXED_HEADER_SIZE_V11:
        raise MDL0HeaderError("declared subfile length is smaller than the fixed v11 header")
    if length > len(data) - mdl0_start:
        raise MDL0HeaderError("declared subfile extends beyond the supplied buffer")

    brres_relative = _i32(data, mdl0_start + 0x0C)
    brres_target = mdl0_start + brres_relative
    if not 0 <= brres_target < len(data):
        raise MDL0HeaderError("BRRES back-reference resolves outside the supplied buffer")
    if brres_start is not None and brres_target != brres_start:
        raise MDL0HeaderError("BRRES back-reference does not resolve to the expected container")

    section_offsets = tuple(_i32(data, mdl0_start + 0x10 + i * 4)
                             for i in range(SECTION_COUNT_V11))
    for index, relative in enumerate(section_offsets):
        if relative == 0:
            continue
        if relative < FIXED_HEADER_SIZE_V11 or relative >= length:
            raise MDL0HeaderError(f"section offset {index} is outside the declared subfile")

    name_relative = _i32(data, mdl0_start + 0x48)
    name_target = mdl0_start + name_relative
    if not 0 <= name_target < len(data):
        raise MDL0HeaderError("name offset resolves outside the supplied buffer")
    if data.find(b"\0", name_target) < 0:
        raise MDL0HeaderError("name string is not NUL-terminated within the supplied buffer")

    return MDL0Header(
        start=mdl0_start,
        length=length,
        version=version,
        brres_relative_offset=brres_relative,
        brres_target=brres_target,
        section_offsets=section_offsets,
        name_relative_offset=name_relative,
        name_target=name_target,
    )
