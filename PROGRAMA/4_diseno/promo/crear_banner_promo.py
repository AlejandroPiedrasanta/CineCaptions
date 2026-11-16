# CineCaptions · By Cinema Productions
# 4_diseno/promo/crear_banner_promo.py — el banner promocional 1280×720 (con los iconos de Windows y Mac en la esquina).
"""
    python 4_diseno/promo/crear_banner_promo.py [salida.png]

Se compone a 2× (2560×1440) y se reduce con LANCZOS (bordes suaves). Usa el logo, las fuentes y las capturas del propio programa; los iconos de Windows y de Apple son SVG
(trazos de Simple Icons, dominio público) que se dibujan con QtSvg.
"""
import os
import sys
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / '1_codigo'))

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ANCHO, ALTO, K = 1280, 720, 2
W, H = ANCHO * K, ALTO * K
VERDE = (39, 224, 138)
BLANCO = (255, 255, 255)
GRIS = (176, 196, 190)

SVG_WINDOWS = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="#FFFFFF" d="M0 3.449L9.75 2.1v9.451H0m10.949-9.602L24 0v11.4H10.949M0 12.6h9.75v9.451L0 20.699M10.949 12.6H24V24l-12.9-1.801"/></svg>'
SVG_APPLE = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="#FFFFFF" d="M12.152 6.896c-.948 0-2.415-1.078-3.96-1.04-2.04.027-3.91 1.183-4.961 3.014-2.117 '
             '3.675-.546 9.103 1.519 12.09 1.013 1.454 2.208 3.09 3.792 3.039 1.52-.065 2.09-.987 3.935-.987 1.831 0 2.35.987 3.96.948 1.637-.026 2.676-1.48 3.676-2.948 1.156-1.688 '
             '1.636-3.325 1.662-3.415-.039-.013-3.182-1.221-3.22-4.857-.026-3.04 2.48-4.494 2.597-4.559-1.429-2.09-3.623-2.324-4.39-2.376-2-.156-3.675 1.09-4.61 1.09zM15.53 '
             '3.83c.843-1.012 1.4-2.427 1.245-3.83-1.207.052-2.662.805-3.532 1.818-.78.896-1.454 2.338-1.273 3.714 1.338.104 2.715-.688 3.559-1.701"/></svg>')


def icono_svg(svg, lado):
    """Un SVG a una imagen RGBA de lado×lado (QtSvg)."""
    from PySide6.QtCore import QByteArray, Qt
    from PySide6.QtGui import QColor, QGuiApplication, QImage, QPainter
    from PySide6.QtSvg import QSvgRenderer
    if QGuiApplication.instance() is None:
        QGuiApplication([])
    r = QSvgRenderer(QByteArray(svg.encode('utf-8')))
    img = QImage(lado, lado, QImage.Format.Format_ARGB32)
    img.fill(QColor(0, 0, 0, 0))
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    r.render(p)
    p.end()
    buf = img.bits().tobytes() if hasattr(img.bits(), 'tobytes') else bytes(img.bits())
    return Image.frombuffer('RGBA', (lado, lado), buf, 'raw', 'BGRA', 0, 1).copy()


def fuente(nombre, tam):
    return ImageFont.truetype(str(RAIZ / '2_recursos' / 'fonts' / nombre), int(tam * K))


def redondeada(im, radio):
    m = Image.new('L', im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width - 1, im.height - 1), radius=int(radio * K), fill=255)
    im = im.convert('RGBA')
    a = ImageChops.multiply(im.split()[3], m)
    im.putalpha(a)
    return im


def con_sombra(lienzo, im, pos, desenfoque=28, color=(0, 0, 0, 170), desp=(0, 18), brillo=None):
    """Pega `im` (RGBA) en `pos` con una sombra suave (y un resplandor opcional del color `brillo`)."""
    pad = int((desenfoque * 3 + 40) * K)
    sombra = Image.new('RGBA', (im.width + pad * 2, im.height + pad * 2), (0, 0, 0, 0))
    capa = Image.new('RGBA', im.size, color)
    capa.putalpha(ImageChops.multiply(im.split()[3], Image.new('L', im.size, color[3])))
    sombra.paste(capa, (pad + int(desp[0] * K), pad + int(desp[1] * K)), im.split()[3])
    sombra = sombra.filter(ImageFilter.GaussianBlur(desenfoque * K))
    if brillo:
        res = Image.new('RGBA', sombra.size, (0, 0, 0, 0))
        r = Image.new('RGBA', im.size, brillo)
        res.paste(r, (pad, pad), im.split()[3])
        res = res.filter(ImageFilter.GaussianBlur(40 * K))
        lienzo.alpha_composite(res, (pos[0] - pad, pos[1] - pad))
    lienzo.alpha_composite(sombra, (pos[0] - pad, pos[1] - pad))
    lienzo.alpha_composite(im, pos)


def girada(im, grados):
    return im.rotate(grados, resample=Image.Resampling.BICUBIC, expand=True)


def texto(g, xy, t, fuente_, relleno, ancla='la'):
    g.text((xy[0] * K, xy[1] * K), t, font=fuente_, fill=relleno, anchor=ancla)


def main(salida):
    # ---- fondo: degradado oscuro verdoso + resplandores
    fondo = Image.new('RGBA', (W, H), (4, 14, 12, 255))
    px = Image.linear_gradient('L').resize((W, H))                          # 0 arriba → 255 abajo
    diag = ImageChops.add(px.rotate(90, expand=False).resize((W, H)), px, scale=2)
    tinte = Image.new('RGBA', (W, H), (10, 54, 42, 255))
    fondo = Image.composite(tinte, fondo, diag.point(lambda v: int(v * 0.55)))
    brillo = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    gb = ImageDraw.Draw(brillo)
    gb.ellipse((int(W * 0.50), int(-H * 0.10), int(W * 1.10), int(H * 0.95)), fill=(39, 224, 138, 70))
    gb.ellipse((int(-W * 0.12), int(H * 0.55), int(W * 0.40), int(H * 1.25)), fill=(30, 140, 220, 38))
    brillo = brillo.filter(ImageFilter.GaussianBlur(120 * K))
    fondo.alpha_composite(brillo)
    g = ImageDraw.Draw(fondo)
    # ---- logo + nombre (arriba izquierda)
    logo = Image.open(RAIZ / '2_recursos' / 'logo_cinecaptions.png').convert('RGBA').resize((92 * K, 92 * K), Image.Resampling.LANCZOS)
    con_sombra(fondo, logo, (64 * K, 46 * K), desenfoque=10, color=(0, 0, 0, 140), desp=(0, 6))
    g = ImageDraw.Draw(fondo)
    texto(g, (176, 92), 'CineCaptions', fuente('Inter-Black.ttf', 46), BLANCO, 'lm')
    texto(g, (178, 124), 'BY CINEMA PRODUCTIONS', fuente('Inter_18pt-Medium.ttf', 15), GRIS, 'lm')

    # ---- titular
    f_t = fuente('Inter-Black.ttf', 72)
    texto(g, (64, 236), 'Subtítulos animados', f_t, BLANCO, 'ls')
    texto(g, (64, 318), 'con IA, en ', f_t, BLANCO, 'ls')
    ancho_ia = g.textlength('con IA, en ', font=f_t) / K
    texto(g, (64 + ancho_ia, 318), '1 clic', f_t, VERDE, 'ls')
    texto(g, (66, 368), 'Directo en DaVinci Resolve', fuente('Inter_18pt-Medium.ttf', 28), GRIS, 'ls')

    # ---- tres ventajas con marca verde
    f_b = fuente('Inter_18pt-Medium.ttf', 29)
    for i, linea in enumerate(('IA 100% local y privada', 'Estilos, efectos y música listos', 'Sin límites ni pagar por minuto')):
        y = 442 + i * 56
        g.ellipse(((66) * K, (y - 18) * K, (102) * K, (y + 18) * K), fill=(39, 224, 138, 255))
        g.line((75 * K, y * K, 82 * K, (y + 7) * K), fill=(5, 30, 20), width=4 * K, joint='curve')
        g.line((82 * K, (y + 7) * K, 94 * K, (y - 8) * K), fill=(5, 30, 20), width=4 * K, joint='curve')
        texto(g, (118, y), linea, f_b, (232, 245, 240), 'lm')

    # ---- ventana del programa (captura) y teléfono con captions
    cap = Image.open(RAIZ / 'DOCUMENTACION' / 'capturas' / '01_inicio.png').convert('RGBA').resize((500 * K, int(500 * 900 / 1400) * K), Image.Resampling.LANCZOS)
    cap = redondeada(cap, 16)
    borde = Image.new('RGBA', cap.size, (0, 0, 0, 0))
    ImageDraw.Draw(borde).rounded_rectangle((0, 0, cap.width - 1, cap.height - 1), radius=16 * K, outline=(255, 255, 255, 60), width=2 * K)
    cap.alpha_composite(borde)
    cap = girada(cap, 4)
    con_sombra(fondo, cap, (int(668 * K), int(352 * K)), desenfoque=26, color=(0, 0, 0, 190), desp=(0, 22), brillo=(39, 224, 138, 70))

    tel = Image.open(RAIZ / '2_recursos' / 'vistas_slider' / 'Referencia.jpg').convert('RGBA').resize((292 * K, int(292 * 864 / 486) * K), Image.Resampling.LANCZOS)
    tel = redondeada(tel, 30)
    marco = Image.new('RGBA', tel.size, (0, 0, 0, 0))
    ImageDraw.Draw(marco).rounded_rectangle((0, 0, tel.width - 1, tel.height - 1), radius=30 * K, outline=(255, 255, 255, 235), width=5 * K)
    tel.alpha_composite(marco)
    tel = girada(tel, -5)
    con_sombra(fondo, tel, (int(940 * K), int(136 * K)), desenfoque=30, color=(0, 0, 0, 200), desp=(0, 26), brillo=(39, 224, 138, 90))

    # ---- esquina: iconos de Windows y Mac
    g = ImageDraw.Draw(fondo)
    px0, py0, px1, py1 = 1010, 30, 1236, 96
    pill = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    gp = ImageDraw.Draw(pill)
    gp.rounded_rectangle((px0 * K, py0 * K, px1 * K, py1 * K), radius=33 * K, fill=(255, 255, 255, 30), outline=(255, 255, 255, 90), width=2 * K)
    fondo.alpha_composite(pill)
    lado = 40 * K
    win = icono_svg(SVG_WINDOWS, lado)
    mac = icono_svg(SVG_APPLE, lado)
    fondo.alpha_composite(win, (int(1034 * K), int(43 * K)))
    fondo.alpha_composite(mac, (int(1084 * K), int(43 * K)))
    g = ImageDraw.Draw(fondo)
    texto(g, (1140, 52), 'WINDOWS', fuente('Inter-Black.ttf', 15), BLANCO, 'lm')
    texto(g, (1140, 76), '+ MAC', fuente('Inter-Black.ttf', 15), VERDE, 'lm')

    # ---- botón inferior
    g.rounded_rectangle((64 * K, 640 * K, 340 * K, 696 * K), radius=28 * K, fill=VERDE)
    texto(g, (202, 668), 'Pruébalo hoy', fuente('Inter-Black.ttf', 26), (4, 28, 18), 'mm')
    texto(g, (362, 668), 'Windows y Mac · Apple Silicon e Intel', fuente('Inter_18pt-Medium.ttf', 19), GRIS, 'lm')

    final = fondo.resize((ANCHO, ALTO), Image.Resampling.LANCZOS).convert('RGB')
    final.save(salida, optimize=True)
    return salida


if __name__ == '__main__':
    destino = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name('CineCaptions_banner_1280x720.png')
    print(main(destino))
