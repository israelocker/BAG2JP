"""Static and pose audit of every character model variant (regression aid).

Run: PYTHONPATH=. py -3.13 -m tools.move_viewer.audit [--out audit.json] [--samples 5]
Exit status 1 when any variant has a blocking finding (see ``blocking``).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

from .model_codec import load_character
from .pose import animlib, decode_motion, is_empty_motion, pose_model, sample_motion, world_meshes
from .render_offline import character_slot_map

EXPLODE_RATIO = 2.5      # posed extent / rest extent above this counts as an explosion


def audit_variant(base: Path, variant: str, samples: int = 5) -> dict:
    model, bank, tims = load_character(base / f'model_{variant}', base / f'pack_{variant}')
    meshes = [n.mesh for n in model.nodes if n.mesh is not None]
    prims = [p for m in meshes for p in m.primitives]
    r = {'char': base.name, 'variant': variant, 'nodes': len(model.nodes), 'prims': len(prims),
         'roots': len(model.roots)}
    unsupported: dict[str, int] = {}
    for m in meshes:
        for kind, count in m.unsupported.items():
            unsupported[hex(kind)] = unsupported.get(hex(kind), 0) + count
    uv_oob = slot_bad = clut_bad = semi = 0
    for p in prims:
        semi += bool(p.semi_transparency)
        if p.uvs is None:
            continue
        if p.texture_slot is None or p.texture_slot >= len(tims):
            slot_bad += 1
            continue
        tim = tims[p.texture_slot]
        h, w = tim.pixels.shape
        uv_oob += any(u >= w or v >= h for u, v in p.uvs)
        clut_bad += p.clut_row >= len(tim.clut)
    rest = world_meshes(model, pose_model(model))
    skipped = sum(max(p.vertices) >= len(pos)
                  for n, pos in rest.positions.items() for p in model.nodes[n].mesh.primitives)
    points = np.concatenate(list(rest.positions.values()))
    rest_extent = float(np.linalg.norm(points.max(0) - points.min(0)))
    slot_map = character_slot_map(base / f'pack_{variant}', costume=0 if variant.startswith('a') else 1)
    bodies = animlib.anim_list(bank)
    empty, failed, exploded = [], [], []
    for i, body in enumerate(bodies):
        if is_empty_motion(body):
            empty.append(i)
            continue
        try:
            motion = decode_motion(bank, i)
            worst = 0.0
            for f in np.linspace(0, motion['frames'] - 1, samples).round().astype(int):
                pts = np.concatenate(list(world_meshes(
                    model, pose_model(model, sample_motion(motion, int(f)), slot_map)).positions.values()))
                if not np.isfinite(pts).all():
                    worst = float('inf')
                    break
                worst = max(worst, float(np.linalg.norm(pts.max(0) - pts.min(0))) / rest_extent)
        except (IndexError, KeyError, ValueError, ArithmeticError) as error:
            failed.append([i, str(error)[:80]])
            continue
        if worst > EXPLODE_RATIO:
            exploded.append([i, round(worst, 2)])
    r.update(unsupported=unsupported, semi_prims=semi, uv_oob=uv_oob, slot_bad=slot_bad,
             clut_bad=clut_bad, skipped_prims_rest=skipped, motions=len(bodies), empty=empty,
             decode_fail=failed, explode=exploded)
    return r


def blocking(r: dict) -> list[str]:
    """Findings that make a variant fail the audit."""
    keys = ('unsupported', 'uv_oob', 'slot_bad', 'clut_bad', 'skipped_prims_rest',
            'decode_fail', 'explode')
    return [f'{k}={r[k]}' for k in keys if r[k]]


def audit_all(characters: Path, samples: int = 5) -> list[dict]:
    return [audit_variant(c, m.name[6:], samples)
            for c in sorted(characters.iterdir()) if c.is_dir()
            for m in sorted(c.glob('model_*'))]


def main(argv: list[str] | None = None) -> int:
    from tools.workflow.project_config import load_config, require_paths
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--samples', type=int, default=5)
    args = parser.parse_args(argv)
    assets, = require_paths(load_config(), ('inputs.bag2jp_assets',))
    results = audit_all(assets / 'archive' / 'characters', args.samples)
    failures = 0
    for r in results:
        found = blocking(r)
        failures += bool(found)
        print(f"{r['char']}/{r['variant']}: {'FAIL ' + '; '.join(found) if found else 'ok'}"
              f" (motions {r['motions']}, empty {len(r['empty'])})")
    if args.out:
        args.out.write_text(json.dumps(results, indent=1), encoding='utf-8')
    print(f'{len(results)} variants, {failures} failing')
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
