"""Versus harness settings resolve once from project configuration, before any effect."""
from contextlib import redirect_stderr
import dataclasses
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))  # versus_session imports siblings by name
import versus_session
from versus_settings_fixture import LOCAL, build_config, make_settings, relocated_root

project_config = versus_session.project_config
RUN_ARGV = ["--action", "probe", "--temporary-controls", "--tag", "config-test"]


class ResolveSettingsTest(unittest.TestCase):
    def test_relocated_root_resolves_the_reviewed_defaults(self) -> None:
        root = relocated_root(self)
        settings = versus_session.resolve_settings(build_config(root))
        self.assertEqual(settings.game, root / "game")
        self.assertEqual(settings.winshot, root / "winshot")
        self.assertEqual(settings.runs, root / "_work/versus-runs")
        self.assertEqual(settings.catalog, root / "_work/versus-navigation/catalog.json")
        self.assertEqual((settings.state_timeout, settings.helper_timeout, settings.startup_timeout,
                          settings.finish_timeout), (25.0, 35.0, 40.0, 420.0))
        self.assertEqual((settings.key_hold_ms, settings.key_gap_ms, settings.menu_fade), (100, 350, 1.3))

    def test_working_directory_does_not_select_paths(self) -> None:
        root = relocated_root(self)
        config = build_config(root)
        before = versus_session.resolve_settings(config)
        previous = Path.cwd()
        with tempfile.TemporaryDirectory() as elsewhere:
            os.chdir(elsewhere)
            try:
                after = versus_session.resolve_settings(project_config.load_config(repo_root=root))
            finally:
                os.chdir(previous)
        self.assertEqual(dataclasses.replace(after, config=config), before)

    def test_local_budget_override_is_used_and_attributed(self) -> None:
        settings = make_settings(self, versus_session, LOCAL + "[harness]\nstate_timeout_seconds = 7.5\n")
        self.assertEqual(settings.state_timeout, 7.5)
        provenance = settings.provenance()
        self.assertEqual(provenance["values"]["harness.state_timeout_seconds"], 7.5)
        self.assertEqual(provenance["origins"]["harness.state_timeout_seconds"], "local")
        self.assertEqual(provenance["origins"]["harness.key_hold_ms"], "common")
        self.assertIn("local", provenance["input_hashes"])

    def test_locked_input_policy_rejects_local_override(self) -> None:
        for override in ("key_hold_ms = 50", "key_gap_ms = 200", "menu_fade_seconds = 0.5"):
            with self.subTest(override=override), self.assertRaises(project_config.ConfigError):
                build_config(relocated_root(self), LOCAL + f"[harness]\n{override}\n")

    def test_missing_winshot_root_fails_naming_the_key(self) -> None:
        local = 'schema_version = 1\n[paths]\nexperimental_install = "game"\nstable_install = "stable"\n'
        with self.assertRaisesRegex(project_config.ConfigError, "tools.winshot_root"):
            versus_session.resolve_settings(build_config(relocated_root(self), local))

    def test_stable_install_is_never_the_experimental_destination(self) -> None:
        local = LOCAL.replace('stable_install = "stable"', 'stable_install = "game"')
        with self.assertRaises(project_config.ConfigError):
            versus_session.resolve_settings(build_config(relocated_root(self), local))

    def test_settings_are_immutable(self) -> None:
        settings = make_settings(self, versus_session)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            settings.game = Path("elsewhere")

    def test_catalog_and_game_targets_are_guarded_with_their_roles(self) -> None:
        config = build_config(relocated_root(self))
        real = project_config.assert_write_target
        calls = []

        def record(configuration, target, *, role):
            checked = real(configuration, target, role=role)
            calls.append((Path(target).name, role))
            return checked

        with mock.patch.object(project_config, "assert_write_target", side_effect=record):
            versus_session.resolve_settings(config)
        roles = dict(calls)
        self.assertEqual(roles.get("catalog.json"), "work")
        self.assertEqual(roles.get("game"), "experimental")

    def test_key_uses_resolved_hold_gap_and_helper_budget(self) -> None:
        settings = make_settings(self, versus_session)
        session = versus_session.Session(Path("unused"), settings)
        session.process = mock.Mock(pid=5)
        with mock.patch.object(session, "assert_process"), \
             mock.patch.object(versus_session.nav, "key_for", return_value="Z"), \
             mock.patch.object(versus_session, "powershell") as shell:
            session.key(1, "confirm")
        script, timeout = shell.call_args.args
        self.assertIn(str(settings.winshot / "postkey.ps1"), script)
        self.assertIn("-HoldMs 100 -GapMs 350", script)
        self.assertEqual(timeout, settings.helper_timeout)


class SessionUsesItsOwnSettingsTest(unittest.TestCase):
    """Distinct values prove the session reads its settings object, not former literals."""

    def setUp(self) -> None:
        self.settings = dataclasses.replace(
            make_settings(self, versus_session), state_timeout=3.25, helper_timeout=4.5,
            startup_timeout=6.75, key_hold_ms=111, key_gap_ms=333, menu_fade=0.4)

    def test_launch_uses_startup_and_helper_budgets(self) -> None:
        game = self.settings.game
        (game / "settings.toml").write_text('[controller]\np1_device = "keyboard"\np2_device = "keyboard"\n')
        (game / "keybinds.ini").write_text("")
        with tempfile.TemporaryDirectory() as tmp, \
             mock.patch.object(versus_session, "powershell", return_value="0") as shell, \
             mock.patch.object(versus_session.nav, "parse_bindings", return_value={}), \
             mock.patch.object(versus_session.nav, "key_for"), \
             mock.patch.object(versus_session.nav, "wait_until") as wait_until, \
             mock.patch.object(versus_session, "process_identity", return_value={}) as identity, \
             mock.patch.object(versus_session.subprocess, "Popen", return_value=mock.Mock(pid=3)), \
             mock.patch.dict(versus_session.os.environ, {}, clear=True):
            session = versus_session.Session(Path(tmp), self.settings)
            session.start()
            for log in session.logs:
                log.close()
        self.assertEqual(shell.call_args.args[1], 4.5)
        identity.assert_called_once_with(3, game, 4.5)
        self.assertEqual(wait_until.call_args.args[2], 6.75)

    def test_default_wait_uses_state_budget(self) -> None:
        session = versus_session.Session(Path("unused"), self.settings)
        with mock.patch.object(versus_session.nav, "wait_until", return_value={}) as wait_until:
            session.wait(lambda state: True)
            session.wait(lambda state: True, 9.0)
        self.assertEqual([call.args[2] for call in wait_until.call_args_list], [3.25, 9.0])

    def test_finish_match_uses_the_given_budget_over_the_setting(self) -> None:
        session = versus_session.Session(Path("unused"), self.settings)  # settings.finish_timeout stays 420
        with mock.patch.object(versus_session.time, "monotonic", side_effect=[0.0, 30.0]), \
             mock.patch.object(session, "state", side_effect=AssertionError("sampled after the budget")):
            with self.assertRaises(TimeoutError):
                session.finish_match(29.0)

    def test_missing_controller_table_is_a_plain_value_error(self) -> None:
        (self.settings.game / "settings.toml").write_text("[graphics]\nlevel = 1\n")
        session = versus_session.Session(Path("unused"), self.settings)
        with mock.patch.object(versus_session, "powershell", return_value="0"), \
             self.assertRaisesRegex(ValueError, r"\[controller\]"):
            session.start()

    def test_key_uses_session_hold_and_gap(self) -> None:
        session = versus_session.Session(Path("unused"), self.settings)
        session.process = mock.Mock(pid=5)
        with mock.patch.object(session, "assert_process"), \
             mock.patch.object(versus_session.nav, "key_for", return_value="Z"), \
             mock.patch.object(versus_session, "powershell") as shell:
            session.key(1, "confirm")
        script, timeout = shell.call_args.args
        self.assertIn("-HoldMs 111 -GapMs 333", script)
        self.assertEqual(timeout, 4.5)


class ParserPrecedenceTest(unittest.TestCase):
    def _error(self, parser, argv: list[str]) -> tuple[int, str]:
        stderr = io.StringIO()
        with redirect_stderr(stderr), self.assertRaises(SystemExit) as raised:
            parser.parse_args(argv)
        return raised.exception.code, stderr.getvalue()

    def test_default_finish_budget_is_the_resolved_value(self) -> None:
        common = build_config(relocated_root(self))
        local = build_config(relocated_root(self), LOCAL + "[harness]\nfinish_timeout_seconds = 5.0\n")
        self.assertEqual(versus_session.build_parser(common).parse_args([]).finish_timeout, 420.0)
        self.assertEqual(versus_session.build_parser(local).parse_args([]).finish_timeout, 5.0)

    def test_explicit_finish_budget_wins(self) -> None:
        parser = versus_session.build_parser(build_config(relocated_root(self)))
        self.assertEqual(parser.parse_args(["--finish-timeout", "30"]).finish_timeout, 30.0)
        self.assertEqual(parser.parse_args(["--finish-timeout", "30.5"]).finish_timeout, 30.5)

    def test_invalid_finish_budget_is_rejected(self) -> None:
        parser = versus_session.build_parser(build_config(relocated_root(self)))
        for value in ("0", "-1", "inf", "nan", "86401", "soon"):
            with self.subTest(value=value):
                code, _ = self._error(parser, ["--finish-timeout", value])
                self.assertEqual(code, 2)
        self.assertEqual(parser.parse_args(["--finish-timeout", "86400"]).finish_timeout, 86400.0)

    def test_second_versions_accepts_only_two_known_versions(self) -> None:
        parser = versus_session.build_parser(build_config(relocated_root(self)))
        self.assertEqual(parser.parse_args(["--second-versions", "BAG2,BAG1"]).second_versions, "BAG2,BAG1")
        self.assertIsNone(parser.parse_args([]).second_versions)
        for value in ("BAG2", "BAG2,BAG3", "BAG1,BAG2,BAG2", "bag2,bag2"):
            with self.subTest(value=value):
                code, _ = self._error(parser, ["--second-versions", value])
                self.assertEqual(code, 2)

    def test_second_versions_requires_finish(self) -> None:
        with mock.patch.object(versus_session, "load_config", return_value=build_config(relocated_root(self))):
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
                versus_session.main(["--action", "run", "--second-versions", "BAG2,BAG2"])
        self.assertEqual(raised.exception.code, 2)


class MainBeforeEffectsTest(unittest.TestCase):
    def test_config_error_exits_before_any_effect(self) -> None:
        stderr = io.StringIO()
        with mock.patch.object(versus_session, "load_config",
                               side_effect=project_config.ConfigError("bad local")), \
             mock.patch.object(versus_session, "powershell") as shell, \
             mock.patch.object(versus_session.Path, "mkdir") as mkdir, \
             redirect_stderr(stderr), self.assertRaises(SystemExit) as raised:
            versus_session.main(RUN_ARGV)
        self.assertEqual(raised.exception.code, 2)
        self.assertIn("config error: bad local", stderr.getvalue())
        shell.assert_not_called()
        mkdir.assert_not_called()

    def test_local_config_selector_reaches_the_resolver(self) -> None:
        selected = Path("custom.local.toml")
        with mock.patch.object(versus_session, "load_config",
                               side_effect=project_config.ConfigError("stop")) as load, \
             redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            versus_session.main(["--local-config", str(selected), *RUN_ARGV])
        load.assert_called_once_with(local_config=selected)

    def test_unresolved_session_key_exits_before_hash_shell_or_mkdir(self) -> None:
        local = 'schema_version = 1\n[paths]\nexperimental_install = "game"\nstable_install = "stable"\n'
        config = build_config(relocated_root(self), local)
        stderr = io.StringIO()
        with mock.patch.object(versus_session, "load_config", return_value=config), \
             mock.patch.object(versus_session, "powershell") as shell, \
             mock.patch.object(versus_session.Path, "mkdir") as mkdir, \
             mock.patch.object(versus_session.nav, "sha256") as digest, \
             redirect_stderr(stderr), self.assertRaises(SystemExit) as raised:
            versus_session.main(RUN_ARGV)
        self.assertEqual(raised.exception.code, 2)
        self.assertIn("tools.winshot_root", stderr.getvalue())
        for effect in (shell, mkdir, digest):
            effect.assert_not_called()

    def test_run_directory_is_guarded_before_mkdir(self) -> None:
        config = build_config(relocated_root(self))
        guard = project_config.assert_write_target
        calls = []

        def refuse_run(configuration, target, *, role):
            calls.append((Path(target), role))
            if Path(target).name.endswith("-config-test"):
                raise project_config.ConfigError("refused run destination")
            return guard(configuration, target, role=role)

        stderr = io.StringIO()
        with mock.patch.object(versus_session, "load_config", return_value=config), \
             mock.patch.object(project_config, "assert_write_target", side_effect=refuse_run), \
             mock.patch.object(versus_session, "powershell", return_value="0"), \
             mock.patch.object(versus_session.nav, "sha256", return_value="0" * 64), \
             mock.patch.object(versus_session.Path, "mkdir",
                               side_effect=AssertionError("run directory created before its guard")) as mkdir, \
             redirect_stderr(stderr), self.assertRaises(SystemExit) as raised:
            versus_session.main(RUN_ARGV)
        self.assertEqual(raised.exception.code, 2)
        self.assertIn("refused run destination", stderr.getvalue())
        mkdir.assert_not_called()
        run_target, role = calls[-1]
        self.assertEqual((run_target.parent, role), (config.values["paths.work_root"] / "versus-runs", "work"))

    def test_active_session_is_refused_before_creating_a_run(self) -> None:
        config = build_config(relocated_root(self))
        with mock.patch.object(versus_session, "load_config", return_value=config), \
             mock.patch.object(versus_session, "powershell", return_value="1"), \
             mock.patch.object(versus_session.nav, "sha256", return_value="0" * 64), \
             mock.patch.object(versus_session.Path, "mkdir",
                               side_effect=AssertionError("run created despite the active session")) as mkdir, \
             mock.patch.object(versus_session, "LOGGER"):
            self.assertEqual(versus_session.main(RUN_ARGV), 1)
        mkdir.assert_not_called()

    def test_explicit_finish_timeout_reaches_the_sink(self) -> None:
        config = build_config(relocated_root(self))
        settings = versus_session.resolve_settings(config)
        settings.catalog.parent.mkdir(parents=True, exist_ok=True)
        settings.catalog.write_text("{}")
        session = mock.Mock(process=None, actions=[], shots=[], checkpoints={}, debug_fixtures={})

        class Files:
            restoration = {"verified": True}

            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

        with mock.patch.object(versus_session, "load_config", return_value=config), \
             mock.patch.object(versus_session, "powershell", return_value="0"), \
             mock.patch.object(versus_session.nav, "sha256", return_value="0" * 64), \
             mock.patch.object(versus_session.nav, "validated_edges", return_value={}), \
             mock.patch.object(versus_session.nav, "verify_catalog_review"), \
             mock.patch.object(versus_session.nav, "IsolatedFiles", return_value=Files()), \
             mock.patch.object(versus_session, "Session", return_value=session), \
             mock.patch.object(versus_session, "save_result"), \
             mock.patch.object(versus_session, "LOGGER"):
            status = versus_session.main(["--action", "run", "--temporary-controls", "--tag", "sink",
                                          "--finish", "--finish-timeout", "30"])
        self.assertEqual(status, 0)
        session.finish_match.assert_called_once_with(30.0)

    def test_inspect_needs_only_identity_keys(self) -> None:
        local = 'schema_version = 1\n[paths]\nexperimental_install = "game"\nstable_install = "stable"\n'
        config = build_config(relocated_root(self), local)
        game = config.values["paths.experimental_install"]
        (game / "keybinds.ini").write_text("")
        with mock.patch.object(versus_session, "load_config", return_value=config), \
             mock.patch.object(versus_session, "process_identity", return_value={}) as identity, \
             mock.patch.object(versus_session.nav, "parse_bindings", return_value={}), \
             mock.patch.object(versus_session, "LOGGER"):
            try:
                status = versus_session.main(["--action", "inspect", "--game-id", "9"])
            except SystemExit as exc:
                self.fail(f"inspect demanded keys beyond versus-inspect (exit {exc.code})")
        self.assertEqual(status, 0)
        identity.assert_called_once_with(9, game, 35.0)


@unittest.skipUnless(os.name == "nt", "PowerShell wrapper runs on Windows")
class WrapperFinishBudgetTest(unittest.TestCase):
    """The wrapper forwards a finish budget only when the caller binds one."""

    def _argv(self, *options: str) -> list[str]:
        script = Path(versus_session.__file__).with_name("bag2_versus.ps1")
        # A `py` function shadows the launcher, so only the forwarded arguments are observed.
        command = ("function py { $global:LASTEXITCODE = 0; $args -join '|' }; "
                   f"& '{script}' {' '.join(options)}")
        completed = subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                                    "-Command", command], capture_output=True, timeout=60)
        self.assertEqual(completed.returncode, 0, completed.stderr.decode("utf-8", "replace"))
        return completed.stdout.decode("utf-8", "replace").strip().split("|")

    def test_unbound_finish_budget_defers_to_resolved_value(self) -> None:
        argv = self._argv("-Finish")
        self.assertIn("--finish", argv)
        self.assertNotIn("--finish-timeout", argv)
        self.assertNotIn("--local-config", argv)

    def test_bound_finish_budget_and_local_config_are_forwarded(self) -> None:
        argv = self._argv("-Finish", "-FinishTimeout", "30", "-LocalConfig", "custom.local.toml")
        for option in ("--finish-timeout", "--local-config"):
            self.assertIn(option, argv)
        self.assertEqual(argv[argv.index("--finish-timeout") + 1], "30")
        self.assertEqual(argv[argv.index("--local-config") + 1], "custom.local.toml")

    def test_bound_finish_budget_is_forwarded_without_finish(self) -> None:
        # The wrapper forwards what the caller binds; the driver decides when it applies.
        argv = self._argv("-FinishTimeout", "31")
        self.assertNotIn("--finish", argv)
        self.assertEqual(argv[argv.index("--finish-timeout") + 1], "31")


if __name__ == "__main__":
    unittest.main()
