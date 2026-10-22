"""Vista Qt aislada con datos ficticios; sin importar el motor ni tocar Resolve."""
import copy
import json
import os
from pathlib import Path
import py_compile
import sys
import types

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent / 'vista_qt'
OUT.mkdir(parents=True, exist_ok=True)
TASK_HOME = OUT / 'home_aislado'
TASK_HOME.mkdir(exist_ok=True)
Path.home = classmethod(lambda cls: TASK_HOME)
for folder in ('Roaming', 'Local', 'tmp'):
    (TASK_HOME / folder).mkdir(exist_ok=True)
os.environ.update(USERPROFILE=str(TASK_HOME), HOME=str(TASK_HOME),
                  APPDATA=str(TASK_HOME / 'Roaming'), LOCALAPPDATA=str(TASK_HOME / 'Local'),
                  TEMP=str(TASK_HOME / 'tmp'), TMP=str(TASK_HOME / 'tmp'), QT_QPA_PLATFORM='offscreen')
sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(ROOT / '1_codigo'))
sys.modules['director_sonido_sesion'] = types.SimpleNamespace(detener=lambda: None)
py_compile.compile(str(ROOT / '1_codigo' / 'director_sonido_ui.py'), cfile=str(OUT / 'director_sonido_ui.pyc'), doraise=True)

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout
import qt_kit as ui
import director_sonido_ui as U

app = ui.crear_app(['vista-sonido'], carpeta_fuentes=str(ROOT / '2_recursos' / 'fonts'))
eventos = [dict(clave=f'sfx-{i}', nombre=nombre, ancla=t, t=t-.15, dur=.5+i*.1,
                tipo=tipo, suena=True, diseno='Acento sutil sobre la transición',
                fuente='procedural', importancia=.75, por_que='Acompaña el cambio de escena sin tapar la voz.')
           for i, (nombre, t, tipo) in enumerate((('Entrada del título', 2.4, 'golpe'), ('Nuevo paisaje', 8.0, 'whoosh'),
               ('Palabra clave', 14.7, 'pop'), ('Cambio de escena', 22.2, 'giro'), ('Cierre', 37.1, 'golpe')))]
res = dict(hay=True, activo=True, nombre_video='Una historia en Guatemala.mp4', video='E:/demo/Una historia en Guatemala.mp4',
           duracion=42.8, tema='Viajes', sonic_style='Cinemático cálido', sound_score=92, sound_score_viejo=False,
           controles={}, pendiente_resolve=True, puede_aplicar=True, destino={'proyecto':'CineCaptions','timeline':'Viaje a Guatemala'},
           eventos=eventos, carriles={'voz':[(0, 11), (13, 27), (29, 41)], 'musica':[(0, 42.8, '')],
           'ambiente':[(0, 20, 'Exterior', 'ADD_SUBTLE_AMBIENCE'), (20, 42.8, 'Ciudad', 'ADD_SUBTLE_AMBIENCE')],
           'cortes':[0,8,22,37], 'captions':[(2.4, 'GENERATE',''), (14.7, 'GENERATE','')]},
           notas=[dict(clave=k, titulo=nombre, valor='Lista', detalle='El diseño acompaña el video y protege la voz.', nivel='ok')
                  for k,nombre in (('voz','Voz'),('ruido','Ruido'),('musica','Música'),('ambiente','Ambiente'),
                  ('motion','Motions'),('mezcla','Mezcla'),('master','Master'),('material','Material'))])
results=[]
for width,height in ((1240,900),(1000,720),(760,720)):
    frame=QWidget()
    frame.setObjectName('vista_sonido')
    frame.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    frame.setStyleSheet('QWidget#vista_sonido { background: #080C14; }')
    layout=QVBoxLayout(frame)
    layout.setContentsMargins(40,86,28,22)
    scroll=ui.Desplazable(espacio=20, margenes=(0,4,12,8), estirar_final=False)
    layout.addWidget(scroll)
    page=U.PaginaDirector(video=lambda:res['video'])
    scroll.capa.addWidget(page)
    page._pintar(copy.deepcopy(res))
    page._elegir(page._res['eventos'][1])
    frame.resize(width,height)
    frame.show()
    for _ in range(12):
        app.processEvents()
    frame.grab().save(str(OUT/f'sonido_{width}x{height}.png'))
    page.grab().save(str(OUT/f'sonido_contenido_{width}.png'))
    results.append(dict(size=[frame.width(),frame.height()],page=[page.width(),page.height()],
                        minimum=[page.minimumSizeHint().width(),page.minimumSizeHint().height()],
                        horizontal_scroll=scroll.horizontalScrollBar().maximum(),
                        inspector_lateral=page._ancho_distribuido[0],events=page._lista_eventos.count()))
    if width==1000:
        # Navegación nativa de lista e inspector, sin motor ni preferencias.
        page._lista_eventos.setCurrentRow(2)
        assert page._ev['clave']=='sfx-2'
        page._estado('Error de prueba que debe seguir visible')
        page._pintar(page._res)
        assert page._lbl_estado.text()=='Error de prueba que debe seguir visible'
        page._ocupado=True
        page._actualizar_disponibles()
        assert not page._entrada.isEnabled() and not page._b_enviar.isEnabled() and not page._sw.isEnabled()
        assert all(not c.isEnabled() for c in page._controles.values())
        page._var_frase.set('menos sonidos')
        page._frase()
        assert page._var_frase.get()=='menos sonidos'
        page._ocupado=False
        page._pintar(dict(res,sound_score_viejo=True))
        assert page._score._v is None and page._lbl_score.text()
        page._pintar(dict(hay=False,activo=True))
        assert page._vacio.isVisible() and not page._cuerpo.isVisible()
        frame.grab().save(str(OUT/'sonido_vacio_1000.png'))
    frame.hide()
(OUT/'resultado.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(results,ensure_ascii=False,indent=2))
