"""Local BAG2JP preflight and timed commands; full logs on disk, compact output."""
import argparse
from collections import deque
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time

REPO = Path(__file__).resolve().parents[2]
BUILD = REPO.parent / "BAG2JP-codex-build/BAG2JP"
EXPERIMENTAL = Path(r"D:\Games\Bust A Groove 2 (Japan)\BAG2JP-exp-8mb")
BUILD_SCRIPT = REPO.parents[1] / "Tools/codex-integrations/build_bag2jp.sh"
REPORT_PYTHON = Path.home() / "AppData/Local/Microsoft/WindowsApps/PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0/python.exe"
PINS = {"psxrecomp": "1a3fc0db", "recomp-ui": "3f1d6f1"}

def valid_tag(value):
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", value):
        raise argparse.ArgumentTypeError("tag: use 1-64 ASCII letters, digits, _ or -")
    return value

def wsl_path(path):
    resolved = path.resolve()
    if not resolved.drive or len(resolved.drive) != 2:
        raise ValueError("Expected a local Windows drive path")
    return "/mnt/" + resolved.drive[0].lower() + resolved.as_posix()[2:]

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

def preflight(log):
    required = [REPO / "NOTES.md", REPO / "AGENTS.md", BUILD / "CMakeLists.txt",
                BUILD / "build-win-codex/CMakeCache.txt", BUILD_SCRIPT,
                EXPERIMENTAL / "BAG2JP.exe", EXPERIMENTAL / "mods/bundled"]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise RuntimeError("Missing required paths: " + ", ".join(missing))
    cache = (BUILD / "build-win-codex/CMakeCache.txt").read_text()
    if "CMAKE_HOME_DIRECTORY:INTERNAL=" + wsl_path(BUILD) not in cache.splitlines():
        raise RuntimeError("CMake cache belongs to a different source tree")
    pins = {}
    for dependency, expected in PINS.items():
        actual = git(BUILD / dependency, "rev-parse", "HEAD")
        if not actual.startswith(expected):
            raise RuntimeError("Unexpected dependency revision: " + dependency)
        pins[dependency] = actual[:12]
    built_exe = BUILD / "build-win-codex/BAG2JP.exe"
    resource_drift = []
    package = Path("bag2jp.feature.bag1-content/1.0.0/popup_assets")
    for name in ("heat_bag1.png", "heat_bag2.png", "strike_bag1.png", "strike_bag2.png"):
        source = REPO / "mods-src" / package / name
        for parent in (BUILD / "mods/preloaded/packages", EXPERIMENTAL / "mods/bundled"):
            target = parent / package / name
            if not source.is_file() or not target.is_file() or digest(source) != digest(target):
                resource_drift.append(str(target))
    result = {"git_head": git(REPO, "rev-parse", "--short", "HEAD"),
              "git_changes": git(REPO, "status", "--short").splitlines(), "pins": pins,
              "sources": source_summary(REPO, BUILD), "resource_drift": resource_drift,
              "report_python_present": REPORT_PYTHON.is_file(), "built_exe_present": built_exe.is_file(),
              "deployed_exe_matches": built_exe.is_file() and digest(built_exe) == digest(EXPERIMENTAL / "BAG2JP.exe")}
    log.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result

def run_command(command, log, success_lines=2, summary_prefixes=None):
    with log.open("w", encoding="utf-8") as stream:
        child = subprocess.run(command, cwd=REPO, stdout=stream, stderr=subprocess.STDOUT)
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
    args = parser.parse_args(argv)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    run_dir = REPO / "_work/workflow" / (stamp + "-" + args.tag)
    run_dir.mkdir(parents=True, exist_ok=False)
    report = {"schema": 1, "action": args.action, "started_utc": stamp, "phases": []}
    exit_code = 0
    try:
        run_phase("preflight", preflight, run_dir, report["phases"])
        commands = {
            "test-stage-select": ["wsl.exe", "-d", "Ubuntu", "--exec", "bash",
                                 wsl_path(REPO / "tools/test/stage_select/run.sh")],
            "build": ["wsl.exe", "-d", "Ubuntu", "--exec", "bash", wsl_path(BUILD_SCRIPT)],
            "report": [str(REPORT_PYTHON), str(REPO / "tools/test/bag2_report.py"),
                       "--tag", args.tag, "--timeout", "0"],
        }
        if args.action != "preflight":
            prefixes = ("state:", "phases:", "fever anims:", "run report:", "sheet:", "shots log:")
            run_phase(args.action, lambda log: run_command(commands[args.action], log,
                      summary_prefixes=prefixes if args.action == "report" else None), run_dir, report["phases"])
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
