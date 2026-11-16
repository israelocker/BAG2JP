"""Print the archive folder names of a character's fever choreography (solo, duet).
BAG2 loads them by main exe table 0x8005510C[char id * 2 + fever type - 1] (archive entry index);
the asset folders of entries 17-52 were named by order and are not the character (Heat = id 0 ->
entries 22/40, which sit in "kelly/choreography_a|b").
usage: fever_entries.py <project dir> <char id>"""
import json, struct, sys
from pathlib import Path
from host_inputs import input_path, load_config
P, cid = sys.argv[1], int(sys.argv[2])
d = input_path('inputs.bag2_main_exe', config=load_config(repo_root=Path(P))).read_bytes()
a, b = struct.unpack_from('<2H', d, 0x8005510C - 0x80010000 + 4 * cid)
e = json.load(open(f'{P}/assets/archive/_container.json'))['entries']
print(e[a]['name'], e[b]['name'])
