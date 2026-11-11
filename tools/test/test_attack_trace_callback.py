"""Compile the production input callback with real guarded Gas-O helpers."""
from pathlib import Path
import subprocess
import tempfile
import unittest

from tools.test.test_anim_trace_samples import ROOT, linux_path


class AttackTraceCallbackTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        """Isolate the actual callback; replace only guest memory and environment."""
        cls.directory = tempfile.TemporaryDirectory(dir=ROOT / '_work')
        cls.addClassCleanup(cls.directory.cleanup)
        directory = Path(cls.directory.name)
        text = (ROOT / 'mods-src/bag2jp.debug.anim-trace/bag2jp_anim_trace.c').read_text()
        start = text.index('static void at_attack_input(')
        callback = text[start:text.index('\n}', start) + 2]
        header = linux_path(ROOT / 'mods-src/bag2jp.debug.anim-trace/bag2jp_attack_fixture.h')
        harness = r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
struct CPUState { uint32_t gpr[32]; };
static FILE *s_log;
static int s_on;
static uint32_t s_attack_frame;
static const char *fixture;
static unsigned writes, side, under_attack, wrong_character;
static uint16_t command;
static char *fixture_env(const char *name) {
    return strcmp(name, fixture) == 0 ? "1" : NULL;
}
static uint32_t psx_mod_read_word(uint32_t a) {
    switch (a) {
    case 0x8004E2D8: return 0x54535542;
    case 0x8004E2DC: return 0x4D5F415F;
    case 0x8005D3D4: return 19;
    case 0x8005D2C4: return 2;
    case 0x8005D3D8: return 1;
    case 0x8005D3DC: case 0x8005D3E0: return 3;
    case 0x8009B084: return 0xAC510020;
    case 0x8005E6A0: return wrong_character ? 0 : 9;
    default: return 0;
    }
}
static uint32_t psx_mod_read_byte(uint32_t a) {
    return a == 0x80180000u + side + 0x30u ? under_attack : 0;
}
static uint16_t psx_mod_read_half(uint32_t a) {
    assert(a == 0x8005CF40u); return command;
}
static void psx_mod_write_half(uint32_t a, uint16_t value) {
    uint32_t input = 0x8005CF08u + side * 0x24u;
    if (side == 0) {
        assert((a == input + 8 && value == 0) || (a == input + 12 && value == 0) ||
               (a == input + 20 && value == 0x6e));
    } else {
        assert(a == input + 20 && value == 0);
    }
    writes++;
}
''' + f'#include "{header}"\n#define getenv fixture_env\n' + callback + r'''
int main(int argc, char **argv) {
    assert(argc == 3);
    fixture = argv[1];
    int scenario = atoi(argv[2]);
    s_on = scenario == 0 ? 0 : 1;
    s_log = scenario == 1 ? NULL : stdout;
    side = scenario >= 3 && scenario <= 5 ? 1 : 0;
    under_attack = scenario == 3 || scenario == 4;
    command = scenario == 4 ? 0x6e : 0xaa;
    wrong_character = scenario == 6;
    struct CPUState cpu = {{0}};
    cpu.gpr[20] = side;
    cpu.gpr[21] = 0x8005CF08u + side * 0x24u;
    cpu.gpr[29] = 0x80180000u;
    at_attack_input(&cpu, BAG2_ATTACK_INPUT_SITE);
    unsigned expected = scenario == 2 ? 3 : (scenario == 3 || scenario == 4 ? 1 : 0);
    assert(writes == expected);
    return 0;
}
'''
        source = directory / 'callback.c'
        cls.binary = directory / 'callback'
        source.write_text(harness, encoding='utf-8')
        subprocess.run(['wsl.exe', '-d', 'Ubuntu', '--exec', 'gcc', '-std=c11', '-Wall',
                        '-Werror', linux_path(source), '-o', linux_path(cls.binary)],
                       check=True, capture_output=True)

    def run_scenario(self, fixture: str, scenario: int) -> bytes:
        """Run in a child so a regression's null log cannot kill unittest itself."""
        result = subprocess.run(['wsl.exe', '-d', 'Ubuntu', '--exec', linux_path(self.binary),
                                 'BAG2JP_TEST_' + fixture, str(scenario)], capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors='replace'))
        return result.stdout

    def test_disabled_trace_refuses_every_fixture(self) -> None:
        for fixture in ('GASO_ATTACK', 'HEAT_ATTACK', 'STRIKE_ATTACK', 'HEAT_STRIKE_DUEL', 'ORDERED_DUEL'):
            with self.subTest(fixture=fixture):
                self.assertEqual(self.run_scenario(fixture, 0), b'')

    def test_null_log_refuses_every_fixture(self) -> None:
        for fixture in ('GASO_ATTACK', 'HEAT_ATTACK', 'STRIKE_ATTACK', 'HEAT_STRIKE_DUEL', 'ORDERED_DUEL'):
            with self.subTest(fixture=fixture):
                self.assertEqual(self.run_scenario(fixture, 1), b'')

    def test_gaso_attack_uses_only_native_input_and_discloses_fixture(self) -> None:
        self.assertIn(b'P1 Gas-O attack input 0x6E; not natural play', self.run_scenario('GASO_ATTACK', 2))

    def test_gaso_defense_clears_dodge_and_counter_only_under_attack(self) -> None:
        for scenario in (3, 4):
            with self.subTest(scenario=scenario):
                self.assertIn(b'P2 defense command cleared under Gas-O attack; not natural play',
                              self.run_scenario('GASO_ATTACK', scenario))

    def test_gaso_defense_does_not_clear_when_not_under_attack(self) -> None:
        self.run_scenario('GASO_ATTACK', 5)

    def test_gaso_fixture_refuses_another_character(self) -> None:
        self.run_scenario('GASO_ATTACK', 6)


if __name__ == '__main__':
    unittest.main()
