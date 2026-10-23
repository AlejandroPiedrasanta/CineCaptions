# CineCaptions · By Cinema Productions
# 1_codigo/sonido_skill_ui.py — la página SONIDO (v5.43) tipo LÍNEA DE TIEMPO: lo que decidió sonido_skill, carril por carril, y retoques a mano.
"""
Reemplaza a la página del «AI Sound Director» (ya no se muestra). Arriba a abajo:

    cabecera     «Sonido», el video y una línea de estado (al día en Resolve / cambios sin aplicar)
    controles    estilo (Automático según el tema · Elegante · Dinámico · Lista · Tipografía cinética), gancho al inicio, video de fiesta o mar,
                 carpeta de la biblioteca, «Rehacer el sonido» y «Aplicar a Resolve»
    línea        LineaTiempo: regla de segundos, carriles guía (palabras clave de los captions, cortes) y un carril por pista de Resolve
                 (AI SFX MOTION / IMPACTS / TONAL / UI / TEXTURE) con cada sonido como bloque (largo real, línea en su PICO = el frame del evento);
                 zoom − / +, desplazamiento horizontal; clic en un bloque → inspector
    inspector    qué es, en qué segundo, qué archivo y POR QUÉ; ▶ Escuchar, Otra variante, ◀ / ▶ un fotograma, Quitar (sonido_skill.editar)
    revisión     la crítica de siempre (repetidos, amontonados, impactos de más) y el interruptor para los próximos GO

Todo lo que cuesta va por correr_en_hilo; sin globos: una línea de estado.
"""
from pathlib import Path

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QScrollArea, QSizePolicy, QVBoxLayout, QWidget

import qt_kit as ui
from i18n import tr
from qt_kit import Boton, Combo, Etiqueta, Interruptor, StringVar, Tarjeta, caja_h

TEXT_MUTED = ui.TEXT_MUTED
ESTILOS = (('auto', 'Automático (según el tema)'), ('elegante', 'Elegante'), ('dinamico', 'Dinámico'), ('lista', 'Lista / top'),
           ('cinetica', 'Tipografía cinética'))
NOMBRE_TIPO = {'gancho': 'Gancho', 'acento': 'Acento', 'texto_grande': 'Palabra clave', 'texto_chico': 'Subtítulo', 'aro': 'Aro',
               'corte': 'Corte', 'corte_fuerte': 'Cambio de escena', 'transicion': 'Transición', 'flash': 'Flash', 'logo': 'Logo',
               'barrido_luz': 'Brillo', 'neon': 'Neón', 'icono': 'Ícono', 'tarjeta': 'Tarjeta', 'foto': 'Foto', 'numero_precio': 'Dinero',
               'check': 'Check', 'boton_on': 'Botón ON', 'boton_off': 'Botón OFF', 'cursor_click': 'Click', 'notificacion': 'Notificación',
               'barra_carga': 'Carga', 'pagina': 'Página', 'glitch': 'Glitch', 'tachado': 'Tachado', 'positivo': 'Positivo',
               'negativo': 'Negativo', 'grafica': 'Gráfica'}
CARRILES = (('AI SFX MOTION', 'Movimiento', '#4589FF'), ('AI SFX IMPACTS', 'Impactos', '#FF5D73'), ('AI SFX TONAL', 'Acentos', '#F5C451'),
            ('AI SFX UI', 'Interfaz', '#2BD4A4'), ('AI SFX TEXTURE', 'Textura', '#B07CFF'))
FPS = 30.0


def _mmss(t):
    t = float(t or 0)
    return f'{int(t // 60)}:{t % 60:05.2f}'


class LineaTiempo(QWidget):
    """La línea de tiempo del sonido: guía + un carril por pista; clic en un bloque = seleccionado(índice en filas)."""
    seleccionado = Signal(int)
    IZQ, REGLA, GUIA, ALTO = 112, 26, 24, 34

    def __init__(self, padre=None):
        super().__init__(padre)
        self.filas, self.guia, self.sel, self.pps = [], {}, -1, 60.0
        self._cajas = []
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setMouseTracking(True)

    def poner(self, filas, guia):
        self.filas, self.guia = filas or [], guia or {}
        self.sel = min(self.sel, len(self.filas) - 1)
        self._medir()

    def duracion(self):
        return max([float(self.guia.get('duracion') or 0)] + [float(f.get('segundo') or 0) + 1.5 for f in self.filas] + [5.0])

    def zoom(self, factor):
        self.pps = max(20.0, min(320.0, self.pps * factor))
        self._medir()

    def _medir(self):
        ancho = int(self.IZQ + self.duracion() * self.pps + 40)
        alto = int(self.REGLA + 2 * self.GUIA + len(CARRILES) * self.ALTO + 10)
        self.setFixedSize(ancho, alto)
        self.update()

    def x_de(self, t):
        return self.IZQ + float(t) * self.pps

    def paintEvent(self, _ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        f = ui.fuente(10)
        p.setFont(f)
        w, h = self.width(), self.height()
        p.fillRect(QRectF(0, 0, w, h), QColor('#0B1424'))
        dur = self.duracion()
        # regla
        paso = 1 if self.pps >= 45 else 2 if self.pps >= 25 else 5
        p.setPen(QPen(QColor('#3A4A66'), 1))
        for s in range(0, int(dur) + 1, paso):
            x = self.x_de(s)
            p.drawLine(int(x), self.REGLA - 6, int(x), h)
            p.setPen(QColor('#8D9BB5'))
            p.drawText(int(x) + 3, 16, _mmss(s)[:-3])
            p.setPen(QPen(QColor(255, 255, 255, 18), 1))
        y = self.REGLA
        # carriles guía: palabras clave y cortes
        for nombre, items, color in (('Palabras clave', [(c['t'], c['texto']) for c in self.guia.get('captions') or []], '#E0EBFB'),
                                     ('Cortes', [(t, '') for t in self.guia.get('cortes') or []], '#8D9BB5')):
            p.fillRect(QRectF(0, y, w, self.GUIA - 2), QColor(255, 255, 255, 6))
            p.setPen(QColor('#8D9BB5'))
            p.drawText(QRectF(10, y, self.IZQ - 14, self.GUIA - 2), Qt.AlignmentFlag.AlignVCenter, tr(nombre))
            for t, texto in items:
                x = self.x_de(t)
                p.setPen(QPen(QColor(color), 2))
                p.drawLine(int(x), int(y + 4), int(x), int(y + self.GUIA - 6))
                if texto and self.pps >= 45:
                    p.setPen(QColor(color))
                    p.drawText(int(x) + 4, int(y + self.GUIA - 8), texto.replace('caption ', '').split(' (')[0][:16])
            y += self.GUIA
        # carriles de sonido
        self._cajas = []
        fila_de = {c[0]: k for k, c in enumerate(CARRILES)}
        for k, (_pista, nombre, color) in enumerate(CARRILES):
            yy = y + k * self.ALTO
            p.fillRect(QRectF(0, yy, w, self.ALTO - 4), QColor(255, 255, 255, 10 if k % 2 == 0 else 5))
            p.setPen(QColor(color))
            p.drawText(QRectF(10, yy, self.IZQ - 14, self.ALTO - 4), Qt.AlignmentFlag.AlignVCenter, tr(nombre))
        for i, f_ in enumerate(self.filas):
            k = fila_de.get(f_.get('pista'), 3)
            color = QColor(CARRILES[k][2])
            ini = float(f_.get('ini') if f_.get('ini') is not None else f_.get('segundo') or 0)
            dur_ = max(0.08, float(f_.get('dur') or 0.3))
            caja = QRectF(self.x_de(ini), y + k * self.ALTO + 4, max(6.0, dur_ * self.pps), self.ALTO - 12)
            self._cajas.append((caja, i))
            relleno = QColor(color)
            relleno.setAlpha(230 if i == self.sel else 120)
            p.setPen(QPen(QColor('#FFFFFF') if i == self.sel else color, 2 if i == self.sel else 1))
            p.setBrush(relleno)
            p.drawRoundedRect(caja, 6, 6)
            xp = self.x_de(f_.get('segundo') or 0)          # el PICO = el frame del evento
            p.setPen(QPen(QColor('#FFFFFF'), 2))
            p.drawLine(int(xp), int(caja.top() + 2), int(xp), int(caja.bottom() - 2))
            if caja.width() > 48:
                p.setPen(QColor('#0B1220'))
                p.drawText(caja.adjusted(6, 0, -4, 0), Qt.AlignmentFlag.AlignVCenter, NOMBRE_TIPO.get(f_.get('tipo'), '')[:10])
        p.end()

    def mousePressEvent(self, ev):
        pos = ev.position()
        for caja, i in reversed(self._cajas):
            if caja.contains(pos):
                self.sel = i
                self.update()
                self.seleccionado.emit(i)
                return


class PaginaSonido(QWidget):
    """La página SONIDO. `video` = función que da el video de Inicio; `offset` = desplazamiento de GO en el timeline (Aplicar)."""

    def __init__(self, padre=None, video=None, offset=None):
        super().__init__(padre)
        import sonido_skill as S
        self._video_fn = video or (lambda: '')
        self._offset_fn = offset or (lambda: 0)
        self._ocupado = False
        self._res = {}
        prefs = S._prefs()
        capa = QVBoxLayout(self)
        capa.setContentsMargins(0, 0, 0, 0)
        capa.setSpacing(12)
        cab, cc = caja_h(espacio=14)
        col = QVBoxLayout()
        col.setSpacing(2)
        col.addWidget(Etiqueta(tr('Sonido'), 24, peso='extra', color='#FFFFFF'))
        self._lbl_video = ui.Elidida('', 13, color=TEXT_MUTED)
        col.addWidget(self._lbl_video)
        cc.addLayout(col, 1)
        self._lbl_cuenta = Etiqueta('', 13, color='#E0EBFB')
        cc.addWidget(self._lbl_cuenta, 0, Qt.AlignmentFlag.AlignBottom)
        capa.addWidget(cab)
        self._lbl_estado = Etiqueta(tr('Haz GO con un video: aquí ves qué sonido va en cada momento y por qué.'), 12, color=TEXT_MUTED, envolver=True)
        capa.addWidget(self._lbl_estado)

        # ---- controles
        t = Tarjeta(espacio=10, margenes=(20, 14, 20, 14))
        fila, cf = caja_h(espacio=12)
        cf.addWidget(Etiqueta(tr('Estilo'), 13, color='#E0EBFB'))
        actual = dict(ESTILOS).get(prefs.get(S.PREF_ESTILO) or 'auto', ESTILOS[0][1])
        self._var_estilo = StringVar(tr(actual))
        cf.addWidget(Combo([tr(n) for _, n in ESTILOS], self._var_estilo, self._cambio_estilo, alto=34, tam=13), 1)
        self._var_gancho = ui.BooleanVar(prefs.get(S.PREF_GANCHO, True) is not False)
        cf.addWidget(Interruptor(tr('Gancho al inicio'), self._var_gancho, lambda: self._pref(S.PREF_GANCHO, bool(self._var_gancho.get())),
                                 tam=13, color='#E0EBFB'))
        self._var_fiesta = ui.BooleanVar(prefs.get(S.PREF_FIESTA, False) is True)
        cf.addWidget(Interruptor(tr('Fiesta o mar'), self._var_fiesta, lambda: self._pref(S.PREF_FIESTA, bool(self._var_fiesta.get())),
                                 tam=13, color='#E0EBFB'))
        t.capa.addWidget(fila)
        fila, cf = caja_h(espacio=12)
        self._lbl_lib = ui.Elidida('', 12, color=TEXT_MUTED)
        cf.addWidget(self._lbl_lib, 1)
        cf.addWidget(Boton(tr('Cambiar carpeta…'), self._elegir_carpeta, alto=34, tam=12))
        self._b_rehacer = Boton(tr('Rehacer el sonido'), self._rehacer, alto=40, tam=13)
        cf.addWidget(self._b_rehacer)
        self._b_aplicar = Boton(tr('Aplicar a Resolve'), self._aplicar, tipo='primario', alto=40, tam=13, negrita=True)
        cf.addWidget(self._b_aplicar)
        t.capa.addWidget(fila)
        capa.addWidget(t)

        # ---- línea de tiempo
        lt = Tarjeta(espacio=8, margenes=(16, 12, 16, 12))
        fila, cf = caja_h(espacio=8)
        cf.addWidget(Etiqueta(tr('Línea de tiempo del sonido'), 15, peso='medio', color='#FFFFFF'), 1)
        cf.addWidget(Boton('−', lambda: self._zoom(1 / 1.4), alto=30, ancho=36, tam=14))
        cf.addWidget(Boton('+', lambda: self._zoom(1.4), alto=30, ancho=36, tam=14))
        lt.capa.addWidget(fila)
        self._linea = LineaTiempo()
        self._linea.seleccionado.connect(self._elegir)
        self._scroll = QScrollArea()
        self._scroll.setWidget(self._linea)
        self._scroll.setWidgetResizable(False)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet('QScrollArea{background:#0B1424;border:none;border-radius:8px}')
        self._scroll.viewport().setStyleSheet('background:#0B1424')
        self._scroll.setFixedHeight(self._linea.REGLA + 2 * self._linea.GUIA + len(CARRILES) * self._linea.ALTO + 30)
        lt.capa.addWidget(self._scroll)
        capa.addWidget(lt)

        # ---- inspector
        ins = Tarjeta(espacio=8, margenes=(20, 14, 20, 14))
        self._lbl_sel = Etiqueta(tr('Toca un sonido de la línea para ver por qué está ahí.'), 15, peso='medio', color='#FFFFFF', envolver=True)
        ins.capa.addWidget(self._lbl_sel)
        self._lbl_porque = Etiqueta('', 13, color='#C9D6EA', envolver=True)
        ins.capa.addWidget(self._lbl_porque)
        fila, cf = caja_h(espacio=10)
        self._b_oir = Boton(tr('▶ Escuchar'), self._oir, alto=36, tam=13)
        self._b_var = Boton(tr('Otra variante'), lambda: self._editar('variante'), alto=36, tam=13)
        self._b_izq = Boton(tr('◀ 1 fotograma'), lambda: self._editar('mover', -1 / FPS), alto=36, tam=13)
        self._b_der = Boton(tr('1 fotograma ▶'), lambda: self._editar('mover', 1 / FPS), alto=36, tam=13)
        self._b_quitar = Boton(tr('Quitar'), lambda: self._editar('quitar'), alto=36, tam=13)
        for b in (self._b_oir, self._b_var, self._b_izq, self._b_der, self._b_quitar):
            cf.addWidget(b)
        cf.addStretch(1)
        ins.capa.addWidget(fila)
        self._lbl_revision = Etiqueta('', 12, color=TEXT_MUTED, envolver=True)
        ins.capa.addWidget(self._lbl_revision)
        capa.addWidget(ins)

        on = Tarjeta(espacio=12, margenes=(20, 10, 20, 10), horizontal=True)
        on.capa.addWidget(Etiqueta(tr('Poner el sonido con la biblioteca en los próximos GO'), 13, peso='medio', color='#E0EBFB'), 1)
        self._var_on = ui.BooleanVar(S.activo(prefs))
        on.capa.addWidget(Interruptor(tr('Activado'), self._var_on, lambda: self._pref(S.PREF_ON, bool(self._var_on.get())),
                                      tam=13, color='#E0EBFB'))
        capa.addWidget(on)
        capa.addStretch(1)
        self._botones_sel(False)

    # ------------------------------------------------------------------ datos
    def video(self):
        try:
            return str(self._video_fn() or '').strip().strip('"')
        except Exception:
            return ''

    def _estado(self, texto):
        self._lbl_estado.setText(str(texto))

    def _pref(self, clave, valor):
        import sonido_skill as S
        try:
            S.poner_pref(**{clave: valor})
        except Exception:
            pass

    def _cambio_estilo(self, *_):
        elegido = self._var_estilo.get()
        self._pref('sonido_estilo', next((k for k, n in ESTILOS if tr(n) == elegido), 'auto'))
        self._estado(tr('Estilo guardado. Pulsa «Rehacer el sonido» para oírlo en este video.'))

    def _elegir_carpeta(self):
        import sonido_skill as S
        ruta = ui.filedialog.askdirectory(title=tr('Elige la carpeta de tu biblioteca de sonidos (la que tiene MAPA_SFX.md)'), parent=self.window())
        if ruta:
            self._pref(S.PREF_LIB, str(ruta))
            self._lbl_lib.setText(tr('Biblioteca: {r}', r=ruta))
            self._estado(tr('Biblioteca cambiada. Pulsa «Rehacer el sonido».'))

    def _zoom(self, factor):
        self._linea.zoom(factor)

    def refrescar(self):
        if self._ocupado:
            return
        import sonido_skill as S
        v = self.video()
        self._lbl_video.setText(Path(v).name if v else tr('Sin video'))
        ui.correr_en_hilo(self, lambda: S.resumen(v), self._pintar)

    def _pintar(self, res, err=None):
        import sonido_skill as S
        if err is not None or not isinstance(res, dict):
            self._estado(tr('No pude leer el sonido del video: {e}', e=err))
            return
        self._res = res
        self._lbl_lib.setText(tr('Biblioteca: {r}', r=res.get('biblioteca') or ''))
        if res.get('video'):
            self._lbl_video.setText(Path(res['video']).name)
        filas = res.get('filas') or []
        self._linea.poner(filas, res.get('guia'))
        estilo = S.NOMBRE_ESTILO.get(res.get('estilo') or '', '')
        self._lbl_cuenta.setText(tr('{n} sonidos · {e}', n=len(filas), e=estilo) if filas else '')
        avisos = S.revisar(filas) if filas else []
        self._lbl_revision.setText(tr('Revisión: todo en orden.') if filas and not avisos else ('Revisión: ' + ' · '.join(avisos[:4]) if avisos else ''))
        self._elegir(self._linea.sel) if 0 <= self._linea.sel < len(filas) else self._botones_sel(False)
        if not filas:
            self._estado(tr('Haz GO con este video: el sonido sale de tu biblioteca y aquí ves cada decisión.'))
        elif res.get('pendiente'):
            self._estado(tr('Hay cambios sin poner en Resolve: pulsa «Aplicar a Resolve».'))
        else:
            self._estado(tr('Al día en Resolve ({f}).', f=res.get('en_resolve') or res.get('fecha') or ''))

    def _botones_sel(self, si):
        for b in (self._b_oir, self._b_var, self._b_izq, self._b_der, self._b_quitar):
            b.setEnabled(bool(si))

    def _elegir(self, i):
        filas = self._res.get('filas') or []
        if not 0 <= i < len(filas):
            self._botones_sel(False)
            return
        f = filas[i]
        self._lbl_sel.setText(f"{_mmss(f.get('segundo'))}  ·  {NOMBRE_TIPO.get(f.get('tipo'), f.get('tipo'))}  ·  {Path(f['archivo']).stem}")
        self._lbl_porque.setText(tr('Por qué: {p}', p=f.get('por_que') or '—') + '   ·   ' + str(f.get('pista') or ''))
        self._botones_sel(True)

    # ------------------------------------------------------------------ acciones
    def _trabajar(self, texto, trabajo, fin):
        if self._ocupado:
            return
        self._ocupado = True
        for b in (self._b_rehacer, self._b_aplicar):
            b.setEnabled(False)
        self._estado(texto)

        def listo(r, err):
            self._ocupado = False
            for b in (self._b_rehacer, self._b_aplicar):
                b.setEnabled(True)
            if err is not None:
                self._estado(tr('Algo falló: {e}', e=err))
                return
            fin(r)
        ui.correr_en_hilo(self, trabajo, listo)

    def _oir(self):
        import director_sonido_sesion as DS
        filas = self._res.get('filas') or []
        i = self._linea.sel
        if 0 <= i < len(filas) and filas[i].get('wav'):
            try:
                DS.reproducir(filas[i]['wav'])
            except Exception as e:
                self._estado(tr('No pude reproducirlo: {e}', e=e))

    def _editar(self, accion, valor=None):
        import sonido_skill as S
        v, i = self.video(), self._linea.sel

        def trabajo():
            ok, msg = S.editar(v, i, accion, valor)
            return ok, msg, S.resumen(v)

        def fin(r):
            ok, msg, res = r
            if accion == 'quitar':
                self._linea.sel = -1
            self._pintar(res)
            self._estado(msg)
        self._trabajar(tr('Cambiando el sonido…'), trabajo, fin)

    def _rehacer(self):
        import sonido_skill as S
        v = self.video()
        if not v:
            self._estado(tr('Primero carga un video en Inicio.'))
            return

        def trabajo():
            ok, msg = S.rehacer(v)
            return ok, msg, S.resumen(v)

        def fin(r):
            ok, msg, res = r
            self._linea.sel = -1
            self._pintar(res)
            self._estado(msg)
        self._trabajar(tr('Rehaciendo el sonido con tu biblioteca…'), trabajo, fin)

    def _aplicar(self):
        import director_sonido_sesion as DS
        import sonido_skill as S
        v = self.video()
        try:
            off = int(self._offset_fn() or 0)
        except Exception:
            off = 0

        def trabajo():
            ok, msg = DS.aplicar(v, offset_frames=off)
            return ok, msg, S.resumen(v)

        def fin(r):
            ok, msg, res = r
            self._pintar(res)
            self._estado(tr('Puesto en Resolve: los sonidos de la biblioteca en sus pistas; los de siempre, apagados.') if ok
                         else tr('No se pudo poner en Resolve: {m}', m=str(msg)[:160]))
        self._trabajar(tr('Poniendo el sonido en Resolve…'), trabajo, fin)
