"""Windows-only bounded BAG2JP UI driver; no runtime or package modifications."""
import argparse
from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
import tomllib
from typing import Callable

import versus_navigation as nav

LOGGER = logging.getLogger(__name__)
REPO = Path(__file__).resolve().parents[2]
GAME = Path("D:/Games/Bust A Groove 2 (Japan)/BAG2JP-exp-8mb")
WINSHOT = Path("D:/Dev/Tools/winshot")
CATALOG = REPO / "_work/versus-navigation/catalog.json"
MENU_ROOT = 7
MENU_VERSUS = 1
TIMEOUT = 25.0
HELPER_CALLS = 0


def ps_quote(value: str | Path) -> str:
    """Quote one literal PowerShell argument, never interpolate caller code."""
    return "'" + str(value).replace("'", "''") + "'"


def powershell(script: str) -> str:
    """Run bounded Windows helpers, surfacing nonzero exits."""
    global HELPER_CALLS
    HELPER_CALLS += 1
    process = subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command",
                              "$ErrorActionPreference='Stop'; " + script],
                             capture_output=True, text=True, timeout=35)
    if process.returncode:
        raise RuntimeError(process.stderr.strip()[-1500:])
    return process.stdout.strip()


def process_identity(pid: int) -> dict:
    """Resolve path/start time to reject recycled PIDs and stable installations."""
    if pid <= 0:
        raise ValueError("Positive game PID required")
    data = json.loads(powershell(f"$p=Get-Process -Id {pid}; @{{path=$p.Path; ticks=$p.StartTime.ToUniversalTime().Ticks}} | ConvertTo-Json -Compress"))
    if Path(data["path"]).resolve() != (GAME / "BAG2JP.exe").resolve():
        raise ValueError("Not the experimental BAG2JP executable")
    return data


def assert_process_safe(pid: int) -> None:
    """Verifica que el proceso siga vivo y sea el ejecutable experimental esperado."""
    if pid <= 0:
        raise ValueError("Positive game PID required")
    process_identity(pid)


def tail(path: Path) -> str:
    """Read bounded log suffixes, avoiding repeated whole-log ingestion."""
    with path.open("rb") as stream:
        stream.seek(max(0, path.stat().st_size - 65536))
        return stream.read().decode("utf-8", errors="replace")


def session_log(path: Path, started: float) -> str:
    """Do not accept a previous process's popup confirmations."""
    if path.stat().st_mtime < started:
        raise ValueError("Popup log belongs to an earlier process")
    return tail(path)


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


class Session:
    """Own exactly one experimental process and one unique evidence directory."""

    def __init__(self, run: Path) -> None:
        self.run = run
        self.process: subprocess.Popen | None = None
        self.identity: dict = {}
        self.started = 0.0
        self.bindings: dict = {}
        self.actions: list[dict] = []
        self.shots: list[str] = []
        self.checkpoints: dict[str, dict] = {}
        self.logs: list = []

    def start(self) -> None:
        """Refuse active sessions; launch with only explicit debug instrumentation."""
        active = powershell("@(Get-Process BAG2JP -ErrorAction SilentlyContinue).Count")
        if active != "0":
            raise ValueError("An active BAG2JP session exists; not closing it automatically")
        settings = tomllib.loads((GAME / "settings.toml").read_text(encoding="utf-8-sig"))
        if any(settings["controller"][f"p{side}_device"] != "keyboard" for side in (1, 2)):
            raise ValueError("Both pads must already use keyboard")
        self.bindings = nav.parse_bindings((GAME / "keybinds.ini").read_text(encoding="utf-8-sig"))
        for side in (1, 2):
            for action in nav.TEMPORARY_KEYS[side]:
                nav.key_for(self.bindings, side, action)
        env = {key: value for key, value in os.environ.items() if not key.startswith("BAG2JP_")}
        env["BAG2JP_ANIM_TRACE"] = "1"
        env["BAG2JP_WATCH"] = ",".join(f"{address:08X}:{size}" for address, size in nav.WATCHES.values())
        self.logs = [(self.run / name).open("wb") for name in ("stdout.log", "stderr.log")]
        self.started = time.time()
        self.process = subprocess.Popen([str(GAME / "BAG2JP.exe"), "--no-launcher"], cwd=GAME,
                                        env=env, stdout=self.logs[0], stderr=self.logs[1])
        self.identity = process_identity(self.process.pid)
        nav.wait_until(self.maybe_state, lambda state: state is not None, 40)

    def assert_process(self) -> None:
        """Guard every input and capture against process exit or PID reuse."""
        if self.process is None or self.process.poll() is not None:
            raise RuntimeError("Task-owned game exited")
        if process_identity(self.process.pid) != self.identity:
            raise ValueError("Process identity changed")

    def state(self) -> dict[str, int]:
        """Require current-session logs plus a fresh debug heartbeat."""
        if self.process is None or self.process.poll() is not None:
            raise RuntimeError("Task-owned game exited")
        heartbeat = GAME / "bag2jp_frame.txt"
        watch = GAME / "bag2jp_watch.log"
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

    def wait(self, predicate: Callable[[dict], bool], timeout: float = TIMEOUT) -> dict:
        """Wait without issuing more inputs; reject timeout instead of restarting."""
        return nav.wait_until(self.maybe_state, lambda value: value is not None and predicate(value), timeout)

    def key(self, side: int, action: str) -> None:
        """Send only an independently bound action to the verified task PID."""
        self.assert_process()
        key = nav.key_for(self.bindings, side, action)
        powershell(f"& {ps_quote(WINSHOT / 'postkey.ps1')} -Id {self.process.pid} -Keys {ps_quote(key)} -HoldMs 100 -GapMs 350 | Out-Null")
        self.actions.append({"player": side, "action": action, "key": key, "time": round(time.time() - self.started, 3)})

    def shot(self, name: str) -> None:
        """Save evidence; this does not claim automatic visual interpretation."""
        self.assert_process()
        path = self.run / f"{name}.png"
        if path.exists():
            raise FileExistsError(path)
        powershell(f"& {ps_quote(WINSHOT / 'winshot.ps1')} -Ids {self.process.pid} -Out {ps_quote(path)} | Out-Null")
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
        time.sleep(1.3)  # Root changes before the menu fade accepts controller inputs.
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
        """Calibrate four local edges, leaving all other roster entries unsupported."""
        if nav.cursor(self.state(), 1) != 0:
            raise ValueError("Probe requires observed initial P1 Heat")
        edges = []
        for action, expected in (("right", 2), ("left", 0), ("down", 1), ("up", 0)):
            source = nav.cursor(self.state(), 1)
            self.move(1, action, expected)
            self.shot(f"probe-{source}-{action}-{expected}")
            edges.append([source, action, expected])
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
        log_path = GAME / "bag2jp_charsel_popup.log"
        # Popup log is truncated on activation in this task-owned process.
        log = nav.wait_until(lambda: session_log(log_path, self.started), lambda text: f"open: side {side-1} char {character} " in text, TIMEOUT)
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
        log = nav.wait_until(lambda: session_log(log_path, self.started), lambda text: f"confirm: side {side-1} char {character} " in text, TIMEOUT)
        observed = nav.confirmation(log, side - 1, character, version, costume)
        self.wait(lambda state: (state[f"p{side}_status"] >> 16 & 255) == 2)
        self.key(side, "circle")  # NORMAL commands, separate from the version popup.
        self.wait(lambda state: (state[f"p{side}_status"] >> 16 & 255) == 3)
        return observed

    def match(self, stage: str, characters: list[int], costumes: list[int], survey: bool = False) -> None:
        """Check stage cursor and then require both selected IDs in gameplay.

        survey: first step through all 14 carousel rows, shooting each one."""
        self.wait(lambda state: state["select_phase"] in (2, 3))
        if survey:
            for step in range(14):
                row = self.state()["stage_position"] >> 16 & 255
                self.shot(f"stage-survey-{step:02d}-row-{row:02d}")
                self.key(1, "left")
                self.wait(lambda current: (current["stage_position"] >> 16 & 255) != row)
        wanted = 0 if stage == "HeatBAG2" else 1
        for _ in range(14):
            state = self.state()
            nav.require_selector(state)
            row = state["stage_position"] >> 16 & 255
            if row == wanted:
                break
            self.key(1, "left")
            self.wait(lambda current: (current["stage_position"] >> 16 & 255) != row)
        if (self.state()["stage_position"] >> 16 & 255) != wanted:
            raise ValueError("Requested stage row not observed")
        self.shot("stage-selected")
        self.key(1, "circle")
        self.wait(nav.is_gameplay, 60)
        state = self.state()
        nav.verify_gameplay(state, characters, costumes)
        self.shot("gameplay")

    def finish_match(self, timeout: float = 420.0, interval: float = 20.0) -> dict:
        """Follow the song to its end and back to character select, keeping evidence.

        Fever runs inside the battle root, so leaving that root - not a phase change -
        marks the song's end; the selector gate then proves the return.
        """
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
            powershell(f"$p=Get-Process -Id {self.process.pid}; $null=$p.CloseMainWindow(); if(-not $p.WaitForExit(15000)) {{throw 'Game did not close; configuration retained for safe recovery'}}")
            self.process.wait(timeout=2)
        for stream in self.logs:
            stream.close()


def main() -> int:
    """CLI entry point: every run writes evidence and an honest machine status."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--action", choices=("probe", "run", "inspect"), default="inspect")
    parser.add_argument("--game-id", type=int)
    parser.add_argument("--tag", default="versus")
    parser.add_argument("--temporary-controls", action="store_true")
    for side in (1, 2):
        parser.add_argument(f"--p{side}-character", default="Heat")
        parser.add_argument(f"--p{side}-version", choices=("BAG1", "BAG2"), default="BAG2")
        parser.add_argument(f"--p{side}-costume", choices=("A", "B"), default="A")
    parser.add_argument("--stage", choices=("HeatBAG2", "HeatBAG1"), default="HeatBAG2")
    parser.add_argument("--stage-survey", action="store_true",
                        help="shoot every stage carousel row before choosing the stage")
    parser.add_argument("--finish", action="store_true",
                        help="follow the song to its end and require the return to character select")
    parser.add_argument("--finish-timeout", type=float, default=420.0,
                        help="seconds allowed for song end plus return")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    if os.name != "nt":
        parser.error("Windows test host required")
    if args.action == "inspect":
        identity = process_identity(args.game_id or 0)
        LOGGER.info(json.dumps({"pid": args.game_id, "identity": identity,
                                "bindings": nav.parse_bindings((GAME / "keybinds.ini").read_text()),
                                "note": "Read-only identity/bindings inspection; no gameplay claim"}))
        return 0
    if not args.temporary_controls or not re.fullmatch(r"[A-Za-z0-9_-]{1,48}", args.tag):
        parser.error("Explicit --temporary-controls and a safe tag are required")
    characters = [nav.validate_pick(getattr(args, f"p{side}_character"), getattr(args, f"p{side}_version"), getattr(args, f"p{side}_costume")) for side in (1, 2)]
    executable_hash = nav.sha256(GAME / "BAG2JP.exe")
    catalog = None
    if args.action == "run":
        catalog = json.loads(CATALOG.read_text())
        nav.validated_edges(catalog, executable_hash)
        nav.verify_catalog_review(catalog)
    # Refuse before any configuration edit, not merely after backing it up.
    if powershell("@(Get-Process BAG2JP -ErrorAction SilentlyContinue).Count") != "0":
        raise ValueError("Active game session; no files changed")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    run = REPO / "_work/versus-runs" / f"{stamp}-{args.tag}"
    run.mkdir(parents=True, exist_ok=False)
    session = Session(run)
    files = nav.IsolatedFiles(GAME, run, safe_to_restore=lambda: session.process is None or session.process.poll() is not None)
    result = {"status": "failed", "requested": vars(args), "runtime_sha256": executable_hash,
              "visual_review": "pending", "evidence": str(run),
              "script_sha256": {name: nav.sha256(Path(__file__).with_name(name)) for name in
                                ("versus_navigation.py", "versus_session.py", "bag2_versus.ps1")}}
    started = time.monotonic()
    try:
        with files:
            try:
                session.start()
                session.menu()
                if args.action == "probe":
                    catalog = session.probe(executable_hash)
                    (run / "catalog.json").write_text(json.dumps(catalog, indent=2))
                    CATALOG.parent.mkdir(parents=True, exist_ok=True)
                    CATALOG.write_text(json.dumps(catalog, indent=2))
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
                        path = GAME / name
                        if path.exists():
                            shutil.copy2(path, run / name)
                finally:
                    session.close()
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
