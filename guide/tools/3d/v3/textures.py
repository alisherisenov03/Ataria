# Textures for model v3, drawn to match the owner's photos (044 display, 034 port cover, 037 lever, 006 dial).
import math
from PIL import Image, ImageDraw, ImageFilter, ImageFont
F = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def seg_digit(d, x, y, w, h, t, segs, col, skew=0.12):
    # 7-segment digit with italic skew; segs: string of lit segments 'abcdefg'
    def P(px, py): return (x + px + (h - py) * skew, y + py)
    hw = t / 2; m = h / 2
    S = {
        'a': [(t*0.6, 0), (w - t*0.6, 0), (w - t*1.2, t), (t*1.2, t)],
        'd': [(t*1.2, h - t), (w - t*1.2, h - t), (w - t*0.6, h), (t*0.6, h)],
        'g': [(t*0.9, m - hw), (w - t*0.9, m - hw), (w - t*0.4, m), (w - t*0.9, m + hw), (t*0.9, m + hw), (t*0.4, m)],
        'f': [(0, t*0.6), (t, t*1.2), (t, m - t*0.7), (0, m - t*0.2)],
        'e': [(0, m + t*0.2), (t, m + t*0.7), (t, h - t*1.2), (0, h - t*0.6)],
        'b': [(w, t*0.6), (w, m - t*0.2), (w - t, m - t*0.7), (w - t, t*1.2)],
        'c': [(w, m + t*0.2), (w, h - t*0.6), (w - t, h - t*1.2), (w - t, m + t*0.7)],
    }
    for k in segs: d.polygon([P(*p) for p in S[k]], fill=col)

DIG = {'0': 'abcdef', '1': 'bc', '5': 'afgcd', '3': 'abgcd'}

def display():
    W, H = 1400, 1000
    im = Image.new("RGB", (W, H), (6, 7, 12)); d = ImageDraw.Draw(im)
    # backlit LCD window
    win = (90, 130, W - 90, 560)
    glow = Image.new("RGB", (W, H), (0, 0, 0)); gd = ImageDraw.Draw(glow)
    gd.rectangle(win, fill=(70, 62, 210)); glow = glow.filter(ImageFilter.GaussianBlur(18))
    im = Image.blend(im, glow, 0.35); d = ImageDraw.Draw(im)
    d.rectangle(win, fill=(88, 76, 226))
    lay = Image.new("RGB", (W, H), (0, 0, 0)); ld = ImageDraw.Draw(lay)
    col = (225, 222, 255)
    y0, w, h, t = 175, 210, 340, 34
    for x, ch in zip((140, 395, 700, 955), "1500"):
        seg_digit(ld, x, y0, w, h, t, DIG[ch], col)
    for cy in (y0 + h * 0.32, y0 + h * 0.68):
        cx = 650 + (y0 + h - cy) * 0.12
        ld.ellipse((cx - 16, cy - 16, cx + 16, cy + 16), fill=col)
    halo = lay.filter(ImageFilter.GaussianBlur(6))
    im = Image.composite(lay, im, lay.convert("L"))
    im = Image.blend(im, Image.eval(halo, lambda v: min(255, v)), 0.0)
    d = ImageDraw.Draw(im)
    # touch buttons: white glyphs with blue glowing rings
    ring = Image.new("RGB", (W, H), (0, 0, 0)); rd = ImageDraw.Draw(ring)
    cs = [(330, 790), (700, 790), (1070, 790)]
    for cx, cy in cs: rd.ellipse((cx - 115, cy - 115, cx + 115, cy + 115), outline=(70, 110, 255), width=16)
    im = Image.composite(ring.filter(ImageFilter.GaussianBlur(5)), im, ring.convert("L").filter(ImageFilter.GaussianBlur(5)).point(lambda v: min(255, v * 3)))
    d = ImageDraw.Draw(im)
    for cx, cy in cs: d.ellipse((cx - 108, cy - 108, cx + 108, cy + 108), outline=(205, 215, 255), width=7)
    f = ImageFont.truetype(F, 74)
    d.text((330, 792), "TIME", font=f, fill=(235, 238, 255), anchor="mm")
    d.rectangle((700 - 55, 790 - 8, 700 + 55, 790 + 8), fill=(235, 238, 255)); d.rectangle((700 - 8, 790 - 55, 700 + 8, 790 + 55), fill=(235, 238, 255))
    d.rectangle((1070 - 55, 790 - 8, 1070 + 55, 790 + 8), fill=(235, 238, 255))
    im.save("display3.png")

def port_cover():
    # U-shaped cover outline with two lines and a triangle (photo 034); transparent background
    W, H = 600, 900
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    ln = (14, 14, 15, 255)
    d.rounded_rectangle((20, -200, W - 20, H - 20), radius=110, outline=ln, width=9)
    hl = (95, 95, 98, 255)
    d.line((185, 170, 415, 170), fill=hl, width=10); d.line((205, 250, 395, 250), fill=hl, width=10)
    d.polygon([(215, 360), (385, 360), (300, 520)], outline=hl, width=10)
    im.save("port.png")

def lock_icon():
    W, H = 700, 400
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    c = (225, 225, 228, 255)
    d.rectangle((60, 215, 190, 330), outline=c, width=14)
    d.arc((85, 110, 205, 260), 180, 360, fill=c, width=14)  # open shackle shifted right
    d.line((205, 185, 205, 190), fill=c, width=14)
    d.arc((-60, -260, 420, 330), 10, 70, fill=c, width=10)
    im.save("lock.png")

def dial_parts():
    src = Image.open("006.png").convert("RGBA")
    c = 512
    ring = src.copy(); m = Image.new("L", src.size, 0); md = ImageDraw.Draw(m)
    md.ellipse((c - 500, c - 500, c + 500, c + 500), fill=255); md.ellipse((c - 340, c - 340, c + 340, c + 340), fill=0)
    ring.putalpha(m.filter(ImageFilter.GaussianBlur(2))); ring.save("dial_ring.png")
    cap = src.crop((c - 300, c - 300, c + 300, c + 300)); m2 = Image.new("L", cap.size, 0)
    ImageDraw.Draw(m2).ellipse((4, 4, 596, 596), fill=255); cap.putalpha(m2); cap.save("dial_cap.png")

display(); port_cover(); lock_icon(); dial_parts(); print("ok")
