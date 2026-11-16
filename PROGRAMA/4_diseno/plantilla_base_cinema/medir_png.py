# CineCaptions · By Cinema Productions
# 4_diseno/plantilla_base_cinema/medir_png.py — caja (ancho x alto, centro) del texto claro de cada fotograma de medida.
"""Mide lo que ocupa cada Text+ en los fotogramas de medidas/ (fondo negro): bbox de lo claro, en px y en fracción del cuadro."""
import sys
import pathlib
from PySide6.QtGui import QImage

AQUI = pathlib.Path(__file__).resolve().parent


def caja(ruta, umbral=60):
    im = QImage(str(ruta)).convertToFormat(QImage.Format.Format_RGB32)
    w, h = im.width(), im.height()
    x0, y0, x1, y1 = w, h, -1, -1
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            c = im.pixel(x, y)
            if ((c >> 16) & 255) + ((c >> 8) & 255) + (c & 255) > umbral * 3:
                x0, y0, x1, y1 = min(x0, x), min(y0, y), max(x1, x), max(y1, y)
    return w, h, (x0, y0, x1, y1)


if __name__ == '__main__':
    carpeta = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else AQUI / 'medidas'
    for f in sorted(carpeta.glob('*.png')):
        w, h, (x0, y0, x1, y1) = caja(f)
        if x1 < 0:
            print(f.name, 'vacío')
            continue
        print(f'{f.name}: {w}x{h} caja {x1 - x0}x{y1 - y0}px  = {(x1 - x0) / w:.3f} x {(y1 - y0) / h:.3f} del cuadro; '
              f'centro y={((y0 + y1) / 2 - h / 2) / h * -1:+.3f}')
