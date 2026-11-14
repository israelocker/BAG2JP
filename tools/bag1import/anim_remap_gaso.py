"""Rebuild Gas-O's BAG2 model animation list (101 slots) from BAG1's 84-animation list.

Uses the shared BAG1->BAG2 dance grid (B2_ROWS, B2_ALT, B1_PATHS, b1_anim, ROLES)
and data-driven policy adaptations (profiles/gaso-animation-policy.json).
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
POLICY_PATH = Path(__file__).resolve().parent / "profiles" / "gaso-animation-policy.json"
POLICY = load_policy(POLICY_PATH, PROJECT_ROOT)
ACCEPTED_POLICY_STATUSES = {"accepted_local", "verified", "proposed"}
CHAR_ID = POLICY.get("target_character_id", 9)
SOURCE_CUE_BASE = POLICY.get("source_cue_base", 0x1800)
FEVER_SOURCES = (82, 83, 82)  # BAG1 FEVER1/FEVER2 (requests 160/161), shared Heat layout


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
    """Keep type-16 projectile trigger at the attack slot, normalising value to 0."""
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
    """Build the 101-slot BAG2 model animation list for Gas-O."""
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


def build_fever(b1_anims: list[bytes], stock_slots: int) -> bytes:
    """Build the solo fever list (choreography_a 000.bin) from BAG1 fever anims 82/83.

    Follows the shared Heat layout (82, 83, 82, then empty slots). Unlike Heat, the
    Gas-O voices stay audible: stock Bi-O fever fires its own voice cues, and the
    BAG1 ids move to the rebased Gas-O bank like the model animations.
    """
    if stock_slots < len(FEVER_SOURCES):
        raise ValueError(f"Stock fever list has {stock_slots} slots, need {len(FEVER_SOURCES)}")
    fever = [
        rebase_events(fix_events(b1_anims[src]), SOURCE_CUE_BASE, b1_cue_base(CHAR_ID), 0x100)
        for src in FEVER_SOURCES
    ]
    fever += [EMPTY] * (stock_slots - len(fever))
    return b"".join(struct.pack("<I", len(anim)) + anim for anim in fever) + b"\x00" * 4


def main() -> int:
    allow_proposed = "--allow-proposed" in sys.argv[1:]
    args = [arg for arg in sys.argv[1:] if arg != "--allow-proposed"]
    if POLICY.get("status") not in ACCEPTED_POLICY_STATUSES and not allow_proposed:
        logging.error("Gas-O animation policy is not accepted; semantic audit is required")
        return 2
    if len(args) < 2:
        logging.error("Usage: anim_remap_gaso.py [--allow-proposed] <bag1_001.bin> <out_model_001.bin>")
        return 1

    src_path = Path(args[0])
    dst_path = Path(args[1])
    b1_anims = anim_list(src_path.read_bytes())
    data, used, missing = build(b1_anims)
    if missing:
        raise ValueError(f"Unmapped Gas-O animation slots: {missing}")

    dst_path.parent.mkdir(parents=True, exist_ok=True)
    dst_path.write_bytes(data)
    print(f"Generated {len(data)} bytes ({len(used)} active slots, {len(b1_anims)} source anims) -> {dst_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
