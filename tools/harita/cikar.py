# Eski haritadan vektör çizgiler çıkarır → ozellik.json (kırpılmış koordinatlar)
import json, numpy as np
from PIL import Image
from scipy import ndimage as nd
from skimage.morphology import skeletonize, remove_small_objects
from skimage.measure import find_contours, approximate_polygon
X0, Y0 = 137, 107
a = np.asarray(Image.open('/home/user/acipayam-site/static/img/acipayam-map.webp').convert('RGB')).astype(int)
R, G, B = a[..., 0], a[..., 1], a[..., 2]
lum = a.mean(2); mx = a.max(2); mn = a.min(2)
# ilçe maskesi
light = nd.binary_closing(lum > 150, iterations=6)
lab, n = nd.label(light); m = lab == (1 + int(np.argmax(nd.sum(light, lab, range(1, n + 1)))))
m = nd.binary_fill_holes(m)
inner = nd.binary_erosion(m, iterations=9)
f = nd.gaussian_filter(nd.binary_erosion(m, iterations=4).astype(float), 5)
c = max(find_contours(f, 0.5), key=len)
sinir = approximate_polygon(c, 0.6)[:, ::-1] - [X0, Y0]

def trace(mask, minlen):
    sk = skeletonize(mask)
    ys, xs = np.nonzero(sk); S = set(zip(ys.tolist(), xs.tolist()))
    nb = lambda p: [(p[0] + dy, p[1] + dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dy or dx) and (p[0] + dy, p[1] + dx) in S]
    deg = {p: len(nb(p)) for p in S}
    used = set(); paths = []
    def walk(start, nxt):
        path = [start, nxt]; used.add(frozenset((start, nxt)))
        while True:
            cur = path[-1]
            if deg[cur] != 2: break
            cand = [q for q in nb(cur) if frozenset((cur, q)) not in used and q != path[-2]]
            if not cand: break
            q = cand[0]; used.add(frozenset((cur, q))); path.append(q)
        return path
    for p in S:
        if deg[p] != 2:
            for q in nb(p):
                if frozenset((p, q)) not in used: paths.append(walk(p, q))
    for p in S:  # halkalar
        for q in nb(p):
            if frozenset((p, q)) not in used: paths.append(walk(p, q))
    out = []
    for pth in paths:
        if len(pth) < minlen: continue
        arr = np.array(pth, float)
        arr = approximate_polygon(arr, 0.9)[:, ::-1] - [X0, Y0]
        out.append(np.round(arr, 1).tolist())
    return out

orange = (R > 190) & (R - G > 60) & (B < 110) & (G < 190)
yellow = (R > 160) & (R - B > 70) & (R - G < 60) & (G > 120) & ~orange
river = (lum < 180) & (B - R > 14) & (B - G > 6)
minor = (lum > 120) & (mx - mn < 34)
def prep(mask, close=1, small=20):
    mask = mask & inner
    if close: mask = nd.binary_closing(mask, iterations=close)
    return remove_small_objects(mask, small)
feat = {
    'sinir': np.round(sinir, 1).tolist(),
    'anayol': trace(prep(nd.binary_dilation(orange, iterations=1), 2, 60), 25),
    'yol2': trace(prep(nd.binary_dilation(yellow, iterations=1), 5, 40), 20),
    'dere': trace(prep(river, 3, 60), 30),
    'koyyolu': trace(prep(minor, 3, 80), 28),
}
for k, v in feat.items(): print(k, len(v))
json.dump(feat, open('ozellik.json', 'w'))
