"""Compile the actual score fixture seam and exercise every write guard."""
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class ScoreFixtureTests(unittest.TestCase):
    """Only an explicitly opted-in, verified Heat mirror may receive scores."""

    def test_instruction_callback_signature_and_opt_in(self) -> None:
        """Compile the real adapter with its two-argument API and trace/env gates."""
        output = ROOT / '_work/character_import/heat/fever_exit/score-guard-tests'
        output.mkdir(parents=True, exist_ok=True)
        plugin = (ROOT / 'mods-src/bag2jp.debug.anim-trace/bag2jp_anim_trace.c').read_text()
        callback = plugin[plugin.index('static void at_duet_rng('):plugin.index('/* BAG2JP_WATCH=')]
        source = '''#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
struct CPUState;
typedef void (*PSXModFunctionEntryCallback)(struct CPUState*,uint32_t);
#define BAG2_FIXTURE_RNG_CALL_ADDR 0x8009CDB8u
static int s_on, calls;
static FILE* s_log;
static int bag2_duet_rng_fixture_tick(int enabled) {assert(enabled==1);++calls;return 1;}
''' + callback + '''
int main(void) {
 PSXModFunctionEntryCallback cb=at_duet_rng;
 setenv("BAG2JP_TEST_P1_DUET","1",1);s_on=1;s_log=tmpfile();assert(s_log);
 cb(NULL,0);assert(calls==0);
 s_on=0;cb(NULL,BAG2_FIXTURE_RNG_CALL_ADDR);assert(calls==0);s_on=1;
 FILE* file=s_log;s_log=NULL;cb(NULL,BAG2_FIXTURE_RNG_CALL_ADDR);assert(calls==0);s_log=file;
 unsetenv("BAG2JP_TEST_P1_DUET");cb(NULL,BAG2_FIXTURE_RNG_CALL_ADDR);assert(calls==0);
 setenv("BAG2JP_TEST_P1_DUET","10",1);cb(NULL,BAG2_FIXTURE_RNG_CALL_ADDR);assert(calls==0);
 setenv("BAG2JP_TEST_P1_DUET","1",1);cb(NULL,BAG2_FIXTURE_RNG_CALL_ADDR);assert(calls==1);
 fclose(s_log);return 0;
}
'''
        (output / 'callback_test.c').write_text(source, encoding='utf-8', newline='\n')
        linux_output = '/mnt/d/' + output.as_posix()[3:]
        prefix = ['wsl.exe', '-d', 'Ubuntu', '--exec']
        subprocess.run(prefix + ['gcc', '-Wall', '-Wextra', '-Werror',
                                linux_output + '/callback_test.c', '-o', linux_output + '/callback_test'], check=True)
        subprocess.run(prefix + [linux_output + '/callback_test'], check=True)

    def test_native_guards_and_score_only_writes(self) -> None:
        """Reject each wrong region/module/phase/actor before any RAM write."""
        output = ROOT / '_work/character_import/heat/fever_exit/score-guard-tests'
        output.mkdir(parents=True, exist_ok=True)
        source = output / 'test.c'
        header = ROOT / 'mods-src/bag2jp.debug.anim-trace/bag2jp_score_fixture.h'
        linux_header = '/mnt/d/' + header.as_posix()[3:]
        source.write_text('''#include <stdint.h>
#include <stdlib.h>
#include <assert.h>
static int bad, writes;
static const uint32_t guards[][2] = {
 {0x8004E2D8,0x54535542}, {0x8004E2DC,0x4D5F415F},
 {0x8005D3D4,19}, {0x8005D2C4,2}, {0x8005D3D8,1},
 {0x8005D3DC,3}, {0x8005D3E0,3},
 {0x8005E6A0,0}, {0x8005E6A4,0}, {0x8005E668,0x100},
 {0x80098C44,0x284203E8}
};
uint32_t psx_mod_read_word(uint32_t address) {
 for (int i=0; i<11; ++i) if (address==guards[i][0])
  return guards[i][1] ^ (bad==i+1 ? 1 : 0);
 assert(0 && "Unexpected fixture read"); return 0;
}
void psx_mod_write_word(uint32_t address,uint32_t value) {
  assert((address==0x8005E6F8 && value==500000) ||
        (address==0x8005E6FC && value==500100));
 ++writes;
}
''' + f'#include "{linux_header}"\n' + '''
int main(int argc,char**argv) {
 (void)&bag2_duet_rng_fixture_tick;
 assert(argc==2); bad=atoi(argv[1]);
 int applied=bag2_score_fixture_tick(bad!=12);
 assert(writes==(bad==0 ? 2 : 0));
 assert(applied==(bad==0));
 return 0;
}
''', encoding='utf-8', newline='\n')
        linux_output = '/mnt/d/' + output.as_posix()[3:]
        prefix = ['wsl.exe', '-d', 'Ubuntu', '--exec']
        subprocess.run(prefix + ['gcc', '-Wall', '-Wextra', '-Werror',
                                linux_output + '/test.c', '-o', linux_output + '/test'], check=True)
        for case in range(13):
            with self.subTest(case=case):
                subprocess.run(prefix + [linux_output + '/test', str(case)], check=True,
                               capture_output=True, text=True)

    def test_rng_seed_only_at_verified_duet_call(self) -> None:
        """Reject disabled/wrong-phase/modified-code cases before seed writes."""
        output = ROOT / '_work/character_import/heat/fever_exit/score-guard-tests'
        output.mkdir(parents=True, exist_ok=True)
        header = '/mnt/d/' + (ROOT / 'mods-src/bag2jp.debug.anim-trace/bag2jp_score_fixture.h').as_posix()[3:]
        source = '''#include <stdint.h>
#include <assert.h>
static int bad, writes;
static const uint32_t expected[][2] = {
 {0x8004E2D8,0x54535542}, {0x8004E2DC,0x4D5F415F},
 {0x8005D3D4,19}, {0x8005D2C4,2}, {0x8005D3D8,1},
 {0x8005D3DC,7}, {0x8005D3E0,1}, {0x8005E6A0,0},
 {0x8005E6A4,0}, {0x8005E668,0x100}, {0x8005E6C0,2},
 {0x8009CDB8,0x0C0127C9}, {0x8009CE20,0x244200B4},
 {0x8009CE24,0x02221021},
 {0x80049F24,0x240A00A0}, {0x80049F28,0x01400008},
 {0x80049F2C,0x2409002F},
 {0xBFC060E4,0x3C030001}, {0xBFC060E8,0x8C648548},
 {0xBFC060EC,0x3C0241C6}, {0xBFC060F0,0x24424E6D},
 {0xBFC060F4,0x00820018}, {0xBFC060F8,0x00001012},
 {0xBFC060FC,0x24423039}, {0xBFC06100,0xAC628548},
 {0xBFC06104,0x00021402}, {0xBFC06108,0x03E00008},
 {0xBFC0610C,0x30427FFF}
};
uint32_t psx_mod_read_word(uint32_t address) {
 for (unsigned i=0;i<sizeof(expected)/sizeof(expected[0]);++i)
  if (address==expected[i][0]) return expected[i][1] ^ (bad==(int)i+1 ? 1 : 0);
 assert(0 && "Unexpected RNG fixture read"); return 0;
}
void psx_mod_write_word(uint32_t address,uint32_t value) {
 assert(address==0x00008548 && value==1); ++writes;
}
''' + f'#include "{header}"\n' + '''
int main(void) {
 (void)&bag2_score_fixture_tick;
 unsigned rand_value=((1u*0x41C64E6Du+0x3039u)>>16)&0x7FFFu;
 assert(rand_value==16838 && rand_value%3==2);
 assert(!bag2_duet_rng_fixture_tick(0)); assert(writes==0);
 for (bad=1;bad<=(int)(sizeof(expected)/sizeof(expected[0]));++bad) {
  assert(!bag2_duet_rng_fixture_tick(1)); assert(writes==0);
 }
 bad=0; assert(bag2_duet_rng_fixture_tick(1)); assert(writes==1);
 return 0;
}
'''
        (output / 'rng_test.c').write_text(source, encoding='utf-8', newline='\n')
        linux_output = '/mnt/d/' + output.as_posix()[3:]
        prefix = ['wsl.exe', '-d', 'Ubuntu', '--exec']
        subprocess.run(prefix + ['gcc', '-Wall', '-Wextra', '-Werror',
                                linux_output + '/rng_test.c', '-o', linux_output + '/rng_test'], check=True)
        subprocess.run(prefix + [linux_output + '/rng_test'], check=True)


if __name__ == '__main__':
    unittest.main()
