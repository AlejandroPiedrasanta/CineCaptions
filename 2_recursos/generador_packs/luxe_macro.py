# CineCaptions · By Cinema Productions
# 2_recursos/generador_packs/luxe_macro.py — pone los macros REALES «Luxe Shine» (principal) y «Luxe Slide» (el resto) del Luxe Title Pack en cada clip, con la tipografía, el color y la posición de cada variante.
"""
Los macros del Luxe Title Pack viajan DENTRO de la comp: se toman tal cual de un .drb del pack
(luxe_shine_*.lua / luxe_slide_*.lua + su cabecera, extraídos una vez con extraer_base) y se le cambian solo los valores:

    Text1.Font / Style / color / texto        (la herramienta Text+ que hay dentro del macro)
    sizeCtrl.RestingSize                      (tamaño en reposo)
    positionCtrl.RestingCenter + Text1.Center (posición)

La app escribe el texto en el primer Text+ que encuentra (Text1), igual que con los packs Luxe de antes.
"""
import os
import re

AQUI = os.path.dirname(os.path.abspath(__file__))
# v5.8 (pedido: «todos los textos plus deben ser del paquete Luxe Title Pack, sin excepción»): además del macro Luxe Shine ahora viaja
# el Luxe Slide REAL (sacado del clip «arriba» de «Base titulos dinamicos vertical.drb»). Antes contexto/complemento/base eran una
# imitación hecha con Text+ sueltos que solo se llamaba «Luxe Slide».
ARCHIVOS = {'shine': ('luxe_shine_base.lua', 'luxe_shine_cabecera.txt'), 'slide': ('luxe_slide_base.lua', 'luxe_slide_cabecera.txt')}
BASE = os.path.join(AQUI, ARCHIVOS['shine'][0])
CABECERA = os.path.join(AQUI, ARCHIVOS['shine'][1])


def _rutas(tipo):
    base, cabecera = ARCHIVOS[tipo]
    return os.path.join(AQUI, base), os.path.join(AQUI, cabecera)


def extraer_base(drb, clip='principal', tipo='shine'):
    """Guarda el macro y la cabecera de la comp de ese clip del .drb (una sola vez). tipo: 'shine' | 'slide'."""
    BASE, CABECERA = _rutas(tipo)
    import binascii
    import struct
    import zipfile
    import zlib
    z = zipfile.ZipFile(drb)
    ruta = next(n for n in z.namelist() if n.endswith('MpFolder.xml') and '/Master/0' in '/' + n)
    xml = z.read(ruta).decode('utf-8')
    for m in re.finditer(r'<Sm2MpGenerator.*?</Sm2MpGenerator>', xml, re.S):
        if re.search(r'<Name>' + re.escape(clip) + '</Name>', m.group(0)):
            h = re.search(r'<CompositionBA>([0-9a-f]*)</CompositionBA>', m.group(0)).group(1)
            cab = zlib.decompress(binascii.unhexlify(h)[4:])
            i = cab.index(b'Composition {')
            n = struct.unpack('>I', cab[i - 4:i])[0]
            datos = cab[i:i + n]
            z0 = datos.index(b'\x00')
            cabecera = datos[:z0].decode('utf-8', 'replace')
            tools = zlib.decompress(datos[z0 + 5:]).decode('utf-8', 'replace')
            open(BASE, 'w', encoding='utf-8').write(tools)
            open(CABECERA, 'w', encoding='utf-8').write(cabecera)
            return len(tools), len(cabecera)
    raise SystemExit('no encuentro el clip ' + clip)


def _n(v):
    return f'{v:.6g}'


def comp_luxe_shine(familia, estilo, tam, color, y, texto='Texto', mayus=True, esp=0.985, ajustar=True, anim=None):
    """Texto de la comp completa (cabecera + Tools) con el macro Luxe Shine ya personalizado."""
    return comp_luxe('shine', familia, estilo, tam, color, y, texto, mayus, esp, ajustar, anim)


def comp_luxe_slide(familia, estilo, tam, color, y, texto='Texto', mayus=True, esp=0.985, ajustar=True, anim=None):
    """Lo mismo con el macro Luxe Slide (contexto, complemento)."""
    return comp_luxe('slide', familia, estilo, tam, color, y, texto, mayus, esp, ajustar, anim)


def comp_luxe(tipo, familia, estilo, tam, color, y, texto='Texto', mayus=True, esp=0.985, ajustar=True, anim=None):
    """Texto de la comp completa (cabecera + Tools) con el macro del Luxe Title Pack (tipo 'shine' o 'slide') ya personalizado.
    ajustar=False deja el tamaño en reposo como un valor suelto (sin la expresión que encoge el texto largo): así se puede cambiar desde fuera
    con sizeCtrl.RestingSize (lo hace la guía «Crea tu estilo» en Resolve)."""
    ruta_base, ruta_cab = _rutas(tipo)
    tools = open(ruta_base, encoding='utf-8').read().replace(chr(0), '').rstrip()
    cabecera = open(ruta_cab, encoding='utf-8').read()
    i = tools.index('Text1 = TextPlus {')
    j = tools.index('glow1 = Glow', i)
    t1 = tools[i:j]
    t1 = re.sub(r'Font = Input \{ Value = "[^"]*", \}', f'Font = Input {{ Value = "{familia}", }}', t1, count=1)
    t1 = re.sub(r'Style = Input \{ Value = "[^"]*", \}', f'Style = Input {{ Value = "{estilo}", }}', t1, count=1)
    # el texto llega a un Text+ de primer nivel llamado «Template» (es lo que busca el script); el del macro lo lee de ahi
    base = 'tostring(Template.StyledText.Value)'
    if mayus:
        import generar_comps as g
        base = '(' + base + ':upper()' + ''.join(f':gsub("{x}","{y_}")' for x, y_ in g.MAYUS_ACENTOS) + ')'
    barra = chr(92)
    expr = base.replace(barra, barra * 2).replace('"', barra + '"')
    t1 = re.sub(r'StyledText = Input \{ Value = "[^"]*", \}', lambda m: f'StyledText = Input {{ Value = "", Expression = "{expr}", }}', t1, count=1)
    t1 = re.sub(r'CharacterSpacing = Input \{ Value = [^,]*,', f'CharacterSpacing = Input {{ Value = {_n(esp)},', t1, count=1)
    t1 = re.sub(r'(Center = Input \{ Value = \{ )[^}]*( \},)', lambda m: f'{m.group(1)}0.5, {_n(y)}{m.group(2)}', t1, count=1)
    colores = f'Red1 = Input {{ Value = {_n(color[0])}, }}, Green1 = Input {{ Value = {_n(color[1])}, }}, Blue1 = Input {{ Value = {_n(color[2])}, }}, '
    t1 = t1.replace('UseFrameFormatSettings = Input { Value = 1, }, ', 'UseFrameFormatSettings = Input { Value = 1, }, ' + colores, 1)
    tools = tools[:i] + t1 + tools[j:]
    # el tamaño se reduce solo si el texto (varias palabras principales) no cabe en el 90 % del ancho
    # ancho aproximado por numero de letras (el DataWindow de un Text+ suelto no llega dentro del macro): 0,80 em por letra
    ancho = f'(tostring(Template.StyledText.Value):len() * 0.80 * {_n(tam)} * 640 / 1080)'
    ajuste = f'{_n(tam)}*math.min(1, 0.86/math.max(0.0001, {ancho}))'.replace(chr(34), chr(92) + chr(34))
    tools = re.sub(r'(sizeCtrl = AlphaDivide \{.*?RestingSize = Input \{ Value = )[^,]*(, \})',
                   lambda m: m.group(1) + _n(tam) + ((', Expression = "' + ajuste + '"') if ajustar else '') + m.group(2), tools, count=1, flags=re.S)
    marca = 'positionCtrl = AlphaDivide { CtrlWShown = false, NameSet = true, Inputs = { '
    if marca not in tools:
        raise SystemExit('el macro no trae positionCtrl con la forma esperada')
    tools = tools.replace(marca, marca + f'RestingCenter = Input {{ Value = {{ 0.5, {_n(y)} }}, }}, ', 1)
    import generar_comps as g
    plantilla = g._texto_plus('Template', 0, 0, (familia, estilo), valor=texto, tam=tam, color=color, centro=(0.5, y))
    tools = '{ ' + plantilla.strip() + ' ' + tools.lstrip()[1:].lstrip()
    if anim:
        # v5.9: duración de la entrada y la salida del macro (AnimEngine.InLength / OutLength, en segundos; de fábrica 0,7 s cada una: una palabra que dura menos
        # de 1,4 s ni se ve, porque el macro se esconde si entrada + salida no caben en el clip). Los captions rápidos usan ~0,12 s.
        entrada, salida = anim
        tools = re.sub(r'InLength = Input \{ Value = [0-9.eE+-]+, \}', f'InLength = Input {{ Value = {_n(entrada)}, }}', tools, count=1)
        tools = re.sub(r'OutLength = Input \{ Value = [0-9.eE+-]+, \}', f'OutLength = Input {{ Value = {_n(salida)}, }}', tools, count=1)
    cab = re.sub(r',?\s*Compressed = true,?\s*\}\s*$', ' }', cabecera.rstrip())
    return cab[:-1].rstrip().rstrip(',') + ',\n\tTools = ' + tools + '\n}'
