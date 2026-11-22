"""Pose a decoded BAG2 model: node matrices, motion frames and world-space mesh data.

Sources (SLPM_862.19, Ghidra MCP):
  FUN_8001F004  angles -> matrix, 12-bit (4096 = 360 deg); R = Rz(z) . Ry(y) . Rx(x)
                (m00 = cy*cz, m10 = cy*sz, m20 = -sy, m21 = cy*sx, m22 = cy*cx).
  FUN_80022800  rest matrices: rest angles + node translation, one per node in walk order
                for the first two roots.
  FUN_80012B9C  animated matrices: slot map player+0x7CC (node -> angle slot, 0xFF = keep
                rest); node 0 takes the root translation track (s16 >> 1).
  FUN_80013144 / FUN_800133CC  compose: world = parent.R*local + parent.t; child
                translations are scaled by the accumulated scale (>> 12); the draw matrix is
                world.R with columns scaled (FUN_80013544). Siblings (link[1]) inherit the
                parent's matrix/scale, children (link[2]) this node's.
  FUN_800128B4  keyframe index = frame // step; the last frame maps to an extra keyframe.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .model_codec import FIXED_ONE, Mesh, Model

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'bag1import'))
import animlib  # noqa: E402
import motion_codec  # noqa: E402

ANGLE_UNITS = 4096
UNMAPPED_SLOT = 0xFF
# Player world scale param_3 of FUN_80013144; BAG2 scale table byte for Heat (slot 0).
DEFAULT_PLAYER_SCALE = 128
# player+0x7CC read from RAM dumps with native BAG2 Heat loaded (nodes 11/12/13 = 33/42/171
# vertices): node 12 is not animated, later nodes shift down one slot.
HEAT_SLOT_MAP = list(range(12)) + [UNMAPPED_SLOT] + list(range(12, 19))


def rotation(angles: tuple[float, float, float]) -> np.ndarray:
    """PS1 12-bit angles -> 3x3 float matrix, R = Rz . Ry . Rx (FUN_8001F004)."""
    x, y, z = (a * 2 * np.pi / ANGLE_UNITS for a in angles)
    cx, sx, cy, sy, cz, sz = np.cos(x), np.sin(x), np.cos(y), np.sin(y), np.cos(z), np.sin(z)
    rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return rz @ ry @ rx


@dataclass
class MotionPose:
    """Angles per slot and root translation for one (possibly fractional) frame."""
    slot_angles: dict[int, np.ndarray]
    root_translation: np.ndarray


def keyframe_position(frame: float, frames: int, step: int) -> float:
    """Frame -> keyframe coordinate (FUN_800128B4); fractional between keyframes."""
    if step <= 1:
        return min(frame, frames - 1)
    if frame >= frames - 1:
        return (frames - 2) // step + 1
    return frame / step


def _lerp_angles(a: np.ndarray, b: np.ndarray, t: float) -> np.ndarray:
    d = (b - a + ANGLE_UNITS // 2) % ANGLE_UNITS - ANGLE_UNITS // 2
    return a + d * t


def sample_motion(decoded: dict, frame: float) -> MotionPose:
    """Pose at ``frame``; in-between frames lerp angles (game blends matrices, FUN_80012350)."""
    k = keyframe_position(frame, decoded['frames'], decoded['step'])
    k0 = int(np.floor(k))
    k1 = min(k0 + 1, len(decoded['translation'][0]) - 1)
    t = k - k0
    angles = {}
    for bone, axes in zip(decoded['bones'], decoded['rotations']):
        a0 = np.array([ax[k0] for ax in axes], float)
        a1 = np.array([ax[k1] for ax in axes], float)
        angles[bone] = _lerp_angles(a0, a1, t)
    tr = np.array([[ax[k0] >> 1, ax[k1] >> 1] for ax in decoded['translation']], float)
    return MotionPose(angles, tr[:, 0] * (1 - t) + tr[:, 1] * t)


def decode_motion(bank: bytes, index: int) -> dict:
    """Decode motion ``index`` of a 001.bin bank (motion_codec / animlib layout)."""
    return motion_codec.decode(animlib.anim_list(bank)[index])


@dataclass
class NodePose:
    rotation: np.ndarray        # world rotation (unscaled)
    translation: np.ndarray     # world origin
    draw: np.ndarray            # rotation with per-axis scale columns (vertex transform)


def pose_model(model: Model, motion: MotionPose | None = None,
               slot_map: list[int] | None = None,
               player_scale: int = DEFAULT_PLAYER_SCALE,
               roots: list[int] | None = None) -> dict[int, NodePose]:
    """World matrices for every node reachable from ``roots`` (default: first root)."""
    poses: dict[int, NodePose] = {}
    order = model.walk()
    matrix_index = {n: i for i, n in enumerate(order)}

    def local(n: int, pscale: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        node = model.nodes[n]
        slot = None
        if motion is not None and slot_map is not None:
            i = matrix_index[n]
            slot = slot_map[i] if i < len(slot_map) else UNMAPPED_SLOT
        angles = motion.slot_angles.get(slot) if slot not in (None, UNMAPPED_SLOT) else None
        r = rotation(angles if angles is not None else node.rest_angles)
        if n == model.roots[0] and motion is not None:
            t = motion.root_translation * player_scale / 128     # FUN_80013144: * scale >> 7
        else:
            t = np.array(node.translation, float) * pscale / FIXED_ONE
        return r, t

    def rec(n: int, pr: np.ndarray, pt: np.ndarray, pscale: np.ndarray) -> None:
        if n < 0:
            return
        node = model.nodes[n]
        r, t = local(n, pscale)
        wr, wt = pr @ r, pr @ t + pt
        lscale = pscale * np.array(node.scale, float) / FIXED_ONE
        poses[n] = NodePose(wr, wt, wr * (lscale / FIXED_ONE)[None, :])
        rec(node.sibling, pr, pt, pscale)
        rec(node.child, wr, wt, lscale)

    base = np.full(3, float(player_scale))
    for root in roots if roots is not None else model.roots[:1]:
        node = model.nodes[root]
        r, t = local(root, base)
        lscale = base * np.array(node.scale, float) / FIXED_ONE
        poses[root] = NodePose(r, t, r * (lscale / FIXED_ONE)[None, :])
        rec(node.child, r, t, lscale)
    return poses


@dataclass
class WorldMesh:
    """Per node: scratch slot -> world position, plus the global colour array."""
    positions: dict[int, np.ndarray]     # node -> (slots, 3)
    colors: np.ndarray                   # (N, 3) float 0..255 (lit)


LIGHT_DIRECTION = np.array([0.3, 0.6, 0.75])   # +z = character front (toes point +z)
AMBIENT = 0.7  # matched to the in-game Heat recording heat-ref-20261122a (white suit)


def world_meshes(model: Model, poses: dict[int, NodePose]) -> WorldMesh:
    """Transform vertices, run export/import in draw order and light the normals.

    Lighting is an approximation (one directional light + ambient); the game uses the GTE
    light/colour matrices (0x80027DC4) whose runtime values were not read.
    """
    globals_xyz: dict[int, np.ndarray] = {}
    positions: dict[int, np.ndarray] = {}
    size = 1 + max((n.mesh.color_base + sum(len(g.normals) for g in n.mesh.groups)
                    for n in model.nodes if n.mesh), default=0)
    colors = np.zeros((size, 3))
    light = LIGHT_DIRECTION / np.linalg.norm(LIGHT_DIRECTION)
    for n in model.walk():
        node, pose = model.nodes[n], poses.get(n)
        mesh: Mesh | None = node.mesh
        if pose is None or mesh is None:
            continue
        local = (pose.draw @ mesh.vertices.T).T + pose.translation
        slots = max([len(local)] + [s + 1 for _, s in mesh.imports])
        scratch = np.zeros((slots, 3))
        scratch[:len(local)] = local
        for slot, gidx in mesh.exports:
            globals_xyz[gidx] = scratch[slot]
        for gidx, slot in mesh.imports:
            if gidx in globals_xyz:
                scratch[slot] = globals_xyz[gidx]
        positions[n] = scratch
        ci = mesh.color_base
        for g in mesh.groups:
            nw = (pose.rotation @ (g.normals.T / FIXED_ONE)).T
            lam = np.clip(nw @ light, 0, None)
            colors[ci:ci + len(nw)] = np.array(g.color, float)[None, :] * np.clip(AMBIENT + lam, 0, 2)[:, None]
            ci += len(nw)
    return WorldMesh(positions, colors)
