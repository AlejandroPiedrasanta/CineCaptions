# CineCaptions · By Cinema Productions
# 1_codigo/estilos_inicio.py — los 3 estilos de la pantalla de Inicio (Nebulosa, Astrolabio, Proceso): el astrolabio de bronce con su escena y su proceso de GO.
"""
v5.49 (el usuario, tras ver las tres propuestas: «me gustan los 3, púlelo más, elimina todos estos y deja estos 3 para que se pueda
escoger, y deja por defecto la opción B»): los 11 estilos de antes (orbe, synthwave, reactor, agujero, líquido, prisma, ecualizador,
plasma, carrete, matrix y el astrolabio de líneas) se quitaron. Quedan tres, los tres con el MISMO botón (el astrolabio de bronce de
`orbe_mecanica`) y cada uno con su escena (lo que hay detrás y alrededor) y su manera de enseñar el proceso de GO:

  nebulosa    luz y volumen: una nebulosa que gira, haces suaves, destellos con profundidad; en GO un remolino del color de cada paso
  astrolabio  (la de fábrica) mecánica celeste: aros de bronce en 3D, anillo horario, constelaciones; en GO cada paso es una estrella
              de una constelación y los aros se alinean uno a uno
  proceso     se ve lo que hace GO: anillo de voz y palabras de cristal; en GO seis tarjetas con su haz de energía, palabras que salen al
              transcribir, captions en Diseño, ondas en Sonido y el timeline que se llena al colocar

Un estilo = `dibujar` (el botón), `fondo` (a 1/3 de resolución, lo escala la escena), `escena` (todo lo demás, a resolución completa:
la llama `EscenaGo.dibujar` con la escena viva) y `onda` (cómo se ven las ondas de choque). La escena real pone encima lo común (chispas,
barra de progreso, destello y, si el estilo los quiere, la lista de pasos y los cometas). Cada estilo trae además su `tema`, su `acento`
y su `aurora` (las 3 luces de fondo de todas las páginas). Lo que no cambia de un cuadro a otro va en sprites ya pintados (`_luz`, las
texturas de la nebulosa, el anillo horario, las palabras de cristal): copiar una imagen cuesta mucho menos que pintar un degradado.
"""
import math
import random

import numpy as np
from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import (QBrush, QColor, QFont, QFontMetricsF, QImage, QLinearGradient, QPainter, QPainterPath,
                           QPen, QPixmap, QPolygonF, QRadialGradient)

from i18n import tr
from qt_kit import fuente

TAU = math.tau
PLUS = QPainter.CompositionMode.CompositionMode_Plus
OVER = QPainter.CompositionMode.CompositionMode_SourceOver
FASE_COL = {'timeline': '#7DFFB2', 'voz': '#4FD8FF', 'ia': '#B388FF', 'diseno': '#FFC46B', 'sfx': '#FF7BD5', 'resolve': '#8FFFD6'}
FASES = ('timeline', 'voz', 'ia', 'diseno', 'sfx', 'resolve')
NOMBRES_PASO = {'timeline': tr('Timeline'), 'voz': tr('Voz'), 'ia': tr('IA'), 'diseno': tr('Diseño'), 'sfx': tr('Sonido'), 'resolve': tr('Resolve')}


def _c(hexa, a=255):
    c = QColor(hexa)
    c.setAlpha(int(max(0, min(255, a))))
    return c


def _suave(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def mezcla(h1, h2, f):
    a, b = QColor(h1), QColor(h2)
    f = max(0.0, min(1.0, f))
    return QColor(int(a.red() + (b.red() - a.red()) * f), int(a.green() + (b.green() - a.green()) * f), int(a.blue() + (b.blue() - a.blue()) * f))


class Ctx:
    """Lo que el botón le cuenta al estilo en cada cuadro."""
    __slots__ = ('estado', 't', 'progreso', 'marca', 'flare', 'hover', 'presion', 'fase', 'fase_t', 'tono', 'vibra', 'apagon',
                 'residuo', 'eta', 'texto', 'entrada', 'vel', 'quieto', 'cierre', 'cortes')

    def __init__(self):
        self.estado = 'listo'
        self.t = 0.0
        self.progreso = 0.0
        self.marca = 0.0
        self.flare = 0.0
        self.hover = 0.0
        self.presion = 0.0
        self.fase = ''
        self.fase_t = 9.0
        self.tono = 'ok'
        self.vibra = 0.0
        self.apagon = 0.0
        self.residuo = 0.0
        self.eta = ''
        self.texto = ''
        self.entrada = 9.0
        self.vel = 1.0
        self.quieto = False
        self.cierre = -1.0
        self.cortes = ()                 # v5.22: dónde acaba cada paso de GO (0..1): el anillo de progreso los marca


# --------------------------------------------------------------------------------------------------- piezas comunes
def cifras(f):
    """v5.22: cifras de ancho fijo (tnum): el porcentaje no baila de lado a lado mientras cuenta."""
    try:
        f.setFeature(QFont.Tag('tnum'), 1)
    except Exception:
        pass
    return f


_CABE = {}


def fuente_que_cabe(texto, ancho, tam, minimo=10, peso='medio', tnum=False):
    """v5.22: la fuente más grande (de `tam` a `minimo` px) con la que `texto` cabe en `ancho` px en UNA línea, o None si ni así cabe
    (el centro del botón la omite: la barra de abajo de Inicio ya lo dice). Con caché: se pide en cada cuadro."""
    clave = (texto, int(ancho), int(tam), int(minimo), peso, tnum)
    if clave in _CABE:
        return _CABE[clave]
    elegida = None
    for t in range(int(tam), int(minimo) - 1, -1):
        f = fuente(t, peso=peso)
        if tnum:
            f = cifras(f)
        if QFontMetricsF(f).horizontalAdvance(texto) <= ancho:
            elegida = f
            break
    if len(_CABE) > 400:
        _CABE.clear()
    _CABE[clave] = elegida
    return elegida


_LUCES = {}
_PERFILES = {'suave': ((0, 255), (0.15, 185), (0.4, 70), (0.7, 18), (1, 0)),
             'bokeh': ((0, 70), (0.70, 95), (0.86, 170), (0.94, 80), (1, 0)),
             'nucleo': ((0, 255), (0.1, 250), (0.22, 120), (0.5, 26), (1, 0)),
             'anillo': ((0, 0), (0.78, 0), (0.88, 200), (0.93, 255), (0.97, 120), (1, 0))}


def _luz(r, hexa, dpr, perfil='suave'):
    """Una luz redonda ya pintada (degradado radial) de radio `r`: se copia en vez de pintar el degradado en cada cuadro."""
    clave = (int(r * 4), hexa, round(dpr, 2), perfil)
    pm = _LUCES.get(clave)
    if pm is not None:
        return pm
    if len(_LUCES) > 700:
        _LUCES.clear()
    r = max(1.0, r)
    n = max(2, int(math.ceil(2 * r * dpr)))
    img = QImage(n, n, QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(Qt.GlobalColor.transparent)
    img.setDevicePixelRatio(dpr)
    q = QPainter(img)
    q.setRenderHint(QPainter.RenderHint.Antialiasing)
    g = QRadialGradient(QPointF(r, r), r)
    base = QColor(hexa)
    for s, a in _PERFILES[perfil]:
        c = QColor(base)
        c.setAlpha(a)
        g.setColorAt(s, c)
    q.setPen(Qt.PenStyle.NoPen)
    q.setBrush(QBrush(g))
    q.drawEllipse(QPointF(r, r), r, r)
    q.end()
    pm = QPixmap.fromImage(img)
    _LUCES[clave] = pm
    return pm


def _poner(p, pm, x, y, alfa=1.0, esc=1.0):
    """Copia un sprite centrado en (x, y) con su opacidad (y escalado si `esc` != 1)."""
    if alfa <= 0.003:
        return
    dw, dh = pm.width() / pm.devicePixelRatio(), pm.height() / pm.devicePixelRatio()
    if alfa < 0.999:
        p.setOpacity(alfa)
    if abs(esc - 1.0) < 1e-3:
        p.drawPixmap(QPointF(x - dw / 2, y - dh / 2), pm)
    else:
        dw, dh = dw * esc, dh * esc
        p.drawPixmap(QRectF(x - dw / 2, y - dh / 2, dw, dh), pm, QRectF(pm.rect()))
    if alfa < 0.999:
        p.setOpacity(1.0)


def _dpr(p):
    d = p.device()
    return d.devicePixelRatioF() if hasattr(d, 'devicePixelRatioF') else 1.0


def _ruido(n, rng, octavas=(4, 8, 16, 32, 64)):
    """Ruido fractal suave en [0, 1] (n x n): octavas de valores al azar interpolados (matriz de pesos: rápido) y difuminados."""
    acc = np.zeros((n, n), np.float32)
    total = 0.0
    for i, o in enumerate(octavas):
        xs = np.linspace(0.0, o, n)
        i0 = np.minimum(xs.astype(int), o - 1)
        f = xs - i0
        f = f * f * (3 - 2 * f)
        m = np.zeros((n, o + 1), np.float32)
        m[np.arange(n), i0] = 1 - f
        m[np.arange(n), i0 + 1] += f
        base = rng.random((o + 1, o + 1)).astype(np.float32)
        w = 1.0 / (1.7 ** i)
        acc += (m @ base @ m.T) * w
        total += w
    acc /= total
    for _ in range(2):
        acc = (np.roll(acc, 2, 0) + acc + np.roll(acc, -2, 0)) / 3
        acc = (np.roll(acc, 2, 1) + acc + np.roll(acc, -2, 1)) / 3
    return (acc - acc.min()) / max(1e-6, float(acc.max() - acc.min()))


def _imagen(rgb, a):
    """numpy rgb (alto, ancho, 3) 0..255 y alfa 0..1 -> QImage ARGB32 premultiplicado."""
    h, w = a.shape
    buf = np.zeros((h, w, 4), np.uint8)
    buf[..., 0] = np.clip(rgb[..., 2] * a, 0, 255)
    buf[..., 1] = np.clip(rgb[..., 1] * a, 0, 255)
    buf[..., 2] = np.clip(rgb[..., 0] * a, 0, 255)
    buf[..., 3] = np.clip(a * 255, 0, 255)
    return QImage(buf.data, w, h, w * 4, QImage.Format.Format_ARGB32_Premultiplied).copy()


def _textura_nube(n, semilla, c1, c2, densidad=1.0):
    rng = np.random.default_rng(semilla)
    f = _ruido(n, rng)
    g = _ruido(n, rng, (3, 6, 12))
    yy, xx = (np.mgrid[0:n, 0:n] / (n - 1)) * 2 - 1
    caida = np.clip(1 - np.sqrt(xx ** 2 + yy ** 2), 0, 1) ** 1.5
    dens = (np.clip((f - 0.30) * 2.0, 0, 1) ** 1.5) * caida * densidad
    m = np.clip(g * 1.5 - 0.25, 0, 1)[..., None]
    rgb = np.array(c1, np.float32) * (1 - m) + np.array(c2, np.float32) * m
    return QPixmap.fromImage(_imagen(rgb, np.clip(dens, 0, 1)))


def _textura_haz(largo=512, ancho=96):
    """Un haz de luz: se apaga a lo largo y es gaussiano a lo ancho (verde claro)."""
    xs = np.linspace(0, 1, largo)[None, :]
    ys = np.linspace(-1, 1, ancho)[:, None]
    a = (1 - xs) ** 1.6 * np.exp(-(ys ** 2) / (0.10 + 0.5 * xs ** 1.2)) * np.clip(xs * 8, 0, 1)
    rgb = np.broadcast_to(np.array((200, 255, 235), np.float32), (ancho, largo, 3))
    return QPixmap.fromImage(_imagen(rgb, a))


class _Escena:
    """Lo que un estilo lee de la escena en cada cuadro (de la real, `EscenaGo`, o de la falsa de las miniaturas)."""
    __slots__ = ('t', 'estado', 'trab', 'en', 'prog', 'fase', 'fcol', 'reap', 'expl', 'pasos', 'hechos', 'fin')

    def __init__(self, e):
        self.t = e._t
        self.estado = e._estado
        self.trab = self.estado in ('trabajando', 'explotando')
        self.en = e.energia
        self.prog = max(0.0, min(1.0, (e.meta - 0.08) / 0.8)) if self.trab else 0.0
        self.fase = e._fase if self.trab else ''
        self.fcol = FASE_COL.get(e._fase, '#7DFFB2') if self.trab else '#7DFFB2'
        self.reap = e.reaparecer if self.estado in ('hecho', 'reposo') else 1.0
        self.expl = e.expl
        self.pasos = e._pasos
        self.fin = self.estado == 'hecho' or self.expl > 0
        self.hechos = 6 if self.fin else sum(1 for s in self.pasos if s['estado'] in ('hecho', 'saltado'))


# --------------------------------------------------------------------------------------------------- estilo base: el astrolabio
class Estilo:
    """El botón GO es el astrolabio de bronce (`orbe_mecanica.OrbeMecanica`, capas cacheadas que giran); la escena la pone cada estilo."""
    clave = ''
    nombre = ''
    descr = ''
    tema = 'noche'                       # superficies de la interfaz: noche | negro | grafito
    acento = '#22B573'                   # color de resaltado de toda la interfaz
    aurora = ('#0B8F5B', '#1D6B7A', '#B8742C')       # las 3 luces del fondo de todas las páginas
    pal = ('#7DFFB2', '#4FFFB0', '#4FD8FF', '#FFFFFF', '#B7FFE0', '#FFD166', '#B388FF', '#FF7BD5', '#FFB35C', '#E6C9FF', '#FFC857', '#FFE3A3')
    modo = 'espiral'                     # cómo se mueven las motas de la escena (EscenaGo._posiciones_particulas)
    perfiles = True                      # las motas usan los perfiles por fase de GO (EscenaGo.PERFIL)
    ensambla = True                      # el astrolabio entra pieza a pieza: BotonGo no lo hace crecer
    pasos_lista = True                   # la lista de pasos de la escena (Proceso pone sus tarjetas)
    cometas = True                       # los cometas que llevan cada paso a su etiqueta

    def __init__(self):
        import orbe_mecanica
        self._orb = orbe_mecanica.OrbeMecanica()
        self._bajo = None
        self._st = None

    def avanzar(self, dt, vel):
        self._orb.avanzar(dt, vel)

    def dibujar(self, p, c, R, ctx, R_base=None):
        self._orb.dibujar(p, c, R, ctx.t, ctx.estado, ctx.hover, ctx.presion, ctx.progreso, ctx.marca, ctx.texto,
                          1.0 if ctx.apagon > 0 else 0.0, ctx.quieto, ctx.flare, R_base, ctx.fase, ctx.fase_t, ctx.tono, ctx.entrada,
                          ctx.vibra, (0.0, 0.0), ctx.residuo, ctx.apagon, ctx.eta, cortes=ctx.cortes)

    # -- la escena
    def escena(self, e, p, W, H, c, Rs, rect):
        """Todo lo del estilo a resolución completa (antes de lo común: chispas, pasos, barra…). `e` = la escena."""
        self._st = _Escena(e)
        self._pintar_fondo(e, p, W, H, c)

    def fondo(self, q, W, H, c, e, t, estado):
        g = QRadialGradient(c, max(W, H) * 0.8)
        g.setColorAt(0.0, QColor(6, 34 + int(36 * e), 30 + int(30 * e)))
        g.setColorAt(0.5, QColor(3, 16, 16))
        g.setColorAt(1.0, QColor(1, 6, 8))
        q.fillRect(QRectF(0, 0, W, H), g)

    def onda(self, e, p, onda, W, H):
        e._dibujar_onda(p, onda, W, H)

    def _pintar_fondo(self, e, p, W, H, c):
        bajo = e._fondo_bajo(W, H, c, e.energia)
        p.drawPixmap(QRectF(-10, -10, W + 20, H + 20), bajo, QRectF(bajo.rect()))

    @staticmethod
    def _vineta(q, W, H, fuerza=170):
        vig = QRadialGradient(QPointF(W / 2, H / 2), max(W, H) * 0.7)
        vig.setColorAt(0.5, QColor(0, 0, 0, 0))
        vig.setColorAt(1.0, QColor(0, 0, 0, fuerza))
        q.fillRect(QRectF(0, 0, W, H), vig)

    @staticmethod
    def _charco(q, c, Rs, hexa, alfa, ancho=2.2):
        """El charco de luz bajo el orbe (una elipse aplastada)."""
        q.save()
        q.translate(c.x(), c.y() + Rs * 1.05)
        q.scale(1.0, 0.22)
        g = QRadialGradient(QPointF(0, 0), Rs * ancho)
        g.setColorAt(0.0, _c(hexa, alfa))
        g.setColorAt(1.0, _c(hexa, 0))
        q.setPen(Qt.PenStyle.NoPen)
        q.setBrush(g)
        q.drawEllipse(QPointF(0, 0), Rs * ancho, Rs * ancho)
        q.restore()

    @staticmethod
    def _sombra(p, c, Rs):
        """Una sombra suave bajo el texto del botón: se lee aunque detrás pase luz."""
        sombra = QRadialGradient(QPointF(0, 0), Rs * 0.95)
        sombra.setColorAt(0.0, QColor(2, 6, 16, 140))
        sombra.setColorAt(1.0, QColor(2, 6, 16, 0))
        p.save()
        p.translate(c.x(), c.y() + Rs * 0.82)
        p.scale(1.0, 0.34)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(sombra)
        p.drawEllipse(QPointF(0, 0), Rs * 0.95, Rs * 0.95)
        p.restore()

    def _onda_suave(self, e, p, onda, hexa=None):
        """Una onda de choque como un anillo de luz que crece (no una línea)."""
        t0, centro, color, grueso, chica = onda
        u = (e._t - t0) / 1.7
        if u < 0 or u > 1:
            return
        Rs = e._geometria()[1]
        r = (Rs * (0.5 + 0.9 * u)) if chica else (Rs * (0.9 + 3.4 * u))
        p.setCompositionMode(PLUS)
        _poner(p, _luz(round(Rs * 0.6) if chica else round(Rs * 1.1), hexa or color, _dpr(p), 'anillo'), centro.x(), centro.y(),
               (1 - u) ** 1.6 * min(1.0, grueso + 0.3), r / (Rs * (0.6 if chica else 1.1)))
        p.setCompositionMode(OVER)


# =================================================================================================== A · NEBULOSA
class Nebulosa(Estilo):
    clave = 'nebulosa'
    nombre = tr('Nebulosa')
    descr = tr('Una nebulosa de luz gira tras el astrolabio. En GO se vuelve un remolino del color de cada paso.')
    aurora = ('#0B8F5B', '#1D6B7A', '#B8742C')
    _NUBES = None
    _HAZ = None
    _TINTE = None

    def __init__(self):
        super().__init__()
        r = random.Random(3)
        self._bokeh = [(r.random(), r.random(), r.uniform(0.2, 1.0), r.uniform(0, TAU), r.choice(('#7DFFB2', '#4FD8FF', '#FFD9A0', '#B7FFE0')))
                       for _ in range(46)]

    @classmethod
    def _texturas(cls):
        """Las tres nubes, la blanca para teñir y el haz: se hacen una vez (numpy, ~20 ms) y las comparten todas las instancias."""
        if cls._NUBES is None:
            cls._NUBES = [_textura_nube(256, 11, (20, 190, 130), (40, 120, 200), 1.0),
                          _textura_nube(256, 23, (10, 140, 160), (220, 150, 60), 0.85),
                          _textura_nube(256, 37, (60, 230, 170), (20, 90, 140), 0.9)]
            cls._HAZ = _textura_haz()
            cls._TINTE = {'_blanca': _textura_nube(256, 51, (255, 255, 255), (210, 210, 210), 1.0)}
        return cls._NUBES

    @classmethod
    def _tinte(cls, hexa):
        """La nube blanca teñida del color (multiplicar y recortar con su propia transparencia), en caché por color."""
        pm = cls._TINTE.get(hexa)
        if pm is None:
            blanca = cls._TINTE['_blanca'].toImage()
            img = blanca.convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)
            q = QPainter(img)
            q.setCompositionMode(QPainter.CompositionMode.CompositionMode_Multiply)
            q.fillRect(img.rect(), QColor(hexa))
            q.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationIn)
            q.drawImage(0, 0, blanca)
            q.end()
            pm = cls._TINTE[hexa] = QPixmap.fromImage(img)
        return pm

    def fondo(self, q, W, H, c, e, t, estado):
        st = self._st
        trab = st.trab if st else False
        prog = st.prog if st else 0.0
        fcol = st.fcol if st else '#7DFFB2'
        reap = st.reap if st else 1.0
        Rs = min(W * 0.28, H * 0.32) if st is None else self._rs
        g = QRadialGradient(c, max(W, H) * 0.75)
        g.setColorAt(0.0, QColor(6, 40 + int(30 * e), 36 + int(20 * e)))
        g.setColorAt(0.45, QColor(3, 18, 20))
        g.setColorAt(1.0, QColor(1, 5, 8))
        q.fillRect(QRectF(0, 0, W, H), g)
        q.setCompositionMode(PLUS)
        # la nebulosa: tres nubes que giran despacio y respiran; en GO se aprietan hacia el orbe y giran cada vez más rápido (un remolino)
        vel = 1.0 + (5.0 + 10.0 * prog) * (1.0 if trab else 0.0)
        for k, nube in enumerate(self._texturas()):
            q.save()
            q.translate(c)
            q.rotate((t * (2.2 + 1.3 * k) * vel * (1 if k % 2 == 0 else -1)) % 360)
            tam = max(W, H) * (0.95 - 0.12 * k) * (1.0 - 0.28 * prog) * (1.0 + 0.04 * math.sin(t * 0.3 + k * 2.0))
            q.setOpacity((0.62 - 0.08 * k) * (0.75 + 0.25 * math.sin(t * 0.4 + k)) * reap)
            q.drawPixmap(QRectF(-tam / 2, -tam / 2 * 0.62, tam, tam * 0.62), nube, QRectF(nube.rect()))
            q.restore()
        # su color: en reposo pasa despacio de esmeralda a turquesa y a ámbar; en GO, el del paso en curso
        if trab:
            tintes = ((fcol, 0.55),)
        else:
            ciclo = (t / 14.0) % 3.0
            i = int(ciclo)
            f = _suave(ciclo - i)
            cols = ('#2FE6A0', '#3FB8FF', '#FFB347')
            tintes = ((cols[i], 0.26 * (1 - f)), (cols[(i + 1) % 3], 0.26 * f))
        for hexa, op in tintes:
            if op < 0.01:
                continue
            q.save()
            q.translate(c)
            q.rotate((-t * (30 if trab else 4)) % 360)
            tam = max(W, H) * (0.62 if trab else 0.85) * (1.0 - 0.3 * prog)
            q.setOpacity(op * reap)
            tn = self._tinte(hexa)
            q.drawPixmap(QRectF(-tam / 2, -tam / 2 * 0.7, tam, tam * 0.7), tn, QRectF(tn.rect()))
            q.restore()
        # haces de luz anchos y suaves que salen del orbe y respiran
        for k in range(7):
            q.save()
            q.translate(c)
            q.rotate((k * 360 / 7 + t * (4.0 + 18.0 * prog)) % 360)
            largo = max(W, H) * (0.42 + 0.06 * math.sin(t * 0.7 + k * 1.7))
            ancho = Rs * (0.9 + 0.35 * math.sin(t * 0.5 + k))
            q.setOpacity((0.16 + 0.10 * math.sin(t * 0.9 + k * 2.1) + 0.18 * e) * reap)
            q.drawPixmap(QRectF(Rs * 0.6, -ancho / 2, largo, ancho), self._HAZ, QRectF(self._HAZ.rect()))
            q.restore()
        q.setOpacity(1.0)
        self._charco(q, c, Rs, fcol, 90 + 70 * e)
        q.setCompositionMode(OVER)
        self._vineta(q, W, H)

    def escena(self, e, p, W, H, c, Rs, rect):
        self._rs = Rs
        super().escena(e, p, W, H, c, Rs, rect)
        st = self._st
        t, trab, reap, fcol, en = st.t, st.trab, st.reap, st.fcol, st.en
        dpr = _dpr(p)
        p.setCompositionMode(PLUS)
        # luces desenfocadas (bokeh) a distintas profundidades: las lejanas, pequeñas y nítidas; las cercanas, grandes y en anillo
        for (bx, by, z, ph, hexa) in self._bokeh:
            x = (bx * W + math.sin(t * 0.11 * (1.5 - z) + ph) * 60 * z + t * 6 * (1.2 - z)) % (W + 80) - 40
            y = (by * H + math.cos(t * 0.09 + ph) * 40 * z - t * 10 * (1.3 - z)) % (H + 80) - 40
            _poner(p, _luz(round(4 + 26 * z), hexa, dpr, 'bokeh' if z > 0.55 else 'nucleo'), x, y,
                   (0.10 + 0.22 * (1 - z)) * (0.6 + 0.4 * math.sin(t * 1.3 + ph * 3)) * reap)
        # las motas de la escena (su movimiento real: espiral hacia el orbe) como luces; en GO con una cola de luz
        pts = self._motas(e)
        if pts is not None:
            x, y, x2, y2, a, idx = pts
            for i in range(len(x)):
                k = int(idx[i])
                z = (k * 37 % 100) / 100.0
                r = 2.5 + 9 * z
                hexa = fcol if (trab and k % 3 == 0) else ('#B7FFE0' if k % 2 else '#7DFFB2')
                al = float(a[i]) * (0.35 + 0.65 * (1 - z * 0.5))
                if trab:
                    for f, s_ in ((0.66, 0.55), (0.33, 0.35)):
                        _poner(p, _luz(round(r * s_ + 1), hexa, dpr, 'nucleo'), x2[i] + (x[i] - x2[i]) * f, y2[i] + (y[i] - y2[i]) * f, al * s_)
                _poner(p, _luz(round(r), hexa, dpr, 'nucleo' if z < 0.6 else 'bokeh'), float(x[i]), float(y[i]), al)
        # un anillo de luz alrededor del orbe y tres luces que orbitan con su estela
        _poner(p, _luz(round(Rs * 1.18), fcol if trab else '#6FE8C0', dpr, 'anillo'), c.x(), c.y(), (0.15 + 0.09 * math.sin(t * 1.4) + 0.16 * en) * reap)
        for k in range(3):
            vel = (0.55 + 0.25 * k) * (1 + 3 * st.prog)
            rx, ry, inc = Rs * (1.55 + 0.25 * k), Rs * (0.42 + 0.06 * k), math.radians((-18, 23, 8)[k])
            for cola in range(7):
                th = t * vel + k * TAU / 3 - cola * 0.045
                ox, oy = rx * math.cos(th), ry * math.sin(th)
                delante = 0.5 + 0.5 * math.sin(th)
                _poner(p, _luz(9 - cola, ('#4FD8FF', '#B7FFE0', '#FFD9A0')[k], dpr, 'nucleo'),
                       c.x() + ox * math.cos(inc) - oy * math.sin(inc), c.y() + ox * math.sin(inc) + oy * math.cos(inc),
                       (0.85 - cola * 0.12) * (0.45 + 0.55 * delante) * reap)
        # en GO el orbe brilla del color del paso y late con la energía; al estallar, una floración de luz
        if trab or getattr(e, '_carga_final', False):
            _poner(p, _luz(round(Rs * 1.7), fcol, dpr, 'suave'), c.x(), c.y(), 0.12 + 0.16 * en + 0.06 * math.sin(t * 6))
        if st.expl > 0:
            _poner(p, _luz(round(Rs * 2.0), '#E8FFF4', dpr, 'suave'), c.x(), c.y(), (1 - st.expl) ** 1.5 * 0.9, 1.0 + 4.0 * st.expl)
        p.setCompositionMode(OVER)

    def onda(self, e, p, onda, W, H):
        self._onda_suave(e, p, onda, self._st.fcol if (self._st and self._st.trab) else None)

    @staticmethod
    def _motas(e):
        return e.posiciones_motas() if hasattr(e, 'posiciones_motas') else None


# =================================================================================================== B · ASTROLABIO (de fábrica)
CONSTELACIONES = (
    ((0.10, 0.20), (0.16, 0.13), (0.23, 0.16), (0.27, 0.10), (0.33, 0.14)),
    ((0.08, 0.62), (0.13, 0.70), (0.19, 0.66), (0.22, 0.76), (0.15, 0.82)),
    ((0.74, 0.12), (0.80, 0.18), (0.86, 0.14), (0.90, 0.22), (0.84, 0.27), (0.80, 0.18)),
    ((0.78, 0.66), (0.84, 0.60), (0.91, 0.64), (0.88, 0.74), (0.94, 0.80)),
    ((0.40, 0.08), (0.45, 0.04), (0.52, 0.07), (0.58, 0.03)),
)
HORAS = ('I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII')


class Astrolabio(Estilo):
    clave = 'astrolabio'
    nombre = tr('Astrolabio')
    descr = tr('Aros de bronce en 3D y constelaciones de oro. En GO cada paso es una estrella y los aros se alinean.')
    aurora = ('#16507A', '#B8862C', '#0B8F5B')

    def __init__(self):
        super().__init__()
        r = random.Random(5)
        self._estrellas = [(r.random(), r.random(), int(r.random() * 4)) for _ in range(340)]
        self._grupos = None
        self._horas = None
        self._fijo = [0.0, 0.0, 0.0]
        self._destello = [-9.0, -9.0, -9.0]

    def fondo(self, q, W, H, c, e, t, estado):
        g = QRadialGradient(c, max(W, H) * 0.8)
        g.setColorAt(0.0, QColor(10, 36 + int(26 * e), 46 + int(20 * e)))
        g.setColorAt(0.5, QColor(4, 14, 26))
        g.setColorAt(1.0, QColor(1, 4, 10))
        q.fillRect(QRectF(0, 0, W, H), g)
        q.setCompositionMode(PLUS)
        via = QLinearGradient(QPointF(0, 0), QPointF(0, 1))                 # una vía láctea tenue en diagonal
        via.setCoordinateMode(QLinearGradient.CoordinateMode.ObjectBoundingMode)
        via.setColorAt(0.0, QColor(0, 0, 0, 0))
        via.setColorAt(0.5, QColor(40, 70, 90, 70))
        via.setColorAt(1.0, QColor(0, 0, 0, 0))
        q.save()
        q.translate(W / 2, H / 2)
        q.rotate(-22)
        q.fillRect(QRectF(-W, -H * 0.22, 2 * W, H * 0.44), via)
        q.restore()
        q.setCompositionMode(OVER)
        self._vineta(q, W, H, 150)

    def _anillo_horas(self, Rz, dpr):
        """El anillo horario (números romanos y marcas de oro), pintado una vez: cada cuadro solo se gira."""
        clave = (round(Rz, 1), round(dpr, 2))
        if self._horas is not None and self._horas[0] == clave:
            return self._horas[1]
        lado = Rz * 2 + 60
        img = QImage(int(lado * dpr), int(lado * dpr), QImage.Format.Format_ARGB32_Premultiplied)
        img.fill(Qt.GlobalColor.transparent)
        img.setDevicePixelRatio(dpr)
        q = QPainter(img)
        q.setRenderHint(QPainter.RenderHint.Antialiasing)
        q.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        q.translate(lado / 2, lado / 2)
        for rr, w_, a in ((Rz - 17, 1.0, 120), (Rz + 17, 1.6, 150), (Rz + 22, 0.8, 80)):
            q.setPen(QPen(_c('#E9C27C', a), w_))
            q.setBrush(Qt.BrushStyle.NoBrush)
            q.drawEllipse(QPointF(0, 0), rr, rr)
        f = QFont('Georgia', 13)
        q.setFont(f)
        for i, ch in enumerate(HORAS):
            q.save()
            q.rotate(i * 30)
            q.setPen(_c('#F3D9A6', 215))
            q.drawText(QRectF(-26, -Rz - 12, 52, 24), int(Qt.AlignmentFlag.AlignCenter), ch)
            q.setPen(QPen(_c('#E9C27C', 150), 1.2))
            q.drawLine(QPointF(0, -Rz + 13), QPointF(0, -Rz + 19))
            for j in range(1, 6):
                q.rotate(5)
                q.drawLine(QPointF(0, -Rz + 16), QPointF(0, -Rz + 19))
            q.restore()
        q.end()
        pm = QPixmap.fromImage(img)
        self._horas = (clave, pm)
        return pm

    @staticmethod
    def _aro(c, R, inc, giro, n=48):
        """Los puntos (x, y, z) de un aro inclinado `inc` (eje x) y girado `giro` (eje y), proyectado."""
        ci, si, cg, sg = math.cos(inc), math.sin(inc), math.cos(giro), math.sin(giro)
        pts = []
        for i in range(n + 1):
            th = i * TAU / n
            x, y = R * math.cos(th), R * math.sin(th)
            y, z = y * ci, y * si
            x, z = x * cg + z * sg, -x * sg + z * cg
            pts.append((c.x() + x, c.y() + y * 0.9, z))
        return pts

    @staticmethod
    def _mitad(pts, delante):
        camino = QPainterPath()
        dentro = False
        for (x, y, z) in pts:
            if (z >= 0) == delante:
                if dentro:
                    camino.lineTo(x, y)
                else:
                    camino.moveTo(x, y)
                    dentro = True
            else:
                dentro = False
        return camino

    def _pintar_aro(self, p, pts, ancho, delante, luz, destello):
        """Un aro de bronce: delante el cuerpo y su brillo (más claro cuanto más alineado), detrás solo el cuerpo, más oscuro.
        (Cada trazo ancho cuesta ~0,3 ms a 3440x1440: dos delante y uno detrás.)"""
        camino = self._mitad(pts, delante)
        if delante:
            capas = ((ancho + 2, '#80522A', 240), (ancho * 0.5, mezcla('#D9A866', '#FFF1D6', 0.5 * luz).name(), 235))
        else:
            capas = ((ancho + 1, '#5A381A', 200),)
        p.setBrush(Qt.BrushStyle.NoBrush)
        k = 1.0 if delante else 0.55
        for w_, hexa, a in capas:
            p.setPen(QPen(_c(hexa, a), w_, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawPath(camino)
        if destello > 0.01:                                           # el aro acaba de alinearse: un relámpago de oro lo recorre
            p.setCompositionMode(PLUS)
            p.setPen(QPen(_c('#FFE2A8', 200 * destello * k), ancho + 6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawPath(camino)
            p.setCompositionMode(OVER)

    def escena(self, e, p, W, H, c, Rs, rect):
        super().escena(e, p, W, H, c, Rs, rect)
        st = self._st
        t, trab, reap, en = st.t, st.trab, st.reap, st.en
        dpr = _dpr(p)
        # estrellas nítidas que titilan por grupos (cuatro llamadas a Qt, no 340; puntos cuadrados sin antialias: a 1-2 px no se nota y
        # cuesta la décima parte)
        if self._grupos is None or self._grupos[0] != (W, H):
            self._grupos = ((W, H), [QPolygonF([QPointF(x * W, y * H) for (x, y, g) in self._estrellas if g == k]) for k in range(4)])
        p.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        for k, pts in enumerate(self._grupos[1]):
            brillo = 0.5 + 0.5 * math.sin(t * (0.8 + k * 0.37) + k * 1.9)
            p.setPen(QPen(_c('#E8F4FF', (60 + 50 * k) * (0.55 + 0.45 * brillo) * reap), 1.0 + 0.5 * k, Qt.PenStyle.SolidLine, Qt.PenCapStyle.SquareCap))
            p.drawPoints(pts)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        # constelaciones de oro que se dibujan, se quedan y se apagan, una tras otra; y alguna estrella fugaz
        p.setCompositionMode(PLUS)
        for k, cons in enumerate(CONSTELACIONES):
            ciclo = (t + k * 2.3) % 11.5
            alfa = (1.0 if ciclo < 7.5 else max(0.0, 1 - (ciclo - 7.5) / 2.0)) * reap
            if alfa <= 0:
                continue
            puntos = [QPointF(x * W, y * H) for x, y in cons]
            tramos = (len(puntos) - 1) * _suave(ciclo / 2.4)
            p.setPen(QPen(_c('#E9C27C', 110 * alfa), 1.1))
            for i in range(len(puntos) - 1):
                f = max(0.0, min(1.0, tramos - i))
                if f > 0:
                    a_, b_ = puntos[i], puntos[i + 1]
                    p.drawLine(a_, a_ + (b_ - a_) * f)
            for i, q_ in enumerate(puntos):
                if tramos >= i - 0.2:
                    _poner(p, _luz(7, '#FFE2A8', dpr, 'nucleo'), q_.x(), q_.y(), alfa * (0.7 + 0.3 * math.sin(t * 2 + i)))
        if t % 9.0 < 0.9:
            f = (t % 9.0) / 0.9
            x0, y0 = W * 0.15 + (int(t / 9) * 0.37 % 1) * W * 0.6, H * 0.08
            for j in range(10):
                g_ = f - j * 0.025
                if g_ > 0:
                    _poner(p, _luz(5 - j * 0.3, '#FFFFFF', dpr, 'nucleo'), x0 + g_ * 380, y0 + g_ * 160, (1 - f) * (1 - j / 10))
        _poner(p, _luz(round(Rs * 1.5), '#2FE6A0', dpr, 'suave'), c.x(), c.y(), (0.10 + 0.10 * en) * reap)
        p.setCompositionMode(OVER)
        # el anillo horario: quieto en reposo (copiarlo sin girar cuesta ~0,1 ms; girado, ~1,5 ms) y en GO gira con la energía
        horas = self._anillo_horas(Rs * 1.62, dpr)
        paso_t = max(0.0, min(0.1, t - getattr(self, '_t_horas', t)))
        self._t_horas = t
        giro_h = getattr(self, '_giro_horas', 0.0)
        if trab:
            giro_h += paso_t * (15.0 + 180.0 * en)
        elif giro_h:                                                   # tras GO termina la vuelta hasta quedar como estaba
            giro_h += paso_t * 25.0
            if giro_h >= 360.0:
                giro_h = 0.0
        self._giro_horas = giro_h = giro_h % 360.0 if trab else giro_h
        if giro_h:
            p.save()
            p.translate(c)
            p.rotate(giro_h)
            d = horas.width() / dpr
            p.setOpacity(0.75 * reap)
            p.drawPixmap(QRectF(-d / 2, -d / 2, d, d), horas, QRectF(horas.rect()))
            p.restore()
            p.setOpacity(1.0)
        else:
            _poner(p, horas, c.x(), c.y(), 0.75 * reap)
        # la esfera armilar: tres aros de bronce en 3D; en GO, cada dos pasos hechos uno se alinea (plano y quieto) con un destello
        vel = 1.0 + (3.5 * en if trab else 0.0)
        aros = []
        for k, (Rk, inc0, w_) in enumerate(((Rs * 1.20, 62, 7), (Rs * 1.36, -48, 6), (Rs * 1.08, 80, 5))):
            fijo = _suave((st.hechos - 2 * k) / 1.5) if (trab or st.fin) else 0.0
            if fijo > 0.97 and self._fijo[k] <= 0.97:
                self._destello[k] = t
            self._fijo[k] = fijo
            inc = math.radians(inc0 * (1 - fijo) + 74 * fijo)
            giro = (t * (0.35 + 0.18 * k) * vel * (1 if k != 1 else -1)) * (1 - fijo)
            aros.append((self._aro(c, Rk, inc, giro), w_, 0.4 + 0.6 * fijo, max(0.0, 1.0 - (t - self._destello[k]) / 0.7)))
        for pts, w_, luz, des in aros:
            self._pintar_aro(p, pts, w_, False, luz, des)
        for pts, w_, luz, des in aros:
            self._pintar_aro(p, pts, w_, True, luz, des)
        # un brillo que recorre el aro de fuera (el metal refleja)
        pts = aros[1][0]
        i = int((t * 9) % len(pts))
        if pts[i][2] >= 0:
            p.setCompositionMode(PLUS)
            _poner(p, _luz(10, '#FFF1D6', dpr, 'nucleo'), pts[i][0], pts[i][1], 0.8 * reap)
            p.setCompositionMode(OVER)
        self._sombra(p, c, Rs)
        if st.pasos and (trab or st.fin):
            self._constelacion_go(p, W, H, c, Rs, st, dpr)
        if st.expl > 0:
            p.setCompositionMode(PLUS)
            _poner(p, _luz(round(Rs * 1.4), '#FFE2A8', dpr, 'anillo'), c.x(), c.y(), 0.55 * (1 - st.expl) ** 1.6, 1.0 + 2.2 * st.expl)
            p.setCompositionMode(OVER)

    def _constelacion_go(self, p, W, H, c, Rs, st, dpr):
        """GO: cada paso es una estrella en un arco sobre el orbe; la activa late y manda luz al orbe; las hechas forman la constelación."""
        t = st.t
        rx = min(W / 2 - 140, Rs * 3.0)
        ry = min(c.y() - 120, Rs * 1.9)
        pos = [QPointF(c.x() + rx * math.cos(math.pi + (i + 0.5) / 6 * math.pi), c.y() + ry * math.sin(math.pi + (i + 0.5) / 6 * math.pi) + Rs * 0.35)
               for i in range(6)]
        estados = [s['estado'] for s in st.pasos[:6]]
        hecho = [est in ('hecho', 'saltado') or st.fin for est in estados]
        p.setCompositionMode(PLUS)
        for i in range(1, len(estados)):
            if hecho[i] and hecho[i - 1]:
                for w_, a in ((7, 40), (1.8, 210)):
                    p.setPen(QPen(_c('#FFD98A', a), w_, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                    p.drawLine(pos[i - 1], pos[i])
        for i, est in enumerate(estados):
            q_ = pos[i]
            hexa = FASE_COL[FASES[i]]
            if est in ('activo', 'cayendo') and not st.fin:
                pul = 0.5 + 0.5 * math.sin(t * 7)
                _poner(p, _luz(40, hexa, dpr, 'suave'), q_.x(), q_.y(), 0.55 + 0.4 * pul)
                _poner(p, _luz(22, hexa, dpr, 'anillo'), q_.x(), q_.y(), 0.9 * (1 - (t * 1.5) % 1.0), 1.0 + 0.6 * ((t * 1.5) % 1.0))
                p.setPen(QPen(_c(hexa, 70), 4.0))
                p.drawLine(q_, c)
                for j in range(7):                                      # paquetes de luz de la estrella al orbe
                    f = (t * 1.3 + j / 7) % 1.0
                    _poner(p, _luz(8, hexa, dpr, 'nucleo'), q_.x() + (c.x() - q_.x()) * f, q_.y() + (c.y() - q_.y()) * f, 0.95 * math.sin(f * math.pi))
            elif hecho[i]:
                _poner(p, _luz(30, '#FFE2A8', dpr, 'suave'), q_.x(), q_.y(), 0.8)
                for ang in (0, 90):                                     # destello de cuatro puntas
                    p.save()
                    p.translate(q_)
                    p.rotate(ang + 45 * math.sin(t * 0.8 + i))
                    p.scale(3.2, 0.32)
                    _poner(p, _luz(9, '#FFF4DC', dpr, 'nucleo'), 0, 0, 0.95)
                    p.restore()
                _poner(p, _luz(7, '#FFFFFF', dpr, 'nucleo'), q_.x(), q_.y(), 1.0)
            else:
                _poner(p, _luz(12, '#9FB6D8', dpr, 'anillo'), q_.x(), q_.y(), 0.55)
                _poner(p, _luz(5, '#C8D8F0', dpr, 'nucleo'), q_.x(), q_.y(), 0.5)
        p.setCompositionMode(OVER)
        p.setFont(QFont('Georgia', 11))
        for i, est in enumerate(estados):
            p.setPen(_c('#F3D9A6', 235 if (est in ('activo', 'cayendo') or hecho[i]) else 110))
            p.drawText(QRectF(pos[i].x() - 70, pos[i].y() + 16, 140, 20), int(Qt.AlignmentFlag.AlignCenter), NOMBRES_PASO[FASES[i]].upper())

    def onda(self, e, p, onda, W, H):
        self._onda_suave(e, p, onda, '#FFD98A')


# =================================================================================================== C · PROCESO
FRASE = ('Hoy', 'te', 'enseño', 'a', 'poner', 'captions', 'en', 'un', 'clic', 'y', 'listo')
PALABRAS_REPOSO = ('Un clic', 'y listo', 'captions', '✨', 'IA', 'VIRAL', '🔥', '3 líneas', '🎬', 'ritmo')
CAPTIONS_DISENO = (('UN CLIC', '#7DFFB2'), ('Y LISTO', '#FFC46B'), ('captions', '#4FD8FF'))
ICONOS_PASO = {'timeline': 'ph.film-strip', 'voz': 'ph.waveform', 'ia': 'ph.sparkle', 'diseno': 'ph.text-aa', 'sfx': 'ph.speaker-high',
               'resolve': 'ph.monitor-play'}


class Proceso(Estilo):
    clave = 'proceso'
    nombre = tr('Proceso')
    descr = tr('Anillo de voz y palabras de cristal. En GO seis tarjetas enseñan cada paso y el timeline se llena.')
    aurora = ('#0B8F5B', '#1D7FA0', '#6B3FB8')
    pasos_lista = False
    cometas = False

    def __init__(self):
        super().__init__()
        r = random.Random(9)
        self._chips_reposo = [(w, r.random(), r.random(), r.uniform(0.55, 1.0), r.uniform(0, TAU)) for w in PALABRAS_REPOSO]
        self._chips = {}
        self._iconos = {}
        self._palabras = []                 # (t0, texto, ángulo, fase)
        self._t_pal = -9.0
        self._bloques = []                  # (t0, i): los captions que bajan al timeline
        self._t_blo = -9.0
        self._t_hecho = None
        self._rnd = random.Random(4)

    def _chip(self, texto, dpr, tam=19, color='#7DFFB2'):
        """Una palabra en una píldora de cristal (con su borde de color y su reflejo), pintada una vez."""
        clave = (texto, round(dpr, 2), tam, color)
        pm = self._chips.get(clave)
        if pm is not None:
            return pm
        f = fuente(tam, peso='extra')
        fm = QFontMetricsF(f)
        w = fm.horizontalAdvance(texto) + tam * 1.8
        h = fm.height() + tam * 0.85
        img = QImage(int((w + 12) * dpr), int((h + 12) * dpr), QImage.Format.Format_ARGB32_Premultiplied)
        img.fill(Qt.GlobalColor.transparent)
        img.setDevicePixelRatio(dpr)
        q = QPainter(img)
        q.setRenderHint(QPainter.RenderHint.Antialiasing)
        q.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        caja = QRectF(6, 6, w, h)
        g = QLinearGradient(caja.topLeft(), caja.bottomLeft())
        g.setColorAt(0, QColor(30, 70, 60, 205))
        g.setColorAt(1, QColor(6, 26, 22, 225))
        q.setBrush(g)
        borde = QLinearGradient(caja.topLeft(), caja.bottomRight())
        borde.setColorAt(0, _c(color, 230))
        borde.setColorAt(1, _c('#4FD8FF', 120))
        q.setPen(QPen(QBrush(borde), 1.4))
        q.drawRoundedRect(caja, h / 2, h / 2)
        q.setPen(QPen(_c('#FFFFFF', 45), 1.0))
        q.drawLine(QPointF(caja.left() + h / 2, caja.top() + 2.5), QPointF(caja.right() - h / 2, caja.top() + 2.5))
        q.setFont(f)
        q.setPen(QColor('#FFFFFF'))
        q.drawText(caja, int(Qt.AlignmentFlag.AlignCenter), texto)
        q.end()
        pm = self._chips[clave] = QPixmap.fromImage(img)
        if len(self._chips) > 120:
            self._chips.clear()
            self._chips[clave] = pm
        return pm

    def _icono(self, clave, hexa, dpr):
        pm = self._iconos.get((clave, hexa))
        if pm is None:
            import qt_kit
            ic = qt_kit.icono_linea(ICONOS_PASO[clave], hexa)
            pm = ic.pixmap(QSize(26, 26), dpr) if ic is not None else QPixmap()
            self._iconos[(clave, hexa)] = pm
        return pm

    def fondo(self, q, W, H, c, e, t, estado):
        st = self._st
        fcol = st.fcol if st else '#7DFFB2'
        Rs = getattr(self, '_rs', min(W * 0.28, H * 0.32))
        g = QRadialGradient(c, max(W, H) * 0.8)
        g.setColorAt(0.0, QColor(6, 40 + int(26 * e), 36 + int(16 * e)))
        g.setColorAt(0.5, QColor(3, 16, 18))
        g.setColorAt(1.0, QColor(1, 5, 8))
        q.fillRect(QRectF(0, 0, W, H), g)
        q.setCompositionMode(PLUS)
        self._charco(q, c, Rs, fcol, 80 + 60 * e, 2.6)
        q.setCompositionMode(OVER)
        q.setPen(QPen(_c('#2E8A72', 26), 1.0))                       # el «suelo» del estudio: una rejilla tenue en perspectiva
        hz = c.y() + Rs * 1.15
        for i in range(-14, 15):
            q.drawLine(QPointF(c.x() + i * 60, hz), QPointF(c.x() + i * 260, H + 40))
        for j in range(1, 7):
            y = hz + (H - hz) * (j / 6) ** 1.8
            q.drawLine(QPointF(0, y), QPointF(W, y))
        self._vineta(q, W, H)

    def _anillo_voz(self, p, c, R0, t, energia, hexa):
        """Una cinta rellena alrededor del orbe cuyo grosor sigue a una «voz» (senoides), con su resplandor."""
        n = 96
        fuera, dentro = [], []
        for i in range(n):
            th = i * TAU / n
            v = (math.sin(th * 3 + t * 2.1) * 0.5 + math.sin(th * 7 - t * 3.3) * 0.35 + math.sin(th * 13 + t * 5.7) * 0.25 * energia
                 + math.sin(th * 19 - t * 8.1) * 0.18 * energia)
            a = (6 + 10 * energia) + (14 + 46 * energia) * max(0.0, v) ** 1.3
            ct, s_ = math.cos(th), math.sin(th)
            fuera.append(QPointF(c.x() + (R0 + a / 2) * ct, c.y() + (R0 + a / 2) * s_))
            dentro.append(QPointF(c.x() + (R0 - a / 2) * ct, c.y() + (R0 - a / 2) * s_))
        borde = QPainterPath()
        borde.addPolygon(QPolygonF(fuera))
        borde.closeSubpath()
        cinta = QPainterPath(borde)                                   # los dos contornos con relleno par-impar (restar caminos es carísimo)
        cinta.addPolygon(QPolygonF(dentro))
        cinta.closeSubpath()
        cinta.setFillRule(Qt.FillRule.OddEvenFill)
        ang = t * 0.7                                                  # el color gira (un degradado lineal que rota: el cónico cuesta el doble)
        u = QPointF(math.cos(ang), math.sin(ang)) * (R0 + 40)
        g = QLinearGradient(c - u, c + u)
        g.setColorAt(0.0, _c(hexa, 210))
        g.setColorAt(0.5, _c('#4FD8FF', 160))
        g.setColorAt(1.0, _c('#B7FFE0', 200))
        p.setPen(QPen(_c(hexa, 45), 9))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(borde)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(g))
        p.drawPath(cinta)

    def _tarjetas(self, p, W, c, Rs, dpr, st):
        """Los seis pasos de GO en tarjetas de cristal (tres a cada lado); la activa, con su haz de energía al orbe."""
        t = st.t
        pasos = {s['clave']: s for s in st.pasos}
        tw, th_ = 236.0, 60.0
        for lado, claves in ((-1, FASES[:3]), (1, FASES[3:])):
            for j, k in enumerate(claves):
                ang = math.radians(-38 + j * 38)
                sep = min(Rs * 2.05 + 120 + 40 * math.cos(ang), W / 2 - tw - 24)          # (en ventanas estrechas no se salen)
                x = c.x() + lado * sep - (tw if lado < 0 else 0)
                caja = QRectF(x, c.y() + Rs * 1.15 * math.sin(ang) - th_ / 2, tw, th_)
                s = pasos.get(k)
                est = s['estado'] if s else 'pendiente'
                activo = est in ('activo', 'cayendo') and not st.fin
                hecho = est in ('hecho', 'saltado') or st.fin
                hexa = FASE_COL[k]
                if activo:
                    ancla = QPointF(caja.right() if lado < 0 else caja.left(), caja.center().y())
                    camino = QPainterPath(ancla)
                    camino.quadTo(QPointF((ancla.x() + c.x()) / 2, ancla.y() - 60), c)
                    p.setBrush(Qt.BrushStyle.NoBrush)
                    for w_, a in ((10, 50), (2.0, 200)):
                        p.setPen(QPen(_c(hexa, a), w_, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                        p.drawPath(camino)
                    p.setCompositionMode(PLUS)
                    for i in range(5):                                  # paquetes de luz hacia el orbe
                        f = (t * 1.2 + i / 5) % 1.0
                        q_ = camino.pointAtPercent(f)
                        _poner(p, _luz(9, hexa, dpr, 'nucleo'), q_.x(), q_.y(), math.sin(f * math.pi))
                    _poner(p, _luz(70, hexa, dpr, 'suave'), caja.center().x(), caja.center().y(), 0.35 + 0.15 * math.sin(t * 6))
                    p.setCompositionMode(OVER)
                g = QLinearGradient(caja.topLeft(), caja.bottomLeft())
                g.setColorAt(0, QColor(24, 60, 54, 215 if (activo or hecho) else 150))
                g.setColorAt(1, QColor(5, 22, 20, 230 if (activo or hecho) else 160))
                p.setBrush(g)
                p.setPen(QPen(_c(hexa, 230) if activo else (_c('#24D18F', 170) if hecho else _c('#5E7A86', 110)), 2.0 if activo else 1.2))
                p.drawRoundedRect(caja, 16, 16)
                if activo:
                    borde = QPainterPath()                               # una luz que recorre el borde
                    borde.addRoundedRect(caja, 16, 16)
                    f = (t * 0.7) % 1.0
                    p.setCompositionMode(PLUS)
                    for i in range(8):
                        q_ = borde.pointAtPercent((f - i * 0.012) % 1.0)
                        _poner(p, _luz(7 - i * 0.6, '#FFFFFF', dpr, 'nucleo'), q_.x(), q_.y(), 1 - i / 8)
                    p.setCompositionMode(OVER)
                    barra = QRectF(caja.left() + 58, caja.bottom() - 11, caja.width() - 74, 3)      # «trabajando»: una barra que corre
                    p.setPen(Qt.PenStyle.NoPen)
                    p.setBrush(_c('#FFFFFF', 30))
                    p.drawRoundedRect(barra, 1.5, 1.5)
                    u = (t * 0.8) % 1.0
                    p.setBrush(_c(hexa, 220))
                    p.drawRoundedRect(QRectF(barra.left() + barra.width() * max(0.0, u - 0.3), barra.top(), barra.width() * min(0.3, u, 1.3 - u), 3), 1.5, 1.5)
                circ = QPointF(caja.left() + 30, caja.center().y())
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(_c('#24D18F', 230) if hecho else _c(hexa, 60))
                p.drawEllipse(circ, 17, 17)
                if hecho:
                    p.setPen(QPen(QColor('#04140C'), 2.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
                    p.drawPolyline([circ + QPointF(-6, 0.5), circ + QPointF(-1.5, 5), circ + QPointF(6.5, -4.5)])
                else:
                    ic = self._icono(k, hexa if activo else '#9FB3C8', dpr)
                    if not ic.isNull():
                        p.drawPixmap(QPointF(circ.x() - 13, circ.y() - 13), ic)
                p.setFont(fuente(16, peso='extra' if activo else 'medio'))
                p.setPen(QColor('#FFFFFF') if (activo or hecho) else QColor('#8FA3B8'))
                p.drawText(QRectF(caja.left() + 58, caja.top() + 6, caja.width() - 64, 26), int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), NOMBRES_PASO[k])
                if not activo:
                    p.setFont(fuente(12))
                    p.setPen(_c('#7F93A8', 210))
                    p.drawText(QRectF(caja.left() + 58, caja.top() + 31, caja.width() - 64, 20), int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                               tr('hecho') if hecho else tr('en espera'))

    def escena(self, e, p, W, H, c, Rs, rect):
        self._rs = Rs
        super().escena(e, p, W, H, c, Rs, rect)
        st = self._st
        t, trab, reap, fcol, en, fase = st.t, st.trab, st.reap, st.fcol, st.en, st.fase
        dpr = _dpr(p)
        p.setCompositionMode(PLUS)
        _poner(p, _luz(round(Rs * 1.5), fcol, dpr, 'suave'), c.x(), c.y(), 0.18 + 0.2 * en)
        p.setCompositionMode(OVER)
        self._anillo_voz(p, c, Rs * 1.18, t, 1.0 if fase == 'voz' else (0.55 if trab else 0.18), fcol)
        self._sombra(p, c, Rs)
        # reposo: palabras de cristal que llegan despacio desde los lados y entran en el orbe
        if st.estado == 'reposo':
            for k, (txt, bx, by, z, ph) in enumerate(self._chips_reposo):
                ciclo = (t * 0.07 + k / len(self._chips_reposo)) % 1.0
                lado = -1 if k % 2 else 1
                y0 = 140 + by * (H - 300)
                x0 = c.x() + lado * (W * 0.40 - bx * W * 0.10)
                f = _suave(ciclo) ** 1.4
                _poner(p, self._chip(txt, dpr), x0 + (c.x() - x0) * f, y0 + (c.y() - y0) * f + math.sin(t * 0.8 + ph) * 12 * (1 - f),
                       (0.45 + 0.55 * z) * min(1.0, ciclo * 8) * (1 - f ** 3) * reap, (1.05 + 0.45 * z) * (1 - 0.8 * f))
        # Voz: las palabras salen del orbe al transcribirse; IA: se vuelven píldoras con ✨; Diseño: captions con su estilo
        if trab and fase in ('voz', 'ia') and t - self._t_pal > (0.22 if fase == 'voz' else 0.35):
            self._t_pal = t
            self._palabras.append((t, FRASE[len(self._palabras) % len(FRASE)], self._rnd.uniform(-0.9, 0.9) + (math.pi if self._rnd.random() < 0.5 else 0), fase))
        self._palabras = [w_ for w_ in self._palabras if t - w_[0] < 2.2]
        for (t0, txt, ang, f_) in self._palabras:
            u = (t - t0) / 2.2
            r = Rs * (1.25 + 1.6 * _suave(u))
            x, y = c.x() + math.cos(ang) * r * 1.5, c.y() + math.sin(ang) * r * 0.6
            al = min(1.0, u * 6) * (1 - u) ** 0.7
            if f_ == 'ia':
                _poner(p, self._chip(txt + (' ✨' if len(txt) > 4 else ''), dpr, 17, '#B388FF'), x, y, al, 0.9 + 0.2 * _suave(u))
            else:
                _poner(p, self._chip(txt, dpr, 15, '#4FD8FF'), x, y, al, 0.85 + 0.15 * _suave(u))
        if trab and fase == 'diseno':
            for i, (txt, col) in enumerate(CAPTIONS_DISENO):
                u = ((t * 0.5) + i / 3) % 1.0
                ang = math.radians(-150 + i * 60 + 20 * math.sin(t * 0.7 + i))
                _poner(p, self._chip(txt, dpr, 24 if i < 2 else 18, col), c.x() + math.cos(ang) * Rs * 2.0, c.y() + math.sin(ang) * Rs * 1.15,
                       min(1.0, u * 5) * (1 - u) ** 0.5, 0.8 + 0.3 * _suave(u))
        if trab and fase == 'sfx':                                      # Sonido: ondas que salen del orbe
            p.setCompositionMode(PLUS)
            for j in range(3):
                f = (t * 0.9 + j / 3) % 1.0
                _poner(p, _luz(round(Rs * 1.3), '#FF7BD5', dpr, 'anillo'), c.x(), c.y(), (1 - f) ** 2 * 0.35, 1.0 + 0.7 * f)
            p.setCompositionMode(OVER)
        self._timeline(p, W, H, c, Rs, st)
        if trab or st.fin:
            self._tarjetas(p, W, c, Rs, dpr, st)
        if st.expl > 0:
            p.setCompositionMode(PLUS)
            _poner(p, _luz(round(Rs * 1.6), '#E8FFF4', dpr, 'suave'), c.x(), c.y(), (1 - st.expl) ** 1.4, 1.0 + 3.5 * st.expl)
            p.setCompositionMode(OVER)

    def _timeline(self, p, W, H, c, Rs, st):
        """Resolve: los captions bajan del orbe a un timeline pequeño que se va llenando; se va cuando entran los contadores del final."""
        t = st.t
        if st.estado != 'hecho':
            self._t_hecho = None
        elif self._t_hecho is None:
            self._t_hecho = t
        alfa = 1.0 if st.estado != 'hecho' else max(0.0, 1.0 - (t - self._t_hecho) / 0.8)
        if st.estado == 'reposo':
            self._bloques = []
        if not (((st.trab and st.fase == 'resolve') or st.fin) and alfa > 0):
            return
        if st.trab and st.fase == 'resolve' and t - self._t_blo > 0.16 and len(self._bloques) < 24:
            self._t_blo = t
            self._bloques.append((t, len(self._bloques)))
        p.setOpacity(alfa)
        tl = QRectF(c.x() - 380, H - 120, 760, 64)
        p.setPen(QPen(_c('#3B5B66', 160), 1.0))
        p.setBrush(QColor(6, 18, 22, 200))
        p.drawRoundedRect(tl, 10, 10)
        p.setFont(fuente(10, peso='medio'))
        for j, (nom, hexa) in enumerate((('V2', '#7DFFB2'), ('V1', '#4FD8FF'), ('A1', '#FFC46B'))):
            y = tl.top() + 6 + j * 18
            p.setPen(_c('#7F93A8'))
            p.drawText(QRectF(tl.left() + 8, y, 24, 16), int(Qt.AlignmentFlag.AlignVCenter), nom)
            if nom != 'V2':
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(_c(hexa, 70))
                p.drawRoundedRect(QRectF(tl.left() + 36, y + 2, tl.width() - 46, 12), 3, 3)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(_c('#7DFFB2', 230))
        for (t0, i) in self._bloques:
            u = _suave(min(1.0, (t - t0) / 0.5))
            x1, y1 = tl.left() + 36 + i * 29, tl.top() + 8
            x0, y0 = c.x() - 10, c.y() + Rs * 0.9
            p.drawRoundedRect(QRectF(x0 + (x1 - x0) * u, y0 + (y1 - y0) * u, 26, 12), 3, 3)
        p.setOpacity(1.0)

    def onda(self, e, p, onda, W, H):
        self._onda_suave(e, p, onda, self._st.fcol if (self._st and self._st.trab) else None)


# --------------------------------------------------------------------------------------------------- registro
ESTILOS = {c.clave: c for c in (Nebulosa, Astrolabio, Proceso)}
ORDEN = tuple(ESTILOS.keys())
POR_DEFECTO = 'astrolabio'               # v5.49: la propuesta B (el usuario: «deja por defecto la opción B»)


def crear(clave):
    """Una instancia NUEVA del estilo (cada botón/miniatura lleva la suya: guardan su propia rotación)."""
    return ESTILOS.get(clave, ESTILOS[POR_DEFECTO])()


def clave_guardada():
    """El estilo elegido en Ajustes › Interfaz; los de antes de la v5.49 (orbe, synthwave…) pasan al de fábrica."""
    try:
        import ajustes_ui
        c = str(ajustes_ui.leer_prefs().get('go_estilo') or POR_DEFECTO)
        return c if c in ESTILOS else POR_DEFECTO
    except Exception:
        return POR_DEFECTO


class _EscenaMini:
    """Una escena de mentira para las miniaturas de Ajustes: lo que el estilo lee de `EscenaGo` (sin motas, ondas ni explosión)."""

    def __init__(self, ctx, W, H, c, Rs, rect):
        self._W, self._H, self._c, self._Rs, self._rect = W, H, c, Rs, rect
        trab = ctx.estado == 'trabajando'
        self._t = ctx.t
        self._estado = 'trabajando' if trab else ('hecho' if ctx.estado == 'hecho' else 'reposo')
        self.energia = 0.3 + 0.5 * ctx.progreso if trab else 0.15
        self.meta = 0.08 + 0.8 * ctx.progreso
        n = min(5, int(ctx.progreso * 6))
        self._fase = FASES[n] if trab else ''
        self._pasos = [{'clave': k, 'estado': ('hecho' if i < n else ('activo' if i == n else 'pendiente'))} for i, k in enumerate(FASES)] if trab else []
        self.expl = 0.0
        self.reaparecer = 1.0
        self._carga_final = False
        self._pviva = None
        self._bajo = None

    def width(self):
        return self._W

    def height(self):
        return self._H

    def _geometria(self):
        return self._c, self._Rs, self._rect

    def _fondo_bajo(self, W, H, c, e):
        w, h = max(8, int(W / 3.0)), max(8, int(H / 3.0))
        if self._bajo is None:
            self._bajo = QPixmap(w, h)
        q = QPainter(self._bajo)
        q.setRenderHint(QPainter.RenderHint.Antialiasing)
        q.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        q.scale(w / float(W), h / float(H))
        self._estilo.fondo(q, W, H, c, e, self._t, self._estado)
        q.end()
        return self._bajo

    def _dibujar_onda(self, p, onda, W, H):
        pass


def dibujar_miniatura(est, ctx, w, h, dpr=1.0, destino=None):
    """Dibuja el estilo `est` (instancia viva) con el contexto `ctx` en un pixmap w x h: la escena y el botón, como en una ventana de
    1000 px de ancho reducida (así se ve igual que en Inicio: tarjetas, aros y palabras en su sitio). Para las tarjetas de Ajustes."""
    pm = destino or QPixmap(int(w * dpr), int(h * dpr))
    pm.setDevicePixelRatio(dpr)
    W = 1000.0
    H = W * h / float(w)
    c = QPointF(W * 0.5, H * 0.46)
    Rs = H * 0.24
    mini = _EscenaMini(ctx, W, H, c, Rs, QRectF(W / 2 - 240, H * 0.8, 480, 200))
    mini._estilo = est
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    p.scale(w / W, h / H)
    est.escena(mini, p, W, H, c, Rs, mini._rect)
    est.dibujar(p, c, Rs * 0.8, ctx, Rs * 0.8)
    p.end()
    return pm


def miniatura(clave, w=320, h=180, t=2.4, estado='listo', dpr=1.0):
    """Una imagen del estilo (escena + botón) para las tarjetas de Ajustes."""
    est = crear(clave)
    ctx = Ctx()
    ctx.t = t
    ctx.estado = estado
    ctx.progreso = 0.62
    for _ in range(int(t * 30)):
        est.avanzar(1 / 30.0, 1.0 if estado == 'listo' else 4.0)
    return dibujar_miniatura(est, ctx, w, h, dpr)
