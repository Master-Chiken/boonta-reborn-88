import struct
import unittest

from mdl0_header import FIXED_HEADER_SIZE_V11, MDL0HeaderError, validate_mdl0_v11


def synthetic_container():
    # Container at 0, MDL0 at 0x20, shared name pool at 0x80.
    mdl0_start = 0x20
    data = bytearray(0x90)
    data[0:4] = b"bres"
    data[mdl0_start:mdl0_start + 4] = b"MDL0"
    struct.pack_into(">IIi", data, mdl0_start + 4, 0x60, 11, -mdl0_start)
    struct.pack_into(">i", data, mdl0_start + 0x10, 0x4C)
    struct.pack_into(">i", data, mdl0_start + 0x48, 0x60)
    data[0x80:0x8A] = b"synthetic\0"
    return data, mdl0_start


class MDL0HeaderTests(unittest.TestCase):
    def valid(self):
        data, start = synthetic_container()
        header = validate_mdl0_v11(data, start, brres_start=0)
        self.assertEqual(header.version, 11)
        self.assertEqual(header.length, 0x60)
        self.assertEqual(header.brres_target, 0)
        self.assertEqual(header.section_offsets[0], 0x4C)
        self.assertEqual(header.name_target, 0x80)
        return data, start

    def test_valid_synthetic_header_and_negative_back_reference(self):
        self.valid()

    def test_detached_subfile_zero_back_reference(self):
        # An extracted MDL0 subfile begins at offset zero; the documented
        # signed back-reference is zero for this detached representation.
        data = bytearray(0x70)
        data[0:4] = b"MDL0"
        struct.pack_into(">IIi", data, 4, 0x60, 11, 0)
        struct.pack_into(">i", data, 0x10, 0x4C)
        struct.pack_into(">i", data, 0x48, 0x60)
        data[0x60:0x6A] = b"detached\\0"

        header = validate_mdl0_v11(data, 0, brres_start=0)
        self.assertEqual(header.brres_relative_offset, 0)
        self.assertEqual(header.brres_target, 0)
        self.assertEqual(header.start, 0)
        self.assertEqual(header.name_target, 0x60)

    def test_wrong_magic(self):
        data, start = self.valid()
        data[start:start + 4] = b"NOPE"
        with self.assertRaises(MDL0HeaderError):
            validate_mdl0_v11(data, start, 0)

    def test_unsupported_version(self):
        data, start = self.valid()
        struct.pack_into(">I", data, start + 8, 10)
        with self.assertRaises(MDL0HeaderError):
            validate_mdl0_v11(data, start, 0)

    def test_truncated_fixed_header(self):
        data, start = self.valid()
        with self.assertRaises(MDL0HeaderError):
            validate_mdl0_v11(data[:start + FIXED_HEADER_SIZE_V11 - 1], start, 0)

    def test_too_small_declared_length(self):
        data, start = self.valid()
        struct.pack_into(">I", data, start + 4, FIXED_HEADER_SIZE_V11 - 1)
        with self.assertRaises(MDL0HeaderError):
            validate_mdl0_v11(data, start, 0)

    def test_declared_length_beyond_buffer(self):
        data, start = self.valid()
        struct.pack_into(">I", data, start + 4, 0xFFFFFFFF)
        with self.assertRaises(MDL0HeaderError):
            validate_mdl0_v11(data, start, 0)

    def test_section_offsets_outside_subfile_are_rejected(self):
        for value in (-1, 0x60, 0x7FFFFFFF):
            data, start = self.valid()
            struct.pack_into(">i", data, start + 0x10, value)
            with self.subTest(value=value), self.assertRaises(MDL0HeaderError):
                validate_mdl0_v11(data, start, 0)

    def test_zero_optional_section_offsets_are_accepted(self):
        data, start = self.valid()
        data[start + 0x10:start + 0x48] = bytes(14 * 4)
        header = validate_mdl0_v11(data, start, 0)
        self.assertEqual(set(header.section_offsets), {0})

    def test_wrong_or_out_of_container_back_reference(self):
        data, start = self.valid()
        with self.assertRaises(MDL0HeaderError):
            validate_mdl0_v11(data, start, brres_start=4)
        struct.pack_into(">i", data, start + 0x0C, -0x7FFFFFFF)
        with self.assertRaises(MDL0HeaderError):
            validate_mdl0_v11(data, start)

    def test_name_offset_outside_buffer_and_unterminated_name(self):
        data, start = self.valid()
        struct.pack_into(">i", data, start + 0x48, 0x7FFFFFFF)
        with self.assertRaises(MDL0HeaderError):
            validate_mdl0_v11(data, start, 0)
        data, start = self.valid()
        data[0x80:] = b"x" * (len(data) - 0x80)
        with self.assertRaises(MDL0HeaderError):
            validate_mdl0_v11(data, start, 0)

    def test_32_bit_field_boundaries_and_determinism(self):
        data, start = self.valid()
        self.assertEqual(validate_mdl0_v11(data, start, 0),
                         validate_mdl0_v11(data, start, 0))
        struct.pack_into(">I", data, start + 4, 0xFFFFFFFF)
        with self.assertRaises(MDL0HeaderError):
            validate_mdl0_v11(data, start, 0)
        data, start = self.valid()
        struct.pack_into(">i", data, start + 0x0C, -0x80000000)
        with self.assertRaises(MDL0HeaderError):
            validate_mdl0_v11(data, start, 0)

    def test_malformed_inputs_never_leak_struct_errors(self):
        for data in (b"", b"MDL0", bytes(range(32)), bytearray(b"MDL0" * 40)):
            with self.assertRaises((MDL0HeaderError, TypeError)):
                validate_mdl0_v11(data, 0)


if __name__ == "__main__":
    unittest.main()
