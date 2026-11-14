"""Exercise the actual native-init callback and its BAG1 selection seam."""
from pathlib import Path
import subprocess
import tempfile
import tomllib
import unittest

from tools.test.test_bag1_leash import ROOT, linux_path


class Bag1HomeTest(unittest.TestCase):
    def test_native_callback_only_changes_selected_main_bag1_stack_x(self) -> None:
        """Compile production selection/callback with the real RAM-backed helpers."""
        source = (ROOT / 'mods-src/bag2jp.feature.bag1-content/bag2jp_bag1_versions.c').read_text()
        selection = source[source.index('static uint32_t b1v_bag1_dancer('):
                           source.index('static void b1v_dancer_scale(')]
        callback = source[source.index('static void b1v_home_hook('):
                          source.index('/* Native update seam:')]
        prefix = r'''
#define B1V_DANCERS 0x8005F808u
#define B1V_SELECTED 0x80089250u
#define B1V_CHARS 18
#define B1V_CHAR_MASK 31u
struct CPUState { uint32_t gpr[32]; };
static int b1v_active = 1, b1v_force_stock, b1v_version[18][2];
static uint8_t psx_mod_read_byte(uint32_t a) {
    assert(a >= BASE && a < BASE + SIZE); return ram[a - BASE];
}
static int b1v_has_alt(uint32_t c) { return c == 0 || c == 1 || c == 9; }
#define b1v_log(...) ((void)0)
'''
        scenario = r'''
int main(void) {
    for (int side=0; side<2; ++side) {
        const int slot = side*2;
        memset(ram,0,sizeof ram);
        init_ctl(slot,side ? 520 : -520,440);
        put_word(0x80051918u,0x82828282u);
        put_word(DANCER[slot]+4u,9u+(uint32_t)side*256u);
        put_word(B1V_DANCERS+4u*(uint32_t)slot,DANCER[slot]);
        ram[B1V_SELECTED-BASE+(uint32_t)side]=9;
        b1v_version[9][side]=1;
        put_word(B1HOME_MODE,2);
        struct CPUState cpu={{0}};
        cpu.gpr[29]=0x8010A000u; cpu.gpr[6]=cpu.gpr[29]+16u;
        cpu.gpr[4]=cpu.gpr[18]=CTL[slot];
        cpu.gpr[5]=cpu.gpr[17]=DANCER[slot];
        struct CPUState before=cpu;
        put_word(cpu.gpr[6],(uint32_t)(side ? 520 : -520));
        put_word(cpu.gpr[6]+4u,123u); writes=0;
        b1v_home_hook(&cpu,B1HOME_SITE);
        assert(writes==1 && (int32_t)psx_mod_read_word(cpu.gpr[6])==(side ? 870 : -870));
        assert(memcmp(&before,&cpu,sizeof cpu)==0 && psx_mod_read_word(cpu.gpr[6]+4u)==123u);
        for (unsigned i=0;i<15;++i) {
            cpu=before; b1v_active=1; b1v_force_stock=0; b1v_version[9][side]=1;
            put_word(before.gpr[6],(uint32_t)(side ? 520 : -520));
            if(i==0) b1v_active=0;
            if(i==1) b1v_force_stock=1;
            if(i==2) b1v_version[9][side]=0;
            if(i==3) cpu.gpr[4]+=0x4Cu;
            if(i==4) cpu.gpr[5]+=4u;
            if(i==5) cpu.gpr[6]+=4u;
            if(i==6) cpu.gpr[29]=0x807FFFF0u;
            if(i==7) cpu.gpr[17]+=4u;
            if(i==9) cpu.gpr[18]+=0x4Cu;
            if(i==10) { cpu.gpr[29]+=2u; cpu.gpr[6]=cpu.gpr[29]+16u; }
            if(i==11) { cpu.gpr[29]=0x8000FFF0u; cpu.gpr[6]=cpu.gpr[29]+16u; }
            if(i==12) { cpu.gpr[4]+=0x4Cu; cpu.gpr[18]=cpu.gpr[4]; }
            if(i==13) put_word(B1V_DANCERS+4u*(uint32_t)slot,0x807FFFFCu);
            if(i==14) put_word(B1V_DANCERS+4u*(uint32_t)slot,0x80100001u);
            writes=0;
            struct CPUState guard=cpu;
            b1v_home_hook(&cpu,i==8 ? B1HOME_SITE+4u : B1HOME_SITE);
            assert(writes==0 && memcmp(&guard,&cpu,sizeof cpu)==0);
            put_word(B1V_DANCERS+4u*(uint32_t)slot,DANCER[slot]);
        }
        b1v_active=1; b1v_force_stock=0; b1v_version[9][side]=1;
    }
    return 0;
}
'''
        harness = (ROOT / 'tools/test/bag1_leash_harness.c').read_text()
        text = '#define main leash_main\n' + harness + '\n#undef main\n' + prefix + selection + callback + scenario
        with tempfile.TemporaryDirectory(dir=ROOT / '_work') as temporary:
            folder = Path(temporary)
            path = folder / 'home.c'
            path.write_text(text, encoding='utf-8')
            subprocess.run(['wsl.exe', '-d', 'Ubuntu', '--exec', 'gcc', '-std=c11',
                            '-Wall', '-Wextra', '-Werror',
                            '-I' + linux_path(ROOT / 'mods-src/bag2jp.feature.bag1-content'),
                            linux_path(path), '-o', linux_path(folder / 'home')],
                           check=True, capture_output=True)
            result = subprocess.run(['wsl.exe', '-d', 'Ubuntu', '--exec', linux_path(folder / 'home')],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_init_site_matches_native_executable_and_registration(self) -> None:
        """Pin the JAL, argument vector and registry rather than a copied address."""
        exe = (ROOT / 'SLPM_862.19').read_bytes()
        base = int.from_bytes(exe[0x18:0x1c], 'little')
        for address, expected in ((0x8002BA14, 0x27A60010), (0x8002BA18, 0x0C00B617)):
            offset = 0x800 + address - base
            self.assertEqual(int.from_bytes(exe[offset:offset+4], 'little'), expected)
        source = (ROOT / 'mods-src/bag2jp.feature.bag1-content/bag2jp_bag1_versions.c').read_text()
        self.assertIn('B1HOME_SITE, B1HOME_WORD, b1v_home_hook)', source)
        self.assertRegex(source, r'#define B1V_CHARS\s+18\b')
        config = tomllib.loads((ROOT / 'patches/BAG2JP-game.toml').read_text())
        self.assertIn('0x8002BA18', config['recompiler']['mod_instruction_sites'])


if __name__ == '__main__':
    unittest.main()
