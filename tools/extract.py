#!/usr/bin/env python3
"""acipayam.com'un yerel kopyasından (tools/fetch.sh) içerik ve veri çıkarır.

Çıktılar:
  data/*.json         yapılandırılmış veri (kitaplar, köyler, şehitler, radyo...)
  data/images.json    sitede kullanılan görsellerin listesi (build.py kopyalar)

Kullanım:  python3 tools/extract.py <mirror-klasörü>
"""
import json
import re
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse, parse_qs

from bs4 import BeautifulSoup, NavigableString, Comment

ORIGIN = "https://acipayam.com/"
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
MIRROR = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "mirror"

MEDIA_EXT = (".mp3", ".pdf", ".m4a", ".wav", ".mp4", ".zip")
IMG_EXT = (".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg")
KEEP_CLASSES = {"prose", "human", "bro", "emphasis", "dedication"}
KEEP_TAGS = {
    "h2", "h3", "h4", "p", "em", "strong", "b", "i", "a", "ul", "ol", "li",
    "table", "thead", "tbody", "tr", "th", "td", "blockquote", "figure",
    "figcaption", "img", "time", "br", "dl", "dt", "dd", "small", "audio",
    "sup", "sub", "hr", "cite", "q", "abbr",
}
DROP_TAGS = {"script", "style", "svg", "button", "dialog", "form", "input",
             "select", "label", "noscript", "link", "meta", "source", "textarea"}

images = {}  # mutlak url -> {"src": ..., "alt": ...}


def soup(rel):
    path = MIRROR / rel
    return BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser"), urljoin(ORIGIN, rel.replace("index.html", ""))


def text(el):
    if el is None:
        return ""
    return re.sub(r"\s+", " ", el.get_text(" ", strip=True)).replace(" ,", ",").replace(" .", ".").strip()


def inner_text_lines(el):
    """<br> ve satır öğelerini koruyarak metni döndürür."""
    for br in el.find_all("br"):
        br.replace_with("\n")
    return [re.sub(r"\s+", " ", t).strip() for t in el.get_text("\n").split("\n") if t.strip()]


def img_ref(url, alt=""):
    """Görseli listeye ekler, sitedeki yeni yolunu döndürür."""
    url = url.split("?")[0]
    name = Path(urlparse(url).path).stem
    folder = Path(urlparse(url).path).parent.name
    key = re.sub(r"[^a-z0-9-]+", "-", f"{folder}-{name}".lower()).strip("-")
    if folder in ("img", "assets", ""):
        key = re.sub(r"[^a-z0-9-]+", "-", name.lower()).strip("-")
    ext = ".svg" if url.endswith(".svg") else ".webp"
    new = f"/img/{key}{ext}"
    images[url] = {"out": new, "alt": alt}
    return new


def link(href, base):
    """Bağlantıyı yeni siteye göre yeniden yazar."""
    if not href or href.startswith(("mailto:", "tel:", "#", "javascript:")):
        return href
    absu = urljoin(base, href)
    u = urlparse(absu)
    if u.netloc in ("acipayam.com", "www.acipayam.com"):
        path = u.path
        if path.lower().endswith(MEDIA_EXT):
            return absu  # büyük dosyalar orijinal sunucudan
        if path.lower().endswith(IMG_EXT):
            return img_ref(absu)
        if not path.endswith("/") and "." not in Path(path).name:
            path += "/"
        return path + (f"#{u.fragment}" if u.fragment else "")
    return absu


def media(href, base):
    return urljoin(base, href) if href else None


def youtube_id(src):
    if not src:
        return None
    m = re.search(r"(?:embed/|youtu\.be/|v=)([\w-]{11})", src)
    return m.group(1) if m else None


def clean(el, base):
    """Bir içerik bölümünü sınıfsız, sade HTML'e çevirir."""
    el = BeautifulSoup(str(el), "html.parser")
    for c in el.find_all(string=lambda s: isinstance(s, Comment)):
        c.extract()
    for t in el.find_all("iframe"):
        vid = youtube_id(t.get("src"))
        if vid:
            new = el.new_tag("div")
            new["class"] = "yt"
            new["data-id"] = vid
            new["data-title"] = t.get("title", "Video")
            t.replace_with(new)
        else:
            t.decompose()
    for t in el.find_all("audio"):
        src = t.get("src") or (t.find("source") or {}).get("src")
        if src:
            new = el.new_tag("audio", controls="", preload="none", src=media(src, base))
            t.replace_with(new)
        else:
            t.decompose()
    for t in el.find_all(DROP_TAGS):
        t.decompose()
    for t in el.find_all(True):
        if t.name == "div" and "yt" in (t.get("class") or []):
            continue
        if t.name not in KEEP_TAGS:
            t.unwrap()
            continue
        attrs = {}
        if t.name == "a" and t.get("href"):
            attrs["href"] = link(t["href"], base)
            if attrs["href"] and attrs["href"].startswith("http") and "acipayam.com" not in attrs["href"]:
                attrs["rel"] = "noopener"
        if t.name == "img":
            src = t.get("src")
            if not src or src.startswith("data:"):
                t.decompose()
                continue
            attrs["src"] = img_ref(urljoin(base, src), t.get("alt", ""))
            attrs["alt"] = t.get("alt", "")
            attrs["loading"] = "lazy"
        if t.name == "audio":
            attrs = dict(t.attrs)
        if t.name in ("td", "th") and t.get("colspan"):
            attrs["colspan"] = t["colspan"]
        cls = [c for c in (t.get("class") or []) if c in KEEP_CLASSES]
        if cls:
            attrs["class"] = " ".join(cls)
        t.attrs = attrs
    out = str(el)
    out = re.sub(r"[ \t]*\n\s*\n+", "\n", out)
    return out.strip()


def write(name, obj):
    (DATA / name).write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")
    print("yazıldı:", name)


# ---------------------------------------------------------------- ana sayfa
def home():
    s, base = soup("index.html")
    out = {}
    out["banner"] = img_ref(urljoin(base, s.select_one(".heritage-banner img")["src"]),
                            s.select_one(".heritage-banner img").get("alt", ""))
    books = []
    for card in s.select(".projects .project-card"):
        acts = {}
        for a in card.select(".book-card-actions a"):
            kind = [c for c in a["class"] if c.startswith("action-")][0][7:]
            acts[kind] = link(a["href"], base)
        img = card.select_one("img")
        books.append({
            "title": text(card.select_one("h3")),
            "author": text(card.select_one(".project-by")),
            "summary": text(card.select_one(".book-summary")),
            "cover": img_ref(urljoin(base, img["src"]), img.get("alt", "")),
            "href": link(card.select_one("a")["href"], base),
            "actions": acts,
        })
    out["books"] = books
    feat = s.select_one(".latest-feature")
    out["latest"] = {
        "title": text(feat.select_one("h3")),
        "paragraphs": [clean(p, base) for p in feat.select(".featured-copy p")],
        "back": img_ref(urljoin(base, feat.select_one(".cover-preview-button img")["src"])),
    }
    upcoming = []
    for u in s.select(".upcoming-feature"):
        imgs = [img_ref(urljoin(base, i["src"]), i.get("alt", "")) for i in u.select("img")]
        ps = u.select(".featured-copy p")
        upcoming.append({
            "title": text(u.select_one("h3")),
            "status": text(u.select_one(".status-upcoming")),
            "tagline": text(ps[0]) if ps else "",
            "paragraphs": [text(p) for p in ps[1:] if not p.find("em")],
            "images": imgs,
        })
    out["upcoming"] = upcoming
    h = s.select_one(".history-feature")
    out["history"] = {
        "label": text(h.select_one(".project-live")),
        "title": text(h.select_one("h2")),
        "by": text(h.select_one(".project-by")),
        "text": text(h.select("p")[-1]),
        "image": img_ref(urljoin(base, h.select_one("img")["src"]), h.select_one("img").get("alt", "")),
    }
    r = s.select_one(".radio-archive-card")
    out["radio"] = {"kicker": text(r.select_one("p")), "title": text(r.select_one("h2")),
                    "text": text(r.select_one(".radio-archive-copy > span"))}
    st = s.select_one(".story-panel")
    out["story"] = {
        "kicker": text(st.select_one(".story-kicker")),
        "title": text(st.select_one("h2")),
        "lead": text(st.select_one(".story-lead")),
        "body": clean(BeautifulSoup("".join(str(x) for x in st.select_one(".story-panel-body").children
                                            if getattr(x, "get", None) is None or "story-signature" not in (x.get("class") or [])), "html.parser"), base),
        "signature": inner_text_lines(st.select_one(".story-signature")),
        "highlights": [text(p) for p in st.select(".story-highlight")],
        "motto": text(st.select_one(".story-motto")),
    }
    ap = s.select_one(".april-archive")
    out["april"] = {
        "kicker": text(ap.select_one(".section-kicker")),
        "title": text(ap.select_one("h2")),
        "intro": text(ap.select_one(".intro")),
        "items": [{"year": text(i.select_one("time")), "title": text(i.select_one("b")),
                   "text": text(i.select_one("p"))} for i in ap.select(".april-item")],
        "feature": {
            "title": text(ap.select_one(".april-feature h3")),
            "text": text(ap.select(".april-feature p")[-1]),
            "links": [{"label": text(a), "href": a["href"]} for a in ap.select(".source-links a")],
        },
    }
    out["videos"] = [{"id": b["data-youtube-id"], "title": b.get("aria-label", text(b))
                      .replace(" videosunu oynat", "").replace("videosunu oynat", "").strip()}
                     for b in s.select("[data-youtube-id]")]
    m = s.select_one(".memorial-feature")
    out["memorial"] = {"kicker": text(m.select_one(".memorial-kicker")), "title": text(m.select_one("h2")),
                       "text": text(m.select_one("p")), "stat": text(m.select_one(".memorial-stat strong")),
                       "stat_label": text(m.select_one(".memorial-stat span"))}
    out["contacts"] = [{"label": text(a.select_one("b")), "value": text(a.select_one(".tx > span")),
                        "href": a["href"]} for a in s.select(".contact-card")]
    out["sisters"] = [{"group": text(g.select_one("h3")),
                       "links": [{"label": text(a), "href": a["href"]} for a in g.select("a")]}
                      for g in s.select(".sister-group")]
    out["sisters_intro"] = text(s.select_one(".sister-directory").find_previous("p"))
    write("home.json", out)


# ---------------------------------------------------------------- kitap sayfaları
def book_pages():
    out = {}
    # İçimde Kalan Çocuk
    s, base = soup("icimde-kalan-cocuk/index.html")
    hero = s.select_one(".std-book-copy")
    imgs = s.select(".std-cover-stage img")
    out["icimde-kalan-cocuk"] = {
        "eyebrow": text(hero.select_one(".std-eyebrow")),
        "title": text(hero.select_one("h1")),
        "intro": text(hero.select_one(".std-intro")),
        "badge": text(hero.select_one(".std-badge")),
        "covers": [img_ref(urljoin(base, i["src"]), i.get("alt", "")) for i in imgs],
        "pdf": media(hero.select_one(".std-pdf")["href"], base),
        "audio_full": ORIGIN + "icimde-kalan-cocuk/Icimde_Kalan_Cocuk_SESLI_KITAP_Onyx_Yuzde_10_Hizli.mp3",
        "audio_intro": text(s.select_one("#sesli-kitap p")),
        "chapters_audio_base": ORIGIN + "icimde-kalan-cocuk/bolumler/",
        "sections": [{"title": text(sec.select_one("h2")),
                      "html": clean(BeautifulSoup("".join(str(p) for p in sec.find_all(recursive=False) if p.name != "h2"), "html.parser"), base)}
                     for sec in s.select(".std-detail") if sec.get("id") != "sesli-kitap"],
    }
    man = MIRROR.parent / "data-raw" / "icimde-kalan-cocuk-bolumler.json"
    if man.exists():
        out["icimde-kalan-cocuk"]["tracks"] = json.loads(man.read_text(encoding="utf-8"))["tracks"]

    # Karanlık Odada Yedi Ay
    s, base = soup("karanlik-odada-yedi-ay/index.html")
    hero = s.select_one(".std-book-copy")
    card = s.select_one("section.card")
    out["karanlik-odada-yedi-ay"] = {
        "eyebrow": text(hero.select_one(".std-eyebrow")),
        "title": text(hero.select_one("h1")),
        "intro": text(hero.select_one(".std-intro")),
        "badge": text(hero.select_one(".std-badge")),
        "covers": [img_ref(urljoin(base, i["src"]), i.get("alt", "")) for i in s.select(".std-cover-stage img")],
        "pdf": media(hero.select_one(".std-pdf")["href"], base),
        "audio_full": media(card.select_one("audio source")["src"], base),
        "sections": [{"title": text(card.select_one("h2")),
                      "html": clean(BeautifulSoup("".join(str(p) for p in card.select("h2")[0].find_next_siblings("p", limit=20)
                                                          if p.find_previous("h2") == card.select("h2")[0]), "html.parser"), base)}],
    }

    # Kelekçi'de Yaşamak
    s, base = soup("kelekcide-yasamak/index.html")
    t = s.select_one(".text-col")
    out["kelekcide-yasamak"] = {
        "eyebrow": text(t.select_one(".eyebrow")),
        "title": text(t.select_one("h1")),
        "byline": text(t.select_one(".by-line")),
        "intro": text(t.select_one(".lead")),
        "badge": " · ".join(inner_text_lines(s.select_one(".cover-meta"))),
        "covers": [img_ref(urljoin(base, s.select_one(".cover-col img")["src"]))],
        "pdf": media(t.select_one(".btn-pdf")["href"], base),
        "audio_full": media(t.select_one("audio source")["src"], base),
        "quote": text(t.select_one(".quote")),
        "meta": text(t.select_one(".meta-note")),
        "sections": [{"title": text(sec.select_one("h2")),
                      "html": clean(BeautifulSoup("".join(str(p) for p in sec.find_all(recursive=False) if p.name != "h2"), "html.parser"), base)}
                     for sec in s.select("section.detail")],
    }
    write("book-pages.json", out)


# ---------------------------------------------------------------- US'lu Düşler
def uslu():
    s, base = soup("uslu-dusler/index.html")
    hero = s.select_one(".std-book-copy")
    ov = s.select_one(".overview")
    data = {
        "eyebrow": text(hero.select_one(".std-eyebrow")),
        "title": text(hero.select_one("h1")),
        "intro": text(hero.select_one(".std-intro")),
        "badge": text(hero.select_one(".std-badge")),
        "covers": [img_ref(urljoin(base, i["src"]), i.get("alt", "")) for i in s.select(".std-cover-stage img")],
        "pdf": ORIGIN + "uslu-dusler/assets/USLU_DUSLER_SON.pdf",
        "audio_full": ORIGIN + "uslu-dusler/assets/USLU_DUSLER_TAM_SESLI_KITAP.mp3",
        "overview_title": inner_text_lines(ov.select_one("h2")),
        "overview": [text(p) for p in ov.select("div > p")],
        "chapters": [],
    }
    s, base = soup("uslu-dusler/giris/index.html")
    data["giris"] = {"title": text(s.select_one(".reading-head h1")),
                     "eyebrow": text(s.select_one(".reading-head .eyebrow")),
                     "html": clean(s.select_one("article.book-text"), base)}
    for d in sorted((MIRROR / "uslu-dusler" / "bolum").iterdir()):
        s, base = soup(f"uslu-dusler/bolum/{d.name}/index.html")
        data["chapters"].append({
            "num": d.name,
            "title": text(s.select_one(".reading-head h1")),
            "html": clean(s.select_one("article.book-text"), base),
        })
    s, base = soup("uslu-dusler/dinle/index.html")
    data["listen"] = {"title": inner_text_lines(s.select_one(".reading-head h1")),
                      "duration": text(s.select_one(".player-label")).split()[-1],
                      "note": text(s.select_one(".listen-note"))}
    write("uslu-dusler.json", data)


# ---------------------------------------------------------------- Bana Köyünü Anlat
def sabit():
    s, base = soup("sabit/index.html")
    k = s.select_one("#kitap")
    data = {
        "title": text(k.select_one("h2")),
        "lead": text(k.select_one(".section-lead")),
        "qr_note": text(k.select_one(".qr-note")),
        "pdf": ORIGIN + "sabit/downloads/Bana_Koyunu_Anlat_Sabit_Kizilhan.pdf",
        "audio_full": ORIGIN + "sabit/downloads/bana-koyunu-anlat-sesli-kitap.mp3",
        "cover": img_ref(urljoin(base, k.select_one("img")["src"]), k.select_one("img").get("alt", "")),
        "editor": {"name": text(k.select_one(".editor-name")), "role": text(k.select_one(".editor-role")),
                   "note": text(k.select_one(".editor-note")),
                   "links": [a["href"] for a in k.select(".social-row a")]},
        "map": img_ref(urljoin(base, s.select_one(".map-bg")["src"]), "Acıpayam haritası"),
        "map_title": inner_text_lines(s.select_one(".mosaic-h1")),
        "pins": [],
        "themes": [{"icon": text(c.select_one(".t-icon")), "title": text(c.select_one("h3")),
                    "text": text(c.select_one("p"))} for c in s.select("#temalar .t-card")],
        "themes_title": text(s.select_one("#temalar h2")),
        "themes_lead": text(s.select_one("#temalar .section-lead")),
        "villages_title": text(s.select_one("#koyler h2")),
        "villages_lead": text(s.select_one("#koyler .section-lead")),
        "villages": [{"name": text(v), "href": link(v["href"], base) if v.name == "a" else None}
                     for v in s.select("#koyler .v-chip")],
        "interviews": [],
    }
    for a in s.select(".map-dot"):
        st = dict(x.split(":") for x in a["style"].replace(" ", "").strip(";").split(";"))
        data["pins"].append({"name": a.get("data-name") or text(a), "href": link(a.get("href"), base) if a.get("href") else None, "video": a.get("data-video"),
                             "left": st["left"], "top": st["top"], "big": "map-dot-big" in a["class"]})
    # dizin
    s2, base2 = soup("sabit/kizilhan/index.html")
    data["index_title"] = text(s2.select_one("h1"))
    data["index_lead"] = text(s2.select_one("h1").find_next("p"))
    for tr in s2.select("table.idx-table tbody tr"):
        href = link(tr.select_one(".c-village a")["href"], base2)
        slug = href.strip("/").split("/")[-1]
        p, b = soup(f"sabit/{slug}/index.html")
        content = p.select_one("article.i-content")
        extra = []
        for rv in content.select("section.reviewed-video"):
            extra.append(clean(rv, b))
            rv.decompose()
        vid = p.select_one(".video-wrap iframe")
        data["interviews"].append({
            "no": text(tr.select_one(".c-no")),
            "slug": slug,
            "village": text(tr.select_one(".c-village")),
            "people": text(tr.select_one(".c-people")),
            "eyebrow": text(p.select_one(".eyebrow")),
            "title": text(p.select_one(".i-title")),
            "subtitle": text(p.select_one(".i-subtitle")),
            "video": youtube_id(vid["src"]) if vid else None,
            "html": clean(content, b),
            "extra": extra,
        })
    # sözlük
    s3, base3 = soup("sabit/sozluk/index.html")
    first = s3.select("body > section")
    data["glossary"] = {
        "title": text(s3.select_one("h1")),
        "lead": text(s3.select_one("h1").find_next("p")),
        "sections": [],
    }
    for h in s3.select("h2.g-section-title"):
        tbl = h.find_next("table")
        rows = [[text(td) for td in tr.select("td")] for tr in tbl.select("tbody tr")]
        head = [text(th) for th in tbl.select("thead th")]
        notes = []
        for sib in h.find_next_siblings():
            if sib.name == "h2":
                break
        data["glossary"]["sections"].append({"title": text(h), "head": head, "rows": rows})
    tail = [clean(p, base3) for p in s3.select("body > section p") if p.find_parent("table") is None][1:]
    data["glossary"]["notes"] = tail
    write("sabit.json", data)


# ---------------------------------------------------------------- Acıpayam Dünü Bugünü
def dunu_bugunu():
    s, base = soup("acipayam-dunu-bugunu/index.html")
    head = s.select_one("h1")
    data = {
        "title": text(head),
        "intro": [text(p) for p in head.find_all_next("p", limit=3) if not p.find_parent(class_="episode")][:2],
        "image": img_ref(urljoin(base, s.select_one("img[src*=hikmet]")["src"]), "Hikmet Başaran"),
        "editor_note": text(s.find(string=re.compile("Editörün notu")).find_parent("p")) if s.find(string=re.compile("Editörün notu")) else "",
        "episodes": [],
    }
    for ep in s.select("section.episode"):
        vid = youtube_id(ep.select_one("iframe")["src"])
        blocks = []
        for b in ep.select(".transcript-block"):
            a = b.select_one("a.timecode")
            sec = int(parse_qs(urlparse(a["href"]).query).get("t", ["0s"])[0].rstrip("s"))
            blocks.append({"t": sec, "label": text(a.select_one(".timecode-value")),
                           "text": " ".join(text(p) for p in b.select("p"))})
        data["episodes"].append({"id": ep.get("id"), "no": text(ep.select_one(".episode-no")),
                                 "title": text(ep.select_one("h2")), "sub": text(ep.select_one(".episode-sub")),
                                 "video": vid, "blocks": blocks})
    write("acipayam-dunu-bugunu.json", data)


# ---------------------------------------------------------------- radyo
def radyo():
    s, base = soup("radyo-arsivi/index.html")
    js = next(MIRROR.glob("radyo-arsivi/assets/tum-kayitlar.js*")).read_text(encoding="utf-8")
    recs = []
    for m in re.finditer(r"\{([^}]*)\}", js):
        d = dict(re.findall(r'(\w+):\s*"((?:[^"\\]|\\.)*)"', m.group(1)))
        d["file"] = ORIGIN + "radyo-arsivi/" + d["file"]
        recs.append(d)
    write("radyo.json", {
        "title": text(s.select_one("h1")),
        "eyebrow": text(s.select_one(".intro .eyebrow")),
        "intro": [text(p) for p in s.select(".intro p:not(.eyebrow)")],
        "records": recs,
    })


# ---------------------------------------------------------------- şehitler
def sehitler():
    s, base = soup("sehit-bilgi-kapisi/index.html")
    js = "".join(sc.string or "" for sc in s.find_all("script"))
    header = json.loads(re.search(r"const HEADER\s*=\s*(\[.*?\]);", js, re.S).group(1))
    records = json.loads(re.search(r"const RECORDS\s*=\s*(\[.*?\]);\s*\n", js, re.S).group(1))
    slogan = inner_text_lines(s.select_one(".hero .slogan"))
    meta = {
        "slogan": slogan,
        "title": text(s.select_one(".hero h1")),
        "lead": text(s.select_one(".hero p")),
        "intro_title": text(s.select_one(".archive-intro h2")),
        "intro": text(s.select_one(".archive-intro p")),
        "source": {"label": "MSB Şehit Bilgi Kapısı", "href": "https://www.msb.gov.tr/SehitBilgiKapisi/SehitListesi"},
        "count": len(records),
    }
    write("sehitler-meta.json", meta)
    (DATA / "sehitler.json").write_text(json.dumps({"h": header, "r": records}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("yazıldı: sehitler.json", len(records), "kayıt")


def sohbet():
    raw = MIRROR.parent / "data-raw" / "mini-sohbet.json"
    if raw.exists():
        write("sohbet.json", json.loads(raw.read_text(encoding="utf-8")))


if __name__ == "__main__":
    DATA.mkdir(exist_ok=True)
    for fn in (home, book_pages, uslu, sabit, dunu_bugunu, radyo, sehitler, sohbet):
        fn()
    write("images.json", images)


def copy_images():
    """Görselleri yerel kopyadan alıp static/img altına webp olarak yazar."""
    from PIL import Image
    out = ROOT / "static"
    for url, info in images.items():
        src = MIRROR / urlparse(url).path.lstrip("/")
        dst = out / info["out"].lstrip("/")
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not src.exists():
            print("  eksik görsel:", url)
            continue
        if dst.suffix == ".svg":
            dst.write_bytes(src.read_bytes())
            continue
        with Image.open(src) as im:
            im = im.convert("RGB")
            im.thumbnail((1600, 1600))
            im.save(dst, "WEBP", quality=80, method=5)


copy_images()
