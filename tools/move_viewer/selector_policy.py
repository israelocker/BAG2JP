"""Read the native selector's complete protected-entry authority."""
import hashlib
from pathlib import Path
import re

_TABLE = re.compile(r'static const B1AltEntry b1_alt_entries\[\]\s*=\s*\{(.*?)\};', re.S)
_NUMBER = r'(?:0x[0-9a-fA-F]+|[0-9]+)u?'
_ROW = re.compile(r'\{\s*(' + _NUMBER + r')\s*,' + (r'\s*' + _NUMBER + r'\s*,') * 7
                  + r'\s*' + _NUMBER + r'\s*\}')


def _strip_comments(source: str) -> str:
    source = re.sub(r'/\*.*?\*/', ' ', source, flags=re.S)
    return re.sub(r'//[^\n]*', ' ', source)


def blocked_entries(source: str) -> frozenset[int]:
    """Return every entry of the single live table; any doubt raises ValueError."""
    tables = _TABLE.findall(_strip_comments(source))
    if len(tables) != 1:
        raise ValueError(f'expected one native selector table, found {len(tables)}')
    body = tables[0]
    entries = []
    position = 0
    while True:
        position += len(body[position:]) - len(body[position:].lstrip())
        if position == len(body):
            break
        item = _ROW.match(body, position)
        if item is None:
            raise ValueError('unrecognized native selector row')
        value = item.group(1).rstrip('u')
        entry = int(value, 16 if value.startswith('0x') else 10)
        if entry in entries:
            raise ValueError('duplicate native selector entry')
        entries.append(entry)
        position = item.end()
        rest = body[position:].lstrip()
        if rest.startswith(','):
            position = len(body) - len(rest) + 1
        elif rest:
            raise ValueError('missing comma between native selector rows')
    if not entries:
        raise ValueError('empty native selector table')
    return frozenset(entries)


# Builds whose bag1-content selector records relocated BAG2 offsets (b1v_bag2_off) and whose
# relocation was accepted in a recorded take. Unknown builds keep the conservative block.
RELOCATION_AWARE_SHA256 = frozenset({
    '35266C386CABD9019D7441FB558C3EA72BF5B6182C7C09417833D5BB837268CD',  # f3-bag1reloc-strike-20261121c
})


def exe_follows_relocation(exe: Path) -> bool:
    """True only for an installed exe proven to follow relocated selector entries."""
    if not exe.is_file():
        return False
    return hashlib.sha256(exe.read_bytes()).hexdigest().upper() in RELOCATION_AWARE_SHA256
