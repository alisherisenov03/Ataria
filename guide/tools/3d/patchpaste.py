# Paste a circular patch from a real photo onto a generated photo, matched in colour.
import sys, numpy as np
from PIL import Image, ImageDraw, ImageFilter
dst, src, out = sys.argv[1:4]
sx, sy, sr, dx, dy, dr = map(float, sys.argv[4:10])
D = Image.open(dst).convert("RGB"); S = Image.open(src).convert("RGB")
p = S.crop((int(sx-sr), int(sy-sr), int(sx+sr), int(sy+sr))).resize((int(2*dr), int(2*dr)), Image.LANCZOS)
box = (int(dx-dr), int(dy-dr), int(dx-dr)+p.width, int(dy-dr)+p.height)
t = np.asarray(D.crop(box), float); a = np.asarray(p, float)
a = (a - a.mean((0, 1))) * (t.std((0, 1)) / (a.std((0, 1)) + 1e-6)) ** 0.5 + t.mean((0, 1))
p = Image.fromarray(np.clip(a, 0, 255).astype("uint8"))
m = Image.new("L", p.size, 0); ImageDraw.Draw(m).ellipse((4, 4, p.width-4, p.height-4), fill=255)
D.paste(p, box[:2], m.filter(ImageFilter.GaussianBlur(3)))
D.save(out)
D.crop((int(dx-1.6*dr), int(dy-1.6*dr), int(dx+1.6*dr), int(dy+1.6*dr))).save(out.rsplit(".", 1)[0] + "-pcrop.jpg")
