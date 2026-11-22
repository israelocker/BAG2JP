"""Selector authority must be parsed completely, never partially trusted."""
import unittest
import unittest.mock
from pathlib import Path

from tools.move_viewer import selector_policy


class SelectorPolicyTest(unittest.TestCase):
    def test_recorded_phase23_build_is_explicitly_registered(self):
        self.assertIn(
            '1518964FC6ED69C48DE03B5EEEBDC92DCBBF676182E4D8D816D5E7DEEF394264',
            selector_policy.RELOCATION_AWARE_SHA256)

    def test_only_proven_exe_follows_relocation(self):
        import hashlib, tempfile
        with tempfile.TemporaryDirectory() as temp:
            exe = Path(temp) / 'BAG2JP.exe'
            self.assertFalse(selector_policy.exe_follows_relocation(exe))
            exe.write_bytes(b'unknown build')
            self.assertFalse(selector_policy.exe_follows_relocation(exe))
            digest = hashlib.sha256(b'unknown build').hexdigest().upper()
            with unittest.mock.patch.object(selector_policy, 'RELOCATION_AWARE_SHA256',
                                            frozenset({digest})):
                self.assertTrue(selector_policy.exe_follows_relocation(exe))

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
