/* Ending View: a sixth item on the main menu that plays one character's ending.
 *
 * The ending itself already works (system/004.dbi state 0x1A reads the chosen
 * character from 0x8005E6A0 and the costume from 0x8005E668), and the stock
 * one-character selector (system/007.dbi state 0x0C, dance-view mode) already
 * writes both. So this plugin only adds the way in, with no new screen:
 *
 *  1. system/002.dbi (main menu, state 7): widen the cursor to six items,
 *     move the first four sprites up 20 pixels and add ENDING VIEW before
 *     OPTIONS. Its final sprite setup call is replayed before drawing text.
 *  2. The confirm test (`andi v0,v0,0x820`, P1 and P2) is hooked: with index 4
 *     selected the menu's own confirm is swallowed and the module request
 *     becomes system/007.dbi state 0x0C in dance-view mode.
 *  3. When that selector exits (0x8008FDE0) its module/state request is
 *     rewritten from dance-view's module 1/state 0x18 to system/004.dbi
 *     state 0x1A. Cancellation retains its original destination.
 *
 * Every write is guarded by the exact instruction it replaces, and the patched
 * menu words are re-applied when the main-menu overlay is loaded again.
 *
 * Audited for SLPM-86219 (JP) only.
 */
#include "mod_plugins.h"
#include "cpu_state.h"
#include "gpu_hd_textures.h"
#include <SDL3/SDL.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>

#define EV_PLUGIN "bag2jp.endings_view"

/* ---------------------------------------------------------- main menu (002.dbi) */
#define EV_DRAW_ORIG      0x80049924u   /* final menu label's sprite setup */
#define EV_DRAW_SITE      0x8009AD30u   /* jal 0x80049924 */
#define EV_DRAW_WORD      0x0C012649u
#define EV_GUEST_DRAW     0x0F000200u   /* 0x0F000100 belongs to MODS */
#define EV_JAL_DRAW       (0x0C000000u | ((EV_GUEST_DRAW >> 2) & 0x03FFFFFFu))

#define EV_UP_WRAP_A      0x80099F48u   /* addiu v0,zero,4 : wrap 0 -> 5 */
#define EV_UP_WRAP_B      0x8009A024u
#define EV_WRAP_OLD       0x24020004u
#define EV_WRAP_NEW       0x24020005u

#define EV_DOWN_LIM_A     0x8009A0C0u   /* slti v0,v0,5 : 6 keeps index 5 */
#define EV_DOWN_LIM_B     0x8009A1A0u
#define EV_LIMIT_OLD      0x28420005u
#define EV_LIMIT_NEW      0x28420006u

#define EV_CONFIRM_P1     0x8009A23Cu   /* andi v0,v0,0x820 */
#define EV_CONFIRM_P2     0x8009A28Cu
#define EV_CONFIRM_WORD   0x30420820u
#define EV_CONFIRM_BITS   0x00000820u   /* Start | Circle */

#define EV_CURSOR         0x80192028u
#define EV_ITEM           4u
#define EV_MENU_GUARD     0x80099C50u
#define EV_MENU_GUARD_W   0x3C028019u
#define EV_DISPATCH       0x80099D30u   /* sltiu v0,v1,5 */
#define EV_DISPATCH_W     0x2C620005u
#define EV_HIGHLIGHT      0x8009A814u   /* addiu a2,zero,1 */
#define EV_HIGHLIGHT_W    0x24060001u

/* ------------------------------------------------- character select (007.dbi) */
#define EV_SELECT_EXIT    0x8008FDE0u   /* sw s1,-0x2c2c(v0): module/state request */
#define EV_SELECT_EXIT_W  0xAC51D3D4u

/* ------------------------------------------------------------- shared state */
#define EV_STATE          0x8005D3D4u
#define EV_NEXT_MODULE    0x8005F7CCu   /* byte */
#define EV_NEXT_STATE     0x8005F7C8u
#define EV_MODE           0x8005D2C4u   /* half */
#define EV_SIDE           0x8005E6C8u   /* byte */
#define EV_CHAR           0x8005E6A0u
#define EV_COSTUME        0x8005E668u

#define EV_ST_MENU        0x00000007u
#define EV_ST_SELECT      0x0000000Cu
#define EV_ST_RELOAD      0x00000021u
#define EV_MOD_SELECT     2u
#define EV_MOD_ENDING     3u
#define EV_ST_ENDING      0x0000001Au
#define EV_MODE_DANCE     4u

/* ------------------------------------------------------------------ drawing */
#define EV_LABEL_Y        167
#define EV_DRAW_HEAP      0x80051A88u
#define EV_DRAW_OT        0x8006D990u

static FILE* s_logf;
static int s_armed, s_pending, s_wait;
static int s_hd_menu;

/* JP menu identity, not merely a single coincidental instruction in an overlay. */
static int ev_is_menu(void) {
    return psx_mod_read_word(EV_MENU_GUARD) == EV_MENU_GUARD_W &&
           psx_mod_read_word(EV_CONFIRM_P1) == EV_CONFIRM_WORD &&
           psx_mod_read_word(EV_CONFIRM_P2) == EV_CONFIRM_WORD;
}

static void ev_log(const char* fmt, ...) {
    if (!s_logf) {
        const char* b = SDL_GetBasePath(); char p[1024];
        snprintf(p, sizeof p, "%sbag2jp_endings_view.log", b ? b : "");
        s_logf = fopen(p, "w"); if (!s_logf) return;
    }
    va_list ap; va_start(ap, fmt); vfprintf(s_logf, fmt, ap); va_end(ap);
    fputc('\n', s_logf); fflush(s_logf);
}

/* --------------------------------------------------------------- menu patch */
/* Re-applied every frame: the overlay at 0x8008F890 is replaced on every module
 * change, which restores the stock instructions. Each word is written only when
 * the stock instruction is still there, so the patch is idempotent and can never
 * touch another overlay. */
static void ev_patch_menu(void) {
    if (!ev_is_menu()) return;
    int changed = 0;
    if (psx_mod_read_word(EV_UP_WRAP_A) == EV_WRAP_OLD) {
        psx_mod_write_code_word(EV_UP_WRAP_A, EV_WRAP_NEW); changed = 1;
    }
    if (psx_mod_read_word(EV_UP_WRAP_B) == EV_WRAP_OLD) {
        psx_mod_write_code_word(EV_UP_WRAP_B, EV_WRAP_NEW); changed = 1;
    }
    if (psx_mod_read_word(EV_DOWN_LIM_A) == EV_LIMIT_OLD) {
        psx_mod_write_code_word(EV_DOWN_LIM_A, EV_LIMIT_NEW); changed = 1;
    }
    if (psx_mod_read_word(EV_DOWN_LIM_B) == EV_LIMIT_OLD) {
        psx_mod_write_code_word(EV_DOWN_LIM_B, EV_LIMIT_NEW); changed = 1;
    }
    if (psx_mod_read_word(EV_DRAW_SITE) == EV_DRAW_WORD) {
        psx_mod_write_code_word(EV_DRAW_SITE, EV_JAL_DRAW); changed = 1;
    }
    /* Make room above OPTIONS without covering the copyright strip. */
    static const uint32_t positions[][3] = {
        {0x8009A894u, 0x24020068u, 0x24020054u},
        {0x8009A9C4u, 0x2402007Eu, 0x2402006Au},
        {0x8009AAC4u, 0x240C0094u, 0x240C0080u},
        {0x8009ABF0u, 0x240200A7u, 0x24020093u},
    };
    for (unsigned i = 0; i < sizeof positions / sizeof positions[0]; ++i)
        if (psx_mod_read_word(positions[i][0]) == positions[i][1])
            psx_mod_write_code_word(positions[i][0], positions[i][2]);
    if (changed) ev_log("main menu patched: cursor 0..5, label hook");
}

/* ------------------------------------------------------------------ label */
/* Reuse the actual title-menu artwork from system/016/001.tim, not a font.
 * E,N,D,I,N and VIEW are cropped from DANCE VIEW (v=72); G is from GAME (v=0).
 * Each triple is source u/v/width. No replacement texture or new palette. */
static const uint8_t s_label_glyphs[][3] = {
    {60,72,15}, {30,72,14}, {0,72,16}, {94,72,14}, {30,72,14}, {118,0,18},
    {75,72,19}, {94,72,14}, {108,72,15}, {123,72,25},
};

static void ev_label(struct CPUState* cpu, uint32_t sp, uint32_t ra) {
    (void)sp; (void)ra;
    /* At AD30, s6 is the OPTIONS DR_TPAGE+SPRT allocation, s0 its sprite.
     * Clone its packet format, texture page, modulation and selected palette. */
    const uint32_t source = cpu->gpr[22];
    if (cpu->gpr[16] != source + 8u ||
        (psx_mod_read_word(source + 4u) >> 24) != 0xE1u ||
        (psx_mod_read_word(source + 12u) >> 24) != 0x64u) return;
    uint32_t packet[7];
    for (unsigned i = 0; i < 7; ++i) packet[i] = psx_mod_read_word(source + i * 4u);
    const unsigned cursor = psx_mod_read_word(EV_CURSOR);
    const unsigned u = packet[5] & 255u, v = ((packet[5] >> 8) - 96u) & 255u;
    uint16_t clut = (uint16_t)(packet[5] >> 16);
    if (cursor != 5u) clut -= 64u; /* OPTIONS' stock unselected CLUT row */
    if (cursor != EV_ITEM) clut += 64u;
    if (s_hd_menu && gpu_hd_textures_replacements_enabled()) {
        /* The HD atlas keeps the five native label cells. ENDING VIEW lives in
         * unused OPTIONS-row UVs (101,96,91,24), expanded to 150x24 by the
         * game's own textured-quad helper. Never stretch the whole menu. */
        const uint32_t args[12] = {EV_LABEL_Y, (u + 101u) & 255u, (v + 96u) & 255u,
            clut, 91u, 24u, 150u, 24u, psx_mod_read_half(0x8009CA36u), 0u, 0u,
            psx_mod_read_word(EV_DRAW_OT)};
        uint32_t saved[12];
        for (unsigned i = 0; i < 12; ++i) {
            saved[i] = psx_mod_read_word(sp + 16u + i * 4u);
            psx_mod_write_word(sp + 16u + i * 4u, args[i]);
        }
        (void)psx_mod_call_guest(cpu, 0x8009B258u, ra, packet[3] & 255u,
            (packet[3] >> 8) & 255u, (packet[3] >> 16) & 255u, 181u);
        for (unsigned i = 0; i < 12; ++i) psx_mod_write_word(sp + 16u + i * 4u, saved[i]);
        return;
    }
    unsigned width = 8u;
    for (unsigned i = 0; i < sizeof s_label_glyphs / sizeof s_label_glyphs[0]; ++i)
        width += s_label_glyphs[i][2];
    unsigned x = (512u - width) / 2u;
    uint32_t next = psx_mod_read_word(EV_DRAW_HEAP);
    const uint32_t ot = psx_mod_read_word(EV_DRAW_OT);
    for (unsigned i = 0; i < sizeof s_label_glyphs / sizeof s_label_glyphs[0]; ++i) {
        if (i == 6u) x += 8u;
        for (unsigned j = 0; j < 7; ++j) psx_mod_write_word(next + j * 4u, packet[j]);
        psx_mod_write_word(next + 16u, (EV_LABEL_Y << 16) | x);
        psx_mod_write_word(next + 20u, ((uint32_t)clut << 16) |
            (((v + s_label_glyphs[i][1]) & 255u) << 8) | ((u + s_label_glyphs[i][0]) & 255u));
        psx_mod_write_word(next + 24u, (24u << 16) | s_label_glyphs[i][2]);
        /* Same two-packet OT linkage as the audited stock menu after AD30. */
        psx_mod_write_word(next + 8u, (packet[2] & 0xFF000000u) | (psx_mod_read_word(ot) & 0xFFFFFFu));
        psx_mod_write_word(next, (packet[0] & 0xFF000000u) | ((next + 8u) & 0xFFFFFFu));
        psx_mod_write_word(ot, (psx_mod_read_word(ot) & 0xFF000000u) | (next & 0xFFFFFFu));
        next += 28u; x += s_label_glyphs[i][2];
    }
    psx_mod_write_word(EV_DRAW_HEAP, next);
}

/* jal target replacing the stock label call: replay it, then add the label. */
static void ev_draw_fn(struct CPUState* cpu, uint32_t address) {
    (void)address;
    const uint32_t ra = cpu->gpr[31], sp = cpu->gpr[29];
    const uint32_t a0 = cpu->gpr[4], a1 = cpu->gpr[5], a2 = cpu->gpr[6], a3 = cpu->gpr[7];
    const uint32_t v0 = psx_mod_call_guest(cpu, EV_DRAW_ORIG, ra, a0, a1, a2, a3);
    if (psx_mod_read_word(EV_STATE) == EV_ST_MENU) ev_label(cpu, sp, ra);
    cpu->gpr[2] = v0;
}

/* ---------------------------------------------------------------- confirm */
/* Keep the stock sound and 30-frame confirmation fade. Redirect its later
 * dispatch instead of swallowing the confirm button. */
static void ev_confirm(struct CPUState* cpu, uint32_t address) {
    if (!ev_is_menu()) return;
    if (!(cpu->gpr[2] & EV_CONFIRM_BITS)) return;
    if (psx_mod_read_word(EV_CURSOR) != EV_ITEM) return;
    (void)address;
    s_pending = 1; s_wait = 0;
    ev_log("ending view confirmed: stock sound/fade -> character select");
}

/* Visual index 5 is stock OPTIONS (dispatch index 4). Never grow its jump table. */
static void ev_dispatch(struct CPUState* cpu, uint32_t address) {
    (void)address;
    if (!ev_is_menu()) return;
    if (cpu->gpr[3] == 5) cpu->gpr[3] = 4;
    else if (s_pending && cpu->gpr[3] == EV_ITEM) cpu->gpr[3] = 3;
}

/* Only remap the register used to build the five stock highlight flags. */
static void ev_highlight(struct CPUState* cpu, uint32_t address) {
    (void)address;
    if (!ev_is_menu()) return;
    if (cpu->gpr[5] == 5) cpu->gpr[5] = 4;
    else if (cpu->gpr[5] == 4) cpu->gpr[5] = 5;
}

/* ------------------------------------------------------------ selector exit */
static void ev_select_exit(struct CPUState* cpu, uint32_t address) {
    (void)address;
    if (!s_armed) return;
    if (cpu->gpr[17] != EV_ST_RELOAD) return;   /* s1: the module-reload trigger */
    s_armed = 0;
    /* Dance-view acceptance is module 1/state 0x18. Cancel must stay stock. */
    if (cpu->gpr[18] != 1 || cpu->gpr[19] != 0x18) {
        ev_log("selector cancelled: module %u state %02X", cpu->gpr[18], cpu->gpr[19]);
        return;
    }
    const uint32_t side = psx_mod_read_byte(EV_SIDE) & 1u;
    ev_log("selector exit: char %u costume %u (side %u) -> ending",
           psx_mod_read_word(EV_CHAR + 4u * side), psx_mod_read_byte(EV_COSTUME + side), side);
    cpu->gpr[18] = EV_MOD_ENDING;    /* s2: module request byte */
    cpu->gpr[19] = EV_ST_ENDING;     /* s3: next state */
}

/* ------------------------------------------------------------------ hooks */
static void ev_vblank(void) {
    ev_patch_menu();

    const uint32_t state = psx_mod_read_word(EV_STATE);
    if (s_pending) {
        if (state != EV_ST_MENU) { s_pending = 0; s_armed = 1; ev_log("armed after leaving the menu"); }
        else if (++s_wait > 120) { s_pending = 0; ev_log("pending expired"); }
    }
    if (s_armed && state == EV_ST_MENU) { s_armed = 0; ev_log("disarmed: back at the menu"); }
}

static void ev_activate(void) {
    s_armed = s_pending = s_wait = 0;
    s_hd_menu = 0;
    char dir[1024], path[1100];
    if (psx_mod_current_resource_path("menu_hd", dir, sizeof dir)) {
        snprintf(path, sizeof path, "%s/ready.txt", dir);
        FILE* ready = fopen(path, "r");
        if (ready) { s_hd_menu = 1; fclose(ready); }
    }
    ev_log("activate: HD menu assets %d", s_hd_menu);
}

static void ev_session_reset(void) {
    s_armed = s_pending = s_wait = 0;
}

PSX_MOD_CONSTRUCTOR(bag2jp_register_endings_view) {
    (void)psx_mod_register_activation_plugin(EV_PLUGIN, ev_activate);
    (void)psx_mod_register_session_reset_plugin(EV_PLUGIN, ev_session_reset);
    (void)psx_mod_register_vblank_plugin(EV_PLUGIN, ev_vblank);
    (void)psx_mod_register_guest_function_plugin(EV_PLUGIN, EV_GUEST_DRAW, ev_draw_fn);
    (void)psx_mod_register_instruction_plugin(EV_PLUGIN, EV_CONFIRM_P1, EV_CONFIRM_WORD, ev_confirm);
    (void)psx_mod_register_instruction_plugin(EV_PLUGIN, EV_CONFIRM_P2, EV_CONFIRM_WORD, ev_confirm);
    (void)psx_mod_register_instruction_plugin(EV_PLUGIN, EV_SELECT_EXIT, EV_SELECT_EXIT_W, ev_select_exit);
    (void)psx_mod_register_instruction_plugin(EV_PLUGIN, EV_DISPATCH, EV_DISPATCH_W, ev_dispatch);
    (void)psx_mod_register_instruction_plugin(EV_PLUGIN, EV_HIGHLIGHT, EV_HIGHLIGHT_W, ev_highlight);
}
