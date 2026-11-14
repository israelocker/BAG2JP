/* Synthetic dancer control blocks, production BAG1 leash proportion. */
#undef NDEBUG
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

enum { BASE = 0x80000000u, SIZE = 0x800000u };
static uint8_t ram[SIZE];
static unsigned writes;
static uint32_t psx_mod_read_word(uint32_t a) {
    assert(a >= BASE && a - BASE <= SIZE - 4u);
    uint32_t v; memcpy(&v, ram + (a - BASE), 4); return v;
}
static void psx_mod_write_word(uint32_t a, uint32_t v) {
    assert(a >= BASE && a - BASE <= SIZE - 4u);
    memcpy(ram + (a - BASE), &v, 4); ++writes;
}
#include "bag2jp_bag1_leash.h"
#include "bag2jp_bag1_center.h"

/* Literal control blocks: FUN_8001E0F4 passes 0x8005F820 + {0, 0x4C, 0x98, 0xE4}. */
static const uint32_t CTL[4] = {0x8005F820u, 0x8005F86Cu, 0x8005F8B8u, 0x8005F904u};
static const uint32_t DANCER[4] = {0x80100000u, 0x80102000u, 0x80104000u, 0x80106000u};

static void put_word(uint32_t address, uint32_t value) { memcpy(ram + address - BASE, &value, 4); }

static void init_ctl(int slot, int32_t home_x, uint32_t radius) {   /* FUN_8002D85C + rescale */
    put_word(0x80089200u, 0x80108000u);
    put_word(0x80108004u, 256u);
    memcpy(ram + (CTL[slot] - BASE), &DANCER[slot], 4);
    memcpy(ram + (CTL[slot] + 0x28u - BASE), &home_x, 4);
    memcpy(ram + (CTL[slot] + 0x38u - BASE), &radius, 4);
    put_word(CTL[slot] + 0x3Cu, radius);   /* Unscaled table radius (native 0x8002D920). */
}
static uint32_t radius_of(int slot) { return psx_mod_read_word(CTL[slot] + 0x38u); }

static void test_wider_home_keeps_tight_radius(void) {
    memset(ram, 0, sizeof ram); b1leash_forget();
    for (int side = 0; side < 2; ++side) {
        const int slot = side * 2;
        init_ctl(slot, side ? 870 : -870, 440);
        put_word(DANCER[slot] + 4u, (uint32_t)(9 + side * 256));
        put_word(0x8005F808u + (uint32_t)slot * 4u, DANCER[slot]);
        put_word(0x80051918u, 0x82828282u);
        put_word(0x8005191Cu, 0x82825682u); /* stage5 native86, others130 */
        put_word(0x80051920u, 0x82828282u); /* stage11 keeps separate native path */
        assert(b1leash_apply(slot, DANCER[slot]) == 199);
        assert(b1center_radius_ready(CTL[slot], side ? 870 : -870, 199));
        const uint32_t vector = 0x80109000u;
        put_word(0x8005D2C4u, 2u);
        put_word(vector, (uint32_t)(side ? 520 : -520));
        put_word(vector + 4u, 123u); put_word(vector + 8u, 0u);
        writes = 0;
        assert(b1home_apply(slot, DANCER[slot], vector) == 1 && writes == 1);
        assert((int32_t)psx_mod_read_word(vector) == (side ? 870 : -870));
        assert(psx_mod_read_word(vector + 4u) == 123u && psx_mod_read_word(vector + 8u) == 0u);
        assert(b1home_apply(slot, DANCER[slot], vector) == 0 && writes == 1);
        const uint32_t excluded[][2] = {
            {0x8005D2C4u,4u}, {0x80108000u,5u}, {0x80108000u,11u},
            {0x80108004u,0u}, {0x80108004u,0xFFFFu}, {0x80089200u,0u},
            {DANCER[slot]+4u,10u+(uint32_t)side*256u},
            {DANCER[slot]+4u,14u+(uint32_t)side*256u},
            {DANCER[slot]+4u,9u+(uint32_t)(side+2)*256u}, {vector+8u,1u},
        };
        for (unsigned i=0; i<sizeof excluded/sizeof excluded[0]; ++i) {
            put_word(vector, (uint32_t)(side ? 520 : -520));
            uint32_t old = psx_mod_read_word(excluded[i][0]);
            put_word(excluded[i][0], excluded[i][1]); writes = 0;
            assert(b1home_apply(slot, DANCER[slot], vector) == 0 && writes == 0);
            put_word(excluded[i][0], old);
        }
        put_word(0x80108004u,128u);
        put_word(vector,(uint32_t)(side ? 260 : -260)); writes = 0;
        assert(b1home_apply(slot,DANCER[slot],vector) == 1 && writes == 1);
        assert((int32_t)psx_mod_read_word(vector) == (side ? 435 : -435));
        assert(b1home_reference(CTL[slot],side ? 435 : -435) == (side ? 260 : -260));
        put_word(0x80108004u,256u);
        put_word(DANCER[slot],0x01000000u);
        put_word(CTL[slot]+4u,0x1000u); put_word(CTL[slot]+0xCu,1u);
        put_word(0x8005D3D4u,19u); put_word(0x8005D3D8u,1u);
        /* Restore guest widened home/radius while host latch held INT_MAX. */
        put_word(CTL[slot]+0x38u,0x7FFFFFFFu);
        assert(b1leash_apply(slot,DANCER[slot]) == 0);
        put_word(CTL[slot]+0x38u,199u);
        b1center_forget(); /* Deliberately retain the stale host INT_MAX latch. */
        assert(b1leash_radius[slot] == 0x7FFFFFFFu);
        for (uint32_t phase=3;phase<=4;++phase) {
            const int32_t home = side ? 870 : -870;
            put_word(0x8005D3DCu,phase);
            put_word(DANCER[slot]+0x154Cu,phase==3 ? 45u : 67u);
            put_word(DANCER[slot]+0x810u,(uint32_t)(home+100));
            put_word(DANCER[slot]+0x818u,100u);
            for (uint32_t tick=1;tick<=240;++tick) {
                for (unsigned axis=0;axis<2;++axis) {
                    const uint32_t root=DANCER[slot]+0x810u+8u*axis;
                    const uint32_t base=DANCER[slot]+0x14B8u+8u*axis;
                    put_word(base,psx_mod_read_word(root));
                }
                b1center_apply(slot,DANCER[slot],tick+phase*1000u);
                put_word(DANCER[slot]+0x810u,psx_mod_read_word(DANCER[slot]+0x14B8u));
                put_word(DANCER[slot]+0x818u,psx_mod_read_word(DANCER[slot]+0x14C0u));
            }
            int32_t x=(int32_t)psx_mod_read_word(DANCER[slot]+0x810u);
            int32_t z=(int32_t)psx_mod_read_word(DANCER[slot]+0x818u);
            assert(x>=home-(phase==3 ? 16 : 0) && x<=home+(phase==3 ? 16 : 0));
            assert(z>=0 && z<=(phase==3 ? 16 : 0) && radius_of(slot)==199u);
            assert(b1leash_radius[slot] == 0x7FFFFFFFu);
        }
    }
}

/* Measured gf15504 roots/bases, accepted bag1-release-autoplay capture.
 * The pose consumer is modeled as root += base delta (settled blend only). */
static void init_end_center(void) {
    memset(ram, 0, sizeof ram); b1leash_forget(); b1center_forget();
    put_word(0x8005D3D4u, 19u); put_word(0x8005D2C4u, 2u);
    put_word(0x8005D3D8u, 1u); put_word(0x8005D3DCu, 4u);
    const int32_t root[2][3] = {{-380,473,-275}, {649,520,272}};
    const int32_t base[2][3] = {{-378,0,-308}, {649,0,283}};
    for (int side = 0; side < 2; ++side) {
        const int slot = side * 2;
        init_ctl(slot, side ? 520 : -520, 440);
        assert(b1leash_apply(slot, DANCER[slot]) == 199);
        put_word(0x8005F808u + 4u * slot, DANCER[slot]);
        put_word(CTL[slot] + 0xCu, 1u);
        put_word(CTL[slot] + 4u, 0x1000u);
        put_word(DANCER[slot], 0x01000000u);  /* actor[3] active */
        put_word(DANCER[slot] + 0x154Cu, 68u);
        for (unsigned axis = 0; axis < 3; ++axis) {
            put_word(DANCER[slot] + 0x810u + axis*4u, (uint32_t)root[side][axis]);
            put_word(DANCER[slot] + 0x14B8u + axis*4u, (uint32_t)base[side][axis]);
        }
    }
}

static void test_end_center(void) {
    for (int idle_case = 0; idle_case < 2; ++idle_case) {
        init_end_center();
        if (idle_case == 1) {
            put_word(DANCER[0] + 0x154Cu, 67u);
            put_word(DANCER[2] + 0x154Cu, 67u);
        }
        for (uint32_t tick = 1; tick <= 160; ++tick) {
            for (int slot = 0; slot <= 2; slot += 2) {
                const uint32_t d = DANCER[slot];
                int32_t old_base[2], old_root[2];
                for (unsigned axis = 0; axis < 2; ++axis) {
                    old_base[axis] = (int32_t)psx_mod_read_word(d + 0x14B8u + axis*8u);
                    old_root[axis] = (int32_t)psx_mod_read_word(d + 0x810u + axis*8u);
                }
                b1center_apply(slot, d, tick);
                const unsigned once = writes;
                b1center_apply(slot, d, tick);
                assert(writes == once);  /* duplicate callback in same VBlank */
                for (unsigned axis = 0; axis < 2; ++axis) {
                    const int32_t home = axis ? 0 : (slot ? 520 : -520);
                    int32_t delta = (int32_t)psx_mod_read_word(d + 0x14B8u + axis*8u) - old_base[axis];
                    assert(delta >= -8 && delta <= 8);
                    int32_t now = old_root[axis] + delta;
                    assert((int64_t)(now-home)*(now-home) <= (int64_t)(old_root[axis]-home)*(old_root[axis]-home));
                    put_word(d + 0x810u + axis*8u, (uint32_t)now);
                }
                assert(psx_mod_read_word(d + 0x814u) == (slot ? 520u : 473u));
                assert(psx_mod_read_word(d + 0x14BCu) == 0u && radius_of(slot) == 199u);
            }
        }
        assert((int32_t)psx_mod_read_word(DANCER[0]+0x810u) == -520);
        assert((int32_t)psx_mod_read_word(DANCER[2]+0x810u) == 520);
        assert(psx_mod_read_word(DANCER[0]+0x818u) == 0u);
        assert(psx_mod_read_word(DANCER[2]+0x818u) == 0u);
    }
}

static void test_center_restore(void) {
    init_end_center();
    static uint8_t snapshot[SIZE];
    memcpy(snapshot, ram, sizeof ram);
    put_word(CTL[0]+0x38u, 0x7FFFFFFFu);
    assert(b1leash_apply(0, DANCER[0]) == 0);
    assert(b1leash_radius[0] == 0x7FFFFFFFu);
    memcpy(ram, snapshot, sizeof ram); /* guest restored, host leash cache is not */
    b1center_forget(); /* actual composed restore resets only load/center latches */
    assert(b1leash_apply(0, DANCER[0]) == 0); /* 199 is not native 440 */
    writes = 0;
    b1center_apply(0, DANCER[0], 1);
    assert(writes == 2);
    assert((int32_t)psx_mod_read_word(DANCER[0]+0x14B8u) == -383);
    assert((int32_t)psx_mod_read_word(DANCER[0]+0x14C0u) == -300);
}

static void test_center_exclusions(void) {
    /* Mutate one real eligibility fact at a time; all writes must be refused. */
    const uint32_t excluded[][2] = {
        {0x8005D3D4u, 13}, {0x8005D3D8u, 0}, {0x8005D3DCu, 2},
        {0x8005D3DCu, 5}, {0x8005D3DCu, 7}, {0x8005D3E4u, 1},
        {0x8005D2C4u, 0}, {0x8005D2C4u, 3}, {0x8005F808u, 0},
        {0x8005F820u, 0}, {0x8005F858u, 0x7FFFFFFFu},
        {0x8005F858u, 0}, {0x8005F858u, 440}, {0x8005F848u, 0},
        {0x8005F848u, 520}, {0x8005F850u, 1}, {0x8005F82Cu, 0},
        {0x80100000u, 0}, {0x8005F824u, 0xFFF}, {0x8010154Cu, 66},
        {0x8010154Cu, 69}, {0x8010154Cu, 89},
        {0x8010154Cu, 96}, {0x8010154Cu, 102}, {0x8010154Cu, 126},
        {0x80089200u, 0}, {0x80089200u, 0x807FFFFCu},
        {0x80108004u, 0}, {0x80108004u, 0xFFFFu}, {0x8005F85Cu, 0x10000u},
    };
    for (unsigned i = 0; i < sizeof excluded / sizeof excluded[0]; ++i) {
        init_end_center();
        put_word(excluded[i][0], excluded[i][1]);
        if (excluded[i][0] == 0x8005F858u && excluded[i][1] != 440u)
            b1leash_radius[0] = excluded[i][1]; /* VBlank may already latch release. */
        writes = 0;
        b1center_apply(0, DANCER[0], 1);
        assert(writes == 0);
    }
    const int slots[] = {-1, 1, 3, 4};
    for (unsigned i = 0; i < sizeof slots / sizeof slots[0]; ++i) {
        init_end_center(); writes = 0;
        b1center_apply(slots[i], DANCER[0], 1);
        assert(writes == 0);
    }
    const uint32_t invalid[] = {0, 0x8000FFFCu, 0x807FEAA8u, 0x80100001u, 0xFFFFFFFFu};
    for (unsigned i = 0; i < sizeof invalid / sizeof invalid[0]; ++i) {
        init_end_center(); writes = 0;
        b1center_apply(0, invalid[i], 1);
        assert(writes == 0);
    }
    init_end_center(); b1leash_forget(); writes = 0;
    b1center_apply(0, DANCER[0], 1); assert(writes == 2); /* restored RAM is sufficient */
    init_end_center(); writes = 0;
    b1center_apply(0, DANCER[0], 0); assert(writes == 2);
    b1center_forget();
    b1center_apply(0, DANCER[0], 0); assert(writes == 4);
    /* Bounded arithmetic: stale/extreme coordinates never overflow base. */
    put_word(DANCER[0] + 0x810u, (uint32_t)INT32_MIN);
    put_word(DANCER[0] + 0x14B8u, (uint32_t)INT32_MAX); writes = 0;
    b1center_axis_step(DANCER[0]+0x810u, DANCER[0]+0x14B8u, 0, 0, B1CENTER_DIVISOR, B1CENTER_MAX_STEP);
    assert(writes == 0);
    put_word(DANCER[0] + 0x810u, (uint32_t)INT32_MAX);
    put_word(DANCER[0] + 0x14B8u, (uint32_t)INT32_MIN);
    b1center_axis_step(DANCER[0]+0x810u, DANCER[0]+0x14B8u, 0, 0, B1CENTER_DIVISOR, B1CENTER_MAX_STEP);
    assert(writes == 0);
}

static void test_center_step_boundaries(void) {
    const int32_t errors[] = {-257,-256,-255,-33,-32,-31,-1,0,1,31,32,33,255,256,257};
    const int32_t bases[] = {108,108,108,102,101,101,101,100,99,99,99,98,92,92,92};
    for (unsigned i = 0; i < sizeof errors / sizeof errors[0]; ++i) {
        put_word(DANCER[0] + 0x810u, (uint32_t)errors[i]);
        put_word(DANCER[0] + 0x14B8u, 100);
        b1center_axis_step(DANCER[0]+0x810u, DANCER[0]+0x14B8u, 0, 0, B1CENTER_DIVISOR, B1CENTER_MAX_STEP);
        assert((int32_t)psx_mod_read_word(DANCER[0]+0x14B8u) == bases[i]);
    }
}

static void test_dance_centering_and_attack_exclusions(void) {
    init_end_center();
    put_word(0x8005D3DCu, 3u); /* phase2 == 3: active dance */
    put_word(DANCER[0] + 0x154Cu, 45u);
    put_word(DANCER[2] + 0x154Cu, 45u);
    for (uint32_t tick = 1; tick <= 160; ++tick) {
        for (int slot = 0; slot <= 2; slot += 2) {
            const uint32_t d = DANCER[slot];
            int32_t old_base[2], old_root[2];
            for (unsigned axis = 0; axis < 2; ++axis) {
                old_base[axis] = (int32_t)psx_mod_read_word(d + 0x14B8u + axis*8u);
                old_root[axis] = (int32_t)psx_mod_read_word(d + 0x810u + axis*8u);
            }
            b1center_apply(slot, d, tick);
            for (unsigned axis = 0; axis < 2; ++axis) {
                const int32_t home = axis ? 0 : (slot ? 520 : -520);
                int32_t delta = (int32_t)psx_mod_read_word(d + 0x14B8u + axis*8u) - old_base[axis];
                assert(delta >= -3 && delta <= 3);
                int32_t now = old_root[axis] + delta;
                assert((int64_t)(now-home)*(now-home) <= (int64_t)(old_root[axis]-home)*(old_root[axis]-home));
                put_word(d + 0x810u + axis*8u, (uint32_t)now);
            }
            assert(psx_mod_read_word(d + 0x814u) == (slot ? 520u : 473u));
            assert(psx_mod_read_word(d + 0x14BCu) == 0u && radius_of(slot) == 199u);
        }
    }
    for (int slot = 0; slot <= 2; slot += 2) {
        const int32_t hx = slot ? 520 : -520;
        const int32_t rx = (int32_t)psx_mod_read_word(DANCER[slot] + 0x810u);
        const int32_t rz = (int32_t)psx_mod_read_word(DANCER[slot] + 0x818u);
        assert(rx >= hx - 16 && rx <= hx + 16);
        assert(rz >= -16 && rz <= 16);
    }
    const int32_t dance_errors[] = {-113,-112,-65,-64,-17,-16,0,16,17,64,65,112,113};
    const int32_t dance_bases[]  = { 103, 102,102,101,101,100,100,100,99, 99,98, 98, 97};
    for (unsigned i = 0; i < sizeof dance_errors / sizeof dance_errors[0]; ++i) {
        put_word(DANCER[0] + 0x810u, (uint32_t)dance_errors[i]);
        put_word(DANCER[0] + 0x14B8u, 100);
        b1center_axis_step(DANCER[0]+0x810u, DANCER[0]+0x14B8u, 0,
                           B1CENTER_DANCE_DEADZONE, B1CENTER_DANCE_DIVISOR, B1CENTER_DANCE_MAX_STEP);
        assert((int32_t)psx_mod_read_word(DANCER[0]+0x14B8u) == dance_bases[i]);
    }
    const uint32_t excluded[][2] = {
        {0x8010154Cu, 73}, {0x8010154Cu, 74}, {0x8010154Cu, 78},
        {0x8005E748u, 1}, {0x8005E754u, 1},
        {0x8005E778u, 0x00010000u}, {0x8005E784u, 0x00010000u},
        {0x8005F824u, 0x0FFF}, {0x8005D3E4u, 1},
    };
    for (unsigned i = 0; i < sizeof excluded / sizeof excluded[0]; ++i) {
        init_end_center();
        put_word(0x8005D3DCu, 3u);
        put_word(DANCER[0] + 0x154Cu, 45u);
        put_word(excluded[i][0], excluded[i][1]);
        writes = 0;
        b1center_apply(0, DANCER[0], 1);
        assert(writes == 0);
        if (excluded[i][0] != 0x8010154Cu && excluded[i][0] != 0x8005F824u) {
            put_word(DANCER[2] + 0x154Cu, 45u);
            b1center_apply(2, DANCER[2], 1);
            assert(writes == 0);
        }
    }
    /* Neighbor bytes inside the same 32-bit words must not false-trigger attack busy;
     * anim 0/72 and mode 1 stay eligible; phase2 == 4 ignores dance attack flags. */
    init_end_center();
    put_word(0x8005D2C4u, 1u);
    put_word(0x8005D3DCu, 3u);
    put_word(DANCER[0] + 0x154Cu, 0u);
    put_word(DANCER[2] + 0x154Cu, 72u);
    put_word(0x8005E748u, 0xFFFF0000u);
    put_word(0x8005E754u, 0xFFFFFF00u);
    put_word(0x8005E778u, 0x0000FFFFu);
    put_word(0x8005E784u, 0xFF00FFFFu);
    writes = 0;
    b1center_apply(0, DANCER[0], 1);
    b1center_apply(2, DANCER[2], 1);
    assert(writes == 4);
    init_end_center();
    put_word(0x8005E748u, 0x00010001u);
    put_word(0x8005E754u, 0x00000001u);
    put_word(0x8005E778u, 0x00010000u);
    put_word(0x8005E784u, 0x00010000u);
    writes = 0;
    b1center_apply(0, DANCER[0], 2);
    assert(writes == 2);
}

int main(int argc, char** argv) {
    if (argc == 2 && strcmp(argv[1], "wide-radius") == 0) { test_wider_home_keeps_tight_radius(); return 0; }
    if (argc == 2 && strcmp(argv[1], "center") == 0) { test_end_center(); return 0; }
    if (argc == 2 && strcmp(argv[1], "dance") == 0) { test_dance_centering_and_attack_exclusions(); return 0; }
    if (argc == 2 && strcmp(argv[1], "exclusions") == 0) { test_center_exclusions(); return 0; }
    if (argc == 2 && strcmp(argv[1], "restore") == 0) { test_center_restore(); return 0; }
    if (argc == 2 && strcmp(argv[1], "steps") == 0) { test_center_step_boundaries(); return 0; }
    /* Proportion 300/784 of |home|, rounded; never loosens; zero home keeps stock. */
    assert(b1leash_target(-520, 440) == 199 && b1leash_target(520, 440) == 199);
    assert(b1leash_target(784, 600) == 300);
    assert(b1leash_target(522, 440) == 200);   /* 199.74 rounds up */
    assert(b1leash_target(344, 146) == 132);   /* stage 5: tighter than 146 */
    assert(b1leash_target(0, 110) == 110);     /* stage 0xB: home X 0 */
    assert(b1leash_target(INT32_MIN, 440) == 440);
    assert(b1leash_target(-520, 0x7FFFFFFFu) == 0x7FFFFFFFu);

    for (int slot = 0; slot < 4; ++slot) {
        memset(ram, 0, sizeof ram); b1leash_forget(); writes = 0;
        const int32_t home = (slot >> 1) ? 520 : -520;
        init_ctl(slot, home, 440);
        assert(b1leash_apply(slot, DANCER[slot]) == 199 && radius_of(slot) == 199 && writes == 1);
        for (int other = 0; other < 4; ++other) if (other != slot) assert(radius_of(other) == 0);
        assert(b1leash_apply(slot, DANCER[slot]) == 0 && writes == 1);   /* steady: no rewrite */
        /* Changing home alone does not recalculate the radius (not a full pair-move test). */
        int32_t moved = 100; memcpy(ram + (CTL[slot] + 0x28u - BASE), &moved, 4);
        assert(b1leash_apply(slot, DANCER[slot]) == 0 && radius_of(slot) == 199);
        /* New match stores the stock radius again: rescaled from the new home. */
        init_ctl(slot, home, 440);
        assert(b1leash_apply(slot, DANCER[slot]) == 199 && writes == 2);
        /* Combat overlay 005, 0x8009CAC4..0x8009CB10, intentionally releases the leash.
         * Reproduce the recorded sequence 440 -> 199 -> INT_MAX, including repeated ticks. */
        put_word(CTL[slot] + 0x38u, 0x7FFFFFFFu);
        for (int tick = 0; tick < 3; ++tick) {
            assert(b1leash_apply(slot, DANCER[slot]) == 0);
            assert(radius_of(slot) == 0x7FFFFFFFu && writes == 2);
        }
        /* A later native finite initialization must still receive the BAG1 correction. */
        init_ctl(slot, home, 440);
        assert(b1leash_apply(slot, DANCER[slot]) == 199 && writes == 3);
        /* Stage whose proportion would loosen: recorded, left alone. */
        init_ctl(slot, 344, 90);
        assert(b1leash_apply(slot, DANCER[slot]) == 0 && radius_of(slot) == 90 && writes == 3);
        assert(b1leash_apply(slot, DANCER[slot]) == 0 && writes == 3);
        put_word(CTL[slot] + 0x28u, 100u);
        assert(b1leash_apply(slot, DANCER[slot]) == 0 && radius_of(slot) == 90 && writes == 3);
    }
    /* VBlank may run at the native call at 0x8002D924, before 0x8002BA38 scales
     * the radius. Do not tighten 440 to 99 before the game's /2 would make it 49. */
    memset(ram, 0, sizeof ram); b1leash_forget(); writes = 0;
    init_ctl(0, -260, 440);
    put_word(0x80108004u, 128u);
    assert(b1leash_apply(0, DANCER[0]) == 0 && radius_of(0) == 440 && writes == 0);
    put_word(CTL[0] + 0x38u, 220u);   /* Native zoom store has now completed. */
    assert(b1leash_apply(0, DANCER[0]) == 99 && radius_of(0) == 99 && writes == 1);
    assert(b1leash_apply(0, DANCER[0]) == 0 && writes == 1);
    /* Unknown finite overrides and invalid stage metadata are not native init radii. */
    init_ctl(0, -520, 600);
    put_word(CTL[0] + 0x3Cu, 440u);
    assert(b1leash_apply(0, DANCER[0]) == 0 && radius_of(0) == 600 && writes == 1);
    init_ctl(0, -520, 440);
    put_word(0x80089200u, 0u);
    assert(b1leash_apply(0, DANCER[0]) == 0 && radius_of(0) == 440 && writes == 1);
    put_word(0x80089200u, 0x807FFFFCu);
    assert(b1leash_apply(0, DANCER[0]) == 0 && writes == 1);
    put_word(0x80089200u, 0x80108001u);
    assert(b1leash_apply(0, DANCER[0]) == 0 && writes == 1);
    put_word(0x80089200u, 0x80108000u);
    put_word(0x80108004u, 0xFFFFu);
    assert(b1leash_apply(0, DANCER[0]) == 0 && writes == 1);
    /* Refusals: no BAG1 dancer, block of another dancer, slot out of range. */
    memset(ram, 0, sizeof ram); b1leash_forget(); writes = 0;
    init_ctl(0, -520, 440);
    assert(b1leash_apply(0, 0) == 0);
    assert(b1leash_apply(0, DANCER[1]) == 0);
    assert(b1leash_apply(-1, DANCER[0]) == 0 && b1leash_apply(4, DANCER[0]) == 0);
    assert(writes == 0 && radius_of(0) == 440);
    /* Reset forgets the latch: the same values are applied again. */
    assert(b1leash_apply(0, DANCER[0]) == 199);
    b1leash_forget(); init_ctl(0, -520, 440);
    assert(b1leash_apply(0, DANCER[0]) == 199 && writes == 2);
    puts("BAG1 leash: 4 slots, proportion, steady state, re-init, no loosening, 5 refusals");
    return 0;
}
