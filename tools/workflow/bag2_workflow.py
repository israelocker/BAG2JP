"""Local BAG2JP preflight and timed commands; full logs on disk, compact output."""
import argparse
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time
from types import MappingProxyType
from typing import Mapping

# Documented usage runs this file by path, so the repo root may be missing from sys.path.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.workflow import project_config

# Aliases keep the resolver patchable in tests; the class is read from its module so a
# reloaded registry still raises the exception type this module catches.
load_config = project_config.load_config
require_paths = project_config.require_paths


@dataclass(frozen=True)
class Settings:
    """Resolved host locations for this run; nothing here is a module-level literal."""

    repo: Path
    build: Path
    experimental: Path
    build_script: Path
    report_python: Path | None
    report_script: Path
    pins: Mapping[str, str]
    wsl_distribution: str
    work_root: Path
    configuration: project_config.ProjectConfig
    jobs: int


def resolve_settings(config: project_config.ProjectConfig) -> Settings:
    """Resolve the locations this workflow needs; missing keys fail by name."""
    build, experimental, build_script, work_root = require_paths(
        config, ("paths.build_root", "paths.experimental_install",
                 "tools.build_script", "paths.work_root"))
    for key in ("pins.psxrecomp", "pins.recomp_ui", "wsl.distribution", "build.jobs"):
        if key not in config.values:
            raise project_config.ConfigError(f"{key}: required workflow value is unresolved")
    pins = {"psxrecomp": config.values["pins.psxrecomp"],
            "recomp-ui": config.values["pins.recomp_ui"]}
    return Settings(
        repo=config.repo_root, build=build, experimental=experimental,
        build_script=build_script, report_python=config.values.get("tools.python_report"),
        report_script=config.repo_root / "tools/test/bag2_report.py",
        pins=MappingProxyType(pins), wsl_distribution=config.values["wsl.distribution"],
        work_root=work_root, configuration=config, jobs=config.values["build.jobs"])


def _literal_script_path(text: str) -> str:
    """Recognize one literal absolute shell path, never operators or expansions."""
    if text.startswith("'") and text.endswith("'") and "'" not in text[1:-1]:
        value = text[1:-1]
    elif (text.startswith('"') and text.endswith('"')
          and not any(symbol in text[1:-1] for symbol in ('"', '$', '`', '\\'))):
        value = text[1:-1]
    elif re.fullmatch(r"/[A-Za-z0-9_./+-]+", text):
        value = text
    else:
        raise ValueError("script path must be one literal absolute argument")
    if not value.startswith("/") or "\n" in value or "\r" in value:
        raise ValueError("script path must be one literal absolute argument")
    return value


def build_script_contract(settings: Settings) -> dict[str, object]:
    """Inspect the supported legacy fixed script without executing shell text.

    Unknown scripts are not assumed reconfigurable. This is a bounded compatibility
    adapter for the installed six-line script, not a general Bash interpreter.
    """
    result = {"script": str(settings.build_script), "compatible": False}
    try:
        raw = settings.build_script.read_bytes()
        result["sha256"] = hashlib.sha256(raw).hexdigest()
        lines = raw.decode("utf-8-sig").splitlines()
        if (len(lines) != 6 or lines[:2] != ["#!/usr/bin/env bash", "set -euo pipefail"]
                or lines[3] != 'export PATH="$toolchain/bin:$PATH"'
                or lines[4] != "command -v x86_64-w64-mingw32-windres"):
            raise ValueError("unsupported fixed build script format")
        if not lines[2].startswith("toolchain="):
            raise ValueError("unsupported toolchain assignment")
        toolchain = _literal_script_path(lines[2].split("=", 1)[1])
        command = re.fullmatch(r"cmake --build (.+) --target psx-runtime -j ([0-9]+)", lines[5])
        if command is None:
            raise ValueError("unsupported build invocation")
        result.update({"build_directory": _literal_script_path(command[1]), "jobs": int(command[2]),
                       "toolchain": toolchain})
        if result["build_directory"] != wsl_path(settings.build / "build-win-codex"):
            raise ValueError("fixed build script targets a different build root")
        if result["jobs"] != settings.jobs:
            raise ValueError("fixed build script jobs differ from build.jobs")
        result["compatible"] = True
    except (OSError, UnicodeError, ValueError) as exc:
        result["error"] = str(exc)
    return result


def command_for(settings: Settings, action: str, tag: str) -> list[str]:
    """Create only the selected action's argv, preserving its configuration overlay."""
    if action == "report":
        if settings.report_python is None:
            raise project_config.ConfigError("tools.python_report: required for report")
        command = [str(settings.report_python), str(settings.report_script),
                   "--tag", tag, "--timeout", "0"]
        local = settings.configuration.input_files["local"]
        if local is not None:
            command += ["--local-config", str(Path(local).resolve())]
        return command
    if action == "build":
        project_config.assert_write_target(settings.configuration, settings.build, role="build")
        project_config.assert_write_target(
            settings.configuration, settings.build / "build-win-codex", role="build")
        contract = build_script_contract(settings)
        if not contract["compatible"]:
            raise RuntimeError(f"Build blocked: {contract.get('error')}")
        script = settings.build_script
    elif action == "test-stage-select":
        script = settings.repo / "tools/test/stage_select/run.sh"
    else:
        raise ValueError(f"Unknown command action: {action}")
    return ["wsl.exe", "-d", settings.wsl_distribution, "--exec", "bash", wsl_path(script)]

def valid_tag(value):
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", value):
        raise argparse.ArgumentTypeError("tag: use 1-64 ASCII letters, digits, _ or -")
    return value

def wsl_path(path):
    return project_config.to_wsl_path(path.resolve())

def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def git(path, *args):
    result = subprocess.run(["git", "-C", str(path), *args], capture_output=True,
                            text=True, encoding="utf-8", errors="replace", timeout=30)
    if result.returncode:
        raise RuntimeError("Git check failed: " + str(path) + " " + " ".join(args))
    return result.stdout.rstrip("\r\n")

def source_summary(repo, build):
    same, different, unmapped = 0, [], 0
    for source in sorted((repo / "mods-src").rglob("*")):
        if not source.is_file() or source.suffix not in {".c", ".h", ".inc"}:
            continue
        if "_superseded" in source.relative_to(repo / "mods-src").parts:
            continue
        target = build / "src" / source.name
        if not target.is_file():
            unmapped += 1
        elif digest(source) == digest(target):
            same += 1
        else:
            different.append(source.relative_to(repo).as_posix())
    return {"matching": same, "different": different, "unmapped": unmapped}

def preflight(log, settings):
    repo, build = settings.repo, settings.build
    required = [repo / "NOTES.md", repo / "AGENTS.md", build / "CMakeLists.txt",
                build / "build-win-codex/CMakeCache.txt", settings.build_script,
                settings.experimental / "BAG2JP.exe", settings.experimental / "mods/bundled"]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise RuntimeError("Missing required paths: " + ", ".join(missing))
    cache = (build / "build-win-codex/CMakeCache.txt").read_text()
    if "CMAKE_HOME_DIRECTORY:INTERNAL=" + wsl_path(build) not in cache.splitlines():
        raise RuntimeError("CMake cache belongs to a different source tree")
    pins = {}
    for dependency, expected in settings.pins.items():
        actual = git(build / dependency, "rev-parse", "HEAD")
        if not actual.startswith(expected):
            raise RuntimeError("Unexpected dependency revision: " + dependency)
        pins[dependency] = actual[:12]
    built_exe = build / "build-win-codex/BAG2JP.exe"
    resource_drift = []
    package = Path("bag2jp.feature.bag1-content/1.0.0/popup_assets")
    for name in ("heat_bag1.png", "heat_bag2.png", "strike_bag1.png", "strike_bag2.png"):
        source = repo / "mods-src" / package / name
        for parent in (build / "mods/preloaded/packages", settings.experimental / "mods/bundled"):
            target = parent / package / name
            if not source.is_file() or not target.is_file() or digest(source) != digest(target):
                resource_drift.append(str(target))
    result = {"git_head": git(repo, "rev-parse", "--short", "HEAD"),
              "git_changes": git(repo, "status", "--short").splitlines(), "pins": pins,
              "sources": source_summary(repo, build), "resource_drift": resource_drift,
              "report_python_present": settings.report_python is not None and settings.report_python.is_file(),
              "fixed_build_contract": build_script_contract(settings),
              "built_exe_present": built_exe.is_file(),
              "deployed_exe_matches": built_exe.is_file()
              and digest(built_exe) == digest(settings.experimental / "BAG2JP.exe")}
    log.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result

def run_command(command, log, success_lines=2, summary_prefixes=None, cwd=None):
    with log.open("w", encoding="utf-8") as stream:
        child = subprocess.run(command, cwd=cwd or Path.cwd(), stdout=stream, stderr=subprocess.STDOUT)
    tail, summary = deque(maxlen=12), []
    with log.open(encoding="utf-8", errors="replace") as stream:
        for line in stream:
            line = line.rstrip()[:400]
            tail.append(line)
            if summary_prefixes and line.startswith(summary_prefixes) and len(summary) < 12:
                summary.append(line)
    if not child.returncode and summary_prefixes:
        return {"returncode": 0, "summary": summary}
    return {"returncode": child.returncode, "tail": list(tail) if child.returncode else list(tail)[-success_lines:]}

def run_phase(name, action, run_dir, records):
    started = time.perf_counter()
    record = {"phase": name, "status": "failed", "log": str(run_dir / (name + ".log"))}
    records.append(record)
    try:
        record["result"] = action(Path(record["log"]))
        if record["result"].get("returncode", 0):
            raise RuntimeError("Command failed; inspect its log")
        record["status"] = "passed"
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        record["error"] = str(exc)
        raise
    finally:
        record["seconds"] = round(time.perf_counter() - started, 3)

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", nargs="?", default="preflight",
                        choices=("preflight", "test-stage-select", "build", "report"))
    parser.add_argument("--tag", type=valid_tag, default="workflow")
    parser.add_argument("--local-config", type=Path, default=None,
                        help="local TOML overlay; relative selections anchor to the repository")
    args = parser.parse_args(argv)
    try:
        configuration = load_config(local_config=args.local_config)
        settings = resolve_settings(configuration)
        if args.action == "report" and settings.report_python is None:
            raise project_config.ConfigError("tools.python_report: required for report")
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        run_dir = project_config.assert_write_target(
            configuration, settings.work_root / "workflow" / (stamp + "-" + args.tag), role="work")
    except project_config.ConfigError as exc:
        print(f"config error: {exc}", file=sys.stderr)
        return 2
    run_dir.mkdir(parents=True, exist_ok=False)
    report = {"schema": 1, "action": args.action, "started_utc": stamp, "phases": [],
              "configuration": project_config.export_config(
                  configuration, operation="workflow-report" if args.action == "report" else "workflow")}
    exit_code = 0
    try:
        run_phase("preflight", lambda log: preflight(log, settings), run_dir, report["phases"])
        if args.action != "preflight":
            prefixes = ("state:", "phases:", "fever anims:", "run report:", "sheet:", "shots log:")
            run_phase(args.action, lambda log: run_command(command_for(settings, args.action, args.tag), log,
                      summary_prefixes=prefixes if args.action == "report" else None,
                      cwd=settings.repo), run_dir, report["phases"])
    except KeyboardInterrupt:
        exit_code = 130
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError):
        exit_code = 1
    finally:
        report["status"] = "failed" if exit_code else "passed"
        metrics = run_dir / "metrics.json"
        metrics.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps({**report, "metrics": str(metrics)}, ensure_ascii=True))
    return exit_code

if __name__ == "__main__":
    raise SystemExit(main())
