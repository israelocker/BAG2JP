"""Compliance checks for host configuration inventory (S2b)."""
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

import sys
sys.path.insert(0, str(ROOT / "tools/workflow"))

from audit_config import AuditConfigChecker, hardcode_findings  # noqa: E402


class AuditConfigComplianceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "tools" / "workflow").mkdir(parents=True)
        (self.root / "plans" / "pending").mkdir(parents=True)

    def _write_inventory(self, files):
        data = {
            "schema": 1,
            "files": files,
            "reconciliation": {"lots": []},
        }
        path = self.root / "plans" / "pending" / "host-configuration-migration.inventory.json"
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return path

    def test_all_files_have_disposition(self):
        files = [
            {"file": "tools/bag1import/a.py", "progress": {"status": "reviewed"}},
            {"file": "tools/bag1import/b.py", "progress": {"status": "unreviewed"}},
        ]
        self._write_inventory(files)
        checker = AuditConfigChecker(self.root, self.root / "plans" / "pending" / "host-configuration-migration.inventory.json", tracked=[])
        report = checker.check()
        self.assertEqual(report["files_without_disposition"], 1)
        self.assertIn("tools/bag1import/b.py", report["pending_files"])

    def test_hardcode_detection_flags_machine_path(self):
        (self.root / "tools" / "workflow" / "sample.py").write_text(
            'PATH = "D:/Dev/Recomp/BAG2JP/_work/bag1/scus.bin"\n', encoding="utf-8"
        )
        findings = hardcode_findings(self.root / "tools" / "workflow" / "sample.py")
        self.assertTrue(any("D:/" in f for f in findings))

    def test_hardcode_detection_flags_indirect_forms(self):
        sample = self.root / "tools" / "workflow" / "sample.py"
        for source in ('W = Path("_work") / "x"\n', 'W = root / "_work/x.bin"\n',
                       "d = open(f'{P}/_work/mainexe/slpm.bin')\n",
                       'T = root.parents[1] / "Tools/psx-asset-tools"\n',
                       "T = os.path.expanduser('~/work/hq')\n", "T = '~/mnt/Dev'\n"):
            with self.subTest(source=source):
                sample.write_text(source, encoding="utf-8")
                self.assertNotEqual(hardcode_findings(sample), [])

    def test_unregistered_host_source_fails_the_audit(self):
        from audit_config import exit_code
        self.assertEqual(exit_code({"hardcoded_files": 0, "unregistered_files": ["tools/x.py"]}), 1)
        self.assertEqual(exit_code({"hardcoded_files": 0, "unregistered_files": []}), 0)

    def test_line_pragma_with_reason_is_the_only_allowance(self):
        sample = self.root / "tools" / "workflow" / "sample.py"
        sample.write_text('TOKEN = "_work"  # config-audit: allow declared-syntax token\n', encoding="utf-8")
        self.assertEqual(hardcode_findings(sample), [])
        for source in ('TOKEN = "_work"  # config-audit: allow\n', 'TOKEN = "_work"  # allow declared\n'):
            with self.subTest(source=source):
                sample.write_text(source, encoding="utf-8")
                self.assertNotEqual(hardcode_findings(sample), [])

    def test_tracked_python_outside_inventory_is_scanned(self):
        (self.root / "mods-src" / "pkg" / "tools").mkdir(parents=True)
        (self.root / "mods-src" / "pkg" / "tools" / "stray.py").write_text(
            "T = os.path.expanduser('~/work/x')\n", encoding="utf-8")
        (self.root / "tools" / "workflow" / "listed.py").write_text("x = 1\n", encoding="utf-8")
        self._write_inventory([{"file": "tools/workflow/listed.py", "progress": {"status": "reviewed"}}])
        checker = AuditConfigChecker(self.root, self.root / "plans" / "pending" / "host-configuration-migration.inventory.json",
                                     tracked=["mods-src/pkg/tools/stray.py", "tools/workflow/listed.py"])
        report = checker.check()
        self.assertEqual([d["file"] for d in report["hardcoded_details"]], ["mods-src/pkg/tools/stray.py"])
        self.assertEqual(report["unregistered_files"], ["mods-src/pkg/tools/stray.py"])

    def test_no_hardcode_on_config_driven_file(self):
        (self.root / "tools" / "workflow" / "sample.py").write_text(
            'path = config.values["paths.work_root"]\n', encoding="utf-8"
        )
        findings = hardcode_findings(self.root / "tools" / "workflow" / "sample.py")
        self.assertEqual(findings, [])

    def test_hardcoded_files_reports_unapproved_python(self):
        (self.root / "tools" / "workflow" / "bad.py").write_text(
            'PATH = "D:/Dev/Recomp/BAG2JP/_work/bag1/scus.bin"\n', encoding="utf-8"
        )
        (self.root / "tools" / "workflow" / "good.py").write_text(
            'path = config.values["paths.work_root"]\n', encoding="utf-8"
        )
        files = [
            {"file": "tools/workflow/bad.py", "progress": {"status": "reviewed"}},
            {"file": "tools/workflow/good.py", "progress": {"status": "reviewed"}},
        ]
        self._write_inventory(files)
        checker = AuditConfigChecker(self.root, self.root / "plans" / "pending" / "host-configuration-migration.inventory.json", tracked=[])
        report = checker.check()
        self.assertEqual(report["hardcoded_files"], 1)
        self.assertEqual(report["hardcoded_details"][0]["file"], "tools/workflow/bad.py")

    def test_exception_justified_not_flagged_for_hardcode(self):
        (self.root / "tools" / "workflow" / "native.py").write_text(
            'PATH = "D:/Games/Bust A Groove 2 (Japan)/ISO/SLPM-86219.cue"\n', encoding="utf-8"
        )
        files = [
            {"file": "tools/workflow/native.py", "progress": {"status": "exception_justified"}},
        ]
        self._write_inventory(files)
        checker = AuditConfigChecker(self.root, self.root / "plans" / "pending" / "host-configuration-migration.inventory.json", tracked=[])
        report = checker.check()
        self.assertEqual(report["hardcoded_files"], 0)

    def test_new_unapproved_hardcode_fails(self):
        (self.root / "tools" / "workflow" / "new_bad.py").write_text(
            'DATA = "C:/Users/israe/AppData/Local/Temp/secret.bin"\n', encoding="utf-8"
        )
        files = [
            {"file": "tools/workflow/new_bad.py", "progress": {"status": "reviewed"}},
        ]
        self._write_inventory(files)
        checker = AuditConfigChecker(self.root, self.root / "plans" / "pending" / "host-configuration-migration.inventory.json", tracked=[])
        report = checker.check()
        self.assertEqual(report["hardcoded_files"], 1)

    def test_lot_filter_only_audits_requested_lot(self):
        (self.root / "tools" / "workflow" / "lot_a.py").write_text(
            'PATH = "D:/lot/a.bin"\n', encoding="utf-8"
        )
        (self.root / "tools" / "workflow" / "lot_b.py").write_text(
            'path = config.values["paths.work_root"]\n', encoding="utf-8"
        )
        files = [
            {"file": "tools/workflow/lot_a.py", "primary_lot": "LOT-A",
             "progress": {"status": "reviewed"}},
            {"file": "tools/workflow/lot_b.py", "primary_lot": "LOT-B",
             "progress": {"status": "reviewed"}},
        ]
        self._write_inventory(files)
        checker = AuditConfigChecker(self.root, self.root / "plans" / "pending" / "host-configuration-migration.inventory.json", tracked=[])
        report_a = checker.check(lot_id="LOT-A")
        self.assertEqual(report_a["hardcoded_files"], 1)
        report_b = checker.check(lot_id="LOT-B")
        self.assertEqual(report_b["hardcoded_files"], 0)

    def test_exit_code_based_on_hardcodes_not_disposition(self):
        (self.root / "tools" / "workflow" / "clean.py").write_text(
            'path = config.values["paths.work_root"]\n', encoding="utf-8"
        )
        files = [
            {"file": "tools/workflow/clean.py", "progress": {"status": "unreviewed"}},
        ]
        self._write_inventory(files)
        checker = AuditConfigChecker(self.root, self.root / "plans" / "pending" / "host-configuration-migration.inventory.json", tracked=[])
        report = checker.check()
        self.assertEqual(report["files_without_disposition"], 1)
        self.assertEqual(report["hardcoded_files"], 0)
