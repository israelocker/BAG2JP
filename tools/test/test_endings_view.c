/* Host-side regression tests for the real plugin, with a byte-addressed RAM seam.
 * Run with WSL gcc; actual guest execution is covered separately in game. */
#include <assert.h>
#include <stdlib.h>
#include <string.h>
#include "endings_view_stubs/mod_plugins.h"
static unsigned char ram[8 * 1024 * 1024];
static uint32_t last_guest, guest_stack[12];
static unsigned offset(uint32_t a) { return a & 0x7fffff; }
uint32_t psx_mod_read_word(uint32_t a) { uint32_t v; memcpy(&v, ram + offset(a), 4); return v; }
uint16_t psx_mod_read_half(uint32_t a) { uint16_t v; memcpy(&v, ram + offset(a), 2); return v; }
uint8_t psx_mod_read_byte(uint32_t a) { return ram[offset(a)]; }
void psx_mod_write_word(uint32_t a, uint32_t v) { memcpy(ram + offset(a), &v, 4); }
void psx_mod_write_half(uint32_t a, uint16_t v) { memcpy(ram + offset(a), &v, 2); }
void psx_mod_write_byte(uint32_t a, uint8_t v) { ram[offset(a)] = v; }
void psx_mod_write_code_word(uint32_t a, uint32_t v) { psx_mod_write_word(a, v); }
uint32_t psx_mod_call_guest(struct CPUState* c, uint32_t a, uint32_t r, uint32_t x, uint32_t y, uint32_t z, uint32_t w) {
    last_guest = a;
    for (unsigned i = 0; i < 12; ++i) guest_stack[i] = psx_mod_read_word(c->gpr[29] + 16 + i * 4);
    return 100;
}
int gpu_hd_textures_replacements_enabled(void) { return 1; }
int psx_mod_current_resource_path(const char* id, char* out, uint32_t size) { assert(size > 1); strcpy(out, "."); return 1; }
int psx_mod_register_activation_plugin(const char* p, void (*f)(void)) { return 1; }
int psx_mod_register_session_reset_plugin(const char* p, void (*f)(void)) { return 1; }
int psx_mod_register_vblank_plugin(const char* p, void (*f)(void)) { return 1; }
int psx_mod_register_guest_function_plugin(const char* p, uint32_t a, void (*f)(struct CPUState*, uint32_t)) { return 1; }
int psx_mod_register_instruction_plugin(const char* p, uint32_t a, uint32_t w, void (*f)(struct CPUState*, uint32_t)) { return 1; }
#include "../../mods-src/bag2jp.feature.endings-view/bag2jp_endings_view.c"

static void menu(void) {
    psx_mod_write_word(EV_STATE, 7);
    psx_mod_write_word(0x80099C50u, 0x3C028019u);
    psx_mod_write_word(EV_CONFIRM_P1, EV_CONFIRM_WORD);
    psx_mod_write_word(EV_CONFIRM_P2, EV_CONFIRM_WORD);
    psx_mod_write_word(EV_DRAW_SITE, EV_DRAW_WORD);
    psx_mod_write_word(EV_UP_WRAP_A, EV_WRAP_OLD);
    psx_mod_write_word(EV_UP_WRAP_B, EV_WRAP_OLD);
    psx_mod_write_word(EV_DOWN_LIM_A, EV_LIMIT_OLD);
    psx_mod_write_word(EV_DOWN_LIM_B, EV_LIMIT_OLD);
    psx_mod_write_word(0x8009ACE8u, 0x240200BBu);
}
int main(int argc, char** argv) {
    assert(argc == 2);
    s_logf = tmpfile();
    struct CPUState cpu = {0};
    if (!strcmp(argv[1], "guest-address")) assert(EV_GUEST_DRAW != 0x0F000100u);
    else if (!strcmp(argv[1], "menu-order")) { assert(EV_ITEM == 4); assert(EV_LABEL_Y == 167); }
    else if (!strcmp(argv[1], "overlay-guard")) {
        menu(); psx_mod_write_word(0x80099C50u, 0); ev_vblank();
        assert(psx_mod_read_word(EV_UP_WRAP_A) == EV_WRAP_OLD);
    } else if (!strcmp(argv[1], "confirm")) {
        menu(); psx_mod_write_word(EV_CURSOR, 4); cpu.gpr[2] = 0x820;
        ev_confirm(&cpu, EV_CONFIRM_P1);
        /* Stock confirmation must still play its sound and run its fade. */
        assert(psx_mod_read_word(EV_STATE) == 7);
        assert(cpu.gpr[2] == 0x820 && s_pending);
        cpu.gpr[3] = 4;
        ev_dispatch(&cpu, EV_DISPATCH);
        assert(cpu.gpr[3] == 3); /* reuse stock DANCE VIEW initialization */
    } else if (!strcmp(argv[1], "cancel")) {
        s_armed = 1; cpu.gpr[17] = EV_ST_RELOAD; cpu.gpr[18] = 4; cpu.gpr[19] = 4;
        ev_select_exit(&cpu, EV_SELECT_EXIT);
        assert(cpu.gpr[18] == 4 && cpu.gpr[19] == 4 && !s_armed);
    } else if (!strcmp(argv[1], "ending")) {
        s_armed = 1; cpu.gpr[17] = EV_ST_RELOAD; cpu.gpr[18] = 1; cpu.gpr[19] = 24;
        ev_select_exit(&cpu, EV_SELECT_EXIT);
        assert(cpu.gpr[18] == 3 && cpu.gpr[19] == 26 && !s_armed);
    } else if (!strcmp(argv[1], "stock-selector")) {
        cpu.gpr[17] = EV_ST_RELOAD; cpu.gpr[18] = 1; cpu.gpr[19] = 24;
        ev_select_exit(&cpu, EV_SELECT_EXIT);
        assert(cpu.gpr[18] == 1 && cpu.gpr[19] == 24);
    } else if (!strcmp(argv[1], "native-lettering") || !strcmp(argv[1], "hd-lettering")) {
        const uint32_t p = 0x80100000, ot = 0x80110000;
        cpu.gpr[22] = p; cpu.gpr[16] = p + 8;
        psx_mod_write_word(p + 4, 0xE1000000);
        psx_mod_write_word(p + 8, 0x04000000);
        psx_mod_write_word(p + 12, 0x64808080);
        psx_mod_write_word(p + 20, (0x3C40u << 16) | (96u << 8));
        psx_mod_write_word(p + 24, (24u << 16) | 101u);
        psx_mod_write_word(0x80051A88u, p + 28);
        psx_mod_write_word(0x8006D990u, ot);
        psx_mod_write_word(ot, 0xFFFFFF);
        psx_mod_write_word(EV_CURSOR, 4);
        if (!strcmp(argv[1], "hd-lettering")) {
            FILE* ready = fopen("ready.txt", "w"); assert(ready); fclose(ready);
            ev_activate();
            cpu.gpr[29] = 0x80120000;
            ev_label(&cpu, cpu.gpr[29], 0);
            remove("ready.txt");
            assert(last_guest == 0x8009B258u);
            assert(guest_stack[1] == 101 && guest_stack[2] == 96);
            assert(guest_stack[4] == 91 && guest_stack[6] == 150);
            assert(psx_mod_read_word(cpu.gpr[29] + 16) == 0); /* restored */
            fclose(s_logf);
            return 0;
        }
        ev_label(&cpu, 0, 0);
        assert(psx_mod_read_word(0x80051A88u) == p + 28 * 11);
        /* First E comes from DANCE VIEW's native texture and selected palette. */
        assert(psx_mod_read_word(p + 28 + 20) == (0x3C00u << 16 | 72u << 8 | 60u));
    } else return 2;
    fclose(s_logf);
    return 0;
}
