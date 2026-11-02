"""Convierte las animaciones de BAG1 Strike (001.bin, 84 anims) al formato BAG2 (101 slots).
Adaptado de anim_remap.py de Heat, usando el contrato de animación de Strike."""
import json, logging, sys, os, struct
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from animlib import anim_list, info, frames
from rebase_cues import rebase_events, b1_cue_base

# Cargar política de animación de Strike
POLICY_PATH = Path(__file__).resolve().parent / "profiles" / "strike-animation-policy.json"
with POLICY_PATH.open() as f:
    POLICY = json.load(f)

ACCEPTED_POLICY_STATUSES = {"accepted_local", "verified"}

# Construir mapeo target -> source
ROLES = {row["target"]: row["source"] for row in POLICY["roles"]}

# Slots vacíos en BAG2 (como en Heat)
EMPTY = b'\x00\x00\x00\x00'

# CHAR_ID para Strike (target_character_id = 1)
CHAR_ID = 1

def fix_events(d, attack=False):
    """Reajusta eventos de ataque para BAG2."""
    d = bytearray(d)
    hb, ev, o, end = info(bytes(d))
    p = o + len(hb)
    for t, f, v in ev:
        if t == 16:
            v = 0
            if attack:
                f = 29
        struct.pack_into('<HHH', d, p, t, f, v); p += 6
    return bytes(d)

def mute_voices(d, lo=0x1000, hi=0x2000):
    """Silencia voces de BAG1 en rango de personaje para evitar conflictos."""
    d = bytearray(d)
    hb, ev, o, end = info(bytes(d))
    p = o + len(hb)
    for t, f, v in ev:
        if t in (2, 3) and lo <= v < hi:
            v = 0x1FFF
        struct.pack_into('<HHH', d, p, t, f, v); p += 6
    return bytes(d)

def build(b1_anims):
    """Construye el 001.bin de BAG2 con 101 slots."""
    out = bytearray()
    used = {}
    missing = []
    
    for i in range(101):
        if i in (1, 97):
            # Slots vacíos como en Heat
            data = EMPTY
        elif i in ROLES:
            src = ROLES[i]
            if src >= len(b1_anims):
                missing.append(i)
                data = EMPTY
            else:
                used[i] = src
                data = rebase_events(fix_events(b1_anims[src], attack=(i == 74)), 0x1000, b1_cue_base(CHAR_ID), 0x100)
        else:
            missing.append(i)
            data = EMPTY
        
        out += struct.pack('<I', len(data)) + data
    
    out += b'\x00' * 4  # terminator
    return bytes(out), used, missing

def main():
    if POLICY.get("status") not in ACCEPTED_POLICY_STATUSES:
        logging.error("Strike animation policy is not accepted; semantic audit is required")
        return 2
    if len(sys.argv) < 3:
        print("Uso: anim_remap_strike.py <bag1_001.bin> <out_model_001.bin>")
        return 1
    
    src_path = Path(sys.argv[1])
    dst_path = Path(sys.argv[2])
    
    b1_data = src_path.read_bytes()
    b1_anims = anim_list(b1_data)
    
    print('Strike BAG1: {} animaciones'.format(len(b1_anims)))
    
    data, used, missing = build(b1_anims)
    
    dst_path.write_bytes(data)
    
    print('model 001: {} bytes'.format(len(data)))
    print('Slots usados: {} de 101'.format(len(used)))
    print('Slots vacíos (1, 97): 2')
    print('Slots faltantes (no mapeados): {}'.format(missing))
    print('Mapeo: {}'.format(' '.join('{}<{}'.format(k, v) for k, v in sorted(used.items()))))
    return 0

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    raise SystemExit(main())
