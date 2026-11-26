import json, math, numpy as np
from PIL import Image
from scipy import ndimage as nd
X0, Y0, W, H = 137, 107, 1216, 1441
F = json.load(open('temiz.json'))
K = json.load(open('/home/user/acipayam-site/data/harita-koyler.json'))
a = np.asarray(Image.open('/home/user/acipayam-site/static/img/acipayam-map.webp').convert('RGB')).astype(int)
lum = a.mean(2); chroma = a.max(2) - a.min(2)
txt = (lum < 125) & (chroma < 45)

def horiz(l):
    p = np.array(l); return np.ptp(p[:, 1]) < 3 and np.ptp(p[:, 0]) < 90
for k in ('koyyolu', 'dere'): F[k] = [l for l in F[k] if not horiz(l)]

def d(pts, close=False):
    p = [f"{x:.1f},{y:.1f}" for x, y in pts]
    return "M" + " L".join(p) + (" Z" if close else "")

def smooth(pts, close=False):
    # Catmull-Rom → kübik Bezier
    P = [tuple(p) for p in pts]
    if close and P[0] == P[-1]: P = P[:-1]
    n = len(P)
    if n < 3: return d(P, close)
    s = f"M{P[0][0]:.1f},{P[0][1]:.1f}"
    rng = range(n) if close else range(n - 1)
    for i in rng:
        p0 = P[(i - 1) % n] if close else P[max(i - 1, 0)]
        p1 = P[i]; p2 = P[(i + 1) % n]
        p3 = P[(i + 2) % n] if close else P[min(i + 2, n - 1)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        s += f" C{c1[0]:.1f},{c1[1]:.1f} {c2[0]:.1f},{c2[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}"
    return s + (" Z" if close else "")

FS = 19
GORUSME = {'Akalan','Alaattin','Apa','Bademli','Mevlütler','Darıveren','Dedebağı','Eskiköy','Yeşilyuva','Güneyköy','Karahüyük','Karaismailler','Kurtlar','Kuzören','Köke','Ovayurt','Suçatı','Uçarı','Yazır','Yeniköy','Yumrutaş','Çakırköy','Örenköy','Kumafşarı'}
ZORLA = {'Yukarı': 'd', 'Eskiköy': 'r', 'Boğazdere': 'u', 'Pınaryazı': 'l', 'Mevlütler': 'r'}
def place(name, x, y):
    w = len(name) * FS * 0.53; h = FS
    o = 16 if name in GORUSME else 9; v = 7 if name in GORUSME else 0
    ox, oy = x + X0, y + Y0
    cands = {'r': (ox + 9, oy - h / 2, ox + 9 + w, oy + h / 2, 'start', x + o, y + FS * .35),
             'l': (ox - 9 - w, oy - h / 2, ox - 9, oy + h / 2, 'end', x - o, y + FS * .35),
             'u': (ox - w / 2, oy - 8 - h, ox + w / 2, oy - 8, 'middle', x, y - 11 - v),
             'd': (ox - w / 2, oy + 8, ox + w / 2, oy + 8 + h, 'middle', x, y + 8 + FS * .9 + v)}
    if name in ZORLA:
        c = cands[ZORLA[name]]; return c[4:]
    best = None
    for k, (x1, y1, x2, y2, anc, tx, ty) in cands.items():
        sc = txt[int(max(y1, 0)):int(y2), int(max(x1, 0)):int(x2)].sum() + (3 if k == 'r' else 0)
        if best is None or sc > best[0]: best = (sc, anc, tx, ty)
    return best[1:]

sinir = smooth(F['sinir'], close=True)
out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="Overpass, \'Segoe UI\', Helvetica, Arial, sans-serif">',
'''<defs>
<linearGradient id="zemin" x1="0" y1="0" x2="0.6" y2="1"><stop offset="0" stop-color="#efe4f7"/><stop offset="1" stop-color="#dcc8ec"/></linearGradient>
<clipPath id="ilce"><path d="''' + sinir + '''"/></clipPath>
<filter id="golge" x="-10%" y="-10%" width="120%" height="120%"><feDropShadow dx="0" dy="6" stdDeviation="8" flood-color="#3a1458" flood-opacity=".22"/></filter>
<style>
.ky{font-size:19px;font-weight:600;fill:#33263f;paint-order:stroke;stroke:#f3ebf8;stroke-width:4.5px;stroke-linejoin:round}
.ko{fill:#fff;stroke:#a3326f;stroke-width:2.6}
.kom{font-size:23px;font-weight:700;letter-spacing:.14em;fill:#8d80a0}
.drad{font-size:17px;font-style:italic;font-weight:600;fill:#3f78b8;paint-order:stroke;stroke:#ece1f5;stroke-width:4px;letter-spacing:.04em}
</style>
</defs>''']
out.append(f'<path d="{sinir}" fill="url(#zemin)" filter="url(#golge)"/>')
out.append('<g clip-path="url(#ilce)">')
out.append(f'<path d="{sinir}" fill="none" stroke="#fff" stroke-opacity=".55" stroke-width="14"/>')
# köy yolları
yol = "".join(f'<path d="{smooth(l)}"/>' for l in F['koyyolu'])
out.append(f'<g fill="none" stroke-linecap="round" stroke-linejoin="round"><g stroke="#b9a5cb" stroke-width="5.5">{yol}</g><g stroke="#fbf8fd" stroke-width="2.6">{yol}</g></g>')
# dereler
out.append('<g fill="none" stroke="#5b97d8" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round">' + "".join(f'<path d="{smooth(l)}"/>' for l in F['dere']) + '</g>')
# il yolu (sarı) ve ana yol (turuncu)
y2 = "".join(f'<path d="{smooth(l)}"/>' for l in F['yol2'])
out.append(f'<g fill="none" stroke-linecap="round" stroke-linejoin="round"><g stroke="#a8740f" stroke-width="7.5">{y2}</g><g stroke="#f5c74f" stroke-width="4.6">{y2}</g></g>')
ay = "".join(f'<path d="{smooth(l)}"/>' for l in F['anayol'])
out.append(f'<g fill="none" stroke-linecap="round" stroke-linejoin="round"><g stroke="#9c3409" stroke-width="10">{ay}</g><g stroke="#f47c2c" stroke-width="6.4">{ay}</g></g>')
out.append('</g>')
out.append(f'<path d="{sinir}" fill="none" stroke="#4f1f75" stroke-width="3.6" stroke-linejoin="round"/>')
# dere adları (orijinal haritadaki yerleri)
for t, x, y, r in [("Kırmızı D.", 622, 708, 50), ("Dalaman Ç.", 742, 985, -66), ("Çatak D.", 518, 1028, 63), ("Kırkpınar D.", 447, 1430, 62)]:
    out.append(f'<text class="drad" text-anchor="middle" transform="translate({x - X0},{y - Y0}) rotate({r})">{t}</text>')
# komşu ilçeler
for t, x, y in [("TAVAS", 341, 300), ("SERİNHİSAR", 684, 284), ("ÇAMELİ", 790, 1400), ("GÖLHİSAR", 1150, 1250), ("ALTINYAYLA", 1150, 1515)]:
    out.append(f'<text class="kom" text-anchor="middle" x="{x - X0}" y="{y - Y0}">{t}</text>')
# kuzey oku
out.append('<g transform="translate(80,90)" fill="#4f1f75"><path d="M0,-34 L13,12 L0,4 L-13,12 Z"/><path d="M0,-34 L0,4 L-13,12 Z" fill="#8a63ad"/><text y="38" text-anchor="middle" font-size="20" font-weight="800">K</text></g>')
# köyler
lab = []
for name, (x, y) in K.items():
    if name == "Acıpayam":
        out.append(f'<circle cx="{x}" cy="{y}" r="11" fill="#d7263d" stroke="#fff" stroke-width="3.5"/><circle cx="{x}" cy="{y}" r="15" fill="none" stroke="#7a1022" stroke-width="1.6"/>')
        lab.append(f'<text class="ky" x="{x - 26}" y="{y + 1}" text-anchor="end" style="font-size:27px;font-weight:800;letter-spacing:.04em;fill:#1f1428">ACIPAYAM</text>')
        continue
    out.append(f'<circle class="ko" cx="{x}" cy="{y}" r="5.5"/>')
    anc, tx, ty = place(name, x, y)
    lab.append(f'<text class="ky" x="{tx:.1f}" y="{ty:.1f}" text-anchor="{anc}">{name}</text>')
out += lab
out.append('</svg>')
s = "\n".join(out)
open('/home/user/acipayam-site/static/img/acipayam-harita.svg', 'w').write(s)
print(len(s) // 1024, 'KB')
