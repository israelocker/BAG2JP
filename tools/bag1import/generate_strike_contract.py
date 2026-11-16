"""Genera el contrato de animación de Strike (BAG1 -> BAG2).

Para cada request number r que Strike tiene en BAG1 (según reqmap.py):
- Lee el anim de Strike en el slot bag1(r) de su 001.bin
- Determina el rol semántico (del catálogo de roles o "req_{r}")
- Anota el slot BAG2 correspondiente (bag2(r))
- Clasifica estado: mapped / unresolved / duplicate / unused
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from animlib import anim_list, frames, info

# Importar reqmap para obtener el mapeo request -> slot
sys.path.insert(0, str(Path(__file__).parent))
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

# Leer 001.bin de Strike
strike_001 = input_path("inputs.character_inventory") / "strike" / "001.bin"
strike_data = strike_001.read_bytes()
strike_anims = anim_list(strike_data)

print("Strike 001.bin: %d anims" % len(strike_anims))

# Verificar qué slots tienen datos reales (no vacíos)
def is_empty(anim_data):
    """Un anim está vacío si todo son ceros o es muy corto."""
    if len(anim_data) < 8:
        return True
    # Verificar si el header y datos son todos ceros
    return all(b == 0 for b in anim_data)

slot_has_data = []
for i, anim in enumerate(strike_anims):
    slot_has_data.append((i, len(anim), frames(anim), is_empty(anim)))

# Mostrar slots vacíos
empty_slots = [i for i, _, _, empty in slot_has_data if empty]
print("Slots vacíos en Strike 001.bin:", empty_slots)
print("Slots con datos: %d de %d" % (84 - len(empty_slots), 84))

# Generar contrato de animación
contract = {
    "schema": 1,
    "character": "strike",
    "source_character_id": 1,
    "target_character_id": 1,
    "source_animation_list": project_label(strike_001),
    "generated_from": "reqmap.py + animlib.py + bag1-usa-bag2jp.roles.json",
    "notes": "Rol semántico determinado por request number. Slots BAG1 de reqmap.py (bag1). Slots BAG2 de reqmap.py (bag2). Estados: mapped (existe en ambos), unresolved (solo en uno), duplicate (mismo rol, múltiples requests), unused (slot vacío en BAG1).",
    "entries": []
}

seen_bag2_slots = {}  # bag2_slot -> list of bag1_requests

# Recorrer todos los requests de 0 a 299
for r in range(300):
    bag1_slot = reqmap.bag1(r)
    bag2_slot = reqmap.bag2(r)

    # Solo interesar requests que Strike usa en BAG1 (slot 0-83, no None)
    if bag1_slot is None or bag1_slot >= len(strike_anims):
        continue

    slot_index = bag1_slot
    anim_data = strike_anims[slot_index]
    anim_len = len(anim_data)
    anim_frames = frames(anim_data)
    anim_empty = is_empty(anim_data)

    # Rol semántico
    role_name = request_to_role.get(r, "req_%d" % r)

    # Eventos del anim
    try:
        header, events, info_o, info_p = info(anim_data)
        event_list = [{"type": e[0], "frame": e[1], "value": e[2]} for e in events]
    except Exception as exc:
        event_list = []
        print("  Warning: no se pudieron leer eventos de slot %d: %s" % (slot_index, exc))

    # Determinar estado
    if anim_empty:
        estado = "unused"
    elif bag2_slot is None:
        estado = "unresolved"  # Strike tiene la anim en BAG1 pero BAG2 no tiene slot para ella
    else:
        estado = "mapped"

    # Detectar duplicados en BAG2 (múltiples requests BAG1 mapeando al mismo slot BAG2)
    if bag2_slot is not None:
        if bag2_slot in seen_bag2_slots:
            seen_bag2_slots[bag2_slot].append(r)
            # Marcar este como duplicate si otro ya ocupa el mismo slot BAG2 con el mismo rol
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

# Marcar duplicados en BAG2
for entry in contract["entries"]:
    if entry["bag2_slot"] is not None:
        requests_for_slot = seen_bag2_slots.get(entry["bag2_slot"], [])
        if len(requests_for_slot) > 1:
            # Si múltiples requests BAG1 mapean al mismo slot BAG2, son duplicados
            # (a menos que sean diferentes roles semánticos - en ese caso es una adaptación)
            other_requests = [x for x in requests_for_slot if x != entry["bag1_request"]]
            if other_requests:
                entry["estado"] = "duplicate"
                entry["duplicate_of_requests"] = other_requests

# Estadísticas
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

print()
print("=== UNRESOLVED (en BAG1 pero sin slot BAG2) ===")
for e in unresolved:
    print("  req %d (slot BAG1 %d, rol %s)" % (e["bag1_request"], e["bag1_slot"], e["rol_semantico"]))

print()
print("=== UNUSED (slots vacíos en BAG1) ===")
for e in unused:
    print("  req %d (slot BAG1 %d, rol %s)" % (e["bag1_request"], e["bag1_slot"], e["rol_semantico"]))

print()
print("=== DUPLICATE (múltiples requests BAG1 al mismo slot BAG2) ===")
for e in duplicate:
    print("  req %d (slot BAG1 %d, slot BAG2 %d, rol %s, dup_of %s)" % (
        e["bag1_request"], e["bag1_slot"], e["bag2_slot"], e["rol_semantico"],
        e.get("duplicate_of_requests", [])))

# Guardar contrato
output_path = Path("tools/bag1import/contracts/strike-animation-contract.json")
with output_path.open("w", encoding="utf-8") as f:
    json.dump(contract, f, indent=2, ensure_ascii=False)

print()
print("Contrato guardado en:", output_path)
