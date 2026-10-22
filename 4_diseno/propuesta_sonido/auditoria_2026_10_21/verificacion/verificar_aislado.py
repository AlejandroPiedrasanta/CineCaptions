"""Run the existing page harness with user data redirected; capture actual Qt widgets.

No production files are changed. Original words are read once into memory.
All home data, caches, prefs and Qt/ffmpeg temporary files go below this directory.
Resolve execution methods are guarded before the harness is imported.
"""
import copy
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
CODE = ROOT / '1_codigo'
DEV = CODE / 'herramientas_dev'
REAL_HOME = Path.home()
VIDEO = REAL_HOME / 'Desktop' / 'VIDEOS EN ESPAÑOL' / 'PRUEBA ESPAÑOL.mp4'
assert VIDEO.is_file(), VIDEO
sys.dont_write_bytecode = True
sys.path[:0] = [str(CODE), str(DEV)]
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import probar_director_sonido as P
WORDS = P._palabras_de_cache(VIDEO)
assert WORDS, 'No cached transcript exists for the default sample video.'
P._palabras_de_cache = lambda video: copy.deepcopy(WORDS)

VHOME = OUT / 'home_aislado'
VTEMP = OUT / 'tmp_aislado'
for p in (VHOME, VTEMP, VHOME / 'AppData' / 'Roaming', VHOME / 'AppData' / 'Local'):
    p.mkdir(parents=True, exist_ok=True)
Path.home = classmethod(lambda cls: VHOME)
os.environ.update({
    'USERPROFILE': str(VHOME), 'HOME': str(VHOME),
    'APPDATA': str(VHOME / 'AppData' / 'Roaming'),
    'LOCALAPPDATA': str(VHOME / 'AppData' / 'Local'),
    'TEMP': str(VTEMP), 'TMP': str(VTEMP), 'QT_QPA_PLATFORM': 'offscreen',
    'CINECAPTIONS_AI_SOUND': '1', 'PYTHONDONTWRITEBYTECODE': '1',
})
tempfile.tempdir = str(VTEMP)

import resolve_mcp as RM
RESOLVE_ATTEMPTS = []
def blocked_resolve(*args, **kwargs):
    RESOLVE_ATTEMPTS.append('blocked')
    raise RuntimeError('Audit isolation: real Resolve calls are disabled')
for name in ('script', 'ejecutar_py', 'ejecutar_lua', 'conectar', 'abrir_resolve'):
    if hasattr(RM, name):
        setattr(RM, name, blocked_resolve)
RM.resolve_abierto = lambda: False
RM.ruta_exe = lambda: ''

spec = importlib.util.spec_from_file_location('page_harness_audit', DEV / 'probar_pagina_director.py')
H = importlib.util.module_from_spec(spec)
spec.loader.exec_module(H)
sys.argv = [str(DEV / 'probar_pagina_director.py'), '--video', str(VIDEO), '--salida', str(OUT)]
real_exit = os._exit
os._exit = lambda code: (_ for _ in ()).throw(SystemExit(code))
HARNESS_EXIT = None
try:
    H.main()
except SystemExit as e:
    HARNESS_EXIT = e.code
finally:
    os._exit = real_exit

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout
import qt_kit as ui
import director_sonido_ui as U
import director_sonido_sesion as S
import director_sonido_estado as E
import efectos_visuales as FX

app = QApplication.instance()
res = S.resumen(VIDEO)
assert res.get('hay'), 'The existing isolated design was not found.'
captures = []
for w, h in ((1240, 900), (1000, 720)):
    frame = QWidget()
    frame.setObjectName('audit_frame')
    frame.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    frame.setStyleSheet('QWidget#audit_frame { background: #080C14; }')
    layout = QVBoxLayout(frame)
    # _nueva_pagina('sfx', con_barra=False) uses these exact margins.
    layout.setContentsMargins(40, 86, 28, 22)
    layout.setSpacing(18)
    scroll = ui.Desplazable(espacio=20, margenes=(0, 4, 12, 8), estirar_final=False)
    layout.addWidget(scroll, 1)
    page = U.PaginaDirector(video=lambda: str(VIDEO))
    scroll.capa.addWidget(page, 1)
    page._pintar(copy.deepcopy(res))
    # Match the selected-event state used in the existing test capture.
    event = next(e for e in res['eventos'] if e['suena'] and e['tipo'] == 'golpe')
    page._elegir(event)
    frame.resize(w, h)
    frame.show()
    for _ in range(8):
        app.processEvents()
    filename = OUT / f'pagina_actual_{w}x{h}_arriba.png'
    frame.grab().save(str(filename))
    bar = scroll.verticalScrollBar()
    info = {
        'requested': [w, h], 'actual': [frame.width(), frame.height()],
        'page_size': [page.width(), page.height()],
        'page_minimum_hint': [page.minimumSizeHint().width(), page.minimumSizeHint().height()],
        'scroll_viewport': [scroll.viewport().width(), scroll.viewport().height()],
        'vertical_scroll_max': bar.maximum(),
        'horizontal_scroll_max': scroll.horizontalScrollBar().maximum(),
        'screenshot_top': str(filename),
        'widgets': {},
    }
    viewport_rect = scroll.viewport().rect()
    for name, widget in (
        ('timeline', page._linea), ('selected_event', page._lbl_ev),
        ('phrase_entry', page._entrada), ('apply', page._b_aplicar),
        ('redesign', page._b_redisenar), ('preview', page._b_ai),
    ):
        point = widget.mapTo(scroll.viewport(), widget.rect().topLeft())
        r = widget.rect().translated(point)
        info['widgets'][name] = {
            'rect_in_viewport': [r.x(), r.y(), r.width(), r.height()],
            'fully_visible': viewport_rect.contains(r),
            'intersects': viewport_rect.intersects(r),
        }
    bar.setValue(bar.maximum())
    app.processEvents()
    bottom = OUT / f'pagina_actual_{w}x{h}_abajo.png'
    frame.grab().save(str(bottom))
    info['screenshot_bottom'] = str(bottom)
    full = OUT / f'pagina_actual_contenido_{w}.png'
    page.grab().save(str(full))
    info['screenshot_full_page'] = str(full)
    captures.append(info)
    frame.hide()

report = {
    'harness_exit': HARNESS_EXIT,
    'passed': sum(int(passed) for _, passed in H.RESULTADOS),
    'total': len(H.RESULTADOS),
    'failed': [name for name, passed in H.RESULTADOS if not passed],
    'sample_video': str(VIDEO), 'cached_transcript_word_count': len(WORDS),
    'resolve_attempts': RESOLVE_ATTEMPTS,
    'isolated_home': str(VHOME), 'isolated_director_state': str(E.CARPETA),
    'isolated_effects_cache': str(FX.CACHE), 'captures': captures,
    'limits': ['Offscreen Qt page and production scroll container; no complete application shell.',
               'Uses existing cached transcription of the real local sample video.',
               'Resolve is mocked; no live timeline or audible playback tested.',
               'Only this sample and these two viewport sizes were checked.'],
}
(OUT / 'resultado_verificacion.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)
real_exit(0 if HARNESS_EXIT == 0 else 1)
