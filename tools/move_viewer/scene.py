"""Isolated character scenes; native companion rules are not a match simulator."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .gte_lighting import NodeLighting
from .model_codec import Model, Tim, load_character, parse_model
from .pose import (NodePose, WorldMesh, animlib, decode_motion, native_key_context,
                   native_root_translation, native_world_root, pose_model, sample_motion,
                   world_meshes)

# JP main 80031d3c -> 800319fc: IDs10/14 consume model002, sharing bank001.
# Archive003 is an effect model, never a second motion bank.
COMPANION_CHARACTERS = frozenset({'chichi_sally', 'capoeira'})
# SLPM_862.19 native updater 8002a754..8002a874. Only bank-local dance
# ranges are admitted; fever banks, event requests and transitions need context.
PAIRED_DANCE_RANGES = ((54, 66, 47), (94, 96, 20))


@dataclass(frozen=True)
class NativeActorContext:
    """One captured same-motion actor, with identity parent rotation only."""

    slot: int
    first_frame: int
    second_frame: int
    blend: int
    scale: int
    parent: tuple[int, int, int]

    def __post_init__(self) -> None:
        """Reject malformed snapshot fields before any decoding or rendering."""
        values = (self.slot, self.first_frame, self.second_frame, self.blend, self.scale)
        if (any(type(value) is not int for value in values) or self.slot < 0 or
                min(self.first_frame, self.second_frame) < 0 or
                not 0 <= self.blend <= 4096 or not 0 < self.scale <= 4096 or
                len(self.parent) != 3 or any(type(value) is not int for value in self.parent)):
            raise ValueError('invalid native actor context')


def snapshot_world_root(motion: dict, context: NativeActorContext) -> np.ndarray:
    """Resolve a captured identity-parent root, not an entire native pose."""
    first, second, weight = native_key_context(
        context.first_frame, context.second_frame, context.blend,
        motion['step'], motion['frames'])
    root = native_root_translation(motion['translation'], first, second, weight)
    return native_world_root(root.tolist(), context.scale, list(context.parent))


def companion_slot(character: str, primary_slot: int, bank_slots: int) -> int:
    """Resolve an isolated native pair or reject context-dependent/absent slots."""
    if character in COMPANION_CHARACTERS and 0 <= primary_slot < bank_slots:
        for first, last, offset in PAIRED_DANCE_RANGES:
            if first <= primary_slot <= last and primary_slot + offset < bank_slots:
                return primary_slot + offset
    raise ValueError('companion pairing requires native match context or another bank')


@dataclass(frozen=True)
class CharacterScene:
    """Models sharing the native motion bank, textures and node-to-track map."""

    models: tuple[Model, ...]
    bank: bytes
    tims: list[Tim]
    slot_map: list[int]
    character: str


def load_scene(model_dir: Path, pack_dir: Path) -> CharacterScene:
    """Load the character's isolated scene from extracted archive members."""
    from .render_offline import character_slot_map

    model, bank, tims = load_character(model_dir, pack_dir)
    costume = 0 if model_dir.name.startswith('model_a_') else 1
    slots = character_slot_map(pack_dir, costume)
    character = model_dir.parent.name
    models = (model,)
    if character in COMPANION_CHARACTERS:
        models += (parse_model((model_dir / '002.bin').read_bytes()),)
    return CharacterScene(models, bank, tims, slots, character)


def pose_snapshot_scene(scene: CharacterScene, contexts: tuple[NativeActorContext, ...]
                        ) -> list[tuple[Model, WorldMesh, list[Tim]]]:
    """Render an observed snapshot; rotations remain the preview approximation."""
    if len(contexts) != len(scene.models) or len(contexts) not in (1, 2):
        raise ValueError('snapshot context count must match actors')
    actors = []
    for model, context in zip(scene.models, contexts):
        motion = decode_motion(scene.bank, context.slot)
        root = snapshot_world_root(motion, context)
        frame = (context.first_frame +
                 (context.second_frame - context.first_frame) * context.blend / 4096)
        sampled = sample_motion(motion, frame)
        poses = pose_model(model, sampled, scene.slot_map, player_scale=context.scale)
        # Preserve preview rotations, correcting only the independently verified root.
        preview_root = sampled.root_translation * context.scale / 128
        offset = root - preview_root
        placed = {index: NodePose(value.rotation, value.translation + offset, value.draw)
                  for index, value in poses.items()}
        actors.append((model, world_meshes(model, placed), scene.tims))
    return actors


def pose_scene(scene: CharacterScene, primary_slot: int, frames: tuple[float, ...],
               placements: tuple[np.ndarray, ...] | None, *,
               previous_local_rotations: tuple[dict[int, np.ndarray], ...] | None = None,
               lighting: tuple[dict[int, NodeLighting], ...] | None = None
                ) -> list[tuple[Model, WorldMesh, list[Tim]]]:
    """Prepare actors with optional explicit local history and per-node GTE state.

    Entries follow scene actor order. History is unscaled local rotation, not the
    raw actor+3EC blend history. Light matrices must already include each node's
    final rotation/placement; neither input is inferred from a RAM record.
    Omitting either input retains that subsystem's approximate preview path.
    """
    count = len(scene.models)
    if count not in (1, 2):
        raise ValueError('scene requires one or two actors')
    for states in (previous_local_rotations, lighting):
        if states is not None and (len(states) != count or
                                   any(not isinstance(state, dict) for state in states)):
            raise ValueError('explicit state mappings must match actors')
    if placements is None:
        if count != 1:
            raise ValueError('companion placement requires explicit native context')
        placements = (np.eye(4),)
    if len(placements) != count or len(frames) != count:
        raise ValueError('placement and frame counts must match actors')
    transforms = tuple(np.asarray(matrix, dtype=float) for matrix in placements)
    if any(matrix.shape != (4, 4) or not np.isfinite(matrix).all() or
           not np.array_equal(matrix[3], [0, 0, 0, 1]) for matrix in transforms):
        raise ValueError('placement must be a finite affine matrix')
    if any(not np.isfinite(frame) or frame < 0 for frame in frames):
        raise ValueError('actor frames must be finite and nonnegative')
    slots = [primary_slot]
    if count == 2:
        slots.append(companion_slot(scene.character, primary_slot, len(animlib.anim_list(scene.bank))))
    actors = []
    for actor_index, (model, slot, frame, transform) in enumerate(
            zip(scene.models, slots, frames, transforms)):
        motion = decode_motion(scene.bank, slot)
        if frame >= motion['frames']:
            raise ValueError('actor frame outside motion')
        pose_options = ({} if previous_local_rotations is None else
                        {'previous_local_rotations': previous_local_rotations[actor_index]})
        poses = pose_model(model, sample_motion(motion, frame), scene.slot_map, **pose_options)
        rotation, translation = transform[:3, :3], transform[:3, 3]
        transformed = {index: NodePose(rotation @ pose.rotation,
                                      rotation @ pose.translation + translation,
                                      rotation @ pose.draw) for index, pose in poses.items()}
        light_options = {} if lighting is None else {'lighting': lighting[actor_index]}
        actors.append((model, world_meshes(model, transformed, **light_options), scene.tims))
    return actors
