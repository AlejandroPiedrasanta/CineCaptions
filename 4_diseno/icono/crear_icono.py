# CineCaptions · By Cinema Productions
# 4_diseno/icono/crear_icono.py — crea el icono del programa (2_recursos/logo_cinecaptions.png y .ico) desde el logo.
"""Icono de CineCaptions (5.3): las cuatro barras de colores del diseño nuevo (logo_original.jpg) sobre un cuadrado
redondeado blanco con esquinas transparentes, listo para el .exe, el instalador y la ventana."""
import sys
import pathlib
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

# Uso: python 4_diseno/icono/crear_icono.py [logo.jpg]  ->  2_recursos/logo_cinecaptions.png y .ico (los que usan el
# programa y el instalador; no se guardan copias aqui) + 4_diseno/icono/muestra_iconos.png para revisarlos.
AQUI = pathlib.Path(__file__).resolve().parent
ORIGEN = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else AQUI / 'logo_original.jpg'
SALIDA = AQUI.parent.parent / '2_recursos'

img = Image.open(ORIGEN).convert('RGB')
a = np.asarray(img).astype(np.float32)
H, W, _ = a.shape
# las barras: pixeles con color (saturacion alta) dentro del cuadro del icono
sat = a.max(axis=2) - a.min(axis=2)
oy, ox = int(H * 0.2), int(W * 0.1)
ys, xs = np.nonzero(sat[oy:int(H * 0.95), ox:int(W * 0.92)] > 60)
by0, by1 = ys.min() + oy, ys.max() + oy
bx0, bx1 = xs.min() + ox, xs.max() + ox
print('barras', (bx0, by0, bx1, by1))
m = 34                                           # margen alrededor (incluye el brillo suave de las barras)
recorte = img.crop((bx0 - m, by0 - m, bx1 + m + 1, by1 + m + 1))
# color del cuadro (blanco casi puro) muestreado dentro del icono, lejos de las barras
muestra = a[int(H * 0.2):int(H * 0.27), int(W * 0.3):int(W * 0.7)].reshape(-1, 3)
BLANCO = tuple(int(v) for v in np.median(muestra, axis=0))
print('cuadro', BLANCO)
cw, ch = recorte.size
pluma = Image.new('L', (cw, ch), 0)             # difumina el borde del recorte para fundirlo con el cuadro
ImageDraw.Draw(pluma).rectangle((m // 2, m // 2, cw - m // 2, ch - m // 2), fill=255)
pluma = pluma.filter(ImageFilter.GaussianBlur(m / 3))
S = 1024


def icono(lado):
    k = 4
    s = lado * k
    radio = int(s * 0.225)
    mascara = Image.new('L', (s, s), 0)
    ImageDraw.Draw(mascara).rounded_rectangle((0, 0, s - 1, s - 1), radio, fill=255)
    t = np.linspace(0, 1, s)[:, None]
    arriba, abajo = np.array([255, 255, 255]), np.array(BLANCO) - np.array([6, 5, 3])
    filas = (arriba * (1 - t) + abajo * t).astype(np.uint8)
    cuadro = Image.fromarray(np.repeat(filas[:, None, :], s, axis=1).reshape(s, s, 3)).convert('RGBA')
    ocupa = 0.80 if lado >= 32 else 0.88
    esc = ocupa * s / max(bx1 - bx0 + 1, by1 - by0 + 1)
    tam = (max(1, int(cw * esc)), max(1, int(ch * esc)))
    g = recorte.resize(tam, Image.LANCZOS).convert('RGBA')
    g.putalpha(pluma.resize(tam, Image.LANCZOS))
    cuadro.alpha_composite(g, ((s - tam[0]) // 2, (s - tam[1]) // 2))
    if lado >= 48:
        borde = Image.new('L', (s, s), 0)
        ImageDraw.Draw(borde).rounded_rectangle((0, 0, s - 1, s - 1), radio, outline=255, width=max(2, s // 180))
        cuadro.paste(Image.new('RGBA', (s, s), (214, 218, 228, 255)), (0, 0), borde)
    cuadro.putalpha(mascara)
    return cuadro.resize((lado, lado), Image.LANCZOS)


grande = icono(S)
grande.save(SALIDA / 'logo_cinecaptions.png')
tamanos = [16, 20, 24, 32, 40, 48, 64, 128, 256]
icono(256).save(SALIDA / 'logo_cinecaptions.ico', sizes=[(t, t) for t in tamanos],
                append_images=[icono(t) for t in tamanos[:-1]])
# muestra para revisar: sobre oscuro y claro, varios tamanos
prueba = Image.new('RGBA', (900, 300), (8, 12, 20, 255))
x = 20
for t in (256, 128, 64, 48, 32, 24, 16):
    prueba.alpha_composite(icono(t), (x, 20))
    x += t + 20
claro = Image.new('RGBA', (900, 300), (240, 240, 240, 255))
x = 20
for t in (256, 128, 64, 48, 32, 24, 16):
    claro.alpha_composite(icono(t), (x, 20))
    x += t + 20
hoja = Image.new('RGBA', (900, 600))
hoja.paste(prueba, (0, 0))
hoja.paste(claro, (0, 300))
hoja.save(AQUI / 'muestra_iconos.png')
print('listo')
