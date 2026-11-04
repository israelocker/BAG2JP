"""Apply reversible, hash-bound data-driven word contracts to DBI copies."""
import hashlib
import struct

DBI_HEADER_BYTES = 12
WORD_BYTES = 4


def _word_offset(offset: int, code_bytes: int) -> int:
    """Validate a code-relative aligned offset and return its file position."""
    if offset < 0 or offset % WORD_BYTES or offset + WORD_BYTES > code_bytes:
        raise ValueError(f'Invalid DBI word offset: {offset}')
    return DBI_HEADER_BYTES + offset


def _replace_word(data: bytearray, position: int, expected: int, replacement: int) -> None:
    """Validate a word before changing the private candidate buffer."""
    if not 0 <= replacement <= 0xFFFFFFFF or struct.unpack_from('<I', data, position)[0] != expected:
        raise ValueError(f'DBI contract word mismatch at file offset {position:#x}')
    struct.pack_into('<I', data, position, replacement)


def _contract_patches(contract: dict, code_bytes: int) -> list[tuple[int, int, int]]:
    """Resolve and validate distinct code-relative word patches."""
    patches = []
    seen = set()
    for patch in contract['patches']:
        position = _word_offset(patch['offset'], code_bytes)
        if position in seen:
            raise ValueError('Duplicate DBI contract patch')
        seen.add(position)
        expected, replacement = (int(patch[key], 16) for key in ('expected', 'replacement'))
        patches.append((position, expected, replacement))
    return patches


def _validate_original(original: bytes, contract: dict, code_bytes: int) -> None:
    """Require both source identity and all independently recorded word guards."""
    if hashlib.sha256(original).hexdigest() not in contract['source_sha256']:
        raise ValueError('DBI input is not a recognized original')
    for offset, expected in contract['word_guards'].items():
        position = _word_offset(int(offset, 0), code_bytes)
        if struct.unpack_from('<I', original, position)[0] != int(expected, 16):
            raise ValueError(f'DBI guard mismatch at {position:#x}')


def apply_word_contract(data: bytes, contract: dict, restore: bool = False) -> bytes:
    """Return a validated DBI copy with contract words changed (or restored)."""
    if len(data) < DBI_HEADER_BYTES or data[:4] != b'DBI_':
        raise ValueError('Expected a DBI container')
    code_bytes = struct.unpack_from('<I', data, 4)[0]
    if code_bytes != len(data) - DBI_HEADER_BYTES:
        raise ValueError('DBI code size does not match container length')
    candidate = bytearray(data)
    for position, expected, replacement in _contract_patches(contract, code_bytes):
        if restore:
            _replace_word(candidate, position, replacement, expected)
        else:
            _replace_word(candidate, position, expected, replacement)
    _validate_original(bytes(candidate) if restore else data, contract, code_bytes)
    return bytes(candidate)
