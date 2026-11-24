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
ASSET_V = "2"


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
    {"slug": "uslu-dimag", "base": "/uslu-dimag/", "title": "US’lu Dimağ", "author": "Mustafa Ünal",
     "series": "US’lu Anlatılar · Beşinci kitap · Final", "new": True,
     "summary": "Doksan öğretide ölçüsü oturmuş bir zihin. Her öğretinin sonunda okura dönüp bakması için bir soru.",
     "intro": "Bu kitap öğretmek ya da ikna etmek için yazılmadı. Bir insanın hayatın içinde düşe kalka, zamanla oluşmuş us izlerinin kaydı; davranıştan zamana, güvenden vedaya doksan kısa öğreti."},
    {"slug": "gonul-dostu", "base": "/gonul-dostu/", "title": "Gönül Dostu", "subtitle": "Sabit Kızılhan ile Yol Yürümek",
     "author": "Mustafa Ünal", "series": "Bağımsız eser", "new": True,
     "summary": "2005–2026 arasındaki yol arkadaşlığından; dostluğun, memleketin ve hak mücadelesinin canlı tanıklığı.",
     "intro": next(u for u in HOME["upcoming"] if u["title"].startswith("Gönül"))["paragraphs"][0]},
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
SOON = {
    "slug": "adi-konmamis-islere-don-bicen-adam", "base": "/adi-konmamis-islere-don-bicen-adam/",
    "title": "Adı Konmamış İşlere Don Biçen Adam", "author": "Mustafa Ünal",
    "series": "US’lu Anlatılar · Dördüncü kitap · Henüz yayında değil", "status": _soon["status"],
    "summary": _soon["tagline"], "intro": " ".join(_soon["paragraphs"]),
    "cover": "/img/kapak/adi-konmamis-islere-don-bicen-adam.webp",
    "back": "/img/kapak/adi-konmamis-islere-don-bicen-adam-arka.webp",
    "color": COLORS["adi-konmamis-islere-don-bicen-adam"], "soon": True,
}

SERI = {"icimde-kalan-cocuk": (1, "Kitap I"), "karanlik-odada-yedi-ay": (2, "Kitap II"),
        "uslu-dusler": (3, "Kitap III · Bonus"), "adi-konmamis-islere-don-bicen-adam": (4, "Kitap IV · Hazırlanıyor"),
        "uslu-dimag": (5, "Kitap V · Final")}
for b in BOOKS + [SOON]:
    if b["slug"] in SERI:
        b["seri"], b["seri_ad"] = SERI[b["slug"]]
SERI_BOOKS = sorted((b for b in BOOKS + [SOON] if b.get("seri")), key=lambda b: b["seri"])
OTHER_BOOKS = [b for b in BOOKS if not b.get("seri")]

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
<meta name="theme-color" content="#0f1a2e">
<link rel="icon" href="/img/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;1,500&family=Literata:ital,opsz,wght@0,7..72,400..650;1,7..72,400..500&display=swap">
<link rel="stylesheet" href="/assets/site.css?v={ASSET_V}">
</head>
<body class="{cls}"{f' style="{style}"' if style else ''}>
<a class="skip" href="#icerik">İçeriğe geç</a>
<header class="bar">
  <div class="bar-in">
    <a class="mark" href="/">{MARK}<span>Acıpayam<em>.com</em></span></a>
    <details class="menu">
      <summary><span>Menü</span></summary>
      <nav aria-label="Ana menü">{nav}</nav>
    </details>
  </div>
</header>
<main id="icerik">
{body}
</main>
{footer()}
<script src="/assets/site.js?v={ASSET_V}" defer></script>
</body>
</html>
"""


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
      <a class="mark" href="/">{MARK}<span>Acıpayam<em>.com</em></span></a>
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
    return '<div class="actions">' + "".join(a) + "</div>"


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
                    f'<span class="toc-t">{E(tr_title(c["title"]))}</span><span class="toc-m">{minutes(c["words"])} dk</span></a></li>')
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
      <dl class="facts"><div><dt>Bölüm</dt><dd>{len(book['data']['chapters'])}</dd></div>
        <div><dt>Okuma süresi</dt><dd>{'yaklaşık ' + format(hours, '.1f').replace('.', ',') + ' saat' if hours >= 1 else str(minutes(book['words'])) + ' dakika'}</dd></div>
        <div><dt>PDF</dt><dd>{mb(book['pdf_size'])}</dd></div>{extra_meta}</dl>
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
      <span>{minutes(c['words'])} dakikalık okuma</span>
      <button type="button" data-size="-1" aria-label="Yazıyı küçült">A−</button>
      <button type="button" data-size="1" aria-label="Yazıyı büyüt">A+</button>
      <a href="{book['base']}#icindekiler">İçindekiler</a>
    </div>
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


def build_home():
    h = HOME
    feat = BOOKS[0]
    shelf_data = json.dumps({b["slug"]: {
        "title": b["title"], "subtitle": b.get("subtitle", ""), "author": b["author"], "series": b["series"],
        "summary": b["summary"], "color": b["color"], "href": b["base"], "read": first_url(b), "pdf": b["pdf"],
        "audio": (b["base"] + "#dinle") if b.get("audio") else "", "chapters": len(b["data"]["chapters"]),
        "new": bool(b.get("new"))} for b in BOOKS}, ensure_ascii=False)
    shelf_data = shelf_data[:-1] + ", " + json.dumps({SOON["slug"]: {
        "title": SOON["title"], "author": SOON["author"], "series": SOON["series"],
        "summary": SOON["summary"] + " " + SOON["status"] + ".", "color": SOON["color"], "href": SOON["base"],
        "read": "", "audio": "", "soon": True}}, ensure_ascii=False)[1:]
    def spine(b):
        no = f'<span class="spine-no">{E(b["seri_ad"])}</span>' if b.get("seri") else ""
        soon = b.get("soon")
        cls = "spine" + (" is-on" if b is feat else "") + (" spine-soon" if soon else "")
        ribbon = '<span class="ribbon">Yakında</span>' if soon else ""
        return (f'<li><a class="{cls}" href="{b["base"]}" data-book="{b["slug"]}" style="--book:{b["color"]}">'
                f'{ribbon}{cover(b, lazy=False)}{no}<span class="spine-label">{E(b["title"])}</span></a></li>')
    seri_shelf = "".join(spine(b) for b in SERI_BOOKS)
    other_shelf = "".join(spine(b) for b in OTHER_BOOKS)
    listen = f'<a href="{feat["base"]}#dinle" data-f="audio"{"" if feat.get("audio") else " hidden"}>Sesli kitap</a>'
    soon_html = (f'<a class="soon" href="{SOON["base"]}"><img src="{SOON["cover"]}" alt="{E(SOON["title"])} kapağı" loading="lazy" width="200" height="310">'
                 f'<div><p class="kicker">Henüz yayında değil · {E(SOON["status"])}</p><h3>{E(SOON["title"])}</h3><p>{E(SOON["summary"])}</p></div></a>')
    hist = h["history"]
    dunu = J("acipayam-dunu-bugunu.json")
    radyo = J("radyo.json")
    mem = h["memorial"]
    april = "".join(f'<li><time>{E(a["year"])}</time><div><b>{E(a["title"])}</b><p>{E(a["text"])}</p></div></li>'
                    for a in h["april"]["items"])
    videos = "".join(f"<li>{yt(v['id'], v['title'])}</li>" for v in h["videos"])
    msgs = [m for m in J("sohbet.json").get("messages", []) if len(m["message"]) > 8][:3]
    chat = "".join(
        f'<li><blockquote>{E(m["message"])}</blockquote><p><b>{E(m["name"])}</b>{" · " + E(m["hometown"]) if m.get("hometown") else ""}</p></li>'
        for m in msgs)
    chat_static = (f'<ul class="chat">{chat}</ul>'
                   f'<a class="btn btn-line" href="{ORIGIN}/#mini-sohbet">acipayam.com’da selam bırakın</a>')
    story = h["story"]
    cut = story["body"].find("<h3>")
    story_html = story["body"] if cut < 0 else (
        story["body"][:cut] + '<details class="story-more"><summary>Hikâyenin devamını okuyun</summary>'
        + story["body"][cut:] + "</details>")
    total_words = sum(b["words"] for b in BOOKS)
    body = f"""
<section class="vitrin" style="--book:{feat['color']}" data-vitrin>
  <script type="application/json" id="raf-veri">{shelf_data}</script>
  <div class="vitrin-in">
    <div class="vitrin-head">
      <p class="kicker">ACIPAYAM.com Kültür Yayınları</p>
      <h1 class="sr-only">ACIPAYAM.com Kültür Yayınları</h1>
      <p class="vitrin-lead">Köylerin anlattıkları, bir ömrün hatıraları, Kelekçi’den mektuplar. Hepsi ücretsiz; internette okuyun, PDF olarak indirin, kimini dinleyin.</p>
    </div>
    <div class="vitrin-feature" aria-live="polite">
      <p class="kicker" data-f="series">{E(feat['series'])}</p>
      <h2 data-f="title">{E(feat['title'])}</h2>
      <p class="vf-by" data-f="author">{E(feat['author'])}</p>
      <p class="vf-sum" data-f="summary">{E(feat['summary'])}</p>
      <p class="vf-links"><a class="btn btn-gold" href="{first_url(feat)}" data-f="read">Okumaya başla</a>
        <a href="{feat['base']}" data-f="href">Kitabın sayfası</a>{listen}</p>
    </div>
  </div>
  <div class="raf-wrap" id="kitaplar">
    <div class="raf-gruplar">
      <section class="raf-grup" aria-label="Acıpayam kitaplığı">
        <header><p class="grup-ad">Acıpayam kitaplığı</p><p class="grup-alt">Sözlü tarih, tanıklık ve hatıra</p></header>
        <ul class="raf">{other_shelf}</ul>
      </section>
      <section class="raf-grup raf-seri" aria-label="US’lu Anlatılar serisi">
        <header><p class="grup-ad">US’lu Anlatılar</p><p class="grup-alt">Mustafa Ünal’ın beş kitaplık serisi</p></header>
        <ul class="raf">{seri_shelf}</ul>
      </section>
    </div>
    <div class="raf-line" aria-hidden="true"></div>
    <p class="raf-hint">{len(BOOKS)} kitap · {sum(len(b['data']['chapters']) for b in BOOKS)} bölüm · yaklaşık {round(total_words / 200 / 60)} saatlik okuma</p>
  </div>
</section>

<section class="sheet">
  <div class="sheet-in">
    <header class="sec-head"><h2>Arşivler</h2><p>Kitapların yanında, memleketin sesi ve kayıtları.</p></header>
    <div class="tiles">
      <a class="tile tile-wide" href="/sabit/">
        <img src="/img/acipayam-map.webp" alt="" loading="lazy" width="1600" height="1000">
        <div><p class="kicker">Sözlü tarih · {len(SABIT['interviews'])} görüşme</p><h3>Bana Köyünü Anlat</h3><p>Sabit Kızılhan’ın köy köy kaydettiği anlatılar. Haritadan bir köy seçin; videosu ve metni açılsın.</p></div>
      </a>
      <a class="tile" href="/acipayam-dunu-bugunu/">
        <img src="{hist['image']}" alt="" loading="lazy" width="800" height="800">
        <div><p class="kicker">{len(dunu['episodes'])} söyleşi</p><h3>{E(hist['title'])}</h3><p>{E(hist['by'])}: belediyecilik hafızası, kaybolan değerler, Millî Mücadele.</p></div>
      </a>
      <a class="tile tile-num" href="/sehit-bilgi-kapisi/">
        <p class="big-num">{E(mem['stat'])}</p>
        <div><p class="kicker">1853–1928</p><h3>Denizli Şehit Bilgi Kapısı</h3><p>İsim, köy ya da savaşa göre aranabilen kalıcı anma arşivi.</p></div>
      </a>
      <a class="tile tile-radio" href="/radyo-arsivi/">
        <svg class="wave" viewBox="0 0 240 60" aria-hidden="true"><path d="M0 30 Q10 5 20 30 T40 30 T60 30 Q70 10 80 30 T100 30 Q110 0 120 30 T140 30 Q150 15 160 30 T180 30 Q190 8 200 30 T220 30 T240 30" fill="none" stroke="currentColor" stroke-width="1.5"/></svg>
        <div><p class="kicker">{len(radyo['records'])} kayıt</p><h3>Radyo ACIPAYAM.com</h3><p>2000’li yıllardan şiirler, türküler ve canlı yayınlar.</p></div>
      </a>
    </div>
  </div>
</section>

<section class="story" id="hikaye">
  <div class="story-in">
    <div class="story-side">
      <p class="kicker">{E(story['lead'])}</p>
      <h2>{E(story['title'])}</h2>
      <p class="motto">Ortak paydamız memleketimiz.</p>
      <figure class="relic"><img src="{h['banner']}" alt="ACIPAYAM.com Memleketimin Kokusu afişi" loading="lazy" width="1600" height="672"><figcaption>ACIPAYAM.com afişi</figcaption></figure>
    </div>
    <div class="story-text">{story_html}<p class="sign">{E(story['signature'][0])}<small>ACIPAYAM.com kurucusu</small></p></div>
  </div>
</section>

<section class="sheet sheet-alt">
  <div class="sheet-in notes">
    <div class="note-col">
      <h2>{E(h['april']['title'])}</h2>
      <p>{E(h['april']['intro'])}</p>
      <ol class="years">{april}</ol>
    </div>
    <div class="note-col">
      <h2>Mini Sohbet</h2>
      <p>2004 ruhuyla, yine aynı memleket meydanı.</p>
      {LIVE_CHAT if CANLI else chat_static}
    </div>
  </div>
  <div class="sheet-in">
    <header class="sec-head"><h2>Videolar</h2><p>Acıpayam’ın hafızasından seçkiler.</p></header>
    <ul class="videos">{videos}</ul>
    <div class="soon-row"><h2 class="small-h">Hazırlanıyor</h2>{soon_html}</div>
  </div>
</section>
"""
    write("/", layout("/", "ACIPAYAM.com — Memleket Kokusu", body, cls="page-home"))


# ------------------------------------------------------------------ Bana Köyünü Anlat
def page_hero(kicker, title, lead="", img=""):
    pic = f'<img class="ph-img" src="{img}" alt="" width="400" height="400">' if img else ""
    return (f'<header class="page-hero"><div class="page-hero-in">{pic}<div><p class="kicker">{E(kicker)}</p>'
            f'<h1>{E(title)}</h1>{f"<p class=hero-intro>{E(lead)}</p>" if lead else ""}</div></div></header>')


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
<article class="reader"><header class="chap-head"><h1>{E(iv['title'])}</h1><p class="chap-lead">{E(iv['subtitle'])}</p></header>{vid}
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
    write("/acipayam-dunu-bugunu/", layout("/acipayam-dunu-bugunu/", d["title"], body, style="--book:#3b2a1f"))


def build_radyo():
    r = J("radyo.json")
    items = "".join(
        f'<li class="rec"><span class="rec-n">{i + 1:02d}</span><div><h2>{E(x["title"])}</h2><p>{E(x["person"])}</p>'
        f'<audio controls preload="none" src="{E(x["file"])}"></audio></div><time>{E(x["duration"])}</time></li>'
        for i, x in enumerate(r["records"]))
    body = page_hero(r["eyebrow"], r["title"], " ".join(r["intro"])) + f"""<div class="page-body narrow">
  <label class="search"><span>Kayıtlarda ara</span><input type="search" data-filter-list="#kayitlar" placeholder="Şiir, türkü, isim…"></label>
  <ol class="records" id="kayitlar">{items}</ol></div>"""
    write("/radyo-arsivi/", layout("/radyo-arsivi/", r["title"], body, style="--book:#2a1d3a"))


def build_sehit():
    m = J("sehitler-meta.json")
    shutil.copy(DATA / "sehitler.json", OUT / "veri" / "sehitler.json")
    body = f"""<header class="page-hero memorial-hero"><div class="page-hero-in"><div>
  <blockquote>{"<br>".join(E(s.strip(chr(34))) for s in m['slogan'][:2])}<cite>Mehmet Âkif Ersoy</cite></blockquote>
  <h1>{E(m['title'])}</h1><p class="hero-intro">{E(m['lead'])}</p></div></div></header>
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
                                         desc=m["lead"], cls="page-martyrs", style="--book:#1b2438"))


def build_soon():
    b = SOON
    others = "".join(
        f'<li><a href="{o["base"]}" style="--book:{o["color"]}">{cover(o)}<span>{E(o["title"])}</span></a></li>' for o in BOOKS)
    body = f"""<header class="book-hero">
  <div class="book-hero-in">
    {cover_pair(b)}
    <div class="book-hero-copy">
      <p class="kicker">US’lu Anlatılar · Dördüncü kitap · GAMEKS 1999–2026</p>
      <h1>{E(b['title'])}</h1>
      <p class="hero-by">{E(b['author'])}</p>
      <p class="hero-intro">{E(b['summary'])}</p>
      <p class="hero-intro">{E(b['intro'])}</p>
      <div class="status-box"><b>Henüz yayında değil</b><span>{E(b['status'])}. Kitap yayımlandığında burada okunabilecek, PDF olarak indirilebilecek.</span></div>
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
    build_sehit()
    redirects()
    not_found()
    print(f"{len(written)} sayfa yazıldı → {OUT}")


if __name__ == "__main__":
    main()
