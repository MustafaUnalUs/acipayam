#!/usr/bin/env python3
"""ACIPAYAM.com test sitesi üreticisi.

data/ ve static/ klasörlerinden docs/ altına statik site üretir.
    python3 build.py
"""
import html
import json
import math
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
OUT = ROOT / "docs"
SITE = "https://acipayam.gunerunal.com.tr"
ORIGIN = "https://acipayam.com"
ASSET_V = "1"


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
    words = []
    for i, w in enumerate(s.split(" ")):
        low = w.replace("I", "ı").replace("İ", "i").lower()
        if i and w in small:
            words.append(low)
        elif re.fullmatch(r"[A-ZÇĞİÖŞÜ]{2,5}[’']?\w*", w) and w in ("GAMEKS", "US", "PTT", "TRT", "ADB", "AI"):
            words.append(w)
        else:
            words.append(low[:1].replace("i", "İ").upper() + low[1:] if low else low)
    return " ".join(words)


# ------------------------------------------------------------------ kitaplar
HOME = J("home.json")
PAGES = J("book-pages.json")
USLU = J("uslu-dusler.json")
SABIT = J("sabit.json")

BOOKS = [
    {
        "slug": "uslu-dimag", "base": "/uslu-dimag/", "title": "US’lu Dimağ", "author": "Mustafa Ünal",
        "series": "US’lu Anlatılar · Dördüncü kitap", "cover": "/img/kapak-uslu-dimag.webp", "back": None,
        "summary": "Doksan öğretide ölçüsü oturmuş bir zihin. Her öğretinin sonunda okura dönüp bakması için bir soru.",
        "intro": "Bu kitap öğretmek ya da ikna etmek için yazılmadı. Bir insanın hayatın içinde düşe kalka, zamanla oluşmuş us izlerinin kaydı; davranıştan zamana, güvenden vedaya doksan kısa öğreti.",
        "new": True,
    },
    {
        "slug": "gonul-dostu", "base": "/gonul-dostu/", "title": "Gönül Dostu", "subtitle": "Sabit Kızılhan ile Yol Yürümek",
        "author": "Mustafa Ünal", "series": "Bağımsız eser",
        "cover": "/img/gonul-dostu-sabit-kizilhan-ile-yol-yurumek.webp",
        "back": "/img/gonul-dostu-sabit-kizilhan-ile-yol-yurumek-arka.webp",
        "summary": "2005–2026 arasındaki yol arkadaşlığından; dostluğun, memleketin ve hak mücadelesinin canlı tanıklığı.",
        "intro": next(u for u in HOME["upcoming"] if u["title"].startswith("Gönül"))["paragraphs"][0],
        "new": True,
    },
    {
        "slug": "uslu-dusler", "base": "/uslu-dusler/", "title": "US’lu Düşler", "subtitle": "Olmuş Zekâ",
        "author": "Mustafa Ünal", "series": "US’lu Anlatılar · Üçüncü kitap (bonus)",
        "cover": "/img/kapak-uslu-dusler.webp", "back": "/img/back.webp",
        "summary": HOME["books"][0]["summary"], "intro": USLU["intro"],
        "audio": USLU["audio_full"], "audio_len": USLU["listen"]["duration"],
        "overview": USLU["overview"],
    },
    {
        "slug": "bana-koyunu-anlat", "base": "/sabit/", "title": "Bana Köyünü Anlat", "author": "Sabit Kızılhan",
        "editor": "Mustafa Ünal", "series": "Sözlü tarih", "cover": "/img/kapak-bana-koyunu-anlat.webp", "back": None,
        "summary": HOME["books"][1]["summary"], "intro": SABIT["lead"], "audio": SABIT["audio_full"],
    },
    {
        "slug": "karanlik-odada-yedi-ay", "base": "/karanlik-odada-yedi-ay/", "title": "Karanlık Odada Yedi Ay",
        "author": "Mustafa Ünal", "series": "US’lu Anlatılar · İkinci kitap",
        "cover": "/img/karanlik-odada-yedi-ay-kapak.webp", "back": "/img/karanlik-odada-yedi-ay-arka.webp",
        "summary": HOME["books"][2]["summary"], "intro": PAGES["karanlik-odada-yedi-ay"]["intro"],
        "audio": PAGES["karanlik-odada-yedi-ay"]["audio_full"], "extra": PAGES["karanlik-odada-yedi-ay"]["sections"],
    },
    {
        "slug": "icimde-kalan-cocuk", "base": "/icimde-kalan-cocuk/", "title": "İçimde Kalan Çocuk",
        "author": "Mustafa Ünal", "series": "US’lu Anlatılar · Birinci kitap",
        "cover": "/img/kapak-icimde-kalan-cocuk.webp", "back": "/img/icimde-kalan-cocuk-arka.webp",
        "summary": HOME["books"][3]["summary"], "intro": PAGES["icimde-kalan-cocuk"]["intro"],
        "audio": PAGES["icimde-kalan-cocuk"]["audio_full"], "tracks": PAGES["icimde-kalan-cocuk"].get("tracks"),
        "tracks_base": PAGES["icimde-kalan-cocuk"]["chapters_audio_base"],
        "extra": PAGES["icimde-kalan-cocuk"]["sections"],
    },
    {
        "slug": "kelekcide-yasamak", "base": "/kelekcide-yasamak/", "title": "Kelekçi’de Yaşamak",
        "author": "Dr. Oktar Öner", "editor": "Mustafa Ünal", "series": "Acıpayam.com Kültür Hizmeti",
        "cover": "/img/kapak-kelekcide-yasamak.webp", "back": None,
        "summary": HOME["books"][4]["summary"], "intro": PAGES["kelekcide-yasamak"]["intro"],
        "audio": PAGES["kelekcide-yasamak"]["audio_full"], "quote": PAGES["kelekcide-yasamak"]["quote"],
        "extra": [s for s in PAGES["kelekcide-yasamak"]["sections"] if s["title"] in ("Kitabın Hikâyesi", "Baskı Hakkında")],
    },
]
for b in BOOKS:
    b["data"] = J(f"kitaplar/{b['slug']}.json")
    b["pdf"] = f"/indir/{b['slug']}.pdf"
    b["pdf_size"] = (ROOT / "static" / "indir" / f"{b['slug']}.pdf").stat().st_size
    b["words"] = sum(c["words"] for c in b["data"]["chapters"])

# Bana Köyünü Anlat: köy bölümlerini görüşme sayfalarıyla eşleştir
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


# ------------------------------------------------------------------ parçalar
KILIM = '<div class="kilim" aria-hidden="true"></div>'

NAV = [
    ("/#kitaplik", "Kitaplık"),
    ("/sabit/", "Köyler"),
    ("/acipayam-dunu-bugunu/", "Acıpayam Tarihi"),
    ("/sehit-bilgi-kapisi/", "Şehitler"),
    ("/radyo-arsivi/", "Radyo"),
    ("/#hikaye", "Hikâyemiz"),
]


def layout(path, title, body, desc="", cls="", head_extra=""):
    full = title if "ACIPAYAM" in title else f"{title} · ACIPAYAM.com"
    nav = "".join(
        f'<a href="{h}"{" aria-current=\"page\"" if path.startswith(h) and h != "/" and not h.startswith("/#") else ""}>{t}</a>'
        for h, t in NAV)
    return f"""<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(full)}</title>
<meta name="description" content="{E(desc or 'Acıpayam’ın kitapları, sözlü tarihi ve ortak hafızası. 2004’ten beri memleket kokusu.')}">
<meta name="robots" content="noindex">
<link rel="canonical" href="{ORIGIN}{path}">
<meta property="og:title" content="{E(full)}">
<meta property="og:description" content="{E(desc)}">
<meta property="og:locale" content="tr_TR">
<meta name="theme-color" content="#eef1ee" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#121715" media="(prefers-color-scheme: dark)">
<link rel="icon" href="/img/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400..800&family=Literata:ital,opsz,wght@0,7..72,400..700;1,7..72,400..600&display=swap">
<link rel="stylesheet" href="/assets/site.css?v={ASSET_V}">
{head_extra}
</head>
<body class="{cls}">
<a class="skip" href="#icerik">İçeriğe geç</a>
<header class="top">
  <div class="top-in">
    <a class="mark" href="/" aria-label="ACIPAYAM.com ana sayfa"><b>ACIPAYAM<span>.com</span></b><small>Memleket Kokusu</small></a>
    <details class="menu">
      <summary>Menü</summary>
      <nav aria-label="Ana menü">{nav}</nav>
    </details>
  </div>
</header>
<main id="icerik">
{body}
</main>
<footer class="foot">
  {KILIM}
  <div class="foot-in">
    <p class="foot-mark"><b>ACIPAYAM.com</b> · 2004’ten beri memleket kokusu</p>
    <p>Ortak paydamız memleketimiz. Sorular ve katkılar için <a href="mailto:acipayam.com@gmail.com">acipayam.com@gmail.com</a></p>
    <p class="test-note">Bu adres, acipayam.com içeriğiyle hazırlanmış yeni tasarımın test sürümüdür. Asıl site: <a href="{ORIGIN}/">acipayam.com</a></p>
  </div>
</footer>
<script src="/assets/site.js?v={ASSET_V}" defer></script>
</body>
</html>
"""


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


def cover_figure(book, big=False):
    back = (f'<button type="button" class="cover-flip" data-flip aria-label="Arka kapağı göster">Arka kapak</button>'
            if book.get("back") else "")
    imgs = f'<img class="cover-front" src="{book["cover"]}" alt="{E(book["title"])} kapağı" width="600" height="900">'
    if book.get("back"):
        imgs += f'<img class="cover-back" src="{book["back"]}" alt="{E(book["title"])} arka kapağı" width="600" height="900" loading="lazy">'
    return f'<div class="cover{" cover-big" if big else ""}"><div class="cover-stack">{imgs}</div>{back}</div>'


def mb(n):
    return f"{n / 1_048_576:.0f} MB" if n > 1_048_576 else f"{n / 1024:.0f} KB"


def book_actions(book, first_url):
    a = [f'<a class="btn" href="{first_url}">Okumaya başla</a>',
         f'<a class="btn btn-line" href="{book["pdf"]}" download>PDF indir <small>{mb(book["pdf_size"])}</small></a>']
    if book.get("audio"):
        a.append(f'<a class="btn btn-line" href="{book["base"]}#dinle">Sesli kitabı dinle</a>')
    return '<div class="actions">' + "".join(a) + "</div>"


def render_blocks(blocks, book_slug=""):
    out = []
    for b in blocks:
        k = b["k"]
        h = b.get("h", "")
        t = plain(h).strip()
        if k == "img":
            cap = b.get("cap", "")
            out.append(f'<figure class="photo"><img src="{b["src"]}" alt="{E(plain(cap) or "Kitaptan fotoğraf")}" '
                       f'width="{b["w"]}" height="{b["ht"]}" loading="lazy">'
                       + (f"<figcaption>{cap}</figcaption>" if cap else "") + "</figure>")
        elif k == "orn":
            out.append('<div class="orn" aria-hidden="true"></div>')
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
            out.append(f'<p{" class=" + chr(34) + " ".join(c) + chr(34) if c else ""}>{h}</p>')
    return "\n".join(out)


# ------------------------------------------------------------------ sayfa üretimi
written = []


def write(path, content):
    p = OUT / path.lstrip("/")
    if path.endswith("/"):
        p = p / "index.html"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    written.append(path)


def toc(book):
    rows, part = [], object()
    for i, c in enumerate(book["data"]["chapters"]):
        if c["part"] != part:
            part = c["part"]
            if rows:
                rows.append("</ol>")
            rows.append((f'<h3 class="toc-part">{E(tr_title(part))}</h3>' if part else "") + '<ol class="toc">')
        label = tr_title(c["title"])
        n = f'{i + 1:02d}'
        rows.append(f'<li><a href="{chapter_url(book, i, c)}"><span class="toc-n">{n}</span>'
                    f'<span class="toc-t">{E(label)}</span><span class="toc-m">{minutes(c["words"])} dk</span></a></li>')
    rows.append("</ol>")
    return "\n".join(rows)


def build_book(book):
    ch = book["data"]["chapters"]
    first = chapter_url(book, 0, ch[0])
    sub = f'<p class="book-sub">{E(book["subtitle"])}</p>' if book.get("subtitle") else ""
    by = E(book["author"]) + (f' · Editör: {E(book["editor"])}' if book.get("editor") else "")
    sections = []
    if book.get("overview"):
        sections.append('<section class="prose-block"><h2>Kitabın içinden</h2>' +
                        "".join(f"<p>{E(p)}</p>" for p in book["overview"]) + "</section>")
    if book.get("quote"):
        sections.append(f'<blockquote class="pull">{E(book["quote"])}</blockquote>')
    for s in book.get("extra", []):
        title = s["title"] if s["title"] != "Mustafa Ünal" else "Yazar hakkında"
        sections.append(f'<section class="prose-block"><h2>{E(title)}</h2>{fix_yt(s["html"])}</section>')
    if book.get("audio"):
        tracks = ""
        if book.get("tracks"):
            items = "".join(
                f'<li><button type="button" data-track="{E(book["tracks_base"] + t["file"])}">'
                f'<span class="toc-n">{t["track"]:02d}</span><span class="toc-t">{E(tr_title(t["title"]))}</span>'
                f'<span class="toc-m">{int(t["planned_duration_seconds"]) // 60}:{int(t["planned_duration_seconds"]) % 60:02d}</span></button></li>'
                for t in book["tracks"])
            tracks = f'<h3 class="toc-part">Bölüm bölüm dinle</h3><ol class="toc tracks" data-tracks>{items}</ol>'
        sections.append(
            f'<section class="listen" id="dinle"><h2>Sesli kitap</h2>'
            f'<p class="muted">Ses kaydı kitabın ilk yayımlanan sürümünden hazırlandı; metinde sonradan yapılan düzeltmeler kayda yansımamış olabilir.</p>'
            f'{audio(book["audio"], "Kitabın tamamı" + (" · " + book["audio_len"] if book.get("audio_len") else ""))}{tracks}</section>')
    body = f"""
<article class="book">
  <header class="book-head">
    {cover_figure(book, big=True)}
    <div class="book-copy">
      <p class="book-series">{E(book["series"])}</p>
      <h1>{E(book["title"])}</h1>
      {sub}
      <p class="book-by">{by}</p>
      <p class="book-intro">{E(book["intro"])}</p>
      <p class="book-meta">{len(ch)} bölüm · yaklaşık {round(book["words"] / 200 / 60, 1):g} saatlik okuma</p>
      {book_actions(book, first)}
    </div>
  </header>
  <section class="contents" id="icindekiler">
    <h2>İçindekiler</h2>
    {toc(book)}
  </section>
  {"".join(sections)}
</article>"""
    return body


def build_chapter(book, i):
    ch = book["data"]["chapters"]
    c = ch[i]
    prev_ = (chapter_url(book, i - 1, ch[i - 1]), tr_title(ch[i - 1]["title"])) if i else None
    next_ = (chapter_url(book, i + 1, ch[i + 1]), tr_title(ch[i + 1]["title"])) if i + 1 < len(ch) else None
    title = tr_title(c["title"])
    iv = c.get("interview")
    lead = ""
    if iv:
        title = iv["title"] if iv.get("title") else title
        lead = f'<p class="chap-lead">{E(iv["subtitle"])}</p>'
        if iv.get("video"):
            lead += yt(iv["video"], f'{iv["title"]} — {iv["subtitle"]}')
    subs = [b for b in c["blocks"] if b["k"] == "h3"]
    inpage = ""
    if len(subs) >= 4:
        inpage = ('<nav class="inpage" aria-label="Bu bölümde"><p>Bu bölümde</p><ol>' +
                  "".join(f'<li><a href="#{slugify(plain(b["h"]))}">{E(plain(b["h"]))}</a></li>' for b in subs) +
                  "</ol></nav>")
    extra = ""
    if iv and iv.get("extra"):
        extra = '<section class="chap-extra">' + "".join(fix_yt(x) for x in iv["extra"]) + "</section>"
    pager = '<nav class="pager" aria-label="Bölümler arasında gezin">'
    pager += (f'<a class="pager-prev" href="{prev_[0]}"><small>Önceki bölüm</small>{E(prev_[1])}</a>' if prev_ else "<span></span>")
    pager += (f'<a class="pager-next" href="{next_[0]}"><small>Sonraki bölüm</small>{E(next_[1])}</a>' if next_ else
              f'<a class="pager-next" href="{book["base"]}"><small>Kitap bitti</small>Kitabın sayfasına dön</a>')
    pager += "</nav>"
    part = f'<p class="chap-part">{E(tr_title(c["part"]))}</p>' if c.get("part") else ""
    body = f"""
<div class="progress" aria-hidden="true"><span></span></div>
<article class="reader" data-book="{book['slug']}">
  <header class="chap-head">
    <p class="chap-book"><a href="{book['base']}">{E(book['title'])}</a> <span>· Bölüm {i + 1} / {len(ch)}</span></p>
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
  {inpage}
  <div class="text">
{render_blocks(c["blocks"], book["slug"])}
  </div>
  {extra}
  {pager}
</article>"""
    return layout(chapter_url(book, i, c), f"{title} · {book['title']}", body,
                  desc=f"{book['title']} — {title}", cls="page-reader")


# ------------------------------------------------------------------ ana sayfa
def shelf_card(book):
    first = chapter_url(book, 0, book["data"]["chapters"][0])
    flag = '<span class="flag">Yeni</span>' if book.get("new") else ""
    listen = f'<a href="{book["base"]}#dinle">Dinle</a>' if book.get("audio") else ""
    return f"""<li class="shelf-item">
  <a class="shelf-cover" href="{book['base']}">{flag}<img src="{book['cover']}" alt="{E(book['title'])} kapağı" loading="lazy" width="300" height="450"></a>
  <h3><a href="{book['base']}">{E(book['title'])}</a></h3>
  <p class="shelf-by">{E(book['author'])}</p>
  <p class="shelf-sum">{E(book['summary'])}</p>
  <p class="shelf-acts"><a href="{first}">Oku</a><a href="{book['pdf']}" download>PDF</a>{listen}</p>
</li>"""


def build_home():
    h = HOME
    soon = [u for u in h["upcoming"] if not u["title"].startswith(("Gönül", "US’lu Dimağ"))]
    soon_html = "".join(
        f'<article class="soon"><img src="{u["images"][0]}" alt="{E(u["title"])} kapak taslağı" loading="lazy" width="300" height="450">'
        f'<div><p class="soon-when">{E(u["status"])}</p><h3>{E(u["title"])}</h3><p><b>{E(u["tagline"])}</b></p>'
        + "".join(f"<p>{E(p)}</p>" for p in u["paragraphs"]) + "</div></article>"
        for u in soon if u["images"])
    hist = h["history"]
    dunu = J("acipayam-dunu-bugunu.json")
    radyo = J("radyo.json")
    radio_items = "".join(
        f'<li><button type="button" data-track="{E(r["file"])}"><span class="toc-t">{E(r["title"])}</span>'
        f'<span class="toc-m">{E(r["duration"])}</span></button><small>{E(r["person"])}</small></li>'
        for r in radyo["records"][:5])
    april = "".join(f'<li><time>{E(a["year"])}</time><div><b>{E(a["title"])}</b><p>{E(a["text"])}</p></div></li>'
                    for a in h["april"]["items"])
    april_links = " · ".join(f'<a href="{E(l["href"])}" rel="noopener">{E(l["label"])}</a>' for l in h["april"]["feature"]["links"])
    videos = "".join(f"<li>{yt(v['id'], v['title'])}</li>" for v in h["videos"])
    msgs = J("sohbet.json").get("messages", [])
    chat = "".join(
        f'<li><p>{E(m["message"])}</p><small><b>{E(m["name"])}</b>{" · " + E(m["hometown"]) if m.get("hometown") else ""}'
        f' · <time datetime="{E(m["created_at"])}">{E(m["created_at"][:10])}</time></small></li>'
        for m in msgs if len(m["message"]) > 8)
    contacts = "".join(f'<li><a href="{E(c["href"])}"><b>{E(c["label"])}</b>{E(c["value"])}</a></li>' for c in h["contacts"])
    sisters = "".join(
        f'<div><h3>{E(g["group"])}</h3><ul>' + "".join(f'<li><a href="{E(l["href"])}" rel="noopener">{E(l["label"])}</a></li>' for l in g["links"]) + "</ul></div>"
        for g in h["sisters"])
    story = h["story"]
    pins = SABIT["interviews"]
    mem = h["memorial"]
    body = f"""
<section class="hero">
  <div class="hero-in">
    <p class="hero-since">2004’ten beri</p>
    <h1 class="hero-mark">ACIPAYAM<span>.com</span></h1>
    {KILIM}
    <div class="hero-grid">
      <p class="hero-lead">Acıpayam’ın kitapları, köylerin anlattıkları, kayıtlar ve sesler. Memleketin ortak hafızası, herkesin ücretsiz okuyup dinleyebileceği bir yerde.</p>
      <ul class="hero-facts">
        <li><b>{len(BOOKS)}</b> kitap, tamamı ücretsiz</li>
        <li><b>{len(pins)}</b> köy görüşmesi</li>
        <li><b>{mem['stat']}</b> şehit kaydı</li>
      </ul>
    </div>
    <figure class="hero-art"><img src="{h['banner']}" alt="ACIPAYAM.com Memleketimin Kokusu afişi: yöresel giysili bir kız, Acıpayam ovası ve Atatürk" width="1600" height="672"></figure>
  </div>
</section>

<section class="band" id="kitaplik">
  <div class="band-head">
    <h2>Kitaplık</h2>
    <p>Her kitap internette bölüm bölüm okunabilir, PDF olarak indirilebilir. Bazılarının sesli kitabı da var.</p>
  </div>
  <ol class="shelf">{"".join(shelf_card(b) for b in BOOKS)}</ol>
  <div class="soon-list"><h3 class="small-head">Hazırlanıyor</h3>{soon_html}</div>
</section>

<section class="band band-split">
  <a class="feature" href="/sabit/">
    <img src="/img/acipayam-map.webp" alt="Acıpayam köyleri haritası" loading="lazy" width="1600" height="1000">
    <div>
      <h2>Bana Köyünü Anlat</h2>
      <p>Sabit Kızılhan’ın köy köy dolaşıp kaydettiği {len(pins)} görüşme: yoksulluk, emek, düğünler, göçler. Her anlatı videosuyla birlikte, haritadan seçerek okunur.</p>
      <span class="more">Haritayı aç</span>
    </div>
  </a>
  <a class="feature" href="/acipayam-dunu-bugunu/">
    <img src="{hist['image']}" alt="Hikmet Başaran" loading="lazy" width="800" height="800">
    <div>
      <h2>{E(hist['title'])}</h2>
      <p>{E(hist['by'])}. {E(hist['text'])}</p>
      <span class="more">{len(dunu['episodes'])} söyleşiyi izle ve oku</span>
    </div>
  </a>
</section>

<section class="memorial">
  <div class="memorial-in">
    <p class="memorial-num">{E(mem['stat'])}</p>
    <div>
      <h2>{E(mem['title'])}</h2>
      <p>{E(mem['text'])}</p>
      <a class="btn btn-light" href="/sehit-bilgi-kapisi/">Bir isim ara</a>
    </div>
  </div>
</section>

<section class="band band-split">
  <div class="radio">
    <h2>{E(h['radio']['title'])}</h2>
    <p>{E(h['radio']['kicker'])}: {E(h['radio']['text'][:1].lower() + h['radio']['text'][1:])}</p>
    <ol class="toc tracks" data-tracks>{radio_items}</ol>
    <a class="more" href="/radyo-arsivi/">{len(radyo['records'])} kaydın tamamı</a>
  </div>
  <div class="april">
    <h2>{E(h['april']['title'])}</h2>
    <p>{E(h['april']['intro'])}</p>
    <ol class="years">{april}</ol>
    <p class="small-links">Basında: {april_links}</p>
  </div>
</section>

<section class="band">
  <div class="band-head"><h2>Videolar</h2><p>Acıpayam’ın hafızasından seçkiler.</p></div>
  <ul class="videos">{videos}</ul>
</section>

<section class="band chat">
  <div class="band-head"><h2>Mini Sohbet</h2><p>2004 ruhuyla, yine aynı memleket meydanı. Selamınızı acipayam.com’daki sohbet kutusuna bırakabilirsiniz.</p></div>
  <ul class="chat-list">{chat}</ul>
  <a class="btn btn-line" href="{ORIGIN}/#mini-sohbet">acipayam.com’da selam bırak</a>
</section>

<section class="story" id="hikaye">
  <div class="story-in">
    <h2>{E(story['title'])}</h2>
    <p class="story-lead">{E(story['lead'])}</p>
    <div class="story-text">{story['body']}</div>
    <p class="story-sign">{E(story['signature'][0])}<small>ACIPAYAM.com kurucusu</small></p>
  </div>
</section>

<section class="band band-split">
  <div><h2>Takip edin</h2><ul class="contacts">{contacts}</ul></div>
  <div><h2>Kardeş bağlantılar</h2><p>{E(h['sisters_intro'])}</p><div class="sisters">{sisters}</div></div>
</section>
"""
    write("/", layout("/", "ACIPAYAM.com — Memleket Kokusu", body, cls="page-home"))


# ------------------------------------------------------------------ Bana Köyünü Anlat
def build_sabit():
    b = bana
    ch = b["data"]["chapters"]
    pins = "".join(
        f'<a class="pin{" pin-on" if p["href"] else ""}" href="{p["href"] or "#koyler"}" style="left:{p["left"]};top:{p["top"]}"'
        f' aria-label="{E(p["name"])}"><span>{E(p["name"])}</span></a>'
        for p in SABIT["pins"] if p["href"])
    villages = "".join(
        (f'<li><a href="{v["href"]}">{E(v["name"])}</a></li>' if v["href"] else f'<li class="todo">{E(v["name"])}</li>')
        for v in SABIT["villages"])
    themes = "".join(f'<li><h3>{E(t["title"])}</h3><p>{E(t["text"])}</p></li>' for t in SABIT["themes"])
    ed = SABIT["editor"]
    first = chapter_url(b, 0, ch[0])
    others = [(i, c) for i, c in enumerate(ch) if not c.get("interview")]
    body = f"""
<article class="book">
  <header class="book-head">
    {cover_figure(b, big=True)}
    <div class="book-copy">
      <p class="book-series">Sözlü tarih arşivi · Acıpayam</p>
      <h1>{E(b['title'])}</h1>
      <p class="book-by">Derleyen: {E(ed['name'])} · Editör: Mustafa Ünal</p>
      <p class="book-intro">{E(SABIT['lead'])}</p>
      <p class="book-meta">{len(INTERVIEWS)} görüşme · {len(ch)} bölüm · {E(SABIT['qr_note'])}</p>
      {book_actions(b, first)}
    </div>
  </header>
  <section class="mapsec" id="harita">
    <h2>{E(' '.join(SABIT['map_title']))}</h2>
    <p>Haritada görüşmesi yapılan köyler işaretli. Bir köye dokunun; anlatının metni ve videosu açılır.</p>
    <div class="map"><img src="{SABIT['map']}" alt="Acıpayam ve köylerinin haritası" width="1600" height="1000" loading="lazy">{pins}</div>
  </section>
  <section class="prose-block"><h2>{E(SABIT['themes_title'])}</h2><p>{E(SABIT['themes_lead'])}</p><ul class="themes">{themes}</ul></section>
  <section class="contents" id="icindekiler"><h2>İçindekiler</h2>{toc(b)}</section>
  <section class="prose-block" id="koyler">
    <h2>{E(SABIT['villages_title'])}</h2>
    <p>{E(SABIT['villages_lead'])}</p>
    <ul class="chips">{villages}</ul>
    <p class="small-links"><a href="/sabit/kizilhan/">Görüşmelerin tam dizini</a> · <a href="/sabit/sozluk/">Yerel ağız ve kültür sözlüğü</a></p>
  </section>
  <section class="listen" id="dinle"><h2>Sesli kitap</h2>{audio(b['audio'], 'Bana Köyünü Anlat · kitabın tamamı')}</section>
</article>"""
    write("/sabit/", layout("/sabit/", b["title"], body, desc=SABIT["lead"]))

    # dizin
    rows = "".join(
        f'<tr><td>{E(i["no"])}</td><td><a href="/sabit/{i["slug"]}/">{E(i["village"])}</a></td><td>{E(i["people"])}</td></tr>'
        for i in SABIT["interviews"])
    body = f"""<article class="page-narrow">
  <p class="chap-book"><a href="/sabit/">Bana Köyünü Anlat</a></p>
  <h1>{E(SABIT['index_title'])}</h1><p class="lead">{E(SABIT['index_lead'])}</p>
  <div class="table-wrap"><table class="data"><thead><tr><th scope="col">No</th><th scope="col">Köy</th><th scope="col">Görüşülen</th></tr></thead><tbody>{rows}</tbody></table></div>
</article>"""
    write("/sabit/kizilhan/", layout("/sabit/kizilhan/", "Görüşme dizini · Bana Köyünü Anlat", body))

    # sözlük
    g = SABIT["glossary"]
    secs = ""
    for s in g["sections"]:
        rows = "".join("<tr>" + "".join(f"<td>{E(c)}</td>" for c in r) + "</tr>" for r in s["rows"])
        head = "".join(f'<th scope="col">{E(x)}</th>' for x in s["head"])
        secs += f'<h2>{E(s["title"])}</h2><div class="table-wrap"><table class="data" data-filterable><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div>'
    body = f"""<article class="page-narrow">
  <p class="chap-book"><a href="/sabit/">Bana Köyünü Anlat</a></p>
  <h1>{E(g['title'])}</h1><p class="lead">{E(g['lead'])}</p>
  <label class="search"><span>Sözlükte ara</span><input type="search" data-filter placeholder="Örneğin: camız, babıç"></label>
  {secs}
</article>"""
    write("/sabit/sozluk/", layout("/sabit/sozluk/", g["title"], body))

    # kitapta olmayan ek görüşmeler (26, 27)
    in_book = {c["interview"]["no"] for c in ch if c.get("interview")}
    for iv in SABIT["interviews"]:
        if iv["no"] in in_book:
            continue
        vid = yt(iv["video"], iv["title"]) if iv.get("video") else ""
        body = f"""<article class="reader">
  <header class="chap-head"><p class="chap-book"><a href="/sabit/">Bana Köyünü Anlat</a> <span>· Kitap dışı görüşme</span></p>
  <h1>{E(iv['title'])}</h1><p class="chap-lead">{E(iv['subtitle'])}</p>{vid}</header>
  <div class="text">{fix_yt(iv['html'])}</div>
  {('<section class="chap-extra">' + "".join(fix_yt(x) for x in iv['extra']) + '</section>') if iv['extra'] else ''}
  <nav class="pager"><a class="pager-prev" href="/sabit/kizilhan/"><small>Dizin</small>Tüm görüşmeler</a><a class="pager-next" href="/sabit/#harita"><small>Harita</small>Köy haritasına dön</a></nav>
</article>"""
        write(f"/sabit/{iv['slug']}/", layout(f"/sabit/{iv['slug']}/", iv["title"], body, cls="page-reader"))


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
  <h2><span>{E(e['no'])}</span>{E(e['title'])}</h2><p class="lead">{E(e['sub'])}</p>
  {yt(e['video'], e['title'])}
  <details class="transcript"><summary>Konuşmanın yazılı metni</summary><p class="muted">Saatler videonun ilgili anını yeni sekmede açar.</p>{blocks}</details>
</section>"""
    toc_ = "".join(f'<li><a href="#{E(e["id"])}">{E(e["title"])}</a></li>' for e in d["episodes"])
    body = f"""<article class="page-narrow">
  <header class="talk-head">
    <img src="{d['image']}" alt="Hikmet Başaran" width="400" height="400">
    <div><p class="book-series">Sözlü tarih · Hikmet Başaran’ın anlatımıyla</p><h1>{E(d['title'])}</h1>
    {"".join(f'<p class="lead">{E(p)}</p>' for p in d['intro'])}
    <ol class="mini-toc">{toc_}</ol></div>
  </header>
  {f'<p class="note-box">{E(d["editor_note"])}</p>' if d['editor_note'] else ''}
  {eps}
</article>"""
    write("/acipayam-dunu-bugunu/", layout("/acipayam-dunu-bugunu/", d["title"], body, desc=d["intro"][0] if d["intro"] else ""))


def build_radyo():
    r = J("radyo.json")
    items = "".join(
        f'<li class="rec"><span class="rec-n">{i + 1:02d}</span><div><h2>{E(x["title"])}</h2><p>{E(x["person"])}</p>'
        f'<audio controls preload="none" src="{E(x["file"])}"></audio></div><time>{E(x["duration"])}</time></li>'
        for i, x in enumerate(r["records"]))
    body = f"""<article class="page-narrow">
  <p class="book-series">{E(r['eyebrow'])}</p>
  <h1>{E(r['title'])}</h1>
  {"".join(f'<p class="lead">{E(p)}</p>' for p in r['intro'])}
  <label class="search"><span>Kayıtlarda ara</span><input type="search" data-filter-list="#kayitlar" placeholder="Şiir, türkü, isim…"></label>
  <ol class="records" id="kayitlar">{items}</ol>
</article>"""
    write("/radyo-arsivi/", layout("/radyo-arsivi/", r["title"], body))


def build_sehit():
    m = J("sehitler-meta.json")
    shutil.copy(DATA / "sehitler.json", OUT / "veri" / "sehitler.json")
    body = f"""<article class="martyrs">
  <header class="martyrs-head">
    <blockquote>{"<br>".join(E(s) for s in m['slogan'][:2])}<cite>Mehmet Âkif Ersoy</cite></blockquote>
    <h1>{E(m['title'])}</h1>
    <p class="lead">{E(m['lead'])}</p>
  </header>
  <section class="finder" aria-labelledby="ara">
    <h2 id="ara">{E(m['intro_title'])}</h2>
    <p>{E(m['intro'])}</p>
    <div class="finder-tools">
      <label class="search"><span>İsim, baba adı, köy veya şehadet yeri</span><input type="search" id="q" autocomplete="off"></label>
      <label><span>Savaş</span><select id="war"><option value="">Tüm savaşlar</option></select></label>
      <label><span>İlçe</span><select id="ilce"><option value="">Tüm ilçeler</option></select></label>
    </div>
    <p class="finder-count" id="count" aria-live="polite">Kayıtlar yükleniyor…</p>
    <ol class="martyr-list" id="list"></ol>
    <button type="button" class="btn btn-line" id="more" hidden>Daha fazla göster</button>
    <p class="muted">Kaynak: <a href="{m['source']['href']}" rel="noopener">{E(m['source']['label'])}</a>. Tarihî kayıtlar özgün yazımıyla korunmuştur.</p>
  </section>
</article>"""
    write("/sehit-bilgi-kapisi/", layout("/sehit-bilgi-kapisi/", "Denizli Şehit Bilgi Kapısı", body,
                                         desc=m["lead"], cls="page-martyrs"))


def redirects():
    """Eski adresleri yeni sayfalara yönlendirir."""
    uslu = next(b for b in BOOKS if b["slug"] == "uslu-dusler")
    pairs = {"/uslu-dusler/dinle/": "/uslu-dusler/#dinle", "/uslu-dusler/giris/": chapter_url(uslu, 0, uslu["data"]["chapters"][0])}
    for src, dst in pairs.items():
        write(src, f'<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0; url={dst}">'
                   f'<link rel="canonical" href="{dst}"><title>Yönlendiriliyor</title><a href="{dst}">Devam etmek için tıklayın</a>')


def not_found():
    body = """<article class="page-narrow center"><h1>Bu sayfa bulunamadı</h1>
<p class="lead">Adres değişmiş ya da yanlış yazılmış olabilir. Kitaplığa ya da köy haritasına buradan ulaşabilirsiniz.</p>
<div class="actions"><a class="btn" href="/#kitaplik">Kitaplığa git</a><a class="btn btn-line" href="/sabit/">Köy haritası</a></div></article>"""
    (OUT / "404.html").write_text(layout("/404", "Sayfa bulunamadı", body), encoding="utf-8")


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    (OUT / "veri").mkdir()
    shutil.copytree(ROOT / "static", OUT, dirs_exist_ok=True)
    shutil.copytree(ROOT / "assets", OUT / "assets", dirs_exist_ok=True)
    (OUT / "CNAME").write_text("acipayam.gunerunal.com.tr\n")
    (OUT / ".nojekyll").write_text("")
    (OUT / "robots.txt").write_text("User-agent: *\nDisallow: /\n")
    build_home()
    for b in BOOKS:
        if b["slug"] != "bana-koyunu-anlat":
            write(b["base"], layout(b["base"], b["title"], build_book(b), desc=b["summary"]))
        for i in range(len(b["data"]["chapters"])):
            write(chapter_url(b, i, b["data"]["chapters"][i]), build_chapter(b, i))
    build_sabit()
    build_dunu()
    build_radyo()
    build_sehit()
    redirects()
    not_found()
    print(f"{len(written)} sayfa yazıldı → {OUT}")


if __name__ == "__main__":
    main()
