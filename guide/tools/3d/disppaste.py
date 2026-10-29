# Warp the clean display glyphs (TIME + -) onto a generated photo's display glass.
import sys, numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
src, out = sys.argv[1], sys.argv[2]
q = [tuple(map(float, p.split(","))) for p in sys.argv[3:7]]  # TL TR BR BL of glass
gain = float(sys.argv[7]) if len(sys.argv) > 7 else 0.82
im = Image.open(src).convert("RGB")
g = Image.open("display.png").convert("RGBA")
bg = Image.new("RGB", g.size, (0, 0, 0)); bg.paste(g, mask=g.split()[3]); g = bg
d = ImageDraw.Draw(g)
for cx in (440, 530): d.ellipse((cx-16, 148, cx+16, 182), fill=(0, 0, 0))
w, h = g.size
def coeffs(dst, srcp):
    A = []; B = []
    for (x, y), (u, v) in zip(dst, srcp):
        A += [[x, y, 1, 0, 0, 0, -u*x, -u*y], [0, 0, 0, x, y, 1, -v*x, -v*y]]; B += [u, v]
    return np.linalg.solve(np.array(A), np.array(B)).tolist()
c = coeffs(q, [(0, 0), (w, 0), (w, h), (0, h)])
warped = im.copy(); warped.paste((0, 0, 0), (0, 0) + im.size)
glyph = g.transform(im.size, Image.PERSPECTIVE, c, Image.BICUBIC).filter(ImageFilter.GaussianBlur(0.8))
mask = Image.new("L", im.size, 0); ImageDraw.Draw(mask).polygon(q, fill=255)
mask = mask.filter(ImageFilter.GaussianBlur(1.5))
# keep glass reflections: darken the old glyphs with a smoothed glass colour, then add new glyphs
glass = im.filter(ImageFilter.MedianFilter(15)).filter(ImageFilter.MinFilter(9))
base = Image.composite(glass, im, mask)
glyph = glyph.point(lambda v: int(v * gain))
res = ImageChops.add(base, Image.composite(glyph, Image.new("RGB", im.size), mask))
res.save(out)
xs = [p[0] for p in q]; ys = [p[1] for p in q]
pad = 40
res.crop((int(min(xs))-pad, int(min(ys))-pad, int(max(xs))+pad, int(max(ys))+pad)).resize((int((max(xs)-min(xs)+2*pad)*3), int((max(ys)-min(ys)+2*pad)*3))).save(out.rsplit(".", 1)[0] + "-dcrop.jpg")
