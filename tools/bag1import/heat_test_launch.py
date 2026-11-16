"""Plan or run the legacy Heat test-mod adapters from the shared host configuration.

The bash adapters only prepare a workspace copy of assets/archive; the external
psx-asset-tools make-mod step, which installs into the experimental install, is a
separate explicit step. Host checks do not validate converter or package contents.
Without --run the plan is printed and nothing is launched.

Usage:
    py -3.13 tools/bag1import/heat_test_launch.py {character,stage} [--local-config TOML]
        [--omit model,tex,camera,sound] [--run [--package]]
"""
import argparse
from dataclasses import dataclass
import json
import os
import stat
from pathlib import Path
import subprocess
import sys
from collections.abc import Callable, Sequence

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.workflow.project_config import (ConfigError, ProjectConfig, assert_write_target,
                                           export_config, load_config, require_paths,
                                           require_values, to_wsl_path)

SCRIPT_DIR = Path(__file__).resolve().parent
PACKAGE_OPERATION = "heat-test-package"


@dataclass(frozen=True)
class Target:
    script: str
    operation: str
    source_key: str
    workspace_key: str
    mod_id: str
    mod_name: str
    description: str
    parts: tuple[str, ...] = ()


TARGETS = {
    "character": Target(
        "build_heat_test.sh", "heat-character-prepare", "inputs.heat_bag1_members",
        "paths.heat_test_workspace", "bag2jp.test.bag1-heat-model", "TEST BAG1 Heat model",
        "Test: BAG1 Heat (mesh, animations, textures, voices) in place of BAG2 Heat, both costumes"),
    # Stage parts are per-run experiment selectors, not host configuration.
    "stage": Target(
        "build_heat_stage_test.sh", "heat-stage-prepare", "inputs.bag1_usa_extraction",
        "paths.heat_stage_workspace", "bag2jp.test.bag1-heat-stage", "TEST BAG1 Heat stage",
        "Test: BAG1 Heat stage geometry and textures in place of Heat's BAG2 stage",
        ("model", "tex", "camera", "sound")),
}


def _overlaps(first: Path, second: Path) -> bool:
    a, b = (Path(os.path.normcase(path.resolve())) for path in (first, second))
    return a == b or a.is_relative_to(b) or b.is_relative_to(a)


def _require_operation(config: ProjectConfig, operation: str) -> None:
    missing = export_config(config, operation=operation)["missing"]
    if missing:
        raise ConfigError(f"{operation}: unresolved {', '.join(missing)}")


def _reject_links(root: Path) -> None:
    """Reject links/reparse points without traversing them (not a race-free sandbox)."""
    def checked(path: Path):
        info = path.lstat()
        if (stat.S_ISLNK(info.st_mode)
                or getattr(info, 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT):
            raise ConfigError(f"Heat writable tree contains a link/reparse point: {path}")
        return info

    try:
        for parent in root.parents:
            if parent.exists():
                checked(parent)
        pending = [root]
        while pending:
            path = pending.pop()
            try:
                info = checked(path)
            except FileNotFoundError:
                if path == root:
                    continue  # a new workspace is allowed; dangling links have lstat data
                raise
            if stat.S_ISDIR(info.st_mode):
                with os.scandir(path) as entries:
                    pending.extend(Path(entry.path) for entry in entries)
    except OSError as error:
        raise ConfigError(f"Cannot inspect Heat writable tree {root}: {error}") from error


def _require_direct_sources(target_name: str, source: Path) -> None:
    """Check direct BAG1 inputs, not transitive helper inputs or asset validity."""
    names = (('PLAYER2_P_HEATA2/001.bin',
              *(f'PLAYER{n}_P_HEAT{side}{n}/000.bin' for n in (2, 4) for side in ('A', 'B')),
              'PLAYER1E_P_HEATA1/007.sedt',
              *(f'PLAYER1E_P_HEATA1/{slot}.tim' for slot in ('004', '005', '006')),
              'PLAYER3E_P_HEATA3/004.tim') if target_name == 'character'
             else ('STAGEE/ST_HEAT.DFS', 'SCUS_942.63'))
    try:
        for name in names:
            if not (source / name).is_file():
                raise ConfigError(f"Heat direct input is not a file: {source / name}")
        if target_name == 'stage':
            executable = source / 'SCUS_942.63'
            with executable.open('rb') as stream:
                magic = stream.read(8)
            if magic != b'PS-X EXE' or executable.stat().st_size <= 0x800:
                raise ConfigError(f"Heat executable requires PS-X EXE header and payload: {executable}")
    except OSError as error:
        raise ConfigError(f"Cannot inspect Heat direct inputs {source}: {error}") from error


def plan(target_name: str, config: ProjectConfig, *, omit: Sequence[str] = (),
         package: bool = False) -> dict:
    """Return validated WSL argument vectors; never executes or creates anything."""
    target = TARGETS.get(target_name)
    if target is None:
        raise ConfigError(f"Unknown Heat test target: {target_name}")
    unknown = sorted(set(omit) - set(target.parts))
    if unknown:
        raise ConfigError(f"{target_name}: unsupported parts to omit: {', '.join(unknown)}")
    _require_operation(config, target.operation)
    if package:
        _require_operation(config, PACKAGE_OPERATION)
    source, workspace = require_paths(config, (target.source_key, target.workspace_key))
    distribution, = require_values(config, ("wsl.distribution",))
    if not source.is_dir():
        raise ConfigError(f"{target.source_key} is not a directory: {source}")
    archive = config.repo_root / "assets/archive"
    if not archive.is_dir():
        raise ConfigError(f"BAG2 asset tree is not a directory: {archive}")
    # The adapter deletes and recreates workspace/archive: confine it to the work root.
    workspace = assert_write_target(config, workspace, role="work")
    protected = [source, archive, config.repo_root / "config"]
    if "paths.experimental_install" in config.values:
        protected.append(config.values["paths.experimental_install"])
    for base in protected:
        if _overlaps(workspace, base):
            raise ConfigError(f"Heat workspace {workspace} overlaps protected location {base}")
    _reject_links(archive)
    _reject_links(workspace)
    _require_direct_sources(target_name, source)
    env = [f"BAG2JP_REPO={to_wsl_path(config.repo_root)}",
           f"BAG2JP_SOURCE={to_wsl_path(source)}",
           f"BAG2JP_WORKSPACE={to_wsl_path(workspace)}"]
    env += [f"STAGE_{part.upper()}={'0' if part in omit else '1'}" for part in target.parts]
    steps = {
        "target": target_name,
        "operations": [target.operation] + ([PACKAGE_OPERATION] if package else []),
        "config": dict(config.input_hashes),
        "prepare": ["wsl.exe", "-d", distribution, "--exec", "env", *env,
                    "bash", to_wsl_path(SCRIPT_DIR / target.script)],
        "package": None,
    }
    if package:
        tools, cue, experimental = require_paths(
            config, ("tools.psx_asset_tools", "inputs.bag2_cue", "paths.experimental_install"))
        if not tools.is_dir():
            raise ConfigError(f"tools.psx_asset_tools is not a directory: {tools}")
        if not cue.is_file():
            raise ConfigError(f"inputs.bag2_cue is not a file: {cue}")
        installed = assert_write_target(config, experimental / "mods/installed", role="experimental")
        steps["package"] = [
            "wsl.exe", "-d", distribution, "--cd", to_wsl_path(tools), "--exec",
            "python3", "-m", "psxassets", "make-mod", to_wsl_path(cue), to_wsl_path(workspace),
            to_wsl_path(installed), "--id", target.mod_id, "--name", target.mod_name,
            "--author", "BAG2JP", "--description", target.description]
    return steps


def main(argv: Sequence[str] | None = None, *, runner: Callable = subprocess.run,
         repo_root: Path | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("target", choices=sorted(TARGETS))
    parser.add_argument("--local-config", type=Path, default=None)
    parser.add_argument("--omit", default="", help="stage only: comma-separated parts kept stock")
    parser.add_argument("--run", action="store_true", help="execute the preparation adapter")
    parser.add_argument("--package", action="store_true",
                        help="after preparation, run make-mod into the experimental install")
    args = parser.parse_args(argv)
    if args.package and not args.run:
        parser.error("--package requires --run")
    omit = tuple(part for part in args.omit.split(",") if part)
    try:
        config = load_config(repo_root=repo_root, local_config=args.local_config)
        steps = plan(args.target, config, omit=omit, package=args.package)
    except ConfigError as error:
        parser.error(str(error))
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.stdout.write(json.dumps(steps, ensure_ascii=False, indent=2) + "\n")
    if args.run:
        runner(steps["prepare"], check=True)
        if steps["package"] is not None:
            runner(steps["package"], check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
