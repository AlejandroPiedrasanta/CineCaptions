# CineCaptions · By Cinema Productions
# 5_licencias/administrador/dialogos_nuevos.py — Administrador de Licencias: cuentas de Gumroad, cupones, webhooks y mensajes.
"""Cinema Productions · Administrador de Licencias — ventanas emergentes de la versión 6.

  - DialogoCuentasGumroad: varios access tokens (cuentas) de Gumroad a la vez.
  - DialogoCupon / DialogoCupones: códigos de descuento de un producto de Gumroad.
  - DialogoWebhooks: registra en Gumroad los avisos que llaman a tu servidor.
  - DialogoMensajeMasivo: avisa a muchas personas (dentro del programa, WhatsApp en cola o correo).

Creado por Cinema Productions.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QComboBox, QDoubleSpinBox, QLineEdit, QPlainTextEdit, QSpinBox, QVBoxLayout, QWidget)

from acciones import PLANTILLAS_MENSAJE, rellenar
from control import estado_por_webhook  # noqa: F401  (reexportado para las pruebas)
from dialogos import caja_codigo, copiar, formulario
from interfaz import (C, Avatar, Chips, DialogoBase, EstadoVacio, Interruptor, Pila, Spinner, Toast, boton, celda,
                      dato_seleccionado, en_hilo, etiqueta, fila, llenar_tabla, pildora, priv_correo, priv_nombre,
                      sacudir, tabla)
from plataformas import PLATAFORMAS, WEBHOOKS_GUMROAD, Gumroad

__author__ = "Cinema Productions"

EVENTOS_UTILES = ("sale", "refund", "dispute", "dispute_won", "cancellation", "subscription_ended",
                  "subscription_restarted")


# ============================================================ cuentas de Gumroad

class DialogoCuentasGumroad(DialogoBase):
    """Todas tus cuentas de Gumroad en un solo panel. Cada una es un access token (Settings → Advanced)."""

    def __init__(self, ventana):
        super().__init__(ventana, "Cuentas de Gumroad", ancho=680)
        self.v = ventana
        self.cuentas = ventana.cuentas_gumroad()
        self.cuerpo.addWidget(etiqueta("🛍️  Tus cuentas de Gumroad", "tituloPagina"))
        self.cuerpo.addWidget(etiqueta(
            "Añade un access token por cada cuenta o tienda. El panel junta sus productos, ventas y licencias como si "
            "fueran una sola tienda, y cada acción (bloquear, reembolsar…) va a la cuenta correcta.", "nota",
            ajustar=True))
        self.lista = QVBoxLayout()
        self.lista.setSpacing(8)
        self.cuerpo.addLayout(self.lista)
        self.token = QLineEdit(placeholderText="Pega aquí el access token de otra cuenta de Gumroad")
        self.token.setEchoMode(QLineEdit.EchoMode.Password)
        self.token.returnPressed.connect(self.añadir)
        self.error = etiqueta("", ajustar=True)
        self.error.setStyleSheet(f"color:{C['error']}")
        self.spinner = Spinner(18)
        self.b_añadir = boton("＋  Añadir cuenta", "primario")
        self.b_añadir.clicked.connect(self.añadir)
        cerrar = boton("Cerrar")
        cerrar.clicked.connect(self.accept)
        self.cuerpo.addWidget(etiqueta("Añadir otra cuenta", "tituloTarjeta"))
        self.cuerpo.addLayout(fila(self.token, self.spinner, self.b_añadir))
        self.cuerpo.addWidget(self.error)
        self.cuerpo.addLayout(fila(None, cerrar))
        self._pintar()
        self._completar()

    def _completar(self):
        """Las cuentas guardadas sin nombre (p. ej. de una configuración vieja) piden su nombre a Gumroad."""
        for c in self.cuentas:
            if not (c.get("nombre") or c.get("correo")):
                en_hilo(Gumroad(c["token"]).usuario, ok=lambda u, t=c["token"]: self._poner_nombre(t, u))

    def _poner_nombre(self, token: str, u: dict):
        for c in self.cuentas:
            if c["token"] == token:
                c["nombre"], c["correo"] = u.get("name") or "", u.get("email") or ""
        self.v.recordar_datos_cuentas(self.cuentas)
        self._pintar()

    def _productos_de(self, i: int) -> int:
        return sum(1 for p in self.v.modelo.get("productos", []) if p["plataforma"] == "gumroad" and p.get("cuenta") == i)

    def _pintar(self):
        while self.lista.count():
            it = self.lista.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
            elif it.layout():
                while it.layout().count():
                    w = it.layout().takeAt(0).widget()
                    if w:
                        w.deleteLater()
        if not self.cuentas:
            self.lista.addWidget(etiqueta("Aún no hay cuentas conectadas.", "nota"))
        for i, c in enumerate(self.cuentas):
            nombre = priv_nombre(c.get("nombre")) or "Cuenta de Gumroad"
            textos = QVBoxLayout()
            textos.setSpacing(0)
            textos.addWidget(etiqueta(nombre + ("   · principal" if i == 0 else ""), "valorFuerte"))
            textos.addWidget(etiqueta(f"{priv_correo(c.get('correo')) or '—'}  ·  token …{c['token'][-4:]}  ·  "
                                      f"{self._productos_de(i)} productos", "tenue"))
            quitar = boton("Quitar", "peligro")
            quitar.clicked.connect(lambda _=False, k=i: self.quitar(k))
            caja = QWidget(objectName="tarjeta")
            lay = fila(Avatar(c.get("nombre") or c.get("correo"), c["token"], 38), textos, None, quitar, espacio=12)
            lay.setContentsMargins(12, 10, 12, 10)
            caja.setLayout(lay)
            self.lista.addWidget(caja)

    def añadir(self):
        token = self.token.text().strip()
        self.error.clear()
        if not token:
            sacudir(self.tarjeta)
            return
        if any(c["token"] == token for c in self.cuentas):
            self.error.setText("Esa cuenta ya está conectada.")
            return
        self.b_añadir.setEnabled(False)
        self.spinner.iniciar()

        def ok(u):
            self.spinner.detener()
            self.b_añadir.setEnabled(True)
            self.token.clear()
            self.cuentas.append({"token": token, "nombre": u.get("name") or "", "correo": u.get("email") or ""})
            self.v.guardar_cuentas_gumroad(self.cuentas)
            self._pintar()
            Toast.mostrar(self, "Cuenta añadida", u.get("name") or u.get("email") or "", "ok")

        def error(e):
            self.spinner.detener()
            self.b_añadir.setEnabled(True)
            self.error.setText(f"✕  {e}")
            sacudir(self.tarjeta)

        en_hilo(Gumroad(token).usuario, ok=ok, error=error)

    def quitar(self, i: int):
        c = self.cuentas[i]
        extra = ("<br><br>Es la cuenta principal: la siguiente pasará a serlo." if i == 0 and len(self.cuentas) > 1
                 else ("<br><br>Era la única: Gumroad quedará desconectado." if len(self.cuentas) == 1 else ""))
        if not self.v.confirmar("Quitar cuenta", f"¿Quitar la cuenta <b>{priv_nombre(c.get('nombre')) or '…'}</b> de este "
                                f"panel?{extra}<br><br>Tus datos en Gumroad no cambian.", "Sí, quitar"):
            return
        self.cuentas.pop(i)
        self.v.guardar_cuentas_gumroad(self.cuentas)
        if not self.cuentas:
            self.accept()
            return
        self._pintar()


# ============================================================ cupones

class DialogoCupon(DialogoBase):
    def __init__(self, producto: dict, parent=None):
        super().__init__(parent, "Nuevo cupón", ancho=520)
        self.codigo = QLineEdit(placeholderText="Por ejemplo: GRACIAS20")
        self.tipo = QComboBox()
        self.tipo.addItem("% de descuento", True)
        self.tipo.addItem("Monto fijo", False)
        self.valor = QDoubleSpinBox()
        self.valor.setRange(1, 100)
        self.valor.setValue(20)
        self.valor.setDecimals(0)
        self.tipo.currentIndexChanged.connect(self._tipo)
        self.usos = QSpinBox()
        self.usos.setRange(0, 1_000_000)
        self.usos.setSpecialValueText("Sin límite")
        form = formulario()
        form.addRow("Código", self.codigo)
        form.addRow("Tipo", self.tipo)
        form.addRow("Valor", self.valor)
        form.addRow("Usos máximos", self.usos)
        crear = boton("🎟️  Crear cupón", "primario")
        crear.clicked.connect(self.validar)
        cancelar = boton("Cancelar")
        cancelar.clicked.connect(self.reject)
        self.cuerpo.addWidget(etiqueta("🎟️  Nuevo cupón", "tituloPagina"))
        self.cuerpo.addWidget(etiqueta(f"Para <b>{producto['nombre']}</b> en Gumroad. Quien lo escriba al pagar recibe "
                                       "el descuento.", "nota", ajustar=True))
        self.cuerpo.addLayout(form)
        self.cuerpo.addLayout(fila(None, cancelar, crear))

    def _tipo(self):
        porcentaje = self.tipo.currentData()
        self.valor.setRange(1, 100 if porcentaje else 100000)
        self.valor.setDecimals(0 if porcentaje else 2)
        self.valor.setValue(20 if porcentaje else 5)

    def validar(self):
        if not self.codigo.text().strip():
            sacudir(self.tarjeta)
            return
        self.accept()

    def datos(self) -> dict:
        return {"nombre": self.codigo.text().strip(), "valor": self.valor.value(),
                "porcentaje": bool(self.tipo.currentData()), "usos_max": self.usos.value()}


class DialogoCupones(DialogoBase):
    def __init__(self, producto: dict, ventana):
        super().__init__(ventana, "Cupones", ancho=640)
        self.v, self.p = ventana, producto
        self.t = tabla(["Código", "Descuento", "Usos", "Límite"], [200, 140, 90], ordenable=False)
        self.vacio = EstadoVacio("🎟️", "Sin cupones", "Crea uno para regalar descuentos a tus clientes.")
        nuevo = boton("＋  Nuevo cupón", "primario")
        nuevo.clicked.connect(self.nuevo)
        self.b_borrar = boton("Borrar", "peligro")
        self.b_borrar.clicked.connect(self.borrar)
        cerrar = boton("Cerrar")
        cerrar.clicked.connect(self.accept)
        self.spinner = Spinner(18)
        self.cuerpo.addWidget(etiqueta(f"🎟️  Cupones de {producto['nombre']}", "tituloPagina"))
        self.cuerpo.addWidget(self.t, 1)
        self.cuerpo.addWidget(self.vacio, 1)
        self.cuerpo.addLayout(fila(nuevo, self.b_borrar, self.spinner, None, cerrar))
        self.t.itemSelectionChanged.connect(lambda: self.b_borrar.setEnabled(dato_seleccionado(self.t) is not None))
        self.b_borrar.setEnabled(False)
        self.cargar()

    def cargar(self):
        self.spinner.iniciar()

        def ok(codigos):
            self.spinner.detener()
            filas = []
            for c in codigos:
                desc = (f"{c['percent_off']} %" if c.get("percent_off") else
                        f"{(c.get('amount_cents') or 0) / 100:,.2f}")
                filas.append([celda(c.get("name"), dato=c.get("id"), negrita=True), celda(desc),
                              celda(c.get("times_used", 0)), celda(c.get("max_purchase_count") or "Sin límite")])
            llenar_tabla(self.t, filas)
            self.t.setVisible(bool(filas))
            self.vacio.setVisible(not filas)

        def error(e):
            self.spinner.detener()
            Toast.mostrar(self, "Gumroad", e, "error")

        en_hilo(self.v.gumroad().codigos, self.p["id"], ok=ok, error=error)

    def nuevo(self):
        d = DialogoCupon(self.p, self)
        if d.exec() != DialogoCupon.DialogCode.Accepted:
            return
        c = d.datos()
        en_hilo(self.v.gumroad().crear_codigo, self.p["id"], c["nombre"], c["valor"], c["porcentaje"], c["usos_max"],
                ok=lambda _: self.cargar(), error=lambda e: Toast.mostrar(self, "Gumroad", e, "error"))

    def borrar(self):
        id_ = dato_seleccionado(self.t)
        if id_ is not None and self.v.confirmar("Borrar cupón", "¿Borrar este cupón? Dejará de funcionar.",
                                                "Sí, borrar"):
            en_hilo(self.v.gumroad().borrar_codigo, self.p["id"], id_, ok=lambda _: self.cargar(),
                    error=lambda e: Toast.mostrar(self, "Gumroad", e, "error"))


# ============================================================ webhooks

class DialogoWebhooks(DialogoBase):
    """Gumroad llama a TU URL cuando hay una venta, reembolso o disputa. Con la función de Supabase incluida
    (servidor/gumroad_webhook.ts), un reembolso suspende la licencia al instante."""

    def __init__(self, ventana):
        super().__init__(ventana, "Webhooks de Gumroad", ancho=860)
        self.v = ventana
        self.cuerpo.addWidget(etiqueta("🔔  Webhooks de Gumroad", "tituloPagina"))
        ayuda = etiqueta(
            "Gumroad avisa a una dirección web tuya cada vez que pasa algo. Con la función "
            "<b>servidor/gumroad_webhook.ts</b> (se publica en Supabase en 3 pasos, ver el archivo) un reembolso, una "
            "disputa o una suscripción cancelada <b>suspende la licencia al instante</b>, aunque este panel esté "
            "cerrado.", "nota", ajustar=True)
        ayuda.setTextFormat(Qt.TextFormat.RichText)
        self.cuerpo.addWidget(ayuda)
        self.url = QLineEdit(ventana.url_webhook())
        self.url.setPlaceholderText("https://TU-PROYECTO.supabase.co/functions/v1/gumroad-webhook?secreto=…")
        copiar_b = boton("Copiar")
        copiar_b.clicked.connect(lambda: (copiar(self.url.text()), Toast.mostrar(self, "URL copiada", "", "ok")))
        self.cuerpo.addWidget(etiqueta("Dirección que recibirá los avisos", "tituloTarjeta"))
        self.cuerpo.addLayout(fila(self.url, copiar_b))
        self.t = tabla(["Evento", "Dirección", "Cuenta"], [200, 440], ordenable=False)
        self.vacio = EstadoVacio("🔔", "Sin webhooks", "Pulsa «Registrar los eventos útiles» para crearlos en Gumroad.")
        self.cuerpo.addWidget(self.t, 1)
        self.cuerpo.addWidget(self.vacio, 1)
        self.spinner = Spinner(18)
        self.b_registrar = boton("⚡  Registrar los eventos útiles", "primario",
                                 "Venta, reembolso, disputa, disputa ganada y suscripciones.")
        self.b_registrar.clicked.connect(self.registrar)
        self.b_borrar = boton("Borrar seleccionado", "peligro")
        self.b_borrar.clicked.connect(self.borrar)
        self.b_borrar.setEnabled(False)
        self.t.itemSelectionChanged.connect(lambda: self.b_borrar.setEnabled(dato_seleccionado(self.t) is not None))
        cerrar = boton("Cerrar")
        cerrar.clicked.connect(self.accept)
        self.cuerpo.addLayout(fila(self.b_registrar, self.b_borrar, self.spinner, None, cerrar))
        self.hooks: dict[str, dict] = {}
        self.cargar()

    def cargar(self):
        self.spinner.iniciar()

        def ok(lista):
            self.spinner.detener()
            self.hooks = {f"{w['_cuenta'] if '_cuenta' in w else 0}|{w['id']}": w for w in lista}
            filas = [[celda(WEBHOOKS_GUMROAD.get(w["recurso"], w["recurso"]), dato=k, negrita=True),
                      celda(w["url"], C["suave"]), celda(f"Cuenta {w.get('_cuenta', 0) + 1}")]
                     for k, w in self.hooks.items()]
            llenar_tabla(self.t, filas)
            self.t.setVisible(bool(filas))
            self.vacio.setVisible(not filas)

        def error(e):
            self.spinner.detener()
            Toast.mostrar(self, "Gumroad", e, "error")

        en_hilo(self.v.gumroad().todos_los_webhooks, ok=ok, error=error)

    def registrar(self):
        base = self.url.text().strip()
        if not base.startswith("https://"):
            sacudir(self.tarjeta)
            Toast.mostrar(self, "Falta la dirección", "Debe empezar por https:// (conecta el servidor de control para "
                                                      "tener una).", "error")
            return
        gr = self.v.gumroad()
        existentes = {(w["recurso"], w["url"], w.get("_cuenta", 0)) for w in self.hooks.values()}
        cuentas = len(getattr(gr, "cuentas", [None]))
        self.spinner.iniciar()

        def trabajar():
            n = 0
            for cuenta in range(cuentas):
                for recurso in EVENTOS_UTILES:
                    url = base + ("&" if "?" in base else "?") + f"recurso={recurso}"
                    if (recurso, url, cuenta) in existentes:
                        continue
                    if hasattr(gr, "cuentas"):
                        gr.crear_webhook(recurso, url, cuenta)
                    else:
                        gr.crear_webhook(recurso, url)
                    n += 1
            return n

        def ok(n):
            self.spinner.detener()
            Toast.mostrar(self, "Webhooks registrados", f"{n} nuevo{'s' if n != 1 else ''}", "ok")
            self.cargar()

        def error(e):
            self.spinner.detener()
            Toast.mostrar(self, "Gumroad", e, "error")

        en_hilo(trabajar, ok=ok, error=error)

    def borrar(self):
        w = self.hooks.get(dato_seleccionado(self.t))
        if not w:
            return
        gr = self.v.gumroad()

        def trabajar():
            if hasattr(gr, "cuentas"):
                gr.borrar_webhook(w["id"], w.get("_cuenta", 0))
            else:
                gr.borrar_webhook(w["id"])

        en_hilo(trabajar, ok=lambda _: self.cargar(), error=lambda e: Toast.mostrar(self, "Gumroad", e, "error"))


# ============================================================ mensaje a muchas personas

class DialogoMensajeMasivo(DialogoBase):
    """Elige a quién, por qué canal y qué decirle. Soporta {nombre}, {producto}, {app} y {clave}."""

    def __init__(self, ventana, producto: str = ""):
        super().__init__(ventana, "Mensaje a muchas personas", ancho=760)
        self.v = ventana
        self.personas: list[dict] = []
        self.cola: list[dict] = []
        self.pila = Pila()
        self.pila.addWidget(self._pagina_redactar(producto))
        self.pila.addWidget(self._pagina_cola())
        self.cuerpo.addWidget(self.pila)
        self._recalcular()

    # ---- redactar
    def _pagina_redactar(self, producto: str) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)
        lay.addWidget(etiqueta("📨  Mensaje a muchas personas", "tituloPagina"))
        self.producto = QComboBox()
        self.producto.addItem("Todos los productos", "")
        for p in self.v.modelo.get("productos", []):
            self.producto.addItem(f"{PLATAFORMAS[p['plataforma']]['icono']}  {p['nombre']}", p["clave"])
        self.producto.setCurrentIndex(max(0, self.producto.findData(producto)))
        self.plataforma = QComboBox()
        self.plataforma.addItem("Todas las plataformas", "")
        for k, p in PLATAFORMAS.items():
            if k in self.v.clientes:
                self.plataforma.addItem(f"{p['icono']}  {p['nombre']}", k)
        self.estado = QComboBox()
        for clave, texto in (("todas", "Todas las personas"), ("con", "Con el programa"), ("sin", "Sin acceso"),
                             ("reembolsos", "Con reembolsos")):
            self.estado.addItem(texto, clave)
        for c in (self.producto, self.plataforma, self.estado):
            c.currentIndexChanged.connect(self._recalcular)
        form = formulario()
        form.addRow("Producto", self.producto)
        form.addRow("Plataforma", self.plataforma)
        form.addRow("Personas", self.estado)
        lay.addLayout(form)
        self.resumen = etiqueta("", "nota", ajustar=True)
        self.resumen.setTextFormat(Qt.TextFormat.RichText)
        lay.addWidget(self.resumen)
        self.canal = Chips([("programa", "📣 En el programa"), ("whatsapp", "WhatsApp"), ("correo", "✉ Correo"),
                            ("copiar", "Copiar correos")])
        self.canal.cambiado.connect(lambda _: self._recalcular())
        lay.addWidget(etiqueta("¿Por dónde?", "tituloTarjeta"))
        lay.addWidget(self.canal)
        self.plantilla = QComboBox()
        for clave, texto in (("novedad", "Novedad / actualización"), ("ayuda", "¿Necesitas ayuda?"),
                             ("oferta", "Oferta para clientes"), ("licencia", "Reenviar su licencia"),
                             ("libre", "Mensaje libre")):
            self.plantilla.addItem(texto, clave)
        self.plantilla.currentIndexChanged.connect(self._plantilla)
        self.titulo = QLineEdit(placeholderText="Asunto / título")
        self.mensaje = QPlainTextEdit()
        self.mensaje.setFixedHeight(110)
        form2 = formulario()
        form2.addRow("Plantilla", self.plantilla)
        form2.addRow("Asunto", self.titulo)
        form2.addRow("Mensaje", self.mensaje)
        lay.addLayout(form2)
        lay.addWidget(etiqueta("Puedes usar <b>{nombre}</b>, <b>{producto}</b>, <b>{app}</b> y <b>{clave}</b>: cada "
                               "persona recibe sus propios datos.", "tenue", ajustar=True))
        self.enviar = boton("📨  Preparar envío", "primario")
        self.enviar.clicked.connect(self._enviar)
        cancelar = boton("Cancelar")
        cancelar.clicked.connect(self.reject)
        self.spinner = Spinner(18)
        lay.addLayout(fila(self.spinner, None, cancelar, self.enviar))
        self._plantilla()
        return w

    def _plantilla(self):
        titulo, mensaje = PLANTILLAS_MENSAJE[self.plantilla.currentData()]
        app = self.v.cfg.get("nombre_app", "")
        self.titulo.setText(titulo.replace("{app}", app))
        self.mensaje.setPlainText(mensaje)

    def _filtro(self) -> dict:
        return {"producto": self.producto.currentData() or "", "plataforma": self.plataforma.currentData() or "",
                "estado": self.estado.currentData()}

    def _recalcular(self, *_):
        self.personas = self.v.destinatarios(self._filtro())
        canal = self.canal.actual()
        con_correo = sum(1 for p in self.personas if p.get("correo"))
        con_tel = sum(1 for p in self.personas if self.v.cfg["telefonos"].get(p["clave"])
                      or self.v.cfg["telefonos"].get((p.get("correo") or "").lower()))
        con_prog = sum(1 for p in self.personas if any(l.get("hash") for l in p["licencias"]))
        alcanzables = {"programa": con_prog, "whatsapp": con_tel, "correo": con_correo, "copiar": con_correo}[canal]
        color = C["ok"] if alcanzables else C["error"]
        self.resumen.setText(f"<b>{len(self.personas)}</b> personas coinciden · alcanzables por este canal: "
                             f"<b style='color:{color}'>{alcanzables}</b>  "
                             f"<span style='color:{C['tenue']}'>(programa {con_prog} · WhatsApp {con_tel} · "
                             f"correo {con_correo})</span>")
        if hasattr(self, "enviar"):
            self.enviar.setEnabled(bool(alcanzables) and (canal != "programa" or self.v.servidor() is not None))
            self.enviar.setToolTip("" if self.enviar.isEnabled() else
                                   "Conecta el servidor de control para avisar dentro del programa."
                                   if canal == "programa" and not self.v.servidor() else "Nadie alcanzable por este canal.")

    def _enviar(self):
        if not self.titulo.text().strip() and self.canal.actual() != "whatsapp" or not self.mensaje.toPlainText().strip():
            sacudir(self.tarjeta)
            return
        canal = self.canal.actual()
        nombre_producto = (self.producto.currentText().split("  ", 1)[-1] if self.producto.currentData() else "")
        args = (list(self.personas), canal, self.titulo.text().strip(), self.mensaje.toPlainText().strip(),
                nombre_producto)
        if canal == "programa":
            self.spinner.iniciar()
            self.enviar.setEnabled(False)

            def ok(r):
                self.spinner.detener()
                self.v.registro_envio("el programa", r["enviados"])
                Toast.mostrar(self.v, "Aviso enviado", f"A {r['enviados']} licencia{'s' if r['enviados'] != 1 else ''}",
                              "ok")
                self.accept()

            def error(e):
                self.spinner.detener()
                self.enviar.setEnabled(True)
                Toast.mostrar(self, "No se pudo enviar", e, "error")

            en_hilo(self.v.enviar_mensaje_masivo, *args, ok=ok, error=error)
            return
        r = self.v.enviar_mensaje_masivo(*args)
        if canal == "copiar":
            self.v.registro_envio("correo (copiado)", r["enviados"])
            Toast.mostrar(self.v, "Correos copiados", f"{r['enviados']} direcciones en el portapapeles", "ok")
            self.accept()
            return
        self.cola, self._canal, self._total = r["cola"], canal, r["enviados"]
        self._indice = 0
        self._pintar_cola()
        self.pila.ir_a(1)

    # ---- cola (WhatsApp / correo)
    def _pagina_cola(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(14)
        self.cola_titulo = etiqueta("", "tituloPagina")
        self.cola_texto = etiqueta("", "nota", ajustar=True)
        self.cola_actual = etiqueta("", "valorFuerte", ajustar=True)
        self.abrir = boton("Abrir el primero  →", "primario")
        self.abrir.clicked.connect(self._abrir_siguiente)
        saltar = boton("Saltar")
        saltar.clicked.connect(self._saltar)
        atras = boton("←  Volver")
        atras.clicked.connect(lambda: self.pila.ir_a(0))
        self.listo = boton("Terminar", "secundario")
        self.listo.clicked.connect(self._terminar)
        lay.addWidget(self.cola_titulo)
        lay.addWidget(self.cola_texto)
        lay.addWidget(self.cola_actual)
        lay.addStretch()
        lay.addLayout(fila(atras, None, saltar, self.listo, self.abrir))
        return w

    def _pintar_cola(self):
        n = len(self.cola)
        quedan = n - self._indice
        wa = self._canal == "whatsapp"
        self.cola_titulo.setText(("💬  Cola de WhatsApp" if wa else "✉  Correos preparados"))
        self.cola_texto.setText(
            ("Se abre WhatsApp con el mensaje ya escrito para cada persona; solo tienes que pulsar enviar. " if wa else
             "Se abre tu programa de correo con los destinatarios en copia oculta (de 40 en 40). ")
            + f"Llevas <b>{self._indice}</b> de <b>{n}</b>.")
        self.cola_texto.setTextFormat(Qt.TextFormat.RichText)
        if quedan > 0:
            sig = self.cola[self._indice]
            self.cola_actual.setText(f"Siguiente: {priv_nombre(sig.get('nombre')) or ''}  "
                                     f"{'· ' + sig['telefono'][-4:].rjust(len(sig['telefono']), '•') if wa else ''}"
                                     f"{'· ' + str(sig.get('cantidad')) + ' destinatarios' if not wa else ''}")
            self.abrir.setText(f"Abrir {self._indice + 1} de {n}  →")
            self.abrir.setEnabled(True)
        else:
            self.cola_actual.setText("¡Listo! Ya abriste todos.")
            self.abrir.setEnabled(False)

    def _abrir_siguiente(self):
        if self._indice < len(self.cola):
            self.v.abrir_url(self.cola[self._indice]["url"])
            self._indice += 1
            self._pintar_cola()

    def _saltar(self):
        if self._indice < len(self.cola):
            self._indice += 1
            self._pintar_cola()

    def _terminar(self):
        self.v.registro_envio("WhatsApp" if self._canal == "whatsapp" else "correo", self._indice)
        self.accept()
