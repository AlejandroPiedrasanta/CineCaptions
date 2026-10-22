# CineCaptions · By Cinema Productions
# 4_diseno/plantillas_virales/resolve_taller.py — funciones que corren DENTRO de Resolve: construir los timelines, importar y verificar los .drb de los packs.
"""Taller de «Plantillas virales cinema»: utilidades que corren DENTRO de Resolve (por el MCP), en un hilo,
con el avance en estado.json (así ninguna llamada larga del MCP se corta a medias)."""
import json
import os
import threading
import time
import traceback

AQUI = os.path.dirname(os.path.abspath(__file__))
ESTADO = os.path.join(AQUI, 'estado.json')
_R = {'resolve': None}


def escribir_estado(**datos):
    datos['t'] = time.time()
    tmp = ESTADO + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent=1, default=str)
    os.replace(tmp, ESTADO)


def lanzar(resolve, funcion, **kw):
    """Corre funcion(resolve, avisar, **kw) en un hilo. avisar(texto) va al estado."""
    _R['resolve'] = resolve
    registro = []

    def avisar(texto):
        registro.append(f'{time.strftime("%H:%M:%S")} {texto}')
        escribir_estado(estado='corriendo', registro=registro[-60:])

    def hilo():
        try:
            escribir_estado(estado='corriendo', registro=[])
            salida = funcion(resolve, avisar, **kw)
            escribir_estado(estado='listo', registro=registro[-60:], resultado=salida)
        except Exception:
            escribir_estado(estado='error', registro=registro[-60:], error=traceback.format_exc())
    threading.Thread(target=hilo, daemon=True, name='taller').start()
    return 'lanzado'


def timecode(marco, fps=30):
    h = marco // (3600 * fps)
    m = (marco // (60 * fps)) % 60
    s = (marco // fps) % 60
    f = marco % fps
    return f'{h:02d}:{m:02d}:{s:02d}:{f:02d}'


def primera_textplus(item):
    comp = item.GetFusionCompByIndex(1)
    if not comp:
        return None
    for _, t in comp.GetToolList().items():
        if t.ID == 'TextPlus':
            return t
    return None


# ------------------------------------------------------------------ configuración de un título
FORMATOS = {'v': (1080, 1920), 'h': (1920, 1080)}


def configurar(item, cfg):
    """Aplica cfg = {preset, size, color, barra, tono, texto} a un título recién insertado."""
    comp = item.GetFusionCompByIndex(1)
    t1 = comp.FindTool('Text1')
    if cfg.get('texto') is not None:
        t1.SetInput('StyledText', cfg['texto'])
    preset = cfg['preset']
    if preset == 'Fire_Captions':           # el tamaño real de Fire lo da su Transform1 (Text Size no cuenta)
        comp.FindTool('Transform1').SetInput('Size', float(cfg['size']))
    elif preset.startswith('Luxe'):
        sc = comp.FindTool('sizeCtrl')
        if cfg.get('size') is not None:
            sc.SetInput('RestingSize', float(cfg['size']))
    elif cfg.get('size') is not None:
        try:
            if t1.Size.GetExpression():     # Underline: Size es una expresión fija ("0.126") que pisa SetInput
                t1.Size.SetExpression(None)
        except Exception:
            pass
        t1.SetInput('Size', float(cfg['size']))
    if cfg.get('color') is not None:
        r, g, b = cfg['color']
        t1.SetInput('Red1', float(r))
        t1.SetInput('Green1', float(g))
        t1.SetInput('Blue1', float(b))
    ln = comp.FindTool('Line')
    if ln is not None and cfg.get('barra') is False:
        ln.SetInput('Enabled8', 0)
    cc = comp.FindTool('ColorCorrector1')
    if cc is not None and cfg.get('tono') is not None:
        cc.SetInput('Hue1', float(cfg['tono']))
    if cfg.get('tracking') is not None:
        t1.SetInput('CharacterSpacing', float(cfg['tracking']))


def nuevo_timeline(p, nombre, formato):
    mp = p.GetMediaPool()
    tl = mp.CreateEmptyTimeline(nombre)
    w, h = FORMATOS[formato]
    tl.SetSetting('useCustomSettings', '1')
    tl.SetSetting('timelineResolutionWidth', str(w))
    tl.SetSetting('timelineResolutionHeight', str(h))
    tl.SetSetting('timelineFrameRate', '30')
    p.SetCurrentTimeline(tl)
    return tl


def fotos(resolve, p, tl, items, carpeta, prefijo, avisar, desfase=70):
    """Exporta un fotograma de cada item (a 'desfase' frames de su inicio)."""
    os.makedirs(carpeta, exist_ok=True)
    resolve.OpenPage('color')
    time.sleep(1.0)
    rutas = []
    for i, item in enumerate(items):
        tl.SetCurrentTimecode(timecode(int(item.GetStart() + desfase)))
        time.sleep(0.5)
        ruta = os.path.join(carpeta, f'{prefijo}_{i:02d}.png')
        p.ExportCurrentFrameAsStill(ruta)
        rutas.append(ruta)
        avisar(f'foto {ruta}')
    resolve.OpenPage('edit')
    return rutas


# ------------------------------------------------------------------ calibración
def calibrar(resolve, avisar, pruebas, carpeta):
    """pruebas = [{formato, preset, size, color, barra, texto}] -> fotos para medir."""
    p = resolve.GetProjectManager().GetCurrentProject()
    resolve.OpenPage('edit')
    salida = {}
    for formato in ('v', 'h'):
        tl = nuevo_timeline(p, f'calibracion {formato} {time.strftime("%H%M%S")}', formato)
        items = []
        for prueba in [x for x in pruebas if x['formato'] == formato]:
            item = tl.InsertFusionTitleIntoTimeline(prueba['preset'])
            configurar(item, prueba)
            items.append(item)
            avisar(f'{formato} {prueba["preset"]} {prueba.get("size")}')
        salida[formato] = fotos(resolve, p, tl, items, carpeta, f'cal_{formato}', avisar)
    return salida


# ------------------------------------------------------------------ pasar los Text+ de un .drt a un bin y exportarlo
def promover_a_bin(resolve, avisar, ruta_drt, nombre_bin, ruta_drb):
    """Importa el .drt (crea los clips en el Media Pool), mueve esos clips a un bin nuevo con su nombre de
    rol y exporta el bin como .drb. Devuelve un informe."""
    p = resolve.GetProjectManager().GetCurrentProject()
    mp = p.GetMediaPool()
    raiz = mp.GetRootFolder()
    mp.SetCurrentFolder(raiz)
    bin_ = mp.AddSubFolder(raiz, nombre_bin)
    mp.SetCurrentFolder(bin_)
    tl = mp.ImportTimelineFromFile(ruta_drt, {'timelineName': nombre_bin + ' (importado)',
                                              'importSourceClips': True})
    if not tl:
        raise RuntimeError('ImportTimelineFromFile no devolvió timeline')
    informe = {'pistas': tl.GetTrackCount('video'), 'clips': [], 'sin_mpi': []}
    movidos = []
    for pista in range(1, tl.GetTrackCount('video') + 1):
        for it in tl.GetItemListInTrack('video', pista) or []:
            mpi = it.GetMediaPoolItem()
            if not mpi:
                informe['sin_mpi'].append(it.GetName())
                continue
            movidos.append((mpi, it.GetName()))
    for mpi, nombre in movidos:
        mp.MoveClips([mpi], bin_)
        try:
            mpi.SetClipProperty('Clip Name', nombre)
        except Exception:
            pass
        if (mpi.GetName() or '').strip().lower() != nombre.strip().lower():
            mpi.SetName(nombre)
        informe['clips'].append(mpi.GetName())
    avisar(f'{len(informe["clips"])} clips en el bin «{nombre_bin}»')
    if os.path.exists(ruta_drb):
        os.remove(ruta_drb)
    ok = bin_.Export(ruta_drb)
    informe['drb'] = bool(ok) and os.path.exists(ruta_drb)
    informe['timeline_importado'] = tl.GetName()
    mp.SetCurrentFolder(raiz)
    return informe


def prueba_promover(resolve, avisar, carpeta):
    p = resolve.GetProjectManager().GetCurrentProject()
    resolve.OpenPage('edit')
    tl = nuevo_timeline(p, 'prueba promover ' + time.strftime('%H%M%S'), 'v')
    for nombre, preset in (('contexto', 'Luxe Slide'), ('principal', 'Luxe Shine'), ('complemento', 'Luxe Slide')):
        it = tl.InsertFusionTitleIntoTimeline(preset)
        configurar(it, {'preset': preset, 'texto': nombre})
        it.SetName(nombre)
        it.SetProperties({'Tilt': 300.0 if nombre == 'contexto' else (-300.0 if nombre == 'complemento' else 0.0)})
    drt = os.path.join(carpeta, 'prueba.drt')
    if os.path.exists(drt):
        os.remove(drt)
    ok = tl.Export(drt, resolve.EXPORT_DRT, resolve.EXPORT_NONE)
    avisar(f'drt {ok} {os.path.exists(drt)}')
    return {'drt': ok, 'promover': promover_a_bin(resolve, avisar, drt, 'prueba bin ' + time.strftime('%H%M%S'),
                                                   os.path.join(carpeta, 'prueba.drb'))}


# ------------------------------------------------------------------ paso 1: timelines de diseño + .drt
def construir_disenos(resolve, avisar, diseno, carpeta, solo=None):
    with open(diseno, encoding='utf-8') as f:
        packs = json.load(f)
    p = resolve.GetProjectManager().GetCurrentProject()
    resolve.OpenPage('edit')
    os.makedirs(carpeta, exist_ok=True)
    hechos = {}
    for pk in packs:
        if solo and pk['archivo'] not in solo:
            continue
        w, h = FORMATOS[pk['formato']]
        tl = nuevo_timeline(p, pk['archivo'] + ' · diseño ' + time.strftime('%H%M%S'), pk['formato'])
        nombres = []
        for clip in pk['clips']:
            cfg = clip['cfg']
            item = tl.InsertFusionTitleIntoTimeline(cfg['preset'])
            if not item:
                raise RuntimeError(f'no se insertó {cfg["preset"]} ({clip["nombre"]})')
            configurar(item, cfg)
            item.SetName(clip['nombre'])
            x, y, zx, zy = clip['pos']
            item.SetProperties({'Pan': x * w, 'Tilt': y * h, 'ZoomX': zx, 'ZoomY': zy})
            nombres.append(item.GetName())
        drt = os.path.join(carpeta, pk['archivo'] + '.drt')
        if os.path.exists(drt):
            os.remove(drt)
        ok = tl.Export(drt, resolve.EXPORT_DRT, resolve.EXPORT_NONE)
        hechos[pk['archivo']] = {'drt': bool(ok) and os.path.exists(drt), 'clips': len(nombres),
                                 'timeline': tl.GetName()}
        avisar(f'{pk["archivo"]}: {len(nombres)} clips, drt {hechos[pk["archivo"]]["drt"]}')
    return hechos


# ------------------------------------------------------------------ experimento 1: leer valores
def leer_valores(resolve, avisar):
    p = resolve.GetProjectManager().GetCurrentProject()
    tl = p.GetCurrentTimeline()
    fuera = {}
    for item in tl.GetItemListInTrack('video', 1):
        avisar('leo ' + item.GetName())
        comp = item.GetFusionCompByIndex(1)
        t1 = comp.FindTool('Text1')
        d = {k: t1.GetInput(k) for k in ('Size', 'LayoutSize', 'Font', 'Style', 'Red1', 'Green1', 'Blue1',
                                          'CharacterSpacing', 'StyledText')}
        sc = comp.FindTool('sizeCtrl')
        if sc:
            d['sizeCtrl.RestingSize'] = sc.GetInput('RestingSize')
        ln = comp.FindTool('Line')
        if ln:
            d['Line'] = {k: ln.GetInput(k) for k in ('Enabled1', 'Enabled2', 'Enabled8', 'Red8', 'Green8', 'Blue8',
                                                      'Red1', 'Green1', 'Blue1', 'Size')}
        cc = comp.FindTool('ColorCorrector1')
        if cc:
            d['CC'] = {k: cc.GetInput(k) for k in ('Hue1', 'Saturation1', 'WheelTintAngle1', 'WheelTintLength1')}
        ts = comp.FindTool('TimeSpeed1')
        if ts:
            d['Speed'] = ts.GetInput('Speed')
        fuera[item.GetName()] = d
    return fuera


# ------------------------------------------------------------------ paso 3: importar el .drb provisional
def importar_drb(resolve, avisar, ruta_drb, nombre_bin):
    """Importa el .drb en un bin propio y devuelve (bin, clips del Media Pool)."""
    p = resolve.GetProjectManager().GetCurrentProject()
    mp = p.GetMediaPool()
    raiz = mp.GetRootFolder()
    bin_ = mp.AddSubFolder(raiz, nombre_bin)
    mp.SetCurrentFolder(bin_)
    ok = mp.ImportFolderFromFile(ruta_drb)
    mp.SetCurrentFolder(raiz)
    clips = []

    def recorrer(f):
        for c in f.GetClipList() or []:
            clips.append(c)
        for s in f.GetSubFolderList() or []:
            recorrer(s)
    recorrer(bin_)
    avisar(f'importado {ok}: {len(clips)} clips')
    return bin_, clips, ok


def prueba_importar(resolve, avisar, ruta_drb, carpeta):
    p = resolve.GetProjectManager().GetCurrentProject()
    mp = p.GetMediaPool()
    bin_, clips, ok = importar_drb(resolve, avisar, ruta_drb, 'prueba importar ' + time.strftime('%H%M%S'))
    info = {'ok': ok, 'clips': [(c.GetName(), c.GetClipProperty('Type')) for c in clips]}
    tl = nuevo_timeline(p, 'prueba importar ' + time.strftime('%H%M%S'), 'v')
    pruebas = []
    for c in clips[:4]:
        nuevos = mp.AppendToTimeline([{'mediaPoolItem': c, 'startFrame': 0, 'endFrame': 59, 'trackIndex': 1,
                                       'mediaType': 1}])
        it = nuevos[0] if nuevos else None
        tp = primera_textplus(it) if it else None
        if tp is not None:
            tp.StyledText = 'Prueba ' + c.GetName()
        pruebas.append((c.GetName(), bool(it), tp.Name if tp else None))
    info['pruebas'] = pruebas
    items = tl.GetItemListInTrack('video', 1)
    info['fotos'] = fotos(resolve, p, tl, items, carpeta, 'imp', avisar, desfase=40)
    return info


# ------------------------------------------------------------------ paso 4: .drb DEFINITIVO exportado por Resolve
def exportar_nativos(resolve, avisar, carpeta_prov, carpeta_final, diseno, solo=None):
    """Para cada pack: importa el .drb provisional (con posiciones), comprueba que el Tilt llega a un timeline
    y exporta el bin con Folder.Export -> .drb hecho por Resolve."""
    with open(diseno, encoding='utf-8') as f:
        packs = json.load(f)
    p = resolve.GetProjectManager().GetCurrentProject()
    mp = p.GetMediaPool()
    raiz = mp.GetRootFolder()
    os.makedirs(carpeta_final, exist_ok=True)
    informe = {}
    for pk in packs:
        if solo and pk['archivo'] not in solo:
            continue
        w, h = FORMATOS[pk['formato']]
        nombre = pk['archivo']
        bin_ = mp.AddSubFolder(raiz, nombre)
        mp.SetCurrentFolder(bin_)
        ok = mp.ImportFolderFromFile(os.path.join(carpeta_prov, nombre + '.drb'))
        mp.SetCurrentFolder(raiz)
        clips = {}
        for sub in [bin_] + list(bin_.GetSubFolderList() or []):
            for c in sub.GetClipList() or []:
                clips[c.GetName()] = c
        tl = nuevo_timeline(p, nombre + ' · prueba ' + time.strftime('%H%M%S'), pk['formato'])
        errores = []
        for c in pk['clips']:
            mpi = clips.get(c['nombre'])
            if mpi is None:
                errores.append('falta ' + c['nombre'])
                continue
            nuevos = mp.AppendToTimeline([{'mediaPoolItem': mpi, 'startFrame': 0, 'endFrame': 59,
                                           'trackIndex': 1, 'mediaType': 1}])
            it = nuevos[0] if nuevos else None
            if not it:
                errores.append('no entra ' + c['nombre'])
                continue
            tilt = float(it.GetProperty('Tilt') or 0)
            esperado = c['pos'][1] * h
            if abs(tilt - esperado) > 1.0:
                errores.append(f'{c["nombre"]}: Tilt {tilt:.1f} != {esperado:.1f}')
        destino = os.path.join(carpeta_final, nombre + '.drb')
        if os.path.exists(destino):
            os.remove(destino)
        exp = bin_.Export(destino)
        informe[nombre] = {'importado': bool(ok), 'clips': len(clips), 'errores': errores,
                           'exportado': bool(exp) and os.path.exists(destino),
                           'bytes': os.path.getsize(destino) if os.path.exists(destino) else 0}
        avisar(f'{nombre}: {informe[nombre]}')
    return informe


# ------------------------------------------------------------------ paso 5: verificar cada pack en Resolve
def verificar_packs(resolve, avisar, carpeta_prov, carpeta_ver, diseno, solo=None):
    """Importa cada .drb, apila contexto/principal/complemento de cada set con su texto de muestra (fotograma
    por set) y comprueba que el Tilt de cada clip llega a la timeline. Devuelve el informe."""
    with open(diseno, encoding='utf-8') as f:
        packs = json.load(f)
    p = resolve.GetProjectManager().GetCurrentProject()
    mp = p.GetMediaPool()
    raiz = mp.GetRootFolder()
    os.makedirs(carpeta_ver, exist_ok=True)
    informe = {}
    for pk in packs:
        if solo and pk['archivo'] not in solo:
            continue
        w, h = FORMATOS[pk['formato']]
        nombre = pk['archivo']
        bin_ = mp.AddSubFolder(raiz, 'ver ' + nombre)
        mp.SetCurrentFolder(bin_)
        ok = mp.ImportFolderFromFile(os.path.join(carpeta_prov, nombre + '.drb'))
        mp.SetCurrentFolder(raiz)
        clips = {}

        def recorrer(fo):
            for c in fo.GetClipList() or []:
                clips[c.GetName()] = c
            for s in fo.GetSubFolderList() or []:
                recorrer(s)
        recorrer(bin_)
        tl = nuevo_timeline(p, nombre + ' · verificacion ' + time.strftime('%H%M%S'), pk['formato'])
        for _ in range(2):
            tl.AddTrack('video')
        por_set = {}
        for c in pk['clips']:
            por_set.setdefault(c['set'], []).append(c)
        errores, momentos = [], []
        for k, n in enumerate(sorted(por_set, key=lambda x: (x == 0, x))):
            inicio = None
            for pista, c in enumerate(por_set[n], 1):
                mpi = clips.get(c['nombre'])
                if mpi is None:
                    errores.append('falta ' + c['nombre'])
                    continue
                info = {'mediaPoolItem': mpi, 'startFrame': 0, 'endFrame': 59, 'trackIndex': pista, 'mediaType': 1}
                if inicio is not None:
                    info['recordFrame'] = inicio
                nuevos = mp.AppendToTimeline([info])
                it = nuevos[0] if nuevos else None
                if not it:
                    errores.append('no entra ' + c['nombre'])
                    continue
                if inicio is None:
                    inicio = it.GetStart()
                tp = primera_textplus(it)
                if tp is not None:
                    tp.StyledText = c['cfg']['texto']
                else:
                    errores.append('sin Text+ ' + c['nombre'])
                tilt = float(it.GetProperty('Tilt') or 0)
                esperado = c['pos'][1] * h
                if abs(tilt - esperado) > 1.0:
                    errores.append(f'{c["nombre"]}: Tilt {tilt:.1f} != {esperado:.1f}')
            if inicio is not None:
                momentos.append((n, inicio))
            # los sets siguientes empiezan tras este: el siguiente append va al final de la pista 1
        resolve.OpenPage('color')
        time.sleep(1.0)
        fotos_ = []
        for n, inicio in momentos:
            tl.SetCurrentTimecode(timecode(int(inicio + 45)))
            time.sleep(0.6)
            ruta = os.path.join(carpeta_ver, f'{nombre}__set{n}.png')
            p.ExportCurrentFrameAsStill(ruta)
            fotos_.append(ruta)
        resolve.OpenPage('edit')
        informe[nombre] = {'importado': bool(ok), 'clips': len(clips), 'errores': errores, 'fotos': len(fotos_)}
        avisar(f'{nombre}: {len(clips)} clips, {len(errores)} errores, {len(fotos_)} fotos')
    return informe
