"""Build the DUMMY.BIN alternate-entry payload from exact per-entry files.

`make_alt_entries.py` rebuilds each entry from stock sectors patched by
sector-aligned overlays, so an alternate entry can never be larger than the
stock one: the tail is silently dropped. BAG1 imports need the opposite -
converted packs and models may be a few dozen bytes bigger, and the versions
plugin already rewrites the DF2_ table's size field from `alt_size`.

This tool takes a JSON spec whose rows name the exact bytes of each alternate
entry:

    {"rows": [{"entry": 73, "chr": 1, "kind": 0, "file": "pack_a_p1.dfs"}]}

For regional entries, replace ``file`` with ``regions`` containing exactly
``international`` and ``japanese`` file paths. Both receive exact offsets/sizes;
identical bytes share storage. Legacy rows have no Japanese variant (jp_size=0),
not an implicitly Japanese copy of their International payload.

Stock offset/size always come from the disc's DF2_ table; only the payload
comes from the file, so a row can never point the game at the wrong entry.
Entries are stored sector-aligned in DUMMY.BIN and recorded with their exact
byte length.

Usage:
    py -3.13 tools/bag1import/make_alt_entries_exact.py <disc.bin> <spec.json> <out_dir>
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from iso_extract import Disc  # noqa: E402

ARCHIVE = "BUST2.BIN"
DUMMY = "DUMMY.BIN"
SECTOR = 2048


def extents(disc: Disc) -> dict[str, tuple[int, int]]:
    """Map each disc file name to its (lba, size)."""
    return {Path(name).name: (lba, size) for name, lba, size in disc.walk()}


def read_entries(header: bytes, entries: list[int]) -> dict[int, tuple[int, int]]:
    """Return the stock {offset, size} of each entry from the DF2_ header."""
    if header[:4] != b"DF2_":
        raise SystemExit("BUST2.BIN does not start with a DF2_ table")
    table = {}
    for entry in entries:
        offset = int.from_bytes(header[8 + entry * 8:12 + entry * 8], "little")
        size = int.from_bytes(header[12 + entry * 8:16 + entry * 8], "little")
        if size == 0:
            raise SystemExit(f"entry {entry} is empty in the stock table")
        table[entry] = (offset, size)
    return table


def _store_variant(file: str, payload: bytearray, seen: dict, base: int) -> tuple[int, int, int, str]:
    data = Path(file).read_bytes()
    if not data:
        raise ValueError(f"empty alternate file: {file}")
    digest = hashlib.sha256(data).hexdigest()
    if digest not in seen:
        seen[digest] = len(payload) // SECTOR
        payload.extend(data)
        payload.extend(b"\x00" * (-len(payload) % SECTOR))
    start = seen[digest]
    return base + start * SECTOR, len(data), start, digest


def build(spec: dict, disc: Disc) -> tuple[bytes, list[dict], str]:
    """Pack every row's exact bytes into one sector-aligned payload."""
    rows = spec["rows"]
    layout = extents(disc)
    archive_lba, _ = layout[ARCHIVE]
    dummy_lba, dummy_size = layout[DUMMY]
    stock = read_entries(disc.read(archive_lba, 4096), [row["entry"] for row in rows])
    capacity = dummy_size  # dummy_size is already in bytes

    payload = bytearray()
    index = []
    seen = {}
    for row in rows:
        entry = row["entry"]
        regions = row.get("regions")
        if "regions" in row and (not isinstance(regions, dict)
                or set(regions) != {"international", "japanese"} or "file" in row):
            raise ValueError(f"entry {entry}: regions requires exactly international/japanese and no file")
        file = regions["international"] if regions else row["file"]
        base = (dummy_lba - archive_lba) * SECTOR
        alt_off, alt_size, start, digest = _store_variant(file, payload, seen, base)
        jp_off, jp_size, jp_digest = 0, 0, None
        if regions:
            jp_off, jp_size, _, jp_digest = _store_variant(regions["japanese"], payload, seen, base)
        offset, size = stock[entry]
        index.append({
            "entry": entry, "chr": row["chr"], "kind": row["kind"],
            "off": offset, "size": size,
            # DUMMY offsets are stored relative to the archive base, like the stock table.
            "alt_off": alt_off, "alt_size": alt_size,
            "jp_off": jp_off, "jp_size": jp_size,
            "sectors": start,
            "file": file,
            "sha256": digest,
            "jp_file": regions["japanese"] if regions else None,
            "jp_sha256": jp_digest,
        })
    if len(payload) > capacity:
        raise SystemExit(f"payload {len(payload)} exceeds DUMMY.BIN capacity {capacity}")
    # Compute expected_sha256 from actual stock data in DUMMY.BIN, not zeros.
    stock_data = disc.read(dummy_lba, len(payload))
    expected_digest = hashlib.sha256(stock_data).hexdigest()
    return bytes(payload), index, expected_digest


def render_index(index: list[dict]) -> str:
    """Render the C header consumed by bag2jp_bag1_versions.c."""
    lines = [
        f"#define B1_ALT_CONTENT_TAG 0x{int(0):08X}u",
        "/* Generated by tools/bag1import/make_alt_entries_exact.py: BUST2.BIN entries",
        " * with a BAG1 version stored in DUMMY.BIN. kind: 0 player 1, 1 player 2,",
        " * 2 fever (winner), 3 stage. */",
        "typedef struct { uint16_t entry; uint8_t chr, kind; uint32_t off, size,"
         " alt_off, alt_size, jp_off, jp_size; } B1AltEntry;",
        "static const B1AltEntry b1_alt_entries[] = {",
    ]
    for row in index:
        lines.append(f"    {{{row['entry']}, {row['chr']}, {row['kind']}, "
                     f"0x{row['off']:X}u, {row['size']}u, "
                      f"0x{row['alt_off']:X}u, {row['alt_size']}u, "
                      f"0x{row.get('jp_off', 0):X}u, {row.get('jp_size', 0)}u}},")
    lines.append("};")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("disc", type=Path)
    parser.add_argument("spec", type=Path)
    parser.add_argument("out_dir", type=Path)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    disc = Disc(args.disc)
    try:
        payload, index, expected_digest = build(spec, disc)
    finally:
        disc.f.close()

    digest = hashlib.sha256(payload).hexdigest()
    out = args.out_dir
    (out / "payload").mkdir(parents=True, exist_ok=True)
    (out / "payload" / "bag1_alt.bin").write_bytes(payload)
    header = render_index(index).replace("0x00000000u", f"0x{digest[:8].upper()}u", 1)
    (out / "bag2jp_bag1_alt_index.h").write_text(header, encoding="utf-8", newline="\n")
    (out / "alt_report.json").write_text(json.dumps({
        "payload_bytes": len(payload),
        "payload_sectors": len(payload) // SECTOR,
        "payload_sha256": digest,
        "expected_sha256": expected_digest,
        "rows": index,
    }, indent=2) + "\n", encoding="utf-8")
    print(f"{len(index)} entries, {len(payload) // SECTOR} sectors, sha256 {digest}")
    for row in index:
        delta = row["alt_size"] - row["size"]
        print(f"entry {row['entry']}: chr {row['chr']} kind {row['kind']} "
              f"size {row['size']} -> {row['alt_size']} ({delta:+d}) DUMMY+{row['sectors']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
