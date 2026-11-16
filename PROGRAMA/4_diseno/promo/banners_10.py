# CineCaptions · By Cinema Productions
# 4_diseno/promo/banners_10.py — 10 banners promocionales de 1280×720 (todos con los iconos de Windows y Mac en una esquina).
"""
    python 4_diseno/promo/banners_10.py [carpeta_salida]

Reusa los ayudantes de crear_banner_promo.py (composición a 2×, QtSvg para los iconos). Cada banner tiene su propio concepto, paleta y composición:
  01 Clásico · 02 Privacidad · 03 Un clic · 04 Antes y después · 05 Estilos · 06 Efectos · 07 Windows + Mac · 08 Horas a segundos · 09 Reels/TikTok/Shorts · 10 Timeline de Resolve
"""
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

import crear_banner_promo as B
from crear_banner_promo import (ALTO, ANCHO, BLANCO, GRIS, H, K, RAIZ, SVG_APPLE, SVG_WINDOWS, W, con_sombra, fuente, girada, icono_svg, redondeada)

DOC = RAIZ / 'DOCUMENTACION' / 'capturas'
RECURSOS = RAIZ / '2_recursos'


# ----------------------------------------------------------------------------------------------------------------------- ayudantes
def degradado(a, b, angulo=40):
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.radians(angulo)
    t = x * np.cos(r) + y * np.sin(r)
    t = (t - t.min()) / (t.max() - t.min() + 1e-9)
    arr = np.array(a, np.float32)[None, None, :] + (np.array(b, np.float32) - np.array(a, np.float32))[None, None, :] * t[:, :, None]
    return Image.fromarray(arr.astype('uint8'), 'RGB').convert('RGBA')


def brillo(img, cx, cy, rx, ry, color, alpha=80, blur=110):
    capa = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(capa).ellipse(((cx - rx) * K, (cy - ry) * K, (cx + rx) * K, (cy + ry) * K), fill=tuple(color) + (alpha,))
    img.alpha_composite(capa.filter(ImageFilter.GaussianBlur(blur * K)))


def txt(img, xy, t, nombre, tam, color, ancla='ls', borde=None):
    g = ImageDraw.Draw(img)
    kw = {}
    if borde:
        kw = {'stroke_width': int(borde[0] * K), 'stroke_fill': borde[1]}
    g.text((xy[0] * K, xy[1] * K), t, font=fuente(nombre, tam), fill=color, anchor=ancla, **kw)


def ancho_txt(t, nombre, tam):
    return ImageDraw.Draw(Image.new('RGBA', (4, 4))).textlength(t, font=fuente(nombre, tam)) / K


def foto(n, ancho, alto):
    im = Image.open(RECURSOS / 'fondos_estilos' / f'fondo_{n:02d}.jpg').convert('RGB')
    e = max(ancho * K / im.width, alto * K / im.height)
    im = im.resize((int(im.width * e) + 1, int(im.height * e) + 1), Image.Resampling.LANCZOS)
    x0, y0 = (im.width - ancho * K) // 2, (im.height - alto * K) // 2
    return im.crop((x0, y0, x0 + ancho * K, y0 + alto * K)).convert('RGBA')


def pegar(img, im, x, y, **kw):
    con_sombra(img, im, (int(x * K), int(y * K)), **kw)


def pastilla(img, x, y, claro=False, acento=(39, 224, 138)):
    """Los iconos de Windows y Mac en una pastilla de 226×66 con su esquina en (x, y)."""
    capa = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    g = ImageDraw.Draw(capa)
    relleno, borde = ((255, 255, 255, 215), (0, 0, 0, 60)) if claro else ((255, 255, 255, 32), (255, 255, 255, 95))
    g.rounded_rectangle((x * K, y * K, (x + 226) * K, (y + 66) * K), radius=33 * K, fill=relleno, outline=borde, width=2 * K)
    img.alpha_composite(capa)
    lado = 40 * K
    win, mac = icono_svg(SVG_WINDOWS, lado), icono_svg(SVG_APPLE, lado)
    if claro:                                                       # iconos oscuros sobre la pastilla clara
        for im in (win, mac):
            r, gg, b, a = im.split()
            negro = Image.new('L', im.size, 25)
            im.paste(Image.merge('RGBA', (negro, negro, negro, a)))
    img.alpha_composite(win, (int((x + 24) * K), int((y + 13) * K)))
    img.alpha_composite(mac, (int((x + 74) * K), int((y + 13) * K)))
    c1, c2 = ((20, 20, 20), tuple(int(v * 0.55) for v in acento)) if claro else (BLANCO, acento)
    txt(img, (x + 130, y + 22), 'WINDOWS', 'Inter-Black.ttf', 15, c1, 'lm')
    txt(img, (x + 130, y + 46), '+ MAC', 'Inter-Black.ttf', 15, c2, 'lm')


def marca(img, x, y, tam=64, color=BLANCO, sub=None):
    logo = Image.open(RAIZ / '2_recursos' / 'logo_cinecaptions.png').convert('RGBA').resize((tam * K, tam * K), Image.Resampling.LANCZOS)
    con_sombra(img, logo, (int(x * K), int(y * K)), desenfoque=8, color=(0, 0, 0, 130), desp=(0, 4))
    txt(img, (x + tam + 14, y + tam * 0.52), 'CineCaptions', 'Inter-Black.ttf', tam * 0.46, color, 'lm')
    if sub:
        txt(img, (x + tam + 16, y + tam * 0.9), sub, 'Inter_18pt-Medium.ttf', max(12, tam * 0.2), tuple(int(c * 0.75) for c in color), 'lm')


def boton(img, x, y, ancho_b, t, fondo, color_t, alto_b=56, tam=26):
    g = ImageDraw.Draw(img)
    g.rounded_rectangle((x * K, y * K, (x + ancho_b) * K, (y + alto_b) * K), radius=(alto_b // 2) * K, fill=tuple(fondo))
    txt(img, (x + ancho_b / 2, y + alto_b / 2 + 1), t, 'Inter-Black.ttf', tam, color_t, 'mm')


def chip(img, x, y, t, color_borde, color_t=BLANCO, tam=20):
    w = ancho_txt(t, 'Inter_18pt-Medium.ttf', tam) + 36
    capa = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(capa).rounded_rectangle((x * K, y * K, (x + w) * K, (y + 40) * K), radius=20 * K, fill=tuple(color_borde) + (40,), outline=tuple(color_borde) + (200,), width=2 * K)
    img.alpha_composite(capa)
    txt(img, (x + w / 2, y + 21), t, 'Inter_18pt-Medium.ttf', tam, color_t, 'mm')
    return w


def titular(img, x, y, lineas, tam, color=BLANCO, acento=None, interlineado=1.08, nombre='Inter-Black.ttf'):
    """Líneas de titular; una línea puede ser [(texto, color), …] para teñir una parte."""
    for i, linea in enumerate(lineas):
        yy = y + i * tam * interlineado
        if isinstance(linea, str):
            txt(img, (x, yy), linea, nombre, tam, color, 'ls')
        else:
            xx = x
            for parte, col in linea:
                txt(img, (xx, yy), parte, nombre, tam, col, 'ls')
                xx += ancho_txt(parte, nombre, tam)


def captions_en_foto(im, hero, arriba, abajo, color, tam_hero=0.17):
    """Dibuja unos captions con el estilo de CineCaptions (línea fina, palabra HÉROE enorme con contorno, línea fina) en el tercio inferior de la foto."""
    g = ImageDraw.Draw(im)
    w, h = im.size
    f_h = ImageFont.truetype(str(RAIZ / '2_recursos' / 'fonts' / 'Inter-Black.ttf'), int(w * tam_hero))
    f_s = ImageFont.truetype(str(RAIZ / '2_recursos' / 'fonts' / 'Inter_18pt-Medium.ttf'), int(w * 0.06))
    cx = w / 2
    y0 = h * 0.60
    g.text((cx, y0), arriba, font=f_s, fill=(255, 255, 255, 235), anchor='mm', stroke_width=int(K * 2), stroke_fill=(0, 0, 0, 160))
    g.text((cx, y0 + w * 0.15), hero, font=f_h, fill=tuple(color) + (255,), anchor='mm', stroke_width=int(K * 5), stroke_fill=(0, 0, 0, 230))
    g.text((cx, y0 + w * 0.30), abajo, font=f_s, fill=(255, 255, 255, 235), anchor='mm', stroke_width=int(K * 2), stroke_fill=(0, 0, 0, 160))
    return im


def telefono(ruta_o_img, ancho_t, radio=30, borde=5, grados=0):
    im = Image.open(ruta_o_img).convert('RGBA') if not isinstance(ruta_o_img, Image.Image) else ruta_o_img.convert('RGBA')
    alto_t = int(ancho_t * 16 / 9)
    e = max(ancho_t * K / im.width, alto_t * K / im.height)
    im = im.resize((int(im.width * e) + 1, int(im.height * e) + 1), Image.Resampling.LANCZOS)
    x0, y0 = (im.width - ancho_t * K) // 2, (im.height - alto_t * K) // 2
    im = redondeada(im.crop((x0, y0, x0 + ancho_t * K, y0 + alto_t * K)), radio)
    marco = Image.new('RGBA', im.size, (0, 0, 0, 0))
    ImageDraw.Draw(marco).rounded_rectangle((0, 0, im.width - 1, im.height - 1), radius=radio * K, outline=(255, 255, 255, 235), width=borde * K)
    im.alpha_composite(marco)
    return girada(im, grados) if grados else im


def captura(nombre, ancho_c, radio=14, grados=0, recorte=None):
    im = Image.open(DOC / nombre).convert('RGBA')
    if recorte:
        im = im.crop(recorte)
    im = im.resize((ancho_c * K, int(ancho_c * im.height / im.width) * K), Image.Resampling.LANCZOS)
    im = redondeada(im, radio)
    borde = Image.new('RGBA', im.size, (0, 0, 0, 0))
    ImageDraw.Draw(borde).rounded_rectangle((0, 0, im.width - 1, im.height - 1), radius=radio * K, outline=(255, 255, 255, 60), width=2 * K)
    im.alpha_composite(borde)
    return girada(im, grados) if grados else im


def previa(nombre, ancho_p, radio=18, grados=0):
    im = Image.open(RECURSOS / 'efectos' / 'previas' / nombre).convert('RGBA')
    im = im.resize((ancho_p * K, int(ancho_p * im.height / im.width) * K), Image.Resampling.LANCZOS)
    im = redondeada(im, radio)
    return girada(im, grados) if grados else im


def emoji(nombre, lado, grados=0):
    im = Image.open(RECURSOS / 'emojis' / 'png' / f'rcs_emoji_{nombre}.png').convert('RGBA').resize((lado * K, lado * K), Image.Resampling.LANCZOS)
    return girada(im, grados) if grados else im


def cerrar(img, ruta):
    img.resize((ANCHO, ALTO), Image.Resampling.LANCZOS).convert('RGB').save(ruta, optimize=True)
    return ruta


# ----------------------------------------------------------------------------------------------------------------------- los banners
def b01(ruta):
    return B.main(ruta)


def b02(ruta):
    """Privacidad: un escudo con candado."""
    ver = (79, 209, 255)
    f = degradado((6, 10, 28), (42, 22, 112), 35)
    brillo(f, 960, 330, 330, 300, ver, 70)
    brillo(f, 120, 640, 300, 200, (140, 80, 255), 50)
    marca(f, 60, 40, 60)
    pastilla(f, 1000, 30)
    titular(f, 64, 238, ['Tus videos nunca', [('salen ', BLANCO), ('de tu equipo', ver)]], 70)
    txt(f, (66, 372), 'IA local: sin nube, sin API, sin cuotas', 'Inter_18pt-Medium.ttf', 26, GRIS, 'ls')
    x = 66
    for t in ('Sin nube', 'Sin API', '100% privado'):
        x += chip(f, x, 410, t, ver) + 14
    # escudo
    sc = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    g = ImageDraw.Draw(sc)
    cx, cy, s = 960 * K, 392 * K, 1.0 * K
    pts = [(cx - 150 * s, cy - 190 * s), (cx, cy - 235 * s), (cx + 150 * s, cy - 190 * s), (cx + 150 * s, cy + 20 * s), (cx + 100 * s, cy + 130 * s), (cx, cy + 215 * s),
           (cx - 100 * s, cy + 130 * s), (cx - 150 * s, cy + 20 * s)]
    g.polygon(pts, fill=(14, 24, 62, 255), outline=ver + (255,), width=int(9 * s))
    g.polygon([(cx - 124 * s, cy - 170 * s), (cx, cy - 208 * s), (cx + 124 * s, cy - 170 * s), (cx + 124 * s, cy + 14 * s), (cx + 86 * s, cy + 110 * s), (cx, cy + 184 * s),
               (cx - 86 * s, cy + 110 * s), (cx - 124 * s, cy + 14 * s)], outline=ver + (70,), width=int(3 * s))
    g.rounded_rectangle((cx - 62 * s, cy - 12 * s, cx + 62 * s, cy + 92 * s), radius=int(16 * s), fill=ver + (255,))
    g.arc((cx - 40 * s, cy - 90 * s, cx + 40 * s, cy + 12 * s), 180, 360, fill=ver + (255,), width=int(15 * s))
    g.line((cx - 40 * s, cy - 40 * s, cx - 40 * s, cy - 8 * s), fill=ver + (255,), width=int(15 * s))
    g.line((cx + 40 * s, cy - 40 * s, cx + 40 * s, cy - 8 * s), fill=ver + (255,), width=int(15 * s))
    g.ellipse((cx - 13 * s, cy + 22 * s, cx + 13 * s, cy + 48 * s), fill=(14, 24, 62, 255))
    g.rectangle((cx - 5 * s, cy + 40 * s, cx + 5 * s, cy + 68 * s), fill=(14, 24, 62, 255))
    f.alpha_composite(sc.filter(ImageFilter.GaussianBlur(26 * K)).point(lambda v: v) if False else sc)
    boton(f, 64, 640, 300, 'Pruébalo hoy', ver, (5, 12, 36))
    txt(f, (384, 668), 'Windows y Mac', 'Inter_18pt-Medium.ttf', 20, GRIS, 'lm')
    return cerrar(f, ruta)


def b03(ruta):
    """Un clic: el orbe GO."""
    lima = (190, 255, 70)
    f = degradado((3, 5, 4), (12, 26, 14), 60)
    brillo(f, 900, 360, 360, 330, lima, 60)
    orbe = Image.open(DOC / '01_inicio.png').convert('RGBA').crop((520, 232, 876, 592)).resize((470 * K, 470 * K), Image.Resampling.LANCZOS)
    m = Image.new('L', orbe.size, 0)
    ImageDraw.Draw(m).ellipse((0, 0, orbe.width - 1, orbe.height - 1), fill=255)
    orbe.putalpha(ImageChops.multiply(orbe.split()[3], m.filter(ImageFilter.GaussianBlur(4 * K))))
    pegar(f, orbe, 700, 124, desenfoque=34, color=(0, 0, 0, 120), brillo=lima + (110,))
    marca(f, 60, 40, 60)
    titular(f, 64, 190, [[('Un clic ', BLANCO), ('y listo', lima)]], 78)
    for i, (n, t, s) in enumerate((('1', 'Suelta tu video', 'arrástralo a Inicio'), ('2', 'Pulsa GO', 'la IA hace el resto'), ('3', 'Subtítulos listos', 'en tu timeline de Resolve'))):
        y = 262 + i * 110
        g = ImageDraw.Draw(f)
        g.ellipse((66 * K, y * K, 126 * K, (y + 60) * K), fill=lima)
        txt(f, (96, y + 31), n, 'Inter-Black.ttf', 34, (8, 20, 6), 'mm')
        txt(f, (150, y + 22), t, 'Inter-Black.ttf', 31, BLANCO, 'lm')
        txt(f, (150, y + 52), s, 'Inter_18pt-Medium.ttf', 21, GRIS, 'lm')
    pastilla(f, 1010, 624, acento=lima)
    boton(f, 64, 640, 280, 'Pruébalo hoy', lima, (8, 20, 6))
    return cerrar(f, ruta)


def b04(ruta):
    """Antes y después."""
    nar = (255, 122, 26)
    f = degradado((18, 8, 6), (46, 20, 8), 30)
    brillo(f, 900, 380, 420, 320, nar, 55)
    marca(f, 60, 36, 56)
    pastilla(f, 1000, 28)
    txt(f, (640, 150), 'Del video plano a subtítulos que retienen', 'Inter-Black.ttf', 54, BLANCO, 'mm')
    base = foto(3, 330, 450)
    antes = redondeada(base.copy(), 22)
    despues = redondeada(captions_en_foto(base.copy(), 'FUERTE', 'Tus subtítulos', 'con estilo', nar), 22)
    pegar(f, antes, 150, 210, desenfoque=24, color=(0, 0, 0, 190))
    pegar(f, despues, 800, 210, desenfoque=28, color=(0, 0, 0, 200), brillo=nar + (90,))
    boton(f, 220, 674, 190, 'ANTES', (90, 80, 76), BLANCO, alto_b=44, tam=22)
    boton(f, 870, 674, 190, 'DESPUÉS', nar, (30, 12, 2), alto_b=44, tam=22)
    # flecha
    g = ImageDraw.Draw(f)
    ax, ay = 640 * K, 440 * K
    g.polygon([(ax - 70 * K, ay - 24 * K), (ax + 10 * K, ay - 24 * K), (ax + 10 * K, ay - 52 * K), (ax + 78 * K, ay), (ax + 10 * K, ay + 52 * K), (ax + 10 * K, ay + 24 * K), (ax - 70 * K, ay + 24 * K)], fill=nar)
    txt(f, (640, 560), 'en 1 clic', 'Inter-Black.ttf', 26, BLANCO, 'mm')
    return cerrar(f, ruta)


def b05(ruta):
    """Estilos: tres teléfonos."""
    ros, oro = (255, 90, 220), (255, 200, 70)
    f = degradado((18, 6, 32), (62, 14, 84), 35)
    brillo(f, 900, 380, 420, 330, ros, 60)
    brillo(f, 60, 700, 300, 200, (110, 70, 255), 50)
    marca(f, 60, 40, 60)
    pastilla(f, 1000, 30)
    titular(f, 64, 248, ['Estilos listos', [('para ', BLANCO), ('publicar', ros)]], 70)
    txt(f, (66, 376), 'Shine Referencia · Shine Kinetic', 'Inter_18pt-Medium.ttf', 27, GRIS, 'ls')
    for i, t in enumerate(('Palabra clave destacada', 'Entrada y salida animadas', 'Emojis que acompañan')):
        y = 452 + i * 54
        g = ImageDraw.Draw(f)
        g.ellipse((66 * K, (y - 16) * K, 98 * K, (y + 16) * K), fill=ros)
        g.line((74 * K, y * K, 80 * K, (y + 6) * K), fill=(30, 0, 30), width=4 * K)
        g.line((80 * K, (y + 6) * K, 91 * K, (y - 7) * K), fill=(30, 0, 30), width=4 * K)
        txt(f, (116, y), t, 'Inter_18pt-Medium.ttf', 27, (240, 232, 246), 'lm')
    tres = captions_en_foto(foto(7, 292, 520), 'AHORA', 'Hazlo', 'con estilo', oro, 0.2)
    pegar(f, telefono(RECURSOS / 'vistas_slider' / 'Kinetic.jpg', 250, grados=-9), 590, 196, desenfoque=26, color=(0, 0, 0, 190), brillo=ros + (60,))
    pegar(f, telefono(tres, 250, grados=9), 1000, 200, desenfoque=26, color=(0, 0, 0, 190), brillo=oro + (60,))
    pegar(f, telefono(RECURSOS / 'vistas_slider' / 'Referencia.jpg', 310), 760, 130, desenfoque=34, color=(0, 0, 0, 210), brillo=ros + (110,))
    boton(f, 64, 640, 280, 'Pruébalo hoy', ros, (30, 0, 30))
    return cerrar(f, ruta)


def b06(ruta):
    """Efectos: mosaico de vistas previas."""
    az, na = (61, 139, 255), (255, 176, 32)
    f = degradado((4, 16, 42), (10, 38, 96), 40)
    brillo(f, 900, 380, 420, 330, az, 70)
    marca(f, 60, 40, 60)
    pastilla(f, 1000, 30)
    titular(f, 64, 236, ['Efectos que', [('enganchan', na)]], 80)
    txt(f, (66, 394), 'Intro, transiciones, iconos, zoom y más', 'Inter_18pt-Medium.ttf', 27, GRIS, 'ls')
    y = 436
    x = 66
    for t in ('Zoom desenfocado', 'Glitch RGB', 'Whip pan', 'Iconos flotantes'):
        x += chip(f, x, y, t, na if x % 2 else az, tam=19) + 10
        if x > 560:
            x = 66
            y += 50
    bloque = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    nombres = ['corte_glitch.jpg', 'iconos_pack1.jpg', 'corte_zoom_blur.jpg', 'intro_destello.jpg', 'iconos_pack3.jpg', 'corte_whip.jpg']
    for i, n in enumerate(nombres):
        col, fila = i % 3, i // 3
        im = previa(n, 190, 18)
        bloque.alpha_composite(im, (int((10 + col * 210) * K), int((30 + fila * 350 - (col % 2) * 40) * K)))
    bloque = girada(bloque, -6)
    sombra = bloque.filter(ImageFilter.GaussianBlur(24 * K))
    sombra = Image.merge('RGBA', (Image.new('L', sombra.size, 0), Image.new('L', sombra.size, 0), Image.new('L', sombra.size, 0), sombra.split()[3].point(lambda v: int(v * 0.65))))
    f.alpha_composite(sombra, (int(560 * K) - (bloque.width - W) // 2, int(-10 * K) - (bloque.height - H) // 2 + 22 * K))
    f.alpha_composite(bloque, (int(560 * K) - (bloque.width - W) // 2, int(-10 * K) - (bloque.height - H) // 2))
    boton(f, 64, 640, 280, 'Pruébalo hoy', na, (30, 16, 0))
    return cerrar(f, ruta)


def b07(ruta):
    """Windows + Mac como protagonistas."""
    f = Image.new('RGBA', (W, H), (0, 0, 0, 255))
    izq = degradado((6, 52, 130), (26, 120, 235), 60)
    der = degradado((24, 26, 30), (92, 98, 108), 120)
    f.alpha_composite(izq)
    m = Image.new('L', (W, H), 0)
    ImageDraw.Draw(m).polygon([(int(W * 0.58), 0), (W, 0), (W, H), (int(W * 0.42), H)], fill=255)
    f.paste(der, (0, 0), m)
    sep = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sep).line([(int(W * 0.58), 0), (int(W * 0.42), H)], fill=(255, 255, 255, 120), width=4 * K)
    f.alpha_composite(sep)
    brillo(f, 330, 420, 300, 260, (120, 190, 255), 70)
    brillo(f, 960, 420, 300, 260, (255, 255, 255), 40)
    win = icono_svg(SVG_WINDOWS, 230 * K)
    mac = icono_svg(SVG_APPLE, 230 * K)
    con_sombra(f, win, (int(214 * K), int(250 * K)), desenfoque=18, color=(0, 0, 0, 120), desp=(0, 10))
    con_sombra(f, mac, (int(836 * K), int(250 * K)), desenfoque=18, color=(0, 0, 0, 120), desp=(0, 10))
    txt(f, (330, 540), 'Windows', 'Inter-Black.ttf', 40, BLANCO, 'mm')
    txt(f, (950, 540), 'Mac', 'Inter-Black.ttf', 40, BLANCO, 'mm')
    txt(f, (950, 580), 'Apple Silicon e Intel', 'Inter_18pt-Medium.ttf', 22, (210, 214, 222), 'mm')
    txt(f, (330, 580), 'Instalador y actualizaciones', 'Inter_18pt-Medium.ttf', 22, (214, 232, 255), 'mm')
    txt(f, (600, 128), 'Ahora para Windows y Mac', 'Inter-Black.ttf', 56, BLANCO, 'mm', borde=(2, (0, 0, 0, 60)))
    txt(f, (600, 184), 'Subtítulos con IA en 1 clic, directo en DaVinci Resolve', 'Inter_18pt-Medium.ttf', 27, (236, 240, 248), 'mm')
    marca(f, 60, 626, 62)
    boton(f, 920, 636, 300, 'Pruébalo hoy', BLANCO, (14, 22, 40))
    pastilla(f, 1010, 30, claro=True, acento=(39, 224, 138))
    return cerrar(f, ruta)


def b08(ruta):
    """De horas a segundos."""
    amb = (255, 194, 26)
    f = degradado((8, 7, 4), (30, 24, 8), 30)
    brillo(f, 930, 380, 360, 330, amb, 60)
    marca(f, 60, 40, 60)
    titular(f, 64, 228, ['De horas', [('a ', BLANCO), ('segundos', amb)]], 86)
    txt(f, (66, 392), 'Transcribe y coloca tus subtítulos en 1 clic', 'Inter_18pt-Medium.ttf', 27, GRIS, 'ls')
    for i, t in enumerate(('Sin sincronizar a mano', 'Sin editar palabra por palabra', 'Sin pagar por minuto')):
        y = 462 + i * 54
        g = ImageDraw.Draw(f)
        g.ellipse((66 * K, (y - 17) * K, 100 * K, (y + 17) * K), fill=amb)
        g.line((74 * K, (y - 7) * K, 92 * K, (y + 7) * K), fill=(30, 20, 0), width=4 * K)
        g.line((92 * K, (y - 7) * K, 74 * K, (y + 7) * K), fill=(30, 20, 0), width=4 * K)
        txt(f, (118, y), t, 'Inter_18pt-Medium.ttf', 28, (244, 238, 224), 'lm')
    # cronómetro
    c = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    g = ImageDraw.Draw(c)
    cx, cy, r = 930 * K, 400 * K, 215 * K
    g.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(20, 16, 6, 255), outline=(255, 255, 255, 40), width=6 * K)
    g.ellipse((cx - r + 26 * K, cy - r + 26 * K, cx + r - 26 * K, cy + r - 26 * K), outline=(255, 194, 26, 70), width=18 * K)
    g.arc((cx - r + 26 * K, cy - r + 26 * K, cx + r - 26 * K, cy + r - 26 * K), -90, 232, fill=amb + (255,), width=18 * K)
    g.rounded_rectangle((cx - 28 * K, cy - r - 40 * K, cx + 28 * K, cy - r + 6 * K), radius=10 * K, fill=amb + (255,))
    g.polygon([(cx + r * 0.62, cy - r * 0.62), (cx + r * 0.78, cy - r * 0.46), (cx + r * 0.66, cy - r * 0.5)], fill=amb + (255,))
    con_sombra(f, c, (0, 0), desenfoque=30, color=(0, 0, 0, 120), brillo=amb + (70,)) if False else f.alpha_composite(c)
    txt(f, (930, 372), '1 clic', 'Inter-Black.ttf', 78, BLANCO, 'mm')
    txt(f, (930, 446), 'y listo', 'Inter-Black.ttf', 44, amb, 'mm')
    pastilla(f, 1010, 624, acento=amb)
    boton(f, 64, 640, 280, 'Pruébalo hoy', amb, (30, 20, 0))
    return cerrar(f, ruta)


def b09(ruta):
    """Reels, TikTok y Shorts: fondo vivo con un teléfono y pegatinas."""
    f = degradado((255, 45, 135), (62, 44, 255), 25)
    brillo(f, 900, 380, 420, 330, (0, 220, 255), 110)
    brillo(f, 100, 120, 300, 200, (255, 200, 80), 70)
    marca(f, 60, 40, 60, color=BLANCO)
    pastilla(f, 1000, 30, claro=True, acento=(255, 45, 135))
    titular(f, 64, 244, ['Hecho para', 'Reels, TikTok', 'y Shorts'], 74)
    txt(f, (66, 466), 'Formato vertical 9:16 listo para publicar', 'Inter_18pt-Medium.ttf', 27, (255, 240, 250), 'ls')
    x = 66
    for t in ('9:16', 'Vertical', 'Palabra clave', 'Emojis'):
        x += chip(f, x, 496, t, BLANCO, tam=20) + 12
    pegar(f, telefono(RECURSOS / 'vistas_slider' / 'Referencia.jpg', 292, grados=-4), 830, 120, desenfoque=34, color=(0, 0, 0, 170), brillo=(0, 230, 255, 120))
    for nombre, lado, x, y, gr in (('fire', 92, 770, 140, -14), ('rocket', 96, 1118, 210, 12), ('sparkles', 84, 1110, 480, -10), ('money_bag', 88, 760, 520, 10), ('red_heart', 74, 1000, 96, 8)):
        try:
            pegar(f, emoji(nombre, lado, gr), x, y, desenfoque=12, color=(0, 0, 0, 120), desp=(0, 8))
        except Exception:
            pass
    boton(f, 64, 640, 280, 'Pruébalo hoy', BLANCO, (60, 20, 110))
    return cerrar(f, ruta)


def b10(ruta):
    """Dentro del timeline de DaVinci Resolve."""
    rojo, teal = (240, 84, 70), (60, 210, 190)
    f = degradado((14, 14, 16), (34, 28, 32), 80)
    brillo(f, 640, 560, 520, 220, rojo, 40)
    marca(f, 60, 40, 60)
    pastilla(f, 1000, 30)
    titular(f, 64, 236, ['Tus subtítulos,', [('dentro de tu timeline', rojo)]], 62)
    txt(f, (66, 346), 'CineCaptions los coloca solos en DaVinci Resolve, listos para editar', 'Inter_18pt-Medium.ttf', 25, GRIS, 'ls')
    # panel de timeline dibujado
    panel = Image.new('RGBA', (1150 * K, 280 * K), (0, 0, 0, 0))
    g = ImageDraw.Draw(panel)
    g.rounded_rectangle((0, 0, panel.width - 1, panel.height - 1), radius=18 * K, fill=(22, 22, 26, 250), outline=(255, 255, 255, 40), width=2 * K)
    for i in range(0, 23):
        x = (150 + i * 44) * K
        g.line((x, 16 * K, x, (30 if i % 2 else 36) * K), fill=(255, 255, 255, 90), width=K)
    pistas = [('V1', 60, (46, 96, 168)), ('T1', 110, rojo), ('T2', 156, (240, 170, 60)), ('A1', 214, teal)]
    rnd = random.Random(4)
    for nombre, y, col in pistas:
        g.rounded_rectangle((16 * K, y * K, 120 * K, (y + 38) * K), radius=8 * K, fill=(40, 40, 46, 255))
        g.text((68 * K, (y + 19) * K), nombre, font=fuente('Inter-Black.ttf', 18), fill=(220, 220, 224), anchor='mm')
    x = 150
    for k in range(6):                                              # clips de video
        ancho_c = rnd.randint(110, 190)
        g.rounded_rectangle((x * K, 60 * K, (x + ancho_c - 6) * K, 98 * K), radius=8 * K, fill=(46, 96, 168, 255))
        x += ancho_c
    x = 168
    textos = ['Hola', 'esto es', 'GRANDE', 'en 1 clic', 'Windows', 'y Mac']
    for t in textos:                                                # captions
        ancho_c = max(88, int(ancho_txt(t, 'Inter-Black.ttf', 20)) + 40)
        g.rounded_rectangle((x * K, 110 * K, (x + ancho_c) * K, 148 * K), radius=8 * K, fill=rojo + (255,))
        g.text(((x + ancho_c / 2) * K, 129 * K), t, font=fuente('Inter-Black.ttf', 20), fill=(255, 255, 255), anchor='mm')
        x += ancho_c + 22
    x = 190
    for t in ('Palabra', 'clave', 'Efecto', 'Emoji', 'Riser'):
        ancho_c = max(80, int(ancho_txt(t, 'Inter_18pt-Medium.ttf', 18)) + 34)
        g.rounded_rectangle((x * K, 156 * K, (x + ancho_c) * K, 194 * K), radius=8 * K, fill=(240, 170, 60, 255))
        g.text(((x + ancho_c / 2) * K, 175 * K), t, font=fuente('Inter_18pt-Medium.ttf', 18), fill=(40, 24, 0), anchor='mm')
        x += ancho_c + 40
    for i in range(0, 1000, 6):                                     # onda de audio
        h = int(8 + abs(np.sin(i * 0.11) * np.sin(i * 0.031 + 1)) * 34 * (0.5 + rnd.random() * 0.6))
        g.line(((150 + i) * K, (233 - h) * K, (150 + i) * K, (233 + h) * K), fill=teal + (255,), width=3 * K)
    g.line((470 * K, 8 * K, 470 * K, 290 * K), fill=(255, 255, 255, 230), width=3 * K)         # el cabezal
    g.polygon([(458 * K, 8 * K), (482 * K, 8 * K), (470 * K, 28 * K)], fill=(255, 255, 255, 240))
    pegar(f, panel, 65, 372, desenfoque=26, color=(0, 0, 0, 200), desp=(0, 18))
    boton(f, 64, 670, 240, 'Pruébalo hoy', rojo, BLANCO, alto_b=40, tam=21)
    txt(f, (326, 690), 'Windows y Mac · Apple Silicon e Intel', 'Inter_18pt-Medium.ttf', 19, GRIS, 'lm')
    return cerrar(f, ruta)


BANNERS = [('01_clasico', b01), ('02_privacidad', b02), ('03_un_clic', b03), ('04_antes_despues', b04), ('05_estilos', b05), ('06_efectos', b06),
           ('07_windows_mac', b07), ('08_horas_a_segundos', b08), ('09_reels_tiktok_shorts', b09), ('10_timeline_resolve', b10)]

if __name__ == '__main__':
    carpeta = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent / 'banners'
    carpeta.mkdir(parents=True, exist_ok=True)
    solo = sys.argv[2:] if len(sys.argv) > 2 else None
    for nombre, fn in BANNERS:
        if solo and not any(nombre.startswith(s) for s in solo):
            continue
        try:
            print(fn(carpeta / f'CineCaptions_banner_{nombre}.png'), flush=True)
        except Exception as e:
            import traceback
            print('FALLO', nombre, repr(e), flush=True)
            traceback.print_exc()
