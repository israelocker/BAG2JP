/* Static title plugins for BAG2JP (Bust A Move 2: Dance Tengoku Mix, SLPM-86219).
 * Widescreen on PSX is mod-owned: the runtime only widens the display when a
 * trusted title plugin selects the aspect (psxrecomp docs/WIDESCREEN.md).
 * The package mods/preloaded/packages/bag2jp.enhancement.widescreen enables it. */
#include "mod_plugins.h"
#include "cpu_state.h"

static void bag2jp_widescreen_activate(void) {
    /* Native-wide 16:9: the GTE projects more world at the sides; 2D frames
     * (menus, FMV, BIOS) stay 4:3 via the [widescreen] keys in game.toml. */
    (void)psx_mod_set_fixed_display_aspect(16u, 9u);
    (void)psx_mod_set_widescreen_hud_size(0);
}

PSX_MOD_CONSTRUCTOR(bag2jp_register_plugins) {
    (void)psx_mod_register_activation_plugin("bag2jp.widescreen", bag2jp_widescreen_activate);
}

/* ---------------------------------------------------------------- autoplay
 * Game module system/005.dbi is loaded at 0x8008F890 (= *(0x80010CE0)) for every
 * match. mode = 0x8005D2C4 (0 demo, 1 one-player, 2 two-player),
 * human_player = 0x8005E6C8, CPU dancer state = 0x8005CF08 + p*0x24.
 *
 * Three things make player p a CPU dancer; autoplay applies them to the human
 * player in one-player mode (two-player mode uses register hooks, see below):
 *
 * 1. Input source, per frame (0x8009A994..): s1/s2 = "player reads the pad".
 *      0x8009A9A4 bnez human, skip   ; human==0 -> P1 reads pad
 *      0x8009A9CC beqz human, skip   ; human==1 -> P2 reads pad
 *    Both become unconditional "b skip", so in mode 1 nobody reads the pad and
 *    FUN_80099c0c (the CPU input generator) drives both dancers. Mode 2 sets the
 *    flags through its own branch and is unaffected.
 * 2. Per-measure setup: 0x8009ADC8 beq $s4,$v0 (p == human -> skip CPU path)
 *    becomes a nop so the human gets the CPU timing/judgement setup too.
 * 3. Fumbles: FUN_80099c0c rolls rand() % ((skill+50)*8) == 0 each tick and
 *    sets step = -1 (a miss). An instruction hook on 0x80099CD0 cancels that for
 *    the human player only; the real CPU opponent keeps its behaviour.
 *
 * The module is reloaded from disc each match, so the words are re-patched
 * whenever the stock code is back, and only when every guard word matches. */
typedef struct { uint32_t address, stock, patched; } ApPatch;
static const ApPatch ap_patches[] = {
    {0x8009A9A4u, 0x14400003u, 0x10000003u},  /* bnez $v0,+3 -> b +3 */
    {0x8009A9CCu, 0x10400004u, 0x10000004u},  /* beqz $v0,+4 -> b +4 */
    {0x8009ADC8u, 0x128200AEu, 0x00000000u},  /* beq $s4,$v0 -> nop  */
};
static const uint32_t ap_guard[][2] = {
    {0x8009A99Cu, 0x8042E6C8u},  /* lb   $v0, human_player  */
    {0x8009A9ACu, 0x24110001u},  /* addiu $s1, $zero, 1     */
    {0x8009A9C4u, 0x8042E6C8u},  /* lb   $v0, human_player  */
    {0x8009A9D4u, 0x24120001u},  /* addiu $s2, $zero, 1     */
    {0x8009ADA4u, 0x85A2D2C4u},  /* lh   $v0, mode          */
    {0x8009ADB4u, 0x145100B3u},  /* bne  $v0, $s1, ...      */
    {0x8009ADC0u, 0x8042E6C8u},  /* lb   $v0, human_player  */
    {0x8009ADCCu, 0x03B21021u},  /* addu $v0, $sp, $s2      */
};
#define AP_COUNT(a) (sizeof (a) / sizeof (a)[0])

/* Live switch: option "active" of feature "autoplay". The in-game menu (F10 /
 * Ctrl+L -> Mods) changes it on a running game; the vblank plugin then patches
 * or restores the stock code within one frame. */
#define AP_PACKAGE "bag2jp.feature.autoplay"
#define AP_FEATURE "autoplay"
static volatile int ap_active = 1;
/* Two-player mode (testing): bit 0 = P1, bit 1 = P2 dance by themselves (options p1_2p / p2_2p). */
static volatile unsigned ap_2p_mask = 0;

static int ap_bool_option(const char* id, int fallback) {
    char value[16] = {0};
    if (psx_mod_option_value(AP_PACKAGE, AP_FEATURE, id, value, sizeof value) > 0)
        return !(value[0] == 'f' || value[0] == '0');
    return fallback;
}
static void ap_read_option(void) {
    ap_active = ap_bool_option("active", ap_active);
    ap_2p_mask = (ap_bool_option("p1_2p", 0) ? 1u : 0u) | (ap_bool_option("p2_2p", 0) ? 2u : 0u);
}
static void bag2jp_autoplay_activate(void) { ap_read_option(); }
static int bag2jp_autoplay_option_changed(const char* option_id, const char* value) {
    (void)option_id; (void)value;
    ap_read_option();
    return 1;
}

static int ap_guards_ok(void) {
    for (unsigned i = 0; i < AP_COUNT(ap_guard); ++i)
        if (psx_mod_read_word(ap_guard[i][0]) != ap_guard[i][1]) return 0;
    return 1;
}

/* In-game hotkey: hold Select and press R1 on controller 1 (keyboard default:
 * Right Shift + W). Reads the game's own pad state (0x8005E870 = P1 held
 * buttons, PsyQ bit layout: Select 0x0100, R1 0x0008). Session only; the
 * launcher's "Active" checkbox sets the state at start. */
#define AP_PAD_HELD   0x8005E870u
#define AP_BTN_SELECT 0x0100u
#define AP_BTN_R1     0x0008u
static int ap_combo_was;

static void ap_poll_hotkey(void) {
    const uint16_t held = psx_mod_read_half(AP_PAD_HELD);
    const int combo = (held & (AP_BTN_SELECT | AP_BTN_R1)) == (AP_BTN_SELECT | AP_BTN_R1);
    if (combo && !ap_combo_was) {
        ap_active = !ap_active;
        psx_mod_counter_add(ap_active ? "bag2jp.autoplay.hotkey_on" : "bag2jp.autoplay.hotkey_off", 1);
    }
    ap_combo_was = combo;
}

static void bag2jp_autoplay_vblank(void) {
    ap_poll_hotkey();
    const int active = ap_active;
    unsigned stock = 0, patched = 0;
    for (unsigned i = 0; i < AP_COUNT(ap_patches); ++i) {
        const uint32_t w = psx_mod_read_word(ap_patches[i].address);
        if (w == ap_patches[i].stock) ++stock;
        else if (w == ap_patches[i].patched) ++patched;
        else return;                                    /* some other code is resident */
    }
    if (active ? stock == 0 : patched == 0) return;     /* already in the wanted state */
    if (!ap_guards_ok()) return;
    for (unsigned i = 0; i < AP_COUNT(ap_patches); ++i) {
        const uint32_t want = active ? ap_patches[i].patched : ap_patches[i].stock;
        if (psx_mod_read_word(ap_patches[i].address) != want)
            psx_mod_write_code_word(ap_patches[i].address, want);
    }
    psx_mod_counter_add(active ? "bag2jp.autoplay.patched" : "bag2jp.autoplay.restored", 1);
}

#define AP_FUMBLE_SITE  0x80099CD0u   /* bgtz $v1,+2 : skip "cpu->step = -1" */
#define AP_FUMBLE_WORD  0x1C600002u
#define AP_CPU_BASE     0x8005CF08u
#define AP_CPU_STRIDE   0x24u
#define AP_MODE_ADDR    0x8005D2C4u
#define AP_HUMAN_ADDR   0x8005E6C8u
static void bag2jp_autoplay_no_fumble(struct CPUState* cpu, uint32_t address) {
    (void)address;
    const int16_t mode = (int16_t)psx_mod_read_half(AP_MODE_ADDR);
    uint32_t p;
    if (mode == 1) {
        if (!ap_active) return;
        p = psx_mod_read_byte(AP_HUMAN_ADDR) & 1u;
        if (cpu->gpr[19] != AP_CPU_BASE + p * AP_CPU_STRIDE) return;  /* $s3 */
    } else if (mode == 2) {
        p = (cpu->gpr[19] - AP_CPU_BASE) / AP_CPU_STRIDE;
        if (p > 1 || !(ap_2p_mask & (1u << p))) return;
    } else {
        return;
    }
    if ((int32_t)cpu->gpr[3] <= 0) {                                   /* $v1 */
        cpu->gpr[3] = 1;
        psx_mod_counter_add("bag2jp.autoplay.fumble_blocked", 1);
    }
}

/* ------------------------------------------------ two-player autoplay (testing)
 * Mode 2 takes its own branches, so it is done with register hooks (the module code is shared by
 * all modes and a word patch would also change one-player games with P2 as the human):
 * - 0x8009A9DC (after the "who reads the pad" flags, reached in mode 2): clear $s1 (P1) / $s2 (P2)
 *   for autoplayed players and keep $a2 = $s2 like the stock code.
 * - 0x8009ADB4 bne $v0(mode),$s1(1): per-measure CPU setup is skipped for every player in mode 2;
 *   for an autoplayed player ($s4 = player) make it fall through ($v0 = 1) ...
 * - 0x8009ADC8 beq $s4,$v0(human): ... and not match the human byte ($v0 = $s4 ^ 1).
 * That per-measure path also holds the CPU attack choice, so autoplayed 2P dancers would attack;
 * 0x8009AFE0 hides their attack stock from it (bag2jp_ap2_no_attack.h). */
#define AP2_PAD_SITE   0x8009A9DCu
#define AP2_PAD_WORD   0x3C038006u   /* lui $v1, 0x8006 */
#define AP2_SETUP_SITE 0x8009ADB4u
#define AP2_SETUP_WORD 0x145100B3u
#define AP2_HUMAN_SITE 0x8009ADC8u
#define AP2_HUMAN_WORD 0x128200AEu
static int ap2_on(void) { return ap_2p_mask && (int16_t)psx_mod_read_half(AP_MODE_ADDR) == 2; }
static void ap2_pad_hook(struct CPUState* cpu, uint32_t address) {
    (void)address;
    if (!ap2_on()) return;
    if (ap_2p_mask & 1u) cpu->gpr[17] = 0;   /* $s1 */
    if (ap_2p_mask & 2u) cpu->gpr[18] = 0;   /* $s2 */
    cpu->gpr[6] = cpu->gpr[18];              /* $a2 = $s2 */
}
static void ap2_setup_hook(struct CPUState* cpu, uint32_t address) {
    (void)address;
    if (!ap2_on()) return;
    const uint32_t p = cpu->gpr[20] & 1u;    /* $s4 */
    if (ap_2p_mask & (1u << p)) cpu->gpr[2] = cpu->gpr[17];   /* $v0 = $s1 -> fall through */
}
static void ap2_human_hook(struct CPUState* cpu, uint32_t address) {
    (void)address;
    if (!ap2_on()) return;
    const uint32_t p = cpu->gpr[20] & 1u;
    if (ap_2p_mask & (1u << p)) cpu->gpr[2] = p ^ 1u;
}
#include "bag2jp_ap2_no_attack.h"
static void ap2_attack_hook(struct CPUState* cpu, uint32_t address) {
    if (ap2_on() && ap2_block_attack(cpu, address, ap_2p_mask))
        psx_mod_counter_add("bag2jp.autoplay.attack_blocked", 1);
}

PSX_MOD_CONSTRUCTOR(bag2jp_register_autoplay) {
    (void)psx_mod_register_instruction_plugin("bag2jp.autoplay", AP2_PAD_SITE, AP2_PAD_WORD, ap2_pad_hook);
    (void)psx_mod_register_instruction_plugin("bag2jp.autoplay", AP2_SETUP_SITE, AP2_SETUP_WORD, ap2_setup_hook);
    (void)psx_mod_register_instruction_plugin("bag2jp.autoplay", AP2_HUMAN_SITE, AP2_HUMAN_WORD, ap2_human_hook);
    (void)psx_mod_register_instruction_plugin("bag2jp.autoplay", AP2_ATTACK_SITE, AP2_ATTACK_WORD, ap2_attack_hook);
    (void)psx_mod_register_activation_plugin("bag2jp.autoplay", bag2jp_autoplay_activate);
    (void)psx_mod_register_option_changed_plugin("bag2jp.autoplay", bag2jp_autoplay_option_changed);
    (void)psx_mod_register_vblank_plugin("bag2jp.autoplay", bag2jp_autoplay_vblank);
    (void)psx_mod_register_instruction_plugin("bag2jp.autoplay", AP_FUMBLE_SITE,
                                              AP_FUMBLE_WORD, bag2jp_autoplay_no_fumble);
}
