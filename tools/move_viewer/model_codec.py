"""Decode a BAG2 character model (DFS member 000.bin) and its TIM textures.

Sources (SLPM_862.19, read-only Ghidra MCP + Capstone over the main executable):
  FUN_80022410  links -> node struct: +0x90 link[0] parent, +0x94 link[1] next sibling,
                +0x98 link[2] first child, +0x9c link[3] next root.
  FUN_80022518  record per node in walk order: u32 type, payload, 10 transform words copied
                verbatim to node+0x00..0x27 (3 s16 rest angles, s32 scale xyz, pad,
                s32 translation xyz, pad).
  FUN_800220B8  mesh (type 1) header 0x48 words; [0x25] vertex count, [0x26] global
                colour base, [0x27]/[0x28] normal groups (A: lit, B: lit + specular),
                [0x29] exports, [0x2A] imports, [0x2B..0x3A] primitive counts (lo/hi s16).
  0x8008E780    per-mesh draw: vertex transform 0x80027CF8, lighting 0x80027DC4,
                export/import loops, then one emitter per primitive kind.
  0x80027FC8..  emitters (vertex/colour fields); FUN_800201B0 packet init (UV, texture
                slot byte: bits 0-4 slot, bits 5-7 semi-transparency, next byte CLUT row).
Kinds in DECODED_KINDS are decoded; 0x34/0x36/0x37/0x39 (unused by shipped models) raise UnsupportedPrimitive.
"""
from __future__ import annotations

import struct
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

MESH_HEADER_WORDS = 0x48
TRANSFORM_WORDS = 10
NO_LINK = -1
FIXED_ONE = 4096

# Header word -> (low-half words, high-half words) per record; order of FUN_800220B8.
PRIMITIVE_LAYOUT = ((0x2B, 2, 2), (0x2C, 4, 4), (0x2D, 5, 6), (0x2E, 3, 3), (0x2F, 6, 8),
                    (0x30, 4, 5), (0x31, 5, 6), (0x32, 4, 5), (0x33, 2, 2), (0x34, 2, 2),
                    (0x35, 3, 4), (0x36, 2, 2), (0x37, 4, 5), (0x38, 6, 8), (0x39, 6, 8))
LAST_COUNT_WORD = 0x3A          # low: 4-word records, high: 0x14-byte records
# 0x30-0x33/0x38 inferred from Sushi Boy, Comet and Strike records (2026-11-22), not yet from their emitters.
DECODED_KINDS = {0x2B, 0x2C, 0x2D, 0x2E, 0x2F, 0x30, 0x31, 0x32, 0x33, 0x35, 0x38}
# 0x35 inferred from Comet B records (2026-11-23): 0x2E colour layout plus a trailing mode word.


class UnsupportedPrimitive(ValueError):
    """Raised for primitive kinds whose emitter has not been read yet."""


@dataclass
class Primitive:
    """One polygon in GPU vertex order (quads: v0,v1,v2,v3 as the GPU strip)."""
    kind: int                   # header count word (0x2B..0x2F)
    quad: bool
    vertices: list[int]         # local scratch slots
    colors: list[int]           # global colour indices, one per vertex
    uvs: list[tuple[int, int]] | None = None
    texture_slot: int | None = None
    clut_row: int = 0
    semi_transparency: int = 0  # 0 = opaque, else GPU abr + 1
    rgb: tuple[int, int, int] | None = None  # direct colour (kind 0x30) instead of indices
    vertex_rgb: list[tuple[int, int, int]] | None = None  # direct per-vertex colour (0x38)
    base_colors: list[int] | None = None  # 0x2F Gouraud layer drawn under the texture


@dataclass
class NormalGroup:
    color: tuple[int, int, int]
    normals: np.ndarray         # (n, 3) int16, 4096 = 1.0
    specular: int | None = None  # group B only: repeat count from the top byte


@dataclass
class Mesh:
    vertices: np.ndarray        # (n, 3) int16 model units
    color_base: int
    groups: list[NormalGroup]
    exports: list[tuple[int, int]]   # (local slot, global index)
    imports: list[tuple[int, int]]   # (global index, local slot)
    primitives: list[Primitive]
    unsupported: dict[int, int] = field(default_factory=dict)


@dataclass
class Node:
    index: int
    links: list[int]
    kind: int
    rest_angles: tuple[int, int, int]
    scale: tuple[int, int, int]
    translation: tuple[int, int, int]
    mesh: Mesh | None = None
    instance_of: int | None = None    # type 2

    @property
    def parent(self) -> int:
        return self.links[0]

    @property
    def sibling(self) -> int:
        return self.links[1]

    @property
    def child(self) -> int:
        return self.links[2]


@dataclass
class Model:
    nodes: list[Node]
    roots: list[int]

    def walk(self) -> list[int]:
        """Nodes in file/draw order: roots via link[3], each recursing sibling then child."""
        return _walk([n.links for n in self.nodes], self.roots)


def _half(word: int) -> tuple[int, int]:
    return struct.unpack('<hh', struct.pack('<I', word & 0xFFFFFFFF))


def _lo(word: int) -> int:
    return word & 0xFFFF


def _hi(word: int) -> int:
    return (word >> 16) & 0xFFFF


def _indices(w0: int) -> tuple[int, int, int, int]:
    """Bytes of the index word: a = bits 8-15, b = 16-23, c = 24-31, d = 0-7."""
    return (w0 >> 8) & 0xFF, (w0 >> 16) & 0xFF, (w0 >> 24) & 0xFF, w0 & 0xFF


def _uv(rec: bytes, off: int) -> tuple[int, int]:
    return rec[off], rec[off + 1]


def _textured(prim: Primitive, rec: bytes, slot_off: int) -> Primitive:
    prim.texture_slot = rec[slot_off] & 0x1F
    prim.semi_transparency = rec[slot_off] >> 5
    prim.clut_row = rec[slot_off + 1]
    return prim


def decode_primitive(kind: int, quad: bool, rec: bytes) -> Primitive:
    """Decode one record; vertex/colour/UV order follows the emitter and packet init."""
    w = struct.unpack(f'<{len(rec) // 4}I', rec)
    a, b, c, d = _indices(w[0])
    if kind == 0x30:              # FT3 / FT4 with a direct RGB word
        rgb = (w[1] & 0xFF, (w[1] >> 8) & 0xFF, (w[1] >> 16) & 0xFF)
        if quad:
            p = Primitive(kind, True, [c, d, b, a], [0] * 4,
                          [_uv(rec, 8), _uv(rec, 0xE), _uv(rec, 0xA), _uv(rec, 0xC)], rgb=rgb)
            return _textured(p, rec, 0x10)
        p = Primitive(kind, False, [a, b, c], [0] * 3,
                      [_uv(rec, 8), _uv(rec, 0xA), _uv(rec, 0xC)], rgb=rgb)
        return _textured(p, rec, 0xE)
    if kind == 0x32:              # FT3 / FT4 layout of 0x30 with colour indices; first one used
        p = decode_primitive(0x30, quad, rec)
        p.kind, p.rgb, p.colors = kind, None, [_lo(w[1])] * len(p.vertices)
        return p
    if kind == 0x38:              # GT3 / GT4 with direct RGB words per vertex
        rgb = [(x & 0xFF, (x >> 8) & 0xFF, (x >> 16) & 0xFF) for x in w[1:5 if quad else 4]]
        if quad:
            p = Primitive(kind, True, [c, d, b, a], [0] * 4,
                          [_uv(rec, 0x14), _uv(rec, 0x1A), _uv(rec, 0x16), _uv(rec, 0x18)],
                          vertex_rgb=[rgb[0], rgb[3], rgb[1], rgb[2]])
            return _textured(p, rec, 0x1C)
        p = Primitive(kind, False, [a, b, c], [0] * 3,
                      [_uv(rec, 0x10), _uv(rec, 0x12), _uv(rec, 0x14)], vertex_rgb=rgb)
        return _textured(p, rec, 0x16)
    if kind == 0x31:              # same record layout as GT3 / GT4
        p = decode_primitive(0x2D, quad, rec)
        p.kind = kind
        return p
    if kind in (0x2B, 0x33):      # F3 / F4 (0x33: same two-word layout)
        col = _lo(w[1])
        return Primitive(kind, quad, [c, d, b, a] if quad else [a, b, c], [col] * (4 if quad else 3))
    if kind == 0x35:              # G3 / G4 plus a mode word (always 1 in Comet B; inferred, emitter unread)
        p = decode_primitive(0x2E, quad, rec)
        p.kind, p.semi_transparency = kind, _hi(w[2]) if not quad else w[3] & 0xFFFF
        return p
    if kind == 0x2E:              # G3 / G4
        if quad:
            return Primitive(kind, True, [c, d, b, a], [_lo(w[1]), _hi(w[2]), _hi(w[1]), _lo(w[2])])
        return Primitive(kind, False, [a, b, c], [_lo(w[1]), _hi(w[1]), _lo(w[2])])
    if kind == 0x2C:              # FT3 / FT4
        col = _lo(w[1])
        if quad:
            p = Primitive(kind, True, [c, d, b, a], [col] * 4,
                          [_uv(rec, 6), _uv(rec, 0xC), _uv(rec, 8), _uv(rec, 0xA)])
        else:
            p = Primitive(kind, False, [a, b, c], [col] * 3,
                          [_uv(rec, 8), _uv(rec, 0xA), _uv(rec, 0xC)])
        return _textured(p, rec, 0xE)
    if kind == 0x2D:              # GT3 / GT4
        if quad:
            p = Primitive(kind, True, [c, d, b, a], [_lo(w[1]), _hi(w[2]), _hi(w[1]), _lo(w[2])],
                          [_uv(rec, 0xC), _uv(rec, 0x12), _uv(rec, 0xE), _uv(rec, 0x10)])
            return _textured(p, rec, 0x14)
        p = Primitive(kind, False, [a, b, c], [_lo(w[1]), _hi(w[1]), _lo(w[2])],
                      [_uv(rec, 0xC), _uv(rec, 0xE), _uv(rec, 0x10)])
        return _textured(p, rec, 0x12)
    if kind == 0x2F:              # G3+GT3 / G4+GT4 in one packet: Gouraud base, texture on top
        if quad:
            p = Primitive(kind, True, [c, d, b, a], [_lo(w[3]), _hi(w[4]), _hi(w[3]), _lo(w[4])],
                          [_uv(rec, 0x14), _uv(rec, 0x1A), _uv(rec, 0x16), _uv(rec, 0x18)],
                          base_colors=[_lo(w[1]), _hi(w[2]), _hi(w[1]), _lo(w[2])])
            return _textured(p, rec, 0x1C)
        p = Primitive(kind, False, [a, b, c], [_hi(w[2]), _lo(w[3]), _hi(w[3])],
                      [_uv(rec, 0x10), _uv(rec, 0x12), _uv(rec, 0x14)],
                      base_colors=[_lo(w[1]), _hi(w[1]), _lo(w[2])])
        return _textured(p, rec, 0x16)
    raise UnsupportedPrimitive(f'primitive kind 0x{kind:02X}')


def parse_mesh(data: bytes, start: int) -> tuple[Mesh, int]:
    """Parse a type 0-2 mesh at byte offset ``start``; returns (mesh, end offset)."""
    h = struct.unpack_from(f'<{MESH_HEADER_WORDS}I', data, start)
    pos = start + MESH_HEADER_WORDS * 4
    count = h[0x25]
    verts = np.frombuffer(data, '<i2', count * 4, pos).reshape(count, 4)[:, :3].astype(np.int32)
    pos += count * 8
    groups = []
    for g in range(h[0x27] + h[0x28]):
        word, n = struct.unpack_from('<II', data, pos)
        normals = np.frombuffer(data, '<i2', n * 4, pos + 8).reshape(n, 4)[:, :3].astype(np.int32)
        groups.append(NormalGroup((word & 0xFF, (word >> 8) & 0xFF, (word >> 16) & 0xFF), normals,
                                  word >> 24 if g >= h[0x27] else None))
        pos += 8 + n * 8
    exports = [((w & 0xFF), _hi(w)) for w in struct.unpack_from(f'<{h[0x29]}I', data, pos)]
    pos += h[0x29] * 4
    imports = [(_lo(w), _hi(w)) for w in struct.unpack_from(f'<{h[0x2A]}I', data, pos)]
    pos += h[0x2A] * 4
    prims, unsupported = [], {}
    for key, lo_words, hi_words in PRIMITIVE_LAYOUT:
        for quad, (n, words) in enumerate(zip(_half(h[key]), (lo_words, hi_words))):
            for _ in range(n):
                rec = data[pos:pos + words * 4]
                if key in DECODED_KINDS:
                    prims.append(decode_primitive(key, bool(quad), rec))
                else:
                    unsupported[key] = unsupported.get(key, 0) + 1
                pos += words * 4
    lo, hi = _half(h[LAST_COUNT_WORD])
    if lo or hi:
        unsupported[LAST_COUNT_WORD] = lo + hi
    pos += lo * 16 + hi * 0x14
    return Mesh(verts, h[0x26], groups, exports, imports, prims, unsupported), pos


def parse_model(data: bytes, *, allow_zero_padding: bool = False) -> Model:
    """Parse exactly, optionally accepting only zero padding after a complete model."""
    count = struct.unpack_from('<I', data, 0)[0]
    if not count or 4 + 16 * count > len(data):
        raise ValueError('invalid model node count')
    links = [list(struct.unpack_from('<4i', data, 4 + 16 * i)) for i in range(count)]
    if any(link < NO_LINK or link >= count for row in links for link in row):
        raise ValueError('model link outside node table')
    roots, r = [], 0
    while r != NO_LINK:
        if r in roots:
            raise ValueError('cyclic model roots')
        roots.append(r)
        r = links[r][3]
    model = Model([None] * count, roots)          # type: ignore[list-item]
    pos = 4 + 16 * count
    for n in _walk(links, roots):
        kind = struct.unpack_from('<I', data, pos)[0]
        mesh, inst = None, None
        if kind == 0:
            pos += 4
        elif kind == 2:
            inst = n + struct.unpack_from('<i', data, pos + 4)[0]
            pos += 8
        elif kind == 1:
            mesh, pos = parse_mesh(data, pos)
        elif kind == 3:
            pos += (3 + struct.unpack_from('<I', data, pos + 8)[0] * 2) * 4
        elif kind == 4:
            n4 = struct.unpack_from('<I', data, pos + 16)[0]
            lo, hi = _half(struct.unpack_from('<I', data, pos + 20)[0])
            pos += (0x13 + n4 * 2 + lo * 2 + hi * 2) * 4
        else:
            raise ValueError(f'node {n}: unknown type {kind}')
        xf = struct.unpack_from('<3h2x8i', data, pos)
        model.nodes[n] = Node(n, links[n], kind, xf[0:3], xf[3:6], xf[7:10], mesh, inst)
        pos += TRANSFORM_WORDS * 4
    if pos != len(data) and not (allow_zero_padding and pos < len(data) and not any(data[pos:])):
        raise ValueError(f'model parse ended at {pos}, file has {len(data)} bytes')
    return model


def _walk(links: list[list[int]], roots: list[int]) -> list[int]:
    order: list[int] = []
    seen: set[int] = set()

    for root in roots:
        pending = [root]
        while pending:
            n = pending.pop()
            if n < 0:
                continue
            if n in seen:
                raise ValueError('cyclic or shared model node')
            seen.add(n)
            order.append(n)
            pending.extend((links[n][2], links[n][1]))
    if len(order) != len(links):
        raise ValueError('unreachable model nodes')
    return order


# ---------------------------------------------------------------- TIM textures

@dataclass
class Tim:
    bpp: int                     # 4 or 8 (16-bit direct not used by character packs)
    clut: np.ndarray             # (rows, entries) uint16
    pixels: np.ndarray           # (h, w_texels) palette indices
    clut_origin: tuple[int, int]
    image_origin: tuple[int, int]


def parse_tim(data: bytes) -> Tim:
    """Parse a 4/8-bit CLUT TIM."""
    magic, flags = struct.unpack_from('<II', data, 0)
    if magic != 0x10 or not flags & 8 or (flags & 3) > 1:
        raise ValueError('only 4/8-bit TIMs with CLUT are supported')
    bpp = 4 if flags & 3 == 0 else 8
    ln, cx, cy, cw, ch = struct.unpack_from('<IHHHH', data, 8)
    clut = np.frombuffer(data, '<u2', cw * ch, 20).reshape(ch, cw)
    o = 8 + ln
    _, ix, iy, iw, ih = struct.unpack_from('<IHHHH', data, o)
    raw = np.frombuffer(data, np.uint8, iw * ih * 2, o + 12).reshape(ih, iw * 2)
    if bpp == 4:
        pix = np.empty((ih, iw * 4), np.uint8)
        pix[:, 0::2], pix[:, 1::2] = raw & 0xF, raw >> 4
    else:
        pix = raw.copy()
    return Tim(bpp, clut, pix, (cx, cy), (ix, iy))


def clut_to_rgba(clut_row: np.ndarray) -> np.ndarray:
    """15-bit BGR palette -> RGBA uint8; colour 0x0000 is the GPU's transparent texel."""
    c = clut_row.astype(np.uint32)
    rgba = np.stack([(c & 31) * 255 // 31, ((c >> 5) & 31) * 255 // 31,
                     ((c >> 10) & 31) * 255 // 31, np.where(c == 0, 0, 255)], -1)
    return rgba.astype(np.uint8)


def tim_rgba(tim: Tim, clut_row: int = 0) -> np.ndarray:
    """Whole TIM image as RGBA with the given CLUT row."""
    return clut_to_rgba(tim.clut[min(clut_row, len(tim.clut) - 1)])[tim.pixels]


def load_character(model_dir: Path, pack_dir: Path) -> tuple[Model, bytes, list[Tim]]:
    """Model 000.bin, motion bank 001.bin and the texture-slot TIMs of a character.

    Texture slot k -> k-th TIM after 000.tim (shared shadow/effect sheet). Evidence: Strike
    RAM dump slot table 0x80051DA4 (slot 0 CLUT 13 rows = 002.tim); not proven for Heat.
    """
    model = parse_model((model_dir / '000.bin').read_bytes())
    motions = (model_dir / '001.bin').read_bytes()
    tims = [parse_tim(p.read_bytes()) for p in sorted(pack_dir.glob('*.tim')) if p.stem != '000']
    return model, motions, tims
