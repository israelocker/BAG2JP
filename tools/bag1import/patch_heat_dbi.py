"""Patch BAG2 Heat's character code (pack DBI) for the BAG1 Heat model.

1. The outfit-A init (p1 0x801CEDA8) fills dancer+0x7CC[bone] = animation slot. BAG2 Heat outfit A has
   an extra unanimated bone 12 (chest piece) and the head at bone 13, so it stores slot 12 at bone 13.
   BAG1 Heat has the head at bone 12 and the beanie at bone 13 (child of the head, unanimated), so the
   store `sb v0(=12), 0xd(t8)` becomes `sb v0, 0xc(t8)`: head animated, beanie left at 0xFF.
   Everything else in that table (arms 14-19, hand bones) already matches BAG1.
2. --outfit-b: BAG1 Heat uses the same skeleton for both costumes, so the outfit-B packs run the
   outfit-A path: the `bnez v0` on dancer+6 (costume) in the init (p1 0x801CEDC8) and in the setup
   handler (p1 0x801CFC10, hand bone indices) become nops.
3. The face animation (type-1 values 0x65-0x6a, 0xc9/0xca, p1 FUN_801cefa4) copies BAG2 face rects
   with MoveImage (jal 0x80046c7c, 6 sites) inside the character tpage. With BAG1 textures loaded
   those rects overwrite the BAG1 flame strip used by the attack effect, so every call becomes a
   nop (delay slots only set arguments; the result is unused).
4. The attack fire renderer (p1 FUN_801ce628, called once per slot from FUN_801cc688) samples BAG2
   flame UVs that hold BAG1 textures (white ring, blocky arc). Its call becomes a nop; the slot
   logic (FUN_801cc3cc/FUN_801cc760: hit reaction and cues) still runs. The BAG1 effect is drawn by
   bag2jp.feature.bag1-content (bag2jp_heat_flame.h). The call is found by its pause-check context
   because the jal targets differ between the P1 and P2 links.
usage: patch_heat_dbi.py <dbi in> <dbi out> [--outfit-b]"""
import re
import sys

MOVE_IMAGE_JAL = (0x0C000000 | (0x80046C7C >> 2) & 0x3FFFFFF).to_bytes(4, 'little')
MOVE_IMAGE_SITES = 6
# lui v0,0x8006; lbu v0,-0x2c1c(v0) (pause 0x8005D3E4); nop; bnez v0,+3; move a0,s4;
# jal FUN_801cc760; move a1,s0; jal FUN_801ce628; move a0,s0
ATTACK_RENDER_CALL = re.compile(
    re.escape(bytes.fromhex('0680023c' 'e4d34290' '00000000' '03004014' '21208002')) +
    b'(?:....)' + re.escape(bytes.fromhex('21280002')) + b'(....)' +
    re.escape(bytes.fromhex('21200002')), re.S)

def nop_attack_render(d):
    """Nop the renderer jal; returns its offset, or None when already patched."""
    hits = list(ATTACK_RENDER_CALL.finditer(d))
    assert len(hits) == 1, f'attack render call found {len(hits)} times'
    i = hits[0].start(1)
    if d[i:i + 4] == bytes(4):
        return None
    assert d[i + 3] == 0x0C, 'attack render call is not a jal'
    d[i:i + 4] = bytes(4)
    return i

def patch(d, seq, new_last):
    n = d.count(seq)
    assert n == 1, f'pattern {seq.hex()} found {n} times'
    i = d.find(seq) + len(seq) - 4
    d[i:i + 4] = new_last
    return i - 12

def nop_face_move_image(d):
    sites = [i for i in range(0, len(d) - 3, 4) if d[i:i + 4] == MOVE_IMAGE_JAL]
    assert len(sites) == MOVE_IMAGE_SITES, f'MoveImage jal found {len(sites)} times'
    for i in sites:
        d[i:i + 4] = bytes(4)
    return [i - 12 for i in sites]

if __name__ == '__main__':
    d = bytearray(open(sys.argv[1], 'rb').read())
    offs = [patch(d, bytes.fromhex('0c000224' '0d000924' '0e000624' '0f000724' '10000524' '0d0002a3'),
                  bytes.fromhex('0c0002a3'))]
    if '--outfit-b' in sys.argv:
        offs.append(patch(d, bytes.fromhex('06004292' '00000000' '3a004014'), bytes(4)))
        offs.append(patch(d, bytes.fromhex('06000292' '00000000' '21004014'), bytes(4)))
    offs += nop_face_move_image(d)
    offs.append(nop_attack_render(d))
    open(sys.argv[2], 'wb').write(d)
    print(f'{sys.argv[1]}: patched at payload offsets', ', '.join(f'0x{o:x}' for o in offs))
