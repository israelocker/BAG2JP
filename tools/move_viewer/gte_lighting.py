"""Native lighting colour results for explicit GTE register inputs (sf=12, lm=1).

Mirrors runtime/src/gte.cpp light_transform/light_color/depth_cue_from_mac.
Not a stage-light profile or projection emulator.
No FLAG/FIFO emulation. Callers must supply already transformed node light and
the actual projection IR0; absent state must not be silently manufactured.
"""
from dataclasses import dataclass
from numbers import Integral


@dataclass(frozen=True)
class NodeLighting:
    """Same-draw node light matrix plus actor colour/BK/FC and projection IR0.

    Light already includes native node rotation. It must not be multiplied by
    preview world rotation a second time. No absent-state defaults are supplied.
    """

    light: tuple[tuple[int, int, int], ...]
    colour: tuple[tuple[int, int, int], ...]
    background: tuple[int, int, int]
    far: tuple[int, int, int]
    ir0: int

    def shade(self, normal, rgb, repeats=None):
        """Convert one parsed normal group using its native lighting branch."""
        if repeats is None:
            return ncds(normal, rgb, self.light, self.colour, self.background, self.far, self.ir0)
        return specular_colour(normal, rgb, self.light, self.colour,
                               self.background, self.far, self.ir0, repeats)


def _registers(values, count, low, high):
    values = tuple(values)
    if len(values) != count or any(isinstance(v, bool) or not isinstance(v, Integral)
                                   or not low <= v <= high for v in values):
        raise ValueError('invalid GTE register values')
    return tuple(int(v) for v in values)


def _matrix(values):
    rows = tuple(values)
    if len(rows) != 3:
        raise ValueError('invalid GTE matrix')
    return tuple(_registers(row, 3, -32768, 32767) for row in rows)


def _signed(value, bits):
    value &= (1 << bits) - 1
    return value - (1 << bits) if value & (1 << (bits - 1)) else value


def _mac(value):
    return _signed(_signed(value, 44) >> 12, 32)


def _ir(value, minimum=0):
    return min(32767, max(minimum, value))


def specular_colour(normal, rgb, light, colour, background, far, ir0, repeats):
    """Group B: light MVMVA, header-count SQR commands, then CDP.

    Zero repeats would execute 2**32 native iterations after counter wrap; reject it.
    Each square operates on the clamped previous IR, not the original normal.
    """
    if type(repeats) is not int or not 1 <= repeats <= 255:
        raise ValueError('invalid native specular repeat count')
    normal = _registers(normal, 3, -32768, 32767)
    light = _matrix(light)
    values = tuple(_ir(_mac(sum(a * b for a, b in zip(row, normal)))) for row in light)
    for _ in range(repeats):
        values = tuple(_ir(_mac(value * value)) for value in values)
    # NCDS with identity light is exactly CDP on these already prepared IRs.
    identity = ((4096, 0, 0), (0, 4096, 0), (0, 0, 4096))
    return ncds(values, rgb, identity, colour, background, far, ir0)


def ncds(normal, rgb, light, colour, background, far, ir0):
    """Return RGB8; matrices use4096=1, FC uses16=1 output intensity.

    BK/FC are signed control-register values, not RGB bytes. A BK value4096
    supplies unit light intensity before multiplication by the input RGB.
    """
    normal = _registers(normal, 3, -32768, 32767)
    rgb = _registers(rgb, 3, 0, 255)
    light, colour = _matrix(light), _matrix(colour)
    background = _registers(background, 3, -(1 << 31), (1 << 31) - 1)
    far = _registers(far, 3, -(1 << 31), (1 << 31) - 1)
    if type(ir0) is not int or not 0 <= ir0 <= 4096:
        raise ValueError('invalid GTE depth-cue IR0')
    lit = tuple(_ir(_mac(sum(a * b for a, b in zip(row, normal)))) for row in light)
    coloured = tuple(_ir(_mac(bk * 4096 + sum(a * b for a, b in zip(row, lit))))
                     for row, bk in zip(colour, background))
    output = []
    for value, channel, distant in zip(coloured, rgb, far):
        base = channel * value * 16
        difference = _ir(_mac(distant * 4096 - base), -32768)
        result = _mac(base + ir0 * difference)
        output.append(min(255, max(0, result >> 4)))
    return tuple(output)
