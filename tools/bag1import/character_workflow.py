"""Shared character-profile validation and motion-reference cache (no runtime writes)."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import tempfile

def file_sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()

def load_profile(path, project):
    path, project = Path(path), Path(project)
    profile = json.loads(path.read_text(encoding="utf-8"))
    if profile.get("schema") != 1 or not re.fullmatch(r"[a-z0-9-]+", profile.get("character", "")):
        raise ValueError("Profile requires schema 1 and a character slug")
    for key in ("source_animation_list", "game_catalog", "reference_runtime"):
        if not isinstance(profile.get(key), str) or not profile[key]:
            raise ValueError(f"Missing profile field: {key}")
    if profile.get("stage") not in ("inventory", "contract", "verified"):
        raise ValueError("Invalid workflow stage")
    for key in ("source_animation_list", "game_catalog", "reference_runtime"):
        if not (project / profile[key]).is_file():
            raise ValueError(f"Missing input: {key}")
    catalog = json.loads((project / profile["game_catalog"]).read_text(encoding="utf-8"))
    if catalog.get("schema") != 1 or not catalog.get("games"):
        raise ValueError("Invalid shared game catalog")
    for game in catalog["games"].values():
        if not game.get("inputs"):
            raise ValueError("Game catalog requires hashed input evidence")
        for item in game["inputs"]:
            if file_sha(project / item["file"]) != item["sha256"]:
                raise ValueError("Game catalog input changed; re-verify base tables")
    pending = []
    ids = set()
    for exception in profile.get("exceptions", []):
        if exception.get("id") in ids or not exception.get("id"):
            raise ValueError("Exception IDs must be present and unique")
        ids.add(exception["id"])
        if exception.get("character") != profile["character"] or not exception.get("reason"):
            raise ValueError("Exception needs a narrow character scope and a reason")
        if exception.get("status") == "pending":
            pending.append(exception["id"])
        elif exception.get("status") == "verified":
            evidence = exception.get("evidence", {})
            evidence_path = project / evidence.get("file", "")
            if not evidence_path.is_file() or file_sha(evidence_path) != evidence.get("sha256"):
                raise ValueError("Verified exception requires unchanged evidence")
        else:
            raise ValueError("Exception status must be pending or verified")
    evidence = profile.get("validation_evidence", [])
    if profile["stage"] == "verified":
        if not evidence or pending:
            raise ValueError("Verified stage needs gameplay evidence and resolved exceptions")
        for item in evidence:
            if file_sha(project / item["file"]) != item["sha256"]:
                raise ValueError("Gameplay evidence changed")
    return profile, pending

def motion_fingerprint(path):
    """Hash motion prefix only, excluding animation info/events, with strict list bounds."""
    return motion_fingerprint_data(Path(path).read_bytes())

def motion_fingerprint_data(data):
    offset, hashes, terminated = 0, [], False
    while offset + 4 <= len(data):
        size = struct.unpack_from("<I", data, offset)[0]
        offset += 4
        if size == 0:
            if any(data[offset:]):
                raise ValueError("Nonzero data after animation-list terminator")
            terminated = True
            break
        if size > len(data) - offset:
            raise ValueError("Truncated animation")
        anim = data[offset:offset+size]
        offset += size
        if anim == bytes(4):
            hashes.append(None)
            continue
        if len(anim) < 32:
            raise ValueError("Animation header is truncated")
        info_base = struct.unpack_from("<I", anim, 0)[0]
        if info_base < 4 or info_base + 4 > len(anim):
            raise ValueError("Invalid animation info base")
        info_offset = info_base + struct.unpack_from("<I", anim, info_base)[0]
        if not info_base + 4 <= info_offset <= len(anim)-4:
            raise ValueError("Invalid animation info offset")
        hashes.append(hashlib.sha256(anim[:info_offset]).hexdigest())
    if not terminated or not hashes:
        raise ValueError("Animation list requires entries and a terminator")
    digest = hashlib.sha256(json.dumps(hashes, separators=(",", ":")).encode()).hexdigest()
    return digest, len(hashes)

def signature(profile_path, project):
    profile, pending = load_profile(profile_path, project)
    digest, count = motion_fingerprint(Path(project) / profile["source_animation_list"])
    return {"schema": 1, "decoder": "metro-motion-prefix-v1", "character": profile["character"],
            "profile_sha256": file_sha(profile_path),
            "catalog_sha256": file_sha(Path(project) / profile["game_catalog"]),
            "runtime_sha256": file_sha(Path(project) / profile["reference_runtime"]),
            "motion_sha256": digest, "animation_count": count}

def record_cache(profile_path, project, cache_path, evidence):
    key = signature(profile_path, project)
    if not evidence:
        raise ValueError("A reference cache requires evidence")
    inputs = [Path(profile_path).resolve(),
              (Path(project)/load_profile(profile_path, project)[0]["source_animation_list"]).resolve()]
    profile = load_profile(profile_path, project)[0]
    inputs += [(Path(project)/profile[k]).resolve() for k in ("game_catalog","reference_runtime")]
    catalog = json.loads((Path(project)/profile["game_catalog"]).read_text(encoding="utf-8"))
    inputs += [(Path(project)/item["file"]).resolve()
               for game in catalog["games"].values() for item in game["inputs"]]
    inputs += [(Path(project)/exception["evidence"]["file"]).resolve()
               for exception in profile.get("exceptions", []) if exception.get("status") == "verified"]
    inputs += [(Path(project)/item["file"]).resolve() for item in profile.get("validation_evidence", [])]
    inputs += [Path(path).resolve() for path in evidence]
    cache_path = Path(cache_path)
    if cache_path.resolve() in inputs:
        raise ValueError("Cache output cannot overwrite an input")
    if cache_path.exists():
        previous = json.loads(cache_path.read_text(encoding="utf-8"))
        if previous.get("key", {}).get("decoder") != "metro-motion-prefix-v1" or "evidence" not in previous:
            raise ValueError("Refusing to overwrite a non-cache JSON file")
    record = {"key": key, "evidence": [{"file": str(Path(p).resolve()), "sha256": file_sha(p)} for p in evidence]}
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n",
                                         dir=cache_path.parent, prefix=cache_path.name+".", suffix=".tmp",
                                         delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(json.dumps(record, indent=2)+"\n")
        temporary.replace(cache_path)
    except BaseException:
        if temporary is not None and temporary.exists():
            temporary.unlink()
        raise
    return {"status": "recorded", **key}

def check_cache(profile_path, project, cache_path):
    expected = signature(profile_path, project)
    path = Path(cache_path)
    if not path.is_file():
        return {"status": "miss", "reason": "no_record"}
    record = json.loads(path.read_text(encoding="utf-8"))
    if record.get("key") != expected:
        return {"status": "miss", "reason": "inputs_changed"}
    evidence = record.get("evidence", [])
    if not evidence or any(not Path(item["file"]).is_file() or file_sha(item["file"]) != item["sha256"] for item in evidence):
        return {"status": "miss", "reason": "evidence_changed"}
    return {"status": "hit", "animation_count": expected["animation_count"]}

def init_profile(project, profile_path, character, source_archive, source_list, runtime, catalog):
    project, profile_path = Path(project), Path(profile_path)
    if not re.fullmatch(r"[a-z0-9-]+", character):
        raise ValueError("Character must be a slug")
    archive_path, source_path = project/Path(source_archive), project/Path(source_list)
    runtime_path, catalog_path = project/Path(runtime), project/Path(catalog)
    protected = {archive_path.resolve(), runtime_path.resolve(), catalog_path.resolve()}
    if profile_path.resolve() in protected or source_path.resolve() in protected or profile_path.resolve() == source_path.resolve():
        raise ValueError("Outputs cannot replace an input")
    if profile_path.exists():
        raise ValueError("Profile already exists; preserve it")
    if not runtime_path.is_file() or not catalog_path.is_file():
        raise ValueError("Reference runtime and shared catalog must exist")
    catalog_data = json.loads(catalog_path.read_text(encoding="utf-8"))
    if catalog_data.get("schema") != 1 or not catalog_data.get("games"):
        raise ValueError("Invalid game catalog")
    for game in catalog_data["games"].values():
        for item in game["inputs"]:
            if file_sha(project/item["file"]) != item["sha256"]:
                raise ValueError("Game catalog input changed")
            if (project/item["file"]).resolve() in (profile_path.resolve(),source_path.resolve()):
                raise ValueError("Output would replace a catalog input")
    data = archive_path.read_bytes()
    if len(data) < 24 or data[:4] != b"DFS_":
        raise ValueError("Expected an unpacked model DFS archive")
    count = struct.unpack_from("<I", data, 4)[0]
    if count < 2 or 8+8*count > len(data):
        raise ValueError("Invalid DFS member table")
    offset,size = struct.unpack_from("<II", data, 16)
    if offset < 8+8*count or size > len(data)-offset:
        raise ValueError("Invalid DFS animation member")
    animation_data = data[offset:offset+size]
    if source_path.exists() and source_path.read_bytes() != animation_data:
        raise ValueError("Preserve existing source inventory")
    profile = {"schema":1,"character":character,"stage":"inventory",
               "source_animation_list":str(source_list),"game_catalog":str(catalog),
               "reference_runtime":str(runtime),"source_archive_sha256":file_sha(archive_path),
               "source_character_id":None,"target_character_id":None,
               "capabilities":{},"exceptions":[],"exception_assessment":"pending","validation_evidence":[]}
    digest,count = motion_fingerprint_data(animation_data)
    source_path.parent.mkdir(parents=True,exist_ok=True)
    if not source_path.exists():
        with source_path.open("xb") as stream:
            stream.write(animation_data)
    profile_path.parent.mkdir(parents=True,exist_ok=True)
    with profile_path.open("x",encoding="utf-8",newline="\n") as stream:
        stream.write(json.dumps(profile,indent=2)+"\n")
    return {"status":"profile_initialized","character":character,"animation_count":count,"generation_ready":False}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("init-profile", "validate-profile", "cache-record", "cache-check"))
    parser.add_argument("--project", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--cache", type=Path)
    parser.add_argument("--evidence", type=Path, action="append", default=[])
    parser.add_argument("--character")
    parser.add_argument("--source-archive", type=Path)
    parser.add_argument("--source-list", type=Path)
    parser.add_argument("--runtime", type=Path)
    parser.add_argument("--catalog", type=Path, default=Path("tools/bag1import/contracts/bag1-usa-bag2jp.roles.json"))
    args = parser.parse_args()
    if args.action == "init-profile":
        if not all((args.character,args.source_archive,args.source_list,args.runtime)):
            parser.error("init-profile needs --character --source-archive --source-list --runtime")
        result = init_profile(args.project,args.profile,args.character,args.source_archive,args.source_list,args.runtime,args.catalog)
    elif args.action == "validate-profile":
        profile, pending = load_profile(args.profile, args.project)
        digest, count = motion_fingerprint(args.project/profile["source_animation_list"])
        result = {"status": "valid_profile", "character": profile["character"], "animation_count": count,
                  "stage": profile["stage"], "pending_exceptions": pending,
                  "generation_ready": profile["stage"] == "verified" and not pending}
    else:
        if args.cache is None:
            parser.error("--cache is required for cache actions")
        result = record_cache(args.profile, args.project, args.cache, args.evidence) if args.action == "cache-record" else check_cache(args.profile, args.project, args.cache)
    print(json.dumps(result))
    return 2 if result.get("status") == "miss" else 0

if __name__ == "__main__":
    raise SystemExit(main())
