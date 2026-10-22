#!/bin/sh
# Uso: sh render.sh archivo.html  -> archivo.png (1240x1000)
d=$(cd "$(dirname "$1")" && pwd); f=$(basename "$1" .html)
/opt/pw-browsers/chromium --headless=new --no-sandbox --disable-gpu --hide-scrollbars --force-device-scale-factor=1 --window-size=1240,1100 --virtual-time-budget=2000 --screenshot="$d/$f.png" "file://$d/$f.html" >/dev/null 2>&1
python3 -c "from PIL import Image;import sys;p=sys.argv[1];Image.open(p).crop((0,0,1240,1000)).save(p)" "$d/$f.png"
