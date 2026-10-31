"""Read-only comparison of BAG1/BAG2 Dance View labels and installed Heat animations."""
from pathlib import Path
import argparse, hashlib, json, re, struct, sys

PROJECT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--package", type=Path, required=True, help="Installed bag1-content package")
parser.add_argument("--output", type=Path, help="Optional JSON report path (parent must exist)")
args = parser.parse_args()
sys.path.insert(0, str(PROJECT / "tools/bag1import"))
from animlib import anim_list, dfs_entries, frames
from anim_remap import fix_events
from rebase_cues import rebase_events, b1_cue_base

b1_view = (PROJECT / "_work/bag1_disc/BIN1/VIEW.DBI").read_bytes()[12:]
b2_view = (PROJECT / "assets/archive/system/008.dbi").read_bytes()[12:]
b1_exe = (PROJECT / "_work/bag1/scus.bin").read_bytes()
b2_exe = (PROJECT / "_work/mainexe/slpm.bin").read_bytes()
source = anim_list((PROJECT / "_work/bag1_assets/heat/PLAYER2_P_HEATA2/001.bin").read_bytes())

def labels(data, base, pointer_table, requests, count):
    result = {}
    for i in range(count):
        ptr = struct.unpack_from("<I", data, pointer_table-base+4*i)[0]-base
        if not 0 <= ptr < len(data):
            raise ValueError(f"Bad label pointer at index {i}")
        name = data[ptr:].split(b"\0", 1)[0].decode("ascii")
        result[name] = {"index": i, "request": data[requests-base+i]}
    return result

b1_labels = labels(b1_view, 0x8009CC50, 0x8009F84C, 0x8009FD88, 66)
label_offset = b2_view.find(struct.pack("<I", 0x8008FAF8))
if label_offset < 0:
    raise ValueError("BAG2 NEUTRAL label table not found")
b2_labels = labels(b2_view, 0x8008F890, 0x8008F890+label_offset, 0x80092484, 87)
assert b1_labels["TIRED"]["request"] == 124
assert b2_labels["TIRED"]["request"] == 123
assert b2_labels["GUARD"]["request"] == 171

package = args.package
payload = (package / "payload/bag1_alt.bin").read_bytes()
header = (PROJECT / "mods-src/bag2jp.feature.bag1-content/bag2jp_bag1_alt_index.h").read_text()
rows = re.findall(r"\{(\d+), \d+, \d+, 0x[0-9A-F]+u, \d+u, 0x([0-9A-F]+)u, (\d+)u\}", header)
models = {}
for entry, offset, size in rows:
    entry = int(entry)
    if entry not in (95, 96, 167, 168):
        continue
    offset = int(offset, 16) - (224035 - 179) * 2048
    data = payload[offset:offset+int(size)]
    models[entry] = anim_list(dfs_entries(data)[1])
assert set(models) == {95, 96, 167, 168}
converted = [rebase_events(fix_events(anim), 0x1000, b1_cue_base(0), 0x100)
             for anim in source]
role_rows = []
for name in ("TIRED", "GUARD", "REFLECT", "DODGE", "MISS1", "MISS6"):
    req = b2_labels[name]["request"]
    slot = b2_exe[0x8005181C + req - 0x80010000]
    matches = [i for i, anim in enumerate(converted) if anim == models[95][slot]]
    for entry, model in models.items():
        assert model[slot] == models[95][slot], (entry, name)
    names = []
    for source_name, record in b1_labels.items():
        request = record["request"]
        if 100 <= request < 180:
            anim_index = b1_exe[0x80055838+request-0x80010000]
            if anim_index in matches:
                names.append(source_name)
    role_rows.append({"bag2": name, "request": req, "slot": slot,
                      "installed_bag1_indices": matches, "bag1_labels": names,
                      "frames": frames(models[95][slot])})
report = {"payload_sha256": hashlib.sha256(payload).hexdigest(),
          "bag1_view": b1_labels, "bag2_view": b2_labels,
          "installed_roles": role_rows}
if args.output:
    args.output.write_text(json.dumps(report, indent=2)+"\n")
for row in role_rows:
    print(f"{row['bag2']}: BAG2 req {row['request']} slot {row['slot']} -> BAG1 {row['installed_bag1_indices']} {row['bag1_labels']}")
print("Checked roles agree across all four installed model lists.")
if args.output:
    print("Report:", args.output)
