"""Verify that every copy of the alternate payload matches its manifest sha256.

Writing a rebuilt stage DFS into payload/bag1_alt.bin without updating the
manifest makes the runtime reject the whole package ("overlay payload
checksum failed"), which silently disables every plugin of bag1-content
(character version popup, BAG1 stages, tank, fan patch).

usage: check_payload_manifest.py [--package DIR ...]
"""
import argparse
import hashlib
import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PACKAGE = Path("bag2jp.feature.bag1-content/1.0.0")
DEFAULT_PACKAGES = (
    REPO / "mods-src" / PACKAGE,
    Path("D:/Dev/Recomp/BAG2JP-codex-build/BAG2JP/mods/preloaded/packages") / PACKAGE,
    Path("D:/Dev/Recomp/BAG2JP-codex-build/BAG2JP/build-win-codex/mods/bundled") / PACKAGE,
    Path("D:/Games/Bust A Groove 2 (Japan)/BAG2JP-exp-8mb/mods/bundled") / PACKAGE,
)
OVERLAY = "payload/bag1_alt.bin"


def check(package: Path) -> tuple[bool, str]:
    manifest = package / "manifest.toml"
    payload = package / OVERLAY
    if not manifest.is_file() or not payload.is_file():
        return False, "missing manifest or payload"
    spec = tomllib.loads(manifest.read_text(encoding="utf-8-sig"))
    overlay = next((row for row in spec.get("overlay", []) if row.get("file") == OVERLAY), None)
    if overlay is None:
        return False, "manifest has no bag1_alt overlay"
    digest = hashlib.sha256(payload.read_bytes()).hexdigest()
    if digest != overlay.get("sha256"):
        return False, f"sha256 {digest} != manifest {overlay.get('sha256')}"
    return True, digest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, action="append", default=None)
    args = parser.parse_args()
    packages = args.package or DEFAULT_PACKAGES
    failed = 0
    for package in packages:
        ok, detail = check(package)
        print(("OK   " if ok else "FAIL ") + str(package) + " :: " + detail)
        failed += not ok
    print(f"{len(packages) - failed}/{len(packages)} copies match their manifest")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
