#!/usr/bin/env python3
"""ACIPAYAM.com test sitesi üreticisi.

data/ ve static/ klasörlerinden docs/ altına statik site üretir.
    python3 build.py
"""
import html
import json
import math
import re
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
OUT = ROOT / "docs"
ORIGIN = "https://acipayam.com"
# SITE_MODE=canli: acipayam.com için (arama motorlarına açık, test notu yok, Mini Sohbet canlı).
CANLI = os.environ.get("SITE_MODE", "test") == "canli"
# Büyük ses dosyaları eski Worker’dan gelir. MEDIA_BASE ile adresi değiştirilebilir.
MEDIA_BASE = os.environ.get("MEDIA_BASE", "https://acipayam.com/")
MEDIA_RE = re.compile(r"https://acipayam\.com/([^\"\s<>]*?(?:\.mp3|/bolumler/))")
ASSET_V = "17"


def J(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


E = lambda s: html.escape(str(s or ""), quote=True)  # noqa: E731


def plain(s):
    return re.sub(r"<[^>]+>", "", html.unescape(s or ""))


def slugify(s):
    tr = str.maketrans("çğıöşüâîûÇĞİÖŞÜÂÎÛ", "cgiosuaiuCGIOSUAIU")
    return re.sub(r"[^a-z0-9]+", "-", plain(s).translate(tr).lower()).strip("-")[:60]


def minutes(words):
    return max(1, math.ceil(words / 200))


def tr_title(s):
    """TAMAMI BÜYÜK başlıkları okunur hâle getirir (Türkçe i/ı kuralıyla)."""
    s = plain(s)
    if s.upper() != s:
        return s
    small = {"VE", "İLE", "DE", "DA", "Mİ", "MI", "MU", "MÜ", "Kİ", "YA"}
    keep = {"GAMEKS", "US", "PTT", "TRT", "ADB", "AI", "ADEBİR", "ACİBİR"}
    words = []
    for i, w in enumerate(s.split(" ")):
        low = w.replace("I", "ı").replace("İ", "i").lower()
        if i and w in small:
            words.append(low)
        elif re.sub(r"[’'].*$", "", w) in keep:
            words.append(w)
        else:
            words.append(low[:1].replace("i", "İ").upper() + low[1:] if low else low)
    return " ".join(words)


# ------------------------------------------------------------------ veriler
HOME = J("home.json")
PAGES = J("book-pages.json")
USLU = J("uslu-dusler.json")
SABIT = J("sabit.json")
COLORS = J("kapak-renkleri.json")

BOOKS = [
    {"slug": "uslu-dusler", "base": "/uslu-dusler/", "title": "US’lu Düşler", "subtitle": "Olmuş Zekâ",
     "author": "Mustafa Ünal", "series": "US’lu Anlatılar · Üçüncü kitap",
     "summary": HOME["books"][0]["summary"], "intro": USLU["intro"],
     "audio": USLU["audio_full"], "audio_len": USLU["listen"]["duration"], "overview": USLU["overview"]},
    {"slug": "bana-koyunu-anlat", "base": "/sabit/", "title": "Bana Köyünü Anlat", "author": "Sabit Kızılhan",
     "editor": "Mustafa Ünal", "series": "Sözlü tarih",
     "summary": HOME["books"][1]["summary"], "intro": SABIT["lead"], "audio": SABIT["audio_full"]},
    {"slug": "karanlik-odada-yedi-ay", "base": "/karanlik-odada-yedi-ay/", "title": "Karanlık Odada Yedi Ay",
     "author": "Mustafa Ünal", "series": "US’lu Anlatılar · İkinci kitap",
     "summary": HOME["books"][2]["summary"], "intro": PAGES["karanlik-odada-yedi-ay"]["intro"],
     "audio": PAGES["karanlik-odada-yedi-ay"]["audio_full"]},
    {"slug": "icimde-kalan-cocuk", "base": "/icimde-kalan-cocuk/", "title": "İçimde Kalan Çocuk",
     "author": "Mustafa Ünal", "series": "US’lu Anlatılar · Birinci kitap",
     "summary": HOME["books"][3]["summary"], "intro": PAGES["icimde-kalan-cocuk"]["intro"],
     "audio": PAGES["icimde-kalan-cocuk"]["audio_full"], "tracks": PAGES["icimde-kalan-cocuk"].get("tracks"),
     "tracks_base": PAGES["icimde-kalan-cocuk"]["chapters_audio_base"]},
    {"slug": "kelekcide-yasamak", "base": "/kelekcide-yasamak/", "title": "Kelekçi’de Yaşamak",
     "author": "Dr. Oktar Öner", "editor": "Mustafa Ünal", "series": "Bir ömrün son durağı · 1938–2010",
     "summary": HOME["books"][4]["summary"], "intro": PAGES["kelekcide-yasamak"]["intro"],
     "audio": PAGES["kelekcide-yasamak"]["audio_full"], "quote": PAGES["kelekcide-yasamak"]["quote"],
     "extra": [s for s in PAGES["kelekcide-yasamak"]["sections"] if s["title"] in ("Baskı Hakkında",)]},
]
for b in BOOKS:
    b["data"] = J(f"kitaplar/{b['slug']}.json")
    b["cover"] = f"/img/kapak/{b['slug']}.webp"
    b["back"] = f"/img/kapak/{b['slug']}-arka.webp"
    b["color"] = COLORS[b["slug"]]
    b["pdf"] = f"/indir/{b['slug']}.pdf"
    b["pdf_size"] = (ROOT / "static" / "indir" / f"{b['slug']}.pdf").stat().st_size
    b["words"] = sum(c["words"] for c in b["data"]["chapters"])

_soon = next(u for u in HOME["upcoming"] if u["title"].startswith("Adı Konmamış"))
_gonul = next(u for u in HOME["upcoming"] if u["title"].startswith("Gönül"))
SOON = {
    "slug": "adi-konmamis-islere-don-bicen-adam", "base": "/adi-konmamis-islere-don-bicen-adam/",
    "title": "Adı Konmamış İşlere Don Biçen Adam", "author": "Mustafa Ünal",
    "series": "US’lu Anlatılar · Dördüncü kitap · Henüz yayında değil", "status": _soon["status"],
    "summary": _soon["tagline"], "intro": " ".join(_soon["paragraphs"]),
    "cover": "/img/kapak/adi-konmamis-islere-don-bicen-adam.webp",
    "back": "/img/kapak/adi-konmamis-islere-don-bicen-adam-arka.webp",
    "color": COLORS["adi-konmamis-islere-don-bicen-adam"], "soon": True,
    "kicker": "US’lu Anlatılar · Dördüncü kitap · GAMEKS 1999–2026",
}
SOONS = [SOON]
for _b in [
    {"slug": "uslu-dimag", "title": "US’lu Dimağ", "author": "Mustafa Ünal",
     "series": "US’lu Anlatılar · Beşinci kitap · Henüz yayında değil", "kicker": "US’lu Anlatılar · Beşinci kitap · Final",
     "summary": "Doksan öğretide ölçüsü oturmuş bir zihin.", "status": "2027’de yayımlanması planlanıyor",
     "intro": "Bu kitap öğretmek ya da ikna etmek için yazılmadı. Bir insanın hayatın içinde düşe kalka, zamanla oluşmuş us izlerinin kaydı; davranıştan zamana, güvenden vedaya doksan kısa öğreti."},
    {"slug": "gonul-dostu", "title": "Gönül Dostu", "author": "Mustafa Ünal",
     "series": "Bağımsız eser · Henüz yayında değil", "kicker": "Bağımsız eser · Sabit Kızılhan ile Yol Yürümek",
     "summary": "2005–2026 arasındaki yol arkadaşlığından; dostluğun, memleketin ve hak mücadelesinin canlı tanıklığı.",
     "status": "2027’de yayımlanması planlanıyor", "intro": _gonul["paragraphs"][0]},
]:
    _b.update({"base": f"/{_b['slug']}/", "cover": f"/img/kapak/{_b['slug']}.webp",
               "back": f"/img/kapak/{_b['slug']}-arka.webp", "color": COLORS[_b["slug"]], "soon": True})
    SOONS.append(_b)

SERI = {"icimde-kalan-cocuk": (1, "Kitap I"), "karanlik-odada-yedi-ay": (2, "Kitap II"),
        "uslu-dusler": (3, "Kitap III · Bonus"), "adi-konmamis-islere-don-bicen-adam": (4, "Kitap IV · Hazırlanıyor"),
        "uslu-dimag": (5, "Kitap V · Final · Hazırlanıyor")}
for b in BOOKS + SOONS:
    if b["slug"] in SERI:
        b["seri"], b["seri_ad"] = SERI[b["slug"]]
SERI_BOOKS = sorted((b for b in BOOKS + SOONS if b.get("seri")), key=lambda b: b["seri"])
OTHER_BOOKS = [b for b in BOOKS + SOONS if not b.get("seri")]

INTERVIEWS = {int(i["no"]): i for i in SABIT["interviews"]}
bana = next(b for b in BOOKS if b["slug"] == "bana-koyunu-anlat")
for c in bana["data"]["chapters"]:
    m = re.match(r"(\d+)\.\s", c["title"])
    if m and int(m.group(1)) in INTERVIEWS:
        c["interview"] = INTERVIEWS[int(m.group(1))]


def chapter_url(book, i, c):
    if c.get("interview"):
        return f"{book['base']}{c['interview']['slug']}/"
    return f"{book['base']}bolum/{i + 1:02d}/"


def first_url(book):
    return chapter_url(book, 0, book["data"]["chapters"][0])


def mb(n):
    return f"{n / 1_048_576:.0f} MB" if n > 1_048_576 else f"{n / 1024:.0f} KB"


# ------------------------------------------------------------------ iskelet
NAV = [
    ("/#kitaplar", "Kitaplar"),
    ("/sabit/", "Köyler"),
    ("/acipayam-dunu-bugunu/", "Acıpayam Tarihi"),
    ("/sehit-bilgi-kapisi/", "Şehitler"),
    ("/radyo-arsivi/", "Radyo"),
    ("/fotograflar/", "Fotoğraflar"),
    ("/#hikaye", "Hikâyemiz"),
]

MARK = ('<svg class="mark-sign" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2 21 12 12 22 3 12Z" fill="none" '
        'stroke="currentColor" stroke-width="1.2"/><path d="M12 8 16 12 12 16 8 12Z" fill="currentColor"/></svg>')


NOINDEX = '<meta name="robots" content="noindex">\n'
TEST_NOTE = ('<p class="foot-note">Bu adres, acipayam.com içeriğiyle hazırlanmış yeni tasarımın test sürümüdür. '
             f'Asıl site: <a href="{ORIGIN}/">acipayam.com</a></p>')


def layout(path, title, body, desc="", cls="", style=""):
    full = title if "ACIPAYAM" in title else f"{title} · ACIPAYAM.com"
    nav = "".join(
        f'<a href="{h}"{" aria-current=\"page\"" if path.startswith(h) and not h.startswith("/#") else ""}>{t}</a>'
        for h, t in NAV)
    return f"""<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(full)}</title>
<meta name="description" content="{E(desc or 'Acıpayam’ın kitapları, sözlü tarihi ve ortak hafızası. 2004’ten beri memleket kokusu.')}">
{"" if CANLI else NOINDEX}<link rel="canonical" href="{ORIGIN}{path}">
<meta property="og:title" content="{E(full)}">
<meta property="og:locale" content="tr_TR">
<meta name="theme-color" content="#4f1f75">
<link rel="icon" href="/img/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Overpass:wght@400..800&family=Newsreader:ital,opsz,wght@0,6..72,400..600;1,6..72,400..500&display=swap">
<link rel="stylesheet" href="/assets/site.css?v={ASSET_V}">
</head>
<body class="{cls}"{f' style="{style}"' if style else ''}>
<a class="skip" href="#icerik">İçeriğe geç</a>
<header class="bar">
  <div class="bar-in">
    <a class="mark" href="/">{MARK}<span>ACIPAYAM<em>.com</em></span></a>
    <details class="menu">
      <summary><span>Menü</span></summary>
      <nav aria-label="Ana menü">{nav}</nav>
    </details>
  </div>
</header>
<main id="icerik">
{body}
{share_bar(path, full)}
</main>
{footer()}
<script src="/assets/site.js?v={ASSET_V}" defer></script>
</body>
</html>
"""


SHARE_IC = {
    "wa": '<path d="M12 3a9 9 0 0 0-7.8 13.5L3 21l4.6-1.2A9 9 0 1 0 12 3z"/><path d="M9 8.5c0 3.5 3 6.5 6.5 6.5l1-1.6-2-1-1 1c-1.2-.5-2.4-1.7-2.9-2.9l1-1-1-2z"/>',
    "fb": '<path d="M14 8h3V4h-3a4 4 0 0 0-4 4v3H7v4h3v6h4v-6h3l1-4h-4V8z"/>',
    "x": '<path d="M4 4l16 16M20 4 4 20"/>',
}


def share_mini():
    def a(cls, href, label):
        return (f'<a class="sh sh-{cls}" data-share="{cls}" href="{href}" target="_blank" rel="noopener" aria-label="{label} ile paylaş">'
                f'<svg viewBox="0 0 24 24" aria-hidden="true">{SHARE_IC[cls]}</svg><span>{label}</span></a>')
    return ('<div class="share-mini"><span>Paylaş:</span>'
            + a("wa", "https://wa.me/", "WhatsApp") + a("fb", "https://www.facebook.com/", "Facebook")
            + a("x", "https://x.com/", "X") + "</div>")


def share_bar(path, title):
    from urllib.parse import quote
    url = ORIGIN + path
    t = quote(title)
    u = quote(url, safe="")
    ic = {
        "wa": '<path d="M12 3a9 9 0 0 0-7.8 13.5L3 21l4.6-1.2A9 9 0 1 0 12 3z"/><path d="M9 8.5c0 3.5 3 6.5 6.5 6.5l1-1.6-2-1-1 1c-1.2-.5-2.4-1.7-2.9-2.9l1-1-1-2z"/>',
        "fb": '<path d="M14 8h3V4h-3a4 4 0 0 0-4 4v3H7v4h3v6h4v-6h3l1-4h-4V8z"/>',
        "x": '<path d="M4 4l16 16M20 4 4 20"/>',
    }
    def a(cls, href, icon, label):
        return (f'<a class="sh sh-{cls}" data-share="{cls}" href="{href}" target="_blank" rel="noopener">'
                f'<svg viewBox="0 0 24 24" aria-hidden="true">{ic[icon]}</svg><span>{label}</span></a>')
    return (f'<aside class="share" aria-label="Paylaş"><div class="share-in"><p>Bu bölümü paylaşın</p><div class="share-row">'
            + a("wa", f"https://wa.me/?text={t}%20{u}", "wa", "WhatsApp")
            + a("fb", f"https://www.facebook.com/sharer/sharer.php?u={u}", "fb", "Facebook")
            + a("x", f"https://x.com/intent/post?text={t}&url={u}", "x", "X")
            + "</div></div></aside>")


def footer():
    books = "".join(f'<li><a href="{b["base"]}">{E(b["title"])}</a></li>' for b in BOOKS)
    contacts = "".join(f'<li><a href="{E(c["href"])}">{E(c["value"])}</a></li>' for c in HOME["contacts"])
    sisters = "".join(
        f'<div><h4>{E(g["group"])}</h4><ul>' +
        "".join(f'<li><a href="{E(l["href"])}" rel="noopener">{E(l["label"])}</a></li>' for l in g["links"]) +
        "</ul></div>" for g in HOME["sisters"])
    return f"""<footer class="foot">
  <div class="foot-in">
    <div class="foot-brand">
      <a class="mark" href="/">{MARK}<span>ACIPAYAM<em>.com</em></span></a>
      <p class="foot-motto">Ortak paydamız memleketimiz.</p>
      <p>2004’ten beri Acıpayam’ın kitapları, sözlü tarihi ve sesleri. Ticari amacı olmayan bağımsız bir kültür hizmeti.</p>
    </div>
    <div><h3>Kitaplar</h3><ul>{books}</ul></div>
    <div><h3>Arşivler</h3><ul>
      <li><a href="/sabit/">Köy haritası</a></li><li><a href="/sabit/kizilhan/">Görüşme dizini</a></li>
      <li><a href="/sabit/sozluk/">Yerel ağız sözlüğü</a></li><li><a href="/acipayam-dunu-bugunu/">Acıpayam Dünü Bugünü</a></li>
      <li><a href="/sehit-bilgi-kapisi/">Şehit Bilgi Kapısı</a></li><li><a href="/radyo-arsivi/">Radyo arşivi</a></li></ul></div>
    <div><h3>İletişim</h3><ul>{contacts}</ul></div>
  </div>
  <details class="foot-sisters"><summary>Kardeş bağlantılar</summary><div class="sisters">{sisters}</div></details>
  {"" if CANLI else TEST_NOTE}
</footer>"""


def yt(vid, title="Video"):
    return (f'<div class="yt" data-id="{E(vid)}"><button type="button" aria-label="{E(title)} videosunu oynat">'
            f'<img src="https://i.ytimg.com/vi/{E(vid)}/hqdefault.jpg" alt="" loading="lazy" width="480" height="360">'
            f'<span class="yt-play" aria-hidden="true"></span><span class="yt-title">{E(title)}</span></button></div>')


def fix_yt(htm):
    return re.sub(r'<div class="yt" data-id="([\w-]+)" data-title="([^"]*)"></div>',
                  lambda m: yt(m.group(1), html.unescape(m.group(2))), htm)


def audio(src, label):
    return (f'<figure class="audio"><figcaption>{E(label)}</figcaption>'
            f'<audio controls preload="none" src="{E(src)}"></audio>'
            f'<a class="quiet" href="{E(src)}">MP3 dosyasını aç</a></figure>')


def cover(book, cls="", lazy=True):
    return (f'<img class="cover-img {cls}" src="{book["cover"]}" alt="{E(book["title"])} kapağı" width="400" height="620"'
            f'{" loading=" + chr(34) + "lazy" + chr(34) if lazy else ""}>')


def book_actions(book, light=True):
    a = [f'<a class="btn btn-gold" href="{first_url(book)}">Okumaya başla</a>',
         f'<a class="btn btn-ghost" href="{book["pdf"]}" download>PDF indir <small>{mb(book["pdf_size"])}</small></a>']
    if book.get("audio"):
        a.append(f'<a class="btn btn-ghost" href="{book["base"]}#dinle">Sesli kitap</a>')
    return '<div class="actions">' + "".join(a) + "</div>" + share_mini()


def render_blocks(blocks, book_slug=""):
    out = []
    first_p = True
    for b in blocks:
        k, h = b["k"], b.get("h", "")
        t = plain(h).strip()
        if k == "img":
            cap = b.get("cap", "")
            out.append(f'<figure class="photo"><img src="{b["src"]}" alt="{E(plain(cap) or "Kitaptan fotoğraf")}" '
                       f'width="{b["w"]}" height="{b["ht"]}" loading="lazy">'
                       + (f"<figcaption>{cap}</figcaption>" if cap else "") + "</figure>")
        elif k == "orn":
            out.append('<div class="orn" aria-hidden="true">' + MARK + "</div>")
        elif k == "h3":
            out.append(f'<h2 class="sub" id="{slugify(t)}">{h}</h2>')
        elif k == "verse":
            out.append(f'<p class="verse">{h}</p>')
        elif k == "small":
            out.append(f'<p class="note">{h}</p>')
        else:
            c = []
            if k == "alt":
                c.append("alt")
            if t.startswith("✧"):
                c = ["bro"]
                h = re.sub(r"^\s*✧\s*", "", h)
            elif t.startswith("—") and book_slug == "uslu-dusler":
                c.append("human")
            if first_p and k == "p" and not c and len(t) > 120:
                c.append("lead-p")
                first_p = False
            out.append(f'<p{" class=" + chr(34) + " ".join(c) + chr(34) if c else ""}>{h}</p>')
    return "\n".join(out)


written = []


def write(path, content):
    p = OUT / path.lstrip("/")
    if path.endswith("/"):
        p = p / "index.html"
    p.parent.mkdir(parents=True, exist_ok=True)
    content = MEDIA_RE.sub(lambda m: MEDIA_BASE + m.group(1), content)
    p.write_text(content, encoding="utf-8")
    written.append(path)


# ------------------------------------------------------------------ kitap sayfaları
def toc(book):
    rows, part = [], object()
    for i, c in enumerate(book["data"]["chapters"]):
        if c["part"] != part:
            part = c["part"]
            if rows:
                rows.append("</ol>")
            rows.append((f'<h3 class="toc-part">{E(tr_title(part))}</h3>' if part else "") + '<ol class="toc">')
        rows.append(f'<li><a href="{chapter_url(book, i, c)}"><span class="toc-n">{i + 1:02d}</span>'
                    f'<span class="toc-t">{E(tr_title(c["title"]))}</span></a></li>')
    rows.append("</ol>")
    return "\n".join(rows)


def cover_pair(book):
    """Ön ve arka kapak yan yana; dokununca büyük hâli açılır."""
    items = []
    for side, src, label in (("", book["cover"], "Ön kapak"), ("-arka", book["back"], "Arka kapak")):
        full = f"/img/kapak/{book['slug']}{side}-buyuk.webp"
        items.append(
            f'<button type="button" class="zoom" data-full="{full}" data-label="{E(book["title"])} · {label}" '
            f'aria-label="{E(book["title"])}, {label.lower()}: büyüt">'
            f'<img src="{src}" alt="{E(book["title"])} {label.lower()}" width="400" height="620"><span>{label}</span></button>')
    return (f'<figure class="covers" data-zoom-group>{"".join(items)}'
            f'<figcaption>Büyütmek ve okumak için kapağa dokunun</figcaption></figure>')


def book_hero(book, extra_meta=""):
    sub = f'<p class="hero-sub">{E(book["subtitle"])}</p>' if book.get("subtitle") else ""
    by = E(book["author"]) + (f' <span>· Editör: {E(book["editor"])}</span>' if book.get("editor") else "")
    hours = book["words"] / 200 / 60
    return f"""<header class="book-hero">
  <div class="book-hero-in">
    {cover_pair(book)}
    <div class="book-hero-copy">
      <p class="kicker">{E(book['series'])}</p>
      <h1>{E(book['title'])}</h1>
      {sub}
      <p class="hero-by">{by}</p>
      <p class="hero-intro">{E(book['intro'])}</p>
      {book_actions(book)}
    </div>
  </div>
</header>"""


def listen_section(book):
    if not book.get("audio"):
        return ""
    tracks = ""
    if book.get("tracks"):
        items = "".join(
            f'<li><button type="button" data-track="{E(book["tracks_base"] + t["file"])}">'
            f'<span class="toc-n">{t["track"]:02d}</span><span class="toc-t">{E(tr_title(t["title"]))}</span>'
            f'<span class="toc-m">{int(t["planned_duration_seconds"]) // 60}:{int(t["planned_duration_seconds"]) % 60:02d}</span></button></li>'
            for t in book["tracks"])
        tracks = f'<h3 class="toc-part">Bölüm bölüm dinle</h3><ol class="toc tracks">{items}</ol>'
    label = "Kitabın tamamı" + (" · " + book["audio_len"] if book.get("audio_len") else "")
    return (f'<section class="panel" id="dinle"><h2>Sesli kitap</h2>'
            f'<p class="muted">Ses kaydı kitabın ilk yayımlanan sürümünden hazırlandı; metinde sonradan yapılan düzeltmeler kayda yansımamış olabilir.</p>'
            f'{audio(book["audio"], label)}{tracks}</section>')


def series_strip(book):
    if not book.get("seri"):
        return ""
    items = "".join(
        f'<li><a href="{b["base"]}"{" aria-current=" + chr(34) + "page" + chr(34) if b is book else ""} style="--book:{b["color"]}">'
        f'{cover(b)}<span class="seri-no">{E(b["seri_ad"])}</span><span class="seri-t">{E(b["title"])}</span></a></li>'
        for b in SERI_BOOKS)
    return f"""<section class="seri" aria-label="US’lu Anlatılar serisi">
  <div class="seri-in">
    <div class="seri-head"><p class="kicker">Seri</p><h2>US’lu Anlatılar</h2>
      <p>Mustafa Ünal’ın beş kitaplık serisi: çocukluktan bugüne bir hayatın hatıraları ve süzgeçten geçmiş düşünceleri. Her kitap tek başına da okunabilir.</p></div>
    <ol class="seri-list">{items}</ol>
  </div>
</section>"""


def build_book(book):
    side = []
    if book.get("overview"):
        side.append('<section class="panel"><h2>Kitabın içinden</h2>' + "".join(f"<p>{E(p)}</p>" for p in book["overview"]) + "</section>")
    if book.get("quote"):
        side.append(f'<blockquote class="pull">{E(book["quote"])}</blockquote>')
    for s in book.get("extra", []):
        side.append(f'<section class="panel"><h2>{E(s["title"])}</h2>{fix_yt(s["html"])}</section>')
    side.append(listen_section(book))
    others = "".join(
        f'<li><a href="{o["base"]}" style="--book:{o["color"]}">{cover(o)}<span>{E(o["title"])}</span></a></li>'
        for o in BOOKS if o is not book)
    body = f"""{book_hero(book)}
{series_strip(book)}
<div class="book-body">
  <section class="contents" id="icindekiler"><h2>İçindekiler</h2>{toc(book)}</section>
  <aside class="book-side">{''.join(side)}</aside>
</div>
<section class="more-books"><h2>Koleksiyondaki diğer kitaplar</h2><ul class="mini-shelf">{others}</ul></section>"""
    return layout(book["base"], book["title"], body, desc=book["summary"], cls="page-book", style=f"--book:{book['color']}")


def build_chapter(book, i):
    ch = book["data"]["chapters"]
    c = ch[i]
    prev_ = (chapter_url(book, i - 1, ch[i - 1]), tr_title(ch[i - 1]["title"])) if i else None
    next_ = (chapter_url(book, i + 1, ch[i + 1]), tr_title(ch[i + 1]["title"])) if i + 1 < len(ch) else None
    title = tr_title(c["title"])
    iv = c.get("interview")
    lead = ""
    if iv:
        title = iv.get("title") or title
        lead = f'<p class="chap-lead">{E(iv["subtitle"])}</p>'
    video = yt(iv["video"], f'{iv["title"]} — {iv["subtitle"]}') if iv and iv.get("video") else ""
    subs = [b for b in c["blocks"] if b["k"] == "h3"]
    inpage = ""
    if len(subs) >= 4:
        inpage = ('<details class="inpage"><summary>Bu bölümde ' + str(len(subs)) + ' başlık var</summary><ol>' +
                  "".join(f'<li><a href="#{slugify(plain(b["h"]))}">{E(plain(b["h"]))}</a></li>' for b in subs) +
                  "</ol></details>")
    extra = ('<section class="chap-extra">' + "".join(fix_yt(x) for x in iv["extra"]) + "</section>") if iv and iv.get("extra") else ""
    pager = '<nav class="pager" aria-label="Bölümler arasında gezin">'
    pager += (f'<a class="pager-prev" href="{prev_[0]}"><small>Önceki bölüm</small>{E(prev_[1])}</a>' if prev_ else "<span></span>")
    pager += (f'<a class="pager-next" href="{next_[0]}"><small>Sonraki bölüm</small>{E(next_[1])}</a>' if next_ else
              f'<a class="pager-next" href="{book["base"]}"><small>Kitabın sonu</small>Kitabın sayfasına dön</a>')
    pager += "</nav>"
    part = f'<p class="chap-part">{E(tr_title(c["part"]))}</p>' if c.get("part") else ""
    body = f"""<div class="progress" aria-hidden="true"><span></span></div>
<div class="chap-band"><div class="chap-band-in">
  <a href="{book['base']}"><img src="{book['cover']}" alt="" width="40" height="62">{E(book['title'])}</a>
  <span>{i + 1} / {len(ch)}</span>
</div></div>
<article class="reader" data-book="{book['slug']}">
  <header class="chap-head">
    <p class="chap-num" aria-hidden="true">{i + 1:02d}</p>
    {part}
    <h1>{E(title)}</h1>
    {lead}
    <div class="tools" role="group" aria-label="Okuma ayarları">
      <span>Yazı boyutu</span>
      <button type="button" data-size="-1" aria-label="Yazıyı küçült">A−</button>
      <button type="button" data-size="1" aria-label="Yazıyı büyüt">A+</button>
      <a href="{book['base']}#icindekiler">İçindekiler</a>
    </div>
    {share_mini()}
  </header>
  {video}
  {inpage}
  <div class="text">
{render_blocks(c["blocks"], book["slug"])}
  </div>
  {extra}
  {pager}
</article>"""
    return layout(chapter_url(book, i, c), f"{title} · {book['title']}", body,
                  desc=f"{book['title']} — {title}", cls="page-reader", style=f"--book:{book['color']}")


# ------------------------------------------------------------------ ana sayfa
LIVE_CHAT = """<ul class="chat" id="chat-list" aria-live="polite"><li><p>Mesajlar getiriliyor…</p></li></ul>
<form class="chat-form" id="chat-form" autocomplete="off">
  <div class="chat-row"><label>Ad veya rumuz<input name="name" maxlength="32" required autocomplete="nickname"></label>
  <label>Memleket / köy<input name="hometown" maxlength="40"></label></div>
  <label>Mesajınız<textarea name="message" maxlength="250" required rows="3" placeholder="Selamınızı yazın"></textarea></label>
  <label class="hp" aria-hidden="true">Web sitesi<input name="website" tabindex="-1" autocomplete="off"></label>
  <p class="chat-foot"><button class="btn btn-gold" type="submit">Selamı gönder</button><span id="chat-status" role="status"></span></p>
  <p class="muted">Mesajlar herkese açık görünür. Telefon numarası ve kişisel bilgi paylaşmayın.</p>
</form>"""


SIGN_ICONS = {
    # basit, tabela piktogramları (beyaz çizgi)
    "koy": '<path d="M4 20V10l8-6 8 6v10"/><path d="M10 20v-6h4v6"/>',
    "kitap": '<path d="M4 5h6a2 2 0 0 1 2 2v13a2 2 0 0 0-2-2H4z"/><path d="M20 5h-6a2 2 0 0 0-2 2v13a2 2 0 0 1 2-2h6z"/>',
    "tarih": '<path d="M4 20h16"/><path d="M6 20V9M10 20V9M14 20V9M18 20V9"/><path d="M3 9l9-5 9 5z"/>',
    "sehit": '<path d="M12 3l2.6 5.6 6 .6-4.5 4 1.3 6-5.4-3.1-5.4 3.1 1.3-6-4.5-4 6-.6z"/>',
    "radyo": '<rect x="3" y="8" width="18" height="12" rx="2"/><circle cx="8" cy="14" r="3"/><path d="M14 12h4M14 16h4M7 8l9-5"/>',
    "sohbet": '<path d="M4 5h16v10H9l-5 4z"/>',
    "video": '<rect x="3" y="6" width="13" height="12" rx="2"/><path d="M16 10l5-3v10l-5-3z"/>',
}


def sign(href, icon, title, sub):
    return (f'<li><a class="sign" href="{href}"><svg viewBox="0 0 24 24" aria-hidden="true">{SIGN_ICONS[icon]}</svg>'
            f'<span class="sign-t">{E(title)}</span><span class="sign-s">{E(sub)}</span>'
            f'<span class="sign-arrow" aria-hidden="true">→</span></a></li>')


def build_home():
    h = HOME
    dunu = J("acipayam-dunu-bugunu.json")
    radyo = J("radyo.json")
    mem = h["memorial"]
    signs = "".join([
        sign("#koyler", "koy", "Köyler", f"{len(SABIT['interviews'])} görüşme, köy haritası"),
        sign("#kitaplar", "kitap", "Kitaplar", f"{len(BOOKS)} kitap okunabilir"),
        sign("/acipayam-dunu-bugunu/", "tarih", "Acıpayam Tarihi", f"{len(dunu['episodes'])} söyleşi, Hikmet Başaran"),
        sign("/sehit-bilgi-kapisi/", "sehit", "Şehitler", f"{mem['stat']} şehit kaydı"),
        sign("/#radyo", "radyo", "Radyo ACIPAYAM.com", f"{len(radyo['records'])} eski yayın kaydı"),
        sign("#videolar", "video", "Videolar", "Eski videolar ve etkinlikler"),
    ])
    pins = "".join(
        f'<a class="pin" href="{p["href"]}" style="left:{p["left"]};top:{p["top"]}"><span>{E(p["name"])}</span></a>'
        for p in SABIT["pins"] if p["href"])
    # kitaplar: 8 kitap, 4'lü dengeli ızgara
    order = ["bana-koyunu-anlat", "kelekcide-yasamak", "gonul-dostu", "icimde-kalan-cocuk",
             "karanlik-odada-yedi-ay", "uslu-dusler", "adi-konmamis-islere-don-bicen-adam", "uslu-dimag"]
    allb = {b["slug"]: b for b in BOOKS + SOONS}
    cards = ""
    for slug in order:
        b = allb[slug]
        tag = b.get("seri_ad") or ("Sözlü tarih" if slug == "bana-koyunu-anlat" else "Bağımsız eser" if slug == "gonul-dostu" else "Hatıra kitabı")
        soon = b.get("soon")
        cards += (f'<li class="bk{" is-soon" if soon else ""}"><a href="{b["base"]}">'
                  f'<span class="bk-cover">{cover(b)}{"<span class=bk-ribbon>Yakında</span>" if soon else ""}</span>'
                  f'<span class="bk-tag">{E(tag)}</span><span class="bk-t">{E(b["title"])}</span>'
                  f'<span class="bk-a">{E(b["author"])}</span></a></li>')
    videos = "".join(f"<li>{yt(v['id'], v['title'])}</li>" for v in h["videos"])
    story = h["story"]
    def _rec(x):
        return (f'<li><div class="r-head"><b>{E(x["title"])}</b><time>{E(x["duration"])}</time></div>'
                f'<p>{E(x["person"])}</p><audio controls preload="none" src="{E(x["file"])}"></audio></li>')
    recs = radyo["records"]
    radyo_html = f"""<div class="radyo" id="radyo">
      <h3>Radyo ACIPAYAM.com</h3>
      <p>Sitenin ilk yıllarında radyomuz da vardı. “Toprağın Sesi” gibi programlarda şiirler, türküler ve köşe yazıları okundu; memleketin sesi gurbete taşındı. O yayınlardan {len(recs)} kayıt bugün hâlâ dinlenebiliyor.</p>
      <ol class="radyo-list">{"".join(_rec(x) for x in recs[:3])}</ol>
      <details class="radyo-more"><summary>Bütün kayıtlar ({len(recs)})</summary><ol class="radyo-list" start="4">{"".join(_rec(x) for x in recs[3:])}</ol></details>
      <p class="radyo-link"><a href="/radyo-arsivi/">Radyo arşivi sayfası →</a></p>
    </div>"""
    split = story["body"].find("<p>Ancak ACIPAYAM.com")
    assert split > 0
    story_old, story_new = story["body"][:split], story["body"][split:]
    cut = story_new.find("<h3>")
    story_new = story_new if cut < 0 else (
        story_new[:cut] + '<details class="story-more"><summary>Devamını okuyun</summary>'
        + story_new[cut:] + "</details>")
    hist = h["history"]
    body = f"""
<section class="giris">
  <img class="giris-img" src="/img/photo-01.webp" alt="Acıpayam Alaaddin Mahallesi’ndeki Taşkın Dede hayrında ateşte kaynayan kazanlar" width="1536" height="1024">
  <div class="giris-in">
    <p class="giris-kicker">ACIPAYAM.com · 2004’ten beri</p>
    <h1>Memleket kokusu.</h1>
    <p class="giris-lead">Acıpayam’ın ortak hafızası: köylerin anlattıkları, şehitlerin adları, radyonun sesleri ve memleket kitapları. Hepsi ücretsiz, hepsi burada.</p>
    {share_mini()}
  </div>
  <p class="giris-credit">Taşkın Dede hayrı, 700 yıllık gelenek · Alaaddin Mahallesi, Acıpayam · Fotoğraf: Mustafa Ünal</p>
</section>

<div class="signs-wrap">
  <div class="signs-in">
    <figure class="afis"><img src="{h['banner']}" alt="ACIPAYAM.com, Memleketimin Kokusu, 2004’ten beri: yöresel kıyafetli kız çocuğu, çiçekler, eski Acıpayam ovası, Türk bayrağı ve Atatürk" width="1600" height="671"></figure>
    <nav aria-label="Bölümler"><ul class="signs">{signs}</ul></nav>
  </div>
</div>

<section class="blok" id="koyler" aria-labelledby="koyler-b">
  <header class="blok-head"><h2 id="koyler-b">Köy köy Acıpayam</h2>
    <p>Sabit Kızılhan’ın kaydettiği {len(SABIT['interviews'])} sözlü tarih görüşmesi. Haritada bir köye dokunun; anlatının metni ve videosu açılır.</p></header>
  <div class="map"><img src="{SABIT['map']}" alt="Acıpayam ve köylerinin haritası" width="1600" height="1000" loading="lazy">{pins}</div>
  <p class="blok-links"><a class="btn" href="/sabit/">Bana Köyünü Anlat</a><a class="btn btn-line" href="/sabit/kizilhan/">Bütün görüşmeler</a><a class="btn btn-line" href="/sabit/sozluk/">Yerel ağız sözlüğü</a></p>
</section>

<section class="blok blok-alt" id="kitaplar" aria-labelledby="kitaplar-b">
  <header class="blok-head"><h2 id="kitaplar-b">Memleket kitapları</h2>
    <p>İnternette bölüm bölüm okunur, PDF olarak indirilir, kimi sesli dinlenir. US’lu Anlatılar beş kitaplık bir seridir.</p></header>
  <ul class="bks">{cards}</ul>
</section>

<section class="hikaye" id="hikaye">
  <div class="hikaye-in">
    <div class="hikaye-side">
      <p class="hikaye-k">2004–2014 · İlk on yıl</p>
      <h2>{E(story['title'])}</h2>
    </div>
    <div class="hikaye-text">{story_old}{radyo_html}</div>
  </div>
  <div class="yol">
    <h3 class="yol-baslik">ACIPAYAM.com’un yolculuğu</h3>
    <p class="yol-not">Eski görünümlere dokunun, büyüsün.</p>
    <ol class="yol-list" data-zoom-group>
      <li><p class="yol-yil">2006</p>
        <button type="button" class="zoom" data-full="/img/eski/2006-mayis.webp" data-label="ACIPAYAM.com · Mayıs 2006" aria-label="ACIPAYAM.com, Mayıs 2006 görünümü: büyüt"><img src="/img/eski/2006-mayis.webp" alt="ACIPAYAM.com’un 2006’daki ana sayfası: Memleketin Kokusu başlığı, bazlama yapan kadınlar fotoğrafı" width="1036" height="1166" loading="lazy"><span>2006</span></button>
        <p class="yol-t">İlk tasarım: “Memleketin Kokusu”</p>
        <p>Haber arşivi, forumlar, foto albümleri, mini sohbet ve radyo. Mayıs 2006’da 6.839 üye.</p></li>
      <li><p class="yol-yil">2011</p>
        <button type="button" class="zoom" data-full="/img/eski/2011.webp" data-label="ACIPAYAM.com · Temmuz 2011" aria-label="ACIPAYAM.com, 2011 görünümü: büyüt"><img src="/img/eski/2011.webp" alt="ACIPAYAM.com’un 2011’deki bordo renkli ana sayfası" width="1036" height="1024" loading="lazy"><span>2011</span></button>
        <p class="yol-t">Bordo dönem</p>
        <p>“2004’ten beri… Memleketimin Kokusu.” Köşe yazarları, kan bankası, köy köy yerleşim yerleri; 30 bini aşan üye.</p></li>
      <li><p class="yol-yil">2014’e kadar</p>
        <button type="button" class="zoom" data-full="/img/eski-site-2.webp" data-label="ACIPAYAM.com · Mor dönem" aria-label="ACIPAYAM.com, mor dönem görünümü: büyüt"><img src="/img/eski-site-2.webp" alt="ACIPAYAM.com’un mor renkli son dönem ana sayfası" width="494" height="796" loading="lazy"><span>Mor dönem</span></button>
        <p class="yol-t">Mor dönem: “Ortak Paydamız Memleketimiz”</p>
        <p>Sitenin 10. yaşına kadarki son görünümü. 3 Nisan 2014’te yayına ara verildi.</p></li>
      <li class="yol-bugun"><p class="yol-yil">2026</p>
        <a class="yol-afis" href="#yeniden"><img src="{h['banner']}" alt="ACIPAYAM.com’un yeni afişi" width="1600" height="671" loading="lazy"></a>
        <p class="yol-t">Yeniden yayında</p>
        <p>Aynı isim, aynı ruh: kitaplar, köy köy sözlü tarih, şehitlerimiz ve eski radyonun sesleri.</p>
        <p><a class="yol-link" href="#yeniden">Neden yeniden yayındayız? →</a></p></li>
    </ol>
  </div>
  <div class="yol ekip">
    <h3 class="yol-baslik">Eski ekibimiz</h3>
    <p class="yol-not">ACIPAYAM.com’u gönüllü emekleriyle yıllarca ayakta tutanlar. Hepsine teşekkür ediyoruz.</p>
    <ol class="ekip-list" data-zoom-group><li class="ekip-kart"><p class="yol-yil">2005</p><button type="button" class="zoom" data-full="/img/eski/ekip-2005.webp" data-label="ACIPAYAM.com ekibi · 2005" aria-label="2005 ekibinin fotoğrafları: büyüt"><img src="/img/eski/ekip-2005.webp" alt="ACIPAYAM.com 2005 ekibinin fotoğrafları" width="1028" height="108" loading="lazy"><span>2005</span></button><ul class="ekip-adlar"><li><b>Mustafa Ünal</b><span>Kurucu</span></li><li><b>Nuri Gökgöz</b><span>Site editörü</span></li><li><b>Muhammet Ak</b><span>Site yöneticisi</span></li><li><b>İsmail Yıldırım</b><span>Site yöneticisi</span></li><li><b>Mehmet Soysal</b><span>Radyo yöneticisi</span></li><li><b>Emin Okkaya</b><span>Haber editörü</span></li><li><b>Muhammet Dilek</b><span>Köşe yazarı</span></li><li><b>Ümran Songun</b><span>Köşe yazarı</span></li></ul></li><li class="ekip-kart"><p class="yol-yil">2006</p><button type="button" class="zoom" data-full="/img/eski/ekip-2006.webp" data-label="ACIPAYAM.com ekibi · 2006" aria-label="2006 ekibinin fotoğrafları: büyüt"><img src="/img/eski/ekip-2006.webp" alt="ACIPAYAM.com 2006 ekibinin fotoğrafları" width="756" height="168" loading="lazy"><span>2006</span></button><ul class="ekip-adlar"><li><b>Mustafa Ünal</b><span>Kurucu, imtiyaz sahibi</span></li><li><b>Nuri Gökgöz</b><span>Genel koordinatör</span></li><li><b>Emin Okkaya</b><span>Site editörü</span></li><li><b>Muhammet Ak</b><span>Medya direktörü</span></li><li><b>Müzeyyen Savaş</b><span>Haber editörü</span></li><li><b>Osman Can</b><span>Köşe yazarı</span></li><li><b>Baki Evkaralı</b><span>Köşe yazarı</span></li><li><b>Ümran Songun</b><span>Köşe yazarı</span></li><li><b>Ali Can</b><span>Köşe yazarı</span></li><li><b>İsmail Yıldırım</b><span>Teknik sorumlu</span></li></ul></li><li class="ekip-kart"><p class="yol-yil">2011</p><button type="button" class="zoom" data-full="/img/eski/ekip-2011.webp" data-label="ACIPAYAM.com ekibi · 2011" aria-label="2011 ekibinin fotoğrafları: büyüt"><img src="/img/eski/ekip-2011.webp" alt="ACIPAYAM.com 2011 ekibinin fotoğrafları" width="1036" height="112" loading="lazy"><span>2011</span></button><ul class="ekip-adlar"><li><b>Mustafa Ünal</b><span>Kurucu</span></li><li><b>Sabit Kızılhan</b><span>Halkla ilişkiler</span></li><li><b>İsmail Yıldırım</b><span>Teknik sorumlu</span></li><li><b>R. Alkan</b><span>Haber koordinatörü</span></li><li><b>M. Karaoğlan</b><span>Genel sorumlu</span></li><li><b>Hüseyin Kaçmaz</b><span>Avrupa sorumlusu</span></li><li><b>Hüzün</b><span>Bayan sorumlusu</span></li><li><b>E. İlhan</b><span>Haber editörü</span></li><li><b>Can Acar</b><span>Haber editörü</span></li><li><b>H. Baki Çelen</b><span>Haber editörü</span></li></ul></li><li class="ekip-kart"><p class="yol-yil">2013</p><button type="button" class="zoom" data-full="/img/eski/ekip-2013.webp" data-label="ACIPAYAM.com ekibi · 2013" aria-label="2013 ekibinin fotoğrafları: büyüt"><img src="/img/eski/ekip-2013.webp" alt="ACIPAYAM.com 2013 ekibinin fotoğrafları" width="1218" height="108" loading="lazy"><span>2013</span></button><ul class="ekip-adlar"><li><b>Mustafa Ünal</b><span>İmtiyaz sahibi</span></li><li><b>Sabit Kızılhan</b><span>Halkla ilişkiler</span></li><li><b>M. Karaoğlan</b><span>Genel sorumlu</span></li><li><b>Hüseyin Kaçmaz</b><span>Avrupa sorumlusu</span></li><li><b>Can Acar</b><span>Haber editörü</span></li><li><b>H. Baki Çelen</b><span>Radyo DJ</span></li></ul></li></ol>
  </div>
</section>

<section class="hikaye hikaye-yeni" id="yeniden">
  <div class="hikaye-in">
    <div class="hikaye-side">
      <p class="hikaye-k">Bugün · Yeniden yayındayız</p>
      <h2>Neden yeniden yayındayız?</h2>
      <p class="hikaye-motto">Ortak paydamız memleketimiz.</p>
      <figure class="afis afis-yeni"><img src="{h['banner']}" alt="ACIPAYAM.com, Memleketimin Kokusu, 2004’ten beri: yeni afiş" width="1600" height="671" loading="lazy"><figcaption>Eski afişimizden esinlenen yeni tasarım</figcaption></figure>
    </div>
    <div class="hikaye-text">{story_new}<p class="imza">{E(story['signature'][0])}<small>ACIPAYAM.com kurucusu</small></p></div>
  </div>
</section>

<section class="katki" id="katki" aria-labelledby="katki-b">
  <div class="katki-in">
    <div>
      <p class="hikaye-k">Siz de katkıda bulunun</p>
      <h2 id="katki-b">Sizin de anlatacak bir hikâyeniz var mı?</h2>
      <p>Eski bir fotoğraf, bir mektup, köyünüzün unutulmuş bir hatırası, bir şiir ya da bir ses kaydı… ACIPAYAM.com herkesin katkısına açık. Gönderdikleriniz incelenir; uygun görülenler gönderenin adıyla birlikte arşive eklenir.</p>
      <p class="actions"><a class="btn btn-gold" href="mailto:acipayam.com@gmail.com?subject=ACIPAYAM.com%20i%C3%A7in%20katk%C4%B1">E-postayla gönderin</a><a class="btn btn-ghost" href="https://www.facebook.com/acipayamcom" rel="noopener">Facebook’tan yazın</a></p>
    </div>
    <ul class="katki-list">
      <li><b>Fotoğraf</b><span>Nerede, hangi yıl, kimin çektiği</span></li>
      <li><b>Hatıra</b><span>Bir yaşanmışlık, bir köy hikâyesi</span></li>
      <li><b>Belge ve mektup</b><span>Eski kâğıtların fotoğrafı yeter</span></li>
      <li><b>Ses ve video</b><span>Türkü, şiir, sohbet kayıtları</span></li>
    </ul>
  </div>
</section>

<section class="blok" id="videolar" aria-labelledby="video-b">
  <header class="blok-head"><h2 id="video-b">Eski videolar ve etkinlikler</h2><p>ACIPAYAM.com arşivinden görüntüler.</p></header>
  <ul class="videos">{videos}</ul>
</section>

<section class="blok tek" aria-label="Acıpayam tarihi">
  <a class="kart" href="/acipayam-dunu-bugunu/">
    <img src="{hist['image']}" alt="Hikmet Başaran" loading="lazy" width="800" height="800">
    <span class="kart-body"><span class="kart-k">Sözlü tarih · {len(dunu['episodes'])} söyleşi</span><b>{E(hist['title'])}</b>
      <span>{E(hist['by'])}: belediyecilik hafızası, kaybolan değerler, Millî Mücadele.</span></span>
  </a>
</section>

<section class="blok tek tek-son" aria-label="Şehit Bilgi Kapısı">
  <a class="kart kart-anma" href="/sehit-bilgi-kapisi/">
    <span class="anma-sayi">{E(mem['stat'])}</span>
    <span class="kart-body"><span class="kart-k">1853–1928 · Kalıcı anma arşivi</span><b>Denizli Şehit Bilgi Kapısı</b>
      <span>İsim, köy ya da savaşa göre aranabilir.</span></span>
  </a>
</section>
"""
    write("/", layout("/", "ACIPAYAM.com — Memleket Kokusu", body, cls="page-home"))


# ------------------------------------------------------------------ Bana Köyünü Anlat
def page_hero(kicker, title, lead="", img=""):
    pic = f'<img class="ph-img" src="{img}" alt="" width="400" height="400">' if img else ""
    return (f'<header class="page-hero"><div class="page-hero-in">{pic}<div><p class="kicker">{E(kicker)}</p>'
            f'<h1>{E(title)}</h1>{f"<p class=hero-intro>{E(lead)}</p>" if lead else ""}{share_mini()}</div></div></header>')


def build_sabit():
    b = bana
    ch = b["data"]["chapters"]
    pins = "".join(
        f'<a class="pin" href="{p["href"]}" style="left:{p["left"]};top:{p["top"]}"><span>{E(p["name"])}</span></a>'
        for p in SABIT["pins"] if p["href"])
    villages = "".join(
        (f'<li><a href="{v["href"]}">{E(v["name"])}</a></li>' if v["href"] else f'<li class="todo">{E(v["name"])}</li>')
        for v in SABIT["villages"])
    themes = "".join(f'<li><h3>{E(t["title"])}</h3><p>{E(t["text"])}</p></li>' for t in SABIT["themes"])
    body = f"""{book_hero(b, f'<div><dt>Görüşme</dt><dd>{len(INTERVIEWS)}</dd></div>')}
<section class="sheet"><div class="sheet-in">
  <header class="sec-head"><h2>{E(' '.join(SABIT['map_title']))}</h2><p>Görüşmesi yapılan köyler işaretli. Bir köye dokunun; anlatının metni ve videosu açılır.</p></header>
  <div class="map"><img src="{SABIT['map']}" alt="Acıpayam ve köylerinin haritası" width="1600" height="1000" loading="lazy">{pins}</div>
</div></section>
<div class="book-body">
  <section class="contents" id="icindekiler"><h2>İçindekiler</h2>{toc(b)}</section>
  <aside class="book-side">
    <section class="panel"><h2>{E(SABIT['themes_title'])}</h2><ul class="themes">{themes}</ul></section>
    {listen_section(b)}
  </aside>
</div>
<section class="sheet"><div class="sheet-in" id="koyler">
  <header class="sec-head"><h2>{E(SABIT['villages_title'])}</h2><p>{E(SABIT['villages_lead'])}</p></header>
  <ul class="chips">{villages}</ul>
  <p class="links-row"><a href="/sabit/kizilhan/">Görüşmelerin tam dizini</a><a href="/sabit/sozluk/">Yerel ağız ve kültür sözlüğü</a></p>
</div></section>"""
    write("/sabit/", layout("/sabit/", b["title"], body, desc=SABIT["lead"], cls="page-book", style=f"--book:{b['color']}"))

    rows = "".join(
        f'<tr><td>{E(i["no"])}</td><td><a href="/sabit/{i["slug"]}/">{E(i["village"])}</a></td><td>{E(i["people"])}</td></tr>'
        for i in SABIT["interviews"])
    body = page_hero("Bana Köyünü Anlat", SABIT["index_title"], SABIT["index_lead"]) + \
        f'<div class="page-body"><div class="table-wrap"><table class="data"><thead><tr><th scope="col">No</th><th scope="col">Köy</th><th scope="col">Görüşülen</th></tr></thead><tbody>{rows}</tbody></table></div></div>'
    write("/sabit/kizilhan/", layout("/sabit/kizilhan/", "Görüşme dizini", body, style=f"--book:{b['color']}"))

    g = SABIT["glossary"]
    secs = ""
    for s in g["sections"]:
        rows = "".join("<tr>" + "".join(f"<td>{E(c)}</td>" for c in r) + "</tr>" for r in s["rows"])
        head = "".join(f'<th scope="col">{E(x)}</th>' for x in s["head"])
        secs += f'<h2>{E(s["title"])}</h2><div class="table-wrap"><table class="data" data-filterable><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div>'
    body = page_hero("Bana Köyünü Anlat", g["title"], g["lead"]) + f"""<div class="page-body">
  <label class="search"><span>Sözlükte ara</span><input type="search" data-filter placeholder="Örneğin: camız, babıç"></label>{secs}</div>"""
    write("/sabit/sozluk/", layout("/sabit/sozluk/", g["title"], body, style=f"--book:{b['color']}"))

    in_book = {c["interview"]["no"] for c in ch if c.get("interview")}
    for iv in SABIT["interviews"]:
        if iv["no"] in in_book:
            continue
        vid = yt(iv["video"], iv["title"]) if iv.get("video") else ""
        body = f"""<div class="chap-band"><div class="chap-band-in"><a href="/sabit/"><img src="{b['cover']}" alt="" width="40" height="62">Bana Köyünü Anlat</a><span>Kitap dışı görüşme</span></div></div>
<article class="reader"><header class="chap-head"><h1>{E(iv['title'])}</h1><p class="chap-lead">{E(iv['subtitle'])}</p>{share_mini()}</header>{vid}
  <div class="text">{fix_yt(iv['html'])}</div>
  {('<section class="chap-extra">' + "".join(fix_yt(x) for x in iv['extra']) + '</section>') if iv['extra'] else ''}
  <nav class="pager"><a class="pager-prev" href="/sabit/kizilhan/"><small>Dizin</small>Tüm görüşmeler</a><a class="pager-next" href="/sabit/#koyler"><small>Harita</small>Köylere dön</a></nav>
</article>"""
        write(f"/sabit/{iv['slug']}/", layout(f"/sabit/{iv['slug']}/", iv["title"], body, cls="page-reader", style=f"--book:{b['color']}"))


# ------------------------------------------------------------------ diğer sayfalar
def build_dunu():
    d = J("acipayam-dunu-bugunu.json")
    eps = ""
    for e in d["episodes"]:
        blocks = "".join(
            f'<div class="tc"><a class="tc-time" href="https://www.youtube.com/watch?v={e["video"]}&amp;t={b["t"]}s" rel="noopener" '
            f'aria-label="Videoda {E(b["label"])} anına git">{E(b["label"])}</a><p>{E(b["text"])}</p></div>'
            for b in e["blocks"])
        eps += f"""<section class="episode" id="{E(e['id'])}">
  <p class="chap-num" aria-hidden="true">{E(e['no']).zfill(2)}</p><h2>{E(e['title'])}</h2><p class="lead">{E(e['sub'])}</p>
  {yt(e['video'], e['title'])}
  <details class="transcript"><summary>Konuşmanın yazılı metni</summary><p class="muted">Saatler videonun ilgili anını yeni sekmede açar. Metin videonun sesinden çözümlenmiştir.</p>{blocks}</details>
</section>"""
    note = f'<p class="note-box">{E(d["editor_note"])}</p>' if d["editor_note"] else ""
    body = page_hero("Sözlü tarih · Hikmet Başaran’ın anlatımıyla", d["title"], d["intro"][0] if d["intro"] else "", d["image"]) + \
        f'<div class="page-body narrow">{note}{eps}</div>'
    write("/acipayam-dunu-bugunu/", layout("/acipayam-dunu-bugunu/", d["title"], body, style="--book:#4f1f75"))


def build_radyo():
    r = J("radyo.json")
    items = "".join(
        f'<li class="rec"><span class="rec-n">{i + 1:02d}</span><div><h2>{E(x["title"])}</h2><p>{E(x["person"])}</p>'
        f'<audio controls preload="none" src="{E(x["file"])}"></audio></div><time>{E(x["duration"])}</time></li>'
        for i, x in enumerate(r["records"]))
    body = page_hero(r["eyebrow"], r["title"], " ".join(r["intro"])) + f"""<div class="page-body narrow">
  <label class="search"><span>Kayıtlarda ara</span><input type="search" data-filter-list="#kayitlar" placeholder="Şiir, türkü, isim…"></label>
  <ol class="records" id="kayitlar">{items}</ol></div>"""
    write("/radyo-arsivi/", layout("/radyo-arsivi/", r["title"], body, style="--book:#3d1760"))


def build_foto():
    f = J("fotograflar.json")
    items = "".join(
        f'<li><button type="button" class="zoom" data-full="{x["src"]}" data-label="{E(x["title"])} · {E(x["place"])}" '
        f'aria-label="{E(x["title"])}: büyüt"><img src="{x["src"]}" alt="{E(x["title"])}, {E(x["place"])}" width="{x["w"]}" height="{x["h"]}" loading="lazy">'
        f'<span>{E(x["title"])}</span></button>'
        f'<p class="foto-meta">{E(x["place"])}{" · " + E(x["note"]) if x.get("note") else ""}{" · Fotoğraf: " + E(x["by"]) if x.get("by") else ""}</p></li>'
        for x in f["photos"])
    body = page_hero(f["kicker"], f["title"], f["lead"]) + f"""<div class="page-body">
  <ul class="foto-grid" data-zoom-group>{items}</ul>
  <div class="foto-cta"><h2>Albüme fotoğraf ekleyin</h2>
    <p>Elinizde Acıpayam’a dair eski ya da yeni bir fotoğraf varsa gönderin. Nerede, hangi yıl ve kimin çektiğini de yazarsanız altına ekleriz.</p>
    <p class="actions"><a class="btn" href="mailto:acipayam.com@gmail.com?subject=Foto%C4%9Fraf%20alb%C3%BCm%C3%BC">Fotoğraf gönderin</a></p></div>
</div>"""
    write("/fotograflar/", layout("/fotograflar/", f["title"], body, desc=f["lead"], style="--book:#4f1f75"))


def build_sehit():
    m = J("sehitler-meta.json")
    shutil.copy(DATA / "sehitler.json", OUT / "veri" / "sehitler.json")
    body = f"""<header class="page-hero memorial-hero"><div class="page-hero-in"><div>
  <blockquote>{"<br>".join(E(s.strip(chr(34))) for s in m['slogan'][:2])}<cite>Mehmet Âkif Ersoy</cite></blockquote>
  <h1>{E(m['title'])}</h1><p class="hero-intro">{E(m['lead'])}</p>{share_mini()}</div></div></header>
<div class="page-body">
  <h2>{E(m['intro_title'])}</h2><p>{E(m['intro'])}</p>
  <div class="finder-tools">
    <label class="search"><span>İsim, baba adı, köy veya şehadet yeri</span><input type="search" id="q" autocomplete="off"></label>
    <label><span>Savaş</span><select id="war"><option value="">Tüm savaşlar</option></select></label>
    <label><span>İlçe</span><select id="ilce"><option value="">Tüm ilçeler</option></select></label>
  </div>
  <p class="finder-count" id="count" aria-live="polite">Kayıtlar yükleniyor…</p>
  <ol class="martyr-list" id="list"></ol>
  <button type="button" class="btn btn-line" id="more" hidden>Daha fazla göster</button>
  <p class="muted">Kaynak: <a href="{m['source']['href']}" rel="noopener">{E(m['source']['label'])}</a>. Tarihî kayıtlar özgün yazımıyla korunmuştur.</p>
</div>"""
    write("/sehit-bilgi-kapisi/", layout("/sehit-bilgi-kapisi/", "Denizli Şehit Bilgi Kapısı", body,
                                         desc=m["lead"], cls="page-martyrs", style="--book:#2b1240"))


def build_soon():
    for b in SOONS:
        build_soon_one(b)


def build_soon_one(b):
    others = "".join(
        f'<li><a href="{o["base"]}" style="--book:{o["color"]}">{cover(o)}<span>{E(o["title"])}</span></a></li>' for o in BOOKS)
    body = f"""<header class="book-hero">
  <div class="book-hero-in">
    {cover_pair(b)}
    <div class="book-hero-copy">
      <p class="kicker">{E(b['kicker'])}</p>
      <h1>{E(b['title'])}</h1>
      <p class="hero-by">{E(b['author'])}</p>
      <p class="hero-intro">{E(b['summary'])}</p>
      <p class="hero-intro">{E(b['intro'])}</p>
      <div class="status-box"><b>Henüz yayında değil</b><span>{E(b['status'])}. Kitap yayımlandığında burada okunabilecek, PDF olarak indirilebilecek.</span></div>{share_mini()}
    </div>
  </div>
</header>
{series_strip(b)}
<section class="more-books" style="padding-top:4rem"><h2>Yayımlanan kitaplar</h2><ul class="mini-shelf">{others}</ul></section>"""
    write(b["base"], layout(b["base"], b["title"], body, desc=b["summary"], cls="page-book", style=f"--book:{b['color']}"))


def redirects():
    uslu = next(b for b in BOOKS if b["slug"] == "uslu-dusler")
    for src, dst in {"/uslu-dusler/dinle/": "/uslu-dusler/#dinle", "/uslu-dusler/giris/": first_url(uslu)}.items():
        write(src, f'<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0; url={dst}">'
                   f'<link rel="canonical" href="{dst}"><title>Yönlendiriliyor</title><a href="{dst}">Devam etmek için tıklayın</a>')


def not_found():
    body = page_hero("Sayfa bulunamadı", "Bu sayfa burada değil.", "Adres değişmiş ya da yanlış yazılmış olabilir.") + \
        '<div class="page-body narrow"><div class="actions"><a class="btn btn-gold" href="/#kitaplar">Kitaplara git</a><a class="btn btn-line" href="/sabit/">Köy haritası</a></div></div>'
    (OUT / "404.html").write_text(layout("/404", "Sayfa bulunamadı", body), encoding="utf-8")


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    (OUT / "veri").mkdir()
    shutil.copytree(ROOT / "static", OUT, dirs_exist_ok=True)
    shutil.copytree(ROOT / "assets", OUT / "assets", dirs_exist_ok=True)
    if not CANLI:
        (OUT / "CNAME").write_text("acipayam.gunerunal.com.tr\n")
    (OUT / ".nojekyll").write_text("")
    if CANLI and MEDIA_BASE.rstrip("/") != ORIGIN:
        # eski ses ve indirme bağlantıları, sesleri tutan eski sunucuya yönlensin
        base = MEDIA_BASE.rstrip("/")
        rules = [f"/{d}/* {base}/{d}/:splat 302" for d in (
            "icimde-kalan-cocuk/bolumler", "radyo-arsivi/media", "kelekcide-yasamak/downloads",
            "sabit/downloads", "uslu-dusler/assets")]
        rules += [f"{f} {base}{f} 302" for f in (
            "/icimde-kalan-cocuk/Icimde_Kalan_Cocuk_SESLI_KITAP_Onyx_Yuzde_10_Hizli.mp3",
            "/karanlik-odada-yedi-ay/Karanlik_Odada_Yedi_Ay_SESLI_KITAP_DUZELTILMIS_NIHAI.mp3")]
        (OUT / "_redirects").write_text("\n".join(rules) + "\n")
    (OUT / "robots.txt").write_text("User-agent: *\n" + ("Allow: /\n" if CANLI else "Disallow: /\n"))
    build_home()
    for b in BOOKS:
        if b["slug"] != "bana-koyunu-anlat":
            write(b["base"], build_book(b))
        for i in range(len(b["data"]["chapters"])):
            write(chapter_url(b, i, b["data"]["chapters"][i]), build_chapter(b, i))
    build_sabit()
    build_soon()
    build_dunu()
    build_radyo()
    build_foto()
    build_sehit()
    redirects()
    not_found()
    print(f"{len(written)} sayfa yazıldı → {OUT}")


if __name__ == "__main__":
    main()
