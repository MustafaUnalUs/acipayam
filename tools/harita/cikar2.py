# HGM Denizli il haritasından (Acıpayam bölgesi kesiti) vektör özellikleri çıkarır.
import json, sys, numpy as np
from PIL import Image
from scipy import ndimage as nd
from skimage.morphology import skeletonize, remove_small_objects
from skimage.measure import find_contours, approximate_polygon
SRC = sys.argv[1] if len(sys.argv) > 1 else 'acp.png'
a = np.asarray(Image.open(SRC).convert('RGB')).astype(int)
R, G, B = a[..., 0], a[..., 1], a[..., 2]
lum = a.mean(2); ch = a.max(2) - a.min(2)
neutral = ch < 32
out = nd.binary_opening(neutral, iterations=4)
lab, n = nd.label(out)
edge = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
out = np.isin(lab, list(edge))
ins = ~out
lab, n = nd.label(ins); m = lab == (1 + int(np.argmax(nd.sum(ins, lab, range(1, n + 1)))))
m = nd.binary_fill_holes(m)
m = nd.binary_opening(m, iterations=3)
m = nd.binary_dilation(m, iterations=3)   # yeşilin dış kenarı = sınır çizgisinin ortası
inner = nd.binary_erosion(m, iterations=8)
f = nd.gaussian_filter(m.astype(float), 2.5)
sinir = approximate_polygon(max(find_contours(f, .5), key=len), .7)[:, ::-1]

def trace(mask, minlen):
    sk = skeletonize(mask)
    ys, xs = np.nonzero(sk); S = set(zip(ys.tolist(), xs.tolist()))
    nb = lambda p: [(p[0] + dy, p[1] + dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dy or dx) and (p[0] + dy, p[1] + dx) in S]
    deg = {p: len(nb(p)) for p in S}; used = set(); paths = []
    def walk(s0, s1):
        path = [s0, s1]; used.add(frozenset((s0, s1)))
        while deg[path[-1]] == 2:
            cur = path[-1]
            c = [q for q in nb(cur) if frozenset((cur, q)) not in used and q != path[-2]]
            if not c: break
            used.add(frozenset((cur, c[0]))); path.append(c[0])
        return path
    for p in S:
        if deg[p] != 2:
            for q in nb(p):
                if frozenset((p, q)) not in used: paths.append(walk(p, q))
    for p in S:
        for q in nb(p):
            if frozenset((p, q)) not in used: paths.append(walk(p, q))
    return [approximate_polygon(np.array(p, float), 1.0)[:, ::-1].round(1).tolist() for p in paths if len(p) >= minlen]

red = (R > 170) & (G < 70) & (B < 80)
oryel = (R > 195) & (G > 110) & (G < 200) & (B < 90)
nearred = nd.binary_dilation(red, iterations=4)
orange = (oryel | red) & nearred                          # ana yol: turuncu dolgu + kırmızı kenar
yellow = oryel & ~nd.binary_dilation(red, iterations=7)   # il yolu: kenarsız turuncu-sarı
river = (B > R + 35) & (B > G + 10) & (lum < 200)
white = (lum > 232) & (ch < 30)
mag = (R > 150) & (G < 110) & (B > 90) & (R - G > 80)
def prep(x, close, small):
    x = x & inner
    if close: x = nd.binary_closing(x, iterations=close)
    return remove_small_objects(x, max_size=small)
feat = {'sinir': sinir.round(1).tolist(),
        'anayol': trace(prep(orange, 3, 200), 40),
        'yol2': trace(prep(yellow, 4, 120), 30),
        'dere': trace(prep(river, 2, 120), 40),
        'koyyolu': trace(prep(white, 2, 150), 40)}
labm, nm = nd.label(nd.binary_closing(mag & m, iterations=2))
cs = nd.center_of_mass(mag, labm, range(1, nm + 1)); sz = nd.sum(mag & m, labm, range(1, nm + 1))
feat['noktalar'] = [[round(c[1], 1), round(c[0], 1)] for c, s in zip(cs, sz) if 25 <= s <= 400]
for k, v in feat.items(): print(k, len(v))
json.dump(feat, open('ozellik2.json', 'w'))
np.save('yazi_maske.npy', (lum < 100) & (ch < 40))
