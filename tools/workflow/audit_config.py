"""Host configuration compliance checker (S2b).

Reads the reconciled inventory and reports:
- files without a registered disposition (status reviewed/partial/etc.),
- hardcoded machine paths in Python sources that bypass config keys.

No fixes are applied; it only reports.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

_MACHINE_PATH = re.compile(r'["\']([A-Za-z]:[/\\\\]|\\\\\\[^"\\])[^"\']*["\']')
_WORK_BARE = re.compile(r'["\']_work/[^"\']*["\']|["\']_work\\[^"\']*["\']')
# Indirect forms: a bare quoted work-root segment, a /_work/ inside any literal or f-string,
# a parents[N] walk to a sibling Tools folder, and home-relative locations.
_INDIRECT = re.compile(r'["\']_work["\']'
                       r'|["\'][^"\'\n]*[/\\]_work[/\\][^"\'\n]*["\']'
                       r'|parents\[\d+\]\s*/\s*["\']Tools'
                       r'|expanduser\(|["\']~/')
# Home-relative and absolute POSIX locations that bypass configured keys.
_HOME_FORMS = re.compile(r'Path\.home\(\)|os\.environ\[|getenv\(|os\.path\.expanduser\(')
_POSIX_ROOT = re.compile(r'["\'](/mnt/|/home/)[^"\'\n]*["\']')
_ALLOW = re.compile(r"#\s*config-audit:\s*allow\s+([A-Za-z0-9][A-Za-z0-9 .-]{2,})$")
# Host sources scanned even when absent from the inventory (Git-tracked only).
_HOST_SOURCES = re.compile(r'^(tools/.+|mods-src/[^/]+/tools/.+)\.py$')


class AuditConfigChecker:
    """Audit the host configuration inventory for missing dispositions."""

    def __init__(self, repo_root: Path, inventory_path: Path, *, tracked: list[str] | None = None):
        self.repo_root = Path(repo_root).resolve()
        self.inventory_path = Path(inventory_path)
        self._inventory = None
        self._tracked = tracked

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
        entries = list(self._entries(lot_id))
        if lot_id is None:
            entries += [{"file": rel} for rel in self.unregistered_files()]
        for entry in entries:
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

    def unregistered_files(self):
        """Tracked host Python sources that the inventory does not list."""
        listed = {entry.get("file", "") for entry in self._entries()}
        tracked = self._tracked if self._tracked is not None else tracked_files(self.repo_root)
        return sorted(rel for rel in tracked if _HOST_SOURCES.match(rel) and rel not in listed)

    def check(self, lot_id: str | None = None):
        pending = self.files_without_disposition(lot_id)
        hardcoded = self.hardcoded_files(lot_id)
        return {
            "files_without_disposition": len(pending),
            "pending_files": pending,
            "unregistered_files": self.unregistered_files() if lot_id is None else [],
            "hardcoded_files": len(hardcoded),
            "hardcoded_details": hardcoded,
        }


def hardcode_findings(path: Path):
    """Return machine-path hardcode findings in a Python source file."""
    path = Path(path)
    # A line may opt out only with a stated reason, e.g. a declared-syntax token.
    text = "\n".join(line for line in path.read_text(encoding="utf-8").splitlines()
                     if not _ALLOW.search(line))
    findings = []
    for match in _MACHINE_PATH.finditer(text):
        findings.append(match.group(0))
    for match in _WORK_BARE.finditer(text):
        findings.append(match.group(0))
    for match in _INDIRECT.finditer(text):
        if match.group(0) not in findings:
            findings.append(match.group(0))
    for match in _HOME_FORMS.finditer(text):
        if match.group(0) not in findings:
            findings.append(match.group(0))
    for match in _POSIX_ROOT.finditer(text):
        if match.group(0) not in findings:
            findings.append(match.group(0))
    return findings


def tracked_files(repo_root: Path) -> list[str]:
    """Git-tracked paths of the repository (untracked third-party trees are not host code)."""
    result = subprocess.run(["git", "-C", str(repo_root), "ls-files", "-z"],
                            capture_output=True, check=True)
    return [name for name in result.stdout.decode("utf-8").split("\0") if name]


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
    return exit_code(report)


def exit_code(report: dict) -> int:
    """Nonzero on real defects: unapproved hardcodes or host sources the inventory does not cover.

    Disposition counts stay informational.
    """
    return 1 if report["hardcoded_files"] or report["unregistered_files"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
