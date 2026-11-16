# CineCaptions · By Cinema Productions
# 4_diseno/plantillas_virales/medir.py — mide la caja de texto de las fotos de calibración (cal_v.json / cal_h.json).
"""Mide la caja del texto (píxeles no oscuros) de cada foto de calibración y arma una hoja de contactos."""
import json
import pathlib
import sys

import numpy as np
from PIL import Image

AQUI = pathlib.Path(__file__).resolve().parent


def caja(ruta, umbral=40):
    a = np.asarray(Image.open(ruta).convert('RGB')).astype(np.int16)
    m = a.max(axis=2) > umbral
    ys, xs = np.nonzero(m)
    h, w = m.shape
    if len(xs) == 0:
        return None
    # respecto del centro del cuadro: y positiva = arriba
    return {'w': w, 'h': h, 'ancho': int(xs.max() - xs.min() + 1), 'alto': int(ys.max() - ys.min() + 1),
            'arriba': int(h / 2 - ys.min()), 'abajo': int(ys.max() - h / 2),
            'izq': int(w / 2 - xs.min()), 'der': int(xs.max() - w / 2)}


def main(patron, salida):
    rutas = sorted(AQUI.glob(patron))
    datos = {r.name: caja(r) for r in rutas}
    for k, v in datos.items():
        print(k, v)
    (AQUI / (salida + '.json')).write_text(json.dumps(datos, indent=1), encoding='utf-8')
    ims = [Image.open(r).convert('RGB') for r in rutas]
    alto = 360
    ims = [im.resize((int(im.width * alto / im.height), alto)) for im in ims]
    hoja = Image.new('RGB', (sum(i.width for i in ims) + 8 * len(ims), alto), (70, 70, 70))
    x = 0
    for im in ims:
        hoja.paste(im, (x, 0))
        x += im.width + 8
    hoja.save(AQUI / (salida + '.png'))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
