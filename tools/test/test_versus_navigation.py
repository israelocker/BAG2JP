"""Regression tests for observed-state versus selection and safe test sessions."""
from pathlib import Path
import tempfile
import unittest
import tomllib
import json
import subprocess
from unittest.mock import patch

import versus_session

import versus_navigation as nav


class NavigationTests(unittest.TestCase):
    """Catch silent fallback, wrong mode, stale evidence and shared input."""

    def test_resolve_normalizes_known_character_name(self):
        self.assertEqual(nav.resolve_character(" comet "), 2)

    def test_unknown_character_is_not_heat(self):
        with self.assertRaises(ValueError):
            nav.resolve_character("missing")

    def test_stock_character_rejects_unimplemented_bag1(self):
        with self.assertRaises(ValueError):
            nav.validate_pick("Strike", "BAG1", "A")

    def test_invalid_costume_rejected(self):
        with self.assertRaises(ValueError):
            nav.validate_pick("Heat", "BAG1", "C")

    def test_missing_player2_confirmation_detected(self):
        bindings = nav.parse_bindings("[player1]\ncircle=S\n[player2]\ncircle=None\n")
        with self.assertRaises(ValueError):
            nav.key_for(bindings, 2, "circle")

    def test_shared_direction_is_not_independent(self):
        bindings = nav.parse_bindings("[player1]\ndown=Down, K\n[player2]\ndown=K\n")
        with self.assertRaises(ValueError):
            nav.key_for(bindings, 2, "down")

    def test_original_player1_arrow_is_independent(self):
        bindings = nav.parse_bindings("[player1]\ndown=Down, K\n[player2]\ndown=K\n")
        self.assertEqual(nav.key_for(bindings, 1, "down"), "Down")

    def test_route_uses_observed_edges(self):
        self.assertEqual(nav.route(2, 1, {(2, "left"): 0, (0, "down"): 1}), ["left", "down"])

    def test_unproven_route_is_not_guessed(self):
        with self.assertRaises(ValueError):
            nav.route(2, 1, {(2, "left"): 0})

    def test_parse_watch_requires_all_fields(self):
        with self.assertRaises(ValueError):
            nav.parse_watch("f000001 8005D3D4=7")

    def test_stale_heartbeat_rejected(self):
        with self.assertRaises(ValueError):
            nav.check_freshness(100.0, 110.0, 100.0)

    def test_watch_from_prior_session_rejected(self):
        with self.assertRaises(ValueError):
            nav.check_freshness(109.0, 110.0, 109.5)

    def test_single_player_mode_rejected(self):
        with self.assertRaises(ValueError):
            nav.require_versus({"mode": 1})

    def test_wrong_popup_identity_rejected(self):
        with self.assertRaises(ValueError):
            nav.confirmation("confirm: side 1 char 1 version - costume A", 1, 0, "BAG2", "A")

    def test_stock_popup_dash_means_stock_not_bag1(self):
        self.assertEqual(nav.confirmation("confirm: side 1 char 1 version - costume A", 1, 1, "BAG2", "A"), {"side": 1, "character": 1, "version": "BAG2", "costume": "A"})

    def test_backup_restore_preserves_exact_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            file = root / "game/keybinds.ini"
            file.parent.mkdir()
            file.write_bytes(b"original\r\n")
            backup = nav.Backup(root / "game", root / "backup", ["keybinds.ini"])
            backup.create()
            file.write_bytes(b"temporary\n")
            backup.restore()
            self.assertEqual(file.read_bytes(), b"original\r\n")

    def test_backup_cannot_overwrite_existing_baseline(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "game").mkdir()
            (root / "backup").mkdir()
            with self.assertRaises(FileExistsError):
                nav.Backup(root / "game", root / "backup", []).create()

    def test_temporary_keys_preserve_other_players(self):
        text = "[player1]\ncircle=S\n[player2]\ncircle=None\n[player3]\ncircle=S\n"
        self.assertIn("[player3]\ncircle=S", nav.temporary_bindings(text))

    def test_temporary_keys_allow_independent_confirmation(self):
        text = "[player1]\ncircle=S\n[player2]\ncircle=None\n"
        self.assertEqual(nav.key_for(nav.parse_bindings(nav.temporary_bindings(text)), 2, "circle"), "M")

    def test_isolated_settings_route_cards_away_from_original(self):
        text = '[memcard]\ndir="saves"\ncard1="saves/card1.mcd"\ncard2="saves/card2.mcd"\n[video]\nfullscreen=0\n'
        self.assertEqual(tomllib.loads(nav.isolated_settings(text, Path("D:/evidence/cards")))["memcard"]["card1"], "D:/evidence/cards/card1.mcd")

    def test_wait_stops_after_deadline(self):
        clock = iter([0, 0, 1, 2, 3])
        with self.assertRaises(TimeoutError):
            nav.wait_until(lambda: 1, lambda value: value == 2, 2, clock=lambda: next(clock), sleep=lambda _: None)

    def test_wait_returns_observed_value_not_expected_value(self):
        self.assertEqual(nav.wait_until(lambda: {"mode": 2}, lambda value: value["mode"] == 2, 2), {"mode": 2})

    def test_session_restores_settings_after_body_error(self):
        with tempfile.TemporaryDirectory() as directory:
            game = Path(directory) / "game"
            (game / "mods").mkdir(parents=True)
            (game / "saves").mkdir()
            (game / "saves/card1.mcd").write_bytes(b"card-one")
            (game / "saves/card2.mcd").write_bytes(b"card-two")
            settings = b'[memcard]\ndir="saves"\ncard1="saves/card1.mcd"\ncard2="saves/card2.mcd"\n'
            (game / "settings.toml").write_bytes(settings)
            (game / "keybinds.ini").write_text("[player1]\ncircle=S\n[player2]\ncircle=None\n")
            (game / "mods/state.toml").write_bytes(b"# original\r\n")
            with self.assertRaisesRegex(RuntimeError, "test failure"):
                with nav.IsolatedFiles(game, Path(directory) / "run"):
                    raise RuntimeError("test failure")
            self.assertEqual((game / "settings.toml").read_bytes(), settings)

    def test_read_watch_decodes_cursor_byte_not_player_side(self):
        line = "f000001 " + " ".join(f"{address:08X}={0x00020100 if name == 'p2_position' else 0:X}" for name, (address, _) in nav.WATCHES.items())
        self.assertEqual(nav.cursor(nav.parse_watch(line), 2), 2)

    def test_selector_rejects_other_overlay(self):
        with self.assertRaises(ValueError):
            nav.require_selector({"mode": 2, "root": 12, "guard1": 0, "guard2": 0})

    def test_files_are_not_restored_under_running_game(self):
        with tempfile.TemporaryDirectory() as directory:
            files = nav.IsolatedFiles(Path(directory), Path(directory) / "run", safe_to_restore=lambda: False)
            with self.assertRaises(RuntimeError):
                files.__exit__(None, None, None)

    def test_active_selector_root_13_accepts_correct_overlay(self):
        state = {"mode": 2, "root": 13, "guard1": 0x27BDFFC8, "guard2": 0x27BDFFB0}
        self.assertIsNone(nav.require_selector(state))

    def test_same_pad_duplicate_action_is_ambiguous(self):
        bindings = nav.parse_bindings("[player1]\ncircle=S\ncross=S\n[player2]\ncircle=M\n")
        with self.assertRaises(ValueError):
            nav.key_for(bindings, 1, "circle")

    def test_menu_waits_for_title_without_unsafe_start(self):
        class ObservedSession(versus_session.Session):
            def __init__(self):
                self.observed = {"root": 0, "mode": 0, "menu": 0,
                                 "p1_status": 65536, "p2_status": 65536,
                                 "guard1": 0x27BDFFC8, "guard2": 0x27BDFFB0}

            def state(self):
                return self.observed.copy()

            def wait(self, predicate, timeout=25):
                if self.observed["root"] == 0:
                    self.observed["root"] = 7
                if not predicate(self.observed):
                    raise TimeoutError("wrong observation")
                return self.state()

            def key(self, side, action):
                if action == "start":
                    raise AssertionError("Unsafe Start can confirm campaign during boot transition")
                if action == "down":
                    self.observed["menu"] = 1
                elif action == "circle":
                    self.observed.update(root=13, mode=2)

            def shot(self, name):
                pass

        session = ObservedSession()
        with patch.object(versus_session.time, "sleep"):
            session.menu()
        self.assertEqual(session.state()["mode"], 2)

    def test_popup_log_from_previous_process_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "popup.log"
            path.write_text("confirm: side 0 char 0 version BAG1 costume A")
            with self.assertRaises(ValueError):
                versus_session.session_log(path, path.stat().st_mtime + 10)

    def test_opening_skip_happens_only_in_observed_root5(self):
        class OpeningSession(versus_session.Session):
            def __init__(self):
                self.observed = {"root": 5, "mode": 0, "menu": 0,
                                 "p1_status": 65536, "p2_status": 65536,
                                 "guard1": 0x27BDFFC8, "guard2": 0x27BDFFB0}

            def state(self):
                return self.observed.copy()

            def wait(self, predicate, timeout=25):
                if not predicate(self.observed):
                    raise TimeoutError("Opening requires one skip; root6 is transition, not another prompt")
                return self.state()

            def key(self, side, action):
                if action == "start":
                    if self.observed["root"] != 5:
                        raise AssertionError("Start outside observed opening")
                    self.observed["root"] = 7
                elif action == "down":
                    self.observed["menu"] = 1
                elif action == "circle":
                    self.observed.update(root=13, mode=2)

            def shot(self, name):
                pass

        session = OpeningSession()
        with patch.object(versus_session.time, "sleep"):
            session.menu()
        self.assertEqual(session.state()["mode"], 2)

    def test_gameplay_rejects_native_mirror_costume_substitution(self):
        with self.assertRaises(ValueError):
            nav.verify_gameplay({"mode": 2, "character1": 0, "character2": 0, "costumes": 256}, [0, 0], [0, 0])

    def test_gameplay_accepts_exact_characters_and_costumes(self):
        self.assertIsNone(nav.verify_gameplay({"mode": 2, "character1": 2, "character2": 1, "costumes": 0}, [2, 1], [0, 0]))

    def test_unreviewed_calibration_cannot_drive_match(self):
        with self.assertRaises(ValueError):
            nav.validated_edges({"runtime_sha256": "abc", "edges": [[2, "left", 0]]}, "abc")

    def test_approved_calibration_rejects_runtime_change(self):
        with self.assertRaises(ValueError):
            nav.validated_edges({"runtime_sha256": "abc", "visual_review": "accepted", "edges": [[2, "left", 0]]}, "def")

    def test_approved_calibration_returns_graph(self):
        self.assertEqual(nav.validated_edges({"runtime_sha256": "abc", "visual_review": "accepted", "edges": [[2, "left", 0]]}, "abc"), {(2, "left"): 0})

    def test_partial_heartbeat_is_not_gameplay_evidence(self):
        with self.assertRaises(ValueError):
            nav.heartbeat_phases("001234 1/")

    def test_changed_calibration_image_requires_review_again(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "probe.png"
            path.write_bytes(b"changed")
            with self.assertRaises(ValueError):
                nav.verify_catalog_images({"evidence": directory, "image_sha256": {"probe.png": "old"}})

    def test_selector_cannot_be_mistaken_for_gameplay(self):
        self.assertFalse(nav.is_gameplay({"root": 13, "mode": 2, "phase1": 1, "phase2": 3}))

    def test_contact_sheet_contains_only_available_checkpoints(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory)
            Image.new("RGB", (12, 8), "red").save(run / "versus-selected.png")
            Image.new("RGB", (12, 8), "blue").save(run / "gameplay.png")
            sheet = versus_session.contact_sheet(run)
            with Image.open(sheet) as image:
                self.assertEqual(image.getpixel((601, 1)), (0, 0, 255))

    def test_frozen_watch_rejected_while_heartbeat_advances(self):
        with self.assertRaises(ValueError):
            nav.check_watch_progress(109.0, 100.0, 110.0, 90.0, 6600, 6000)

    def test_preparation_interrupt_restores_original_settings(self):
        with tempfile.TemporaryDirectory() as directory:
            game, run = Path(directory) / "game", Path(directory) / "run"
            (game / "mods").mkdir(parents=True)
            (game / "saves").mkdir()
            for name in ("card1", "card2"):
                (game / "saves" / f"{name}.mcd").write_bytes(b"original card")
            original = '[memcard]\ndir="saves"\ncard1="saves/card1.mcd"\ncard2="saves/card2.mcd"\n'
            (game / "settings.toml").write_text(original)
            (game / "keybinds.ini").write_text("[player1]\ncircle=S\n[player2]\ncircle=None\n")
            (game / "mods/state.toml").write_bytes(b"original")
            with patch.object(nav, "temporary_bindings", side_effect=KeyboardInterrupt):
                with self.assertRaises(KeyboardInterrupt):
                    with nav.IsolatedFiles(game, run):
                        pass
            self.assertEqual((game / "settings.toml").read_text(), original)

    def test_sheet_failure_does_not_lose_final_report(self):
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory)
            result = {"status": "failed", "restoration": {"verified": True}}
            with patch.object(versus_session, "contact_sheet", side_effect=OSError("image unreadable")):
                versus_session.save_result(run, result, True)
            self.assertTrue(json.loads((run / "result.json").read_text())["restoration"]["verified"])

    def test_edge_edit_invalidates_visual_approval(self):
        catalog = {"runtime_sha256": "abc", "visual_review": "accepted", "edges": [[2, "left", 0]], "image_sha256": {}, "evidence": "unused"}
        catalog["reviewed_catalog_sha256"] = nav.catalog_review_digest(catalog)
        catalog["edges"] = [[2, "right", 1]]
        with self.assertRaises(ValueError):
            nav.verify_catalog_review(catalog)

    def test_helper_metric_counts_invocation(self):
        before = versus_session.HELPER_CALLS
        response = subprocess.CompletedProcess([], 0, stdout="ok", stderr="")
        with patch.object(versus_session.subprocess, "run", return_value=response):
            versus_session.powershell("Write-Output ok")
        self.assertEqual(versus_session.HELPER_CALLS - before, 1)

    def test_unterminated_watch_row_cannot_replace_complete_observation(self):
        complete = "f000001 " + " ".join(f"{address:08X}=0" for address, _ in nav.WATCHES.values())
        partial = complete.replace("f000001", "f000002").replace("=0", "=F")
        self.assertEqual(nav.watch_observation(complete + "\n" + partial)[0], 1)


if __name__ == "__main__":
    unittest.main()
