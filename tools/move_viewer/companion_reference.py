"""Asset-bound, static native companion references; never general motion placement.

The digest covers every regular file of ``model_a_p1`` and ``pack_a_p1`` (any suffix
or case), so a swapped bank, texture or overlay cannot pass. It does NOT cover other
variants (b_p1, a_p2), choreography, extracted PNGs, code or configuration.
"""
from pathlib import Path
import hashlib
from .scene import NativeActorContext, load_scene

REFERENCES = {
    'capoeira': ('819e6a3f7b92b85c45665758e65c4b9d0b93dfae33dadedbb18e88b9f26c7dda',
        (NativeActorContext(66, 67, 68, 2070, 74, (-648, 0, -193)),
         NativeActorContext(113, 69, 70, 3588, 74, (-780, 0, -232))),
        'viewer-capoeira-strike-12500-b gf12500 — A/P1, native draw/shape blend 4096'),
    'chichi_sally': ('4f14920001d4889293d7b949b2f7013f9fa737027467b9e18857b1380cd212b1',
        (NativeActorContext(66, 156, 157, 2145, 53, (-521, -88, 169)),
         NativeActorContext(113, 159, 160, 924, 60, (-91, -136, -60))),
        'viewer-companion-strike-12430-a gf12430 — A/P1, native draw/shape blend 4096'),
}

def asset_digest(base: Path) -> str:
    """Hash every member of the recorded model/pack pair, case-insensitively."""
    files = [p for folder in ('model_a_p1', 'pack_a_p1')
             for p in (base / folder).iterdir() if p.is_file()]
    digest = hashlib.sha256()
    for path in sorted(files, key=lambda p: p.relative_to(base).as_posix()):
        data = path.read_bytes()
        digest.update(path.relative_to(base).as_posix().encode('utf-8'))
        digest.update(len(data).to_bytes(8, 'little'))
        digest.update(data)
    return digest.hexdigest()

def reference_matches(characters: Path, character: str) -> bool:
    """True only when the assets are byte-identical to a recorded capture."""
    if character not in REFERENCES:
        return False
    try:
        return asset_digest(characters / character) == REFERENCES[character][0]
    except (OSError, KeyError):
        return False


def load_reference(characters: Path, character: str):
    """Load only the exact A/P1 assets associated with a recorded static context."""
    if character not in REFERENCES:
        raise ValueError('reference unavailable for this character')
    expected, contexts, label = REFERENCES[character]
    base = characters / character
    if asset_digest(base) != expected:
        raise ValueError('reference assets differ from the recorded context')
    scene = load_scene(base / 'model_a_p1', base / 'pack_a_p1')
    # Re-verify: a local concurrent write between hashing and parsing is rejected.
    if asset_digest(base) != expected:
        raise ValueError('reference assets changed while loading')
    return scene, contexts, label
