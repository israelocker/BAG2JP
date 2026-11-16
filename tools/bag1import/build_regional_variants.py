"""Build Japanese variants of existing BAG1 alternate entries from a recipe profile.

Each profile rule recomputes one member of an accepted (International) candidate
from a regional BAG1 source. The International recomputation must reproduce the
candidate byte for byte before any Japanese file is written, so a rule that does
not describe the real conversion fails instead of producing plausible bytes.
Every source member that differs between regions must be consumed by a rule or
explicitly ignored for that entry class; otherwise the entry is rejected.

Usage:
    py -3.13 tools/bag1import/build_regional_variants.py <profile.json> <new-output-dir>
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools/bag1import"))
sys.path.insert(0, str(REPO))

from iso_extract import Disc  # noqa: E402
from model_bag1_to_bag2 import convert  # noqa: E402
from rebuild_dfs_members import build_container, read_members  # noqa: E402
from tim_retarget import retarget  # noqa: E402
from tools.workflow.project_config import ConfigError, ProjectConfig, load_config, require_paths  # noqa: E402
from character_workflow import resolve_declared_input  # noqa: E402

ARCHIVE = "BUST2.BIN"
SECTOR = 2048
REGIONS = ("international", "japanese")
REGION_ROOT_KEYS = ("inputs.bag1_usa_extraction", "inputs.bag1_jp_extraction")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stock_entries(disc_path: str, entries: list[int]) -> dict[int, bytes]:
    disc = Disc(disc_path)
    lba = next(l for name, l, _ in disc.walk() if Path(name).name == ARCHIVE)
    header = disc.read(lba, 8 + 8 * (max(entries) + 1))
    if header[:4] != b"DF2_":
        raise ValueError("BUST2.BIN does not start with a DF2_ table")
    result = {}
    for entry in entries:
        offset = int.from_bytes(header[8 + entry * 8:12 + entry * 8], "little")
        size = int.from_bytes(header[12 + entry * 8:16 + entry * 8], "little")
        if offset % SECTOR:
            raise ValueError(f"entry {entry}: stock offset is not sector aligned")
        result[entry] = disc.read(lba + offset // SECTOR, size)
    return result


def apply_rules(members: list[bytes], rules: list[dict], source: list[bytes], stock: list[bytes]) -> list[bytes]:
    out = list(members)
    for rule in rules:
        data = source[rule["source"]]
        if rule["op"] == "copy":
            out[rule["member"]] = data
        elif rule["op"] == "retarget":
            out[rule["member"]] = retarget(data, stock[rule["member"]])
        elif rule["op"] == "convert_model":
            out[rule["member"]] = convert(data)[0]
        else:
            raise ValueError(f"unknown rule op {rule['op']}")
    return out


def pack(members: list[bytes], padding: int) -> bytes:
    return build_container(members) + b"\x00" * padding


def profile_locations(profile: dict, config: ProjectConfig) -> dict:
    """Resolve regional locations: source roots from configuration, candidates from the profile."""
    if config.repo_root != REPO.resolve():
        raise ConfigError("Regional profile configuration belongs to a different project")
    usa, jp = require_paths(config, REGION_ROOT_KEYS)
    roots = {"international": usa, "japanese": jp}
    return {"candidate_directory": resolve_declared_input(REPO, config, profile["candidate_directory"]),
            "region_roots": roots}


def _trusted_segment(segment: str) -> str:
    """Validate one audited profile segment; it must stay inside the resolved region root."""
    if not isinstance(segment, str) or not segment.strip():
        raise ValueError(f"Invalid regional segment: {segment!r}")
    path = Path(segment)
    if path.is_absolute() or path.anchor:
        raise ValueError(f"Regional segment must not be absolute: {segment!r}")
    for part in path.parts:
        if part.rstrip(" .") in ("", ".", ".."):
            raise ValueError(f"Regional segment must not escape the root: {segment!r}")
    return segment


def build(profile: dict, out_dir: Path, *, config: ProjectConfig | None = None) -> dict:
    config = config if config is not None else load_config(repo_root=REPO)
    locations = profile_locations(profile, config)
    bag2_disc, = require_paths(config, ("inputs.bag2_disc",))
    stock = stock_entries(str(bag2_disc), [row["entry"] for row in profile["entries"]])
    candidates = locations["candidate_directory"]
    report = {"profile_schema": profile["schema"], "entries": []}
    for row in profile["entries"]:
        name = f"entry_{row['entry']}_chr{row['chr']}_kind{row['kind']}.dfs"
        candidate = (candidates / name).read_bytes()
        members, padding = read_members(candidate)
        stock_members, _ = read_members(stock[row["entry"]])
        sources = {}
        for region in REGIONS:
            spec = profile["regions"][region]
            directory = _trusted_segment(spec["directories"][str(row["number"])])
            source = _trusted_segment(row["source"])
            path = locations["region_roots"][region] / directory / source
            sources[region] = (path, read_members(path.read_bytes())[0])
        usa, jp = sources["international"][1], sources["japanese"][1]
        if len(usa) != len(jp):
            raise ValueError(f"entry {row['entry']}: regional sources have different member counts")
        differing = [i for i, (a, b) in enumerate(zip(usa, jp)) if a != b]
        ignored = profile.get("ignored_source_members", {}).get(row["class"], {})
        consumed = {rule["source"] for rule in row["rules"]}
        unmapped = [i for i in differing if i not in consumed and str(i) not in ignored]
        if unmapped:
            raise ValueError(f"entry {row['entry']}: regional source members {unmapped} have no rule")

        if pack(apply_rules(members, row["rules"], usa, stock_members), padding) != candidate:
            raise ValueError(f"entry {row['entry']}: International recipe does not reproduce the candidate")
        japanese = pack(apply_rules(members, row["rules"], jp, stock_members), padding)
        jp_members, _ = read_members(japanese)
        changed = [i for i, (a, b) in enumerate(zip(members, jp_members)) if a != b]

        for region, data in (("international", candidate), ("japanese", japanese)):
            target = out_dir / region / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        report["entries"].append({
            "entry": row["entry"], "chr": row["chr"], "kind": row["kind"], "file": name,
            "sources": {r: {"path": str(p.relative_to(REPO)) if p.is_relative_to(REPO) else str(p),
                            "sha256": sha256(p.read_bytes())}
                        for r, (p, _) in sources.items()},
            "source_members_differing": differing,
            "international": {"size": len(candidate), "sha256": sha256(candidate)},
            "japanese": {"size": len(japanese), "sha256": sha256(japanese)},
            "output_members_changed": changed,
        })
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("profile", type=Path)
    parser.add_argument("out_dir", type=Path)
    parser.add_argument("--project", type=Path, default=REPO)
    parser.add_argument("--local-config", type=Path)
    args = parser.parse_args()
    config = load_config(repo_root=args.project, local_config=args.local_config)
    args.out_dir.mkdir(parents=True, exist_ok=False)
    report = build(json.loads(args.profile.read_text(encoding="utf-8")), args.out_dir, config=config)
    (args.out_dir / "report.json").write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    for row in report["entries"]:
        print(row["entry"], "changed", row["output_members_changed"],
              "jp", row["japanese"]["size"], "usa", row["international"]["size"])


if __name__ == "__main__":
    main()
