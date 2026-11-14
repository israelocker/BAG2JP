"""Exercise the real stage shim with host RAM, without media dependencies."""
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class StageShimTests(unittest.TestCase):
    def test_audited_stage_ids_receive_flags_and_level(self):
        package = ROOT / 'mods-src/bag2jp.feature.bag1-content'
        source = (package / 'bag2jp_bag1_stage.c').read_text()
        shim = source[source.index('#define B1S_SHIM'):source.index('/* ---- song audio ---- */')]
        # The real Gas-O stage detection: its DF2_ defines, alternate-entry index and lookup.
        versions = (package / 'bag2jp_bag1_versions.c').read_text()
        table_defines = '\n'.join(line for line in versions.splitlines()
                                  if line.startswith(('#define B1V_TABLE', '#define B1V_MAGIC')))
        entry_lookup = versions[versions.index('int bag2jp_bag1_offset_is_alt(unsigned entry, uint32_t offset) {'):
                                versions.index('int bag2jp_bag1_get_version(int chr, int side) {')]
        alt_index = (package / 'bag2jp_bag1_alt_index.h').read_text()
        out = ROOT / '_work/stage_import/strike/shim-tests'
        out.mkdir(parents=True, exist_ok=True)
        harness = '''#include <stdint.h>
#include <assert.h>
#include <string.h>
static uint8_t ram[0x800000];
#define RAM(a) (ram+((a)&0x7fffff))
uint8_t psx_mod_read_byte(uint32_t a) { return *RAM(a); }
uint16_t psx_mod_read_half(uint32_t a) { uint16_t v; memcpy(&v,RAM(a),2); return v; }
uint32_t psx_mod_read_word(uint32_t a) { uint32_t v; memcpy(&v,RAM(a),4); return v; }
void psx_mod_write_byte(uint32_t a,uint8_t v) { *RAM(a)=v; }
void psx_mod_write_word(uint32_t a,uint32_t v) { memcpy(RAM(a),&v,4); }
void psx_mod_write_half(uint32_t a,uint16_t v) { memcpy(RAM(a),&v,2); }
void half(uint32_t a,uint16_t v) { memcpy(RAM(a),&v,2); }
''' + table_defines + '\n' + alt_index + '\n' + entry_lookup + '\n' + shim + '''
#define FAN_ANGLE 0x801DECC0u
#define FAN_SPEED 0x801DECC2u
static const B1AltEntry* gaso_stage(void) {
  for (unsigned i=0;i<sizeof b1_alt_entries/sizeof b1_alt_entries[0];i++)
    if (b1_alt_entries[i].entry==B1S_GASO_STAGE_ENTRY) return &b1_alt_entries[i];
  assert(!"entry 197 missing from the alternate-entry index");
  return 0;
}
/* Fresh RAM with a resident ported DBI, a running fan and the plugin's frame state reset. */
static void setup(unsigned id, uint32_t entry197) {
  memset(ram,0,sizeof ram); b1s_vblank();
  psx_mod_write_word(B1S_SHIM,B1S_MAGIC);
  psx_mod_write_word(0x80089200,0x80200000);
  psx_mod_write_byte(0x80200000,id);
  psx_mod_write_word(B1V_TABLE,B1V_MAGIC);
  psx_mod_write_word(B1V_TABLE+4,400);
  psx_mod_write_word(B1V_TABLE+8+8*B1S_GASO_STAGE_ENTRY,entry197);
  half(0x8005e2e8,256); half(0x8005e658,100);
  half(0x8005e2d0,1); psx_mod_write_word(0x8005e6f8,20000);
  half(FAN_ANGLE,0x1234); half(FAN_SPEED,0x0567);
}
/* Two gameplay frames: match start, then a beat that opens a bar. */
static void play_bar_start(void) {
  psx_mod_write_word(0x8005d3d4u,0x13u);
  b1s_vblank();
  half(0x8005e2d0,2); half(0x8005e684,2); b1s_vblank();
}
static void assert_untouched(void) {
  assert(psx_mod_read_word(B1S_SHIM+4)==0xDEADBEEFu);
  assert(psx_mod_read_byte(B1S_SHIM+8)==0x77);
  assert(psx_mod_read_half(FAN_ANGLE)==0x1234);
  assert(psx_mod_read_half(FAN_SPEED)==0x0567);
}
int main(void) {
  /* The real lookup the HUD load latch uses: each Gas-O pack listed once, BAG1 offsets only. */
  const unsigned packs[] = {53u, 54u, 125u, 126u};
  for (unsigned p=0;p<4;p++) {
    const B1AltEntry* pack = 0;
    for (unsigned i=0;i<sizeof b1_alt_entries/sizeof b1_alt_entries[0];i++)
      if (b1_alt_entries[i].entry==packs[p]) { assert(!pack); pack=&b1_alt_entries[i]; }
    assert(pack && pack->alt_off!=pack->off);
    assert(bag2jp_bag1_offset_is_alt(packs[p],pack->alt_off));
    assert(!bag2jp_bag1_offset_is_alt(packs[p],pack->off));
    if (pack->jp_size) assert(bag2jp_bag1_offset_is_alt(packs[p],pack->jp_off));
    assert(!bag2jp_bag1_offset_is_alt(packs[p]+1u-2u*(p&1u),pack->alt_off)); /* other player's pack */
  }
  const B1AltEntry* gaso = gaso_stage();
  for (unsigned id=0;id<3;id++) {
    setup(id,gaso->alt_off);
    b1s_vblank();
    /* Non-gameplay root: vblank must do nothing */
    assert(psx_mod_read_byte(B1S_SHIM+8)==0);
    assert(psx_mod_read_word(B1S_SHIM+4)==0);
    /* Gameplay root: vblank processes beats and score */
    play_bar_start();
    assert(psx_mod_read_byte(B1S_SHIM+8)==(id<2?2:0));
    assert(psx_mod_read_word(B1S_SHIM+4)==(id<2?0x11:0));
    assert(psx_mod_read_byte(B1S_SHIM+9)==0);
    /* Only the Gas-O stage owns the fan words. */
    assert(psx_mod_read_half(FAN_ANGLE)==0x1234);
    assert(psx_mod_read_half(FAN_SPEED)==0x0567);
  }
  /* Stage 9 with the BAG1 stage (international and, when present, JP file): flags, level and a
   * stationary fan at match start. */
  for (unsigned jp=0;jp<2;jp++) {
    if (jp && !gaso->jp_size) continue;
    setup(9u,jp?gaso->jp_off:gaso->alt_off);
    play_bar_start();
    assert(psx_mod_read_byte(B1S_SHIM+8)==2);
    assert(psx_mod_read_word(B1S_SHIM+4)==0x11);
    assert(psx_mod_read_byte(B1S_SHIM+9)==0);
    assert(psx_mod_read_half(FAN_ANGLE)==0);
    assert(psx_mod_read_half(FAN_SPEED)==0);
    /* Song over (beats left 0) sets bit 6 without a new beat. */
    half(0x8005e658,0); b1s_vblank();
    assert(psx_mod_read_word(B1S_SHIM+4)==0x40);
    /* Leaving gameplay and starting again resets level and fan once more. */
    half(FAN_SPEED,0x0300);
    psx_mod_write_word(0x8005d3d4u,0x05u); b1s_vblank();
    psx_mod_write_word(0x8005e6f8,0); half(0x8005e658,100);
    psx_mod_write_word(0x8005d3d4u,0x13u); b1s_vblank();
    assert(psx_mod_read_byte(B1S_SHIM+8)==0);
    assert(psx_mod_read_half(FAN_SPEED)==0);
  }
  /* Stage 9 must leave everything alone when the BAG1 stage is not resident or not selected:
   * stock Bi-O file, any other offset, entry missing, or no 'B1ST' in the loaded DBI. */
  const uint32_t not_gaso[] = {gaso->off, gaso->alt_off + 0x800u, 0u};
  for (unsigned i=0;i<4;i++) {
    setup(9u,i<3?not_gaso[i]:gaso->alt_off);
    if (i==3) psx_mod_write_word(B1S_SHIM,0);
    psx_mod_write_word(B1S_SHIM+4,0xDEADBEEFu); psx_mod_write_byte(B1S_SHIM+8,0x77);
    play_bar_start();
    assert_untouched();
  }
  return 0;
}
'''
        (out / 'shim.c').write_text(harness)
        # Convert Windows path D:\... to WSL /mnt/d/...
        win_path = str(out)
        if len(win_path) >= 2 and win_path[1] == ':':
            drive = win_path[0].lower()
            rest = win_path[2:].replace('\\', '/')
            path = f'/mnt/{drive}/{rest}'
        else:
            path = win_path
        subprocess.run(['wsl.exe', '-d', 'Ubuntu', '--exec', 'gcc', '-std=c11', '-Wall',
                        '-Werror', f'{path}/shim.c', '-o', f'{path}/shim'], check=True)
        subprocess.run(['wsl.exe', '-d', 'Ubuntu', '--exec', f'{path}/shim'], check=True)
