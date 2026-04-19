"""HOMTECH uygulama ikonu üretir."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "src" / "web_demo"
PNG_PATH = OUTPUT_DIR / "app_icon.png"
ICO_PATH = OUTPUT_DIR / "app_icon.ico"


def _rounded_panel_mask(size: int, radius: int) -> Image.Image:
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((12, 12, size - 12, size - 12), radius=radius, fill=255)
    return mask


def _draw_orb(draw: ImageDraw.ImageDraw, center: tuple[int, int], radius: int) -> None:
    x, y = center
    draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(255, 248, 239, 255))
    draw.ellipse((x - radius + 10, y - radius + 10, x + radius - 10, y + radius - 10), fill=(255, 255, 255, 35))


def _draw_home_outline(draw: ImageDraw.ImageDraw, size: int) -> None:
    stroke = 18
    line = (255, 255, 255, 230)
    roof = [
        (size * 0.30, size * 0.47),
        (size * 0.50, size * 0.27),
        (size * 0.70, size * 0.47),
    ]
    draw.line(roof, fill=line, width=stroke, joint="curve")
    draw.line([(size * 0.35, size * 0.47), (size * 0.35, size * 0.69)], fill=line, width=stroke)
    draw.line([(size * 0.65, size * 0.47), (size * 0.65, size * 0.69)], fill=line, width=stroke)
    draw.line([(size * 0.35, size * 0.69), (size * 0.65, size * 0.69)], fill=line, width=stroke)
    draw.rounded_rectangle(
        (size * 0.46, size * 0.56, size * 0.54, size * 0.69),
        radius=12,
        outline=line,
        width=stroke - 6,
    )


def build_icon(size: int = 1024) -> Image.Image:
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    base = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    base_draw = ImageDraw.Draw(base)

    for index, color in enumerate(
        [
            (255, 208, 126, 255),
            (243, 174, 98, 255),
            (79, 201, 213, 255),
            (21, 42, 82, 255),
        ]
    ):
        inset = 24 + (index * 34)
        base_draw.rounded_rectangle(
            (inset, inset, size - inset, size - inset),
            radius=250 - (index * 26),
            outline=color,
            width=36,
        )

    base = base.filter(ImageFilter.GaussianBlur(1.2))

    panel = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    panel_draw = ImageDraw.Draw(panel)
    panel_draw.rounded_rectangle(
        (18, 18, size - 18, size - 18),
        radius=240,
        fill=(17, 28, 54, 255),
    )

    glow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse((140, 110, 700, 670), fill=(64, 218, 224, 140))
    glow_draw.ellipse((330, 360, 920, 960), fill=(255, 177, 96, 115))
    glow = glow.filter(ImageFilter.GaussianBlur(48))

    accent = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    accent_draw = ImageDraw.Draw(accent)
    accent_draw.rounded_rectangle(
        (72, 72, size - 72, size - 72),
        radius=190,
        outline=(255, 255, 255, 24),
        width=4,
    )
    accent_draw.arc((150, 150, size - 150, size - 150), 212, 334, fill=(255, 202, 122, 235), width=28)
    accent_draw.arc((180, 180, size - 180, size - 180), 22, 132, fill=(95, 225, 231, 235), width=22)

    image.alpha_composite(panel)
    image.alpha_composite(glow)
    image.alpha_composite(base)
    image.alpha_composite(accent)

    draw = ImageDraw.Draw(image)
    _draw_orb(draw, (size // 2, int(size * 0.45)), 124)
    _draw_home_outline(draw, size)

    mask = _rounded_panel_mask(size, 240)
    image.putalpha(mask)
    return image


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    icon = build_icon()
    icon.save(PNG_PATH)
    icon.save(ICO_PATH, sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
    print(f"PNG kaydedildi: {PNG_PATH}")
    print(f"ICO kaydedildi: {ICO_PATH}")


if __name__ == "__main__":
    main()
