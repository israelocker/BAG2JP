"""Host-only view adapters on relocated trees; never touch a real game or helpers."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[2]

# Every effectful PowerShell command is replaced, including directory creation.
HARNESS = r'''
param([string]$Wrapper,[string]$Arguments,[string]$Report)
$ErrorActionPreference='Stop'
$global:viewTestEvents=New-Object System.Collections.ArrayList
$global:viewTestPressed=$false
function Get-Process { param($Name,$Id,$ErrorAction)
 if ($Id) { return [pscustomobject]@{Path=$env:VIEW_TEST_EXE;Id=$Id;HasExited=$true} }
}
function Get-Date { param($Format)
 if($Format) { return '20400101-000000' }; return [datetime]::UtcNow
}
function New-Item { param($ItemType,$Path,[switch]$Force)
 [void]$global:viewTestEvents.Add(@{kind='mkdir';path=$Path})
}
function Copy-Item { param($Path,$Destination,$LiteralPath)
 $p=if($LiteralPath){$LiteralPath}else{$Path}
 [void]$global:viewTestEvents.Add(@{kind='copy';path=$p;destination=$Destination})
 if($env:VIEW_TEST_REAL_FILES -eq '1') { Microsoft.PowerShell.Management\Copy-Item @PSBoundParameters }
}
function Set-Content { param($Path,$LiteralPath,[Parameter(ValueFromPipeline)]$Value) process {
 [void]$global:viewTestEvents.Add(@{kind='write';path=$(if($LiteralPath){$LiteralPath}else{$Path});value=$Value})
} }
function Start-Sleep { param($Seconds,$Milliseconds) }
function Get-Content { param($Path,$LiteralPath,[switch]$Raw,$Tail)
 if($env:VIEW_TEST_REAL_FILES -eq '1') {
  [void]$global:viewTestEvents.Add(@{kind='read';literal=[bool]$LiteralPath})
  return Microsoft.PowerShell.Management\Get-Content @PSBoundParameters
 }
 $p=if($LiteralPath){$LiteralPath}else{$Path}
 if($p -eq $env:VIEW_TEST_CASES) { return '[{"index":0,"name":"idle"}]' }
 if($p -like '*charsel_popup.log') { return 'open: current 1' }
 if($p -like '*watch.log') {
  $root=if($global:viewTestStarted){$global:viewTestRootValue}elseif($global:viewTestPressed){7}else{12}
  return ('8005D3D4={0:X8} 80192028=00000004' -f $root)
 }
 return 'owned fixture log'
}
function Start-Process { param($FilePath,$WorkingDirectory,$ArgumentList,[switch]$PassThru)
 $global:viewTestStarted=$true
 $global:viewTestRootValue=7
 [void]$global:viewTestEvents.Add(@{kind='start';path=$FilePath;cwd=$WorkingDirectory;argv=$ArgumentList})
 return [pscustomobject]@{Id=42;HasExited=$true}
}
$global:viewTestAllowedRoot=[IO.Path]::GetDirectoryName($Report)+[IO.Path]::DirectorySeparatorChar
$global:viewTestPython=@(Get-Command py -CommandType Application)[0].Path
# Reject resolved external helpers before invocation, not after their side effects.
$ExecutionContext.InvokeCommand.PostCommandLookupAction={ param($sender,$lookup)
 if($lookup.Command -is [Management.Automation.ExternalScriptInfo] -or
    $lookup.Command -is [Management.Automation.ApplicationInfo]) {
  $path=[IO.Path]::GetFullPath($lookup.Command.Path)
  if(!$path.StartsWith($global:viewTestAllowedRoot,[StringComparison]::OrdinalIgnoreCase) -and
     $path -ne $global:viewTestPython) {
   $lookup.Command=$null
   $global:viewTestBlockedPath=$path
   $lookup.CommandScriptBlock={ throw ('Helper outside test fixture blocked: '+$global:viewTestBlockedPath) }
   $lookup.StopSearch=$true
  }
 }
}
$code=0;$message=''
try {
 $bound=@{};($Arguments | ConvertFrom-Json).psobject.Properties | ForEach-Object { $bound[$_.Name]=$_.Value }
 & $Wrapper @bound | Out-Null
} catch { $code=1;$message=$_.Exception.Message }
$ExecutionContext.InvokeCommand.PostCommandLookupAction=$null
[IO.File]::WriteAllText($Report,(@{code=$code;message=$message;events=@($global:viewTestEvents);
 encoding=[Console]::OutputEncoding.CodePage} | ConvertTo-Json -Depth 8),[Text.Encoding]::UTF8)
'''

HELPER = r'''
param($Id,$Ids,$Keys,$HoldMs,$GapMs,$Out,[switch]$Screen)
$kind=if($Out){'shot'}else{'key'}
[void]$global:viewTestEvents.Add(@{kind=$kind;id=$Id;ids=$Ids;keys=$Keys;hold=$HoldMs;gap=$GapMs;out=$Out;screen=[bool]$Screen;tool=$PSCommandPath})
if($Keys -contains 'X') { $global:viewTestPressed=$true }
if($Keys -contains 'S') { $global:viewTestPressed=$true }
if($global:viewTestStarted -and $Keys -contains 'S') {
 $global:viewTestRootValue=if($GapMs -eq 350){12}else{27}
}
'''


class ViewWrapperTests(unittest.TestCase):
    """Drive the actual PS entrypoints and the real resolver with harmless boundaries."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="view-config-", dir=REPO / "_work")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        for directory in ("config", "tools/test", "tools/workflow", "helpers ñ ; &", "elsewhere"):
            (self.root / directory).mkdir(parents=True)
        for name in ("bag2_endings_view.ps1", "bag2_endings_acceptance.ps1", "capture_dance_view.ps1",
                     "view_config.py", "view_config.ps1"):
            source = REPO / "tools/test" / name
            if source.exists():
                shutil.copy2(source, self.root / "tools/test" / name)
        shutil.copy2(REPO / "tools/workflow/project_config.py", self.root / "tools/workflow")
        shutil.copy2(REPO / "config/project.toml", self.root / "config")
        self.local = self.root / "config/selected.toml"
        self.write_local()
        for name in ("postkey.ps1", "winshot.ps1", "custom-key.ps1", "custom-shot.ps1"):
            (self.root / "helpers ñ ; &" / name).write_text(HELPER, encoding="utf-8", newline="\n")
        self.runner = self.root / "runner.ps1"
        self.runner.write_text(HARNESS, encoding="utf-8", newline="\n")
        self.exe = self.root / "experimental ñ ; &/BAG2JP.exe"
        self.shells = [shutil.which(name) for name in ("pwsh", "powershell")]
        self.assertTrue(all(self.shells), "Both PowerShell 7 and 5.1 are required for this Windows seam")

    def write_local(self, *, work="evidence ñ ; &", experimental="experimental ñ ; &", tools=True):
        text = (f'schema_version=1\n[paths]\nwork_root={json.dumps(work, ensure_ascii=False)}\n'
                f'experimental_install={json.dumps(experimental, ensure_ascii=False)}\nstable_install="stable"\n')
        if tools:
            text += '[tools]\nwinshot_root="helpers ñ ; &"\n'
        self.local.write_text(text, encoding="utf-8", newline="\n")

    def run_wrapper(self, name, arguments, *, exe=None, real_files=False):
        import os
        results = []
        for shell in self.shells:
            with self.subTest(shell=shell):
                if real_files:
                    for watch in self.root.glob("*/bag2jp_watch.log"):
                        watch.write_text("8005D3D4=0000000C 80192028=00000004", encoding="utf-8")
                report = self.root / "report.json"
                result = subprocess.run([shell, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
                    "-File", str(self.runner), "-Wrapper", str(self.root / "tools/test" / name),
                    "-Arguments", json.dumps(arguments, ensure_ascii=False), "-Report", str(report)],
                    cwd=self.root / "elsewhere", env=dict(os.environ, VIEW_TEST_EXE=str(exe or self.exe),
                    VIEW_TEST_CASES=str(self.root / "cases.json"), VIEW_TEST_REAL_FILES=str(int(real_files))), capture_output=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
                self.assertTrue(report.is_file())
                results.append(json.loads(report.read_text(encoding="utf-8-sig")))
        return results

    def view_args(self, **changes):
        return dict(GameId=42, Action="cancel", Tag="view-probe", LocalConfig=str(self.local), **changes)

    def dance_args(self, **changes):
        args = dict(GameId=42, ExpectedExe=str(self.exe), Cases=str(self.root / "cases.json"),
                    Output="dance-probe", CurrentIndex=0, ItemCount=3, LocalConfig=str(self.local))
        args.update(changes)
        return args

    def test_view_uses_effective_paths_and_preserves_key_arguments(self):
        for data in self.run_wrapper("bag2_endings_view.ps1", self.view_args()):
            self.assertEqual(data["code"], 0, data["message"])
            events = data["events"]
            self.assertEqual(Path(events[0]["path"]), self.root / "evidence ñ ; &/view-probe")
            key = next(e for e in events if e["kind"] == "key")
            self.assertEqual((key["id"], key["keys"], key["hold"], key["gap"]), (42, ["X"], 150, 350))
            self.assertEqual(Path(key["tool"]), self.root / "helpers ñ ; &/postkey.ps1")
            shot = next(e for e in events if e["kind"] == "shot")
            self.assertEqual(Path(shot["out"]), self.root / "evidence ñ ; &/view-probe/cancel-return.png")

    def test_view_wrong_identity_rejected_before_effects(self):
        for data in self.run_wrapper("bag2_endings_view.ps1", self.view_args(), exe=self.root / "other.exe"):
            self.assertNotEqual(data["code"], 0)
            self.assertIn("experimental", data["message"])
            self.assertEqual(data["events"], [])

    def test_view_escape_rejected_before_effects(self):
        args = self.view_args(); args["Tag"] = "../escape"
        for data in self.run_wrapper("bag2_endings_view.ps1", args):
            self.assertNotEqual(data["code"], 0)
            self.assertIn("configuration", data["message"].lower())
            self.assertEqual(data["events"], [])

    def test_missing_tools_and_stable_overlap_rejected_before_effects(self):
        for changes in ({"tools": False}, {"experimental": "stable"}, {"work": "stable"}):
            self.write_local(**changes)
            for data in self.run_wrapper("bag2_endings_view.ps1", self.view_args()):
                self.assertNotEqual(data["code"], 0)
                self.assertIn("configuration", data["message"].lower())
                self.assertEqual(data["events"], [])

    def test_explicit_helpers_do_not_require_tool_root(self):
        self.write_local(tools=False)
        args = self.dance_args(KeyTool=str(self.root / "helpers ñ ; &/custom-key.ps1"),
                               ShotTool=str(self.root / "helpers ñ ; &/custom-shot.ps1"))
        for data in self.run_wrapper("capture_dance_view.ps1", args):
            self.assertEqual(data["code"], 0, data["message"])

    def test_json_bridge_restores_native_output_encoding(self):
        original = self.runner.read_text(encoding="utf-8")
        self.runner.write_text(original.replace("$code=0;$message=''", "[Console]::OutputEncoding=[Text.Encoding]::GetEncoding(437)\n$code=0;$message=''"),
                               encoding="utf-8", newline="\n")
        for data in self.run_wrapper("bag2_endings_view.ps1", self.view_args()):
            self.assertEqual(data["code"], 0, data["message"])
            self.assertEqual(data["encoding"], 437)

    def test_child_rejects_changed_config_before_effects(self):
        args = self.view_args()
        args["ExpectedConfig"] = '{"common":"wrong","local":"wrong","schema":"wrong"}'
        for data in self.run_wrapper("bag2_endings_view.ps1", args):
            self.assertNotEqual(data["code"], 0)
            self.assertIn("changed", data["message"])
            self.assertEqual(data["events"], [])

    def test_dance_defaults_and_explicit_helper_precedence(self):
        for overrides in ({}, {"KeyTool": str(self.root / "helpers ñ ; &/custom-key.ps1"),
                               "ShotTool": str(self.root / "helpers ñ ; &/custom-shot.ps1")}):
            for data in self.run_wrapper("capture_dance_view.ps1", self.dance_args(**overrides)):
                self.assertEqual(data["code"], 0, data["message"])
                key = next(e for e in data["events"] if e["kind"] == "key")
                expected = overrides.get("KeyTool", str(self.root / "helpers ñ ; &/postkey.ps1"))
                self.assertEqual(key["tool"], expected)
                self.assertEqual((key["id"], key["keys"], key["hold"], key["gap"]), (42, "X", 70, 100))
                shots = [e for e in data["events"] if e["kind"] == "shot"]
                self.assertEqual(len(shots), 3)
                self.assertEqual(shots[0]["tool"], overrides.get("ShotTool", str(self.root / "helpers ñ ; &/winshot.ps1")))
                self.assertEqual(Path(shots[0]["out"]), self.root / "evidence ñ ; &/dance-probe/00-idle-0.png")
                self.assertTrue(shots[0]["screen"])

    def test_dance_escape_and_wrong_identity_before_effects(self):
        for args, exe in ((self.dance_args(Output="../escape"), self.exe),
                          (self.dance_args(), self.root / "other.exe")):
            for data in self.run_wrapper("capture_dance_view.ps1", args, exe=exe):
                self.assertNotEqual(data["code"], 0)
                self.assertEqual(data["events"], [])

    def test_dance_explicit_identity_and_existing_output_contract(self):
        native = self.root / "native-reference/BAG2JP.exe"
        for data in self.run_wrapper("capture_dance_view.ps1", self.dance_args(ExpectedExe=str(native)), exe=native):
            self.assertEqual(data["code"], 0, data["message"])
        existing = self.root / "evidence ñ ; &/preserved"
        existing.mkdir(parents=True)
        marker = existing / "keep.txt"
        marker.write_text("owner data", encoding="utf-8")
        for data in self.run_wrapper("capture_dance_view.ps1", self.dance_args(Output=str(existing))):
            self.assertNotEqual(data["code"], 0)
            self.assertIn("Preserve", data["message"])
            self.assertEqual(data["events"], [])
        self.assertEqual(marker.read_text(encoding="utf-8"), "owner data")

    def test_one_explicit_helper_still_requires_other_default(self):
        self.write_local(tools=False)
        for data in self.run_wrapper("capture_dance_view.ps1", self.dance_args(
                KeyTool=str(self.root / "helpers ñ ; &/custom-key.ps1"))):
            self.assertNotEqual(data["code"], 0)
            self.assertEqual(data["events"], [])
        import sys
        result = subprocess.run([sys.executable, str(self.root / "tools/test/view_config.py"),
            "--operation", "dance-capture", "--output", "probe", "--local-config", str(self.local),
            "--expected-exe", str(self.exe), "--key-tool", str(self.root / "custom.ps1")],
            cwd=self.root / "elsewhere", capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 2, result.stderr.decode("utf-8", "replace"))
        self.assertIn(b"tools.winshot_root", result.stderr)

    def test_acceptance_effective_destinations_and_child_overlay(self):
        # Child flow is tested above; here inspect the parent-to-child argv seam.
        child = self.root / "tools/test/bag2_endings_view.ps1"
        child.write_text('param($GameId,$Action,$Tag,$LocalConfig,$ExpectedConfig)\n'
            '[void]$global:viewTestEvents.Add(@{kind="child";id=$GameId;action=$Action;tag=$Tag;local=$LocalConfig;config=$ExpectedConfig})\n',
            encoding="utf-8", newline="\n")
        for data in self.run_wrapper("bag2_endings_acceptance.ps1", dict(Mode="HeatBag1", Tag="accept-probe",
                                  ObserveSeconds=17, LocalConfig=str(self.local))):
            self.assertEqual(data["code"], 0, data["message"])
            events = data["events"]
            self.assertEqual(Path(events[0]["path"]).parent.parent, self.root / "evidence ñ ; &")
            start = next(e for e in events if e["kind"] == "start")
            self.assertEqual(Path(start["path"]), self.exe)
            self.assertEqual(Path(start["cwd"]), self.exe.parent)
            self.assertEqual(start["argv"], "--no-launcher")
            call = next(e for e in events if e["kind"] == "child")
            self.assertEqual((call["id"], call["action"], call["local"]), (42, "selector", str(self.local)))
            self.assertEqual(Path(call["tag"]), Path(events[0]["path"]).parent)
            contract = json.loads(call["config"])
            self.assertEqual(set(contract), {"common", "local", "schema", "files", "effective"})
            self.assertEqual(Path(contract["files"]["local"]), self.local)
            self.assertEqual(Path(contract["effective"]["output"]), Path(call["tag"]))

    def test_relative_helper_overrides_keep_execution_identity(self):
        for name in ("custom-key.ps1", "custom-shot.ps1"):
            (self.root / "elsewhere" / name).write_text(HELPER, encoding="utf-8", newline="\n")
        for data in self.run_wrapper("capture_dance_view.ps1", self.dance_args(
                KeyTool=r".\custom-key.ps1", ShotTool=r".\custom-shot.ps1")):
            self.assertEqual(data["code"], 0, data["message"])
            self.assertEqual(Path(next(e for e in data["events"] if e["kind"] == "key")["tool"]),
                             self.root / "elsewhere/custom-key.ps1")

    def test_acceptance_existing_output_refused_before_effects(self):
        out = self.root / "evidence ñ ; &/accept-probe-20400101-000000"
        (out / "backups").mkdir(parents=True)
        marker = out / "backups/keep.txt"
        marker.write_text("owner data", encoding="utf-8")
        for data in self.run_wrapper("bag2_endings_acceptance.ps1", dict(Mode="HeatBag1", Tag="accept-probe", LocalConfig=str(self.local))):
            self.assertNotEqual(data["code"], 0)
            self.assertIn("configuration", data["message"].lower())
            self.assertEqual(data["events"], [])
        import sys
        result = subprocess.run([sys.executable, str(self.root / "tools/test/view_config.py"),
            "--operation", "endings-acceptance", "--output", str(out), "--local-config", str(self.local)],
            capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 2)
        self.assertIn(b"existing acceptance output", result.stderr)
        self.assertEqual(marker.read_text(encoding="utf-8"), "owner data")

    def test_invalid_index_address_rejected_before_effects(self):
        for data in self.run_wrapper("capture_dance_view.ps1", self.dance_args(IndexAddress="INVALID")):
            self.assertNotEqual(data["code"], 0)
            self.assertEqual(data["events"], [])

    def test_literal_bracket_paths_use_real_provider_sources(self):
        self.write_local(experimental="[exp]")
        self.exe = self.root / "[exp]/BAG2JP.exe"
        out = self.root / "evidence ñ ; &/view-probe"
        out.mkdir(parents=True)
        for name, text in (("[exp]", "literal"), ("e", "decoy")):
            game = self.root / name
            game.mkdir()
            (game / "bag2jp_watch.log").write_text("8005D3D4=0000000C 80192028=00000004", encoding="utf-8")
            (game / "bag2jp_endings_view.log").write_text(text, encoding="utf-8")
        helper = HELPER + '\nif($Keys -contains "X") {\n' + '\n'.join(
            '[IO.File]::WriteAllText(\'' + str(self.root / name / "bag2jp_watch.log").replace("'", "''") +
            "','8005D3D4=00000007 80192028=00000004')" for name in ("[exp]", "e")) + '\n}\n'
        (self.root / "helpers ñ ; &/postkey.ps1").write_text(helper, encoding="utf-8", newline="\n")
        for data in self.run_wrapper("bag2_endings_view.ps1", self.view_args(), real_files=True):
            self.assertEqual(data["code"], 0, data["message"])
            self.assertTrue(all(e["literal"] for e in data["events"] if e["kind"] == "read"))
        self.assertEqual((out / "cancel-plugin.log").read_text(encoding="utf-8"), "literal")

    def test_acceptance_real_child_checks_actual_contract(self):
        for data in self.run_wrapper("bag2_endings_acceptance.ps1", dict(Mode="HeatBag1", Tag="integrated",
                                  ObserveSeconds=17, LocalConfig=str(self.local))):
            self.assertEqual(data["code"], 0, data["message"])
            copies = [e for e in data["events"] if e["kind"] == "copy"]
            self.assertTrue(any(Path(e["destination"]).name == "selector-plugin.log" for e in copies))

    def test_child_rejects_same_bytes_different_selection_or_destination(self):
        import sys
        result = subprocess.run([sys.executable, str(self.root / "tools/test/view_config.py"),
            "--operation", "endings-view", "--output", "view-probe", "--local-config", str(self.local)],
            capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0)
        current = json.loads(result.stdout)
        expected = dict(current["config"], files=current["files"], effective=current["effective"])
        other = self.local.with_name("same-bytes.toml")
        other.write_bytes(self.local.read_bytes())
        for changes in ({"Tag": "other-output"}, {"LocalConfig": str(other)}):
            args = self.view_args()
            args.update(changes, ExpectedConfig=json.dumps(expected))
            for data in self.run_wrapper("bag2_endings_view.ps1", args):
                self.assertNotEqual(data["code"], 0)
                self.assertIn("changed", data["message"])
                self.assertEqual(data["events"], [])

    def test_harness_blocks_helpers_outside_fixture_before_execution(self):
        with tempfile.TemporaryDirectory(prefix="outside-helper-", dir=REPO / "_work") as outside:
            helper = Path(outside) / "sentinel.ps1"
            helper.write_text("throw 'OUTSIDE EXECUTED'", encoding="utf-8")
            for data in self.run_wrapper("capture_dance_view.ps1", self.dance_args(KeyTool=str(helper))):
                self.assertNotEqual(data["code"], 0)
                self.assertIn("outside test fixture blocked", data["message"])


if __name__ == "__main__":
    unittest.main()
