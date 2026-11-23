"""Read raw PHV2 captures without interpreting matrices or capture provenance."""
from dataclasses import dataclass
import struct


# Native contract: mods-src/bag2jp.debug.anim-trace/bag2jp_anim_trace.c.
# These are producer format facts, not configurable host settings.
_MAGIC = 0x32564850
_HEADER = struct.Struct('<4I')
_MATRIX_BYTES = 960
_RECORD_BYTES = _HEADER.size + 2 * _MATRIX_BYTES
_MAX_DRAW_WEIGHT = 0xFFFF  # Producer reads a guest halfword, not a normalized blend.


@dataclass(frozen=True)
class PrehistoryRecord:
    """One raw producer call; actor is an opaque value, not a validated pointer."""

    frame: int
    actor: int
    draw_weight: int
    local_matrices: bytes
    history_matrices: bytes


def parse_prehistory(data: bytes) -> tuple[PrehistoryRecord, ...]:
    """Return records from complete PHV2 bytes, preserving call order and repeats.

    Raise ValueError for non-bytes/empty/incomplete data, bad magic in any record or
    out-of-contract draw weight. Matrix blocks remain opaque bytes from actor
    offsets +0x2C and +0x3EC. Weight is the raw unsigned halfword, not a promise
    of a normalized 0..4096 blend. No session provenance is established here.
    """
    if type(data) is not bytes:
        raise ValueError('PHV2 input must be immutable bytes')
    if not data or len(data) % _RECORD_BYTES:
        raise ValueError('PHV2 data must contain complete nonempty 1936-byte records')
    records = []
    for offset in range(0, len(data), _RECORD_BYTES):
        magic, frame, actor, weight = _HEADER.unpack_from(data, offset)
        if magic != _MAGIC:
            raise ValueError(f'Invalid PHV2 magic at byte {offset}')
        if weight > _MAX_DRAW_WEIGHT:
            raise ValueError(f'Invalid PHV2 draw weight at byte {offset}: {weight}')
        local_start = offset + _HEADER.size
        history_start = local_start + _MATRIX_BYTES
        records.append(PrehistoryRecord(
            frame, actor, weight, data[local_start:history_start],
            data[history_start:offset + _RECORD_BYTES]))
    return tuple(records)


def select_actor_record(records: tuple[PrehistoryRecord, ...], frame: int,
                        actor: int) -> PrehistoryRecord:
    """Return the sole exact frame/actor match from records.

    Raise ValueError when missing or ambiguous; repeated calls are valid records
    but cannot be disambiguated by this pair. Selection verifies no provenance.
    """
    matches = [record for record in records
               if record.frame == frame and record.actor == actor]
    if len(matches) != 1:
        raise ValueError(f'Expected one PHV2 record for frame {frame}, actor {actor:#x}; '
                         f'found {len(matches)}')
    return matches[0]
