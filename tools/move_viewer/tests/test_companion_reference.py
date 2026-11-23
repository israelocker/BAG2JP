"""Recorded references must never authorize unknown or modified asset sets."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.move_viewer import companion_reference as reference


class ReferenceTest(unittest.TestCase):
    def test_verified_assets_select_only_the_recorded_pair(self):
        with patch.object(reference, 'asset_digest', return_value=reference.REFERENCES['capoeira'][0]), \
             patch.object(reference, 'load_scene', return_value='scene'):
            scene, contexts, label = reference.load_reference(Path('.'), 'capoeira')
        self.assertEqual(scene, 'scene')
        self.assertEqual([c.slot for c in contexts], [66, 113])
        self.assertIn('gf12500', label)
        self.assertEqual(contexts[0].first_frame, 67)
        self.assertEqual(contexts[1].first_frame, 69)
        self.assertEqual(contexts[0].parent, (-648, 0, -193))
        self.assertEqual(contexts[1].parent, (-780, 0, -232))
        self.assertEqual([(c.second_frame, c.blend, c.scale) for c in contexts],
                         [(68, 2070, 74), (70, 3588, 74)])

    def test_chichi_reference_uses_verified_unblended_draw_context(self):
        with patch.object(reference, 'asset_digest', return_value=reference.REFERENCES['chichi_sally'][0]), \
             patch.object(reference, 'load_scene', return_value='scene'):
            _, contexts, label = reference.load_reference(Path('.'), 'chichi_sally')
        self.assertIn('gf12430', label)
        self.assertEqual([c.slot for c in contexts], [66, 113])
        self.assertEqual([c.first_frame for c in contexts], [156, 159])
        self.assertEqual([c.parent for c in contexts], [(-521, -88, 169), (-91, -136, -60)])
        self.assertEqual([(c.second_frame, c.blend, c.scale) for c in contexts],
                         [(157, 2145, 53), (160, 924, 60)])

    def test_assets_changed_during_load_are_rejected(self):
        expected = reference.REFERENCES['capoeira'][0]
        with patch.object(reference, 'asset_digest', side_effect=[expected, 'changed']), \
             patch.object(reference, 'load_scene', return_value='scene'):
            with self.assertRaisesRegex(ValueError, 'changed while loading'):
                reference.load_reference(Path('.'), 'capoeira')

    def test_modified_and_unknown_assets_are_denied_before_loading(self):
        with patch.object(reference, 'asset_digest', return_value='changed'), \
             patch.object(reference, 'load_scene') as load:
            with self.assertRaises(ValueError):
                reference.load_reference(Path('.'), 'capoeira')
            with self.assertRaises(ValueError):
                reference.load_reference(Path('.'), 'heat')
            load.assert_not_called()

    def test_digest_binds_companion_bank_and_texture_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            for directory, files in [('model_a_p1', ['000.bin','001.bin','002.bin']),
                                     ('pack_a_p1', ['000.dbi','001.tim'])]:
                (base / directory).mkdir()
                for name in files:
                    (base / directory / name).write_bytes(name.encode())
            initial = reference.asset_digest(base)
            (base / 'pack_a_p1/001.tim').write_bytes(b'changed')
            self.assertNotEqual(reference.asset_digest(base), initial)
            (base / 'pack_a_p1/001.tim').write_bytes(b'001.tim')
            (base / 'model_a_p1/001.bin').write_bytes(b'changed bank')
            self.assertNotEqual(reference.asset_digest(base), initial)
            (base / 'model_a_p1/001.bin').write_bytes(b'001.bin')
            (base / 'pack_a_p1/000.dbi').write_bytes(b'changed dbi')
            self.assertNotEqual(reference.asset_digest(base), initial)

    def test_recorded_digests_match_extracted_tree(self):
        from tools.move_viewer.app import ROOT, load_config, require_paths
        assets, = require_paths(load_config(repo_root=ROOT), ('inputs.bag2jp_assets',))
        tree = assets / 'archive/characters'
        for character, (expected, contexts, label) in reference.REFERENCES.items():
            with self.subTest(character=character):
                self.assertEqual(reference.asset_digest(tree / character), expected,
                                 f'constante obsoleta para {character}')
                self.assertEqual(len(contexts), 2, f'{character} debe tener dos contextos')
                self.assertIn('A/P1', label)
                self.assertTrue(all(c.slot >= 0 for c in contexts))
