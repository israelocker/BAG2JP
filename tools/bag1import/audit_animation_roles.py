"""Complete read-only installed Heat animation inventory; no game files are modified."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import struct
import sys
import tomllib

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--project", type=Path, default=Path(__file__).resolve().parents[2])
parser.add_argument("--package", type=Path, required=True)
parser.add_argument("--output", type=Path)
parser.add_argument("--bag1-japan", type=Path, help="Optional JP raw disc for regional animation comparison")
args = parser.parse_args()
root = args.project
sys.path.insert(0, str(root / "tools/bag1import"))
from animlib import anim_list, dfs_entries, frames, info
from anim_remap import fix_events, mute_voices, build, EMPTY, POLICY
from animation_policy import adapt_events
policy_roles = {row["target"]: row for row in POLICY["roles"]}
from rebase_cues import rebase_events, b1_cue_base

def sha(data):
    return hashlib.sha256(data).hexdigest()

def u32(data, offset):
    return struct.unpack_from("<I", data, offset)[0]

def view_labels(data, base, pointers, requests, count):
    rows = []
    for index in range(count):
        pointer = u32(data, pointers-base+4*index)-base
        if not 0 <= pointer < len(data):
            raise ValueError("Label pointer outside overlay")
        end = data.index(0, pointer)
        rows.append({"index": index, "name": data[pointer:end].decode("ascii"),
                     "request": data[requests-base+index]})
    return rows

def resolve(exe, game, request):
    if game == 1:
        if request < 36:
            address = 0x80055830 + request
        elif 50 <= request <= 52:
            address = 0x8005585e + request
        elif 60 <= request <= 62:
            address = 0x80055857 + request
        elif 70 <= request <= 72:
            address = 0x80055850 + request
        elif 100 <= request < 180:
            address = 0x80055838 + request
        elif 200 <= request < 300:
            address = 0x800558ec + request - 200
        else:
            return None
    else:
        if request < 43:
            address = 0x8005180c + request
        elif request < 100:
            address = 0x8005182e + request
        elif request < 200:
            address = 0x8005181c + request
        else:
            address = 0x800518e4 + request - 200
    result = exe[address-0x80010000]
    return None if result == 255 else result

def metadata(anim):
    if anim == EMPTY:
        return {"frames": 0, "beats": 0, "events": [], "empty": True, "motion_sha256": None}
    header, events, info_offset, _ = info(anim)
    beats = struct.unpack_from("<H", header, 2)[0]
    return {"frames": frames(anim), "beats": beats, "events": events, "empty": False, "motion_sha256": sha(anim[:info_offset])}

b1exe = (root/"_work/bag1/scus.bin").read_bytes()
b2exe = (root/"_work/mainexe/slpm.bin").read_bytes()
b1view = (root/"_work/bag1_disc/BIN1/VIEW.DBI").read_bytes()[12:]
b2view = (root/"assets/archive/system/008.dbi").read_bytes()[12:]
b1labels = view_labels(b1view, 0x8009cc50, 0x8009f84c, 0x8009fd88, 66)
b2pointer = b2view.index(struct.pack("<I", 0x8008faf8)) + 0x8008f890
b2labels = view_labels(b2view, 0x8008f890, b2pointer, 0x80092484, 87)
source = anim_list((root/"_work/bag1_assets/heat/PLAYER2_P_HEATA2/001.bin").read_bytes())
if len(source) != 84:
    raise ValueError("Unexpected BAG1 Heat animation count")
source_names = defaultdict(list)
for row in b1labels:
    source_names[resolve(b1exe, 1, row["request"])].append(row["name"])
b1alternates = [tuple(b1exe[0x45854+4*i:0x45858+4*i]) for i in range(15)]
b2alternates = [tuple(b2exe[0x41838+4*i:0x4183c+4*i]) for i in range(10)]
for normal, alternate, previous_a, previous_b in b1alternates:
    source_names[alternate].append("ALT:" + "/".join(source_names[normal]))
for index in (72, 74, 76):
    source_names[index].append("DOWN_RECOVERY:" + "/".join(source_names[index-1]))

payload = (args.package/"payload/bag1_alt.bin").read_bytes()
manifest = tomllib.loads((args.package/"manifest.toml").read_text(encoding="utf-8-sig"))
hashes = [overlay.get("sha256") for overlay in manifest.get("overlay", [])
          if overlay.get("file") == "payload/bag1_alt.bin"]
if sha(payload) not in hashes:
    raise ValueError("Installed payload does not match its manifest")
header = (root/"mods-src/bag2jp.feature.bag1-content/bag2jp_bag1_alt_index.h").read_text()
index_rows = re.findall(r"\{(\d+), \d+, \d+, 0x[0-9A-F]+u, \d+u, 0x([0-9A-F]+)u, (\d+)u\}", header)
archives = {}
for entry, offset, size in index_rows:
    offset = int(offset, 16) - (224035-179)*2048
    size = int(size)
    if offset < 0 or offset+size > len(payload):
        raise ValueError("Alternate entry outside installed payload")
    archives[int(entry)] = dfs_entries(payload[offset:offset+size])
model_ids = (95, 96, 167, 168)
models = {entry: anim_list(archives[entry][1]) for entry in model_ids}
if any(len(model) != 101 for model in models.values()):
    raise ValueError("Unexpected installed model animation count")
expected_bytes, expected_map = build(source)
expected = anim_list(expected_bytes)
converted = {False: [], True: []}
for attack in converted:
    converted[attack] = [rebase_events(fix_events(anim, attack=attack), 0x1000,
                                      b1_cue_base(0), 0x100) for anim in source]
slots = []
for slot, animation in enumerate(models[95]):
    matches = [index for index, original in enumerate(converted[slot == 74])
               if (adapt_events(original, policy_roles[slot]) if slot in policy_roles else original) == animation]
    row = {"slot": slot, "bag1_indices": matches,
           "bag1_labels": [name for i in matches for name in source_names[i]],
           "all_four_identical": all(model[slot] == animation for model in models.values()),
           "matches_converter": animation == expected[slot],
           "sha256": sha(animation), **metadata(animation)}
    slots.append(row)
if not all(row["all_four_identical"] and row["matches_converter"] for row in slots):
    raise ValueError("Installed models differ from each other or current conversion output")

fever_solo = anim_list(archives[22][0])
fever_duet = anim_list(archives[40][0])
archive_names = json.loads((root/"assets/archive/_container.json").read_text())["entries"]
stock_solo = anim_list((root/"assets/archive"/archive_names[22]["name"]/"000.bin").read_bytes())
stock_duet = anim_list((root/"assets/archive"/archive_names[40]["name"]/"000.bin").read_bytes())
solo_expected = [mute_voices(fix_events(source[i]), 0, 0x2000) for i in (82,83,82)]
solo_expected += [EMPTY] * (len(stock_solo)-3)
duet_expected = [mute_voices(anim, 0x1000, 0x1100) if len(anim)>8 else anim for anim in stock_duet]
if fever_solo != solo_expected or fever_duet != duet_expected:
    raise ValueError("Installed fever content differs from the conversion policy")
fever_rows = []
for index, anim in enumerate(fever_solo):
    matches = [i for i, original in enumerate(source)
               if mute_voices(fix_events(original), 0, 0x2000) == anim]
    fever_rows.append({"index": index, "bag1_indices": matches,
                       "bag1_labels": [name for i in matches for name in source_names[i]],
                       **metadata(anim)})

aliases = {"ATTACK": "ATTACK1", "INDIVIDUAL1": "INDIVIDUAL", "INDIVIDUAL2": "INDIVIDUAL"}
stock_model = anim_list((root/"assets/archive/characters/heat/model_a_p1/001.bin").read_bytes())
view_rows = []
for label in b2labels:
    row = dict(label)
    slot = resolve(b2exe, 2, label["request"])
    row["slot"] = slot
    name = label["name"]
    if slot is None:
        raise ValueError("Invalid request in BAG2 Dance View")
    row.update({k:v for k,v in (fever_rows[slot-101] if slot >= 101 else slots[slot]).items() if k != "index"})
    row["slot"] = slot
    actual = row["bag1_labels"]
    if name.startswith("FEVER"):
        row["status"] = "duplicate" if name == "FEVER3" else "unavailable" if row["empty"] else "equivalent"
    elif row["empty"]:
        row["status"] = "unavailable"
    elif name == "NEUTRAL" or name in ("WAIT","DODGE","TIRED","WIN1","WIN2","WIN3","LOSE1","LOSE2"):
        row["status"] = "equivalent" if name in actual else "wrong_role"
    elif name in aliases:
        row["status"] = "equivalent" if aliases[name] in actual else "wrong_role"
    elif name.startswith("SOLO_"):
        family = name.rsplit("_",1)[0] + "_"
        row["status"] = "equivalent" if name in actual else "adapted_variant" if any(x.startswith(family) for x in actual) else "wrong_duration_family"
    elif name.startswith("DOWN"):
        row["status"] = "equivalent" if name in actual else "wrong_role"
    elif name in ("GUARD","REFLECT","POSE1","POSE2"):
        row["status"] = "wrong_role" if any(x.startswith(("ATTACK","WALK","HIT")) for x in actual) else "adaptation"
    elif name == "LOSE3":
        row["status"] = "adapted_variant"
    elif name.startswith("MISS"):
        row["status"] = "wrong_role" if "TIRED" in actual else "adaptation"
    else:
        row["status"] = "adapted_grid"
    if slot in policy_roles:
        row["adaptation"] = policy_roles[slot]
        if policy_roles[slot]["classification"] == "adaptation": row["status"] = "documented_adaptation"
    stock = stock_model[slot] if slot < 101 else stock_solo[slot-101]
    row["stock"] = metadata(stock)
    if row["empty"] and stock == EMPTY:
        row["status"] = "stock_unused"
    view_rows.append(row)

dance_rows = []
row_lengths = (4,6,6,6,8,6,4,2)
active_starts = (0,0,0,0,0,2,4,6)
request = 1
for level, (length, active_start) in enumerate(zip(row_lengths, active_starts)):
    for column in range(length):
        bar = active_start+column
        slot = resolve(b2exe, 2, request)
        source_bar = column+8-length
        source_level = min(level, source_bar)
        b1_request = 36-max(source_level,1) if source_bar == 7 else source_bar*(source_bar+1)//2+source_bar-source_level+1
        original = resolve(b1exe, 1, b1_request)
        matches = slots[slot]["bag1_indices"]
        dance_rows.append({"level": level, "bar": bar, "request": request, "slot": slot,
                           "source_cell": [source_bar,source_level], "source_request": b1_request,
                           "source_index": original, "matches_independent_grid": original in matches})
        request += 1
alternate_rows = []
for normal, alternate, previous, _ in b2alternates:
    normal_source = slots[normal]["bag1_indices"]
    alternate_source = slots[alternate]["bag1_indices"]
    previous_source = slots[previous]["bag1_indices"]
    allowed = [list(record) for record in b1alternates
               if record[0] in normal_source and record[1] in alternate_source
               and (record[2] in previous_source or record[3] in previous_source)]
    predicted = set()
    for original in normal_source:
        for predecessor in previous_source:
            chosen = original
            for original_from, original_to, prior_a, prior_b in b1alternates:
                if original == original_from and predecessor in (prior_a, prior_b):
                    chosen = original_to
            predicted.add(chosen)
    target_cell = next(row["source_cell"] for row in dance_rows if row["slot"] == normal)
    previous_cell = next(row["source_cell"] for row in dance_rows if row["slot"] == previous)
    adjacent = target_cell[0] == previous_cell[0]+1 and target_cell[1] in (previous_cell[1],previous_cell[1]+1)
    alternate_rows.append({"slot": alternate, "normal_slot": normal, "previous_slot": previous,
                           "source": alternate_source, "normal_source": normal_source,
                           "previous_source": previous_source,
                           "original_transition_matches": bool(allowed),
                           "predicted_native_indices": sorted(predicted),
                           "matches_original_dispatch": bool(set(alternate_source) & predicted),
                           "adjacent_source_cells": adjacent,
                           "target_source_cell": target_cell,
                           "previous_source_cell": previous_cell,
                           "same_as_normal": models[95][normal] == models[95][alternate],
                           "original_table_records": allowed})
source_inventory = [{"index":i,"labels":source_names[i],"sha256":sha(anim),
                     "installed_model_slots":[row["slot"] for row in slots if i in row["bag1_indices"]],
                     "installed_solo_slots":[row["index"]+101 for row in fever_rows if i in row["bag1_indices"]],
                     **metadata(anim)} for i,anim in enumerate(source)]
used = {i for row in slots+fever_rows for i in row["bag1_indices"]}
source_variants = []
for folder in ("PLAYER2_P_HEATA2","PLAYER2_P_HEATB2","PLAYER4_P_HEATA4","PLAYER4_P_HEATB4"):
    data = (root/"_work/bag1_assets/heat"/folder/"001.bin").read_bytes()
    source_variants.append({"folder":folder,"sha256":sha(data),
                            "equals_primary":data == (root/"_work/bag1_assets/heat/PLAYER2_P_HEATA2/001.bin").read_bytes()})
regional = []
if args.bag1_japan:
    from iso_extract import Disc
    disc = Disc(args.bag1_japan)
    try:
        for filename,lba,size in disc.walk():
            if "HEAT" not in filename or not filename.startswith(("PLAYER2/","PLAYER4/")):
                continue
            data = dfs_entries(disc.read(lba,size))[1]
            folder = filename.replace("/","_").replace(".DFS","")
            usa = (root/"_work/bag1_assets/heat"/folder/"001.bin").read_bytes()
            regional.append({"file":filename,"sha256":sha(data),"animation_count":len(anim_list(data)),
                             "equals_usa":data == usa})
        if len(regional) != 4:
            raise ValueError("Expected four Japanese Heat model files")
    finally:
        disc.f.close()
visible_model_slots = {row["slot"] for row in view_rows if row["slot"] < 101}
alternate_slots = {row["slot"] for row in alternate_rows}
internal = []
for row in slots:
    if row["slot"] not in visible_model_slots | alternate_slots:
        item = dict(row)
        item["stock"] = metadata(stock_model[row["slot"]])
        item["purpose"] = "special_recovery_idle_fallback" if row["slot"] in (69,70) else "reserved_empty" if row["slot"] == 1 else "knockdown_recovery_or_extra_reaction"
        internal.append(item)

motion_hashes = {row["motion_sha256"] for row in slots+fever_rows if not row["empty"]}
unreferenced_motions = [row["index"] for row in source_inventory if row["motion_sha256"] not in motion_hashes]
report = {"schema":2, "payload_sha256":sha(payload),
          "coverage":{"bag1_source_animations":len(source), "model_slots":len(slots),
                      "model_variants":len(models), "slot_checks":len(slots)*len(models),
                      "dance_view_entries":len(view_rows), "dance_cells":len(dance_rows),
                      "alternate_transitions":len(alternate_rows),
                      "solo_fever_slots":len(fever_solo),"duet_fever_slots":len(fever_duet),
                      "unused_source_indices":sorted(set(range(len(source)))-used),
                      "unreferenced_motion_indices":unreferenced_motions},
          "status_counts":dict(Counter(row["status"] for row in view_rows)),
          "source_inventory":source_inventory,
          "source_variants":source_variants, "regional":regional,
          "input_sha256":{"bag1_exe":sha(b1exe),"bag2_exe":sha(b2exe),"bag1_view":sha(b1view),
                          "bag2_view":sha(b2view)},
          "internal_slots":internal,
          "bag1_view":b1labels, "bag2_view":view_rows, "slots":slots,
          "dance_grid":dance_rows, "alternate_transitions":alternate_rows,
          "fever_solo":fever_rows,
          "fever_duet":{"source":"BAG2 stock with muted Heat voice cues", "matches":True,
                        "slot_count":len(fever_duet),
                        "entries":[{"slot":126+i,"sha256":sha(anim),**metadata(anim)}
                                   for i,anim in enumerate(fever_duet)]}}
if args.output:
    args.output.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8",newline="\n")
print(json.dumps({"coverage":report["coverage"],"status_counts":report["status_counts"],
                  "dance_grid_matches":sum(row["matches_independent_grid"] for row in dance_rows),
                  "original_alt_transition_matches":sum(row["matches_original_dispatch"] for row in alternate_rows)}))
print("Role mismatches:", ", ".join(row["name"] for row in view_rows if row["status"] == "wrong_role"))
print("Regional source files compared:", len(regional))
print("Internal slots accounted for:", len(internal))
print("Payload unchanged:", sha(payload))
