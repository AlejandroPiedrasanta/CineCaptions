# CineCaptions · By Cinema Productions
# 1_codigo/pro_lateral_ui.py — Proyecto con la Edición PRO: a la DERECHA del slider, los motions que GO pondrá (interruptores) y, a la IZQUIERDA,
# un móvil con el ejemplo REAL del que se señala (v5.5.10).
"""
El usuario: «en la página de Proyecto, cuando se active el modo PRO, salgan a los laterales los motions que quiero que aplique (píldora abajo de
captions, B-roll, Magic Mask, Motions completo, intro con overlays…) y al lado izquierdo un ejemplo real de cómo se vería; conectado a la página de
Efectos para que no se contradigan».

    OPCIONES                 -> los interruptores, en el orden en que se enseñan
    ids_de(clave)            -> los motions del catálogo (motions_catalogo) que enciende/apaga ese interruptor
    estado(clave, op=None)   -> bool
    poner(clave, si)         -> guarda en las MISMAS preferencias que la página Efectos (pro_motions_modo / pro_motions, pro_internet,
                                pro_mascara, pro_motions_completo) con edicion_pro.guardar_opciones; Efectos las vuelve a leer al abrirse
    FilaPro(carrusel, …)     -> [ejemplo | slider | interruptores]; los lados solo con la PRO en juego (interruptor o Temas 5/6)

Cada interruptor de motions es un GRUPO del carrusel de Efectos: apagarlo en Automático pasa a «Solo los que elija» con todos menos ese grupo;
encenderlo los vuelve a marcar y, si quedan todos, vuelve a Automático. Nunca deja la lista vacía (motions_catalogo.modo la trataría como «todos»).
Los ejemplos: 2_recursos/edicion_pro/ejemplos_pro/<clave>.mp4 (+ .jpg), hechos con herramientas_dev/hacer_ejemplos_pro.py.
"""
from pathlib import Path

from PySide6.QtCore import QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFontMetricsF, QImage, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QHBoxLayout, QSizePolicy, QWidget

import qt_kit as ui
from i18n import tr

OPCIONES = [
    {'clave': 'pildora', 'nombre': 'Píldora bajo captions', 'icono': 'ph.pill-bold', 'motions': ['acompanante'],
     'detalle': 'Una píldora animada justo debajo del texto con el lugar, la cifra o el emoji de lo que dices.'},
    {'clave': 'broll', 'nombre': 'B-roll con fotos', 'icono': 'ph.image-bold', 'motions': ['escena:foto'], 'pref': 'pro_internet',
     'detalle': 'Fotos de internet con licencia a pantalla completa cuando nombras algo.'},
    {'clave': 'detras', 'nombre': 'Captions detrás de ti', 'icono': 'ph.user-focus-bold', 'mascara': True,
     'detalle': 'Se recorta a la persona (IA local o Magic Mask) y el texto pasa por detrás.'},
    {'clave': 'motions_completo', 'nombre': 'Motions completo', 'icono': 'ph.film-strip-bold', 'pref': 'pro_motions_completo',
     'detalle': 'Un video de motions encima de todo: el titular palabra a palabra y una tarjeta por idea.'},
    {'clave': 'gancho', 'nombre': 'Gancho del inicio', 'icono': 'ph.lightning-bold', 'motions': ['ograf:titular', 'ograf:orbita', 't5:orbita', 't5:sticker'],
     'detalle': 'Los primeros segundos: un titular detrás de ti e iconos que giran alrededor de tu cabeza.'},
    {'clave': 'escenas', 'nombre': 'Escenas completas', 'icono': 'ph.frame-corners-bold',
     'detalle': 'Cuaderno, chat, polaroid, calendario… a pantalla completa cuando cuentas algo.'},
    {'clave': 'kit', 'nombre': 'Kit de motions', 'icono': 'ph.stack-bold',
     'detalle': 'Listas, ruletas, títulos neón y cajas misterio sobre el video.'},
    {'clave': 'graficos', 'nombre': 'Gráficos', 'icono': 'ph.chart-bar-bold',
     'detalle': 'Cifras, mapas con bandera, marcos de cámara y llamadas a la acción.'},
    {'clave': 'plantillas', 'nombre': 'Plantillas por frase', 'icono': 'ph.chat-circle-text-bold',
     'detalle': '«¡Hola amigos!», «Guárdalo», encuestas… justo cuando dices esa frase.'},
]
_POR_CLAVE = {o['clave']: o for o in OPCIONES}
_IDS = {}


def carpeta_ejemplos() -> Path:
    try:
        import edicion_pro
        return Path(edicion_pro.carpeta_recursos()) / 'ejemplos_pro'
    except Exception:
        return Path(__file__).resolve().parent.parent / '2_recursos' / 'edicion_pro' / 'ejemplos_pro'


def ejemplo(clave):
    """(mp4, jpg) del ejemplo real de un interruptor (pueden no existir)."""
    c = carpeta_ejemplos()
    return c / f'{clave}.mp4', c / f'{clave}.jpg'


# ----------------------------------------------------------------------------------------------------------------------- estado
def _catalogo_ids():
    try:
        import motions_catalogo as MC
        return [(m['id'], m['grupo']) for m in MC.catalogo()]
    except Exception:
        return []


def ids_de(clave):
    """Los motions del catálogo de ese interruptor: los nombrados y, del resto, por su grupo (Temas 5/6: escena y foco → escenas; lo demás → gráficos)."""
    if not _IDS:
        todos = _catalogo_ids()
        validos = {i for i, _g in todos}
        nombrados = {}
        for o in OPCIONES:
            for i in o.get('motions') or []:
                if i in validos:
                    nombrados[i] = o['clave']
        reparto = {k: [i for i, c in nombrados.items() if c == k] for k in _POR_CLAVE}
        destino = {'escena': 'escenas', 'kit': 'kit', 'grafico': 'graficos', 'plantilla': 'plantillas'}
        for i, g in todos:
            if i in nombrados:
                continue
            k = destino.get(g) or ('escenas' if i in ('t5:escena', 't5:foco') else 'graficos')
            reparto[k].append(i)
        if todos:                                 # (si el catálogo no cargó, no se guarda vacío: se reintenta la próxima vez)
            _IDS.update(reparto)
        return list(reparto.get(clave) or [])
    return list(_IDS.get(clave) or [])


def _op():
    try:
        import edicion_pro
        return edicion_pro.opciones_guardadas()
    except Exception:
        return {}


def estado(clave, op=None):
    o = _POR_CLAVE[clave]
    op = _op() if op is None else op
    if o.get('mascara'):
        return str(op.get('pro_mascara') or 'auto') != 'no'
    ids = ids_de(clave) if o.get('motions') is not None or 'pref' not in o else []
    try:
        import motions_catalogo as MC
        motion = any(MC.permitido(i, op) for i in ids) if ids else True
    except Exception:
        motion = True
    if o.get('pref'):
        return bool(op.get(o['pref'], o['pref'] == 'pro_internet')) and motion
    return motion


def poner(clave, si):
    """Guarda el interruptor. Devuelve False si no se pudo (apagar el último grupo de motions dejaría la lista vacía = «todos»)."""
    import edicion_pro
    import motions_catalogo as MC
    o = _POR_CLAVE[clave]
    op = edicion_pro.opciones_guardadas()
    cambios = {}
    if o.get('mascara'):
        antes = str(op.get('pro_mascara') or 'auto')
        cambios['pro_mascara'] = (antes if antes != 'no' else 'auto') if si else 'no'
    if o.get('pref'):
        cambios[o['pref']] = bool(si)
    ids = ids_de(clave) if (o.get('motions') is not None or 'pref' not in o) and not o.get('mascara') else []
    if ids:
        todos = [i for i, _g in _catalogo_ids()]
        lista = [i for i in (op.get('pro_motions') or []) if i in set(todos)] if MC.modo(op) == 'elegidos' else list(todos)
        if si:
            lista += [i for i in ids if i not in lista]
        else:
            fuera = set(ids)
            lista = [i for i in lista if i not in fuera]
            if not lista:
                return False
        if set(lista) >= set(todos):
            cambios.update(pro_motions_modo='auto', pro_motions=[])
        else:
            cambios.update(pro_motions_modo='elegidos', pro_motions=lista)
    edicion_pro.guardar_opciones(cambios)
    return True


def pro_en_juego():
    try:
        import edicion_pro
        return bool(edicion_pro.en_juego())
    except Exception:
        return False


# ----------------------------------------------------------------------------------------------------------------------- dibujo común
_PIX = {}


def _pix(nombre, color, tam, dpr):
    """El icono de línea ya rasterizado (cacheado): qt_kit.icono_linea crea el QIcon y dibuja el glifo en cada llamada, y estos paneles se
    repintan a 30–60 fps mientras animan."""
    clave = (nombre, color, int(tam), round(float(dpr), 2))
    pm = _PIX.get(clave)
    if pm is None:
        ic = ui.icono_linea(nombre, color)
        pm = ic.pixmap(QSize(int(tam), int(tam)), float(dpr)) if ic is not None else QPixmap()
        if len(_PIX) > 600:
            _PIX.clear()
        _PIX[clave] = pm
    return pm


def _icono(p, w, nombre, color, cx, cy, tam, opacidad=1.0, escala=1.0):
    pm = _pix(nombre, color, tam, w.devicePixelRatioF())
    if pm.isNull() or opacidad <= 0.01:
        return
    t = tam * escala
    p.save()
    p.setOpacity(p.opacity() * min(1.0, opacidad))
    p.drawPixmap(QRectF(cx - t / 2, cy - t / 2, t, t), pm, QRectF(pm.rect()))
    p.restore()


# ----------------------------------------------------------------------------------------------------------------------- interruptores (derecha)
class PanelMotionsPro(QWidget):
    """La barra cápsula (propuesta «B» que eligió el usuario): una cápsula negra con SOLO los iconos de los motions. El señalado (pasar el ratón)
    lleva una burbuja blanca que se desliza con un resorte y, a su izquierda, su nombre fijo en una píldora blanca (no es un globo: siempre está).
    Clic en un icono = encender / apagar (verde con su punto = GO lo pondrá; gris = apagado). Arriba, la marca de la PRO; abajo, a Efectos.
    v5.5.10 animaciones (todo con Resorte + motor_resortes, pintado): el punto verde salta con rebote al encender y se encoge al apagar, el
    icono pasa de gris a verde con un fundido, crece un poco con el ratón encima, la píldora del nombre ajusta su ancho y funde el texto, y la
    barra entra deslizándose al activar la PRO."""
    senalada = Signal(str)
    cambiado = Signal()
    BARRA = 66            # ancho de la cápsula (a escala 1)
    PASO_MAX = 52         # alto de cada icono
    CABEZA = 70           # sitio de la marca de arriba (y del botón de abajo)
    ETIQUETA = 230        # sitio de la píldora con el nombre, a la izquierda de la cápsula

    def __init__(self, ir_efectos=None, padre=None):
        super().__init__(padre)
        self._s = 1.0
        self.setMinimumHeight(320)
        self.setMouseTracking(True)
        self._ir_efectos = ir_efectos
        self._on = {o['clave']: True for o in OPCIONES}
        self._k = {o['clave']: ui.Resorte(1.0, 420.0, 17.0) for o in OPCIONES}      # 0 apagado → 1 encendido (rebota un poco al llegar)
        self._hov = {o['clave']: ui.Resorte(0.0, 520.0, 30.0) for o in OPCIONES}
        self._hov['efectos'] = ui.Resorte(0.0, 520.0, 30.0)
        self.activa = OPCIONES[0]['clave']
        self._res = ui.Resorte(0.0, 260.0, 26.0)        # la burbuja: índice (float) del icono señalado
        self._et_w = ui.Resorte(0.0, 340.0, 30.0)       # ancho de la píldora del nombre
        self._et_f = ui.Resorte(1.0, 260.0, 26.0)       # 0 → 1: fundido del texto viejo al nuevo
        self._et_txt = None                              # (nombre, sub, encendido) de ahora y el de antes
        self._et_prev = None
        self._entrada = ui.Resorte(1.0, 150.0, 21.0)
        self._encima = None
        self.poner_escala(1.0)
        self.refrescar(animar=False)

    def poner_escala(self, s):
        """v5.5.10 («que se vea coherente en tamaños»): la barra crece y se achica con el slider (FilaPro le da la escala por el alto)."""
        s = max(0.75, min(1.6, float(s)))
        cambio = abs(s - self._s) > 0.004 or not self.minimumWidth()
        self._s = s
        if cambio:
            self.setFixedWidth(int(round(self.BARRA * s + 14 + self.ETIQUETA * min(s, 1.25))))
            if self._et_txt is not None:
                self._et_w.poner(self._ancho_etiqueta(*self._et_txt[:2]))
            self.update()

    def entrar(self):
        """La barra entra deslizándose desde la derecha (al activar la PRO)."""
        self._entrada.poner(0.0)
        self._entrada.objetivo = 1.0
        ui.motor_resortes.pedir(self)

    # -- estado
    def encendido(self, clave):
        return bool(self._on.get(clave))

    def refrescar(self, animar=True):
        op = _op()
        for o in OPCIONES:
            k = o['clave']
            self._on[k] = estado(k, op)
            self._k[k].objetivo = 1.0 if self._on[k] else 0.0
            if not animar:
                self._k[k].poner(self._k[k].objetivo)
        self.senalar(self.activa, animar=animar)
        if animar:
            ui.motor_resortes.pedir(self)
        self.update()

    def _fuentes(self):
        se = min(self._s, 1.25)
        return ui.fuente(13 * se, peso='medio'), ui.fuente(10 * se), se

    def _ancho_etiqueta(self, nombre, sub):
        f1, f2, se = self._fuentes()
        return max(QFontMetricsF(f1).horizontalAdvance(nombre), QFontMetricsF(f2).horizontalAdvance(sub)) + 44 * se

    def _texto_etiqueta(self):
        o = _POR_CLAVE[self.activa]
        si = self.encendido(self.activa)
        return tr(o['nombre']), (tr('Encendido · clic para apagar') if si else tr('Apagado · clic para encender')), si

    def senalar(self, clave, animar=True):
        self.activa = clave
        i = [o['clave'] for o in OPCIONES].index(clave)
        nuevo = self._texto_etiqueta()
        if nuevo != self._et_txt:
            self._et_prev, self._et_txt = self._et_txt, nuevo
            ancho = self._ancho_etiqueta(*nuevo[:2])
            if animar and self._et_prev is not None:
                self._et_f.poner(0.0)
                self._et_f.objetivo = 1.0
                self._et_w.objetivo = ancho
            else:
                self._et_f.poner(1.0)
                self._et_w.poner(ancho)
        if animar:
            self._res.objetivo = float(i)
            ui.motor_resortes.pedir(self)
        else:
            self._res.poner(float(i))
        self.update()
        self.senalada.emit(clave)

    def paso_resorte(self, dt):
        sigue = False
        for r in [self._res, self._et_w, self._et_f, self._entrada] + list(self._k.values()) + list(self._hov.values()):
            sigue = r.paso(dt) or sigue
        self.update()
        return sigue

    def _tocar(self, clave):
        si = not self.encendido(clave)
        ok = False
        try:
            ok = poner(clave, si)
        except Exception:
            import registro
            registro.excepcion(origen='Proyecto · motions de la PRO')
        if not ok and not si:
            import registro
            registro.aviso(tr('La Edición PRO necesita al menos un tipo de motion. Para no poner ninguno, apaga la Edición PRO.'), 'edición pro')
        self.refrescar()
        self.cambiado.emit()

    # -- geometría
    def _geo(self):
        """(cápsula, paso entre iconos, y del primer icono)."""
        n, s = len(OPCIONES), self._s
        cabeza = self.CABEZA * s
        paso = max(30.0 * s, min(self.PASO_MAX * s, (self.height() - 2 * cabeza - 24) / n))
        alto = 2 * cabeza + n * paso
        x = self.width() - self.BARRA * s - 4
        top = max(0.0, (self.height() - alto) / 2)
        return QRectF(x, top, self.BARRA * s, alto), paso, top + cabeza

    def _icono_en(self, pos):
        barra, paso, y0 = self._geo()
        if not barra.adjusted(-6, 0, 6, 0).contains(pos):
            return None
        if pos.y() >= barra.bottom() - self.CABEZA * self._s + 8:
            return 'efectos'
        i = int((pos.y() - y0) // paso)
        return OPCIONES[i]['clave'] if 0 <= i < len(OPCIONES) else None

    # -- ratón
    def _poner_encima(self, k):
        if k == self._encima:
            return
        if self._encima in self._hov:
            self._hov[self._encima].objetivo = 0.0
        self._encima = k
        if k in self._hov:
            self._hov[k].objetivo = 1.0
        ui.motor_resortes.pedir(self)

    def mouseMoveEvent(self, e):
        k = self._icono_en(e.position())
        self.setCursor(Qt.CursorShape.PointingHandCursor if k else Qt.CursorShape.ArrowCursor)
        if k and k != 'efectos' and k != self.activa:
            self.senalar(k)
        self._poner_encima(k)
        super().mouseMoveEvent(e)

    def leaveEvent(self, e):
        self._poner_encima(None)
        super().leaveEvent(e)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            k = self._icono_en(e.position())
            if k == 'efectos':
                if self._ir_efectos is not None:
                    self._ir_efectos()
            elif k:
                self.senalar(k)
                self._tocar(k)
        super().mousePressEvent(e)

    # -- dibujo
    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        e = max(0.0, min(1.0, self._entrada.x))
        if e < 0.999:                                   # la entrada: desde la derecha y apareciendo
            p.setOpacity(e)
            p.translate((1.0 - e) * 36.0 * self._s, 0.0)
        s = self._s
        barra, paso, y0 = self._geo()
        cx = barra.center().x()
        t_ic = int(round(20 * s))
        p.setPen(QPen(QColor(255, 255, 255, 20), 1))
        p.setBrush(QColor('#05070C'))
        p.drawRoundedRect(barra, barra.width() / 2, barra.width() / 2)
        p.setPen(Qt.PenStyle.NoPen)
        # arriba: la marca de la PRO
        c = QRectF(cx - 20 * s, barra.top() + 14 * s, 40 * s, 40 * s)
        p.setBrush(QColor('#FFFFFF'))
        p.drawEllipse(c)
        _icono(p, self, 'ph.sparkle-bold', '#05070C', cx, c.center().y(), t_ic)
        # los iconos: verdes con su punto si GO los pondrá, grises si no (fundido entre los dos al cambiar)
        for i, o in enumerate(OPCIONES):
            k = o['clave']
            cy = y0 + i * paso + paso / 2
            on = max(0.0, min(1.0, self._k[k].x))
            esc = 1.0 + 0.16 * max(0.0, self._hov[k].x)
            if on < 0.99:
                _icono(p, self, o['icono'], '#4A5670', cx, cy, t_ic, 1.0 - on, esc)
            if on > 0.01:
                _icono(p, self, o['icono'], '#7FE0B5', cx, cy, t_ic, on, esc)
            r = 3.0 * s * max(0.0, self._k[k].x)        # (el resorte pasa de 1 al llegar: el punto rebota)
            if r > 0.2:
                p.setBrush(QColor('#24D18F'))
                p.drawEllipse(QRectF(cx + 17 * s - r, cy - 11 * s - r, 2 * r, 2 * r))
        # la burbuja blanca del señalado (se desliza) y su icono en oscuro
        by = y0 + self._res.x * paso + paso / 2
        rb = min(22 * s, paso / 2 - 1)
        p.setBrush(QColor('#FFFFFF'))
        p.drawEllipse(QRectF(cx - rb, by - rb, 2 * rb, 2 * rb))
        o = _POR_CLAVE[self.activa]
        on = max(0.0, min(1.0, self._k[self.activa].x))
        _icono(p, self, o['icono'], '#7D8AA5', cx, by, t_ic, 1.0 - on)
        _icono(p, self, o['icono'], '#05070C', cx, by, t_ic, on)
        # su nombre, fijo a la izquierda de la burbuja: el punto de estado, el nombre y qué hace un clic (el texto viejo se va, el nuevo entra)
        f1, f2, se = self._fuentes()
        alto = 44 * se
        ancho = max(alto, self._et_w.x)
        et = QRectF(max(2.0, barra.left() - ancho - 10 * s), by - alto / 2, ancho, alto)
        p.setBrush(QColor('#FFFFFF'))
        p.drawRoundedRect(et, alto / 2, alto / 2)
        p.save()
        p.setClipRect(et.adjusted(4, 2, -4, -2))
        f = max(0.0, min(1.0, self._et_f.x))
        for txt, op, dy in ((self._et_prev, 1.0 - f, -6.0 * f), (self._et_txt, f, 6.0 * (1.0 - f))):
            if txt is None or op <= 0.01:
                continue
            nombre, sub, si = txt
            p.setOpacity(op * e)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor('#24D18F') if si else QColor('#9AA7BF'))
            p.drawEllipse(QRectF(et.left() + 16 * se, et.center().y() - 4 * se + dy, 8 * se, 8 * se))
            izq = et.left() + 32 * se
            p.setFont(f1)
            p.setPen(QColor('#05070C'))
            p.drawText(QRectF(izq, et.top() + 4 * se + dy, 400, 20 * se), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, nombre)
            p.setFont(f2)
            p.setPen(QColor('#1E7A56' if si else '#6F7C96'))
            p.drawText(QRectF(izq, et.top() + 22 * se + dy, 400, 16 * se), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, sub)
        p.restore()
        # abajo: a la página Efectos (uno por uno)
        c = QRectF(cx - 20 * s, barra.bottom() - 54 * s, 40 * s, 40 * s)
        h = max(0.0, self._hov['efectos'].x)
        c = c.adjusted(-2 * s * h, -2 * s * h, 2 * s * h, 2 * s * h)
        p.setPen(Qt.PenStyle.NoPen)
        blanco, menta = QColor('#FFFFFF'), QColor('#7FE0B5')
        p.setBrush(QColor(int(blanco.red() + (menta.red() - blanco.red()) * h), int(blanco.green() + (menta.green() - blanco.green()) * h),
                          int(blanco.blue() + (menta.blue() - blanco.blue()) * h)))
        p.drawEllipse(c)
        _icono(p, self, 'ph.sliders-horizontal-bold', '#05070C', cx, c.center().y(), t_ic)


# ----------------------------------------------------------------------------------------------------------------------- ejemplo real (izquierda)
class PanelEjemploPro(QWidget):
    """Un móvil con el ejemplo real del interruptor señalado (en bucle, sin sonido) y, debajo, qué es y si GO lo pondrá. Sin tarjeta de fondo
    (el usuario: «solo el mockup de vista real y abajo la función que está activa»). v5.5.10 animaciones: al cambiar de motion el clip viejo se
    funde con el nuevo y el nombre de debajo entra deslizándose; apagar/encender atenúa la pantalla con suavidad; el panel entra desde la
    izquierda al activar la PRO. El marco del móvil se escala UNA vez por tamaño (antes, en cada fotograma: 30 por segundo)."""
    TIC_MS = 33

    def __init__(self, padre=None):
        super().__init__(padre)
        self.setFixedWidth(330)                        # (FilaPro lo ajusta: el móvil tan alto como la tarjeta del centro del slider)
        self.setMinimumHeight(300)
        self._clave = None
        self._reprod = None
        self._poster = {}
        self._encendido = True
        self._anterior = None                          # el último cuadro del clip de antes (para el fundido) y su texto
        self._prev_txt = None
        self._fundido = ui.Resorte(1.0, 190.0, 24.0)
        self._apagado = ui.Resorte(0.0, 260.0, 26.0)
        self._entrada = ui.Resorte(1.0, 150.0, 21.0)
        self._marco = None                             # (ancho, alto, dpr, QPixmap)
        self._reloj = QTimer(self)
        self._reloj.setInterval(self.TIC_MS)
        self._reloj.timeout.connect(self.update)

    def entrar(self):
        """El panel entra desde la izquierda (al activar la PRO)."""
        self._entrada.poner(0.0)
        self._entrada.objetivo = 1.0
        ui.motor_resortes.pedir(self)

    def paso_resorte(self, dt):
        sigue = False
        for r in (self._fundido, self._apagado, self._entrada):
            sigue = r.paso(dt) or sigue
        if not sigue:
            self._anterior = None
        self.update()
        return sigue

    def poner(self, clave, encendido):
        self._apagado.objetivo = 0.0 if encendido else 1.0
        if self._encendido != bool(encendido):
            ui.motor_resortes.pedir(self)
        if clave != self._clave:
            if self._clave is not None and self.isVisible():
                img = self._cuadro()
                self._anterior = img.copy() if img is not None and not img.isNull() else None
                self._prev_txt = (self._clave, self._encendido)
                self._fundido.poner(0.0)
                self._fundido.objetivo = 1.0
                ui.motor_resortes.pedir(self)
            self._clave = clave
            if self._reprod is not None:
                self._reprod.parar()
                self._reprod = None
            self._arrancar()
        if self._clave is not None and not self.isVisible():
            self._apagado.poner(self._apagado.objetivo)
        self._encendido = bool(encendido)
        self.update()

    def _arrancar(self):
        if not self.isVisible() or self._clave is None:
            return
        mp4, _jpg = ejemplo(self._clave)
        if mp4.exists():
            import vistas_slider
            self._reprod = vistas_slider.Reproductor(mp4, pausa_s=0.4)
            self._reprod.arrancar()
            if not self._reloj.isActive():
                self._reloj.start()

    def showEvent(self, e):
        super().showEvent(e)
        if self._reprod is None:
            self._arrancar()
        elif not self._reprod.activo:
            self._reprod.arrancar()
        if self._reprod is not None:
            self._reloj.start()

    def hideEvent(self, e):
        super().hideEvent(e)
        self._reloj.stop()
        if self._reprod is not None:
            self._reprod.parar()

    def _cuadro(self):
        img = self._reprod.imagen() if self._reprod is not None else None
        if img is not None:
            return img
        if self._clave not in self._poster:
            _mp4, jpg = ejemplo(self._clave)
            self._poster[self._clave] = QImage(str(jpg)) if jpg.exists() else None
        return self._poster.get(self._clave)

    def _marco_pm(self, marco, caja):
        dpr = self.devicePixelRatioF()
        w, h = int(round(caja.width() * dpr)), int(round(caja.height() * dpr))
        if self._marco is None or self._marco[:3] != (w, h, round(dpr, 2)):
            pm = QPixmap.fromImage(marco.scaled(w, h, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation))
            pm.setDevicePixelRatio(dpr)
            self._marco = (w, h, round(dpr, 2), pm)
        return self._marco[3]

    @staticmethod
    def _cubrir(p, img, pant):
        esc = max(pant.width() / max(1, img.width()), pant.height() / max(1, img.height()))     # cubre la pantalla (sin franjas)
        dw, dh = img.width() * esc, img.height() * esc
        p.drawImage(QRectF(pant.center().x() - dw / 2, pant.center().y() - dh / 2, dw, dh), img)

    def paintEvent(self, _e):
        o = _POR_CLAVE.get(self._clave)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        e = max(0.0, min(1.0, self._entrada.x))
        if e < 0.999:                                              # la entrada: desde la izquierda y apareciendo
            p.setOpacity(e)
            p.translate(-(1.0 - e) * 36.0, 0.0)
        abajo = 58                                                 # la función activa, justo debajo del móvil (van juntos, centrados en el alto)
        disponible = QRectF(self.rect()).adjusted(10, 8, -10, -abajo - 8)
        # el MISMO móvil que Creativo (2_recursos/creativo/movil_marco.png, ~9:19,5 como uno de verdad) y su pantalla LLENA con el ejemplo, que ya
        # se hace a esa proporción (hacer_ejemplos_pro; el usuario: «que encaje bien el mockup, no franjas negras»)
        marco, info, _foto = ui.MarcoVista._recursos_movil()
        asp = float(info.get('aspecto') or 0.5)
        h = min(disponible.height(), disponible.width() / asp)
        w = h * asp
        caja = QRectF(disponible.center().x() - w / 2, disponible.top() + (disponible.height() - h) / 2, w, h)
        a = info.get('pantalla') or [0.0625, 0.0272, 0.9363, 0.9728]
        pant = QRectF(caja.left() + a[0] * w, caja.top() + a[1] * h, (a[2] - a[0]) * w, (a[3] - a[1]) * h)
        radio = float(info.get('radio') or 0.127) * pant.width()
        pantalla = QPainterPath()
        pantalla.addRoundedRect(pant, radio, radio)
        p.save()
        p.setClipPath(pantalla)
        p.fillRect(pant, QColor('#05080F'))
        img = self._cuadro() if o is not None else None
        if img is not None and not img.isNull():
            self._cubrir(p, img, pant)
        elif o is not None:
            _icono(p, self, o['icono'], '#3B4D6E', pant.center().x(), pant.center().y(), 48)
        f = max(0.0, min(1.0, self._fundido.x))
        if self._anterior is not None and f < 0.999:              # el clip de antes se va fundiendo encima del nuevo
            p.save()
            p.setOpacity(p.opacity() * (1.0 - f))
            self._cubrir(p, self._anterior, pant)
            p.restore()
        apagado = max(0.0, min(1.0, self._apagado.x))
        if apagado > 0.01:                                         # apagado: se ve, pero atenuado y con «no se pondrá»
            p.fillRect(pant, QColor(8, 12, 22, int(150 * apagado)))
        p.restore()
        if marco is not None and not marco.isNull():
            p.drawPixmap(caja.topLeft(), self._marco_pm(marco, caja))
        # la etiqueta «Ejemplo real» arriba a la izquierda del video
        p.setFont(ui.fuente(10, peso='medio'))
        chip = QRectF(pant.left() + 12, pant.top() + pant.height() * 0.075, 86, 20)        # (debajo de la isla de la cámara)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(0, 0, 0, 140))
        p.drawRoundedRect(chip, 10, 10)
        p.setPen(QColor('#7FE0B5'))
        p.drawText(chip, Qt.AlignmentFlag.AlignCenter, tr('Ejemplo real'))
        if o is None:
            return
        # debajo: el icono y el nombre de la función señalada y, más pequeño, si GO la pondrá (el de antes sube y se va, el nuevo entra)
        fuente_n, fuente_s = ui.fuente(14, peso='medio'), ui.fuente(11)
        y0 = caja.bottom() + 18
        textos = [(self._clave, self._encendido, f, 8.0 * (1.0 - f))]
        if self._prev_txt is not None and f < 0.999:
            textos.insert(0, (self._prev_txt[0], self._prev_txt[1], 1.0 - f, -8.0 * f))
        base = p.opacity()
        for clave, enc, op, dy in textos:
            oo = _POR_CLAVE.get(clave)
            if oo is None or op <= 0.01:
                continue
            p.setOpacity(base * op)
            nombre = tr(oo['nombre'])
            ancho = QFontMetricsF(fuente_n).horizontalAdvance(nombre) + 26
            x0 = caja.center().x() - ancho / 2
            _icono(p, self, oo['icono'], '#7FE0B5' if enc else '#5F6F8C', x0 + 9, y0 + dy + 10, 18)
            p.setFont(fuente_n)
            p.setPen(QColor('#FFFFFF' if enc else '#9AA7BF'))
            p.drawText(QRectF(x0 + 26, y0 + dy, ancho, 20), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, nombre)
            p.setFont(fuente_s)
            p.setPen(QColor(ui.VERDE if enc else ui.TEXT_MUTED))
            p.drawText(QRectF(0, y0 + 22 + dy, self.width(), 18), Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
                       tr('GO lo pondrá en tu video') if enc else tr('Apagado: GO no lo pondrá'))


# ----------------------------------------------------------------------------------------------------------------------- la fila de Proyecto
class FilaPro(QWidget):
    """[ejemplo | slider | interruptores]. Los lados se ven solo con la PRO en juego. v5.5.10 («que se vea coherente en tamaños»): crecen y
    se achican CON el slider: el móvil, tan alto como su tarjeta del centro; la barra, a la escala del alto de la fila. Con poco sitio se
    esconde primero el ejemplo y luego la barra."""
    cambiado = Signal()
    ESPACIO = 14
    TEXTO_MOVIL = 74          # lo que ocupa, debajo del móvil, el nombre de la función (y los márgenes del panel)
    MOVIL_MIN = 300           # más bajo que esto el móvil no se lee: se esconde
    CENTRO_MIN = 420          # sitio mínimo para el slider
    ANCHO_LISTA = 860

    def __init__(self, centro, ir_efectos=None, padre=None):
        super().__init__(padre)
        capa = QHBoxLayout(self)
        capa.setContentsMargins(0, 0, 0, 0)
        capa.setSpacing(self.ESPACIO)
        self.ejemplo = PanelEjemploPro()
        self.lista = PanelMotionsPro(ir_efectos=ir_efectos)
        capa.addWidget(self.ejemplo)
        capa.addWidget(centro, 1)
        capa.addWidget(self.lista)
        centro.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.lista.senalada.connect(self._senalada)
        self.lista.cambiado.connect(self._cambio)
        self._pro = False
        self.refrescar()

    def _senalada(self, clave):
        self.ejemplo.poner(clave, self.lista.encendido(clave))

    def _cambio(self):
        self._senalada(self.lista.activa)
        self.cambiado.emit()

    def refrescar(self):
        """Vuelve a leer si la PRO está en juego y los interruptores (pueden haber cambiado en Inicio o en Efectos)."""
        antes = self._pro
        self._pro = pro_en_juego()
        if self._pro:
            self.lista.refrescar()
        self._lados()
        if self._pro and not antes and self.isVisible():          # la PRO se acaba de activar: los lados entran animados
            for lado in (self.ejemplo, self.lista):
                if lado.isVisible():
                    lado.entrar()

    def _lados(self):
        w, h = self.width(), self.height()
        self.lista.poner_escala(h / 620.0)
        ver_lista = self._pro and w >= self.ANCHO_LISTA
        lista = self.lista.width() + self.ESPACIO if ver_lista else 0
        # el móvil, del alto de la tarjeta del centro: la misma cuenta que CarruselPacks._medidas con el ancho que le quedaría al slider
        try:
            import estilos_slider as ES
            _marco, info, _foto = ui.MarcoVista._recursos_movil()
            asp = float(info.get('aspecto') or 0.5)
            paso, controles = ES.CarruselPacks.PASO, ES.CarruselPacks.ALTO_CONTROLES
        except Exception:
            ES, asp, paso, controles = None, 0.5, 0.94, 0
        alto_max = max(0.0, h - self.TEXTO_MOVIL)
        movil = alto_max
        for _ in range(4):                        # (el ancho del móvil quita sitio al slider, que achica su tarjeta: se busca el punto fijo)
            centro = w - lista - (movil * asp + 20 + self.ESPACIO)
            carta = max(0.0, centro - 32.0) / (0.88 + 2.0 * paso) / (ES.ASPECTO if ES else 0.5625)
            movil = max(0.0, min(alto_max, h - controles - 16.0, 1040.0, carta))
        ancho_ej = int(round(movil * asp + 20))
        ver_ej = self._pro and movil >= self.MOVIL_MIN and (w - lista - ancho_ej - self.ESPACIO) >= self.CENTRO_MIN
        if ver_ej and self.ejemplo.width() != ancho_ej:
            self.ejemplo.setFixedWidth(ancho_ej)
        self.lista.setVisible(ver_lista)
        self.ejemplo.setVisible(ver_ej)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._lados()

    def showEvent(self, e):
        super().showEvent(e)
        self.refrescar()
