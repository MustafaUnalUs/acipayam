#!/usr/bin/env python3
"""Düzenlenmiş kitap PDF'lerini bölümlere ayrılmış web metnine çevirir.

Önce poppler ile konumlu XML üretilir:
    pdftohtml -xml -zoom 1.5 -fmt jpg -q kitap.pdf work/<slug>/p
Sonra:
    python3 tools/pdf2book.py <work-klasörü>

Çıktı: data/kitaplar/<slug>.json ve static/kitap/<slug>/img/*.webp
"""
import html
import json
import re
import statistics
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
WORK = Path(sys.argv[1])
OUT = ROOT / "data" / "kitaplar"
IMG_OUT = ROOT / "static" / "kitap"

# Her kitap için: içeriğin başladığı sayfa, bölüm başlığı yazı tipi kimlikleri,
# kısım (bölüm grubu) olarak sayılacak başlık kalıbı.
BOOKS = {
    "icimde-kalan-cocuk": {"start": 7, "chapter": {"18"}},
    "karanlik-odada-yedi-ay": {"start": 4, "chapter": {"18", "25"}},
    "kelekcide-yasamak": {"start": 3, "chapter": {"9"}},
    "bana-koyunu-anlat": {"start": 4, "chapter": {"14"}},
    "gonul-dostu": {"start": 6, "chapter": {"15"}, "part": r"KISIM\b|^SEÇİLMİŞ KRONOLOJİ"},
    "uslu-dusler": {"start": 3, "chapter": {"13"}},
    "uslu-dimag": {"start": 4, "chapter": {"16"}, "part_marker": "❧"},
}
SKIP_TITLES = re.compile(r"^(İÇİNDEKİLER|İçindekiler)$")

FIX = str.maketrans({"ș": "ş", "Ș": "Ş", "ț": "ţ", "\xa0": " ", "­": ""})
LIGS = {"ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl"}


def norm(s):
    s = s.translate(FIX).replace("DU RU P DÜ Ş Ü N", "Durup düşün")
    for a, b in LIGS.items():
        s = s.replace(a, b)
    return re.sub(r"[ \t]{2,}", " ", s)


def inner(el):
    """<text> içeriğini, <i>/<b> biçimlerini koruyarak HTML'e çevirir."""
    out = html.escape(el.text or "", quote=False)
    for ch in el:
        tag = {"i": "em", "b": "strong"}.get(ch.tag)
        body = inner(ch)
        out += f"<{tag}>{body}</{tag}>" if tag and body.strip() else body
        out += html.escape(ch.tail or "", quote=False)
    return norm(out)


def plain(s):
    return re.sub(r"<[^>]+>", "", html.unescape(s))


def slugify(s):
    tr = str.maketrans("çğıöşüâîûÇĞİÖŞÜÂÎÛ", "cgiosuaiuCGIOSUAIU")
    s = plain(s).translate(tr).lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:60] or "bolum"


def convert(slug, cfg):
    xml = WORK / slug / "p.xml"
    root = ET.parse(xml).getroot()
    fonts = {}
    pages = []
    for pg in root.iter("page"):
        for f in pg.iter("fontspec"):
            fonts[f.get("id")] = {"size": int(f.get("size")), "color": f.get("color")}
        pages.append(pg)

    # gövde yazı tipi = en çok karakter taşıyan
    count = {}
    for pg in pages:
        for t in pg.iter("text"):
            count[t.get("font")] = count.get(t.get("font"), 0) + len("".join(t.itertext()))
    body_font = max(count, key=count.get)
    body = fonts[body_font]["size"]

    img_dir = IMG_OUT / slug / "img"
    img_dir.mkdir(parents=True, exist_ok=True)

    chapters = []
    cur = None
    part = None
    pending_cap = ""
    para = None  # {"kind", "lines":[...], "last":(top,left,right)}

    def new_chapter(title, page_no):
        nonlocal cur
        flush()
        cur = {"title": title, "part": part, "page": page_no, "blocks": []}
        chapters.append(cur)

    def flush():
        nonlocal para
        if para and cur is not None:
            txt = ""
            for ln in para["lines"]:
                if txt.endswith("-") and ln[:1].islower() and not txt.endswith(" -"):
                    txt = txt[:-1] + ln
                elif txt:
                    txt += ("<br>" if para["kind"] == "verse" else " ") + ln
                else:
                    txt = ln
            txt = re.sub(r"\s+", " ", txt).strip()
            txt = re.sub(r"</em>(\s*)<em>", r"\1", txt).replace("</strong> <strong>", " ")
            if plain(txt).strip():
                cur["blocks"].append({"k": para["kind"], "h": txt})
        para = None

    def close_heading(page_no):
        """Biriken bölüm/kısım başlığını kapatır, gerekiyorsa yeni bölüm açar."""
        nonlocal para, part
        if not (para and para["kind"] in ("chapter", "part")):
            return
        title = " ".join(plain(l).strip() for l in para["lines"])
        kind = para["kind"]
        para = None
        if kind == "part":
            part = title
            if not re.search(r"KRONOLOJİ", title):
                return
            part = None
        new_chapter(title, page_no)
        if SKIP_TITLES.match(title):
            cur["skip"] = True

    for pg in pages:
        no = int(pg.get("number"))
        if no < cfg["start"]:
            continue
        H, W = float(pg.get("height")), float(pg.get("width"))
        items = []
        for t in pg.iter("text"):
            top = int(t.get("top"))
            if top < 0.06 * H or top > 0.925 * H:
                continue  # üst bilgi / sayfa numarası
            h = inner(t)
            if not plain(h).strip():
                continue
            items.append(("t", top, int(t.get("left")), int(t.get("width")), t.get("font"), h))
        for im in pg.iter("image"):
            w, h = int(im.get("width")), int(im.get("height"))
            if w >= 140 and h >= 100 and w < W * 0.98:
                items.append(("i", int(im.get("top")), int(im.get("left")), w, h, im.get("src")))
        # "✧" gibi satır başı işaretlerini ait oldukları satıra hizala
        texts = [x for x in items if x[0] == "t"]
        for i, x in enumerate(items):
            if x[0] == "t" and plain(x[5]).strip() in ("✧", "—"):
                near = [y for y in texts if y is not x and y[2] > x[2] and abs(y[1] - x[1]) <= 10]
                if near:
                    y = min(near, key=lambda y: abs(y[1] - x[1]))
                    items[i] = ("t", y[1], x[2], x[3], y[4], x[5].strip())
        items.sort(key=lambda x: (x[1], x[2]))

        # Aynı satırda, aynı yazı tipinde parçalanmış metinleri birleştir
        merged = []
        for x in items:
            if (x[0] == "t" and merged and merged[-1][0] == "t"
                    and (merged[-1][4] == x[4] or fonts[merged[-1][4]]["size"] == fonts[x[4]]["size"] == body)
                    and abs(merged[-1][1] - x[1]) <= 3 and x[2] >= merged[-1][2] + merged[-1][3] - 2):
                m = merged[-1]
                piece = x[5].strip()
                if x[4] != m[4] and x[4] != body_font and "<em>" not in piece:
                    piece = f"<em>{piece}</em>"
                gap = "" if x[2] - (m[2] + m[3]) < 2 and re.match(r"^[\w’']", plain(piece)) else " "
                merged[-1] = ("t", m[1], m[2], x[2] + x[3] - m[2], m[4], m[5].rstrip() + gap + piece)
            else:
                merged.append(x)
        items = merged

        body_lines = [x for x in items if x[0] == "t" and x[4] == body_font]
        base_left = min((x[2] for x in body_lines), default=0)
        right_edge = max((x[2] + x[3] for x in body_lines), default=W)
        # gövde dışı yazı tipleri için kendi kenar boşlukları
        margins = {}
        for x in items:
            if x[0] == "t":
                l, r, n = margins.get(x[4], (10**6, 0, 0))
                margins[x[4]] = (min(l, x[2]), max(r, x[2] + x[3]), n + 1)
        gaps = [b[1] - a[1] for a, b in zip(body_lines, body_lines[1:]) if 0 < b[1] - a[1] < 40]
        step = statistics.median(gaps) if gaps else body * 1.5 * 1.45

        # kısım işareti (US'lu Dimağ)
        if cfg.get("part_marker") and any(x[0] == "t" and plain(x[5]).strip() == cfg["part_marker"] for x in items):
            ttl = [x for x in items if x[0] == "t" and x[4] in cfg["chapter"]]
            if ttl:
                flush()
                part = " ".join(plain(x[5]).strip() for x in ttl)
                continue

        prev_top = None
        for x in items:
            if x[0] == "i":
                close_heading(no)
                flush()
                src = Path(x[5])
                if not src.exists():
                    src = WORK / slug / src.name
                name = f"s{no:03d}-{x[1]}.webp"
                try:
                    with Image.open(src) as im:
                        im = im.convert("RGB")
                        im.thumbnail((1400, 1400))
                        im.save(img_dir / name, "WEBP", quality=78, method=5)
                        size = im.size
                except Exception as e:  # bozuk görseli atla
                    print("  görsel atlandı:", src, e)
                    continue
                if cur is not None:
                    cur["blocks"].append({"k": "img", "src": f"/kitap/{slug}/img/{name}", "w": size[0], "ht": size[1],
                                          "bottom": x[1] + x[4]})
                prev_top = None
                continue

            _, top, left, width, font, h = x
            size = fonts[font]["size"]
            txt = plain(h).strip()

            # büyük ilk harf (drop cap)
            if len(txt) <= 2 and size >= body * 1.6 and font not in cfg["chapter"]:
                close_heading(no)
                flush()
                pending_cap = h.strip()
                prev_top = None
                continue

            if font in cfg["chapter"]:
                if txt == cfg.get("part_marker"):
                    continue
                if cfg.get("part") and re.search(cfg["part"], txt) and not (para and para["kind"] == "part"):
                    close_heading(no)
                    flush()
                    para = {"kind": "part", "lines": [h], "font": font, "top": top, "page": no}
                    continue
                if (para and para["kind"] in ("chapter", "part") and para["font"] == font
                        and para.get("page") == no and 0 <= top - para["top"] < size * 2.4):
                    para["lines"].append(h)
                    para["top"] = top
                    continue
                close_heading(no)
                flush()
                para = {"kind": "chapter", "lines": [h], "font": font, "top": top, "page": no}
                continue

            close_heading(no)

            if cur is None:
                continue

            # sayfadaki sayılar, harf aralıklı etiketler (US 4 gibi)
            if font != body_font and (re.fullmatch(r"\d{1,3}", txt) or re.fullmatch(r"(\S )+\S", txt)):
                continue

            # görsel altı yazısı
            last = cur["blocks"][-1] if cur["blocks"] else None
            if para is None and last and last["k"] == "img" and (size < body or font != body_font) and len(txt) < 140 and 0 <= top - last["bottom"] < 60 and "cap" not in last:
                last["cap"] = h
                continue

            bl, re_ = base_left, right_edge
            if font != body_font and margins.get(font, (0, 0, 0))[2] >= 2:
                bl, re_ = margins[font][0], margins[font][1]
            if re.fullmatch(r"[—–-]\s*\d{1,3}\s*[—–-]", txt) or re.search(r"üzerine kendi düşüncelerin için$", txt):
                continue
            if size >= body + 2:
                kind = "h3"
            elif size <= body - 3:
                kind = "small"
            else:
                kind = "p"
            centered = font == body_font and left > bl + 30 and abs((left - bl) - (re_ - (left + width))) < 25
            if kind == "p" and centered:
                kind = "verse"
            if font != body_font and kind == "p":
                kind = "alt"

            if pending_cap:
                h = pending_cap + h.lstrip()
                pending_cap = ""
                flush()
                para = {"kind": "p", "lines": [h], "font": font, "top": top, "left": left, "end": left + width,
                        "cap_until": top + step * 2.6}
                prev_top = top
                continue

            start_new = (
                para is None
                or para["kind"] != kind
                or para["font"] != font
                or (kind in ("p", "alt") and left > bl + 8 and left > para.get("left", 0) - 2 and not centered
                    and top > para.get("cap_until", -1)
                    and not (re.match(r"^(—|–|✧)", plain(para["lines"][0]).strip()) and left > para.get("left", 0) + 4))
                or (not para.get("cont") and (top - para["top"]) > step * 1.45)
                or (not para.get("cont") and (top - para["top"]) < 0)
                or re.match(r"^(—|–|✧|-\s)", txt)
                or (not para.get("cont") and kind in ("p", "alt") and para.get("end", 0) < re_ - 60
                    and re.search(r"[.!?…:”\"»)]$", plain(para["lines"][-1]).strip()))
            )
            if kind == "h3" and para and para["kind"] == "h3" and 0 <= top - para["top"] < size * 2.2:
                start_new = False
            if kind == "verse" and para and para["kind"] == "verse" and 0 <= top - para["top"] < step * 1.45:
                start_new = False
            if start_new:
                flush()
                para = {"kind": kind, "lines": [h], "font": font, "top": top, "left": left, "end": left + width}
            else:
                para["lines"].append(h)
                para["cont"] = False
                para["top"] = top
                para["end"] = left + width
            prev_top = top
        # sayfa sonu: cümle bitmediyse paragraf sonraki sayfada devam eder
        if para and para["kind"] not in ("chapter", "part"):
            if para["kind"] in ("p", "alt") and not re.search(r"[.!?…:”\"»)]$", plain(para["lines"][-1]).strip()):
                para["cont"] = True
            else:
                flush()
    flush()

    # sayfa geçişinde devam eden paragraflar için düzeltme yapıldı; şimdi JSON
    out = []
    used = set()
    for c in chapters:
        if c.get("skip"):
            continue
        s = slugify(c["title"])
        base, i = s, 2
        while s in used:
            s, i = f"{base}-{i}", i + 1
        used.add(s)
        blocks = [{k: v for k, v in b.items() if k != "bottom"} for b in c["blocks"]]
        # süs işaretleri ve görselin üstündeki alt yazılar
        tidy = []
        for b in blocks:
            t = plain(b.get("h", "")).strip()
            if b["k"] != "img" and t in ("❧", "•", "·", "* * *", "***"):
                tidy.append({"k": "orn"})
                continue
            if b["k"] == "img" and not b.get("cap") and tidy and tidy[-1]["k"] == "small":
                b["cap"] = tidy.pop()["h"]
            tidy.append(b)
        while tidy and tidy[0]["k"] == "orn":
            tidy.pop(0)
        blocks = tidy
        out.append({"title": c["title"], "slug": s, "part": c["part"], "page": c["page"], "blocks": blocks,
                    "words": sum(len(plain(b.get("h", "")).split()) for b in blocks)})
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{slug}.json").write_text(json.dumps({"slug": slug, "chapters": out}, ensure_ascii=False, indent=1),
                                      encoding="utf-8")
    print(f"{slug}: {len(out)} bölüm, {sum(c['words'] for c in out)} kelime, "
          f"{sum(1 for c in out for b in c['blocks'] if b['k'] == 'img')} görsel")


if __name__ == "__main__":
    only = sys.argv[2:] or list(BOOKS)
    for slug in only:
        convert(slug, BOOKS[slug])
