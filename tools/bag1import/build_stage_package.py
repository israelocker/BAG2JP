"""Build an experimental stage DFS from audited profile data; never deploy it."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from animlib import dfs_entries
import model_bag1_to_bag2 as model
import stage_geometry
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
    if len(members) not in (13, 14):
        raise ValueError(f'Expected audited 13 or 14-member destination stage, got {len(members)}')
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
    scale = tuple(config['model_scale']) if config.get('model_scale') else None
    flatten_type2 = bool(config.get('flatten_type2', False))
    members[11], model_stats, tail = model.convert(source[config['model_entry']],
                                                  scale=scale,
                                                  flatten_type2=flatten_type2)
    members[11] = stage_geometry.subdivide_ft4_meshes(members[11], config.get('ft4_subdivisions', []))
    if tail or model.check_bag2(members[11]):
        raise ValueError('Converted model failed structural validation')
    camera = source[config['camera_entry']]
    if camera[-4:] != bytes(4) or struct.unpack_from('<I', camera)[0] + 8 != len(camera):
        raise ValueError('Expected one native intro camera track')
    cam_speed = float(config.get('camera_speed', 1.0))
    if cam_speed != 1.0:
        c_track_len, c_flags_keys = struct.unpack_from('<II', camera, 0)
        c_flags = c_flags_keys >> 16
        c_nkeys = c_flags_keys & 0xFFFF
        c_keys = [struct.unpack_from('<6h', camera, 8 + i * 12) for i in range(c_nkeys)]
        # Target total frames matching stock track 0 (e.g. 165 frames for stage 197)
        first_stock_track = struct.unpack_from('<I', members[12])[0]
        s_flags_keys = struct.unpack_from('<I', members[12], 4)[0]
        s_target_keys = s_flags_keys & 0xFFFF
        resampled_keys = []
        for out_f in range(s_target_keys):
            in_pos = out_f * cam_speed
            if in_pos >= c_nkeys - 1:
                resampled_keys.append(c_keys[-1])
            else:
                i0 = int(in_pos)
                i1 = min(i0 + 1, c_nkeys - 1)
                frac = in_pos - i0
                k0 = c_keys[i0]
                k1 = c_keys[i1]
                resampled_keys.append(tuple(int(round(k0[c] + (k1[c] - k0[c]) * frac)) for c in range(6)))
        new_track_len = 4 + len(resampled_keys) * 12
        new_cam = struct.pack('<II', new_track_len, (c_flags << 16) | len(resampled_keys))
        for rk in resampled_keys:
            new_cam += struct.pack('<6h', *rk)
        new_cam += bytes(4)
        camera = new_cam
    cam_scale = float(config.get('camera_scale', 1.0))
    if cam_scale != 1.0:
        # Keys are s16 eye xyz + target xyz: scale the eye-target distance, keep the target.
        c_track_len, c_flags_keys = struct.unpack_from('<II', camera, 0)
        c_nkeys = c_flags_keys & 0xFFFF
        if c_track_len != 4 + c_nkeys * 12:
            raise ValueError('camera_scale expects 12-byte eye/target keys')
        body = bytearray()
        for i in range(c_nkeys):
            k = struct.unpack_from('<6h', camera, 8 + i * 12)
            eye = [int(round(k[3 + c] + (k[c] - k[3 + c]) * cam_scale)) for c in range(3)]
            if any(not -0x8000 <= v <= 0x7FFF for v in eye):
                raise ValueError(f'camera_scale {cam_scale} overflows s16 at key {i}: {eye}')
            body += struct.pack('<6h', *eye, k[3], k[4], k[5])
        camera = struct.pack('<II', c_track_len, c_flags_keys) + body + bytes(4)
    first_stock_track = struct.unpack_from('<I', members[12])[0]
    members[12] = camera[:-4] + members[12][4 + first_stock_track:]
    if config.get('empty_animation_list') and len(members) > 13:
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
