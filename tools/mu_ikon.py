"""mustafaunal.tr simgesi: diyafram + US. Küçük boylarda kalın çizgi ve iri harf."""
from PIL import Image, ImageDraw, ImageFont
import math, base64, io, sys
from pathlib import Path
MU = Path(__file__).resolve().parents[2] / "mustafaunal-site"
SERIF = "/usr/share/fonts/truetype/crosextra/"
G = (22, 35, 29); B = (217, 189, 133); B2 = (184, 149, 90)
def ikon(S, pad=0.0):
    k = 4; N = S * k; im = Image.new("RGB", (N, N), G); d = ImageDraw.Draw(im); C = N / 2; s = N / 512 * (1 - 2 * pad)
    for i in range(N):
        a = max(0, 1 - i / N) * 18; d.line((0, i, N, i), fill=tuple(int(c + a) for c in G))
    def ring(r, col, w): d.ellipse((C - r * s, C - r * s, C + r * s, C + r * s), outline=col, width=max(1, round(w * s)))
    ring(228, B, 20)                       # kalın dış halka
    for j in range(6):                     # 6 kalın kanat
        a = j * 2 * math.pi / 6; a2 = a + math.pi * 0.55
        d.line((C + 212 * s * math.cos(a), C + 212 * s * math.sin(a), C + 140 * s * math.cos(a2), C + 140 * s * math.sin(a2)), fill=B2, width=max(1, round(9 * s)))
    d.ellipse((C - 150 * s, C - 150 * s, C + 150 * s, C + 150 * s), fill=G); ring(150, B, 8)
    f = ImageFont.truetype(SERIF + "Caladea-Bold.ttf", round(168 * s)); bb = d.textbbox((0, 0), "US", font=f)
    d.text(((N - (bb[2] - bb[0])) / 2 - bb[0], (N - (bb[3] - bb[1])) / 2 - bb[1]), "US", font=f, fill=B)
    return im.resize((S, S), Image.LANCZOS)
if __name__ == "__main__":
    v = sys.argv[1]
    for n in (180, 192, 512): ikon(n).save(MU / f"static/img/uygulama{v}-{n}.png")
    ikon(512, 0.1).save(MU / f"static/img/uygulama{v}-512m.png")
    b = io.BytesIO(); ikon(128).save(b, "PNG")
    (MU / "static/img/favicon.svg").write_text(f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 128 128"><image width="128" height="128" xlink:href="data:image/png;base64,{base64.b64encode(b.getvalue()).decode()}"/></svg>')
