"""Shared character-profile validation and motion-reference cache (no runtime writes)."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import tempfile
import datetime
import sys
from collections.abc import Iterable, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.workflow.project_config import (
    ConfigError, ProjectConfig, assert_write_target, export_config, load_config, require_paths,
)

def file_sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()

def _runtime_config(project: Path | str, config: ProjectConfig | None = None) -> ProjectConfig:
    config = config if config is not None else load_config(repo_root=project)
    if config.repo_root != Path(project).resolve():
        raise ConfigError("Runtime configuration belongs to a different project")
    runtime, = require_paths(config, ("inputs.bag1_reference_runtime",))
    if not runtime.is_file():
        raise ConfigError(f"Missing reference runtime: {runtime}")
    return config


WORK_ROOT_MEMBER = "_work"  # config-audit: allow declared-location syntax token, resolved via paths.work_root


def _operator_input(project: Path, config: ProjectConfig, declared: str) -> Path:
    """Resolve an explicit operator path; absolute locations stay as given.

    Initialization receives locations from the command line, including a reference
    runtime outside the project. Relative ones follow the configured work root.
    """
    path = Path(declared)
    if path.is_absolute():
        return path.resolve()
    return resolve_declared_input(project, config, declared)


def declared_location(project: Path | str, config: ProjectConfig, path: Path | str) -> str:
    """Inverse of resolve_declared_input: ``_work/...`` inside the work root, else project-relative."""
    resolved = Path(path).resolve()
    bases = []
    if config.values.get("paths.work_root") is not None:
        work, = require_paths(config, ("paths.work_root",))
        bases.append((work.resolve(), (WORK_ROOT_MEMBER,)))
    bases.append((Path(project).resolve(), ()))
    for base, prefix in bases:
        try:
            return Path(*prefix, resolved.relative_to(base)).as_posix()
        except ValueError:
            continue
    raise ValueError(f"Location is outside the project and its work root: {resolved}")


def resolve_declared_input(project: Path, config: ProjectConfig, declared: str) -> Path:
    """Resolve a profile-declared location; the host work root comes from configuration.

    A leading ``_work`` component (compared with the platform's case rules) names the
    configured work root; other declared locations stay project-relative. Absolute
    paths, traversal and physically escaping links are rejected so a profile cannot
    silently select bytes outside the project or its work root.
    """
    if not isinstance(declared, str) or not declared.strip():
        raise ValueError("Declared input must be a nonempty relative path")
    path = Path(declared)
    if path.is_absolute() or path.anchor:
        raise ValueError(f"Declared input must be project-relative: {declared}")
    for part in path.parts:
        # Windows also strips trailing spaces/dots, so alias forms must not slip through.
        if part.rstrip(" .") in ("", ".", ".."):
            raise ValueError(f"Declared input must not escape the project: {declared}")
    if path.parts and os.path.normcase(path.parts[0]) == os.path.normcase(WORK_ROOT_MEMBER):
        work, = require_paths(config, ("paths.work_root",))
        base, candidate = work, work.joinpath(*path.parts[1:])
    else:
        base, candidate = Path(project), Path(project) / path
    resolved, resolved_base = candidate.resolve(), Path(base).resolve()
    try:
        resolved.relative_to(resolved_base)
    except ValueError:
        raise ValueError(f"Declared input must not escape the project: {declared}") from None
    return resolved


def load_profile(path: Path | str, project: Path | str, *,
                 config: ProjectConfig | None = None) -> tuple[dict, list[str]]:
    """Validate a profile using central runtime authority; return data and pending IDs.

    The historical reference_runtime field is preserved as data, never read as a path.
    """
    config = _runtime_config(project, config)
    path, project = Path(path), Path(project)
    profile = json.loads(path.read_text(encoding="utf-8"))
    schema = profile.get("schema")
    if schema not in (1, 2) or not re.fullmatch(r"[a-z0-9-]+", profile.get("character", "")):
        raise ValueError("Profile requires schema 1 and a character slug")
    required = ("source_animation_list", "game_catalog")
    if schema == 2:
        required += ("display_name", "capabilities", "assets")
    for key in required:
        if not isinstance(profile.get(key), str if key not in ("assets","capabilities") else dict) or (key not in ("assets", "capabilities") and not profile[key]):
            raise ValueError(f"Missing profile field: {key}")
    stages = ("inventory", "contract", "verified") if schema == 1 else ("inventory", "contract", "candidate", "verified")
    if profile.get("stage") not in stages:
        raise ValueError("Invalid workflow stage")
    for key in ("source_animation_list", "game_catalog"):
        if not resolve_declared_input(project, config, profile[key]).is_file():
            raise ValueError(f"Missing input: {key}")
    if schema == 2:
        if not isinstance(profile.get("capabilities"), dict):
            raise ValueError("Missing capability map")
        for asset in profile["assets"].values():
            if not isinstance(asset, dict) or not asset.get("file") or not asset.get("sha256"):
                raise ValueError("Asset records require file and sha256")
            asset_path = resolve_declared_input(project, config, asset["file"])
            if not asset_path.is_file():
                raise ValueError(f"Missing asset input: {asset['file']}")
            if file_sha(asset_path) != asset["sha256"]:
                raise ValueError(f"Asset input changed: {asset['file']}")
    catalog = json.loads(resolve_declared_input(project, config, profile["game_catalog"]).read_text(encoding="utf-8"))
    if catalog.get("schema") != 1 or not catalog.get("games"):
        raise ValueError("Invalid shared game catalog")
    for game in catalog["games"].values():
        if not game.get("inputs"):
            raise ValueError("Game catalog requires hashed input evidence")
        for item in game["inputs"]:
            if file_sha(resolve_declared_input(project, config, item["file"])) != item["sha256"]:
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
            evidence_path = resolve_declared_input(project, config, evidence.get("file", ""))
            if not evidence_path.is_file() or file_sha(evidence_path) != evidence.get("sha256"):
                raise ValueError("Verified exception requires unchanged evidence")
        else:
            raise ValueError("Exception status must be pending or verified")
    evidence = profile.get("validation_evidence", [])
    if profile["stage"] == "verified":
        if not evidence or pending:
            raise ValueError("Verified stage needs gameplay evidence and resolved exceptions")
        for item in evidence:
            if file_sha(resolve_declared_input(project, config, item["file"])) != item["sha256"]:
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

def _workspace_config(project: Path | str, config: ProjectConfig | None = None) -> ProjectConfig:
    config = config if config is not None else load_config(repo_root=project)
    if config.repo_root != Path(project).resolve():
        raise ConfigError("Workspace configuration belongs to a different project")
    require_paths(config, ("paths.work_root", "paths.stable_install"))
    return config


def _workspace_file(config: ProjectConfig, character: str, *parts: str,
                    protected_inputs: Iterable[Path] = ()) -> Path:
    if not isinstance(character, str) or not re.fullmatch(r"[a-z0-9-]+", character):
        raise ConfigError("Character must be a slug")
    work, = require_paths(config, ("paths.work_root",))
    path = assert_write_target(config, work / "character-import" / character / Path(*parts), role="work")
    if path.exists() and not path.is_file():
        raise ConfigError(f"Expected a workspace file: {path}")
    protected = [Path(p).resolve() for p in protected_inputs]
    protected += [Path(p).resolve() for p in config.input_files.values() if p]
    if path in protected:
        raise ConfigError(f"Workspace output would overwrite an input: {path}")
    return path


def _workspace_inputs(profile_path: Path | str, project: Path | str, profile: dict,
                      config: ProjectConfig) -> tuple[Path, ...]:
    project = Path(project)
    inputs = [Path(profile_path)]
    inputs += [resolve_declared_input(project, config, profile[key]) for key in ("source_animation_list", "game_catalog")]
    inputs += list(require_paths(config, ("inputs.bag1_reference_runtime",)))
    inputs += [resolve_declared_input(project, config, item["file"]) for item in profile.get("assets", {}).values()]
    catalog = json.loads(resolve_declared_input(project, config, profile["game_catalog"]).read_text(encoding="utf-8"))
    inputs += [resolve_declared_input(project, config, item["file"]) for game in catalog["games"].values() for item in game["inputs"]]
    inputs += [resolve_declared_input(project, config, item["evidence"].get("file", "")) for item in profile.get("exceptions", [])
               if item.get("status") == "verified"]
    inputs += [resolve_declared_input(project, config, item.get("file", "")) for item in profile.get("validation_evidence", [])]
    return tuple(inputs)

def _atomic_write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n",
                                         dir=path.parent, prefix=path.name+".", suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(json.dumps(value, indent=2, sort_keys=True)+"\n")
        temporary.replace(path)
    except BaseException:
        if temporary is not None and temporary.exists():
            temporary.unlink()
        raise

def _missing_schema2_gaps(profile):
    gaps = []
    if profile.get("target_character_id") is None:
        gaps.append("target_character_id")
    if profile.get("stage") not in ("candidate", "verified"):
        gaps.append("contract_not_approved")
    if profile.get("exception_assessment") != "complete":
        gaps.append("exception_assessment")
    if profile.get("pending_exceptions", []):
        gaps.append("pending_exceptions")
    if profile.get("stage") == "verified" and not profile.get("validation_evidence"):
        gaps.append("gameplay_evidence")
    return gaps

def acceptance_cases(profile):
    capabilities = profile.get("capabilities", {})
    cases = [{"id":"inventory-validation","category":"inventory","required":True},
             {"id":"model-sides-costumes","category":"model","required":True},
             {"id":"game-flow","category":"gameplay","required":True},
             {"id":"song-end","category":"audio","required":True},
             {"id":"return-to-selection","category":"gameplay","required":True}]
    if capabilities.get("costumes"):
        cases.append({"id":"costume-selection","category":"ui","required":True})
    if capabilities.get("versions"):
        cases.append({"id":"mixed-version","category":"online","required":capabilities.get("online_content",False)})
    if capabilities.get("fever"):
        cases.extend([{"id":"fever-solo","category":"gameplay","required":True},
                      {"id":"fever-duet","category":"gameplay","required":"duet" in capabilities.get("fever",[])}])
    if capabilities.get("stage"):
        cases.append({"id":"stage-load","category":"stage","required":True})
    if capabilities.get("song"):
        cases.append({"id":"song-end","category":"audio","required":True})
    if capabilities.get("ending"):
        cases.append({"id":"ending-video-credits-return","category":"ending","required":True})
    if capabilities.get("shared_announcer_name"):
        cases.append({"id":"announcer-name","category":"audio","required":True})
    if capabilities.get("online_content"):
        cases.append({"id":"online-content-identity","category":"online","required":True})
    return cases

def character_plan(profile_path: Path | str, project: Path | str, *,
                   config: ProjectConfig | None = None) -> dict:
    """Return capability-driven acceptance requirements for the selected profile."""
    config = _runtime_config(project, config)
    profile, pending = load_profile(profile_path, project, config=config)
    gaps = _missing_schema2_gaps(profile) if profile.get("schema") == 2 else []
    if profile.get("schema") != 2:
        gaps.append("schema_2_required_for_plan")
    if pending:
        gaps.append("pending_exceptions")
    gaps = sorted(set(gaps))
    cases = acceptance_cases(profile) if profile.get("schema") == 2 else []
    return {"schema":1,"character":profile["character"],"display_name":profile.get("display_name",profile["character"]),
            "stage":profile.get("stage"),"pending_exceptions":pending,"gaps":gaps,
            "prepare_ready":not gaps,"acceptance":cases,"next_action":"prepare" if not gaps else "resolve_gaps"}

def write_state(project: Path | str, plan: dict, status: str = "planned", *,
                config: ProjectConfig | None = None, protected_inputs: Iterable[Path] = ()) -> Path:
    """Write host state; callers must supply profile inputs that cannot be overwritten."""
    config = _workspace_config(project, config)
    state = {"schema":1,"character":plan["character"],"display_name":plan["display_name"],
             "stage":plan["stage"],"status":status,"pending_exceptions":plan["pending_exceptions"],
             "gaps":plan["gaps"],"prepare_ready":plan["prepare_ready"],"next_action":plan["next_action"],
             "acceptance_count":len(plan["acceptance"]),"updated_utc":datetime.datetime.now(datetime.timezone.utc).isoformat()}
    state["configuration"] = export_config(config, operation="character-workspace")
    path = _workspace_file(config, plan["character"], "state.json", protected_inputs=protected_inputs)
    _atomic_write_json(path,state)
    return path

def prepare_workspace(profile_path: Path | str, project: Path | str, *,
                      config: ProjectConfig | None = None) -> dict:
    """Create only a candidate manifest, protecting validated inputs and host configuration."""
    config = _workspace_config(project, config)
    config = _runtime_config(project, config)
    profile, pending = load_profile(profile_path, project, config=config)
    plan = character_plan(profile_path, project, config=config)
    if plan["gaps"]:
        raise ValueError("Cannot prepare: "+", ".join(plan["gaps"]))
    inputs = _workspace_inputs(profile_path, project, profile, config)
    path = _workspace_file(config, profile["character"], "candidate", "manifest.json", protected_inputs=inputs)
    manifest = {"schema":1,"character":profile["character"],"status":"candidate_only",
                "profile_sha256":file_sha(profile_path),"assets":profile.get("assets",{}),
                "acceptance":plan["acceptance"],"deployed":False,
                "configuration":export_config(config, operation="character-workspace")}
    _atomic_write_json(path,manifest)
    return {"status":"candidate_created","character":profile["character"],"manifest":str(path),"deployed":False}

def signature(profile_path: Path | str, project: Path | str, *,
              config: ProjectConfig | None = None) -> dict:
    """Return a content-based reference key, independent of runtime location."""
    config = _runtime_config(project, config)
    profile, pending = load_profile(profile_path, project, config=config)
    return _profile_signature(profile, project, config)


def _profile_signature(profile: dict, project: Path | str, config: ProjectConfig) -> dict:
    runtime, = require_paths(config, ("inputs.bag1_reference_runtime",))
    digest, count = motion_fingerprint(resolve_declared_input(Path(project), config, profile["source_animation_list"]))
    return {"schema": 1, "decoder": "metro-motion-prefix-v1", "character": profile["character"],
            "catalog_sha256": file_sha(resolve_declared_input(Path(project), config, profile["game_catalog"])),
            "runtime_sha256": file_sha(runtime),
            "motion_sha256": digest, "animation_count": count}

def record_cache(profile_path: Path | str, project: Path | str, cache_path: Path | str,
                 evidence: Sequence[Path | str], *, config: ProjectConfig | None = None) -> dict:
    """Record reference evidence without replacing any validated/configuration input."""
    config = _runtime_config(project, config)
    profile, _ = load_profile(profile_path, project, config=config)
    key = _profile_signature(profile, project, config)
    if not evidence:
        raise ValueError("A reference cache requires evidence")
    inputs = [path.resolve() for path in _workspace_inputs(profile_path, project, profile, config)]
    inputs += [Path(path).resolve() for path in config.input_files.values() if path]
    inputs += [Path(path).resolve() for path in evidence]
    cache_path = Path(cache_path)
    if cache_path.resolve() in inputs or (cache_path.exists() and any(
            path.exists() and cache_path.samefile(path) for path in inputs)):
        raise ValueError("Cache output cannot overwrite an input")
    if cache_path.exists():
        previous = json.loads(cache_path.read_text(encoding="utf-8"))
        if previous.get("key", {}).get("decoder") != "metro-motion-prefix-v1" or "evidence" not in previous:
            raise ValueError("Refusing to overwrite a non-cache JSON file")
    record = {"key": key, "evidence": [{"file": declared_location(project, config, p), "sha256": file_sha(p)}
                                       for p in evidence]}
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

def check_cache(profile_path: Path | str, project: Path | str, cache_path: Path | str, *,
                config: ProjectConfig | None = None) -> dict:
    """Check content identity and evidence for the configured runtime."""
    config = _runtime_config(project, config)
    expected = signature(profile_path, project, config=config)
    path = Path(cache_path)
    if not path.is_file():
        return {"status": "miss", "reason": "no_record"}
    record = json.loads(path.read_text(encoding="utf-8"))
    if record.get("key") != expected:
        return {"status": "miss", "reason": "inputs_changed"}
    evidence = record.get("evidence", [])
    try:
        files = [resolve_declared_input(Path(project), config, item["file"]) for item in evidence]
    except ValueError:
        return {"status": "miss", "reason": "evidence_changed"}
    if not evidence or any(not path.is_file() or file_sha(path) != item["sha256"]
                           for path, item in zip(files, evidence)):
        return {"status": "miss", "reason": "evidence_changed"}
    return {"status": "hit", "animation_count": expected["animation_count"]}

def init_profile(project, profile_path, character, source_archive, source_list, runtime, catalog, *, config=None):
    """Initialize a profile; declared host locations resolve through configuration."""
    project, profile_path = Path(project), Path(profile_path)
    config = config if config is not None else load_config(repo_root=project)
    if config.repo_root != project.resolve():
        raise ConfigError("Profile configuration belongs to a different project")
    if not re.fullmatch(r"[a-z0-9-]+", character):
        raise ValueError("Character must be a slug")
    declared = {"source_archive": str(source_archive), "source_list": str(source_list),
                "runtime": str(runtime), "catalog": str(catalog)}
    archive_path = _operator_input(project, config, declared["source_archive"])
    source_path = _operator_input(project, config, declared["source_list"])
    runtime_path = _operator_input(project, config, declared["runtime"])
    catalog_path = _operator_input(project, config, declared["catalog"])
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
            item_path = resolve_declared_input(project, config, item["file"])
            if file_sha(item_path) != item["sha256"]:
                raise ValueError("Game catalog input changed")
            if item_path.resolve() in (profile_path.resolve(), source_path.resolve()):
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
    recorded = {key: Path(value).as_posix() for key, value in declared.items()}
    profile = {"schema":1,"character":character,"stage":"inventory",
               "source_animation_list":recorded["source_list"],"game_catalog":recorded["catalog"],
               "reference_runtime":recorded["runtime"],"source_archive_sha256":file_sha(archive_path),
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

def main(argv: Sequence[str] | None = None) -> int:
    """Dispatch profile actions; preflight every workspace output before writes."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("init-profile", "validate-profile", "cache-record", "cache-check",
                                         "plan", "prepare", "status", "acceptance-plan"))
    parser.add_argument("--project", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--local-config", type=Path)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--cache", type=Path)
    parser.add_argument("--evidence", type=Path, action="append", default=[])
    parser.add_argument("--character")
    parser.add_argument("--source-archive", type=Path)
    parser.add_argument("--source-list", type=Path)
    parser.add_argument("--runtime", type=Path)
    parser.add_argument("--catalog", type=Path, default=Path("tools/bag1import/contracts/bag1-usa-bag2jp.roles.json"))
    args = parser.parse_args(argv)
    config = None
    protected_inputs = ()
    try:
        loaded = load_config(repo_root=args.project, local_config=args.local_config)
        # Initialization records its inputs explicitly; other actions also need the runtime.
        config = loaded if args.action == "init-profile" else _runtime_config(args.project, loaded)
    except ConfigError as error:
        parser.error(str(error))
    if args.action in ("plan", "prepare"):
        try:
            config = _workspace_config(args.project, config)
            profile, _ = load_profile(args.profile, args.project, config=config)
            protected_inputs = _workspace_inputs(args.profile, args.project, profile, config)
            state_path = _workspace_file(config, profile["character"], "state.json", protected_inputs=protected_inputs)
            if args.action == "prepare":
                manifest_path = _workspace_file(config, profile["character"], "candidate", "manifest.json", protected_inputs=protected_inputs)
                if state_path == manifest_path:
                    raise ConfigError("Workspace state and manifest must have distinct physical destinations")
        except ConfigError as error:
            parser.error(str(error))
    if args.action == "init-profile":
        if not all((args.character,args.source_archive,args.source_list,args.runtime)):
            parser.error("init-profile needs --character --source-archive --source-list --runtime")
        result = init_profile(args.project,args.profile,args.character,args.source_archive,args.source_list,args.runtime,args.catalog,config=config)
    elif args.action == "validate-profile":
        profile, pending = load_profile(args.profile, args.project, config=config)
        digest, count = motion_fingerprint(resolve_declared_input(args.project, config, profile["source_animation_list"]))
        result = {"status": "valid_profile", "character": profile["character"], "animation_count": count,
                  "stage": profile["stage"], "pending_exceptions": pending,
                  "generation_ready": profile["stage"] == "verified" and not pending}
    elif args.action in ("plan","status","acceptance-plan"):
        plan = character_plan(args.profile, args.project, config=config)
        if args.action == "acceptance-plan":
            result = {"status":"acceptance_plan","character":plan["character"],"cases":plan["acceptance"]}
        else:
            result = {"status":args.action+"_ready","character":plan["character"],"plan":plan}
            if args.action == "plan":
                write_state(args.project, plan, "planned", config=config, protected_inputs=protected_inputs)
    elif args.action == "prepare":
        result = prepare_workspace(args.profile, args.project, config=config)
        plan = character_plan(args.profile, args.project, config=config)
        write_state(args.project, plan, "candidate_created", config=config, protected_inputs=protected_inputs)
    else:
        if args.cache is None:
            parser.error("--cache is required for cache actions")
        result = record_cache(args.profile, args.project, args.cache, args.evidence, config=config) if args.action == "cache-record" else check_cache(args.profile, args.project, args.cache, config=config)
    print(json.dumps(result))
    return 2 if result.get("status") == "miss" else 0

if __name__ == "__main__":
    raise SystemExit(main())
