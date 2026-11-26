import json, numpy as np
from skimage.measure import approximate_polygon
f = json.load(open('ozellik.json'))
L = lambda p: float(np.sum(np.hypot(*np.diff(np.array(p), axis=0).T))) if len(p) > 1 else 0
def grid(p):
    a = np.array(p); w, h = np.ptp(a[:, 0]), np.ptp(a[:, 1])
    return (w < 5 and h > 60) or (h < 5 and w > 60)
def join(lines, gap):
    lines = [list(map(tuple, l)) for l in lines if not grid(l)]
    while True:
        best = None
        for i in range(len(lines)):
            for j in range(i + 1, len(lines)):
                for ei in (0, -1):
                    for ej in (0, -1):
                        d = np.hypot(*np.subtract(lines[i][ei], lines[j][ej]))
                        if d < gap and (best is None or d < best[0]): best = (d, i, j, ei, ej)
        if not best: return lines
        _, i, j, ei, ej = best
        a = lines[i] if ei == -1 else lines[i][::-1]
        b = lines[j] if ej == 0 else lines[j][::-1]
        lines[i] = a + b; del lines[j]
def chaikin(p, n=3):
    p = np.array(p, float)
    for _ in range(n):
        q = np.empty((len(p) * 2 - 2, 2))
        q[0::2] = .75 * p[:-1] + .25 * p[1:]; q[1::2] = .25 * p[:-1] + .75 * p[1:]
        q[0] = p[0]; q[-1] = p[-1]; p = q
    return p
out = {}
for k, gap, minlen in [('anayol', 30, 0), ('yol2', 40, 30), ('dere', 22, 70), ('koyyolu', 20, 60)]:
    ls = join(f[k], gap)
    ls = [l for l in ls if L(l) >= minlen]
    out[k] = [np.round(approximate_polygon(chaikin(l), .5), 1).tolist() for l in ls]
    print(k, len(out[k]))
s = np.array(f['sinir']); out['sinir'] = np.round(approximate_polygon(chaikin(np.vstack([s, s[:1]]), 2), .4), 1).tolist()
json.dump(out, open('temiz.json', 'w'))
