"""Kitaplardan alıntı kartları (1080×1080, WhatsApp/Instagram için kare) + data/alintilar.json"""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
MU = Path(__file__).resolve().parents[2] / "mustafaunal-site"
SERIF = "/usr/share/fonts/truetype/crosextra/"
INTER = "/usr/share/fonts/opentype/inter/"
COLORS = json.loads((MU / "data/kapak-renkleri.json").read_text()) if (MU / "data/kapak-renkleri.json").exists() else {}
Q = [
 ("icimde-kalan-cocuk", "İçimde Kalan Çocuk", "Çocukluk, insanın ömrü boyunca taşıdığı en saf pusuladır.", 2),
 ("icimde-kalan-cocuk", "İçimde Kalan Çocuk", "Us, insanın büyüdükçe kaybetmemesi gereken meraktır.", 3),
 ("icimde-kalan-cocuk", "İçimde Kalan Çocuk", "Hafızanın derinliklerindeki hiçbir şey bütünüyle silinmez; yalnızca üzeri zamanın tozlu yapraklarıyla örtülür.", 2),
 ("karanlik-odada-yedi-ay", "Karanlık Odada Yedi Ay", "Bilgisayar, söylediğim şeyi eksiksiz yapıyor; yanlış söylediğimde ise aynı kesinlikle yanlış yapıyordu.", 2),
 ("karanlik-odada-yedi-ay", "Karanlık Odada Yedi Ay", "Eski program açıldığında ilk anda sanki bilgisayar beni hatırlamış gibi hissettim.", 31),
 ("uslu-dusler", "US’lu Düşler", "Bir isim vermek makineyi insan yapmıyordu.", 15),
 ("uslu-dusler", "US’lu Düşler", "İnsan bazen dün değiştirdiği bir şifreyi hatırlayamazken yıllar önce duyduğu bir sesi neden unutmuyordu?", 14),
 ("kelekcide-yasamak", "Kelekçi’de Yaşamak", "Her şey akar: su, tarih, yıldız, insan ve fikir.", 18),
]
GOLD = (217, 189, 133)
def hexrgb(h): h = h.lstrip("#"); return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
def wrap(d, t, f, w):
    out, cur = [], ""
    for word in t.split():
        x = (cur + " " + word).strip()
        if d.textlength(x, font=f) <= w: cur = x
        else: out.append(cur); cur = word
    return out + [cur]
items = []
for n, (slug, title, text, ch) in enumerate(Q, 1):
    S = 1080
    bg = hexrgb(COLORS.get(slug, "#16231d"))
    img = Image.new("RGB", (S, S), bg)
    d = ImageDraw.Draw(img)
    for i in range(S):  # hafif ışık
        a = max(0, 1 - i / S) * 22
        d.line((0, i, S, i), fill=tuple(min(255, int(c + a)) for c in bg))
    d.rectangle((40, 40, S - 40, S - 40), outline=GOLD, width=2)
    d.text((90, 90), "“", font=ImageFont.truetype(SERIF + "Caladea-Bold.ttf", 220), fill=GOLD)
    size = 64 if len(text) < 70 else 54 if len(text) < 110 else 48
    f = ImageFont.truetype(SERIF + "Caladea-Regular.ttf", size)
    lines = wrap(d, text, f, S - 220)
    lh = size * 1.32
    y = (S - lh * len(lines)) / 2 - 20
    for l in lines:
        d.text((110, y), l, font=f, fill=(246, 236, 214)); y += lh
    d.line((110, y + 30, 190, y + 30), fill=GOLD, width=3)
    d.text((110, y + 55), title, font=ImageFont.truetype(SERIF + "Caladea-Italic.ttf", 40), fill=GOLD)
    d.text((110, S - 130), "DR. OKTAR ÖNER" if slug == "kelekcide-yasamak" else "MUSTAFA ÜNAL", font=ImageFont.truetype(INTER + "Inter-Bold.otf", 28), fill=(246, 236, 214))
    d.text((S - 110 - d.textlength("mustafaunal.tr", font=ImageFont.truetype(INTER + "Inter-Medium.otf", 28)), S - 130), "mustafaunal.tr",
           font=ImageFont.truetype(INTER + "Inter-Medium.otf", 28), fill=GOLD)
    name = f"{n:02d}.jpg"
    img.save(MU / "static/img/alinti" / name, quality=86, optimize=True)
    import re
    book = json.loads((MU / "data/kitap/kitaplar" / f"{slug}.json").read_text())
    key = re.sub(r"\W", "", text[:40]).lower()[2:]
    ch = next(i for i, c in enumerate(book["chapters"]) if any(key in re.sub(r"\W", "", re.sub("<[^>]+>", "", str(b.get("h", "")))).lower() for b in c["blocks"]))
    items.append({"no": n, "slug": slug, "title": title, "text": text, "img": f"/img/alinti/{name}", "url": f"/kitaplar/{slug}/bolum/{ch + 1:02d}/",
                  "author": "Dr. Oktar Öner" if slug == "kelekcide-yasamak" else "Mustafa Ünal"})
(MU / "data/alintilar.json").write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(items), "kart")
