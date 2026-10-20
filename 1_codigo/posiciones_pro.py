# CineCaptions · By Cinema Productions
# 1_codigo/posiciones_pro.py — «Posición» de cada efecto de la Edición PRO: el usuario marca en la línea de tiempo de SU video (con sus
# fotogramas) los segundos donde quiere cada efecto y GO lo pone ahí: solo ahí o, además, donde lo elige el automático.
"""
posiciones_pro.py
-----------------
v5.22 (el usuario: «en la página de Efectos, al hacer doble clic o con el botón Posición, la sección cambia y me muestra la línea de tiempo
con sus fotogramas para indicar dónde lo quiero; en todas las secciones; por ejemplo "detrás de ti" en el segundo tal; varias veces; que
sea interactivo y útil» y «deja un botón para decidir: solo mis marcas o mis marcas + automático»).

Datos: ~/DaVinciSubtitles/posiciones_pro.json = {clave del video: {'video': ruta, 'secciones': {sección: {'modo': 'solo'|'suma',
'ts': [s, …]}}}} (siempre con archivos_seguros). Los segundos son del ARCHIVO de video; GO los pasa a su timeline (con las pausas
quitadas, pausas.mapear) con para_plan().

    leer(ruta) / guardar(ruta, sección, ts, modo)     las marcas de un video
    para_plan(ruta, recorte)                           {sección: {'modo', 'ts' (s del timeline de GO)}} de las secciones ENCENDIDAS
    fotogramas(ruta)                                   las miniaturas del video (PyAV, en caché; derechas aunque el móvil grabe «acostado»)
    palabras(ruta)                                     lo que se dice y cuándo (de la caché de la voz, si ese video ya se transcribió)
    VistaPosiciones                                    la vista de Efectos: la línea de tiempo con fotogramas, las marcas y el modo

En GO (edicion_pro): las secciones «ligadas» a un caption (detrás de ti, píldora) eligen el bloque de captions de ese segundo; las demás
(gancho, escenas, kit, gráficos, B-roll) empiezan JUSTO en la marca con la pieza más cercana a lo que se dice ahí; «Motions completo» solo
sale en los tramos marcados (con «+ automático», en todo el video, como siempre).
"""
import hashlib
import json
import os
from pathlib import Path

from i18n import tr

ARCHIVO = Path.home() / 'DaVinciSubtitles' / 'posiciones_pro.json'
CACHE = Path.home() / 'DaVinciSubtitles' / 'cache_posiciones'
MODOS = ('solo', 'suma')
SECCIONES = ('detras', 'gancho', 'pildora', 'emoji', 'broll', 'motions_completo', 'escenas', 'kit', 'graficos')
LIGADAS = ('detras', 'pildora', 'emoji')  # van con un bloque de captions: la marca elige el bloque de ese segundo (v5.25: + emojis animados)
N_FOTOS = 60
ALTO_FOTO = 120
PASO = 0.1                               # las marcas van en décimas de segundo
_PROVEEDOR = None
_PONER = None
# v5.27 (el usuario: «que tenga topes de recomendación para que el caption quede bien»): «detrás de ti» necesita a una PERSONA en el cuadro;
# la tira pinta en verde dónde queda bien y las marcas no salen de ahí (zonas_detras). Además, cuántas como mucho (cada una es un recorte con
# Magic Mask que Resolve rastrea: muchas lo cargan) y lo mínimo entre dos (en el mismo caption sobran)
CON_PERSONA = ('detras',)
TOPE_MARCAS = {'detras': 8}
SEPARACION_MIN = 1.0
PASO_ZONAS = 0.5                         # cada cuánto se mira el video
ZONA_MIN_S = 0.6                         # un tramo bueno más corto no vale (un caption dura más)
ZONA_CORONILLA_MIN = 0.2                 # la pila de un caption mide ~0,15 del alto: con la cabeza más arriba, el texto no cabe (TEMA6USAR.mp4: 0,16)
ZONA_X = (0.15, 0.85)                    # la cabeza, no pegada a un lado (el caption va centrado)
MOVIMIENTO_ZONA = (0.06, 0.08)           # lo que puede moverse la cabeza entre dos miradas seguidas (alto, ancho) sin cortar la zona
VERSION_ZONAS = 1


# ======================================================================================================================== datos
def clave_video(ruta):
    try:
        return os.path.normcase(os.path.abspath(str(ruta)))
    except Exception:
        return str(ruta)


def _todo():
    try:
        import archivos_seguros
        d = archivos_seguros.leer_json(ARCHIVO, defecto={})
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def leer(ruta):
    """{sección: {'modo': 'solo'|'suma', 'ts': [s ordenados]}} de ese video ({} si no tiene marcas)."""
    if not ruta:
        return {}
    e = _todo().get(clave_video(ruta)) or {}
    out = {}
    for sec, m in (e.get('secciones') or {}).items():
        if not isinstance(m, dict):
            continue
        ts = sorted(round(float(t), 2) for t in m.get('ts') or [] if isinstance(t, (int, float)) and t >= 0)
        out[sec] = {'modo': m.get('modo') if m.get('modo') in MODOS else 'solo', 'ts': ts}
    return out


def guardar(ruta, seccion, ts, modo='solo'):
    """Guarda las marcas de una sección de ese video (las demás secciones y videos no se tocan). True si se guardó."""
    if not ruta or seccion not in SECCIONES:
        return False
    clave = clave_video(ruta)
    e = dict(_todo().get(clave) or {})
    secciones = dict(e.get('secciones') or {})
    limpias = sorted({round(max(0.0, float(t)), 2) for t in ts or []})
    if limpias or modo != 'solo':
        secciones[seccion] = {'modo': modo if modo in MODOS else 'solo', 'ts': limpias}
    else:
        secciones.pop(seccion, None)
    e.update(video=str(ruta), secciones=secciones)
    try:
        import archivos_seguros
        return bool(archivos_seguros.mezclar_json(ARCHIVO, {clave: e}))
    except Exception:
        return False


def leer_linea(ruta, imagen=None):
    """Las marcas de lo que suena en `ruta`, en SU tiempo: {sección: {'modo', 'ts'}}. v5.27: se guardan con el VIDEO (segundos del archivo); con
    el audio de un timeline («Obtener», o GO pulsado sin volver a soltar el video) se pasan a su tiempo con el desfase de su clip principal. Antes
    GO buscaba las marcas con la ruta del .wav y no veía las hechas sobre el video: «Listo» y GO no las aplicaba. `imagen` = fuente_imagen(ruta)
    si ya se conoce; si no, se lee (en un HILO)."""
    img, desde, dur = imagen or fuente_imagen(ruta, duracion=False)
    if not img or clave_video(img) == clave_video(ruta):
        return leer(ruta)
    out = {}
    for sec, m in leer(img).items():
        ts = [max(0.0, round(t - desde, 2)) for t in m['ts'] if t - desde >= -0.05 and (dur is None or t - desde <= dur + 0.05)]
        out[sec] = {'modo': m['modo'], 'ts': sorted(set(ts))}
    for sec, m in leer(ruta).items():                    # (las de antes de la 5.27, guardadas con la ruta del audio)
        if m['ts']:
            o = out.setdefault(sec, {'modo': m['modo'], 'ts': []})
            o['ts'] = sorted(set(o['ts']) | set(m['ts']))
    return out


def guardar_linea(ruta, seccion, ts, modo='solo', imagen=None):
    """guardar() con los segundos de lo que suena en `ruta` (leer_linea): con el audio de un timeline, van al VIDEO en segundos del archivo
    (las marcas de ese video fuera del tramo del audio no se tocan)."""
    img, desde, dur = imagen or fuente_imagen(ruta, duracion=False)
    if not img or clave_video(img) == clave_video(ruta):
        return guardar(ruta, seccion, ts, modo)
    fuera = [t for t in (leer(img).get(seccion) or {}).get('ts') or [] if t < desde - 0.05 or (dur is not None and t > desde + dur + 0.05)]
    ok = guardar(img, seccion, fuera + [float(t) + desde for t in ts or []], modo)
    if (leer(ruta).get(seccion) or {}).get('ts'):
        guardar(ruta, seccion, [], 'solo')               # (lo viejo con la ruta del audio ya va con el video)
    return ok


_IMAGENES = {}                                           # clave de la ruta → fuente_imagen (lo leen los hilos; la interfaz solo lo consulta)


def _imagen_rapida(ruta):
    """fuente_imagen(ruta) sin mirar el disco desde la interfaz: un video es él mismo; un audio, lo que ya averiguó un hilo (o None, y se averigua)."""
    if Path(str(ruta)).suffix.lower() not in AUDIO:
        return str(ruta), 0.0, None
    k = clave_video(ruta)
    if k not in _IMAGENES:
        _IMAGENES[k] = None
        import threading

        def averiguar():
            try:
                _IMAGENES[k] = fuente_imagen(ruta)
            except Exception:
                pass
        threading.Thread(target=averiguar, daemon=True, name='posiciones-imagen').start()
    return _IMAGENES.get(k)


def resumen(ruta, seccion):
    """(cuántas marcas, modo) de una sección de lo que suena en `ruta` (se llama desde la interfaz: no lee videos)."""
    try:
        img = _imagen_rapida(ruta)
        m = (leer_linea(ruta, img) if img else leer(ruta)).get(seccion) or {}
    except Exception:
        m = {}
    return len(m.get('ts') or []), m.get('modo') or 'solo'


def _mapear(t, segmentos):
    """El segundo `t` de la fuente en el timeline recortado; si cae en una pausa quitada, el instante con voz más cercano."""
    import pausas
    n = pausas.mapear(t, segmentos)
    if n is not None:
        return n
    for d in range(1, 31):
        for s in (+1, -1):
            n = pausas.mapear(t + s * d * 0.1, segmentos)
            if n is not None:
                return n
    return None


def para_plan(ruta, recorte=None):
    """Las marcas de ese video para GO: {sección: {'modo', 'ts' (segundos de SU timeline)}}, solo de las secciones encendidas en GO.
    v5.27: `ruta` puede ser el audio del timeline (GO sin soltar el video): valen las marcas hechas sobre su video (leer_linea)."""
    try:
        datos = leer_linea(ruta)
    except Exception:
        datos = leer(ruta)
    if not datos:
        return {}
    try:
        import pro_lateral_ui as LAT
        encendida = LAT.estado
    except Exception:
        encendida = None
    segs = (recorte or {}).get('segmentos') if recorte else None
    out = {}
    for sec, m in datos.items():
        if not m['ts']:
            continue
        try:
            if encendida is not None and not encendida(sec):
                continue
        except Exception:
            pass
        ts = []
        for t in m['ts']:
            n = _mapear(t, segs) if segs else t
            if n is not None:
                ts.append(round(float(n), 3))
        if ts:
            out[sec] = {'modo': m['modo'], 'ts': sorted(set(ts))}
    return out


def poner_proveedor(fn, poner=None):
    """El programa dice cuál es el video de Inicio (el que va a usar GO) y, v5.27, cómo poner otro (`poner(ruta)`, para «Listo»)."""
    global _PROVEEDOR, _PONER
    _PROVEEDOR = fn
    _PONER = poner


def poner_video_inicio(ruta):
    """v5.27: «Listo» con un video elegido a mano (no el de Inicio): pasa a ser el de Inicio, así el próximo GO lo usa con sus marcas. True si se puso."""
    try:
        if _PONER and ruta:
            _PONER(str(ruta))
            return True
    except Exception:
        pass
    return False


def es_de_inicio(ruta):
    """¿`ruta` es (o es el video de) lo que GO usará? (sin mirar el disco: con el audio de un timeline, lo que ya se averiguó)."""
    actual = video_actual()
    if not actual or not ruta:
        return False
    if clave_video(actual) == clave_video(ruta):
        return True
    img = _imagen_rapida(actual)
    return bool(img and img[0] and clave_video(img[0]) == clave_video(ruta))


def video_actual():
    """La ruta del video de Inicio (sin mirar el disco: se llama desde la interfaz; si no existe, la vista lo dice al leerlo en su hilo)."""
    try:
        r = _PROVEEDOR() if _PROVEEDOR else None
        r = str(r or '').strip().strip('"')
        return r or None
    except Exception:
        return None


# ======================================================================================================================== fotogramas y voz
AUDIO = ('.wav', '.mp3', '.m4a', '.aac', '.flac', '.ogg', '.aif', '.aiff')


def _carpeta_de(ruta, extra=''):
    st = os.stat(ruta)
    return CACHE / hashlib.sha1(f'{clave_video(ruta)}|{st.st_size}|{st.st_mtime_ns}|{extra}'.encode('utf-8')).hexdigest()[:16]


def _duracion(ruta):
    import av
    with av.open(str(ruta)) as c:
        if c.duration:
            return float(c.duration / 1e6)
        s = (c.streams.audio or c.streams.video or [None])[0]
        return float(s.duration * s.time_base) if s is not None and s.duration else 0.0


def fuente_imagen(ruta, duracion=True):
    """v5.23 (el usuario: «cuando obtenga el audio debe traer el video, para que Efectos tenga el video»): (archivo con imagen, desfase s,
    duración del audio s | None). Un video: él mismo. El audio que «Obtener» renderiza del timeline de Resolve: el clip principal de V1
    (video_detectado.json), con el segundo del archivo que suena al empezar ese audio (`clip_principal_desde`; recortado o con zona no es
    0). (None, 0, None) si no hay imagen. En un HILO (lee el disco). `duracion=False`: sin abrir el audio para medirlo."""
    if Path(str(ruta)).suffix.lower() not in AUDIO:
        return str(ruta), 0.0, None
    try:
        import resolve_bridge
        d = resolve_bridge.video_detectado() or {}
    except Exception:
        d = {}
    clip = d.get('clip_principal')
    if clip and clave_video(d.get('video_path') or '') == clave_video(ruta) and Path(str(clip)).is_file():
        try:
            r = str(clip), float(d.get('clip_principal_desde') or 0.0), (_duracion(ruta) if duracion else None)
        except Exception:
            r = str(clip), float(d.get('clip_principal_desde') or 0.0), None
        if duracion:
            _IMAGENES[clave_video(ruta)] = r
        return r
    return None, 0.0, None


def fotogramas(ruta, n=N_FOTOS, alto=ALTO_FOTO):
    """{'dur', 'ancho', 'alto', 'fotos': [(t, ruta .jpg)], 'imagen': archivo} sobre el TIEMPO de `ruta` (en caché) o None si no tiene
    imagen. Con el audio de un timeline, la imagen sale de su clip principal (fuente_imagen). Corre en un HILO (PyAV)."""
    img, desde, dur_audio = fuente_imagen(ruta)
    if not img:
        return None
    carpeta = _carpeta_de(img, f'{ruta}|{desde}|{dur_audio}')
    meta = carpeta / 'meta.json'
    try:
        d = json.loads(meta.read_text(encoding='utf-8'))
        if d.get('fotos') and all((carpeta / f).exists() for _t, f in d['fotos']):
            return dict(d, fotos=[(t, str(carpeta / f)) for t, f in d['fotos']], imagen=img)
    except Exception:
        pass
    import av
    import rotacion_video
    k = rotacion_video.giro(img)
    fotos = []
    with av.open(str(img)) as c:
        if not c.streams.video:
            return None
        vs = c.streams.video[0]
        vs.thread_type = 'AUTO'
        dur_v = float(c.duration / 1e6) if c.duration else (float(vs.duration * vs.time_base) if vs.duration else 0.0)
        dur = float(dur_audio) if dur_audio else dur_v          # (la línea de tiempo es la del AUDIO que transcribe GO)
        if dur <= 0 or dur_v <= 0:
            return None
        carpeta.mkdir(parents=True, exist_ok=True)
        tb = float(vs.time_base)
        w = h = 0
        for i in range(n):
            t_linea = dur * (i + 0.5) / n
            t = min(max(0.0, t_linea + desde), dur_v - 0.05)     # el segundo del ARCHIVO que se ve en ese momento
            try:
                c.seek(int(t / tb), stream=vs, backward=True, any_frame=False)
                fr = None
                for j, f in enumerate(c.decode(vs)):          # desde el fotograma clave, unos pocos hacia el segundo pedido
                    fr = f
                    if (f.time is not None and f.time >= t - 0.05) or j >= 10:
                        break
                if fr is None:
                    continue
                foto = rotacion_video.derecho_img(fr.to_image(), k)
                w, h = foto.size
                foto.thumbnail((max(1, int(alto * w / max(1, h))), alto))
                nombre = f'{i:03d}.jpg'
                foto.convert('RGB').save(carpeta / nombre, quality=82)
                fotos.append((round(t_linea, 3), nombre))
            except Exception:
                continue
    if not fotos:
        return None
    d = {'dur': round(dur, 3), 'ancho': w, 'alto': h, 'fotos': fotos}
    try:
        import archivos_seguros
        archivos_seguros.escribir_json(meta, d)
    except Exception:
        pass
    return dict(d, fotos=[(t, str(carpeta / f)) for t, f in fotos], imagen=img)


def palabras(ruta):
    """[(segundo, palabra)] de lo que se dice en ese video, si GO ya lo transcribió (la caché de la voz); [] si no."""
    try:
        import cache_voz
        nombre = Path(ruta).name
        archivos = sorted(cache_voz.CARPETA.glob('*.json'), key=lambda f: f.stat().st_mtime, reverse=True)[:120]
        for f in archivos:
            try:
                d = json.loads(f.read_text(encoding='utf-8'))
            except Exception:
                continue
            if d.get('video') == nombre and isinstance(d.get('palabras'), list):
                return [(float(p['start']), str(p.get('word') or '').strip()) for p in d['palabras'] if p.get('start') is not None]
    except Exception:
        pass
    return []


def texto_t(t):
    """0:12.4 · 1:05.0"""
    t = max(0.0, float(t))
    return f'{int(t // 60)}:{t % 60:04.1f}'


# ======================================================================================================================== dónde queda bien (v5.27)
def analizar_detras(ruta, al_progreso=None):
    """Dónde hay una PERSONA que deje poner los captions detrás (la misma IA local y las mismas reglas que GO: edicion_pro.motivo_cabeza): una
    pasada por el video (la de los cortes de toma de GO, efectos_visuales.detectar_cortes) mirando un fotograma cada PASO_ZONAS s.
    {'dur', 'paso', 'muestras': [[t, motivo | None, coronilla, x de la cabeza]], 'cortes': [t]} en el tiempo de `ruta` (con el audio de un
    timeline, el de ese audio), en caché; None si no hay imagen. En un HILO (tarda lo que dura leer el video)."""
    img, desde, dur_audio = fuente_imagen(ruta)
    if not img:
        return None
    carpeta = _carpeta_de(img, f'{ruta}|{desde}|{dur_audio}')
    archivo = carpeta / f'detras_v{VERSION_ZONAS}.json'
    try:
        d = json.loads(archivo.read_text(encoding='utf-8'))
        if isinstance(d.get('muestras'), list):
            return d
    except Exception:
        pass
    import edicion_pro as EP
    import edicion_pro_persona as PE
    import efectos_visuales as EV
    import rotacion_video as RV
    dur_v = _duracion(img)
    dur = float(dur_audio) if dur_audio else dur_v
    if dur <= 0:
        return None
    objetivos = [round(PASO_ZONAS * (i + 0.5), 3) for i in range(int(dur / PASO_ZONAS))]
    muestras, i_sig = [], [0]

    def mirar(fr, t):
        i = i_sig[0]
        if i >= len(objetivos) or t + 0.02 < objetivos[i] + desde:
            return
        while i_sig[0] < len(objetivos) and objetivos[i_sig[0]] + desde <= t + 0.02:
            i_sig[0] += 1
        try:
            det = PE.personas_de_imagen(RV.derecho_nd(fr.to_ndarray(format='rgb24'), RV.cuartos(fr)))
            h = EP._cabeza(det)
        except Exception:
            h = None
        if h is None:
            motivo = 'sin_persona'
        else:
            motivo = EP.motivo_cabeza(h[0], h[2])
            if motivo is None and h[0] < ZONA_CORONILLA_MIN:
                motivo = 'cabeza_arriba'
            elif motivo is None and not ZONA_X[0] <= h[1] <= ZONA_X[1]:
                motivo = 'lado'
        for j in range(i, i_sig[0]):
            muestras.append([objetivos[j], motivo, round(h[0], 4) if h else None, round(h[1], 4) if h else None])
        if al_progreso:
            try:
                al_progreso(min(1.0, i_sig[0] / max(1, len(objetivos))))
            except Exception:
                pass
    tope = desde + dur + 0.1 if (desde or dur_audio) else None
    cortes = [round(t - desde, 3) for t, _f in EV.detectar_cortes(img, tope_s=tope, por_fotograma=mirar) if 0.0 < t - desde < dur]
    d = {'dur': round(dur, 3), 'paso': PASO_ZONAS, 'muestras': muestras, 'cortes': cortes}
    try:
        carpeta.mkdir(parents=True, exist_ok=True)
        import archivos_seguros
        archivos_seguros.escribir_json(archivo, d)
    except Exception:
        pass
    return d


def zonas_detras(analisis, palabras=()):
    """De analizar_detras: ([(ini, fin)] donde «detrás de ti» queda bien, motivo(t) → clave de edicion_pro.MOTIVOS_DETRAS o None).
    Una zona = miradas seguidas con la persona bien, en la MISMA toma (sin corte entre medias), con la cabeza quieta (MOVIMIENTO_ZONA) y, si el
    video ya está transcrito, hablando (sin voz no hay captions)."""
    import bisect
    if not analisis:
        return [], (lambda t: None)
    paso = float(analisis.get('paso') or PASO_ZONAS)
    dur = float(analisis.get('dur') or 0.0)
    cortes = sorted(float(c) for c in analisis.get('cortes') or [])
    voz = sorted(float(s) for s, _w in palabras or [])

    def hablando(t):
        if not voz:
            return True
        i = bisect.bisect_left(voz, t - 0.9)
        return i < len(voz) and voz[i] <= t + 0.9

    def corte_entre(a, b):
        i = bisect.bisect_right(cortes, a)
        return i < len(cortes) and cortes[i] <= b
    ms = []
    for t, motivo, cor, x in analisis.get('muestras') or []:
        if motivo is None and not hablando(t):
            motivo = 'sin_captions'
        ms.append((float(t), motivo, cor, x))
    zonas, actual, previo = [], None, None
    for t, motivo, cor, x in ms:
        sigue = (motivo is None and previo is not None and previo[1] is None and not corte_entre(previo[0], t)
                 and abs(cor - previo[2]) <= MOVIMIENTO_ZONA[0] and abs(x - previo[3]) <= MOVIMIENTO_ZONA[1])
        if motivo is None and sigue and actual is not None:
            actual[1] = t
        elif motivo is None:
            if actual is not None:
                zonas.append(actual)
            actual = [t, t]
        else:
            if actual is not None:
                zonas.append(actual)
            actual = None
        previo = (t, motivo, cor, x)
    if actual is not None:
        zonas.append(actual)
    out = []
    for a, b in zonas:
        ini, fin = max(0.0, a - paso / 2), min(dur, b + paso / 2)
        i = bisect.bisect_right(cortes, a) - 1                        # (no pasa del corte de toma de cada lado)
        if i >= 0:
            ini = max(ini, cortes[i])
        j = bisect.bisect_left(cortes, b)
        if j < len(cortes):
            fin = min(fin, cortes[j])
        if fin - ini >= ZONA_MIN_S:
            out.append((round(ini, 2), round(fin, 2)))
    tiempos = [m[0] for m in ms]

    def motivo(t):
        if any(a <= t <= b for a, b in out):
            return None
        if not ms:
            return 'sin_persona'
        k = min(max(0, bisect.bisect_left(tiempos, t)), len(ms) - 1)
        if k > 0 and abs(tiempos[k - 1] - t) < abs(tiempos[k] - t):
            k -= 1
        return ms[k][1] or ('corte' if any(abs(c - t) < paso for c in cortes) else 'se_mueve')
    return out, motivo


def ajustar_a_zonas(t, zonas, margen=0.15):
    """El segundo más cercano a t dentro de una zona (a `margen` de sus bordes si cabe): el «tope» de las marcas. t si no hay zonas."""
    if not zonas:
        return t
    mejor, dist = t, None
    for a, b in zonas:
        m = min(margen, (b - a) / 2)
        c = min(max(t, a + m), b - m)
        if dist is None or abs(c - t) < dist:
            mejor, dist = c, abs(c - t)
    r = round(round(mejor / PASO) * PASO, 2)
    return r if any(a <= r <= b for a, b in zonas) else round(mejor, 2)


# ======================================================================================================================== la vista
try:
    from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
    from PySide6.QtGui import QFontMetricsF, QPainter, QPainterPath, QPen, QPixmap
    from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget
    import qt_kit as ui
    from qt_kit import Boton, Etiqueta, QColor, QColorReal, Segmentado, StringVar, correr_en_hilo, fuente
    _QT = True
except Exception:                                   # (GO y las pruebas sin interfaz importan solo los datos)
    _QT = False


if _QT:
    class LineaTiempo(QWidget):
        """Los fotogramas del video en una tira, la regla de tiempo y las marcas. Arriba, el fotograma bajo el ratón en grande y lo que se
        dice en ese momento. Clic = marca nueva (y se puede arrastrar) · arrastrar una marca = moverla · doble clic o clic derecho = quitarla ·
        ← → la mueven una décima (con Mayús, un segundo) · Supr la quita. Todo se guarda al momento.
        v5.27 («detrás de ti», CON_PERSONA): en verde dónde queda bien (zonas_detras) y las marcas no salen de ahí; arriba, por qué no en cada
        instante; como mucho TOPE_MARCAS y nunca dos en el mismo caption (SEPARACION_MIN)."""
        cambio = Signal()
        cargado = Signal(str)                        # el archivo del que salen los fotogramas (con el audio de un timeline, su clip de V1)
        ALTO_TIRA, MARGEN, ALTO_REGLA = 64, 18, 22
        VERDE, AMBAR = '#34D399', '#F5B544'

        def __init__(self, seccion, padre=None):
            super().__init__(padre)
            self.seccion = seccion
            self.ruta = None
            self.modo = 'solo'
            self.dur = 0.0
            self.fotos = []                          # [(t, QPixmap)]
            self.palabras = []
            self.marcas = []
            self.aviso = ''
            self.zonas = None                        # v5.27: dónde queda bien [(ini, fin)]; None = aún no se sabe (o no aplica)
            self._motivo = None                      # motivo(t) de zonas_detras
            self._imagen = None                      # fuente_imagen(ruta): para guardar las marcas con el video
            self._progreso = [0.0]
            self._reloj = None
            self.nota = ''                           # lo último que pasó con una marca (movida al verde, el tope…)
            self._t_sobre = None
            self._arr = None
            self._sel = None
            self._movido = False
            self.setMouseTracking(True)
            self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            self.setMinimumHeight(340)

        # -- datos
        def cargar(self, ruta):
            self.ruta = ruta
            self.marcas, self.modo = [], 'solo'
            self.fotos, self.palabras, self.dur = [], [], 0.0
            self.zonas, self._motivo, self._imagen, self.nota = None, None, None, ''
            self._sel = None
            self.aviso = tr('Leyendo los fotogramas del video…')
            self.update()

            def trabajo():
                img = fuente_imagen(ruta)
                return fotogramas(ruta), palabras(ruta), img, leer_linea(ruta, img).get(self.seccion) or {}

            def fin(r, error):
                if ruta != self.ruta:
                    return
                if error is None and r:
                    self._imagen = r[2]
                    self.marcas = list(r[3].get('ts') or [])
                    self.modo = r[3].get('modo') or 'solo'
                    self.cambio.emit()
                if error is not None or not r or not r[0]:
                    self.aviso = (tr('Este audio no trae imagen: pulsa «Obtener» con tu timeline abierto en Resolve (trae su video) o «Elegir video…».')
                                  if Path(str(ruta)).suffix.lower() in AUDIO else tr('No pude leer la imagen de este video.'))
                    self.update()
                    return
                d, pals = r[0], r[1]
                self.dur = float(d['dur'])
                self.fotos = [(t, QPixmap(f)) for t, f in d['fotos']]
                self.palabras = pals
                self.aviso = ''
                self.marcas = [t for t in self.marcas if t <= self.dur + 0.05]
                self.update()
                self.cargado.emit(str(d.get('imagen') or ruta))
                if self.seccion in CON_PERSONA:
                    self._analizar(ruta)
            correr_en_hilo(self, trabajo, fin)

        def _analizar(self, ruta):
            """v5.27: dónde hay una persona que deje el texto detrás (en un hilo; mientras, la tira dice cuánto lleva)."""
            self.zonas, self._motivo, self._progreso[0] = None, None, 0.0
            prog = self._progreso

            def trabajo():
                return analizar_detras(ruta, al_progreso=lambda f: prog.__setitem__(0, f))

            def fin(an, error):
                if ruta != self.ruta:                # (el de un video anterior: el reloj ya es del nuevo)
                    return
                if self._reloj is not None:
                    self._reloj.stop()
                if error is not None or not an:
                    self.nota = tr('No pude ver dónde está la persona: tus marcas van donde las pongas.')
                else:
                    self.zonas, self._motivo = zonas_detras(an, self.palabras)
                    self._aplicar_topes()
                self.update()
                self.cambio.emit()
            if self._reloj is None:
                self._reloj = QTimer(self)
                self._reloj.timeout.connect(self.update)
            self._reloj.start(300)
            correr_en_hilo(self, trabajo, fin)

        def analizando(self):
            return self.seccion in CON_PERSONA and self.dur > 0 and self.zonas is None and self._reloj is not None and self._reloj.isActive()

        def texto_motivo(self, t):
            """Por qué en el segundo t no queda bien (texto para el usuario) o '' si queda bien / aún no se sabe."""
            if self._motivo is None:
                return ''
            m = self._motivo(t)
            if not m:
                return ''
            try:
                import edicion_pro as EP
                return tr(EP.MOTIVOS_DETRAS.get(m, m))
            except Exception:
                return ''

        def _aplicar_topes(self):
            """Las marcas que ya había (de antes o puestas mientras se miraba el video) van al verde más cercano; las que sobran o caen en el
            mismo caption se juntan."""
            if not self.zonas:
                if self.zonas == [] and self.marcas:
                    self.nota = tr('Aquí el texto no queda bien detrás de la persona en ningún momento ({m}): GO lo intentará, pero puede no ponerlo.',
                                   m=self.texto_motivo(self.marcas[0]) or tr('no se ve a ninguna persona'))
                return
            nuevas = []
            for t in sorted(self.marcas):
                t2 = ajustar_a_zonas(t, self.zonas)
                if all(abs(t2 - x) >= SEPARACION_MIN for x in nuevas):
                    nuevas.append(t2)
            tope = TOPE_MARCAS.get(self.seccion)
            if tope:
                nuevas = nuevas[:tope]
            if nuevas != sorted(self.marcas):
                movidas = sum(1 for t in self.marcas if t not in nuevas)
                self.marcas, self._sel = nuevas, None
                self.nota = (tr('Moví 1 marca a donde el texto queda bien detrás de ti.') if movidas == 1 else
                             tr('Moví {n} marcas a donde el texto queda bien detrás de ti.', n=movidas))
                self._guardar()

        def _ajustar(self, t):
            return ajustar_a_zonas(t, self.zonas) if self.seccion in CON_PERSONA and self.zonas else t

        def _puede_anadir(self, t):
            """(sí/no, segundo donde va): los topes de una marca nueva."""
            self.nota = ''
            tope = TOPE_MARCAS.get(self.seccion)
            if tope and len(self.marcas) >= tope:
                self.nota = tr('Máximo {n} marcas: cada una es un recorte con Magic Mask que Resolve tiene que seguir y más lo cargan.', n=tope)
                return False, t
            if self.seccion in CON_PERSONA and self.zonas == []:
                self.nota = tr('En este video el texto no queda bien detrás de la persona en ningún momento: {m}.',
                               m=self.texto_motivo(t) or tr('no se ve a ninguna persona'))
                return False, t
            t2 = self._ajustar(t)
            cerca = next((j for j, x in enumerate(self.marcas) if abs(x - t2) < SEPARACION_MIN), None)
            if cerca is not None:
                self.nota = tr('Ya hay una marca en {t}: dos en el mismo caption sobran.', t=texto_t(self.marcas[cerca]))
                self._sel = cerca
                return False, t2
            if abs(t2 - t) >= 0.05:
                self.nota = tr('Puesta en {t}, lo más cerca donde queda bien (en {o}: {m}).', t=texto_t(t2), o=texto_t(t), m=self.texto_motivo(t))
            return True, t2

        def _guardar(self):
            if self.ruta:                            # (sin leer el disco aquí: hasta que el hilo sabe su video, un audio guarda con su ruta)
                guardar_linea(self.ruta, self.seccion, self.marcas, self.modo, imagen=self._imagen or (str(self.ruta), 0.0, None))
            self.cambio.emit()

        def poner_modo(self, modo):
            self.modo = modo if modo in MODOS else 'solo'
            self._guardar()

        def quitar_todas(self):
            self.marcas, self._sel = [], None
            self._guardar()
            self.update()

        # -- geometría
        def _tira(self):
            y = self.height() - self.ALTO_REGLA - self.ALTO_TIRA
            return QRectF(self.MARGEN, y, self.width() - 2 * self.MARGEN, self.ALTO_TIRA)

        def _x(self, t):
            r = self._tira()
            return r.left() + (t / self.dur) * r.width() if self.dur > 0 else r.left()

        def _t(self, x):
            r = self._tira()
            if self.dur <= 0 or r.width() <= 0:
                return 0.0
            t = (x - r.left()) / r.width() * self.dur
            return round(max(0.0, min(self.dur, t)) / PASO) * PASO

        def _marca_en(self, pos):
            r = self._tira()
            if not (r.top() - 44 <= pos.y() <= r.bottom() + 4):
                return None
            mejor, dist = None, 9.0
            for i, t in enumerate(self.marcas):
                d = abs(self._x(t) - pos.x())
                if d <= dist:
                    mejor, dist = i, d
            return mejor

        def _en_tira(self, pos):
            r = self._tira()
            return r.left() - 6 <= pos.x() <= r.right() + 6 and r.top() - 44 <= pos.y() <= r.bottom() + self.ALTO_REGLA

        # -- ratón y teclado
        def mousePressEvent(self, e):
            if self.dur <= 0:
                return
            pos = e.position()
            i = self._marca_en(pos)
            if e.button() == Qt.MouseButton.RightButton:
                if i is not None:
                    self._quitar(i)
                return
            if e.button() != Qt.MouseButton.LeftButton or not self._en_tira(pos):
                return
            self.setFocus()
            if i is None:                            # marca nueva donde se pulsó (y se puede arrastrar en el mismo gesto)
                ok, t = self._puede_anadir(self._t(pos.x()))
                if not ok:
                    self.update()
                    return
                self.marcas.append(t)
                i = len(self.marcas) - 1
                self._movido = True
            else:
                self.nota = ''
                self._movido = False
            self._arr = self._sel = i
            self.update()

        def mouseMoveEvent(self, e):
            pos = e.position()
            if self.dur > 0 and self._en_tira(pos):
                self._t_sobre = self._t(pos.x())
            else:
                self._t_sobre = None
            if self._arr is not None:
                t = self._ajustar(self._t(pos.x()))  # (v5.27: el «tope»: la marca no sale del verde)
                if t != self.marcas[self._arr]:
                    self.marcas[self._arr] = t
                    self._movido = True
            hay = self._marca_en(pos) is not None or self._en_tira(pos)
            self.setCursor(Qt.CursorShape.SizeHorCursor if self._marca_en(pos) is not None else
                           Qt.CursorShape.PointingHandCursor if hay else Qt.CursorShape.ArrowCursor)
            self.update()

        def mouseReleaseEvent(self, e):
            if self._arr is not None:
                t = self.marcas[self._arr]
                otra = next((x for j, x in enumerate(self.marcas) if j != self._arr and abs(x - t) < SEPARACION_MIN), None)
                if otra is not None:                 # (v5.27: soltada sobre otra, en el mismo caption: se juntan)
                    self.marcas.pop(self._arr)
                    self.nota = tr('Ya hay una marca en {t}: dos en el mismo caption sobran.', t=texto_t(otra))
                    self._movido, t = True, otra
                self.marcas.sort()
                self._sel = self.marcas.index(t)
                self._arr = None
                if self._movido:
                    self._guardar()
                self.update()

        def mouseDoubleClickEvent(self, e):
            i = self._marca_en(e.position())
            if i is not None:
                self._quitar(i)

        def leaveEvent(self, e):
            self._t_sobre = None
            self.update()

        def keyPressEvent(self, e):
            if self._sel is None or self._sel >= len(self.marcas):
                return super().keyPressEvent(e)
            k = e.key()
            if k in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
                self._quitar(self._sel)
            elif k in (Qt.Key.Key_Left, Qt.Key.Key_Right):
                paso = 1.0 if e.modifiers() & Qt.KeyboardModifier.ShiftModifier else PASO
                t = self.marcas[self._sel] + (paso if k == Qt.Key.Key_Right else -paso)
                self.marcas[self._sel] = self._ajustar(round(max(0.0, min(self.dur, t)) / PASO) * PASO)
                self._t_sobre = self.marcas[self._sel]
                t = self.marcas[self._sel]
                self.marcas.sort()
                self._sel = self.marcas.index(t)
                self._guardar()
                self.update()
            else:
                super().keyPressEvent(e)

        def _quitar(self, i):
            if 0 <= i < len(self.marcas):
                self.marcas.pop(i)
                self._sel = None
                self._arr = None
                self._guardar()
                self.update()

        # -- dibujo
        def _foto_en(self, t):
            if not self.fotos:
                return None
            return min(self.fotos, key=lambda f: abs(f[0] - t))[1]

        def _dicho_en(self, t):
            """Las palabras de ±2,5 s alrededor de t y cuál suena en t."""
            cerca = [(s, w) for s, w in self.palabras if t - 2.5 <= s <= t + 2.5]
            actual = max((s for s, _w in cerca if s <= t + 0.05), default=None)
            return cerca, actual

        def paintEvent(self, _e):
            p = QPainter(self)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            tira = self._tira()
            acento = QColor(ui.ACCENT)
            if self.aviso or self.dur <= 0:
                p.setPen(QColor('#8EA2C6'))
                p.setFont(fuente(14, peso='medio'))
                p.drawText(QRectF(self.rect()), int(Qt.AlignmentFlag.AlignCenter), self.aviso or tr('Sin video.'))
                p.end()
                return
            # ---- arriba: el fotograma en grande y lo que se dice
            t_ver = self._t_sobre if self._t_sobre is not None else (self.marcas[self._sel] if self._sel is not None and self._sel < len(self.marcas) else
                                                                    (self.marcas[0] if self.marcas else 0.0))
            alto_prev = max(60.0, tira.top() - 58)
            pm = self._foto_en(t_ver)
            x_txt = self.MARGEN
            if pm is not None and not pm.isNull():
                ancho_prev = alto_prev * pm.width() / max(1, pm.height())
                caja = QRectF(self.MARGEN, 6, ancho_prev, alto_prev)
                camino = QPainterPath()
                camino.addRoundedRect(caja, 12, 12)
                p.save()
                p.setClipPath(camino)
                p.drawPixmap(caja.toRect(), pm)
                p.restore()
                p.setPen(QPen(QColorReal(255, 255, 255, 40), 1))
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawPath(camino)
                x_txt = caja.right() + 22
            ancho_txt = self.width() - x_txt - self.MARGEN
            p.setPen(QColor('#FFFFFF'))
            p.setFont(fuente(26, peso='negrita'))
            p.drawText(QRectF(x_txt, 6, ancho_txt, 40), int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), texto_t(t_ver))
            if self.seccion in CON_PERSONA:          # v5.27: ¿aquí queda bien el texto detrás de la persona?
                x_est = x_txt + QFontMetricsF(p.font()).horizontalAdvance(texto_t(t_ver)) + 18
                p.setFont(fuente(13, peso='medio'))
                if self.analizando():
                    p.setPen(QColor('#8EA2C6'))
                    est = tr('Buscando en tu video dónde queda bien… {p} %', p=int(round(100 * self._progreso[0])))
                elif self.zonas is not None:
                    motivo = self.texto_motivo(t_ver)
                    p.setPen(QColor(self.AMBAR if motivo else self.VERDE))
                    est = (tr('Aquí no queda bien: {m}', m=motivo) if motivo else tr('Aquí queda bien detrás de ti'))
                else:
                    est = ''
                if est:
                    p.drawText(QRectF(x_est, 6, max(10.0, x_txt + ancho_txt - x_est), 40),
                               int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), QFontMetricsF(p.font()).elidedText(
                                   est, Qt.TextElideMode.ElideRight, max(10.0, x_txt + ancho_txt - x_est)))
            y = 52
            cerca, actual = self._dicho_en(t_ver)
            if cerca:
                p.setFont(fuente(15, peso='medio'))
                fm = QFontMetricsF(p.font())
                x, linea = x_txt, 0
                for s, w in cerca:
                    ancho = fm.horizontalAdvance(w + ' ')
                    if x + ancho > x_txt + ancho_txt:
                        linea += 1
                        x = x_txt
                        if linea >= 3:
                            break
                    p.setPen(acento if s == actual else (QColor('#E6EEFB') if s <= t_ver else QColor('#7D8DAA')))
                    p.drawText(QPointF(x, y + 20 + linea * 24), w)
                    x += ancho
                y += 20 + 3 * 24
            else:
                p.setPen(QColor('#7D8DAA'))
                p.setFont(fuente(13))
                p.drawText(QRectF(x_txt, y, ancho_txt, 40), int(Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap),
                           tr('Aquí no se habla: no hay captions.') if self.palabras else       # (v5.27: ya transcrito, pero nadie habla ahí)
                           tr('Lo que dices saldrá aquí cuando GO haya transcrito este video.'))
                y += 52
            p.setFont(fuente(12))
            ayuda = tr('Clic en la tira: añadir · arrastrar: mover · doble clic o clic derecho: quitar · ← → afinan (Mayús: 1 s)')
            if self.seccion in CON_PERSONA:
                ayuda += ' · ' + tr('verde: aquí queda bien')
            p.setPen(QColor(self.AMBAR) if self.nota else QColor('#8EA2C6'))
            p.drawText(QRectF(x_txt, max(y, alto_prev - 30), ancho_txt, 40), int(Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap), self.nota or ayuda)
            # ---- la tira de fotogramas
            camino = QPainterPath()
            camino.addRoundedRect(tira, 10, 10)
            p.save()
            p.setClipPath(camino)
            p.fillRect(tira, QColor('#0A1120'))
            if self.fotos:
                f0 = self.fotos[0][1]
                ancho_f = tira.height() * f0.width() / max(1, f0.height())
                n = max(1, int(tira.width() // max(8.0, ancho_f)) + 1)
                for j in range(n):
                    x = tira.left() + j * ancho_f
                    t = (x + ancho_f / 2 - tira.left()) / tira.width() * self.dur
                    pmj = self._foto_en(t)
                    if pmj is not None:
                        p.drawPixmap(QRectF(x, tira.top(), ancho_f, tira.height()).toRect(), pmj)
            p.fillRect(tira, QColorReal(5, 10, 20, 70))
            if self.seccion in CON_PERSONA and self.zonas is not None:     # v5.27: lo que no vale, apagado; lo que sí, con su raya verde
                x_prev = tira.left()
                for a, b in self.zonas + [(self.dur, self.dur)]:
                    xa, xb = self._x(a), self._x(b)
                    if xa > x_prev:
                        p.fillRect(QRectF(x_prev, tira.top(), xa - x_prev, tira.height()), QColorReal(4, 8, 16, 150))
                    if xb > xa:
                        p.fillRect(QRectF(xa, tira.bottom() - 5, xb - xa, 5), QColor(self.VERDE))
                    x_prev = max(x_prev, xb)
            elif self.analizando():
                p.fillRect(QRectF(tira.left(), tira.bottom() - 3, tira.width() * self._progreso[0], 3), QColor('#8EA2C6'))
            p.restore()
            p.setPen(QPen(QColorReal(255, 255, 255, 34), 1))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPath(camino)
            # ---- la regla
            p.setFont(fuente(11))
            paso = next((s for s in (1, 2, 5, 10, 15, 30, 60, 120, 300) if tira.width() / max(1.0, self.dur / s) >= 70), 600)
            t = 0.0
            while t <= self.dur + 1e-6:
                x = self._x(t)
                p.setPen(QPen(QColorReal(255, 255, 255, 60), 1))
                p.drawLine(QPointF(x, tira.bottom() + 2), QPointF(x, tira.bottom() + 7))
                p.setPen(QColor('#7D8DAA'))
                p.drawText(QRectF(x - 30, tira.bottom() + 6, 60, 16), int(Qt.AlignmentFlag.AlignCenter), f'{int(t // 60)}:{int(t % 60):02d}')
                t += paso
            # ---- el ratón
            if self._t_sobre is not None and self._arr is None:
                x = self._x(self._t_sobre)
                p.setPen(QPen(QColorReal(255, 255, 255, 150), 1.4))
                p.drawLine(QPointF(x, tira.top() - 4), QPointF(x, tira.bottom() + 2))
            # ---- las marcas
            p.setFont(fuente(11, peso='negrita'))
            fm = QFontMetricsF(p.font())
            for i, t in enumerate(self.marcas):
                x = self._x(t)
                sel = i == self._sel
                acento = (QColor(self.AMBAR) if self.seccion in CON_PERSONA and self.zonas is not None and not any(a <= t <= b for a, b in self.zonas)
                          else QColor(ui.ACCENT))        # (v5.27: una marca donde no queda bien, en ámbar)
                p.setPen(QPen(acento, 2.4 if sel else 1.8))
                p.drawLine(QPointF(x, tira.top() - 12), QPointF(x, tira.bottom()))
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(acento)
                p.drawEllipse(QPointF(x, tira.top() - 14), 6.5 if sel else 5.5, 6.5 if sel else 5.5)
                txt = texto_t(t)
                w = fm.horizontalAdvance(txt) + 14
                caja = QRectF(min(max(tira.left(), x - w / 2), tira.right() - w), tira.top() - 42, w, 20)
                p.setBrush(acento if sel else QColorReal(10, 18, 34, 230))
                p.setPen(QPen(acento, 1.2))
                p.drawRoundedRect(caja, 10, 10)
                p.setPen(QColorReal('#0B1220') if sel else QColor('#FFFFFF'))
                p.drawText(caja, int(Qt.AlignmentFlag.AlignCenter), txt)
            p.end()

    class VistaPosiciones(QWidget):
        """La vista «Posición» de una sección de Efectos: el video, el modo (solo mis marcas / + automático), la línea de tiempo y «Listo»."""
        cambio = Signal()
        listo = Signal()
        MODOS_UI = (('solo', 'Solo mis marcas'), ('suma', 'Mis marcas + automático'))

        def __init__(self, seccion, padre=None):
            super().__init__(padre)
            self.seccion = seccion
            capa = QVBoxLayout(self)
            capa.setContentsMargins(0, 2, 0, 4)
            capa.setSpacing(10)
            fila = QHBoxLayout()
            fila.setSpacing(10)
            self._lbl_video = ui.Elidida('', 13, color='#C9D6EC') if hasattr(ui, 'Elidida') else Etiqueta('', 13, color='#C9D6EC')
            fila.addWidget(self._lbl_video, 1)
            nombres = [tr(n) for _k, n in self.MODOS_UI]
            self._v_modo = StringVar(nombres[0])
            self._seg = Segmentado(nombres, self._v_modo, self._cambio_modo, alto=32, tam=12)
            fila.addWidget(self._seg)
            fila.addWidget(Boton(tr('Elegir video…'), self._elegir_video, tipo='neutro', alto=32, tam=12))
            fila.addWidget(Boton(tr('Quitar todas'), self._quitar_todas, tipo='fantasma', alto=32, tam=12))
            fila.addWidget(Boton(tr('Listo'), self._listo, tipo='primario', alto=32, tam=12))
            capa.addLayout(fila)
            self._lbl_modo = Etiqueta('', 12, color='#8EA2C6', envolver=True)
            capa.addWidget(self._lbl_modo)
            self.linea = LineaTiempo(seccion)
            self.linea.cambio.connect(self._al_cambiar)
            self.linea.cargado.connect(self._al_cargar)
            capa.addWidget(self.linea)

        def _al_cargar(self, imagen):
            ruta = self.linea.ruta or ''
            if imagen and clave_video(imagen) != clave_video(ruta):     # el audio de «Obtener»: la imagen es el clip de su timeline
                self._lbl_video.setText(tr('Video del timeline: ') + Path(imagen).name)

        def abrir(self, ruta=None):
            ruta = ruta or video_actual()
            if not ruta:
                self.linea.ruta = None
                self.linea.dur = 0.0
                self.linea.aviso = tr('Suelta un video en Inicio (o pulsa «Elegir video…») para marcar dónde va este efecto.')
                self._lbl_video.setText('')
                self.linea.update()
                self._pintar_modo()
                return
            self._lbl_video.setText(tr('Video: ') + Path(ruta).name)
            self.linea.cargar(ruta)
            self._v_modo.set(tr(dict(self.MODOS_UI)[self.linea.modo]))
            try:
                self._seg.refrescar() if hasattr(self._seg, 'refrescar') else self._seg.update()
            except Exception:
                pass
            self._pintar_modo()
            self.linea.setFocus()

        def _pintar_modo(self):
            ligada = self.seccion in LIGADAS
            if self.linea.modo == 'solo':
                txt = tr('GO pone este efecto SOLO en tus marcas (sin marcas, donde lo elija el automático).')
            else:
                txt = tr('GO lo pone en tus marcas y, además, donde lo elija el automático.')
            if self.seccion == 'motions_completo':
                txt = (tr('Solo mis marcas: el video de motions sale solo en los tramos que marques.') if self.linea.modo == 'solo'
                       else tr('Con «+ automático», el video de motions va en todo el video, como siempre.'))
            elif ligada:
                txt += ' ' + tr('Se usa el bloque de captions que suena en ese segundo.')
            if self.seccion in CON_PERSONA:          # v5.27: los topes, dichos
                txt += ' ' + tr('Verde = hay una persona quieta y su cabeza deja sitio al texto: tus marcas van ahí (máximo {n}).',
                                n=TOPE_MARCAS.get(self.seccion, 8))
            n = len(self.linea.marcas)
            if n:
                txt += ' · ' + (tr('1 marca') if n == 1 else tr('{n} marcas', n=n))
            self._lbl_modo.setText(txt)

        def a_mano(self):
            """¿El video de la vista lo eligió el usuario con «Elegir video…» (y no es el de Inicio)?"""
            return bool(getattr(self, '_a_mano', False)) and bool(self.linea.ruta) and not es_de_inicio(self.linea.ruta)

        def _listo(self):
            """v5.27 (el usuario: «cuando le doy Listo que quede guardado y al volver a Inicio lo aplique»): guarda (ya se guardaba con cada
            cambio) y avisa; la sección (efectos_pro_ui) enciende el efecto en GO y pone este video en Inicio si se eligió a mano."""
            if self.linea.ruta and self.linea.dur > 0:
                self.linea._guardar()
            self.listo.emit()

        def _cambio_modo(self, *_a):
            inv = {tr(n): k for k, n in self.MODOS_UI}
            self.linea.poner_modo(inv.get(str(self._v_modo.get()), 'solo'))
            self._pintar_modo()

        def _quitar_todas(self):
            self.linea.quitar_todas()
            self._pintar_modo()

        def _al_cambiar(self):
            nombre = tr(dict(self.MODOS_UI)[self.linea.modo])   # (v5.27: las marcas y el modo llegan del hilo, ya con el video de un audio)
            if str(self._v_modo.get()) != nombre:
                self._v_modo.set(nombre)
            self._pintar_modo()
            self.cambio.emit()

        def _elegir_video(self):
            from qt_kit import filedialog
            ruta = filedialog.askopenfilename(parent=self.window(), title=tr('Elige el video'),
                                              filetypes=[(tr('Videos'), '*.mp4 *.mov *.m4v *.mkv *.avi *.mxf'), (tr('Todos'), '*.*')])
            if ruta:
                self._a_mano = True
                self.abrir(ruta)

        def al_volver(self):
            """Al volver a Efectos: si el video de Inicio cambió (soltaste otro o pulsaste «Obtener»), se carga ese (salvo uno elegido a mano)."""
            actual = video_actual()
            if actual and not getattr(self, '_a_mano', False) and clave_video(actual) != clave_video(self.linea.ruta or ''):
                self.abrir(actual)
