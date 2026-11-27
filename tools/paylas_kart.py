"""WhatsApp / Facebook / X önizleme kartları (1200×630 JPG).

Her kitap için iki kart üretir: acipayam.com renkleriyle ve mustafaunal.tr renkleriyle.
Ayrıca iki sitenin genel kartlarını üretir.
Çalıştırma: python3 tools/paylas_kart.py   (acipayam-site klasöründen)
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ACP = Path(__file__).resolve().parents[1]
MU = ACP.parent / "mustafaunal-site"
W, H = 1200, 630
INTER = "/usr/share/fonts/opentype/inter/"
SERIF = "/usr/share/fonts/truetype/crosextra/"

BOOKS = [
    ("bana-koyunu-anlat", "Bana Köyünü Anlat", "Sabit Kızılhan · Editör: Mustafa Ünal", "Acıpayam köylerinden sözlü tarih", False),
    ("kelekcide-yasamak", "Kelekçi’de Yaşamak", "Dr. Oktar Öner · Yayına hazırlayan: Mustafa Ünal", "Bir ömrün son durağı", False),
    ("icimde-kalan-cocuk", "İçimde Kalan Çocuk", "Mustafa Ünal", "US’lu Anlatılar · Kitap I", False),
    ("karanlik-odada-yedi-ay", "Karanlık Odada Yedi Ay", "Mustafa Ünal", "US’lu Anlatılar · Kitap II", False),
    ("uslu-dusler", "US’lu Düşler", "Mustafa Ünal", "US’lu Anlatılar · Kitap III · Bonus", False),
    ("adi-konmamis-islere-don-bicen-adam", "Adı Konmamış İşlere Don Biçen Adam", "Mustafa Ünal", "US’lu Anlatılar · Kitap IV", True),
    ("gonul-dostu", "Gönül Dostu", "Mustafa Ünal", "US’lu Anlatılar · Kitap V", True),
    ("uslu-dimag", "US’lu Dimağ", "Mustafa Ünal", "US’lu Anlatılar · Kitap VI · Final", True),
]
COLORS = {"bana-koyunu-anlat": "#5a3d2d", "gonul-dostu": "#184759", "icimde-kalan-cocuk": "#242925",
          "karanlik-odada-yedi-ay": "#111312", "kelekcide-yasamak": "#492235", "uslu-dimag": "#0f1a2e",
          "uslu-dusler": "#241c41", "adi-konmamis-islere-don-bicen-adam": "#3f3a1f"}


def F(path, size):
    return ImageFont.truetype(path, size)


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, t):
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def wrap(draw, text, font, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= width:
            cur = t
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def background(base, glow):
    img = Image.new("RGB", (W, H), base)
    g = Image.new("L", (W, H), 0)
    ImageDraw.Draw(g).ellipse((-300, -350, 700, 650), fill=255)
    g = g.filter(ImageFilter.GaussianBlur(160))
    img.paste(Image.new("RGB", (W, H), glow), (0, 0), g.point(lambda v: int(v * .55)))
    return img


def paste_cover(img, path, x, y, h):
    cov = Image.open(path).convert("RGB")
    cov = cov.resize((round(cov.width * h / cov.height), h), Image.LANCZOS)
    sh = Image.new("L", (cov.width + 120, cov.height + 120), 0)
    ImageDraw.Draw(sh).rectangle((60, 75, 60 + cov.width, 75 + cov.height), fill=190)
    sh = sh.filter(ImageFilter.GaussianBlur(26))
    img.paste((0, 0, 0), (x - 60, y - 60), sh)
    img.paste(cov, (x, y))
    return cov.width


def book_card(slug, title, author, kicker, soon, site):
    col = hexrgb(COLORS[slug])
    if site == "acp":
        base, glow, accent, brand = mix(col, (40, 12, 60), .35), mix(col, (190, 140, 230), .35), (207, 166, 240), "ACIPAYAM.com"
        tf = F(INTER + "InterDisplay-Bold.otf", 62)
        root, out = ACP, ACP / "static/img/paylas"
    else:
        base, glow, accent, brand = mix(col, (14, 22, 18), .45), mix(col, (217, 189, 133), .3), (217, 189, 133), "Mustafa Ünal"
        tf = F(SERIF + "Caladea-Bold.ttf", 66)
        root, out = MU, MU / "static/img/paylas"
    out.mkdir(parents=True, exist_ok=True)
    img = background(base, glow)
    d = ImageDraw.Draw(img)
    cw = paste_cover(img, root / f"static/img/kapak/{slug}.webp", 80, 55, 520)
    x = 80 + cw + 70
    tw = W - x - 70
    d.text((x, 92), brand.upper(), font=F(INTER + "Bold.otf" if False else INTER + "Inter-Bold.otf", 22), fill=accent)
    y = 140
    d.text((x, y), kicker, font=F(INTER + "Inter-Medium.otf", 26), fill=mix(accent, (255, 255, 255), .45))
    y += 56
    for line in wrap(d, title, tf, tw)[:3]:
        d.text((x, y), line, font=tf, fill=(255, 255, 255))
        y += 74
    y += 14
    af = F(INTER + "Inter-Medium.otf", 26)
    for line in wrap(d, author, af, tw)[:2]:
        d.text((x, y), line, font=af, fill=(225, 225, 225))
        y += 36
    pill = "Hazırlanıyor" if soon else "Ücretsiz oku · PDF · Sesli kitap"
    pf = F(INTER + "Inter-Bold.otf", 24)
    pw = d.textlength(pill, font=pf)
    d.rounded_rectangle((x, 500, x + pw + 44, 556), radius=16, fill=accent)
    d.text((x + 22, 512), pill, font=pf, fill=(24, 18, 28))
    img.save(out / f"{slug}.jpg", quality=86, optimize=True)


def acp_default():
    """Ana kart: üstte eski ikonik afiş, altta slogan şeridi (sitenin açılışıyla aynı)."""
    BG, GOLD = (42, 15, 63), (231, 196, 110)
    img = Image.new("RGB", (W, H), BG)
    ban = Image.open(ACP / "static/img/acipayam-cicekli-hatirasi-opt.webp").convert("RGB")
    ban = ban.resize((W, round(ban.height * W / ban.width)), Image.LANCZOS)
    bh = 430
    top = (ban.height - bh) // 2
    img.paste(ban.crop((0, top, W, top + bh)), (0, 0))
    d = ImageDraw.Draw(img)
    d.line((0, bh, W, bh), fill=GOLD, width=3)
    f1 = F(INTER + "Inter-ExtraBold.otf", 50)
    a, b = "Eskiyi Arşivliyoruz, ", "Yeniyi Eskitiyoruz."
    wa, wb = d.textlength(a, font=f1), d.textlength(b, font=f1)
    x = (W - wa - wb) / 2
    d.text((x, bh + 34), a, font=f1, fill=(255, 255, 255))
    d.text((x + wa, bh + 34), b, font=f1, fill=GOLD)
    d.line((W / 2 - 30, bh + 108, W / 2 + 30, bh + 108), fill=GOLD, width=3)
    f2 = F(INTER + "Inter-Medium.otf", 28)
    t = "ACIPAYAM.com · Kitaplar, köyler, fotoğraflar, radyo · Ücretsiz"
    d.text(((W - d.textlength(t, font=f2)) / 2, bh + 128), t, font=f2, fill=(225, 214, 235))
    out = ACP / "static/img/paylas"
    out.mkdir(parents=True, exist_ok=True)
    img.save(out / "acipayam-v3.jpg", quality=88, optimize=True)


def mu_default():
    img = background((22, 35, 29), (70, 80, 55))
    d = ImageDraw.Draw(img)
    por = Image.open(MU / "static/img/mustafa-unal-portre-renkli-seffaf-v1.webp").convert("RGBA")
    por = por.resize((round(por.width * 600 / por.height), 600), Image.LANCZOS)
    img.paste(por, (W - por.width - 30, H - por.height), por)
    d.text((70, 120), "YAZAR · FOTOĞRAFÇI · YEREL HAFIZA", font=F(INTER + "Inter-Bold.otf", 24), fill=(217, 189, 133))
    d.text((66, 170), "Mustafa", font=F(SERIF + "Caladea-Regular.ttf", 120), fill=(246, 236, 214))
    d.text((66, 290), "Ünal", font=F(SERIF + "Caladea-Regular.ttf", 120), fill=(246, 236, 214))
    d.text((70, 440), "Bir ömür, birçok iz.", font=F(SERIF + "Caladea-Italic.ttf", 46), fill=(217, 189, 133))
    out = MU / "static/img/paylas"
    out.mkdir(parents=True, exist_ok=True)
    img.save(out / "mustafaunal.jpg", quality=86, optimize=True)


if __name__ == "__main__":
    for b in BOOKS:
        for site in ("acp", "mu"):
            book_card(*b, site)
    acp_default()
    mu_default()
    print("kartlar hazır")
