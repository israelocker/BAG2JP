"""The game process only receives explicitly allowlisted BAG2JP debug fixtures."""
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))  # versus_session imports siblings by name
import versus_session
from versus_settings_fixture import make_settings


class DebugEnvAllowlistTest(unittest.TestCase):
    def test_duet_fixture_reaches_the_game(self) -> None:
        # bag2jp_anim_trace.c reads BAG2JP_TEST_P1_DUET at the native duet RNG call.
        env = versus_session.build_game_env({"PATH": "x", "BAG2JP_TEST_P1_DUET": "1"})
        self.assertEqual(env, {"PATH": "x", "BAG2JP_TEST_P1_DUET": "1", "BAG2JP_ANIM_TRACE": "1"})

    def test_unlisted_bag2jp_variables_are_stripped(self) -> None:
        # HEAT_STRIKE_DUEL is read by the plugin but is not allowlisted for versus runs.
        env = versus_session.build_game_env({"BAG2JP_TEST_HEAT_STRIKE_DUEL": "1", "BAG2JP_WATCH": "80008548:4",
                                             "BAG2JP_ANIM_TRACE": "0"})
        self.assertEqual(env, {"BAG2JP_ANIM_TRACE": "1"})

    def test_absent_fixture_is_not_injected(self) -> None:
        self.assertEqual(versus_session.build_game_env({}), {"BAG2JP_ANIM_TRACE": "1"})

    def test_armed_fixtures_are_reported(self) -> None:
        self.assertEqual(versus_session.armed_debug_fixtures({"BAG2JP_TEST_GASO_ATTACK": "1", "BAG2JP_X": "1"}),
                         {"BAG2JP_TEST_GASO_ATTACK": "1"})
        self.assertEqual(versus_session.armed_debug_fixtures({}), {})

    def _launch(self, environ: dict[str, str], vram_dump_frames: tuple[int, ...] = (),
                **session_options) -> tuple[versus_session.Session, dict, mock.Mock]:
        settings = make_settings(self, versus_session)
        (settings.game / "settings.toml").write_text('[controller]\np1_device = "keyboard"\np2_device = "keyboard"\n')
        (settings.game / "keybinds.ini").write_text("")
        popen = mock.Mock(return_value=mock.Mock(pid=1))
        with tempfile.TemporaryDirectory() as tmp, \
             mock.patch.object(versus_session, "powershell", return_value="0"), \
             mock.patch.object(versus_session.nav, "parse_bindings", return_value={}), \
             mock.patch.object(versus_session.nav, "key_for"), \
             mock.patch.object(versus_session.nav, "wait_until"), \
             mock.patch.object(versus_session, "process_identity", return_value={}), \
             mock.patch.object(versus_session.subprocess, "Popen", popen), \
             mock.patch.dict(versus_session.os.environ, environ, clear=True):
            session = versus_session.Session(Path(tmp), settings, **session_options)
            session.vram_dump_frames = vram_dump_frames
            self.assertIsNone(session.debug_fixtures)
            session.start()
            for log in session.logs:
                log.close()
        return session, popen.call_args.kwargs["env"], popen

    def test_recorded_fixtures_are_those_passed_to_the_game(self) -> None:
        session, env, popen = self._launch({"BAG2JP_TEST_P1_DUET": "1", "BAG2JP_TEST_HEAT_STRIKE_DUEL": "1"})
        self.assertEqual(env.get("BAG2JP_TEST_P1_DUET"), "1")
        self.assertNotIn("BAG2JP_TEST_HEAT_STRIKE_DUEL", env)
        self.assertEqual(session.debug_fixtures, versus_session.armed_debug_fixtures(env))
        self.assertEqual(session.debug_fixtures, {"BAG2JP_TEST_P1_DUET": "1"})
        self.assertEqual(popen.call_args.args[0][0], str(session.settings.game / "BAG2JP.exe"))
        self.assertEqual(popen.call_args.kwargs["cwd"], session.settings.game)

    def test_declared_fixture_and_vram_schedule_reach_the_game_and_are_recorded(self) -> None:
        # The Strike batch declares HEAT_STRIKE_DUEL per run; it is never inherited from the caller.
        session, env, _ = self._launch({}, fixtures={"BAG2JP_TEST_HEAT_STRIKE_DUEL": "1"})
        self.assertEqual(env.get("BAG2JP_TEST_HEAT_STRIKE_DUEL"), "1")
        self.assertEqual(session.debug_fixtures, {"BAG2JP_TEST_HEAT_STRIKE_DUEL": "1"})
        self.assertNotIn("BAG2JP_VRAM_DUMP", env)

    def test_vram_schedule_is_passed_only_when_declared(self) -> None:
        _, env, _ = self._launch({"BAG2JP_VRAM_DUMP": "1"}, vram_dump_frames=(6500, 6620))
        self.assertEqual(env.get("BAG2JP_VRAM_DUMP"), "6500,6620")

    def test_inherited_vram_schedule_is_stripped(self) -> None:
        _, env, _ = self._launch({"BAG2JP_VRAM_DUMP": "6500"})
        self.assertNotIn("BAG2JP_VRAM_DUMP", env)

    def test_undeclared_or_empty_fixture_is_rejected_before_launch(self) -> None:
        settings = make_settings(self, versus_session)
        for fixtures in ({"BAG2JP_WATCH": "1"}, {"BAG2JP_TEST_HEAT_STRIKE_DUEL": ""},
                         {"BAG2JP_TEST_STRIKE_ATTACK": 1}):
            with self.subTest(fixtures=fixtures), \
                 mock.patch.object(versus_session.subprocess, "Popen") as popen:
                with self.assertRaises(ValueError):
                    versus_session.Session(Path("unused"), settings, fixtures=fixtures)
                popen.assert_not_called()

    def test_declared_fixtures_are_immutable(self) -> None:
        session = versus_session.Session(Path("unused"), make_settings(self, versus_session),
                                         fixtures={"BAG2JP_TEST_STRIKE_ATTACK": "1"})
        with self.assertRaises(TypeError):
            session.fixtures["BAG2JP_TEST_HEAT_STRIKE_DUEL"] = "1"

    def test_declared_fixtures_cannot_be_replaced_after_construction(self) -> None:
        session = versus_session.Session(Path("unused"), make_settings(self, versus_session),
                                         fixtures={"BAG2JP_TEST_STRIKE_ATTACK": "1"})
        with self.assertRaises(AttributeError):
            session.fixtures = {"BAG2JP_WATCH": "80008548:4"}
        self.assertEqual(dict(session.fixtures), {"BAG2JP_TEST_STRIKE_ATTACK": "1"})

    def test_only_evidence_from_this_session_is_copied(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "bag2jp_anim_trace.log"
            source.write_text("earlier run", encoding="utf-8")
            run = Path(tmp) / "run"
            run.mkdir()
            earlier = source.stat().st_mtime - 60
            os.utime(source, (earlier, earlier))
            self.assertFalse(versus_session.copy_current(source, run, 0.0))
            self.assertFalse(versus_session.copy_current(source, run, earlier + 1))
            self.assertFalse((run / source.name).exists())
            self.assertTrue(versus_session.copy_current(source, run, earlier - 1))
            self.assertEqual((run / source.name).read_text(encoding="utf-8"), "earlier run")
            self.assertFalse(versus_session.copy_current(run / "absent.log", run, earlier - 1))

    def test_declared_allowlist_extends_inherited_allowlist_only_by_reviewed_batch_fixture(self) -> None:
        self.assertEqual(set(versus_session.DECLARED_FIXTURE_ALLOWLIST) - set(versus_session.DEBUG_ENV_ALLOWLIST),
                         {"BAG2JP_TEST_HEAT_STRIKE_DUEL"})
        self.assertNotIn("BAG2JP_TEST_HEAT_STRIKE_DUEL", versus_session.DEBUG_ENV_ALLOWLIST)

    def test_only_test_fixtures_are_allowlisted(self) -> None:
        for name in versus_session.DEBUG_ENV_ALLOWLIST:
            with self.subTest(name=name):
                self.assertTrue(name.startswith("BAG2JP_TEST_"))


if __name__ == "__main__":
    unittest.main()
