# ACIPAYAM.com — yeni tasarım (test sürümü)

acipayam.com'daki içeriğin sıfırdan tasarlanmış yeni sürümü. Test adresi:
**https://acipayam.gunerunal.com.tr**

## İçinde ne var

- **7 kitap**, bölüm bölüm okunabilir web metni olarak: US’lu Dimağ, Gönül Dostu,
  US’lu Düşler, Bana Köyünü Anlat, Karanlık Odada Yedi Ay, İçimde Kalan Çocuk,
  Kelekçi’de Yaşamak. Metinler yazarın düzenlenmiş (WEB_RENKLI) PDF'lerinden
  çıkarıldı; PDF'lerin kendisi `/indir/` altında indirilebilir.
- **Bana Köyünü Anlat**: köy haritası, 27 görüşme (videolarıyla), dizin ve yerel ağız sözlüğü.
- **Acıpayam Dünü Bugünü**: Hikmet Başaran söyleşileri ve zaman damgalı dökümleri.
- **Denizli Şehit Bilgi Kapısı**: 3.290 kayıt; isim, savaş ve ilçeye göre arama.
- **Radyo arşivi**, 1 Nisan geleneği, videolar, sohbetten seçmeler, ACIPAYAM.com’un hikâyesi.

Ses kayıtları (MP3) ve sohbet kutusu asıl siteden (acipayam.com) kullanılır.

## Klasörler

| Klasör | Ne var |
| --- | --- |
| `data/` | Siteden ve kitaplardan çıkarılmış içerik (JSON) |
| `data/kitaplar/` | Her kitabın bölümleri |
| `static/` | Görseller, kitap fotoğrafları, indirilebilir PDF'ler |
| `assets/` | Tasarım (`site.css`) ve etkileşim (`site.js`) |
| `build.py` | Siteyi `docs/` klasörüne üretir |
| `tools/` | İçeriği yeniden çekme ve PDF dönüştürme araçları |

## Siteyi üretmek

Ek paket gerekmez:

```bash
python3 build.py
```

Yerelde bakmak için: `cd docs && python3 -m http.server`, ardından http://localhost:8000

`main` dalına her gönderimde GitHub Actions siteyi üretip GitHub Pages’e yayınlar
(`.github/workflows/pages.yml`).

## İçeriği güncellemek

**Siteden yeniden çekmek** (Python'da `beautifulsoup4` ve `Pillow` gerekir):

```bash
tools/fetch.sh ../mirror
python3 tools/extract.py ../mirror
```

**Bir kitabın yeni PDF'ini eklemek** (poppler-utils ve `Pillow` gerekir):

```bash
mkdir -p ../work/gonul-dostu
pdftohtml -xml -zoom 1.5 -fmt jpg -q GONUL_DOSTU.pdf ../work/gonul-dostu/p
python3 tools/pdf2book.py ../work gonul-dostu
cp GONUL_DOSTU.pdf static/indir/gonul-dostu.pdf
python3 build.py
```

Kitapların bölüm başlığı yazı tipi ve başlangıç sayfası `tools/pdf2book.py` içindeki
`BOOKS` tablosunda tanımlıdır; PDF düzeni değişirse orası güncellenmelidir.

## Yayına alma (bir kez)

1. GitHub’da deponun **Settings → Pages** bölümünde **Source: GitHub Actions** seçin.
2. Aynı sayfada **Custom domain** alanına `acipayam.gunerunal.com.tr` yazın ve kaydedin.
3. Alan adı yönetim panelinde bir **CNAME** kaydı açın:
   `acipayam` → `<github-kullanıcı-adı>.github.io`
4. DNS yayıldıktan sonra **Enforce HTTPS** kutusunu işaretleyin.

Test sürümü arama motorlarına kapalıdır (`noindex` ve `robots.txt`).
