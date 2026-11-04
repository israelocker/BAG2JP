"""Rebuild Strike's BAG2 model animation list (101 slots) from BAG1's 84-animation list.

Uses the shared BAG1->BAG2 dance grid (B2_ROWS, B2_ALT, B1_PATHS, b1_anim, ROLES)
and data-driven policy adaptations (profiles/strike-animation-policy.json).
"""
import json
import logging
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from animation_policy import adapt_events, load_policy, native_variant
from anim_remap import B1_PATHS, B2_ALT, B2_ROWS, EMPTY, ROLES, b1_anim
from animlib import anim_list, info
from rebase_cues import b1_cue_base, rebase_events

PROJECT_ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = Path(__file__).resolve().parent / "profiles" / "strike-animation-policy.json"
POLICY = load_policy(POLICY_PATH, PROJECT_ROOT)
ACCEPTED_POLICY_STATUSES = {"accepted_local", "verified"}
CHAR_ID = POLICY.get("target_character_id", 1)
SOURCE_CUE_BASE = POLICY.get("source_cue_base", 0x1200)


def dance_slots(policy: dict | None = None) -> dict[int, int]:
    """Map BAG2 dance grid slots (2..53) to BAG1 slots with native predecessor variants."""
    active_policy = policy or POLICY
    slots: dict[int, int] = {}
    for level, (s0, row) in B2_ROWS.items():
        path = B1_PATHS[level]
        for index, slot in enumerate(row):
            slots[slot] = b1_anim(path[index], path[index - 1] if index else None)
            step = s0 + index
            if slot in B2_ALT:
                prev_s0, _ = B2_ROWS[level - 1]
                slots[B2_ALT[slot]] = b1_anim(path[index], B1_PATHS[level - 1][step - 1 - prev_s0])
    for edge in active_policy.get("alternate_edges", []):
        slots[edge["slot"]] = native_variant(
            slots[edge["normal_slot"]],
            slots[edge["previous_slot"]],
            active_policy.get("native_transitions", []),
        )
    return slots


def fix_events(data: bytes, attack: bool = False) -> bytes:
    """Keep one type-16 projectile trigger (value 0) at the first shot frame on attack slots."""
    header, events, offset, _ = info(data)
    if not any(event_type == 16 for event_type, _, _ in events):
        return data
    updated: list[tuple[int, int, int]] = []
    seen_attack = False
    for event_type, frame, value in events:
        if event_type == 16:
            if not attack or seen_attack:
                continue
            seen_attack = True
            updated.append((16, frame, 0))
        else:
            updated.append((event_type, frame, value))
    result = (
        data[:offset]
        + header
        + b"".join(struct.pack("<HHH", *event) for event in updated)
        + bytes(2)
    )
    return result + bytes((-len(result)) % 4)


def build(b1_anims: list[bytes], policy: dict | None = None) -> tuple[bytes, dict[int, int], list[int]]:
    """Build the 101-slot BAG2 model animation list for Strike."""
    active_policy = policy or POLICY
    slots = dance_slots(active_policy)
    slots.update(ROLES)
    rules = {row["target"]: row for row in active_policy["roles"]}
    slots.update({slot: row["source"] for slot, row in rules.items()})

    out = bytearray()
    used: dict[int, int] = {}
    missing: list[int] = []
    for index in range(101):
        if index in (1, 97):
            data = EMPTY
        elif index not in slots or not 0 <= slots[index] < len(b1_anims):
            missing.append(index)
            data = EMPTY
        else:
            src = slots[index]
            used[index] = src
            data = rebase_events(
                fix_events(b1_anims[src], attack=(index == 74)),
                SOURCE_CUE_BASE,
                b1_cue_base(CHAR_ID),
                0x100,
            )
            if index in rules:
                data = adapt_events(data, rules[index])
                data += bytes((-len(data)) % 4)
        out += struct.pack("<I", len(data)) + data
    out += b"\x00" * 4
    return bytes(out), used, missing


def main() -> int:
    allow_proposed = "--allow-proposed" in sys.argv[1:]
    args = [arg for arg in sys.argv[1:] if arg != "--allow-proposed"]
    if POLICY.get("status") not in ACCEPTED_POLICY_STATUSES and not allow_proposed:
        logging.error("Strike animation policy is not accepted; semantic audit is required")
        return 2
    if len(args) < 2:
        logging.error("Usage: anim_remap_strike.py [--allow-proposed] <bag1_001.bin> <out_model_001.bin>")
        return 1

    src_path = Path(args[0])
    dst_path = Path(args[1])
    b1_anims = anim_list(src_path.read_bytes())
    data, used, missing = build(b1_anims)
    if missing:
        raise ValueError(f"Unmapped Strike animation slots: {missing}")
    dst_path.write_bytes(data)
    logging.info("Strike 001.bin: %d bytes, %d/101 active slots populated", len(data), len(used))
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    raise SystemExit(main())
