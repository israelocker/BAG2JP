"""Fit a single-bank character voice SEDT into an SPU byte budget.

Two steps, applied in order by fit_voice_budget():
  1. dedupe_samples(): lossless; programs that use byte-identical VAG bodies
     share one sample, as stock BAG2 voice banks already do.
  2. resample_samples(): lossy; decodes the selected PS-ADPCM samples,
     resamples them by r = 2^(-units/1536) and re-encodes them. Each tone that
     uses a resampled sample raises center/shift by `units` 1/128 semitones,
     because SsPitchFromNote computes center + (shift+fine)/128 - note
     (Ghidra 8003BA10/80039314, notes/tool-evidence ghidra-034).
"""
import logging
import math
import struct
from fractions import Fraction

import numpy as np
from scipy.signal import resample_poly

from preserve_announcer import banks, pack_banks

logger = logging.getLogger("vab_budget")

FILTERS = ((0, 0), (60, 0), (115, -52), (98, -55), (122, -60))
BLOCK = 16
SAMPLES_PER_BLOCK = 28
UNITS_PER_OCTAVE = 12 * 128
FLAG_LOOP_START = 4
FLAG_END = 1
FLAG_TAIL = 7


class Vab:
    """Mutable view of the bank-0 VAB of a one-bank SEDT."""

    def __init__(self, sedt: bytes):
        items = banks(sedt)
        if len(items) != 1:
            raise ValueError("Requires a one-bank SEDT")
        head, body, self.table = items[0]
        if head[:4] != b"pBAV":
            raise ValueError("Invalid VAB")
        self.programs, self.tones, count = struct.unpack_from("<HHH", head, 0x12)
        self.head = bytearray(head)
        table = 0x820 + self.programs * 512
        sizes = struct.unpack_from("<%dH" % (count + 1), head, table)[1:]
        self.samples: list[bytes] = []
        position = 0
        for size in sizes:
            self.samples.append(bytes(body[position:position + size * 8]))
            position += size * 8
        if position != len(body):
            raise ValueError("VAB sample table does not match body")

    def tone_records(self) -> list[int]:
        """Return head offsets of every active tone record."""
        offsets = []
        for program in range(self.programs):
            for tone in range(self.head[0x20 + program * 16]):
                offsets.append(0x820 + program * 512 + tone * 32)
        return offsets

    def body_bytes(self) -> int:
        """Return the SPU body size of the bank."""
        return sum(len(sample) for sample in self.samples)

    def pack(self) -> bytes:
        """Serialize back to a one-bank SEDT with updated head fields."""
        head = self.head
        table = 0x820 + self.programs * 512
        head[table:table + 512] = bytes(512)
        for index, sample in enumerate(self.samples, 1):
            struct.pack_into("<H", head, table + index * 2, len(sample) // 8)
        struct.pack_into("<H", head, 0x16, len(self.samples))
        body = b"".join(self.samples)
        struct.pack_into("<I", head, 12, len(head) + len(body))
        return pack_banks([(bytes(head), body, self.table)])


def dedupe_samples(sedt: bytes) -> bytes:
    """Make tones share byte-identical samples and drop the duplicates.

    Args:
        sedt: One-bank voice SEDT.

    Returns:
        SEDT with the same programs/cues and only unique sample bodies.
    """
    vab = Vab(sedt)
    unique: list[bytes] = []
    remap = {}
    for index, sample in enumerate(vab.samples, 1):
        if sample not in unique:
            unique.append(sample)
        remap[index] = unique.index(sample) + 1
    for offset in vab.tone_records():
        old = struct.unpack_from("<H", vab.head, offset + 22)[0]
        struct.pack_into("<H", vab.head, offset + 22, remap[old])
    vab.samples = unique
    return vab.pack()


def decode_adpcm(data: bytes) -> np.ndarray:
    """Decode PS-ADPCM blocks to signed 16-bit PCM."""
    out = np.zeros(len(data) // BLOCK * SAMPLES_PER_BLOCK, dtype=np.int32)
    s1 = s2 = 0
    for block in range(len(data) // BLOCK):
        header = data[block * BLOCK]
        shift, f0, f1 = header & 15, *FILTERS[min(header >> 4, 4)]
        for i in range(SAMPLES_PER_BLOCK):
            nibble = (data[block * BLOCK + 2 + i // 2] >> (4 * (i & 1))) & 15
            value = ((nibble - 16 if nibble > 7 else nibble) << 12) >> shift
            value += (s1 * f0 + s2 * f1 + 32) >> 6
            value = max(-32768, min(32767, value))
            out[block * SAMPLES_PER_BLOCK + i] = value
            s2, s1 = s1, value
    return out.astype(np.int16)


def _encode_block(pcm: np.ndarray, s1: int, s2: int) -> tuple[bytes, int, int]:
    """Encode 28 samples with the filter/shift pair of least squared error."""
    best = None
    for index, (f0, f1) in enumerate(FILTERS):
        for shift in range(13):
            h1, h2, error, nibbles = s1, s2, 0, []
            for sample in pcm:
                predicted = (h1 * f0 + h2 * f1 + 32) >> 6
                scaled = ((int(sample) - predicted) << shift) + 2048 >> 12
                nibble = max(-8, min(7, scaled))
                value = max(-32768, min(32767, ((nibble << 12) >> shift) + predicted))
                error += (value - int(sample)) ** 2
                if best is not None and error >= best[0]:
                    break
                nibbles.append(nibble & 15)
                h2, h1 = h1, value
            else:
                best = (error, index, shift, nibbles, h1, h2)
    _, index, shift, nibbles, h1, h2 = best
    packed = bytes(nibbles[i] | nibbles[i + 1] << 4 for i in range(0, SAMPLES_PER_BLOCK, 2))
    return bytes((index << 4 | shift, 0)) + packed, h1, h2


def encode_adpcm(pcm: np.ndarray) -> bytes:
    """Encode PCM as a one-shot VAG body in the stock BAG2 layout.

    Layout: silent lead block, data blocks (loop-start flag on the first, end
    flag on the last), then a silent flag-7 tail block.
    """
    count = max(1, math.ceil(len(pcm) / SAMPLES_PER_BLOCK))
    padded = np.zeros(count * SAMPLES_PER_BLOCK, dtype=np.int32)
    padded[:len(pcm)] = pcm
    blocks = [bytearray(BLOCK)]
    s1 = s2 = 0
    for block in range(count):
        data, s1, s2 = _encode_block(padded[block * 28:(block + 1) * 28], s1, s2)
        blocks.append(bytearray(data))
    blocks[1][1] |= FLAG_LOOP_START
    blocks[-1][1] |= FLAG_END
    tail = bytearray(BLOCK)
    tail[1] = FLAG_TAIL
    blocks.append(tail)
    return b"".join(bytes(block) for block in blocks)


def payload(sample: bytes) -> bytes:
    """Return the data blocks between the silent lead and the flag-7 tail."""
    if sample[:BLOCK] != bytes(BLOCK) or sample[-BLOCK + 1] != FLAG_TAIL:
        raise ValueError("Unexpected one-shot VAG layout")
    return sample[BLOCK:-BLOCK]


def ratio_for_units(units: int) -> Fraction:
    """Rational resampling ratio whose pitch error is under 1/256 semitone."""
    return Fraction(2 ** (-units / UNITS_PER_OCTAVE)).limit_denominator(512)


def resample_samples(sedt: bytes, sample_ids: list[int], units: int) -> bytes:
    """Resample selected samples by 2^(-units/1536) and compensate tone pitch.

    Args:
        sedt: One-bank voice SEDT.
        sample_ids: 1-based VAG ids to resample; others stay byte-exact.
        units: Pitch compensation in 1/128 semitones (> 0 lowers the rate).

    Returns:
        SEDT with re-encoded samples and raised center/shift on their tones.
    """
    vab = Vab(sedt)
    ratio = ratio_for_units(units)
    actual = round(UNITS_PER_OCTAVE * math.log2(1 / ratio))
    for sample_id in sample_ids:
        pcm = decode_adpcm(payload(vab.samples[sample_id - 1])).astype(np.float64)
        resampled = resample_poly(pcm, ratio.numerator, ratio.denominator)
        clipped = np.clip(np.rint(resampled), -32768, 32767).astype(np.int32)
        vab.samples[sample_id - 1] = encode_adpcm(clipped)
    for offset in vab.tone_records():
        if struct.unpack_from("<H", vab.head, offset + 22)[0] not in sample_ids:
            continue
        total = vab.head[offset + 4] * 128 + vab.head[offset + 5] + actual
        if total // 128 > 127:
            raise ValueError("Pitch compensation exceeds note range")
        vab.head[offset + 4], vab.head[offset + 5] = divmod(total, 128)
    return vab.pack()


def fit_voice_budget(sedt: bytes, keep_samples: list[bytes], max_body: int,
                     step: int = 16) -> tuple[bytes, int]:
    """Dedupe, then resample every sample not in keep_samples until it fits.

    Args:
        sedt: One-bank voice SEDT.
        keep_samples: Sample bodies that must stay byte-exact (stock content).
        max_body: Maximum SPU body bytes.
        step: Search increment in 1/128 semitones.

    Returns:
        (fitted SEDT, applied units); units is 0 when dedup alone fits.
    """
    deduped = dedupe_samples(sedt)
    vab = Vab(deduped)
    if vab.body_bytes() <= max_body:
        return deduped, 0
    keep = sum(len(s) for s in vab.samples if s in keep_samples)
    targets = [i for i, s in enumerate(vab.samples, 1) if s not in keep_samples]
    blocks = {i: len(payload(vab.samples[i - 1])) // BLOCK * SAMPLES_PER_BLOCK for i in targets}
    units = step
    while units <= UNITS_PER_OCTAVE * 2:
        ratio = ratio_for_units(units)
        estimate = keep + sum(
            (math.ceil(blocks[i] * ratio / SAMPLES_PER_BLOCK) + 2) * BLOCK for i in targets)
        if estimate <= max_body:
            fitted = resample_samples(deduped, targets, units)
            if Vab(fitted).body_bytes() <= max_body:
                logger.info("Voice bank fitted: %d units, %d bytes", units, Vab(fitted).body_bytes())
                return fitted, units
        units += step
    raise ValueError("Voice bank cannot fit the budget within two octaves")
