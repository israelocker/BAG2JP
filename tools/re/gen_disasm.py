"""Disassemble MIPS R3000 words recovered from generated recompiler comments.

The generated C files annotate every instruction as ``/* 0xADDR: 0xWORD */``.
This tool rebuilds an address->word map from those comments and prints a
compact disassembly (including GTE/COP2 ops) for an address range, so code can
be read without Ghidra.

Usage:
    py -3.13 tools/re/gen_disasm.py <generated_dir> <start_hex> [count]
"""
from __future__ import annotations

import pathlib
import re
import sys

COMMENT_RE = re.compile(r"/\* 0x([0-9A-F]{8}): 0x([0-9A-F]{8}) \*/")
REG = ["zero", "at", "v0", "v1", "a0", "a1", "a2", "a3",
       "t0", "t1", "t2", "t3", "t4", "t5", "t6", "t7",
       "s0", "s1", "s2", "s3", "s4", "s5", "s6", "s7",
       "t8", "t9", "k0", "k1", "gp", "sp", "fp", "ra"]
GTE_OPS = {0x01: "RTPS", 0x06: "NCLIP", 0x0C: "OP", 0x10: "DPCS", 0x11: "INTPL",
           0x12: "MVMVA", 0x13: "NCDS", 0x14: "CDP", 0x16: "NCDT", 0x1B: "NCCS",
           0x1C: "CC", 0x1E: "NCS", 0x20: "NCT", 0x28: "SQR", 0x29: "DCPL",
           0x2A: "DPCT", 0x2D: "AVSZ3", 0x2E: "AVSZ4", 0x30: "RTPT", 0x3D: "GPF",
           0x3E: "GPL", 0x3F: "NCCT"}
I_OPS = {0x08: "addi", 0x09: "addiu", 0x0A: "slti", 0x0B: "sltiu", 0x0C: "andi",
         0x0D: "ori", 0x0E: "xori"}
MEM_OPS = {0x20: "lb", 0x21: "lh", 0x22: "lwl", 0x23: "lw", 0x24: "lbu", 0x25: "lhu",
           0x26: "lwr", 0x28: "sb", 0x29: "sh", 0x2A: "swl", 0x2B: "sw", 0x2E: "swr",
           0x32: "lwc2", 0x3A: "swc2"}
R_OPS = {0x20: "add", 0x21: "addu", 0x22: "sub", 0x23: "subu", 0x24: "and",
         0x25: "or", 0x26: "xor", 0x27: "nor", 0x2A: "slt", 0x2B: "sltu"}
SHIFT_OPS = {0x00: "sll", 0x02: "srl", 0x03: "sra"}
SHIFTV_OPS = {0x04: "sllv", 0x06: "srlv", 0x07: "srav"}


JAL_RE = re.compile(r"cpu->gpr\[31\] = 0x([0-9A-F]{8})u;  /\* jal link.*?jal -> 0x([0-9A-F]{8})",
                    re.S)


def load_words(gen_dir: pathlib.Path) -> tuple[dict[int, int], dict[int, str]]:
    """Return instruction words plus text for jal sites the generator inlines."""
    words: dict[int, int] = {}
    calls: dict[int, str] = {}
    for path in sorted(gen_dir.glob("*full*.c")):
        text = path.read_text(errors="replace")
        for match in COMMENT_RE.finditer(text):
            words[int(match.group(1), 16)] = int(match.group(2), 16)
        for match in JAL_RE.finditer(text):
            calls[int(match.group(1), 16) - 8] = f"jal 0x{match.group(2)}"
    return words, calls


def simm(value: int) -> int:
    return value - 0x10000 if value & 0x8000 else value


def disasm(addr: int, word: int) -> str:
    op = word >> 26
    rs, rt, rd = (word >> 21) & 31, (word >> 16) & 31, (word >> 11) & 31
    sa, fn, imm = (word >> 6) & 31, word & 63, word & 0xFFFF
    if word == 0:
        return "nop"
    if op == 0:
        if fn in SHIFT_OPS:
            return f"{SHIFT_OPS[fn]} {REG[rd]}, {REG[rt]}, {sa}"
        if fn in SHIFTV_OPS:
            return f"{SHIFTV_OPS[fn]} {REG[rd]}, {REG[rt]}, {REG[rs]}"
        if fn in R_OPS:
            return f"{R_OPS[fn]} {REG[rd]}, {REG[rs]}, {REG[rt]}"
        names = {0x08: f"jr {REG[rs]}", 0x09: f"jalr {REG[rd]}, {REG[rs]}",
                 0x10: f"mfhi {REG[rd]}", 0x12: f"mflo {REG[rd]}",
                 0x11: f"mthi {REG[rs]}", 0x13: f"mtlo {REG[rs]}",
                 0x18: f"mult {REG[rs]}, {REG[rt]}", 0x19: f"multu {REG[rs]}, {REG[rt]}",
                 0x1A: f"div {REG[rs]}, {REG[rt]}", 0x1B: f"divu {REG[rs]}, {REG[rt]}"}
        return names.get(fn, f".word 0x{word:08X}")
    if op == 1:
        name = {0: "bltz", 1: "bgez", 16: "bltzal", 17: "bgezal"}.get(rt, "regimm?")
        return f"{name} {REG[rs]}, 0x{addr + 4 + (simm(imm) << 2) & 0xFFFFFFFF:08X}"
    if op in (2, 3):
        target = ((addr + 4) & 0xF0000000) | ((word & 0x3FFFFFF) << 2)
        return f"{'j' if op == 2 else 'jal'} 0x{target:08X}"
    if op in (4, 5, 6, 7):
        name = {4: "beq", 5: "bne", 6: "blez", 7: "bgtz"}[op]
        target = (addr + 4 + (simm(imm) << 2)) & 0xFFFFFFFF
        return f"{name} {REG[rs]}, {REG[rt]}, 0x{target:08X}"
    if op == 0x0F:
        return f"lui {REG[rt]}, 0x{imm:04X}"
    if op in I_OPS:
        shown = imm if op in (0x0C, 0x0D, 0x0E) else simm(imm)
        return f"{I_OPS[op]} {REG[rt]}, {REG[rs]}, {shown}"
    if op in MEM_OPS:
        dst = f"gte{rt}" if op in (0x32, 0x3A) else REG[rt]
        return f"{MEM_OPS[op]} {dst}, {simm(imm)}({REG[rs]})"
    if op == 0x12:
        if rs & 0x10:
            cmd = word & 0x1FFFFFF
            return (f"{GTE_OPS.get(cmd & 0x3F, 'gte?')} sf={(cmd >> 19) & 1} "
                    f"mx={(cmd >> 17) & 3} v={(cmd >> 15) & 3} cv={(cmd >> 13) & 3} "
                    f"lm={(cmd >> 10) & 1}")
        name = {0: "mfc2", 2: "cfc2", 4: "mtc2", 6: "ctc2"}.get(rs, "cop2?")
        return f"{name} {REG[rt]}, ${rd}"
    return f".word 0x{word:08X}"


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(__doc__)
        return 2
    words, calls = load_words(pathlib.Path(argv[1]))
    start = int(argv[2], 16)
    count = int(argv[3]) if len(argv) > 3 else 64
    for index in range(count):
        addr = start + index * 4
        word = words.get(addr)
        text = calls.get(addr, "??") if word is None else disasm(addr, word)
        print(f"{addr:08X}: {text}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
