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
VERSION_ZONAS = 2                        # (2: los cortes con su fuerza)


# ======================================================================================================================== datos
def clave_video(ruta):
    """La clave de un video en posiciones_pro.json. v5.29: la copia con el audio compatible (audio_compatible, la que GO lleva a Resolve
    cuando el video trae HE-AAC) cuenta como su ORIGINAL: si no, GO con el audio del timeline no veía las marcas hechas sobre el video."""
    try:
        import audio_compatible
        ruta = audio_compatible.original_de(ruta)
    except Exception:
        pass
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


def _clave_en(todo, ruta):
    """La clave de `ruta` en posiciones_pro.json: la suya o, si no tiene entrada (una copia de audio compatible de antes de la 5.29, sin su
    origen.json, o el original de una), la de otro archivo con el MISMO nombre que tenga marcas."""
    clave = clave_video(ruta)
    if clave in todo:
        return clave
    nombre = Path(str(ruta)).name.lower()
    return next((k for k, v in todo.items() if isinstance(v, dict) and Path(str(v.get('video') or k)).name.lower() == nombre
                 and any((m or {}).get('ts') for m in (v.get('secciones') or {}).values())), clave)


def leer(ruta):
    """{sección: {'modo': 'solo'|'suma', 'ts': [s ordenados]}} de ese video ({} si no tiene marcas)."""
    if not ruta:
        return {}
    todo = _todo()
    e = todo.get(_clave_en(todo, ruta)) or {}
    out = {}
    for sec, m in (e.get('secciones') or {}).items():
        if not isinstance(m, dict):
            continue
        ts = sorted(round(float(t), 2) for t in m.get('ts') or [] if isinstance(t, (int, float)) and t >= 0)
        out[sec] = {'modo': m.get('modo') if m.get('modo') in MODOS else 'solo', 'ts': ts, 'cuando': float(m.get('cuando') or 0.0)}
    return out


def guardar(ruta, seccion, ts, modo='solo'):
    """Guarda las marcas de una sección de ese video (las demás secciones y videos no se tocan). True si se guardó."""
    if not ruta or seccion not in SECCIONES:
        return False
    todo = _todo()
    clave = _clave_en(todo, ruta)
    e = dict(todo.get(clave) or {})
    secciones = dict(e.get('secciones') or {})
    limpias = sorted({round(max(0.0, float(t)), 2) for t in ts or []})
    # v5.30: con su hora (la tira enseña lo del timeline si es más nuevo que lo guardado) y, aunque quede VACÍA, se guarda: «Quitar todas» +
    # «Listo» quita «detrás de ti» del timeline (para GO, una sección vacía sigue siendo «donde lo elija el automático»)
    import time as _t
    secciones[seccion] = {'modo': modo if modo in MODOS else 'solo', 'ts': limpias, 'cuando': round(_t.time(), 1)}
    e.update(video=e.get('video') or str(ruta), secciones=secciones)     # (v5.29: la entrada del original no pasa a nombre de su copia)
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
        out[sec] = {'modo': m['modo'], 'ts': sorted(set(ts)), 'cuando': m.get('cuando', 0.0)}
    for sec, m in leer(ruta).items():                    # (las de antes de la 5.27, guardadas con la ruta del audio)
        if m['ts']:
            o = out.setdefault(sec, {'modo': m['modo'], 'ts': [], 'cuando': m.get('cuando', 0.0)})
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


def _voz_de(ruta):
    """Las palabras [{'word', 'start', 'end'}] de ese video si GO ya lo transcribió (la caché de la voz, la más nueva); [] si no."""
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
                return [p for p in d['palabras'] if isinstance(p, dict) and p.get('start') is not None]
    except Exception:
        pass
    return []


def palabras(ruta):
    """[(segundo, palabra)] de lo que se dice en ese video, si GO ya lo transcribió (la caché de la voz); [] si no."""
    return [(float(p['start']), str(p.get('word') or '').strip()) for p in _voz_de(ruta)]


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
    cortes = [[round(t - desde, 3), f] for t, f in EV.detectar_cortes(img, tope_s=tope, por_fotograma=mirar) if 0.0 < t - desde < dur]   # (con su fuerza: GO la usa)
    d = {'dur': round(dur, 3), 'paso': PASO_ZONAS, 'muestras': muestras, 'cortes': cortes}
    try:
        carpeta.mkdir(parents=True, exist_ok=True)
        import archivos_seguros
        archivos_seguros.escribir_json(archivo, d)
    except Exception:
        pass
    return d


def zonas_detras(analisis, palabras=(), cues=None):
    """De analizar_detras: ([(ini, fin)] donde «detrás de ti» queda bien, motivo(t) → clave de edicion_pro.MOTIVOS_DETRAS o None).
    Una zona = miradas seguidas con la persona bien, en la MISMA toma (sin corte entre medias), con la cabeza quieta (MOVIMIENTO_ZONA) y, si el
    video ya está transcrito, hablando (sin voz no hay captions). v5.27: con `cues` (los captions del tema), solo donde HAY un caption (en el
    Tema 1 los motions del kit ocupan tramos con voz y sin captions)."""
    import bisect
    if not analisis:
        return [], (lambda t: None)
    paso = float(analisis.get('paso') or PASO_ZONAS)
    dur = float(analisis.get('dur') or 0.0)
    cortes = sorted(float(c[0] if isinstance(c, (list, tuple)) else c) for c in analisis.get('cortes') or [])
    voz = sorted(float(s) for s, _w in palabras or [])
    tramos = sorted((float(c.get('start') or 0.0), float(c.get('end') or 0.0)) for c in cues or [])

    def hablando(t):
        if tramos:
            return any(a - 0.1 <= t <= b + 0.1 for a, b in tramos)
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
    """El segundo más cercano a t dentro de una zona (a `margen` de sus bordes si cabe): el «tope» de las marcas. t si no hay zonas o si ya está
    dentro de una (v5.27: antes lo apartaba del borde y avisaba «Puesta en 0:47.3… (en 0:47.4: )» sin motivo)."""
    if not zonas or any(a <= t <= b for a, b in zonas):
        return t
    mejor, dist = t, None
    for a, b in zonas:
        m = min(margen, (b - a) / 2)
        c = min(max(t, a + m), b - m)
        if dist is None or abs(c - t) < dist:
            mejor, dist = c, abs(c - t)
    r = round(round(mejor / PASO) * PASO, 2)
    return r if any(a <= r <= b for a, b in zonas) else round(mejor, 2)


# ======================================================================================================================== sugerencias y vista (v5.27)
# El usuario: «me dice dónde queda bien, pero que me lo indique: si me sugiere 3 lugares y les doy clic, que quede lista la selección; que
# detecte el tema y me dé la vista con los captions; si ya lo puse en la línea de tiempo, que muestre ese resultado aquí»
N_SUGERIDAS = 3
SEPARACION_SUGERIDAS = 3.0


def texto_cue(cue, n=4):
    """Las primeras palabras de un cue (lo que se lee en él)."""
    trozos = [str(r.get('texto') or '') for r in cue.get('runs') or []] + [str(ln.get('text') or '') for ln in cue.get('lines') or []]
    palabras_ = ' '.join(t for t in trozos if t.strip()).split()
    txt = ' '.join(palabras_[:n])
    return (txt[:1].upper() + txt[1:].lower() if txt.isupper() else txt) + ('…' if len(palabras_) > n else '')


def _grande_abajo(cue):
    """¿La palabra GRANDE del cue es la de abajo? (es la que tapa la cabeza: así la línea pequeña siempre se lee)."""
    runs = [r for r in cue.get('runs') or [] if isinstance(r.get('y'), (int, float))]
    if not runs:
        return False
    tam = lambda r: float(r.get('size') or r.get('zoom') or (2.0 if r.get('rol') == 'main' or r.get('fu') == 'main' else 1.0))
    abajo = max(runs, key=lambda r: float(r['y']))
    return tam(abajo) >= 0.8 * max(tam(r) for r in runs)


def _cue_en(cues, t, holgura=0.6):
    """Índice del cue que se ve en t (o el más cercano a menos de `holgura` s), o None."""
    mejor, dist = None, holgura
    for i, c in enumerate(cues or []):
        a, b = float(c.get('start') or 0.0), float(c.get('end') or 0.0)
        d = 0.0 if a <= t <= b else min(abs(t - a), abs(t - b))
        if d < dist or (d == 0.0 and mejor is None):
            mejor, dist = i, d
            if d == 0.0:
                break
    return mejor


def bloques_de(captions):
    """Los bloques con los que se decide (el verde, las sugeridas): {'start', 'end', 'caja' [arriba, abajo], 'grande' (la palabra grande abajo),
    'texto'}. Con el Tema 1 y la PRO, los de GO (captions_del_video: los del kit, sin los que tapan sus motions); si no, de los cues del tema."""
    if not captions:
        return []
    if captions.get('bloques') is not None:
        return captions['bloques']
    out = []
    for c in captions.get('cues') or []:
        caja = c.get('caja')
        if not (isinstance(caja, (list, tuple)) and len(caja) == 2):
            ys = [float(r['y']) for r in c.get('runs') or [] if isinstance(r.get('y'), (int, float))]
            caja = [min(ys) - 0.03, max(ys) + 0.03] if ys else [0.6, 0.75]
        out.append({'start': float(c.get('start') or 0.0), 'end': float(c.get('end') or 0.0), 'caja': [float(caja[0]), float(caja[1])],
                    'grande': _grande_abajo(c), 'texto': texto_cue(c)})
    return out


def sugerir(zonas, analisis=None, bloques=None, n=N_SUGERIDAS, ya=(), exigir_grande=False):
    """[(t, texto)] los `n` mejores sitios para «detrás de ti»: un bloque (bloques_de) que cabe ENTERO en el verde o, sin captions, el centro
    de cada zona; antes los de más aire sobre la cabeza, los más largos y los que llevan la palabra grande abajo, el primero (el gancho) con
    ventaja; separados SEPARACION_SUGERIDAS y sin los que ya están marcados (`ya`). Ordenados por tiempo. `exigir_grande` (Tema 1: GO solo
    pone detrás un caption con la palabra grande abajo): los demás no se sugieren."""
    if not zonas:
        return []
    ms = [m for m in (analisis or {}).get('muestras') or [] if m[1] is None and m[2] is not None]

    def aire(t):                                             # la coronilla bajo el borde de arriba (0,2 justo; 0,45 o más, de sobra)
        cerca = [m[2] for m in ms if abs(m[0] - t) <= 0.6]
        return max(0.0, min(1.0, (sum(cerca) / len(cerca) - ZONA_CORONILLA_MIN) / 0.25)) if cerca else 0.3
    cand = []
    for c in bloques or []:
        a, b = float(c['start']), float(c['end'])
        if b - a < 0.8 or (exigir_grande and not c.get('grande')):
            continue
        cor = [m[2] for m in ms if a - 0.25 <= m[0] <= b + 0.25]
        if cor and min(cor) < 0.08 + max(0.03, c['caja'][1] - c['caja'][0]) - 0.025:
            continue                                         # (ese caption es tan alto que, subido encima de la cabeza, se saldría por arriba)
        for za, zb in zonas:
            dentro = min(b, zb) - max(a, za)
            if dentro >= 0.7 * (b - a):
                t = round(min(max((a + b) / 2.0, za + 0.15), zb - 0.15), 1)
                cand.append((t, c.get('texto') or '', aire(t) + 0.3 * min(b - a, 3.0) / 3.0 + (0.5 if c.get('grande') else 0.0)))
                break
    if not cand:                                             # (sin captions todavía: el centro de cada zona y, si es larga, cada 5 s)
        for za, zb in zonas:
            puntos = [(za + zb) / 2.0] if zb - za <= 6.0 else [za + 2.0 + 5.0 * i for i in range(int((zb - za - 2.0) // 5.0) + 1)]
            for t in puntos:
                t = round(min(max(t, za + 0.15), zb - 0.15), 1)
                cand.append((t, '', aire(t) + 0.3 * min(zb - za, 3.0) / 3.0))
    if cand:
        primero = min(cand, key=lambda c: c[0])
        cand = [(t, x, s + (0.4 if (t, x) == primero[:2] else 0.0)) for t, x, s in cand]
    elegidas = []
    for t, x, _s in sorted(cand, key=lambda c: -c[2]):
        if len(elegidas) >= n:
            break
        if all(abs(t - e[0]) >= SEPARACION_SUGERIDAS for e in elegidas):
            elegidas.append((t, x))
    # (siempre las MISMAS n mejores: las ya marcadas se quitan y no salen otras —con «Poner las 3» se acaba—; si quitas una, vuelve)
    return sorted(e for e in elegidas if all(abs(e[0] - y) >= SEPARACION_MIN for y in ya))


def _clave_nombre(ruta_o_nombre):
    """El nombre de un video o del proyecto de GO, comparable: sin «CineCaptions», sin «_audio», solo letras y números."""
    import re
    s = re.sub(r'[^0-9a-z]', '', Path(str(ruta_o_nombre)).stem.lower() if '.' in Path(str(ruta_o_nombre)).name else str(ruta_o_nombre).lower())
    s = s[len('cinecaptions'):] if s.startswith('cinecaptions') else s
    return s[:-len('audio')] if s.endswith('audio') else s


def tema_de_inicio():
    """El tema elegido en Inicio (pack de plantillas: 'Kinetic', 'Referencia'… o '')."""
    try:
        import edicion_pro
        return edicion_pro.tema_actual() or ''
    except Exception:
        return ''


def _idioma_de(pal):
    """'en' o 'es' según las palabras más corrientes de lo que se dice."""
    en = sum(1 for p in pal if str(p.get('word') or '').strip().lower() in ('the', 'and', 'to', 'you', 'is', 'of', 'a', 'it', 'that', 'in'))
    es = sum(1 for p in pal if str(p.get('word') or '').strip().lower() in ('el', 'la', 'de', 'que', 'y', 'en', 'los', 'es', 'un', 'se'))
    return 'en' if en > es else 'es'


def bloques_neon(ruta, pal, imagen=None, analisis=None):
    """Tema 1 con la PRO: los bloques que GO pone detrás de verdad (kit_neon: sus captions, quitados los que pisan un motion del kit, con las
    mismas entradas que edicion_pro.planificar), como bloques_de. None si no se pudo. En un HILO (~3 s)."""
    try:
        import edicion_pro as EP
        import kit_neon as KN
        import kit_neon_motions as KM
        img = imagen or fuente_imagen(ruta)
        an = analisis or analizar_detras(ruta)
        dur = float((an or {}).get('dur') or 0.0) or None
        cortes = [tuple(c) if isinstance(c, (list, tuple)) else (float(c), 30.0) for c in (an or {}).get('cortes') or []]
        idioma = _idioma_de(pal)
        mot = KM.escena_motions(pal, idioma, dur, cortes=cortes, video=str(img[0] or ruta),
                                usuario=str(EP.opciones_guardadas().get('pro_usuario') or '') or None)
        out = []
        for b in KN.bloques_pro(KM.ajustar_captions(KN.escena_captions(pal, idioma, fin_video=dur), mot)):
            ws = [str(p[0]) for p in b.get('palabras') or []]
            out.append({'start': b['ini'], 'end': b['fin'], 'caja': [b['arriba'], b['abajo']], 'grande': bool(b.get('grande_abajo')),
                        'texto': ' '.join(ws[:4]) + ('…' if len(ws) > 4 else '')})
        return out
    except Exception:
        return None


def captions_del_video(ruta, imagen=None):
    """Los captions de ese video con su tema: {'cues', 'estilo', 'pack', 'nombre' («Tema N»), 'de_go' (True = los que GO puso en el timeline),
    'bloques' (Tema 1 con la PRO: bloques_neon; si no, None)}. Si el último GO fue de este video y con el mismo tema, sus cues tal cual (el
    manifiesto); si no, los que pondría el tema de Inicio con lo que se dice (vista_tema.planificar, como Creativo). None si no hay tema de
    fábrica o el video no está transcrito. En un HILO."""
    r = _captions_del_video(ruta, imagen)
    if r and r.get('pack') == 'Kinetic':
        try:
            import edicion_pro as EP
            pal = _voz_de(ruta) if EP.en_juego() else []
        except Exception:
            pal = []
        r['bloques'] = bloques_neon(ruta, pal, imagen) if pal else None
    return r


def _captions_del_video(ruta, imagen=None):
    import plantillas
    import vista_tema
    img = imagen or fuente_imagen(ruta)
    pack = tema_de_inicio()
    vertical = True
    try:
        import edicion_pro as EP
        w, h, _d, _f = EP.medir(img[0] or ruta)
        vertical = not (w and h and w > h)
    except Exception:
        pass
    estilo = vista_tema.estilo_de_pack(pack, 'v' if vertical else 'h')
    if not estilo:
        return None
    nombre = plantillas.nombre_visible(pack)
    try:                                                     # lo que GO ya puso en el timeline (si fue este video y con este tema)
        import edicion_pro as EP
        m = json.loads(EP.MANIFIESTO.read_text(encoding='utf-8'))
        if _clave_nombre(m.get('project') or '') in {_clave_nombre(ruta), _clave_nombre(img[0] or ruta)}:
            for t in m.get('tracks') or []:
                if t.get('style') in ('guion', 'kinetic') and (t.get('plantilla') or {}).get('pack') == pack and t.get('data_path'):
                    cues = json.loads(Path(t['data_path']).read_text(encoding='utf-8')).get('cues') or []
                    if cues:
                        return {'cues': cues, 'estilo': estilo, 'pack': pack, 'nombre': nombre, 'de_go': True}
    except Exception:
        pass
    pal = _voz_de(ruta)
    if not pal:
        return None
    try:
        cues = vista_tema.planificar(pal, [], pack, estilo, idioma=_idioma_de(pal), fin_video=img[2])
    except Exception:
        cues = []
    return {'cues': cues, 'estilo': estilo, 'pack': pack, 'nombre': nombre, 'de_go': False} if cues else None


def vista_detras(ruta, t, captions, imagen=None, alto=640):
    """La vista previa del instante t COMO QUEDA: el fotograma del video, el caption del tema que suena ahí y la persona DELANTE, subido con la
    misma regla de GO (la pila acaba un poco por debajo de la coronilla; edicion_pro.motivo_cabeza / INTENSIDAD_DETRAS). Si ahí no puede, el
    caption en su sitio de siempre. → (RGB uint8 HxWx3, {'detras': bool, 'motivo': clave | None, 'texto'}) o None. En un HILO."""
    import numpy as np
    from PIL import Image
    import edicion_pro as EP
    import edicion_pro_persona as PE
    import render_sin_resolve as RSR
    img_f, desde, _dur = imagen or fuente_imagen(ruta)
    if not img_f:
        return None
    rgb = PE.fotograma(img_f, float(t) + float(desde or 0.0))
    if rgb is None:
        return None
    h0, w0 = rgb.shape[:2]
    H = int(alto)
    W = max(2, int(round(H * w0 / float(h0))))
    base = np.asarray(Image.fromarray(rgb).resize((W, H), Image.LANCZOS), dtype=np.uint8)
    info = {'detras': False, 'motivo': None, 'texto': ''}
    cues = (captions or {}).get('cues') or []
    k = _cue_en(cues, float(t))
    neon = (captions or {}).get('bloques')
    if neon is not None and not any(b['start'] - 0.15 <= t <= b['end'] + 0.15 for b in neon):
        k = None                                             # (Tema 1 con la PRO: ahí va un motion del kit y GO quita ese caption)
    if k is None:
        info['motivo'] = 'sin_captions'
        return base, info
    cue = cues[k]
    info['texto'] = texto_cue(cue, 6)
    capas = RSR.preparar([cue], W, H, estilo=(captions or {}).get('estilo'))
    letras = [c for c in capas if c.get('tipo') != 'emoji']
    if not letras:
        return base, info
    t_vis = min(float(cue.get('end') or t) - 0.04, max(c['t0'] + c.get('entrada', 0.2) for c in capas) + 0.08)   # (con todo ya dentro)

    def tinta(c):                                            # (filas de la capa con letra de verdad: sin su halo ni su margen)
        filas = np.nonzero(c['a'][..., 0].max(axis=1) > 0.5)[0]
        return (c['y'] + int(filas[0]), c['y'] + int(filas[-1]) + 1) if len(filas) else (c['y'], c['y'] + c['a'].shape[0])
    tintas = [tinta(c) for c in letras]
    arriba = min(a for a, _b in tintas) / float(H)
    abajo = max(b for _a, b in tintas) / float(H)
    linea = max((b - a for a, b in tintas if b == max(z for _y, z in tintas)), default=0) / float(H)   # (el alto de la palabra de abajo)
    det = PE.personas_de_imagen(rgb)
    hcab = EP._cabeza(det)
    dy_px = 0
    if hcab is None:
        info['motivo'] = 'sin_persona'
    else:
        coronilla, cab_x, alto_p, cab = hcab
        cfg = EP.INTENSIDAD_DETRAS.get(EP.intensidad_detras()) or EP.INTENSIDAD_DETRAS['media']
        tapa = max(0.012, min(cfg['tapa_max'], 0.4 * cab, cfg['tapa'] * linea))
        dy = coronilla + tapa - abajo
        xs = [(c['x'] + c['a'].shape[1] / 2.0) / W for c in letras]
        m = EP.motivo_cabeza(coronilla, alto_p)
        if m is None and not (min(xs) - 0.16 <= cab_x <= max(xs) + 0.16):
            m = 'lado'
        if m is None and arriba + dy < 0.08:
            m = 'cabeza_arriba'
        if m is None and (abajo + dy > 0.9 or abajo + dy < coronilla + 0.012):
            m = 'no_cabe'
        info['motivo'] = m
        if m is None:
            dy_px = int(round(dy * H))
            info['detras'] = True
    for c in capas:
        c['y'] += dy_px
    arr = base.copy()
    RSR.componer(arr, capas, t_vis)
    if info['detras']:                                       # la persona DELANTE del texto (su silueta, como el recorte de Magic Mask)
        alfa = PE.refinar_alfa(PE.mate(rgb), W, H).astype(np.float32)[..., None] / 255.0
        arr = np.clip(arr.astype(np.float32) * (1.0 - alfa) + base.astype(np.float32) * alfa + 0.5, 0, 255).astype(np.uint8)
    return arr, info


# ======================================================================================================================== la vista
try:
    from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
    from PySide6.QtGui import QFontMetricsF, QImage, QPainter, QPainterPath, QPen, QPixmap
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
        instante; como mucho TOPE_MARCAS y nunca dos en el mismo caption (SEPARACION_MIN). Además: 3 sitios SUGERIDOS (anillos con «+» en la
        tira; un clic y queda puesta) y la vista grande enseña cómo QUEDA: el caption del tema detrás de la persona (vista_detras)."""
        cambio = Signal()
        cargado = Signal(str)                        # el archivo del que salen los fotogramas (con el audio de un timeline, su clip de V1)
        sugerencias = Signal()                       # v5.27: cambiaron los sitios sugeridos
        marca_puesta = Signal()                      # v5.27: el usuario puso una marca (la sección se enciende en GO)
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
            self._analisis = None
            self.captions = None                     # v5.27: captions_del_video (los del tema, para la vista)
            self.captions_listos = False
            self._aplicados = None
            self.sugeridas = []                      # [(t, texto)]
            self._vistas = {}                        # segundo (décimas) → (QPixmap | None, info) de vista_detras
            self._vista_pedida = None
            self._vista_ocupada = False
            self._cola_vistas = []
            self._reloj_vista = QTimer(self)
            self._reloj_vista.setSingleShot(True)
            self._reloj_vista.timeout.connect(self._hacer_vista)
            self._t_sobre = None
            self._arr = None
            self._sel = None
            self._movido = False
            self.setMouseTracking(True)
            self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            self.setMinimumHeight(520 if seccion in CON_PERSONA else 340)   # (v5.28: la vista con los captions, más grande)

        def igual_que_timeline(self):
            """v5.30: ¿la tira tiene exactamente lo que ya está en el timeline? (entonces «Listo» no necesita tocar Resolve)."""
            a = self._aplicados
            return (a is not None and self.modo == 'solo' and len(a) == len(self.marcas)
                    and all(abs(x - y) < 0.06 for x, y in zip(sorted(a), sorted(self.marcas))))

        # -- datos
        def cargar(self, ruta):
            self.ruta = ruta
            self.marcas, self.modo = [], 'solo'
            self.fotos, self.palabras, self.dur = [], [], 0.0
            self.zonas, self._motivo, self._imagen, self.nota = None, None, None, ''
            self._aplicados = None                   # v5.30: lo que hay en el timeline (tiempo de la tira) o None si no se sabe
            self._analisis, self.captions, self.sugeridas, self._cola_vistas = None, None, [], []
            self._vistas, self._vista_pedida, self.captions_listos = {}, None, False
            self.sugerencias.emit()
            self._sel = None
            self.aviso = tr('Leyendo los fotogramas del video…')
            self.update()

            def trabajo():
                img = fuente_imagen(ruta)
                aplicados, hecho = None, 0.0
                if self.seccion in CON_PERSONA:          # v5.30: lo que está AHORA en el timeline (lo puso GO por su cuenta o un «Listo»)
                    try:
                        import edicion_pro as EP
                        ctx = EP.contexto_detras(ruta)
                        if ctx is not None:
                            aplicados, hecho = EP.aplicados_para(ruta, ctx), float(ctx.get('hecho') or 0.0)
                    except Exception:
                        aplicados = None
                return fotogramas(ruta), palabras(ruta), img, leer_linea(ruta, img).get(self.seccion) or {}, aplicados, hecho

            def fin(r, error):
                if ruta != self.ruta:
                    return
                if error is None and r:
                    self._imagen = r[2]
                    guardadas, aplicados, hecho = r[3], r[4], r[5]
                    self._aplicados = None if aplicados is None else sorted(aplicados)
                    if aplicados is not None and float(guardadas.get('cuando') or 0.0) <= hecho:
                        # (el timeline es más nuevo que lo guardado: la tira enseña lo que hay, y «Listo» pone exactamente lo que quede)
                        self.marcas, self.modo = sorted(aplicados), 'solo'
                        self.nota = (tr('Así está ahora en tu timeline: {n}. Quita, mueve o añade y pulsa «Listo»: lo pongo en Resolve sin rehacer el video.',
                                        n=len(aplicados)) if aplicados else
                                     tr('En tu timeline no hay ninguno detrás de ti: toca una sugerencia o haz clic en lo verde y pulsa «Listo».'))
                    else:
                        self.marcas = list(guardadas.get('ts') or [])
                        self.modo = guardadas.get('modo') or 'solo'
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
                    self.recargar_captions()
            correr_en_hilo(self, trabajo, fin)

        def recargar_captions(self):
            """v5.27: los captions del tema de Inicio para la vista (los del timeline si GO ya pasó por este video con ese tema). En un hilo."""
            ruta, img = self.ruta, self._imagen
            if not ruta:
                return
            self._pack_pedido = tema_de_inicio()
            self.captions_listos = False

            def fin(cap, error):
                if ruta != self.ruta:
                    return
                self.captions = cap if error is None else None
                self.captions_listos = True
                self._vistas, self._vista_pedida, self._cola_vistas = {}, None, []
                self._rehacer_zonas()                # (con los captions del tema, el verde solo donde HAY caption)
                self.update()
                self.cambio.emit()
            correr_en_hilo(self, lambda: captions_del_video(ruta, img), fin)

        def pack_vista(self):
            return getattr(self, '_pack_pedido', None)

        def _rehacer_zonas(self):
            if self._analisis is None:
                return
            self.zonas, self._motivo = zonas_detras(self._analisis, self.palabras, bloques_de(self.captions))
            self._aplicar_topes()
            self._calcular_sugeridas()

        def _calcular_sugeridas(self):
            """Los sitios sugeridos (sin los ya marcados) y, de paso, sus vistas y las de las marcas, preparadas para que salgan al momento."""
            if self.seccion not in CON_PERSONA or self.zonas is None:
                return
            nuevas = sugerir(self.zonas, self._analisis, bloques_de(self.captions), ya=self.marcas,
                             exigir_grande=(self.captions or {}).get('pack') == 'Kinetic')
            if nuevas != self.sugeridas:
                self.sugeridas = nuevas
                self.sugerencias.emit()
            if self.captions is not None:
                for t in [s[0] for s in self.sugeridas] + list(self.marcas):
                    k = round(float(t), 1)
                    if k not in self._vistas and k not in self._cola_vistas:
                        self._cola_vistas.append(k)
                if not self._vista_ocupada:
                    self._hacer_vista()

        def anadir(self, t):
            """Pone una marca en t (una sugerencia): con los mismos topes que un clic. True si se puso."""
            if self.dur <= 0:
                return False
            ok, t2 = self._puede_anadir(float(t))
            if ok:
                self.marcas = sorted(self.marcas + [t2])
                self._sel = self.marcas.index(t2)
                self.nota = ''
                self._guardar()
                self.marca_puesta.emit()
            self.update()
            return ok

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
                    self._analisis = an
                    self._rehacer_zonas()
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
            if self.igual_que_timeline():
                return                               # (v5.30: lo que llega del timeline se enseña tal cual: es lo que hay)
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
                m = self.texto_motivo(t)
                self.nota = (tr('Puesta en {t}, lo más cerca donde queda bien (en {o}: {m}).', t=texto_t(t2), o=texto_t(t), m=m) if m else
                             tr('Puesta en {t}, lo más cerca donde queda bien.', t=texto_t(t2)))
            return True, t2

        def _guardar(self):
            if self.ruta:                            # (sin leer el disco aquí: hasta que el hilo sabe su video, un audio guarda con su ruta)
                guardar_linea(self.ruta, self.seccion, self.marcas, self.modo, imagen=self._imagen or (str(self.ruta), 0.0, None))
            self._calcular_sugeridas()               # (lo ya marcado deja de sugerirse; lo que se quita, vuelve)
            self.cambio.emit()

        # -- la vista con los captions (v5.27)
        def _alto_prev(self):
            return max(60.0, self._tira().top() - 58)

        def _vista_de(self, t):
            return self._vistas.get(round(float(t), 1))

        def _pedir_vista(self, t):
            """La vista de t, en cuanto el ratón se para (lo que ya está hecho sale al momento)."""
            if self.captions is None or self.dur <= 0:
                return
            k = round(float(t), 1)
            if k in self._vistas or k == self._vista_pedida:
                return
            self._vista_pedida = k
            self._reloj_vista.start(140)

        def _hacer_vista(self):
            """Una vista en un hilo: la pedida (el ratón) o, si no, la siguiente de la cola (sugerencias y marcas)."""
            if self._vista_ocupada or self.captions is None or not self.ruta:
                return
            k = self._vista_pedida if self._vista_pedida is not None and self._vista_pedida not in self._vistas else None
            while k is None and self._cola_vistas:
                c = self._cola_vistas.pop(0)
                k = c if c not in self._vistas else None
            if k is None:
                return
            self._vista_ocupada = True
            ruta, cap, img = self.ruta, self.captions, self._imagen
            dpr = max(1.0, float(self.devicePixelRatioF()))
            alto = int(max(240, min(960, self._alto_prev() * dpr)))

            def trabajo():
                r = vista_detras(ruta, k, cap, img, alto=alto)
                if r is None:
                    return None
                arr, info = r
                h, w = arr.shape[:2]
                return QImage(arr.data, w, h, 3 * w, QImage.Format.Format_RGB888).copy(), info

            def fin(r, error):
                self._vista_ocupada = False
                if ruta != self.ruta or cap is not self.captions:
                    self._hacer_vista()
                    return
                pm = None
                if error is None and r:
                    pm = QPixmap.fromImage(r[0])
                    pm.setDevicePixelRatio(dpr)
                self._vistas[k] = (pm, r[1] if (error is None and r) else {'detras': False, 'motivo': None})
                while len(self._vistas) > 60:
                    self._vistas.pop(next(iter(self._vistas)))
                self.update()
                self._hacer_vista()
            correr_en_hilo(self, trabajo, fin)

        def _sugerida_en(self, pos):
            r = self._tira()
            if not (r.top() - 30 <= pos.y() <= r.bottom() + 4):
                return None
            mejor, dist = None, 9.0
            for i, (t, _x) in enumerate(self.sugeridas):
                d = abs(self._x(t) - pos.x())
                if d <= dist:
                    mejor, dist = i, d
            return mejor

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
            j = self._sugerida_en(pos) if i is None else None
            if j is not None:                        # (v5.27: un anillo sugerido: un clic y queda puesta)
                self.anadir(self.sugeridas[j][0])
                return
            if i is None:                            # marca nueva donde se pulsó (y se puede arrastrar en el mismo gesto)
                ok, t = self._puede_anadir(self._t(pos.x()))
                if not ok:
                    self.update()
                    return
                self.marcas.append(t)
                i = len(self.marcas) - 1
                self._movido = True
                self.marca_puesta.emit()
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
                                                                    (self.marcas[0] if self.marcas else (self.sugeridas[0][0] if self.sugeridas else 0.0)))
            alto_prev = self._alto_prev()
            con_persona = self.seccion in CON_PERSONA
            vista = self._vista_de(t_ver) if con_persona else None   # v5.27: cómo QUEDA (el caption del tema detrás de la persona)
            if con_persona and vista is None:
                self._pedir_vista(t_ver)
            info = vista[1] if vista and vista[0] is not None else None
            pm = vista[0] if info is not None else self._foto_en(t_ver)
            x_txt = self.MARGEN
            motivo = self.texto_motivo(t_ver) if con_persona and self.zonas is not None else ''
            if not motivo and info is not None and not info.get('detras') and info.get('motivo'):
                try:
                    import edicion_pro as EP
                    motivo = tr(EP.MOTIVOS_DETRAS.get(info['motivo'], info['motivo']))
                except Exception:
                    motivo = ''
            if pm is not None and not pm.isNull():
                ancho_prev = alto_prev * pm.width() / max(1, pm.height())
                caja = QRectF(self.MARGEN, 6, ancho_prev, alto_prev)
                camino = QPainterPath()
                camino.addRoundedRect(caja, 12, 12)
                p.save()
                p.setClipPath(camino)
                p.drawPixmap(caja, pm, QRectF(pm.rect()))
                if info is not None:                 # el tema con el que se ve (Inicio) en una pastilla
                    nombre = (self.captions or {}).get('nombre') or ''
                    p.setFont(fuente(11, peso='negrita'))
                    w_chip = QFontMetricsF(p.font()).horizontalAdvance(nombre) + 16
                    chip = QRectF(caja.left() + 8, caja.top() + 8, w_chip, 20)
                    p.setPen(Qt.PenStyle.NoPen)
                    p.setBrush(QColorReal(0, 0, 0, 150))
                    p.drawRoundedRect(chip, 10, 10)
                    p.setPen(QColor('#FFFFFF'))
                    p.drawText(chip, int(Qt.AlignmentFlag.AlignCenter), nombre)
                p.restore()
                p.setPen(QPen(QColor(self.AMBAR), 2) if con_persona and info is not None and motivo else QPen(QColorReal(255, 255, 255, 40), 1))
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawPath(camino)
                x_txt = caja.right() + 22
            ancho_txt = self.width() - x_txt - self.MARGEN
            p.setPen(QColor('#FFFFFF'))
            p.setFont(fuente(26, peso='negrita'))
            p.drawText(QRectF(x_txt, 6, ancho_txt, 40), int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), texto_t(t_ver))
            if con_persona:                          # v5.27: ¿aquí queda bien el texto detrás de la persona?
                x_est = x_txt + QFontMetricsF(p.font()).horizontalAdvance(texto_t(t_ver)) + 18
                p.setFont(fuente(13, peso='medio'))
                if self.analizando():
                    p.setPen(QColor('#8EA2C6'))
                    est = tr('Buscando en tu video dónde queda bien… {p} %', p=int(round(100 * self._progreso[0])))
                elif self.zonas is not None:
                    p.setPen(QColor(self.AMBAR if motivo else self.VERDE))
                    est = (tr('Aquí no queda bien: {m}', m=motivo) if motivo else
                           tr('Así queda detrás de ti') if info is not None else tr('Aquí queda bien detrás de ti'))
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
                ayuda += ' · ' + tr('verde: queda bien · +: sugerido')
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
            # ---- v5.27: los sitios sugeridos (un anillo con «+»: clic = queda puesta)
            verde = QColor(self.VERDE)
            for t, _txt in self.sugeridas:
                x = self._x(t)
                p.setPen(QPen(QColorReal(52, 211, 153, 120), 1.2, Qt.PenStyle.DashLine))
                p.drawLine(QPointF(x, tira.top() - 6), QPointF(x, tira.bottom()))
                p.setPen(QPen(verde, 1.8))
                p.setBrush(QColorReal(10, 18, 34, 235))
                p.drawEllipse(QPointF(x, tira.top() - 14), 7.5, 7.5)
                p.drawLine(QPointF(x - 3.5, tira.top() - 14), QPointF(x + 3.5, tira.top() - 14))
                p.drawLine(QPointF(x, tira.top() - 17.5), QPointF(x, tira.top() - 10.5))
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
            # v5.27: los sitios sugeridos, a un clic (también son los anillos «+» de la tira)
            self._fila_sug = QWidget()
            self._capa_sug = QHBoxLayout(self._fila_sug)
            self._capa_sug.setContentsMargins(0, 0, 0, 0)
            self._capa_sug.setSpacing(8)
            self._fila_sug.setVisible(False)
            capa.addWidget(self._fila_sug)
            self.linea = LineaTiempo(seccion)
            self.linea.cambio.connect(self._al_cambiar)
            self.linea.cargado.connect(self._al_cargar)
            self.linea.sugerencias.connect(self._pintar_sugeridas)
            capa.addWidget(self.linea)

        def _pintar_sugeridas(self):
            while self._capa_sug.count():
                it = self._capa_sug.takeAt(0)
                if it.widget() is not None:
                    it.widget().deleteLater()
            sug = list(self.linea.sugeridas)
            self._fila_sug.setVisible(bool(sug))
            if not sug:
                return
            self._capa_sug.addWidget(Etiqueta(tr('Sugeridas:'), 13, peso='medio', color='#C9D6EC'))
            for t, txt in sug:
                self._capa_sug.addWidget(Boton('+ ' + texto_t(t) + (f' · {txt}' if txt else ''), lambda t=t: self._poner(t), tipo='neutro', alto=30, tam=12))
            if len(sug) > 1:
                self._capa_sug.addWidget(Boton(tr('Poner las {n}', n=len(sug)), self._poner_todas, tipo='primario', alto=30, tam=12))
            self._capa_sug.addStretch(1)

        def _poner(self, t):
            self.linea.anadir(t)
            self.linea.setFocus()

        def _poner_todas(self):
            for t, _txt in list(self.linea.sugeridas):
                if not self.linea.anadir(t):
                    break
            self.linea.setFocus()

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
            n = len(self.linea.marcas)
            if self.seccion in CON_PERSONA:          # v5.27 (el usuario: «más intuitivo, sin ser tan complicado»): una frase
                txt = (tr('Toca una sugerencia o haz clic en lo verde: el caption de ese momento va detrás de ti.') + ' ' +
                       (tr('Solo ahí.') if self.linea.modo == 'solo' else tr('Ahí y donde elija el automático.')))
                if n:
                    txt += ' · ' + (tr('1 marca') if n == 1 else tr('{n} marcas', n=n)) + f' / {TOPE_MARCAS.get(self.seccion, 8)}'
                self._lbl_modo.setText(txt)
                return
            if self.linea.modo == 'solo':
                txt = tr('GO pone este efecto SOLO en tus marcas (sin marcas, donde lo elija el automático).')
            else:
                txt = tr('GO lo pone en tus marcas y, además, donde lo elija el automático.')
            if self.seccion == 'motions_completo':
                txt = (tr('Solo mis marcas: el video de motions sale solo en los tramos que marques.') if self.linea.modo == 'solo'
                       else tr('Con «+ automático», el video de motions va en todo el video, como siempre.'))
            elif ligada:
                txt += ' ' + tr('Se usa el bloque de captions que suena en ese segundo.')
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
            elif (self.seccion in CON_PERSONA and self.linea.dur > 0 and self.linea.pack_vista() is not None
                  and self.linea.pack_vista() != tema_de_inicio()):
                self.linea.recargar_captions()           # (v5.27: otro tema en Inicio: la vista con SUS captions)
