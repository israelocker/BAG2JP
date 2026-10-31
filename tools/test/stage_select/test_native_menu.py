"""Check original JP words, carousel mappings and the patched MIPS random remainder."""
from pathlib import Path
import argparse
import re
import struct

root = Path(__file__).resolve().parents[3]
p = argparse.ArgumentParser()
p.add_argument("--stock", action="store_true", help="Run against stock behavior (expected regression failure)")
p.add_argument("--module", type=Path, default=root / "assets/archive/system/007.dbi")
a = p.parse_args()
raw = a.module.read_bytes()
assert raw[:4] == b"DBI_", "Requires the original extracted JP system/007.dbi"
image = bytearray(raw[12:])
base = 0x8008F890
header = (root / "mods-src/bag2jp.feature.bag1-content/bag2jp_stage_select_patches.h").read_text()
patches = [tuple(int(x, 16) for x in m) for m in re.findall(
    r"\{0x([0-9A-F]+)u, 0x([0-9A-F]+)u, 0x([0-9A-F]+)u\}", header)]
assert len(patches) == 23
for addr, old, new in patches:
    assert struct.unpack_from("<I", image, addr - base)[0] == old, f"Unexpected JP word at {addr:x}"
    if not a.stock:
        struct.pack_into("<I", image, addr - base, new)
for addr, word in [(0x800917A8, 0x00531021), (0x80093DB0, 0x145E0002), (0x80093E38, 0x0C007EFF)]:
    assert struct.unpack_from("<I", image, addr - base)[0] == word
arrays = {name: list(map(int, values.split(","))) for name, values in re.findall(
    r"cs_stage_(\w+)\[16\] = \{([^}]+)\}", header)}
for name, addr in [("order", 0x800963D0), ("inverse", 0x800963E0)]:
    assert list(image[addr-base:addr-base+16]) == arrays[name + "_stock"]
    if not a.stock:
        image[addr-base:addr-base+16] = bytes(arrays[name + "_expanded"])

def remainder(n):
    registers = [0] * 32
    registers[2] = n
    hi = 0
    def signed(x):
        return x if x < 0x80000000 else x - 0x100000000
    for addr in range(0x8009177C, 0x800917A8, 4):
        word = struct.unpack_from("<I", image, addr-base)[0]
        op, rs, rt = word >> 26, (word >> 21) & 31, (word >> 16) & 31
        rd, shift, fn, imm = (word >> 11) & 31, (word >> 6) & 31, word & 63, word & 65535
        if op == 15: registers[rt] = imm << 16
        elif op == 13: registers[rt] = registers[rs] | imm
        elif op == 0:
            if fn == 24: hi = ((signed(registers[rs]) * signed(registers[rt])) >> 32) & 0xFFFFFFFF
            elif fn == 16: registers[rd] = hi
            elif fn == 3: registers[rd] = (signed(registers[rt]) >> shift) & 0xFFFFFFFF
            elif fn == 0: registers[rd] = (registers[rt] << shift) & 0xFFFFFFFF
            elif fn == 33: registers[rd] = (registers[rs] + registers[rt]) & 0xFFFFFFFF
            elif fn == 35: registers[rd] = (registers[rs] - registers[rt]) & 0xFFFFFFFF
            else: raise AssertionError(hex(word))
        else: raise AssertionError(hex(word))
    return registers[2]

assert remainder(13) == 0, "Random selection still has only 12 stage choices"
for n in list(range(32768)) + [0x7FFFFFFF, 0x7FFFFFFE, 123456789, 1000000000]:
    assert remainder(n) == n % 13, (n, remainder(n))
assert struct.unpack_from("<I", image, 0x80091268-base)[0] & 65535 == 14
order = list(image[0x800963D0-base:0x800963E0-base])
inverse = list(image[0x800963E0-base:0x800963F0-base])
assert order[:2] == [0, 0] and order[2:13] == arrays["order_stock"][1:12]
assert inverse[12] == 13
for character in range(12):
    assert order[inverse[character]] == character
print("PASS: JP word guards, 14-row carousel, inverse mapping and MIPS random modulo 13")
