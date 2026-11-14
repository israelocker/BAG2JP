/* A separate clip arena must never relax main-RAM actor/table guards. */
#define main baseline_binding_main
#include "caught_binding_harness.c"
#undef main
#include <sys/mman.h>
#include <unistd.h>

enum { OWNED_BASE = 0x9f000100u, OWNED_BYTES = 96, OWNED_OFFSET = 16 };
static uint8_t owned[OWNED_BYTES], owned_before[OWNED_BYTES];

static B1CaughtClipRegion region_setup(B1CaughtBinding *b) {
    *b = setup();
    memset(owned, 0xa5, sizeof owned);
    memcpy(owned + OWNED_OFFSET, ram + CLIP - 0x80000000u, CLIP_BYTES);
    b->clip = OWNED_BASE + OWNED_OFFSET;
    B1CaughtClipRegion region = {owned, OWNED_BASE, sizeof owned};
    return region;
}
static void snapshot(void) {
    memcpy(before, ram, sizeof ram);
    memcpy(owned_before, owned, sizeof owned);
}
static void arena_unchanged(void) {
    assert(memcmp(owned, owned_before, sizeof owned) == 0);
}
static void owned_lifecycle(void) {
    B1CaughtBinding b;
    B1CaughtClipRegion region = region_setup(&b);
    snapshot();
    assert(b1cb_publish_in(ram, sizeof ram, &b, 1, &region));
    assert(get32(RAW + 4) == 0x9f000110u);
    assert(get32(META + 4) == 0x9f000140u);
    assert(b1cb_read(ram, LENGTH - B1CB_BASE + 2, 2) == 2);
    only_entry_changed(&b); arena_unchanged();
    snapshot();
    assert(b1cb_restore_in(ram, sizeof ram, &b, 1, 1, &region));
    assert(get32(RAW + 4) == EMPTY && get32(META + 4) == 0);
    assert(b1cb_read(ram, LENGTH - B1CB_BASE + 2, 2) == 0);
    only_entry_changed(&b); arena_unchanged();
    assert(b1cb_publish_in(ram, sizeof ram, &b, 1, &region));
    assert(b1cb_read(ram, LENGTH - B1CB_BASE + 2, 2) == 2);
    assert(b1cb_restore_in(ram, sizeof ram, &b, 1, 1, &region));
    assert(b1cb_read(ram, LENGTH - B1CB_BASE + 2, 2) == 0);
}
static void invalid_region(int field) {
    B1CaughtBinding b;
    B1CaughtClipRegion region = region_setup(&b);
    switch (field) {
    case 0: region.data = NULL; break;
    case 1: region.bytes = 0; break;
    case 2: region.bytes = OWNED_OFFSET + CLIP_BYTES - 1; break;
    case 3: region.guest_base = 0x9f000120u; break;
    case 4: region.guest_base = 0x800d0000u; b.clip = region.guest_base + OWNED_OFFSET; break;
    case 5: region.guest_base = 0x80800000u; b.clip = region.guest_base + OWNED_OFFSET; break;
    case 6: region.guest_base = 0x9f0ffff0u; b.clip = region.guest_base + OWNED_OFFSET; break;
    case 7: region.bytes = (size_t)-1; break;
    case 8: b.clip += 2; break;
    case 9: b.clip_bytes = 0xffffffffu; break;
    case 10: owned[OWNED_OFFSET + 4] = 3; break;
    case 11: owned[OWNED_OFFSET + 50] = 5; break;
    case 12: memset(owned + OWNED_OFFSET + 32, 0xfc, 4); break;
    case 13: b.actor = OWNED_BASE; break;
    case 14: b.raw_table = OWNED_BASE; put32(ACTOR + 0x824, OWNED_BASE); break;
    case 15: b.empty_raw = OWNED_BASE; break;
    case 16: put32(0x8005f80cu, OWNED_BASE); break;
    case 17: region.guest_base++; break;
    case 18: b1cb_write(owned, OWNED_OFFSET, CLIP_BYTES, 4); break;
    case 19: {
        uint8_t info[12];
        memcpy(info, owned + OWNED_OFFSET + 48, sizeof info);
        memcpy(owned + OWNED_OFFSET + 49, info, sizeof info);
        b1cb_write(owned, OWNED_OFFSET + 32, 17, 4);
        break;
    }
    case 20: b.clip_bytes = 59; break;
    default: assert(0);
    }
    snapshot();
    assert(!b1cb_publish_in(ram, sizeof ram, &b, 1, &region));
    unchanged(); arena_unchanged();
}
static void blocked_retirement(int field) {
    B1CaughtBinding b;
    B1CaughtClipRegion region = region_setup(&b);
    assert(b1cb_publish_in(ram, sizeof ram, &b, 1, &region));
    if (field < 3) put32(ACTOR + (uint32_t[]){0x830, 0x1494, 0x1498}[field], b.clip + 8);
    else if (field == 3) put32(ACTOR + 0x154c, 1);
    else if (field == 4) put32(ACTOR + 0x1550, 1);
    else if (field == 7) put32(META + 4, b.clip + 52);
    snapshot();
    assert(!b1cb_restore_in(ram, sizeof ram, &b, field != 5, field != 6, &region));
    unchanged(); arena_unchanged();
}
/* Restore with region owned but quiescent=false must refuse and write nothing. */
static void restore_not_quiescent_owned(void) {
    B1CaughtBinding b;
    B1CaughtClipRegion region = region_setup(&b);
    assert(b1cb_publish_in(ram, sizeof ram, &b, 1, &region));
    snapshot();
    assert(!b1cb_restore_in(ram, sizeof ram, &b, 1, 0, &region));
    unchanged(); arena_unchanged();
}
/* Region identity changed between ENTER and RESTORE: restore must refuse. */
static void restore_different_region_owned(void) {
    B1CaughtBinding b;
    B1CaughtClipRegion region = region_setup(&b);
    assert(b1cb_publish_in(ram, sizeof ram, &b, 1, &region));
    /* Publish again with a different region (different base) for the same clip. */
    B1CaughtClipRegion other = {owned, OWNED_BASE + 16, sizeof owned - 16};
    snapshot();
    assert(!b1cb_restore_in(ram, sizeof ram, &b, 1, 1, &other));
    unchanged(); arena_unchanged();
    /* Original region still restores fine. */
    assert(b1cb_restore_in(ram, sizeof ram, &b, 1, 1, &region));
    only_entry_changed(&b); arena_unchanged();
}
/* Tables of the owner actor aliased into the owned region: publication must refuse. */
static void tables_inside_owned_region(void) {
    B1CaughtBinding b;
    B1CaughtClipRegion region = region_setup(&b);
    /* Overlap the actor's raw table span with the owned region. */
    put32(ACTOR + 0x824, OWNED_BASE + OWNED_OFFSET + 32);
    snapshot();
    assert(!b1cb_publish_in(ram, sizeof ram, &b, 1, &region));
    unchanged(); arena_unchanged();
}
static void exact_region_end(void) {
    B1CaughtBinding b;
    B1CaughtClipRegion region = region_setup(&b);
    region.bytes = OWNED_OFFSET + CLIP_BYTES;
    assert(b1cb_publish_in(ram, sizeof ram, &b, 1, &region));
    assert(b1cb_restore_in(ram, sizeof ram, &b, 1, 1, &region));
}
static void exact_aperture_end(void) {
    B1CaughtBinding b;
    B1CaughtClipRegion region = region_setup(&b);
    region.guest_base = 0x9f100000u - OWNED_BYTES;
    b.clip = region.guest_base + OWNED_OFFSET;
    snapshot();
    assert(b1cb_publish_in(ram, sizeof ram, &b, 1, &region));
    assert(b1cb_restore_in(ram, sizeof ram, &b, 1, 1, &region));
    only_entry_changed(&b); arena_unchanged();
}
static void alternate_metadata_layout(void) {
    B1CaughtBinding b;
    B1CaughtClipRegion region = region_setup(&b);
    uint8_t info[12];
    memcpy(info, owned + OWNED_OFFSET + 48, sizeof info);
    memcpy(owned + OWNED_OFFSET + 32, info, sizeof info);
    b1cb_write(owned, OWNED_OFFSET, 16, 4);
    b1cb_write(owned, OWNED_OFFSET + 16, 16, 4);
    snapshot();
    assert(b1cb_publish_in(ram, sizeof ram, &b, 1, &region));
    assert(get32(META + 4) == b.clip + 32);
    assert(b1cb_restore_in(ram, sizeof ram, &b, 1, 1, &region));
    only_entry_changed(&b); arena_unchanged();
}
static void aligned_tail_outside_guarded_clip(void) {
    B1CaughtBinding b;
    B1CaughtClipRegion region = region_setup(&b);
    size_t page = (size_t)sysconf(_SC_PAGESIZE);
    uint8_t *pages = mmap(NULL, page * 2, PROT_READ | PROT_WRITE,
                          MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    assert(pages != MAP_FAILED);
    assert(mprotect(pages + page, page, PROT_NONE) == 0);
    region.bytes = OWNED_OFFSET + CLIP_BYTES;
    uint8_t *data = pages + page - region.bytes;
    memcpy(data, owned, region.bytes);
    b1cb_write(data, OWNED_OFFSET, CLIP_BYTES, 4);
    region.data = data;
    snapshot();
    assert(!b1cb_publish_in(ram, sizeof ram, &b, 1, &region));
    unchanged(); arena_unchanged();
    assert(munmap(pages, page * 2) == 0);
}
int main(int argc, char **argv) {
    assert(argc == 3);
    int scenario = atoi(argv[1]), field = atoi(argv[2]);
    switch (scenario) {
    case 0: owned_lifecycle(); break;
    case 1: invalid_region(field); break;
    case 2: blocked_retirement(field); break;
    case 3: exact_region_end(); break;
    case 4: {
        B1CaughtBinding b;
        (void)region_setup(&b);
        rejects_publish(b, 1); /* Old API must remain main-RAM-only. */
        break;
    }
    case 5: exact_aperture_end(); break;
    case 6: alternate_metadata_layout(); break;
    case 7: aligned_tail_outside_guarded_clip(); break;
    case 8: restore_not_quiescent_owned(); break;
    case 9: restore_different_region_owned(); break;
    case 10: tables_inside_owned_region(); break;
    default: assert(0);
    }
    return 0;
}
