# CineCaptions · By Cinema Productions
# 4_diseno/plantilla_base_cinema/hoja.py — hoja de contacto de la plantilla base nueva (variantes 1..3 y simple, vertical y horizontal).
"""Junta los fotogramas de ver/ en una sola imagen por formato: la vertical en 4 columnas, la horizontal en 2x2."""
import pathlib
from PySide6.QtGui import QImage, QPainter, QColor, QFont, QGuiApplication

AQUI = pathlib.Path(__file__).resolve().parent
ARCH = {'v': 'Base titulos dinamicos vertical', 'h': 'Base titulos dinamicos Horizontal'}
ETIQ = {1: 'variante 1 · blanco', 2: 'variante 2 · ámbar', 3: 'variante 3 · cian', 0: 'simple'}


def hoja(f):
    QGuiApplication.instance() or QGuiApplication([])
    cw, ch, cols = (270, 480, 4) if f == 'v' else (480, 270, 2)
    filas = 1 if f == 'v' else 2
    out = QImage(cols * (cw + 8) + 8, filas * (ch + 28) + 8, QImage.Format.Format_RGB32)
    out.fill(QColor(28, 28, 32))
    p = QPainter(out)
    p.setPen(QColor(230, 230, 230))
    p.setFont(QFont('Segoe UI', 10))
    for i, n in enumerate((1, 2, 3, 0)):
        x, y = 8 + (i % cols) * (cw + 8), 8 + (i // cols) * (ch + 28) + 18
        ruta = AQUI / 'ver' / f'{ARCH[f]}__set{n}.png'
        if ruta.is_file():
            p.drawImage(x, y, QImage(str(ruta)).scaled(cw, ch))
        p.drawText(x, y - 5, ETIQ[n])
    p.end()
    destino = AQUI / 'ver' / f'HOJA {f}.png'
    out.save(str(destino))
    return destino


if __name__ == '__main__':
    print(hoja('v'), hoja('h'))
