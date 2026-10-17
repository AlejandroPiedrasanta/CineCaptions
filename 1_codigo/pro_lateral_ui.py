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

from PySide6.QtCore import QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFontMetricsF, QPainter, QPainterPath, QPen
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
        _IDS.update(reparto)
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


# ----------------------------------------------------------------------------------------------------------------------- interruptores (derecha)
class PanelMotionsPro(QWidget):
    """La barra cápsula (propuesta «B» que eligió el usuario): una cápsula negra con SOLO los iconos de los motions. El señalado (pasar el ratón)
    lleva una burbuja blanca que se desliza con un resorte y, a su izquierda, su nombre fijo en una píldora blanca (no es un globo: siempre está).
    Clic en un icono = encender / apagar (verde con su punto = GO lo pondrá; gris = apagado). Arriba, la marca de la PRO; abajo, a Efectos."""
    senalada = Signal(str)
    cambiado = Signal()
    BARRA = 66            # ancho de la cápsula
    PASO_MAX = 52         # alto de cada icono
    CABEZA = 70           # sitio de la marca de arriba (y del botón de abajo)

    def __init__(self, ir_efectos=None, padre=None):
        super().__init__(padre)
        self.setFixedWidth(300)
        self.setMinimumHeight(420)
        self.setMouseTracking(True)
        self._ir_efectos = ir_efectos
        self._on = {o['clave']: True for o in OPCIONES}
        self.activa = OPCIONES[0]['clave']
        self._res = ui.Resorte(0.0, 260.0, 26.0)        # la burbuja: índice (float) del icono señalado
        self._encima = None
        self.refrescar()

    # -- estado
    def encendido(self, clave):
        return bool(self._on.get(clave))

    def refrescar(self):
        op = _op()
        for o in OPCIONES:
            self._on[o['clave']] = estado(o['clave'], op)
        self.senalar(self.activa, animar=False)
        self.update()

    def senalar(self, clave, animar=True):
        self.activa = clave
        i = [o['clave'] for o in OPCIONES].index(clave)
        if animar:
            self._res.objetivo = float(i)
            ui.motor_resortes.pedir(self)
        else:
            self._res.poner(float(i))
        self.update()
        self.senalada.emit(clave)

    def paso_resorte(self, dt):
        sigue = self._res.paso(dt)
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
        n = len(OPCIONES)
        paso = max(36.0, min(self.PASO_MAX, (self.height() - 2 * self.CABEZA - 24) / n))
        alto = 2 * self.CABEZA + n * paso
        x = self.width() - self.BARRA - 4
        top = max(0.0, (self.height() - alto) / 2)
        return QRectF(x, top, self.BARRA, alto), paso, top + self.CABEZA

    def _icono_en(self, pos):
        barra, paso, y0 = self._geo()
        if not barra.adjusted(-6, 0, 6, 0).contains(pos):
            return None
        if pos.y() >= barra.bottom() - self.CABEZA + 8:
            return 'efectos'
        i = int((pos.y() - y0) // paso)
        return OPCIONES[i]['clave'] if 0 <= i < len(OPCIONES) else None

    # -- ratón
    def mouseMoveEvent(self, e):
        k = self._icono_en(e.position())
        self.setCursor(Qt.CursorShape.PointingHandCursor if k else Qt.CursorShape.ArrowCursor)
        if k and k != 'efectos' and k != self.activa:
            self.senalar(k)
        if k != self._encima:
            self._encima = k
            self.update()
        super().mouseMoveEvent(e)

    def leaveEvent(self, e):
        self._encima = None
        self.update()
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
    def _icono(self, p, nombre, color, cx, cy, t=20):
        ic = ui.icono_linea(nombre, color)
        if ic is not None:
            p.drawPixmap(int(round(cx - t / 2)), int(round(cy - t / 2)), ic.pixmap(t, t))

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        barra, paso, y0 = self._geo()
        cx = barra.center().x()
        p.setPen(QPen(QColor(255, 255, 255, 20), 1))
        p.setBrush(QColor('#05070C'))
        p.drawRoundedRect(barra, self.BARRA / 2, self.BARRA / 2)
        p.setPen(Qt.PenStyle.NoPen)
        # arriba: la marca de la PRO
        c = QRectF(cx - 20, barra.top() + 14, 40, 40)
        p.setBrush(QColor('#FFFFFF'))
        p.drawEllipse(c)
        self._icono(p, 'ph.sparkle-bold', '#05070C', cx, c.center().y())
        # los iconos: verdes con su punto si GO los pondrá, grises si no
        for i, o in enumerate(OPCIONES):
            cy = y0 + i * paso + paso / 2
            si = self.encendido(o['clave'])
            encima = self._encima == o['clave']
            self._icono(p, o['icono'], ('#7FE0B5' if si else '#4A5670') if not encima else ('#B8F2D8' if si else '#7D8AA5'), cx, cy)
            if si:
                p.setBrush(QColor('#24D18F'))
                p.drawEllipse(QRectF(cx + 14, cy - 14, 6, 6))
        # la burbuja blanca del señalado (se desliza) y su icono en oscuro
        by = y0 + self._res.x * paso + paso / 2
        b = QRectF(cx - 22, by - 22, 44, 44)
        p.setBrush(QColor('#FFFFFF'))
        p.drawEllipse(b)
        o = _POR_CLAVE[self.activa]
        si = self.encendido(self.activa)
        self._icono(p, o['icono'], '#05070C' if si else '#7D8AA5', cx, by)
        # su nombre, fijo a la izquierda de la burbuja: el punto de estado, el nombre y qué hace un clic
        f1, f2 = ui.fuente(13, peso='medio'), ui.fuente(10)
        nombre = tr(o['nombre'])
        sub = tr('Encendido · clic para apagar') if si else tr('Apagado · clic para encender')
        ancho = max(QFontMetricsF(f1).horizontalAdvance(nombre), QFontMetricsF(f2).horizontalAdvance(sub)) + 44
        et = QRectF(max(2.0, barra.left() - ancho - 10), by - 22, ancho, 44)
        p.setBrush(QColor('#FFFFFF'))
        p.drawRoundedRect(et, 22, 22)
        p.setBrush(QColor('#24D18F') if si else QColor('#9AA7BF'))
        p.drawEllipse(QRectF(et.left() + 16, et.center().y() - 4, 8, 8))
        p.setFont(f1)
        p.setPen(QColor('#05070C'))
        p.drawText(QRectF(et.left() + 32, et.top() + 4, ancho - 40, 20), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, nombre)
        p.setFont(f2)
        p.setPen(QColor('#1E7A56' if si else '#6F7C96'))
        p.drawText(QRectF(et.left() + 32, et.top() + 22, ancho - 40, 16), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, sub)
        # abajo: a la página Efectos (uno por uno)
        c = QRectF(cx - 20, barra.bottom() - 54, 40, 40)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor('#FFFFFF') if self._encima != 'efectos' else QColor('#7FE0B5'))
        p.drawEllipse(c)
        self._icono(p, 'ph.sliders-horizontal-bold', '#05070C', cx, c.center().y())


# ----------------------------------------------------------------------------------------------------------------------- ejemplo real (izquierda)
class PanelEjemploPro(QWidget):
    """Un móvil con el ejemplo real del interruptor señalado (en bucle, sin sonido) y, debajo, qué es y si GO lo pondrá. Sin tarjeta de fondo
    (el usuario: «solo el mockup de vista real y abajo la función que está activa»)."""
    TIC_MS = 33

    def __init__(self, padre=None):
        super().__init__(padre)
        self.setFixedWidth(330)
        self.setMinimumHeight(420)
        self._clave = None
        self._reprod = None
        self._poster = {}
        self._encendido = True
        self._reloj = QTimer(self)
        self._reloj.setInterval(self.TIC_MS)
        self._reloj.timeout.connect(self.update)

    def poner(self, clave, encendido):
        self._encendido = bool(encendido)
        if clave != self._clave:
            self._clave = clave
            if self._reprod is not None:
                self._reprod.parar()
                self._reprod = None
            self._arrancar()
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
            from PySide6.QtGui import QImage
            _mp4, jpg = ejemplo(self._clave)
            self._poster[self._clave] = QImage(str(jpg)) if jpg.exists() else None
        return self._poster.get(self._clave)

    def paintEvent(self, _e):
        o = _POR_CLAVE.get(self._clave)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
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
            esc = max(pant.width() / max(1, img.width()), pant.height() / max(1, img.height()))     # cubre la pantalla (sin franjas)
            dw, dh = img.width() * esc, img.height() * esc
            p.drawImage(QRectF(pant.center().x() - dw / 2, pant.center().y() - dh / 2, dw, dh), img)
            video = pant
        else:
            video = pant
            ic = ui.icono_linea(o['icono'] if o else 'ph.play-bold', '#3B4D6E')
            if ic is not None:
                p.drawPixmap(int(pant.center().x() - 24), int(pant.center().y() - 24), ic.pixmap(48, 48))
        if not self._encendido:                                    # apagado: se ve, pero en gris y con «no se pondrá»
            p.fillRect(pant, QColor(8, 12, 22, 150))
        p.restore()
        if marco is not None and not marco.isNull():
            p.drawImage(caja, marco)
        # la etiqueta «Ejemplo real» arriba a la izquierda del video
        f = ui.fuente(10, peso='medio')
        p.setFont(f)
        chip = QRectF(video.left() + 12, video.top() + video.height() * 0.075, 86, 20)        # (debajo de la isla de la cámara)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(0, 0, 0, 140))
        p.drawRoundedRect(chip, 10, 10)
        p.setPen(QColor('#7FE0B5'))
        p.drawText(chip, Qt.AlignmentFlag.AlignCenter, tr('Ejemplo real'))
        if o is None:
            return
        # debajo: el icono y el nombre de la función señalada y, más pequeño, si GO la pondrá
        f = ui.fuente(14, peso='medio')
        p.setFont(f)
        nombre = tr(o['nombre'])
        ancho = QFontMetricsF(f).horizontalAdvance(nombre) + 26
        x0 = caja.center().x() - ancho / 2
        y0 = caja.bottom() + 18
        ic = ui.icono_linea(o['icono'], '#7FE0B5' if self._encendido else '#5F6F8C')
        if ic is not None:
            p.drawPixmap(int(x0), int(y0 + 1), ic.pixmap(18, 18))
        p.setPen(QColor('#FFFFFF' if self._encendido else '#9AA7BF'))
        p.drawText(QRectF(x0 + 26, y0, ancho, 20), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, nombre)
        p.setFont(ui.fuente(11))
        p.setPen(QColor(ui.VERDE if self._encendido else ui.TEXT_MUTED))
        p.drawText(QRectF(0, y0 + 22, self.width(), 18), Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
                   tr('GO lo pondrá en tu video') if self._encendido else tr('Apagado: GO no lo pondrá'))


# ----------------------------------------------------------------------------------------------------------------------- la fila de Proyecto
class FilaPro(QWidget):
    """[ejemplo | slider | interruptores]. Los lados se ven solo con la PRO en juego; con poco ancho se esconde primero el ejemplo y luego la lista."""
    cambiado = Signal()
    ANCHO_EJEMPLO = 1220
    ANCHO_LISTA = 900

    def __init__(self, centro, ir_efectos=None, padre=None):
        super().__init__(padre)
        capa = QHBoxLayout(self)
        capa.setContentsMargins(0, 0, 0, 0)
        capa.setSpacing(14)
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
        self._pro = pro_en_juego()
        if self._pro:
            self.lista.refrescar()
        self._lados()

    def _lados(self):
        w = self.width()
        self.lista.setVisible(self._pro and w >= self.ANCHO_LISTA)
        self.ejemplo.setVisible(self._pro and w >= self.ANCHO_EJEMPLO)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._lados()

    def showEvent(self, e):
        super().showEvent(e)
        self.refrescar()
