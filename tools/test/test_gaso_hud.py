"""Regional Gas-O HUD label checks against the local disc extractions."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/bag1import'))

from build_gaso_assets import build_hud_texture, read_members, region_sources
from tim_retarget import parse, retarget, paste_native_glyphs


def indices(data: bytes) -> list[list[int]]:
    """Unpack each TIM row without using the production copier."""
    image = parse(data)[2]
    flat = [v for byte in image['data'] for v in (byte & 15, byte >> 4)]
    width = image['w'] * 4
    return [flat[i:i + width] for i in range(0, len(flat), width)]


class GasoHudTest(unittest.TestCase):
    def test_native_font_keeps_original_glyph_widths(self) -> None:
        profile = json.loads((ROOT / 'tools/bag1import/profiles/gaso.json').read_text(encoding='utf-8'))
        self.assertEqual(profile['hud_name']['target_rect'], [0, 0, 69, 7])

    def test_s_has_transparent_spacing_not_the_neighbouring_t(self) -> None:
        profile = json.loads((ROOT / 'tools/bag1import/profiles/gaso.json').read_text(encoding='utf-8'))
        data = (ROOT / 'assets/archive/characters/bi_o/pack_a_p1/003.tim').read_bytes()
        result = indices(build_hud_texture(data, data, profile['hud_name']))
        # G15 + A16 + S14: column45 is spacing, not STRIKE's next glyph at x70.
        self.assertEqual([row[45] for row in result[:7]], [0] * 7)

    def test_native_sprite_override_is_registered_at_verified_site(self) -> None:
        source = (ROOT / 'mods-src/bag2jp.feature.bag1-content/bag2jp_bag1_versions.c').read_text()
        self.assertIn('b1hud_sprite_hook);', source)
        self.assertIn('0x80093F6Cu, 0x3C0400FFu', source)

    def test_profile_matches_both_native_bio_hud_descriptors(self) -> None:
        profile = json.loads((ROOT / 'tools/bag1import/profiles/gaso.json').read_text(encoding='utf-8'))
        x0, y0, x1, y1 = profile['hud_name']['stock_rect']
        descriptor = bytes([x0, y0, x1 - x0, y1 - y0, 1, 0])
        overlay = (ROOT / 'assets/archive/system/005.dbi').read_bytes()
        self.assertEqual(descriptor, overlay[0xee52:0xee58])
        self.assertEqual(descriptor, overlay[0xeebe:0xeec4])

    def test_all_regional_costumes_preserve_every_pixel_outside_hud_slot(self) -> None:
        profile = json.loads((ROOT / 'tools/bag1import/profiles/gaso.json').read_text(encoding='utf-8'))
        reference, _ = read_members((ROOT / '_work/stage_import/gaso/stock_bio_entries/pack_a_p1.dfs').read_bytes())
        label = profile['hud_name']
        # Independently slice native raster indices, no copier/palette helper.
        expected = [[] for _ in range(7)]
        for path, rect, spacing in (
            ('hustle_kong/pack_a_p1/002.tim', (125, 56, 140, 63), 0),
            ('heat/pack_a_p1/003.tim', (87, 168, 103, 175), 0),
            ('strike/pack_a_p1/003.tim', (56, 80, 70, 87), 1),
            ('bi_o/pack_a_p1/003.tim', (54, 112, 61, 119), 0),
            ('bi_o/pack_a_p1/003.tim', (61, 112, 77, 119), 0),
        ):
            raster = indices((ROOT / 'assets/archive/characters' / path).read_bytes())
            for y in range(7):
                expected[y].extend(raster[rect[1] + y][rect[0]:rect[2]])
                expected[y].extend([0] * spacing)
        self.assertEqual({v for row in expected for v in row}, {0, 9, 10, 11, 12, 13, 14, 15})
        for region in ('usa', 'jp'):
            source_root, dirs, _ = region_sources(region)
            for costume, filename in (('costume_a', 'P_GAS_A1.DFS'), ('costume_a', 'P_GAS_B1.DFS'),
                                      ('costume_b', 'P_GAS_A3.DFS'), ('costume_b', 'P_GAS_B3.DFS')):
                with self.subTest(region=region, filename=filename):
                    members, _ = read_members((source_root / dirs[costume] / filename).read_bytes())
                    target_rect = tuple(label['target_rect'])
                    before = retarget(members[5], reference[3])
                    result = build_hud_texture(members[5], reference[3], label)
                    old, new = indices(before), indices(result)
                    x0, y0, x1, y1 = target_rect
                    changed = 0
                    for y, row in enumerate(new):
                        for x, value in enumerate(row):
                            if x0 <= x < x1 and y0 <= y < y1:
                                self.assertEqual(value, expected[y - y0][x - x0])
                                changed += value != old[y][x]
                            else:
                                self.assertEqual(value, old[y][x])
                    self.assertGreater(changed, 0)
                    self.assertEqual(parse(before)[:2], parse(result)[:2])
                    # Body palettes remain native; the label indices match BAG2's shared HUD CLUT.
                    self.assertEqual(parse(members[5])[1]['data'], parse(result)[1]['data'])

    def test_native_glyph_composer_rejects_resizing_and_invalid_rectangles(self) -> None:
        data = (ROOT / 'assets/archive/characters/heat/pack_a_p1/003.tim').read_bytes()
        for glyphs, target in (
            ([], (0, 0, 1, 7)),
            ([(data, (87, 168, 103, 175))], (0, 0, 15, 7)),
            ([(data, (87, 168, 103, 175))], (0, 0, 16, 8)),
            ([(data, (-1, 168, 103, 175))], (0, 0, 16, 7)),
        ):
            with self.subTest(target=target, glyphs=len(glyphs)), self.assertRaises(ValueError):
                paste_native_glyphs(data, glyphs, target)

    def test_native_spacing_rejects_wrong_count_negative_and_noninteger(self) -> None:
        data = (ROOT / 'assets/archive/characters/heat/pack_a_p1/003.tim').read_bytes()
        glyphs = [(data, (87, 168, 103, 175))]
        for spacing in ([], [-1], [True], [False], [1.5], [0.0], [0, 0]):
            with self.subTest(spacing=spacing), self.assertRaises(ValueError):
                paste_native_glyphs(data, glyphs, (0, 0, 16, 7), spacing)


if __name__ == '__main__':
    unittest.main()
