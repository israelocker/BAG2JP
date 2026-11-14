/* Synthetic RAM around the production selector callbacks; no SDL renderer. */
#include <assert.h>
#include <stdint.h>
#include <stdatomic.h>
#include <stdlib.h>
#include <string.h>

struct CPUState { uint32_t gpr[32]; };
static uint8_t ram[0x200000];
static int versions[2], uploads;
static uint32_t last_upload;
static uint16_t uploaded_marker[2];
static uint32_t offset(uint32_t address) {
    assert(address >= 0x80000000u && address < 0x80200000u);
    return address - 0x80000000u;
}
static uint8_t psx_mod_read_byte(uint32_t a) { return ram[offset(a)]; }
static uint16_t psx_mod_read_half(uint32_t a) {
    return psx_mod_read_byte(a) | (uint16_t)psx_mod_read_byte(a + 1) << 8;
}
static uint32_t psx_mod_read_word(uint32_t a) {
    return psx_mod_read_half(a) | (uint32_t)psx_mod_read_half(a + 2) << 16;
}
static void psx_mod_write_byte(uint32_t a, uint8_t v) { ram[offset(a)] = v; }
static void psx_mod_write_half(uint32_t a, uint16_t v) {
    psx_mod_write_byte(a, v); psx_mod_write_byte(a + 1, v >> 8);
}
static void write_word(uint32_t a, uint32_t v) {
    psx_mod_write_half(a, v); psx_mod_write_half(a + 2, v >> 16);
}
static int bag2jp_bag1_get_version(int chr, int side) {
    assert(chr == 9 && side >= 0 && side < 2);
    return versions[side];
}
static void psx_mod_psyq_load_image(uint32_t x, uint32_t y, uint32_t w,
                                    uint32_t h, uint32_t source) {
    assert(x < 1024 && y < 512 && w && h);
    ++uploads; last_upload = source;
    uploaded_marker[x / 256u] = psx_mod_read_half(source + 235u * 2u);
}
static uint32_t psx_mod_call_guest(struct CPUState *cpu, uint32_t fn,
                                 uint32_t ret, uint32_t a, uint32_t b,
                                 uint32_t c, uint32_t d) {
    (void)cpu; (void)fn; (void)ret; (void)a; (void)b; (void)c; (void)d;
    assert(!"Unexpected guest sound call"); return 0;
}
static void cs_log(const char *fmt, ...) { (void)fmt; }
static void cs_stage_vblank(void) {}
static void cs_publish(void) {}

/* PRODUCTION_CALLBACKS */

static void setup(int side) {
    const uint32_t player = CS_PLAYER + (uint32_t)side * 0x20u;
    s_enabled = 1;
    s_cur_gaso[0] = s_cur_gaso[1] = -1;
    write_word(CS_GUARD1, CS_GUARD1_W);
    write_word(CS_GUARD2, CS_GUARD2_W);
    write_word(0x80090258u, 0x27BDFFD8u);
    psx_mod_write_byte(player + 0x19u, side);
    psx_mod_write_byte(player + 0x1au, 9);
    psx_mod_write_byte(player + 0x1eu, 1);
    write_word(0x8005e6a0u + (uint32_t)side * 4, 0xff);
    write_word(0x80096438u + 9 * 48 + 0x18u, 0x80180000u);
    write_word(0x800967c8u + 9 * 48 + 0x18u, 0x80181000u);
    for (int s = 0; s < 2; ++s) {
        const uint32_t rect = 0x80096458u + (uint32_t)s * 48;
        psx_mod_write_half(rect, (uint16_t)s * 256u);
        psx_mod_write_half(rect + 4, 256);
        psx_mod_write_half(rect + 6, 1);
    }
    psx_mod_write_half(0x800967e8u + 4, 256);
    psx_mod_write_half(0x800967e8u + 6, 1);
}

int main(int argc, char **argv) {
    assert(argc == 2);
    const int scenario = atoi(argv[1]);
    const int side = scenario == 1 ? 1 : 0;
    const uint32_t player = CS_PLAYER + (uint32_t)side * 0x20;
    const uint32_t label = 0x80096dd8u + 9 * 8;
    struct CPUState cpu = {0};
    setup(side);
    cpu.gpr[19] = player; cpu.gpr[29] = 0x801f0000u;
    versions[side] = scenario != 2;
    if (scenario == 6 || scenario == 11) {
        setup(1);
        versions[0] = 1; versions[1] = 0;
        if (scenario == 11) { s_pop[1].phase = P_OPEN; s_pop[1].version = 1; }
        cs_feedback_hook(&cpu, 0x80090258u);
        assert(uploaded_marker[0] == 0x7ffe);
        assert(uploaded_marker[1] == (scenario == 11 ? 0x7ffe : 0x7fff));
        if (scenario == 11) {
            s_pop[1].phase = P_SWALLOW;
            cs_feedback_hook(&cpu, 0x80090258u);
            assert(uploaded_marker[0] == 0x7ffe && uploaded_marker[1] == 0x7fff);
        }
        for (int s = 0; s < 2; ++s) {
            cpu.gpr[19] = CS_PLAYER + (uint32_t)s * 0x20;
            cs_char_name_hook(&cpu, 0x8009347cu);
            assert(psx_mod_read_byte(label + 1) == (s ? 62 : 226));
        }
        return 0;
    }
    if (scenario == 13) {
        setup(1);
        for (int reversed = 0; reversed < 2; ++reversed) {
            versions[0] = !reversed; versions[1] = reversed;
            cs_feedback_hook(&cpu, 0x80090258u);
            for (int s = 0; s < 2; ++s) {
                cpu.gpr[19] = CS_PLAYER + (uint32_t)s * 0x20;
                /* Retail code calls the name consumer at JAL80093474.
                 * Dispatch only a callback registered BEFORE that call. */
                if (TEST_NAME_SITE == 0x80093474u)
                    cs_char_name_hook(&cpu, TEST_NAME_SITE);
                assert(psx_mod_read_byte(label + 1) == (versions[s] ? 226 : 62));
                assert(psx_mod_read_byte(label + 2) == (versions[s] ? 115 : 129));
                assert(psx_mod_read_byte(label + 3) == (versions[s] ? 29 : 31));
                assert(psx_mod_read_byte(label + 4) == (versions[s] ? 1 : 0));
                if (TEST_NAME_SITE == 0x8009347cu)
                    cs_char_name_hook(&cpu, TEST_NAME_SITE);
            }
        }
        return 0;
    }
    if (scenario == 7) { s_pop[side].phase = P_REPLAY; s_pop[side].version = 0; }
    if (scenario == 8) {
        psx_mod_write_byte(player + 0x1a, 0); /* Heat is untouched. */
        psx_mod_write_byte(label + 1, 0xaa);
        cs_feedback_hook(&cpu, 0x80090258u);
        cs_char_name_hook(&cpu, 0x8009347cu);
        assert(uploads == 0 && psx_mod_read_byte(label + 1) == 0xaa);
        return 0;
    }
    if (scenario == 9) {
        write_word(0x80096f94u, 2); /* Stage select uses confirmed character. */
        write_word(0x8005e6a0u, 9);
        psx_mod_write_byte(player + 0x1a, 0);
        cs_feedback_hook(&cpu, 0x80090258u);
        assert(last_upload == 0x80181000u);
        assert(psx_mod_read_half(last_upload + 235 * 2) == 0x7ffe);
        return 0;
    }
    if (scenario == 10) {
        cs_feedback_hook(&cpu, 0x80090258u);
        cs_vblank();
        cs_feedback_hook(&cpu, 0x80090258u);
        assert(uploads == 1);
        return 0;
    }
    if (scenario == 3) { s_pop[side].phase = P_OPEN; s_pop[side].version = 0; }
    if (scenario == 4) { s_pop[side].phase = P_SWALLOW; s_pop[side].version = 0; }
    if (scenario == 5) {
        /* Native overlay reload restores stock CLUTs but not host statics. */
        write_word(0x8005e6a0u, 9);
        cs_feedback_hook(&cpu, 0x80090258u);
        assert(uploads == 1);
        write_word(CS_GUARD1, 0);
        cs_vblank();
        write_word(CS_GUARD1, CS_GUARD1_W);
        psx_mod_write_half(0x80180000u + 235 * 2, 0x7fff);
        write_word(0x8005e6a0u, 9);
        cs_feedback_hook(&cpu, 0x80090258u);
        assert(uploads == 2);
        assert(last_upload == 0x80180000u);
        assert(psx_mod_read_half(0x80180000u + 235 * 2) == 0x7ffe);
        return 0;
    }
    cs_feedback_hook(&cpu, 0x80090258u);
    if (scenario == 12) {
        if (TEST_NAME_SITE == 0x80093474u) cs_char_name_hook(&cpu, TEST_NAME_SITE);
        /* Initial consumer must see GAS-O, not the descriptor from another player. */
        assert(psx_mod_read_byte(label + 1) == 226);
        assert(psx_mod_read_byte(label + 4) == 1);
        return 0;
    }
    cs_char_name_hook(&cpu, 0x8009347cu);
    const int expected_gaso = scenario != 2 && scenario != 3 && scenario != 7;
    assert(psx_mod_read_half(0x80180000u + 235 * 2) ==
           (expected_gaso ? 0x7ffe : 0x7fff));
    assert(psx_mod_read_byte(label + 1) == (expected_gaso ? 226 : 62));
    assert(psx_mod_read_byte(cpu.gpr[29] + 0x28) == (expected_gaso ? 0x20 : 0x40));
    assert(versions[side] == (scenario != 2));
    return 0;
}
