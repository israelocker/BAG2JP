"""Build all candidate DFS containers for Gas-O (character ID 9, Bi-O target).

Generates candidate containers for entries:
  - 53: Pack A P1 (Gas-O A1)
  - 54: Pack A P2 (Gas-O B1)
  - 125: Pack B P1 (Gas-O A3)
  - 126: Pack B P2 (Gas-O B3)
  - 89: Model A P1 (Gas-O A2 model + 001.bin + accessory)
  - 90: Model A P2 (Gas-O B2 model + 001.bin + accessory)
  - 161: Model B P1 (Gas-O A4 model + 001.bin + accessory)
  - 162: Model B P2 (Gas-O B4 model + 001.bin + accessory)

Source disc region comes from the profile's source_layout.regions (usa or jp):
its extraction root and pack directories; model directories are shared.

Uses exact documented seams:
  - Models converted via model_bag1_to_bag2.convert()
  - Retargeted body textures via tim_retarget.retarget()
  - Rebased voice bank (0x1800 -> 0x6900) + BAG1 Gas-O announcer name calls renamed to the
    Bi-O name cues (profile "announcer"), fitted to the voice_bank budget by
    vab_budget.fit_voice_budget()
  - DFS containers packed via rebuild_dfs_members.build_container()

Usage:
    py -3.13 tools/bag1import/build_gaso_assets.py [--region usa|jp] [--out-dir DIR]
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/bag1import"))

from model_bag1_to_bag2 import convert, check_bag2
from preserve_announcer import append_cue, cue_record, rename_cue
from rebase_cues import rebase_sedt
from rebuild_dfs_members import build_container, read_members
from tim_retarget import retarget
from patch_gaso_dbi import patch_gaso_dbi
from vab_budget import Vab, fit_voice_budget

PROFILE = ROOT / "tools/bag1import/profiles/gaso.json"
STOCK_BIO_DIR = ROOT / "_work/stage_import/gaso/stock_bio_entries"
MOTIONS = ROOT / "_work/gaso/test_001.bin"
DEFAULT_OUT = {
    "usa": ROOT / "_work/character_import/gaso/candidate",
    "jp": ROOT / "_work/character_import/gaso/candidate-jp",
}
VOICE_MEMBER = 6
BODY_MEMBERS = (4, 5)


def region_sources(region: str) -> tuple[Path, dict, dict]:
    """Extraction root, pack directories and model directories for one disc region."""
    layout = json.loads(PROFILE.read_text(encoding="utf-8"))["source_layout"]
    source = layout["regions"][region]
    models = {costume: layout[costume]["model_directory"] for costume in ("costume_a", "costume_b")}
    return ROOT / source["extraction"], source["pack_directories"], models


def write_entry(out_dir: Path, name: str, members: list[bytes]) -> None:
    data = build_container(members)
    (out_dir / name).write_bytes(data)
    print(f"Built {name}: {len(data)} bytes, sha {hashlib.sha256(data).hexdigest()[:12]}")


def build(region: str, out_dir: Path) -> None:
    extraction, pack_dirs, model_dirs = region_sources(region)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Bi-O reference members:
    # P1: [0] TIM portrait, [1] DBI, [2] TIM body1, [3] TIM body2, [4] SEDT voice, [5] SEDT sfx
    # P2: [0] DBI, [1] TIM body1, [2] TIM body2, [3] SEDT voice, [4] SEDT sfx
    stock_p1, _ = read_members((STOCK_BIO_DIR / "pack_a_p1.dfs").read_bytes())
    stock_p2, _ = read_members((STOCK_BIO_DIR / "pack_a_p2.dfs").read_bytes())
    bio_portrait, bio_dbi_p1, bio_body1_ref, bio_body2_ref, bio_voice_ref, bio_sfx_p1 = stock_p1[:6]
    bio_dbi_p2, bio_sfx_p2 = stock_p2[0], stock_p2[4]
    gaso_dbi_p1 = patch_gaso_dbi(bio_dbi_p1)
    gaso_dbi_p2 = patch_gaso_dbi(bio_dbi_p2)

    def pack(costume: str, name: str) -> list[bytes]:
        return read_members((extraction / pack_dirs[costume] / name).read_bytes())[0]

    packs = {
        "a_p1": pack("costume_a", "P_GAS_A1.DFS"), "a_p2": pack("costume_a", "P_GAS_B1.DFS"),
        "b_p1": pack("costume_b", "P_GAS_A3.DFS"), "b_p2": pack("costume_b", "P_GAS_B3.DFS"),
    }

    rebased_voice, moved = rebase_sedt(packs["a_p1"][VOICE_MEMBER], 0x1800, 0x6900)
    assert moved == 11, f"Expected 11 cues rebased, got {moved}"
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    announcer = profile["announcer"]
    names_root, names_dirs, _ = region_sources(announcer["source_region"])
    names = read_members((names_root / names_dirs["costume_a"] / "P_GAS_A1.DFS").read_bytes())[0]
    names = names[announcer["source_member"]]
    merged_voice = rebased_voice
    for target, source in announcer["cue_map"].items():
        target, source = int(target, 16), int(source, 16)
        # The BAG1 clip takes the stock record (flags, volume, note 60) of the Bi-O call.
        clip = rename_cue(names, source, target, cue_record(bio_voice_ref, target))
        merged_voice = append_cue(merged_voice, clip, target)
    budget = profile["voice_bank"]["max_body_bytes"]
    merged_voice, units = fit_voice_budget(merged_voice, [], budget)
    print(f"[{region}] Merged voice bank ready: {len(merged_voice)} bytes, "
          f"body {Vab(merged_voice).body_bytes()}/{budget}, resample {units}/128 semitones")

    for key, entry in (("a_p1", 53), ("a_p2", 54), ("b_p1", 125), ("b_p2", 126)):
        body1 = retarget(packs[key][BODY_MEMBERS[0]], bio_body1_ref)
        body2 = retarget(packs[key][BODY_MEMBERS[1]], bio_body2_ref)
        costume, side = key.split("_")
        if side == "p1":
            members = [bio_portrait, gaso_dbi_p1, body1, body2, merged_voice, bio_sfx_p1]
        else:
            members = [gaso_dbi_p2, body1, body2, merged_voice, bio_sfx_p2]
        write_entry(out_dir, f"entry_{entry}_pack_{costume}_{side}.dfs", members)

    model_a, _ = read_members((extraction / model_dirs["costume_a"] / "P_GAS_A2.DFS").read_bytes())
    model_b, _ = read_members((extraction / model_dirs["costume_b"] / "P_GAS_A4.DFS").read_bytes())
    converted = {}
    for label, source in (("A", model_a[0]), ("B", model_b[0]), ("accessory", model_a[2])):
        data, stats, _ = convert(source)
        assert check_bag2(data) == 0, f"Model {label} layout check failed"
        print(f"[{region}] Model {label} converted: {len(data)} bytes, stats {stats}")
        converted[label] = data

    motions = MOTIONS.read_bytes()
    for entry, label, costume, side in ((89, "A", "a", "p1"), (90, "A", "a", "p2"),
                                        (161, "B", "b", "p1"), (162, "B", "b", "p2")):
        write_entry(out_dir, f"entry_{entry}_model_{costume}_{side}.dfs",
                    [converted[label], motions, converted["accessory"]])
    print(f"All 8 Gas-O {region} candidate DFS containers built in {out_dir}.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--region", choices=("usa", "jp"), default="usa")
    parser.add_argument("--out-dir", type=Path)
    args = parser.parse_args()
    build(args.region, args.out_dir or DEFAULT_OUT[args.region])


if __name__ == "__main__":
    main()
