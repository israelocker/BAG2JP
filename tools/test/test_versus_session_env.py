"""The game process only receives explicitly allowlisted BAG2JP debug fixtures."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))  # versus_session imports siblings by name
import versus_session


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

    def test_recorded_fixtures_are_those_passed_to_the_game(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            game = Path(tmp)
            (game / "settings.toml").write_text('[controller]\np1_device = "keyboard"\np2_device = "keyboard"\n')
            (game / "keybinds.ini").write_text("")
            popen = mock.Mock(return_value=mock.Mock(pid=1))
            with mock.patch.object(versus_session, "GAME", game), \
                 mock.patch.object(versus_session, "powershell", return_value="0"), \
                 mock.patch.object(versus_session.nav, "parse_bindings", return_value={}), \
                 mock.patch.object(versus_session.nav, "key_for"), \
                 mock.patch.object(versus_session.nav, "wait_until"), \
                 mock.patch.object(versus_session, "process_identity", return_value={}), \
                 mock.patch.object(versus_session.subprocess, "Popen", popen), \
                 mock.patch.dict(versus_session.os.environ, {"BAG2JP_TEST_P1_DUET": "1",
                                                             "BAG2JP_TEST_HEAT_STRIKE_DUEL": "1"}):
                session = versus_session.Session(game)
                self.assertIsNone(session.debug_fixtures)
                session.start()
                for log in session.logs:
                    log.close()
        env = popen.call_args.kwargs["env"]
        self.assertEqual(env["BAG2JP_TEST_P1_DUET"], "1")
        self.assertNotIn("BAG2JP_TEST_HEAT_STRIKE_DUEL", env)
        self.assertEqual(session.debug_fixtures, versus_session.armed_debug_fixtures(env))
        self.assertEqual(session.debug_fixtures, {"BAG2JP_TEST_P1_DUET": "1"})

    def test_only_test_fixtures_are_allowlisted(self) -> None:
        for name in versus_session.DEBUG_ENV_ALLOWLIST:
            with self.subTest(name=name):
                self.assertTrue(name.startswith("BAG2JP_TEST_"))


if __name__ == "__main__":
    unittest.main()
