# CineCaptions · By Cinema Productions
# 4_diseno/plantilla_base_cinema/taller_base.py — funciones que corren DENTRO de Resolve (por el MCP) para construir y comprobar la plantilla base nueva.
"""Taller de la plantilla BASE nueva (estructura arriba · principal · abajo · imagen, variantes 1..3 + simple).

Corre DENTRO de Resolve (MCP: run_script_unsafe) y reusa el taller de «Plantillas virales cinema»
(lanzar en un hilo, fotogramas, timelines). Nunca en un proyecto de un cliente: crea el suyo.
"""
import json
import os
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(AQUI), 'plantillas_virales'))
import resolve_taller as T      # noqa: E402

NOMBRE_PROYECTO = 'CineCaptions taller (borrable)'
FORMATOS = T.FORMATOS


def proyecto(resolve):
    pm = resolve.GetProjectManager()
    p = pm.GetCurrentProject()
    if p and p.GetName() == NOMBRE_PROYECTO:
        return p
    p = pm.LoadProject(NOMBRE_PROYECTO) or pm.CreateProject(NOMBRE_PROYECTO)
    if not p:
        raise RuntimeError('no pude abrir el proyecto de pruebas')
    return p


def textplus(item):
    comp = item.GetFusionCompByIndex(1)
    for _, t in comp.GetToolList().items():
        if t.ID == 'TextPlus':
            return t
    return None


def configurar(item, cfg):
    """Configura un clip que YA es un efecto de la sección Títulos (Luxe Slide / Luxe Shine): texto, tamaño en reposo
    (sizeCtrl.RestingSize), color y tipografía de su Text1. No crea Text+ ni composiciones: solo mueve lo que el efecto ofrece."""
    comp = item.GetFusionCompByIndex(1)
    t = comp.FindTool('Text1') or textplus(item)
    if t is None:
        raise RuntimeError('el clip no trae un Text1')
    if cfg.get('texto') is not None:
        t.SetInput('StyledText', cfg['texto'])
    if cfg.get('font'):
        t.SetInput('Font', cfg['font'])
    if cfg.get('style'):
        t.SetInput('Style', cfg['style'])
    if cfg.get('size') is not None:
        sc = comp.FindTool('sizeCtrl')
        if sc is not None:
            sc.SetInput('RestingSize', float(cfg['size']))
        else:
            t.SetInput('Size', float(cfg['size']))
    if cfg.get('color'):
        r, g, b = cfg['color']
        t.SetInput('Red1', float(r))
        t.SetInput('Green1', float(g))
        t.SetInput('Blue1', float(b))
    if cfg.get('tracking') is not None:
        t.SetInput('CharacterSpacing', float(cfg['tracking']))


def inspeccionar(resolve, avisar):
    """Qué trae cada efecto Luxe por dentro (herramientas y entradas del Text1)."""
    p = proyecto(resolve)
    resolve.OpenPage('edit')
    tl = T.nuevo_timeline(p, 'inspeccion luxe ' + time.strftime('%H%M%S'), 'v')
    salida = {}
    for preset in ('Luxe Slide', 'Luxe Shine'):
        avisar('inserto ' + preset)
        it = tl.InsertFusionTitleIntoTimeline(preset)
        info = {'item': bool(it)}
        if it:
            comp = it.GetFusionCompByIndex(1)
            info['tools'] = {str(k): (v.ID, v.Name) for k, v in comp.GetToolList().items()}
            t1 = comp.FindTool('Text1')
            if t1:
                info['Text1'] = {n: t1.GetInput(n) for n in ('Font', 'Style', 'Size', 'StyledText', 'Red1', 'Green1', 'Blue1',
                                                            'CharacterSpacing', 'LineSpacing')}
            sc = comp.FindTool('sizeCtrl')
            if sc:
                info['sizeCtrl'] = {'RestingSize': sc.GetInput('RestingSize')}
        salida[preset] = info
        avisar(preset + ' ok')
    return salida


def medir(resolve, avisar, carpeta, pruebas):
    """pruebas = [{formato, texto, font, style, size}] -> un fotograma de cada una (para medir lo que ocupa)."""
    p = proyecto(resolve)
    resolve.OpenPage('edit')
    salida = {}
    for formato in ('v', 'h'):
        lista = [x for x in pruebas if x['formato'] == formato]
        if not lista:
            continue
        tl = T.nuevo_timeline(p, f'medida {formato} {time.strftime("%H%M%S")}', formato)
        items = []
        for prueba in lista:
            item = tl.InsertFusionTitleIntoTimeline('Text+')
            configurar(item, prueba)
            items.append(item)
            avisar(f'{formato} {prueba["font"]} {prueba["size"]}')
        salida[formato] = fotos_aisladas(resolve, p, tl, items, carpeta, f'med_{formato}', avisar)
    return salida


def fotos_aisladas(resolve, p, tl, items, carpeta, prefijo, avisar, desfase=30):
    """Un fotograma de cada clip (los Text+ nuevos caen uno tras otro en la pista 1). Se salta a otro fotograma antes
    de volver al bueno: si no, el visor reusa el cuadro anterior y el still sale de otro clip."""
    os.makedirs(carpeta, exist_ok=True)
    resolve.OpenPage('color')
    time.sleep(1.0)
    rutas = []
    for k, item in enumerate(items):
        inicio = int(item.GetStart())
        tl.SetCurrentTimecode(T.timecode(inicio + desfase + 12))
        time.sleep(0.4)
        tl.SetCurrentTimecode(T.timecode(inicio + desfase))
        time.sleep(0.8)
        ruta = os.path.join(carpeta, f'{prefijo}_{k:02d}.png')
        p.ExportCurrentFrameAsStill(ruta)
        rutas.append(ruta)
        avisar(f'foto {ruta}')
    resolve.OpenPage('edit')
    return rutas


def construir(resolve, avisar, diseno, carpeta):
    """diseno = lista de {archivo, formato, clips: [{nombre, cfg, pos}]} -> un timeline por formato y su .drt."""
    with open(diseno, encoding='utf-8') as f:
        packs = json.load(f)
    p = proyecto(resolve)
    resolve.OpenPage('edit')
    os.makedirs(carpeta, exist_ok=True)
    hechos = {}
    for pk in packs:
        w, h = FORMATOS[pk['formato']]
        tl = T.nuevo_timeline(p, pk['archivo'] + ' · diseño ' + time.strftime('%H%M%S'), pk['formato'])
        n = 0
        for clip in pk['clips']:
            item = tl.InsertFusionTitleIntoTimeline(clip['cfg']['preset'])      # Luxe Slide / Luxe Shine, nada más
            if not item:
                raise RuntimeError(f'no se insertó el efecto {clip["cfg"]["preset"]} de {clip["nombre"]}')
            configurar(item, clip['cfg'])
            item.SetName(clip['nombre'])
            x, y, zx, zy = clip['pos']
            item.SetProperties({'Pan': x * w, 'Tilt': y * h, 'ZoomX': zx, 'ZoomY': zy})
            n += 1
        drt = os.path.join(carpeta, pk['archivo'] + '.drt')
        if os.path.exists(drt):
            os.remove(drt)
        ok = tl.Export(drt, resolve.EXPORT_DRT, resolve.EXPORT_NONE)
        hechos[pk['archivo']] = {'drt': bool(ok) and os.path.exists(drt), 'clips': n, 'timeline': tl.GetName()}
        avisar(f'{pk["archivo"]}: {n} clips, drt {hechos[pk["archivo"]]["drt"]}')
    return hechos


def verificar(resolve, avisar, carpeta_prov, carpeta_ver, diseno, con_fotos=False):
    """Importa cada .drb provisional, apila arriba/principal/abajo/imagen de cada variante con su texto y saca
    un fotograma por variante. Comprueba que el Pan/Tilt/Zoom de cada clip llega a la timeline."""
    with open(diseno, encoding='utf-8') as f:
        packs = json.load(f)
    p = proyecto(resolve)
    mp = p.GetMediaPool()
    raiz = mp.GetRootFolder()
    os.makedirs(carpeta_ver, exist_ok=True)
    informe = {}
    for pk in packs:
        w, h = FORMATOS[pk['formato']]
        nombre = pk['archivo']
        bin_ = mp.AddSubFolder(raiz, 'ver ' + nombre + ' ' + time.strftime('%H%M%S'))
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
        tl = T.nuevo_timeline(p, nombre + ' · verificacion ' + time.strftime('%H%M%S'), pk['formato'])
        for _ in range(4):
            tl.AddTrack('video')
        por_set = {}
        for c in pk['clips']:
            por_set.setdefault(c['set'], []).append(c)
        errores, momentos = [], []
        for n in sorted(por_set, key=lambda x: (x == 0, x)):
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
                tp = textplus(it)
                if tp is None:
                    errores.append('sin Text+ ' + c['nombre'])
                else:
                    tp.SetInput('StyledText', c['cfg']['texto'])
                tilt = float(it.GetProperty('Tilt') or 0)
                esperado = c['pos'][1] * h
                if abs(tilt - esperado) > 1.0:
                    errores.append(f'{c["nombre"]}: Tilt {tilt:.1f} != {esperado:.1f}')
                pan = float(it.GetProperty('Pan') or 0)
                if abs(pan - c['pos'][0] * w) > 1.0:
                    errores.append(f'{c["nombre"]}: Pan {pan:.1f} != {c["pos"][0] * w:.1f}')
                zoom = float(it.GetProperty('ZoomX') or 1)
                if abs(zoom - c['pos'][2]) > 0.01:
                    errores.append(f'{c["nombre"]}: Zoom {zoom:.2f} != {c["pos"][2]:.2f}')
            if inicio is not None:
                momentos.append((n, inicio))
        fotos_ = []
        if con_fotos:           # las capturas tumbaron a Resolve una vez: solo si se piden y despacio
            resolve.OpenPage('color')
            time.sleep(2.0)
            for n, inicio in momentos:
                # el visor va con 1-2 cuadros de retraso: se pasa por otro cuadro y se espera antes de exportar
                tl.SetCurrentTimecode(T.timecode(int(inicio + 95)))
                time.sleep(2.0)
                tl.SetCurrentTimecode(T.timecode(int(inicio + 75)))
                time.sleep(3.0)
                ruta = os.path.join(carpeta_ver, f'{nombre}__set{n}.png')
                p.ExportCurrentFrameAsStill(ruta)
                time.sleep(1.0)
                fotos_.append(ruta)
            resolve.OpenPage('edit')
        informe[nombre] = {'importado': bool(ok), 'clips': len(clips), 'errores': errores, 'fotos': len(fotos_)}
        avisar(f'{nombre}: {len(clips)} clips, {len(errores)} errores, {len(fotos_)} fotos')
    return informe


# ------------------------------------------------------------------ la estructura visual: los bloques uno encima del otro
ORDEN_PISTAS = ('principal', 'arriba', 'abajo', 'imagen')       # V1 · V2 · V3 · V4 (el orden de la jerarquía)
DURACION_SET = 150


def apilar(resolve, avisar, ruta_drb, ruta_drt, formato, diseno):
    """Un timeline con los bloques de cada variante UNO ENCIMA DEL OTRO (V1 principal · V2 arriba · V3 abajo · V4 imagen),
    una variante tras otra, y 'simple' al final. Es el .drt del pack: al abrirlo en Resolve se ve la estructura entera."""
    with open(diseno, encoding='utf-8') as f:
        packs = json.load(f)
    pk = next(x for x in packs if x['formato'] == formato)
    p = proyecto(resolve)
    mp = p.GetMediaPool()
    raiz = mp.GetRootFolder()
    resolve.OpenPage('edit')
    bin_ = mp.AddSubFolder(raiz, 'apilar ' + pk['archivo'] + ' ' + time.strftime('%H%M%S'))
    mp.SetCurrentFolder(bin_)
    mp.ImportFolderFromFile(ruta_drb)
    mp.SetCurrentFolder(raiz)
    clips = {}

    def recorrer(fo):
        for c in fo.GetClipList() or []:
            clips[c.GetName()] = c
        for s in fo.GetSubFolderList() or []:
            recorrer(s)
    recorrer(bin_)
    tl = T.nuevo_timeline(p, pk['archivo'] + ' · estructura ' + time.strftime('%H%M%S'), formato)
    for _ in range(3):
        tl.AddTrack('video')
    inicio = int(tl.GetStartFrame())
    puestos = 0
    for k, n in enumerate((1, 2, 3)):
        sufijo = '' if n == 1 else f' {n}'
        for pista, rol in enumerate(ORDEN_PISTAS, 1):
            mpi = clips.get(rol + sufijo)
            if mpi is None:
                raise RuntimeError('falta ' + rol + sufijo)
            nuevos = mp.AppendToTimeline([{'mediaPoolItem': mpi, 'startFrame': 0, 'endFrame': DURACION_SET - 1,
                                           'trackIndex': pista, 'recordFrame': inicio + k * DURACION_SET, 'mediaType': 1}])
            if not nuevos:
                raise RuntimeError('no entra ' + rol + sufijo)
            puestos += 1
    nuevos = mp.AppendToTimeline([{'mediaPoolItem': clips['simple'], 'startFrame': 0, 'endFrame': DURACION_SET - 1,
                                   'trackIndex': 1, 'recordFrame': inicio + 3 * DURACION_SET, 'mediaType': 1}])
    puestos += 1 if nuevos else 0
    if os.path.exists(ruta_drt):
        os.remove(ruta_drt)
    ok = tl.Export(ruta_drt, resolve.EXPORT_DRT, resolve.EXPORT_NONE)
    informe = {'drt': bool(ok) and os.path.exists(ruta_drt), 'clips': puestos, 'timeline': tl.GetName()}
    avisar(f'{pk["archivo"]}: {informe}')
    return informe


def apilar_todo(resolve, avisar, carpeta_prov, carpeta_salida, diseno):
    os.makedirs(carpeta_salida, exist_ok=True)
    salida = {}
    with open(diseno, encoding='utf-8') as f:
        packs = json.load(f)
    for pk in packs:
        salida[pk['archivo']] = apilar(resolve, avisar, os.path.join(carpeta_prov, pk['archivo'] + '.drb'),
                                       os.path.join(carpeta_salida, pk['archivo'] + '.drt'), pk['formato'], diseno)
    return salida
