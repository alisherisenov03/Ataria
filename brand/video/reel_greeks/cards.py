"""Illustration cards for the reel, built from the owner's real pillow photos (no renders).

    python cards.py brand/photos/pillow1 OUT_DIR
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

# card name: (photo, crop box or None, fill the square?, label lines)
CARDS = {
    "info_profile.png": ("front_view.jpg", (100, 520, 880, 800), False, ["Валик — под шею"]),
    "info_top.png": ("top_dimensions.jpg", (0, 280, 900, 840), False, ["Крылья — для сна на боку"]),
    "photo_bed.png": ("on_bed_hand.jpg", None, True, []),
    "photo_foam.png": ("foam_insert.jpg", None, False, ["Внутри — пена с памятью"]),
    "photo_top.png": ("top_grey.jpg", (0, 640, 1920, 1920), True, []),
    "info_zip.png": ("zipper.jpg", None, True, ["Чехол на молнии"]),
    "photo_stack.png": ("stack.jpg", None, True, []),
}


def rounded(im, r):
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, *im.size), r, fill=255)
    out = Image.new("RGBA", im.size)
    out.paste(im, (0, 0), mask)
    return out


def card(photo, crop, fill, lines):
    if crop:
        photo = photo.crop(crop)
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
    photos, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    for name, (photo, crop, fill, lines) in CARDS.items():
        card(Image.open(photos / photo).convert("RGB"), crop, fill, lines).save(out / name)
    kaspi_card().save(out / "kaspi.png")


if __name__ == "__main__":
    main()
