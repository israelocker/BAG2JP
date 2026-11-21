"""Conservative, read-only package reservation inventory for the verified JP disc."""
from pathlib import Path
import hashlib
import tomllib

from tools.move_viewer.swap_mod import DISC_SHA256, GAME_ID, RAW_SECTOR, SECTOR


def allocate(sectors: int, spans: tuple[tuple[int, int], ...], first_lba: int,
             end_lba: int) -> int:
    """Choose the first sector-aligned space avoiding absolute user-byte spans."""
    if (any(type(v) is not int for v in (sectors, first_lba, end_lba)) or
            sectors <= 0 or first_lba < 0 or end_lba <= first_lba):
        raise ValueError('invalid allocation bounds')
    for start, end in spans:
        if type(start) is not int or type(end) is not int or start < 0 or end <= start:
            raise ValueError('invalid reservation span')
    cursor = first_lba
    for start, end in sorted(spans):
        if cursor * SECTOR >= end:
            continue
        if (cursor + sectors) * SECTOR <= start:
            break
        cursor = (end + SECTOR - 1) // SECTOR
    if cursor + sectors > end_lba:
        raise ValueError('no free relocation extent')
    return cursor


def inventory(roots: tuple[Path, ...]) -> tuple[tuple[int, int], ...]:
    """Return absolute disc_user half-open reservations from all declared packages."""
    spans = set()
    for root in roots:
        if not root.is_dir():
            raise ValueError(f'reservation root missing: {root}')
        for manifest in sorted(root.rglob('manifest.toml')):
            data = tomllib.loads(manifest.read_text(encoding='utf-8'))
            for field in ('target', 'overlay', 'patch'):
                collection = data.get(field, [])
                if not isinstance(collection, list) or any(not isinstance(item, dict)
                                                          for item in collection):
                    raise ValueError(f'invalid reservation {field} collection: {manifest}')
            targets = data.get('target', [])
            if not targets or any(t.get('game_id') != GAME_ID or
                                  t.get('disc_sha256', DISC_SHA256) != DISC_SHA256
                                  for t in targets):
                raise ValueError(f'unverified reservation target: {manifest}')
            # Only executable patches have no disc footprint. Unknown patch forms
            # must not disappear from the inventory through a permissive default.
            if any(p.get('target') != 'main_exe' for p in data.get('patch', [])):
                raise ValueError(f'unsupported reservation patch: {manifest}')
            for overlay in data.get('overlay', []):
                target = overlay.get('target')
                if target not in ('disc_user', 'disc_raw'):
                    raise ValueError(f'unsupported reservation overlay: {manifest}')
                offset = overlay.get('offset')
                if type(offset) is not int or offset < 0:
                    raise ValueError(f'invalid reservation offset: {manifest}')
                payload = (manifest.parent / overlay['file']).resolve()
                if not payload.is_relative_to(manifest.parent.resolve()):
                    raise ValueError(f'reservation payload outside package: {manifest}')
                contents = payload.read_bytes()
                if not contents or hashlib.sha256(contents).hexdigest() != overlay.get('sha256'):
                    raise ValueError(f'invalid reservation payload: {manifest}')
                end = offset + len(contents)
                if target == 'disc_raw':
                    # Reserve entire touched sectors, including writes to their raw
                    # headers/ECC: conservative protection, not a byte-exact mapping.
                    offset = offset // RAW_SECTOR * SECTOR
                    end = ((end + RAW_SECTOR - 1) // RAW_SECTOR) * SECTOR
                spans.add((offset, end))
    return tuple(sorted(spans))
