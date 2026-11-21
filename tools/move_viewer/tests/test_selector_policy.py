"""Selector authority must be parsed completely, never partially trusted."""
import unittest
from pathlib import Path

from tools.move_viewer import selector_policy


class SelectorPolicyTest(unittest.TestCase):
    def test_canonical_native_authority_protects_both_sides(self):
        root = Path(__file__).resolve().parents[3]
        header = root / 'mods-src/bag2jp.feature.bag1-content/bag2jp_bag1_alt_index.h'
        entries = selector_policy.blocked_entries(header.read_text(encoding='utf-8'))
        self.assertEqual(len(entries), 30)
        self.assertTrue({89, 90, 95, 96, 109, 110, 161, 162, 167, 168, 181, 182} <= entries)

    def test_reads_entries_and_rejects_unrecognized_rows(self):
        source = 'static const B1AltEntry b1_alt_entries[] = {\n{109, 1, 0, 1u, 2u, 3u, 4u, 5u, 6u},\n};'
        self.assertEqual(selector_policy.blocked_entries(source), frozenset({109}))
        stale = '/* ' + source.replace('109,', '7,') + ' */\n// ' + source.replace('\n', ' ') + '\n'
        two = source.replace('};', '{110, 1, 0, 1u, 2u, 3u, 4u, 5u, 6u},\n};')
        self.assertEqual(selector_policy.blocked_entries(stale + two), frozenset({109, 110}))
        for invalid in ('', source.replace('109,', 'oops,'),
                        source.replace('};', '{110, broken},\n};'),
                        source.replace('};', '{109, 1, 0, 1u, 2u, 3u, 4u, 5u, 6u},\n};'),
                        'static const B1AltEntry b1_alt_entries[] = {};',
                        source.replace('},\n};', '}\n{110, 1, 0, 1u, 2u, 3u, 4u, 5u, 6u},\n};'),
                        source + '\n' + source.replace('109,', '110,')):
            with self.subTest(source=invalid), self.assertRaises(ValueError):
                selector_policy.blocked_entries(invalid)
