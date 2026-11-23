#!/usr/bin/env python3
"""Generate Bust A Groove 2 PS1-style custom graffiti headers and VS badge
as raw RGBA textures for bag2jp_lobby_ui.c (glBlitFramebuffer)."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT_DIR = Path(r"D:\Games\Bust A Groove 2 (Japan)\BAG2JP-exp-8mb\online_avatars")

FONT_CANDIDATES = [
    r"C:\Windows\Fonts\impact.ttf",
    r"C:\Windows\Fonts\ariblk.ttf",
    r"C:\Windows\Fonts\comicbd.ttf",
    r"C:\Windows\Fonts\arialbd.ttf",
]


def load_font(size: int) -> ImageFont.FreeTypeFont:
    for p in FONT_CANDIDATES:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def draw_outlined_text(
    img: Image.Image,
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int, int],
    inner_outline: tuple[int, int, int, int],
    outer_outline: tuple[int, int, int, int],
) -> None:
    draw = ImageDraw.Draw(img)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (img.width - tw) // 2 - bbox[0]
    y = (img.height - th) // 2 - bbox[1]
    # Outer black comic outline
    for dy in range(-4, 5):
        for dx in range(-4, 5):
            if dx * dx + dy * dy <= 18:
                draw.text((x + dx, y + dy), text, font=font, fill=outer_outline)
    # Inner fiery red outline
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            if dx * dx + dy * dy <= 5:
                draw.text((x + dx, y + dy), text, font=font, fill=inner_outline)
    # Main fill
    draw.text((x, y), text, font=font, fill=fill)


def save_rgba_gl(img: Image.Image, path: Path) -> None:
    flipped = img.convert("RGBA").transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    path.write_bytes(flipped.tobytes())
    print(f"Saved {path.name} ({img.width}x{img.height})")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. ONLINE LOBBY header (320x56) on flat sky-blue (#66B8E8)
    hdr_lobby = Image.new("RGBA", (320, 56), (102, 184, 232, 255))
    draw_outlined_text(
        hdr_lobby,
        "ONLINE LOBBY",
        load_font(40),
        fill=(255, 232, 24, 255),
        inner_outline=(220, 24, 16, 255),
        outer_outline=(16, 16, 20, 255),
    )
    save_rgba_gl(hdr_lobby, OUT_DIR / "hdr_lobby.rgba")

    # 2. ROOM 1V1 header (320x56) on mustard-yellow (#D9B81F) | sky-blue (#66B8E8) split
    hdr_room = Image.new("RGBA", (320, 56), (102, 184, 232, 255))
    ImageDraw.Draw(hdr_room).rectangle([0, 0, 159, 55], fill=(217, 184, 31, 255))
    draw_outlined_text(
        hdr_room,
        "ROOM 1V1",
        load_font(42),
        fill=(255, 232, 24, 255),
        inner_outline=(220, 24, 16, 255),
        outer_outline=(16, 16, 20, 255),
    )
    save_rgba_gl(hdr_room, OUT_DIR / "hdr_room.rgba")

    # 3. VS badge (96x64) on mustard-yellow | sky-blue split
    vs_img = Image.new("RGBA", (96, 64), (102, 184, 232, 255))
    ImageDraw.Draw(vs_img).rectangle([0, 0, 47, 63], fill=(217, 184, 31, 255))
    draw_outlined_text(
        vs_img,
        "VS",
        load_font(48),
        fill=(255, 255, 255, 255),
        inner_outline=(230, 32, 24, 255),
        outer_outline=(16, 16, 20, 255),
    )
    save_rgba_gl(vs_img, OUT_DIR / "vs_badge.rgba")

    # 4. Vertical graffiti side-banners (48x448) matching BAG2 main menu / PS1 mockup
    banner_h = Image.new("RGBA", (448, 48), (217, 184, 31, 255))
    draw_outlined_text(
        banner_h,
        "BUST A GROOVE 2  *  ONLINE",
        load_font(34),
        fill=(64, 224, 56, 255),
        inner_outline=(220, 28, 20, 255),
        outer_outline=(12, 12, 16, 255),
    )
    side_left = banner_h.rotate(90, expand=True)
    side_right = banner_h.rotate(-90, expand=True)
    save_rgba_gl(side_left, OUT_DIR / "side_left.rgba")
    save_rgba_gl(side_right, OUT_DIR / "side_right.rgba")


if __name__ == "__main__":
    main()
