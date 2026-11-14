"""Compile the real diagnostic extent selector, without starting a game."""
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]


class RamDumpExtentTests(unittest.TestCase):
    def test_default_and_explicit_extended_ram(self):
        text = (ROOT / 'mods-src/bag2jp.debug.anim-trace/bag2jp_anim_trace.c').read_text()
        start = text.index('static uint32_t bag2_ram_dump_end(')
        end = text.index('\n}', start) + 2
        function = text[start:end]
        dump = text[text.index('if (s_dump_at > 0 && frame =='):text.index('/* BAG2JP_VRAM_DUMP=frame')]
        self.assertIn('bag2_ram_dump_end(getenv("BAG2JP_RAM_DUMP_SIZE"))', dump)
        self.assertIn('a < end; a += 4', dump)
        harness = '''#include <assert.h>
#include <stdint.h>
#include <string.h>
''' + function + '''
int main(void) {
    assert(bag2_ram_dump_end(NULL) == 0x80200000u);
    assert(bag2_ram_dump_end("") == 0x80200000u);
    assert(bag2_ram_dump_end("8mb") == 0x80800000u);
    assert(bag2_ram_dump_end("16mb") == 0x80200000u);
    assert(bag2_ram_dump_end("8mb-junk") == 0x80200000u);
    return 0;
}
'''
        out = ROOT / '_work/stage_import/strike/ram-dump-test'
        out.mkdir(parents=True, exist_ok=True)
        source = out / 'extent.c'
        source.write_text(harness)
        linux = '/mnt/d/' + source.as_posix()[3:]
        subprocess.run(['wsl.exe', '-d', 'Ubuntu', '--exec', 'gcc', '-Wall', '-Werror',
                        linux, '-o', linux[:-2]], check=True, capture_output=True)
        subprocess.run(['wsl.exe', '-d', 'Ubuntu', '--exec', linux[:-2]],
                       check=True, capture_output=True)


if __name__ == '__main__':
    unittest.main()
