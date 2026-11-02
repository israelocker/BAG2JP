"""Behavioral checks for the read-only, stdlib documentation auditor."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class DocumentationAuditTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        tool = Path(__file__).with_name("audit_docs.py")
        spec = importlib.util.spec_from_file_location("audit_docs", tool)
        self.audit = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.audit)

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
        return path

    def test_inventory_excludes_generated_and_third_party_trees(self):
        for name in ("notes/current.md", "_work/log.md", "assets/readme.md",
                     "node_modules/lib/readme.md", ".git/info.md", "third_party/lib.md"):
            self.write(name, "# note\n")
        self.assertEqual(self.audit.inventory(self.root), ["notes/current.md"])

    def test_hidden_owned_documents_are_not_silently_excluded(self):
        self.write(".opencode/commands/help.md", "# Help\n")
        self.assertEqual(self.audit.inventory(self.root), [".opencode/commands/help.md"])

    def test_missing_local_link_is_reported(self):
        path = self.write("notes/a.md", "[missing](missing.md)\n")
        self.assertIn("missing-link", self.codes(path))

    def test_missing_literal_project_path_is_reported(self):
        path = self.write("a.md", "Use `tools/no_such_script.py`.\n")
        self.assertIn("missing-literal", self.codes(path))

    def test_ignored_evidence_path_is_warning_not_error(self):
        path = self.write("a.md", "[evidence](_work/old-run/result.json)\n")
        issues = self.audit.inspect_document(self.root, path)["issues"]
        self.assertEqual([i["severity"] for i in issues if i["code"] == "missing-link"], ["warning"])

    def test_historical_fences_do_not_block_active_docs(self):
        path = self.write("notes/archive/a.md", "```markdown\nold\n")
        issues = self.audit.inspect_document(self.root, path)["issues"]
        self.assertEqual([i["severity"] for i in issues if i["code"] == "unclosed-fence"], ["warning"])

    def test_check_fails_for_empty_inventory(self):
        tool = Path(__file__).with_name("audit_docs.py")
        result = subprocess.run([sys.executable, str(tool), "check", "--root", str(self.root)],
                                capture_output=True)
        self.assertNotEqual(result.returncode, 0)

    def test_root_relative_related_paths_are_checked(self):
        path = self.write("notes/a.md", '---\nrelated: ["notes/missing.md"]\n---\n# A\n')
        self.assertIn("missing-related", self.codes(path))

    def test_relative_link_with_anchor_resolves_file(self):
        self.write("notes/b.md", "# B\n")
        path = self.write("notes/a.md", "[B](b.md#b)\n")
        self.assertNotIn("missing-link", self.codes(path))

    def test_relative_link_does_not_fall_back_to_repo_root(self):
        self.write("NOTES.md", "# Index\n")
        path = self.write("notes/a.md", "[wrong](NOTES.md)\n")
        self.assertIn("missing-link", self.codes(path))

    def test_explicit_repo_root_link_resolves_from_repo(self):
        self.write("NOTES.md", "# Index\n")
        path = self.write("notes/a.md", "[root](/NOTES.md)\n")
        self.assertNotIn("missing-link", self.codes(path))

    def test_digest_requires_source_hash(self):
        self.write("source.md", "# Source\n")
        path = self.write("digest.md", '---\ndoc_kind: digest\nsource: "source.md"\n---\n')
        self.assertIn("digest-provenance", self.codes(path))

    def test_digest_requires_source_path(self):
        path = self.write("digest.md", '---\ndoc_kind: digest\nsource_sha256: "0000"\n---\n')
        self.assertIn("digest-provenance", self.codes(path))

    def test_required_metadata_cannot_be_empty(self):
        path = self.write("a.md", '---\nid:\ntitle:\ntags:\nsummary:\nrelated: []\ncreated:\nupdated:\n---\n')
        self.assertIn("metadata-value", self.codes(path))

    def test_tags_must_be_array_of_strings(self):
        path = self.write("a.md", '---\ntags: "not an array"\n---\n')
        self.assertIn("metadata-value", self.codes(path))

    def test_metadata_dates_must_be_real_dates(self):
        path = self.write("a.md", '---\ncreated: "2026-02-30"\n---\n')
        self.assertIn("metadata-value", self.codes(path))

    def test_missing_metadata_is_check_error_not_only_warning(self):
        path = self.write("a.md", "# No metadata\n")
        issues = self.audit.inspect_document(self.root, path)["issues"]
        self.assertEqual([i['severity'] for i in issues if i['code']=='metadata'], ['error'])

    def test_valid_metadata_passes_without_issues(self):
        path = self.write("a.md", '---\nid: valid\ntitle: "Title"\ntags: ["docs"]\nsummary: "Scope"\nrelated: []\ncreated: "2026-11-02"\nupdated: "2026-11-02"\n---\n# Valid\n')
        self.assertEqual(self.codes(path), [])

    def test_examples_inside_fences_are_not_links(self):
        path = self.write("a.md", "```markdown\n[x](missing.md)\n```\n")
        self.assertNotIn("missing-link", self.codes(path))

    def test_external_links_are_not_fetched(self):
        path = self.write("a.md", "[external](https://invalid.example/a)\n")
        self.assertNotIn("missing-link", self.codes(path))

    def test_globs_and_templates_are_not_missing_files(self):
        path = self.write("a.md", "[tests](tools/test/test_*.py)\n[x](<slug>.md)\n")
        self.assertNotIn("missing-link", self.codes(path))

    def test_fence_length_matters_for_nested_example(self):
        path = self.write("a.md", "````markdown\n```python\npass\n```\n````\n")
        self.assertNotIn("unclosed-fence", self.codes(path))

    def test_unclosed_fence_is_an_error(self):
        path = self.write("a.md", "```python\npass\n")
        self.assertIn("unclosed-fence", self.codes(path))

    def test_digest_hash_drift_is_reported(self):
        self.write("source.md", "# Changed\n")
        path = self.write("notes/digest.md", '---\nsource: "source.md"\nsource_sha256: "0000"\n---\n# Digest\n')
        self.assertIn("stale-digest", self.codes(path))

    def test_digest_source_cannot_escape_root(self):
        path = self.write("digest.md", '---\nsource: "../outside.md"\nsource_sha256: "0000"\n---\n')
        self.assertIn("source-outside-root", self.codes(path))

    def test_active_ids_are_unique_but_history_is_not_rewritten(self):
        self.write("a.md", '---\nid: same\n---\n# A\n')
        self.write("b.md", '---\nid: same\n---\n# B\n')
        self.write("notes/archive/old.md", '---\nid: same\n---\n# Old\n')
        self.assertEqual(self.audit.report(self.root)["duplicate_ids"], {"same": ["a.md", "b.md"]})

    def test_cli_refuses_to_overwrite_markdown_with_report(self):
        path = self.write("a.md", "# Keep\n")
        before = path.read_bytes()
        tool = Path(__file__).with_name("audit_docs.py")
        subprocess.run([sys.executable, str(tool), "inventory", "--root", str(self.root),
                        "--output", str(path)], capture_output=True)
        self.assertEqual(path.read_bytes(), before)

    def test_byte_count_is_utf8_not_character_count(self):
        self.write("a.md", "á\n")
        self.assertEqual(self.audit.report(self.root)["total_bytes"], 3)

    def test_archival_text_is_not_certified_by_a_clean_check(self):
        self.write("notes/archive/a.md", "# Historical unverified assertion\n")
        self.assertEqual(self.audit.report(self.root)["documents"][0]["kind"], "historical")

    def test_checker_does_not_mutate_input(self):
        path = self.write("a.md", "[bad](missing.md)\n")
        before = path.read_bytes()
        self.audit.report(self.root)
        self.assertEqual(path.read_bytes(), before)

    def test_cli_missing_root_is_failure(self):
        tool = Path(__file__).with_name("audit_docs.py")
        result = subprocess.run([sys.executable, str(tool), "check", "--root",
                                 str(self.root / "missing")], capture_output=True)
        self.assertNotEqual(result.returncode, 0)

    def test_cli_check_fails_for_broken_link(self):
        self.write("a.md", "[bad](missing.md)\n")
        tool = Path(__file__).with_name("audit_docs.py")
        result = subprocess.run([sys.executable, str(tool), "check", "--root", str(self.root)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)

    def codes(self, path):
        return [item["code"] for item in self.audit.inspect_document(self.root, path)["issues"]]


if __name__ == "__main__":
    unittest.main()
