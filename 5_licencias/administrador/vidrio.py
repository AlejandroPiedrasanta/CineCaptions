# CineCaptions · By Cinema Productions
# 5_licencias/administrador/vidrio.py — Administrador de Licencias: cristal, resortes, orbe y tarjetas de producto.
"""Cinema Productions · Administrador de Licencias — piezas visuales de la versión 6.

  - `Resorte`: animación con FÍSICA de resorte (rigidez, amortiguación y masa). Nada es lineal: los botones
    rebotan al soltarse, las tarjetas se elevan y vuelven a su sitio con un pequeño sobreimpulso.
  - `Cristal`: tarjeta de vidrio (capas, borde translúcido de 1 px, brillo que SIGUE al cursor).
  - `TarjetaProducto`: producto con precio, ventas, ingresos y minigráfico; sube al pasar el cursor y se
    hunde (0.97) al pulsar.
  - `OrbeParticulas`: esfera de malla y puntos que respira y gira; reacciona al cursor (parallax).
  - `InterruptorCristal`, `RachaSemana`, `BarraMeta`, `Sparkline`, iconos pintados (dinero, personas).

Todo se pinta con QPainter (sin imágenes) y toma sus colores del tema activo. Si las animaciones están
desactivadas en Ajustes, los resortes saltan directo al valor final.

Creado por Cinema Productions.
"""
from __future__ import annotations

import math
from datetime import datetime
import random

from PySide6.QtCore import QElapsedTimer, QObject, QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import (QColor, QCursor, QFont, QFontMetrics, QLinearGradient, QPainter, QPainterPath, QPen,
                           QPixmap, QRadialGradient)
from PySide6.QtWidgets import QAbstractButton, QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget

from interfaz import ANIM, C, ContadorAnimado, etiqueta, legible, ms, tinte

__author__ = "Cinema Productions"


def _alfa(color: str | QColor, a: float) -> QColor:
    c = QColor(color)
    c.setAlphaF(max(0.0, min(1.0, a)))
    return c


def _oscuro() -> bool:
    return bool(C.get("oscuro", True))


# ============================================================ resortes

class Resorte(QObject):
    """Valor que persigue un destino como un resorte amortiguado (integración por pasos de 1/240 s).

    rigidez (k)      cuánto tira hacia el destino. Alta = rápido.
    amortiguación(c) frena. ζ = c / (2·√(k·m)); ζ < 1 deja un pequeño rebote, ζ ≥ 1 no rebota.
    masa (m)         inercia: más masa = más lento y más sobreimpulso.
    """

    cambiado = Signal(float)

    def __init__(self, padre: QObject, valor: float = 0.0, rigidez: float = 320.0, amortiguacion: float = 24.0,
                 masa: float = 1.0):
        super().__init__(padre)
        self.x = self.destino = float(valor)
        self.v = 0.0
        self.k, self.c, self.m = rigidez, amortiguacion, masa
        self._reloj = QElapsedTimer()
        self._t = QTimer(self)
        self._t.setTimerType(Qt.TimerType.PreciseTimer)
        self._t.setInterval(8)
        self._t.timeout.connect(self._paso)

    def ir_a(self, destino: float, impulso: float = 0.0):
        self.destino = float(destino)
        self.v += impulso
        if not ms(1):
            self.x, self.v = self.destino, 0.0
            self._t.stop()
            self.cambiado.emit(self.x)
            return
        if not self._t.isActive():
            self._reloj.restart()
            self._t.start()

    def fijar(self, valor: float):
        """Salta sin animar."""
        self.x = self.destino = float(valor)
        self.v = 0.0
        self._t.stop()
        self.cambiado.emit(self.x)

    def _paso(self):
        dt = min(self._reloj.restart() / 1000.0, 1 / 20) / max(0.35, ANIM.get("factor", 1.0) or 1.0)
        n = max(1, int(dt * 240))
        h = dt / n
        for _ in range(n):
            a = (-self.k * (self.x - self.destino) - self.c * self.v) / self.m
            self.v += a * h
            self.x += self.v * h
        if abs(self.v) < 0.004 and abs(self.x - self.destino) < 0.0006:
            self.x, self.v = self.destino, 0.0
            self._t.stop()
        self.cambiado.emit(self.x)


# ============================================================ cristal

class Cristal(QFrame):
    """Contenedor de vidrio: degradado sutil, borde de 1 px translúcido y un foco de luz que sigue al cursor.

    Se usa igual que un QFrame: pon dentro un layout y widgets.
    """

    def __init__(self, acento: str | None = None, radio: int = 18, objectName: str = "cristal"):
        super().__init__(objectName=objectName)
        self.acento = acento
        self.radio = radio
        self._pos = QPointF(-999, -999)
        self._luz = Resorte(self, 0.0, 180.0, 22.0)
        self._luz.cambiado.connect(lambda _: self.update())
        self._vigia = QTimer(self)
        self._vigia.setInterval(16)
        self._vigia.timeout.connect(self._seguir)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

    def _color(self) -> QColor:
        return QColor(self.acento or C["acento"])

    def enterEvent(self, e):
        self._luz.ir_a(1.0)
        if not self._vigia.isActive():
            self._vigia.start()
        super().enterEvent(e)

    def _seguir(self):
        p = self.mapFromGlobal(QCursor.pos())
        dentro = self.rect().contains(p)
        if dentro:
            self._pos = QPointF(p)
            self.update()
        elif self._luz.destino:
            self._luz.ir_a(0.0)
            self._vigia.stop()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        forma = QPainterPath()
        forma.addRoundedRect(r, self.radio, self.radio)
        oscuro = _oscuro()
        base = QLinearGradient(r.topLeft(), r.bottomLeft())
        if oscuro:
            base.setColorAt(0, _alfa(QColor(C["panel2"]).lighter(112), 0.96))
            base.setColorAt(1, _alfa(C["panel"], 0.98))
        else:
            base.setColorAt(0, QColor("#ffffff"))
            base.setColorAt(1, QColor(C["panel2"]))
        p.fillPath(forma, base)
        p.setClipPath(forma)
        luz = self._luz.x
        if luz > 0.01:                                                  # foco que sigue al cursor
            foco = QRadialGradient(self._pos, max(self.width(), self.height()) * 0.62)
            foco.setColorAt(0, _alfa(self._color(), (0.20 if oscuro else 0.14) * luz))
            foco.setColorAt(1, _alfa(self._color(), 0))
            p.fillPath(forma, foco)
        brillo = QLinearGradient(r.topLeft(), QPointF(r.left(), r.top() + r.height() * 0.45))   # reflejo superior
        brillo.setColorAt(0, _alfa("#ffffff", 0.07 if oscuro else 0.5))
        brillo.setColorAt(1, _alfa("#ffffff", 0))
        p.fillPath(forma, brillo)
        p.setClipping(False)
        p.setPen(QPen(_alfa("#ffffff", 0.10) if oscuro else QColor(C["borde"]), 1))             # borde de 1 px
        p.drawPath(forma)
        if luz > 0.01:                                                  # el borde se enciende cerca del cursor
            borde = QRadialGradient(self._pos, max(self.width(), self.height()) * 0.5)
            borde.setColorAt(0, _alfa(self._color().lighter(135), 0.75 * luz))
            borde.setColorAt(1, _alfa(self._color(), 0))
            p.setPen(QPen(borde, 1.4))
            p.drawPath(forma)


# ============================================================ minigráfico y barras

class Sparkline(QWidget):
    """Línea suave con área degradada. Se dibuja con trazo de crecimiento al aparecer."""

    def __init__(self, color: str | None = None, alto: int = 34):
        super().__init__()
        self.color = color
        self.valores: list[float] = []
        self.setFixedHeight(alto)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._prog = Resorte(self, 1.0, 120.0, 18.0)
        self._prog.cambiado.connect(lambda _: self.update())

    def fijar(self, valores: list[float]):
        cambio = list(valores) != self.valores
        self.valores = list(valores)
        if cambio:
            self._prog.fijar(0.0)
            self._prog.ir_a(1.0)
        self.update()

    def paintEvent(self, _):
        pintar_sparkline(self, self.rect(), self.valores, QColor(self.color or C["acento"]), self._prog.x)


def pintar_sparkline(p_o_widget, rect, valores: list[float], color: QColor, progreso: float = 1.0):
    p = QPainter(p_o_widget) if isinstance(p_o_widget, QWidget) else p_o_widget
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    r = QRectF(rect).adjusted(2, 3, -2, -3)
    if len(valores) < 2 or r.width() < 4:
        return
    m = max(valores) or 1.0
    n = len(valores)
    pts = [QPointF(r.left() + r.width() * i / (n - 1), r.bottom() - r.height() * (v / m) * min(1.0, progreso * 1.0))
           for i, v in enumerate(valores)]
    linea = QPainterPath(pts[0])
    for a, b in zip(pts, pts[1:]):                                      # curva suave
        medio = (a.x() + b.x()) / 2
        linea.cubicTo(QPointF(medio, a.y()), QPointF(medio, b.y()), b)
    area = QPainterPath(linea)
    area.lineTo(r.right(), r.bottom())
    area.lineTo(r.left(), r.bottom())
    area.closeSubpath()
    grad = QLinearGradient(r.topLeft(), r.bottomLeft())
    grad.setColorAt(0, _alfa(color, 0.32))
    grad.setColorAt(1, _alfa(color, 0))
    p.fillPath(area, grad)
    p.setPen(QPen(color, 1.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    p.drawPath(linea)
    if progreso >= 0.98 and valores[-1] > 0:
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(_alfa(color, 0.35))
        p.drawEllipse(pts[-1], 5, 5)
        p.setBrush(color)
        p.drawEllipse(pts[-1], 2.6, 2.6)


class BarraMeta(QWidget):
    """Barra de progreso con brillo (como la de pasos de la referencia): se llena con resorte."""

    def __init__(self, color: str | None = None, alto: int = 14):
        super().__init__()
        self.color = color
        self.setFixedHeight(alto + 8)
        self._v = Resorte(self, 0.0, 90.0, 13.0)
        self._v.cambiado.connect(lambda _: self.update())

    def fijar(self, fraccion: float):
        self._v.ir_a(max(0.0, min(1.0, fraccion)))

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        h = self.height() - 8
        r = QRectF(0, 4, self.width(), h)
        color = QColor(self.color or C["ok"])
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(_alfa("#ffffff", 0.07) if _oscuro() else QColor(C["borde"]))
        p.drawRoundedRect(r, h / 2, h / 2)
        ancho = max(h, r.width() * max(0.0, min(1.1, self._v.x)))
        lleno = QRectF(0, 4, min(ancho, r.width()), h)
        halo = QRadialGradient(lleno.center(), max(lleno.width(), 30))
        halo.setColorAt(0, _alfa(color, 0.35))
        halo.setColorAt(1, _alfa(color, 0))
        p.setBrush(halo)
        p.drawRoundedRect(lleno.adjusted(-6, -4, 6, 4), h, h)
        g = QLinearGradient(lleno.topLeft(), lleno.topRight())
        g.setColorAt(0, color.darker(115))
        g.setColorAt(1, color.lighter(118))
        p.setBrush(g)
        p.drawRoundedRect(lleno, h / 2, h / 2)


# ============================================================ interruptor de cristal

class InterruptorCristal(QAbstractButton):
    """Interruptor ancho de cristal (inspirado en el ON naranja): al activarse se enciende con brillo de color,
    la perilla se desliza con resorte y rebota un poco. Pulsarlo la hunde (0.97)."""

    def __init__(self, texto_on: str = "ON", texto_off: str = "OFF", color: str | None = None):
        super().__init__()
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(132, 46)
        self.on, self.off, self.color = texto_on, texto_off, color
        self._pos = Resorte(self, 0.0, 380.0, 19.0, 0.9)          # ζ≈0.5: rebota lo justo
        self._pulso = Resorte(self, 1.0, 520.0, 30.0)
        for r in (self._pos, self._pulso):
            r.cambiado.connect(lambda _: self.update())
        self.toggled.connect(lambda v: self._pos.ir_a(1.0 if v else 0.0))

    def fijar_sin_animar(self, valor: bool):
        self.blockSignals(True)
        self.setChecked(valor)
        self.blockSignals(False)
        self._pos.fijar(1.0 if valor else 0.0)

    def mousePressEvent(self, e):
        self._pulso.ir_a(0.97)
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        self._pulso.ir_a(1.0)
        super().mouseReleaseEvent(e)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        p.translate(w / 2, h / 2)
        p.scale(self._pulso.x, self._pulso.x)
        p.translate(-w / 2, -h / 2)
        t = max(0.0, min(1.2, self._pos.x))
        color = QColor(self.color or C["aviso"])
        r = QRectF(3, 3, w - 6, h - 6)
        p.setPen(Qt.PenStyle.NoPen)
        pista = QLinearGradient(r.topLeft(), r.bottomLeft())
        pista.setColorAt(0, _alfa("#000000", 0.55) if _oscuro() else QColor(C["borde2"]))
        pista.setColorAt(1, _alfa("#ffffff", 0.06) if _oscuro() else QColor(C["borde"]))
        p.setBrush(pista)
        p.drawRoundedRect(r, r.height() / 2, r.height() / 2)
        if t > 0.02:                                                     # estela de luz detrás de la perilla
            cx = r.left() + r.height() / 2 + (r.width() - r.height()) * t
            luz = QLinearGradient(r.left(), 0, cx, 0)
            luz.setColorAt(0, _alfa(color, 0))
            luz.setColorAt(1, _alfa(color, min(1.0, t) * 0.95))
            p.setBrush(luz)
            p.drawRoundedRect(QRectF(r.left(), r.top(), cx - r.left() + r.height() / 2, r.height()), r.height() / 2,
                              r.height() / 2)
        p.setPen(QPen(_alfa("#ffffff", 0.14) if _oscuro() else QColor(C["borde2"]), 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(r, r.height() / 2, r.height() / 2)
        activo = self.isChecked()
        d = r.height() - 8                                               # perilla de cristal
        x = r.left() + 4 + (r.width() - r.height()) * t
        f = QFont(self.font())
        f.setBold(True)
        f.setPixelSize(14)
        p.setFont(f)
        texto = self.off if not activo else self.on
        libre = (QRectF(r.left() + 12, r.top(), max(10.0, x - r.left() - 18), r.height()) if activo else
                 QRectF(x + d + 6, r.top(), max(10.0, r.right() - (x + d) - 18), r.height()))
        p.setPen(_alfa("#ffffff" if (_oscuro() or activo) else C["texto"], 0.95 if activo else 0.8))
        p.drawText(libre, Qt.AlignmentFlag.AlignCenter, QFontMetrics(f).elidedText(
            texto, Qt.TextElideMode.ElideRight, int(libre.width())))
        perilla = QRectF(x, r.top() + 4, d, d)
        p.setPen(Qt.PenStyle.NoPen)
        sombra = QRadialGradient(perilla.center() + QPointF(0, 3), d)
        sombra.setColorAt(0, _alfa("#000000", 0.35))
        sombra.setColorAt(1, _alfa("#000000", 0))
        p.setBrush(sombra)
        p.drawEllipse(perilla.adjusted(-4, -2, 4, 6))
        g = QLinearGradient(perilla.topLeft(), perilla.bottomRight())
        g.setColorAt(0, _alfa("#ffffff", 0.92))
        g.setColorAt(1, _alfa(color.lighter(160) if activo else QColor("#c9ccd6"), 0.85))
        p.setBrush(g)
        p.drawEllipse(perilla)
        p.setPen(QPen(_alfa("#ffffff", 0.7), 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(perilla.adjusted(0.5, 0.5, -0.5, -0.5))
        p.setPen(QPen(_alfa("#000000", 0.12), 1))                       # rayitas del cristal
        for i in range(-3, 4):
            p.drawLine(QPointF(perilla.center().x() + i * 3.2 - 4, perilla.bottom() - 6),
                       QPointF(perilla.center().x() + i * 3.2 + 4, perilla.top() + 6))


# ============================================================ racha / semana

class RachaSemana(QWidget):
    """Resumen estilo «racha»: llama, número de días y los 7 días de la semana con palomitas verdes.
    Muestra qué días hubo actividad (ventas o uso) y marca el día de hoy con un anillo."""

    DIAS = ("Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom")

    def __init__(self, titulo: str = "RACHA", unidad: str = "DÍAS"):
        super().__init__()
        self.titulo, self.unidad = titulo, unidad
        self.racha = 0
        self.dias = [False] * 7
        self.hoy = 0
        self.setMinimumSize(300, 150)
        self._ap = Resorte(self, 0.0, 110.0, 14.0)
        self._llama = QTimer(self)
        self._llama.setInterval(60)
        self._fase = 0.0
        self._llama.timeout.connect(self._parpadeo)
        self._ap.cambiado.connect(lambda _: self.update())

    def fijar(self, racha: int, dias: list[bool], hoy: int):
        self.racha, self.dias, self.hoy = racha, list(dias), hoy
        self._ap.fijar(0.0)
        self._ap.ir_a(1.0)
        self.update()

    def showEvent(self, e):
        super().showEvent(e)
        if ms(1):
            self._llama.start()

    def hideEvent(self, e):
        self._llama.stop()
        super().hideEvent(e)

    def _parpadeo(self):
        self._fase += 0.35
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        fuego = QColor("#ff4a1c")
        # llama
        cx, cy = 34.0, 36.0
        halo = QRadialGradient(QPointF(cx, cy + 4), 34)
        halo.setColorAt(0, _alfa(fuego, 0.45 + 0.08 * math.sin(self._fase)))
        halo.setColorAt(1, _alfa(fuego, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(halo)
        p.drawEllipse(QPointF(cx, cy + 4), 34, 34)
        s = 1.0 + 0.03 * math.sin(self._fase * 1.3)
        llama = QPainterPath()
        llama.moveTo(cx, cy - 22 * s)
        llama.cubicTo(cx + 5, cy - 12, cx + 22, cy - 6, cx + 20, cy + 10)
        llama.cubicTo(cx + 18, cy + 24, cx - 18, cy + 24, cx - 20, cy + 10)
        llama.cubicTo(cx - 22, cy - 2, cx - 8, cy - 8, cx, cy - 22 * s)
        g = QLinearGradient(cx, cy - 22, cx, cy + 24)
        g.setColorAt(0, QColor("#ff7a2e"))
        g.setColorAt(1, QColor("#ff2d12"))
        p.setBrush(g)
        p.drawPath(llama)
        p.setBrush(QColor("#fff3e6"))
        p.drawEllipse(QPointF(cx, cy + 12), 6, 7.5)
        # texto
        f = QFont(self.font())
        f.setPixelSize(11)
        f.setBold(True)
        f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.2)
        p.setFont(f)
        p.setPen(QColor(C["tenue"]))
        p.drawText(QPointF(72, 24), self.titulo)
        f2 = QFont(self.font())
        f2.setPixelSize(30)
        f2.setBold(True)
        p.setFont(f2)
        p.setPen(QColor(C["titulo"]))
        n = f"{round(self.racha * self._ap.x)}"
        p.drawText(QPointF(72, 54), n)
        ancho_n = QFontMetrics(f2).horizontalAdvance(n)
        f3 = QFont(self.font())
        f3.setPixelSize(13)
        p.setFont(f3)
        p.setPen(QColor(C["suave"]))
        p.drawText(QPointF(72 + ancho_n + 8, 54), self.unidad)
        p.setPen(QPen(_alfa("#ffffff", 0.08) if _oscuro() else QColor(C["borde"]), 1))
        p.drawLine(QPointF(10, 72), QPointF(w - 10, 72))
        # días
        ancho = (w - 20) / 7
        for i in range(7):
            c = QPointF(10 + ancho * (i + 0.5), 100)
            rad = min(17.0, ancho * 0.38)
            t = max(0.0, min(1.0, self._ap.x * 1.4 - i * 0.07))
            p.setPen(Qt.PenStyle.NoPen)
            if self.dias[i]:
                v = QRadialGradient(c + QPointF(-3, -4), rad * 1.4)
                v.setColorAt(0, QColor("#8dff6a"))
                v.setColorAt(1, QColor("#38b81c"))
                p.setBrush(v)
                p.drawEllipse(c, rad * t, rad * t)
                if t > 0.8:
                    p.setPen(QPen(QColor("#0a1f06"), 2.4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
                                  Qt.PenJoinStyle.RoundJoin))
                    p.drawPolyline([c + QPointF(-6, 0.5), c + QPointF(-1.8, 5), c + QPointF(6.5, -5)])
            else:
                p.setBrush(_alfa("#ffffff", 0.05) if _oscuro() else QColor(C["panel2"]))
                p.drawEllipse(c, rad, rad)
                if i == self.hoy:
                    p.setBrush(Qt.BrushStyle.NoBrush)
                    p.setPen(QPen(QColor("#38b81c"), 2.2))
                    p.drawArc(QRectF(c.x() - rad, c.y() - rad, rad * 2, rad * 2), 90 * 16, -250 * 16)
            f4 = QFont(self.font())
            f4.setPixelSize(11)
            p.setFont(f4)
            p.setPen(QColor(C["titulo"] if i == self.hoy else C["tenue"]))
            p.drawText(QRectF(c.x() - ancho / 2, 122, ancho, 18), Qt.AlignmentFlag.AlignCenter, self.DIAS[i])


# ============================================================ tarjeta de producto

class TarjetaProducto(QWidget):
    """Tarjeta de producto pintada a mano: insignia degradada, nombre, precio, tres números y minigráfico.

    Resortes: al pasar el cursor sube (escala 1.025, rigidez 340 / amortiguación 22) y al pulsar se hunde a 0.97
    (rigidez 520 / amortiguación 30, casi sin rebote para que se sienta táctil). El borde de la tarjeta elegida
    brilla con el color de su plataforma.
    """

    clic = Signal(str)
    doble_clic = Signal(str)
    ALTO, ANCHO_MIN = 176, 250

    def __init__(self, producto: dict, color: str, icono: str, moneda_txt: str = ""):
        super().__init__()
        self.p, self.color, self.icono, self.moneda_txt = producto, QColor(color), icono, moneda_txt
        self.elegida = False
        self.setFixedHeight(self.ALTO)
        self.setMinimumWidth(self.ANCHO_MIN)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMouseTracking(True)
        self._pos = QPointF(-999, -999)
        self._escala = Resorte(self, 1.0, 340.0, 22.0)
        self._luz = Resorte(self, 0.0, 200.0, 24.0)
        self._sel = Resorte(self, 0.0, 260.0, 20.0)
        self._ap = Resorte(self, 0.0, 120.0, 15.0)
        for r in (self._escala, self._luz, self._sel, self._ap):
            r.cambiado.connect(lambda _: self.update())
        self._pulsada = False
        self.setToolTip(producto.get("nombre", ""))

    # --- estado
    def fijar_elegida(self, v: bool):
        self.elegida = v
        self._sel.ir_a(1.0 if v else 0.0)

    def aparecer(self, retardo_ms: int = 0):
        """Entrada: cada tarjeta sube y se llena con resorte, una tras otra."""
        self._ap.fijar(0.0)
        def subir():
            try:
                self._ap.ir_a(1.0)
            except RuntimeError:          # la tarjeta ya se reemplazó
                pass

        QTimer.singleShot(int(retardo_ms * (ANIM.get("factor", 1.0) or 0)), subir)

    # --- ratón
    def enterEvent(self, e):
        self._escala.ir_a(1.025)
        self._luz.ir_a(1.0)
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._escala.ir_a(1.0)
        self._luz.ir_a(0.0)
        self._pulsada = False
        super().leaveEvent(e)

    def mouseMoveEvent(self, e):
        self._pos = e.position()
        self.update()
        super().mouseMoveEvent(e)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._pulsada = True
            self._escala.ir_a(0.97)
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        if self._pulsada and e.button() == Qt.MouseButton.LeftButton:
            self._escala.ir_a(1.025 if self.underMouse() else 1.0, impulso=0.5)
            self.clic.emit(self.p["clave"])
        self._pulsada = False
        super().mouseReleaseEvent(e)

    def mouseDoubleClickEvent(self, e):
        self.doble_clic.emit(self.p["clave"])

    # --- pintura
    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        a = max(0.0, min(1.0, self._ap.x))
        sube = (1 - a) * 22
        s = self._escala.x
        p.translate(w / 2, h / 2 + sube)
        p.scale(s, s)
        p.translate(-w / 2, -h / 2)
        p.setOpacity(min(1.0, a * 1.6))
        r = QRectF(7, 7, w - 14, h - 14)
        oscuro = _oscuro()
        sombra = QRadialGradient(QPointF(w / 2, h - 6), w * 0.5)
        sombra.setColorAt(0, _alfa(self.color if self._luz.x > 0.05 else "#000000", 0.30 * (0.4 + self._luz.x * 0.8)))
        sombra.setColorAt(1, _alfa("#000000", 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(sombra)
        p.drawEllipse(QPointF(w / 2, h - 8), w * 0.46, 11)
        forma = QPainterPath()
        forma.addRoundedRect(r, 18, 18)
        fondo = QLinearGradient(r.topLeft(), r.bottomRight())
        if oscuro:
            fondo.setColorAt(0, _alfa(QColor(C["panel2"]).lighter(118), 0.98))
            fondo.setColorAt(1, _alfa(C["panel"], 1))
        else:
            fondo.setColorAt(0, QColor("#ffffff"))
            fondo.setColorAt(1, QColor(C["panel2"]))
        p.fillPath(forma, fondo)
        p.setClipPath(forma)
        tinta = QRadialGradient(QPointF(r.left() + 40, r.top() + 30), r.width() * 0.8)     # tinte del color de la plataforma
        tinta.setColorAt(0, _alfa(self.color, 0.20 if oscuro else 0.13))
        tinta.setColorAt(1, _alfa(self.color, 0))
        p.fillPath(forma, tinta)
        if self._luz.x > 0.02:
            foco = QRadialGradient(self._pos, r.width() * 0.7)
            foco.setColorAt(0, _alfa("#ffffff" if oscuro else self.color, (0.10 if oscuro else 0.10) * self._luz.x))
            foco.setColorAt(1, _alfa("#ffffff", 0))
            p.fillPath(forma, foco)
        p.setClipping(False)
        sel = self._sel.x
        borde = QColor(self.color.lighter(125)) if sel > 0.02 else QColor("#ffffff" if oscuro else C["borde"])
        p.setPen(QPen(_alfa(borde, 0.11 + 0.8 * sel + 0.25 * self._luz.x) if oscuro or sel > 0.02 else QColor(C["borde"]),
                      1 + 0.9 * sel))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(forma)
        if sel > 0.02:                                                       # halo de la tarjeta elegida
            halo = QPainterPath()
            halo.addRoundedRect(r.adjusted(-2, -2, 2, 2), 20, 20)
            p.setPen(QPen(_alfa(self.color, 0.22 * sel), 4))
            p.drawPath(halo)

        # insignia
        ins = QRectF(r.left() + 16, r.top() + 16, 42, 42)
        gi = QLinearGradient(ins.topLeft(), ins.bottomRight())
        gi.setColorAt(0, self.color.lighter(135))
        gi.setColorAt(1, self.color.darker(125))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(gi)
        p.drawRoundedRect(ins, 13, 13)
        brillo = QLinearGradient(ins.topLeft(), QPointF(ins.left(), ins.center().y()))
        brillo.setColorAt(0, _alfa("#ffffff", 0.45))
        brillo.setColorAt(1, _alfa("#ffffff", 0))
        p.setBrush(brillo)
        p.drawRoundedRect(ins.adjusted(1, 1, -1, -ins.height() / 2), 12, 12)
        fi = QFont(self.font())
        fi.setPixelSize(21)
        p.setFont(fi)
        p.setPen(QColor("#ffffff"))
        p.drawText(ins, Qt.AlignmentFlag.AlignCenter, self.icono)

        # estado (publicado / oculto)
        activo = self.p.get("activo", True)
        fe = QFont(self.font())
        fe.setPixelSize(10)
        fe.setBold(True)
        p.setFont(fe)
        txt = "● PUBLICADO" if activo else "● OCULTO"
        col = QColor(C["ok"] if activo else C["tenue"])
        wt = QFontMetrics(fe).horizontalAdvance(txt) + 16
        pil = QRectF(r.right() - 16 - wt, r.top() + 22, wt, 22)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(_alfa(col, 0.16))
        p.drawRoundedRect(pil, 11, 11)
        p.setPen(col if oscuro else col.darker(130))
        p.drawText(pil, Qt.AlignmentFlag.AlignCenter, txt)

        # nombre y precio
        fn = QFont(self.font())
        fn.setPixelSize(15)
        fn.setBold(True)
        p.setFont(fn)
        p.setPen(QColor(C["titulo"]))
        nombre = QFontMetrics(fn).elidedText(self.p.get("nombre", ""), Qt.TextElideMode.ElideRight, int(r.width() - 32))
        p.drawText(QPointF(r.left() + 16, r.top() + 80), nombre)
        fp = QFont(self.font())
        fp.setPixelSize(12)
        p.setFont(fp)
        p.setPen(QColor(C["suave"]))
        sub = "  ·  ".join(x for x in (self.p.get("precio_txt"), self.moneda_txt) if x)
        p.drawText(QPointF(r.left() + 16, r.top() + 98), QFontMetrics(fp).elidedText(
            sub or " ", Qt.TextElideMode.ElideRight, int(r.width() - 32)))

        # tres números + minigráfico
        y = r.bottom() - 40
        cols = ((str(self.p.get("ventas", 0)), "ventas"), (self._ingresos(), "ingresos"),
                (str(self.p.get("activas", 0)), "licencias"))
        interior = r.width() - 32
        pesos = (0.17, 0.27, 0.19)
        for i, (valor, texto) in enumerate(cols):
            ancho_col = interior * pesos[i]
            x = r.left() + 16 + interior * sum(pesos[:i])
            fv = QFont(self.font())
            fv.setPixelSize(15)
            fv.setBold(True)
            p.setFont(fv)
            p.setPen(QColor(legible(self.color.name()) if i == 0 else C["titulo"]))
            p.drawText(QRectF(x, y, ancho_col, 20), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                       QFontMetrics(fv).elidedText(valor, Qt.TextElideMode.ElideRight, int(ancho_col - 4)))
            fl = QFont(self.font())
            fl.setPixelSize(10)
            p.setFont(fl)
            p.setPen(QColor(C["tenue"]))
            p.drawText(QRectF(x, y + 18, ancho_col, 14), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, texto)
        pintar_sparkline(p, QRectF(r.right() - 16 - interior * 0.35, y - 2, interior * 0.35, 38),
                         self.p.get("serie", []), self.color.lighter(120) if oscuro else self.color.darker(110), a)

    def _ingresos(self) -> str:
        ing = self.p.get("ingresos") or {}
        if not ing:
            return "—"
        moneda, total = max(ing.items(), key=lambda x: x[1])
        simbolo = {"USD": "$", "$": "$", "EUR": "€", "GBP": "£"}.get(moneda, moneda)
        texto = f"{total / 1000:.1f}k" if total >= 10000 else f"{total:,.0f}"
        return f"{simbolo}{texto}" if len(simbolo) == 1 else f"{texto} {simbolo}"

    def sizeHint(self):
        from PySide6.QtCore import QSize
        return QSize(self.ANCHO_MIN, self.ALTO)


class Cuadricula(QWidget):
    """Reparte widgets en filas según el ancho disponible (como la galería de «Acceso rápido»)."""

    def __init__(self, ancho_min: int = 250, espacio: int = 14, alto_fila: int = 176):
        super().__init__()
        self.ancho_min, self.espacio, self.alto_fila = ancho_min, espacio, alto_fila
        self.items: list[QWidget] = []

    def poner(self, widgets: list[QWidget]):
        for w in self.items:
            w.setParent(None)
            w.deleteLater()
        self.items = list(widgets)
        for w in self.items:
            w.setParent(self)
            w.show()
        self._acomodar()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._acomodar()

    def _acomodar(self):
        if not self.items:
            self.setMinimumHeight(0)
            return
        ancho = max(self.width(), self.ancho_min)
        cols = max(1, (ancho + self.espacio) // (self.ancho_min + self.espacio))
        w = (ancho - self.espacio * (cols - 1)) // cols
        for i, it in enumerate(self.items):
            f, c = divmod(i, cols)
            it.setGeometry(c * (w + self.espacio), f * (self.alto_fila + self.espacio), w, self.alto_fila)
        filas = -(-len(self.items) // cols)
        alto = filas * self.alto_fila + (filas - 1) * self.espacio
        if self.minimumHeight() != alto:
            self.setMinimumHeight(alto)
            self.updateGeometry()


# ============================================================ orbe de partículas

class OrbeParticulas(QWidget):
    """Esfera de malla y puntos que respira (referencia: orbe de luz azul → magenta).

    Dibuja ~700 puntos de una esfera de Fibonacci deformada con ondas, más una malla de meridianos y paralelos
    muy tenue. Gira despacio y se inclina hacia el cursor (resorte). Mezcla aditiva para el brillo. ~30 fps y solo
    cuando está visible; con las animaciones desactivadas se pinta una vez, quieto.
    """

    def __init__(self, puntos: int = 640, colores: tuple[str, str, str] | None = None):
        super().__init__()
        self.setMinimumSize(200, 200)
        self.setMouseTracking(True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        rnd = random.Random(7)
        n = puntos
        self.base = []
        oro = math.pi * (3 - math.sqrt(5))
        for i in range(n):
            y = 1 - 2 * (i + 0.5) / n
            r = math.sqrt(max(0.0, 1 - y * y))
            th = oro * i
            self.base.append((math.cos(th) * r, y, math.sin(th) * r, rnd.random()))
        self.colores = [QColor(c) for c in (colores or ("#3b6bff", "#9b5cff", "#ff3df0"))]
        self.t = 0.0
        self._gx = Resorte(self, 0.0, 60.0, 11.0)
        self._gy = Resorte(self, 0.0, 60.0, 11.0)
        self._reloj = QTimer(self)
        self._reloj.setInterval(33)
        self._reloj.timeout.connect(self._tic)

    def showEvent(self, e):
        super().showEvent(e)
        if ms(1):
            self._reloj.start()

    def hideEvent(self, e):
        self._reloj.stop()
        super().hideEvent(e)

    def _tic(self):
        self.t += 0.033 / max(0.4, ANIM.get("factor", 1.0) or 1.0)
        self.update()

    def mouseMoveEvent(self, e):
        self._gy.ir_a((e.position().x() / max(1, self.width()) - 0.5) * 0.9)
        self._gx.ir_a((e.position().y() / max(1, self.height()) - 0.5) * 0.7)

    def leaveEvent(self, e):
        self._gx.ir_a(0.0)
        self._gy.ir_a(0.0)
        super().leaveEvent(e)

    def _punto(self, x: float, y: float, z: float, t: float):
        """Deformación de la esfera: ondas que viajan, así parece un globo que respira."""
        d = (0.11 * math.sin(3 * x + 2 * y + t * 1.1) + 0.08 * math.sin(4 * z - 3 * x - t * 0.8)
             + 0.05 * math.sin(5 * y + 2 * z + t * 1.7))
        k = 1.0 + d
        return x * k, y * k, z * k

    def _color(self, x: float, y: float, a: float) -> QColor:
        """Azul arriba-izquierda → magenta abajo-derecha."""
        m = max(0.0, min(1.0, (x * 0.55 + y * 0.8) * 0.5 + 0.5))
        c0, c1, c2 = self.colores
        if m < 0.5:
            u = m / 0.5
            c = QColor(int(c0.red() + (c1.red() - c0.red()) * u), int(c0.green() + (c1.green() - c0.green()) * u),
                       int(c0.blue() + (c1.blue() - c0.blue()) * u))
        else:
            u = (m - 0.5) / 0.5
            c = QColor(int(c1.red() + (c2.red() - c1.red()) * u), int(c1.green() + (c2.green() - c1.green()) * u),
                       int(c1.blue() + (c2.blue() - c1.blue()) * u))
        c.setAlphaF(max(0.0, min(1.0, a)))
        return c

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        R = min(w, h) * 0.33
        cx, cy = w / 2, h / 2
        halo = QRadialGradient(QPointF(cx, cy), R * 1.9)
        halo.setColorAt(0, _alfa(self.colores[1], 0.20))
        halo.setColorAt(0.55, _alfa(self.colores[0], 0.07))
        halo.setColorAt(1, _alfa(self.colores[0], 0))
        p.fillRect(self.rect(), halo)
        giro = self.t * 0.25
        ay, ax = giro + self._gy.x, 0.35 + self._gx.x
        cay, say, cax, sax = math.cos(ay), math.sin(ay), math.cos(ax), math.sin(ax)

        def proyectar(x, y, z):
            x, y, z = self._punto(x, y, z, self.t)
            x, z = x * cay + z * say, -x * say + z * cay
            y, z = y * cax - z * sax, y * sax + z * cax
            f = 1.0 / (1.0 - z * 0.35)
            return QPointF(cx + x * R * f, cy + y * R * f), z, x, y

        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Plus if _oscuro()
                             else QPainter.CompositionMode.CompositionMode_SourceOver)
        # malla: meridianos y paralelos
        p.setBrush(Qt.BrushStyle.NoBrush)
        for k in range(14):
            th = math.pi * k / 14
            pts = [proyectar(math.cos(th) * math.sin(a), math.cos(a), math.sin(th) * math.sin(a))
                   for a in (math.pi * j / 36 for j in range(37))]
            for (a, za, xa, ya), (b, zb, _xb, _yb) in zip(pts, pts[1:]):
                z = (za + zb) / 2
                p.setPen(QPen(self._color(xa, ya, 0.05 + 0.22 * (z * 0.5 + 0.5)), 0.8))
                p.drawLine(a, b)
        for k in range(1, 11):
            lat = math.pi * k / 11
            pts = [proyectar(math.sin(lat) * math.cos(a), math.cos(lat), math.sin(lat) * math.sin(a))
                   for a in (2 * math.pi * j / 44 for j in range(45))]
            for (a, za, xa, ya), (b, zb, _xb, _yb) in zip(pts, pts[1:]):
                z = (za + zb) / 2
                p.setPen(QPen(self._color(xa, ya, 0.05 + 0.22 * (z * 0.5 + 0.5)), 0.8))
                p.drawLine(a, b)
        # puntos
        p.setPen(Qt.PenStyle.NoPen)
        for x, y, z, azar in self.base:
            q, zz, xx, yy = proyectar(x, y, z)
            prof = zz * 0.5 + 0.5
            tam = 0.8 + 2.0 * prof + azar * 0.8
            p.setBrush(self._color(xx, yy, 0.25 + 0.75 * prof))
            p.drawEllipse(q, tam, tam)
        # núcleo luminoso
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        brillo = QRadialGradient(QPointF(cx + R * 0.05, cy + R * 0.55), R * 0.8)
        brillo.setColorAt(0, _alfa(self.colores[2], 0.18))
        brillo.setColorAt(1, _alfa(self.colores[2], 0))
        p.fillRect(self.rect(), brillo)


# ============================================================ iconos pintados

def pixmap_dinero(tam: int = 64) -> QPixmap:
    """Dos billetes verdes con relieve (el «$» de la referencia 3D), dibujados con degradados."""
    pm = QPixmap(tam, tam)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    s = tam / 64.0
    p.scale(s, s)
    for dy, dx, rot, claro in ((12, 4, -6, False), (6, 0, -6, True)):
        p.save()
        p.translate(32 + dx, 32 + dy)
        p.rotate(rot)
        r = QRectF(-26, -14, 52, 28)
        g = QLinearGradient(r.topLeft(), r.bottomRight())
        g.setColorAt(0, QColor("#d9f99d") if claro else QColor("#86c96a"))
        g.setColorAt(1, QColor("#4ca85a") if claro else QColor("#3d8f4a"))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(g)
        p.drawRoundedRect(r, 5, 5)
        p.setBrush(_alfa("#ffffff", 0.35))
        p.drawRoundedRect(QRectF(-23, -11, 46, 8), 3, 3)
        if claro:
            p.setBrush(QColor("#5fb36a"))
            p.drawEllipse(QPointF(0, 0), 10, 10)
            f = QFont()
            f.setPixelSize(15)
            f.setBold(True)
            p.setFont(f)
            p.setPen(QColor("#f1fbe9"))
            p.drawText(QRectF(-10, -10, 20, 20), Qt.AlignmentFlag.AlignCenter, "$")
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(_alfa("#2f7d3b", 0.55))
            p.drawEllipse(QPointF(-18, 0), 3.2, 3.2)
            p.drawEllipse(QPointF(18, 0), 3.2, 3.2)
        p.restore()
    p.end()
    return pm


def pixmap_personas(tam: int = 64) -> QPixmap:
    """Dos siluetas de cristal (azul-turquesa y rosa) dentro de un cuadro redondeado, como el icono de usuarios."""
    pm = QPixmap(tam, tam)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    s = tam / 64.0
    p.scale(s, s)
    marco = QRectF(8, 8, 48, 48)
    g = QLinearGradient(marco.topLeft(), marco.bottomRight())
    g.setColorAt(0, _alfa("#ffb48a", 0.55))
    g.setColorAt(0.5, _alfa("#7aa7ff", 0.55))
    g.setColorAt(1, _alfa("#b58cff", 0.55))
    p.setPen(QPen(_alfa("#ffffff", 0.35), 1))
    p.setBrush(g)
    p.drawRoundedRect(marco, 14, 14)

    def persona(cx, cy, rad, c1, c2):
        gg = QLinearGradient(cx - rad, cy - rad, cx + rad, cy + rad * 3)
        gg.setColorAt(0, QColor(c1))
        gg.setColorAt(1, QColor(c2))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(gg)
        p.drawEllipse(QPointF(cx, cy), rad, rad)
        cuerpo = QPainterPath()
        cuerpo.moveTo(cx - rad * 1.9, cy + rad * 3.3)
        cuerpo.cubicTo(cx - rad * 1.9, cy + rad * 1.1, cx - rad * 0.9, cy + rad * 1.15, cx, cy + rad * 1.15)
        cuerpo.cubicTo(cx + rad * 0.9, cy + rad * 1.15, cx + rad * 1.9, cy + rad * 1.1, cx + rad * 1.9, cy + rad * 3.3)
        cuerpo.closeSubpath()
        p.drawPath(cuerpo)

    p.setClipRect(marco)
    persona(25, 29, 6.2, "#a5ffd6", "#46c6ff")
    persona(39, 31, 7.4, "#ff9bf0", "#ff6fa8")
    p.end()
    return pm


# ============================================================ tarjetas de datos

class KPICristal(Cristal):
    """Tarjeta de cristal con un número que sube, un icono opcional y una nota."""

    def __init__(self, titulo: str, color: str, icono=None, formato=None, ayuda: str = ""):
        super().__init__(color, 18)
        self.color = color
        self.setFixedHeight(104)
        self.setMinimumWidth(120)
        self.valor = ContadorAnimado(formato)
        self.valor.setStyleSheet(f"font-size:28px; font-weight:800; color:{legible(color)}; background:transparent;")
        self.sub = etiqueta(ayuda, "kpiSub")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(18, 12, 14, 12)
        lay.setSpacing(10)
        cuerpo = QVBoxLayout()
        cuerpo.setSpacing(1)
        cuerpo.addWidget(etiqueta(titulo.upper(), "kpiTitulo"))
        cuerpo.addWidget(self.valor)
        cuerpo.addWidget(self.sub)
        lay.addLayout(cuerpo, 1)
        if icono is not None:
            l = QLabel()
            l.setPixmap(icono)
            l.setFixedSize(icono.width(), icono.height())
            lay.addWidget(l, 0, Qt.AlignmentFlag.AlignVCenter)


def racha_semana(serie: list[int]) -> tuple[int, list[bool], int]:
    """(racha de días seguidos con ventas, los 7 días lunes→domingo de esta semana, índice de hoy)."""
    hoy = datetime.now().astimezone().date().weekday()
    dias = [False] * 7
    for i in range(hoy + 1):
        idx = len(serie) - 1 - (hoy - i)
        dias[i] = 0 <= idx < len(serie) and serie[idx] > 0
    racha, i = 0, len(serie) - 1
    if i >= 0 and serie[i] == 0:
        i -= 1                                  # si hoy aún no hay ventas, no se rompe la racha
    while i >= 0 and serie[i] > 0:
        racha += 1
        i -= 1
    return racha, dias, hoy



