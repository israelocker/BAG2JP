"""Plan reserved relocation destinations without writing a package."""
from pathlib import Path

from tools.move_viewer import reservations, swap_mod


def plan(disc: Path, entries: list[int], pairs: list[tuple[int, int]],
         spans: tuple[tuple[int, int], ...], *, max_growth: int = 0,
         cross: swap_mod.CrossBank | None = None,
          relocation_blocked: frozenset[int] | None = None) -> list[tuple[int, bytes, bytes]]:
    """Build overlays; absent an explicit selector policy, forbid all relocation.

    An empty blocked set explicitly opts in; callers must establish compatibility.
    Blocked entries may still grow in place.
    """
    if not entries or len(set(entries)) != len(entries):
        raise ValueError('empty or duplicate package entries')
    for low, high in spans:
        if type(low) is not int or type(high) is not int or low < 0 or high <= low:
            raise ValueError('invalid reservation span')
    occupied = list(spans)
    overlays = []
    first = swap_mod.RELOCATE_FIRST_LBA
    end = swap_mod.RELOCATE_END_LBA
    for entry in entries:
        current = swap_mod.build(disc, entry, pairs, copy=True,
                                 max_growth=max_growth, cross=cross, relocate_lba=first)
        if current[0][0] == first * swap_mod.SECTOR:
            if relocation_blocked is None or entry in relocation_blocked:
                raise ValueError('relocation incompatible with BAG1/BAG2 selector')
            sectors = (len(current[0][2]) + swap_mod.SECTOR - 1) // swap_mod.SECTOR
            lba = reservations.allocate(sectors, tuple(occupied), first, end)
            if lba != first:
                current = swap_mod.build(disc, entry, pairs, copy=True,
                                         max_growth=max_growth, cross=cross,
                                         relocate_lba=lba)
        for offset, _, payload in current:
            stop = offset + len(payload)
            for low, high in occupied:
                if offset < high and low < stop:
                    raise ValueError(f'package overlay [{offset}, {stop}) intersects '
                                     f'reserved span [{low}, {high})')
            occupied.append((offset, stop))
        overlays.extend(current)
    return overlays
