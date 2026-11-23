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
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from .model_codec import FIXED_ONE, Mesh, Model
from .gte_lighting import NodeLighting

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
    """Slot rotations and root translation; matrices override legacy angle poses."""
    slot_angles: dict[int, np.ndarray]
    root_translation: np.ndarray
    slot_rotations: dict[int, np.ndarray] = field(default_factory=dict)


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


def _blend_rotations(first: np.ndarray, second: np.ndarray, weight: float) -> np.ndarray:
    """Float analogue of FUN_80012350: blend rows Y/Z, cross and normalize.

    The GTE uses fixed-point arithmetic; this preserves its interpolation path,
    not bit-exact rounding. Degenerate rows require native context, not a guessed
    Euler fallback.
    """
    if weight == 0:
        return first
    if weight == 1:
        return second
    mixed = first * (1 - weight) + second * weight
    y = mixed[1]
    x = np.cross(y, mixed[2])
    z = np.cross(x, y)
    rows = np.stack((x, y, z))
    lengths = np.linalg.norm(rows, axis=1)
    if not np.isfinite(lengths).all() or np.any(lengths <= np.finfo(float).eps * 16):
        raise ValueError('degenerate native rotation blend requires separate context')
    return rows / lengths[:, None]


def sample_motion(decoded: dict, frame: float) -> MotionPose:
    """Pose at ``frame`` using native-style matrix blending (float approximation)."""
    k = keyframe_position(frame, decoded['frames'], decoded['step'])
    k0 = int(np.floor(k))
    k1 = min(k0 + 1, len(decoded['translation'][0]) - 1)
    t = k - k0
    angles = {}
    matrices = {}
    for bone, axes in zip(decoded['bones'], decoded['rotations']):
        a0 = np.array([ax[k0] for ax in axes], float)
        a1 = np.array([ax[k1] for ax in axes], float)
        angles[bone] = _lerp_angles(a0, a1, t)
        matrices[bone] = _blend_rotations(rotation(a0), rotation(a1), t)
    tr = np.array([[ax[k0] >> 1, ax[k1] >> 1] for ax in decoded['translation']], float)
    return MotionPose(angles, tr[:, 0] * (1 - t) + tr[:, 1] * t, matrices)


def native_key_context(first_frame: int, second_frame: int, blend: int,
                       step: int, frames: int) -> tuple[int, int, int]:
    """Resolve an interior same-motion blend; endpoint/event paths stay blocked."""
    if (step <= 1 or frames <= 1 or not 0 <= blend <= FIXED_ONE or
            not 0 <= first_frame < frames - 1 or
            not 0 <= second_frame < frames - 1):
        raise ValueError('unsupported native key context')
    fixed_frame = first_frame * FIXED_ONE + (second_frame - first_frame) * blend
    first = fixed_frame // (step * FIXED_ONE)
    if (first + 1) * step >= frames:
        raise ValueError('native endpoint sampling requires separate context')
    weight = (fixed_frame - first * step * FIXED_ONE) // step
    return first, first + 1, weight


def native_root_translation(translation: list[list[int]], first: int,
                            second: int, weight: int) -> np.ndarray:
    """Sample signed root keys with the native 12-bit blend arithmetic."""
    if not 0 <= weight <= FIXED_ONE or first < 0 or second < 0:
        raise ValueError('invalid native root sampling context')
    if len(translation) != 3 or any(max(first, second) >= len(axis) for axis in translation):
        raise ValueError('native root key outside translation track')
    return np.array([(((axis[first] >> 1) * (FIXED_ONE - weight)) >> 12) +
                     (((axis[second] >> 1) * weight) >> 12)
                     for axis in translation], dtype=np.int64)


def native_world_root(root: list[int], scale: int, parent: list[int]) -> np.ndarray:
    """Compose a root under an identity native parent rotation."""
    if len(root) != 3 or len(parent) != 3 or not 0 < scale <= FIXED_ONE:
        raise ValueError('invalid native root placement')
    return np.array([((int(value) * scale) >> 7) + int(offset)
                     for value, offset in zip(root, parent)], dtype=np.int64)


EMPTY_MOTION_BYTES = 8     # stock placeholders are 4 zero bytes; a real header needs > 8


class EmptyMotionError(ValueError):
    """The slot holds a stock placeholder, not an animation."""


def is_empty_motion(body: bytes) -> bool:
    return len(body) <= EMPTY_MOTION_BYTES and not any(body)


def decode_motion(bank: bytes, index: int) -> dict:
    """Decode motion ``index`` of a 001.bin bank (motion_codec / animlib layout)."""
    body = animlib.anim_list(bank)[index]
    if is_empty_motion(body):
        raise EmptyMotionError(f'motion {index} is an empty stock placeholder')
    return motion_codec.decode(body)


@dataclass
class NodePose:
    rotation: np.ndarray        # world rotation (unscaled)
    translation: np.ndarray     # world origin
    draw: np.ndarray            # rotation with per-axis scale columns (vertex transform)


def pose_model(model: Model, motion: MotionPose | None = None,
               slot_map: list[int] | None = None,
                player_scale: int = DEFAULT_PLAYER_SCALE,
                roots: list[int] | None = None, *,
                previous_local_rotations: dict[int, np.ndarray] | None = None
                ) -> dict[int, NodePose]:
    """Compose reachable nodes (default: first root).

    Explicit previous local rotations preserve the native destination on missing
    tracks (80012b9c invalidates source; 80012350 skips it). Keys are model node
    indices, values unscaled local 3x3 rotations, not world/draw or +3EC history.
    The caller supplies that semantic identity; only shape/finiteness are checked
    (native fixed-point rotations are not perfectly orthonormal).
    When supplied, absent state fails closed; omission retains standalone rest
    approximation. This does not emulate draw/history blending or capture state.
    """
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
        matrix = motion.slot_rotations.get(slot) if slot not in (None, UNMAPPED_SLOT) else None
        if (motion is not None and angles is None and matrix is None and
                previous_local_rotations is not None):
            if n not in previous_local_rotations:
                raise ValueError(f'missing previous local rotation for node {n}')
            r = np.array(previous_local_rotations[n], dtype=float, copy=True)
            if r.shape != (3, 3) or not np.isfinite(r).all():
                raise ValueError(f'invalid previous local rotation for node {n}')
        else:
            r = matrix if matrix is not None else rotation(angles if angles is not None else node.rest_angles)
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


def world_meshes(model: Model, poses: dict[int, NodePose], *,
                 lighting: dict[int, NodeLighting] | None = None) -> WorldMesh:
    """Transform vertices, run export/import in draw order and light the normals.

    Default lighting retains the reference-calibrated preview approximation.
    Explicit per-node NodeLighting uses native group-A/B arithmetic and requires
    complete same-draw state; it never substitutes guessed missing node values.
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
        if lighting is not None and n not in lighting:
            raise ValueError(f'missing native lighting state for node {n}')
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
            if lighting is not None:
                colors[ci:ci + len(g.normals)] = [
                    lighting[n].shade(tuple(normal),
                                      tuple(g.color), g.specular) for normal in g.normals]
                ci += len(g.normals)
                continue
            nw = (pose.rotation @ (g.normals.T / FIXED_ONE)).T
            lam = np.clip(nw @ light, 0, None)
            colors[ci:ci + len(nw)] = np.array(g.color, float)[None, :] * np.clip(AMBIENT + lam, 0, 2)[:, None]
            ci += len(nw)
    return WorldMesh(positions, colors)
