"""Verify that every copy of the alternate payload matches its manifest sha256.

Writing a rebuilt stage DFS into payload/bag1_alt.bin without updating the
manifest makes the runtime reject the whole package ("overlay payload
checksum failed"), which silently disables every plugin of bag1-content
(character version popup, BAG1 stages, tank, fan patch).

usage: check_payload_manifest.py [--package DIR ...] [--local-config FILE]

Without --package, the four copies are derived from the host configuration
(repo, build root, experimental install), never from machine literals.
"""
import argparse
import hashlib
import sys
import tomllib
from pathlib import Path

# Documented usage runs this file by path, so the repo root may be missing from sys.path.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.workflow import project_config

# Aliases keep the resolver patchable in tests; the class is read from its module so a
# reloaded registry still raises the exception type this module catches.
load_config = project_config.load_config
require_paths = project_config.require_paths

PACKAGE = Path("bag2jp.feature.bag1-content/1.0.0")
OVERLAY = "payload/bag1_alt.bin"


def check(package: Path) -> tuple[bool, str]:
    """Report one copy; unreadable or malformed inputs fail that copy, not the run."""
    manifest = package / "manifest.toml"
    payload = package / OVERLAY
    if not manifest.is_file() or not payload.is_file():
        return False, "missing manifest or payload"
    try:
        spec = tomllib.loads(manifest.read_text(encoding="utf-8-sig"))
        overlay = next((row for row in spec.get("overlay", [])
                        if isinstance(row, dict) and row.get("file") == OVERLAY), None)
        digest = hashlib.sha256(payload.read_bytes()).hexdigest()
    except (OSError, UnicodeError, ValueError, tomllib.TOMLDecodeError) as exc:
        return False, f"invalid manifest or payload: {exc.__class__.__name__}"
    if overlay is None:
        return False, "manifest has no bag1_alt overlay"
    if digest != overlay.get("sha256"):
        return False, f"sha256 {digest} != manifest {overlay.get('sha256')}"
    return True, digest


def default_packages(config) -> tuple[Path, ...]:
    """Derive the four package copies from configured roots; never guess a mount."""
    build_root, experimental = require_paths(
        config, ("paths.build_root", "paths.experimental_install"))
    return (
        config.repo_root / "mods-src" / PACKAGE,
        build_root / "mods/preloaded/packages" / PACKAGE,
        build_root / "build-win-codex/mods/bundled" / PACKAGE,
        experimental / "mods/bundled" / PACKAGE,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, action="append", default=None)
    parser.add_argument("--local-config", type=Path, default=None,
                        help="local TOML overlay; relative selections anchor to the repository; "
                             "ignored when --package is given")
    args = parser.parse_args(argv)
    if args.package:
        packages = tuple(args.package)
    else:
        try:
            packages = default_packages(load_config(local_config=args.local_config))
        except project_config.ConfigError as exc:
            print(f"config error: {exc}", file=sys.stderr)
            return 2
    failed = 0
    for package in packages:
        ok, detail = check(package)
        print(("OK   " if ok else "FAIL ") + str(package) + " :: " + detail)
        failed += not ok
    print(f"{len(packages) - failed}/{len(packages)} copies match their manifest")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
