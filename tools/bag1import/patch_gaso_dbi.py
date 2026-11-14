"""Patch Bi-O pack character code (DBI) for the BAG1 Gas-O model.

Based on native BAG1 Gas-O character code analysis (P_GAS_A1.DFS entry 003, SLPS_012.32):
1. Init callback (P1 0x801CEDBC / P2 0x801D58FC):
   Writes native Gas-O's 35 bone-to-channel table stores into actor + 0x7CC.
   Replaces Bi-O's 21 mismatched stores that corrupted 21 of 30 bone animation channels.
2. Postprocess callback (P1 0x801CF1B0 / P2 0x801D5CF0):
   Performs native Gas-O's 7 node transform copies (stride 0xB0) for backpack hoses
   and gas mask tubes:
     - Node 16 -> Node 20
     - Node 19 -> Node 23
     - Node 16 -> Node 21
     - Node 19 -> Node 24
     - Node 19 -> Node 26
     - Node 12 -> Node 25
     - Node 16 -> Node 22
   Eliminates Bi-O's 5 corrupting node copies and zombie calls to FUN_801ceec4,
   FUN_801cd0a4, and FUN_801cccf0.
"""
import struct
from pathlib import Path

P1_DBI_SIZE = 24076
P2_DBI_SIZE = 13448

P1_INIT_OFF = 0x2D38
P1_EVENT_OFF = 0x2E40
P1_POST_OFF = 0x312C
P1_INIT_LEN = 264
P1_EVENT_LEN = 748
P1_POST_LEN = 468

P2_INIT_OFF = 0x2138
P2_EVENT_OFF = 0x2240
P2_POST_OFF = 0x252C
P2_INIT_LEN = 264
P2_EVENT_LEN = 748
P2_POST_LEN = 468

# MIPS registers
R_ZERO = 0
R_V0, R_V1 = 2, 3
R_A0, R_A1, R_A2, R_A3 = 4, 5, 6, 7
R_T0, R_T1, R_T2, R_T3, R_T4, R_T5, R_T6, R_T7 = 8, 9, 10, 11, 12, 13, 14, 15
R_SP = 29
R_RA = 31

def _R(op: int, rs: int, rt: int, rd: int, sa: int, funct: int) -> bytes:
    return struct.pack("<I", (op << 26) | (rs << 21) | (rt << 16) | (rd << 11) | (sa << 6) | funct)

def _I(op: int, rs: int, rt: int, imm: int) -> bytes:
    return struct.pack("<I", (op << 26) | (rs << 21) | (rt << 16) | (imm & 0xFFFF))

def _ADDIU(rt: int, rs: int, imm: int) -> bytes: return _I(0x09, rs, rt, imm)
def _ADDU(rd: int, rs: int, rt: int) -> bytes: return _R(0x00, rs, rt, rd, 0, 0x21)
def _LW(rt: int, rs: int, imm: int) -> bytes: return _I(0x23, rs, rt, imm)
def _SW(rt: int, rs: int, imm: int) -> bytes: return _I(0x2B, rs, rt, imm)
def _SB(rt: int, rs: int, imm: int) -> bytes: return _I(0x28, rs, rt, imm)
def _BEQZ(rs: int, rel_words: int) -> bytes: return _I(0x04, rs, 0, rel_words)
def _BGTZ(rs: int, rel_words: int) -> bytes: return _I(0x07, rs, 0, rel_words)
def _BAL(rel_words: int) -> bytes: return _I(0x01, 0, 0x11, rel_words)
def _JR(rs: int) -> bytes: return _R(0x00, rs, 0, 0, 0, 0x08)
def _NOP() -> bytes: return b"\x00\x00\x00\x00"

# Gas-O hose/tube node copy pairs: (src_offset, dst_offset) with stride 0xB0
GASO_NODE_COPIES = [
    (0x0B00, 0x0DC0),  # Node 16 -> Node 20
    (0x0D10, 0x0FD0),  # Node 19 -> Node 23
    (0x0B00, 0x0E70),  # Node 16 -> Node 21
    (0x0D10, 0x1080),  # Node 19 -> Node 24
    (0x0D10, 0x11E0),  # Node 19 -> Node 26
    (0x0840, 0x1130),  # Node 12 -> Node 25
    (0x0B00, 0x0F20),  # Node 16 -> Node 22
]


def assemble_gaso_init(padded_len: int = 264) -> bytes:
    """Assemble native Gas-O channel binding table stores for actor + 0x7CC."""
    insns = [
        _ADDIU(R_T7, R_ZERO, 1),
        _ADDIU(R_T6, R_ZERO, 2),
        _ADDIU(R_T5, R_ZERO, 3),
        _ADDIU(R_T4, R_ZERO, 4),
        _ADDIU(R_V0, R_ZERO, 5),
        _ADDIU(R_T3, R_ZERO, 6),
        _SB(R_V0, R_A0, 0x07D1),  # Bone 5 = 5
        _ADDIU(R_V0, R_ZERO, 7),
        _ADDIU(R_A1, R_ZERO, 8),
        _SB(R_V0, R_A0, 0x07D3),  # Bone 7 = 7
        _ADDIU(R_V0, R_ZERO, 9),
        _SB(R_V0, R_A0, 0x07D5),  # Bone 9 = 9
        _ADDIU(R_V0, R_ZERO, 10),
        _ADDIU(R_T1, R_ZERO, 11),
        _SB(R_V0, R_A0, 0x07D6),  # Bone 10 = 10
        _ADDIU(R_V0, R_ZERO, 12),
        _ADDIU(R_T2, R_ZERO, 13),
        _ADDIU(R_A3, R_ZERO, 14),
        _ADDIU(R_T0, R_ZERO, 15),
        _ADDIU(R_A2, R_ZERO, 16),
        _SB(R_V0, R_A0, 0x07D9),  # Bone 13 = 12
        _ADDIU(R_V0, R_ZERO, 17),
        _ADDIU(R_V1, R_ZERO, 18),
        _SB(R_V0, R_A0, 0x07DE),  # Bone 18 = 17
        _SB(R_V0, R_A0, 0x07F1),  # Table 2 idx 7 = 17
        _ADDIU(R_V0, R_ZERO, 19),
        _SB(R_ZERO, R_A0, 0x07CC),  # Bone 0 = 0
        _SB(R_T7, R_A0, 0x07CD),    # Bone 1 = 1
        _SB(R_T6, R_A0, 0x07CE),    # Bone 2 = 2
        _SB(R_T5, R_A0, 0x07CF),    # Bone 3 = 3
        _SB(R_T4, R_A0, 0x07D0),    # Bone 4 = 4
        _SB(R_T3, R_A0, 0x07D2),    # Bone 6 = 6
        _SB(R_A1, R_A0, 0x07D4),    # Bone 8 = 8
        _SB(R_T1, R_A0, 0x07D7),    # Bone 11 = 11
        _SB(R_T2, R_A0, 0x07DA),    # Bone 14 = 13
        _SB(R_A3, R_A0, 0x07DB),    # Bone 15 = 14
        _SB(R_T0, R_A0, 0x07DC),    # Bone 16 = 15
        _SB(R_A2, R_A0, 0x07DD),    # Bone 17 = 16
        _SB(R_V1, R_A0, 0x07DF),    # Bone 19 = 18
        _SB(R_ZERO, R_A0, 0x07EA),  # Table 2 idx 0 = 0
        _SB(R_T7, R_A0, 0x07EB),    # Table 2 idx 1 = 1
        _SB(R_T6, R_A0, 0x07EC),    # Table 2 idx 2 = 2
        _SB(R_T5, R_A0, 0x07ED),    # Table 2 idx 3 = 3
        _SB(R_T4, R_A0, 0x07EE),    # Table 2 idx 4 = 4
        _SB(R_T3, R_A0, 0x07EF),    # Table 2 idx 5 = 6
        _SB(R_A1, R_A0, 0x07F0),    # Table 2 idx 6 = 8
        _SB(R_A3, R_A0, 0x07F2),    # Table 2 idx 8 = 14
        _SB(R_T1, R_A0, 0x07F3),    # Table 2 idx 9 = 11
        _SB(R_T0, R_A0, 0x07F4),    # Table 2 idx 10 = 15
        _SB(R_A2, R_A0, 0x07F5),    # Table 2 idx 11 = 16
        _SB(R_V1, R_A0, 0x07F6),    # Table 2 idx 12 = 18
        _SB(R_V0, R_A0, 0x07F7),    # Table 2 idx 13 = 19
        _SB(R_T2, R_A0, 0x080A),    # Table 3 idx 0 = 13
        _JR(R_RA),
        _SB(R_A1, R_A0, 0x080B),    # Table 3 idx 1 = 8 in delay slot
    ]
    raw = b"".join(insns)
    assert len(raw) <= padded_len, f"Init raw length {len(raw)} exceeds {padded_len}"
    return raw + b"\x00" * (padded_len - len(raw))


def assemble_gaso_postprocess(padded_len: int = 468) -> bytes:
    """Assemble native Gas-O hose/tube 7-node transform copies with stride 0xB0."""
    instructions = [
        _ADDIU(R_SP, R_SP, -8),
        _SW(R_RA, R_SP, 4),
        _LW(R_V1, R_A0, 0x28),
        _BEQZ(R_V1, 29),  # Branch to epilogue if node_buf is NULL
        _NOP(),
    ]

    copy_node_idx = 33 + 4  # 37

    for src, dst in GASO_NODE_COPIES:
        instructions.append(_ADDIU(R_A1, R_ZERO, src))
        instructions.append(_ADDIU(R_A2, R_ZERO, dst))
        bal_idx = len(instructions)
        rel = copy_node_idx - (bal_idx + 1)
        instructions.append(_BAL(rel))
        instructions.append(_NOP())

    assert len(instructions) == 33
    # Epilogue:
    instructions.append(_LW(R_RA, R_SP, 4))
    instructions.append(_ADDIU(R_SP, R_SP, 8))
    instructions.append(_JR(R_RA))
    instructions.append(_NOP())

    # copy_node subroutine (index 37):
    assert len(instructions) == copy_node_idx
    instructions.append(_ADDU(R_T0, R_V1, R_A1))
    instructions.append(_ADDU(R_T1, R_V1, R_A2))
    instructions.append(_LW(R_T2, R_T0, 0x28))
    instructions.append(_SW(R_T2, R_T1, 0x28))
    instructions.append(_ADDIU(R_T3, R_ZERO, 10))
    loop_start_idx = len(instructions)
    instructions.append(_LW(R_T2, R_T0, 0))
    instructions.append(_ADDIU(R_T0, R_T0, 4))
    instructions.append(_ADDIU(R_T3, R_T3, -1))
    instructions.append(_SW(R_T2, R_T1, 0))
    bgtz_idx = len(instructions)
    rel_loop = loop_start_idx - (bgtz_idx + 1)
    instructions.append(_BGTZ(R_T3, rel_loop))
    instructions.append(_ADDIU(R_T1, R_T1, 4))
    instructions.append(_JR(R_RA))
    instructions.append(_NOP())

    raw = b"".join(instructions)
    assert len(raw) <= padded_len, f"Postprocess raw length {len(raw)} exceeds {padded_len}"
    return raw + b"\x00" * (padded_len - len(raw))


def assemble_gaso_event(padded_len: int = 748) -> bytes:
    """Assemble stub event handler returning 0 for Gas-O.

    Prevents Bi-O's FUN_801ceec4 from executing invalid jumps to 0x97664, 0x9768c,
    0x97694 and overwriting node pointers in node_buf at 0xCF8 / 0xF08.
    """
    instructions = [
        _JR(R_RA),
        _ADDIU(R_V0, R_ZERO, 0),  # Return 0 in delay slot
    ]
    raw = b"".join(instructions)
    assert len(raw) <= padded_len, f"Event raw length {len(raw)} exceeds {padded_len}"
    return raw + b"\x00" * (padded_len - len(raw))


def patch_gaso_dbi(dbi_data: bytes) -> bytes:
    """Patch Bi-O P1 or P2 character DBI with Gas-O's Init, Event, and Postprocess routines."""
    length = len(dbi_data)
    if length == P1_DBI_SIZE:
        init_off, init_len = P1_INIT_OFF, P1_INIT_LEN
        event_off, event_len = P1_EVENT_OFF, P1_EVENT_LEN
        post_off, post_len = P1_POST_OFF, P1_POST_LEN
    elif length == P2_DBI_SIZE:
        init_off, init_len = P2_INIT_OFF, P2_INIT_LEN
        event_off, event_len = P2_EVENT_OFF, P2_EVENT_LEN
        post_off, post_len = P2_POST_OFF, P2_POST_LEN
    else:
        raise ValueError(f"Unrecognized Bi-O DBI size: {length} bytes (expected {P1_DBI_SIZE} or {P2_DBI_SIZE})")

    out = bytearray(dbi_data)
    out[init_off:init_off + init_len] = assemble_gaso_init(init_len)
    out[event_off:event_off + event_len] = assemble_gaso_event(event_len)
    out[post_off:post_off + post_len] = assemble_gaso_postprocess(post_len)
    return bytes(out)
