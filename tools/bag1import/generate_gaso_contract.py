"""Genera el contrato de animación de Gas-O (BAG1 -> BAG2).

Para cada request number r que Gas-O tiene en BAG1 (según reqmap.py):
- Lee el anim de Gas-O en el slot bag1(r) de su 001.bin
- Determina el rol semántico (del catálogo de roles o "req_{r}")
- Anota el slot BAG2 correspondiente (bag2(r))
- Clasifica estado: mapped / unresolved / duplicate / unused
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from animlib import anim_list, frames, info
from host_inputs import input_path, project_label
import reqmap

# Cargar catálogo de roles para nombres semánticos
roles_path = Path(__file__).with_name("contracts") / "bag1-usa-bag2jp.roles.json"
with roles_path.open() as f:
    roles_catalog = json.load(f)

# Construir lookup: request -> nombre de rol (BAG1)
request_to_role = {}
for role in roles_catalog["games"]["bag1-usa"]["roles"]:
    request_to_role[role["request"]] = role["name"]

# Leer 001.bin de Gas-O
gaso_001 = input_path("inputs.character_inventory") / "gaso" / "001.bin"
gaso_data = gaso_001.read_bytes()
gaso_anims = anim_list(gaso_data)

print("Gas-O 001.bin: %d anims" % len(gaso_anims))


def is_empty(anim_data):
    """Un anim está vacío si todo son ceros o es muy corto."""
    if len(anim_data) < 8:
        return True
    return all(b == 0 for b in anim_data)


slot_has_data = []
for i, anim in enumerate(gaso_anims):
    slot_has_data.append((i, len(anim), frames(anim), is_empty(anim)))

empty_slots = [i for i, _, _, empty in slot_has_data if empty]
print("Slots vacíos en Gas-O 001.bin:", empty_slots)
print("Slots con datos: %d de %d" % (len(gaso_anims) - len(empty_slots), len(gaso_anims)))

contract = {
    "schema": 1,
    "character": "gaso",
    "source_character_id": 9,
    "target_character_id": 9,
    "source_animation_list": project_label(gaso_001),
    "generated_from": "reqmap.py + animlib.py + bag1-usa-bag2jp.roles.json",
    "notes": "Rol semántico determinado por request number. Slots BAG1 de reqmap.py (bag1). Slots BAG2 de reqmap.py (bag2). Estados: mapped (existe en ambos), unresolved (solo en uno), duplicate (mismo rol, múltiples requests), unused (slot vacío en BAG1).",
    "entries": []
}

seen_bag2_slots = {}  # bag2_slot -> list of bag1_requests

for r in range(300):
    bag1_slot = reqmap.bag1(r)
    bag2_slot = reqmap.bag2(r)

    if bag1_slot is None or bag1_slot >= len(gaso_anims):
        continue

    slot_index = bag1_slot
    anim_data = gaso_anims[slot_index]
    anim_len = len(anim_data)
    anim_frames = frames(anim_data)
    anim_empty = is_empty(anim_data)

    role_name = request_to_role.get(r, "req_%d" % r)

    try:
        header, events, info_o, info_p = info(anim_data)
        event_list = [{"type": e[0], "frame": e[1], "value": e[2]} for e in events]
    except Exception as exc:
        event_list = []
        print("  Warning: no se pudieron leer eventos de slot %d: %s" % (slot_index, exc))

    if anim_empty:
        estado = "unused"
    elif bag2_slot is None:
        estado = "unresolved"
    else:
        estado = "mapped"

    if bag2_slot is not None:
        if bag2_slot in seen_bag2_slots:
            seen_bag2_slots[bag2_slot].append(r)
        else:
            seen_bag2_slots[bag2_slot] = [r]

    entry = {
        "bag1_request": r,
        "bag1_slot": bag1_slot,
        "bag2_slot": bag2_slot,
        "rol_semantico": role_name,
        "frames": anim_frames,
        "anim_size_bytes": anim_len,
        "events": event_list,
        "estado": estado,
        "slot_vacio_en_bag1": anim_empty
    }
    contract["entries"].append(entry)

for entry in contract["entries"]:
    if entry["bag2_slot"] is not None:
        requests_for_slot = seen_bag2_slots.get(entry["bag2_slot"], [])
        if len(requests_for_slot) > 1:
            other_requests = [x for x in requests_for_slot if x != entry["bag1_request"]]
            if other_requests:
                entry["estado"] = "duplicate"
                entry["duplicate_of_requests"] = other_requests

mapped = [e for e in contract["entries"] if e["estado"] == "mapped"]
unresolved = [e for e in contract["entries"] if e["estado"] == "unresolved"]
unused = [e for e in contract["entries"] if e["estado"] == "unused"]
duplicate = [e for e in contract["entries"] if e["estado"] == "duplicate"]

print()
print("=== ESTADÍSTICAS DEL CONTRATO ===")
print("Total entries: %d" % len(contract["entries"]))
print("  mapped: %d" % len(mapped))
print("  unresolved: %d" % len(unresolved))
print("  unused: %d" % len(unused))
print("  duplicate: %d" % len(duplicate))

output_path = Path("tools/bag1import/contracts/gaso-animation-contract.json")
with output_path.open("w", encoding="utf-8") as f:
    json.dump(contract, f, indent=2, ensure_ascii=False)

print()
print("Contrato guardado en:", output_path)
