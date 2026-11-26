(() => {
  "use strict";
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const store = {
    get(k) { try { return localStorage.getItem("acp:" + k); } catch { return null; } },
    set(k, v) { try { localStorage.setItem("acp:" + k, v); } catch { /* yok say */ } },
  };
  const trLower = (s) => (s || "").toLocaleLowerCase("tr-TR");

  // Menü: geniş ekranda hep açık
  const menu = $(".menu");
  const mq = matchMedia("(min-width: 900px)");
  const syncMenu = () => { if (menu) menu.open = mq.matches; };
  syncMenu(); mq.addEventListener?.("change", syncMenu);

  // YouTube: tıklanınca yükle
  document.addEventListener("click", (e) => {
    const btn = e.target.closest(".yt button");
    if (!btn) return;
    const box = btn.parentElement;
    const f = document.createElement("iframe");
    f.src = `https://www.youtube-nocookie.com/embed/${box.dataset.id}?autoplay=1&rel=0`;
    f.title = btn.getAttribute("aria-label") || "Video";
    f.allow = "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture";
    f.allowFullscreen = true;
    box.replaceChildren(f);
    f.focus();
  });

  // Kapak çevirme
  $$("[data-flip]").forEach((fig) => {
    const btn = $("[data-flip-btn]", fig);
    if (!btn) return;
    btn.addEventListener("click", () => {
      const on = fig.classList.toggle("flipped");
      btn.textContent = on ? "Ön kapağa dön" : "Arka kapağı çevir";
    });
  });

  // Ana sayfa vitrini: kapağın üstüne gelince kitabı öne çıkar
  const vitrin = $("[data-vitrin]");
  const raw = $("#raf-veri");
  if (vitrin && raw) {
    const books = JSON.parse(raw.textContent);
    const feat = $(".vitrin-feature", vitrin);
    let current = ($(".spine.is-on", vitrin) || {}).dataset?.book;
    const show = (slug) => {
      if (!slug || slug === current || !books[slug]) return;
      current = slug;
      const b = books[slug];
      vitrin.style.setProperty("--book", b.color);
      $$(".spine", vitrin).forEach((s) => s.classList.toggle("is-on", s.dataset.book === slug));
      const set = (k, v) => { const el = $(`[data-f="${k}"]`, feat); if (el) el.textContent = v; };
      set("series", b.series); set("title", b.title); set("author", b.author); set("summary", b.summary);
      const rd = $('[data-f="read"]', feat);
      rd.hidden = !b.read; if (b.read) rd.href = b.read;
      $('[data-f="href"]', feat).href = b.href;
      const au = $('[data-f="audio"]', feat);
      if (au) { au.hidden = !b.audio; if (b.audio) au.href = b.audio; }
      feat.classList.remove("swap");
      requestAnimationFrame(() => feat.classList.add("swap"));
    };
    $$(".spine", vitrin).forEach((s) => {
      s.addEventListener("mouseenter", () => show(s.dataset.book));
      s.addEventListener("focus", () => show(s.dataset.book));
    });
  }


  // Kapak büyütme
  const groups = $$("[data-zoom-group]");
  if (groups.length) {
    const dlg = document.createElement("dialog");
    dlg.className = "lightbox";
    dlg.setAttribute("aria-label", "Kapak");
    dlg.innerHTML = '<div class="lb-top"><p></p><button type="button" class="lb-close" aria-label="Kapat">×</button></div>' +
      '<div class="lb-stage"><img alt=""></div><div class="lb-bottom"></div>';
    document.body.append(dlg);
    const img = $(".lb-stage img", dlg), title = $(".lb-top p", dlg), bottom = $(".lb-bottom", dlg);
    let items = [], idx = 0;
    const show = (i) => {
      idx = (i + items.length) % items.length;
      const it = items[idx];
      dlg.classList.remove("zoomed");
      img.src = it.dataset.full; img.alt = it.dataset.label; title.textContent = it.dataset.label;
      $$("button:not([data-step]):not([data-zoomtoggle])", bottom).forEach((b, j) => b.setAttribute("aria-pressed", String(j === idx)));
    };
    groups.forEach((g) => $$(".zoom", g).forEach((btn, i) => btn.addEventListener("click", () => {
      items = $$(".zoom", g);
      const many = items.length > 4;
      bottom.innerHTML = (many ? '<button type="button" data-step="-1">‹ Önceki</button><button type="button" data-step="1">Sonraki ›</button>'
        : items.map((it) => `<button type="button">${it.querySelector("span").textContent}</button>`).join("")) +
        '<button type="button" data-zoomtoggle>Yakınlaştır</button>';
      $$("button", bottom).forEach((b, j) => b.addEventListener("click", () => {
        if (b.dataset.step) { show(idx + Number(b.dataset.step)); return; }
        if (b.hasAttribute("data-zoomtoggle")) { dlg.classList.toggle("zoomed"); b.textContent = dlg.classList.contains("zoomed") ? "Sığdır" : "Yakınlaştır"; }
        else show(j);
      }));
      show(i);
      dlg.showModal();
    })));
    img.addEventListener("click", () => {
      dlg.classList.toggle("zoomed");
      const t = $("[data-zoomtoggle]", bottom); if (t) t.textContent = dlg.classList.contains("zoomed") ? "Sığdır" : "Yakınlaştır";
    });
    $(".lb-close", dlg).addEventListener("click", () => dlg.close());
    dlg.addEventListener("click", (e) => { if (e.target === dlg || e.target.classList.contains("lb-stage")) dlg.close(); });
    dlg.addEventListener("keydown", (e) => {
      if (e.key === "ArrowRight") show(idx + 1);
      if (e.key === "ArrowLeft") show(idx - 1);
    });
  }

  // Okuma: yazı boyutu, ilerleme, kaldığın yer
  const reader = $(".reader");
  if (reader) {
    const root = document.documentElement;
    let size = Number(store.get("size")) || 0;
    const apply = () => root.style.setProperty("--read", `${1.3 + size * 0.0625}rem`);
    apply();
    $$("[data-size]").forEach((b) => b.addEventListener("click", () => {
      size = Math.max(-2, Math.min(5, size + Number(b.dataset.size)));
      store.set("size", size); apply();
    }));
    const bar = $(".progress span");
    const onScroll = () => {
      const h = document.documentElement.scrollHeight - innerHeight;
      if (bar) bar.style.width = `${h > 0 ? Math.min(100, (scrollY / h) * 100) : 0}%`;
    };
    addEventListener("scroll", onScroll, { passive: true }); onScroll();
    if (reader.dataset.book) store.set("last:" + reader.dataset.book, location.pathname);
  }

  // Parça listeleri: alttaki tek oynatıcıda çal
  let dock;
  const play = (btn) => {
    if (!dock) {
      dock = document.createElement("div");
      dock.className = "player-dock";
      dock.innerHTML = '<p></p><audio controls preload="none"></audio><button type="button" aria-label="Oynatıcıyı kapat">×</button>';
      document.body.append(dock);
      document.body.classList.add("has-dock");
      $("button", dock).addEventListener("click", () => {
        $("audio", dock).pause(); dock.remove(); dock = null; document.body.classList.remove("has-dock");
        $$("[data-track][aria-current]").forEach((b) => b.removeAttribute("aria-current"));
      });
    }
    $$("[data-track][aria-current]").forEach((b) => b.removeAttribute("aria-current"));
    btn.setAttribute("aria-current", "true");
    const a = $("audio", dock);
    a.src = btn.dataset.track;
    $("p", dock).textContent = $(".toc-t", btn)?.textContent || "";
    a.play().catch(() => {});
    a.onended = () => {
      const next = btn.closest("li")?.nextElementSibling?.querySelector("[data-track]");
      if (next) play(next);
    };
  };
  document.addEventListener("click", (e) => {
    const b = e.target.closest("[data-track]");
    if (b) play(b);
  });
  // Aynı anda tek ses
  document.addEventListener("play", (e) => {
    $$("audio").forEach((a) => { if (a !== e.target) a.pause(); });
  }, true);

  // Tablo ve liste süzgeçleri
  $$("[data-filter]").forEach((inp) => inp.addEventListener("input", () => {
    const q = trLower(inp.value.trim());
    $$("table[data-filterable] tbody tr").forEach((tr) => { tr.hidden = q && !trLower(tr.textContent).includes(q); });
  }));
  $$("[data-filter-list]").forEach((inp) => inp.addEventListener("input", () => {
    const q = trLower(inp.value.trim());
    $$(`${inp.dataset.filterList} > li`).forEach((li) => { li.hidden = q && !trLower(li.textContent).includes(q); });
  }));

  // Şehit Bilgi Kapısı
  const list = $("#list");
  if (list && document.body.classList.contains("page-martyrs")) {
    const q = $("#q"), war = $("#war"), ilce = $("#ilce"), count = $("#count"), more = $("#more");
    const PAGE = 60;
    let H = [], R = [], hits = [], shown = PAGE;
    const idx = (name) => H.indexOf(name);
    const v = (r, name) => { const x = r[idx(name)]; return x && x !== "-" ? x : ""; };
    const esc = (s) => s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
    const fill = (sel, name) => {
      const counts = {};
      R.forEach((r) => { const x = v(r, name); if (x) counts[x] = (counts[x] || 0) + 1; });
      Object.keys(counts).sort((a, b) => a.localeCompare(b, "tr")).forEach((k) => {
        const o = document.createElement("option"); o.value = k; o.textContent = `${k} (${counts[k]})`; sel.append(o);
      });
    };
    const render = () => {
      const t = trLower(q.value.trim());
      hits = R.filter((r) => (!war.value || v(r, "HARP") === war.value) && (!ilce.value || v(r, "İLÇE") === ilce.value)
        && (!t || trLower(r.join(" ")).includes(t)));
      const fields = ["BABA ADI", "LAKABI", "DOĞUM TARİHİ", "İLÇE", "MAHALLE - KÖY", "SINIF", "RÜTBE", "CEPHE", "ŞEHADET TARİHİ", "ŞEHADET YERİ", "BİRLİK", "KOLORDU", "FIRKA", "ALAY", "TABUR", "BÖLÜK"];
      list.innerHTML = hits.slice(0, shown).map((r) => {
        const place = [v(r, "MAHALLE - KÖY"), v(r, "İLÇE")].filter(Boolean).join(", ") || "Denizli";
        const dl = fields.map((f) => v(r, f) ? `<dt>${esc(f.charAt(0) + trLower(f.slice(1)))}</dt><dd>${esc(v(r, f))}</dd>` : "").join("");
        return `<li><details><summary><b>${esc(v(r, "AD SOYAD"))}</b><span>${esc(place)}</span><span class="war">${esc(v(r, "HARP"))}${v(r, "ŞEHADET TARİHİ") ? " · " + esc(v(r, "ŞEHADET TARİHİ")) : ""}</span></summary><dl>${dl}</dl></details></li>`;
      }).join("");
      count.textContent = hits.length === R.length ? `${R.length.toLocaleString("tr-TR")} kaydın tamamı` :
        hits.length ? `${hits.length.toLocaleString("tr-TR")} kayıt bulundu` : "Bu aramayla eşleşen kayıt yok. Yazımı değiştirmeyi ya da süzgeçleri kaldırmayı deneyin.";
      more.hidden = hits.length <= shown;
    };
    const restart = () => { shown = PAGE; render(); };
    fetch("/veri/sehitler.json").then((r) => r.json()).then((d) => {
      H = d.h; R = d.r;
      fill(war, "HARP"); fill(ilce, "İLÇE"); render();
    }).catch(() => { count.textContent = "Kayıtlar yüklenemedi. Sayfayı yenileyin."; });
    q.addEventListener("input", restart); war.addEventListener("change", restart); ilce.addEventListener("change", restart);
    more.addEventListener("click", () => { shown += PAGE; render(); });
  }
})();

// Canlı Mini Sohbet (acipayam.com/api/mini-sohbet, eski Worker)
(() => {
  const list = document.getElementById("chat-list");
  const form = document.getElementById("chat-form");
  if (!list || !form) return;
  const status = document.getElementById("chat-status");
  const fmt = (v) => { try { return new Intl.DateTimeFormat("tr-TR", { day: "numeric", month: "short", year: "numeric" }).format(new Date(v)); } catch { return ""; } };
  const render = (msgs) => {
    list.replaceChildren();
    if (!msgs.length) { const li = document.createElement("li"); li.textContent = "İlk selamı siz bırakın."; list.append(li); return; }
    msgs.forEach((m) => {
      const li = document.createElement("li");
      const q = document.createElement("blockquote"); q.textContent = m.message;
      const p = document.createElement("p"); const b = document.createElement("b"); b.textContent = m.name;
      p.append(b, document.createTextNode([m.hometown, fmt(m.created_at)].filter(Boolean).map((x) => " · " + x).join("")));
      li.append(q, p); list.append(li);
    });
  };
  const load = async () => {
    try {
      const r = await fetch("/api/mini-sohbet", { cache: "no-store" });
      if (!r.ok) throw new Error();
      render(((await r.json()).messages) || []);
    } catch { list.innerHTML = "<li><p>Mini Sohbet şu an yüklenemedi. Biraz sonra yeniden deneyin.</p></li>"; }
  };
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const btn = form.querySelector("button"); btn.disabled = true; status.textContent = "Gönderiliyor…";
    try {
      const r = await fetch("/api/mini-sohbet", { method: "POST", headers: { "content-type": "application/json" },
        body: JSON.stringify(Object.fromEntries(new FormData(form))) });
      const d = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(d.error || "Mesaj gönderilemedi.");
      form.reset(); status.textContent = "Selamınız eklendi."; await load();
    } catch (err) { status.textContent = err.message || "Mesaj gönderilemedi; yeniden deneyin."; }
    finally { btn.disabled = false; }
  });
  load();
  setInterval(load, 60000);
})();

/* paylaş: bulunduğu adresi kullan */
document.querySelectorAll("[data-share]").forEach((a) => {
  const u = encodeURIComponent(location.href.split("#")[0]), t = encodeURIComponent(document.title);
  a.href = { wa: `https://wa.me/?text=${t}%20${u}`, fb: `https://www.facebook.com/sharer/sharer.php?u=${u}`,
             x: `https://x.com/intent/post?text=${t}&url=${u}` }[a.dataset.share];
});

/* zaman makinesi sekmeleri */
document.querySelectorAll(".zm").forEach((zm) => {
  const tabs = [...zm.querySelectorAll('[role="tab"]')];
  const pick = (t) => tabs.forEach((x) => {
    const on = x === t;
    x.setAttribute("aria-selected", on); x.tabIndex = on ? 0 : -1;
    const pnl = document.getElementById(x.getAttribute("aria-controls"));
    pnl.hidden = !on; if (on) pnl.querySelector(".zm-screen").scrollTop = 0;
  });
  tabs.forEach((t, i) => {
    t.addEventListener("click", () => pick(t));
    t.addEventListener("keydown", (e) => {
      const d = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0;
      if (d) { const n = tabs[(i + d + tabs.length) % tabs.length]; pick(n); n.focus(); }
    });
  });
});

/* koyu / açık görünüm düğmesi */
(() => {
  const b = document.getElementById("tema");
  if (!b) return;
  const root = document.documentElement;
  const meta = document.querySelector('meta[name="theme-color"]');
  b.addEventListener("click", () => {
    const t = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
    root.setAttribute("data-theme", t);
    try { localStorage.setItem("tema", t); } catch { /* yok say */ }
  });
  const mq = matchMedia("(prefers-color-scheme: dark)");
  mq.addEventListener?.("change", (e) => {
    let saved = null;
    try { saved = localStorage.getItem("tema"); } catch { /* yok say */ }
  });
  if (meta) meta.content = "#4f1f75";
})();

/* bölümler arası kolay geçiş: klavye okları, telefonda kaydırma, alttaki küçük çubuk */
(() => {
  const prevA = document.querySelector(".pager-prev, .r-pager a:not(.nx)");
  const nextA = document.querySelector(".pager-next, .r-pager a.nx");
  if (!prevA && !nextA) return;
  const go = (a) => { if (a && a.href) location.href = a.href; };
  const label = (a) => (a ? [...a.childNodes].filter((n) => n.nodeType === 3).map((n) => n.textContent).join("").trim() : "");

  // 1) Bilgisayar: ← → tuşları
  addEventListener("keydown", (e) => {
    if (e.altKey || e.ctrlKey || e.metaKey || e.shiftKey) return;
    const t = e.target;
    if (t && (t.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName))) return;
    if (document.querySelector("dialog[open]")) return;
    if (e.key === "ArrowRight") go(nextA);
    else if (e.key === "ArrowLeft") go(prevA);
  });

  // 2) Alttaki küçük geçiş çubuğu
  const pos = document.querySelector(".chap-band-in span, .r-band span");
  const bar = document.createElement("nav");
  bar.className = "gecis";
  bar.setAttribute("aria-label", "Bölüm geçişi");
  const mk = (a, cls, arrow, txt) => {
    const el = document.createElement(a ? "a" : "span");
    el.className = cls + (a ? "" : " is-off");
    if (a) { el.href = a.href; el.title = label(a); }
    el.innerHTML = cls === "g-prev" ? `<b aria-hidden="true">${arrow}</b><span>${txt}</span>` : `<span>${txt}</span><b aria-hidden="true">${arrow}</b>`;
    return el;
  };
  const mid = document.createElement("span");
  mid.className = "g-mid";
  mid.textContent = pos ? pos.textContent.replace(/^Bölüm\s*/, "") : "";
  bar.append(mk(prevA, "g-prev", "‹", "Önceki"), mid, mk(nextA, "g-next", "›", nextA && /sonu|sayfasına/i.test(nextA.textContent) ? "Kitaba dön" : "Sonraki"));
  document.body.append(bar);
  document.body.classList.add("has-gecis");

  // aşağı okurken gizlen, yukarı kaydırınca ya da sona gelince görün
  let lastY = scrollY;
  const onScroll = () => {
    const y = scrollY;
    const nearEnd = y + innerHeight > document.documentElement.scrollHeight - 600;
    bar.classList.toggle("is-hidden", y > lastY + 4 && y > 300 && !nearEnd);
    if (y < lastY - 4 || nearEnd) bar.classList.remove("is-hidden");
    lastY = y;
  };
  addEventListener("scroll", onScroll, { passive: true });

  // 3) Telefon: metni sağa/sola kaydırarak geç
  const area = document.querySelector(".reader") || document.body;
  let sx = 0, sy = 0, st = 0, ok = false;
  area.addEventListener("touchstart", (e) => {
    if (e.touches.length !== 1) { ok = false; return; }
    sx = e.touches[0].clientX; sy = e.touches[0].clientY; st = Date.now(); ok = true;
  }, { passive: true });
  area.addEventListener("touchend", (e) => {
    if (!ok || getSelection().toString()) return;
    const t = e.changedTouches[0], dx = t.clientX - sx, dy = t.clientY - sy;
    if (Date.now() - st < 700 && Math.abs(dx) > 90 && Math.abs(dx) > Math.abs(dy) * 2.2) {
      bar.classList.add(dx < 0 ? "go-next" : "go-prev");
      go(dx < 0 ? nextA : prevA);
    }
  }, { passive: true });
})();

/* okuma alanının iki yanında oklar + telefonda kaydırma ipucu */
(() => {
  const reader = document.querySelector(".reader");
  const prevA = document.querySelector(".pager-prev, .r-pager a:not(.nx)");
  const nextA = document.querySelector(".pager-next, .r-pager a.nx");
  if (!reader || (!prevA && !nextA)) return;
  const mk = (a, cls, ch, lab) => {
    const el = document.createElement(a ? "a" : "span");
    el.className = "yan-ok " + cls + (a ? "" : " is-off");
    if (a) { el.href = a.href; el.setAttribute("aria-label", lab); el.title = lab; }
    el.innerHTML = `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="${ch}"/></svg>`;
    document.body.append(el);
    return el;
  };
  const L = mk(prevA, "yan-sol", "M15 5l-7 7 7 7", "Önceki bölüm");
  const R = mk(nextA, "yan-sag", "M9 5l7 7-7 7", nextA && /sonu|sayfasına/i.test(nextA.textContent) ? "Kitaba dön" : "Sonraki bölüm");
  const place = () => {
    const r = reader.getBoundingClientRect();
    L.style.left = Math.max(8, r.left - 64) + "px";
    R.style.left = Math.min(innerWidth - 56, r.right + 16) + "px";
    const room = r.left > 80;
    L.hidden = R.hidden = !room;
  };
  place();
  addEventListener("resize", place);
  const hint = document.createElement("p");
  hint.className = "kaydir-ipucu";
  hint.innerHTML = "<span aria-hidden=\"true\">←</span> Bölüm değiştirmek için yazıyı sağa ya da sola kaydırın <span aria-hidden=\"true\">→</span>";
  const pager = document.querySelector(".pager, .r-pager");
  (pager ? pager.parentNode : reader).insertBefore(hint, pager || null);
})();

/* kaldığın yerden devam et */
(() => {
  const K = (base) => "devam:" + base;
  const get = (k) => { try { return JSON.parse(localStorage.getItem(k) || "null"); } catch { return null; } };
  const set = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch { /* yok say */ } };
  const band = document.querySelector(".chap-band-in > a, .r-band > a");
  const reader = document.querySelector(".reader");
  if (band && reader) {
    const base = band.getAttribute("href");
    const num = (document.querySelector(".chap-num, .r-num") || {}).textContent || "";
    const title = (reader.querySelector("h1") || {}).textContent || "";
    const frac = () => { const h = document.documentElement.scrollHeight - innerHeight; return h > 0 ? scrollY / h : 0; };
    const save = () => {
      const f = frac();
      if (Number(num) > 1 || f > .08) set(K(base), { u: location.pathname, n: num.trim(), t: title.trim(), f: Math.round(f * 1000) / 1000 });
    };
    if (location.hash === "#devam") {
      const s = get(K(base));
      if (s && s.u === location.pathname && s.f > .02) {
        addEventListener("load", () => scrollTo(0, s.f * (document.documentElement.scrollHeight - innerHeight)));
      }
    }
    let t;
    addEventListener("scroll", () => { clearTimeout(t); t = setTimeout(save, 400); }, { passive: true });
    addEventListener("pagehide", save);
    if (Number(num) > 1) setTimeout(save, 1500);
    return;
  }
  const acts = document.querySelector(".bk-actions");
  if (!acts) return;
  const s = get(K(location.pathname));
  if (!s || !s.u) return;
  const a = document.createElement("a");
  a.className = "devam";
  a.href = s.u + "#devam";
  const pct = s.f ? ` · %${Math.max(1, Math.round(s.f * 100))}` : "";
  a.innerHTML = `<span class="devam-k">Kaldığınız yer${pct}</span><b></b><span class="devam-go">Devam et <span aria-hidden="true">→</span></span>`;
  a.querySelector("b").textContent = (s.n ? s.n + " · " : "") + s.t;
  acts.parentNode.insertBefore(a, acts);
  const main = acts.querySelector(".ba-main span");
  if (main) main.textContent = "Baştan başla";
})();
