"""Windows-only bounded BAG2JP UI driver; no runtime or package modifications."""
import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import logging
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import tomllib
from types import MappingProxyType
from typing import Callable, Mapping

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.workflow import project_config
import versus_navigation as nav

load_config = project_config.load_config
LOGGER = logging.getLogger(__name__)
MENU_ROOT = 7
MENU_VERSUS = 1
CUE_SLOTS = 0x8006D9F6  # u16 cue id per sound slot, stride 8 (FUN_8002e2d0)
RESULT_STATE = 0x8005D3E0  # result-screen announcer state (overlay at 0x80098C88)
HELPER_CALLS = 0
MAX_WATCH = 32  # bag2jp_anim_trace.c MAX_WATCH; the runtime silently drops extra entries
DEBUG_ENV_ALLOWLIST = ("BAG2JP_TEST_HEAT_ATTACK", "BAG2JP_TEST_STRIKE_ATTACK", "BAG2JP_TEST_GASO_ATTACK",
                       "BAG2JP_TEST_ORDERED_DUEL", "BAG2JP_TEST_B1M_TIMING", "BAG2JP_TEST_P1_DUET")
# A runner may declare these per Session; inherited environment still obeys DEBUG_ENV_ALLOWLIST.
# HEAT_STRIKE_DUEL is the Strike batch side-2 fixture read by bag2jp_anim_trace.c.
DECLARED_FIXTURE_ALLOWLIST = DEBUG_ENV_ALLOWLIST + ("BAG2JP_TEST_HEAT_STRIKE_DUEL",)
CATALOG_TARGET = Path("versus-navigation/catalog.json")
RUNS_TARGET = Path("versus-runs")


@dataclass(frozen=True)
class HarnessSettings:
    """Per-run values resolved once from project configuration; never mutated afterwards."""

    config: project_config.ProjectConfig
    game: Path
    winshot: Path
    catalog: Path
    runs: Path
    state_timeout: float
    helper_timeout: float
    startup_timeout: float
    finish_timeout: float
    key_hold_ms: int
    key_gap_ms: int
    menu_fade: float

    def provenance(self) -> dict:
        """Effective values with their origins and config hashes, for the run report."""
        keys = _operation_keys("versus-session")
        return {"operation": "versus-session",
                "values": {key: str(self.config.values[key]) if isinstance(self.config.values[key], Path)
                           else self.config.values[key] for key in keys},
                "origins": {key: self.config.origins[key] for key in keys},
                "input_hashes": dict(self.config.input_hashes)}


def _operation_keys(operation: str) -> tuple[str, ...]:
    return tuple(key for key, spec in project_config.FIELDS.items() if operation in spec.operations)


def _operation_values(config: project_config.ProjectConfig, operation: str) -> dict:
    keys = _operation_keys(operation)
    return dict(zip(keys, project_config.require_values(config, keys)))


def resolve_settings(config: project_config.ProjectConfig) -> HarnessSettings:
    """Validate every versus-session value and write destination before any effect."""
    values = _operation_values(config, "versus-session")
    return HarnessSettings(
        config=config,
        game=project_config.assert_write_target(config, values["paths.experimental_install"], role="experimental"),
        winshot=values["tools.winshot_root"],
        catalog=project_config.assert_write_target(config, CATALOG_TARGET, role="work"),
        runs=project_config.assert_write_target(config, RUNS_TARGET, role="work"),
        state_timeout=values["harness.state_timeout_seconds"],
        helper_timeout=values["harness.helper_timeout_seconds"],
        startup_timeout=values["harness.startup_timeout_seconds"],
        finish_timeout=values["harness.finish_timeout_seconds"],
        key_hold_ms=values["harness.key_hold_ms"],
        key_gap_ms=values["harness.key_gap_ms"],
        menu_fade=values["harness.menu_fade_seconds"])


def resolve_inspection(config: project_config.ProjectConfig) -> tuple[Path, float]:
    """Resolve only the read-only identity inspection keys; the stable install stays excluded."""
    values = _operation_values(config, "versus-inspect")
    game = project_config.assert_write_target(config, values["paths.experimental_install"], role="experimental")
    return game, values["harness.helper_timeout_seconds"]


def armed_debug_fixtures(environ: dict[str, str]) -> dict[str, str]:
    """Allowlisted BAG2JP_TEST_* fixtures present in environ; recorded so a fixture run is never archived as natural play."""
    return {key: environ[key] for key in DEBUG_ENV_ALLOWLIST if key in environ}


def build_game_env(environ: dict[str, str]) -> dict[str, str]:
    """Drop every BAG2JP_* variable except allowlisted fixtures; always enable the trace."""
    env = {key: value for key, value in environ.items() if not key.startswith("BAG2JP_")}
    env.update(armed_debug_fixtures(environ))
    env["BAG2JP_ANIM_TRACE"] = "1"
    return env


def parse_watch_extra(text: str) -> list[tuple[int, int]]:
    """Parse ADDR:SIZE,... (hex RAM address, size 1/2/4, naturally aligned) for diagnostic watches."""
    watches = []
    for entry in text.split(","):
        match = re.fullmatch(r"([0-9A-Fa-f]{8}):([124])", entry)
        if match is None:
            raise ValueError(f"Watch entry must be ADDR:SIZE with size 1, 2 or 4: {entry!r}")
        address, size = int(match[1], 16), int(match[2])
        if not 0x80000000 <= address <= 0x807FFFFF - (size - 1) or address % size:
            raise ValueError(f"Watch address outside 8 MB RAM or misaligned: {entry!r}")
        watches.append((address, size))
    # nav.parse_watch keys rows by address: an overlapping entry would shadow navigation state.
    spans = sorted(watches + list(nav.WATCHES.values()))
    if any(a + s > b for (a, s), (b, _) in zip(spans, spans[1:])):
        raise ValueError("Watch entries must not repeat or overlap each other or the standard watches")
    return watches


def ps_quote(value: str | Path) -> str:
    """Quote one literal PowerShell argument, never interpolate caller code."""
    return "'" + str(value).replace("'", "''") + "'"


def powershell(script: str, timeout: float) -> str:
    """Run bounded Windows helpers, surfacing nonzero exits."""
    global HELPER_CALLS
    HELPER_CALLS += 1
    process = subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command",
                              "$ErrorActionPreference='Stop'; " + script],
                             capture_output=True, text=True, timeout=timeout)
    if process.returncode:
        raise RuntimeError(process.stderr.strip()[-1500:])
    return process.stdout.strip()


def process_identity(pid: int, game: Path, timeout: float) -> dict:
    """Resolve path/start time to reject recycled PIDs and stable installations."""
    if pid <= 0:
        raise ValueError("Positive game PID required")
    data = json.loads(powershell(f"$p=Get-Process -Id {pid}; @{{path=$p.Path; ticks=$p.StartTime.ToUniversalTime().Ticks}} | ConvertTo-Json -Compress", timeout))
    if Path(data["path"]).resolve() != (game / "BAG2JP.exe").resolve():
        raise ValueError("Not the experimental BAG2JP executable")
    return data


def tail(path: Path) -> str:
    """Read bounded log suffixes, avoiding repeated whole-log ingestion."""
    with path.open("rb") as stream:
        stream.seek(max(0, path.stat().st_size - 65536))
        return stream.read().decode("utf-8", errors="replace")


def session_log(path: Path, started: float) -> str:
    """Do not accept a previous process's popup confirmations."""
    if not path.is_file():
        return ""
    if path.stat().st_mtime < started:
        raise ValueError("Popup log belongs to an earlier process")
    return tail(path)


def copy_current(source: Path, run: Path, started: float) -> bool:
    """Archive only evidence this session produced; a never-started session owns nothing."""
    if not started or not source.is_file() or source.stat().st_mtime < started:
        return False
    shutil.copy2(source, run / source.name)
    return True


def contact_sheet(run: Path) -> Path:
    """Combine semantic checkpoints for one compact visual review, not auto-vision."""
    from PIL import Image, ImageDraw
    names = [name for name in ("versus-selected", "selector", "p1-popup", "p2-popup", "stage-selected", "gameplay")
             if (run / f"{name}.png").is_file()]
    if not names:
        names = ["final-state"] if (run / "final-state.png").is_file() else []
    if not names:
        raise ValueError("No captured checkpoints")
    sheet = Image.new("RGB", (1200, ((len(names) + 1) // 2) * 370))
    draw = ImageDraw.Draw(sheet)
    for index, name in enumerate(names):
        x, y = (index % 2) * 600, (index // 2) * 370
        with Image.open(run / f"{name}.png") as source:
            sheet.paste(source.convert("RGB").resize((600, 340)), (x, y))
        draw.text((x, y + 342), name, fill="white")
    output = run / "review-sheet.png"
    sheet.save(output)
    return output


def save_result(run: Path, result: dict, has_shots: bool) -> None:
    """Always retain the primary report even if secondary image processing fails."""
    path = run / "result.json"
    path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    if has_shots:
        try:
            result["contact_sheet"] = str(contact_sheet(run))
        except (OSError, ValueError, ImportError) as exc:
            result["contact_sheet_error"] = str(exc)
        path.write_text(json.dumps(result, indent=2), encoding="utf-8")


def finish_budget(text: str) -> float:
    """Explicit --finish-timeout: the same bounds the configuration schema enforces."""
    try:
        value = float(text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"not a number: {text!r}") from exc
    maximum = project_config.FIELDS["harness.finish_timeout_seconds"].maximum
    if not math.isfinite(value) or not 0 < value <= maximum:
        raise argparse.ArgumentTypeError(f"must be finite, positive and at most {maximum:g} seconds")
    return value


class Session:
    """Own exactly one experimental process and one unique evidence directory."""

    def __init__(self, run: Path, settings: HarnessSettings, *, fixtures: Mapping[str, str] | None = None) -> None:
        fixtures = dict(fixtures or {})
        undeclared = sorted(set(fixtures) - set(DECLARED_FIXTURE_ALLOWLIST))
        if undeclared:
            raise ValueError(f"Fixtures outside the declared allowlist: {', '.join(undeclared)}")
        if any(not isinstance(value, str) or not value for value in fixtures.values()):
            raise ValueError("Declared fixture values must be non-empty strings")
        self.run = run
        self.settings = settings
        self._fixtures = MappingProxyType(fixtures)
        self.process: subprocess.Popen | None = None
        self.identity: dict = {}
        self.started = 0.0
        self.bindings: dict = {}
        self.actions: list[dict] = []
        self.shots: list[str] = []
        self.checkpoints: dict[str, dict] = {}
        self.logs: list = []
        self.ram_dump_frame: int | None = None
        self.ram_dump_size = "2mb"
        self.audio_dump = False
        self.watch_cues = False
        self.watch_extra: list[tuple[int, int]] = []
        self.spu_cue_dump: int | None = None
        self.vram_dump_frames: tuple[int, ...] = ()
        self.debug_fixtures: dict[str, str] | None = None  # fixtures in the launched env; None until launch

    @property
    def fixtures(self) -> Mapping[str, str]:
        """Declared fixtures are fixed at construction; nobody can widen them before launch."""
        return self._fixtures

    def start(self) -> None:
        """Refuse active sessions; launch with only explicit debug instrumentation."""
        game = self.settings.game
        active = powershell("@(Get-Process BAG2JP -ErrorAction SilentlyContinue).Count", self.settings.helper_timeout)
        if active != "0":
            raise ValueError("An active BAG2JP session exists; not closing it automatically")
        game_settings = tomllib.loads((game / "settings.toml").read_text(encoding="utf-8-sig"))
        controller = game_settings.get("controller")
        if not isinstance(controller, dict):
            raise ValueError("settings.toml has no [controller] table")
        if any(controller.get(f"p{side}_device") != "keyboard" for side in (1, 2)):
            raise ValueError("Both pads must already use keyboard")
        self.bindings = nav.parse_bindings((game / "keybinds.ini").read_text(encoding="utf-8-sig"))
        for side in (1, 2):
            for action in nav.TEMPORARY_KEYS[side]:
                nav.key_for(self.bindings, side, action)
        env = build_game_env(dict(os.environ))
        env.update(self.fixtures)
        if self.ram_dump_frame is not None:
            if self.ram_dump_frame <= 0:
                raise ValueError("RAM dump frame must be positive")
            if self.ram_dump_size not in ("2mb", "8mb"):
                raise ValueError("RAM dump size must be 2mb or 8mb")
            env["BAG2JP_RAM_DUMP"] = str(self.ram_dump_frame)
            env["BAG2JP_RAM_DUMP_SIZE"] = self.ram_dump_size
        if self.vram_dump_frames:
            if any(not isinstance(frame, int) or frame <= 0 for frame in self.vram_dump_frames):
                raise ValueError("VRAM dump frames must be positive integers")
            env["BAG2JP_VRAM_DUMP"] = ",".join(str(frame) for frame in self.vram_dump_frames)
        if self.audio_dump:
            env["BAG2JP_AUDIO_DUMP"] = "1"
        if self.spu_cue_dump is not None:
            env["BAG2JP_SPU_CUE_DUMP"] = f"0x{self.spu_cue_dump:04X}"
        watches = list(nav.WATCHES.values())
        if self.watch_cues:
            watches += [(CUE_SLOTS + 8 * slot, 2) for slot in range(15)] + [(RESULT_STATE, 4)]
        watches += self.watch_extra
        if len(watches) > MAX_WATCH:
            raise ValueError(f"The runtime logs at most {MAX_WATCH} watches; {len(watches)} requested")
        env["BAG2JP_WATCH"] = ",".join(f"{address:08X}:{size}" for address, size in watches)
        self.logs = [(self.run / name).open("wb") for name in ("stdout.log", "stderr.log")]
        try:
            (game / 'bag2jp_charsel_popup.log').unlink(missing_ok=True)
        except Exception:
            pass
        self.started = time.time()
        self.debug_fixtures = {key: env[key] for key in DECLARED_FIXTURE_ALLOWLIST if key in env}
        self.process = subprocess.Popen([str(game / "BAG2JP.exe"), "--no-launcher"], cwd=game,
                                        env=env, stdout=self.logs[0], stderr=self.logs[1])
        self.identity = process_identity(self.process.pid, game, self.settings.helper_timeout)
        nav.wait_until(self.maybe_state, lambda state: state is not None, self.settings.startup_timeout)

    def assert_process(self) -> None:
        """Guard every input and capture against process exit or PID reuse."""
        if self.process is None or self.process.poll() is not None:
            raise RuntimeError("Task-owned game exited")
        if process_identity(self.process.pid, self.settings.game, self.settings.helper_timeout) != self.identity:
            raise ValueError("Process identity changed")

    def state(self) -> dict[str, int]:
        """Require current-session logs plus a fresh debug heartbeat."""
        if self.process is None or self.process.poll() is not None:
            raise RuntimeError("Task-owned game exited")
        heartbeat = self.settings.game / "bag2jp_frame.txt"
        watch = self.settings.game / "bag2jp_watch.log"
        nav.check_freshness(heartbeat.stat().st_mtime, time.time(), self.started)
        if watch.stat().st_mtime < self.started:
            raise ValueError("Watch log belongs to an earlier run")
        watch_frame, state = nav.watch_observation(tail(watch))
        # Reusing heartbeat phases leaves RAM-watch slots for costumes and clock.
        record = heartbeat.read_text()
        state.update(nav.heartbeat_phases(record))
        nav.check_watch_progress(heartbeat.stat().st_mtime, watch.stat().st_mtime,
                                 time.time(), self.started, int(record.split()[0]), watch_frame)
        return state

    def maybe_state(self) -> dict | None:
        """Allow incomplete boot telemetry while respecting the outer deadline."""
        try:
            return self.state()
        except (FileNotFoundError, ValueError):
            return None

    def wait(self, predicate: Callable[[dict], bool], timeout: float | None = None) -> dict:
        """Wait without issuing more inputs; reject timeout instead of restarting."""
        if timeout is None:
            timeout = self.settings.state_timeout
        return nav.wait_until(self.maybe_state, lambda value: value is not None and predicate(value), timeout)

    def key(self, side: int, action: str) -> None:
        """Send only an independently bound action to the verified task PID."""
        self.assert_process()
        key = nav.key_for(self.bindings, side, action)
        powershell(f"& {ps_quote(self.settings.winshot / 'postkey.ps1')} -Id {self.process.pid} -Keys {ps_quote(key)} "
                   f"-HoldMs {self.settings.key_hold_ms} -GapMs {self.settings.key_gap_ms} | Out-Null",
                   self.settings.helper_timeout)
        self.actions.append({"player": side, "action": action, "key": key, "time": round(time.time() - self.started, 3)})

    def shot(self, name: str) -> None:
        """Save evidence; this does not claim automatic visual interpretation."""
        self.assert_process()
        path = self.run / f"{name}.png"
        if path.exists():
            raise FileExistsError(path)
        powershell(f"& {ps_quote(self.settings.winshot / 'winshot.ps1')} -Ids {self.process.pid} -Out {ps_quote(path)} | Out-Null",
                   self.settings.helper_timeout)
        self.shots.append(path.name)
        self.checkpoints[name] = self.state()

    def menu(self) -> None:
        """Reach the observed title menu, then verify index 1 before confirmation."""
        # Root5 is the opening movie. Root6 only initializes the menu; sending a
        # second Start there races its transition to root7 and confirms campaign.
        observed = self.wait(lambda current: current["root"] in (5, MENU_ROOT), 60)
        if observed["root"] == 5:
            self.key(1, "start")
        self.wait(lambda current: current["root"] == MENU_ROOT, 30)
        time.sleep(self.settings.menu_fade)  # Root changes before the menu fade accepts controller inputs.
        for _ in range(6):
            state = self.state()
            if state["root"] != MENU_ROOT:
                raise ValueError("Left menu unexpectedly")
            if state["menu"] == MENU_VERSUS:
                break
            self.key(1, "down")
            self.wait(lambda current: current["menu"] != state["menu"])
        if self.state()["menu"] != MENU_VERSUS:
            raise ValueError("Versus menu index not reached")
        self.shot("versus-selected")
        self.key(1, "circle")
        self.wait(lambda state: state["root"] in nav.SELECTOR_ROOTS and state["mode"] == 2 and
                  (state["p1_status"] >> 16 & 255) == 1 and (state["p2_status"] >> 16 & 255) == 1)
        nav.require_selector(self.state())
        self.shot("selector")

    def move(self, side: int, action: str, expected: int) -> None:
        """Require character-select identity and check both cursors after one input."""
        before = self.state()
        nav.require_selector(before)
        if not before["selectable"] & (1 << expected):
            raise ValueError(f"Character {expected} is locked/unavailable")
        self.key(side, action)
        state = self.wait(lambda current: nav.cursor(current, side) != nav.cursor(before, side))
        nav.require_selector(state)
        if nav.cursor(state, side) != expected or nav.cursor(state, 3 - side) != nav.cursor(before, 3 - side):
            raise ValueError("Unexpected target or cross-player cursor movement")

    def probe(self, executable_hash: str) -> dict:
        """Calibrate local edges, reaching Strike (1), Comet (2), Shorty (5), and Bi-O (9)."""
        if nav.cursor(self.state(), 1) != 0:
            raise ValueError("Probe requires observed initial P1 Heat")
        edges = []
        # Calibrated path:
        # 0 -> right -> 2 -> left -> 0
        # 0 -> down -> 1 -> left -> 5 -> down -> 9
        # and back: 9 -> up -> 5 -> right -> 1 -> up -> 0
        steps = [
            ("right", 2),
            ("left", 0),
            ("down", 1),
            ("left", 5),
            ("down", 9),
            ("up", 5),
            ("right", 1),
            ("up", 0),
        ]
        for action, expected in steps:
            source = nav.cursor(self.state(), 1)
            self.move(1, action, expected)
            self.shot(f"probe-{source}-{action}-{expected}")
            edge = [source, action, expected]
            if edge not in edges:
                edges.append(edge)
        return {"runtime_sha256": executable_hash, "edges": edges, "evidence": str(self.run)}

    def pick(self, side: int, name: str, version: str, costume: str, edges: dict) -> dict:
        """Resolve a name, route explicitly, and require exact popup confirmation."""
        character = nav.validate_pick(name, version, costume)
        state = self.state()
        nav.require_selector(state)
        for action in nav.route(nav.cursor(state, side), character, edges):
            expected = edges[(nav.cursor(self.state(), side), action)]
            self.move(side, action, expected)
        self.shot(f"p{side}-character")
        self.key(side, "circle")
        log_path = self.settings.game / "bag2jp_charsel_popup.log"
        # Popup log is truncated on activation in this task-owned process.
        log = nav.wait_until(lambda: session_log(log_path, self.started), lambda text: f"open: side {side-1} char {character} " in text,
                             self.settings.state_timeout)
        match = re.findall(rf"open: side {side-1} char {character} \(bag1 version (\d+), current (\d+)\)", log)
        if not match:
            raise ValueError("Popup capability observation missing")
        has_version, current = map(int, match[-1])
        if version == "BAG1" and not has_version:
            raise ValueError("Installed character has no BAG1 version")
        if has_version and current != (version == "BAG1"):
            self.key(side, "right")
        if costume == "B":
            if has_version:
                self.key(side, "down")
            self.key(side, "right")
        self.shot(f"p{side}-popup")
        self.key(side, "circle")
        log = nav.wait_until(lambda: session_log(log_path, self.started), lambda text: f"confirm: side {side-1} char {character} " in text,
                             self.settings.state_timeout)
        observed = nav.confirmation(log, side - 1, character, version, costume)
        self.wait(lambda state: (state[f"p{side}_status"] >> 16 & 255) == 2)
        self.key(side, "circle")  # NORMAL commands, separate from the version popup.
        self.wait(lambda state: (state[f"p{side}_status"] >> 16 & 255) == 3)
        return observed

    def match(self, stage: str | int, characters: list[int], costumes: list[int], survey: bool = False) -> None:
        """Check stage cursor and then require both selected IDs in gameplay.

        survey: first step through all 15 carousel rows, shooting each one."""
        self.wait(lambda state: state["select_phase"] in (2, 3))
        if survey:
            for step in range(15):
                row = self.state()["stage_position"] >> 16 & 255
                self.shot(f"stage-survey-{step:02d}-row-{row:02d}")
                self.key(1, "left")
                self.wait(lambda current: (current["stage_position"] >> 16 & 255) != row)
        stage_map = {
            "HeatBAG2": 0, "HeatBAG1": 1, 
            "StrikeBAG2": 2, "StrikeBAG1": 3,
            "BiO": 11, "BiOBAG2": 11, 
            "GasOBAG1": 12, "GasoBAG1": 12, "Gaso": 12, "GasO": 12,
            "Random": 15
        }
        wanted = stage_map.get(stage, stage)
        for _ in range(16):
            state = self.state()
            nav.require_selector(state)
            row = state["stage_position"] >> 16 & 255
            if row == wanted:
                break
            self.key(1, "left")
            self.wait(lambda current: (current["stage_position"] >> 16 & 255) != row)
        if (self.state()["stage_position"] >> 16 & 255) != wanted:
            raise ValueError(f"Requested stage row {wanted} ({stage}) not observed")
        self.shot("stage-selected")
        self.key(1, "circle")
        self.wait(nav.is_gameplay, 60)
        state = self.state()
        nav.verify_gameplay(state, characters, costumes)
        self.shot("gameplay")

    def finish_match(self, timeout: float | None = None, interval: float = 20.0) -> dict:
        """Follow the song to its end and back to character select, keeping evidence.

        Fever runs inside the battle root, so leaving that root - not a phase change -
        marks the song's end; the selector gate then proves the return.
        """
        if timeout is None:
            timeout = self.settings.finish_timeout
        started = time.monotonic()
        next_shot = started + interval
        left_battle = None
        samples = 0
        while True:
            elapsed = time.monotonic() - started
            if elapsed > timeout:
                raise TimeoutError("Song never returned to character select")
            state = self.state()
            samples += 1
            if left_battle is None and state["root"] != nav.GAMEPLAY_ROOT:
                left_battle = round(elapsed, 1)
                self.shot("song-end")
            if nav.is_selector(state):
                self.shot("returned-selector")
                return {"seconds": round(time.monotonic() - started, 1), "samples": samples,
                        "left_battle": left_battle, "return_root": state["root"]}
            if time.monotonic() >= next_shot:
                self.shot(f"match-{len(self.shots)}")
                next_shot += interval
            time.sleep(1.0)

    def close(self) -> None:
        """Gracefully close only the process created here, never a name-wide kill."""
        if self.process is not None and self.process.poll() is None:
            self.assert_process()
            powershell(f"$p=Get-Process -Id {self.process.pid}; $null=$p.CloseMainWindow(); if(-not $p.WaitForExit(15000)) {{throw 'Game did not close; configuration retained for safe recovery'}}",
                       self.settings.helper_timeout)
            self.process.wait(timeout=2)
        for stream in self.logs:
            stream.close()


def config_selector() -> argparse.ArgumentParser:
    """Pre-parser: the configuration must resolve before other defaults exist."""
    selector = argparse.ArgumentParser(add_help=False)
    selector.add_argument("--local-config", type=Path, default=None,
                          help="local TOML overlay; relative selections anchor to the repository")
    return selector


def build_parser(config: project_config.ProjectConfig) -> argparse.ArgumentParser:
    """Full CLI whose budget defaults are the resolved configuration values."""
    parser = argparse.ArgumentParser(description=__doc__, parents=[config_selector()])
    parser.add_argument("--action", choices=("probe", "run", "inspect"), default="inspect")
    parser.add_argument("--game-id", type=int)
    parser.add_argument("--tag", default="versus")
    parser.add_argument("--ram-dump-frame", type=int,
                        help="Explicit diagnostic RAM snapshot frame; inherited debug flags remain ignored")
    parser.add_argument("--ram-dump-size", choices=("2mb", "8mb"), default="2mb",
                        help="Snapshot extent; 8mb requires the experimental expanded-RAM runtime")
    parser.add_argument("--audio-dump", action="store_true",
                        help="record bag2jp_audio.wav and its sync log into the run after the game closes")
    parser.add_argument("--spu-cue-dump", type=lambda text: int(text, 0), default=None,
                        help="dump SPU RAM and voice states when sound slot 14 starts this cue")
    parser.add_argument("--watch-cues", action="store_true",
                        help="also watch the 15 sound-slot cue ids (0x8006D9F6 + 8*slot) in bag2jp_watch.log")
    parser.add_argument("--watch-extra", type=parse_watch_extra, default=[],
                        help="diagnostic RAM watches ADDR:SIZE,... appended to bag2jp_watch.log")
    parser.add_argument("--temporary-controls", action="store_true")
    for side in (1, 2):
        parser.add_argument(f"--p{side}-character", default="Heat")
        parser.add_argument(f"--p{side}-version", choices=("BAG1", "BAG2"), default="BAG2")
        parser.add_argument(f"--p{side}-costume", choices=("A", "B"), default="A")
    parser.add_argument("--stage", choices=("HeatBAG2", "HeatBAG1", "StrikeBAG2", "StrikeBAG1", "GasOBAG1", "GasoBAG1"), default="HeatBAG2")
    parser.add_argument("--stage-survey", action="store_true",
                        help="shoot every stage carousel row before choosing the stage")
    parser.add_argument("--finish", action="store_true",
                        help="follow the song to its end and require the return to character select")
    # An explicit value wins; otherwise the resolved harness.finish_timeout_seconds applies.
    parser.add_argument("--finish-timeout", type=finish_budget,
                        default=config.values.get("harness.finish_timeout_seconds"),
                        help="seconds allowed for song end plus return (default: harness.finish_timeout_seconds)")
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: every run writes evidence and an honest machine status."""
    selector = config_selector()
    known, _ = selector.parse_known_args(argv)
    try:
        config = load_config(local_config=known.local_config)
    except project_config.ConfigError as exc:
        selector.error(f"config error: {exc}")
    parser = build_parser(config)
    args = parser.parse_args(argv)
    if args.ram_dump_frame is not None and args.ram_dump_frame <= 0:
        parser.error("--ram-dump-frame must be positive")
    if len(nav.WATCHES) + (16 if args.watch_cues else 0) + len(args.watch_extra) > MAX_WATCH:
        parser.error(f"The runtime logs at most {MAX_WATCH} watches")
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    if os.name != "nt":
        parser.error("Windows test host required")
    if args.action == "inspect":
        try:
            game, helper_timeout = resolve_inspection(config)
        except project_config.ConfigError as exc:
            parser.error(f"config error: {exc}")
        identity = process_identity(args.game_id or 0, game, helper_timeout)
        LOGGER.info(json.dumps({"pid": args.game_id, "identity": identity,
                                "bindings": nav.parse_bindings((game / "keybinds.ini").read_text()),
                                "note": "Read-only identity/bindings inspection; no gameplay claim"}))
        return 0
    if not args.temporary_controls or not re.fullmatch(r"[A-Za-z0-9_-]{1,48}", args.tag):
        parser.error("Explicit --temporary-controls and a safe tag are required")
    try:
        settings = resolve_settings(config)
    except project_config.ConfigError as exc:
        parser.error(f"config error: {exc}")
    characters = [nav.validate_pick(getattr(args, f"p{side}_character"), getattr(args, f"p{side}_version"), getattr(args, f"p{side}_costume")) for side in (1, 2)]
    executable_hash = nav.sha256(settings.game / "BAG2JP.exe")
    catalog = None
    if args.action == "run":
        catalog = json.loads(settings.catalog.read_text())
        nav.validated_edges(catalog, executable_hash)
        nav.verify_catalog_review(catalog)
    # Refuse before any configuration edit, not merely after backing it up.
    if powershell("@(Get-Process BAG2JP -ErrorAction SilentlyContinue).Count", settings.helper_timeout) != "0":
        LOGGER.error("Active game session; no files changed")
        return 1
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    try:
        run = project_config.assert_write_target(config, settings.runs / f"{stamp}-{args.tag}", role="work")
    except project_config.ConfigError as exc:
        parser.error(f"config error: {exc}")
    run.mkdir(parents=True, exist_ok=False)
    session = Session(run, settings)
    session.ram_dump_frame = args.ram_dump_frame
    session.ram_dump_size = args.ram_dump_size
    session.audio_dump = args.audio_dump
    session.watch_cues = args.watch_cues
    session.watch_extra = args.watch_extra
    session.spu_cue_dump = args.spu_cue_dump
    files = nav.IsolatedFiles(settings.game, run, safe_to_restore=lambda: session.process is None or session.process.poll() is not None)
    requested = {key: str(value) if isinstance(value, Path) else value for key, value in vars(args).items()}
    result = {"status": "failed", "requested": requested, "runtime_sha256": executable_hash,
              "debug_fixtures": None, "configuration": settings.provenance(),
              "visual_review": "pending", "evidence": str(run),
              "script_sha256": {name: nav.sha256(Path(__file__).with_name(name)) for name in
                                ("versus_navigation.py", "versus_session.py", "bag2_versus.ps1")}}
    started = time.monotonic()
    try:
        with files:
            try:
                session.start()
                result["debug_fixtures"] = session.debug_fixtures
                session.menu()
                if args.action == "probe":
                    catalog = session.probe(executable_hash)
                    (run / "catalog.json").write_text(json.dumps(catalog, indent=2))
                    settings.catalog.parent.mkdir(parents=True, exist_ok=True)
                    settings.catalog.write_text(json.dumps(catalog, indent=2))
                    result["status"] = "calibrated_awaiting_visual_review"
                else:
                    edges = nav.validated_edges(catalog, executable_hash)
                    result["observed_picks"] = [session.pick(side, getattr(args, f"p{side}_character"), getattr(args, f"p{side}_version"), getattr(args, f"p{side}_costume"), edges) for side in (1, 2)]
                    session.match(args.stage, characters, [int(args.p1_costume == "B"), int(args.p2_costume == "B")], survey=args.stage_survey)
                    result["status"] = "machine_verified_awaiting_visual_review"
                    if args.finish:
                        result["finish"] = session.finish_match(args.finish_timeout)
                        result["status"] = "complete_awaiting_visual_review"
            finally:
                try:
                    if session.process is not None and session.process.poll() is None:
                        try:
                            session.shot("final-state")
                        except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
                            result["final_capture_error"] = str(exc)
                    for name in ("bag2jp_charsel_popup.log", "bag2jp_bag1_versions.log", "bag2jp_watch.log", "bag2jp_anim_trace.log"):
                        copy_current(settings.game / name, run, session.started)
                finally:
                    session.close()
                    # The recorder finalizes the WAV on exit; copy only after close.
                    copies = [name for name in ("bag2jp_audio.wav", "bag2jp_audio_sync.log") if args.audio_dump]
                    if args.ram_dump_frame is not None:
                        copies.append(f"bag2jp_ram_{args.ram_dump_frame}.bin")
                    if args.spu_cue_dump is not None:
                        copies += [path.name for path in settings.game.glob("bag2jp_spu_*.bin")]
                    for name in copies:
                        path = settings.game / name
                        if path.exists() and (session.process is None or session.process.poll() is not None):
                            shutil.copy2(path, run / name)
    except (OSError, ValueError, RuntimeError, TimeoutError, subprocess.SubprocessError, KeyboardInterrupt) as exc:
        result["status"], result["error"] = "failed", str(exc)
    finally:
        result.update(restoration=files.restoration, actions=session.actions, screenshots=session.shots,
                      checkpoints=session.checkpoints, helper_calls=HELPER_CALLS,
                      elapsed_seconds=round(time.monotonic() - started, 3))
        save_result(run, result, bool(session.shots))
        LOGGER.info(json.dumps({key: result[key] for key in ("status", "evidence", "restoration", "elapsed_seconds")}))
    return 1 if result["status"] == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
