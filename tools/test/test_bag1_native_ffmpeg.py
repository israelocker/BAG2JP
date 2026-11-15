"""Host regression: ffmpeg_native() resolves from the shared resolver, never hardcodes a machine path."""
from pathlib import Path
import unittest

from tools.workflow.project_config import ConfigError
from tools.workflow.test_project_config import ConfigFixture


class NativeFFmpegTests(ConfigFixture):
    def setUp(self):
        super().setUp()
        self.write_local('[tools]\nffmpeg_native="tools/ffmpeg_native.exe"\n')
        (self.root / "tools").mkdir()
        (self.root / "tools/ffmpeg_native.exe").write_bytes(b"owned fixture, never executed")

    def test_ffmpeg_native_resolves_from_config(self):
        from tools.bag1native.run_match_and_attack import ffmpeg_native
        path = ffmpeg_native(config=self.load())
        self.assertEqual(path, self.root / "tools/ffmpeg_native.exe")
        self.assertTrue(path.is_file())

    def test_ffmpeg_native_missing_config_raises_before_effects(self):
        from tools.bag1native.run_match_and_attack import ffmpeg_native
        self.write_local('[tools]\n')
        with self.assertRaises(ConfigError):
            ffmpeg_native(config=self.load())

    def test_no_machine_path_literal_in_source(self):
        from pathlib import Path as _P
        source = _P(__file__).resolve().parents[2] / "tools/bag1native/run_match_and_attack.py"
        text = source.read_text(encoding="utf-8")
        self.assertNotIn(r"D:\ffmpeg\bin\ffmpeg.exe", text)
        self.assertNotIn(r"D:\ffmpeg", text)
