# CineCaptions · By Cinema Productions
# 1_codigo/vista_tema.py — la vista previa EXACTA del tema elegido en Creativo (v5.5.10): los cues del planificador del tema y el mismo dibujo que GO sin Resolve.
"""
vista_tema.py
-------------
Pedido (2026-10-17): «en Creativo ver la vista previa real de cómo se verá en DaVinci Resolve: que detecte el tema que estoy usando, que al dar play se vea
exactamente como ese tema y que, si cambio la principal, se vea en tiempo real».

    estilo_de_pack(pack)                       -> {'tipo': 'guion'|'kinetic'|'viral', 'pack'} para los 6 temas de fábrica; None para lo demás
    planificar(palabras, roles, pack, ...)     -> los cues que Generar escribiría para Resolve (el MISMO planificador del tema, con las marcas de Principal)
    Cuadros(cues, estilo, ancho, alto, fondo)  -> .cuadro(t) = QImage del instante t: la foto de fondo con los captions dibujados por render_sin_resolve
                                                  (render_temas.py para los Temas 1, 2, 3, 5 y 6; el dibujo propio del Tema 4)

planificar() y Cuadros() rasterizan con Pillow: van en un hilo (correr_en_hilo). cuadro(t) solo compone arrays pequeños: va en el hilo de la interfaz.
"""
from pathlib import Path

import numpy as np

import guion_editor
import plantillas
import render_sin_resolve as RSR


def estilo_de_pack(pack, formato='v'):
    """El estilo de dibujo de un tema de fábrica, o None (pack propio, mezcla, diseño automático: Creativo sigue con su vista de siempre)."""
    pack = str(pack or '')
    if pack not in plantillas.FABRICA:
        return None
    if pack == 'Kinetic':
        return {'tipo': 'kinetic', 'pack': pack}
    if pack == 'VIRAL':
        return {'tipo': 'viral', 'pack': pack}
    if guion_editor.es_guion(pack, formato or 'v'):
        return {'tipo': 'guion', 'pack': pack}
    return None


def _ancla(clave, defecto):
    try:
        import ajustes_ui
        return str(ajustes_ui.leer_prefs().get(clave, defecto))
    except Exception:
        return defecto


def planificar(palabras, roles, pack, estilo, idioma='es', fin_video=None, ancla_guion='medio', video=None):
    """Los cues del tema con las marcas de AHORA, como los escribe Generar (_generar_con_guion / _generar_con_kinetic), más el emoji de cada bloque.
    video: el de Proyecto (el Tema 5 saca de él el color de la frase clave, como Generar)."""
    palabras = [dict(w) for w in palabras or []]
    tipo = (estilo or {}).get('tipo')
    if tipo == 'guion':
        cues = guion_editor.planear(palabras, roles, pack, ancla=ancla_guion, fin_video=fin_video, idioma=idioma, video=video)['cues']
    elif tipo in ('kinetic', 'viral'):
        mains = guion_editor.parametros_de_marcas(palabras, roles)[0]
        if tipo == 'viral':
            import viral_planificador as kp
            res = kp.planificar(palabras, idioma=idioma, ancho_tl=1080, alto_tl=1920, ancla=_ancla('viral_ancla', 'bajo'), mains=mains, fin_video=fin_video)
        else:
            import kinetic_planificador as kp
            res = kp.planificar(palabras, idioma=idioma, ancla=_ancla('kinetic_ancla', 'bajo'), mains=mains, fin_video=fin_video)
        cues = res['cues']
    else:
        return []
    if tipo != 'kinetic':                     # (Kinetic no lleva emojis): el emoji elegido en Creativo para una palabra del bloque
        for c in cues:
            if c.get('emoji'):
                continue
            a, b = float(c.get('start') or 0.0), float(c.get('end') or 0.0)
            for w in palabras:
                t = float(w.get('start') or 0.0)
                if w.get('emoji') and a <= t < b:
                    c['emoji'], c['emoji_ini'] = w['emoji'], t
                    break
    return cues


def cue_de_palabra(cues, palabra, t):
    """Índice del cue donde SALE esa palabra (dicha en t): el que la lleva escrita, el más cercano en el tiempo; None si ninguno la lleva.
    Por tiempo solo no basta: un bloque de Kinetic puede empezar después de su primera palabra (se retrasa para no pisar el anterior)."""
    import guion_planificador as G
    plano = G._plano(str(palabra or ''))
    mejor, dist = None, 4.0
    if not plano:
        return None
    for i, c in enumerate(cues or []):
        textos = [str(r.get('texto') or '') for r in c.get('runs') or []] + [str(ln.get('text') or '') for ln in c.get('lines') or []]
        if not any(plano == G._plano(tok) for txt in textos for tok in txt.split()):
            continue
        a, b = float(c.get('start') or 0.0), float(c.get('end') or 0.0)
        d = 0.0 if a - 0.05 <= t <= b else min(abs(t - a), abs(t - b))
        if d < dist:
            mejor, dist = i, d
    return mejor


def ruta_fondo():
    try:
        import instalador_scripts
        return Path(instalador_scripts.BASE_RECURSOS) / 'creativo' / 'movil_fondo.jpg'
    except Exception:
        return Path(__file__).resolve().parent.parent / '2_recursos' / 'creativo' / 'movil_fondo.jpg'


def _fondo_cubriendo(ruta, ancho, alto):
    """La foto de muestra cubriendo ancho×alto (recortada al centro), como uint8 HxWx3."""
    from PIL import Image
    try:
        with Image.open(ruta) as im:
            im = im.convert('RGB')
            esc = max(ancho / im.width, alto / im.height)
            im = im.resize((max(1, int(round(im.width * esc))), max(1, int(round(im.height * esc)))), Image.LANCZOS)
            x0, y0 = (im.width - ancho) // 2, (im.height - alto) // 2
            im = im.crop((x0, y0, x0 + ancho, y0 + alto))
            return np.ascontiguousarray(np.asarray(im, dtype=np.uint8))
    except Exception:
        return np.full((alto, ancho, 3), 12, dtype=np.uint8)


class Cuadros:
    """Los cuadros de la vista: la foto de fondo del tamaño de la pantalla del móvil y las capas de TODOS los cues ya rasterizadas.
    El cuadro 9:16 del video va a lo ancho y centrado en la pantalla (render_sin_resolve.encaje), como un reel en un móvil."""

    def __init__(self, cues, estilo, ancho, alto, fondo=None):
        self.ancho, self.alto = int(ancho), int(alto)
        self.cues = list(cues or [])
        self.estilo = estilo
        self.fondo = _fondo_cubriendo(fondo or ruta_fondo(), self.ancho, self.alto)
        emoji_arriba = _ancla('emoji_posicion', '') != 'abajo'          # como GO sin Resolve: arriba, salvo que se eligiera «Abajo» en Sonido
        self.capas = RSR.preparar(self.cues, self.ancho, self.alto, emoji_arriba=emoji_arriba, estilo=estilo)

    def cue_en(self, t):
        """Índice del cue que se ve en t (o el último que empezó antes; el primero si t va antes de todos)."""
        k = 0
        for i, c in enumerate(self.cues):
            if float(c.get('start') or 0.0) <= t:
                k = i
            else:
                break
        return k if self.cues else -1

    def cue_de_palabra(self, palabra, t):
        k = cue_de_palabra(self.cues, palabra, t)
        return k if k is not None else self.cue_en(t)

    def instante_quieto(self, k):
        """Un instante del cue k con TODOS sus elementos ya dentro (para la vista quieta de un bloque)."""
        if not (0 <= k < len(self.cues)):
            return 0.0
        c = self.cues[k]
        a, b = float(c.get('start') or 0.0), float(c.get('end') or 0.0)
        entradas = [cp['t0'] + cp['entrada'] for cp in self.capas if a <= cp['t0'] < b]
        t = (max(entradas) + 0.12) if entradas else a + 0.3
        return max(a, min(t, b - 0.04))

    def cuadro_array(self, t):
        arr = self.fondo.copy()
        RSR.componer(arr, self.capas, float(t))
        return arr

    def cuadro(self, t):
        """QImage (RGB888) del instante t. Se crea en el hilo de la interfaz (solo compone)."""
        from PySide6.QtGui import QImage
        arr = self.cuadro_array(t)
        h, w = arr.shape[:2]
        return QImage(arr.data, w, h, 3 * w, QImage.Format.Format_RGB888).copy()
