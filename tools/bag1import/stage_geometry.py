"""Profile-scoped subdivision of native FT4 surfaces, without global OT biases."""

import struct

import model_bag1_to_bag2 as model

HEADER_WORDS = 0x48
VERTEX_COUNT = 0x25
FT4_COUNTS = 0x30
TRANSFORM_BYTES = 40
PRE_FT4_LAYOUT = ((0x2B, 2, 2), (0x2C, 4, 4), (0x2D, 5, 6),
                  (0x2E, 3, 3), (0x2F, 6, 8))


def _interpolate(corners: list[tuple], x: int, y: int, divisions: int) -> tuple:
    weights = ((divisions-x)*(divisions-y), x*(divisions-y),
               (divisions-x)*y, x*y)
    return tuple(sum(weight*corner[axis] for weight, corner in zip(weights, corners))
                 // (divisions*divisions) for axis in range(len(corners[0])))


def _split_mesh(data: bytes, spec: dict) -> bytes:
    words = list(struct.unpack(f'<{len(data)//4}I', data))
    divisions, quad = spec['divisions'], spec['quad']
    if type(divisions) is not int or not 2 <= divisions <= 8:
        raise ValueError('FT4 divisions must be an integer in 2..8')
    count = words[VERTEX_COUNT]
    if count + (divisions+1)**2 > 256:
        raise ValueError('FT4 subdivision exceeds byte vertex-index capacity')
    cursor = HEADER_WORDS + count*2
    for _ in range(words[0x27] + words[0x28]):
        cursor += words[cursor+1]*2 + 2
    cursor += words[0x29] + words[0x2A]
    for field, low_stride, high_stride in PRE_FT4_LAYOUT:
        cursor += (words[field] & 0xffff)*low_stride + (words[field] >> 16)*high_stride
    cursor += (words[FT4_COUNTS] & 0xffff)*4
    quad_count = words[FT4_COUNTS] >> 16
    if type(quad) is not int or not 0 <= quad < quad_count:
        raise ValueError('FT4 quad index outside selected mesh')
    start = (cursor+quad*5)*4
    native = struct.unpack_from('<5I', data, start)
    if list(native) != spec['expected_words']:
        raise ValueError('FT4 primitive guard does not match native surface')
    indices = [(native[0] >> shift) & 255 for shift in (0, 8, 16, 24)]
    if max(indices) >= count:
        raise ValueError('FT4 primitive references a missing vertex')
    vertices = [struct.unpack_from('<4h', data, HEADER_WORDS*4+index*8)
                for index in indices]
    uv = [(value & 255, value >> 8) for value in
          (native[2] & 0xffff, native[2] >> 16, native[3] & 0xffff, native[3] >> 16)]
    # MCP-verified emitter: GPU vertex order d,a,c,b; UV order a,d,b,c.
    corners, uv_corners = [vertices[i] for i in (3, 0, 2, 1)], [uv[i] for i in (0, 3, 1, 2)]
    grid, uv_grid = [], []
    for y in range(divisions+1):
        for x in range(divisions+1):
            grid.append(_interpolate(corners, x, y, divisions))
            uv_grid.append(_interpolate(uv_corners, x, y, divisions))
    tiles = bytearray()
    for y in range(divisions):
        for x in range(divisions):
            a = y*(divisions+1)+x
            b, c, d = a+1, a+divisions+1, a+divisions+2
            packed_indices = sum((count+index) << shift for index, shift in
                                 zip((b, d, c, a), (0, 8, 16, 24)))
            packed_uv = [uv_grid[i][0] | (uv_grid[i][1] << 8) for i in (a, c, d, b)]
            tiles += struct.pack('<5I', packed_indices, native[1],
                                 packed_uv[0] | (packed_uv[1] << 16),
                                 packed_uv[2] | (packed_uv[3] << 16), native[4])
    words[VERTEX_COUNT] = count+len(grid)
    words[FT4_COUNTS] += (divisions*divisions-1) << 16
    vertex_end = HEADER_WORDS*4+count*8
    return (struct.pack(f'<{HEADER_WORDS}I', *words[:HEADER_WORDS])
            + data[HEADER_WORDS*4:vertex_end]
            + b''.join(struct.pack('<4h', *vertex) for vertex in grid)
            + data[vertex_end:start] + tiles + data[start+20:])


def subdivide_ft4_meshes(data: bytes, specs: list[dict]) -> bytes:
    """Split guarded native quads into bilinear tiles; retain all other node bytes.

    Specs select node, quad, divisions and the five expected native record words.
    Coordinates/UVs are quantized down to their original integer representation.
    Repeated node selections are rejected rather than applying shifting indices.
    """
    if not specs:
        return data
    selected = {spec['node']: spec for spec in specs}
    if len(selected) != len(specs):
        raise ValueError('FT4 subdivision has duplicate node selections')
    if model.check_bag2(data):
        raise ValueError('FT4 subdivision requires a structurally valid BAG2 model')
    words = struct.unpack(f'<{len(data)//4}I', data)
    count = words[0]
    links = [struct.unpack_from('<4i', data, 4+16*i) for i in range(count)]
    cursor, applied = (1+count*4)*4, set()
    out = bytearray(data[:cursor])
    for node in model.walk_order(links):
        wi, kind = cursor//4, words[cursor//4]
        if kind == 1:
            size = model.mesh_len_bag2(words, wi)
        elif kind in (0, 2):
            size = (1 if kind == 0 else 2)*4
        elif kind == 3:
            size = (3+words[wi+2]*2)*4
        elif kind == 4:
            size = (0x13+words[wi+4]*2+(words[wi+5] & 0xffff)*2+(words[wi+5] >> 16)*2)*4
        else:
            raise ValueError(f'Unsupported node type {kind}')
        mesh = data[cursor:cursor+size]
        if node in selected:
            if kind != 1:
                raise ValueError('FT4 subdivision requires a full mesh node')
            mesh = _split_mesh(mesh, selected[node])
            applied.add(node)
        out += mesh + data[cursor+size:cursor+size+TRANSFORM_BYTES]
        cursor += size+TRANSFORM_BYTES
    if applied != set(selected):
        raise ValueError('FT4 subdivision references a missing node')
    if model.check_bag2(out):
        raise ValueError('FT4 subdivision produced invalid model structure')
    return bytes(out)
