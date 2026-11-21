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
#include "cpu_state.h"
#include "bag2jp_bag1_alt_index.h"
#include "bag2jp_model_region.h"
#include "bag2jp_strike_shot.h"
#include "bag2jp_heat_flame.h"
#include "bag2jp_strike_bag1_draw.h"
#include "bag2jp_gaso_tank.h"
#include "bag2jp_bag1_hud.h"
#include "bag2jp_bag1_leash.h"
#include "bag2jp_bag1_center.h"

#define B1V_TABLE    0x8005D418u   /* RAM copy of the DF2_ header */
#define B1V_MAGIC    0x5F324644u   /* 'DF2_' */
#define B1V_CHAR_P1  0x8005E6A0u   /* u32 char id per side (+4 = P2) */
#define B1V_WINNER   0x80089254u
#define B1V_DANCERS  0x8005F808u   /* dancer pointer per side, stride 8 */
#define B1V_CHARS    18
#define B1V_SELECTED 0x80089250u   /* byte per side read by the loader: char | costume << 5, 0xFF none */
#define B1V_GAME_MODE 0x8005D2C4u  /* u16: 0 demo, 2 two players; 1/3/4 human vs CPU (FUN_80033c10) */
#define B1V_ROOT      0x8005D3D4u
#define B1V_ROOT_MENU 7u   /* live title/menu root state (notes/archive/endings-view-before-audit.md) */
#define B1V_HUMAN_SIDE 0x8005E6C8u /* side the human plays in one-player mode */
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
    static const char* const gaso_ids[2] = {"gaso_p1", "gaso_p2"};
    for (int s = 0; s < 2; ++s) {
        char v[16] = {0};
        b1v_version[0][s] = psx_mod_current_option_value(heat_ids[s], v, sizeof v) > 0 && strcmp(v, "bag1") == 0;
        b1v_version[1][s] = psx_mod_current_option_value(strike_ids[s], v, sizeof v) > 0 && strcmp(v, "bag1") == 0;
        b1v_version[9][s] = psx_mod_current_option_value(gaso_ids[s], v, sizeof v) > 0 && strcmp(v, "bag1") == 0;
    }
    b1v_log("Heat version: P1 %s, P2 %s", b1v_version[0][0] ? "BAG1" : "BAG2", b1v_version[0][1] ? "BAG1" : "BAG2");
    b1v_log("Strike version: P1 %s, P2 %s", b1v_version[1][0] ? "BAG1" : "BAG2", b1v_version[1][1] ? "BAG1" : "BAG2");
    b1v_log("Gas-O version: P1 %s, P2 %s", b1v_version[9][0] ? "BAG1" : "BAG2", b1v_version[9][1] ? "BAG1" : "BAG2");
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
        /* Story mode has no stage picker: the stage is the rival's. A mirror match (BAG1 Gas-O
         * vs BAG2 Bi-O share chr 9) takes the CPU side's version in 1P mode (FUN_8001e0f4: stage
         * = side human^1); otherwise mixed versions keep the stock stage and its stock song. */
        if (psx_mod_read_word(B1V_CHAR_P1) == c && psx_mod_read_word(B1V_CHAR_P1 + 4u) == c) {
            const uint32_t mode = psx_mod_read_byte(B1V_GAME_MODE) | psx_mod_read_byte(B1V_GAME_MODE + 1u) << 8;
            if (mode == 1 || mode == 3 || mode == 4)   /* human vs CPU (FUN_80033c10) */
                return b1v_version[c][(psx_mod_read_byte(B1V_HUMAN_SIDE) & 1u) ^ 1u];
            return b1v_version[c][0] && b1v_version[c][1];
        }
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
/* Gas-O retains native model units: anchor its native 116/127 Gas/Strike ratio
 * to corrected Strike A (3429 Q12), rounded to 3132. Both Gas costumes share
 * that scale; this candidate still requires native-relative visual acceptance. */
static const uint16_t b1v_scale_q12[B1V_CHARS][2] = {
    [1] = { 3429u, 3434u },
    [9] = { 3132u, 3132u }
};   /* costume A, B */
static uint32_t b1v_scaled_dancer[4], b1v_scaled_value[4];
/* Dancer in slot 0..3 (0x8005F808 + 4*slot: P1, P1 partner, P2, P2 partner) if it plays
 * its BAG1 version, else 0; `picked` receives the selection byte. */
static uint32_t b1v_bag1_dancer(int slot, uint32_t* picked) {
    const int side = slot >> 1;
    const uint32_t d = psx_mod_read_word(B1V_DANCERS + 4u * (uint32_t)slot);
    if (d < 0x80010000u || d >= 0x80800000u) return 0;
    const uint32_t chr = psx_mod_read_byte(d + 4u);
    *picked = psx_mod_read_byte(B1V_SELECTED + (uint32_t)side);
    if (b1v_force_stock || chr >= B1V_CHARS || (*picked & B1V_CHAR_MASK) != chr
        || !b1v_version[chr][side] || !b1v_has_alt(chr)) return 0;
    return d;
}
static void b1v_dancer_scale(void) {
    for (int slot = 0; slot < 4; ++slot) {
        const int side = slot >> 1;
        const uint32_t d = psx_mod_read_word(B1V_DANCERS + 4u * (uint32_t)slot);
        if (d < 0x80010000u || d >= 0x80800000u) { b1v_scaled_dancer[slot] = 0; continue; }
        uint32_t picked = 0;
        if (!b1v_bag1_dancer(slot, &picked)) continue;
        const uint32_t chr = psx_mod_read_byte(d + 4u);
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

static void b1v_dancer_leash(void) {
    for (int slot = 0; slot < 4; ++slot) {
        uint32_t picked = 0;
        const uint32_t d = b1v_bag1_dancer(slot, &picked);
        const uint32_t radius = b1leash_apply(slot, d);
        if (radius) b1v_log("%07u dancer %d leash radius -> %u", b1v_frame, slot, radius);
    }
}

static int b1v_region_japanese(const char* option) {
    char value[16] = {0};
    /* Explicit package context keeps this independent of character/song choices. */
    if (psx_mod_option_value("bag2jp.content.bag1-visuals", "regional", option,
                             value, sizeof value) <= 0) return 1;
    return strcmp(value, "international") != 0;
}

/* BAG2 size as the disc table reports it. A disc_user mod (move viewer) may grow a BAG2
 * entry in place; forcing the compiled stock size would place the player struct over the
 * grown bank tail (LOSE3 hang, notes/move-viewer.md 2026-11-21). */
static uint32_t b1v_bag2_size[sizeof b1_alt_entries / sizeof b1_alt_entries[0]];

static void b1v_apply_entry(const B1AltEntry* e, uint32_t* bag2_size, uint32_t count,
                            int japanese) {
    if (e->entry >= count) return;
    const uint32_t a = B1V_TABLE + 8u + 8u * e->entry;
    const uint32_t off = psx_mod_read_word(a);
    if (off != e->off && off != e->alt_off && (!e->jp_size || off != e->jp_off)) return;
    if (off == e->off) *bag2_size = psx_mod_read_word(a + 4u);
    if (!*bag2_size) *bag2_size = e->size;
    const int alt = b1v_wanted(e);
    const int available = !japanese || e->jp_size != 0;
    /* Missing JP resources must not be presented as the Japanese variant. */
    const int use_alt = alt && available;
    const uint32_t want = use_alt ? (japanese ? e->jp_off : e->alt_off) : e->off;
    const uint32_t size = use_alt ? (japanese ? e->jp_size : e->alt_size) : *bag2_size;
    if (off == want && psx_mod_read_word(a + 4u) == size) return;
    psx_mod_write_word(a, want);
    psx_mod_write_word(a + 4u, size);
    b1v_log("%07u entry %u -> %s", b1v_frame, e->entry,
            use_alt ? (japanese ? "BAG1 JP" : "BAG1 International") : "BAG2");
}

#define GASO_TANK_PLAY_CUE 0x8002E478u /* BAG2 JP: takes a free voice slot, then 8002e2d0 */

/* Called from the 0x8002d06c entry hook (bag2jp_gaso_caught.c), where guest
 * calls are allowed; the caller's registers are restored after each call. */
void bag2jp_gaso_tank_play_cues(struct CPUState* cpu, uint32_t return_address) {
    static const uint32_t cue[2] = {GASO_TANK_CUE_LOCK, GASO_TANK_CUE_BUBBLE};
    const uint32_t pending = bag2jp_gaso_tank_take_cues();
    for (unsigned i = 0; i < 2; ++i) {
        if (!(pending & (1u << i))) continue;
        const uint32_t slot = psx_mod_call_guest(cpu, GASO_TANK_PLAY_CUE, return_address,
                                                 cue[i], ~0u, ~0u, ~0u);
        b1v_log("%07u gaso_tank: cue %04x slot %d", b1v_frame, (unsigned)cue[i], (int32_t)slot);
    }
}

static void b1v_vblank(void) {
    ++b1v_frame;
    b1v_model_region();
    b1v_dancer_scale();
    b1v_dancer_leash();
    bag2jp_strike_bag1_tick(b1v_frame);
    bag2jp_heat_flame_tick(b1v_frame);
    bag2jp_gaso_tank_tick(b1v_frame);
    /* Returning to the title/main menu (root 7) forgets the VS stage pick so a later story
     * match does not inherit it. */
    if (psx_mod_read_word(B1V_ROOT) == B1V_ROOT_MENU && b1v_stage_choice_chr >= 0) {
        b1v_stage_choice_chr = -1;
        b1v_stage_choice_version = -1;
        b1v_stage_version = -1;
    }
    if (psx_mod_read_word(B1V_TABLE) != B1V_MAGIC) return;
    const uint32_t count = psx_mod_read_word(B1V_TABLE + 4u);
    const int models_jp = b1v_region_japanese("models");
    const int stages_jp = b1v_region_japanese("stages");
    for (unsigned i = 0; i < sizeof b1_alt_entries / sizeof b1_alt_entries[0]; ++i) {
        const B1AltEntry* e = &b1_alt_entries[i];
        b1v_apply_entry(e, &b1v_bag2_size[i], count, e->kind == 3 ? stages_jp : models_jp);
    }
}

static int b1v_active;
/* Before the native JAL, replace only the verified stack home vector's X.
 * No PC/register edits: native initialization still writes root/base/home. */
static void b1v_home_hook(struct CPUState* cpu, uint32_t address) {
    if (!b1v_active || address != B1HOME_SITE) return;
    const uint32_t stack = cpu->gpr[29];
    if ((stack & 3u) || stack < B1LEASH_RAM_LOW || stack > B1LEASH_RAM_END - 28u ||
        cpu->gpr[6] != stack + 16u) return;
    for (int slot = 0; slot <= 2; slot += 2) {
        const uint32_t ctl = B1LEASH_CTL + (uint32_t)slot * B1LEASH_CTL_STRIDE;
        if (cpu->gpr[4] != ctl || cpu->gpr[18] != ctl) continue;
        const uint32_t actor = psx_mod_read_word(B1V_DANCERS + (uint32_t)slot * 4u);
        if ((actor & 3u) || actor < B1LEASH_RAM_LOW ||
            actor > B1LEASH_RAM_END - B1HOME_ACTOR_SIZE ||
            cpu->gpr[5] != actor || cpu->gpr[17] != actor) continue;
        uint32_t picked = 0;
        const uint32_t dancer = b1v_bag1_dancer(slot, &picked);
        if (dancer && b1home_apply(slot, dancer, cpu->gpr[6]))
            b1v_log("home: slot%d initial X widened, native tight radius retained", slot);
    }
}
/* Native update seam: version and controller identity are verified per call.
 * No register/PC changes: the original lw, clamp and pose consumer still run. */
static void b1v_end_center_hook(struct CPUState* cpu, uint32_t address) {
    if (!b1v_active || address != B1CENTER_SITE) return;
    for (int slot = 0; slot <= 2; slot += 2) {
        if (cpu->gpr[19] != B1LEASH_CTL + (uint32_t)slot * B1LEASH_CTL_STRIDE) continue;
        const uint32_t actor = psx_mod_read_word(B1V_DANCERS + (uint32_t)slot * 4u);
        if ((actor & 3u) || actor < B1LEASH_RAM_LOW ||
            actor > B1LEASH_RAM_END - B1CENTER_ACTOR_SIZE || cpu->gpr[16] != actor) continue;
        uint32_t picked = 0;
        const uint32_t dancer = b1v_bag1_dancer(slot, &picked);
        if (dancer && cpu->gpr[16] == dancer) b1center_apply(slot, dancer, b1v_frame);
    }
}
/* The runtime permits one restore callback per plugin ID. Keep both latches. */
static void b1v_restore(void) {
    b1load_forget();
    b1leash_forget();
    b1center_forget();
}
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
    memset(b1v_bag2_size, 0, sizeof b1v_bag2_size); /* no disc size leaks across sessions */
    b1load_forget();
    b1leash_forget();
    b1center_forget();
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
/* Is `offset` one of DF2_ entry `entry`'s BAG1 files? (load latch, bag2jp_bag1_load_latch.h) */
int bag2jp_bag1_offset_is_alt(unsigned entry, uint32_t offset) {
    for (unsigned i = 0; i < sizeof b1_alt_entries / sizeof b1_alt_entries[0]; ++i) {
        const B1AltEntry* e = &b1_alt_entries[i];
        if (e->entry == entry) return offset == e->alt_off || (e->jp_size && offset == e->jp_off);
    }
    return 0;
}
/* Stage shim (bag2jp_bag1_stage.c): does DF2_ entry `entry` point at one of its BAG1 files now? */
int bag2jp_bag1_entry_is_alt(unsigned entry) {
    if (psx_mod_read_word(B1V_TABLE) != B1V_MAGIC || entry >= psx_mod_read_word(B1V_TABLE + 4u)) return 0;
    return bag2jp_bag1_offset_is_alt(entry, psx_mod_read_word(B1V_TABLE + 8u + 8u * entry));
}
int bag2jp_bag1_get_version(int chr, int side) {
    if (!b1v_active || b1v_force_stock || chr < 0 || chr >= B1V_CHARS || side < 0 || side > 1) return 0;
    return b1v_version[chr][side];
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
    (void)psx_mod_register_instruction_plugin("bag2jp.bag1_versions", 0x80093F6Cu, 0x3C0400FFu, b1hud_sprite_hook);
    (void)psx_mod_register_instruction_plugin("bag2jp.bag1_versions", B1LOAD_SITE, B1LOAD_WORD, b1load_read_hook);
    (void)psx_mod_register_instruction_plugin("bag2jp.bag1_versions", B1HOME_SITE, B1HOME_WORD, b1v_home_hook);
    (void)psx_mod_register_instruction_plugin("bag2jp.bag1_versions", B1CENTER_SITE, B1CENTER_WORD, b1v_end_center_hook);
    (void)psx_mod_register_savestate_plugin("bag2jp.bag1_versions", b1v_restore);
    (void)psx_mod_register_vblank_plugin("bag2jp.bag1_versions", b1v_vblank);
    (void)psx_mod_register_activation_plugin("bag2jp.bag1_versions", b1v_activate);
    (void)psx_mod_register_session_reset_plugin("bag2jp.bag1_versions", b1v_reset);
    (void)psx_mod_register_option_changed_plugin("bag2jp.bag1_versions", b1v_option_changed);
}
