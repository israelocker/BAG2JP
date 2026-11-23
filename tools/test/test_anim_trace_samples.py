"""Exercise the production vblank sample with guest reads, without a game."""
import ast
from pathlib import Path
import re
import struct
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


class PreDrawCaptureTest(unittest.TestCase):
    def test_entry_context_contains_weight_and_both_matrix_buffers(self) -> None:
        """Compile the real observer; gates must emit only two complete v2 records."""
        text = (ROOT / 'mods-src/bag2jp.debug.anim-trace/bag2jp_anim_trace.c').read_text()
        start = text.index('#define BAG2_PRE_DRAW_ADDR')
        end = text.index('\nPSX_MOD_CONSTRUCTOR', start)
        block = text[start:end]
        harness = r'''
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
struct CPUState { uint32_t gpr[32]; };
static FILE *s_log;
static int s_dump_at;
static uint32_t s_trace_frame;
static int failure_mode;
static unsigned open_count;
const char *SDL_GetBasePath(void) { return ""; }
uint32_t psx_mod_read_word(uint32_t address) { return address ^ 0x12345678u; }
uint32_t psx_mod_read_half(uint32_t address) { return address & 0xfffu; }
static FILE *capture_open(const char *path, const char *mode) {
    if (strcmp(path, "bag2jp_prehistory_100.v2.bin") || strcmp(mode, "ab")) abort();
    ++open_count;
    return failure_mode == 1 ? NULL : stdout;
}
static size_t capture_write(const void *data, size_t size, size_t count, FILE *stream) {
    if (failure_mode == 2) { fwrite(data, 1, 12, stream); return 0; }
    return fwrite(data, size, count, stream);
}
static int capture_close(FILE *stream) {
    fflush(stream);
    return failure_mode == 3 ? EOF : 0;
}
#define fopen capture_open
#define fclose capture_close
#define fwrite capture_write
''' + block + r'''
int main(int argc, char **argv) {
    struct CPUState cpu = {{0}};
    s_log = stderr;
    failure_mode = argc > 1 ? atoi(argv[1]) : 0;
    cpu.gpr[4] = 0x80100000u;
    at_pre_draw(&cpu, BAG2_PRE_DRAW_ADDR);
    s_dump_at = 100; s_trace_frame = 99;
    at_pre_draw(&cpu, BAG2_PRE_DRAW_ADDR);
    s_trace_frame = 100;
    at_pre_draw(&cpu, BAG2_PRE_DRAW_ADDR);
    cpu.gpr[4] = 0x80110000u;
    at_pre_draw(&cpu, BAG2_PRE_DRAW_ADDR);
    fprintf(stderr, "opens=%u\n", open_count);
    return 0;
}
'''
        with tempfile.TemporaryDirectory(dir=ROOT / '_work') as temporary:
            directory = Path(temporary)
            source, binary = directory / 'pre_draw.c', directory / 'pre_draw'
            source.write_text(harness, encoding='utf-8')
            subprocess.run(['wsl.exe', '-d', 'Ubuntu', '--exec', 'gcc', '-std=c11',
                            '-Wall', '-Werror', linux_path(source), '-o', linux_path(binary)],
                           check=True, capture_output=True)
            result = subprocess.run(['wsl.exe', '-d', 'Ubuntu', '--exec', linux_path(binary)],
                                    check=True, capture_output=True)
            failures = [subprocess.run(['wsl.exe', '-d', 'Ubuntu', '--exec', linux_path(binary), str(mode)],
                                       check=True, capture_output=True) for mode in (1, 2, 3)]
        record_bytes = 16 + 2 * 30 * 32
        self.assertEqual(len(result.stdout), 2 * record_bytes)
        for index, actor in enumerate((0x80100000, 0x80110000)):
            record = result.stdout[index * record_bytes:(index + 1) * record_bytes]
            self.assertEqual(struct.unpack_from('<4I', record), (0x32564850, 100, actor, 0x546))
            expected = [(actor + base + offset) ^ 0x12345678
                        for base in (0x2c, 0x3ec) for offset in range(0, 960, 4)]
            self.assertEqual(struct.unpack_from('<480I', record, 16), tuple(expected))
        self.assertEqual(result.stderr, b'opens=2\n')
        for result, expected_bytes in zip(failures, (0, 12, record_bytes)):
            with self.subTest(failure_output_bytes=expected_bytes):
                self.assertEqual(len(result.stdout), expected_bytes)
                self.assertIn(b'prehistory capture failed', result.stderr)
                self.assertIn(b'opens=1', result.stderr)


if __name__ == '__main__':
    unittest.main()
