"""Resolve shared host-tool configuration without launching tools or writing files."""

import argparse
from dataclasses import dataclass, replace
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import tomllib
from types import MappingProxyType
from typing import Mapping, Sequence


class ConfigError(ValueError):
    """Invalid host configuration or unresolved required field."""


@dataclass(frozen=True)
class FieldSpec:
    """Schema metadata; values/defaults belong in TOML, not in this registry."""

    kind: str
    unit: str
    local_override: bool
    role: str
    operations: tuple[str, ...] = ()
    expected: int | float | None = None
    maximum: float | None = None


@dataclass(frozen=True)
class ProjectConfig:
    """An immutable resolved host configuration."""

    repo_root: Path
    values: Mapping[str, Path | str | int | float]
    origins: Mapping[str, str]
    input_hashes: Mapping[str, str | None]
    input_files: Mapping[str, str | None]


def _field_registry() -> Mapping[str, FieldSpec]:
    fields = {
        "schema_version": FieldSpec("integer", "schema version", True, "schema", expected=1),
        "repo_root": FieldSpec("path", "native path", False, "derived"),
        "build.jobs": FieldSpec("integer", "compile jobs", False, "policy", expected=2),
        "pins.psxrecomp": FieldSpec("revision", "Git hex prefix", False, "policy"),
        "pins.recomp_ui": FieldSpec("revision", "Git hex prefix", False, "policy"),
        "wsl.distribution": FieldSpec("string", "distribution name", True, "tool"),
    }
    path_roles = {"work_root": "work", "build_root": "build",
                  "experimental_install": "experimental", "stable_install": "stable",
                  "tools_root": "tools", "gaso_out_usa": "output", "gaso_out_jp": "output",
                  "heat_test_workspace": "output", "heat_stage_workspace": "output"}
    for name, role in path_roles.items():
        operations = ("payload-manifest",) if name in ("build_root", "experimental_install") else ()
        fields[f"paths.{name}"] = FieldSpec("path", "native path", True, role, operations)
    for name in ("bag1_usa_disc", "bag1_jp_disc", "bag1_usa_extraction", "bag1_jp_extraction",
                 "bag1_reference_runtime", "gaso_profile", "gaso_stock_bio", "gaso_stock_fever",
                 "gaso_motions", "heat_bag1_members", "bag2_cue"):
        fields[f"inputs.{name}"] = FieldSpec("path", "native path", True, "input")
    for name in ("audio_probe", "python_report", "winshot_root", "build_script",
                  "ffmpeg_review", "ffmpeg_wgc", "ffmpeg_native", "ghidra_launcher",
                  "ghidra_project", "ffprobe_review", "ffmpeg_look", "recording_font",
                  "psx_asset_tools"):
        fields[f"tools.{name}"] = FieldSpec("path", "native path", True, "tool")
    # Host capture budgets; native acceptance thresholds never enter this registry.
    for name in ("max_seconds", "poll_seconds", "alive_check_seconds", "window_wait_seconds",
                 "window_poll_seconds", "ffmpeg_quit_seconds", "ffmpeg_stop_poll_seconds",
                 "process_audio_extra_seconds"):
        fields[f"recording.{name}"] = FieldSpec("number", "seconds", True, "host_budget", maximum=86400.0)
    fields["recording.fps"] = FieldSpec("integer", "capture frames/second", True, "host_budget", maximum=240)
    fields["recording.ffmpeg_extra_seconds"] = FieldSpec("integer", "seconds", True, "host_budget", maximum=86400)
    for name in ("state_timeout_seconds", "helper_timeout_seconds", "startup_timeout_seconds",
                 "finish_timeout_seconds"):
        # One day is a sanity ceiling far below threading.TIMEOUT_MAX on every platform.
        fields[f"harness.{name}"] = FieldSpec("number", "seconds", True, "host_budget", maximum=86400.0)
    fields["harness.key_hold_ms"] = FieldSpec("integer", "milliseconds", False, "policy", expected=100)
    fields["harness.key_gap_ms"] = FieldSpec("integer", "milliseconds", False, "policy", expected=350)
    fields["harness.menu_fade_seconds"] = FieldSpec("number", "seconds", False, "policy", expected=1.3)
    workflow = ("repo_root", "paths.work_root", "paths.stable_install", "paths.build_root",
                "paths.experimental_install", "tools.build_script", "pins.psxrecomp",
                "pins.recomp_ui", "build.jobs", "wsl.distribution")
    report = ("repo_root", "paths.work_root", "paths.experimental_install")
    versus_inspect = ("repo_root", "paths.experimental_install", "paths.stable_install",
                      "harness.helper_timeout_seconds")
    versus_session = versus_inspect + (
        "paths.work_root", "tools.winshot_root", "harness.state_timeout_seconds",
        "harness.startup_timeout_seconds", "harness.finish_timeout_seconds",
        "harness.key_hold_ms", "harness.key_gap_ms", "harness.menu_fade_seconds")
    requirements = {
        "workflow": workflow,
        "workflow-report": workflow + ("tools.python_report",),
        "report": report,
        "report-audio": report + ("tools.audio_probe",),
        "report-sheet": report + ("paths.stable_install",),
        "versus-inspect": versus_inspect,
        "versus-session": versus_session,
        "endings-view": ("repo_root", "paths.work_root", "paths.experimental_install",
                         "paths.stable_install", "tools.winshot_root"),
        "endings-acceptance": ("repo_root", "paths.work_root", "paths.experimental_install",
                               "paths.stable_install", "tools.winshot_root"),
        # Explicit dance helper arguments may satisfy the tool dependency instead.
        "dance-capture": ("repo_root", "paths.work_root", "paths.stable_install"),
        "recording-record": ("repo_root", "paths.work_root", "paths.stable_install") + tuple(
            key for key in fields if key.startswith("recording.")),
        "recording-finalize": ("repo_root", "paths.work_root", "paths.stable_install",
                               "tools.ffmpeg_review", "tools.ffprobe_review", "tools.recording_font"),
        "recording-frames": ("repo_root", "paths.work_root", "paths.stable_install", "tools.ffmpeg_look"),
        "native-capture": ("repo_root", "paths.work_root", "paths.stable_install",
                            "tools.ffmpeg_native"),
        "character-workspace": ("repo_root", "paths.work_root", "paths.stable_install"),
        "gaso-source-usa": ("inputs.bag1_usa_extraction",),
        "gaso-source-jp": ("inputs.bag1_jp_extraction",),
        "gaso-build": ("inputs.gaso_profile", "inputs.gaso_stock_bio",
                       "inputs.gaso_stock_fever", "inputs.gaso_motions",
                       "paths.gaso_out_usa", "paths.gaso_out_jp"),
        # Legacy Heat test-mod adapters: preparation and the external make-mod step are separate.
        "heat-character-prepare": ("repo_root", "paths.work_root", "paths.stable_install",
                                   "inputs.heat_bag1_members", "paths.heat_test_workspace",
                                   "wsl.distribution"),
        "heat-stage-prepare": ("repo_root", "paths.work_root", "paths.stable_install",
                               "inputs.bag1_usa_extraction", "paths.heat_stage_workspace",
                               "wsl.distribution"),
        "heat-test-package": ("paths.experimental_install", "paths.stable_install",
                              "tools.psx_asset_tools", "inputs.bag2_cue", "wsl.distribution"),
    }
    for operation, keys in requirements.items():
        for key in keys:
            fields[key] = replace(fields[key], operations=fields[key].operations + (operation,))
    return MappingProxyType(fields)


FIELDS = _field_registry()
_SECTIONS = frozenset(key.split(".")[0] for key in FIELDS if "." in key)


def _read_toml(path: Path, label: str) -> tuple[dict, str]:
    try:
        raw = path.read_bytes()
        data = tomllib.loads(raw.decode("utf-8-sig"))
    except (OSError, UnicodeError, tomllib.TOMLDecodeError) as exc:
        raise ConfigError(f"{label}: cannot read or parse {path}") from exc
    return data, hashlib.sha256(raw).hexdigest()


def _flatten(data: dict) -> dict[str, object]:
    fields = {}
    for section, value in data.items():
        if section in ("schema_version", "repo_root"):
            fields[section] = value
        elif section not in _SECTIONS or not isinstance(value, dict):
            raise ConfigError(f"Unknown or invalid section: {section}")
        else:
            for name, field in value.items():
                key = f"{section}.{name}"
                if key not in FIELDS:
                    raise ConfigError(f"Unknown field: {key}")
                fields[key] = field
    return fields


def _resolve_path(value: str, root: Path, key: str) -> Path:
    if not value.strip() or "\0" in value:
        raise ConfigError(f"{key}: expected a nonempty path without NUL")
    path = Path(value)
    if path.anchor and not path.is_absolute():
        raise ConfigError(f"{key}: ambiguous relative drive or root")
    try:
        return (path if path.is_absolute() else root / path).resolve()
    except (OSError, RuntimeError, ValueError) as exc:
        raise ConfigError(f"{key}: cannot resolve path") from exc


def _validate_layer(data: dict, root: Path, *, local: bool) -> dict[str, Path | str | int | float]:
    fields = _flatten(data)
    if not local and "schema_version" not in fields:
        raise ConfigError("common: schema_version is required")
    result = {}
    for key, value in fields.items():
        spec = FIELDS[key]
        if spec.role == "derived":
            raise ConfigError(f"{key}: derived field cannot be configured")
        if local and not spec.local_override:
            raise ConfigError(f"{key}: local policy override is forbidden")
        if spec.kind == "integer":
            if spec.expected is not None:
                if type(value) is not int or value != spec.expected:
                    raise ConfigError(f"{key}: expected integer {spec.expected}")
            elif (type(value) is not int or value <= 0
                  or (spec.maximum is not None and value > spec.maximum)):
                raise ConfigError(f"{key}: expected a positive integer up to {spec.maximum:g}")
        elif spec.kind == "number":
            finite = False
            if type(value) in (int, float):
                try:
                    finite = math.isfinite(value)
                except OverflowError:
                    pass
            if (not finite or value <= 0
                    or (spec.maximum is not None and value > spec.maximum)
                    or (spec.expected is not None and value != spec.expected)):
                exact = f" exactly {spec.expected}" if spec.expected is not None else ""
                bound = f" up to {spec.maximum:g}" if spec.maximum is not None else ""
                raise ConfigError(f"{key}: expected a positive finite number{bound}{exact}")
        elif not isinstance(value, str) or not value.strip() or "\0" in value:
            raise ConfigError(f"{key}: expected a nonempty string")
        elif spec.kind == "revision" and not re.fullmatch(r"[0-9a-fA-F]{7,40}", value):
            raise ConfigError(f"{key}: expected a Git hex prefix")
        elif spec.kind == "path":
            value = _resolve_path(value, root, key)
        result[key] = value
    return result


def load_config(*, repo_root: Path | None = None,
                local_config: Path | None = None) -> ProjectConfig:
    """Read common plus an explicit/default local overlay; never create or run anything.

    Relative local-config selections and configured path values anchor to the repo.
    A missing default local file is allowed; an explicitly selected missing file is not.
    """
    root = (Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[2]).resolve()
    common, common_hash = _read_toml(root / "config/project.toml", "common")
    values = _validate_layer(common, root, local=False)
    origins = dict.fromkeys(values, "common")
    local = root / "config/project.local.toml" if local_config is None else Path(local_config)
    if not local.is_absolute():
        local = root / local
    local_hash = None
    if local_config is not None or local.exists() or local.is_symlink():
        layer, local_hash = _read_toml(local, "local")
        overlay = _validate_layer(layer, root, local=True)
        values.update(overlay)
        origins.update(dict.fromkeys(overlay, "local"))
    values["repo_root"] = root
    origins["repo_root"] = "derived"
    schema_file = Path(__file__).resolve()
    hashes = {"common": common_hash, "local": local_hash,
              "schema": hashlib.sha256(schema_file.read_bytes()).hexdigest()}
    files = {"common": str(root / "config/project.toml"),
             "local": str(local) if local_hash is not None else None,
             "schema": str(schema_file)}
    return ProjectConfig(root, MappingProxyType(values), MappingProxyType(origins),
                         MappingProxyType(hashes), MappingProxyType(files))


def recording_overrides(config: ProjectConfig, *, environ: Mapping[str, str] | None = None,
                        fps: int | None = None, max_seconds: float | None = None,
                        game_dir: Path | None = None) -> ProjectConfig:
    """Snapshot the recorder's documented CLI/environment interfaces, without fallbacks.

    Explicit empty WGC disables the configured candidate, as in the legacy interface.
    Explicit relative CLI/env paths retain their CWD meaning; TOML paths remain repo-based.
    """
    values, origins = dict(config.values), dict(config.origins)
    environment = dict(os.environ if environ is None else environ)
    name = "BAG2JP_FFMPEG_WGC"
    if name in environment:
        key = "tools.ffmpeg_wgc"
        raw = environment[name]
        values.pop(key, None)
        if raw:
            values[key] = _resolve_path(raw, Path.cwd(), key)
        origins[key] = f"environment:{name}" if raw else f"environment:{name}:disabled"
    arguments = {key: value for key, value in (("fps", fps), ("max_seconds", max_seconds))
                 if value is not None}
    if arguments:
        overridden = _validate_layer({"recording": arguments}, config.repo_root, local=True)
        values.update(overridden)
        origins.update(dict.fromkeys(overridden, "cli"))
    if game_dir is not None:
        values["paths.experimental_install"] = _resolve_path(str(game_dir), Path.cwd(), "--game-dir")
        origins["paths.experimental_install"] = "cli"
    return replace(config, values=MappingProxyType(values), origins=MappingProxyType(origins))


def require_paths(config: ProjectConfig, keys: Sequence[str]) -> tuple[Path, ...]:
    """Return configured paths in request order; do not require existence or invent values."""
    result = []
    for key in keys:
        if key not in FIELDS or FIELDS[key].kind != "path" or not isinstance(config.values.get(key), Path):
            raise ConfigError(f"{key}: required path is unresolved or not a path field")
        result.append(config.values[key])
    return tuple(result)


def require_values(config: ProjectConfig, keys: Sequence[str]) -> tuple:
    """Return resolved registered values of any kind in request order; never invent defaults."""
    unresolved = [key for key in keys if key not in FIELDS or key not in config.values]
    if unresolved:
        raise ConfigError(f"{', '.join(unresolved)}: required value is unresolved or unregistered")
    return tuple(config.values[key] for key in keys)


WRITE_ROLES = MappingProxyType({
    FIELDS[f"paths.{name}"].role: f"paths.{name}"
    for name in ("work_root", "build_root", "experimental_install")
})
OPERATIONS = ("inspect", *dict.fromkeys(operation for spec in FIELDS.values()
                                       for operation in spec.operations))


def _normalized(path: Path) -> str:
    return os.path.normcase(os.path.normpath(str(path)))


def _is_within(root: Path, target: Path) -> bool:
    """Case-insensitive containment on normalized text; unit roots keep one separator."""
    root_text, target_text = _normalized(root), _normalized(target)
    if target_text == root_text:
        return True
    prefix = root_text if root_text.endswith(os.sep) else root_text + os.sep
    return target_text.startswith(prefix)


def _resolve_physical(path: Path) -> Path:
    """Resolve existing ancestry and reattach missing names without creating anything."""
    path = Path(path)
    missing: list[str] = []
    current = path
    while not (current.exists() or current.is_symlink()):
        if current.parent == current:
            break
        missing.append(current.name)
        current = current.parent
    try:
        base = current.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ConfigError(f"Cannot resolve {path}") from exc
    for name in reversed(missing):
        base = base / name
    return base


def assert_write_target(config: ProjectConfig, target: Path, *, role: str) -> Path:
    """Return a checked absolute target for a write role; never create or modify it.

    Relative targets anchor to the role root. The stable installation, and any
    ancestor or descendant overlap with it, is rejected even through aliases.
    Validation cannot make a later filesystem change race-safe.
    """
    if role not in WRITE_ROLES:
        raise ConfigError(f"Unknown write role: {role}")
    root, stable = require_paths(config, (WRITE_ROLES[role], "paths.stable_install"))
    raw = Path(target)
    text = str(raw)
    if not text or text in (".", "..") or "\0" in text:
        raise ConfigError(f"Invalid write target: {target!r}")
    if raw.anchor and not raw.is_absolute():
        raise ConfigError(f"{text}: ambiguous drive-relative write target")
    lexical = raw if raw.is_absolute() else root / raw
    if not _is_within(root, lexical):
        raise ConfigError(f"{raw}: target is outside the {role} root {root}")
    candidate = _resolve_physical(lexical)
    if not _is_within(_resolve_physical(root), candidate):
        raise ConfigError(f"{raw}: target resolves outside the {role} root {root}")
    physical_stable = _resolve_physical(stable)
    if (_is_within(physical_stable, candidate) or _is_within(candidate, physical_stable)
            or _is_within(stable, lexical) or _is_within(lexical, stable)):
        raise ConfigError(f"{raw}: overlaps the protected stable installation {stable}")
    try:
        if candidate.is_file() and candidate.stat().st_nlink > 1:
            raise ConfigError(f"{raw}: write target has multiple hard links")
    except OSError as exc:
        raise ConfigError(f"Cannot inspect write target: {raw}") from exc
    return candidate


_DRIVE_PATH = re.compile(r"([A-Za-z]):[\\/](.*)", re.DOTALL)


def to_wsl_path(path: Path) -> str:
    """Convert a verified local drive path to a WSL mount path; never guesses mounts."""
    text = str(path)
    if not text or "\0" in text:
        raise ConfigError(f"{path}: unsupported path text")
    if text.startswith(("\\\\", "//")):
        raise ConfigError(f"{path}: UNC, network and device paths are not convertible")
    match = _DRIVE_PATH.fullmatch(text)
    if not match:
        raise ConfigError(f"{path}: expected an absolute Windows drive path")
    drive, remainder = match.group(1).lower(), match.group(2)
    parts = [part for part in remainder.replace("\\", "/").split("/") if part]
    if any(part in (".", "..") for part in parts):
        raise ConfigError(f"{path}: '.' or '..' segments are not convertible")
    return "/mnt/" + drive + ("/" + "/".join(parts) if parts else "")


def export_config(config: ProjectConfig, *, operation: str) -> dict[str, object]:
    """Serialize resolved values, provenance and gaps for other runtimes.

    Missing keys are reported, never substituted; serialization does not authorize
    the operation or prove that a WSL mount/tool exists.
    """
    if operation not in OPERATIONS:
        raise ConfigError(f"Unknown operation: {operation}")
    values = {key: str(value) if isinstance(value, Path) else value
              for key, value in sorted(config.values.items())}
    schema_version = config.values.get("schema_version")
    if schema_version is None:
        raise ConfigError("schema_version: unresolved")
    unresolved = sorted(key for key in FIELDS if key not in config.values)
    missing = sorted(key for key, spec in FIELDS.items()
                     if operation in spec.operations and key not in config.values)
    return {
        "schema_version": schema_version,
        "operation": operation,
        "repo_root": str(config.repo_root),
        "values": values,
        "origins": dict(sorted(config.origins.items())),
        "config": dict(sorted(config.input_hashes.items())),
        "files": dict(sorted(config.input_files.items())),
        "unresolved": unresolved,
        "missing": missing,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local-config", type=Path, default=None,
                        help="local TOML overlay; relative selections anchor to the repository")
    parser.add_argument("--operation", choices=OPERATIONS, default="inspect")
    args = parser.parse_args(argv)
    try:
        payload = export_config(load_config(local_config=args.local_config),
                                operation=args.operation)
    except ConfigError as exc:
        print(f"config error: {exc}", file=sys.stderr)
        return 2
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stdout.write(text)
    elif getattr(sys.stdout, "buffer", None) is not None:
        sys.stdout.buffer.write(text.encode("utf-8"))
    else:
        raise ConfigError("stdout cannot carry UTF-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
