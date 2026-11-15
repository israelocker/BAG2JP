"""Host configuration regressions on owned disposable trees, never game files."""

from contextlib import contextmanager
import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from unittest import mock

from tools.workflow import project_config as config


REPO = Path(__file__).resolve().parents[2]
COMMON = '''schema_version = 1
[paths]
work_root = "_work"
[build]
jobs = 2
[pins]
psxrecomp = "1a3fc0db"
recomp_ui = "3f1d6f1"
[wsl]
distribution = "Ubuntu"
'''


@contextmanager
def working_directory(path: Path):
    """Temporarily change only this test process's CWD."""
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


class ConfigFixture(unittest.TestCase):
    """Create a different repository root for each test."""

    def setUp(self):
        parent = REPO / "_work"
        parent.mkdir(exist_ok=True)
        temporary = tempfile.TemporaryDirectory(prefix="host-config-", dir=parent)
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        (self.root / "config").mkdir()
        self.common = self.root / "config/project.toml"
        self.common.write_text(COMMON, encoding="utf-8", newline="\n")
        self.local = self.root / "config/project.local.toml"

    def write_local(self, text: str) -> None:
        self.local.write_text(text, encoding="utf-8", newline="\n")

    def load(self, **kwargs):
        return config.load_config(repo_root=self.root, **kwargs)

    def assert_config_error(self, fragment: str) -> None:
        with self.assertRaisesRegex(config.ConfigError, fragment):
            self.load()


class ResolverTests(ConfigFixture):
    def test_local_overlay_preserves_other_common_keys(self):
        self.write_local('[paths]\nbuild_root = "build space"\n')
        result = self.load()
        self.assertIn("paths.build_root", result.values)
        self.assertEqual(result.values["paths.build_root"], self.root / "build space")
        self.assertEqual(result.values["paths.work_root"], self.root / "_work")
        self.assertEqual(result.values["build.jobs"], 2)
        self.assertEqual(result.values["pins.recomp_ui"], "3f1d6f1")
        self.assertEqual(result.origins["paths.build_root"], "local")

    def test_policy_cannot_be_overridden_locally(self):
        for text, field in [('[build]\njobs = 2\n', 'build.jobs'),
                            ('[pins]\npsxrecomp = "aaaaaaa"\n', 'pins.psxrecomp')]:
            with self.subTest(field=field):
                self.write_local(text)
                self.assert_config_error(field)

    def test_wrong_schema_and_unknown_key(self):
        for text in ('schema_version = 2\n', '[paths]\nbuid_root = "wrong"\n',
                     '[unknown]\nkey = "wrong"\n'):
            with self.subTest(text=text):
                self.write_local(text)
                with self.assertRaises(config.ConfigError):
                    self.load()

    def test_bool_is_not_build_jobs(self):
        self.common.write_text(COMMON.replace('jobs = 2', 'jobs = true'), encoding="utf-8")
        self.assert_config_error("build.jobs")

    def test_bool_is_not_schema_version(self):
        self.common.write_text(COMMON.replace('schema_version = 1', 'schema_version = true'), encoding="utf-8")
        self.assert_config_error("schema_version")

    def test_common_requires_schema_version(self):
        self.common.write_text(COMMON.replace('schema_version = 1\n', ''), encoding="utf-8")
        self.assert_config_error("schema_version")

    def test_path_literal_nul_rejected(self):
        self.write_local('[paths]\nbuild_root = "bad\\u0000path"\n')
        self.assert_config_error("paths.build_root")

    def test_partial_config_and_missing_local(self):
        result = self.load()
        self.assertIn("paths.work_root", result.values)
        self.assertNotIn("inputs.bag1_jp_disc", result.values)
        self.assertIsNone(result.input_hashes["local"])
        with self.assertRaisesRegex(config.ConfigError, "inputs.bag1_jp_disc"):
            config.require_paths(result, ("inputs.bag1_jp_disc",))

    def test_relative_paths_ignore_cwd(self):
        self.write_local('[paths]\nbuild_root = "build"\n')
        with working_directory(self.root / "config"):
            result = self.load()
        self.assertIn("paths.build_root", result.values)
        self.assertEqual(result.values["paths.build_root"], self.root / "build")

    def test_loaded_mappings_are_immutable(self):
        result = self.load()
        with self.assertRaises(TypeError):
            result.values["build.jobs"] = 12
        with self.assertRaises(TypeError):
            result.origins["bad"] = "local"
        with self.assertRaises(TypeError):
            result.input_hashes["common"] = "bad"

    def test_load_does_not_create_dirs_or_processes(self):
        self.write_local('[paths]\nbuild_root = "does-not-exist"\n')
        before = sorted(p.relative_to(self.root).as_posix() for p in self.root.rglob("*"))
        with mock.patch("subprocess.run", side_effect=AssertionError("process started")):
            result = self.load()
        self.assertIn("paths.build_root", result.values)
        self.assertEqual(before, sorted(p.relative_to(self.root).as_posix() for p in self.root.rglob("*")))

    def test_input_hashes_identify_common_local_and_schema(self):
        # BOM plus CRLF makes raw bytes distinct from decoded text.
        self.local.write_bytes(b'\xef\xbb\xbfschema_version = 1\r\n[paths]\r\nbuild_root = "bom"\r\n')
        result = self.load()
        for key, path in (("common", self.common), ("local", self.local),
                          ("schema", Path(config.__file__))):
            self.assertIn(key, result.input_hashes)
            self.assertEqual(result.input_hashes[key], hashlib.sha256(path.read_bytes()).hexdigest())

    def test_explicit_missing_local_does_not_fall_back(self):
        self.write_local('[paths]\nbuild_root = "default"\n')
        with self.assertRaisesRegex(config.ConfigError, r"local: cannot read or parse"):
            self.load(local_config=self.root / "absent.toml")

    def test_explicit_local_path_is_resolved_from_repo(self):
        other = self.root / "alternate.toml"
        other.write_text('[paths]\nbuild_root = "alternate"\n', encoding="utf-8")
        result = self.load(local_config=Path("alternate.toml"))
        self.assertIn("paths.build_root", result.values)
        self.assertEqual(result.values["paths.build_root"], self.root / "alternate")

    def test_missing_common_is_not_synthesized(self):
        self.common.unlink()
        self.assert_config_error("common")

    def test_malformed_toml_reports_config_error(self):
        self.write_local('[paths\n')
        self.assert_config_error("local")

    def test_wrong_types_and_empty_paths_are_rejected(self):
        for value in ('true', '123', '[]', '""'):
            with self.subTest(value=value):
                self.write_local(f'[paths]\nbuild_root = {value}\n')
                self.assert_config_error("paths.build_root")

    def test_nested_unknown_fields_are_rejected(self):
        self.write_local('[paths.build_root]\ninner = "wrong"\n')
        self.assert_config_error("paths.build_root")

    def test_derived_repo_root_cannot_be_set_in_file(self):
        self.write_local('repo_root = "other"\n')
        self.assert_config_error("repo_root")

    def test_existing_paths_are_returned_as_paths_without_environment_expansion(self):
        self.write_local('[paths]\nbuild_root = "%NOT_EXPANDED%"\n')
        result = self.load()
        self.assertIn("paths.build_root", result.values)
        self.assertIsInstance(result.values["paths.build_root"], Path)
        self.assertEqual(result.values["paths.build_root"], self.root / "%NOT_EXPANDED%")


class AdapterTests(ConfigFixture):
    """Path containment, overlap and portability without touching real installs."""

    def setUp(self):
        super().setUp()
        self.write_local(
            'schema_version = 1\n'
            '[paths]\nwork_root = "work"\nbuild_root = "build"\n'
            'experimental_install = "exp"\nstable_install = "stable"\n'
            'tools_root = "tools"\n')
        for name in ("work", "build", "exp", "stable", "tools"):
            (self.root / name).mkdir()

    def test_stable_and_ancestor_overlap_are_not_writable(self):
        cfg = self.load()
        for target in (self.root / "stable", self.root / "stable/BAG2JP.exe"):
            with self.subTest(target=target.name), self.assertRaises(config.ConfigError):
                config.assert_write_target(cfg, target, role="experimental")
        self.write_local(
            'schema_version = 1\n[paths]\nwork_root = "work"\n'
            'stable_install = "work/stable"\nbuild_root = "build"\n'
            'experimental_install = "exp"\n')
        (self.root / "work/stable").mkdir(exist_ok=True)
        nested = self.load()
        with self.assertRaises(config.ConfigError):
            config.assert_write_target(nested, self.root / "work", role="work")

    def test_role_root_inside_stable_is_not_writable(self):
        # The role root lives under the stable tree, so only the stable-overlap guard
        # (not role-root containment) can reject this target.
        self.write_local(
            'schema_version = 1\n[paths]\nwork_root = "work"\nbuild_root = "build"\n'
            'stable_install = "stable"\nexperimental_install = "stable/exp"\n')
        (self.root / "stable/exp").mkdir(parents=True)
        cfg = self.load()
        with self.assertRaises(config.ConfigError):
            config.assert_write_target(cfg, self.root / "stable/exp/out", role="experimental")

    @unittest.skipUnless(os.name == "nt", "Windows case-insensitive semantics; unverified elsewhere")
    def test_windows_case_variant_of_stable_is_not_writable(self):
        self.write_local('schema_version = 1\n[paths]\nwork_root = "work"\n'
                         'stable_install = "work/stable"\n')
        (self.root / "work/stable").mkdir()
        cfg = self.load()
        with self.assertRaisesRegex(config.ConfigError, "protected stable"):
            config.assert_write_target(cfg, self.root / "work/STABLE/BAG2JP.exe", role="work")
        self.assertTrue(config._is_within(Path("D:/stable"), Path("d:/STABLE/file")))

    def test_stable_directory_alias_is_not_writable(self):
        cfg = self.load()
        link = self.root / "work/alias"
        if not _make_directory_alias(link, self.root / "stable"):
            self.skipTest("directory symlink/junction unavailable: alias check unverified")
        with self.assertRaises(config.ConfigError):
            config.assert_write_target(cfg, link / "BAG2JP.exe", role="work")
        # A stable tree inside the role root is reachable physically; only the
        # stable-overlap guard catches this alias.
        self.write_local(
            'schema_version = 1\n[paths]\nwork_root = "work"\n'
            'stable_install = "work/stable"\nbuild_root = "build"\n'
            'experimental_install = "exp"\n')
        (self.root / "work/stable").mkdir(exist_ok=True)
        inner = self.root / "work/inner"
        if not _make_directory_alias(inner, self.root / "work/stable"):
            self.skipTest("second alias unavailable: overlap-via-alias unverified")
        inside = self.load()
        with self.assertRaises(config.ConfigError):
            config.assert_write_target(inside, inner / "BAG2JP.exe", role="work")

    def test_multiply_linked_files_are_not_writable_even_inside_the_role_root(self):
        cfg = self.load()
        source = self.root / "stable/settings.toml"
        source.write_bytes(b"protected fixture")
        target = self.root / "work/result.json"
        os.link(source, target)
        self.assertGreater(target.stat().st_nlink, 1)
        with self.assertRaisesRegex(config.ConfigError, "multiple hard links"):
            config.assert_write_target(cfg, target, role="work")
        self.assertEqual(source.read_bytes(), b"protected fixture")
        self.assertEqual(target.read_bytes(), b"protected fixture")
        unique = self.root / "work/unique.json"
        unique.write_bytes(b"owned")
        self.assertEqual(config.assert_write_target(cfg, unique, role="work"), unique)

    def test_target_outside_role_root_is_rejected(self):
        cfg = self.load()
        with self.assertRaises(config.ConfigError):
            config.assert_write_target(cfg, self.root / "build/out.txt", role="work")
        with self.assertRaises(config.ConfigError):
            config.assert_write_target(cfg, self.root / "work/../build/out.txt", role="work")

    def test_sibling_name_with_shared_prefix_is_outside(self):
        cfg = self.load()
        with self.assertRaises(config.ConfigError):
            config.assert_write_target(cfg, self.root / "work2/out.txt", role="work")

    def test_unit_root_containment_keeps_one_separator(self):
        self.assertTrue(config._is_within(Path("D:/"), Path("D:/")))
        self.assertTrue(config._is_within(Path("D:/"), Path("D:/x")))
        self.assertFalse(config._is_within(Path("D:/work"), Path("D:/work2/x")))

    def test_empty_nul_and_drive_relative_targets_are_rejected(self):
        cfg = self.load()
        for bad in (Path(""), Path("."), Path(".."), Path("bad\0path")):
            with self.subTest(bad=repr(str(bad))), self.assertRaises(config.ConfigError):
                config.assert_write_target(cfg, bad, role="work")
        if os.name == "nt":
            with self.assertRaises(config.ConfigError):
                config.assert_write_target(cfg, Path("D:relative"), role="work")

    def test_unknown_write_role_or_missing_protected_root(self):
        cfg = self.load()
        with self.assertRaises(config.ConfigError):
            config.assert_write_target(cfg, self.root / "exp/x", role="nonsense")
        self.write_local('schema_version = 1\n[paths]\nwork_root = "work"\n')
        partial = self.load()
        for role in ("work", "build", "experimental"):
            with self.subTest(role=role), self.assertRaises(config.ConfigError):
                config.assert_write_target(partial, self.root / "work/x", role=role)

    def test_nonexistent_child_uses_resolved_parent(self):
        cfg = self.load()
        checked = config.assert_write_target(cfg, Path("new/deep/file.txt"), role="work")
        self.assertEqual(checked, self.root / "work/new/deep/file.txt")
        self.assertFalse((self.root / "work/new").exists())

    @unittest.skipUnless(os.name == "nt", "Windows drive paths; unverified elsewhere")
    def test_windows_drive_to_wsl_spaces_unicode(self):
        self.assertEqual(config.to_wsl_path(Path("D:/Space ñ/one file")),
                         "/mnt/d/Space ñ/one file")
        self.assertEqual(config.to_wsl_path(Path("C:\\a\\b")), "/mnt/c/a/b")
        self.assertEqual(config.to_wsl_path(Path("E:/")), "/mnt/e")
        self.assertEqual(config.to_wsl_path(Path("D:/a/./b")), "/mnt/d/a/b")

    def test_unsupported_conversion_fails(self):
        for value in ("relative/path", "\\\\server\\share\\x", "\\\\?\\C:\\x", "D:", "D:foo",
                      "D:/a/../b", "D:/a\0b"):
            with self.subTest(value=value), self.assertRaises(config.ConfigError):
                config.to_wsl_path(Path(value))

    def test_json_keeps_sources_and_unresolved_fields(self):
        cfg = self.load()
        data = config.export_config(cfg, operation="inspect")
        json.dumps(data)
        self.assertEqual(data["schema_version"], 1)
        self.assertEqual(Path(data["repo_root"]), self.root)
        self.assertEqual(data["values"]["paths.work_root"], str(self.root / "work"))
        self.assertEqual(data["origins"]["paths.work_root"], "local")
        self.assertEqual(data["config"]["common"],
                         hashlib.sha256(self.common.read_bytes()).hexdigest())
        self.assertEqual(data["config"]["local"],
                         hashlib.sha256(self.local.read_bytes()).hexdigest())
        self.assertEqual(data["config"]["schema"],
                         hashlib.sha256(Path(config.__file__).read_bytes()).hexdigest())
        self.assertEqual(Path(data["files"]["common"]), self.common)
        self.assertEqual(Path(data["files"]["local"]), self.local)
        self.assertEqual(Path(data["files"]["schema"]), Path(config.__file__).resolve())
        self.assertIn("inputs.bag1_jp_disc", data["unresolved"])
        self.assertNotIn("schema_version", data["unresolved"])
        self.assertEqual(data["missing"], [])
        manifest = config.export_config(cfg, operation="payload-manifest")
        self.assertEqual(manifest["missing"], [])
        with self.assertRaises(config.ConfigError):
            config.export_config(cfg, operation="unknown")

    def test_missing_operation_roots_are_reported_not_substituted(self):
        self.write_local('schema_version = 1\n[paths]\nwork_root = "work"\n')
        cfg = self.load()
        data = config.export_config(cfg, operation="payload-manifest")
        self.assertEqual(data["missing"], ["paths.build_root", "paths.experimental_install"])
        self.assertEqual(config.export_config(cfg, operation="inspect")["missing"], [])
        self.assertNotIn("paths.build_root", data["values"])

    def test_two_loads_do_not_share_state(self):
        first = self.load()
        before = first.values["paths.work_root"]
        self.write_local('schema_version = 1\n[paths]\nwork_root = "elsewhere"\n')
        second = self.load()
        self.assertEqual(first.values["paths.work_root"], before)
        self.assertEqual(second.values["paths.work_root"], self.root / "elsewhere")
        self.assertIsNot(first.values, second.values)

    def test_import_does_not_read_configuration(self):
        watched = ("pathlib.Path.read_bytes", "pathlib.Path.read_text",
                   "builtins.open", "tomllib.load")
        patches = [mock.patch(name, side_effect=AssertionError(f"{name} used at import time"))
                   for name in watched]
        for patch in patches:
            patch.start()
        try:
            module = importlib.reload(config)
        finally:
            for patch in reversed(patches):
                patch.stop()
        self.assertTrue(module.FIELDS)
        self.assertEqual([name for name, value in vars(module).items()
                          if isinstance(value, module.ProjectConfig)], [])


class CliTests(ConfigFixture):
    """The CLI stays a data-only interface to the same resolver."""

    POWERSHELL = textwrap.dedent('''
        param([string]$ConfigJson, [string]$OutputJson)
        $cfg = Get-Content -LiteralPath $ConfigJson -Raw -Encoding UTF8 | ConvertFrom-Json
        [ordered]@{
          repo_root = $cfg.repo_root
          operation = $cfg.operation
          build_root = $cfg.values.'paths.build_root'
          common_hash = $cfg.config.common
          local_hash = $cfg.config.local
        } | ConvertTo-Json -Compress | Set-Content -LiteralPath $OutputJson -Encoding UTF8
    ''')

    def run_cli(self, *arguments, cwd=None):
        environment = dict(os.environ, PYTHONPATH=str(REPO))
        result = subprocess.run(
            [sys.executable, "-m", "tools.workflow.project_config", *arguments],
            cwd=cwd, env=environment, capture_output=True, timeout=120)
        # The CLI contract is UTF-8 bytes, independent of the console code page.
        return subprocess.CompletedProcess(
            result.args, result.returncode,
            result.stdout.decode("utf-8", "strict"),
            result.stderr.decode("utf-8", "replace"))

    def test_cli_json_is_cwd_independent_and_powershell_reads_it_as_data(self):
        self.write_local('schema_version = 1\n[paths]\nbuild_root = "build ñ ; & space"\n')
        with tempfile.TemporaryDirectory(prefix="other-cwd-", dir=REPO / "_work") as cwd:
            result = self.run_cli("--local-config", str(self.local), cwd=cwd)
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        expected_root = str(REPO / "build ñ ; & space")
        self.assertEqual(Path(data["repo_root"]), REPO)
        self.assertEqual(data["values"]["paths.build_root"], expected_root)
        self.assertEqual(data["operation"], "inspect")

        script = self.root / "read-config.ps1"
        script.write_text(self.POWERSHELL, encoding="utf-8", newline="\n")
        json_file = self.root / "config.json"
        json_file.write_text(result.stdout, encoding="utf-8", newline="\n")
        shells = [(name, found) for name, found in
                  (("pwsh", shutil.which("pwsh")),
                   ("windows-powershell", shutil.which("powershell"))) if found]
        if not shells:
            self.skipTest("PowerShell unavailable: JSON/PowerShell integration unverified")
        for name, shell in shells:
            with self.subTest(shell=name):
                output = self.root / f"read-back-{name}.json"
                consumed = subprocess.run(
                    [shell, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
                     "-File", str(script), "-ConfigJson", str(json_file),
                     "-OutputJson", str(output)],
                    capture_output=True, timeout=120)
                self.assertEqual(consumed.returncode, 0,
                                 consumed.stderr.decode("utf-8", "replace"))
                read_back = json.loads(output.read_text(encoding="utf-8-sig"))
                self.assertEqual(read_back["build_root"], expected_root)
                self.assertEqual(read_back["operation"], "inspect")
                self.assertEqual(read_back["common_hash"], data["config"]["common"])
                self.assertEqual(read_back["local_hash"], data["config"]["local"])
                self.assertEqual(read_back["repo_root"], str(REPO))

    def test_cli_reports_bad_config_without_stdout(self):
        self.write_local('[paths]\nnot_a_field = "x"\n')
        result = self.run_cli("--local-config", str(self.local))
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("config error", result.stderr)
        self.assertIn("not_a_field", result.stderr)

    def test_cli_export_does_not_create_or_touch_targets(self):
        self.write_local('schema_version = 1\n[paths]\nwork_root = "absent-work"\n')
        result = self.run_cli("--local-config", str(self.local),
                              "--operation", "payload-manifest")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertIn("paths.work_root", payload["values"])
        self.assertFalse((REPO / "absent-work").exists())
        self.assertIn("paths.build_root", payload["missing"])


def _make_directory_alias(link: Path, target: Path) -> bool:
    """Create a real directory alias when the platform permits it."""
    try:
        os.symlink(target, link, target_is_directory=True)
        return True
    except (OSError, NotImplementedError):
        pass
    if os.name == "nt":
        result = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)],
                                capture_output=True, text=True)
        return result.returncode == 0
    return False


class WorkflowOperationTests(ConfigFixture):
    def test_workflow_and_report_operations_declare_real_requirements(self):
        self.assertIn("workflow", config.OPERATIONS)
        self.assertIn("report", config.OPERATIONS)
        self.assertIn("report-audio", config.OPERATIONS)
        self.assertIn("report-sheet", config.OPERATIONS)
        self.assertIn("workflow", config.FIELDS["paths.work_root"].operations)
        self.assertIn("workflow", config.FIELDS["paths.stable_install"].operations)
        self.assertNotIn("workflow", config.FIELDS["tools.python_report"].operations)
        self.assertNotIn("report", config.FIELDS["tools.audio_probe"].operations)
        self.assertIn("report-audio", config.FIELDS["tools.audio_probe"].operations)
        self.assertIn("report-sheet", config.FIELDS["paths.stable_install"].operations)
        self.assertIn("workflow-report", config.FIELDS["tools.python_report"].operations)


class RequirementTests(ConfigFixture):
    def test_require_paths_rejects_non_path_unknown_and_unresolved_keys(self):
        cfg = self.load()
        with self.assertRaises(config.ConfigError):
            config.require_paths(cfg, ("build.jobs",))
        with self.assertRaises(config.ConfigError):
            config.require_paths(cfg, ("nope.key",))
        with self.assertRaises(config.ConfigError):
            config.require_paths(cfg, ("inputs.bag1_jp_disc",))
        self.assertEqual(config.require_paths(cfg, ("paths.work_root",)),
                         (self.root / "_work",))

    @unittest.skipUnless(os.name == "nt", "Windows drive-relative semantics; unverified elsewhere")
    def test_drive_relative_path_value_is_rejected(self):
        self.write_local('[paths]\nbuild_root = "D:relative"\n')
        self.assert_config_error("paths.build_root")


if __name__ == "__main__":
    unittest.main()
