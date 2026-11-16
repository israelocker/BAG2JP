"""Heat test-mod launcher planning on owned trees; never runs WSL, conversion or make-mod."""
import json
from pathlib import Path
import re
import sys
import subprocess
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/bag1import'))

from tools.workflow import project_config as pc
from tools.workflow.test_project_config import ConfigFixture
import heat_test_launch as launch

SCRIPTS = {'character': ROOT / 'tools/bag1import/build_heat_test.sh',
           'stage': ROOT / 'tools/bag1import/build_heat_stage_test.sh'}


class HeatLaunchTests(ConfigFixture):
    def setUp(self):
        super().setUp()
        for name in ('members ñ', 'usa & disc', 'assets/archive', 'tools x', 'stable', 'exp'):
            (self.root / name).mkdir(parents=True)
        (self.root / 'game.cue').write_text('cue', encoding='utf-8')
        self.member_names = ('PLAYER2_P_HEATA2/001.bin', 'PLAYER2_P_HEATA2/000.bin',
                             'PLAYER2_P_HEATB2/000.bin', 'PLAYER4_P_HEATA4/000.bin',
                             'PLAYER4_P_HEATB4/000.bin', 'PLAYER1E_P_HEATA1/007.sedt',
                             'PLAYER1E_P_HEATA1/004.tim', 'PLAYER1E_P_HEATA1/005.tim',
                             'PLAYER1E_P_HEATA1/006.tim', 'PLAYER3E_P_HEATA3/004.tim')
        for name in self.member_names:
            path = self.root / 'members ñ' / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'owned member fixture; never converted')
        (self.root / 'usa & disc/STAGEE').mkdir()
        (self.root / 'usa & disc/STAGEE/ST_HEAT.DFS').write_bytes(b'owned DFS fixture')
        (self.root / 'usa & disc/SCUS_942.63').write_bytes(b'PS-X EXE' + bytes(0x800))
        self.write_local(self.overlay())

    def overlay(self, **changes):
        values = {'inputs.heat_bag1_members': 'members ñ', 'inputs.bag1_usa_extraction': 'usa & disc',
                  'paths.heat_test_workspace': '_work/heat char', 'paths.heat_stage_workspace': '_work/heat stage',
                  'paths.stable_install': 'stable', 'paths.experimental_install': 'exp'}
        values.update(changes)
        sections = {}
        for key, value in values.items():
            if value is not None:
                section, name = key.split('.')
                sections.setdefault(section, []).append(f'{name} = {json.dumps(value)}')
        return ''.join(f'[{s}]\n' + '\n'.join(rows) + '\n' for s, rows in sections.items())

    def package_overlay(self, **changes):
        text = self.overlay(**changes)
        return text.replace('[inputs]\n', '[inputs]\nbag2_cue = "game.cue"\n') + \
            '[tools]\npsx_asset_tools = "tools x"\n'

    def wsl(self, relative):
        return pc.to_wsl_path(self.root / relative)

    def env(self, argv):
        start, end = argv.index('env') + 1, argv.index('bash')
        return dict(item.split('=', 1) for item in argv[start:end])

    def valid_plan(self, *args, **kwargs):
        try:
            return launch.plan(*args, **kwargs)
        except pc.ConfigError as error:
            self.fail(f'valid host fixture rejected during planning: {error}')

    def valid_main(self, *args, **kwargs):
        try:
            return launch.main(*args, **kwargs)
        except (pc.ConfigError, SystemExit) as error:
            self.fail(f'valid host fixture rejected by CLI: {error}')

    def test_character_plan_passes_only_resolved_locations_to_wsl(self):
        plan = self.valid_plan('character', self.load())
        argv = plan['prepare']
        self.assertEqual(argv[:5], ['wsl.exe', '-d', 'Ubuntu', '--exec', 'env'])
        self.assertEqual(argv[-1], pc.to_wsl_path(SCRIPTS['character']))
        self.assertEqual(self.env(argv), {'BAG2JP_REPO': self.wsl('.'), 'BAG2JP_SOURCE': self.wsl('members ñ'),
                                          'BAG2JP_WORKSPACE': self.wsl('_work/heat char')})
        self.assertIsNone(plan['package'])

    def test_stage_plan_reuses_usa_extraction_and_classifies_part_selectors(self):
        plan = self.valid_plan('stage', self.load(), omit=('camera', 'sound'))
        env = self.env(plan['prepare'])
        self.assertEqual(env['BAG2JP_SOURCE'], self.wsl('usa & disc'))
        self.assertEqual(env['BAG2JP_WORKSPACE'], self.wsl('_work/heat stage'))
        self.assertEqual({k: v for k, v in env.items() if k.startswith('STAGE_')},
                         {'STAGE_MODEL': '1', 'STAGE_TEX': '1', 'STAGE_CAMERA': '0', 'STAGE_SOUND': '0'})
        self.assertEqual(plan['prepare'][-1], pc.to_wsl_path(SCRIPTS['stage']))

    def test_part_selectors_are_stage_only_and_closed(self):
        with self.assertRaises(pc.ConfigError):
            launch.plan('character', self.load(), omit=('model',))
        with self.assertRaises(pc.ConfigError):
            launch.plan('stage', self.load(), omit=('audio',))
        with self.assertRaises(pc.ConfigError):
            launch.plan('other', self.load())

    def test_missing_or_absent_source_fails_without_fallback(self):
        self.write_local(self.overlay(**{'inputs.heat_bag1_members': None}))
        with self.assertRaisesRegex(pc.ConfigError, 'heat_bag1_members'):
            launch.plan('character', self.load())
        self.write_local(self.overlay(**{'inputs.bag1_usa_extraction': 'absent'}))
        with self.assertRaisesRegex(pc.ConfigError, 'is not a directory:.*absent'):
            launch.plan('stage', self.load())

    def test_prepare_operation_requires_its_whole_contract(self):
        # The stable install is never read by the scripts; only the operation guards it.
        self.write_local(self.overlay(**{'paths.stable_install': None}))
        for target in ('character', 'stage'):
            with self.subTest(target=target), self.assertRaisesRegex(
                    pc.ConfigError, f'heat-{target}-prepare: unresolved.*paths.stable_install'):
                launch.plan(target, self.load())

    def test_linked_archive_or_workspace_is_rejected_before_runner(self):
        # Real directory junctions on Windows need no symlink privilege.
        workspace = self.root / '_work/heat char'
        workspace.mkdir(parents=True)
        sentinel = self.root / 'stable/sentinel'
        sentinel.write_bytes(b'untouched')
        for parent, target in ((self.root / 'assets/archive', self.root / 'stable'),
                               (workspace, self.root / 'stable'),
                               (workspace, self.root / 'missing-link-target')):
            link = parent / 'linked-output'
            result = subprocess.run(['cmd.exe', '/c', 'mklink', '/J', str(link),
                                     str(target)], capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr.decode(errors='replace'))
            try:
                runner = MagicMock()
                with patch('sys.stdout'), self.assertRaises(SystemExit) as error:
                    launch.main(['character', '--run', '--local-config', str(self.local)],
                                runner=runner, repo_root=self.root)
                self.assertEqual(error.exception.code, 2)
                runner.assert_not_called()
                self.assertEqual(sentinel.read_bytes(), b'untouched')
            finally:
                link.rmdir()  # remove the owned junction, not its target

    def test_missing_direct_inputs_fail_before_runner_and_preserve_workspace(self):
        cases = [('character', self.root / 'members ñ' / name) for name in self.member_names]
        cases += [('stage', self.root / 'usa & disc' / name)
                  for name in ('STAGEE/ST_HEAT.DFS', 'SCUS_942.63')]
        for target, source in cases:
            with self.subTest(target=target, source=source.name):
                workspace = self.root / ('_work/heat char' if target == 'character' else '_work/heat stage')
                workspace.mkdir(parents=True, exist_ok=True)
                sentinel = workspace / 'sentinel'
                sentinel.write_bytes(b'prior workspace')
                raw = source.read_bytes()
                source.unlink()
                runner = MagicMock()
                try:
                    with patch('sys.stdout'), self.assertRaises(SystemExit) as error:
                        launch.main([target, '--run', '--local-config', str(self.local)],
                                    runner=runner, repo_root=self.root)
                    self.assertEqual(error.exception.code, 2)
                    runner.assert_not_called()
                    self.assertEqual(sentinel.read_bytes(), b'prior workspace')
                finally:
                    source.write_bytes(raw)

    def test_stage_executable_header_is_checked_before_runner(self):
        executable = self.root / 'usa & disc/SCUS_942.63'
        for raw in (b'not an executable' + bytes(0x800), b'PS-X EXE', b'PS-X EXE' + bytes(0x7f8)):
            with self.subTest(size=len(raw)):
                executable.write_bytes(raw)
                runner = MagicMock()
                with patch('sys.stdout'), self.assertRaises(SystemExit) as error:
                    launch.main(['stage', '--run', '--local-config', str(self.local)],
                                runner=runner, repo_root=self.root)
                self.assertEqual(error.exception.code, 2)
                runner.assert_not_called()

    def test_workspace_must_stay_in_work_root_and_off_protected_trees(self):
        cases = {'outside work root': {'paths.heat_test_workspace': 'exp/ws'},
                 'stable overlap': {'paths.heat_test_workspace': '_work', 'paths.stable_install': '_work/stable'},
                 'inside source': {'inputs.heat_bag1_members': '_work/src', 'paths.heat_test_workspace': '_work/src/ws'},
                 'contains source': {'inputs.heat_bag1_members': '_work/ws/src', 'paths.heat_test_workspace': '_work/ws'},
                 'experimental overlap': {'paths.experimental_install': '_work/exp',
                                          'paths.heat_test_workspace': '_work/exp/ws'}}
        for label, change in cases.items():
            for path in change.values():
                (self.root / path).mkdir(parents=True, exist_ok=True)
            with self.subTest(label):
                self.write_local(self.overlay(**change))
                with self.assertRaises(pc.ConfigError):
                    launch.plan('character', self.load())

    def test_workspace_cannot_overlap_the_copied_archive(self):
        self.common.write_text(self.common.read_text(encoding='utf-8').replace(
            'work_root = "_work"', 'work_root = "."'), encoding='utf-8')
        self.write_local(self.overlay(**{'paths.heat_test_workspace': 'ws'}))
        self.assertEqual(self.valid_plan('character', self.load())['target'], 'character')
        for workspace in ('assets', 'assets/archive/x', 'config/ws'):
            with self.subTest(workspace):
                self.write_local(self.overlay(**{'paths.heat_test_workspace': workspace}))
                with self.assertRaises(pc.ConfigError):
                    launch.plan('character', self.load())

    def test_package_is_separate_explicit_and_targets_experimental_mods(self):
        with self.assertRaisesRegex(pc.ConfigError, 'psx_asset_tools|bag2_cue'):
            launch.plan('stage', self.load(), package=True)
        self.write_local(self.package_overlay())
        argv = self.valid_plan('stage', self.load(), package=True)['package']
        self.assertEqual(argv[:6], ['wsl.exe', '-d', 'Ubuntu', '--cd', self.wsl('tools x'), '--exec'])
        self.assertEqual(argv[6:12], ['python3', '-m', 'psxassets', 'make-mod', self.wsl('game.cue'),
                                      self.wsl('_work/heat stage')])
        self.assertEqual(argv[12], self.wsl('exp/mods/installed'))
        self.assertEqual(argv[argv.index('--id') + 1], 'bag2jp.test.bag1-heat-stage')
        character = self.valid_plan('character', self.load(), package=True)['package']
        self.assertEqual(character[character.index('--id') + 1], 'bag2jp.test.bag1-heat-model')

    def test_package_rejects_absent_tools_or_cue(self):
        for change in ({'tools': 'absent tools'}, {'cue': 'absent.cue'}):
            with self.subTest(change):
                text = self.package_overlay()
                if 'tools' in change:
                    text = text.replace('"tools x"', json.dumps(change['tools']))
                else:
                    text = text.replace('"game.cue"', json.dumps(change['cue']))
                self.write_local(text)
                with self.assertRaises(pc.ConfigError):
                    launch.plan('character', self.load(), package=True)

    def test_main_prints_plan_without_running_by_default(self):
        runner = MagicMock()
        with patch('sys.stdout') as out:
            code = self.valid_main(['character', '--local-config', str(self.local)], runner=runner,
                               repo_root=self.root)
        self.assertEqual(code, 0)
        runner.assert_not_called()
        printed = ''.join(call.args[0] for call in out.write.call_args_list)
        self.assertEqual(json.loads(printed)['prepare'][-1], pc.to_wsl_path(SCRIPTS['character']))

    def test_run_validates_everything_before_executing_then_runs_in_order(self):
        runner = MagicMock()
        with self.assertRaises(SystemExit) as error:
            launch.main(['stage', '--run', '--package', '--local-config', str(self.local)],
                        runner=runner, repo_root=self.root)
        self.assertEqual(error.exception.code, 2)
        runner.assert_not_called()
        self.write_local(self.package_overlay())
        with patch('sys.stdout'):
            self.valid_main(['stage', '--run', '--package', '--local-config', str(self.local)],
                        runner=runner, repo_root=self.root)
        self.assertEqual([c.args[0][-1] == pc.to_wsl_path(SCRIPTS['stage']) for c in runner.call_args_list],
                         [True, False])
        self.assertIn('make-mod', runner.call_args_list[1].args[0])
        self.assertTrue(all(c.kwargs.get('check') is True for c in runner.call_args_list))

    def test_package_requires_run(self):
        # A complete package overlay: only the --run requirement may reject this call.
        self.write_local(self.package_overlay())
        runner = MagicMock()
        with patch('sys.stdout'), self.assertRaises(SystemExit) as error:
            launch.main(['stage', '--package', '--local-config', str(self.local)],
                        runner=runner, repo_root=self.root)
        self.assertEqual(error.exception.code, 2)
        runner.assert_not_called()

    def test_failed_prepare_stops_before_package(self):
        self.write_local(self.package_overlay())
        runner = MagicMock(side_effect=launch.subprocess.CalledProcessError(1, 'wsl.exe'))
        with patch('sys.stdout'), self.assertRaises(launch.subprocess.CalledProcessError):
            self.valid_main(['character', '--run', '--package', '--local-config', str(self.local)],
                        runner=runner, repo_root=self.root)
        self.assertEqual(runner.call_count, 1)

    def test_config_is_loaded_once_per_invocation(self):
        with patch.object(launch, 'load_config', wraps=launch.load_config) as loader, patch('sys.stdout'):
            self.valid_main(['stage', '--local-config', str(self.local)], runner=MagicMock(), repo_root=self.root)
        self.assertEqual(loader.call_count, 1)


class HeatScriptContractTests(ConfigFixture):
    def test_workspace_commands_and_native_transforms_remain_explicit(self):
        for target, script in SCRIPTS.items():
            text = script.read_text(encoding='utf-8')
            with self.subTest(target=target):
                self.assertIn('rm -rf "$W/archive"; mkdir -p "$W"; cp -r "$P/assets/archive" "$W/"', text)
                self.assertIn('export T S ' + ('A B' if target == 'character' else 'SCUS A B'), text)
        character = SCRIPTS['character'].read_text(encoding='utf-8')
        self.assertIn('t.paste_rect(out, b2, 54, 165, 124, 177)', character)
        self.assertEqual(character.count(' --cue 1007'), 2)
        self.assertEqual(character.count(' 1000 6000'), 2)
        self.assertIn("open(f'{A}/pack_{o}_{side}/{slot}.tim', 'wb').write(out)", character)
        stage = SCRIPTS['stage'].read_text(encoding='utf-8')
        for line in ('m.convert(es[8], scale=(3, 2))',
                     "struct.pack_into('<H', cue, 4, 0x5000)",
                     "open(f'{A}/000.dbi', 'wb').write(d)",
                     "open(f'{A}/001.sedt', 'wb').write(out)",
                     "open(f'{A}/011.bin', 'wb').write(out)"):
            self.assertIn(line, stage)

    def test_scripts_take_required_locations_and_never_package(self):
        for target, script in SCRIPTS.items():
            text = script.read_text(encoding='utf-8')
            with self.subTest(target):
                self.assertIn('set -euo pipefail', text)
                for name in ('BAG2JP_REPO', 'BAG2JP_SOURCE', 'BAG2JP_WORKSPACE'):
                    self.assertRegex(text, r'\$\{' + name + r':\?')
                for legacy in ('~/mnt', '~/work', '$HOME', 'make-mod', 'psx-asset-tools', '/mnt/'):
                    self.assertNotIn(legacy, text)
                self.assertNotIn("<<PY", text, 'heredoc must be quoted; paths reach Python through os.environ')
                self.assertNotRegex(text, r"'\$[A-Z]", 'no shell interpolation inside Python source')
                self.assertNotRegex(text, r'(?<!")\$[A-Z]\b(?!")', 'unquoted shell location variable')

    def test_stage_script_reads_executable_from_extraction_with_header_check(self):
        text = SCRIPTS['stage'].read_text(encoding='utf-8')
        self.assertIn('STAGEE/ST_HEAT.DFS', text)
        self.assertIn('SCUS_942.63', text)
        self.assertIn("b'PS-X EXE'", text)
        self.assertIn('[0x800:]', text)
        self.assertNotIn('scus.bin', text)
        for name in ('STAGE_MODEL', 'STAGE_TEX', 'STAGE_CAMERA', 'STAGE_SOUND'):
            self.assertRegex(text, r"os\.environ\['" + name + r"'\]")
