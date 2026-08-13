#!/bin/sh
KEY="e04a2c65-748c-4355-9333-1ffb3f7b0436"
OUT="/usr/local/www/alma/paloalto/traffic.json"
TMP="${OUT}.tmp"

curl -s --compressed -o "$TMP" \
  "https://api.511.org/traffic/events?api_key=${KEY}&format=json" 2>/dev/null

# Strip BOM only if present (first 3 bytes are EF BB BF)
BOM=$(head -c 3 "$TMP" | od -A n -t x1 | tr -d " ")
if [ "$BOM" = "efbbbf" ]; then
  tail -c +4 "$TMP" > "${TMP}.clean"
  mv "${TMP}.clean" "$OUT"
else
  mv "$TMP" "$OUT"
fi

chmod 644 "$OUT"
