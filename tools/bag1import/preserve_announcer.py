"""Merge one stock BAG2 announcer cue into the character VAB loaded as SEDT bank 0."""
import argparse
from pathlib import Path
import struct

def banks(data):
    if data[:4] != b"SEDT":
        raise ValueError("Expected SEDT")
    sections = struct.unpack_from("<I", data, 4)[0]
    if sections == 0 or sections % 3:
        raise ValueError("Invalid SEDT section count")
    offsets = list(struct.unpack_from("<%dI" % sections, data, 8)) + [len(data)]
    if offsets[0] < 8 + 4 * sections or offsets != sorted(offsets):
        raise ValueError("Invalid SEDT offsets")
    parts = [data[a:b] for a, b in zip(offsets, offsets[1:])]
    n = sections // 3
    return [(parts[i], parts[n+i], parts[2*n+i]) for i in range(n)]

def cue_records(table):
    count = struct.unpack_from("<I", table)[0]
    if 4 + count * 8 > len(table):
        raise ValueError("Truncated cue table")
    return [table[4+i*8:12+i*8] for i in range(count)]

def pack_banks(items):
    parts = [item[i] for i in range(3) for item in items]
    position = 8 + 4 * len(parts)
    offsets = []
    for part in parts:
        offsets.append(position)
        position += len(part)
    return b"SEDT" + struct.pack("<I", len(parts)) + struct.pack("<%dI" % len(parts), *offsets) + b"".join(parts)

def single_cue(data, cue):
    for head, body, table in banks(data):
        records = cue_records(table)
        matches = [i for i, rec in enumerate(records) if struct.unpack_from("<H", rec)[0] == cue]
        if not matches:
            continue
        if len(matches) != 1 or head[:4] != b"pBAV":
            raise ValueError("Ambiguous cue or invalid VAB")
        program = matches[0]
        ps, ts, vs = struct.unpack_from("<HHH", head, 0x12)
        active = [p for p in range(128) if head[0x20+p*16]]
        if active != list(range(ps)) or len(records) != ps:
            raise ValueError("Requires contiguous cue/program mapping")
        tones = head[0x20+program*16]
        if not 1 <= tones <= 16:
            raise ValueError("Invalid tone count")
        source_sizes = struct.unpack_from("<256H", head, 0x820+ps*512)
        sample_ids = []
        tone_block = bytearray(head[0x820+program*512:0x820+(program+1)*512])
        for t in range(tones):
            vag = struct.unpack_from("<H", tone_block, t*32+22)[0]
            if not 1 <= vag <= vs:
                raise ValueError("Invalid sample id")
            if vag not in sample_ids:
                sample_ids.append(vag)
            struct.pack_into("<HH", tone_block, t*32+20, 0, sample_ids.index(vag)+1)
        out_head = bytearray(0x820+512+512)
        out_head[:0x20] = head[:0x20]
        out_head[0x20:0x30] = head[0x20+program*16:0x30+program*16]
        out_head[0x820:0xa20] = tone_block
        out_body = bytearray()
        for i, vag in enumerate(sample_ids, 1):
            start, size = sum(source_sizes[1:vag])*8, source_sizes[vag]*8
            if start + size > len(body):
                raise ValueError("Truncated VAB sample")
            out_body += body[start:start+size]
            struct.pack_into("<H", out_head, 0xa20+i*2, source_sizes[vag])
        struct.pack_into("<HHH", out_head, 0x12, 1, tones, len(sample_ids))
        struct.pack_into("<I", out_head, 12, len(out_head)+len(out_body))
        return bytes(out_head), bytes(out_body), struct.pack("<I", 1)+records[program]
    raise ValueError("Stock announcer cue not found")

def append_cue(destination, stock, cue):
    items = banks(destination)
    if any(struct.unpack_from("<H", rec)[0] == cue for _, _, table in items for rec in cue_records(table)):
        raise ValueError("Cue already present")
    # Character loading requests SEDT bank 0 only: merge the name into that VAB.
    head, body, table = items[0]
    extra_head, extra_body, extra_table = single_cue(stock, cue)
    ps, ts, vs = struct.unpack_from("<HHH", head, 0x12)
    if ps >= 128 or vs >= 255 or len(items) != 1:
        raise ValueError("Requires one non-full destination bank")
    tone = bytearray(extra_head[0x820:0xa20])
    count = extra_head[0x20]
    extra_vs = struct.unpack_from("<H", extra_head, 0x16)[0]
    if vs + extra_vs > 255:
        raise ValueError("Too many samples")
    for i in range(count):
        vag = struct.unpack_from("<H", tone, i*32+22)[0]
        struct.pack_into("<HH", tone, i*32+20, ps, vs+vag)
    out_head = bytearray(head[:0x820+ps*512] + tone + head[0x820+ps*512:])
    out_head[0x20+ps*16:0x30+ps*16] = extra_head[0x20:0x30]
    sample_table = 0x820+(ps+1)*512
    for i in range(1, extra_vs+1):
        size = struct.unpack_from("<H", extra_head, 0xa20+i*2)[0]
        struct.pack_into("<H", out_head, sample_table+(vs+i)*2, size)
    struct.pack_into("<HHH", out_head, 0x12, ps+1, ts+count, vs+extra_vs)
    struct.pack_into("<I", out_head, 12, len(out_head)+len(body)+len(extra_body))
    records = cue_records(table) + cue_records(extra_table)
    merged_table = struct.pack("<I", len(records)) + b"".join(records)
    return pack_banks([(bytes(out_head), body+extra_body, merged_table)])

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("destination", type=Path)
    p.add_argument("stock", type=Path)
    p.add_argument("output", type=Path)
    p.add_argument("--cue", type=lambda x: int(x, 16), required=True)
    a = p.parse_args()
    result = append_cue(a.destination.read_bytes(), a.stock.read_bytes(), a.cue)
    a.output.write_bytes(result)
    print("Preserved stock announcer cue", hex(a.cue), "bytes", len(result))
