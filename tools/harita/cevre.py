# Çevre altlığı: HGM haritasının Acıpayam çevresi, soluk ve kenarları yumuşak (WebP, alfa)
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
VX0, VY0, VW, VH = -350, -250, 3050, 3100      # acp koordinatları
AX, AY = 1550, 3700                            # acp kesitinin tam haritadaki yeri
im = Image.open('img-000.jpg').convert('L').crop((AX + VX0, AY + VY0, AX + VX0 + VW, AY + VY0 + VH))
im = im.resize((VW // 2, VH // 2), Image.LANCZOS)
L = np.asarray(im).astype(float)
v = 255 - (255 - L) * 0.42
rgb = np.stack([v * .975, v * .955, v * 1.0], -1).clip(0, 255)
h, w = L.shape
yy, xx = np.mgrid[0:h, 0:w]
d = np.minimum.reduce([xx, yy, w - 1 - xx, h - 1 - yy]) / (0.11 * min(w, h))
a = (np.clip(d, 0, 1) ** 1.6 * 255)
Image.fromarray(np.dstack([rgb, a]).astype(np.uint8), 'RGBA').save('/home/user/acipayam-site/static/img/acipayam-cevre.webp', quality=72, method=6)
print(w, h)
