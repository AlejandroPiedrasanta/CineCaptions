# CineCaptions · By Cinema Productions
# 1_codigo/crea_estilo_ui.py — «Crea tu estilo»: la galería de 48 ejemplos (con su vista real de Resolve) para armar un pack en un clic y el popup que explica la estructura de nombres.
"""
Dos ventanas:

  * CreaEstiloDialogo : 48 ejemplos (30 con Luxe Shine de principal y 18 con un preset de Amro.Films Captions) de posición × tipografía × colores, cada uno con su imagen
    REAL: renderizada por Resolve (vistas_guia.py; se hace sola al abrir si Resolve está conectado, o con «Vista real · Resolve»). Se tocan hasta 3 (serán las variantes 1, 2 y 3 del
    pack), se le pone nombre y «Crear mi pack» lo arma en el acto con los macros reales del Luxe Title Pack. «Abrir los 30 en Resolve» arma además
    un timeline con todos (efectos Luxe Shine y Luxe Slide de verdad) para retocarlos allí. Los ejemplos y su imagen viven en ejemplos_estilo.py.
  * AyudaEstilo       : el popup del «!»: por qué los clips se llaman principal / arriba / abajo / simple, qué son principal 2 y principal 3,
    qué pasa si falta una pieza y cómo se exporta. Con dibujos, porque «sin esa estructura el estilo no funciona».
"""
from PySide6.QtCore import QRectF, Qt, QTimer
from PySide6.QtGui import QPainter, QPen
from PySide6.QtWidgets import QFrame, QGridLayout, QSizePolicy, QVBoxLayout, QWidget

import ejemplos_estilo as E
import qt_kit as ui
from qt_kit import Boton, Desplazable, Dialogo, Entrada, Etiqueta, Segmentado, StringVar, Tooltip, caja_h, despues
from qt_kit import QColor
from i18n import tr

AMARILLO = '#FDE047'
VERDE = '#34D399'
ROJO = '#FB7185'
AMBAR = ui.AMBAR
TEXT_MUTED = ui.TEXT_MUTED


def _hoja(css):
    return ui.traducir_hoja(css)


# ====================================================================================== la galería
class _Tarjeta(QWidget):
    """Un ejemplo: su vista REAL de Resolve REPRODUCIÉNDOSE en bucle (la animación de entrada de verdad, con fundido entre fotogramas, y el resultado final
    sostenido), su nombre, su posición y un botón «Vista real · Resolve» que carga SOLO ese estilo en la línea de tiempo. Tocarlo lo elige (1.º, 2.º o 3.º =
    variante 1, 2 o 3). Sin fotogramas reales todavía, se enseña la aproximación pintada."""
    ANCHO = 168
    ALTO_IMAGEN = int((ANCHO - 16) * 16 / 9)
    ALTO_BOTON = 28
    SOSTENER_MS = 1700           # el resultado final se queda a la vista antes de volver a empezar
    PAUSA_MS = 350

    def __init__(self, ej, al_tocar, al_resolve=None, padre=None):
        super().__init__(padre)
        self.ej = ej
        self._al_tocar = al_tocar
        self._orden = 0
        self._hover = False
        self._cuadros = None            # [QPixmap] ya a su tamaño y con las esquinas redondeadas (se cargan al verse por primera vez)
        self._ms = (ej['id'] * 337) % 1600       # cada tarjeta arranca en un punto distinto: no bailan todas a la vez
        self.setFixedSize(self.ANCHO, self.ALTO_IMAGEN + 74 + self.ALTO_BOTON + 10)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMouseTracking(True)
        Tooltip(self, tr('Toca para elegirlo. Los tres primeros que elijas serán las variantes 1, 2 y 3 de tu pack.'))
        self.boton = None
        if al_resolve is not None:
            self.boton = Boton(tr('Vista real · Resolve'), lambda _=False, i=ej['id']: al_resolve(i), alto=self.ALTO_BOTON, tam=11)
            self.boton.setParent(self)
            self.boton.setGeometry(8, self.ALTO_IMAGEN + 74, self.ANCHO - 16, self.ALTO_BOTON)
            Tooltip(self.boton, tr('Carga SOLO este estilo en la línea de tiempo de DaVinci Resolve, para verlo de verdad y retocarlo allí.'))

    # -- los fotogramas
    def recargar(self):
        """Tras renderizar vistas nuevas: se vuelven a leer."""
        self._cuadros = None
        self.update()

    def _cargar(self):
        from PySide6.QtCore import QRectF as _R
        from PySide6.QtGui import QImage, QPainterPath, QPixmap
        dpr = self.devicePixelRatioF()
        ancho = self.ANCHO - 16
        lista = []
        for ruta in E.rutas_vista(self.ej):
            img = QImage(str(ruta))
            if img.isNull():
                continue
            pm = QPixmap(int(ancho * dpr), int(self.ALTO_IMAGEN * dpr))
            pm.setDevicePixelRatio(dpr)
            pm.fill(Qt.GlobalColor.transparent)
            q = QPainter(pm)
            q.setRenderHint(QPainter.RenderHint.Antialiasing)
            q.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            recorte = QPainterPath()
            recorte.addRoundedRect(_R(0, 0, ancho, self.ALTO_IMAGEN), 12, 12)
            q.setClipPath(recorte)
            q.drawImage(_R(0, 0, ancho, self.ALTO_IMAGEN), img)
            q.end()
            lista.append(pm)
        self._cuadros = lista

    def _tiempos(self, n):
        return [int(s * 1000) for s in E.CUADROS_VISTA_S][:n]

    def avanzar(self, ms):
        """El reloj de la galería: solo lo llaman las tarjetas que se ven."""
        self._ms += ms
        self.update()

    def _fotograma(self):
        """(fotograma, siguiente, mezcla 0..1) en este instante de la reproducción."""
        cuadros = self._cuadros
        tiempos = self._tiempos(len(cuadros))
        ciclo = tiempos[-1] + self.SOSTENER_MS + self.PAUSA_MS
        t = self._ms % ciclo
        if t >= tiempos[-1] + self.SOSTENER_MS:
            return None, None, 0.0                       # un instante en negro antes de volver a empezar
        if t >= tiempos[-1]:
            return cuadros[-1], None, 0.0
        if t < tiempos[0]:
            return None, cuadros[0], t / max(1, tiempos[0])
        for k in range(len(tiempos) - 1):
            if tiempos[k] <= t < tiempos[k + 1]:
                return cuadros[k], cuadros[k + 1], (t - tiempos[k]) / max(1, tiempos[k + 1] - tiempos[k])
        return cuadros[-1], None, 0.0

    def poner_orden(self, k):
        if k != self._orden:
            self._orden = k
            self.update()

    def enterEvent(self, e):
        self._hover = True
        self.update()
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._hover = False
        self.update()
        super().leaveEvent(e)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._al_tocar(self.ej['id'])

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        marco = QRectF(1, 1, self.width() - 2, self.height() - 2)
        elegido = self._orden > 0
        p.setBrush(QColor('#13203A' if (elegido or self._hover) else '#0F1A30'))
        p.setPen(QPen(QColor(AMARILLO if elegido else ('#2C4068' if self._hover else '#1E2A42')), 2.0 if elegido else 1.0))
        p.drawRoundedRect(marco, 14, 14)
        if self._cuadros is None:
            self._cargar()
        if self._cuadros:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor('#000000'))
            p.drawRoundedRect(QRectF(8, 8, self.ANCHO - 16, self.ALTO_IMAGEN), 12, 12)
            actual, siguiente, mezcla = self._fotograma()
            if actual is not None:
                p.drawPixmap(8, 8, actual)
            if siguiente is not None:
                p.setOpacity(mezcla)
                p.drawPixmap(8, 8, siguiente)
                p.setOpacity(1.0)
        else:
            p.drawPixmap(8, 8, E.miniatura(self.ej, self.ANCHO - 16, self.devicePixelRatioF()))
        # nombre y qué es
        p.setPen(QColor('#FFFFFF'))
        p.setFont(ui.fuente(13, True))
        p.drawText(QRectF(10, self.ALTO_IMAGEN + 14, self.width() - 20, 20), int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), E.nombre_visible(self.ej))
        p.setPen(QColor(TEXT_MUTED))
        p.setFont(ui.fuente(11))
        p.drawText(QRectF(10, self.ALTO_IMAGEN + 36, self.width() - 20, 18), int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                   tr(E.etiqueta_posicion(self.ej)))
        p.setFont(ui.fuente(10, True))
        p.drawText(QRectF(10, self.ALTO_IMAGEN + 36, self.width() - 20, 18), int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter),
                   f"#{self.ej['id']:02d}")
        if elegido:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(AMARILLO))
            p.drawEllipse(QRectF(14, 14, 26, 26))
            p.setPen(QColor('#101626'))
            p.setFont(ui.fuente(14, True))
            p.drawText(QRectF(14, 14, 26, 26), int(Qt.AlignmentFlag.AlignCenter), str(self._orden))
        p.end()


class CreaEstiloDialogo(Dialogo):
    """La galería de 30 ejemplos. al_crear(nombre, ids) arma el pack; al_resolve() abre los 30 en Resolve; al_ayuda() abre el popup del «!»."""
    COLUMNAS = 5

    def __init__(self, padre, al_crear, al_resolve, al_ayuda, al_resolve_uno=None):
        super().__init__(padre, tr('Crea tu estilo'), 1040, 800, minimo=(960, 560))
        self._al_crear = al_crear
        self._al_resolve = al_resolve
        self._al_ayuda = al_ayuda
        self._al_resolve_uno = al_resolve_uno
        self._elegidos = []
        self._tarjetas = {}
        capa = QVBoxLayout(self)
        capa.setContentsMargins(20, 18, 20, 16)
        capa.setSpacing(10)
        cab, cc = caja_h(espacio=10)
        cc.addWidget(Etiqueta(tr('Crea tu estilo'), 22, peso='extra', color='#FFFFFF'))
        cc.addStretch(1)
        ayuda = _boton_ayuda(self._al_ayuda)
        cc.addWidget(ayuda)
        capa.addWidget(cab)
        capa.addWidget(Etiqueta(tr('48 ejemplos con distinta posición, tipografía y colores. Toca hasta 3 (serán las variantes 1, 2 y 3 de tu pack) y créalo en un clic, o ábrelos en Resolve para retocarlos con los efectos del Luxe Title Pack y de Amro.Films Captions.'),
                                13, color='#B4C0D6', envolver=True))
        # filtros
        self._pos_ops = [tr('Todas')] + [tr(E.POSICIONES[k][0]) for k in E.ORDEN_POSICIONES]
        self._est_ops = [tr('Todos')] + [E.etiqueta_estilo(k) for k in E.ESTILOS]
        self._pos_var = StringVar(self._pos_ops[0])
        self._est_var = StringVar(self._est_ops[0])
        f1, c1 = caja_h(espacio=10)
        c1.addWidget(Etiqueta(tr('Posición'), 12, peso='negrita', color=TEXT_MUTED))
        c1.addWidget(Segmentado(self._pos_ops, self._pos_var, lambda _v=None: self._pintar(), alto=30, tam=12))
        c1.addStretch(1)
        self._estado_real = Etiqueta('', 12, color=TEXT_MUTED)
        c1.addWidget(self._estado_real)
        self._b_real = Boton(tr('Vista real · Resolve'), self._renderizar, alto=30, tam=12)
        Tooltip(self._b_real, tr('DaVinci Resolve vuelve a renderizar de verdad la animación de todos los ejemplos (tipografía, color, posición y los efectos Luxe y Amro) en un timeline temporal que se borra solo. Tarda unos minutos. Cada tarjeta tiene además su propio botón para cargar solo ese estilo en tu línea de tiempo.'))
        c1.addWidget(self._b_real)
        capa.addWidget(f1)
        f2, c2 = caja_h(espacio=10)
        c2.addWidget(Etiqueta(tr('Estilo'), 12, peso='negrita', color=TEXT_MUTED))
        c2.addWidget(Segmentado(self._est_ops, self._est_var, lambda _v=None: self._pintar(), alto=30, tam=12))
        c2.addStretch(1)
        capa.addWidget(f2)
        # la galería
        self._desp = Desplazable(margenes=(0, 4, 8, 4), espacio=0, estirar_final=False)
        self._rejilla_w = QWidget()
        self._rejilla = QGridLayout(self._rejilla_w)
        self._rejilla.setContentsMargins(0, 0, 0, 0)
        self._rejilla.setHorizontalSpacing(10)
        self._rejilla.setVerticalSpacing(10)
        self._desp.agregar(self._rejilla_w)
        capa.addWidget(self._desp, 1)
        for ej in E.EJEMPLOS:
            self._tarjetas[ej['id']] = _Tarjeta(ej, self._tocar, al_resolve_uno)
        # abajo: lo elegido + nombre + botones
        pie = QFrame()
        pie.setObjectName('pieCreaEstilo')
        pie.setStyleSheet(_hoja('QFrame#pieCreaEstilo { background-color: #0F1A30; border: 1px solid #1E2A42; border-radius: 14px; }'))
        pv = QVBoxLayout(pie)
        pv.setContentsMargins(14, 10, 14, 12)
        pv.setSpacing(8)
        self._resumen = Etiqueta('', 13, color='#E0EBFB', envolver=True)
        pv.addWidget(self._resumen)
        fila, cf = caja_h(espacio=10)
        self._nombre = Entrada(placeholder=tr('Nombre de tu estilo'), alto=38, tam=14)
        self._nombre.setText(tr('Mi estilo'))
        cf.addWidget(self._nombre, 1)
        self._b_resolve = Boton(tr('Abrir los 48 en Resolve'), self._abrir_resolve, alto=38, tam=13)
        Tooltip(self._b_resolve, tr('Arma en Resolve un timeline con los 48 ejemplos hechos con los efectos Luxe Shine o Amro.Films Captions (principal) y Luxe Slide (arriba y abajo) para retocarlos. Después los nombras como pide la estructura y los exportas.'))
        cf.addWidget(self._b_resolve)
        self._b_crear = Boton(tr('Crear mi pack'), self._crear, tipo='primario', alto=38, tam=14, negrita=True)
        cf.addWidget(self._b_crear)
        pv.addWidget(fila)
        pv.addWidget(Etiqueta(tr('Los packs que creas aquí ya traen los nombres bien puestos (principal, arriba, abajo, simple y sus variantes 2 y 3). Pulsa «!» para entender por qué importan.'),
                              11, color=TEXT_MUTED, envolver=True))
        capa.addWidget(pie)
        self._renderizando = False
        self._pintar()
        self._resumir()
        self._reloj = QTimer(self)             # el reloj de las vistas: solo mueve las tarjetas que se ven
        self._reloj.timeout.connect(self._tic)
        self._reloj.start(self.TIC_MS)
        despues(700, self._auto_vistas, self)

    TIC_MS = 40

    def _tic(self):
        for t in self._tarjetas.values():
            if not t.isHidden() and not t.visibleRegion().isEmpty():
                t.avanzar(self.TIC_MS)

    # -- la vista REAL de Resolve
    def _auto_vistas(self):
        """Si falta alguna vista real y Resolve está conectado, se piden solas (sin abrir Resolve si estaba cerrado)."""
        try:
            import resolve_mcp
            import vistas_guia
            if vistas_guia.faltan() and resolve_mcp.estado_cacheado().get('conectado'):
                self._renderizar(silencioso=True)
        except Exception:
            pass

    def _renderizar(self, silencioso=False):
        if self._renderizando or not ui.vivo(self):
            return
        self._renderizando = True
        self._b_real.setEnabled(False)
        estado = {'texto': tr('Abriendo Resolve…')}

        def trabajo():
            import vistas_guia
            return vistas_guia.renderizar(al_estado=lambda t: estado.__setitem__('texto', str(t)), abrir_resolve=not silencioso)

        def avance():
            if self._renderizando and ui.vivo(self):
                self._estado_real.configure(text=estado['texto'])
                despues(300, avance, self)

        def fin(resultado, error):
            self._renderizando = False
            if not ui.vivo(self):
                return
            self._b_real.setEnabled(True)
            ok, dato = resultado if (resultado and not error) else (False, str(error or ''))
            self._estado_real.configure(text=tr('Vista real al día') if ok else (tr('Sin vista real: {m}', m=str(dato)[:90]) if not silencioso else ''),
                                        text_color=TEXT_MUTED if ok or silencioso else AMBAR)
            for t in self._tarjetas.values():
                t.recargar()
        avance()
        ui.correr_en_hilo(self, trabajo, fin)

    # -- galería
    def _filtrados(self):
        pos = self._pos_var.get()
        est = self._est_var.get()
        salida = []
        for ej in E.EJEMPLOS:
            if pos != self._pos_ops[0] and tr(E.POSICIONES[ej['posicion']][0]) != pos:
                continue
            if est != self._est_ops[0] and E.etiqueta_estilo(ej['estilo']) != est:
                continue
            salida.append(ej)
        return salida

    def _pintar(self):
        while self._rejilla.count():
            it = self._rejilla.takeAt(0)
            w = it.widget()
            if w is not None:
                w.hide()
        for k, ej in enumerate(self._filtrados()):
            t = self._tarjetas[ej['id']]
            self._rejilla.addWidget(t, k // self.COLUMNAS, k % self.COLUMNAS, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            t.show()
        self._rejilla.setColumnStretch(self.COLUMNAS, 1)
        self._poner_ordenes()

    def _poner_ordenes(self):
        for i, t in self._tarjetas.items():
            t.poner_orden(self._elegidos.index(i) + 1 if i in self._elegidos else 0)

    def _tocar(self, ident):
        if ident in self._elegidos:
            self._elegidos.remove(ident)
        elif len(self._elegidos) < E.MAX_ELEGIDOS:
            self._elegidos.append(ident)
        else:
            self._resumen.configure(text=tr('Ya elegiste 3 (el máximo de variantes de un pack). Toca uno elegido para quitarlo.'), text_color=AMBAR)
            return
        self._poner_ordenes()
        self._resumir()

    def _resumir(self):
        if not self._elegidos:
            self._resumen.configure(text=tr('Toca los ejemplos que te gusten (hasta 3).'), text_color=TEXT_MUTED)
            self._b_crear.setEnabled(False)
            return
        partes = []
        for k, i in enumerate(self._elegidos, 1):
            ej = E.por_id(i)
            partes.append(f"{k} · {E.nombre_visible(ej)} ({tr(E.etiqueta_posicion(ej)).lower()})")
        self._resumen.configure(text=tr('Variantes de tu pack: ') + '   ·   '.join(partes), text_color='#E0EBFB')
        self._b_crear.setEnabled(True)

    # -- acciones
    def _crear(self):
        if not self._elegidos:
            return
        nombre = self._nombre.text().strip() or tr('Mi estilo')
        self._b_crear.setEnabled(False)
        self._b_crear.setText(tr('Creando…'))
        self._al_crear(nombre, list(self._elegidos), self._termino)

    def _termino(self, ok):
        """Lo llama la app cuando el pack ya está (o falló): si salió bien la galería se cierra."""
        if not ui.vivo(self):
            return
        self._b_crear.setText(tr('Crear mi pack'))
        self._resumir()
        if ok:
            self.cerrar()

    def _abrir_resolve(self):
        self._al_resolve()


def _boton_ayuda(comando):
    """El «!» ámbar: abre la explicación de la estructura."""
    b = Boton('!', comando, alto=32, ancho=34, tam=16, negrita=True)
    b.setFixedWidth(34)
    b.setStyleSheet(_hoja('QPushButton { color: #1B1305; background-color: %s; border: none; border-radius: 16px; font-weight: 800; }'
                          'QPushButton:hover { background-color: #FFCB6B; }' % AMBAR))
    Tooltip(b, tr('Cómo funciona «Crea tu estilo»: por qué los clips deben llamarse principal, arriba, abajo o simple, y qué son las variantes 2 y 3. Sin esa estructura el estilo no funciona.'))
    return b


def boton_ayuda(comando):
    return _boton_ayuda(comando)


# ====================================================================================== el popup que explica la estructura
def _pildora(p, x, y, texto, bien=None, ancho=None, color=None):
    """Una «etiqueta de clip» dibujada: verde con ✔ si vale, roja con ✘ si no. Devuelve el ancho."""
    p.setFont(ui.fuente(12, True))
    ancho = ancho or (p.fontMetrics().horizontalAdvance(texto) + (46 if bien is not None else 26))
    c = QColor(color or (VERDE if bien else ROJO if bien is False else '#9FB0CC'))
    p.setPen(QPen(c, 1.4))
    fondo = QColor(c)
    fondo.setAlpha(36)
    p.setBrush(fondo)
    p.drawRoundedRect(QRectF(x, y, ancho, 28), 14, 14)
    p.setPen(QColor('#F1F5FB'))
    p.drawText(QRectF(x + (30 if bien is not None else 0), y, ancho - (30 if bien is not None else 0) - (8 if bien is not None else 0), 28),
               int((Qt.AlignmentFlag.AlignVCenter | (Qt.AlignmentFlag.AlignLeft if bien is not None else Qt.AlignmentFlag.AlignHCenter))), texto)
    if bien is not None:
        p.setPen(QPen(c, 2.0))
        cx, cy = x + 15, y + 14
        if bien:
            p.drawLine(int(cx - 4), int(cy), int(cx - 1), int(cy + 3))
            p.drawLine(int(cx - 1), int(cy + 3), int(cx + 5), int(cy - 4))
        else:
            p.drawLine(int(cx - 4), int(cy - 4), int(cx + 4), int(cy + 4))
            p.drawLine(int(cx + 4), int(cy - 4), int(cx - 4), int(cy + 4))
    return ancho


class _Dibujo(QWidget):
    def __init__(self, alto, pintar):
        super().__init__()
        self._pintar = pintar
        self.setMinimumHeight(alto)
        self.setFixedHeight(alto)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self._pintar(p, self.width(), self.height())
        p.end()


def _dibujo_bloques(p, w, h):
    """El teléfono con las tres líneas apiladas y, a la derecha, el nombre y el efecto de cada bloque."""
    tel = QRectF(14, 8, 118, 210)
    p.setPen(QPen(QColor('#2C4068'), 2))
    p.setBrush(QColor('#0B1426'))
    p.drawRoundedRect(tel, 16, 16)
    E.dibujar(p, tel.adjusted(5, 5, -5, -5), E.por_id(15), escala_texto=1.0)
    nombres = (('arriba', 'Luxe Slide', 'la línea de contexto, encima'), ('principal', 'Luxe Shine', 'la palabra clave, grande y con brillo'),
               ('abajo', 'Luxe Slide', 'la línea que va debajo'))
    y0 = 52
    for k, (nombre, efecto, nota) in enumerate(nombres):
        y = y0 + k * 44
        p.setPen(QPen(QColor(AMARILLO), 1.2, Qt.PenStyle.DashLine))
        p.drawLine(int(tel.right() - 6), int(tel.top() + 70 + k * 30), 150, int(y + 14))
        _pildora(p, 150, y, nombre, None, ancho=118, color=AMARILLO)
        p.setPen(QColor('#E0EBFB'))
        p.setFont(ui.fuente(13, True))
        p.drawText(QRectF(280, y - 2, w - 290, 18), int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), efecto)
        p.setPen(QColor(TEXT_MUTED))
        p.setFont(ui.fuente(12))
        p.drawText(QRectF(280, y + 14, w - 290, 18), int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), tr(nota))
    y = y0 + 3 * 44 + 6
    _pildora(p, 150, y, 'imagen', None, ancho=118, color='#9FB0CC')
    p.setPen(QColor(TEXT_MUTED))
    p.setFont(ui.fuente(12))
    p.drawText(QRectF(280, y, w - 290, 28), int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), tr('(opcional) el hueco del emoji, sin texto'))
    _pildora(p, 150, y + 36, 'simple', None, ancho=118, color='#9FB0CC')
    p.setPen(QColor(TEXT_MUTED))
    p.setFont(ui.fuente(12))
    p.drawText(QRectF(280, y + 36, w - 290, 28), int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), tr('(opcional) una sola línea para palabras sueltas'))


def _dibujo_guion(p, w, h):
    """El estilo «palabra a palabra» (pack Referencia): un bloque de ejemplo y qué hace cada nombre (arriba = fina, abajo = negrita, principal = grande)."""
    tel = QRectF(14, 8, 118, 218)
    p.setPen(QPen(QColor('#2C4068'), 2))
    p.setBrush(QColor('#0B1426'))
    p.drawRoundedRect(tel, 16, 16)
    cx = tel.center().x()

    def linea(y, tramos):
        """[(texto, tam, negrita, color)] centrado en el teléfono, a la altura y."""
        anchos = []
        for t, tam, neg, _c in tramos:
            p.setFont(ui.fuente(tam, neg))
            anchos.append(p.fontMetrics().horizontalAdvance(t + ' '))
        x = cx - sum(anchos) / 2.0
        for (t, tam, neg, c), a in zip(tramos, anchos):
            p.setFont(ui.fuente(tam, neg))
            p.setPen(QColor(c))
            p.drawText(QRectF(x, y, a + 4, tam + 10), int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), t)
            x += a
    linea(78, [('Seamos', 10, False, '#DCE6F7'), ('sinceros', 10, True, '#FFFFFF'), ('tú', 10, False, '#DCE6F7')])
    linea(100, [('LLEVARÍAS', 17, True, '#FFD98A')])
    linea(130, [('niños a tu', 10, False, '#DCE6F7'), ('boda', 10, True, '#FFFFFF')])
    filas = (('arriba', 'Luxe Slide FINO', 'las palabras en letra regular', 80, 38), ('abajo', 'Luxe Slide en NEGRITA', 'las palabras que se resaltan (no significa «debajo»)', 84, 94),
             ('principal', 'Luxe Shine o un preset de Amro', 'la palabra grande: la que manda en la frase', 100, 150))
    for nombre, efecto, nota, y_tel, y in filas:
        p.setPen(QPen(QColor(AMARILLO), 1.2, Qt.PenStyle.DashLine))
        p.drawLine(int(tel.right() - 8), int(y_tel + 6), 150, int(y + 14))
        _pildora(p, 150, y, nombre, None, ancho=118, color=AMARILLO)
        p.setPen(QColor('#E0EBFB'))
        p.setFont(ui.fuente(13, True))
        p.drawText(QRectF(280, y - 2, w - 290, 18), int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), efecto)
        p.setPen(QColor(TEXT_MUTED))
        p.setFont(ui.fuente(12))
        p.drawText(QRectF(280, y + 14, w - 290, 18), int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), tr(nota))


def _dibujo_nombres(p, w, h):
    p.setFont(ui.fuente(11, True))
    p.setPen(QColor(VERDE))
    p.drawText(QRectF(8, 0, 300, 18), int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), tr('SE RECONOCEN').upper())
    x, y = 8, 24
    for t in ('principal', 'arriba', 'abajo', 'imagen', 'simple', 'Principal 2', 'arriba 3'):
        a = p.fontMetrics().horizontalAdvance(t) + 46
        if x + a > w - 8:
            x, y = 8, y + 34
        x += _pildora(p, x, y, t, True) + 8
    y += 48
    p.setFont(ui.fuente(11, True))
    p.setPen(QColor(ROJO))
    p.drawText(QRectF(8, y, 400, 18), int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), tr('NO SE RECONOCEN: EL PROGRAMA LOS IGNORA').upper())
    x, y = 8, y + 24
    for t in ('Luxe Shine', 'Luxe Slide', 'Texto 1', 'título', 'principal grande', 'principal 4'):
        a = p.fontMetrics().horizontalAdvance(t) + 46
        if x + a > w - 8:
            x, y = 8, y + 34
        x += _pildora(p, x, y, t, False) + 8


def _dibujo_variantes(p, w, h):
    ancho_col = (w - 30) / 4.0
    titulos = (tr('Variante 1'), tr('Variante 2'), tr('Variante 3'), tr('Variante 4'))
    for k in range(4):
        x = 8 + k * (ancho_col + 4)
        ok = k < 3
        suf = '' if k == 0 else f' {k + 1}'
        c = QColor(AMARILLO if ok else ROJO)
        p.setPen(QPen(c, 1.2, Qt.PenStyle.SolidLine if ok else Qt.PenStyle.DashLine))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(QRectF(x, 2, ancho_col - 4, h - 6), 12, 12)
        p.setFont(ui.fuente(12, True))
        p.setPen(c)
        p.drawText(QRectF(x, 8, ancho_col - 4, 20), int(Qt.AlignmentFlag.AlignCenter), titulos[k])
        for j, nombre in enumerate(('arriba', 'principal', 'abajo')):
            _pildora(p, x + 8, 36 + j * 34, nombre + suf, ok if k else True, ancho=ancho_col - 20, color=None if ok else ROJO)
        if not ok:
            p.setPen(QColor(ROJO))
            p.setFont(ui.fuente(11))
            p.drawText(QRectF(x + 6, 36 + 3 * 34, ancho_col - 16, 34), int(Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap), tr('Más de 3: se ignora'))


class AyudaEstilo(Dialogo):
    """El popup del «!»: la estructura de nombres, las variantes y el paso a paso, con dibujos."""

    def __init__(self, padre):
        super().__init__(padre, tr('Cómo funciona «Crea tu estilo»'), 700, 780, minimo=(620, 480))
        capa = QVBoxLayout(self)
        capa.setContentsMargins(20, 18, 20, 16)
        capa.setSpacing(10)
        cab, cc = caja_h(espacio=10)
        cc.addWidget(Etiqueta(tr('Cómo funciona «Crea tu estilo»'), 20, peso='extra', color='#FFFFFF'), 1)
        capa.addWidget(cab)
        desp = Desplazable(margenes=(0, 0, 10, 4), espacio=12, estirar_final=False)
        capa.addWidget(desp, 1)
        desp.agregar(Etiqueta(tr('Un estilo es un grupo de bloques de texto. CineCaptions los reconoce SOLO por su nombre: no mira el diseño, ni los colores, ni la tipografía.'),
                              14, color='#E0EBFB', envolver=True))
        aviso = QFrame()
        aviso.setObjectName('avisoEstructura')
        aviso.setStyleSheet(_hoja('QFrame#avisoEstructura { background-color: #2A2108; border: 1px solid %s; border-radius: 12px; }' % AMBAR))
        av = QVBoxLayout(aviso)
        av.setContentsMargins(14, 10, 14, 10)
        av.addWidget(Etiqueta(tr('Si un clip no se llama exactamente como pide la estructura, el programa no sabe qué hace y lo ignora. Sin esa estructura, el estilo no funciona.'),
                              13, peso='medio', color='#FFD98A', envolver=True))
        desp.agregar(aviso)
        # 1
        desp.agregar(self._titulo(tr('1 · Los bloques y el efecto de cada uno')))
        desp.agregar(_Dibujo(272, _dibujo_bloques))
        desp.agregar(Etiqueta(tr('Los textos tienen que ser SOLO del Luxe Title Pack (Efectos > Títulos > Luxe Title Pack): Luxe Shine para el principal y Luxe Slide para arriba y abajo. Un estilo necesita como mínimo arriba + principal + abajo.'),
                              13, color='#B4C0D6', envolver=True))
        desp.agregar(Etiqueta(tr('Los presets de Amro.Films Captions (Highlight, Underline, Fire, Strike…) valen SOLO para el texto principal, como alternativa a Luxe Shine; arriba y abajo siguen siendo siempre Luxe Slide.'),
                              13, color='#B4C0D6', envolver=True))
        # 1 bis: el estilo palabra a palabra (pack Referencia)
        desp.agregar(self._titulo(tr('Estilo «palabra a palabra» (como el pack Referencia)')))
        desp.agregar(Etiqueta(tr('Los captions virales no son una pila fija de 3 líneas: cada PALABRA es su propio clip y entra justo cuando se dice; al acabar la frase se va toda la pila a la vez. Se arma con los mismos nombres, pero con otro papel:'),
                              13, color='#B4C0D6', envolver=True))
        desp.agregar(_Dibujo(238, _dibujo_guion))
        desp.agregar(Etiqueta(tr('«arriba» = las palabras en letra FINA (regular), «abajo» = las palabras en NEGRITA (aquí no quiere decir «debajo») y «principal» = la palabra grande. Dónde cae cada palabra y qué peso lleva lo decide GO al leer tu voz (una palabra en negrita por línea, una o dos grandes por frase); el pack solo pone el aspecto de cada papel.'),
                              13, color='#B4C0D6', envolver=True))
        desp.agregar(Etiqueta(tr('Un pack funciona así cuando su pack.json lleva «guion» (el pack «Referencia» ya viene así, con 8 estilos de palabra grande: 4 de Luxe Shine y 4 de Amro). Los packs que armas aquí usan el diseño de 3 líneas de arriba. En Inicio, el chip «Estilo» de GO elige uno u otro.'),
                              13, color='#B4C0D6', envolver=True))
        # 2
        desp.agregar(self._titulo(tr('2 · El nombre tiene que ser exacto')))
        desp.agregar(Etiqueta(tr('Da igual si escribes mayúsculas o minúsculas. Lo que no vale es cualquier otro nombre: Resolve llama a los clips «Luxe Shine» y «Luxe Slide» y esos nombres NO se reconocen; hay que cambiárselos por principal, arriba, abajo…'),
                              13, color='#B4C0D6', envolver=True))
        desp.agregar(_Dibujo(214, _dibujo_nombres))
        # 3
        desp.agregar(self._titulo(tr('3 · Las variantes: principal, principal 2 y principal 3')))
        desp.agregar(Etiqueta(tr('Para que todo el video no se vea igual puedes crear hasta 3 variantes del mismo estilo (otro color, otra posición, otra letra). La primera lleva solo el nombre; la segunda y la tercera llevan el número al final. El programa las agrupa por ese número: todo lo que termina en 2 forma la variante 2.'),
                              13, color='#B4C0D6', envolver=True))
        desp.agregar(_Dibujo(150, _dibujo_variantes))
        desp.agregar(Etiqueta(tr('Por eso cada variante necesita sus tres bloques con el mismo número: si falta uno, esa variante no se usa. Un número mayor que 3 (por ejemplo «principal 4») se ignora y el programa te avisa. Los bloques del video van alternando las variantes, o usan una fija si la eliges en «Estilo fijo».'),
                              13, color='#B4C0D6', envolver=True))
        # 4
        desp.agregar(self._titulo(tr('4 · Paso a paso')))
        pasos = (tr('Pulsa «Crea tu estilo», toca hasta 3 de los 48 ejemplos y pulsa «Crear mi pack». Ya viene con los nombres bien puestos.'),
                 tr('¿Quieres retocarlos? Pulsa «Abrir los 48 en Resolve»: se arma un timeline con los ejemplos hechos con Luxe Shine, Luxe Slide y los presets de Amro. Cambia fuente, color, tamaño y posición en el Inspector.'),
                 tr('Quédate con los que quieras (máximo 3 variantes), borra el resto y ponles el nombre exacto: clic derecho sobre el clip > cambiar nombre (principal, arriba, abajo, y «2» o «3» para las variantes).'),
                 tr('Exporta: Archivo > Exportar > Timeline (.drt), o clic derecho sobre un bin > Exportar bin (.drb).'),
                 tr('En CineCaptions, en «Pack de estilos», pulsa la tarjeta «Añadir plantilla (.drb)» y elige tu archivo. Si falta algo, el programa te dice qué.'))
        for k, texto in enumerate(pasos, 1):
            fila, cf = caja_h(espacio=10)
            n = Etiqueta(str(k), 13, peso='extra', color='#101626', alineacion=Qt.AlignmentFlag.AlignCenter)
            n.setFixedSize(26, 26)
            n.setStyleSheet(_hoja('background-color: %s; border-radius: 13px;' % AMARILLO))
            cf.addWidget(n, 0, Qt.AlignmentFlag.AlignTop)
            cf.addWidget(Etiqueta(texto, 13, color='#E0EBFB', envolver=True), 1)
            desp.agregar(fila)
        cerrar = Boton(tr('Entendido'), self.cerrar, tipo='primario', alto=38, tam=14, negrita=True)
        capa.addWidget(cerrar)

    @staticmethod
    def _titulo(texto):
        return Etiqueta(texto, 16, peso='extra', color=AMARILLO)
