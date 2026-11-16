"""Host configuration compliance checker (S2b).

Reads the reconciled inventory and reports:
- files without a registered disposition (status reviewed/partial/etc.),
- hardcoded machine paths in Python sources that bypass config keys.

No fixes are applied; it only reports.
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

_MACHINE_PATH = re.compile(r'["\']([A-Za-z]:[/\\\\]|\\\\\\[^"\\])[^"\']*["\']')
_WORK_BARE = re.compile(r'["\']_work/[^"\']*["\']|["\']_work\\[^"\']*["\']')


class AuditConfigChecker:
    """Audit the host configuration inventory for missing dispositions."""

    def __init__(self, repo_root: Path, inventory_path: Path):
        self.repo_root = Path(repo_root).resolve()
        self.inventory_path = Path(inventory_path)
        self._inventory = None

    @property
    def inventory(self):
        if self._inventory is None:
            self._inventory = json.loads(self.inventory_path.read_text(encoding="utf-8"))
        return self._inventory

    def _is_exception(self, entry: dict) -> bool:
        progress = entry.get("progress") or {}
        status = progress.get("status", "")
        scope = progress.get("review_scope", "")
        return status == "exception_justified" or "exception_justified" in scope

    def _entries(self, lot_id: str | None = None):
        for entry in self.inventory.get("files", []):
            if lot_id is not None and entry.get("primary_lot") != lot_id:
                continue
            yield entry
        for entry in self.inventory.get("added_files", []):
            if lot_id is not None and entry.get("primary_lot") != lot_id:
                continue
            yield entry

    def files_without_disposition(self, lot_id: str | None = None):
        """Return files whose progress status is not a reviewed disposition."""
        pending = []
        for entry in self._entries(lot_id):
            progress = entry.get("progress", {})
            status = progress.get("status", "")
            if status in ("reviewed", "partial", "delivered_scoped_host",
                          "delivered_host_scoped_not_lot_closed",
                          "reviewed_scoped", "supporting_change_recorded",
                          "no_host_change_required"):
                continue
            pending.append(entry.get("file", ""))
        return sorted(set(pending))

    def hardcoded_files(self, lot_id: str | None = None):
        """Return Python files of the inventory with unapproved hardcodes.

        Files whose disposition is an exception justified (native/data/test)
        are excluded because hardcodes there are expected and audited.
        Test modules (test_*.py / *_test.py) are excluded: their hardcodes are
        intentional fixtures for validating the checker itself.
        """
        flagged = []
        for entry in self._entries(lot_id):
            rel = entry.get("file", "")
            if not rel.endswith(".py"):
                continue
            name = Path(rel).name
            if name.startswith("test_") or name.endswith("_test.py"):
                continue
            if self._is_exception(entry):
                continue
            target = self.repo_root / rel
            if not target.is_file():
                continue
            findings = hardcode_findings(target)
            if findings:
                flagged.append({"file": rel, "findings": findings})
        return sorted(flagged, key=lambda item: item["file"])

    def check(self, lot_id: str | None = None):
        pending = self.files_without_disposition(lot_id)
        hardcoded = self.hardcoded_files(lot_id)
        return {
            "files_without_disposition": len(pending),
            "pending_files": pending,
            "hardcoded_files": len(hardcoded),
            "hardcoded_details": hardcoded,
        }


def hardcode_findings(path: Path):
    """Return machine-path hardcode findings in a Python source file."""
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    findings = []
    for match in _MACHINE_PATH.finditer(text):
        findings.append(match.group(0))
    for match in _WORK_BARE.finditer(text):
        findings.append(match.group(0))
    return findings


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, default=None,
                        help="inventory JSON path (default: plans/pending/...)")
    parser.add_argument("--lot", type=str, default=None,
                        help="audit only a single reconciliation lot id")
    args = parser.parse_args(argv)

    inventory = args.inventory or (
        ROOT / "plans/pending/host-configuration-migration.inventory.json"
    )
    checker = AuditConfigChecker(ROOT, inventory)
    report = checker.check(lot_id=args.lot)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    # Exit nonzero only on real defects (unapproved hardcodes), not on
    # informational disposition counts.
    return 1 if report["hardcoded_files"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
