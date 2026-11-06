/* Expanded native stage carousel. Both Heat and Strike entries keep their stage ids (0/1);
 * only the archive version differs. system/007.dbi guards prevent writes to other overlays. */
#include "bag2jp_stage_select_patches.h"
static int cs_screen_active(void);
static void cs_read_glyphs(void);
void bag2jp_bag1_set_stage_version(int version);
void bag2jp_bag1_set_stage_choice(int chr, int version);
typedef struct { int kind, x, y, label_y, random; } CsStageView;
static CsStageView cs_stage_view;
static SDL_SpinLock cs_stage_lock;
static atomic_int cs_stage_visible;
static int cs_stage_patched, cs_stage_assets_ready, cs_stage_random_row;
static CsImg cs_stage_images[4]; /* Heat BAG2, Heat BAG1, Strike BAG2, Strike BAG1 */

int bag2jp_stage_select_enabled(void) { return s_enabled && cs_stage_assets_ready; }
static void cs_stage_publish(CsStageView view) {
    SDL_LockSpinlock(&cs_stage_lock);
    const int changed = memcmp(&cs_stage_view, &view, sizeof view) != 0;
    cs_stage_view = view;
    SDL_UnlockSpinlock(&cs_stage_lock);
    atomic_store(&cs_stage_visible, view.kind != 0);
    if (changed) atomic_store(&s_dirty, 1);
}
static void cs_stage_activate(void) {
    cs_stage_assets_ready = 1;
    const char* names[] = {"heat_bag2.png", "heat_bag1.png", "strike_bag2.png", "strike_bag1.png"};
    for (int i = 0; i < 4; ++i) {
        char p[1200]; snprintf(p, sizeof p, "%s/%s", s_dir, names[i]);
        FILE* f = fopen(p, "rb");
        if (f) fclose(f); else cs_stage_assets_ready = 0;
    }
    cs_stage_patched = 0; cs_stage_random_row = 0;
    cs_stage_publish((CsStageView){0});
    cs_log("stage carousel: assets %s", cs_stage_assets_ready ? "ready" : "missing");
}
static int cs_stage_patch(int expand) {
    if (expand == cs_stage_patched) return 1;
    for (unsigned i = 0; i < sizeof cs_stage_patches / sizeof cs_stage_patches[0]; ++i) {
        const CsStagePatch* p = &cs_stage_patches[i];
        const uint32_t word = psx_mod_read_word(p->addr);
        if (word != p->stock && word != p->expanded) return 0;
    }
    const uint8_t* order = cs_stage_patched ? cs_stage_order_expanded : cs_stage_order_stock;
    const uint8_t* inv = cs_stage_patched ? cs_stage_inverse_expanded : cs_stage_inverse_stock;
    for (unsigned i = 0; i < 16; ++i)
        if (psx_mod_read_byte(0x800963D0u + i) != order[i] ||
            psx_mod_read_byte(0x800963E0u + i) != inv[i]) return 0;
    for (unsigned i = 0; i < sizeof cs_stage_patches / sizeof cs_stage_patches[0]; ++i) {
        const CsStagePatch* p = &cs_stage_patches[i];
        psx_mod_write_code_word(p->addr, expand ? p->expanded : p->stock);
    }
    order = expand ? cs_stage_order_expanded : cs_stage_order_stock;
    inv = expand ? cs_stage_inverse_expanded : cs_stage_inverse_stock;
    for (unsigned i = 0; i < 16; ++i) {
        psx_mod_write_byte(0x800963D0u + i, order[i]);
        psx_mod_write_byte(0x800963E0u + i, inv[i]);
    }
    /* The picker is already initialized when the overlay first becomes visible. Remap its
     * current and previous cursor once, preserving the selected stock stage. */
    for (unsigned off = 0x1Au; off <= 0x1Bu; ++off) {
        int row = psx_mod_read_byte(0x80097214u + off);
        if (expand) {
            if (row >= 1 && row <= 3) row += 1;
            else if (row >= 4 && row <= 12) row += 2;
        } else {
            if (row == 0 || row == 1) row = 0;
            else if (row >= 2 && row <= 4) row -= 1;
            else if (row == 5) row = 3;
            else if (row >= 6 && row <= 14) row -= 2;
        }
        psx_mod_write_byte(0x80097214u + off, (uint8_t)row);
    }
    cs_stage_patched = expand;
    cs_log("stage carousel: %s", expand ? "15 rows (Heat BAG2/1, Strike BAG2/1, stock stages, random)" : "stock");
    return 1;
}
static void cs_stage_vblank(void) {
    CsStageView view = {0};
    if (!s_enabled || !cs_screen_active()) {
        cs_stage_patched = 0; cs_stage_publish(view); return;
    }
    const int wanted = cs_stage_assets_ready && (bag2jp_bag1_has_version(0) || bag2jp_bag1_has_version(1));
    if (!cs_stage_patch(wanted) || !wanted) {
        bag2jp_bag1_set_stage_choice(-1, -1); cs_stage_publish(view); return;
    }
    const uint32_t phase = psx_mod_read_word(0x80096F94u);
    if (phase == 1) bag2jp_bag1_set_stage_choice(-1, -1);
    if (phase == 2 || phase == 3 || phase == 6) {
        const int row = psx_mod_read_byte(0x8009722Eu);
        const int chr = psx_mod_read_byte(0x80097231u);
        int active_chr = -1;
        int bag1 = 0;
        if (row == 0) { active_chr = 0; bag1 = 0; }
        else if (row == 1) { active_chr = 0; bag1 = 1; }
        else if (row == 4) { active_chr = 1; bag1 = 0; }
        else if (row == 5) { active_chr = 1; bag1 = 1; }
        else if (row == 14) {
            if (cs_stage_random_row == 0) { active_chr = 0; bag1 = 0; }
            else if (cs_stage_random_row == 1) { active_chr = 0; bag1 = 1; }
            else if (cs_stage_random_row == 4) { active_chr = 1; bag1 = 0; }
            else if (cs_stage_random_row == 5) { active_chr = 1; bag1 = 1; }
        }
        bag2jp_bag1_set_stage_choice(active_chr, active_chr >= 0 ? bag1 : -1);
        if (chr == 0 || chr == 1) {
            if (!s_have_glyphs) cs_read_glyphs();
            if (chr == 0) view.kind = bag1 ? 2 : 1;
            else if (chr == 1) view.kind = bag1 ? 4 : 3;
            view.random = row == 14;
            view.x = (int16_t)psx_mod_read_half(0x8009724Cu);
            view.y = (int16_t)psx_mod_read_half(0x8009724Eu);
            view.label_y = (int16_t)psx_mod_read_half(0x800967DAu) + 0x51;
        }
    }
    cs_stage_publish(view);
}
static void cs_stage_random_hook(struct CPUState* cpu, uint32_t address) {
    (void)address;
    if (s_enabled && cs_stage_patched && cs_screen_active())
        cs_stage_random_row = cpu->gpr[2] < 14 ? (int)cpu->gpr[2] : 0;
}
static void cs_stage_name_hook(struct CPUState* cpu, uint32_t address) {
    (void)address;
    if (!s_enabled || !cs_stage_patched || !cs_screen_active()) return;
    /* The same s8=12 is also used for arrow dimensions. Normalize only the comparison operand. */
    if (cpu->gpr[2] == 14) cpu->gpr[2] = 12;
    else if (cpu->gpr[2] == 12) cpu->gpr[2] = 14;
}
static void cs_stage_heat_label_hook(struct CPUState* cpu, uint32_t address) {
    (void)address;
    if (!s_enabled || !cs_stage_patched || !cs_screen_active()) return;
    const int chr = psx_mod_read_byte(0x80097231u);
    const int row = psx_mod_read_byte(0x8009722Eu);
    if (row == 14) return;
    if (chr != 0 && chr != 1) return;
    const uint32_t text = psx_mod_read_word(0x80096E68u);
    if (text >= 0x8008F890u && text < 0x80096F80u && psx_mod_read_byte(text + 4u) == 0)
        cpu->gpr[2] = text + 4u; /* delay-slot sw stores the empty string for the native label */
}
static void cs_stage_compose(void) {
    CsStageView v;
    SDL_LockSpinlock(&cs_stage_lock); v = cs_stage_view; SDL_UnlockSpinlock(&cs_stage_lock);
    if (v.kind < 1 || v.kind > 4) return;
    CsImg* im = &cs_stage_images[v.kind - 1];
    if (!im->px) {
        const char* names[] = {"heat_bag2.png", "heat_bag1.png", "strike_bag2.png", "strike_bag1.png"};
        cs_load_png(names[v.kind - 1], im);
    }
    if (!im->px) return;
    const int x0 = (int)(v.x * CV_SX), y0 = (int)(v.y * CV_SY);
    const int dw = (int)(186 * CV_SX), dh = (int)(60 * CV_SY);
    for (int y = 0; y < dh; ++y) {
        const int dst_y = y0 + y; if (dst_y < 0 || dst_y >= CV_H) continue;
        const int src_y = y * im->h / dh;
        for (int x = 0; x < dw; ++x) {
            const int dst_x = x0 + x; if (dst_x < 0 || dst_x >= CV_W) continue;
            const unsigned char* p = im->px + ((size_t)src_y * im->w + x * im->w / dw) * 4;
            s_canvas[dst_y * CV_W + dst_x] = 0xFF000000u | ((uint32_t)p[0] << 16) | ((uint32_t)p[1] << 8) | p[2];
        }
    }
    const char* labels[] = {"HEAT BAG2", "HEAT BAG1", "STRIKE BAG2", "STRIKE BAG1"};
    const char* label = labels[v.kind - 1];
    if (!v.random) cv_text(label, v.x + 93 - cv_text_w(label, 1) / 2, v.label_y, CS_FONT_STAGE, 1);
}
