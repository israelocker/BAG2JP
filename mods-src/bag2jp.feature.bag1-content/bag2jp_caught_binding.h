/* Experimental paused-RAM transaction only, not included by the runtime.
 * Caller must own a stopped VM, a verified load/generation and authentic clip.
 * No callbacks run between validation and the ten byte writes. This is atomic
 * to that stopped guest, NOT to concurrent threads or a live controller hook.
 * Success does not enter an animation or advance the separate loan policy.
 */
#ifndef BAG2JP_CAUGHT_BINDING_H
#define BAG2JP_CAUGHT_BINDING_H
#include <stddef.h>
#include <stdint.h>
typedef struct {
    uint32_t actor, raw_table, length_table, metadata_table, count, character, side;
    uint32_t empty_raw, clip, clip_bytes;
} B1CaughtBinding;
/* Caller-owned allocation facts, not an arbitrary guest-address mapping. The
 * data buffer must describe exactly one live allocator-issued Expansion1 span
 * and remain immutable/alive through decoder retirement. This byte transaction
 * checks bounds, NOT allocator provenance, generation or guest pause ownership.
 * Actors, tables and the original empty tuple always remain in main RAM.
 */
typedef struct {
    const uint8_t *data;
    uint32_t guest_base;
    size_t bytes;
} B1CaughtClipRegion;

enum { B1CB_BASE = 0x80000000u, B1CB_MAX_RAM = 0x800000,
       B1CB_ACTORS = 0x8005f808u, B1CB_ACTOR_COUNT = 4, B1CB_ACTOR_BYTES = 0x155c,
       B1CB_COUNT = 0x820, B1CB_RAW = 0x824, B1CB_LENGTH = 0x828, B1CB_META = 0x82c,
       B1CB_DECODER = 0x830, B1CB_POSE_A = 0x1494, B1CB_POSE_B = 0x1498,
       B1CB_CURRENT = 0x154c, B1CB_PREVIOUS = 0x1550, B1CB_SLOT = 1,
       B1CB_INFO_BYTES = 12, B1CB_FRAMES = 2,
       B1CB_OWNED_BASE = 0x9f000000u, B1CB_OWNED_BYTES = 0x100000 };
typedef struct { size_t offset, size; } B1CaughtSpan;
typedef struct {
    B1CaughtSpan tables[3], actor, clip, empty;
    size_t raw, length, metadata;
    uint32_t info;
} B1CaughtWritePlan;

static uint32_t b1cb_read(const uint8_t *ram, size_t at, unsigned width) {
    uint32_t value = 0;
    for (unsigned i = 0; i < width; ++i) value |= (uint32_t)ram[at+i] << (8*i);
    return value;
}
static void b1cb_write(uint8_t *ram, size_t at, uint32_t value, unsigned width) {
    for (unsigned i = 0; i < width; ++i) ram[at+i] = (uint8_t)(value >> (8*i));
}
static int b1cb_span(size_t bytes, uint32_t address, uint64_t size,
                      unsigned alignment, B1CaughtSpan *out) {
    if (address < B1CB_BASE || address % alignment || !size || size > bytes) return 0;
    uint64_t offset = (uint64_t)address - B1CB_BASE;
    if (offset + size > bytes) return 0;
    out->offset = (size_t)offset;
    out->size = (size_t)size;
    return 1;
}
static int b1cb_overlap(B1CaughtSpan a, B1CaughtSpan b) {
    return a.offset < b.offset + b.size && b.offset < a.offset + a.size;
}
static int b1cb_tables(const uint8_t *ram, size_t bytes, B1CaughtSpan actor,
                        B1CaughtSpan out[3]) {
    uint32_t n = b1cb_read(ram, actor.offset + B1CB_COUNT, 4);
    if (n <= B1CB_SLOT) return 0;
    return b1cb_span(bytes, b1cb_read(ram, actor.offset+B1CB_RAW, 4), 4ull*n, 4, &out[0]) &&
        b1cb_span(bytes, b1cb_read(ram, actor.offset+B1CB_LENGTH, 4), 2ull*n, 2, &out[1]) &&
        b1cb_span(bytes, b1cb_read(ram, actor.offset+B1CB_META, 4), 4ull*n, 4, &out[2]);
}
static int b1cb_actor_matches(const uint8_t *ram, const B1CaughtBinding *b,
                               B1CaughtSpan a) {
    return ram[a.offset+4] == b->character && ram[a.offset+5] == b->side &&
        b1cb_read(ram, a.offset+B1CB_COUNT, 4) == b->count &&
        b1cb_read(ram, a.offset+B1CB_RAW, 4) == b->raw_table &&
        b1cb_read(ram, a.offset+B1CB_LENGTH, 4) == b->length_table &&
        b1cb_read(ram, a.offset+B1CB_META, 4) == b->metadata_table &&
        b1cb_read(ram, a.offset+B1CB_CURRENT, 4) < b->count &&
        b1cb_read(ram, a.offset+B1CB_PREVIOUS, 4) < b->count &&
        b1cb_read(ram, a.offset+B1CB_CURRENT, 4) != B1CB_SLOT &&
        b1cb_read(ram, a.offset+B1CB_PREVIOUS, 4) != B1CB_SLOT;
}
static int b1cb_disjoint(const B1CaughtWritePlan *p, B1CaughtSpan extra) {
    for (unsigned i = 0; i < 3; ++i)
        if (b1cb_overlap(p->tables[i], extra)) return 0;
    return !b1cb_overlap(p->clip, extra) && !b1cb_overlap(p->empty, extra);
}
static int b1cb_remember(B1CaughtSpan span, B1CaughtSpan seen[], unsigned *count) {
    /* The owner may be absent: four foreign actors would exceed this inventory. */
    if (*count >= 3*B1CB_ACTOR_COUNT) return 0;
    for (unsigned i = 0; i < *count; ++i)
        if (b1cb_overlap(span, seen[i])) return 0;
    seen[(*count)++] = span;
    return 1;
}
/* Conservatively reject sharing even between two additional actors. This may
 * reject otherwise unrelated companion loads; supporting them needs its own seam.
 * Check the four loaded actor pointers, including partial/cross-kind sharing.
 * This is not proof against unlisted aliases held by an unobserved subsystem.
 */
static int b1cb_exclusive(const uint8_t *ram, size_t bytes,
                           const B1CaughtBinding *b, const B1CaughtWritePlan *p) {
    B1CaughtSpan list, actor, other[3];
    B1CaughtSpan seen[3*B1CB_ACTOR_COUNT];
    unsigned count = 0;
    if (!b1cb_span(bytes, B1CB_ACTORS, 4*B1CB_ACTOR_COUNT, 4, &list) ||
        !b1cb_disjoint(p, list)) return 0;
    for (unsigned i = 0; i < 3; ++i) seen[count++] = p->tables[i];
    unsigned owners = 0;
    for (unsigned i = 0; i < B1CB_ACTOR_COUNT; ++i) {
        uint32_t address = b1cb_read(ram, list.offset+4*i, 4);
        if (!address) continue;
        if (address == b->actor) { ++owners; continue; }
        if (!b1cb_span(bytes, address, B1CB_ACTOR_BYTES, 4, &actor) ||
            b1cb_overlap(actor, p->actor) || !b1cb_disjoint(p, actor) ||
            !b1cb_tables(ram, bytes, actor, other)) return 0;
        for (unsigned j = 0; j < 3; ++j)
            if (!b1cb_disjoint(p, other[j]) || !b1cb_remember(other[j], seen, &count)) return 0;
    }
    return owners == 1;
}
static const uint8_t *b1cb_clip_data(const uint8_t *ram, size_t bytes,
                                     const B1CaughtBinding *b,
                                     const B1CaughtClipRegion *region,
                                     B1CaughtSpan *clip) {
    if (!region) {
        if (!b1cb_span(bytes, b->clip, b->clip_bytes, 4, clip)) return NULL;
        return ram + clip->offset;
    }
    if (!region->data || !region->bytes || region->bytes > B1CB_OWNED_BYTES ||
        region->guest_base < B1CB_OWNED_BASE || region->guest_base % 4 ||
        (uint64_t)region->guest_base + region->bytes >
            (uint64_t)B1CB_OWNED_BASE + B1CB_OWNED_BYTES ||
        b->clip < region->guest_base || b->clip % 4 || !b->clip_bytes) return NULL;
    uint64_t offset = (uint64_t)b->clip - region->guest_base;
    if (offset + b->clip_bytes > region->bytes) return NULL;
    /* All disjointness/reference checks share guest coordinates; only clip
     * reads use the separate host buffer. No main-RAM index uses this offset. */
    clip->offset = (size_t)((uint64_t)b->clip - B1CB_BASE);
    clip->size = b->clip_bytes;
    return region->data + (size_t)offset;
}
static int b1cb_clip_metadata(const uint8_t *data, const B1CaughtBinding *b,
                               B1CaughtWritePlan *p) {
    if (p->clip.size < B1CB_INFO_BYTES || b1cb_read(data, 4, 2) != B1CB_FRAMES)
        return 0;
    uint64_t tail = b1cb_read(data, 0, 4);
    if (tail < 8 || tail % 4 || tail+4 > p->clip.size) return 0;
    uint64_t relative = b1cb_read(data, (size_t)tail, 4);
    uint64_t info = tail+relative;
    if (relative < 4 || relative % 4 || info+B1CB_INFO_BYTES > p->clip.size) return 0;
    for (unsigned i = 0; i < B1CB_INFO_BYTES; ++i)
        if (data[(size_t)info+i] != (i == 2 ? 4 : 0)) return 0;
    p->info = b->clip + (uint32_t)info;
    return 1;
}
/* Legacy adapter helper: its caller already validated a main-RAM clip span. */
static inline int b1cb_clip_info(const uint8_t *ram, const B1CaughtBinding *b,
                                   B1CaughtWritePlan *p) {
    return b1cb_clip_metadata(ram + p->clip.offset, b, p);
}
static int b1cb_no_references(const uint8_t *ram, const B1CaughtWritePlan *p) {
    const unsigned offsets[] = {B1CB_DECODER, B1CB_POSE_A, B1CB_POSE_B};
    for (unsigned i = 0; i < sizeof offsets/sizeof offsets[0]; ++i) {
        uint32_t value = b1cb_read(ram, p->actor.offset+offsets[i], 4);
        uint64_t start = B1CB_BASE+p->clip.offset;
        if (value >= start && (uint64_t)value < start+p->clip.size) return 0;
    }
    return 1;
}
static int b1cb_plan(const uint8_t *ram, size_t bytes, const B1CaughtBinding *b,
                      int paused, const B1CaughtClipRegion *region, B1CaughtWritePlan *p) {
    if (!ram || !b || !paused || !bytes || bytes > B1CB_MAX_RAM || b->side >= 2 ||
        (b->character != 0 && b->character != 1 && b->character != 9)) return 0;
    const uint8_t *data = b1cb_clip_data(ram, bytes, b, region, &p->clip);
    if (!data) return 0;
    if (!b1cb_span(bytes, b->actor, B1CB_ACTOR_BYTES, 4, &p->actor) ||
        !b1cb_actor_matches(ram, b, p->actor) || !b1cb_tables(ram, bytes, p->actor, p->tables) ||
        !b1cb_span(bytes, b->empty_raw, 4, 4, &p->empty)) return 0;
    for (unsigned i = 0; i < 3; ++i) {
        if (b1cb_overlap(p->tables[i], p->actor) || b1cb_overlap(p->tables[i], p->clip) ||
            b1cb_overlap(p->tables[i], p->empty)) return 0;
        for (unsigned j = i+1; j < 3; ++j)
            if (b1cb_overlap(p->tables[i], p->tables[j])) return 0;
    }
    if (b1cb_overlap(p->clip, p->actor) || b1cb_overlap(p->empty, p->actor) ||
        b1cb_overlap(p->clip, p->empty) || b1cb_read(ram, p->empty.offset, 4) ||
        !b1cb_clip_metadata(data, b, p) || !b1cb_no_references(ram, p) ||
        !b1cb_exclusive(ram, bytes, b, p)) return 0;
    p->raw = p->tables[0].offset+4*B1CB_SLOT;
    p->length = p->tables[1].offset+2*B1CB_SLOT;
    p->metadata = p->tables[2].offset+4*B1CB_SLOT;
    return 1;
}
static int b1cb_tuple(const uint8_t *ram, const B1CaughtWritePlan *p,
                       uint32_t raw, unsigned length, uint32_t meta) {
    return b1cb_read(ram, p->raw, 4) == raw && b1cb_read(ram, p->length, 2) == length &&
        b1cb_read(ram, p->metadata, 4) == meta;
}
/* All fallible work precedes these infallible bounded writes to stopped RAM. */
static void b1cb_commit(uint8_t *ram, const B1CaughtWritePlan *p,
                         uint32_t raw, unsigned length, uint32_t meta) {
    b1cb_write(ram, p->raw, raw, 4);
    b1cb_write(ram, p->length, length, 2);
    b1cb_write(ram, p->metadata, meta, 4);
}
static int b1cb_publish_in(uint8_t *ram, size_t bytes, const B1CaughtBinding *b,
                           int paused, const B1CaughtClipRegion *region) {
    B1CaughtWritePlan p;
    if (!b1cb_plan(ram, bytes, b, paused, region, &p) || !b1cb_tuple(ram, &p, b->empty_raw, 0, 0))
        return 0;
    b1cb_commit(ram, &p, b->clip, B1CB_FRAMES, p.info);
    return 1;
}
static int b1cb_publish(uint8_t *ram, size_t bytes, const B1CaughtBinding *b, int paused) __attribute__((unused));
static int b1cb_publish(uint8_t *ram, size_t bytes, const B1CaughtBinding *b, int paused) {
    return b1cb_publish_in(ram, bytes, b, paused, NULL);
}
/* quiescent must come from a proven decoder/pose/controller retirement boundary;
 * checking three pointer words is an additional guard, not that proof itself.
 * No actor slot, frame, pending request or policy descriptor is written here.
 */
static int b1cb_restore_in(uint8_t *ram, size_t bytes, const B1CaughtBinding *b,
                           int paused, int quiescent, const B1CaughtClipRegion *region) {
    B1CaughtWritePlan p;
    if (!quiescent || !b1cb_plan(ram, bytes, b, paused, region, &p) ||
        !b1cb_tuple(ram, &p, b->clip, B1CB_FRAMES, p.info)) return 0;
    b1cb_commit(ram, &p, b->empty_raw, 0, 0);
    return 1;
}
static int b1cb_restore(uint8_t *ram, size_t bytes, const B1CaughtBinding *b,
                        int paused, int quiescent) __attribute__((unused));
static int b1cb_restore(uint8_t *ram, size_t bytes, const B1CaughtBinding *b,
                        int paused, int quiescent) {
    return b1cb_restore_in(ram, bytes, b, paused, quiescent, NULL);
}
#endif
