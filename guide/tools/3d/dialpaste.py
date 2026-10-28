import sys
from PIL import Image, ImageDraw, ImageFilter
src, out, cx, cy, rx, ry, rot = sys.argv[1], sys.argv[2], *map(float, sys.argv[3:8])
im = Image.open(src).convert("RGB")
d = Image.open("zip/x/006.png").convert("RGB")
R = 490; d = d.crop((512-R, 512-R, 512+R, 512+R))
w, h = int(2*rx), int(2*ry)
d = d.resize((w, h), Image.LANCZOS).rotate(rot, resample=Image.BICUBIC, expand=False)
m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).ellipse((3, 3, w-3, h-3), fill=255)
m = m.filter(ImageFilter.GaussianBlur(2.5))
im.paste(d, (int(cx-rx), int(cy-ry)), m)
im.save(out)
im.crop((int(cx-2*rx), int(cy-1.6*ry), int(cx+2*rx), int(cy+1.6*ry))).resize((560, int(560*3.2*ry/(4*rx)))).save(out.replace(".png", "-crop.jpg"))
