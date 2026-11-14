"""Compile production selector callbacks against bounded synthetic guest RAM."""
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mods-src/bag2jp.feature.bag1-content/bag2jp_charsel_popup.c"


def linux_path(path: Path) -> str:
    """Translate an absolute Windows path for the recorded WSL compiler."""
    return "/mnt/" + path.drive[0].lower() + path.as_posix()[2:]


def function_body(source: str, name: str) -> str:
    """Extract an actual static callback, including its balanced function body."""
    match = re.search(r"^static [^\n]+\b" + name + r"\([^\n]*\)\s*\{", source, re.M)
    if not match:
        raise ValueError(f"Missing production function {name}")
    start = source.index("{", match.start())
    depth = 1
    end = start + 1
    while depth:
        depth += (source[end] == "{") - (source[end] == "}")
        end += 1
    return source[match.start():end]


def name_hook_registration(source: str) -> tuple[int, int]:
    """Resolve the actual registered name callback site and expected instruction."""
    match = re.search(r'psx_mod_register_instruction_plugin\("bag2jp.charsel_popup",\s*'
                      r'(\w+),\s*(\w+),\s*cs_char_name_hook\)', source)
    if not match:
        raise ValueError("Missing name-hook registration")
    values = []
    for token in match.groups():
        if token.startswith("CS_"):
            token = re.search(r"#define " + token + r"\s+(\w+)", source).group(1)
        values.append(int(token.rstrip("uU"), 0))
    return values[0], values[1]


class CharselPreviewTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        """Build once; each test starts a fresh synthetic process."""
        cls.temp = tempfile.TemporaryDirectory(dir=ROOT / "_work")
        cls.addClassCleanup(cls.temp.cleanup)
        folder = Path(cls.temp.name)
        cls.binary = folder / "selector-preview"
        source = SOURCE.read_text(encoding="utf-8")
        constants = "\n".join(re.findall(r"^#define CS_.*$", source, re.M))
        state = source[source.index("enum { P_IDLE"):source.index("static char s_dir")]
        names = ["cs_screen_active"]
        if "static void cs_set_gaso_name(" in source:
            names.append("cs_set_gaso_name")
        if "static int cs_gaso_preview(" in source:
            names.append("cs_gaso_preview")
        names += ["cs_feedback_hook", "cs_char_name_hook", "cs_vblank"]
        callbacks = constants + "\n" + state + "\nstatic atomic_uint s_pending_sfx;\n"
        site, word = name_hook_registration(source)
        callbacks += f"#define TEST_NAME_SITE {site}u\n#define TEST_NAME_WORD {word}u\n"
        callbacks += "\n".join(function_body(source, name) for name in names)
        harness = (ROOT / "tools/test/charsel_preview_harness.c").read_text(encoding="utf-8")
        candidate = folder / "selector-preview.c"
        candidate.write_text(harness.replace("/* PRODUCTION_CALLBACKS */", callbacks), encoding="utf-8")
        result = subprocess.run([
            "wsl.exe", "-d", "Ubuntu", "--exec", "gcc", "-std=c11",
            "-Wall", "-Wextra", "-Werror", linux_path(candidate), "-o", linux_path(cls.binary),
        ], capture_output=True, text=True)
        if result.returncode:
            raise AssertionError(result.stdout + result.stderr)

    def check_scenario(self, scenario: int) -> None:
        """Run one callback scenario and retain assertion diagnostics on failure."""
        result = subprocess.run([
            "wsl.exe", "-d", "Ubuntu", "--exec", linux_path(self.binary), str(scenario),
        ], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_return_keeps_gaso_preview_player_one(self) -> None:
        self.check_scenario(0)

    def test_return_keeps_gaso_preview_player_two(self) -> None:
        self.check_scenario(1)

    def test_bio_remains_stock(self) -> None:
        self.check_scenario(2)

    def test_open_popup_can_preview_bio_without_committing(self) -> None:
        self.check_scenario(3)

    def test_cancel_restores_committed_gaso_during_swallow(self) -> None:
        self.check_scenario(4)

    def test_overlay_reload_reuploads_gaso_clut(self) -> None:
        self.check_scenario(5)

    def test_opposite_versions_upload_independent_player_portraits(self) -> None:
        self.check_scenario(6)

    def test_replay_keeps_provisional_version(self) -> None:
        self.check_scenario(7)

    def test_heat_preview_is_untouched(self) -> None:
        self.check_scenario(8)

    def test_stage_select_keeps_confirmed_gaso(self) -> None:
        self.check_scenario(9)

    def test_active_selector_does_not_reupload_unchanged_portrait(self) -> None:
        self.check_scenario(10)

    def test_other_player_popup_and_cancel_preserve_committed_preview(self) -> None:
        self.check_scenario(11)

    def test_return_name_is_prepared_with_portrait_before_draw_hook(self) -> None:
        self.check_scenario(12)

    def test_mixed_names_are_selected_before_each_native_consumer(self) -> None:
        self.check_scenario(13)

    def test_registered_name_instruction_matches_native_overlay(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        site, expected = name_hook_registration(source)
        overlay = (ROOT / "assets/archive/system/007.dbi").read_bytes()
        offset = 12 + site - 0x8008F890
        self.assertEqual(int.from_bytes(overlay[offset:offset + 4], "little"), expected)


if __name__ == "__main__":
    unittest.main()
