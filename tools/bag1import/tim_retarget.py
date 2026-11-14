"""Build a TIM with BAG1 pixels/CLUT rows at the BAG2 TIM's VRAM coordinates.
When the BAG2 CLUT has more rows than the BAG1 one, the extra BAG2 rows are kept after the BAG1
rows (other BAG2 graphics, e.g. the name label, use them).
usage: tim_retarget.py <bag1.tim> <bag2.tim> <out.tim>"""
import struct, sys

def parse(b):
    flags = struct.unpack_from('<I', b, 4)[0]; o = 8; clut = None
    if flags & 8:
        ln, x, y, w, h = struct.unpack_from('<IHHHH', b, o)
        clut = dict(x=x, y=y, w=w, h=h, data=b[o + 12:o + ln]); o += ln
    ln, x, y, w, h = struct.unpack_from('<IHHHH', b, o)
    img = dict(x=x, y=y, w=w, h=h, data=b[o + 12:o + ln])
    return flags, clut, img

def build(flags, clut, img):
    out = struct.pack('<II', 0x10, flags)
    if clut:
        out += struct.pack('<IHHHH', 12 + len(clut['data']), clut['x'], clut['y'], clut['w'], clut['h']) + clut['data']
    out += struct.pack('<IHHHH', 12 + len(img['data']), img['x'], img['y'], img['w'], img['h']) + img['data']
    return out

def retarget(b1, b2):
    f1, c1, i1 = parse(b1); f2, c2, i2 = parse(b2)
    img = dict(i1, x=i2['x'], y=i2['y'])
    clut = None
    if c1:
        clut = dict(c1)
        if c2:
            clut.update(x=c2['x'], y=c2['y'])
            if c2['w'] == c1['w'] and c2['h'] > c1['h']:
                row = c1['w'] * 2
                clut['data'] = c1['data'] + c2['data'][c1['h'] * row:]
                clut['h'] = c2['h']
    return build(f1, clut, img)

if __name__ == '__main__':
    open(sys.argv[3], 'wb').write(retarget(open(sys.argv[1], 'rb').read(), open(sys.argv[2], 'rb').read()))

def paste_rect(dst_tim, src_tim, x0, y0, x1, y1):
    """4bpp: copy pixels [x0,x1) x [y0,y1) (x even) from src TIM into dst TIM (same size)."""
    fd, cd, idd = parse(dst_tim); fs, cs, isrc = parse(src_tim)
    rowb = idd['w'] * 2
    d = bytearray(idd['data']); s = isrc['data']
    for y in range(y0, y1):
        d[y * rowb + x0 // 2: y * rowb + x1 // 2] = s[y * rowb + x0 // 2: y * rowb + x1 // 2]
    idd = dict(idd, data=bytes(d))
    return build(fd, cd, idd)


def _validate_label_chunk(data: bytes, offset: int) -> int:
    try:
        size, _, _, width, height = struct.unpack_from('<IHHHH', data, offset)
    except struct.error as exc:
        raise ValueError('Truncated TIM block header') from exc
    if size != 12 + width * height * 2 or offset + size > len(data):
        raise ValueError('TIM block length does not match dimensions/file')
    return offset + size


def _label_image(data: bytes) -> tuple[int, dict, dict]:
    if len(data) < 8 or data[:4] != struct.pack('<I', 0x10):
        raise ValueError('Label input must be a TIM')
    if struct.unpack_from('<I', data, 4)[0] != 8:
        raise ValueError('Label transfer requires a 4bpp TIM with CLUT')
    image_offset = _validate_label_chunk(data, 8)
    _validate_label_chunk(data, image_offset)
    try:
        flags, clut, image = parse(data)
    except struct.error as exc:
        raise ValueError('Truncated TIM header') from exc
    if flags != 8 or clut is None or clut['w'] != 16 or clut['h'] <= 0:
        raise ValueError('Label transfer requires a 4bpp TIM with 16-colour CLUT rows')
    if len(clut['data']) != clut['w'] * clut['h'] * 2:
        raise ValueError('Truncated label CLUT')
    if image['w'] <= 0 or image['h'] <= 0 or len(image['data']) != image['w'] * image['h'] * 2:
        raise ValueError('Invalid or truncated label image')
    return flags, clut, image


def _label_rect(rect: tuple[int, int, int, int], image: dict) -> None:
    if len(rect) != 4 or any(type(v) is not int for v in rect):
        raise ValueError('Label rectangle requires four integers')
    x0, y0, x1, y1 = rect
    if not (0 <= x0 < x1 <= image['w'] * 4 and 0 <= y0 < y1 <= image['h']):
        raise ValueError('Label rectangle outside TIM image')


def paste_scaled_rect(dst_tim: bytes, src_tim: bytes,
                      source_rect: tuple[int, int, int, int],
                      target_rect: tuple[int, int, int, int],
                      index_map: tuple[int, ...] = tuple(range(16))) -> bytes:
    """Copy 4bpp pixels using centre-sampled nearest neighbours, including zero.

    Rectangles are half-open pixel coordinates local to each image. Destination
    CLUT, coordinates and all pixels outside the rectangle are preserved. The
    index_map translates source indices for a caller-selected HUD palette.
    """
    flags, clut, target = _label_image(dst_tim)
    _, _, source = _label_image(src_tim)
    _label_rect(source_rect, source)
    _label_rect(target_rect, target)
    if len(index_map) != 16 or any(type(v) is not int or not 0 <= v < 16 for v in index_map):
        raise ValueError('Label index map requires sixteen 4bpp indices')
    sx0, sy0, sx1, sy1 = source_rect
    x0, y0, x1, y1 = target_rect
    pixels = bytearray(target['data'])
    for y in range(y0, y1):
        sy = sy0 + (2 * (y - y0) + 1) * (sy1 - sy0) // (2 * (y1 - y0))
        for x in range(x0, x1):
            sx = sx0 + (2 * (x - x0) + 1) * (sx1 - sx0) // (2 * (x1 - x0))
            value = (source['data'][sy * source['w'] * 2 + sx // 2] >> (4 * (sx & 1))) & 15
            value = index_map[value]
            offset = y * target['w'] * 2 + x // 2
            shift = 4 * (x & 1)
            pixels[offset] = (pixels[offset] & ~(15 << shift)) | value << shift
    return build(flags, clut, dict(target, data=bytes(pixels)))


def label_palette_map(source: bytes, reference: bytes) -> tuple[int, ...]:
    """Match first-row RGB555 colours, reserving index zero for transparency.

    STP flags are not copied: HUD rendering selects its own shared palette.
    Nonzero source indices remain nonzero even when their RGB colour is black.
    """
    _, source_clut, _ = _label_image(source)
    _, target_clut, _ = _label_image(reference)
    source_words = struct.unpack('<16H', source_clut['data'][:32])
    target_words = struct.unpack('<16H', target_clut['data'][:32])
    colours = [tuple((word >> shift) & 31 for shift in (0, 5, 10)) for word in target_words]
    result = [0]
    for word in source_words[1:]:
        rgb = tuple((word >> shift) & 31 for shift in (0, 5, 10))
        result.append(min(range(1, 16), key=lambda i: sum((a - b) ** 2 for a, b in zip(rgb, colours[i]))))
    return tuple(result)


def retarget_with_label(source: bytes, reference: bytes,
                        source_rect: tuple[int, int, int, int],
                        target_rect: tuple[int, int, int, int]) -> bytes:
    """Retarget a TIM, then reuse its original label in the destination HUD slot."""
    _label_image(source)
    _label_image(reference)
    return paste_scaled_rect(retarget(source, reference), source, source_rect, target_rect,
                              label_palette_map(source, reference))


def paste_native_glyphs(destination: bytes, glyphs: list[tuple[bytes, tuple[int, int, int, int]]],
                        target_rect: tuple[int, int, int, int],
                        spacing_after: list[int] | None = None) -> bytes:
    """Join unscaled native glyphs, preserving indices for a shared runtime CLUT.

    Glyph widths plus transparent spacing must exactly fill the destination; no
    palette guessing or rasterization. Other pixels and TIM metadata stay unchanged.
    """
    _, _, image = _label_image(destination)
    _label_rect(target_rect, image)
    x0, y0, x1, y1 = target_rect
    if not glyphs:
        raise ValueError('Native label requires glyphs')
    spacing = [0] * len(glyphs) if spacing_after is None else spacing_after
    if len(spacing) != len(glyphs) or any(type(v) is not int or v < 0 for v in spacing):
        raise ValueError('Native spacing requires one nonnegative integer per glyph')
    width = sum(spacing)
    for source, rect in glyphs:
        _label_rect(rect, _label_image(source)[2])
        if rect[3] - rect[1] != y1 - y0:
            raise ValueError('Native glyph height must match destination')
        width += rect[2] - rect[0]
    if width != x1 - x0:
        raise ValueError('Native glyph widths must fill destination without scaling')
    for (source, rect), gap in zip(glyphs, spacing):
        end = x0 + rect[2] - rect[0]
        destination = paste_scaled_rect(destination, source, rect, (x0, y0, end, y1))
        if gap:
            # Map all source indices to zero; gap size never rescales glyphs.
            destination = paste_scaled_rect(destination, source, rect,
                                             (end, y0, end + gap, y1), (0,) * 16)
        x0 = end + gap
    return destination
