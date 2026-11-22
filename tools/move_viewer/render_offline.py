"""Software-render a posed BAG2 model to PNG and export OBJ (spike S0, offline only).

Usage (from the project root):
  py -3.13 -m tools.move_viewer.render_offline --character heat --motion 71 --out _work/move-viewer/s0
Orthographic camera; model +Y is up (screen rows use -Y). Textured texels are modulated by
the vertex colour / 128 like the PS1 GPU; semi-transparency and dithering are not emulated.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import numpy as np
from PIL import Image

from .model_codec import Model, Tim, clut_to_rgba, load_character
from .pose import (HEAT_SLOT_MAP, NodePose, WorldMesh, decode_motion, pose_model,
                   sample_motion, world_meshes)

logger = logging.getLogger('move_viewer.render')


def character_slot_map(pack: Path, costume: int) -> list[int]:
    """Node->track map from the character DBI init (see slot_map.py); fails if not derivable."""
    from .slot_map import P1_DBI_BASE, P2_DBI_BASE, derive_slot_map, find_char_id
    side = 1 if pack.name.endswith('_p2') else 0
    base = P2_DBI_BASE if side else P1_DBI_BASE
    dbi = sorted(pack.glob('*.dbi'))[0].read_bytes()
    hits = find_char_id(dbi, side=side, base=base)
    if not hits:
        raise SystemExit(f'{pack}: no DBI init writes player+0x7CC')
    return derive_slot_map(dbi, hits[0][0], costume=costume, side=side, base=base)
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.workflow.project_config import assert_write_target, load_config, require_paths  # noqa: E402
BACKGROUND = (40, 40, 48)
GPU_NEUTRAL = 128.0


def triangles(model: Model, world: WorldMesh):
    """Yield (xyz[3], rgb[3], uv[3] | None, texture slot, clut row) per triangle."""
    for n, pos in world.positions.items():
        for p in model.nodes[n].mesh.primitives:
            corners = [(0, 1, 2), (1, 3, 2)] if p.quad else [(0, 1, 2)]
            for tri in corners:
                if max(p.vertices[i] for i in tri) >= len(pos):
                    continue
                xyz = np.array([pos[p.vertices[i]] for i in tri])
                rgb = np.array([p.vertex_rgb[i] if p.vertex_rgb else p.rgb if p.rgb is not None
                                else world.colors[p.colors[i]]
                                if p.colors[i] < len(world.colors) else (128, 128, 128) for i in tri], float)
                uv = np.array([p.uvs[i] for i in tri], float) if p.uvs else None
                yield xyz, rgb, uv, p.texture_slot, p.clut_row


def rotate_view(xyz: np.ndarray, yaw_deg: float) -> np.ndarray:
    a = np.radians(yaw_deg)
    m = np.array([[np.cos(a), 0, np.sin(a)], [0, 1, 0], [-np.sin(a), 0, np.cos(a)]])
    return xyz @ m.T


def render(model: Model, world: WorldMesh, tims: list[Tim], size=(360, 520),
           yaw_deg: float = 0.0, bounds: tuple[np.ndarray, float] | None = None) -> Image.Image:
    """Z-buffered orthographic raster of all decoded triangles."""
    w, h = size
    tris = list(triangles(model, world))
    allp = rotate_view(np.concatenate([t[0] for t in tris]), yaw_deg)
    if bounds is None:
        lo, hi = allp.min(0), allp.max(0)
        center, extent = (lo + hi) / 2, max(hi[0] - lo[0], (hi[1] - lo[1]) * w / h) * 1.1
        bounds = (center, extent)
    center, extent = bounds
    k = w / extent
    img = np.zeros((h, w, 3)) + BACKGROUND
    zbuf = np.full((h, w), np.inf)
    palettes = {}
    for xyz, rgb, uv, slot, row in tris:
        p = rotate_view(xyz, yaw_deg)
        sx = (p[:, 0] - center[0]) * k + w / 2
        sy = -(p[:, 1] - center[1]) * k + h / 2
        x0, x1 = int(max(np.floor(sx.min()), 0)), int(min(np.ceil(sx.max()), w - 1))
        y0, y1 = int(max(np.floor(sy.min()), 0)), int(min(np.ceil(sy.max()), h - 1))
        if x0 > x1 or y0 > y1:
            continue
        area = (sx[1] - sx[0]) * (sy[2] - sy[0]) - (sx[2] - sx[0]) * (sy[1] - sy[0])
        if abs(area) < 1e-9:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        b1 = ((gx - sx[0]) * (sy[2] - sy[0]) - (sx[2] - sx[0]) * (gy - sy[0])) / area
        b2 = ((sx[1] - sx[0]) * (gy - sy[0]) - (gx - sx[0]) * (sy[1] - sy[0])) / area
        b0 = 1 - b1 - b2
        inside = (b0 >= 0) & (b1 >= 0) & (b2 >= 0)
        if not inside.any():
            continue
        bc = np.stack([b0, b1, b2], -1)[inside]
        z = bc @ p[:, 2]
        ys, xs = np.nonzero(inside)
        ys, xs = ys + y0, xs + x0
        closer = z < zbuf[ys, xs]
        col = bc @ rgb
        if uv is not None and slot is not None and slot < len(tims):
            tim = tims[slot]
            key = (slot, row)
            if key not in palettes:
                palettes[key] = clut_to_rgba(tim.clut[min(row, len(tim.clut) - 1)])
            tuv = bc @ uv
            tu = np.clip(tuv[:, 0].astype(int), 0, tim.pixels.shape[1] - 1)
            tv = np.clip(tuv[:, 1].astype(int), 0, tim.pixels.shape[0] - 1)
            tex = palettes[key][tim.pixels[tv, tu]]
            closer &= tex[:, 3] > 0
            col = np.clip(tex[:, :3] * col / GPU_NEUTRAL, 0, 255)
        ys, xs, z, col = ys[closer], xs[closer], z[closer], col[closer]
        zbuf[ys, xs] = z
        img[ys, xs] = col
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))


def export_obj(model: Model, world: WorldMesh, path: Path) -> int:
    """Write triangles (posed world positions, per-vertex colours as OBJ extension)."""
    lines, count = [], 0
    for xyz, rgb, _, _, _ in triangles(model, world):
        for v, c in zip(xyz, rgb):
            lines.append('v %.3f %.3f %.3f %.3f %.3f %.3f' % (*v, *(np.clip(c, 0, 255) / 255)))
        lines.append(f'f {count + 1} {count + 2} {count + 3}')
        count += 3
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return count // 3


def main(argv: list[str] | None = None) -> None:
    """Render rest pose, motion frames and a contact sheet; export rest-pose OBJ."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--character', default='heat')
    ap.add_argument('--variant', default='a_p1')
    ap.add_argument('--motion', type=int, default=71, help='001.bin index (71 = WAIT, req 106)')
    ap.add_argument('--frames', type=int, default=8, help='evenly spaced frames to render')
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    config = load_config(repo_root=ROOT)
    assets, = require_paths(config, ('inputs.bag2jp_assets',))
    base = assets / 'archive/characters' / args.character
    args.out = assert_write_target(config, args.out.resolve(), role='work')
    model, bank, tims = load_character(base / f'model_{args.variant}', base / f'pack_{args.variant}')
    args.out.mkdir(parents=True, exist_ok=True)
    slot_map = character_slot_map(base / f'pack_{args.variant}', costume=0 if args.variant.startswith('a') else 1)
    rest = world_meshes(model, pose_model(model))
    for yaw in (0, 180, 90):
        render(model, rest, tims, yaw_deg=yaw).save(args.out / f'{args.character}_rest_yaw{yaw}.png')
    tri = export_obj(model, rest, args.out / f'{args.character}_rest.obj')
    logger.info('rest pose: %d triangles, OBJ written', tri)
    motion = decode_motion(bank, args.motion)
    frames = np.linspace(0, motion['frames'] - 1, args.frames).round().astype(int)
    shots = []
    for f in frames:
        poses = pose_model(model, sample_motion(motion, f), slot_map)
        im = render(model, world_meshes(model, poses), tims, yaw_deg=180)
        im.save(args.out / f'{args.character}_m{args.motion:03d}_f{f:03d}.png')
        shots.append(im)
    sheet = Image.new('RGB', (shots[0].width * len(shots), shots[0].height))
    for i, im in enumerate(shots):
        sheet.paste(im, (i * im.width, 0))
    sheet.save(args.out / f'{args.character}_m{args.motion:03d}_sheet.png')
    logger.info('motion %d: %d frames (step %d), rendered %s', args.motion, motion['frames'],
                motion['step'], list(frames))


if __name__ == '__main__':
    main()
