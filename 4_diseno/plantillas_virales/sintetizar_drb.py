# CineCaptions · By Cinema Productions
# 4_diseno/plantillas_virales/sintetizar_drb.py — arma un .drb (bin de Text+) a partir de un .drt, con la posición de cada clip.
"""Monta un .drb PROVISIONAL a partir de un .drt exportado por Resolve: cada clip del timeline (su
CompositionTable con la comp de Fusion, tal cual) pasa a ser un Sm2MpGenerator del bin, como los de los .drb
hechos a mano. Solo sirve para que Resolve lo importe y cree los Text+ en el Media Pool: el .drb DEFINITIVO
lo exporta Resolve después (Folder.Export)."""
import binascii
import pathlib
import re
import struct
import sys
import uuid
import zipfile
from compression import zstd

RAIZ = pathlib.Path(__file__).resolve().parent.parent.parent      # la carpeta CineCaptions
REF = RAIZ / '2_recursos' / 'plantillas_incluidas' / 'Titulos dinamicos II superior' / 'Vertical superior 2.drb'
_CLIP = re.compile(r'<Sm2TiVideoClip DbId="[^"]+">.*?</Sm2TiVideoClip>', re.S)


def varint(n):
    out = b''
    while True:
        b = n & 0x7F
        n >>= 7
        if n:
            out += bytes([b | 0x80])
        else:
            return out + bytes([b])


def leer_varint(d, i):
    n = s = 0
    while True:
        b = d[i]
        n |= (b & 0x7F) << s
        i += 1
        if not b & 0x80:
            return n, i
        s += 7


def cadenas(d, fuera=None, prof=0):
    """Todas las cadenas UTF-8 legibles de un protobuf (recursivo)."""
    fuera = [] if fuera is None else fuera
    i = 0
    try:
        while i < len(d):
            clave, i = leer_varint(d, i)
            tipo = clave & 7
            if tipo == 0:
                _, i = leer_varint(d, i)
            elif tipo == 1:
                i += 8
            elif tipo == 5:
                i += 4
            elif tipo == 2:
                largo, i = leer_varint(d, i)
                trozo = d[i:i + largo]
                i += largo
                try:
                    s = trozo.decode('utf-8')
                    if s.isprintable() and len(s) >= 2:
                        fuera.append(s)
                except UnicodeDecodeError:
                    pass
                if prof < 4:
                    cadenas(trozo, fuera, prof + 1)
            else:
                return fuera
    except IndexError:
        pass
    return fuera


def abrir_blob(hexa):
    b = binascii.unhexlify(hexa)
    cuerpo = b[8:]
    if cuerpo[:1] == b'\x81':
        return zstd.decompress(cuerpo[1:])
    return cuerpo[1:]


def plantilla_de(fields_hex):
    """(nombre, ruta) de la plantilla de Fusion del clip, leídos de su FieldsBlob."""
    ss = cadenas(abrir_blob(fields_hex))
    for s in ss:
        for t in ss:
            if t != s and t.endswith('/' + s):
                return s, t
    return None, None


def blob_generador(nombre, duracion, plantilla, ruta, fps=30.0):
    nb = nombre.encode('utf-8')
    interno = b'\x12' + varint(len(nb)) + nb + b'\x30\x04'
    pb = (b'\x0a' + varint(len(interno)) + interno
          + b'\x12\x0cFusion Title'
          + b'\x1a\x09\x09' + struct.pack('<d', fps)
          + b'\x28' + varint(int(duracion)))
    if plantilla:
        pt, pr = plantilla.encode('utf-8'), ruta.encode('utf-8')
        pb += b'\x32' + varint(len(pt)) + pt + b'\x3a' + varint(len(pr)) + pr
    carga = b'\x80' + pb
    return (struct.pack('>II', 2, len(carga)) + carga).hex()


# la posición de página Edición de un clip del Media Pool (Sm2MpItemLockableBlob del project.xml), copiada
# de un clip del .drb de referencia con Pan 0 y Zoom 1; solo cambia el Tilt (fracción del alto, Y arriba)
_POS_ANTES = bytes.fromhex('0a5d080438004a004a004a004a004a0f08291a0b0a0911')
_POS_DESPUES = bytes.fromhex('4a004a004a004a004a004a004a004a30083410001a0b0a09110000000000000000220b0a09110000000000000000'
                             '299a9999999999b9bf319a9999999999b93f')


def _campo(id_, valor, defecto):
    """Un campo del bloque de posición (40 Pan, 41 Tilt, 42 ZoomX, 43 ZoomY); con su valor por defecto va vacío."""
    if abs(float(valor) - defecto) < 1e-12:
        return b'\x4a\x00'
    return b'\x4a\x0f\x08' + bytes([id_]) + b'\x1a\x0b\x0a\x09\x11' + struct.pack('<d', float(valor))


def blob_posicion(pos):
    """pos = tilt (número, como antes) o [pan, tilt, zoom_x, zoom_y]: fracciones del cuadro (Y arriba) y zoom."""
    if isinstance(pos, (int, float)):
        x, y, zx, zy = 0.0, float(pos), 1.0, 1.0
    else:
        x, y, zx, zy = (float(v) for v in pos)
    cuerpo = (b'\x08\x04\x38\x00' + _campo(0x2a, zx, 1.0) + _campo(0x2b, zy, 1.0) + b'\x4a\x00'
              + _campo(0x28, x, 0.0) + _campo(0x29, y, 0.0) + _POS_DESPUES)
    pb = b'\x0a' + varint(len(cuerpo)) + cuerpo
    pb = struct.pack('>II', 2, len(pb)) + pb
    carga = b'\x81' + zstd.compress(b'\x6a' + varint(len(pb)) + pb)
    cab = struct.pack('>III', 1, 1, 16) + 'BlobData'.encode('utf-16-be') + struct.pack('>I', 12) + b'\x00'
    return (cab + struct.pack('>III', len(carga) + 8, 10001, len(carga)) + carga).hex()


def sintetizar(drt, drb, nombre_bin, posiciones=None):
    """posiciones = {nombre del clip: tilt normalizado}: si viene, cada clip lleva su posición en el .drb."""
    with zipfile.ZipFile(drt) as z:
        seq = ''.join(z.read(n).decode('utf-8') for n in z.namelist() if n.startswith('SeqContainer/'))
    with zipfile.ZipFile(REF) as z:
        proyecto = z.read('project.xml').decode('utf-8')
        raiz = z.read('MediaPool/Master/MpFolder.xml').decode('utf-8')
    id_master = re.search(r'<Sm2MpFolder DbId="([^"]+)">', raiz).group(1)
    id_pool = re.search(r'<MediaPool>([^<]+)</MediaPool>', raiz).group(1)
    id_bin = str(uuid.uuid4())
    elementos, nombres, blobs = [], [], []
    for bloque in _CLIP.findall(seq):
        nombre = re.search(r'<Name>(.*?)</Name>', bloque).group(1)
        duracion = int(re.search(r'<Duration>(\d+)</Duration>', bloque).group(1))
        fields = re.search(r'<FieldsBlob>([0-9a-f]*)</FieldsBlob>', bloque).group(1)
        tabla = re.search(r'<CompositionTable>.*?</CompositionTable>', bloque, re.S).group(0)
        tabla = re.sub(r'<Sm2TiCompositionTable DbId="[^"]+">',
                       f'<Sm2TiCompositionTable DbId="{uuid.uuid4()}">', tabla)
        plantilla, ruta = plantilla_de(fields)
        id_gen = str(uuid.uuid4())
        if posiciones and nombre in posiciones:
            blobs.append('    <Element>\n'
                         f'     <Sm2MpItemLockableBlob DbId="{uuid.uuid4()}">\n'
                         f'      <FieldsBlob>{blob_posicion(posiciones[nombre])}</FieldsBlob>\n'
                         f'      <BlobOwner>{id_gen}</BlobOwner>\n'
                         '      <DbSavedTime>0</DbSavedTime>\n'
                         '     </Sm2MpItemLockableBlob>\n'
                         '    </Element>\n')
        elementos.append(
            '  <Element>\n'
            f'   <Sm2MpGenerator DbId="{id_gen}">\n'
            f'    <FieldsBlob>{blob_generador(nombre, duracion, plantilla, ruta)}</FieldsBlob>\n'
            f'    <Name>{nombre}</Name>\n'
            f'    <MpFolder>{id_bin}</MpFolder>\n'
            f'    <UniqueMediaPoolItemId>{uuid.uuid4()}</UniqueMediaPoolItemId>\n'
            '    <MarkIn/>\n    <MarkInVideo/>\n    <MarkInAudio/>\n    <MarkOut/>\n    <MarkOutVideo/>\n'
            '    <MarkOutAudio/>\n    <CurPlayheadPosition/>\n'
            f'    {tabla}\n'
            '   </Sm2MpGenerator>\n'
            '  </Element>')
        nombres.append((nombre, plantilla))
    cabecera = re.match(r'(<\?xml[^>]*\?>\s*<!--[^>]*-->)', raiz).group(1)
    bin_xml = (f'{cabecera}\n<Sm2MpFolder DbId="{id_bin}">\n <FieldsBlob/>\n <Name>{nombre_bin}</Name>\n'
               f' <MpFolder>{id_master}</MpFolder>\n <UniqueMediaPoolItemId>{uuid.uuid4()}</UniqueMediaPoolItemId>\n'
               ' <MediaVec>\n' + '\n'.join(elementos) + '\n </MediaVec>\n'
               f' <MediaPool>{id_pool}</MediaPool>\n <Folded>true</Folded>\n <ColorTag>FOLDER_COLOR_NONE</ColorTag>\n'
               ' <LockSysId/>\n <DbSavedTime>0</DbSavedTime>\n</Sm2MpFolder>\n')
    # project.xml de la referencia, sin los blobs de transformación de SUS clips y con otro nombre
    proyecto = re.sub(r'\s*<Element>\s*<Sm2MpItemLockableBlob .*?</Sm2MpItemLockableBlob>\s*</Element>', '',
                      proyecto, flags=re.S)
    if blobs:
        m = re.search(r'\n\s*<Element>\s*<Sm2MediaPoolLockableBlob', proyecto)
        proyecto = proyecto[:m.start() + 1] + ''.join(blobs) + proyecto[m.start() + 1:]
    proyecto = re.sub(r'<ProjectName>[^<]*</ProjectName>', f'<ProjectName>{nombre_bin}</ProjectName>', proyecto)
    pathlib.Path(drb).parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(drb, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('project.xml', proyecto)
        z.writestr(f'MediaPool/Master/000_{nombre_bin}/MpFolder.xml', bin_xml)
        z.writestr('MediaPool/Master/MpFolder.xml', raiz)
    return nombres


if __name__ == '__main__':
    print(sintetizar(sys.argv[1], sys.argv[2], sys.argv[3]))
