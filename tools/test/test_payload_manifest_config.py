"""Config-driven payload manifest checker on disposable packages, never real installs."""

from contextlib import redirect_stderr, redirect_stdout
import hashlib
import importlib
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from tools.bag1import import check_payload_manifest as checker
from tools.workflow import project_config as config


REPO = Path(__file__).resolve().parents[2]
PACKAGE = "bag2jp.feature.bag1-content/1.0.0"


def write_package(root: Path, *, corrupt: bool = False,
                  missing_payload: bool = False) -> Path:
    package = root / PACKAGE
    (package / "payload").mkdir(parents=True, exist_ok=True)
    data = b"alt-payload"
    if not missing_payload:
        (package / "payload/bag1_alt.bin").write_bytes(data)
    digest = hashlib.sha256(b"different" if corrupt else data).hexdigest()
    (package / "manifest.toml").write_text(
        '[[overlay]]\nfile = "payload/bag1_alt.bin"\n'
        f'sha256 = "{digest}"\n', encoding="utf-8", newline="\n")
    return package


class PilotFixture(unittest.TestCase):
    def setUp(self):
        parent = REPO / "_work"
        parent.mkdir(exist_ok=True)
        temporary = tempfile.TemporaryDirectory(prefix="payload-pilot-", dir=parent)
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        (self.root / "config").mkdir()
        self.common = self.root / "config/project.toml"
        self.common.write_text('schema_version = 1\n[paths]\nwork_root = "_work"\n',
                               encoding="utf-8", newline="\n")
        self.local = self.root / "config/project.local.toml"

    def write_local(self, text: str, name: str | None = None) -> Path:
        path = self.local if name is None else self.root / name
        path.write_text(text, encoding="utf-8", newline="\n")
        return path


class DefaultPackageTests(PilotFixture):
    def test_default_packages_derive_from_configured_roots(self):
        self.write_local('schema_version = 1\n[paths]\n'
                         'build_root = "build"\nexperimental_install = "exp"\n')
        cfg = config.load_config(repo_root=self.root, local_config=self.local)
        self.assertEqual(checker.default_packages(cfg), (
            self.root / "mods-src" / PACKAGE,
            self.root / "build/mods/preloaded/packages" / PACKAGE,
            self.root / "build/build-win-codex/mods/bundled" / PACKAGE,
            self.root / "exp/mods/bundled" / PACKAGE,
        ))

    def test_default_packages_require_only_their_roots(self):
        self.write_local('schema_version = 1\n[paths]\nwork_root = "w"\n')
        cfg = config.load_config(repo_root=self.root, local_config=self.local)
        with self.assertRaisesRegex(config.ConfigError, "paths.build_root"):
            checker.default_packages(cfg)
        self.write_local('schema_version = 1\n[paths]\nbuild_root = "b"\n')
        cfg = config.load_config(repo_root=self.root, local_config=self.local)
        with self.assertRaisesRegex(config.ConfigError, "paths.experimental_install"):
            checker.default_packages(cfg)


class MainUnitTests(PilotFixture):
    def run_main(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = checker.main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_explicit_packages_do_not_load_configuration(self):
        package = write_package(self.root)
        with mock.patch.object(checker, "load_config",
                               side_effect=AssertionError("configuration loaded")):
            code, out, _err = self.run_main(["--package", str(package)])
        self.assertEqual(code, 0, out)
        self.assertIn("OK   ", out)

    def test_invalid_configuration_fails_before_package_access(self):
        bad = self.write_local('[paths]\nnot_a_field = "x"\n', "bad.toml")
        with mock.patch.object(checker, "check",
                               side_effect=AssertionError("package accessed")):
            code, out, err = self.run_main(["--local-config", str(bad)])
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("config error", err)
        self.assertIn("not_a_field", err)

    def test_missing_default_roots_are_not_synthesized(self):
        local = self.write_local('schema_version = 1\n[paths]\nwork_root = "w"\n')
        with mock.patch.object(checker, "check",
                               side_effect=AssertionError("package accessed")):
            code, out, err = self.run_main(["--local-config", str(local)])
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("paths.build_root", err)

    def test_sandbox_ok_fail_summary_and_exit_codes(self):
        good = write_package(self.root / "one")
        corrupt = write_package(self.root / "two", corrupt=True)
        missing = write_package(self.root / "three", missing_payload=True)
        code, out, _err = self.run_main(["--package", str(good), "--package", str(corrupt),
                                         "--package", str(missing)])
        lines = out.strip().splitlines()
        self.assertEqual(code, 1)
        self.assertEqual(len(lines), 4)
        self.assertTrue(lines[0].startswith("OK   ") and lines[0].endswith(":: " + hashlib.sha256(b"alt-payload").hexdigest()))
        self.assertTrue(lines[1].startswith("FAIL ") and "sha256" in lines[1])
        self.assertTrue(lines[2].startswith("FAIL ") and "missing manifest or payload" in lines[2])
        self.assertEqual(lines[3], "1/3 copies match their manifest")
        code, out, _err = self.run_main(["--package", str(good)])
        self.assertEqual(code, 0)
        self.assertIn("1/1 copies match their manifest", out)

    def test_malformed_manifest_fails_only_its_own_copy(self):
        good = write_package(self.root / "good")
        broken = write_package(self.root / "broken")
        (broken / "manifest.toml").write_text('[[overlay]\nfile = "x"\n', encoding="utf-8")
        code, out, err = self.run_main(["--package", str(broken), "--package", str(good)])
        lines = out.strip().splitlines()
        self.assertEqual(code, 1, err)
        self.assertEqual(len(lines), 3)
        self.assertTrue(lines[0].startswith("FAIL ") and "invalid manifest or payload" in lines[0])
        self.assertTrue(lines[1].startswith("OK   "), lines[1])
        self.assertEqual(lines[2], "1/2 copies match their manifest")

    def test_defaults_use_the_loaded_configuration(self):
        self.write_local('schema_version = 1\n[paths]\n'
                         'build_root = "build"\nexperimental_install = "exp"\n')
        for relative in ("mods-src", "build/mods/preloaded/packages",
                         "build/build-win-codex/mods/bundled", "exp/mods/bundled"):
            (self.root / relative / PACKAGE).mkdir(parents=True, exist_ok=True)
        cfg = config.load_config(repo_root=self.root, local_config=self.local)
        with mock.patch.object(checker, "load_config", return_value=cfg) as used:
            code, out, _err = self.run_main([])
        used.assert_called_once()
        self.assertEqual(code, 1)  # empty packages: still one FAIL line per copy
        self.assertIn(str(self.root / "build/mods/preloaded/packages" / PACKAGE), out)
        self.assertIn("0/4 copies match their manifest", out)

    def test_cli_syntax_error_remains_exit_two(self):
        with self.assertRaises(SystemExit) as caught, redirect_stderr(io.StringIO()):
            checker.main(["--not-a-flag"])
        self.assertEqual(caught.exception.code, 2)

    def test_import_does_not_load_or_cache_machine_paths(self):
        with mock.patch("pathlib.Path.read_bytes",
                        side_effect=AssertionError("configuration read at import time")):
            module = importlib.reload(checker)
        self.assertFalse(hasattr(module, "DEFAULT_PACKAGES"))
        self.assertFalse(hasattr(module, "REPO"))
        absolute = {name for name, value in vars(module).items()
                    if isinstance(value, Path) and value.is_absolute()}
        self.assertEqual(sorted(absolute), [])


class CliTests(PilotFixture):
    def run_cli(self, *arguments, cwd):
        environment = dict(os.environ, PYTHONPATH=str(REPO))
        result = subprocess.run(
            [sys.executable, "-m", "tools.bag1import.check_payload_manifest", *arguments],
            cwd=cwd, env=environment, capture_output=True, timeout=120)
        return subprocess.CompletedProcess(result.args, result.returncode,
                                           result.stdout.decode("utf-8", "replace"),
                                           result.stderr.decode("utf-8", "replace"))

    def packages_from(self, stdout: str) -> list[str]:
        return [line.split(" :: ", 1)[0].split(None, 1)[1]
                for line in stdout.strip().splitlines() if " :: " in line]

    def test_documented_script_invocation_still_works(self):
        package = write_package(self.root / "script-run")
        with tempfile.TemporaryDirectory(prefix="script-cwd-", dir=REPO / "_work") as cwd:
            result = subprocess.run(
                [sys.executable, str(REPO / "tools/bag1import/check_payload_manifest.py"),
                 "--package", str(package)],
                cwd=cwd, capture_output=True, timeout=120)
        stdout = result.stdout.decode("utf-8", "replace")
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
        self.assertIn("OK   ", stdout)
        self.assertIn("1/1 copies match their manifest", stdout)

    def test_relative_package_path_uses_the_working_directory(self):
        write_package(self.root / "rel")
        result = self.run_cli("--package", f"rel/{PACKAGE}", cwd=self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("1/1 copies match their manifest", result.stdout)

    def test_invalid_config_exits_two_without_stdout(self):
        bad = self.write_local('schema_version = 9\n', "bad-cli.toml")
        result = self.run_cli("--local-config", str(bad), cwd=self.root)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("config error", result.stderr)
        self.assertIn("schema_version", result.stderr)

    def test_two_runs_use_different_local_configs(self):
        first = self.write_local('schema_version = 1\n[paths]\n'
                                 'build_root = "build-a"\nexperimental_install = "exp-a"\n',
                                 "first.toml")
        second = self.write_local('schema_version = 1\n[paths]\n'
                                  'build_root = "build-b"\nexperimental_install = "exp-b"\n',
                                  "second.toml")
        with tempfile.TemporaryDirectory(prefix="other-cwd-", dir=REPO / "_work") as cwd:
            one = self.run_cli("--local-config", str(first), cwd=cwd)
            two = self.run_cli("--local-config", str(second), cwd=cwd)
        self.assertEqual(one.returncode, 1, one.stderr)
        self.assertEqual(two.returncode, 1, two.stderr)
        packages_one, packages_two = self.packages_from(one.stdout), self.packages_from(two.stdout)
        self.assertEqual(len(packages_one), 4)
        self.assertEqual(packages_one[0], str(REPO / "mods-src" / PACKAGE))
        self.assertEqual(packages_one[1], str(REPO / "build-a/mods/preloaded/packages" / PACKAGE))
        self.assertEqual(packages_one[3], str(REPO / "exp-a/mods/bundled" / PACKAGE))
        self.assertEqual(packages_two[1], str(REPO / "build-b/mods/preloaded/packages" / PACKAGE))
        self.assertEqual(packages_two[3], str(REPO / "exp-b/mods/bundled" / PACKAGE))
        self.assertRegex(one.stdout, r"(?m)^\d/4 copies match their manifest\r?$")


if __name__ == "__main__":
    unittest.main()
