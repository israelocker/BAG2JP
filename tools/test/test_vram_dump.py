"""Compile the real VRAM dump helper against a fake renderer and check its contract."""
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class VramDumpTests(unittest.TestCase):
    """Frame-list parsing is bounded; a dump is one exact 1024x512x16-bit image."""

    def test_parse_and_full_vram_write(self) -> None:
        output = ROOT / '_work/vram-dump-tests'
        output.mkdir(parents=True, exist_ok=True)
        header = '/mnt/d/' + (ROOT / 'mods-src/bag2jp.debug.anim-trace/bag2jp_vram_dump.h').as_posix()[3:]
        source = '''#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <assert.h>
static int calls;
void gr_vram_transfer_out(int x, int y, int w, int h, uint16_t *d) {
 assert(x == 0 && y == 0 && w == 1024 && h == 512); ++calls;
 for (int i = 0; i < w * h; ++i) d[i] = (uint16_t)(i * 7);
}
''' + f'#include "{header}"\n' + '''
int main(void) {
 uint32_t f[BAG2_VRAM_DUMP_MAX];
 assert(bag2_vram_dump_parse(NULL, f) == 0);
 assert(bag2_vram_dump_parse("", f) == 0);
 assert(bag2_vram_dump_parse("abc", f) == 0);
 assert(bag2_vram_dump_parse("0", f) == 0);
 assert(bag2_vram_dump_parse("300", f) == 1 && f[0] == 300);
 assert(bag2_vram_dump_parse("10,20,30", f) == 3 && f[2] == 30);
 assert(bag2_vram_dump_parse("10,x", f) == 1);
 assert(bag2_vram_dump_parse("1,2,3,4,5,6,7,8,9,10", f) == BAG2_VRAM_DUMP_MAX);
 FILE *t = tmpfile(); assert(t);
 assert(bag2_vram_dump_write(t) == 1 && calls == 1);
 assert(ftell(t) == 1024L * 512L * 2L);
 rewind(t); uint8_t b[4]; assert(fread(b, 1, 4, t) == 4);
 assert(b[0] == 0 && b[1] == 0 && b[2] == 7 && b[3] == 0);
 assert(bag2_vram_dump_write(NULL) == 0 && calls == 1);
 fclose(t); return 0;
}
'''
        (output / 'test.c').write_text(source, encoding='utf-8', newline='\n')
        linux = '/mnt/d/' + output.as_posix()[3:]
        prefix = ['wsl.exe', '-d', 'Ubuntu', '--exec']
        subprocess.run(prefix + ['gcc', '-Wall', '-Wextra', '-Werror', linux + '/test.c', '-o', linux + '/test'], check=True)
        subprocess.run(prefix + [linux + '/test'], check=True)


if __name__ == '__main__':
    unittest.main()
