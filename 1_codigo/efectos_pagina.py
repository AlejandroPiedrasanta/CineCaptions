# CineCaptions · By Cinema Productions
# 1_codigo/efectos_pagina.py — la página «Efectos»: elegir la intro (con su sonido), las transiciones de los cortes y los iconos flotantes (y en qué palabras salen).
"""
efectos_pagina.py  (v5.4.7)
---------------------------
Tres tarjetas —Intro, Transiciones en los cortes, Iconos flotantes— con una vista previa animada de cada efecto (2_recursos/efectos/previas, hechas con
hacer_previas_efectos.py y reproducidas con vistas_slider.Reproductor solo mientras se ven). Lo que se elige se guarda en las preferencias y lo lee
efectos_visuales.planificar al hacer GO:

    fx_intro / fx_intro_sonido            la intro y su sonido (el Riser 1 de fábrica, otro archivo o 'ninguno' = silenciada)
    fx_cortes / fx_cortes_cuanto          la transición de los cortes y cuántas
    fx_iconos_activo / fx_iconos          los iconos flotantes (interruptor general y packs activos)
    fx_iconos_palabras {pack: [palabras]} en qué palabras sale cada pack (clic en el pack); fx_iconos_extra = también en frases importantes
    fx_iconos_cuanto                      cuántos iconos

Los efectos vienen ACTIVADOS; el interruptor de arriba es el MISMO que el chip «Visuales» de Inicio (preferencia go_efectos_visuales).
"""
from PySide6.QtCore import QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QImage, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QPlainTextEdit, QVBoxLayout, QWidget

import efectos_visuales as F
import qt_kit as ui
from qt_kit import Boton, Dialogo, Etiqueta, Interruptor, Segmentado, StringVar, Tarjeta, Tooltip, caja_h
from qt_kit import QColor
from i18n import tr

VERDE = ui.VERDE
TEXT_MUTED = ui.TEXT_MUTED


def _guardar(cambios):
    try:
        import ajustes_ui
        ajustes_ui.guardar_prefs(cambios)
    except Exception:
        pass


# ====================================================================================== una tarjeta de efecto
class TarjetaEfecto(QWidget):
    """Una vista previa 9:16 (el mp4 del efecto sobre una foto, en bucle mientras se ve), su nombre y una línea. Tocarla la elige. Con `pack=True` (iconos) el clic abre
    «en qué palabras sale» y lleva abajo su interruptor (activo / no) y el botón «Palabras»."""
    clic = Signal(str)
    cambio = Signal(str, bool)               # (ident, activo) — solo en los packs de iconos
    ANCHO = 156
    ALTO_IMAGEN = int((ANCHO - 16) * 16 / 9)

    def __init__(self, ident, nombre, detalle, previa=None, poster=None, ninguna=False, pack=False, padre=None):
        super().__init__(padre)
        self.ident = ident
        self.nombre = nombre
        self.detalle = detalle
        self._ninguna = bool(ninguna)
        self._pack = bool(pack)
        self._sel = False
        self._hover = False
        self._apagada = False
        self._poster = QImage(str(poster)) if poster else None
        self._reprod = None
        if previa:
            import vistas_slider
            self._reprod = vistas_slider.Reproductor(previa)
        self.setFixedSize(self.ANCHO, self.ALTO_IMAGEN + 84 + (40 if pack else 0))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMouseTracking(True)
        Tooltip(self, detalle)
        self._var_activo = ui.BooleanVar(False)
        if pack:
            self._sw = Interruptor('', self._var_activo, self._al_interruptor, tam=12, padre=self)
            self._sw.setToolTip(tr('Activar o desactivar este pack de iconos'))
            self._sw.move(self.ANCHO - 58, self.ALTO_IMAGEN + 88)
            self._b = Boton(tr('Palabras'), self.clic_palabras, alto=26, tam=11, padre=self)
            self._b.setGeometry(8, self.ALTO_IMAGEN + 88, 78, 26)
            Tooltip(self._b, tr('Elige en qué palabras sale este pack de iconos.'))

    def clic_palabras(self):
        self.clic.emit(self.ident)

    def _al_interruptor(self):
        self._sel = bool(self._var_activo.get())
        self.update()
        self.cambio.emit(self.ident, self._sel)

    def poner_seleccionada(self, v):
        if bool(v) != self._sel:
            self._sel = bool(v)
            self.update()
        if self._pack and bool(self._var_activo.get()) != self._sel:
            self._var_activo.set(self._sel)

    def poner_apagada(self, v):
        """El interruptor general de los iconos está apagado: la tarjeta se ve atenuada y no responde."""
        self._apagada = bool(v)
        self.setEnabled(not v)
        self.update()

    def poner_visible(self, visible):
        if self._reprod is not None:
            if visible and not self._apagada:
                self._reprod.arrancar()
            else:
                self._reprod.parar()

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
            self.clic.emit(self.ident)

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        if self._apagada or (self._pack and not self._sel):
            p.setOpacity(0.55)
        marco = QRectF(1, 1, self.width() - 2, self.height() - 2)
        p.setBrush(QColor('#13203A' if (self._sel or self._hover) else '#0F1A30'))
        p.setPen(QPen(QColor(VERDE if self._sel else ('#2C4068' if self._hover else '#1E2A42')), 2.2 if self._sel else 1.0))
        p.drawRoundedRect(marco, 14, 14)
        rect = QRectF(8, 8, self.ANCHO - 16, self.ALTO_IMAGEN)
        camino = QPainterPath()
        camino.addRoundedRect(rect, 12, 12)
        p.save()
        p.setClipPath(camino)
        if self._ninguna:
            p.fillRect(rect, QColor('#0B1424'))
            p.setPen(QColor(TEXT_MUTED))
            p.setFont(ui.fuente(34))
            p.drawText(rect, int(Qt.AlignmentFlag.AlignCenter), '∅')
        else:
            img = self._reprod.imagen() if self._reprod is not None else None
            if img is None:
                img = self._poster
            if img is not None:
                p.drawImage(rect, img)
            else:
                p.fillRect(rect, QColor('#0B1424'))
        p.restore()
        p.setPen(QColor('#FFFFFF'))
        p.setFont(ui.fuente(13, True))
        p.drawText(QRectF(10, self.ALTO_IMAGEN + 14, self.width() - 20, 20), int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), self.nombre)
        p.setPen(QColor(TEXT_MUTED))
        p.setFont(ui.fuente(10))
        p.drawText(QRectF(10, self.ALTO_IMAGEN + 36, self.width() - 20, 40), int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap), self.detalle)
        if self._sel:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(VERDE))
            p.drawEllipse(QRectF(self.ANCHO - 36, 14, 22, 22))
            p.setPen(QPen(QColor('#07140E'), 2.4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            p.drawLine(int(self.ANCHO - 30), 25, int(self.ANCHO - 26), 29)
            p.drawLine(int(self.ANCHO - 26), 29, int(self.ANCHO - 20), 21)
        p.end()


# ====================================================================================== «en qué palabras sale»
class DialogoPalabras(Dialogo):
    """Las palabras (o frases cortas) que hacen salir un pack de iconos. Se escriben separadas por comas; al guardar, el pack sale cuando se dice una de ellas."""
    def __init__(self, padre, pack, nombre, al_guardar):
        super().__init__(padre, tr('Palabras de «{n}»', n=nombre), 560, 470, minimo=(480, 400))
        self._pack = pack
        self._al_guardar = al_guardar
        capa = QVBoxLayout(self)
        capa.setContentsMargins(22, 20, 22, 18)
        capa.setSpacing(12)
        capa.addWidget(Etiqueta(tr('Palabras de «{n}»', n=nombre), 20, peso='extra', color='#FFFFFF'))
        capa.addWidget(Etiqueta(tr('El icono sale en el momento en que se dice una de estas palabras. Escríbelas separadas por comas (también valen frases cortas, como «no lo hagas»). Si la lista queda vacía, este pack solo sale en las frases importantes.'),
                                13, color='#B4C0D6', envolver=True))
        self._caja = QPlainTextEdit()
        self._caja.setFont(ui.fuente(14))
        self._caja.setPlainText(', '.join(F.palabras_de_pack(pack)))
        self._caja.setMinimumHeight(170)
        capa.addWidget(self._caja, 1)
        self._nota = Etiqueta('', 12, color=TEXT_MUTED, envolver=True)
        capa.addWidget(self._nota)
        fila, cf = caja_h(espacio=10)
        self._b_fabrica = Boton(tr('Volver a las de fábrica'), self._fabrica, tipo='fantasma', alto=36, tam=13)
        cf.addWidget(self._b_fabrica)
        cf.addStretch(1)
        cf.addWidget(Boton(tr('Cancelar'), self.cerrar, alto=36, ancho=110, tam=13))
        cf.addWidget(Boton(tr('Guardar'), self._guardar, tipo='primario', alto=36, ancho=130, tam=13, negrita=True))
        capa.addWidget(fila)
        self._caja.textChanged.connect(self._contar)
        self._contar()

    @staticmethod
    def _lista(texto):
        vistas, salida = set(), []
        for t in str(texto).replace('\n', ',').replace(';', ',').split(','):
            t = ' '.join(t.split())
            if t and t.lower() not in vistas:
                vistas.add(t.lower())
                salida.append(t)
        return salida

    def _contar(self):
        n = len(self._lista(self._caja.toPlainText()))
        self._nota.configure(text=tr('{n} palabras', n=n) if n != 1 else tr('1 palabra'))

    def _fabrica(self):
        self._caja.setPlainText(', '.join(F.PALABRAS_POR_DEFECTO.get(self._pack, ())))

    def _guardar(self):
        self._al_guardar(self._pack, self._lista(self._caja.toPlainText()))
        self.cerrar()


# ====================================================================================== la página
class PaginaEfectos(QWidget):
    TIC_MS = 40

    def __init__(self, padre=None, al_cambiar=None):
        super().__init__(padre)
        self._al_cambiar = al_cambiar               # se llama tras cambiar el interruptor general (para que Inicio repinte su chip)
        self._tarjetas = []
        self._dialogo = None
        capa = QVBoxLayout(self)
        capa.setContentsMargins(0, 0, 0, 0)
        capa.setSpacing(18)
        op = F.opciones_guardadas()
        # ---- el interruptor general
        general = Tarjeta(espacio=6, margenes=(22, 16, 22, 16))
        fila, cf = caja_h(espacio=14)
        self._var_activo = ui.BooleanVar(F.activado())
        self._sw = Interruptor(tr('Efectos visuales al hacer GO'), self._var_activo, self._cambio_general, tam=15, color='#FFFFFF')
        cf.addWidget(self._sw)
        cf.addStretch(1)
        general.capa.addWidget(fila)
        general.capa.addWidget(Etiqueta(tr('Acompañan a los captions, la música y los emojis: se colocan solos en pistas propias «FX» (tu video y tus captions no se tocan). También se enciende con el chip «Visuales» de Inicio.'),
                                        13, color=TEXT_MUTED, envolver=True))
        capa.addWidget(general)
        # ---- intro (y su sonido)
        self._intro = op.get('fx_intro') or ''
        t1 = self._tarjeta(tr('Intro'), tr('Un destello de luz con su sonido: primero sube el riser y, cuando llega al final, el destello cubre la imagen.'))
        fila_s, cs = caja_h(espacio=12)
        self._var_sonido = ui.BooleanVar(F.fuente_sonido_intro(op) is not None)
        self._sw_sonido = Interruptor(tr('Sonido en la intro'), self._var_sonido, self._cambio_sonido_on, tam=14, color='#FFFFFF')
        cs.addWidget(self._sw_sonido)
        self._lbl_sonido = Etiqueta('', 13, color='#B4C0D6')
        cs.addWidget(self._lbl_sonido)
        cs.addStretch(1)
        self._b_oir = Boton(tr('Oír'), self._oir_sonido, tipo='fantasma', alto=30, tam=12)
        cs.addWidget(self._b_oir)
        self._b_cambiar = Boton(tr('Cambiar sonido…'), self._cambiar_sonido, alto=30, tam=12)
        cs.addWidget(self._b_cambiar)
        self._b_original = Boton(tr('Riser 1'), self._sonido_original, tipo='fantasma', alto=30, tam=12)
        Tooltip(self._b_original, tr('Volver al sonido que trae el programa (los últimos segundos del Riser 1).'))
        cs.addWidget(self._b_original)
        t1.capa.addWidget(fila_s)
        fila1, c1 = caja_h(espacio=12)
        self._c_intro = {}
        for ident, nombre, detalle in [('', tr('Sin intro'), tr('El video empieza limpio.'))] + [(i, tr(n), tr(d)) for i, n, d in F.INTROS]:
            self._c_intro[ident] = self._carta(ident, nombre, detalle, 'intro', c1)
        c1.addStretch(1)
        t1.capa.addWidget(fila1)
        capa.addWidget(t1)
        self._pintar_unico(self._c_intro, self._intro)
        self._refrescar_sonido()
        # ---- transiciones
        self._cortes = op.get('fx_cortes') or ''
        t2 = self._tarjeta(tr('Transiciones en los cortes'), tr('Se detecta cada salto entre tomas del video y se esconde con un efecto.'))
        self._v_cortes = StringVar(self._texto_cuanto(op.get('fx_cortes_cuanto'), (('pocos', tr('Pocos')), ('normal', tr('Normales')), ('todos', tr('Todos')))))
        fila2a, c2a = caja_h(espacio=10)
        c2a.addWidget(Etiqueta(tr('Cuántos cortes'), 13, color=TEXT_MUTED))
        c2a.addWidget(Segmentado([tr('Pocos'), tr('Normales'), tr('Todos')], self._v_cortes, self._cambio_cortes, alto=32, tam=13))
        c2a.addStretch(1)
        t2.capa.addWidget(fila2a)
        fila2, c2 = caja_h(espacio=12)
        self._c_cortes = {}
        for ident, nombre, detalle in [('', tr('Sin transición'), tr('Los cortes quedan secos.'))] + [(i, tr(n), tr(d)) for i, n, d in F.TRANSICIONES]:
            self._c_cortes[ident] = self._carta(ident, nombre, detalle, 'corte', c2)
        c2.addStretch(1)
        t2.capa.addWidget(fila2)
        capa.addWidget(t2)
        self._pintar_unico(self._c_cortes, self._cortes)
        # ---- iconos
        self._iconos = set(op.get('fx_iconos') or [])
        t3 = self._tarjeta(tr('Iconos flotantes'), tr('Salen iconos animados cuando se dice una palabra que tú eliges (haz clic en un pack para escribirlas) y, si quieres, también en las frases importantes: un número, un aviso, una pregunta o el gancho.'))
        fila3g, c3g = caja_h(espacio=14)
        self._var_iconos_on = ui.BooleanVar(bool(op.get('fx_iconos_activo', True)))
        self._sw_iconos = Interruptor(tr('Iconos flotantes'), self._var_iconos_on, self._cambio_iconos_on, tam=14, color='#FFFFFF')
        c3g.addWidget(self._sw_iconos)
        self._var_extra = ui.BooleanVar(bool(op.get('fx_iconos_extra', True)))
        self._sw_extra = Interruptor(tr('También en frases importantes'), self._var_extra, self._cambio_extra, tam=13, color='#E0EBFB')
        c3g.addWidget(self._sw_extra)
        c3g.addStretch(1)
        t3.capa.addWidget(fila3g)
        self._v_iconos = StringVar(self._texto_cuanto(op.get('fx_iconos_cuanto'), (('pocos', tr('Pocos')), ('normal', tr('Normales')), ('muchos', tr('Muchos')))))
        fila3a, c3a = caja_h(espacio=10)
        c3a.addWidget(Etiqueta(tr('Cuántos iconos'), 13, color=TEXT_MUTED))
        c3a.addWidget(Segmentado([tr('Pocos'), tr('Normales'), tr('Muchos')], self._v_iconos, self._cambio_iconos, alto=32, tam=13))
        c3a.addStretch(1)
        t3.capa.addWidget(fila3a)
        fila3, c3 = caja_h(espacio=12)
        self._c_iconos = {}
        for ident, nombre, detalle in F.PACKS_ICONOS:
            self._c_iconos[ident] = self._carta(ident, tr(nombre), tr(detalle), 'iconos', c3, pack=True)
        c3.addStretch(1)
        t3.capa.addWidget(fila3)
        capa.addWidget(t3)
        for ident, c in self._c_iconos.items():
            c.poner_seleccionada(ident in self._iconos)
        self._aplicar_iconos_on()
        capa.addStretch(1)
        self._reloj = QTimer(self)
        self._reloj.timeout.connect(self._tic)
        self._reloj.start(self.TIC_MS)

    # -- construcción
    def _tarjeta(self, titulo, descripcion):
        t = Tarjeta(espacio=12, margenes=(22, 18, 22, 18))
        t.capa.addWidget(Etiqueta(titulo, 18, peso='medio', color='#FFFFFF'))
        t.capa.addWidget(Etiqueta(descripcion, 13, color=TEXT_MUTED, envolver=True))
        return t

    def _carta(self, ident, nombre, detalle, tipo, capa, pack=False):
        previa = poster = None
        carpeta = F.carpeta_efectos() / 'previas'
        nombre_archivo = (f'{tipo}_{ident}' if tipo != 'iconos' else f'iconos_{ident}') if ident else None
        if nombre_archivo:
            m, j = carpeta / f'{nombre_archivo}.mp4', carpeta / f'{nombre_archivo}.jpg'
            previa = m if m.is_file() else None
            poster = j if j.is_file() else None
        c = TarjetaEfecto(ident, nombre, detalle, previa, poster, ninguna=not ident, pack=pack)
        if pack:
            c.clic.connect(self._abrir_palabras)
            c.cambio.connect(self._pack_activo)
        else:
            c.clic.connect(lambda i, t=tipo: self._tocar(t, i))
        capa.addWidget(c)
        self._tarjetas.append(c)
        return c

    @staticmethod
    def _texto_cuanto(clave, opciones):
        return next((t for k, t in opciones if k == clave), opciones[0][1])

    @staticmethod
    def _pintar_unico(cartas, elegido):
        for ident, c in cartas.items():
            c.poner_seleccionada(ident == (elegido or ''))

    # -- cambios
    def refrescar(self):
        """Al volver a la página: el interruptor general puede haberse movido desde el chip de Inicio."""
        try:
            self._var_activo.set(F.activado())
        except Exception:
            pass

    def _cambio_general(self):
        _guardar({'go_efectos_visuales': bool(self._var_activo.get())})
        if self._al_cambiar:
            self._al_cambiar()

    def _tocar(self, tipo, ident):
        if tipo == 'intro':
            self._intro = ident
            _guardar({'fx_intro': ident})
            self._pintar_unico(self._c_intro, ident)
        else:
            self._cortes = ident
            _guardar({'fx_cortes': ident})
            self._pintar_unico(self._c_cortes, ident)

    def _cambio_cortes(self, _v=None):
        clave = {tr('Pocos'): 'pocos', tr('Normales'): 'normal', tr('Todos'): 'todos'}.get(self._v_cortes.get(), 'pocos')
        _guardar({'fx_cortes_cuanto': clave})

    # -- el sonido de la intro
    def _refrescar_sonido(self):
        op = F.opciones_guardadas()
        f = F.fuente_sonido_intro(op)
        on = f is not None
        if bool(self._var_sonido.get()) != on:
            self._var_sonido.set(on)
        self._lbl_sonido.configure(text=(F.nombre_sonido_intro(op) + ('' if str(op.get('fx_intro_sonido')) != 'riser_1' else ' · ' + tr('últimos segundos')))
                                   if on else tr('Silenciado'))
        self._b_oir.setEnabled(on)
        self._b_original.setVisible(on and str(op.get('fx_intro_sonido')) != 'riser_1')

    def _cambio_sonido_on(self):
        if self._var_sonido.get():
            actual = F.opciones_guardadas().get('fx_intro_sonido')
            _guardar({'fx_intro_sonido': 'riser_1' if str(actual or 'ninguno').lower() in ('ninguno', '') else actual})
        else:
            _guardar({'fx_intro_sonido': 'ninguno'})
        self._refrescar_sonido()

    def _cambiar_sonido(self):
        try:
            ruta = ui.filedialog.askopenfilename(title=tr('Elige el sonido de la intro'), filetypes=[(tr('Audio'), '*.mp3 *.wav *.m4a *.aac *.flac *.ogg *.aiff *.aif'), (tr('Todos'), '*.*')],
                                                 parent=self.window())
        except Exception:
            ruta = ''
        if ruta:
            _guardar({'fx_intro_sonido': str(ruta)})
            self._refrescar_sonido()

    def _sonido_original(self):
        _guardar({'fx_intro_sonido': 'riser_1'})
        self._refrescar_sonido()

    def _oir_sonido(self):
        try:
            F.oir_sonido_intro()
        except Exception:
            pass

    # -- los iconos
    def _aplicar_iconos_on(self):
        apagados = not bool(self._var_iconos_on.get())
        for c in self._c_iconos.values():
            c.poner_apagada(apagados)
        self._sw_extra.setEnabled(not apagados)

    def _cambio_iconos_on(self):
        _guardar({'fx_iconos_activo': bool(self._var_iconos_on.get())})
        self._aplicar_iconos_on()

    def _cambio_extra(self):
        _guardar({'fx_iconos_extra': bool(self._var_extra.get())})

    def _pack_activo(self, ident, activo):
        if activo:
            self._iconos.add(ident)
        else:
            self._iconos.discard(ident)
        _guardar({'fx_iconos': [p for p, _n, _d in F.PACKS_ICONOS if p in self._iconos]})

    def _abrir_palabras(self, ident):
        nombre = next((tr(n) for p, n, _d in F.PACKS_ICONOS if p == ident), ident)
        if self._dialogo is not None and ui.vivo(self._dialogo):
            self._dialogo.close()
        self._dialogo = DialogoPalabras(self.window(), ident, nombre, self._guardar_palabras)
        self._dialogo.show()

    def _guardar_palabras(self, pack, lista):
        propias = dict(F.opciones_guardadas().get('fx_iconos_palabras') or {})
        if [p.lower() for p in lista] == [p.lower() for p in F.PALABRAS_POR_DEFECTO.get(pack, ())]:
            propias.pop(pack, None)                       # igual que las de fábrica: no hace falta guardarlas
        else:
            propias[pack] = lista
        _guardar({'fx_iconos_palabras': propias})

    def _cambio_iconos(self, _v=None):
        clave = {tr('Pocos'): 'pocos', tr('Normales'): 'normal', tr('Muchos'): 'muchos'}.get(self._v_iconos.get(), 'normal')
        _guardar({'fx_iconos_cuanto': clave})

    # -- las vistas previas solo se mueven mientras se ven
    def _tic(self):
        visible_pagina = self.isVisible()
        for c in self._tarjetas:
            v = visible_pagina and not c.visibleRegion().isEmpty()
            c.poner_visible(v)
            if v:
                c.update()
