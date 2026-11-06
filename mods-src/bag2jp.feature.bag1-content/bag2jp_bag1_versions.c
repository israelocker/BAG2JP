/* BAG1/BAG2 character versions (package bag2jp.feature.bag1-content, feature "bag1-heat").
 *
 * Both versions of a character live on the disc: BAG2's in BUST2.BIN as stock, BAG1's as alternate
 * copies of the same archive entries written into DUMMY.BIN (never read by the game) by the package's
 * disc overlay (tools/bag1import/make_alt_entries.py, index in bag2jp_bag1_alt_index.h).
 * Every archive read goes through FUN_8001F874(entry, dest), which takes the entry's offset/size from
 * the RAM copy of the DF2_ table (0x8005D418: 'DF2_', count, then {offset, size} per entry, offsets
 * relative to BUST2.BIN). Once per frame this plugin points each listed entry at the version wanted:
 *   kind 0/1 (character pack/model, player 1/2 side): that player's version;
 *   kind 2 (fever choreography, one file for the fever dancer): the version of the player in the
 *          fever (winner pointer 0x80089254 vs dancers 0x8005F808/0x8005F810), else the side
 *          playing that character;
 *   kind 3 (the character's stage): the independent stage-menu choice; when no stage picker is
 *          used (story mode), the version of the player using that character (player 1 first).
 * The ported BAG1 stage is recognised by the bag1-stage plugin through its 'B1ST' shim, so the song
 * swap and song length follow automatically.
 * Version per player: options heat_p1/heat_p2 are the defaults; the select-screen popup
 * (bag2jp_charsel_popup.c) sets it per pick through bag2jp_bag1_set_version(). */
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <stdarg.h>
#include <SDL3/SDL.h>
#include "mod_plugins.h"
#include "bag2jp_bag1_alt_index.h"
#include "bag2jp_model_region.h"
#include "bag2jp_strike_shot.h"
#include "bag2jp_heat_flame.h"
#include "bag2jp_strike_bag1_draw.h"

#define B1V_TABLE    0x8005D418u   /* RAM copy of the DF2_ header */
#define B1V_MAGIC    0x5F324644u   /* 'DF2_' */
#define B1V_CHAR_P1  0x8005E6A0u   /* u32 char id per side (+4 = P2) */
#define B1V_WINNER   0x80089254u
#define B1V_DANCERS  0x8005F808u   /* dancer pointer per side, stride 8 */
#define B1V_CHARS    18
#define B1V_SELECTED 0x80089250u   /* byte per side read by the loader: char | costume << 5, 0xFF none */
#define B1V_CHAR_MASK 0x1Fu
#define B1V_NO_CHAR  0xFFu

static uint8_t b1v_version[B1V_CHARS][2];   /* 0 = BAG2 (stock), 1 = BAG1 */
static int b1v_stage_version = -1;          /* -1 automatic, 0 BAG2, 1 BAG1: independent stage pick */
static int b1v_stage_choice_chr = -1;
static int b1v_stage_choice_version = -1;
static int b1v_force_stock;                  /* online with different BAG1 content: BAG2 only */
static FILE* b1v_logf;
void b1v_log(const char* fmt, ...) {
    if (!b1v_logf) {
        const char* base = SDL_GetBasePath(); char p[1024];
        snprintf(p, sizeof p, "%sbag2jp_bag1_versions.log", base ? base : "");
        b1v_logf = fopen(p, "w"); if (!b1v_logf) return;
    }
    va_list ap; va_start(ap, fmt); vfprintf(b1v_logf, fmt, ap); va_end(ap);
    fputc('\n', b1v_logf); fflush(b1v_logf);
}

static void b1v_read_options(void) {
    static const char* const heat_ids[2] = {"heat_p1", "heat_p2"};
    static const char* const strike_ids[2] = {"strike_p1", "strike_p2"};
    for (int s = 0; s < 2; ++s) {
        char v[16] = {0};
        b1v_version[0][s] = psx_mod_current_option_value(heat_ids[s], v, sizeof v) > 0 && strcmp(v, "bag2") == 0 ? 0 : 1;
        b1v_version[1][s] = psx_mod_current_option_value(strike_ids[s], v, sizeof v) > 0 && strcmp(v, "bag2") == 0 ? 0 : 1;
    }
    b1v_log("Heat version: P1 %s, P2 %s", b1v_version[0][0] ? "BAG1" : "BAG2", b1v_version[0][1] ? "BAG1" : "BAG2");
    b1v_log("Strike version: P1 %s, P2 %s", b1v_version[1][0] ? "BAG1" : "BAG2", b1v_version[1][1] ? "BAG1" : "BAG2");
}

static int b1v_side_of(uint32_t chr) {      /* side playing chr, player 1 first; -1 if none */
    for (int s = 0; s < 2; ++s) if (psx_mod_read_word(B1V_CHAR_P1 + 4u * s) == chr) return s;
    return -1;
}

static int b1v_wanted(const B1AltEntry* e) {
    const uint32_t c = e->chr;
    if (b1v_force_stock) return 0;
    switch (e->kind) {
    case 0: case 1: return b1v_version[c][e->kind];
    case 2: {
        const uint32_t w = psx_mod_read_word(B1V_WINNER);
        for (int s = 0; s < 2; ++s)
            if (w && w == psx_mod_read_word(B1V_DANCERS + 8u * s) && psx_mod_read_word(B1V_CHAR_P1 + 4u * s) == c)
                return b1v_version[c][s];
        const int s = b1v_side_of(c);
        return b1v_version[c][s < 0 ? 0 : s];
    }
    case 3:
        if (b1v_stage_choice_chr == (int)c && b1v_stage_choice_version >= 0)
            return b1v_stage_choice_version;
        if (c == 0 && b1v_stage_version >= 0) return b1v_stage_version;
        /* Story mode has no stage picker: retain its character-based default. */
        /* fall through */
    default: { const int s = b1v_side_of(c); return b1v_version[c][s < 0 ? 0 : s]; }
    }
}

static int b1v_has_alt(uint32_t chr) {
    for (unsigned i = 0; i < sizeof b1_alt_entries / sizeof b1_alt_entries[0]; ++i)
        if (b1_alt_entries[i].chr == chr) return 1;
    return 0;
}

static uint32_t b1v_frame;
/* BAG1 models (full animation lists) need more than the stock per-side buffer: see the header. */
static void b1v_model_region(void) {
    int wanted[2];
    for (int s = 0; s < 2; ++s) {
        const uint32_t picked = psx_mod_read_byte(B1V_SELECTED + (uint32_t)s);
        const uint32_t chr = picked & B1V_CHAR_MASK;
        wanted[s] = !b1v_force_stock && picked != B1V_NO_CHAR && chr < B1V_CHARS
                    && b1v_version[chr][s] && b1v_has_alt(chr);
    }
    const int moved = bag2_model_region_tick(wanted);
    for (int s = 0; s < 2; ++s)
        if (moved & (1 << s)) b1v_log("%07u side %d model buffer -> expanded RAM", b1v_frame, s + 1);
}

/* Dancer scale. FUN_8002D85C stores a per-character scale (table 0x80051904: Heat 85,
 * Strike 98, times the stage factor) at dancer +0x14E4..EC and its base copy +0x1514..1C.
 * BAG2's Strike model is authored 0.837x the size of BAG1's (vertices and node translations,
 * A 0.8371 / B 0.8384), so the stock 98 draws BAG1 Strike ~19.5% larger than BAG2 Strike.
 * BAG1's own table (0x800558FC: Heat 128, Strike 127) keeps both characters at matching
 * size, and 98 x 0.837 restores that ratio. Heat's models differ by only ~2%: unchanged. */
#define B1V_SCALE_CUR  0x14E4u
#define B1V_SCALE_BASE 0x1514u
static const uint16_t b1v_scale_q12[B1V_CHARS][2] = { [1] = { 3429u, 3434u } };   /* costume A, B */
static uint32_t b1v_scaled_dancer[4], b1v_scaled_value[4];
static void b1v_dancer_scale(void) {
    for (int slot = 0; slot < 4; ++slot) {   /* 0x8005F808 + 4*slot: P1, P1 partner, P2, P2 partner */
        const int side = slot >> 1;
        const uint32_t d = psx_mod_read_word(B1V_DANCERS + 4u * (uint32_t)slot);
        if (d < 0x80010000u || d >= 0x80800000u) { b1v_scaled_dancer[slot] = 0; continue; }
        const uint32_t chr = psx_mod_read_byte(d + 4u);
        const uint32_t picked = psx_mod_read_byte(B1V_SELECTED + (uint32_t)side);
        if (b1v_force_stock || chr >= B1V_CHARS || (picked & B1V_CHAR_MASK) != chr
            || !b1v_version[chr][side] || !b1v_has_alt(chr)) continue;
        const uint32_t q = b1v_scale_q12[chr][(picked >> 5) & 1u];
        const uint32_t base = psx_mod_read_word(d + B1V_SCALE_BASE);
        if (!q || base == 0 || (b1v_scaled_dancer[slot] == d && b1v_scaled_value[slot] == base)) continue;
        const uint32_t v = (base * q + 0x800u) >> 12;   /* freshly initialised: scale once */
        for (uint32_t k = 0; k < 12u; k += 4u) {
            psx_mod_write_word(d + B1V_SCALE_BASE + k, v);
            psx_mod_write_word(d + B1V_SCALE_CUR + k, v);
        }
        b1v_scaled_dancer[slot] = d; b1v_scaled_value[slot] = v;
        b1v_log("%07u dancer %d (char %u side %d) scale %u -> %u", b1v_frame, slot, chr, side + 1, base, v);
    }
}

static void b1v_vblank(void) {
    ++b1v_frame;
    b1v_model_region();
    b1v_dancer_scale();
    bag2jp_strike_bag1_tick(b1v_frame);
    bag2jp_heat_flame_tick(b1v_frame);
    if (psx_mod_read_word(B1V_TABLE) != B1V_MAGIC) return;
    const uint32_t count = psx_mod_read_word(B1V_TABLE + 4u);
    for (unsigned i = 0; i < sizeof b1_alt_entries / sizeof b1_alt_entries[0]; ++i) {
        const B1AltEntry* e = &b1_alt_entries[i];
        if (e->entry >= count) continue;
        const uint32_t a = B1V_TABLE + 8u + 8u * e->entry;
        const uint32_t off = psx_mod_read_word(a);
        if (off != e->off && off != e->alt_off) continue;          /* someone else's entry: leave it */
        const int alt = b1v_wanted(e);
        const uint32_t want = alt ? e->alt_off : e->off;
        if (off == want) continue;
        psx_mod_write_word(a, want);
        psx_mod_write_word(a + 4u, alt ? e->alt_size : e->size);
        b1v_log("%07u entry %u -> %s", b1v_frame, e->entry, alt ? "BAG1" : "BAG2");
    }
}

static int b1v_active;
static void b1v_activate(void) {
    b1v_active = 1;
    b1v_stage_version = -1;
    b1v_stage_choice_chr = -1;
    b1v_stage_choice_version = -1;
    b1v_read_options();
}
static void b1v_reset(void) {
    b1v_active = 0;
    b1v_stage_version = -1;
    b1v_stage_choice_chr = -1;
    b1v_stage_choice_version = -1;
    memset(b1v_scaled_dancer, 0, sizeof b1v_scaled_dancer);
}
void bag2jp_bag1_set_stage_choice(int chr, int version) {
    b1v_stage_choice_chr = chr;
    b1v_stage_choice_version = (version == 0 || version == 1) ? version : -1;
    if (chr == 0) b1v_stage_version = b1v_stage_choice_version;
}
void bag2jp_bag1_set_stage_version(int version) {
    bag2jp_bag1_set_stage_choice(0, version);
}

/* Select-screen popup (bag2jp_charsel_popup.c): which characters have a BAG1 version, and the
 * version each player picked (0 BAG2, 1 BAG1). The pick lasts until the next start/option change. */
int bag2jp_bag1_has_version(int chr) {
    if (!b1v_active || b1v_force_stock || chr < 0 || chr >= B1V_CHARS) return 0;
    for (unsigned i = 0; i < sizeof b1_alt_entries / sizeof b1_alt_entries[0]; ++i)
        if (b1_alt_entries[i].chr == chr) return 1;
    return 0;
}
int bag2jp_bag1_get_version(int chr, int side) {
    return chr >= 0 && chr < B1V_CHARS && side >= 0 && side < 2 ? b1v_version[chr][side] : 0;
}
void bag2jp_bag1_set_version(int chr, int side, int v) {
    if (chr < 0 || chr >= B1V_CHARS || side < 0 || side > 1) return;
    b1v_version[chr][side] = (uint8_t)(v ? 1 : 0);
    b1v_log("popup: char %d player %d -> %s", chr, side + 1, v ? "BAG1" : "BAG2");
}
static int b1v_option_changed(const char* option_id, const char* value) {
    (void)option_id; (void)value; b1v_read_options(); return 1;
}

/* Online play (bag2jp_netsync.c). Both PCs must load the same files, so while linked:
 *  - every version starts as BAG2 (local launcher defaults may differ) and only picks made in the
 *    select popup change it (the picking PC sends them, see bag2jp_netsync_send_pick);
 *  - content id = hash of the alternate-entry index; if the PCs differ, both use BAG2 only. */
int bag2jp_stage_select_enabled(void);
uint32_t bag2jp_bag1_content_id(void) {
    if (!b1v_active) return 0;
    uint32_t h = 2166136261u;
    const uint8_t* d = (const uint8_t*)b1_alt_entries;
    for (unsigned i = 0; i < sizeof b1_alt_entries; ++i) { h ^= d[i]; h *= 16777619u; }
    /* Animation/content bytes must agree even when archive sizes remain equal. */
    h ^= B1_ALT_CONTENT_TAG; h *= 16777619u;
    /* WIN1: BAG1 Heat now retains the stock victory-name cue; its wait affects result timing. */
    h ^= 0x57494E31u; h *= 16777619u;
    /* SCL1: BAG1 Strike draws at BAG2 Strike's size (dancer scale above). */
    h ^= 0x53434C31u; h *= 16777619u;
    /* Menus relay pad changes: peers must agree on the expanded stage order too. */
    if (bag2jp_stage_select_enabled()) { h ^= 0x53544731u; h *= 16777619u; }
    return h ? h : 1;
}
void bag2jp_bag1_online(int linked) {
    b1v_stage_version = -1;
    if (linked) { memset(b1v_version, 0, sizeof b1v_version); b1v_log("online: all versions BAG2 until picked"); }
    else { b1v_force_stock = 0; if (b1v_active) b1v_read_options(); }
}
void bag2jp_bag1_force_stock(int on) {
    if (b1v_force_stock != on) b1v_log("online: BAG1 versions %s", on ? "OFF (the other PC has different content)" : "on");
    b1v_force_stock = on;
}

PSX_MOD_CONSTRUCTOR(bag2jp_register_bag1_versions) {
    (void)psx_mod_register_vblank_plugin("bag2jp.bag1_versions", b1v_vblank);
    (void)psx_mod_register_activation_plugin("bag2jp.bag1_versions", b1v_activate);
    (void)psx_mod_register_session_reset_plugin("bag2jp.bag1_versions", b1v_reset);
    (void)psx_mod_register_option_changed_plugin("bag2jp.bag1_versions", b1v_option_changed);
}
