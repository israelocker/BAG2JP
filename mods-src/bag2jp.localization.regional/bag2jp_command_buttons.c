/* Command buttons (package bag2jp.localization.regional, option command_buttons).
 *
 * The match module (system/005.dbi, base 0x8008F890) draws each dance-command icon in one loop;
 * the CLUT store at 0x80098398 (sh $v0,0xE($s0)) uses the yellow command palette for every face
 * button. The international build gives each face button its own palette row instead. The
 * overlay puts those four rows into unused rows of system/010/005.tim (image slot 4, field
 * 0xD4 of the command-bar image table at 0x80054C44); this hook redirects the CLUT to them.
 * Applied at game start only: the palette rows come from a disc overlay with the same option.
 * Icon kind is known from the texture coordinates chosen just before: $s5 = u, $s4 = v. */
#include <stdint.h>
#include <string.h>
#include "mod_plugins.h"
#include "cpu_state.h"

#define CB_SITE   0x80098398u        /* sh $v0, 0xE($s0) */
#define CB_WORD   0xA602000Eu
#define CB_TABLE  0x80054C44u        /* +0xE/+0xF: u/v base; +0xD4: CLUT of 010/005.tim */

static int cb_active;

static void cb_activate(void) {
    char v[32] = {0};
    cb_active = psx_mod_current_option_value("command_buttons", v, sizeof v) > 0 &&
                strcmp(v, "international") == 0;
}

static void cb_hook(struct CPUState* cpu, uint32_t address) {
    (void)address;
    if (!cb_active) return;
    const uint32_t ub = psx_mod_read_byte(CB_TABLE + 0xE), vb = psx_mod_read_byte(CB_TABLE + 0xF);
    if (((cpu->gpr[20] - vb) & 0xFF) != 0x40) return;               /* $s4: face-button row */
    unsigned row;
    switch ((cpu->gpr[21] - ub) & 0xFF) {                             /* $s5 */
    case 0x80: row = 13; break;   /* Circle   -> red   */
    case 0x96: row = 12; break;   /* Square   -> pink  */
    case 0xAC: row = 7;  break;   /* Triangle -> green */
    case 0xC2: row = 11; break;   /* Cross    -> blue  */
    default: return;               /* 0xD8 = Right arrow: unchanged */
    }
    cpu->gpr[2] = (uint32_t)(psx_mod_read_half(CB_TABLE + 0xD4) + (row << 6));
}

PSX_MOD_CONSTRUCTOR(bag2jp_register_command_buttons) {
    (void)psx_mod_register_activation_plugin("bag2jp.command_buttons", cb_activate);
    (void)psx_mod_register_instruction_plugin("bag2jp.command_buttons", CB_SITE, CB_WORD, cb_hook);
}
