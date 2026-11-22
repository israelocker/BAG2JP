"""Prototype: derive the per-player node->track map (player+0x7CC, 30 bytes, 0xFF = unmapped).

Evidence (Ghidra, SLPM_862.19):
  FUN_800319fc (player init) fills player[0x7CC..0x7E9] = 0xFF, then calls the character DBI
  init through table 0x800535DC[char_id + side*19] (char 6 / 12 hard-wired to 0x801CF1E8 etc.).
  FUN_8002bc38 passes player+0x7CC to FUN_80012b9c, which, for node i<30, uses track map[i]
  (0xFF -> node keeps rest pose, flag 0x80000000).
The map is hard-coded in each DBI init (sb immediates, branch on costume byte player[6]), so
the only exact derivation is to execute that init. This file emulates it with capstone.
"""
import struct, sys
from pathlib import Path
from capstone import Cs, CS_ARCH_MIPS, CS_MODE_MIPS32, CS_MODE_LITTLE_ENDIAN
from capstone.mips import MIPS_OP_REG, MIPS_OP_IMM, MIPS_OP_MEM

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
from tools.workflow.project_config import load_config, require_paths  # noqa: E402


def _exe_path() -> Path:
    return require_paths(load_config(repo_root=ROOT), ('inputs.bag2_main_exe',))[0]


EXE_BASE = 0x80010000
INIT_TABLE = 0x800535DC
MAP_OFF, MAP_LEN, MAP2_OFF, MAP2_LEN = 0x7CC, 30, 0x7EA, 36
P1_DBI_BASE = 0x801CC084   # verified below: table entries land on prologues with this base
P2_DBI_BASE = 0x801D37C4   # native second-player DBI load region, same init-table stride
PLAYER = 0x10000000

md = Cs(CS_ARCH_MIPS, CS_MODE_MIPS32 + CS_MODE_LITTLE_ENDIAN)
md.detail = True


def init_table(side: int = 0) -> list[int]:
    exe = _exe_path().read_bytes()
    off = INIT_TABLE - EXE_BASE + side * 19 * 4
    t = list(struct.unpack_from('<19I', exe, off))
    # FUN_800319fc hard-wires chars 6 and 12 instead of using the table.
    # Columbo's DBI (9208 B) has its init at the TABLE entry 0x801CD194 and nothing at
    # 0x801CE818, so for 12 keep both candidates (see report: unresolved).
    hard = (0x801CF1E8, 0x801CE818) if side == 0 else (0x801D6928, 0x801D5F58)
    return [[a] for a in t[:6]] + [[hard[0]]] + [[a] for a in t[7:12]] + \
        [[hard[1], t[12]]] + [[a] for a in t[13:]]


def map_writer_start(dbi: bytes, base: int, addr: int) -> bool:
    """Entry plausibility: an 'addiu rX, rY, 0x7CC' or (BAG1 Bi-O) an 'sb rX, 0x7CC+i(rY)'
    within the first 8 instructions."""
    off = addr - base
    for k in range(8):
        if not 0 <= off + 4 * k < len(dbi) - 3:
            return False
        w = struct.unpack_from('<I', dbi, off + 4 * k)[0]
        if (w >> 26) == 0x09 and (w & 0xFFFF) == MAP_OFF:
            return True
        if (w >> 26) == 0x28 and MAP_OFF <= (w & 0xFFFF) < MAP_OFF + MAP_LEN:
            return True
    return False


def emulate_init(dbi: bytes, base: int, entry: int, costume: int = 0, max_steps: int = 4000):
    """Run the DBI init until its outer jr ra; return bytes written to player memory."""
    regs = {r: 0 for r in range(32)}
    regs_by_name = {}
    mem: dict[int, int] = {}
    mem[PLAYER + 6] = costume
    for i in range(MAP_LEN):
        mem[PLAYER + MAP_OFF + i] = 0xFF
    R = {}
    def rid(name):
        return md.reg_id(name) if False else name
    reg = {}  # name -> value
    def g(n):
        return 0 if n == 'zero' else reg.get(n, 0)
    def s(n, v):
        if n != 'zero':
            reg[n] = v & 0xFFFFFFFF
    s('a0', PLAYER); s('sp', 0x1F800F00); s('ra', 0xDEAD0000)
    pc, delay = entry, None
    depth = 0
    for _ in range(max_steps):
        off = pc - base
        if pc == 0xDEAD0000 or not 0 <= off < len(dbi):
            break
        ins = next(md.disasm(dbi[off:off + 4], pc), None)
        if ins is None:
            raise NotImplementedError(f'{pc:08x} undecodable')
        m, ops = ins.mnemonic, ins.operands
        rn = lambda k: ins.reg_name(ops[k].reg)
        nxt = pc + 4
        target = None
        def ea():
            o = ops[-1]
            return (g(ins.reg_name(o.mem.base)) + o.mem.disp) & 0xFFFFFFFF
        if m in ('addiu', 'addi'):
            s(rn(0), g(rn(1)) + ops[2].imm)
        elif m == 'li':
            s(rn(0), ops[1].imm)
        elif m in ('move',):
            s(rn(0), g(rn(1)))
        elif m in ('addu', 'add'):
            s(rn(0), g(rn(1)) + g(rn(2)))
        elif m in ('subu', 'sub'):
            s(rn(0), g(rn(1)) - g(rn(2)))
        elif m == 'or':
            s(rn(0), g(rn(1)) | g(rn(2)))
        elif m == 'ori':
            s(rn(0), g(rn(1)) | ops[2].imm)
        elif m == 'andi':
            s(rn(0), g(rn(1)) & ops[2].imm)
        elif m == 'and':
            s(rn(0), g(rn(1)) & g(rn(2)))
        elif m == 'lui':
            s(rn(0), ops[1].imm << 16)
        elif m == 'sll':
            s(rn(0), g(rn(1)) << ops[2].imm)
        elif m == 'srl':
            s(rn(0), g(rn(1)) >> ops[2].imm)
        elif m == 'sra':
            v = g(rn(1)); v = v - (1 << 32) if v & 0x80000000 else v
            s(rn(0), v >> ops[2].imm)
        elif m in ('xor', 'nor', 'sllv', 'srlv', 'srav', 'mult', 'multu', 'div', 'divu',
                   'mflo', 'mfhi', 'xori'):
            # Not needed for the map writes seen; mark destination unknown (0).
            if ops and ops[0].type == MIPS_OP_REG and m not in ('mult', 'multu', 'div', 'divu'):
                s(rn(0), 0)
        elif m in ('slti', 'sltiu'):
            s(rn(0), int(g(rn(1)) < (ops[2].imm & 0xFFFFFFFF if m == 'sltiu' else ops[2].imm)))
        elif m in ('slt', 'sltu'):
            s(rn(0), int(g(rn(1)) < g(rn(2))))
        elif m in ('lbu', 'lb'):
            v = mem.get(ea(), 0)
            s(rn(0), v - 256 if m == 'lb' and v & 0x80 else v)
        elif m in ('lhu', 'lh', 'lw'):
            a = ea(); n = 2 if m != 'lw' else 4
            s(rn(0), sum(mem.get(a + k, 0) << (8 * k) for k in range(n)))
        elif m in ('sb', 'sh', 'sw'):
            a = ea(); n = {'sb': 1, 'sh': 2, 'sw': 4}[m]
            for k in range(n):
                mem[a + k] = (g(rn(0)) >> (8 * k)) & 0xFF
        elif m == 'nop':
            pass
        elif m in ('b', 'j'):
            target = ops[0].imm
        elif m in ('beqz', 'bnez', 'bgez', 'bltz', 'blez', 'bgtz'):
            v = g(rn(0)); v = v - (1 << 32) if v & 0x80000000 else v
            take = {'beqz': v == 0, 'bnez': v != 0, 'bgez': v >= 0, 'bltz': v < 0,
                    'blez': v <= 0, 'bgtz': v > 0}[m]
            target = ops[1].imm if take else None
        elif m in ('beq', 'bne'):
            take = (g(rn(0)) == g(rn(1))) == (m == 'beq')
            target = ops[2].imm if take else None
        elif m == 'jr':
            target = g(rn(0))
        elif m in ('jal', 'jalr'):
            # Calls (sound/effect setup) do not touch the map in observed DBIs; skip, v0 = 0.
            s('v0', 0)
        else:
            raise NotImplementedError(f'{pc:08x} {m} {ins.op_str}')
        if delay is not None:
            pc, delay = delay, None
        else:
            pc = nxt
        if target is not None:
            # execute delay slot next, then jump
            delay = target
            continue
    return mem


def read_map(mem, off, n):
    return [mem.get(PLAYER + off + i, 0xFF) for i in range(n)]


def is_prologue(dbi: bytes, base: int, addr: int) -> bool:
    off = addr - base
    if not 0 <= off < len(dbi) - 4:
        return False
    w = struct.unpack_from('<I', dbi, off)[0]
    return (w >> 16) == 0x27BD and (w & 0x8000)          # addiu sp, sp, -N


def find_char_id(dbi: bytes, base: int = P1_DBI_BASE, side: int = 0):
    hits = []
    for cid, cands in enumerate(init_table(side)):
      for addr in cands:
        if map_writer_start(dbi, base, addr):
            try:
                mem = emulate_init(dbi, base, addr)
            except NotImplementedError as e:
                print(f'   [id {cid}: {e}]')
                continue
            mp = read_map(mem, MAP_OFF, MAP_LEN)
            if mp[0] == 0 and sum(v != 0xFF for v in mp) >= 10:
                hits.append((cid, addr))
    return hits


def derive_slot_map(dbi: bytes, char_id: int, costume: int = 0, side: int = 0,
                    base: int = P1_DBI_BASE) -> list[int]:
    cands = [a for a in init_table(side)[char_id] if map_writer_start(dbi, base, a)]
    entry = cands[0]
    return read_map(emulate_init(dbi, base, entry, costume), MAP_OFF, MAP_LEN)


def main():
    from move_viewer.model_codec import parse_model
    from move_viewer.pose import decode_motion, HEAT_SLOT_MAP
    for d in sorted((ROOT / 'assets/archive/characters').iterdir()):
        for cos in 'ab':
            pk, mdir = d / f'pack_{cos}_p1', d / f'model_{cos}_p1'
            dbis = sorted(pk.glob('*.dbi')) if pk.exists() else []
            if not dbis or not mdir.exists():
                continue
            dbi = dbis[0].read_bytes()
            ids = find_char_id(dbi)
            model = parse_model((mdir / '000.bin').read_bytes())
            try:
                dec = decode_motion((mdir / '001.bin').read_bytes(), 71)
                ntr = len(dec['rotations'])
            except Exception as e:  # noqa: BLE001
                ntr = f'err {e.__class__.__name__}'
            for cid, _entry in ids:
                m = derive_slot_map(dbi, cid, costume=0 if cos == 'a' else 1)
                mapped = [t for t in m if t != 0xFF]
                txt = ' '.join('--' if t == 0xFF else f'{t:2d}' for t in m)
                extra = ''
                if d.name == 'heat' and cos == 'a':
                    extra = ' HEAT_MATCH=' + str(m[:len(HEAT_SLOT_MAP)] == HEAT_SLOT_MAP
                                                  and all(t == 0xFF for t in m[len(HEAT_SLOT_MAP):]))
                print(f'{d.name:13s} {cos} id={cid:2d} nodes={len(model.nodes):2d} '
                      f'maxtrack+1={max(mapped) + 1 if mapped else 0:2d} tracks71={ntr}{extra}\n   {txt}')
            if not ids:
                print(f'{d.name:13s} {cos} NO INIT FOUND')


if __name__ == '__main__':
    main()
