# CineCaptions · By Cinema Productions
# 4_diseno/banner/crear_banner.py — dibuja 3_compilar/banner.jpg, el banner del instalador.
"""Dibuja 3_compilar/banner.jpg (1760x472): el banner del instalador de CineCaptions.

v5.2 (pedido: «mejora el banner por otro que impacte»): tres pantallas de
reels en perspectiva con subtitulos virales de 3 lineas (los colores de los
roles, la palabra clave en caja), emojis 3D (Fluent, MIT) flotando con
profundidad, destellos anamorficos, una onda de voz luminosa que cruza la
escena y el boton GO. El instalador solo oscurece el tercio izquierdo (ahi
van el logo, el titulo y la frase), asi que la escena vive a la derecha.
    python crear_banner.py
"""
import math
import random
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent
FUENTES = RAIZ / '2_recursos' / 'fonts'
EMOJIS = RAIZ / '2_recursos' / 'emojis' / 'png'
SALIDA = RAIZ / '3_compilar' / 'banner.jpg'
W, H = 1760, 472
ESC = 2  # se dibuja al doble y se reduce: bordes limpios

AZUL = (15, 98, 254)
AZUL_CLARO = (69, 137, 255)
CIAN = (64, 214, 255)
AMBAR = (255, 190, 64)
VIOLETA = (179, 120, 255)
MAGENTA = (236, 72, 190)
BLANCO = (255, 255, 255)


def f(nombre, tam):
    return ImageFont.truetype(str(FUENTES / nombre), int(tam * ESC))


def s(v):
    return int(round(v * ESC))


def capa():
    return Image.new('RGBA', (s(W), s(H)), (0, 0, 0, 0))


def luz(img, caja, color, alfa, radio):
    c = capa()
    ImageDraw.Draw(c).ellipse([s(v) for v in caja], fill=color + (alfa,))
    return Image.alpha_composite(img, c.filter(ImageFilter.GaussianBlur(s(radio))))


def fondo():
    img = Image.new('RGBA', (s(W), s(H)), (4, 6, 12, 255))
    # de izquierda (casi negro) a derecha (azul noche)
    g = Image.linear_gradient('L').rotate(90, expand=True).resize((s(W), s(H)))
    g = ImageChops.invert(g)
    noche = Image.new('RGBA', (s(W), s(H)), (10, 16, 44, 255))
    img = Image.composite(noche, img, g)
    img = luz(img, (980, -220, 1620, 380), AZUL, 150, 120)
    img = luz(img, (1420, 200, 1900, 620), (110, 50, 230), 120, 110)
    img = luz(img, (860, 300, 1180, 560), (230, 120, 40), 70, 90)
    img = luz(img, (1180, 120, 1420, 360), CIAN, 40, 70)
    return img


def piso(img):
    """Un suelo de rejilla en perspectiva, muy tenue, bajo las pantallas."""
    c = capa()
    d = ImageDraw.Draw(c)
    horizonte, fuga = 330, 1300
    for k in range(-14, 15):
        x = fuga + k * 130
        d.line([s(fuga + k * 8), s(horizonte), s(x * 1.0 + k * 60), s(H + 40)], fill=(70, 120, 255, 36), width=s(1.2))
    y = horizonte
    paso = 6
    while y < H + 40:
        d.line([s(700), s(y), s(W), s(y)], fill=(70, 120, 255, 30), width=s(1.2))
        paso *= 1.32
        y += paso
    m = Image.new('L', c.size, 0)
    ImageDraw.Draw(m).ellipse([s(800), s(250), s(1800), s(640)], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(s(60)))
    c.putalpha(ImageChops.multiply(c.getchannel('A'), m))
    return Image.alpha_composite(img, c)


def onda(img):
    """La voz: una cinta luminosa que cruza por detras de las pantallas."""
    c = capa()
    d = ImageDraw.Draw(c)
    for capa_k, (col, ancho, amp, fase) in enumerate([(CIAN, 2.4, 34, 0.0), (AZUL_CLARO, 1.6, 22, 1.4),
                                                      (VIOLETA, 1.2, 46, 2.6)]):
        puntos = []
        for i in range(0, 1101, 4):
            x = 660 + i
            env = math.sin(math.pi * i / 1100) ** 1.2
            y = 300 + env * amp * math.sin(i / 38 + fase) * math.cos(i / 97 + fase * 0.7)
            puntos.append((s(x), s(y)))
        d.line(puntos, fill=col + (230,), width=s(ancho), joint='curve')
    brillo = c.filter(ImageFilter.GaussianBlur(s(7)))
    img = Image.alpha_composite(img, brillo)
    img = Image.alpha_composite(img, brillo)
    return Image.alpha_composite(img, c)


def escena(w, h, tipo):
    """El «fotograma» dentro de cada pantalla (a escala ya multiplicada)."""
    im = Image.new('RGBA', (w, h), (0, 0, 0, 255))
    d = ImageDraw.Draw(im)
    if tipo == 'atardecer':
        arriba, abajo = (18, 40, 78), (236, 128, 70)
    elif tipo == 'ciudad':
        arriba, abajo = (8, 10, 30), (60, 30, 110)
    else:
        arriba, abajo = (30, 18, 24), (130, 70, 50)
    for y in range(h):
        t = y / max(1, h - 1)
        col = tuple(int(a + (b - a) * t ** 1.3) for a, b in zip(arriba, abajo))
        d.line([(0, y), (w, y)], fill=col + (255,))
    rnd = random.Random(sum(map(ord, tipo)))
    bokeh = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    db = ImageDraw.Draw(bokeh)
    paleta = {'atardecer': [(255, 200, 120), (255, 150, 90), (255, 230, 170)],
              'ciudad': [(80, 140, 255), (200, 90, 255), (60, 220, 255), (255, 120, 200)],
              'estudio': [(255, 190, 120), (255, 140, 80), (255, 220, 180)]}[tipo]
    for _ in range(22):
        x, y = rnd.uniform(0, w), rnd.uniform(0, h * 0.6)
        r = rnd.uniform(w * 0.03, w * 0.10)
        db.ellipse([x - r, y - r, x + r, y + r], fill=rnd.choice(paleta) + (rnd.randint(40, 110),))
    im = Image.alpha_composite(im, bokeh.filter(ImageFilter.GaussianBlur(w * 0.025)))
    d = ImageDraw.Draw(im)
    if tipo == 'atardecer':
        # sol enorme en el horizonte y cordilleras en capas
        sol = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(sol).ellipse([w * 0.18, h * 0.36, w * 0.82, h * 0.36 + w * 0.64], fill=(255, 214, 140, 255))
        im = Image.alpha_composite(im, sol.filter(ImageFilter.GaussianBlur(w * 0.05)))
        im = Image.alpha_composite(im, sol)
        d = ImageDraw.Draw(im)
        for k, (base, col) in enumerate([(0.62, (92, 46, 60)), (0.70, (52, 26, 44)), (0.80, (20, 12, 24))]):
            pts = [(0, h)]
            for i in range(0, 41):
                x = w * i / 40
                y = h * base - h * 0.07 * abs(math.sin(i * (0.7 + k * 0.3) + k)) - h * 0.03 * math.sin(i * 2.1 + k)
                pts.append((x, y))
            pts.append((w, h))
            d.polygon(pts, fill=col + (255,))
    elif tipo == 'ciudad':
        # skyline con ventanas encendidas
        x = -w * 0.05
        while x < w:
            ancho = rnd.uniform(w * 0.10, w * 0.22)
            alto = rnd.uniform(h * 0.22, h * 0.55)
            y0 = h * 0.86 - alto
            d.rectangle([x, y0, x + ancho, h], fill=(10, 12, 30, 255))
            for vy in range(int(y0 + w * 0.03), int(h * 0.86), max(3, int(w * 0.045))):
                for vx in range(int(x + w * 0.02), int(x + ancho - w * 0.02), max(3, int(w * 0.04))):
                    if rnd.random() < 0.45:
                        col = rnd.choice([(255, 210, 120), (120, 190, 255), (255, 120, 210)])
                        d.rectangle([vx, vy, vx + w * 0.018, vy + w * 0.022], fill=col + (rnd.randint(140, 255),))
            x += ancho + w * 0.01
        d.rectangle([0, h * 0.86, w, h], fill=(6, 8, 20, 255))
    else:
        # estudio de podcast: el microfono a contraluz
        cx, cy = w * 0.56, h * 0.36
        luzc = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(luzc).ellipse([cx - w * 0.5, cy - w * 0.45, cx + w * 0.5, cy + w * 0.55], fill=(255, 170, 90, 120))
        im = Image.alpha_composite(im, luzc.filter(ImageFilter.GaussianBlur(w * 0.12)))
        d = ImageDraw.Draw(im)
        sil = (10, 8, 12, 255)
        d.rounded_rectangle([cx - w * 0.11, cy - w * 0.22, cx + w * 0.11, cy + w * 0.20], radius=int(w * 0.11), fill=sil)
        for k in range(7):
            yy = cy - w * 0.15 + k * w * 0.045
            d.line([cx - w * 0.09, yy, cx + w * 0.09, yy], fill=(60, 44, 40, 255), width=max(1, int(w * 0.008)))
        d.arc([cx - w * 0.17, cy - w * 0.05, cx + w * 0.17, cy + w * 0.30], start=10, end=170, fill=sil, width=int(w * 0.03))
        d.rectangle([cx - w * 0.015, cy + w * 0.28, cx + w * 0.015, h * 0.9], fill=sil)
        d.rounded_rectangle([cx - w * 0.30, h * 0.88, cx + w * 0.30, h * 0.93], radius=int(w * 0.02), fill=sil)
        borde = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(borde).rounded_rectangle([cx - w * 0.115, cy - w * 0.225, cx + w * 0.115, cy + w * 0.205],
                                                radius=int(w * 0.115), outline=(255, 200, 140, 170), width=max(2, int(w * 0.012)))
        im = Image.alpha_composite(im, borde.filter(ImageFilter.GaussianBlur(w * 0.006)))
    # viñeta
    v = Image.new('L', (w, h), 0)
    ImageDraw.Draw(v).ellipse([-w * 0.3, -h * 0.15, w * 1.3, h * 1.15], fill=255)
    v = v.filter(ImageFilter.GaussianBlur(w * 0.12))
    negro = Image.new('RGBA', (w, h), (0, 0, 0, 255))
    return Image.composite(im, negro, v)


def emoji(nombre, lado):
    try:
        e = Image.open(EMOJIS / f'rcs_emoji_{nombre}.png').convert('RGBA')
        return e.resize((lado, lado), Image.Resampling.LANCZOS)
    except OSError:
        return None


def texto_con_sombra(d_img, xy, texto, fuente, color, sombra=6, ancla='mm'):
    x, y = xy
    som = Image.new('RGBA', d_img.size, (0, 0, 0, 0))
    ImageDraw.Draw(som).text((x, y + sombra * 0.4), texto, font=fuente, fill=(0, 0, 0, 200), anchor=ancla)
    d_img.alpha_composite(som.filter(ImageFilter.GaussianBlur(sombra)))
    ImageDraw.Draw(d_img).text((x, y), texto, font=fuente, fill=color, anchor=ancla)


def pantalla(w, h, tipo, lineas, emoji_nombre=None):
    """Un telefono con su fotograma y el subtitulo de 3 lineas (escala x2)."""
    W2, H2 = s(w), s(h)
    marco = Image.new('RGBA', (W2, H2), (0, 0, 0, 0))
    d = ImageDraw.Draw(marco)
    d.rounded_rectangle([0, 0, W2 - 1, H2 - 1], radius=s(30), fill=(10, 12, 18, 255), outline=(90, 110, 150, 255), width=s(2))
    pad = s(7)
    pant = escena(W2 - 2 * pad, H2 - 2 * pad, tipo)
    m = Image.new('L', pant.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, pant.size[0] - 1, pant.size[1] - 1], radius=s(24), fill=255)
    marco.paste(pant, (pad, pad), m)
    # isla de la camara
    d.rounded_rectangle([W2 / 2 - s(22), s(14), W2 / 2 + s(22), s(24)], radius=s(5), fill=(0, 0, 0, 255))
    # subtitulo
    cx = W2 / 2
    y = H2 * 0.56
    anterior = None
    for texto, fuente, color, caja in lineas:
        if anterior is not None:
            # centro a centro: media altura de cada linea + aire (+ el relleno de la caja)
            y += (anterior[0] + fuente.size) * 0.5 * 0.95 + s(4) + (s(6) if (caja or anterior[1]) else 0)
        anterior = (fuente.size, caja)
        if caja:
            bb = ImageDraw.Draw(marco).textbbox((cx, y), texto, font=fuente, anchor='mm')
            caja_capa = Image.new('RGBA', marco.size, (0, 0, 0, 0))
            ImageDraw.Draw(caja_capa).rounded_rectangle([bb[0] - s(9), bb[1] - s(6), bb[2] + s(9), bb[3] + s(6)],
                                                        radius=s(7), fill=caja + (255,))
            brillo = caja_capa.filter(ImageFilter.GaussianBlur(s(10)))
            marco.alpha_composite(brillo)
            marco.alpha_composite(caja_capa)
            ImageDraw.Draw(marco).text((cx, y), texto, font=fuente, fill=color, anchor='mm')
        else:
            texto_con_sombra(marco, (cx, y), texto, fuente, color, sombra=s(4))
    if emoji_nombre:
        e = emoji(emoji_nombre, s(46))
        if e is not None:
            marco.alpha_composite(e, (int(W2 * 0.68), int(H2 * 0.56 - s(70))))
    # reflejo de cristal
    reflejo = Image.new('RGBA', marco.size, (0, 0, 0, 0))
    ImageDraw.Draw(reflejo).polygon([(0, 0), (W2 * 0.55, 0), (W2 * 0.05, H2 * 0.55), (0, H2 * 0.62)], fill=(255, 255, 255, 18))
    marco.alpha_composite(reflejo)
    return marco


def colocar(img, objeto, cx, cy, angulo=0.0, opacidad=1.0, desenfoque=0.0, sombra=True):
    obj = objeto.rotate(angulo, resample=Image.Resampling.BICUBIC, expand=True)
    if desenfoque:
        obj = obj.filter(ImageFilter.GaussianBlur(s(desenfoque)))
    if opacidad < 1:
        obj.putalpha(obj.getchannel('A').point(lambda a: int(a * opacidad)))
    x, y = int(s(cx) - obj.width / 2), int(s(cy) - obj.height / 2)
    if sombra:
        som = Image.new('RGBA', img.size, (0, 0, 0, 0))
        negro = Image.new('RGBA', obj.size, (0, 0, 0, 0))
        negro.putalpha(obj.getchannel('A').point(lambda a: int(a * 0.75)))
        som.alpha_composite(negro, (x + s(10), y + s(22)))
        img = Image.alpha_composite(img, som.filter(ImageFilter.GaussianBlur(s(22))))
    c = Image.new('RGBA', img.size, (0, 0, 0, 0))
    c.alpha_composite(obj, (x, y))
    return Image.alpha_composite(img, c)


def destellos(img):
    """Destellos anamorficos: lineas horizontales finas y largas."""
    c = capa()
    d = ImageDraw.Draw(c)
    for (x, y, largo, col, alfa) in [(1262, 9, 560, CIAN, 200), (1652, 236, 420, AZUL_CLARO, 220),
                                     (1070, 150, 300, VIOLETA, 120), (1450, 118, 260, (255, 200, 150), 110)]:
        d.ellipse([s(x - largo / 2), s(y - 1.4), s(x + largo / 2), s(y + 1.4)], fill=col + (alfa,))
        d.ellipse([s(x - 9), s(y - 9), s(x + 9), s(y + 9)], fill=(255, 255, 255, 230))
    img = Image.alpha_composite(img, c.filter(ImageFilter.GaussianBlur(s(3))))
    return Image.alpha_composite(img, c.filter(ImageFilter.GaussianBlur(s(14))))


def particulas(img):
    c = capa()
    d = ImageDraw.Draw(c)
    rnd = random.Random(5)
    for _ in range(140):
        x = rnd.uniform(760, W)
        y = rnd.uniform(0, H)
        r = rnd.choice([0.8, 1.0, 1.3, 1.8, 2.4])
        col = rnd.choice([BLANCO, CIAN, AZUL_CLARO, VIOLETA, AMBAR])
        d.ellipse([s(x - r), s(y - r), s(x + r), s(y + r)], fill=col + (rnd.randint(90, 230),))
    return Image.alpha_composite(Image.alpha_composite(img, c.filter(ImageFilter.GaussianBlur(s(2.5)))), c)


def boton_go(img):
    cx, cy, r = 1652, 236, 54
    img = luz(img, (cx - r * 1.9, cy - r * 1.9, cx + r * 1.9, cy + r * 1.9), AZUL, 170, 30)
    d = ImageDraw.Draw(img)
    for k, alfa in ((30, 70), (18, 150)):
        d.ellipse([s(cx - r - k), s(cy - r - k), s(cx + r + k), s(cy + r + k)], outline=AZUL_CLARO + (alfa,), width=s(2.5))
    # arco de progreso
    d.arc([s(cx - r - 18), s(cy - r - 18), s(cx + r + 18), s(cy + r + 18)], start=-90, end=150, fill=CIAN + (255,), width=s(4))
    disco = capa()
    dd = ImageDraw.Draw(disco)
    for k in range(int(r), 0, -1):
        t = k / r
        col = tuple(int(a * t + b * (1 - t)) for a, b in zip((10, 60, 200), (110, 170, 255)))
        dd.ellipse([s(cx - k - 6 * (1 - t)), s(cy - k - 8 * (1 - t)), s(cx + k - 6 * (1 - t)), s(cy + k - 8 * (1 - t))], fill=col + (255,))
    img = Image.alpha_composite(img, disco)
    d = ImageDraw.Draw(img)
    tri = [(cx - 7, cy - 31), (cx + 10, cy - 21), (cx - 7, cy - 11)]
    d.polygon([(s(a), s(b)) for a, b in tri], fill=BLANCO)
    d.text((s(cx), s(cy + 12)), 'GO', font=f('Inter_28pt-Black.ttf', 38), fill=BLANCO, anchor='mm')
    return img


def chip_ia(img):
    """La etiqueta «IA local» sobre la pantalla central."""
    fuente = f('Inter_24pt-Bold.ttf', 13)
    texto = 'IA LOCAL  ·  QWEN3'
    d = ImageDraw.Draw(img)
    ancho = d.textlength(texto, font=fuente) / ESC + 40
    x, y = 1260 - ancho / 2, 26
    c = capa()
    ImageDraw.Draw(c).rounded_rectangle([s(x), s(y), s(x + ancho), s(y + 26)], radius=s(13), fill=(12, 26, 60, 230),
                                        outline=CIAN + (200,), width=s(1.4))
    img = Image.alpha_composite(img, c)
    e = emoji('sparkles', s(18))
    if e is not None:
        img.alpha_composite(e, (s(x + 8), s(y + 4)))
    ImageDraw.Draw(img).text((s(x + 30), s(y + 13)), texto, font=fuente, fill=(200, 236, 255), anchor='lm')
    return img


def grano(img):
    ruido = Image.effect_noise((s(W) // 2, s(H) // 2), 24).resize(img.size).convert('L')
    c = Image.merge('RGBA', (ruido, ruido, ruido, Image.new('L', img.size, 9)))
    return Image.alpha_composite(img, c)


# ---------------------------------------------------------------------------------------------------------------------
# v6 (pedido: «mejora el banner»): el banner nuevo gira alrededor del astrolabio de Inicio (se renderiza con el mismo código de la
# app, vectorial), rayos de luz esmeralda, la voz como cinta luminosa y dos tarjetas de cristal con subtítulos virales.
ESM = (58, 230, 140)
ESM_CLARO = (150, 255, 200)
BRONCE = (214, 150, 80)
CODIGO = RAIZ / '1_codigo'


def render_astrolabio(tam=1100):
    """El astrolabio de la pantalla de Inicio, dibujado por la propia app (PySide6) y devuelto como imagen RGBA."""
    import os
    import sys
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    sys.path.insert(0, str(CODIGO))
    from PySide6.QtCore import QPointF
    from PySide6.QtGui import QImage, QPainter
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    import estilos_inicio
    est = estilos_inicio.Astrolabio()
    for _ in range(40):
        est.avanzar(1 / 30.0, 1.0)
    ctx = estilos_inicio.Ctx()
    ctx.t = 3.1
    ctx.entrada = 9.0
    img = QImage(tam, tam, QImage.Format.Format_RGBA8888_Premultiplied)
    img.fill(0)
    p = QPainter(img)
    est.dibujar(p, QPointF(tam / 2, tam / 2), tam * 0.405, ctx, tam * 0.405)
    p.end()
    img = img.convertToFormat(QImage.Format.Format_RGBA8888)
    ptr = img.constBits()
    return Image.frombuffer('RGBA', (tam, tam), bytes(ptr), 'raw', 'RGBA', 0, 1).copy()


def exportar_capas(destino, lado=800):
    """Las capas del astrolabio por separado (runas, engranaje, filigrana y el núcleo fijo) para que el instalador las haga girar."""
    import os
    import sys
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    sys.path.insert(0, str(CODIGO))
    from PySide6.QtCore import QPointF
    from PySide6.QtGui import QImage, QPainter
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    import orbe_mecanica
    orb = orbe_mecanica.OrbeMecanica()
    R = 400.0
    capas = orb._asegurar(R, 1.0)
    destino.mkdir(exist_ok=True)
    for nombre in ('runas', 'engr', 'fili'):
        capas[nombre].scaled(lado, lado, aspectMode=__import__('PySide6.QtCore', fromlist=['Qt']).Qt.AspectRatioMode.IgnoreAspectRatio,
                             mode=__import__('PySide6.QtCore', fromlist=['Qt']).Qt.TransformationMode.SmoothTransformation).save(str(destino / f'astro_{nombre}.png'))
    img = QImage(lado, lado, QImage.Format.Format_RGBA8888_Premultiplied)
    img.fill(0)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    p.translate(lado / 2, lado / 2)
    r = lado / 2.3
    for nombre in ('botones', 'domo'):
        orb._capa(p, capas[nombre], r)
    orb._gema(p, r, 3.1, 0.0, 0.5, 1.0)
    orb._capa(p, capas['vidrio'], r)
    p.end()
    img.save(str(destino / 'astro_nucleo.png'))


def fondo_v6(cx, cy):
    img = Image.new('RGBA', (s(W), s(H)), (3, 8, 9, 255))
    g = Image.linear_gradient('L').rotate(90, expand=True).resize((s(W), s(H)))
    g = ImageChops.invert(g)
    img = Image.composite(Image.new('RGBA', (s(W), s(H)), (6, 24, 24, 255)), img, g)
    img = luz(img, (cx - 520, cy - 420, cx + 520, cy + 420), ESM, 120, 150)
    img = luz(img, (cx - 260, cy - 260, cx + 260, cy + 260), (40, 220, 190), 90, 90)
    img = luz(img, (760, 330, 1100, 640), (230, 140, 50), 60, 90)
    img = luz(img, (1500, -120, 1900, 260), (60, 120, 255), 50, 100)
    return img


def rayos(img, cx, cy):
    """Haces de luz que salen del astrolabio (triángulos finos que se apagan con la distancia)."""
    c = capa()
    d = ImageDraw.Draw(c)
    n = 11
    for i in range(n):
        ang = math.radians(i * 360 / n + 8)
        for largo, ancho, alfa in ((1500, 0.030, 20), (1300, 0.016, 26), (1000, 0.007, 34)):
            pts = [(s(cx), s(cy)), (s(cx + largo * math.cos(ang - ancho)), s(cy + largo * math.sin(ang - ancho))),
                   (s(cx + largo * math.cos(ang + ancho)), s(cy + largo * math.sin(ang + ancho)))]
            d.polygon(pts, fill=ESM + (alfa,))
    m = Image.new('L', c.size, 0)
    ImageDraw.Draw(m).ellipse([s(cx - 760), s(cy - 520), s(cx + 760), s(cy + 520)], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(s(150)))
    c.putalpha(ImageChops.multiply(c.getchannel('A'), m))
    return Image.alpha_composite(img, c.filter(ImageFilter.GaussianBlur(s(1.6))))


def cinta_voz(img, cy):
    c = capa()
    d = ImageDraw.Draw(c)
    for col, ancho, amp, fase in ((ESM_CLARO, 2.2, 36, 0.0), (CIAN, 1.5, 26, 1.4), (AMBAR, 1.2, 46, 2.6)):
        puntos = []
        for i in range(0, 1081, 4):
            x = 690 + i
            env = math.sin(math.pi * i / 1080) ** 1.3
            y = cy + env * amp * math.sin(i / 36 + fase) * math.cos(i / 91 + fase * 0.7)
            puntos.append((s(x), s(y)))
        d.line(puntos, fill=col + (220,), width=s(ancho), joint='curve')
    brillo = c.filter(ImageFilter.GaussianBlur(s(7)))
    img = Image.alpha_composite(img, brillo)
    return Image.alpha_composite(Image.alpha_composite(img, brillo), c)


def tarjeta_cristal(w, h, lineas, radio=22):
    """Una tarjeta de vidrio con un subtítulo viral (líneas: [(texto, fuente, color, caja_o_None)])."""
    W2, H2 = s(w), s(h)
    t = Image.new('RGBA', (W2, H2), (0, 0, 0, 0))
    d = ImageDraw.Draw(t)
    d.rounded_rectangle([0, 0, W2 - 1, H2 - 1], radius=s(radio), fill=(16, 40, 40, 205), outline=(150, 255, 210, 90), width=s(1.6))
    d.rounded_rectangle([s(3), s(3), W2 - s(4), s(h * 0.46)], radius=s(radio - 3), fill=(255, 255, 255, 14))
    y = H2 * 0.20
    anterior = None
    for texto, fuente, color, caja in lineas:
        if anterior is not None:
            y += (anterior[0] + fuente.size) * 0.5 * 0.95 + s(5) + (s(6) if (caja or anterior[1]) else 0)
        anterior = (fuente.size, caja)
        if caja:
            bb = d.textbbox((W2 / 2, y), texto, font=fuente, anchor='mm')
            cc = Image.new('RGBA', t.size, (0, 0, 0, 0))
            ImageDraw.Draw(cc).rounded_rectangle([bb[0] - s(10), bb[1] - s(6), bb[2] + s(10), bb[3] + s(6)], radius=s(8), fill=caja + (255,))
            t.alpha_composite(cc.filter(ImageFilter.GaussianBlur(s(9))))
            t.alpha_composite(cc)
            d.text((W2 / 2, y), texto, font=fuente, fill=color, anchor='mm')
        else:
            texto_con_sombra(t, (W2 / 2, y), texto, fuente, color, sombra=s(4))
    return t


def main():
    cx, cy = 1385, 236
    img = fondo_v6(cx, cy)
    img = rayos(img, cx, cy)
    img = cinta_voz(img, 300)
    # (el astrolabio NO va en la imagen: el instalador lo dibuja girando, capa a capa; ver exportar_capas)
    # tarjetas de subtítulos virales (cristal), a los lados
    mont_b = lambda t: f('Montserrat-Black.ttf', t)
    mont_x = lambda t: f('Montserrat-ExtraBold.ttf', t)
    mont_s = lambda t: f('Montserrat-SemiBold.ttf', t)
    izq = tarjeta_cristal(250, 172, [('ESTO', mont_x(20), BLANCO, None), ('CAMBIA', mont_b(38), (12, 10, 4), AMBAR), ('todo', mont_s(24), VIOLETA, None)])
    der = tarjeta_cristal(200, 150, [('HAZLO EN', mont_x(15), BLANCO, None), ('1 CLIC', mont_b(32), (6, 20, 14), ESM), ('y listo', mont_s(19), ESM_CLARO, None)])
    img = colocar(img, izq, 1040, 150, angulo=7, opacidad=0.97)
    img = colocar(img, der, 1634, 372, angulo=-6, opacidad=0.97)
    for nombre, x, y, lado, ang, blur in [('clapper_board', 905, 372, 56, 12, 1.4), ('sparkles', 1650, 70, 44, -10, 0.0), ('headphone', 1080, 408, 40, -14, 2.0)]:
        e = emoji(nombre, s(lado))
        if e is not None:
            img = colocar(img, e, x, y, angulo=ang, desenfoque=blur, sombra=blur < 1.0)
    img = chip_ia(img)
    # destellos y particulas esmeralda
    c = capa()
    d = ImageDraw.Draw(c)
    for (x, y, largo, col, alfa) in [(cx, 236, 760, ESM, 70), (1050, 62, 380, CIAN, 120), (1500, 430, 320, ESM_CLARO, 100)]:
        d.ellipse([s(x - largo / 2), s(y - 1.4), s(x + largo / 2), s(y + 1.4)], fill=col + (alfa,))
        d.ellipse([s(x - 8), s(y - 8), s(x + 8), s(y + 8)], fill=(255, 255, 255, 220))
    img = Image.alpha_composite(img, c.filter(ImageFilter.GaussianBlur(s(3))))
    pc = capa()
    pd = ImageDraw.Draw(pc)
    rnd = random.Random(9)
    for _ in range(170):
        x, y = rnd.uniform(720, W), rnd.uniform(0, H)
        r = rnd.choice([0.8, 1.0, 1.3, 1.8, 2.4])
        col = rnd.choice([BLANCO, ESM_CLARO, ESM, CIAN, AMBAR])
        pd.ellipse([s(x - r), s(y - r), s(x + r), s(y + r)], fill=col + (rnd.randint(90, 230),))
    img = Image.alpha_composite(Image.alpha_composite(img, pc.filter(ImageFilter.GaussianBlur(s(2.5)))), pc)
    img = grano(img)
    img = img.convert('RGB').resize((W, H), Image.Resampling.LANCZOS)
    img.save(SALIDA, quality=93, optimize=True)
    print('banner ->', SALIDA)
    exportar_capas(SALIDA.parent / 'banner_capas')
    print('capas del astrolabio ->', SALIDA.parent / 'banner_capas')


if __name__ == '__main__':
    main()
