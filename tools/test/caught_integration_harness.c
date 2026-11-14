/* Integration harness: capture at producer site 0x8009b5b4 -> take at consumer
 * call. Host-only, uses real bag2jp_caught_source.c / bag2jp_caught_context.c.
 * No runtime hooks, no guest writes. */
#undef NDEBUG
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "bag2jp_caught_source.h"
#include "bag2jp_caught_context.h"

#ifndef GASO_CAUGHT_SIDES
#define GASO_CAUGHT_SIDES 2
#endif
enum { BASE = 0x80000000u, RAM_BYTES = 0x800000,
       LIST = 0x8005f808u, CONTROLLERS = 0x8005f820u,
       PENDING = 0x8005cf08u, TABLE = 0x80051458u,
       STACK = 0x807ffe00u, ACTOR1 = 0x80410000u, ACTOR2 = 0x80420000u,
       SITE = 0x8009b5b4u, OVERLAY_PTR = 0x80010ce0u,
       OVERLAY_BASE = 0x8008f890u, CHAR_BYTE_SITE = 0x8009b5acu,
       NOP_SITE = 0x8009b5b0u, MAIN_RA = 0x8002ae68u,
       CONSUMER_RA = 0x8009d0c8u,
       /* Original call sites validated by b1cr_read_context at slot 89 */
       CS_DISPATCH_0 = 0x8002ae60u, CS_DISPATCH_1 = 0x8002ae64u,
       CS_CONSUMER_0 = 0x8009d0bcu, CS_CONSUMER_1 = 0x8009d0c0u,
       CS_CONSUMER_2 = 0x8009d0c4u };

static uint8_t ram[RAM_BYTES];

static void put(uint32_t address, uint32_t value, unsigned width) {
    assert(address >= BASE && address - BASE <= RAM_BYTES - width);
    for (unsigned i = 0; i < width; ++i)
        ram[address - BASE + i] = (uint8_t)(value >> (8 * i));
}

static void setup_game(unsigned self, unsigned side, unsigned source_character) {
    memset(ram, 0, sizeof ram);
    /* Original code sites pinned (capture side) */
    put(OVERLAY_PTR, OVERLAY_BASE, 4);
    put(CHAR_BYTE_SITE, 0x90420000u, 4);   /* lbu v0,0(v0) */
    put(NOP_SITE, 0x00000000u, 4);          /* nop */
    put(SITE, 0xa6a20018u, 4);              /* sh v0,0x18(s5) */
    /* Original call sites pinned (take side / b1cr_read_context) */
    put(CS_DISPATCH_0, 0x0c00b41bu, 4);     /* jal original consumer */
    put(CS_DISPATCH_1, 0xafb50010u, 4);     /* sw s5,0x10(s4) */
    put(CS_CONSUMER_0, 0x24071000u, 4);     /* li a3,0x1000 */
    put(CS_CONSUMER_1, 0x0c00a824u, 4);     /* jal original body */
    put(CS_CONSUMER_2, 0xafa20010u, 4);     /* sw v0,0x10(s2) */
    /* Actor list: main controller at LIST + 8*side */
    put(LIST + 8 * side, ACTOR1, 4);
    put(LIST + 8 * (side ^ 1u), ACTOR2, 4);
    /* Controller table points to each actor */
    put(CONTROLLERS + side * 0x98, ACTOR1, 4);
    put(CONTROLLERS + (side ^ 1u) * 0x98, ACTOR2, 4);
    /* Actor bytes: char at +4, side at +5 */
    put(ACTOR1 + 4, source_character, 1);
    put(ACTOR1 + 5, side, 1);
    put(ACTOR2 + 4, source_character, 1);
    put(ACTOR2 + 5, side ^ 1u, 1);
    /* Table source char -> request (row at TABLE + 2*char) */
    put(TABLE + 2u * (unsigned)source_character, 202u, 1);
    /* Stack: sp + 0xd4 = consumer RA; sp + 0x30 + side = direct/reflected flag */
    put(STACK + 0xd4, CONSUMER_RA, 4);
    const uint32_t reflected = (self ? side : side ^ 1u) == side ? 1u : 0u;
    put(STACK + 0x30 + side, reflected ? 2u : 1u, 1);
    /* Pending for recipient side must be 202 (request202) */
    put(PENDING + side * 0x24 + 0x18, 202u, 2);
}

/* Build capture registers as they would be at 0x8009b5b4: v0=request(202),
 * s2=source_side, s4=recipient_side, s5=pending_addr, sp=stack. */
static B1CaughtSourceRegisters build_registers(unsigned source_side,
                                                unsigned recipient_side) {
    return (B1CaughtSourceRegisters){
        .pc = SITE,
        .request = 202,
        .source_side = source_side,
        .recipient_side = recipient_side,
        .pending = PENDING + 0x24 * recipient_side,
        .sp = STACK,
    };
}

/* Build call registers for the consumer original call at slot 89. */
static B1CaughtCallRegisters build_call(unsigned side) {
    return (B1CaughtCallRegisters){
        .controller = CONTROLLERS + side * 0x98,
        .mode = 1,
        .slot = 89,
        .sp = STACK,
        .ra = MAIN_RA,
    };
}

static B1CaughtSourceClock clock_val(void) {
    return (B1CaughtSourceClock){17, 120};
}

int main(int argc, char **argv) {
    assert(argc == 3);
    unsigned scenario = (unsigned)strtoul(argv[1], NULL, 10);
    unsigned kind = (unsigned)strtoul(argv[2], NULL, 10);
    unsigned side = kind & 1u;
    unsigned self = (kind >> 1) & 1u;
    unsigned source_character = kind >> 2; /* 0=Heat, 1=Strike, 9=Gas-O */

    setup_game(self, side, source_character);
    unsigned source_side = self ? side : side ^ 1u;
    unsigned recipient_side = side;

    B1CaughtSource record = {0};
    B1CaughtSourceRegisters regs = build_registers(source_side, recipient_side);
    B1CaughtSourceClock clock = clock_val();

    if (scenario == 0) {
        /* capture -> take happy path */
        assert(b1cs_capture(&record, ram, sizeof ram, &regs, &clock));
        assert(record.available == 1);
        assert(record.side == recipient_side);
        assert(record.source_side == source_side);
        assert(record.source_character == source_character);
        assert(record.request == 202);
        assert(record.reflected == self);

        B1CaughtCallRegisters call = build_call(recipient_side);
        B1CaughtSourceClock take_clock = clock; /* same generation/tick */
        B1CaughtSource out = {0};
        assert(b1cs_take(&record, ram, sizeof ram, &call, &take_clock, &out));
        assert(out.available == 1);
        assert(out.source_character == source_character);
        assert(out.reflected == self);
        assert(record.available == 0); /* consumed */

        /* Replay should fail */
        B1CaughtSource out2 = {0};
        assert(!b1cs_take(&record, ram, sizeof ram, &call, &take_clock, &out2));
        assert(record.available == 0);
        printf("INTEGRATION_OK side=%u self=%u char=%u\n", side, self, source_character);
    } else if (scenario == 1) {
        /* capture then take with clock mismatch */
        assert(b1cs_capture(&record, ram, sizeof ram, &regs, &clock));
        assert(record.available == 1);
        B1CaughtCallRegisters call = build_call(recipient_side);
        B1CaughtSourceClock bad_clock = {clock.generation + 1, clock.tick};
        B1CaughtSource out = {0};
        assert(!b1cs_take(&record, ram, sizeof ram, &call, &bad_clock, &out));
        assert(record.available == 0); /* consumed even on rejection: no stale retry */
        printf("INTEGRATION_CLOCK_MISMATCH_OK side=%u self=%u char=%u\n", side, self, source_character);
    } else if (scenario == 2) {
        /* capture then take with actor mismatch (context actor != captured actor) */
        assert(b1cs_capture(&record, ram, sizeof ram, &regs, &clock));
        assert(record.available == 1);
        /* Change the actor at controller+0 so context actor != captured actor */
        put(CONTROLLERS + recipient_side * 0x98, ACTOR2, 4); /* other actor */
        B1CaughtCallRegisters call = build_call(recipient_side);
        B1CaughtSource out = {0};
        assert(!b1cs_take(&record, ram, sizeof ram, &call, &clock, &out));
        assert(record.available == 0); /* consumed even on rejection: no stale retry */
        printf("INTEGRATION_ACTOR_MISMATCH_OK side=%u self=%u char=%u\n", side, self, source_character);
    } else if (scenario == 3) {
        /* capture with wrong pc (not producer site) */
        B1CaughtSourceRegisters bad_regs = regs;
        bad_regs.pc = SITE + 4;
        assert(!b1cs_capture(&record, ram, sizeof ram, &bad_regs, &clock));
        assert(record.available == 0);
        printf("INTEGRATION_WRONG_PC_OK side=%u self=%u char=%u\n", side, self, source_character);
    } else {
        fprintf(stderr, "unknown scenario %u\n", scenario);
        return 1;
    }
    return 0;
}
