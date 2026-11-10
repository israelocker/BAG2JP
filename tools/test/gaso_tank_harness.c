/* Compile the real tank/packet/projection code; only the guest RAM API is fake. */
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define RAM_BASE 0x80000000u
#define RAM_SIZE 0x00800000u
#define ACTOR0 0x80200000u
#define ACTOR1 0x80202000u
#define PACKET_BASE 0x80300000u
#define OT_BASE 0x80400000u
#define ACTOR_MATRIX_OFF 0x14C4u
#define ACTOR_ANIM_OFF 0x154Cu
static uint8_t ram[RAM_SIZE];

static void *guest(uint32_t address, size_t size) {
    assert(address >= RAM_BASE && size <= RAM_SIZE);
    assert(address - RAM_BASE <= RAM_SIZE - size);
    return ram + address - RAM_BASE;
}
static uint32_t psx_mod_read_word(uint32_t address) {
    uint32_t value; memcpy(&value, guest(address, sizeof(value)), sizeof(value)); return value;
}
static uint16_t psx_mod_read_half(uint32_t address) {
    uint16_t value; memcpy(&value, guest(address, sizeof(value)), sizeof(value)); return value;
}
static void psx_mod_write_word(uint32_t address, uint32_t value) {
    memcpy(guest(address, sizeof(value)), &value, sizeof(value));
}
static void psx_mod_write_half(uint32_t address, uint16_t value) {
    memcpy(guest(address, sizeof(value)), &value, sizeof(value));
}
void b1v_log(const char *format, ...) { (void)format; }
int bag2jp_bag1_get_version(int character, int side) { return character == 9 && side == 0; }

#include "bag2jp_strike_shot.h"
#include "bag2jp_gaso_tank.h"

static void identity(uint32_t address) {
    for (unsigned i = 0; i < 9; ++i)
        psx_mod_write_half(address + i * 2u, i % 4u == 0u ? 4096u : 0u);
}

static void seed(uint32_t elapsed) {
    memset(ram, 0, sizeof(ram));
    bag2jp_gaso_tank_reset();
    s_gaso_combat_frame = 600u;
    psx_mod_write_word(B2_ROOT_ADDR, 19u);
    psx_mod_write_word(B2_HEAP_ADDR, PACKET_BASE);
    psx_mod_write_word(B2_OT_ADDR, OT_BASE);
    psx_mod_write_word(B2_GEOM_H_ADDR, 1000u);
    psx_mod_write_word(B2_CHAR_P1_ADDR, 9u);
    psx_mod_write_word(B2_DANCER_BASE, ACTOR0);
    psx_mod_write_word(B2_DANCER_BASE + 8u, ACTOR1);
    identity(B2_CAM_ROT_ADDR);
    psx_mod_write_half(B2_CAM_ROT_ADDR + 8u, (uint16_t)-4096);
    psx_mod_write_word(B2_CAM_TRANS_ADDR + 4u, 600u);
    psx_mod_write_word(B2_CAM_TRANS_ADDR + 8u, 6000u);
    identity(ACTOR1 + ACTOR_MATRIX_OFF);
    psx_mod_write_word(ACTOR1 + B2_DANCER_ROOT_OFF + 4u, 500u);
    s_gaso_tank[0] = (GasoTankState){.active = 1, .side = 0,
        .opp_dancer = ACTOR1, .elapsed = elapsed};
}

static void check_cap(int expected_x, int expected_y) {
    uint32_t end = psx_mod_read_word(B2_HEAP_ADDR);
    for (uint32_t packet = PACKET_BASE; packet < end;) {
        uint32_t tag = psx_mod_read_word(packet);
        uint32_t opcode = psx_mod_read_word(packet + 4u) >> 24;
        if (opcode == 0x20u) {
            uint32_t xy = psx_mod_read_word(packet + 8u);
            int x = (int16_t)xy, y = (int16_t)(xy >> 16);
            if (x != expected_x || y != expected_y) {
                fprintf(stderr, "cap (%d,%d), expected (%d,%d)\n", x, y, expected_x, expected_y);
                exit(1);
            }
            return;
        }
        packet += ((tag >> 24) + 1u) * 4u;
    }
    fprintf(stderr, "No cap emitted\n"); exit(1);
}

int main(int argc, char **argv) {
    assert(argc == 2);
    int scenario = atoi(argv[1]);
    seed(scenario == 1 ? 0u : 20u);
    if (scenario == 2) {
        /* A model-space X reflection and Y translation must reach the tank too. */
        psx_mod_write_half(ACTOR1 + ACTOR_MATRIX_OFF, (uint16_t)-4096);
        psx_mod_write_word(ACTOR1 + ACTOR_MATRIX_OFF + 0x18u, 120u);
        psx_mod_write_word(ACTOR1 + B2_DANCER_ROOT_OFF, 300u);
    }
    if (scenario == 3) psx_mod_write_word(B2_DANCER_BASE + 8u, 0u);
    if (scenario == 4) psx_mod_write_word(B2_DANCER_BASE + 8u, 0x807FF000u);
    if (scenario == 5) {
        s_gaso_tank[0].active = 0;
        psx_mod_write_word(ACTOR0 + ACTOR_ANIM_OFF, GASO_ATTACK_ANIM);
        psx_mod_write_word(ACTOR0 + 0x1554u, 25u);
    }
    int emitted = bag2jp_gaso_tank_tick(700u);
    if (scenario == 3 || scenario == 4) {
        assert(emitted == 0 && s_gaso_tank[0].active == 0);
        psx_mod_write_word(B2_DANCER_BASE + 8u, ACTOR1);
        assert(bag2jp_gaso_tank_tick(701u) == 0);
        return 0;
    }
    if (scenario == 5) {
        for (unsigned tick = 1; tick < 12; ++tick) {
            psx_mod_write_word(B2_HEAP_ADDR, PACKET_BASE);
            emitted = bag2jp_gaso_tank_tick(700u + tick);
        }
        check_cap(256, 56);
        int floor_vertex = 0;
        uint32_t end = psx_mod_read_word(B2_HEAP_ADDR);
        for (uint32_t packet = PACKET_BASE; packet < end;) {
            uint32_t tag = psx_mod_read_word(packet);
            if ((psx_mod_read_word(packet + 4u) >> 24) == 0x3au) {
                for (unsigned v = 0; v < 4; ++v) {
                    uint32_t xy = psx_mod_read_word(packet + 8u + v * 8u);
                    if ((int16_t)xy == 309 && (int16_t)(xy >> 16) == 220)
                        floor_vertex = 1;
                }
            }
            packet += ((tag >> 24) + 1u) * 4u;
        }
        assert(floor_vertex); /* Native vertex 0: local (378,0,0), not pelvis Y500. */
    }
    assert(emitted > 0);
    /* Hand-derived from the camera above: x=256+85%*x/6,
     * y=120+(600-y)/6; cap height floor(4480*.22)=985. */
    if (scenario == 0) check_cap(256, 56);
    if (scenario == 1) check_cap(256, -112); /* First tick: descent height 1008. */
    if (scenario == 2) check_cap(214, 36);
    return 0;
}
