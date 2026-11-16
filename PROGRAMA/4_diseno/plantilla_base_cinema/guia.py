# CineCaptions · By Cinema Productions
# 4_diseno/plantilla_base_cinema/guia.py — construye DENTRO de Resolve el timeline-guía «Crea tu estilo» (.drt): cómo se arma un pack .drb.
"""El timeline-guía que abre el botón «Crea tu estilo» de CineCaptions (Proyecto → Pack de estilos).

Seis pantallas de 6 s, 1920x1080, hechas SOLO con el efecto «Luxe Slide» (nada de Text+ ni composiciones propias): las
instrucciones van en texto y los colores marcan los roles (cada rol tiene el suyo, en el texto y en la etiqueta de color del clip):

    1 · Portada            2 · El orden de los nombres (uno encima del otro: arriba / principal / abajo / imagen / simple)
    3 · Variantes (máx. 3) 4 · Diseña cada bloque      5 · Expórtalo y úsalo
    6 · Tu turno: los cuatro bloques YA NOMBRADOS y colocados, para editarlos y exportar el bin.

Se apoya en los clips de la plantilla base nueva (provisionales/Base titulos dinamicos Horizontal.drb): cada texto es una
copia de uno de esos Text+, así que la pantalla 6 trae exactamente los nombres y las posiciones que CineCaptions espera.
Corre en Resolve (MCP: run_script_unsafe) dentro de resolve_taller.lanzar.
"""
import os
import time

import taller_base as TB

T = TB.T
FPS = 30
DURACION = 6 * FPS
ANCHO, ALTO = 1920, 1080

# un color por rol: el del texto y el de la etiqueta del clip en Resolve
ROLES = {
    'arriba': ((0.45, 0.72, 1.00), 'Blue'),
    'principal': ((1.00, 0.78, 0.10), 'Orange'),
    'abajo': ((0.74, 0.55, 1.00), 'Purple'),
    'imagen': ((0.30, 0.90, 0.52), 'Green'),
    'simple': ((0.78, 0.80, 0.86), 'Beige'),
}
BLANCO = (1.0, 1.0, 1.0)
SUAVE = (0.80, 0.84, 0.92)

# tamaños del Luxe Slide en 1920x1080 (RestingSize): a 0.09, «de verdad» mide ~400 px; ~0.0053 de tamaño por letra Bold
GRANDE, TITULO, NOMBRE, CUERPO, PIE = 0.125, 0.066, 0.052, 0.040, 0.032


def _linea(texto, y, size, color, font='Poppins', style=None, rol=None):
    """Todo es Luxe Slide en Poppins: Bold para títulos y nombres de rol, Regular para el cuerpo."""
    if font == 'Inter' or style is None:
        style = 'Bold' if (font == 'Inter' or size >= NOMBRE * 0.85 or rol) else 'Regular'
    return dict(texto=texto, y=y, size=size, color=color, font='Poppins', style=style, rol=rol)


def pantallas():
    """Cada pantalla = lista de líneas (texto, y como fracción del alto con Y arriba, tamaño, color, rol)."""
    p = []
    # 1 · portada
    p.append([
        _linea('CREA TU ESTILO', 0.10, GRANDE, BLANCO, 'Inter', 'Black'),
        _linea('Así se arma un pack (.drb) para CineCaptions', -0.06, CUERPO * 1.15, ROLES['principal'][0]),
        _linea('Sigue las 5 pantallas  ·  al final tienes los bloques listos para editar', -0.16, PIE * 1.1, SUAVE),
    ])
    # 2 · la jerarquía
    p.append([
        _linea('1 · EL ORDEN DE LOS NOMBRES', 0.38, TITULO, BLANCO, 'Inter', 'Black'),
        _linea('Un .drb funciona si sus títulos se llaman EXACTAMENTE así, uno encima del otro:', 0.28, CUERPO, SUAVE),
        _linea('arriba   ·   contexto: 1–2 palabras pequeñas', 0.14, NOMBRE, ROLES['arriba'][0], rol='arriba'),
        _linea('principal   ·   la palabra clave, GRANDE', 0.03, NOMBRE, ROLES['principal'][0], rol='principal'),
        _linea('abajo   ·   complemento: 1–2 palabras medianas', -0.08, NOMBRE, ROLES['abajo'][0], rol='abajo'),
        _linea('imagen   ·   el icono o la imagen (opcional), DEBAJO del texto', -0.19, NOMBRE, ROLES['imagen'][0], rol='imagen'),
        _linea('simple   ·   una sola línea para las palabras sueltas (opcional)', -0.30, NOMBRE * 0.85, ROLES['simple'][0], rol='simple'),
        _linea('En el timeline van en este orden:  V1 principal  ·  V2 arriba  ·  V3 abajo  ·  V4 imagen', -0.40, PIE * 1.1, BLANCO),
        _linea('Da igual mayúsculas o minúsculas  ·  nada más en el nombre', -0.46, PIE * 0.9, SUAVE),
    ])
    # 3 · variantes
    p.append([
        _linea('2 · VARIANTES: MÁXIMO 3', 0.38, TITULO, BLANCO, 'Inter', 'Black'),
        _linea('La misma lógica: solo agregas 2 o 3 al final del nombre (la 1 va sin número).', 0.28, CUERPO, SUAVE),
        _linea('arriba   ·   arriba 2   ·   arriba 3', 0.14, NOMBRE, ROLES['arriba'][0], rol='arriba'),
        _linea('principal   ·   principal 2   ·   principal 3', 0.03, NOMBRE, ROLES['principal'][0], rol='principal'),
        _linea('abajo   ·   abajo 2   ·   abajo 3', -0.08, NOMBRE, ROLES['abajo'][0], rol='abajo'),
        _linea('imagen   ·   imagen 2   ·   imagen 3', -0.19, NOMBRE, ROLES['imagen'][0], rol='imagen'),
        _linea('Un set necesita arriba + principal + abajo (imagen es opcional). CineCaptions alterna los sets bloque a bloque.',
               -0.34, PIE, SUAVE),
    ])
    # 4 · diseñar
    p.append([
        _linea('3 · DISEÑA CADA BLOQUE', 0.38, TITULO, BLANCO, 'Inter', 'Black'),
        _linea('Usa SOLO los efectos de Títulos de Joel Van Beek: Luxe Shine para el principal, Luxe Slide para el resto.', 0.18, CUERPO * 1.1, BLANCO),
        _linea('Resalta con negrita poniendo el Luxe Slide en Poppins Bold (Regular para el resto).', 0.06, CUERPO * 1.1, BLANCO),
        _linea('Colócalos donde quieras (Pan / Tilt). «imagen» marca DÓNDE va el icono o la imagen y su tamaño (Zoom).', -0.06, CUERPO * 1.1,
               ROLES['imagen'][0], rol='imagen'),
        _linea('¿Tu pack no trae «imagen»? CineCaptions pone el emoji debajo del texto.', -0.18, CUERPO * 1.1, SUAVE),
    ])
    # 5 · exportar
    p.append([
        _linea('4 · EXPÓRTALO Y ÚSALO', 0.38, TITULO, BLANCO, 'Inter', 'Black'),
        _linea('1.  Arrastra tus títulos al Media Pool, dentro de un bin.', 0.18, CUERPO * 1.1, BLANCO),
        _linea('2.  Clic derecho sobre el bin  >  Exportar bandeja… (.drb).', 0.06, CUERPO * 1.1, BLANCO),
        _linea('3.  En CineCaptions: Proyecto  >  Pack de estilos  >  Añadir plantilla.', -0.06, CUERPO * 1.1, BLANCO),
        _linea('4.  Elígelo y pulsa GO.', -0.18, CUERPO * 1.1, ROLES['principal'][0]),
    ])
    return p


def construir_guia(resolve, avisar, drb_horizontal, salida_drt):
    p = TB.proyecto(resolve)
    mp = p.GetMediaPool()
    raiz = mp.GetRootFolder()
    resolve.OpenPage('edit')
    bin_ = mp.AddSubFolder(raiz, 'guia base ' + time.strftime('%H%M%S'))
    mp.SetCurrentFolder(bin_)
    mp.ImportFolderFromFile(drb_horizontal)
    mp.SetCurrentFolder(raiz)
    clips = {}

    def recorrer(fo):
        for c in fo.GetClipList() or []:
            clips[c.GetName().strip().lower()] = c
        for s in fo.GetSubFolderList() or []:
            recorrer(s)
    recorrer(bin_)
    for esperado in ('principal', 'arriba', 'abajo', 'imagen', 'simple'):
        if esperado not in clips:
            raise RuntimeError('falta en la plantilla base: ' + esperado)
    base = clips['simple']

    tl = T.nuevo_timeline(p, 'GUÍA · Crea tu estilo ' + time.strftime('%H%M%S'), 'h')
    for _ in range(11):
        tl.AddTrack('video')
    inicio = int(tl.GetStartFrame())
    colocados = 0

    def poner(mpi, pista, desde, linea, nombre_clip=None, clip_color=None):
        nonlocal colocados
        info = {'mediaPoolItem': mpi, 'startFrame': 0, 'endFrame': DURACION - 1, 'trackIndex': pista,
                'recordFrame': desde, 'mediaType': 1}
        nuevos = mp.AppendToTimeline([info])
        it = nuevos[0] if nuevos else None
        if not it:
            raise RuntimeError('no entra el clip de la línea: ' + linea['texto'][:30])
        TB.configurar(it, dict(texto=linea['texto'], font=linea['font'], style=linea['style'], size=linea['size'],
                               color=linea['color'], tracking=1.04))
        it.SetProperty('Pan', 0.0)
        it.SetProperty('Tilt', linea['y'] * ALTO)
        it.SetProperty('ZoomX', 1.0)
        it.SetProperty('ZoomY', 1.0)
        if clip_color:
            it.SetClipColor(clip_color)
        colocados += 1
        return it

    # pantallas 1..5: instrucciones (copias del Text+ «simple»; la etiqueta de color marca el rol de cada línea)
    for k, lineas in enumerate(pantallas()):
        desde = inicio + k * DURACION
        for pista, linea in enumerate(lineas, 1):
            color = ROLES[linea['rol']][1] if linea['rol'] else None
            poner(base, pista, desde, linea, clip_color=color)
        avisar(f'pantalla {k + 1}: {len(lineas)} líneas')

    # pantalla 6: los bloques de verdad (los clips nombrados de la plantilla, en su sitio) para editar y exportar
    desde = inicio + 5 * DURACION
    poner(base, 1, desde, _linea('5 · TU TURNO: edita estos bloques y exporta el bin', 0.40, TITULO * 0.8, BLANCO,
                                 'Inter', 'Black'))
    poner(base, 2, desde, _linea('Cámbiales la tipografía, el color o la animación. NO les cambies el nombre ni el orden.',
                                 0.33, PIE, SUAVE))
    reales = [('arriba', 'arriba'), ('principal', 'PRINCIPAL'), ('abajo', 'abajo'), ('imagen', '●')]
    for pista, (nombre, texto) in enumerate(reales, 3):
        mpi = clips[nombre]
        info = {'mediaPoolItem': mpi, 'startFrame': 0, 'endFrame': DURACION - 1, 'trackIndex': pista,
                'recordFrame': desde, 'mediaType': 1}
        nuevos = mp.AppendToTimeline([info])
        it = nuevos[0] if nuevos else None
        if not it:
            raise RuntimeError('no entra el bloque ' + nombre)
        tp = TB.textplus(it)
        tp.SetInput('StyledText', texto)
        it.SetClipColor(ROLES[nombre][1])
        colocados += 1
    avisar('pantalla 6: los 4 bloques nombrados')

    if os.path.exists(salida_drt):
        os.remove(salida_drt)
    ok = tl.Export(salida_drt, resolve.EXPORT_DRT, resolve.EXPORT_NONE)
    return {'drt': bool(ok) and os.path.exists(salida_drt), 'clips': colocados, 'timeline': tl.GetName()}


def fotos_guia(resolve, avisar, carpeta):
    """Una captura de cada pantalla de la guía (control de calidad). Despacio: el visor va con retraso."""
    p = TB.proyecto(resolve)
    tl = None
    for i in range(1, p.GetTimelineCount() + 1):
        t = p.GetTimelineByIndex(i)
        if t.GetName().startswith('GUÍA'):
            tl = t
    p.SetCurrentTimeline(tl)
    inicio = int(tl.GetStartFrame())
    os.makedirs(carpeta, exist_ok=True)
    resolve.OpenPage('color')
    time.sleep(2.0)
    rutas = []
    for k in range(6):
        tl.SetCurrentTimecode(T.timecode(inicio + k * DURACION + 120))
        time.sleep(2.0)
        tl.SetCurrentTimecode(T.timecode(inicio + k * DURACION + 80))
        time.sleep(3.0)
        ruta = os.path.join(carpeta, f'guia_{k + 1}.png')
        p.ExportCurrentFrameAsStill(ruta)
        time.sleep(1.0)
        rutas.append(ruta)
        avisar(ruta)
    resolve.OpenPage('edit')
    return rutas
