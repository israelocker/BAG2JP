"""Build an experimental stage DFS from audited profile data; never deploy it."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from animlib import dfs_entries
import model_bag1_to_bag2 as model
import port_bag1_stage as stage
from rebuild_dfs_members import build_container
import tim_retarget as tim


def build_from_project(root, name):
    root = Path(root)
    profile = stage.load_profile(name)
    config = profile['package']
    source = dfs_entries((root / config['source']).read_bytes())
    common = dfs_entries((root / config['common']).read_bytes())
    stock = sorted(path for path in (root / config['stock']).glob('[0-9][0-9][0-9].*')
                   if path.suffix in {'.dbi', '.sedt', '.tim', '.bin'})
    members = [path.read_bytes() for path in stock]
    if len(members) != 14:
        raise ValueError('Expected audited 14-member destination stage')
    chart = stage.bag1_chart((root / config['exe']).read_bytes(), profile['stage_id'],
                            table=config['chart_table'], header=0x800)
    members[0], stats, _, unknown = stage.build(source[0], members[0], chart, profile,
        main_exe=(root / '_work/mainexe/slpm.bin').read_bytes())
    if unknown:
        raise ValueError(f'Unmapped stage calls: {unknown}')
    if config.get('native_sfx_bank0'):
        import preserve_announcer as pa
        native_banks = pa.banks(source[1])
        stock_banks = pa.banks(members[1])
        members[1] = pa.pack_banks([native_banks[0]] + stock_banks[1:])
    textures = [source[index] for index in config['texture_entries']]
    for item in config['common_textures']:
        flags, clut, image = tim.parse(common[item['entry']])
        if 'image_xy' in item:
            image = dict(image, x=item['image_xy'][0], y=item['image_xy'][1])
        clut = dict(clut, x=item['clut_xy'][0], y=item['clut_xy'][1])
        textures.append(tim.build(flags, clut, image))
    if len(textures) > 9:
        raise ValueError('Too many textures for destination descriptors')
    textures += [source[config['padding_texture_entry']]] * (9 - len(textures))
    members[2:11] = textures
    members[11], model_stats, tail = model.convert(source[config['model_entry']],
                                                  scale=tuple(config['model_scale']))
    if tail or model.check_bag2(members[11]):
        raise ValueError('Converted model failed structural validation')
    camera = source[config['camera_entry']]
    if camera[-4:] != bytes(4) or struct.unpack_from('<I', camera)[0] + 8 != len(camera):
        raise ValueError('Expected one native intro camera track')
    first_stock_track = struct.unpack_from('<I', members[12])[0]
    members[12] = camera[:-4] + members[12][4 + first_stock_track:]
    if config['empty_animation_list']:
        members[13] = bytes(4)
    result = build_container(members)
    if dfs_entries(result) != members:
        raise ValueError('Stage container round-trip failed')
    return result, {'profile': name, 'sha256': hashlib.sha256(result).hexdigest(),
                    'bytes': len(result), 'unmapped_calls': unknown, 'relocations': stats,
                    'model': model_stats, 'experimental': True,
                    'limitations': ['stock stage sound bank', 'empty animation list',
                                    'atlas placement requires live verification']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--profile', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    data, report = build_from_project(args.root, args.profile)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(data)
    args.output.with_suffix('.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
