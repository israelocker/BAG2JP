"""Pure validation and reversible file operations for BAG2JP versus tests."""
from collections import deque
import configparser
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import shutil
import time
import tomllib
from typing import Callable, TypeVar

T = TypeVar("T")

# JP identities verified by popup logs; this is deliberately not a full roster.
CHARACTERS = {"heat": 0, "strike": 1, "comet": 2}
WATCHES = {
    "root": (0x8005D3D4, 4), "menu": (0x80192028, 4),
    "mode": (0x8005D2C4, 2), "p1_position": (0x800971EC, 4),
    "p1_status": (0x800971F0, 4), "p2_position": (0x8009720C, 4),
    "p2_status": (0x80097210, 4), "selectable": (0x80096FA8, 4),
    "select_phase": (0x80096F94, 4), "stage_position": (0x8009722C, 4),
    "character1": (0x8005E6A0, 4), "character2": (0x8005E6A4, 4),
    "costumes": (0x8005E668, 2),
    "guard1": (0x80091DB0, 4), "guard2": (0x80093138, 4),
    "clock": (0x800892EC, 4),  # Song/native clock keeps gameplay observations advancing.
}
# JP character-select overlay: initialization/active roots plus its module guards.
SELECTOR_ROOTS = (12, 13)
SELECTOR_GUARDS = (0x27BDFFC8, 0x27BDFFB0)
GAMEPLAY_ROOT = 0x13  # Native local-versus module; fever stays inside it.
TEMPORARY_KEYS = {
    1: dict(up="Up", down="Down", left="Left", right="Right", circle="S", cross="X", triangle="A", start="Return"),
    2: dict(up="I", down="K", left="J", right="L", circle="M", cross="N", triangle="V", start="P"),
}


def resolve_character(name: str) -> int:
    """Resolve a supported name without silently choosing Heat."""
    try:
        return CHARACTERS[name.strip().casefold()]
    except KeyError as exc:
        raise ValueError(f"Unsupported character: {name}") from exc


def validate_pick(name: str, version: str, costume: str) -> int:
    """Reject unimplemented versions and invalid costumes before any side effect."""
    character = resolve_character(name)
    if version not in {"BAG1", "BAG2"}:
        raise ValueError(f"Unsupported version: {name} {version}")
    if version == "BAG1" and character not in (0, 1):
        raise ValueError(f"Unsupported BAG1 character: {name}")
    if costume not in {"A", "B"}:
        raise ValueError("Costume must be A or B")
    return character


def parse_bindings(text: str) -> dict[int, dict[str, list[str]]]:
    """Parse both keyboard slots, preserving optional secondary bindings."""
    parser = configparser.ConfigParser(interpolation=None)
    parser.read_string(text)
    return {side: {action: [key.strip() for key in value.split(",") if key.strip().lower() != "none"]
                   for action, value in parser[f"player{side}"].items()}
            for side in (1, 2)}


def key_for(bindings: dict, side: int, action: str) -> str:
    """Find a key which cannot also assert any input on the other controller."""
    if side not in (1, 2):
        raise ValueError("Player must be 1 or 2")
    other_keys = {key.casefold() for keys in bindings[3 - side].values() for key in keys}
    other_keys.update(key.casefold() for other_action, keys in bindings[side].items()
                      if other_action != action for key in keys)
    for key in bindings[side].get(action, []):
        if key.casefold() not in other_keys:
            return key
    raise ValueError(f"P{side} {action} lacks an independent binding")


def route(start: int, target: int, edges: dict[tuple[int, str], int]) -> list[str]:
    """Return the shortest path over explicit edges, never assumed grid offsets."""
    pending = deque([(start, [])])
    visited = {start}
    while pending:
        current, path = pending.popleft()
        if current == target:
            return path
        for (source, action), destination in edges.items():
            if source == current and destination not in visited:
                visited.add(destination)
                pending.append((destination, path + [action]))
    raise ValueError(f"No validated route from character {start} to {target}")


def validated_edges(catalog: dict, runtime_hash: str) -> dict[tuple[int, str], int]:
    """Require unchanged runtime plus explicit visual review of calibrated edges."""
    if catalog.get("runtime_sha256") != runtime_hash or catalog.get("visual_review") != "accepted":
        raise ValueError("Calibration is stale or lacks visual review")
    edges = {}
    for source, action, target in catalog["edges"]:
        if source not in CHARACTERS.values() or target not in CHARACTERS.values() or action not in {"up", "down", "left", "right"}:
            raise ValueError("Unsupported calibrated edge")
        if (source, action) in edges:
            raise ValueError("Duplicate or ambiguous calibrated edge")
        edges[source, action] = target
    return edges


def verify_catalog_images(catalog: dict) -> None:
    """Invalidate visual review if its captured evidence is absent or changed."""
    images = catalog.get("image_sha256", {})
    if not images:
        raise ValueError("Missing reviewed calibration images")
    directory = Path(catalog["evidence"])
    for name, expected in images.items():
        if Path(name).name != name or sha256(directory / name) != expected:
            raise ValueError("Calibration evidence changed; visual review required")


def catalog_review_digest(catalog: dict) -> str:
    """Bind the explicit review to runtime, edges and exact captured evidence."""
    payload = {key: catalog.get(key) for key in ("runtime_sha256", "edges", "image_sha256", "evidence")}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def verify_catalog_review(catalog: dict) -> None:
    """Do not reuse approval if an edge or its evidence was edited afterwards."""
    if catalog.get("reviewed_catalog_sha256") != catalog_review_digest(catalog):
        raise ValueError("Reviewed calibration graph changed")
    verify_catalog_images(catalog)


def is_gameplay(state: dict[str, int]) -> bool:
    """Native local-versus combat root, not selector or an arbitrary stable phase."""
    return state["root"] == GAMEPLAY_ROOT and state["mode"] == 2 and state["phase1"] == 1 and state["phase2"] == 3


def heartbeat_phases(text: str) -> dict[str, int]:
    """Decode only a complete heartbeat record, never an in-progress file write."""
    match = re.fullmatch(r"\d+\s+(\d+)/(\d+)/(\d+)\s*", text)
    if match is None:
        raise ValueError("Incomplete heartbeat")
    return {f"phase{index}": int(value) for index, value in enumerate(match.groups(), 1)}


def parse_watch(line: str) -> dict[str, int]:
    """Decode one complete RAM-watch row; partial rows are not observations."""
    values = {int(address, 16): int(value, 16)
              for address, value in re.findall(r"([0-9A-F]{8})=([0-9A-F]+)", line)}
    if any(address not in values for address, _ in WATCHES.values()):
        raise ValueError("Incomplete watch row")
    return {name: values[address] for name, (address, _) in WATCHES.items()}


def watch_observation(text: str) -> tuple[int, dict[str, int]]:
    """Ignore in-progress trailing rows, even when their last hex value looks valid."""
    for line in reversed(text.split("\n")[:-1]):
        match = re.match(r"f(\d+)\s", line)
        if match is None:
            continue
        try:
            return int(match[1]), parse_watch(line)
        except ValueError:
            continue
    raise ValueError("No complete watch observation")


def check_freshness(heartbeat_time: float, now: float, started: float) -> None:
    """Reject old session data and a stopped/paused heartbeat."""
    if heartbeat_time < started or not 0 <= now - heartbeat_time <= 5:
        raise ValueError("Stale or foreign-session heartbeat")


def check_watch_progress(heartbeat_time: float, watch_time: float, now: float,
                         started: float, heartbeat_frame: int, watch_frame: int) -> None:
    """Reject a frozen watch even if the independent heartbeat is still live."""
    check_freshness(heartbeat_time, now, started)
    check_freshness(watch_time, now, started)
    if abs(heartbeat_frame - watch_frame) > 360:
        raise ValueError("Watch and heartbeat no longer describe a current observation")


def require_versus(state: dict[str, int]) -> None:
    """The popup routes independent ports only in native mode 2."""
    if state["mode"] != 2:
        raise ValueError(f"Expected local versus mode 2, got {state['mode']}")


def require_selector(state: dict[str, int]) -> None:
    """Validate native module identity before reading overlay-local structures."""
    require_versus(state)
    if not is_selector(state):
        raise ValueError("Expected JP character-select overlay")


def is_selector(state: dict[str, int]) -> bool:
    """Same evidence the selector gate requires, usable as a wait predicate."""
    return (state["mode"] == 2 and state["root"] in SELECTOR_ROOTS
            and (state["guard1"], state["guard2"]) == SELECTOR_GUARDS)


def cursor(state: dict[str, int], side: int) -> int:
    """Decode char id at player block +0x1A, not side at +0x19."""
    return (state[f"p{side}_position"] >> 16) & 255


def verify_gameplay(state: dict[str, int], characters: list[int], costumes: list[int]) -> None:
    """Reject a native mirror costume change as well as wrong character IDs."""
    require_versus(state)
    if [state["character1"], state["character2"]] != characters:
        raise ValueError("Gameplay character IDs do not match request")
    if [state["costumes"] & 255, state["costumes"] >> 8 & 255] != costumes:
        raise ValueError("Gameplay costumes do not match request (native mirror rule may apply)")


def confirmation(log: str, side: int, character: int, version: str, costume: str) -> dict:
    """Match the most recent confirmation for the requested side, not any old pick."""
    picks = re.findall(r"confirm: side (\d+) char (\d+) version (BAG1|BAG2|-) costume ([AB])", log)
    picks = [pick for pick in picks if int(pick[0]) == side]
    if not picks:
        raise ValueError("Missing popup confirmation")
    _, actual_character, actual_version, actual_costume = picks[-1]
    actual_version = "BAG2" if actual_version == "-" else actual_version
    if (int(actual_character), actual_version, actual_costume) != (character, version, costume):
        raise ValueError(f"Popup confirmation mismatch: {picks[-1]}")
    return dict(side=side, character=character, version=version, costume=costume)


def sha256(path: Path) -> str:
    """Hash file bytes without loading heavy cards into memory."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def temporary_bindings(text: str) -> str:
    """Replace only P1/P2 action rows used by the test, retaining other slots."""
    for side, mapping in TEMPORARY_KEYS.items():
        pattern = rf"(?ms)^\[player{side}\].*?(?=^\[|\Z)"
        match = re.search(pattern, text)
        if match is None:
            raise ValueError(f"Missing player{side} section")
        section = match.group(0)
        for action, key in mapping.items():
            row = rf"(?m)^{action}\s*=.*$"
            if re.search(row, section):
                section = re.sub(row, f"{action} = {key}", section)
            else:
                section += f"\n{action} = {key}\n"
        text = text[:match.start()] + section + text[match.end():]
    return text


def isolated_settings(text: str, cards: Path) -> str:
    """Redirect cards without serializing or changing unrelated settings."""
    match = re.search(r"(?ms)^\[memcard\].*?(?=^\[|\Z)", text)
    if match is None:
        raise ValueError("Missing memcard section")
    section = match.group(0)
    for action, path in {"dir": cards, "card1": cards / "card1.mcd", "card2": cards / "card2.mcd"}.items():
        section, count = re.subn(rf"(?m)^{action}\s*=.*$", f'{action} = "{path.as_posix()}"', section)
        if count != 1:
            raise ValueError(f"Missing or duplicate memcard {action}")
    return text[:match.start()] + section + text[match.end():]


def wait_until(read: Callable[[], T], accept: Callable[[T], bool], timeout: float,
               clock: Callable[[], float] = time.monotonic,
               sleep: Callable[[float], None] = time.sleep) -> T:
    """Bound every observation wait; do not issue keys while waiting."""
    deadline = clock() + timeout
    last = None
    while clock() < deadline:
        last = read()
        if accept(last):
            return last
        sleep(0.15)
    raise TimeoutError(f"Expected state was not observed; last={last}")


@dataclass
class Backup:
    """One immutable baseline; caller must close its game before restoring."""
    game: Path
    directory: Path
    relative_files: list[str]

    def create(self) -> None:
        """Create a new baseline or fail rather than replace an existing one."""
        self.directory.mkdir(parents=True, exist_ok=False)
        for relative in self.relative_files:
            target = self.directory / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(self.game / relative, target)

    def restore(self) -> dict[str, str]:
        """Restore byte-exact files and return verified SHA256 values."""
        hashes = {}
        for relative in self.relative_files:
            source, target = self.directory / relative, self.game / relative
            shutil.copy2(source, target)
            hashes[relative] = sha256(target)
            if hashes[relative] != sha256(source):
                raise OSError(f"Restoration mismatch: {relative}")
        return hashes


class IsolatedFiles:
    """Reversible test bindings/settings plus separate copied memory cards."""

    def __init__(self, game: Path, run: Path, safe_to_restore: Callable[[], bool] = lambda: True) -> None:
        self.game, self.run = game, run
        self.backup = Backup(game, run / "baseline", ["keybinds.ini", "settings.toml", "mods/state.toml"])
        self.cards: dict[Path, str] = {}
        self.restoration: dict = {}
        self.safe_to_restore = safe_to_restore

    def __enter__(self) -> "IsolatedFiles":
        """Back up before any write, and unwind partial preparation on failure."""
        settings = (self.game / "settings.toml").read_text(encoding="utf-8-sig")
        config = tomllib.loads(settings)
        for path in sorted((self.game / "saves").rglob("*")):
            if path.is_file():
                self.cards[path] = sha256(path)
        self.backup.create()
        prepared = False
        try:
            copied = self.run / "cards"
            copied.mkdir()
            for name in ("card1", "card2"):
                source = (self.game / config["memcard"][name]).resolve()
                if not source.is_relative_to(self.game.resolve()) or source not in self.cards:
                    raise ValueError("Memory card must be an existing file under experimental saves")
                shutil.copy2(source, copied / f"{name}.mcd")
            (self.game / "settings.toml").write_text(isolated_settings(settings, copied), encoding="utf-8")
            original = (self.game / "keybinds.ini").read_text(encoding="utf-8-sig")
            (self.game / "keybinds.ini").write_text(temporary_bindings(original), encoding="utf-8")
            prepared = True
        finally:
            if not prepared:
                self.backup.restore()
        return self

    def __exit__(self, kind: type | None, value: BaseException | None, traceback: object) -> None:
        """Caller closes its process first; prove controls and original saves survived."""
        if not self.safe_to_restore():
            self.restoration = {"verified": False, "reason": "Task process still running; restore after closing it"}
            raise RuntimeError("Cannot restore configuration under a running game")
        self.restoration = {"files": self.backup.restore(), "original_saves": len(self.cards)}
        for path, expected in self.cards.items():
            if sha256(path) != expected:
                raise OSError(f"Original save changed: {path.name}")
        self.restoration["verified"] = True
