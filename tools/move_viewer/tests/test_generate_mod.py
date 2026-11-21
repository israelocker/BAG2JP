"""Exercise generation through the viewer's public entry point."""
from pathlib import Path
import hashlib
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from tools.move_viewer import app, package_plan, reservations, swap_mod


class GenerateModTest(unittest.TestCase):
    def test_real_inventory_and_plan_reject_other_package_header(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            bank = root / 'strike/motion/bank.bin'
            bank.parent.mkdir(parents=True)
            bank.write_bytes(b'bank')
            existing = root / 'f2/pkg/other-id/1.0.0'
            existing.mkdir(parents=True)
            installed = root / 'install/mods/installed'
            installed.mkdir(parents=True)
            payload = b'old header'
            (existing / 'data.bin').write_bytes(payload)
            manifest = ('[[target]]\ngame_id="SLPM-86219"\n'
                        '[[overlay]]\ntarget="disc_user"\noffset=367472\n'
                        'file="data.bin"\nsha256="' + hashlib.sha256(payload).hexdigest() + '"\n')
            (existing / 'manifest.toml').write_text(manifest, encoding='utf-8')
            with (patch.object(app, 'load_config', return_value={}),
                  patch.object(app, 'require_paths', side_effect=[
                      (root / 'disc', root), (root / 'install',)]),
                  patch.object(app, 'assert_write_target', side_effect=lambda c, p, **k: p),
                  patch.object(swap_mod, 'check_disc'),
                  patch.object(swap_mod, 'find_entries', return_value=[109]),
                  patch.object(swap_mod, 'copy_growth', return_value=0),
                  patch.object(swap_mod, 'build', return_value=[
                      (10000, b'old', b'new'), (367472, b'12345678', b'abcdefgh')]),
                  patch.object(swap_mod, 'write_package') as write):
                with self.assertRaisesRegex(ValueError, 'reserved span'):
                    app.generate_mod(bank, [(0, 1)])
                write.assert_not_called()
                self.assertEqual((existing / 'manifest.toml').read_text(encoding='utf-8'), manifest)

    def test_inventory_failure_prevents_planning_and_writing(self):
        for failure in (ValueError('invalid manifest'), FileNotFoundError('missing root')):
            with self.subTest(failure=type(failure).__name__), TemporaryDirectory() as temp:
                root = Path(temp)
                bank = root / 'strike' / 'motion' / 'bank.bin'
                bank.parent.mkdir(parents=True)
                bank.write_bytes(b'bank')
                with (patch.object(app, 'load_config', return_value={}),
                      patch.object(app, 'require_paths', side_effect=[
                          (root / 'disc', root), (root / 'install',)]),
                      patch.object(app, 'assert_write_target', side_effect=lambda c, p, **k: p),
                      patch.object(swap_mod, 'check_disc'),
                      patch.object(swap_mod, 'find_entries', return_value=[109]),
                      patch.object(swap_mod, 'copy_growth', return_value=0),
                      patch.object(reservations, 'inventory', side_effect=failure),
                      patch.object(package_plan, 'plan') as plan,
                      patch.object(swap_mod, 'write_package') as write):
                    with self.assertRaises(type(failure)):
                        app.generate_mod(bank, [(0, 1)])
                    plan.assert_not_called()
                    write.assert_not_called()

    def test_success_writes_only_planned_overlays_with_safe_default_policy(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            bank = root / 'strike' / 'motion' / 'bank.bin'
            bank.parent.mkdir(parents=True)
            bank.write_bytes(b'bank')
            overlays = [(10000, b'old', b'new')]
            with (patch.object(app, 'load_config', return_value={}),
                  patch.object(app, 'require_paths', side_effect=[
                      (root / 'disc', root), (root / 'install',)]),
                  patch.object(app, 'assert_write_target', side_effect=lambda c, p, **k: p),
                  patch.object(swap_mod, 'check_disc'),
                  patch.object(swap_mod, 'find_entries', return_value=[109]),
                  patch.object(swap_mod, 'copy_growth', return_value=0),
                  patch.object(reservations, 'inventory', return_value=((200, 300),)) as inventory,
                  patch.object(package_plan, 'plan', return_value=overlays) as plan,
                  patch.object(swap_mod, 'write_package') as write):
                result = app.generate_mod(bank, [(0, 1)])
                inventory.assert_called_once_with((root / 'f2/pkg', root / 'install/mods/installed'))
                plan.assert_called_once_with(root / 'disc', [109], [(0, 1)],
                                             ((200, 300),), max_growth=0, cross=None,
                                             relocation_blocked=plan.call_args.kwargs['relocation_blocked'])
                blocked = plan.call_args.kwargs['relocation_blocked']
                self.assertEqual(len(blocked), 30)
                self.assertTrue({109, 110} <= blocked)
                write.assert_called_once()
                self.assertEqual(write.call_args.args[-1], overlays)
                self.assertIn('desactivado', result)

    def test_existing_package_is_preserved(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            bank = root / 'strike' / 'motion' / 'bank.bin'
            bank.parent.mkdir(parents=True)
            bank.write_bytes(b'bank')
            out = root / 'f2/pkg/bag2jp.test.move-assign-strike/1.0.0'
            out.mkdir(parents=True)
            marker = out / 'manifest.toml'
            marker.write_bytes(b'preserve me')
            with (patch.object(app, 'load_config', return_value={}),
                  patch.object(app, 'require_paths', side_effect=[
                      (root / 'disc', root), (root / 'install',)]),
                  patch.object(app, 'assert_write_target', side_effect=lambda c, p, **k: p),
                  patch.object(swap_mod, 'check_disc'),
                  patch.object(swap_mod, 'find_entries', return_value=[109]),
                  patch.object(swap_mod, 'copy_growth', return_value=0),
                  patch.object(reservations, 'inventory', return_value=()),
                  patch.object(package_plan, 'plan', return_value=[]),
                  patch.object(swap_mod, 'write_package') as write):
                with self.assertRaisesRegex(ValueError, 'already exists'):
                    app.generate_mod(bank, [(0, 1)])
                write.assert_not_called()
                self.assertEqual(marker.read_bytes(), b'preserve me')

    def test_reserved_collision_never_writes_package(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            bank = root / 'strike' / 'motion' / 'bank.bin'
            bank.parent.mkdir(parents=True)
            bank.write_bytes(b'bank')
            with (patch.object(app, 'load_config', return_value={}),
                  patch.object(app, 'require_paths', side_effect=[
                      (root / 'disc', root), (root / 'install',)]),
                  patch.object(app, 'assert_write_target', side_effect=lambda c, p, **k: p),
                  patch.object(swap_mod, 'check_disc'),
                  patch.object(swap_mod, 'find_entries', return_value=[109]),
                  patch.object(swap_mod, 'copy_growth', return_value=0),
                  patch.object(swap_mod, 'generate'),
                  patch.object(reservations, 'inventory', return_value=((100, 200),)),
                  patch.object(package_plan, 'plan', side_effect=ValueError('reserved')),
                  patch.object(swap_mod, 'write_package') as write):
                with self.assertRaisesRegex(ValueError, 'reserved'):
                    app.generate_mod(bank, [(0, 1)])
                write.assert_not_called()
