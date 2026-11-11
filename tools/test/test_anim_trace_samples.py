"""Exercise the production vblank sample with guest reads, without a game."""
import ast
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

from tools.test.combat_inputs import trace_rows

ROOT = Path(__file__).resolve().parents[2]


def linux_path(path: Path) -> str:
    """Translate the recorded checkout path for WSL gcc."""
    return '/mnt/' + path.drive[0].lower() + path.as_posix()[2:]


class AnimTraceSamplesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        """Compile the actual sampling block; mock only guest RAM access."""
        cls.directory = tempfile.TemporaryDirectory(dir=ROOT / '_work')
        cls.addClassCleanup(cls.directory.cleanup)
        directory = Path(cls.directory.name)
        text = (ROOT / 'mods-src/bag2jp.debug.anim-trace/bag2jp_anim_trace.c').read_text()
        start = text.index('    uint32_t cur[16] = {0};')
        end = text.index('\n}', start)
        block = text[start:end]
        harness = r'''
#include <stdint.h>
#include <stdio.h>
static FILE *s_log;
static uint32_t last[16];
static uint32_t clock_value = 100, pending = 202, pending_p1 = 123;
static uint32_t psx_mod_read_word(uint32_t a) {
    switch (a) {
    case 0x8005F808u: return 0x80100000u;
    case 0x8005F810u: return 0x80110000u;
    case 0x8010154Cu: return 74;
    case 0x8011154Cu: return 89;
    case 0x8005D3D8u: return 1;
    case 0x8005D3DCu: return 2;
    case 0x8005D2C4u: return 2;
    case 0x800892ECu: return clock_value;
    default: return 0;
    }
}
static uint32_t psx_mod_read_byte(uint32_t a) {
    return a == 0x80100004u ? 9 : 0;
}
static uint32_t psx_mod_read_half(uint32_t a) {
    switch (a) {
    case 0x8005CF22u: return 110;
    case 0x8005CF46u: return 202;
    case 0x8005CF20u: return pending_p1;
    case 0x8005CF44u: return pending;
    default: return 0;
    }
}
static void sample(uint32_t frame) {
''' + block + r'''
}
int main(void) {
    s_log = stdout;
    sample(10);
    sample(11); /* Identical samples must remain suppressed. */
    clock_value++;
    sample(12); /* Clock-only changes still provide a duration sample. */
    pending = 0;
    sample(13); /* Include pending-only changes. */
    pending_p1 = 0;
    sample(14); /* The two pending fields must be independent. */
    return 0;
}
'''
        source = directory / 'sample.c'
        binary = directory / 'sample'
        source.write_text(harness, encoding='utf-8')
        subprocess.run(['wsl.exe', '-d', 'Ubuntu', '--exec', 'gcc', '-std=c11',
                        '-Wall', '-Werror', linux_path(source), '-o', linux_path(binary)],
                       check=True, capture_output=True)
        result = subprocess.run(['wsl.exe', '-d', 'Ubuntu', '--exec', linux_path(binary)],
                                check=True, capture_output=True)
        cls.output = result.stdout
        cls.log = directory / 'trace.log'
        cls.log.write_bytes(cls.output)

    def test_existing_combat_parser_accepts_trace(self) -> None:
        self.assertEqual(trace_rows(self.log), [(10, 74, 110, 89, 202)])

    def test_existing_report_parser_accepts_trace(self) -> None:
        # Read the real report pattern without executing its CLI and I/O.
        tree = ast.parse((ROOT / 'tools/test/bag2_report.py').read_text())
        patterns = [node.args[0].value for node in ast.walk(tree)
                    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == 'match' and node.args
                    and isinstance(node.args[0], ast.Constant)]
        self.assertEqual(len(patterns), 1)
        matches = [re.match(patterns[0], line) for line in self.output.decode().splitlines()]
        self.assertEqual([int(match[1]) for match in matches if match], [10])

    def test_song_frames_and_pending_are_separate_samples(self) -> None:
        samples = re.findall(rb'^sample f(\d+) songframe(\d+) pend(\d+)/(\d+)$',
                             self.output, re.MULTILINE)
        self.assertEqual([tuple(map(int, sample)) for sample in samples],
                          [(10, 100, 123, 202), (12, 101, 123, 202),
                           (13, 101, 123, 0), (14, 101, 0, 0)])


if __name__ == '__main__':
    unittest.main()
