"""Coverage contract for the bounded Strike acceptance batch."""
from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

from tools.test import strike_acceptance_batch as batch_runner
from tools.test.strike_acceptance_batch import CASES, validate_cases, batch_status

sys.path.insert(0, str(Path(__file__).resolve().parent))  # the batch imports the session driver by name
import versus_session
from versus_settings_fixture import LOCAL, build_config, make_settings, relocated_root


class BatchCoverageTests(unittest.TestCase):
    def test_last_failure_or_unrestored_case_cannot_pass_batch(self):
        results = [dict(status='machine_complete_awaiting_review',
                        restoration={'verified': True}) for _ in CASES]
        self.assertEqual(batch_status(results), 'finished_awaiting_review')
        self.assertEqual(batch_status(results[:-1]), 'stopped_on_failure')
        results[-1]['status'] = 'failed'
        self.assertEqual(batch_status(results), 'stopped_on_failure')
        results[-1]['status'] = 'incomplete'
        self.assertEqual(batch_status(results), 'stopped_on_failure')
        results[-1]['status'] = 'machine_complete_awaiting_review'
        results[-1]['restoration']['verified'] = False
        self.assertEqual(batch_status(results), 'stopped_on_failure')

    def test_covers_both_sides_costumes_and_heat_stages(self):
        validate_cases(CASES)
        self.assertEqual({(c['side'], c['costume']) for c in CASES},
                         {(1, 'A'), (1, 'B'), (2, 'A'), (2, 'B')})
        self.assertEqual({c['stage'] for c in CASES}, {'HeatBAG1', 'HeatBAG2'})

    def test_rejects_missing_case_or_duplicate_label(self):
        with self.assertRaises(ValueError):
            validate_cases(CASES[:-1])
        with self.assertRaises(ValueError):
            validate_cases([CASES[0], CASES[0], *CASES[2:]])


class FakeFiles:
    restoration = {'verified': True}

    def __init__(self, game, folder, safe_to_restore):
        self.game = game

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class RecordingSession:
    """Stands in for the driver; records what the batch declared and the Popen in force at launch."""

    def __init__(self, run, settings, *, fixtures=None):
        self.run, self.settings, self.fixtures = run, settings, dict(fixtures or {})
        self.vram_dump_frames = ()
        self.process = None
        self.started = 0.0
        self.checkpoints, self.shots = {}, []
        self.popen_at_start = None

    def start(self):
        self.popen_at_start = subprocess.Popen
        self.debug_fixtures = dict(self.fixtures)

    def menu(self):
        pass

    def pick(self, side, character, version, costume, edges):
        return {'side': side}

    def match(self, stage, characters, costumes):
        pass

    def close(self):
        pass


class RunCaseTests(unittest.TestCase):
    def _run(self, case):
        settings = make_settings(self, versus_session)
        sessions = []

        def session_factory(*args, **kwargs):
            sessions.append(RecordingSession(*args, **kwargs))
            return sessions[-1]

        nav = SimpleNamespace(IsolatedFiles=FakeFiles, sha256=mock.Mock(return_value='h'),
                              validated_edges=mock.Mock(return_value={}), resolve_character=mock.Mock(return_value=0))
        vs = SimpleNamespace(Session=session_factory, save_result=mock.Mock(),
                             copy_current=versus_session.copy_current)
        original = subprocess.Popen
        with tempfile.TemporaryDirectory() as tmp, \
             mock.patch.object(batch_runner, 'observe_match', return_value={'attack_trace_frames': [1]}):
            result = batch_runner.run_case(case, Path(tmp) / case['name'], 'h', {}, nav, vs, settings)
        self.assertIs(subprocess.Popen, original)
        return result, sessions[0], settings, nav

    def test_fixture_is_declared_per_run_without_replacing_popen(self):
        for case, fixture in ((CASES[0], 'BAG2JP_TEST_STRIKE_ATTACK'), (CASES[1], 'BAG2JP_TEST_HEAT_STRIKE_DUEL')):
            with self.subTest(case=case['name']):
                result, session, settings, nav = self._run(case)
                self.assertEqual(result['status'], 'machine_complete_awaiting_review')
                self.assertIs(session.popen_at_start, subprocess.Popen)
                self.assertIs(session.settings, settings)
                self.assertEqual(session.fixtures, {fixture: '1'})
                self.assertEqual(result['fixture'], fixture)
                self.assertEqual(result['debug_fixtures'], {fixture: '1'})
                first = 8000 if case['stage'] == 'HeatBAG1' else 6500
                self.assertEqual(session.vram_dump_frames, tuple(range(first, first + 8 * 120, 120)))
                nav.sha256.assert_called_once_with(settings.game / 'BAG2JP.exe')

    def test_declared_fixtures_pass_the_driver_allowlist(self):
        settings = make_settings(self, versus_session)
        for fixture in ('BAG2JP_TEST_STRIKE_ATTACK', 'BAG2JP_TEST_HEAT_STRIKE_DUEL'):
            versus_session.Session(Path('unused'), settings, fixtures={fixture: '1'})

    def test_case_never_archives_evidence_from_an_earlier_session(self):
        settings = make_settings(self, versus_session)
        (settings.game / 'bag2jp_anim_trace.log').write_text('earlier run\n', encoding='utf-8')

        def session_factory(run, settings, *, fixtures=None):
            return RecordingSession(run, settings, fixtures=fixtures)  # never starts: started stays 0.0

        nav = SimpleNamespace(IsolatedFiles=FakeFiles, sha256=mock.Mock(return_value='h'),
                              validated_edges=mock.Mock(return_value={}),
                              resolve_character=mock.Mock(return_value=0))
        vs = SimpleNamespace(Session=session_factory, save_result=mock.Mock(),
                             copy_current=versus_session.copy_current)
        with tempfile.TemporaryDirectory() as tmp, \
             mock.patch.object(batch_runner, 'observe_match', return_value={'attack_trace_frames': [1]}):
            folder = Path(tmp) / 'case'
            batch_runner.run_case(CASES[0], folder, 'h', {}, nav, vs, settings)
            self.assertFalse((folder / 'bag2jp_anim_trace.log').exists())


class ObserveMatchTests(unittest.TestCase):
    def test_song_budget_is_the_resolved_finish_timeout(self):
        settings = make_settings(self, versus_session, LOCAL + '[harness]\nfinish_timeout_seconds = 5.0\n')
        session = SimpleNamespace(settings=settings,
                                  state=mock.Mock(side_effect=AssertionError('state polled after the resolved budget')))
        with mock.patch.object(batch_runner.time, 'monotonic', side_effect=[0.0, 6.0]), \
             self.assertRaises(TimeoutError):
            batch_runner.observe_match(session, CASES[0], SimpleNamespace())
        session.state.assert_not_called()


class MainTests(unittest.TestCase):
    def test_listing_cases_needs_no_configuration(self):
        with mock.patch.object(versus_session, 'load_config') as load, redirect_stdout(io.StringIO()):
            self.assertEqual(batch_runner.main([]), 0)
        load.assert_not_called()

    def test_config_error_exits_before_any_effect(self):
        stderr = io.StringIO()
        with mock.patch.object(versus_session, 'load_config',
                               side_effect=versus_session.project_config.ConfigError('bad local')), \
             mock.patch.object(versus_session, 'powershell') as shell, \
             mock.patch.object(Path, 'mkdir') as mkdir, \
             redirect_stderr(stderr), self.assertRaises(SystemExit) as raised:
            batch_runner.main(['--execute', '--local-config', 'custom.local.toml'])
        self.assertEqual(raised.exception.code, 2)
        self.assertIn('config error: bad local', stderr.getvalue())
        shell.assert_not_called()
        mkdir.assert_not_called()

    def _prepared(self):
        config = build_config(relocated_root(self), LOCAL + '[harness]\nhelper_timeout_seconds = 4.5\n')
        settings = versus_session.resolve_settings(config)
        settings.catalog.parent.mkdir(parents=True)
        settings.catalog.write_text('{}')
        return config, settings

    def test_batch_directory_is_guarded_before_mkdir(self):
        config, settings = self._prepared()
        real_guard = versus_session.project_config.assert_write_target

        def guard(configuration, target, *, role):
            if Path(target).name.endswith('-strike-acceptance-batch'):
                raise versus_session.project_config.ConfigError('refused batch')
            return real_guard(configuration, target, role=role)

        stderr = io.StringIO()
        with mock.patch.object(versus_session, 'load_config', return_value=config), \
             mock.patch.object(versus_session, 'powershell', return_value='0') as shell, \
             mock.patch.object(versus_session.nav, 'sha256', return_value='h') as digest, \
             mock.patch.object(versus_session.nav, 'validated_edges'), \
             mock.patch.object(versus_session.nav, 'verify_catalog_review'), \
             mock.patch.object(versus_session.project_config, 'assert_write_target', side_effect=guard) as checked, \
             mock.patch.object(Path, 'mkdir',
                               side_effect=AssertionError('batch directory created before its guard')) as mkdir, \
             redirect_stderr(stderr), self.assertRaises(SystemExit) as raised:
            batch_runner.main(['--execute'])
        self.assertEqual(raised.exception.code, 2)
        self.assertIn('refused batch', stderr.getvalue())
        mkdir.assert_not_called()
        self.assertEqual(shell.call_args.args[1], 4.5)
        digest.assert_called_once_with(settings.game / 'BAG2JP.exe')
        target = checked.call_args.args[1]
        self.assertEqual((target.parent, checked.call_args.kwargs['role']), (settings.runs, 'work'))

    def test_failed_case_stops_the_batch(self):
        config, settings = self._prepared()
        failed = dict(case=CASES[0], status='failed', restoration={'verified': True})
        with mock.patch.object(versus_session, 'load_config', return_value=config), \
             mock.patch.object(versus_session, 'powershell', return_value='0'), \
             mock.patch.object(versus_session.nav, 'sha256', return_value='h'), \
             mock.patch.object(versus_session.nav, 'validated_edges'), \
             mock.patch.object(versus_session.nav, 'verify_catalog_review'), \
             mock.patch.object(batch_runner, 'run_case', side_effect=[failed]) as run_case, \
             redirect_stdout(io.StringIO()):
            code = batch_runner.main(['--execute'])
        self.assertEqual(code, 1)
        self.assertEqual(run_case.call_count, 1)

    def test_unexpected_case_error_is_reported_instead_of_left_running(self):
        config, settings = self._prepared()
        with mock.patch.object(versus_session, 'load_config', return_value=config), \
             mock.patch.object(versus_session, 'powershell', return_value='0'), \
             mock.patch.object(versus_session.nav, 'sha256', return_value='h'), \
             mock.patch.object(versus_session.nav, 'validated_edges'), \
             mock.patch.object(versus_session.nav, 'verify_catalog_review'), \
             mock.patch.object(batch_runner, 'run_case', side_effect=KeyError('controller')), \
             redirect_stdout(io.StringIO()):
            code = batch_runner.main(['--execute'])
        batch_dir = next(settings.runs.glob('*-strike-acceptance-batch'))
        report = json.loads((batch_dir / 'batch.json').read_text(encoding='utf-8'))
        self.assertEqual(code, 1)
        self.assertEqual(report['status'], 'stopped_on_failure')
        self.assertEqual(report['cases'][0]['status'], 'failed')
        self.assertIn('controller', report['cases'][0]['error'])


if __name__ == '__main__':
    unittest.main()
