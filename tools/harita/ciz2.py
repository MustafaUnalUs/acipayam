# ozellik2.json + eslesen.json → static/img/acipayam-harita.svg ve data/harita-koyler.json
import json, numpy as np
VX0, VY0, VW, VH = 60, 40, 2290, 2700
k = 1.77
F = json.load(open('ozellik2.json')); E = json.load(open('eslesen.json'))
txt = np.load('yazi_maske.npy')
E['Acıpayam'] = [1356.5, 981.0]
L = lambda p: float(np.sum(np.hypot(*np.diff(np.array(p), axis=0).T))) if len(p) > 1 else 0
def chaikin(p, n=2):
    p = np.array(p, float)
    for _ in range(n):
        q = np.empty((len(p) * 2 - 2, 2)); q[0::2] = .75 * p[:-1] + .25 * p[1:]; q[1::2] = .25 * p[:-1] + .75 * p[1:]
        q[0] = p[0]; q[-1] = p[-1]; p = q
    return p
def P(pts, close=False):
    s = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    return "M" + s.replace(" ", " L", 0).replace(" ", " L") + (" Z" if close else "")
def smooth(pts, close=False):
    if close:
        p = np.array(pts, float); p = np.vstack([p, p[:1]]); p = chaikin(p, 2)
    else:
        p = chaikin(pts, 2)
    from skimage.measure import approximate_polygon
    p = approximate_polygon(p, .6)
    return P(p, close)
for key, mn in (('koyyolu', 90), ('dere', 90), ('yol2', 40), ('anayol', 0)):
    F[key] = [l for l in F[key] if L(l) >= mn]
sinir = smooth(F['sinir'], True)
GORUSME = {'Akalan','Alaattin','Apa','Bademli','Mevlütler','Darıveren','Dedebağı','Eskiköy','Yeşilyuva','Güneyköy','Karahüyük','Karaismailler','Kurtlar','Kuzören','Köke','Ovayurt','Suçatı','Uçarı','Yazır','Yeniköy','Yumrutaş','Çakırköy','Örenköy','Kumafşarı'}
FS = 33
def place(name, x, y):
    w = len(name) * FS * .55; h = FS
    o = 28 if name in GORUSME else 16; v = 12 if name in GORUSME else 0
    c = {'r': (x + 12, y - h / 2, x + 12 + w, y + h / 2, 'start', x + o, y + FS * .35),
         'l': (x - 12 - w, y - h / 2, x - 12, y + h / 2, 'end', x - o, y + FS * .35),
         'u': (x - w / 2, y - 14 - h, x + w / 2, y - 14, 'middle', x, y - 18 - v),
         'd': (x - w / 2, y + 14, x + w / 2, y + 14 + h, 'middle', x, y + 14 + FS * .9 + v)}
    best = None
    for key, (x1, y1, x2, y2, anc, tx, ty) in c.items():
        sc = txt[int(max(y1, 0)):int(y2), int(max(x1, 0)):int(x2)].sum() + (5 if key == 'r' else 0)
        if best is None or sc > best[0]: best = (sc, anc, tx, ty)
    return best[1:]
g = lambda ls: "".join(f'<path d="{smooth(l)}"/>' for l in ls)
o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{VX0} {VY0} {VW} {VH}" width="{VW // 2}" height="{VH // 2}" font-family="Overpass, \'Segoe UI\', Helvetica, Arial, sans-serif">',
f'''<defs>
<linearGradient id="zemin" x1="0" y1="0" x2="0.55" y2="1"><stop offset="0" stop-color="#f1e7f8"/><stop offset="1" stop-color="#dcc7ec"/></linearGradient>
<clipPath id="ilce"><path d="{sinir}"/></clipPath>
<filter id="golge" x="-10%" y="-10%" width="120%" height="120%"><feDropShadow dx="0" dy="10" stdDeviation="14" flood-color="#3a1458" flood-opacity=".22"/></filter>
<style>
.ky{{font-size:{FS}px;font-weight:600;fill:#33263f;paint-order:stroke;stroke:#f4ecf9;stroke-width:8px;stroke-linejoin:round}}
.ko{{fill:#fff;stroke:#a3326f;stroke-width:4.5}}
.kom{{font-size:36px;font-weight:800;letter-spacing:.1em;fill:#8a7d9b}}
.il{{font-size:72px;font-weight:800;letter-spacing:.34em;fill:#b3a6c2}}
.ilm{{fill:#8a7d9b}}
.drad{{font-size:29px;font-style:italic;font-weight:600;fill:#3f78b8;paint-order:stroke;stroke:#ede2f6;stroke-width:7px;letter-spacing:.04em}}
</style></defs>''',
f'<path d="{sinir}" fill="url(#zemin)" filter="url(#golge)"/>',
'<g clip-path="url(#ilce)">',
f'<path d="{sinir}" fill="none" stroke="#fff" stroke-opacity=".55" stroke-width="24"/>',
f'<g fill="none" stroke-linecap="round" stroke-linejoin="round"><g stroke="#bba7cd" stroke-width="9.5">{g(F["koyyolu"])}</g><g stroke="#fcf9fd" stroke-width="4.6">{g(F["koyyolu"])}</g></g>',
f'<g fill="none" stroke="#5b97d8" stroke-width="4.4" stroke-linecap="round" stroke-linejoin="round">{g(F["dere"])}</g>',
f'<g fill="none" stroke-linecap="round" stroke-linejoin="round"><g stroke="#a8740f" stroke-width="13">{g(F["yol2"])}</g><g stroke="#f5c74f" stroke-width="8">{g(F["yol2"])}</g></g>',
f'<g fill="none" stroke-linecap="round" stroke-linejoin="round"><g stroke="#9c3409" stroke-width="17">{g(F["anayol"])}</g><g stroke="#f47c2c" stroke-width="11">{g(F["anayol"])}</g></g>',
'</g>',
f'<path d="{sinir}" fill="none" stroke="#4f1f75" stroke-width="6.5" stroke-linejoin="round"/>']
for t, x, y, r in [("Kırmızı D.", 1030, 1165, 50), ("Dalaman Ç.", 1178, 1665, -66), ("Çatak D.", 805, 1712, 62), ("Kırkpınar D.", 735, 2430, 52), ("Bulanık D.", 1772, 1735, -72)]:
    o.append(f'<text class="drad" text-anchor="middle" transform="translate({x},{y}) rotate({r})">{t}</text>')
# komşu iller (büyük, soluk) ve komşu ilçeler (gerçek merkez noktası ya da yön oku ile)
for t, x, y in [("DENİZLİ", 560, 1180), ("BURDUR", 2120, 1720), ("MUĞLA", 330, 2705)]:
    o.append(f'<text class="il" x="{x}" y="{y}" text-anchor="middle">{t}</text>')
for t, x, y, a in [("TAVAS", 486.5, 444.3, 'ur'), ("SERİNHİSAR", 1085, 416, 'd'), ("ÇAMELİ", 1325.6, 2353.6, 'ul'), ("GÖLHİSAR", 1833, 2087, 'r'), ("ÇAVDIR", 2329, 2019, 'l')]:
    o.append(f'<circle class="ilm" cx="{x}" cy="{y}" r="12"/><circle cx="{x}" cy="{y}" r="5" fill="#fff"/>')
    tx, ty, anc = {'r': (x + 24, y + 14, 'start'), 'l': (x - 24, y + 14, 'end'), 'd': (x, y + 56, 'middle'), 'ur': (x + 14, y - 22, 'start'), 'ul': (x - 14, y - 22, 'end')}[a]
    o.append(f'<text class="kom" x="{tx}" y="{ty}" text-anchor="{anc}">{t}</text>')
for t, x, y, r in [("YEŞİLOVA", 2330, 1000, 0), ("BEYAĞAÇ", 110, 1900, 180), ("KÖYCEĞİZ", 110, 2590, 180), ("ÇARDAK", 2330, 170, 0), ("HONAZ", 1250, 95, -90), ("DALAMAN", 700, 2640, 90)]:
    ok = f'<path d="M0,-11 L18,0 L0,11 Z" class="ilm" transform="translate({x},{y}) rotate({r})"/>'
    if r == -90:   # yukarı ok: yazı okun altında ortalı
        o.append(ok + f'<text class="kom" x="{x}" y="{y + 52}" text-anchor="middle">{t}</text>'); continue
    if r == 90:    # aşağı ok: yazı okun sağında
        o.append(ok + f'<text class="kom" x="{x + 24}" y="{y + 13}">{t}</text>'); continue
    tx, anc = (x - 14, 'end') if r == 0 else (x + 14, 'start')
    o.append(ok + f'<text class="kom" x="{tx}" y="{y + 13}" text-anchor="{anc}">{t}</text>')
o.append(f'<g transform="translate({VX0 + 90},{VY0 + 110})" fill="#4f1f75"><path d="M0,-60 L23,21 L0,7 L-23,21 Z"/><path d="M0,-60 L0,7 L-23,21 Z" fill="#8a63ad"/><text y="66" text-anchor="middle" font-size="34" font-weight="800">K</text></g>')
lab = []; koy = {}
ZORLA = {'Yukarı': 'd', 'Eskiköy': 'r', 'Boğazdere': 'u', 'Suçatı': 'r'}
for name, (x, y) in E.items():
    koy[name] = [round(x - VX0, 1), round(y - VY0, 1)]
    if name == 'Acıpayam':
        o.append(f'<circle cx="{x}" cy="{y}" r="19" fill="#d7263d" stroke="#fff" stroke-width="6"/><circle cx="{x}" cy="{y}" r="26" fill="none" stroke="#7a1022" stroke-width="2.6"/>')
        lab.append(f'<text class="ky" x="{x - 42}" y="{y + 2}" text-anchor="end" style="font-size:46px;font-weight:800;letter-spacing:.04em;fill:#1f1428;stroke-width:10px">ACIPAYAM</text>')
        continue
    o.append(f'<circle class="ko" cx="{x}" cy="{y}" r="9.5"/>')
    if name in ZORLA:
        oo = 28 if name in GORUSME else 16; vv = 12 if name in GORUSME else 0
        anc, tx, ty = {'d': ('middle', x, y + 14 + FS * .9 + vv), 'r': ('start', x + oo, y + FS * .35), 'u': ('middle', x, y - 18 - vv)}[ZORLA[name]]
    else:
        anc, tx, ty = place(name, x, y)
    lab.append(f'<text class="ky" x="{tx:.1f}" y="{ty:.1f}" text-anchor="{anc}">{name}</text>')
o += lab + ['</svg>']
s = "\n".join(o)
open('/home/user/acipayam-site/static/img/acipayam-harita.svg', 'w').write(s)
json.dump(koy, open('/home/user/acipayam-site/data/harita-koyler.json', 'w'), ensure_ascii=False, indent=0)
print(len(s) // 1024, 'KB', len(koy), 'köy')
