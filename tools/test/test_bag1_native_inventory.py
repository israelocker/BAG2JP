"""Host regression for tools/bag1native/ S2a inventory baseline.

Verifies imports have no side effects and RAM/path constants match the documented
baseline. Does NOT start the game, capture video, or touch machine state.
"""
from pathlib import Path
import unittest

from tools.workflow.test_project_config import ConfigFixture


class Bag1NativeImportTests(ConfigFixture):
    """bag1_mem and attack_bot must import without starting the game."""

    def test_bag1_mem_imports_without_effects(self):
        import tools.bag1native.bag1_mem as m  # noqa: F401
        self.assertEqual(m.PROCESS_NAME, "BustAGroove_Recompiled")
        self.assertEqual(m.RAM_SIZE, 0x200000)
        self.assertEqual(m.PROBE_FILE_OFF, 0x800 + 0x100)
        self.assertEqual(m.PROBE_PSX, 0x80010100)

    def test_bag1_mem_scus_path_is_repo_relative(self):
        import tools.bag1native.bag1_mem as m  # noqa: F401
        scus = m.SCUS
        expected = Path(__file__).resolve().parents[2] / "_work" / "bag1" / "SCUS_942.63"
        self.assertEqual(scus, expected)

    def test_bag1_mem_source_has_no_machine_path_literal(self):
        from pathlib import Path as _P
        source = _P(__file__).resolve().parents[2] / "tools/bag1native/bag1_mem.py"
        text = source.read_text(encoding="utf-8")
        # SCUS is built from __file__ (repo-relative), not a machine-path literal.
        for line in text.splitlines():
            self.assertNotIn("D:", line)
            self.assertNotIn("C:", line)

    def test_attack_bot_imports_without_effects(self):
        import tools.bag1native.attack_bot as m  # noqa: F401
        self.assertEqual(m.FLAG_ADDR, 0x8006875E)
        self.assertEqual(m.ATTACKS_ADDR, 0x80068766)
        self.assertEqual(m.STATE_ADDR, 0x80068704)
        self.assertEqual(m.BEAT_ADDR, 0x80068440)

    def test_run_match_and_attack_uses_resolver_not_hardcoded_path(self):
        from pathlib import Path as _P
        source = _P(__file__).resolve().parents[2] / "tools/bag1native/run_match_and_attack.py"
        text = source.read_text(encoding="utf-8")
        self.assertNotIn(r"D:\ffmpeg\bin\ffmpeg.exe", text)
        self.assertNotIn(r"D:\ffmpeg", text)
        self.assertIn("ffmpeg_native", text)
