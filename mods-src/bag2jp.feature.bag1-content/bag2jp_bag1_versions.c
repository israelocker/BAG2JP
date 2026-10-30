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
 *   kind 3 (the character's stage): the version of the player using that character (player 1 first).
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

#define B1V_TABLE    0x8005D418u   /* RAM copy of the DF2_ header */
#define B1V_MAGIC    0x5F324644u   /* 'DF2_' */
#define B1V_CHAR_P1  0x8005E6A0u   /* u32 char id per side (+4 = P2) */
#define B1V_WINNER   0x80089254u
#define B1V_DANCERS  0x8005F808u   /* dancer pointer per side, stride 8 */
#define B1V_CHARS    18

static uint8_t b1v_version[B1V_CHARS][2];   /* 0 = BAG2 (stock), 1 = BAG1 */
static int b1v_force_stock;                  /* online with different BAG1 content: BAG2 only */
static FILE* b1v_logf;
static void b1v_log(const char* fmt, ...) {
    if (!b1v_logf) {
        const char* base = SDL_GetBasePath(); char p[1024];
        snprintf(p, sizeof p, "%sbag2jp_bag1_versions.log", base ? base : "");
        b1v_logf = fopen(p, "w"); if (!b1v_logf) return;
    }
    va_list ap; va_start(ap, fmt); vfprintf(b1v_logf, fmt, ap); va_end(ap);
    fputc('\n', b1v_logf); fflush(b1v_logf);
}

static void b1v_read_options(void) {
    static const char* const ids[2] = {"heat_p1", "heat_p2"};
    for (int s = 0; s < 2; ++s) {
        char v[16] = {0};
        b1v_version[0][s] = psx_mod_current_option_value(ids[s], v, sizeof v) > 0 && strcmp(v, "bag2") == 0 ? 0 : 1;
    }
    b1v_log("Heat version: P1 %s, P2 %s", b1v_version[0][0] ? "BAG1" : "BAG2", b1v_version[0][1] ? "BAG1" : "BAG2");
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
    default: { const int s = b1v_side_of(c); return b1v_version[c][s < 0 ? 0 : s]; }
    }
}

static uint32_t b1v_frame;
static void b1v_vblank(void) {
    ++b1v_frame;
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
static void b1v_activate(void) { b1v_active = 1; b1v_read_options(); }
static void b1v_reset(void) { b1v_active = 0; }

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
uint32_t bag2jp_bag1_content_id(void) {
    if (!b1v_active) return 0;
    uint32_t h = 2166136261u;
    const uint8_t* d = (const uint8_t*)b1_alt_entries;
    for (unsigned i = 0; i < sizeof b1_alt_entries; ++i) { h ^= d[i]; h *= 16777619u; }
    return h ? h : 1;
}
void bag2jp_bag1_online(int linked) {
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
