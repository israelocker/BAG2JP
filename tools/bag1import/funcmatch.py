"""Find BAG2 main-exe equivalents of BAG1 main-exe functions by masked byte matching.
usage: funcmatch.py addr [addr...]  (BAG1 addresses, hex)"""
import struct, sys
from host_inputs import input_path
B1 = input_path('inputs.bag1_main_exe').read_bytes(); B2 = input_path('inputs.bag2_main_exe').read_bytes()
BASE = 0x80010000
def words(b): return struct.unpack('<%dI' % (len(b) // 4), b[:len(b) // 4 * 4])
W1, W2 = words(B1), words(B2)
def mask(w):
    op = w >> 26
    if op in (2, 3): return w & 0xFC000000                  # j / jal target
    if op == 0x0F: return w & 0xFFFF0000                    # lui imm
    if op in (0x08, 0x09, 0x0D, 0x20, 0x21, 0x23, 0x24, 0x25, 0x28, 0x29, 0x2B):
        rs = (w >> 21) & 31
        if rs != 29: return w & 0xFFFF0000                  # not $sp-relative: global lo16
    return w
def body(W, i, maxw=200):
    out = []
    for k in range(maxw):
        out.append(W[i + k])
        if W[i + k] == 0x03E00008:                          # jr ra (+ delay slot)
            out.append(W[i + k + 1]); break
    return out
M2 = [mask(w) for w in W2]
def find(a1):
    b = body(W1, (a1 - BASE) // 4); m = [mask(w) for w in b]; n = len(m)
    hits = [BASE + 4 * j for j in range(len(M2) - n) if M2[j] == m[0] and M2[j:j + n] == m]
    return n, hits
if __name__ == '__main__':
    for a in sys.argv[1:]:
        n, h = find(int(a, 16))
        print(a, f'{n} words ->', ' '.join(hex(x) for x in h[:5]) or 'NO MATCH')
