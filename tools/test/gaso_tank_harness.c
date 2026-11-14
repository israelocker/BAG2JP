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
/* First drawn tick: descent height 1200*5^2/6^2 = 833, so y=120+(1600-1164-833)/6. */
#define FIRST_DROP_CAP_Y 54
static uint8_t ram[RAM_SIZE];
#define PSX_MOD_DISPLAY_PIXEL_ASPECT 1
static uint32_t pixel_aspect_num = 5u, pixel_aspect_den = 6u;
static int pixel_aspect_available = 1;
static int psx_mod_display_pixel_aspect(uint32_t *n, uint32_t *d) {
    *n = pixel_aspect_num; *d = pixel_aspect_den;
    return pixel_aspect_available;
}

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
static int bag1_enabled = 1;
int bag2jp_bag1_get_version(int character, int side) {
    return bag1_enabled && character == 9 && side == 0;
}
static uint32_t hits[2];
uint32_t bag2jp_gaso_caught_hits(uint32_t side) { return hits[side]; }
static uint32_t lifecycle_epoch;
uint32_t bag2jp_gaso_caught_epoch(void) { return lifecycle_epoch; }
static uint32_t epoch_hits[2];
uint32_t bag2jp_gaso_caught_epoch_hits(uint32_t side) { return epoch_hits[side]; }
static int owns_slot1 = 1;
static uint32_t owned_actors[2] = {0u, ACTOR1};
int bag2jp_gaso_caught_owns_slot1(uint32_t side, uint32_t actor) {
    return owns_slot1 && side < 2u && owned_actors[side] == actor;
}

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
    s_gaso_hits_synced = 1;
    hits[0] = hits[1] = s_gaso_hits_seen[0] = s_gaso_hits_seen[1] = 0;
    psx_mod_write_word(ACTOR1 + ACTOR_ANIM_OFF, GASO_TRAP_SLOT);
    psx_mod_write_word(B2_ROOT_ADDR, 19u);
    psx_mod_write_word(B2_HEAP_ADDR, PACKET_BASE);
    psx_mod_write_word(B2_OT_ADDR, OT_BASE);
    psx_mod_write_word(B2_GEOM_H_ADDR, 1000u);
    psx_mod_write_word(B2_CHAR_P1_ADDR, 9u);
    psx_mod_write_word(B2_DANCER_BASE, ACTOR0);
    psx_mod_write_word(B2_DANCER_BASE + 8u, ACTOR1);
    identity(B2_CAM_ROT_ADDR);
    psx_mod_write_half(B2_CAM_ROT_ADDR + 8u, (uint16_t)-4096);
    /* Above the cap, as in game: camera-facing culling hides it from below. */
    psx_mod_write_word(B2_CAM_TRANS_ADDR + 4u, 1600u);
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
        if (opcode == 0x30u) { /* opaque Gouraud cap; bubbles are semi-transparent 0x32 */
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

/* Walk OT slot 2 in GPU order (packets are prepended), tracking the draw mode
 * each packet sees as the GPU does, after one fresh tick. */
typedef struct { int glass, body, cap, rings, glints; } SlotCounts;
static SlotCounts walk_slot(void) {
    SlotCounts n = {0};
    psx_mod_write_word(OT_BASE + 8u, 0u);
    assert(bag2jp_gaso_tank_tick(700u) > 0);
    int abr = -1, opaque_seen = 0, glint_seen = 0, guard = 0, tinted = 0;
    uint32_t e1 = 0xFFFFFFFFu, tint_g[32];
    int tint_x[32];
    for (uint32_t link = psx_mod_read_word(OT_BASE + 8u) & 0xFFFFFFu; link;) {
        uint32_t packet = RAM_BASE | link;
        uint32_t cmd = psx_mod_read_word(packet + 4u), op = cmd >> 24;
        if (op == 0xE1u) { abr = (int)((cmd >> 5) & 3u); e1 = cmd & 0xFFFFFFu; }
        else if (op == 0x38u || op == 0x30u) {
            opaque_seen = 1;
            if (op == 0x38u) n.body++; else n.cap++;
        } else {
            /* Opaque metal is drawn last so it covers bubbles seen from above. */
            assert(!opaque_seen);
            /* Nothing averages (ABR0 would halve the rival's contrast). The
             * liquid adds a faint green tint first (owner request: as see-
             * through as BAG1); bubbles then add light: clear-centred outline
             * segments and a glint. Independent tint bounds, not macros:
             * (6,18,5) at x18/16..x36/16. */
            assert(!(op == 0x3Au && abr == 0));
            if (op == 0x3Au && (cmd & 0xFFFFFFu) != 0u) {
                assert(abr == 1 && e1 == 0x620u && n.rings == 0 && !glint_seen);
                for (uint32_t vertex = 0; vertex < 4u; ++vertex) {
                    uint32_t c = psx_mod_read_word(packet + 4u + vertex * 8u) & 0xFFFFFFu;
                    uint32_t r = c & 0xFFu, g = (c >> 8) & 0xFFu, b = c >> 16;
                    assert(r >= 6u && r <= 13u && g >= 20u && g <= 40u && b >= 5u && b <= 11u);
                    assert(tinted < 32);
                    tint_g[tinted] = g;
                    tint_x[tinted++] = (int16_t)psx_mod_read_word(packet + 8u + vertex * 8u);
                }
                n.glass++;
            } else if (op == 0x3Au) {
                assert(!glint_seen);
                assert(abr == 1 && (cmd & 0xFFFFFFu) == 0u);
                assert((psx_mod_read_word(packet + 12u) & 0xFFFFFFu) == GASO_BUBBLE_RIM);
                n.rings++;
             } else if (op == 0x32u) {
                glint_seen = 1;
                assert(abr == 1 && (cmd & 0xFFFFFFu) == GASO_GLINT_RGB);
                n.glints++;
            } else assert(0);
        }
        link = psx_mod_read_word(packet) & 0xFFFFFFu;
        assert(++guard < 1000);
    }
    /* Later packets never inherit the additive mode: dithered ABR0 restored. */
    assert(abr == 0 && e1 == 0x600u);
    /* The tint keeps the lateral shading: never brighter further right, and
     * the leftmost vertex is brighter than the rightmost. */
    int left = 0, right = 0;
    for (int i = 0; i < tinted; ++i) {
        for (int j = 0; j < tinted; ++j)
            assert(!(tint_x[i] < tint_x[j] && tint_g[i] < tint_g[j]));
        if (tint_x[i] < tint_x[left]) left = i;
        if (tint_x[i] > tint_x[right]) right = i;
    }
    if (tinted) assert(tint_g[left] > tint_g[right]);
    return n;
}

/* Independent fixture values, not production macros. At elapsed21 with H1000,
 * camera (0,4000,6000), the ring centre is (248,647); vertical outer/inner
 * radii (11,8). Horizontal expectations are independent fixture values for
 * each presentation ratio. These protect the requested smaller, fainter rim,
 * not presented roundness (which also depends on pixel/display aspect). */
static void check_bubble_rim_geometry(int outer_x, int inner_x, int centre_y) {
    int abr = -1, segments = 0;
    int xmin[2] = {32767, 32767}, xmax[2] = {-32768, -32768};
    int ymin[2] = {32767, 32767}, ymax[2] = {-32768, -32768};
    for (uint32_t link = psx_mod_read_word(OT_BASE + 8u) & 0xFFFFFFu; link;) {
        uint32_t packet = RAM_BASE | link;
        uint32_t cmd = psx_mod_read_word(packet + 4u);
        if ((cmd >> 24) == 0xE1u) abr = (int)((cmd >> 5) & 3u);
        if ((cmd >> 24) == 0x3Au && abr == 1 && (cmd & 0xFFFFFFu) == 0u) {
            for (uint32_t vertex = 0; vertex < 4u; ++vertex) {
                uint32_t colour = psx_mod_read_word(packet + 4u + vertex * 8u) & 0xFFFFFFu;
                int outer = (int)(vertex & 1u);
                assert(colour == (outer ? 0x3C3430u : 0u));
                uint32_t xy = psx_mod_read_word(packet + 8u + vertex * 8u);
                int x = (int16_t)xy, y = (int16_t)(xy >> 16);
                if (x < xmin[outer]) xmin[outer] = x;
                if (x > xmax[outer]) xmax[outer] = x;
                if (y < ymin[outer]) ymin[outer] = y;
                if (y > ymax[outer]) ymax[outer] = y;
            }
            segments++;
        }
        link = psx_mod_read_word(packet) & 0xFFFFFFu;
    }
    assert(segments == 16);
    assert(xmin[1] == 248 - outer_x && xmax[1] == 248 + outer_x &&
           ymin[1] == centre_y - 11 && ymax[1] == centre_y + 11);
    assert(xmin[0] == 248 - inner_x && xmax[0] == 248 + inner_x &&
           ymin[0] == centre_y - 8 && ymax[0] == centre_y + 8);
}

/* Run count ticks on a fresh packet heap; returns the last tick's packets. */
static int tick(uint32_t count) {
    static uint32_t frame = 700u;
    int emitted = 0;
    for (uint32_t i = 0; i < count; ++i) {
        psx_mod_write_word(B2_HEAP_ADDR, PACKET_BASE);
        emitted = bag2jp_gaso_tank_tick(frame++);
    }
    return emitted;
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
        /* A hit on side 1 drops the tank; the attack animation alone does not. */
        s_gaso_tank[0].active = 0;
        psx_mod_write_word(ACTOR0 + ACTOR_ANIM_OFF, GASO_ATTACK_ANIM);
        psx_mod_write_word(ACTOR0 + 0x1554u, 25u);
        assert(bag2jp_gaso_tank_tick(699u) == 0 && !s_gaso_tank[0].active);
        psx_mod_write_word(ACTOR0 + ACTOR_ANIM_OFF, 6u);
        psx_mod_write_word(ACTOR1 + ACTOR_ANIM_OFF, GASO_TRAP_BORROWED);
        psx_mod_write_word(B2_HEAP_ADDR, PACKET_BASE);
        hits[1] = 1;
    }
    if (scenario >= 21 && scenario <= 31) {
        if (scenario == 21 || scenario == 22) {
            /* Camera well above the cap: at y=1600 the shallow back cone of the
             * cap leaves triangles 3/7 edge-on (screen area2 = 2). */
            psx_mod_write_word(B2_CAM_TRANS_ADDR + 4u, 4000u);
        }
        if (scenario == 24) {
            /* Camera below the floor: the whole cap faces away. */
            psx_mod_write_word(B2_CAM_TRANS_ADDR + 4u, (uint32_t)-2000);
        }
        if (scenario >= 25) psx_mod_write_word(B2_CAM_TRANS_ADDR + 4u, 4000u);
        if (scenario == 25) pixel_aspect_den = 8u; /* 512x240 at4:3 */
        if (scenario == 26) { pixel_aspect_num = 35u; pixel_aspect_den = 32u; }
        if (scenario == 27) pixel_aspect_num = pixel_aspect_den = 1u;
        if (scenario == 28) pixel_aspect_num = 0u;
        if (scenario == 29) pixel_aspect_available = 0;
        if (scenario == 30) { pixel_aspect_num = 1u; pixel_aspect_den = UINT32_MAX; }
        if (scenario == 22) {
            /* Mirrored rival model (as scenario 2): culling must flip with it. */
            psx_mod_write_half(ACTOR1 + ACTOR_MATRIX_OFF, (uint16_t)-4096);
            psx_mod_write_word(ACTOR1 + B2_DANCER_ROOT_OFF, 300u);
        }
        if (scenario == 23) {
            /* Camera straight above the tank axis, looking down. */
            psx_mod_write_half(B2_CAM_ROT_ADDR + 8u, 0u);
            psx_mod_write_half(B2_CAM_ROT_ADDR + 10u, 4096u);
            psx_mod_write_half(B2_CAM_ROT_ADDR + 14u, (uint16_t)-4096);
            psx_mod_write_half(B2_CAM_ROT_ADDR + 16u, 0u);
            psx_mod_write_word(B2_CAM_TRANS_ADDR + 4u, 0u);
            psx_mod_write_word(B2_CAM_TRANS_ADDR + 8u, 3000u);
        }
        SlotCounts n = walk_slot();
        if (scenario == 21) {
            /* Hand-checked for this camera (no face within |area2| < 40): the
             * 4 front octagon faces, 14 metal quads and all 8 cap triangles. */
            assert(n.glass == 4 && n.body == 14 && n.cap == 8);
            check_bubble_rim_geometry(13, 10, 647);
        }
        if (scenario == 22) assert(n.glass == 4 && n.body == 14 && n.cap == 8);
        if (scenario == 23) assert(n.glass == 0 && n.cap == 8 && n.body > 0);
        if (scenario == 24) assert(n.glass == 4 && n.body == 10 && n.cap == 0);
        if (scenario >= 28 && scenario <= 30) {
            assert(n.rings == 0 && n.glints == 0 && n.glass > 0 && n.body > 0);
            return 0;
        }
        if (scenario == 25) check_bubble_rim_geometry(17, 13, 647);
        if (scenario == 26) check_bubble_rim_geometry(10, 8, 647);
        if (scenario == 27) check_bubble_rim_geometry(11, 8, 647);
        if (scenario == 31) {
            check_bubble_rim_geometry(13, 10, 647);
            pixel_aspect_den = 8u;
            psx_mod_write_word(B2_HEAP_ADDR, PACKET_BASE);
            (void)walk_slot();
            /* Tick22: rise advances native3216->3249, centre Y647->646. */
            check_bubble_rim_geometry(17, 13, 646);
        }
        /* One bubble: a 16-segment outline and an 8-triangle glint. */
        assert(n.rings == 16 && n.glints == 8);
        return 0;
    }
    if (scenario == 33) {
        /* Holding is now metadata-driven: neither recipient is pinned by the visual. */
        const uint32_t replacement = ACTOR1 + 0x2000u;
        owned_actors[0] = ACTOR0;
        psx_mod_write_word(ACTOR0 + ACTOR_ANIM_OFF, GASO_TRAP_BORROWED);
        psx_mod_write_word(ACTOR1 + ACTOR_ANIM_OFF, GASO_TRAP_BORROWED);
        psx_mod_write_word(ACTOR0 + 0x14B8u, (uint32_t)-500);
        psx_mod_write_word(ACTOR0 + 0x14C0u, 80u);
        psx_mod_write_word(ACTOR1 + 0x14B8u, 505u);
        psx_mod_write_word(ACTOR1 + 0x14C0u, 106u);
        tick(1u);
        psx_mod_write_word(ACTOR0 + 0x14B8u, (uint32_t)-504);
        psx_mod_write_word(ACTOR0 + 0x14C0u, 76u);
        psx_mod_write_word(ACTOR1 + 0x14B8u, 501u);
        tick(1u);
        assert((int32_t)psx_mod_read_word(ACTOR0 + 0x14B8u) == -504);
        assert(psx_mod_read_word(ACTOR0 + 0x14C0u) == 76u);
        assert(psx_mod_read_word(ACTOR1 + 0x14B8u) == 501u);
        memcpy(guest(replacement, 0x1800u), guest(ACTOR1, 0x1800u), 0x1800u);
        psx_mod_write_word(replacement + 0x14B8u, 123u);
        psx_mod_write_word(B2_DANCER_BASE + 8u, replacement);
        owned_actors[1] = replacement;
        tick(1u);
        assert(psx_mod_read_word(replacement + 0x14B8u) == 123u);
        psx_mod_write_word(replacement + 0x14B8u, 119u);
        tick(1u);
        assert(psx_mod_read_word(replacement + 0x14B8u) == 119u);
        /* Reset/load epoch must not restore an old coordinate on either side. */
        ++lifecycle_epoch;
        psx_mod_write_word(ACTOR0 + 0x14B8u, (uint32_t)-600);
        psx_mod_write_word(replacement + 0x14B8u, 610u);
        tick(1u);
        psx_mod_write_word(ACTOR0 + 0x14B8u, (uint32_t)-604);
        psx_mod_write_word(replacement + 0x14B8u, 606u);
        tick(1u);
        assert((int32_t)psx_mod_read_word(ACTOR0 + 0x14B8u) == -604);
        assert(psx_mod_read_word(replacement + 0x14B8u) == 606u);
        /* Publication changes do not grant the visual coordinate ownership. */
        owned_actors[1] = 0u;
        tick(1u);
        owned_actors[1] = replacement;
        psx_mod_write_word(replacement + 0x14B8u, 700u);
        tick(1u);
        psx_mod_write_word(replacement + 0x14B8u, 696u);
        tick(1u);
        assert(psx_mod_read_word(replacement + 0x14B8u) == 696u);
        return 0;
    }
    if (scenario == 32) {
        /* Clamp metadata replaces the vblank pin: base stays entirely native. */
        const uint32_t bx = ACTOR1 + 0x14B8u, by = ACTOR1 + 0x14BCu, bz = ACTOR1 + 0x14C0u;
        psx_mod_write_word(ACTOR1 + ACTOR_ANIM_OFF, GASO_TRAP_BORROWED);
        psx_mod_write_word(bx, 505u); psx_mod_write_word(by, 77u); psx_mod_write_word(bz, 106u);
        tick(1u);
        assert(psx_mod_read_word(bx) == 505u && psx_mod_read_word(bz) == 106u);
        psx_mod_write_word(bx, 501u); psx_mod_write_word(by, 70u); psx_mod_write_word(bz, 104u);
        tick(1u);
        assert(psx_mod_read_word(bx) == 501u && psx_mod_read_word(bz) == 104u);
        assert(psx_mod_read_word(by) == 70u); /* height stays native */
        /* An inactive visual cannot own coordinates either. */
        s_gaso_tank[0].active = 0;
        psx_mod_write_word(bx, (uint32_t)-3);
        tick(1u);
        assert((int32_t)psx_mod_read_word(bx) == -3);
        /* Leaving and reentering slot1 must not pin coordinates. */
        psx_mod_write_word(ACTOR1 + ACTOR_ANIM_OFF, 90u);
        psx_mod_write_word(bx, 300u);
        tick(1u);
        assert(psx_mod_read_word(bx) == 300u);
        psx_mod_write_word(ACTOR1 + ACTOR_ANIM_OFF, GASO_TRAP_BORROWED);
        psx_mod_write_word(bx, 400u);
        tick(1u);
        psx_mod_write_word(bx, 396u);
        tick(1u);
        assert(psx_mod_read_word(bx) == 396u);
        /* A slot1 that is not our publication, or the native hit slot, is untouched. */
        owns_slot1 = 0;
        psx_mod_write_word(bx, 250u);
        tick(2u);
        assert(psx_mod_read_word(bx) == 250u);
        owns_slot1 = 1;
        psx_mod_write_word(ACTOR1 + ACTOR_ANIM_OFF, GASO_TRAP_SLOT);
        tick(1u);
        psx_mod_write_word(bx, 240u);
        tick(1u);
        assert(psx_mod_read_word(bx) == 240u);
        /* A replacement actor never inherits the old anchor. */
        psx_mod_write_word(ACTOR1 + ACTOR_ANIM_OFF, GASO_TRAP_BORROWED);
        tick(1u);
        uint32_t replacement = ACTOR1 + 0x2000u;
        memcpy(guest(replacement, 0x1800u), guest(ACTOR1, 0x1800u), 0x1800u);
        psx_mod_write_word(replacement + 0x14B8u, 123u);
        psx_mod_write_word(B2_DANCER_BASE + 8u, replacement);
        tick(1u);
        assert(psx_mod_read_word(replacement + 0x14B8u) == 123u);
        /* Returning to combat must not reapply an old coordinate. */
        psx_mod_write_word(B2_DANCER_BASE + 8u, ACTOR1);
        psx_mod_write_word(bx, 600u);
        tick(1u);
        psx_mod_write_word(B2_ROOT_ADDR, 13u);
        tick(1u);
        psx_mod_write_word(B2_ROOT_ADDR, 19u);
        psx_mod_write_word(bx, 610u);
        tick(1u);
        psx_mod_write_word(bx, 606u);
        tick(1u);
        assert(psx_mod_read_word(bx) == 606u);
        return 0;
    }
    if (scenario == 34) {
        /* BAG1 801d6480/801d7218: the lock plays once, one update after the
         * first beat following the drop; bubbles start once the landed
         * counter exceeds 32 and re-arm within 33 frames. */
        s_gaso_tank[0].active = 0;
        hits[1] = 1;
        psx_mod_write_half(GASO_TANK_BEAT_ADDR, 7u);
        tick(1u);
        assert(s_gaso_tank[0].active && bag2jp_gaso_tank_take_cues() == 0u);
        tick(3u);
        assert(bag2jp_gaso_tank_take_cues() == 0u);
        psx_mod_write_half(GASO_TANK_BEAT_ADDR, 8u);
        tick(1u);
        assert(bag2jp_gaso_tank_take_cues() == 0u);
        tick(1u);
        assert(bag2jp_gaso_tank_take_cues() == GASO_TANK_CUE_LOCK_BIT);
        psx_mod_write_half(GASO_TANK_BEAT_ADDR, 9u);
        tick(4u);
        assert(bag2jp_gaso_tank_take_cues() == 0u);
        tick(27u);  /* elapsed 37: landed counter 32 */
        assert(bag2jp_gaso_tank_take_cues() == 0u);
        tick(1u);
        assert(bag2jp_gaso_tank_take_cues() == GASO_TANK_CUE_BUBBLE_BIT);
        unsigned plays = 0, gap = 0;
        for (unsigned i = 0; i < 330u; ++i) {
            tick(1u);
            if (bag2jp_gaso_tank_take_cues() == GASO_TANK_CUE_BUBBLE_BIT) { ++plays; gap = 0; }
            else assert(++gap <= 33u);
        }
        if (plays < 10u || plays > 60u) { fprintf(stderr, "bubble plays %u\n", plays); return 1; }
        return 0;
    }
    if (scenario == 35) {
        /* No cues once the tank is gone, and none survive a reset. */
        s_gaso_tank[0].active = 0;
        hits[1] = 1;
        tick(40u);
        (void)bag2jp_gaso_tank_take_cues();
        psx_mod_write_word(ACTOR1 + ACTOR_ANIM_OFF, 90u);
        tick(GASO_TANK_RELEASE_DUR);
        assert(s_gaso_tank[0].active);
        (void)bag2jp_gaso_tank_take_cues();
        s_gaso_tank[0].bubble_armed = 0;  /* the cut frame must not bubble */
        tick(1u);
        assert(!s_gaso_tank[0].active && bag2jp_gaso_tank_take_cues() == 0u);
        psx_mod_write_half(GASO_TANK_BEAT_ADDR, 1u);
        tick(40u);
        assert(bag2jp_gaso_tank_take_cues() == 0u);
        atomic_fetch_or(&s_gaso_tank_cues, GASO_TANK_CUE_BUBBLE_BIT);
        bag2jp_gaso_tank_reset();
        assert(bag2jp_gaso_tank_take_cues() == 0u);
        return 0;
    }
    if (scenario >= 6) {
        if (scenario == 6) {
            /* Held past the old fixed 92 frames while trapped, cut after release. */
            assert(tick(200u) > 0 && s_gaso_tank[0].active);
            psx_mod_write_word(ACTOR1 + ACTOR_ANIM_OFF, 90u);
            assert(tick(GASO_TANK_RELEASE_DUR) > 0 && s_gaso_tank[0].active);
            assert(tick(1u) == 0 && !s_gaso_tank[0].active);
        }
        if (scenario == 7) {
            /* Gas-O's next attack clears it; that attack's hit drops a new one. */
            s_gaso_tank[0].elapsed = 100u;   /* the attack started after the drop */
            psx_mod_write_word(ACTOR0 + ACTOR_ANIM_OFF, GASO_ATTACK_ANIM);
            psx_mod_write_word(ACTOR0 + 0x1554u, GASO_TANK_CLEAR_FRAME - 1u);
            assert(tick(1u) > 0 && s_gaso_tank[0].active);
            psx_mod_write_word(ACTOR0 + 0x1554u, GASO_TANK_CLEAR_FRAME);
            assert(tick(1u) == 0 && !s_gaso_tank[0].active);
            hits[1] = 2;
            assert(tick(1u) > 0 && s_gaso_tank[0].active && s_gaso_tank[0].elapsed == 1u);
            check_cap(256, FIRST_DROP_CAP_Y); /* Descent restarts. */
        }
        if (scenario == 8) {
            /* An attack already running when the tank dropped does not clear it. */
            s_gaso_tank[0].active = 0;
            psx_mod_write_word(ACTOR0 + ACTOR_ANIM_OFF, GASO_ATTACK_ANIM);
            psx_mod_write_word(ACTOR0 + 0x1554u, 100u);
            hits[1] = 1u;
            assert(tick(1u) > 0); /* Actual spawn observes the attack already in progress. */
            assert(tick(1u) > 0 && s_gaso_tank[0].active);
        }
        if (scenario == 9) {
            /* Hits counted before a reset are adopted, never replayed. */
            s_gaso_tank[0].active = 0;
            s_gaso_hits_synced = 0;
            hits[1] = 3;
            assert(tick(1u) == 0 && !s_gaso_tank[0].active);
            hits[1] = 4;
            assert(tick(1u) > 0 && s_gaso_tank[0].active);
        }
        if (scenario == 10) {
            /* Re-entering the trap cancels an interrupted release countdown. */
            psx_mod_write_word(ACTOR1 + ACTOR_ANIM_OFF, 90u);
            assert(tick(8u) > 0);
            psx_mod_write_word(ACTOR1 + ACTOR_ANIM_OFF, GASO_TRAP_SLOT);
            assert(tick(1u) > 0);
            psx_mod_write_word(ACTOR1 + ACTOR_ANIM_OFF, 90u);
            assert(tick(9u) > 0 && s_gaso_tank[0].active);
            assert(tick(1u) == 0 && !s_gaso_tank[0].active);
        }
        if (scenario == 11 || scenario == 13) {
            if (scenario == 11) psx_mod_write_word(B2_CHAR_P1_ADDR, 0u);
            else bag1_enabled = 0;
            assert(tick(1u) == 0 && !s_gaso_tank[0].active);
        }
        if (scenario == 12) {
            /* Valid replacement dancer must not inherit the old actor's tank. */
            uint32_t replacement = ACTOR1 + 0x2000u;
            memcpy(guest(replacement, 0x1800u), guest(ACTOR1, 0x1800u), 0x1800u);
            psx_mod_write_word(B2_DANCER_BASE + 8u, replacement);
            assert(tick(1u) == 0 && !s_gaso_tank[0].active);
        }
        if (scenario == 14) {
            /* An unrelated slot1 must not prolong the trap. */
            owns_slot1 = 0;
            psx_mod_write_word(ACTOR1 + ACTOR_ANIM_OFF, GASO_TRAP_BORROWED);
            assert(tick(9u) > 0 && s_gaso_tank[0].active);
            assert(tick(1u) == 0 && !s_gaso_tank[0].active);
        }
        if (scenario == 15) {
            /* Load/reset while root stays 19: neither the visual nor old hits survive. */
            hits[1] = 2u;
            epoch_hits[1] = hits[1];
            ++lifecycle_epoch;
            assert(tick(1u) == 0 && !s_gaso_tank[0].active);
            hits[1] = 3u;
            assert(tick(1u) > 0 && s_gaso_tank[0].active);
        }
        if (scenario == 16) {
            /* A paused frame in the same attack cannot become a new attack by ageing. */
            s_gaso_tank[0].active = 0;
            psx_mod_write_word(ACTOR0 + ACTOR_ANIM_OFF, GASO_ATTACK_ANIM);
            psx_mod_write_word(ACTOR0 + 0x1554u, 100u);
            hits[1] = 1u;
            assert(tick(1u) > 0);
            assert(tick(150u) > 0 && s_gaso_tank[0].active);
        }
        if (scenario == 17) {
            /* Observe an attack edge even when no draw packet can be emitted. */
            assert(tick(1u) > 0);
            psx_mod_write_word(B2_GEOM_H_ADDR, 0u);
            psx_mod_write_word(ACTOR0 + ACTOR_ANIM_OFF, GASO_ATTACK_ANIM);
            psx_mod_write_word(ACTOR0 + 0x1554u, GASO_TANK_CLEAR_FRAME - 1u);
            assert(tick(1u) == 0);
            assert(s_gaso_tank[0].clear_on_attack);
            psx_mod_write_word(ACTOR0 + 0x1554u, GASO_TANK_CLEAR_FRAME);
            assert(tick(1u) == 0 && !s_gaso_tank[0].active);
            psx_mod_write_word(B2_GEOM_H_ADDR, 1000u);
            assert(tick(1u) == 0);
        }
        if (scenario == 18) {
            /* A broken renderer must not pause the lifetime bound. */
            psx_mod_write_word(B2_GEOM_H_ADDR, 0u);
            assert(tick(1801u) == 0);
            psx_mod_write_word(B2_GEOM_H_ADDR, 1000u);
            assert(tick(1u) == 0 && !s_gaso_tank[0].active);
        }
        if (scenario == 19) {
            /* Reset/load -> new hit -> first tick must keep the post-reset hit. */
            hits[1] = 2u;
            epoch_hits[1] = hits[1];
            ++lifecycle_epoch;
            hits[1] = 3u;
            assert(tick(1u) > 0 && s_gaso_tank[0].active);
            assert(s_gaso_tank[0].elapsed == 1u);
        }
        if (scenario == 20) {
            /* Leaving combat adopts old hits, not the first future combat hit. */
            psx_mod_write_word(B2_ROOT_ADDR, 13u);
            hits[1] = 2u;
            assert(tick(1u) == 0 && !s_gaso_tank[0].active);
            psx_mod_write_word(B2_ROOT_ADDR, 19u);
            hits[1] = 3u;
            assert(tick(1u) > 0 && s_gaso_tank[0].active);
        }
        return 0;
    }
    int emitted = bag2jp_gaso_tank_tick(700u);
    if (scenario == 3 || scenario == 4) {
        assert(emitted == 0 && s_gaso_tank[0].active == 0);
        psx_mod_write_word(B2_DANCER_BASE + 8u, ACTOR1);
        assert(bag2jp_gaso_tank_tick(701u) == 0);
        return 0;
    }
    if (scenario == 5) {
        emitted = tick(GASO_TANK_FALL_DUR - 1u);
        check_cap(256, 192);
        int floor_vertex = 0;
        uint32_t end = psx_mod_read_word(B2_HEAP_ADDR);
        for (uint32_t packet = PACKET_BASE; packet < end;) {
            uint32_t tag = psx_mod_read_word(packet);
            if ((psx_mod_read_word(packet + 4u) >> 24) == 0x38u) { /* opaque metal */
                for (unsigned v = 0; v < 4; ++v) {
                    uint32_t xy = psx_mod_read_word(packet + 8u + v * 8u);
                    if ((int16_t)xy == 292 && (int16_t)(xy >> 16) == 386)
                        floor_vertex = 1;
                }
            }
            packet += ((tag >> 24) + 1u) * 4u;
        }
        assert(floor_vertex); /* Native vertex 0: local (259,0,0), not pelvis Y500. */
    }
    assert(emitted > 0);
    /* Hand-derived from the camera above: x=256+85%*x/6,
     * y=120+(1600-y)/6; cap height floor(4480*.26)=1164. */
    if (scenario == 0) check_cap(256, 192);
    if (scenario == 1) check_cap(256, FIRST_DROP_CAP_Y);
    if (scenario == 2) check_cap(214, 172);
    return 0;
}
