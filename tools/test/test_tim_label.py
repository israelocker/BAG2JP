"""4bpp label transfer regression: pixel order, bounds and collateral bytes."""
import struct
import unittest

from tools.bag1import import tim_retarget as tim


def texture(width: int, height: int, pixels: list[int]) -> bytes:
    """Build a small TIM independently of the production pixel encoder."""
    data = bytes(pixels[i] | pixels[i + 1] << 4 for i in range(0, len(pixels), 2))
    palette = struct.pack('<16H', *range(16))
    return tim.build(8, dict(x=0, y=480, w=16, h=1, data=palette),
                     dict(x=64, y=0, w=width // 4, h=height, data=data))


def unpack(data: bytes) -> list[int]:
    """Read the low pixel first, as the PS1 4bpp format requires."""
    return [value for byte in tim.parse(data)[2]['data'] for value in (byte & 15, byte >> 4)]


class TimLabelTest(unittest.TestCase):
    def setUp(self) -> None:
        self.source = texture(8, 4, [i % 16 for i in range(32)])
        self.target = texture(8, 4, [6] * 32)

    def test_odd_boundaries_keep_adjacent_nibbles(self) -> None:
        result = tim.paste_scaled_rect(self.target, self.source, (1, 0, 6, 1), (1, 1, 6, 2))
        expected = [6] * 32
        expected[9:14] = [1, 2, 3, 4, 5]
        self.assertEqual(unpack(result), expected)

    def test_transparent_pixels_replace_old_label(self) -> None:
        result = tim.paste_scaled_rect(self.target, self.source, (0, 0, 4, 1), (0, 0, 4, 1))
        self.assertEqual(unpack(result)[:4], [0, 1, 2, 3])

    def test_downscale_uses_pixel_centres(self) -> None:
        result = tim.paste_scaled_rect(self.target, self.source, (0, 0, 8, 4), (0, 0, 4, 2))
        self.assertEqual(unpack(result)[:4] + unpack(result)[8:12], [9, 11, 13, 15] * 2)

    def test_palette_and_vram_coordinates_are_unchanged(self) -> None:
        result = tim.paste_scaled_rect(self.target, self.source, (0, 0, 4, 2), (0, 0, 4, 2))
        before, after = tim.parse(self.target), tim.parse(result)
        self.assertEqual(before[:2], after[:2])
        self.assertEqual({k: v for k, v in before[2].items() if k != 'data'},
                         {k: v for k, v in after[2].items() if k != 'data'})

    def test_invalid_rectangles_fail_before_output(self) -> None:
        for rect in ((-1, 0, 2, 1), (0, 0, 9, 1), (0, 0, 2, 5),
                     (0, 0, 0, 1), (3, 0, 1, 1), (0, 0, 1, 0)):
            for source_rect, target_rect in ((rect, (0, 0, 4, 2)), ((0, 0, 4, 2), rect)):
                with self.subTest(source=source_rect, target=target_rect):
                    with self.assertRaises(ValueError):
                        tim.paste_scaled_rect(self.target, self.source, source_rect, target_rect)

    def test_non_4bpp_and_truncated_data_are_rejected(self) -> None:
        bad_mode = bytearray(self.source)
        struct.pack_into('<I', bad_mode, 4, 9)
        for invalid in (bytes(bad_mode), self.source[:-1], b''):
            with self.subTest(size=len(invalid)):
                with self.assertRaises(ValueError):
                    tim.paste_scaled_rect(self.target, invalid, (0, 0, 4, 2), (0, 0, 4, 2))

    def test_declared_chunk_lengths_must_match_dimensions_and_file(self) -> None:
        for chunk_offset in (8, 52):
            for extra in (-1, 1, 100):
                invalid = bytearray(self.source)
                length = struct.unpack_from('<I', invalid, chunk_offset)[0]
                struct.pack_into('<I', invalid, chunk_offset, length + extra)
                with self.subTest(chunk=chunk_offset, extra=extra):
                    with self.assertRaises(ValueError):
                        tim.paste_scaled_rect(self.target, bytes(invalid), (0, 0, 4, 2), (0, 0, 4, 2))

    def test_retarget_with_label_uses_source_art_and_reference_placement(self) -> None:
        result = tim.retarget_with_label(self.source, self.target, (0, 0, 4, 1), (1, 1, 5, 2))
        expected = unpack(self.source)
        expected[9:13] = [0, 1, 2, 3]
        self.assertEqual(unpack(result), expected)

    def test_palette_mapping_preserves_transparency_and_opaque_black(self) -> None:
        flags, clut, image = tim.parse(self.source)
        source_colours = [0, 0x7fff, 0] + [0x4210] * 13
        reference_colours = [0, 0x8000] + [0x8421] * 13 + [0xffff]
        source = tim.build(flags, dict(clut, data=struct.pack('<16H', *source_colours)), image)
        reference = tim.build(flags, dict(clut, data=struct.pack('<16H', *reference_colours)), image)
        self.assertEqual(tim.label_palette_map(source, reference)[:3], (0, 15, 1))
        result = tim.retarget_with_label(source, reference, (0, 0, 4, 1), (0, 1, 4, 2))
        self.assertEqual(unpack(result)[8:11], [0, 15, 1])

    def test_invalid_index_map_is_rejected(self) -> None:
        for invalid in ((0,), tuple(range(17)), (-1,) * 16, (16,) * 16, (False,) * 16):
            with self.subTest(mapping=invalid):
                with self.assertRaises(ValueError):
                    tim.paste_scaled_rect(self.target, self.source, (0, 0, 4, 1), (0, 0, 4, 1), invalid)


if __name__ == '__main__':
    unittest.main()
