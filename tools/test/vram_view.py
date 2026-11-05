"""Render a BAG2JP_VRAM_DUMP file and decode Strike's runtime CLUT rows.

The runtime descriptors place Strike's body CLUTs at P1 (960,0)/(976,0) and
P2 (960,16)/(976,16), 16 colours per row (notes/strike-recovery.md).
"""
import argparse
import json
from pathlib import Path

from PIL import Image

WIDTH, HEIGHT = 1024, 512
CLUT_BLOCKS = {'p1_tim1': (960, 0), 'p1_tim2': (976, 0), 'p2_tim1': (960, 16), 'p2_tim2': (976, 16)}
ROWS = 16


def load(path: Path) -> list[int]:
    """Read raw little-endian 16-bit pixels; reject anything not a full VRAM."""
    data = path.read_bytes()
    if len(data) != WIDTH * HEIGHT * 2:
        raise ValueError(f'Unexpected VRAM dump size {len(data)}')
    return [data[i] | data[i + 1] << 8 for i in range(0, len(data), 2)]


def rgb(pixel: int) -> tuple[int, int, int]:
    """PSX 15-bit BGR555 to 8-bit RGB."""
    return ((pixel & 31) * 255 // 31, (pixel >> 5 & 31) * 255 // 31, (pixel >> 10 & 31) * 255 // 31)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('dump', type=Path)
    parser.add_argument('--reference', type=Path, help='second dump for row-by-row CLUT comparison')
    args = parser.parse_args()
    pixels = load(args.dump)
    image = Image.new('RGB', (WIDTH, HEIGHT))
    image.putdata([rgb(p) for p in pixels])
    image.save(args.dump.with_suffix('.png'))
    blocks = {}
    sheet = Image.new('RGB', (len(CLUT_BLOCKS) * 16 * 12 + 30, ROWS * 12), 'black')
    for column, (name, (x, y)) in enumerate(CLUT_BLOCKS.items()):
        rows = [[pixels[(y + r) * WIDTH + x + c] for c in range(16)] for r in range(ROWS)]
        blocks[name] = {'origin': [x, y], 'nonzero_rows': [r for r, row in enumerate(rows) if any(row)],
                        'rows_hex': [''.join(f'{p:04x}' for p in row) for row in rows]}
        for r, row in enumerate(rows):
            for c, p in enumerate(row):
                for dy in range(11):
                    for dx in range(11):
                        sheet.putpixel((column * (16 * 12 + 10) + c * 12 + dx, r * 12 + dy), rgb(p))
    sheet.resize((sheet.width * 2, sheet.height * 2), Image.NEAREST).save(args.dump.with_name(args.dump.stem + '-cluts.png'))
    result = {'dump': str(args.dump), 'clut_blocks': blocks}
    if args.reference:
        other = load(args.reference)
        result['row_differences'] = {
            name: [r for r in range(ROWS) if any(pixels[(y + r) * WIDTH + x + c] != other[(y + r) * WIDTH + x + c] for c in range(16))]
            for name, (x, y) in CLUT_BLOCKS.items()}
    args.dump.with_name(args.dump.stem + '-cluts.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({name: block['nonzero_rows'] for name, block in blocks.items()}))
    if args.reference:
        print(json.dumps(result['row_differences']))


if __name__ == '__main__':
    main()
