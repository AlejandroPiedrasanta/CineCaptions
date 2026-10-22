# CineCaptions · By Cinema Productions
# 5_licencias/administrador/paginas_productos.py — Administrador de Licencias: página Productos (galería tipo «acceso rápido»).
"""Cinema Productions · Administrador de Licencias — página «Productos».

Todos los productos que vendes (de todas tus cuentas de Gumroad y de las demás plataformas) como tarjetas de
cristal, con sus números. Al elegir una se abre el detalle: publicar u ocultar, cupones, avisar o bloquear a todos
sus compradores, racha de ventas de la semana, y abajo la lista de sus ventas con reembolso y recibo.

Creado por Cinema Productions.
"""
from __future__ import annotations

import json
from datetime import datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from dialogos import copiar
from interfaz import (C, Chips, ContadorAnimado, EstadoVacio, PanelDeslizante, boton, celda, color_estado, dato_seleccionado,
                      etiqueta, fila, fundido, legible, llenar_tabla, pildora, priv_correo, priv_nombre, tabla)
from modelo import duracion, fmt_fecha
from paginas import Pagina, _desplazable, _vaciar
from plataformas import PLATAFORMAS, dinero
from vidrio import (Cuadricula, InterruptorCristal, KPICristal, RachaSemana, Sparkline, TarjetaProducto,
                    pixmap_dinero, pixmap_personas, racha_semana)

__author__ = "Cinema Productions"


class PaginaProductos(Pagina):
    titulo = "Productos"
    subtitulo = "Todo lo que vendes, de todas tus cuentas y plataformas, en un solo lugar."
    icono = "📦"

    def __init__(self, v):
        super().__init__(v)
        self.elegido: str | None = None
        self._firma = None
        self.tarjetas: dict[str, TarjetaProducto] = {}
        self.sin_datos = EstadoVacio("📦", "Conecta tu tienda para ver tus productos",
                                     "Aquí aparecen todos tus productos de Gumroad (de todas tus cuentas), Lemon Squeezy, "
                                     "Stripe, Paddle y más, con sus ventas, ingresos y compradores.",
                                     "Conectar plataforma")
        self.sin_datos.boton.clicked.connect(lambda: self.v.conectar())
        self.contenido = QWidget(objectName="pagina")
        cuerpo = QHBoxLayout(self.contenido)
        cuerpo.setContentsMargins(0, 0, 0, 0)
        cuerpo.setSpacing(0)

        # ---- columna izquierda
        izq = QWidget(objectName="pagina")
        c = QVBoxLayout(izq)
        c.setContentsMargins(0, 0, 8, 12)
        c.setSpacing(14)
        kpis = QHBoxLayout()
        kpis.setSpacing(12)
        self.k_productos = KPICristal("Productos", C["acento"], ayuda="En tus cuentas")
        self.k_ventas = KPICristal("Ventas", C["ok"], ayuda="Válidas")
        self.k_ingresos = KPICristal("Ingresos", C["oro"], pixmap_dinero(54), ayuda="Ventas válidas")
        self.k_personas = KPICristal("Compradores", C["info"], pixmap_personas(54), ayuda="Distintos")
        self.k_activas = KPICristal("Licencias activas", C["aviso"], ayuda="En total")
        for k in (self.k_productos, self.k_ventas, self.k_ingresos, self.k_personas, self.k_activas):
            kpis.addWidget(k)
        c.addLayout(kpis)
        self.chips = Chips([("todos", "Todos")])
        self.chips.cambiado.connect(lambda _: self.pintar(self.v.modelo))
        self._claves_chips = ["todos"]
        b_cuentas = boton("🛍️  Cuentas", tip="Añade varios tokens: el panel junta todas tus tiendas.")
        b_cuentas.clicked.connect(self.v.abrir_cuentas_gumroad)
        b_hooks = boton("🔔  Webhooks", tip="Gumroad avisa a tu servidor al instante (reembolsos, disputas…).")
        b_hooks.clicked.connect(self.v.abrir_webhooks)
        b_msg = boton("📨  Mensaje", "primario",
                      tip="Aviso en el programa, WhatsApp en cola o correo a tus compradores.")
        b_msg.clicked.connect(lambda: self.v.abrir_mensaje_masivo(self.elegido or ""))
        self.fila_chips = fila(self.chips, None, espacio=8)
        c.addLayout(self.fila_chips)
        c.addLayout(fila(etiqueta("ACCESO RÁPIDO", "kpiTitulo"), None, b_cuentas, b_hooks, b_msg, espacio=8))
        self.galeria = Cuadricula(250, 14, TarjetaProducto.ALTO + 6)
        c.addWidget(self.galeria)
        self.titulo_ventas = etiqueta("TODAS LAS VENTAS", "kpiTitulo")
        c.addWidget(self.titulo_ventas)
        self.b_persona = boton("👤  Persona")
        self.b_persona.clicked.connect(lambda: (s := self.venta()) and self.v.ver_persona(
            (s["correo"] or "").strip().lower() or "nombre:" + (s["cliente"] or "?").strip().lower()))
        self.b_reembolsar = boton("↩  Reembolsar", "peligro", "Devuelve el dinero al comprador y bloquea su licencia.")
        self.b_reembolsar.clicked.connect(lambda: (s := self.venta()) and self.v.reembolsar_venta(s))
        self.b_parcial = boton("Reembolso parcial")
        self.b_parcial.clicked.connect(lambda: (s := self.venta()) and self.v.reembolsar_venta(s, parcial=True))
        self.b_recibo = boton("✉  Reenviar recibo")
        self.b_recibo.clicked.connect(lambda: (s := self.venta()) and self.v.reenviar_recibo(s))
        self.resumen_ventas = etiqueta("", "nota")
        c.addLayout(fila(self.resumen_ventas, None, self.b_persona, self.b_recibo, self.b_parcial, self.b_reembolsar))
        self.t = tabla(["Fecha", "Cliente", "Correo", "Plataforma", "Producto", "Total", "Estado", "Cupón", "País"],
                       [130, 160, 200, 120, 190, 90, 130, 100], pildoras=(3, 6))
        self.t.setMinimumHeight(300)
        self.t.setMinimumWidth(0)
        self.t.itemSelectionChanged.connect(self._botones)
        self.vacio_ventas = EstadoVacio("🛒", "Sin ventas", "Las ventas de este producto aparecerán aquí.")
        c.addWidget(self.t)
        c.addWidget(self.vacio_ventas)
        c.addStretch()
        area = _desplazable(izq)
        area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        cuerpo.addWidget(area, 1)

        # ---- panel de detalle
        self.panel = PanelDeslizante(400)
        self.panel_lay = QVBoxLayout(self.panel)
        self.panel_lay.setContentsMargins(20, 16, 20, 16)
        self.panel_lay.setSpacing(10)
        cuerpo.addSpacing(10)
        cuerpo.addWidget(self.panel)
        self.lay.addWidget(self.sin_datos, 1)
        self.lay.addWidget(self.contenido, 1)
        self._botones()

    # ---------------------------------------------------------------- selección
    def venta(self) -> dict | None:
        return self.v.modelo["venta_por_pedido"].get(dato_seleccionado(self.t))

    def producto(self) -> dict | None:
        return self.v.modelo.get("producto_por_clave", {}).get(self.elegido or "")

    def _botones(self):
        s = self.venta()
        self.b_persona.setEnabled(s is not None)
        self.b_recibo.setEnabled(bool(s and s["plataforma"] == "gumroad"))
        self.b_parcial.setEnabled(bool(s and self.v.puede_reembolsar(s)))
        self.b_reembolsar.setEnabled(bool(s and self.v.puede_reembolsar(s)))

    def elegir(self, clave: str | None):
        cierra = clave == self.elegido
        self.elegido = None if cierra else clave
        for k, t in self.tarjetas.items():
            t.fijar_elegida(k == self.elegido)
        if self.elegido:
            self._armar_panel(self.producto())
            self.panel.abrir()
        else:
            self.panel.cerrar()
        self._pintar_ventas(self.v.modelo)

    # ---------------------------------------------------------------- detalle
    def _armar_panel(self, p: dict | None):
        _vaciar(self.panel_lay)
        if not p:
            return
        pl = PLATAFORMAS[p["plataforma"]]
        cerrar = QPushButton("✕", objectName="enlace")
        cerrar.setCursor(Qt.CursorShape.PointingHandCursor)
        cerrar.clicked.connect(lambda: self.elegir(self.elegido))
        nombre = etiqueta(p["nombre"], "tituloTarjeta", ajustar=True)
        nombre.setStyleSheet("font-size:18px;")
        self.panel_lay.addLayout(fila(nombre, None, cerrar))
        pills = [pildora(f"{pl['icono']} {pl['nombre']}", pl["color"]),
                 pildora("●  Publicado" if p["activo"] else "●  Oculto", C["ok"] if p["activo"] else C["tenue"])]
        if p["plataforma"] == "gumroad" and len(self.v.cuentas_gumroad()) > 1:
            pills.append(pildora(f"Cuenta {p['cuenta'] + 1}", C["info"]))
        self.panel_lay.addLayout(fila(*pills, None))
        if p.get("descripcion"):
            self.panel_lay.addWidget(etiqueta(p["descripcion"][:220], "nota", ajustar=True))
        ingresos = "  ·  ".join(dinero(v, m) for m, v in sorted(p["ingresos"].items(), key=lambda x: -x[1])) or "—"
        datos = QHBoxLayout()
        for titulo, valor in (("Ventas", str(p["ventas"])), ("Ingresos", ingresos), ("Compradores", str(p["personas"]))):
            col = QVBoxLayout()
            col.setSpacing(0)
            col.addWidget(etiqueta(titulo.upper(), "kpiTitulo"))
            col.addWidget(etiqueta(valor, "valorFuerte", ajustar=True))
            datos.addLayout(col)
        self.panel_lay.addLayout(datos)
        spark = Sparkline(pl["color"], 54)
        spark.fijar(p["ingresos_serie"] if sum(p["ingresos_serie"]) else p["serie"])
        self.panel_lay.addWidget(etiqueta("ÚLTIMOS 30 DÍAS", "kpiTitulo"))
        self.panel_lay.addWidget(spark)
        racha = RachaSemana("RACHA DE VENTAS", "DÍAS")
        racha.setFixedHeight(150)
        r, dias, hoy = racha_semana(p["serie"])
        racha.fijar(r, dias, hoy)
        self.panel_lay.addWidget(racha)
        # licencias
        self.panel_lay.addWidget(etiqueta("LICENCIAS", "kpiTitulo"))
        self.panel_lay.addWidget(etiqueta(
            f"<b>{p['activas']}</b> activas · <b>{p['bloqueadas']}</b> bloqueadas · uso total "
            f"<b>{duracion(p['uso_seg'])}</b>" + (f" · <b>{p['en_linea']}</b> en línea" if p["en_linea"] else ""),
            "nota", ajustar=True))
        # publicar / ocultar
        if p["plataforma"] == "gumroad":
            sw = InterruptorCristal("EN VENTA", "OCULTO", C["aviso"])
            sw.fijar_sin_animar(p["activo"])
            sw.setFixedSize(168, 46)
            sw.setToolTip("Publica u oculta este producto en Gumroad.")

            def cambio(v, sw=sw, p=p):
                if not self.v.publicar_producto(p, v):          # canceló: vuelve a su sitio
                    sw.fijar_sin_animar(not v)
            sw.toggled.connect(cambio)
            self.panel_lay.addLayout(fila(etiqueta("En Gumroad", "nota"), None, sw))
        self.panel_lay.addStretch()
        b_abrir = boton("🔗  Abrir", tip="Abre la página de venta.")
        b_abrir.clicked.connect(lambda: self.v.abrir_producto(p))
        b_copiar = boton("Copiar enlace")
        b_copiar.setEnabled(bool(p.get("url")))
        b_copiar.clicked.connect(lambda: (copiar(p["url"]), self.v.aviso("Enlace copiado", p["nombre"], "ok")))
        self.panel_lay.addLayout(fila(b_abrir, b_copiar, None))
        if p["plataforma"] == "gumroad":
            b_cup = boton("🎟️  Cupones")
            b_cup.clicked.connect(lambda: self.v.ver_cupones(p))
            b_nuevo = boton("＋  Cupón")
            b_nuevo.clicked.connect(lambda: self.v.crear_cupon(p))
            self.panel_lay.addLayout(fila(b_cup, b_nuevo, None))
        b_av = boton("📣  Avisar", tip="Aviso dentro del programa a todos los compradores de este producto.")
        b_av.setEnabled(bool(p["lic_ids"]) and self.v.servidor() is not None)
        b_av.clicked.connect(lambda: self.v.avisar_producto(p))
        b_msg = boton("📨  Mensaje", "whatsapp", "WhatsApp, correo o aviso a los compradores de este producto.")
        b_msg.clicked.connect(lambda: self.v.abrir_mensaje_masivo(p["clave"]))
        self.panel_lay.addLayout(fila(b_av, b_msg, None))
        b_bloq = boton("⛔  Bloquear todas", "peligro", "Bloquea todas las licencias de este producto.")
        b_bloq.setEnabled(bool(p["lic_ids"]))
        b_bloq.clicked.connect(lambda: self.v.bloquear_producto(p, True))
        b_reac = boton("↺  Reactivar todas")
        b_reac.setEnabled(bool(p["lic_ids"]))
        b_reac.clicked.connect(lambda: self.v.bloquear_producto(p, False))
        self.panel_lay.addLayout(fila(b_bloq, b_reac, None))
        fundido(self.panel, 0.4, 1.0, 220)

    # ---------------------------------------------------------------- ventas del producto
    def _pintar_ventas(self, m: dict):
        p = self.producto()
        filas, validas, total = [], 0, {}
        for s in m["ventas"]:
            if p and s.get("producto_clave") != p["clave"]:
                continue
            if not self.v.coincide(s["cliente"], s["correo"], s["producto"], s["referencia"]):
                continue
            validas += s["valida"]
            if s["valida"] and s["total"] is not None:
                total[s["moneda"]] = total.get(s["moneda"], 0) + s["total"]
            pl = PLATAFORMAS[s["plataforma"]]
            filas.append([celda(fmt_fecha(s["fecha"]), dato=s["id"], orden=s["fecha"] or ""),
                          celda(priv_nombre(s["cliente"]), negrita=True), celda(priv_correo(s["correo"])),
                          celda(pl["nombre"], pildora=pl["color"]), celda(s["producto"]),
                          celda(s["total_txt"], orden=s["total"] or 0),
                          celda(s["estado"] + ("  · prueba" if s["prueba"] else ""), pildora=color_estado(s["estado"])),
                          celda(s.get("cupon") or "—"), celda(s.get("pais") or "—")])
        llenar_tabla(self.t, filas)
        suma = "  ·  ".join(dinero(v, mo) for mo, v in sorted(total.items(), key=lambda x: -x[1]))
        self.titulo_ventas.setText(f"VENTAS DE {p['nombre'].upper()}" if p else "TODAS LAS VENTAS")
        self.resumen_ventas.setText(f"{len(filas)} ventas · {validas} válidas" + (f" · {suma}" if suma else ""))
        self.t.setVisible(bool(filas))
        self.vacio_ventas.setVisible(not filas)
        self._botones()

    # ---------------------------------------------------------------- pintar
    def _chips(self, productos: list[dict]):
        claves = ["todos"] + sorted({p["plataforma"] for p in productos}) + ["publicados", "ocultos"]
        if claves == self._claves_chips:
            return
        actual = self.chips.actual() if self.chips.claves else "todos"
        fijos = {"todos": "Todos", "publicados": "Publicados", "ocultos": "Ocultos"}
        nuevo = Chips([(k, fijos[k] if k in fijos else f"{PLATAFORMAS[k]['icono']} {PLATAFORMAS[k]['nombre']}")
                       for k in claves])
        nuevo.cambiado.connect(lambda _: self.pintar(self.v.modelo))
        viejo = self.chips
        self.fila_chips.replaceWidget(viejo, nuevo)
        viejo.deleteLater()
        self.chips = nuevo
        self._claves_chips = claves
        if actual in claves:
            nuevo.elegir(actual)

    def pintar(self, m: dict):
        productos = m.get("productos", [])
        hay = bool(self.v.clientes) and (bool(productos) or bool(self.v.resultados))
        conectado = any(k in self.v.clientes for k in PLATAFORMAS)
        self.sin_datos.setVisible(not conectado)
        self.contenido.setVisible(conectado)
        if not conectado:
            return
        self._chips(productos)
        filtro = self.chips.actual()
        visibles = []
        for p in productos:
            if filtro in PLATAFORMAS and p["plataforma"] != filtro:
                continue
            if (filtro == "publicados" and not p["activo"]) or (filtro == "ocultos" and p["activo"]):
                continue
            if not self.v.coincide(p["nombre"], PLATAFORMAS[p["plataforma"]]["nombre"], p.get("descripcion")):
                continue
            visibles.append(p)
        self.k_productos.valor.fijar(len(productos))
        self.k_productos.sub.setText(f"{sum(1 for p in productos if p['activo'])} publicados · "
                                     f"{sum(1 for p in productos if not p['activo'])} ocultos")
        self.k_ventas.valor.fijar(sum(p["ventas"] for p in productos))
        ing: dict[str, float] = {}
        for p in productos:
            for mo, v in p["ingresos"].items():
                ing[mo] = ing.get(mo, 0) + v
        orden = sorted(ing.items(), key=lambda x: -x[1])
        moneda, total = orden[0] if orden else ("", 0.0)
        self.k_ingresos.valor.formato = lambda v, mo=moneda: f"{v:,.0f} {mo}".strip()
        self.k_ingresos.valor.fijar(total)
        self.k_ingresos.sub.setText("+ " + ", ".join(dinero(v, mo) for mo, v in orden[1:3]) if len(orden) > 1
                                    else "Ventas válidas")
        self.k_personas.valor.fijar(len({c for p in productos for c in p["personas_claves"]}))
        self.k_activas.valor.fijar(sum(p["activas"] for p in productos))
        firma = json.dumps([[p["clave"], p["nombre"], p["activo"], p["ventas"], p["ingresos"], p["activas"], p["serie"],
                             p["precio_txt"], p["bloqueadas"], p["uso_seg"] // 60] for p in visibles], default=str)
        if firma != self._firma:
            self._firma = firma
            self.tarjetas = {}
            widgets = []
            for i, p in enumerate(visibles):
                pl = PLATAFORMAS[p["plataforma"]]
                t = TarjetaProducto(p, pl["color"], pl["icono"])
                t.fijar_elegida(p["clave"] == self.elegido)
                t.clic.connect(self.elegir)
                self.tarjetas[p["clave"]] = t
                widgets.append(t)
            self.galeria.poner(widgets)
            for i, t in enumerate(widgets):
                t.aparecer(i * 70)
        if self.elegido and self.elegido not in self.v.modelo.get("producto_por_clave", {}):
            self.elegido = None
            self.panel.cerrar()
        elif self.elegido and self.panel.abierto():
            self._armar_panel(self.producto())
        self.sin_datos_productos = not visibles
        self._pintar_ventas(m)

    def al_mostrar(self):
        for i, t in enumerate(self.tarjetas.values()):
            t.aparecer(i * 60)
