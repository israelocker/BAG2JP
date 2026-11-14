"""Decode/encode BAG2 delta-compressed motions (format read from SLPM_862.19).

Ghidra: FUN_800126f8 (stream setup), FUN_800128b4 (per-keyframe advance),
FUN_80012850 (rewind). Layout of one motion:
  +0 u32 offset of the stream section, minus 4 (streams start at motion+offset+4)
  +4 u16 keyframe count, +6 u8 frames per keyframe, +7 u8 rotation-track count N
  +8 N bytes: bone index of each rotation track
Streams: root translation x,y,z then N bones x 3 axes. Each stream is
  u16 length (bytes, header included), u16 initial value (LE), delta bytes.
Keyframes: frames when step <= 1, else (frames - 2) // step + 2 (FUN_800128b4
maps the last frame to an extra keyframe). Bytes after the last
needed delta are kept verbatim as tails. Deltas advance one per keyframe:
  translation: signed byte, or 0x80 followed by a big-endian 16-bit value;
  rotation: (b - 0x78) for b < 0xf0, else 12-bit signed from (b << 8 | next).
"""
import struct


def _decode_stream(data, kind, count):
    values = [struct.unpack_from('<h', data, 0)[0]]
    i, value = 0, values[0]
    body = data[2:]
    while len(values) < count:
        b = body[i]
        if kind == 'translation':
            if b == 0x80:
                delta = (body[i + 1] << 8) | body[i + 2]
                i += 3
            else:
                delta = b - 256 if b >= 128 else b
                i += 1
        elif b & 0xf0 == 0xf0:
            raw = ((b << 8) | body[i + 1]) & 0xfff
            delta = raw - 0x1000 if raw & 0x800 else raw
            i += 2
        else:
            delta = b - 0x78
            i += 1
        value = (value + delta + 0x8000) % 0x10000 - 0x8000
        values.append(value)
    return values, i


def keyframes(frames, step):
    return frames if step <= 1 else (frames - 2) // step + 2


def decode(motion):
    """Return dict with header fields and per-track per-axis value lists."""
    offset, frames, step, tracks = struct.unpack_from('<IHBB', motion, 0)
    bones = list(motion[8:8 + tracks])
    pos = offset + 4
    count = keyframes(frames, step)
    streams, tails = [], []
    for track in range(1 + tracks):
        axes = []
        for _ in range(3):
            length = struct.unpack_from('<H', motion, pos)[0]
            chunk = motion[pos + 2:pos + length]
            values, used = _decode_stream(chunk, 'translation' if track == 0 else 'rotation', count)
            axes.append(values)
            tails.append(bytes(chunk[2 + used:]))
            pos += length
        streams.append(axes)
    return {'offset': offset, 'frames': frames, 'step': step, 'bones': bones,
            'translation': streams[0], 'rotations': streams[1:], 'tails': tails, 'end': pos}


def _encode_stream(values, kind):
    out = bytearray(struct.pack('<h', values[0]))
    for prev, cur in zip(values, values[1:]):
        delta = (cur - prev + 0x8000) % 0x10000 - 0x8000
        if kind == 'translation':
            if -128 <= delta <= 127 and delta != -128:
                out.append(delta & 0xff)
            else:
                out += bytes((0x80, (delta >> 8) & 0xff, delta & 0xff))
        elif -0x78 <= delta <= 0x77:
            out.append(delta + 0x78)
        elif -0x800 <= delta <= 0x7ff:
            raw = delta & 0xfff
            out += bytes((0xf0 | raw >> 8, raw & 0xff))
        else:
            raise ValueError(f'rotation delta out of range: {delta}')
    return bytes(out)


def encode(decoded, prefix):
    """Rebuild a motion; prefix holds the original bytes before the stream section."""
    body = bytearray()
    tracks = [('translation', decoded['translation'])] + [('rotation', r) for r in decoded['rotations']]
    count = keyframes(decoded['frames'], decoded['step'])
    tails = iter(decoded['tails'])
    for kind, axes in tracks:
        for values in axes:
            assert len(values) == count
            chunk = _encode_stream(values, kind) + next(tails)
            body += struct.pack('<H', len(chunk) + 2) + chunk
    return bytes(prefix) + bytes(body)
