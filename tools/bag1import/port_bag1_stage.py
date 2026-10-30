"""Port the BAG1 Heat stage program (ST_HEAT.DFS entry 0, a MIPS overlay for BAG1 at 0x801E17B0) to a
BAG2 stage DBI for stage id 0 (Heat), loaded by BAG2 at 0x801DAF10.

- relocation: every absolute reference into the BAG1 image (jal/j, lui+lo pairs, data words) moves by
  0x801DAF10 - 0x801E17B0;
- BAG1 main-exe calls -> BAG2 equivalents (FUNCS, found with funcmatch.py and decomp comparison);
- BAG1 globals -> BAG2 globals (GLOBALS ranges) or the shim block filled by the bag2jp.bag1_stage
  plugin (beat flags, score level);
- struct offsets: BAG1 stage struct +0x0C (bone list) = BAG2 +0x20; BAG1 bone +0xDC (mesh record)
  with 0x100-byte bones = BAG2 +0x8C with 0xB0-byte bones;
- BAG2 calls the 4 stage callbacks of id 0 at fixed addresses (main exe tables 0x80051B88/BBC/BF0,
  0x80054C10): trampolines there (init / draw return 1, update -> BAG1 update, setup -> BAG1 setup).
usage: port_bag1_stage.py <bag1 dbi> <out bag2 dbi>"""
import struct, sys
import capstone

B1_BASE, B2_BASE = 0x801E17B0, 0x801DAF10
DELTA = B2_BASE - B1_BASE
CODE_END = 0x801E48F0                       # first data word after the last function
SHIM = 0x801E0100                           # 'B1ST', beat flags u32, level u8, prev level u8
FUNCS = {
    0x8004FB0C: 0x80049824,  # SetPolyFT4
    0x8004A86C: 0x80043784, 0x8004B08C: 0x80044334, 0x8004AFFC: 0x800442A4, 0x8004A5BC: 0x800434D4,
    0x8004C45C: 0x80046334, 0x8004B47C: 0x80044A04, 0x8004FA0C: 0x80049754, 0x8004B56C: 0x80044AF4,
    0x8004B4AC: 0x80044A34, 0x8004B02C: 0x800442D4,
    0x800500FC: 0x80049F24,  # rand
    0x80036AE8: 0x8002F824, 0x80035A30: 0x8002EE10,  # sprite drawers
    0x80034F40: 0x8002E2D0,  # play sound cue on a slot
    0x8002ACA0: 0x80023724, 0x8002A2B8: 0x80022FF4,  # stage lights setup / update
    0x8001E1A4: 0x8001F384,
}
GLOBALS = [  # (BAG1 start, length, BAG2 start)
    (0x80051B74, 0x2000, 0x8004E488),   # sin table
    (0x80056D48, 4, 0x80051A88),        # GPU primitive pointer
    (0x80057FA4, 9 * 0x30, 0x8005370C), # stage texture slot table (id 0)
    (0x800613B8, 0x20, 0x8005D0F0),     # camera matrix (current)
    (0x800613E8, 0x20, 0x8005D120),     # camera matrix (base)
    (0x80061410, 0x14, 0x8005D150),     # camera angles / position
    (0x800674A4, 1, 0x8005D3E4),        # pause flag
    (0x80068704, 4, SHIM + 4),          # beat flags (shim)
    (0x80068714, 1, SHIM + 8),          # score level (shim)
    (0x800979D0, 1, SHIM + 9),          # previous score level (shim)
    (0x800691B0, 0x180, 0x8005F268),    # stage light block (BAG1 0x800691B0.. = BAG2 - 0x9F48)
    (0x80069368, 4, 0x8008F88C),        # light matrix pointer
    (0x800774DC, 4, 0x8006D980),        # frame accumulator
    (0x800774E4, 4, 0x8006D990),        # ordering table
    (0x800774E8, 4, 0x8006D994),        # frame delta
    (0x800774EC, 4, 0x8006D998),        # buffer index
    (0x800979D4, 4, 0x80089200),        # stage struct pointer
]
LOADS = {'lw', 'sw', 'lh', 'sh', 'lb', 'lbu', 'lhu', 'sb', 'lwl', 'lwr', 'swl', 'swr', 'lwc2', 'swc2'}

def map_addr(a, size1):
    if B1_BASE <= a < B1_BASE + size1: return a + DELTA, 'reloc'
    for s, n, d in GLOBALS:
        if s <= a < s + n: return d + (a - s), 'global'
    return None, None

def port(dbi):
    magic, size, bss = struct.unpack_from('<4sII', dbi, 0)
    assert magic == b'DBI_'
    p = bytearray(dbi[12:12 + size]); img = size + bss
    md = capstone.Cs(capstone.CS_ARCH_MIPS, capstone.CS_MODE_MIPS32 + capstone.CS_MODE_LITTLE_ENDIAN)
    md.detail = True
    W = lambda i: struct.unpack_from('<I', p, i)[0]
    def put(i, w): struct.pack_into('<I', p, i, w)
    stats = {'jal': 0, 'pairs': 0, 'data': 0}; unknown = []
    lui = {}                                  # reg -> (offset of lui, imm, new hi or None)
    code_n = (CODE_END - B1_BASE) // 4
    # a lui in a branch delay slot also reaches the branch target (e.g. 0x801E3A0C -> 0x801E3F64,
    # texture table entry 5 for the night-city backdrop): carry it there, sharing the same entry
    entries = {}; pending = {}
    for k in range(1, code_n - 1):
        w, nw = W(4 * k), W(4 * k + 4); op = w >> 26
        if nw >> 26 != 0x0F or not (op == 1 or 4 <= op <= 7 or 0x14 <= op <= 0x17): continue
        sim = w & 0xFFFF; sim = sim - 0x10000 if sim & 0x8000 else sim
        t = 4 * k + 4 + (sim << 2)
        e = entries.setdefault(4 * k + 4, [4 * k + 4, nw & 0xFFFF, None])
        pending.setdefault(t, []).append(((nw >> 16) & 31, e))
    for k in range(1, code_n):                # word 0 is data (0x26)
        off = 4 * k; w = W(off); op = w >> 26
        for reg, e in pending.get(off, ()): lui[reg] = e
        if op in (2, 3):                      # j / jal
            t = ((B1_BASE + off) & 0xF0000000) | ((w & 0x3FFFFFF) << 2)
            if B1_BASE <= t < B1_BASE + img: nt = t + DELTA
            elif t in FUNCS: nt = FUNCS[t]
            else: unknown.append(('call', hex(B1_BASE + off), hex(t))); continue
            put(off, (w & 0xFC000000) | ((nt >> 2) & 0x3FFFFFF)); stats['jal'] += 1; continue
        if op == 0x0F:                        # lui rt
            lui[(w >> 16) & 31] = entries.get(off) or [off, w & 0xFFFF, None]; continue
        rs, rt, imm = (w >> 21) & 31, (w >> 16) & 31, w & 0xFFFF
        lo_kind = None
        if op in (0x08, 0x09) and rs in lui: lo_kind = 'addiu'
        elif op in (0x20, 0x21, 0x23, 0x24, 0x25, 0x28, 0x29, 0x2B, 0x22, 0x26, 0x2A, 0x2E, 0x32, 0x3A) and rs in lui: lo_kind = 'mem'
        elif op == 0x0D and rs in lui: lo_kind = 'ori'
        if lo_kind:
            lo_off, hi, newhi = lui[rs]
            sim = imm - 0x10000 if (imm & 0x8000 and lo_kind != 'ori') else imm
            a = ((hi << 16) + sim) & 0xFFFFFFFF
            na, kind = map_addr(a, img)
            if na is not None:
                if newhi is None:
                    newhi = ((na + 0x8000) >> 16) & 0xFFFF if lo_kind != 'ori' else na >> 16
                    lui[rs][2] = newhi
                    lw = W(lo_off); put(lo_off, (lw & 0xFFFF0000) | newhi)
                nlo = (na - (newhi << 16)) & 0xFFFFFFFF
                if lo_kind == 'ori': assert nlo < 0x10000
                else:
                    nlo = nlo - 0x100000000 if nlo & 0x80000000 else nlo
                    assert -0x8000 <= nlo < 0x8000, (hex(B1_BASE + off), hex(a), hex(na))
                put(off, (w & 0xFFFF0000) | (nlo & 0xFFFF)); stats['pairs'] += 1
            elif 0x80000000 <= a < 0x801E0000 and not (0x1F800000 <= a < 0x1F801000):
                unknown.append(('global', hex(B1_BASE + off), hex(a)))
        # a write to a register ends its lui pairing; a register copy (addu/or rd, rs, $zero) shares it
        dst = None; src = None
        if op == 0:
            fn = w & 0x3F
            if fn not in (0x08, 0x09, 0x18, 0x19, 0x1A, 0x1B, 0x11, 0x13): dst = (w >> 11) & 31
            if fn in (0x21, 0x25, 0x20) and dst:          # move, or base + index (array access)
                if rs in lui and rt not in lui: src = rs
                elif rt in lui and rs not in lui: src = rt
        elif op in (0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x20, 0x21, 0x23, 0x24, 0x25, 0x22, 0x26): dst = rt
        if dst:
            if src is not None: lui[dst] = lui[src]
            elif dst in lui: del lui[dst]
    # data words that point into the image
    for off in range(CODE_END - B1_BASE, size - 3, 4):
        w = W(off)
        if B1_BASE <= w < B1_BASE + img:
            put(off, w + DELTA); stats['data'] += 1
    return p, bss, stats, unknown

STRUCT_PATCHES = []  # filled by find_struct_sites

def patch_struct_sites(p):
    """BAG1: lw rA, -0x862C(rX)  (stage ptr 0x800979D4, already remapped) ; lw rB, 0xC(rA) ; lw rC, 0x4DC(rB)"""
    n = 0
    for off in range(0, (CODE_END - B1_BASE), 4):
        w = struct.unpack_from('<I', p, off)[0]
        if (w >> 26) == 0x23 and (w & 0xFFFF) == 0x000C:              # lw ?, 0xc(?)
            for k in range(1, 6):
                w2 = struct.unpack_from('<I', p, off + 4 * k)[0]
                if (w2 >> 26) == 0x23 and (w2 & 0xFFFF) == 0x04DC and ((w2 >> 21) & 31) == ((w >> 16) & 31):
                    struct.pack_into('<I', p, off, (w & 0xFFFF0000) | 0x0020)
                    struct.pack_into('<I', p, off + 4 * k, (w2 & 0xFFFF0000) | (4 * 0xB0 + 0x8C))
                    n += 1; break
    return n

def bag1_chart(scus, char_id):
    """BAG1 song chart (main exe table 0x800513DC[id]: start frame, frames, beats, sections
    u16 (mode << 8 | beats), -1; mode 0 = both players, 1/2 = solo; after -1 both play to the end)
    -> BAG2 chart (start, frames, beats, intro beats, sections with mode 0 = no commands,
    1/2 = solo, 3 = both, -1). BAG1 has no intro section: its pre-roll becomes 32 BAG2 intro beats."""
    B = 0x80010000
    p = struct.unpack_from('<I', scus, 0x800513DC + 4 * char_id - B)[0] - B
    start, frames, beats = struct.unpack_from('<3h', scus, p)
    secs = []; o = p + 6
    while True:
        v = struct.unpack_from('<h', scus, o)[0]; o += 2
        if v == -1: break
        secs.append(v)
    used = sum(v & 0xFF for v in secs)
    if used < beats: secs.append(beats - used)              # tail: both players to the end
    intro = 32
    tf, tb = round(frames * (beats + intro) / beats), beats + intro
    st = start - (intro * tf + tb // 2) // tb
    out = [intro]
    for v in secs:
        mode, n = v >> 8, v & 0xFF
        mode = 3 if mode == 0 else mode
        while n > 64: out.append(3 << 8 | 64 if mode == 3 else mode << 8 | 64); n -= 64
        out.append(mode << 8 | n)
    return [st, tf, tb, intro] + out + [-1]

def build(dbi_in, bag2_dbi, chart=None):
    # bag2_dbi: the stock BAG2 stage-0 DBI. Everything from 0x801E5410 on is song data the main exe
    # points at (chart/beat table 0x8004DF08[0] and tables 0x80051AC8.. for id 0), so it is kept as is.
    p, bss, stats, unknown = port(dbi_in)
    n = patch_struct_sites(p)
    # fire-burst sound: BAG1 plays cue 0x4000 on voice slot 20 (BAG2 has 14 slots, and its 0x4000 is
    # the fever cue of stage banks 1-4) -> BAG2 FUN_8002E478(cue 0x5000, -1, -1, -1) picks a free slot;
    # the stage SEDT bank 0 is BAG1's with its cue renumbered 0x4000 -> 0x5000 (build_heat_stage_test.sh)
    for a, old, new in ((0x801E2230, 0x24040014, 0x24045000), (0x801E2234, 0x24054000, 0x2405FFFF)):
        assert struct.unpack_from('<I', p, a - B1_BASE)[0] == old, hex(a)
        struct.pack_into('<I', p, a - B1_BASE, new)
    # night-city backdrop behind broken windows (update FUN_801E358C): tiles $fp = -4..1 around the
    # camera yaw, sized for BAG1's field of view; BAG2's camera sees wider, so the right side had no
    # backdrop and showed stale frame content. Draw -8..5 (off-screen tiles are culled by the code).
    for a, old, new in ((0x801E383C, 0x241EFFFC, 0x241EFFF8), (0x801E4324, 0x2BC20002, 0x2BC20006)):
        assert struct.unpack_from('<I', p, a - B1_BASE)[0] == old, hex(a)
        struct.pack_into('<I', p, a - B1_BASE, new)
    assert struct.unpack_from('<I', p, 0x801E224C - B1_BASE)[0] >> 26 == 3
    struct.pack_into('<I', p, 0x801E224C - B1_BASE, 0x0C000000 | (0x8002E478 >> 2 & 0x3FFFFFF))
    # full image: payload + bss, extended to the trampolines; shim block
    end = 0x801E5410 - B2_BASE
    img = bytearray(end); img[:len(p)] = p
    assert len(p) + bss <= SHIM - B2_BASE
    struct.pack_into('<4s', img, SHIM - B2_BASE, b'B1ST')
    # update helper: run the BAG1 update, then previous level = level (BAG1 main does
    # 0x800979D0 = 0x80068714 after the stage update), so the level-change test sees each change once
    jal = lambda t: 0x0C000000 | ((t >> 2) & 0x3FFFFFF)
    hi = SHIM >> 16; lo = SHIM & 0xFFFF
    # It also adds a black TILE at the back of the OT (entry 0xFFF, linked last = drawn first): the
    # broken windows show the night city strip, but with BAG2's cameras their upper part is above the
    # strip, where nothing was drawn and the previous frames' pixels flickered through.
    R = dict(zero=0, t0=8, t1=9, t2=10, t3=11, t4=12, t5=13, t6=14, t7=15, t8=24, t9=25)
    I = lambda op, rs, rt, imm: (op << 26) | (R[rs] << 21) | (R[rt] << 16) | (imm & 0xFFFF)
    RR = lambda rs, rt, rd, fn: (R[rs] << 21) | (R[rt] << 16) | (R[rd] << 11) | fn
    lui = lambda rt, imm: I(0x0F, 'zero', rt, imm)
    black = [lui('t0', 0x8005), I(0x23, 't0', 't1', 0x1A88), 0,         # t1 = prim pointer 0x80051A88
             I(0x09, 't1', 't2', 16), I(0x2B, 't0', 't2', 0x1A88),       # allocate 4 words
             lui('t3', 0x6000), I(0x2B, 't1', 't3', 4),                  # TILE, rgb 0
             I(0x2B, 't1', 'zero', 8),                                   # x 0, y 0
             lui('t3', 0x01FF), I(0x0D, 't3', 't3', 0x03FF), I(0x2B, 't1', 't3', 12),  # 1023 x 511
             lui('t4', 0x8007), I(0x23, 't4', 't4', 0x10000 - 0x2670), 0,  # t4 = OT (0x8006D990)
             I(0x23, 't4', 't5', 0x3FFC),                                # t5 = OT[0xFFF]
             lui('t6', 0x00FF), I(0x0D, 't6', 't6', 0xFFFF),             # t6 = 0x00FFFFFF
             RR('t5', 't6', 't7', 0x24), lui('t8', 0x0300), RR('t7', 't8', 't7', 0x25),
             I(0x2B, 't1', 't7', 0),                                     # tag = 3 words | next
             RR('t1', 't6', 't9', 0x24), lui('t8', 0xFF00), RR('t5', 't8', 't5', 0x24),
             RR('t5', 't9', 't5', 0x25), I(0x2B, 't4', 't5', 0x3FFC)]   # OT[0xFFF] -> tile
    helper = [0x27BDFFF8, 0xAFBF0000, jal(0x801E358C + DELTA), 0,
              0x3C080000 | hi, 0x91090000 | (lo + 8), 0, 0xA1090000 | (lo + 9)] + black + \
             [0x8FBF0000, 0x27BD0008, 0x03E00008, 0]
    for i, w in enumerate(helper): struct.pack_into('<I', img, SHIM + 0x10 - B2_BASE + 4 * i, w)
    j = lambda t: 0x08000000 | ((t >> 2) & 0x3FFFFFF)
    for addr, words in ((0x801E537C, (0x03E00008, 0x24020001)),             # init: return 1
                        (0x801E539C, (j(SHIM + 0x10), 0)),                  # update -> helper below
                        (0x801E53BC, (0x03E00008, 0x24020001)),             # draw: return 1
                        (0x801E53E4, (j(0x801E4698 + DELTA), 0))):          # setup(heap) -> BAG1 setup
        for i, w in enumerate(words): struct.pack_into('<I', img, addr - B2_BASE + 4 * i, w)
    b2size, b2bss = struct.unpack_from('<II', bag2_dbi, 4)
    tail = bytearray(bag2_dbi[12 + end:12 + b2size])
    if chart:                                     # BAG2 header 4 + 11 sections -> same 15 halfwords
        assert len(chart) <= 15, chart
        struct.pack_into('<%dh' % len(chart), tail, 0, *chart)
    img += tail
    out = struct.pack('<4sII', b'DBI_', len(img), b2bss) + bytes(img)
    return out, stats, n, unknown

if __name__ == '__main__':
    out, stats, n, unknown = build(open(sys.argv[1], 'rb').read(), open(sys.argv[3], 'rb').read())
    open(sys.argv[2], 'wb').write(out)
    print('ported:', stats, 'struct sites', n, 'size', len(out))
    for u in unknown: print('UNMAPPED', *u)
