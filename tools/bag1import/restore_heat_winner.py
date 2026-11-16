"""Audit/restore the shared Heat victory-name cue in the existing alternate payload."""
from pathlib import Path
import argparse
import hashlib
import re
import sys
import tomllib
sys.path.insert(0, str(Path(__file__).resolve().parent))
from preserve_announcer import append_cue, banks, cue_records, single_cue
from host_inputs import input_path

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--apply", action="store_true")
    a = p.parse_args()
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(input_path("tools.psx_asset_tools")))
    from psxassets import containers
    package = root / "mods-src/bag2jp.feature.bag1-content"
    manifest = package / "1.0.0/manifest.toml"
    with manifest.open(encoding="utf-8", newline="") as stream:
        text = stream.read()
    spec = tomllib.loads(text)
    overlay = next(x for x in spec["overlay"] if x.get("file") == "payload/bag1_alt.bin")
    payload = manifest.parent / overlay["file"]
    original = payload.read_bytes()
    old_hash = hashlib.sha256(original).hexdigest()
    if old_hash != overlay["sha256"]:
        raise ValueError("Payload differs from its manifest; preserve existing changes")
    data = bytearray(original)
    header = (package / "bag2jp_bag1_alt_index.h").read_text()
    rows = re.findall(r"\{(\d+), 0, [01], 0x[0-9A-F]+u, \d+u, 0x([0-9A-F]+)u, (\d+)u\}", header)
    entries = {int(i): (int(offset, 16)-(224035-179)*2048, int(size)) for i, offset, size in rows}
    changes = 0
    for entry, costume, side in ((59,"a","p1"),(60,"a","p2"),(131,"b","p1"),(132,"b","p2")):
        start, size = entries[entry]
        if start < 0 or start + size > len(data):
            raise ValueError("Alternate pack is outside the payload")
        packed = bytes(data[start:start+size])
        if not containers.is_archive(packed):
            raise ValueError("Invalid alternate character archive")
        table = containers.parse_archive(packed)
        children = [packed[o:o+n] for o, n in table]
        slot = 5 if side == "p1" else 4
        stock = (root / f"assets/archive/characters/heat/pack_{costume}_{side}/{slot:03d}.sedt").read_bytes()
        ids = [int.from_bytes(rec[:2], "little") for rec in cue_records(banks(children[slot])[0][2])]
        if 0x1007 not in ids:
            if not a.apply:
                raise ValueError(f"Entry {entry}: missing Heat victory-name cue 0x1007")
            children[slot] = append_cue(children[slot], stock, 0x1007)
            alignment = containers.detect_alignment(table, 8+8*len(table))
            replacement = containers.build_archive(packed[:4], children, alignment)
            if len(replacement) > size:
                raise ValueError("Updated pack exceeds its allocated slot")
            data[start:start+size] = replacement.ljust(size, b"\0")
            changes += 1
        if single_cue(children[slot], 0x1007) != single_cue(stock, 0x1007):
            raise ValueError("Victory-name cue differs from stock BAG2")
        print(f"entry {entry}: original Heat name and BAG1 voice bank verified")
    if a.apply and changes:
        new_hash = hashlib.sha256(data).hexdigest()
        old_field = 'sha256 = "' + old_hash + '"'
        if text.count(old_field) != 1:
            raise ValueError("Ambiguous payload hash in manifest")
        new_text = text.replace(old_field, 'sha256 = "' + new_hash + '"')
        payload.write_bytes(data)
        with manifest.open("w", encoding="utf-8", newline="") as stream:
            stream.write(new_text)
        print("Updated four Heat voice packs; payload SHA256", new_hash)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
