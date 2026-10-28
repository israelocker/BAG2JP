"""JP -> US asset groups for bag2jp.localization.regional (one Launcher choice each)."""
import json, os
J = os.path.expanduser('~/mnt/Dev/Recomp/BAG2JP/assets/archive')
U = os.path.expanduser('~/work/bag2us/assets/archive')
rows = json.load(open(os.path.expanduser('~/work/regional/member_diff.json')))
em = json.load(open(os.path.expanduser('~/work/regional/entry_map.json')))
upath = {int(k): v for k, v in em['us_paths'].items()}

def us(entry_idx, member):
    return os.path.join(os.path.dirname(U), upath[entry_idx], member)

def groups():
    g = {k: [] for k in ('title_screen', 'boot_logos', 'hiro_icon', 'stage_signs', 'comet_outfit', 'songs')}
    for ji, jp, ui, name, sz, info in rows:
        if not name.endswith('.tim'):
            continue
        rel = os.path.join(jp.replace('archive/', ''), name)
        src = ('copy', us(ui, name))
        if jp == 'archive/system/016':
            g['title_screen'].append((rel, src))
        elif jp == 'archive/system/012' and name == '004.tim':
            g['title_screen'].append((rel, src))
        elif jp == 'archive/system/011.bpe':
            g['boot_logos'].append((rel, ('rehead', us(ui, name)) if name in ('content/004.tim', 'content/005.tim') else src))
        elif jp == 'archive/system/015.bpe' and name == 'content/001.tim':
            g['hiro_icon'].append((rel, src))
        elif jp == 'archive/system/015.bpe' and name == 'content/033.tim':
            g['stage_signs'].append((rel, src))
        elif 'characters/' in jp and name == '000.tim' and '/pack_' in jp:
            g['hiro_icon'].append((rel, src))
        elif 'characters/hiro/' in jp and '/pack_' in jp:
            g['hiro_icon'].append((rel, src))
        elif 'characters/comet/pack_b' in jp:
            g['comet_outfit'].append((rel, src))
        elif jp == 'archive/system/013' and name in ('014.tim', '017.tim', '018.tim', '020.tim'):
            g['songs'].append((rel, src))       # song names on character select
        elif jp.startswith('archive/stages/'):
            g['stage_signs'].append((rel, src))
    g['title_screen'].append(('system/016/004.tim', ('transparent', 11)))
    return g

if __name__ == '__main__':
    for k, v in groups().items():
        print(k, len(v))
        for rel, src in v:
            print('   ', rel, src[0])
