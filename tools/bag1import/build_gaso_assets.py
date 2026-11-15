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
  - 17: Solo fever choreography (BAG1 Gas-O fever dances, stock Bi-O member 1)

Extraction roots come from the shared host configuration. The profile retains
regional pack directories, shared model directories and announcer source region.

Uses exact documented seams:
  - Models converted via model_bag1_to_bag2.convert()
  - Retargeted body textures via tim_retarget.retarget()
  - Rebased voice bank (0x1800 -> 0x6900) + the BAG1 Gas-O name call as the victory
    name cue 0x1909 (profile "announcer"), fitted to the voice_bank budget by
    vab_budget.fit_voice_budget()
  - VS intro banks with the Bi-O names 0x3090/0x3091 replaced by the BAG1 Gas-O calls
    (stock "versus" kept exact, each bank within its stock body size)
  - DFS containers packed via rebuild_dfs_members.build_container()

Usage:
    py -3.13 tools/bag1import/build_gaso_assets.py [--local-config TOML] [--region usa|jp] [--out-dir DIR]
"""
import argparse
import hashlib
import json
import sys
from collections.abc import Sequence
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/bag1import"))
sys.path.insert(0, str(ROOT))

from tools.workflow.project_config import ConfigError, ProjectConfig, load_config, require_paths

from model_bag1_to_bag2 import convert, check_bag2
from preserve_announcer import append_cue, cue_record, rename_cue, replace_cue
from rebase_cues import rebase_sedt
from rebuild_dfs_members import build_container, read_members
from tim_retarget import retarget, paste_native_glyphs
from patch_gaso_dbi import patch_gaso_dbi
from vab_budget import Vab, fit_voice_budget
from anim_remap_gaso import build_fever
from animlib import anim_list

VOICE_MEMBER = 6
BODY_MEMBERS = (4, 5)


def _guard_output(out_dir: Path, config: ProjectConfig, extraction: Path, names_root: Path,
                  stock_bio: Path, stock_fever: Path, motions: Path) -> None:
    """Rechaza una salida que colapse con entradas, instalación estable o configuración."""
    forbidden = [extraction, names_root, stock_bio, stock_fever, motions.parent,
                 config.values.get("paths.stable_install"),
                 Path(__file__).resolve().parents[2] / "config"]
    out = out_dir.resolve()
    for base in forbidden:
        if base is None:
            continue
        base = base.resolve()
        if out == base or out.is_relative_to(base):
            raise ConfigError(f"Gas-O output collides with a protected location: {out_dir} under {base}")


def region_sources(region: str, *, config: ProjectConfig | None = None,
                   profile: dict | None = None) -> tuple[Path, dict, dict]:
    """Resolve host extraction location; retain regional layout authority in the profile."""
    if region not in ("usa", "jp"):
        raise ConfigError(f"Unsupported Gas-O source region: {region}")
    config = load_config() if config is None else config
    extraction, = require_paths(config, (f"inputs.bag1_{region}_extraction",))
    if not extraction.is_dir():
        raise ConfigError(f"Gas-O {region} extraction root is not a directory: {extraction}")
    if profile is None:
        profile_path, = require_paths(config, ("inputs.gaso_profile",))
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
    layout = profile["source_layout"]
    source = layout["regions"][region]
    models = {costume: layout[costume]["model_directory"] for costume in ("costume_a", "costume_b")}
    return extraction, source["pack_directories"], models


def write_entry(out_dir: Path, name: str, members: list[bytes]) -> None:
    data = build_container(members)
    (out_dir / name).write_bytes(data)
    print(f"Built {name}: {len(data)} bytes, sha {hashlib.sha256(data).hexdigest()[:12]}")


def build_hud_texture(source: bytes, reference: bytes, label: dict) -> bytes:
    """Place stock BAG2 glyphs inside the existing BAG1 name artwork area."""
    glyphs = label['glyphs']
    if ''.join(glyph['character'] for glyph in glyphs) != label['text']:
        raise ValueError('HUD glyph sequence does not match label text')
    target = tuple(label['target_rect'])
    for area in label['source_rect'].values():
        if not (area[0] <= target[0] < target[2] <= area[2]
                and area[1] <= target[1] < target[3] <= area[3]):
            raise ValueError('HUD label must remain inside native name artwork')
    return paste_native_glyphs(retarget(source, reference), [
        ((ROOT / glyph['source']).read_bytes(), tuple(glyph['rect'])) for glyph in glyphs
    ], target, [glyph.get('spacing_after', 0) for glyph in glyphs])


def build(region: str, out_dir: Path, *, config: ProjectConfig | None = None) -> None:
    """Build candidates; host requirements are checked before output creation."""
    config = load_config() if config is None else config
    profile_path, = require_paths(config, ("inputs.gaso_profile",))
    stock_bio, stock_fever = require_paths(config, ("inputs.gaso_stock_bio", "inputs.gaso_stock_fever"))
    motions, = require_paths(config, ("inputs.gaso_motions",))
    if not profile_path.is_file():
        raise ConfigError(f"Gas-O profile is not a file: {profile_path}")
    if not stock_bio.is_dir():
        raise ConfigError(f"Gas-O stock bio dir is not a directory: {stock_bio}")
    if not stock_fever.is_dir():
        raise ConfigError(f"Gas-O stock fever dir is not a directory: {stock_fever}")
    if not motions.is_file():
        raise ConfigError(f"Gas-O motions file is not a file: {motions}")
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    extraction, pack_dirs, model_dirs = region_sources(region, config=config, profile=profile)
    announcer = profile["announcer"]
    names_root, names_dirs, _ = region_sources(announcer["source_region"], config=config, profile=profile)
    _guard_output(out_dir, config, extraction, names_root, stock_bio, stock_fever, motions)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Bi-O reference members:
    # P1: [0] TIM portrait, [1] DBI, [2] TIM body1, [3] TIM body2, [4] SEDT voice, [5] SEDT sfx
    # P2: [0] DBI, [1] TIM body1, [2] TIM body2, [3] SEDT voice, [4] SEDT sfx
    stock_p1, _ = read_members((stock_bio / "pack_a_p1.dfs").read_bytes())
    stock_p2, _ = read_members((stock_bio / "pack_a_p2.dfs").read_bytes())
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
    names = read_members((names_root / names_dirs["costume_a"] / "P_GAS_A1.DFS").read_bytes())[0]
    names = names[announcer["source_member"]]
    merged_voice = rebased_voice
    for target, source in announcer["voice_cues"].items():
        target, source = int(target, 16), int(source, 16)
        # The BAG1 clip takes the stock record (flags, volume, note 60) of the Bi-O call.
        clip = rename_cue(names, source, target, cue_record(bio_voice_ref, target))
        merged_voice = append_cue(merged_voice, clip, target)
    stock_vs = {"p1": bio_sfx_p1, "p2": bio_sfx_p2}
    vs_banks = dict(stock_vs)
    for side, cues in announcer["vs_cues"].items():
        stock_body = Vab(stock_vs[side]).body_bytes()
        for target, source in cues.items():
            vs_banks[side] = replace_cue(vs_banks[side], int(target, 16), names, int(source, 16))
        # Keep the stock "versus" sample exact and the bank within its stock SPU footprint.
        vs_banks[side], vs_units = fit_voice_budget(vs_banks[side], Vab(stock_vs[side]).samples, stock_body)
        print(f"[{region}] VS {side} bank: body {Vab(vs_banks[side]).body_bytes()}/{stock_body}, "
              f"resample {vs_units}/128 semitones")
    budget = profile["voice_bank"]["max_body_bytes"]
    merged_voice, units = fit_voice_budget(merged_voice, [], budget)
    print(f"[{region}] Merged voice bank ready: {len(merged_voice)} bytes, "
          f"body {Vab(merged_voice).body_bytes()}/{budget}, resample {units}/128 semitones")

    for key, entry in (("a_p1", 53), ("a_p2", 54), ("b_p1", 125), ("b_p2", 126)):
        body1 = retarget(packs[key][BODY_MEMBERS[0]], bio_body1_ref)
        # A per-draw runtime override uses this native-size BAG2 label, not the
        # stock Bi-O UV slot (which contains Gas-O body pixels).
        body2 = build_hud_texture(packs[key][BODY_MEMBERS[1]], bio_body2_ref, profile['hud_name'])
        costume, side = key.split("_")
        if side == "p1":
            members = [bio_portrait, gaso_dbi_p1, body1, body2, merged_voice, vs_banks["p1"]]
        else:
            members = [gaso_dbi_p2, body1, body2, merged_voice, vs_banks["p2"]]
        write_entry(out_dir, f"entry_{entry}_pack_{costume}_{side}.dfs", members)

    model_a, _ = read_members((extraction / model_dirs["costume_a"] / "P_GAS_A2.DFS").read_bytes())
    model_b, _ = read_members((extraction / model_dirs["costume_b"] / "P_GAS_A4.DFS").read_bytes())
    converted = {}
    for label, source in (("A", model_a[0]), ("B", model_b[0]), ("accessory", model_a[2])):
        data, stats, _ = convert(source)
        assert check_bag2(data) == 0, f"Model {label} layout check failed"
        print(f"[{region}] Model {label} converted: {len(data)} bytes, stats {stats}")
        converted[label] = data

    motions_data = motions.read_bytes()
    for entry, label, costume, side in ((89, "A", "a", "p1"), (90, "A", "a", "p2"),
                                        (161, "B", "b", "p1"), (162, "B", "b", "p2")):
        write_entry(out_dir, f"entry_{entry}_model_{costume}_{side}.dfs",
                    [converted[label], motions_data, converted["accessory"]])

    # Solo fever: BAG1 Gas-O fever dances; member 1 (choreography data) stays stock.
    stock_fever = [(stock_fever / name).read_bytes() for name in ("000.bin", "001.bin")]
    fever = build_fever(anim_list(model_a[1]), len(anim_list(stock_fever[0])))
    solo_entry = profile["target_entries"]["fever_choreography"][0]
    write_entry(out_dir, f"entry_{solo_entry}_choreography_a.dfs", [fever, stock_fever[1]])
    print(f"All 9 Gas-O {region} candidate DFS containers built in {out_dir}.")


def main(argv: Sequence[str] | None = None) -> None:
    """Select one configuration snapshot for the requested build."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--region", choices=("usa", "jp"), default="usa")
    parser.add_argument("--out-dir", type=Path)
    parser.add_argument("--local-config", type=Path)
    args = parser.parse_args(argv)
    try:
        config = load_config(local_config=args.local_config)
        default_out = config.values[f"paths.gaso_out_{args.region}"]
        build(args.region, args.out_dir or default_out, config=config)
    except ConfigError as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
