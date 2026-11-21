"""Retarget a motion between skeletons whose tracks have a reviewed one-to-one meaning.

Motion tracks hold absolute local angles per track (pose.py, FUN_80012B9C): when both
skeletons animate the same body part with the same track, angles copy unchanged. What
differs is proportion: the root translation track is scaled by the ratio of rest root
heights. Mappings are explicit per profile; unknown profiles are refused, never guessed.
"""
from __future__ import annotations

import struct
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'bag1import'))
import motion_codec  # noqa: E402


@dataclass(frozen=True)
class Retarget:
    """track_map: source track -> target track; root_scale: target/source root height."""
    track_map: dict[int, int]
    root_scale: float


# Heat BAG1 variant -> BAG2 Heat: probe _work/move-viewer/retarget/probe_heat.py shows 19
# tracks driving the same parts (track 12 = head under node 11 in both); rest root y
# 25053 (BAG1) vs 26740 (BAG2).
PROFILES: dict[str, Retarget] = {
    'heat': Retarget({t: t for t in range(19)}, 26740 / 25053),
    # Bi-O: probe_tracks.py shows the same 19-track parent topology in both versions (BAG1
    # DBI init 0x801CEDBC writes the map with sb); rest root y 25942 (BAG1) vs 26401 (BAG2).
    'bi_o': Retarget({t: t for t in range(19)}, 26401 / 25942),
}


def apply(motion: bytes, retarget: Retarget) -> bytes:
    """Retargeted copy of a size-prefixed motion; events and padding are preserved."""
    body = motion[4:]
    decoded = motion_codec.decode(body)
    missing = [b for b in decoded['bones'] if b not in retarget.track_map]
    if missing:
        raise ValueError(f'tracks {missing} have no reviewed mapping')
    decoded['bones'] = [retarget.track_map[b] for b in decoded['bones']]
    if len(set(decoded['bones'])) != len(decoded['bones']):
        raise ValueError('track map merges two tracks')
    scaled = []
    for axis in decoded['translation']:
        values = [int(round(v * retarget.root_scale)) for v in axis]
        if any(not -0x8000 <= v <= 0x7FFF for v in values):
            raise ValueError('scaled root translation out of range')
        scaled.append(values)
    decoded['translation'] = scaled
    offset = decoded['offset']
    pointer = struct.unpack_from('<I', body, offset)[0]
    events = offset + pointer
    if events < decoded['end']:
        raise ValueError('event table overlaps the streams')
    prefix = bytearray(body[:offset + 4])
    streams = motion_codec.encode(decoded, prefix)[offset + 4:]
    growth = len(streams) - (decoded['end'] - offset - 4)
    struct.pack_into('<I', prefix, offset, pointer + growth)
    prefix[8:8 + len(decoded['bones'])] = bytes(decoded['bones'])
    out = bytes(prefix) + streams + body[decoded['end']:]
    return struct.pack('<I', len(out)) + out
