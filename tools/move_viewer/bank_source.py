"""Source banks for the Assign panel (F3.1): a character's own bank, its BAG1-imported
variant bank and other characters' banks whose skeleton and node->track map match.

The variant comes from the accepted BAG1 payload (`inputs.bag1_alt_payload`, built by
tools/bag1import): alt_report.json rows + payload/bag1_alt.bin, where an entry starts at
`alt_off - min(alt_off)` and is a DFS container (member 0 model, member 1 motion bank; the
player-1 costume-A pack entry carries the variant's own DBI, hence its node->track map).
Compatibility itself is decided by swap_mod.incompatibilities / require_compatible.
"""
from __future__ import annotations

import hashlib
import json
import logging
import struct
from pathlib import Path

from .swap_mod import BankSource, incompatibilities, skeleton_of

logger = logging.getLogger('move_viewer.bank_source')
# alt_report.json 'chr' of the characters that have a BAG1 variant (alt_report rows, kind 0).
VARIANT_CHARACTER_ID = {'heat': 0, 'strike': 1, 'bi_o': 9}
PLAYER_ONE, DBI_MAGIC = 0, b'DBI_'


def _members(container: bytes) -> list[bytes]:
    if container[:4] != b'DFS_':
        raise ValueError('payload entry is not a DFS container')
    count = struct.unpack_from('<I', container, 4)[0]
    return [container[o:o + s] for o, s in
            (struct.unpack_from('<II', container, 8 + 8 * i) for i in range(count))]


def _slot_map(pack_dir: Path, dbi: bytes | None = None, costume: int = 0) -> list[int] | None:
    """Node->track map from a DBI (None when no player init writes it, see slot_map.py)."""
    from .slot_map import derive_slot_map, find_char_id
    if dbi is None:
        dbi = sorted(pack_dir.glob('*.dbi'))[0].read_bytes()
    try:
        hits = find_char_id(dbi)
        return derive_slot_map(dbi, hits[0][0], costume=costume) if hits else None
    except (IndexError, ValueError, KeyError, struct.error) as error:
        logger.info('slot map not derivable: %s', error)
        return None


def own_source(characters_dir: Path, folder: str) -> BankSource | None:
    """Stock bank of costume A, player 1 of `folder` (assets/archive/characters/<folder>)."""
    base = characters_dir / folder
    bank, model = base / 'model_a_p1/001.bin', base / 'model_a_p1/000.bin'
    if not (bank.is_file() and model.is_file() and (base / 'pack_a_p1').is_dir()):
        return None
    slot_map = _slot_map(base / 'pack_a_p1')
    return BankSource(f'{folder} (BAG2)', bank.read_bytes(),
                      skeleton_of(model.read_bytes(), slot_map))


def variant_source(payload_dir: Path, folder: str) -> BankSource | None:
    """BAG1 variant of `folder` (costume A, player 1) from the accepted payload, or None.

    Raises ValueError when the payload does not match its report (hash, layout).
    """
    chr_id = VARIANT_CHARACTER_ID.get(folder)
    report, blob = payload_dir / 'alt_report.json', payload_dir / 'payload/bag1_alt.bin'
    if chr_id is None or not (report.is_file() and blob.is_file()):
        return None
    data = json.loads(report.read_text(encoding='utf-8'))
    payload = blob.read_bytes()
    if hashlib.sha256(payload).hexdigest() != data['payload_sha256']:
        raise ValueError(f'{blob}: sha256 differs from alt_report.json')
    rows = data['rows']
    base = min(r['alt_off'] for r in rows)
    pack = model = None
    for row in sorted((r for r in rows if r['chr'] == chr_id and r['kind'] == PLAYER_ONE),
                      key=lambda r: r['entry']):
        entry = payload[row['alt_off'] - base:row['alt_off'] - base + row['alt_size']]
        members = _members(entry)
        if len(members) >= 2 and members[1][:4] == DBI_MAGIC:
            pack = pack or members
        elif len(members) >= 2:
            model = model or members
    if pack is None or model is None:
        return None
    from tools.move_viewer.retarget import PROFILES
    return BankSource(f'{folder} (variante BAG1)', model[1],
                      skeleton_of(model[0], _slot_map(Path(), pack[1])), PROFILES.get(folder))


def compatible_others(characters_dir: Path, folder: str, own: BankSource) -> list[BankSource]:
    """Other characters' own banks with no incompatibility against `own` (usually none)."""
    found = []
    for base in sorted(p for p in characters_dir.iterdir() if p.is_dir() and p.name != folder):
        model = base / 'model_a_p1/000.bin'
        if not model.is_file():
            continue
        links = skeleton_of(model.read_bytes(), None).links
        if links != own.skeleton.links:          # cheap prefilter before the slot-map emulation
            continue
        other = own_source(characters_dir, base.name)
        if other is not None and not incompatibilities(own, other):
            found.append(other)
    return found


def sources_for(characters_dir: Path, payload_dir: Path | None, folder: str) -> list[BankSource]:
    """[own, BAG1 variant if any, compatible other characters]; empty without a stock bank."""
    own = own_source(characters_dir, folder)
    if own is None:
        return []
    sources = [own]
    if payload_dir is not None:
        try:
            variant = variant_source(payload_dir, folder)
        except (OSError, ValueError, KeyError) as error:
            logger.warning('BAG1 variant of %s unavailable: %s', folder, error)
            variant = None
        if variant is not None:
            sources.append(variant)
    return sources + compatible_others(characters_dir, folder, own)
