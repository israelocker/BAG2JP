"""Resolve shared host-tool configuration without launching tools or writing files."""

import argparse
from dataclasses import dataclass
import hashlib
import json
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
    expected: int | None = None


@dataclass(frozen=True)
class ProjectConfig:
    """An immutable resolved host configuration."""

    repo_root: Path
    values: Mapping[str, Path | str | int]
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
                  "tools_root": "tools"}
    for name, role in path_roles.items():
        operations = ("payload-manifest",) if name in ("build_root", "experimental_install") else ()
        fields[f"paths.{name}"] = FieldSpec("path", "native path", True, role, operations)
    for name in ("bag1_usa_disc", "bag1_jp_disc", "bag1_usa_extraction", "bag1_jp_extraction",
                 "bag1_reference_runtime"):
        fields[f"inputs.{name}"] = FieldSpec("path", "native path", True, "input")
    for name in ("python_report", "winshot_root", "build_script", "ffmpeg_review", "ffmpeg_wgc",
                 "ghidra_launcher", "ghidra_project"):
        fields[f"tools.{name}"] = FieldSpec("path", "native path", True, "tool")
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


def _validate_layer(data: dict, root: Path, *, local: bool) -> dict[str, Path | str | int]:
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
            if spec.expected is None or type(value) is not int or value != spec.expected:
                raise ConfigError(f"{key}: expected integer {spec.expected}")
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


def require_paths(config: ProjectConfig, keys: Sequence[str]) -> tuple[Path, ...]:
    """Return configured paths in request order; do not require existence or invent values."""
    result = []
    for key in keys:
        if key not in FIELDS or FIELDS[key].kind != "path" or not isinstance(config.values.get(key), Path):
            raise ConfigError(f"{key}: required path is unresolved or not a path field")
        result.append(config.values[key])
    return tuple(result)



WRITE_ROLES = MappingProxyType({
    FIELDS[f"paths.{name}"].role: f"paths.{name}"
    for name in ("work_root", "build_root", "experimental_install")
})
OPERATIONS = ("inspect", "payload-manifest")


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
