"""Per-character move tables of BAG2JP, read from the main executable and the match overlay.

Every table value comes from the binaries; only the role layout (which request codes a
role uses) mirrors constants in the match overlay code, documented in
_work/move-roles/move-roles-report.md. Static evidence only: not validated in game.

Usage: py -3.13 tools/move_viewer/move_tables.py [--out-dir DIR]
"""
from __future__ import annotations

import argparse
import csv
import json
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools" / "bag1import"))
import animlib  # noqa: E402
from tools.workflow.project_config import assert_write_target, load_config, require_paths  # noqa: E402

MAIN_BASE = 0x80010000
OVERLAY_BASE = 0x8008F890

# Main executable tables (resolver FUN_8002A090 and overlay readers).
NAME_POINTERS = 0x8005147C
REQ_SLOT_LOW = 0x8005180C      # requests 0..0x2A
REQ_SLOT_MID = 0x8005182E      # requests 0x2B..99 (0 or > 0x4F = none)
REQ_SLOT_HIGH = 0x8005181C     # requests 100..199
REQ_SLOT_DOWN = 0x800518E4     # requests 200..299
ALTERNATES = 0x80051838        # 10 x (from slot, to slot, if previous, pad)
ALTERNATE_COUNT = 10
POSE_COUNTS = 0x800517D0
FEVER_COUNTS = 0x800517F8
VOICE_SET = 0x80051320         # 1 selects the 4-entry Groovin' voice table
HIT_REQUEST = 0x80051458       # per character (request, units)
SCORE = 0x80051378             # halfword per request
SCORE_COUNT = (HIT_REQUEST - SCORE) // 2
# The hit table ends where the name table starts: one row per playable character.
CHARACTER_ROWS = (NAME_POINTERS - HIT_REQUEST) // 2
SOLO_LISTS = 0x8004DA14        # row starts, then 4/8/16-beat solo codes
SOLO_LISTS_END = 0x8004DA30

# Match overlay tables.
NEXT_BY_FLAG = 0x8009E818      # byte pair per grid request 0..0x2A
NEXT_STEP = 0x8009E83E         # byte per request 0..0x50
GROOVIN_VOICE_ROW = 0x8009E918  # 3 halfwords (finish 22/16/10)
GROOVIN_VOICE_SET1 = 0x8009E920  # 4 halfwords (finish 40/36/30, voice set 1)
GROOVIN_VOICE_SET0 = 0x8009E928  # 3 halfwords (finish 40/36/30, other sets)
SOLO_CHAIN = 0x8009E938        # 4-byte records (code, units, dance request, 0)

# Request codes compared in the overlay code (see report).
FINISH_REQUESTS = (4, 10, 16, 22, 30, 36, 40, 42)
GRID_LAST = 41


@dataclass(frozen=True)
class Image:
    data: bytes
    base: int
    label: str

    def offset(self, address: int, size: int = 1) -> int:
        off = address - self.base
        if off < 0 or off + size > len(self.data):
            raise ValueError(f"{self.label}: 0x{address:08X}+{size} outside image")
        return off

    def u8(self, address: int) -> int:
        return self.data[self.offset(address)]

    def u16(self, address: int) -> int:
        return struct.unpack_from("<H", self.data, self.offset(address, 2))[0]

    def u32(self, address: int) -> int:
        return struct.unpack_from("<I", self.data, self.offset(address, 4))[0]

    def bytes(self, address: int, size: int) -> bytes:
        off = self.offset(address, size)
        return self.data[off:off + size]

    def cstring(self, address: int) -> str:
        off = self.offset(address)
        end = self.data.index(b"\0", off)
        return self.data[off:end].decode("ascii")


def character_names(exe: Image) -> list[str]:
    """Name pointer table; stops at the first value that is not a printable string."""
    names = []
    address = NAME_POINTERS
    while True:
        pointer = exe.u32(address)
        if not MAIN_BASE <= pointer < MAIN_BASE + len(exe.data):
            break
        name = exe.cstring(pointer)
        if not name or not name.isprintable():
            break
        names.append(name)
        address += 4
    if not names or names[0] != "HEAT":
        raise ValueError("main executable: character name table not found (wrong base?)")
    return names


def resolve_slot(exe: Image, request: int) -> int | None:
    """Request -> model animation slot, as FUN_8002A090 (alternates excluded)."""
    if request < 0:
        return None
    if request < 0x2B:
        return exe.u8(REQ_SLOT_LOW + request)
    if request < 100:
        value = exe.u8(REQ_SLOT_MID + request)
        return None if value == 0 or value > 0x4F else value
    if request < 200:
        return exe.u8(REQ_SLOT_HIGH + request)
    if request < 300:
        return exe.u8(REQ_SLOT_DOWN + request - 200)
    return None


def solo_lists(exe: Image) -> dict[str, list[int]]:
    raw = exe.bytes(SOLO_LISTS, SOLO_LISTS_END - SOLO_LISTS)

    def run(start: int) -> list[int]:
        out = []
        for value in raw[start:start + 8]:
            if value == 0:
                break
            out.append(value)
        return out
    return {"row_start": run(0), "solo4": run(8), "solo8": run(16), "solo16": run(24)}


def solo_chain(overlay: Image) -> list[dict]:
    records = []
    address = SOLO_CHAIN
    while overlay.u8(address + 1) != 0:
        code, units, request, _ = overlay.bytes(address, 4)
        records.append({"code": code, "units": units, "request": request})
        address += 4
    return records


def halfwords(image: Image, address: int, count: int) -> list[int]:
    return [image.u16(address + 2 * i) for i in range(count)]


def global_tables(exe: Image, overlay: Image) -> dict:
    alternates = []
    for i in range(ALTERNATE_COUNT):
        a, b, c, d = exe.bytes(ALTERNATES + 4 * i, 4)
        alternates.append({"from_slot": a, "to_slot": b, "if_previous": c, "extra": d})
    return {
        "request_slot": {str(r): s for r in range(300) if (s := resolve_slot(exe, r)) is not None},
        "alternates": alternates,
        "score_by_request": halfwords(exe, SCORE, SCORE_COUNT),
        "solo_lists": solo_lists(exe),
        "solo_chain": solo_chain(overlay),
        "next_by_flag": [list(overlay.bytes(NEXT_BY_FLAG + 2 * r, 2)) for r in range(0x2B)],
        "next_step": list(overlay.bytes(NEXT_STEP, 0x51)),
        "groovin_voice": {"row": halfwords(overlay, GROOVIN_VOICE_ROW, 3),
                          "set1": halfwords(overlay, GROOVIN_VOICE_SET1, 4),
                          "set0": halfwords(overlay, GROOVIN_VOICE_SET0, 3)},
    }


def role_requests(exe: Image, overlay: Image, char_id: int) -> list[tuple[str, str, int]]:
    """(role, label, request) for one character, in tree order."""
    poses = exe.u8(POSE_COUNTS + char_id)
    fevers = exe.u8(FEVER_COUNTS + char_id)
    hit_request = exe.u8(HIT_REQUEST + 2 * char_id)
    out: list[tuple[str, str, int]] = [
        ("Start", "WAIT", 106), ("Start", "INDIVIDUAL1", 103), ("Start", "INDIVIDUAL2", 104),
        ("Start", "NEUTRAL", 0)]
    row_ends = sorted(FINISH_REQUESTS)
    level, first = 0, 1
    for end in row_ends:
        for bar, request in enumerate(range(first, min(end, GRID_LAST) + 1)):
            if request not in FINISH_REQUESTS:
                out.append(("Grid", f"L{level} bar {bar + 1}", request))
        level, first = level + 1, end + 1
    out += [("Finish/Groovin", f"FINISH L{i}", r) for i, r in enumerate(row_ends)]
    out += [("Pose", f"POSE{i + 1}", 101 + i) for i in range(poses)]
    by_code = {rec["code"]: rec for rec in solo_chain(overlay)}
    lists = solo_lists(exe)
    for key, title in (("solo4", "Solo 4"), ("solo8", "Solo 8"), ("solo16", "Solo 16")):
        for code in lists[key]:
            if code in by_code:
                rec = by_code[code]
                out.append((title, f"code {code} ({rec['units']} bars)", rec["request"]))
    out += [("Miss", f"MISS{i + 1}", 124 + i) for i in range(5)] + [("Miss", "MISS special", 129)]
    out += [("Attack/Dodge/Guard/Reflect", n, r) for n, r in
            (("ATTACK", 110), ("DODGE", 170), ("GUARD", 171), ("REFLECT", 172))]
    out += [("Tired", "TIRED", 123)]
    out += [("Down", f"DOWN{i + 1}", 200 + i) for i in range(3)]
    if hit_request:
        out.append(("Down", "hit reaction (0x80051458)", hit_request))
    out += [("Fever", f"FEVER{i + 1}", 160 + i) for i in range(fevers)]
    out += [("Duet end", f"DUET{r - 179}", r) for r in range(180, 186)]
    out += [("Duet end", f"DUET{r - 189} alt", r) for r in range(190, 196)]
    out += [("Duet end", "special", 186)]
    out += [("Win/Lose", f"WIN{i + 1}", 140 + i) for i in range(4)]
    out += [("Win/Lose", f"LOSE{i + 1}", 150 + i) for i in range(3)]
    return out


def model_frames(assets: Path | None, name: str, variant: str) -> list[int] | None:
    """Frame count per slot from the character's model 001.bin, or None if absent."""
    if assets is None:
        return None
    folder = name.lower().replace("&", "_").replace("-", "_").replace(" ", "_")
    path = assets / "archive" / "characters" / folder / f"model_{variant}_p1" / "001.bin"
    if not path.is_file():
        return None
    return [animlib.frames(a) for a in animlib.anim_list(path.read_bytes())]


def build(exe: Image, overlay: Image, assets: Path | None = None) -> dict:
    names = character_names(exe)
    characters = []
    for char_id, name in enumerate(names[:CHARACTER_ROWS]):
        frames = {v: model_frames(assets, name, v) for v in ("a", "b")}
        moves = []
        for role, label, request in role_requests(exe, overlay, char_id):
            slot = resolve_slot(exe, request)
            move = {"role": role, "label": label, "request": request, "slot": slot}
            for variant, table in frames.items():
                ok = table is not None and slot is not None and slot < len(table)
                move[f"frames_{variant}"] = table[slot] if ok else None
            moves.append(move)
        characters.append({
            "id": char_id, "name": name,
            "pose_count": exe.u8(POSE_COUNTS + char_id),
            "fever_count": exe.u8(FEVER_COUNTS + char_id),
            "voice_set": exe.u8(VOICE_SET + char_id),
            "hit_request": list(exe.bytes(HIT_REQUEST + 2 * char_id, 2)),
            "model_slots": {v: (len(t) if t is not None else None) for v, t in frames.items()},
            "moves": moves})
    return {"source": {"main_exe": exe.label, "overlay": overlay.label,
                       "status": "static extraction; roles not validated in game",
                       "names_without_rows": names[CHARACTER_ROWS:]},
            "global": global_tables(exe, overlay), "characters": characters}


def write_outputs(result: dict, out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path, csv_path = out_dir / "move_tables.json", out_dir / "move_tables.csv"
    json_path.write_text(json.dumps(result, indent=1), encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["char_id", "name", "role", "label", "request", "slot", "frames_a", "frames_b"])
        for char in result["characters"]:
            for m in char["moves"]:
                writer.writerow([char["id"], char["name"], m["role"], m["label"], m["request"],
                                 m["slot"], m["frames_a"], m["frames_b"]])
    return json_path, csv_path


def load_default() -> dict:
    config = load_config(repo_root=ROOT)
    exe_path, overlay_path, assets = require_paths(
        config, ("inputs.bag2_main_exe", "inputs.bag2_match_overlay", "inputs.bag2jp_assets"))
    exe = Image(exe_path.read_bytes(), MAIN_BASE, exe_path.name)
    overlay = Image(overlay_path.read_bytes(), OVERLAY_BASE, overlay_path.name)
    return build(exe, overlay, assets)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out-dir", type=Path, help="defaults to paths.move_viewer_work")
    args = parser.parse_args(argv)
    config = load_config(repo_root=ROOT)
    out_dir = assert_write_target(
        config, args.out_dir or require_paths(config, ("paths.move_viewer_work",))[0], role="work")
    result = load_default()
    paths = write_outputs(result, out_dir)
    print(f"{len(result['characters'])} characters -> {paths[0]} , {paths[1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
