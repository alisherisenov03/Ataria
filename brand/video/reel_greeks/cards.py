"""Illustration cards for the reel, built from the real pillow photos (no renders).

    python cards.py brand/ataria_pillow1_reference.jpg OUT_DIR
The reference is a 2072x2376 collage of six photos; CROPS are their boxes in it.
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

S = 720
CARD = (239, 233, 225)
INK = (38, 33, 29)
ACCENT = (46, 160, 90)
FONT = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
FONT_MED = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"

CROPS = {
    "side": (178, 345, 869, 631),
    "top": (1202, 137, 1880, 601),
    "table": (24, 863, 1026, 1517),
    "bed": (1322, 809, 1779, 1571),
    "zip": (129, 1595, 919, 2356),
    "tag": (1170, 1595, 1930, 2356),
}

# card name: (photo, fill the square?, label lines)
CARDS = {
    "info_profile.png": ("side", False, ["Валик — под шею", "Углубление — под голову"]),
    "info_top.png": ("top", False, ["Крылья по бокам —", "для сна на боку"]),
    "photo_bed.png": ("bed", True, []),
    "info_zip.png": ("zip", True, ["Чехол на молнии"]),
    "photo_table.png": ("table", False, ["Подушка ATARIA 40×60"]),
}


def rounded(im, r):
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, *im.size), r, fill=255)
    out = Image.new("RGBA", im.size)
    out.paste(im, (0, 0), mask)
    return out


def card(src, crop, fill, lines):
    photo = src.crop(CROPS[crop])
    canvas = Image.new("RGB", (S, S), CARD)
    text_h = 70 * len(lines) + (30 if lines else 0)
    if fill:
        box_w, box_h = S, S - text_h
        scale = max(box_w / photo.width, box_h / photo.height)
        photo = photo.resize((round(photo.width * scale), round(photo.height * scale)), Image.LANCZOS)
        x0, y0 = (photo.width - box_w) // 2, (photo.height - box_h) // 2
        photo = photo.crop((x0, y0, x0 + box_w, y0 + box_h))
        canvas.paste(photo, (0, 0))
    else:
        box_w, box_h = S - 60, S - text_h - 60
        scale = min(box_w / photo.width, box_h / photo.height)
        photo = photo.resize((round(photo.width * scale), round(photo.height * scale)), Image.LANCZOS)
        canvas.paste(photo, ((S - photo.width) // 2, 30 + (box_h - photo.height) // 2))
    d = ImageDraw.Draw(canvas)
    font = ImageFont.truetype(FONT_MED, 46)
    y = S - text_h + 10
    for i, line in enumerate(lines):
        w = d.textlength(line, font=font)
        d.text(((S - w) / 2, y + i * 70), line, font=font, fill=ACCENT if i == 0 and len(lines) > 1 else INK)
    return rounded(canvas, 36)


def kaspi_card():
    canvas = Image.new("RGB", (S, S), CARD)
    d = ImageDraw.Draw(canvas)
    big = ImageFont.truetype(FONT, 230)
    mid = ImageFont.truetype(FONT_MED, 56)
    for text, font, y, color in [("4,9", big, 120, INK), ("★★★★★", mid, 400, (242, 168, 0)),
                                 ("рейтинг на Kaspi", mid, 500, INK), ("600+ отзывов", mid, 580, (109, 100, 91))]:
        w = d.textlength(text, font=font)
        d.text(((S - w) / 2, y), text, font=font, fill=color)
    return rounded(canvas, 36)


def main():
    src = Image.open(sys.argv[1]).convert("RGB")
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    for name, (crop, fill, lines) in CARDS.items():
        card(src, crop, fill, lines).save(out / name)
    kaspi_card().save(out / "kaspi.png")


if __name__ == "__main__":
    main()
