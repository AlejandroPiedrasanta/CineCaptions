# CineCaptions · By Cinema Productions
# 4_diseno/plantillas_virales/hoja.py — hoja de contacto (sets 1..6 y base) de un pack verificado en Resolve.
"""Hoja de contacto de un pack verificado: los 7 fotogramas (sets 1..6 y base) en una sola imagen."""
import sys, pathlib
from PySide6.QtGui import QImage, QPainter, QColor, QFont
from PySide6.QtWidgets import QApplication
app = QApplication.instance() or QApplication([])
AQUI = pathlib.Path(__file__).resolve().parent
def hoja(archivo, ancho_celda=300):
    imgs = []
    for n in (1, 2, 3, 4, 5, 6, 0):
        f = AQUI / 'ver' / f'{archivo}__set{n}.png'
        if f.exists():
            imgs.append((n, QImage(str(f))))
    if not imgs: return None
    w0, h0 = imgs[0][1].width(), imgs[0][1].height()
    k = ancho_celda / w0
    cw, ch = int(w0 * k), int(h0 * k)
    cols = 7 if w0 > h0 else 7
    out = QImage(cols * (cw + 6) + 6, ch + 34, QImage.Format_RGB32); out.fill(QColor(30, 30, 34))
    p = QPainter(out); p.setPen(QColor(230, 230, 230)); p.setFont(QFont('Segoe UI', 10))
    for i, (n, im) in enumerate(imgs):
        x = 6 + i * (cw + 6)
        p.drawImage(x, 28, im.scaled(cw, ch))
        p.drawText(x, 18, 'base' if n == 0 else f'set {n}')
    p.end()
    ruta = AQUI / 'ver' / f'HOJA {archivo}.png'
    out.save(str(ruta)); return ruta
if __name__ == '__main__':
    for a in sys.argv[1:]: print(hoja(a))
