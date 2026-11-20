"""Build a declarative disc-overlay mod that swaps motions inside a character model entry (F2).

A BUST2.BIN model entry is a DFS container: member 0 = model (000.bin), member 1 = motion
bank (001.bin, size-prefixed list, see tools/bag1import/animlib.py). Swapping two motions
keeps the bank size, so the patched entry fits the stock sectors and only those sectors are
overlaid. The original disc is only read.

Usage (from the project root):
  py -3.13 -m tools.move_viewer.swap_mod --entry 95 --swap 71:6 --id bag2jp.test.move-swap-heat \
      --out _work/move-viewer/f2/pkg
"""
from __future__ import annotations

import argparse
import hashlib
import logging
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.workflow.project_config import assert_write_target, load_config, require_paths  # noqa: E402

logger = logging.getLogger('move_viewer.swap_mod')
SECTOR, RAW_SECTOR, USER_OFFSET = 2048, 2352, 24
ARCHIVE_LBA = 179            # BUST2.BIN (see tools/bag1import/make_alt_entries.py)
BANK_MEMBER = 1
GAME_ID = 'SLPM-86219'
DISC_SHA256 = 'fe8285f2ee5737680abe4ba20e53be9e029e0ab65ff2aa35c4695709bb0e5268'
# Measured bank growth budgets: character folder -> (entries allowed to grow, bytes).
# Heat P1: RAM dump run 20261120T023117463572Z-heat-ramdump-20261119 left 912 B free in the
# player region (0x8005F818 end vs P2 base); disc slack after entry 95 is 1200 B.
# Heat P2: run 20261120T113536848789Z-heat-p2-ramdump-20261120 left 912 B (0x8005F81C end vs
# P2 base + 0x7729C; the P2 tail block DAT_80089230 is consumed by FUN_80033f14 before the
# player struct is placed). Costume 4 entries 167/168 are unmeasured and keep the stock bank.
# Strike, Comet, Shorty, Bi-O (costume A, both sides): runs budget-*-20261120 measured with
# _work/move-viewer/f2/budget_from_dump.py; P1 and P2 free bytes were equal per character.
# Disc slack after each entry is checked separately when the package is built.
# See _work/move-viewer/f2/buffer/growth-budget.md.
GROWTH_BUDGET = {
    'heat': ((95, 96), 912),
    'strike': ((109, 110), 4388),
    'comet': ((93, 94), 15568),
    'shorty': ((107, 108), 1516),
    'bi_o': ((89, 90), 672),
}


def read_user(disc: Path, lba: int, count: int) -> bytes:
    out = bytearray()
    with disc.open('rb') as f:
        for i in range(count):
            f.seek((lba + i) * RAW_SECTOR + USER_OFFSET)
            out += f.read(SECTOR)
    return bytes(out)


def entry_extent(disc: Path, entry: int) -> tuple[int, int]:
    """(archive offset, size) of a BUST2.BIN entry from the DF2_ header."""
    header = read_user(disc, ARCHIVE_LBA, 2)
    if header[:4] != b'DF2_' or entry >= struct.unpack_from('<I', header, 4)[0]:
        raise ValueError(f'entry {entry} not in BUST2.BIN')
    return struct.unpack_from('<II', header, 8 + 8 * entry)


def split_bank(bank: bytes) -> tuple[list[bytes], bytes]:
    """Motions (with their u32 size prefix) and the trailing bytes after the 0 terminator."""
    motions, o = [], 0
    while o + 4 <= len(bank):
        size = struct.unpack_from('<I', bank, o)[0]
        if size == 0:
            break
        if o + 4 + size > len(bank):
            raise ValueError(f'motion {len(motions)} exceeds the bank')
        motions.append(bank[o:o + 4 + size])
        o += 4 + size
    return motions, bank[o:]


def swap_motions(bank: bytes, pairs: list[tuple[int, int]]) -> bytes:
    motions, tail = split_bank(bank)
    for a, b in pairs:
        if a == b or not (0 <= a < len(motions) and 0 <= b < len(motions)):
            raise ValueError(f'invalid swap {a}:{b} for {len(motions)} motions')
        motions[a], motions[b] = motions[b], motions[a]
    return b''.join(motions) + tail


def copy_motions(bank: bytes, assigns: list[tuple[int, int]], max_growth: int = 0) -> bytes:
    """Slot <- copy of an original motion, other slots untouched.

    The bank may grow by at most `max_growth` bytes (0 by default: growth is only
    allowed where the disc slack and the player RAM region were measured, see
    GROWTH_BUDGET). A smaller result is zero-padded after the 0 terminator.
    """
    motions, tail = split_bank(bank)
    result = list(motions)
    for slot, source in assigns:
        if not (0 <= slot < len(motions) and 0 <= source < len(motions)):
            raise ValueError(f'invalid assignment {slot}<-{source} for {len(motions)} motions')
        result[slot] = motions[source]
    body = b''.join(result)
    growth = len(body) + 4 - len(bank)
    if growth > max_growth:
        raise ValueError(f'does not fit: bank grows by {growth} bytes (allowed {max_growth})')
    return body + bytes(4) + bytes(max(0, -growth))


def copy_growth(bank: bytes, assigns: list[tuple[int, int]]) -> int:
    """Bytes the bank would grow with these copies (<= 0 fits)."""
    motions, _ = split_bank(bank)
    sizes = [len(m) for m in motions]
    for slot, source in assigns:
        sizes[slot] = len(motions[source])
    return sum(sizes) + 4 - len(bank)


def patch_entry(container: bytes, member: int, data: bytes) -> bytes:
    if container[:4] != b'DFS_':
        raise ValueError('entry is not a DFS container')
    offset, size = struct.unpack_from('<II', container, 8 + 8 * member)
    if len(data) != size:
        raise ValueError('member size changed')
    return container[:offset] + data + container[offset + size:]


def next_entry_offset(disc: Path, entry: int) -> int:
    """Archive offset of the first entry that starts after `entry` (its disc slack ends there)."""
    header = read_user(disc, ARCHIVE_LBA, 2)
    count = struct.unpack_from('<I', header, 4)[0]
    if 8 + 8 * count > len(header):
        header = read_user(disc, ARCHIVE_LBA, (8 + 8 * count + SECTOR - 1) // SECTOR)
    offset = struct.unpack_from('<I', header, 8 + 8 * entry)[0]
    later = [o for o, _ in struct.iter_unpack('<II', header[8:8 + 8 * count]) if o > offset]
    if not later:
        raise ValueError(f'entry {entry} is the last one: slack unknown')
    return min(later)


def grow_entry(container: bytes, bank: bytes) -> bytes:
    """Container with a larger motion bank; the bank must be the last member."""
    count = struct.unpack_from('<I', container, 4)[0]
    member_offset, member_size = struct.unpack_from('<II', container, 8 + 8 * BANK_MEMBER)
    if count != BANK_MEMBER + 1 or member_offset + member_size != len(container):
        raise ValueError('motion bank is not the last member: cannot grow the entry')
    head = bytearray(container[:member_offset])
    struct.pack_into('<I', head, 8 + 8 * BANK_MEMBER + 4, len(bank))
    return bytes(head) + bank


def build(disc: Path, entry: int, pairs: list[tuple[int, int]],
          copy: bool = False, max_growth: int = 0) -> list[tuple[int, bytes, bytes]]:
    """Overlays (disc user offset, original bytes, patched bytes) for the entry.

    pairs are swaps a:b, or slot<-source copies when `copy` is set. A grown entry also
    needs its 4-byte BUST2.BIN header size field patched (second overlay; composes with
    other mods that only own other header bytes) and must end before the next entry;
    growth past `max_growth` (measured RAM budget) is refused.
    """
    offset, size = entry_extent(disc, entry)
    first = offset // SECTOR
    start = offset % SECTOR
    count = (start + size + SECTOR - 1) // SECTOR
    container = read_user(disc, ARCHIVE_LBA + first, count)[start:start + size]
    member_offset, member_size = struct.unpack_from('<II', container, 8 + 8 * BANK_MEMBER)
    bank = container[member_offset:member_offset + member_size]
    new_bank = copy_motions(bank, pairs, max_growth) if copy else swap_motions(bank, pairs)
    if len(new_bank) == len(bank):
        patched = patch_entry(container, BANK_MEMBER, new_bank)
    else:
        patched = grow_entry(container, new_bank)
        if offset + len(patched) > next_entry_offset(disc, entry):
            raise ValueError(f'entry {entry} would overrun the next BUST2.BIN entry')
    base = (ARCHIVE_LBA + first) * SECTOR + start
    # expected_sha256 guards the stock bytes of the payload's own length (slack included).
    stock = read_user(disc, ARCHIVE_LBA + first,
                      (start + len(patched) + SECTOR - 1) // SECTOR)[start:start + len(patched)]
    overlays = [(base, stock, patched)]
    if len(patched) != size:
        field = 8 + 8 * entry + 4
        overlays.append((ARCHIVE_LBA * SECTOR + field, struct.pack('<I', size),
                         struct.pack('<I', len(patched))))
    return overlays


def find_entries(disc: Path, bank: bytes) -> list[int]:
    """BUST2.BIN entries whose motion-bank member equals `bank` (e.g. the p1 and p2 copies)."""
    header = read_user(disc, ARCHIVE_LBA, 2)
    if header[:4] != b'DF2_':
        raise ValueError('BUST2.BIN header not found')
    count = struct.unpack_from('<I', header, 4)[0]
    if 8 + 8 * count > len(header):
        header = read_user(disc, ARCHIVE_LBA, (8 + 8 * count + SECTOR - 1) // SECTOR)
    found = []
    for entry in range(count):
        offset, size = struct.unpack_from('<II', header, 8 + 8 * entry)
        if size < 24:
            continue
        start = offset % SECTOR
        head = read_user(disc, ARCHIVE_LBA + offset // SECTOR, 1)[start:start + 24]
        if len(head) < 24 or head[:4] != b'DFS_' or struct.unpack_from('<I', head, 4)[0] <= BANK_MEMBER:
            continue
        member_offset, member_size = struct.unpack_from('<II', head, 8 + 8 * BANK_MEMBER)
        if member_size != len(bank):
            continue
        count_sectors = (start + size + SECTOR - 1) // SECTOR
        data = read_user(disc, ARCHIVE_LBA + offset // SECTOR, count_sectors)[start:start + size]
        if data[member_offset:member_offset + member_size] == bank:
            found.append(entry)
    return found


def write_package(out: Path, package_id: str, name: str,
                  overlays: list[tuple[int, bytes, bytes]]) -> None:
    """Write payload/entry_<n>.bin files and the manifest, then re-read and verify them."""
    (out / 'payload').mkdir(parents=True, exist_ok=True)
    files = []
    for i, (_, _, patched) in enumerate(overlays):
        rel = f'payload/entry_{i}.bin'
        (out / rel).write_bytes(patched)
        files.append(rel)
    (out / 'manifest.toml').write_text(manifest(package_id, name, overlays, files), encoding='utf-8')
    import tomllib
    data = tomllib.loads((out / 'manifest.toml').read_text(encoding='utf-8'))
    for entry, (offset, stock, patched) in zip(data['overlay'], overlays, strict=True):
        payload = (out / entry['file']).read_bytes()
        if (entry['offset'] != offset or payload != patched
                or entry['sha256'] != hashlib.sha256(payload).hexdigest()
                or entry['expected_sha256'] != hashlib.sha256(stock).hexdigest()):
            raise ValueError(f'{out}: package verification failed for {entry["file"]}')


def toml_string(text: str) -> str:
    return '"' + text.replace('\\', '\\\\').replace('"', '\\"') + '"'


def manifest(package_id: str, name: str, overlays: list[tuple[int, bytes, bytes]],
             files: list[str]) -> str:
    sha = lambda b: hashlib.sha256(b).hexdigest()  # noqa: E731
    blocks = ''.join(f'''
[[overlay]]
feature = "main"
target = "disc_user"
offset = {offset}
file = "{file}"
sha256 = "{sha(patched)}"
expected_sha256 = "{sha(stock)}"
''' for (offset, stock, patched), file in zip(overlays, files, strict=True))
    return f'''format_version = 11
id = {toml_string(package_id)}
version = "1.0.0"
name = {toml_string(name)}
author = "BAG2JP"
description = {toml_string(f'Test: {name} (generated by tools/move_viewer/swap_mod.py)')}
resolver = "declarative"

[[target]]
game_id = "{GAME_ID}"
disc_sha256 = "{DISC_SHA256}"

[[feature]]
id = "main"
name = {toml_string(name)}
default_enabled = false
''' + blocks


def parse_pair(text: str) -> tuple[int, int]:
    parts = text.split(':')
    if len(parts) != 2 or not all(p.isdigit() for p in parts):
        raise argparse.ArgumentTypeError(f'expected a:b motion indices, got {text!r}')
    return int(parts[0]), int(parts[1])


def check_disc(disc: Path) -> None:
    with disc.open('rb') as f:
        if hashlib.file_digest(f, 'sha256').hexdigest() != DISC_SHA256:
            raise ValueError(f'{disc}: not the {GAME_ID} disc this package targets')


def generate(disc: Path, entries: list[int], pairs: list[tuple[int, int]], package_id: str,
             name: str, out: Path, copy: bool = False,
             max_growth: int = 0) -> list[tuple[int, bytes, bytes]]:
    """Build the overlays of every entry and write the verified package to `out`."""
    if not entries:
        raise ValueError('no BUST2.BIN entry to patch')
    overlays = [o for entry in entries
                for o in build(disc, entry, pairs, copy, max_growth)]
    write_package(out, package_id, name, overlays)
    return overlays


def check_growth_budget(entries: list[int], max_growth: int) -> None:
    """Reject growth outside the RAM-measured GROWTH_BUDGET.

    Args:
        entries: BUST2.BIN entries that will grow; all must belong to one measured character.
        max_growth: requested growth in bytes, 1..budget.

    Raises:
        ValueError: no measured budget covers `entries`, or `max_growth` is out of range.
    """
    for character, (budget_entries, budget) in GROWTH_BUDGET.items():
        if set(entries) <= set(budget_entries):
            if not 0 < max_growth <= budget:
                raise ValueError(f'max growth {max_growth} B outside 1..{budget} B measured for {character}')
            return
    raise ValueError(f'no measured growth budget covers entries {entries}')


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    where = ap.add_mutually_exclusive_group(required=True)
    where.add_argument('--entry', type=int, action='append', help='BUST2.BIN model entry (Heat A p1 = 95)')
    where.add_argument('--bank', type=Path, help='001.bin motion bank: patch every entry that holds it')
    ap.add_argument('--swap', type=parse_pair, action='append', required=True, help='a:b motion indices')
    ap.add_argument('--copy', action='store_true', help='treat a:b as slot a <- copy of motion b')
    ap.add_argument('--max-growth', type=int, default=0,
                    help='allowed bank growth in bytes (only a measured GROWTH_BUDGET value)')
    ap.add_argument('--id', required=True, help='package id')
    ap.add_argument('--out', type=Path, required=True, help='package version dir to write')
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    config = load_config(repo_root=ROOT)
    disc, = require_paths(config, ('inputs.bag2_disc',))
    check_disc(disc)
    out = assert_write_target(config, args.out.resolve(), role='work')
    entries = args.entry or find_entries(disc, args.bank.read_bytes())
    if args.max_growth:
        if not args.copy:
            ap.error('--max-growth only applies with --copy')
        try:
            check_growth_budget(entries, args.max_growth)
        except ValueError as error:
            ap.error(str(error))
    sep = '<-' if args.copy else '<->'
    name = ('Move assign ' if args.copy else 'Move swap ') + ', '.join(f'{a}{sep}{b}' for a, b in args.swap)
    overlays = generate(disc, entries, args.swap, args.id, name, out, args.copy, args.max_growth)
    for offset, stock, patched in overlays:
        logger.info('%s: overlay at %d, %d -> %d bytes', out, offset, len(stock), len(patched))


if __name__ == '__main__':
    main()
