"""Function-level diff of two PS1 overlay modules (DBI payload at a load base)."""
import sys, struct, json, difflib, capstone
def load(p, base):
    d = open(p, 'rb').read()[12:]
    md = capstone.Cs(capstone.CS_ARCH_MIPS, capstone.CS_MODE_MIPS32); md.detail = False; md.skipdata = True
    ins = list(md.disasm(d, base))
    return d, ins
def funcs(ins):
    # function starts: 'addiu $sp, $sp, -N' after a 'jr $ra' + delay slot, or module start
    starts = [0]
    for k in range(2, len(ins)):
        if ins[k].mnemonic == 'addiu' and ins[k].op_str.startswith('$sp, $sp, -') and \
           (ins[k-2].mnemonic == 'jr' and ins[k-2].op_str == '$ra'):
            starts.append(k)
    starts = sorted(set(starts)); out = []
    for a, b in zip(starts, starts[1:] + [len(ins)]):
        out.append(ins[a:b])
    return out
def norm(i):
    m, o = i.mnemonic, i.op_str
    if m in ('jal', 'j') or m.startswith('b'):
        return m + ' ' + ','.join(x for x in o.split(', ') if x.startswith('$'))   # drop targets
    if m == 'lui': return m + ' ' + o.split(',')[0] + ',HI'
    import re
    def mask(mo):
        v = int(mo.group(0), 16) if mo.group(0).lstrip('-').startswith('0x') else int(mo.group(0))
        return 'X' if abs(v) >= 0x400 else mo.group(0)
    return m + ' ' + re.sub(r'-?0x[0-9a-f]+|-?\b\d+\b', mask, o)
def sig(f): return [norm(i) for i in f]
if __name__ == '__main__':
    (jp, jb), (us, ub) = (sys.argv[1], int(sys.argv[2], 16)), (sys.argv[3], int(sys.argv[4], 16))
    _, ji = load(jp, jb); _, ui = load(us, ub)
    jf, uf = funcs(ji), funcs(ui)
    js, us_ = [tuple(sig(f)) for f in jf], [tuple(sig(f)) for f in uf]
    exact = {}
    for k, s in enumerate(us_): exact.setdefault(s, []).append(k)
    used = set(); rows = []
    for a, s in enumerate(js):
        if s in exact and exact[s]:
            b = exact[s].pop(0); used.add(b); rows.append((a, b, 1.0)); continue
        # best fuzzy match among unused with similar length
        best = (0, None)
        for b, t in enumerate(us_):
            if b in used or abs(len(t) - len(s)) > max(8, len(s) // 3): continue
            r = difflib.SequenceMatcher(None, s, t, autojunk=False).quick_ratio()
            if r > best[0]: best = (r, b)
        if best[1] is not None and best[0] > 0.5:
            r = difflib.SequenceMatcher(None, s, us_[best[1]], autojunk=False).ratio()
            used.add(best[1]); rows.append((a, best[1], round(r, 3)))
        else:
            rows.append((a, None, 0.0))
    out = []
    for a, b, r in rows:
        out.append(dict(jp=hex(jf[a][0].address), jp_len=len(jf[a]), us=hex(uf[b][0].address) if b is not None else None,
                        us_len=len(uf[b]) if b is not None else 0, score=r))
    unmatched_us = [hex(uf[b][0].address) for b in range(len(uf)) if b not in used]
    json.dump(dict(pairs=out, us_only=unmatched_us), open(sys.argv[5], 'w'), indent=0)
    print('functions jp', len(jf), 'us', len(uf), 'identical', sum(1 for x in out if x['score'] == 1.0),
          'changed', sum(1 for x in out if 0 < x['score'] < 1), 'jp-only', sum(1 for x in out if x['us'] is None), 'us-only', len(unmatched_us))
