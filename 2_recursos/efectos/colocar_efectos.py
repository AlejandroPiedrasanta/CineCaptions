# CineCaptions · By Cinema Productions
# 2_recursos/efectos/colocar_efectos.py — corre DENTRO de Resolve: pone la intro, las transiciones de los cortes y los iconos flotantes en pistas propias «FX-…».
"""
Lo lanza efectos_visuales.aplicar() (resolve_mcp.ejecutar_py) y lee ~/DaVinciSubtitles/efectos_plan.json:

    {'fps': 30.0, 'inicio': <primer fotograma del timeline>, 'offset_frames': 0,
     'eventos': [{'tipo': 'intro'|'corte'|'icono'|'sonido', 'ini': segundos, 'modo': 'screen'|'normal'|'audio', 'archivo': mp4/wav | 'secuencia': {'patron', 'n'}}]}

Reglas: nunca toca V1/A1 ni las pistas de los captions; las pistas FX-INTRO / FX-CORTES / FX-ICONOS (video) y FX-SONIDO (audio, el sonido de la intro) se vacían y se vuelven a llenar en cada corrida (re-aplicar no apila
nada); los clips de una misma pista nunca se pisan; los archivos se importan una sola vez al bin «RCS · Efectos» (el prefijo «RCS · » hace que CineCaptions no lo
cuente como plantillas del usuario). Nada de InsertFusionTitleIntoTimeline ni de stills: solo importar medios y AppendToTimeline.
"""
import json
import os

RUTA_JSON = os.path.join(os.path.expanduser('~'), 'DaVinciSubtitles', 'efectos_plan.json')
PISTAS = {'intro': 'FX-INTRO', 'corte': 'FX-CORTES', 'icono': 'FX-ICONOS'}
PISTA_SONIDO = 'FX-SONIDO'
BIN = 'RCS · Efectos'


def _norm(r):
    return os.path.normcase(os.path.normpath(str(r)))


def _buscar_clip(carpeta, buscada):
    for clip in carpeta.GetClipList() or []:
        try:
            r = clip.GetClipProperty('File Path') or ''
        except Exception:
            continue
        if r and _norm(r) == buscada:
            return clip
    for sub in carpeta.GetSubFolderList() or []:
        x = _buscar_clip(sub, buscada)
        if x is not None:
            return x
    return None


def _carpeta_efectos(mp):
    raiz = mp.GetRootFolder()
    for f in raiz.GetSubFolderList() or []:
        if f.GetName() == BIN:
            return f
    return mp.AddSubFolder(raiz, BIN) or raiz


def _importar(mp, caja, ev):
    """El clip del Media Pool de ese archivo / secuencia (se reusa si ya está)."""
    if ev.get('secuencia'):
        patron, n = str(ev['secuencia']['patron']), int(ev['secuencia']['n'])
        buscada = _norm(patron.replace('%04d', '[0001-%04d]' % n))
        pedido = [{'FilePath': patron, 'StartIndex': 1, 'EndIndex': n}]
    else:
        buscada = _norm(ev['archivo'])
        pedido = [str(ev['archivo'])]
    ya = _buscar_clip(mp.GetRootFolder(), buscada)
    if ya is not None:
        return ya
    previa = mp.GetCurrentFolder()
    try:
        mp.SetCurrentFolder(caja)
        nuevos = mp.ImportMedia(pedido)
    finally:
        try:
            mp.SetCurrentFolder(previa)
        except Exception:
            pass
    return nuevos[0] if nuevos else None


def _pista(tl, nombre, tipo='video'):
    """El índice de la pista (de video o de audio) con ese nombre (se crea si no está) y sus clips de antes ya borrados."""
    for i in range(1, int(tl.GetTrackCount(tipo) or 0) + 1):
        if tl.GetTrackName(tipo, i) == nombre:
            viejos = tl.GetItemListInTrack(tipo, i) or []
            if viejos:
                tl.DeleteClips(viejos, False)
            return i
    creada = False
    if tipo == 'audio':
        try:
            creada = bool(tl.AddTrack('audio', 'stereo'))
        except Exception:
            creada = False
    if not creada and not tl.AddTrack(tipo):
        return None
    i = int(tl.GetTrackCount(tipo))
    tl.SetTrackName(tipo, i, nombre)
    return i


def _quitar_si_vacia(tl, nombre, tipo='video'):
    for i in range(int(tl.GetTrackCount(tipo) or 0), 0, -1):
        if tl.GetTrackName(tipo, i) == nombre and not (tl.GetItemListInTrack(tipo, i) or []):
            try:
                tl.DeleteTrack(tipo, i)
            except Exception:
                pass


def main():
    with open(RUTA_JSON, encoding='utf-8') as f:
        datos = json.load(f)
    tl = project.GetCurrentTimeline()
    if tl is None:
        raise SystemExit('no hay un timeline activo en Resolve')
    mp = project.GetMediaPool()
    fps = float(datos.get('fps') or tl.GetSetting('timelineFrameRate') or 30)
    base = int(datos.get('inicio') or tl.GetStartFrame()) + int(datos.get('offset_frames') or 0)
    modo_screen = getattr(resolve, 'COMPOSITE_SCREEN', None)
    caja = _carpeta_efectos(mp)
    puestos = {'intro': 0, 'corte': 0, 'icono': 0}
    saltados = 0
    por_pista = {}
    for tipo, nombre in PISTAS.items():
        eventos = sorted((e for e in datos.get('eventos', []) if e.get('tipo') == tipo), key=lambda e: float(e['ini']))
        idx = _pista(tl, nombre)
        if idx is None:
            print('  no pude crear la pista %s' % nombre)
            saltados += len(eventos)
            continue
        por_pista[tipo] = idx
        fin_anterior = -1
        for ev in eventos:
            clip = _importar(mp, caja, ev)
            if clip is None:
                print('  no pude importar el efecto %s (%s)' % (tipo, ev.get('asset')))
                saltados += 1
                continue
            try:
                frames = int(float(clip.GetClipProperty('Frames') or 0))
                fps_clip = float(clip.GetClipProperty('FPS') or fps)
            except Exception:
                frames, fps_clip = 0, fps
            if frames <= 1:
                saltados += 1
                continue
            dur_tl = int(round(frames * fps / fps_clip))                # lo que dura en el timeline (fotogramas)
            ini = base + int(round(float(ev['ini']) * fps))
            if tipo == 'corte':                                         # el corte cae en medio del efecto
                ini -= dur_tl // 2
            ini = max(base, ini)
            if ini <= fin_anterior:                                     # nunca se pisan dos clips de la misma pista
                saltados += 1
                continue
            nuevos = mp.AppendToTimeline([{'mediaPoolItem': clip, 'startFrame': 0, 'endFrame': frames - 1, 'recordFrame': ini, 'trackIndex': idx, 'mediaType': 1}])
            item = nuevos[0] if nuevos else None
            if not item:
                saltados += 1
                continue
            fin_anterior = ini + dur_tl
            if ev.get('modo') == 'screen' and modo_screen is not None:
                try:
                    item.SetProperty('CompositeMode', modo_screen)
                except Exception as e:
                    print('  (no pude poner Screen: %s)' % e)
            try:
                item.SetName('%s · %s' % (nombre, ev.get('asset', '')))
            except Exception:
                pass
            puestos[tipo] += 1
    # el sonido de la intro: UN clip de audio en su propia pista «FX-SONIDO» (el audio del video, en A1, no se toca)
    sonidos = sorted((e for e in datos.get('eventos', []) if e.get('tipo') == 'sonido'), key=lambda e: float(e['ini']))
    puestos['sonido'] = 0
    idx_audio = _pista(tl, PISTA_SONIDO, 'audio')
    for ev in sonidos:
        if idx_audio is None:
            print('  no pude crear la pista de audio %s' % PISTA_SONIDO)
            saltados += 1
            break
        clip = _importar(mp, caja, ev)
        if clip is None:
            print('  no pude importar el sonido de la intro')
            saltados += 1
            continue
        frames = max(2, int(round(float(ev.get('dur') or 1.0) * fps)))
        ini = base + int(round(float(ev['ini']) * fps))
        nuevos = mp.AppendToTimeline([{'mediaPoolItem': clip, 'startFrame': 0, 'endFrame': frames - 1, 'recordFrame': ini, 'trackIndex': idx_audio, 'mediaType': 2}])
        if not nuevos:
            saltados += 1
            continue
        try:
            nuevos[0].SetName('%s · %s' % (PISTA_SONIDO, ev.get('asset', '')))
        except Exception:
            pass
        puestos['sonido'] += 1
    for tipo, nombre in PISTAS.items():
        if tipo in por_pista and puestos[tipo] == 0:
            _quitar_si_vacia(tl, nombre)
    if puestos['sonido'] == 0:
        _quitar_si_vacia(tl, PISTA_SONIDO, 'audio')
    print('Efectos: %d intro, %d sonido, %d transiciones, %d iconos (%d sin poner).' % (puestos['intro'], puestos['sonido'], puestos['corte'], puestos['icono'], saltados))
    if sum(puestos.values()) == 0 and datos.get('eventos'):
        raise SystemExit('Resolve no colocó ningún efecto')
