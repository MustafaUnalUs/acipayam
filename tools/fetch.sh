#!/usr/bin/env bash
# acipayam.com'un güncel kopyasını indirir (büyük ses/PDF dosyaları hariç).
# Kullanım: tools/fetch.sh <hedef-klasör>
set -euo pipefail
DEST="${1:-mirror}"
mkdir -p "$DEST" "$DEST/../data-raw"
cd "$DEST"
wget -q -r -l 6 -np -nH -E -e robots=off --reject 'mp3,pdf,mp4,m4a,wav,zip' --domains acipayam.com https://acipayam.com/ || true
curl -fsS -o ../data-raw/icimde-kalan-cocuk-bolumler.json https://acipayam.com/icimde-kalan-cocuk/bolumler.json
curl -fsS -o ../data-raw/mini-sohbet.json https://acipayam.com/api/mini-sohbet
echo "Tamam: $(find . -name '*.html' | wc -l) sayfa"
