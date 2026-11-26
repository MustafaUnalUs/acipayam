# Köy haritası üretimi

Kaynak: Harita Genel Müdürlüğü, Denizli İl Haritası (1:250.000), Acıpayam yeşil işaretli
PDF (Mustafa Ünal'ın gönderdiği). Gömülü JPEG'den Acıpayam kesiti alınır:
`crop((1550, 3700, 3900, 6400))` → `acp.png`.

1. `python3 cikar2.py acp.png` → `ozellik2.json` (sınır, ana yol, il yolları, dereler,
   köy yolları, köy noktaları) ve `yazi_maske.npy` (etiket yerleşimi için).
2. Köy noktaları isimlerle eşleştirilip `eslesen.json` yazılır
   (eski `data/harita-koyler.json` + afin dönüşüm; hepsi ≤2 px).
3. `python3 ciz2.py` → `static/img/acipayam-harita.svg` ve `data/harita-koyler.json`.

