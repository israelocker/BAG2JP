"""Record a human visual review of a versus navigation calibration run.

The harness refuses to navigate until the calibration catalog carries an
explicit reviewer decision bound to the runtime hash, the edges and the exact
screenshots reviewed. This helper writes that record, so re-calibrating after a
code change is one reviewed command instead of hand-edited JSON.

Usage:
    py -3.13 tools/test/accept_versus_calibration.py --run _work/versus-runs/<tag>
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import versus_navigation as nav  # noqa: E402

CATALOG = REPO / "_work/versus-navigation/catalog.json"
REVIEWED_IMAGES = ("selector.png", "probe-0-right-2.png", "probe-2-left-0.png",
                   "probe-0-down-1.png", "probe-1-up-0.png", "review-sheet.png")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_catalog(run: Path) -> dict:
    """Keep the calibrated graph and bind it to the reviewed screenshots."""
    source = run / "catalog.json"
    if not source.is_file():
        raise SystemExit(f"missing calibration catalog: {source}")
    catalog = json.loads(source.read_text(encoding="utf-8"))
    missing = [name for name in REVIEWED_IMAGES if not (run / name).is_file()]
    if missing:
        raise SystemExit("missing reviewed evidence: " + ", ".join(missing))
    catalog["image_sha256"] = {name: sha256(run / name) for name in REVIEWED_IMAGES}
    catalog["visual_review"] = "accepted"
    catalog["reviewed_catalog_sha256"] = nav.catalog_review_digest(catalog)
    nav.verify_catalog_review(catalog)
    return catalog


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True, help="calibration run directory")
    args = parser.parse_args()
    catalog = build_catalog(args.run)
    CATALOG.parent.mkdir(parents=True, exist_ok=True)
    CATALOG.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"catalog": str(CATALOG), "runtime_sha256": catalog["runtime_sha256"],
                      "edges": catalog["edges"],
                      "reviewed_catalog_sha256": catalog["reviewed_catalog_sha256"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
