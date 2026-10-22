# CineCaptions · By Cinema Productions
# 5_licencias/administrador/acciones.py — Administrador de Licencias: acciones en masa, productos, cupones, reembolsos y mensajes.
"""Cinema Productions · Administrador de Licencias — acciones nuevas de la versión 6.

Son métodos de la ventana principal (se mezclan con `Ventana`). Todo lo que habla con una tienda se ejecuta en
segundo plano y, al terminar, refresca el panel. Las confirmaciones pasan por `self.confirmar`, que la ventana
define (así las pruebas pueden contestar sin abrir ventanas).

  - Cuentas de Gumroad (varios tokens) y webhooks.
  - Productos: publicar/ocultar, cupones, avisar o bloquear a todos sus compradores.
  - Licencias en masa: bloquear, reactivar, liberar usos, avisar, retirar.
  - Ventas: reembolsar (total o parcial) y reenviar el recibo.
  - Mensajes a muchas personas: aviso dentro del programa, WhatsApp en cola y correo.

Creado por Cinema Productions.
"""
from __future__ import annotations

import re
import urllib.parse

from PySide6.QtWidgets import QApplication

from interfaz import en_hilo, priv_nombre
from modelo import solo_digitos
from plataformas import PLATAFORMAS, ErrorApi, Gumroad

__author__ = "Cinema Productions"

LIMITE_CORREOS = 40          # destinatarios por correo (los programas de correo cortan los enlaces muy largos)
PLANTILLAS_MENSAJE = {
    "novedad": ("Novedad en {app}", "Hola {nombre}, lanzamos una actualización de {app}. Descárgala desde tu enlace de "
                                    "compra de {producto}. ¡Gracias por tu apoyo!"),
    "ayuda": ("¿Necesitas ayuda con {app}?", "Hola {nombre}, soy del equipo de {app}. Si tienes cualquier duda con "
                                             "{producto}, responde a este mensaje y te ayudo."),
    "oferta": ("Oferta para ti", "Hola {nombre}, por ser cliente de {producto} tienes un descuento en nuestros "
                                 "otros productos. Escríbeme y te comparto el código."),
    "licencia": ("Tu licencia de {app}", "Hola {nombre}, aquí está tu licencia de {producto}:\n\n{clave}\n\nAbre el "
                                         "programa, pega la clave en la ventana de activación y presiona Activar."),
    "libre": ("", ""),
}


def rellenar(texto: str, **datos) -> str:
    """Cambia {nombre}, {producto}, {app}, {clave}… sin romperse si falta alguno."""
    class _Seguro(dict):
        def __missing__(self, clave):
            return "{" + clave + "}"
    return texto.format_map(_Seguro(**datos))


class AccionesExtra:
    """Se mezcla con la ventana principal (necesita: cfg, clientes, modelo, accion, aviso, servidor, guardar…)."""

    # ---------------------------------------------------------------- ayudas
    def confirmar(self, titulo: str, texto: str, si: str = "Sí", peligro: bool = True) -> bool:
        from interfaz import preguntar
        return preguntar(self, titulo, texto, si, peligro=peligro)

    def gumroad(self) -> Gumroad | None:
        return self.clientes.get("gumroad")

    def _licencias(self, ids) -> list[dict]:
        return [l for i in ids if (l := self.modelo["lic_por_id"].get(i))]

    # ---------------------------------------------------------------- cuentas de Gumroad
    def cuentas_gumroad(self) -> list[dict]:
        """[{'token','nombre','correo'}…] con la principal primero."""
        pc = self.cfg["plataformas"].get("gumroad") or {}
        cuentas = []
        if pc.get("token"):
            cuentas.append({"token": pc["token"], "nombre": pc.get("cuenta", ""), "correo": pc.get("correo", "")})
        cuentas += [dict(c) for c in pc.get("cuentas") or [] if c.get("token")]
        return cuentas

    def guardar_cuentas_gumroad(self, cuentas: list[dict]):
        """La primera cuenta es la principal; las demás van en `cuentas`. Sin cuentas = desconectar."""
        pc = dict(self.cfg["plataformas"].get("gumroad") or {})
        if not cuentas:
            self.cfg["plataformas"]["gumroad"] = {}
            self.guardar()
            self._quitar_conexion("gumroad", "Gumroad")
            return
        pc.update(token=cuentas[0]["token"], cuenta=cuentas[0].get("nombre", ""), correo=cuentas[0].get("correo", ""),
                  cuentas=[{k: c.get(k, "") for k in ("token", "nombre", "correo")} for c in cuentas[1:]])
        self._guardar_conexion("gumroad", pc)

    def recordar_datos_cuentas(self, cuentas: list[dict]):
        """Guarda los nombres y correos de las cuentas sin volver a conectar nada."""
        pc = self.cfg["plataformas"].get("gumroad") or {}
        if not cuentas or not pc.get("token"):
            return
        pc["cuenta"], pc["correo"] = cuentas[0].get("nombre", ""), cuentas[0].get("correo", "")
        extras = {c["token"]: c for c in cuentas[1:]}
        for c in pc.get("cuentas") or []:
            if c.get("token") in extras:
                c["nombre"], c["correo"] = extras[c["token"]].get("nombre", ""), extras[c["token"]].get("correo", "")
        self.guardar()

    def abrir_cuentas_gumroad(self):
        from dialogos_nuevos import DialogoCuentasGumroad
        DialogoCuentasGumroad(self).exec()

    # ---------------------------------------------------------------- licencias en masa
    def bloquear_licencias(self, lics: list[dict], bloquear: bool, estado_srv: str = "revocada") -> bool:
        lics = [l for l in lics if l]
        if not lics:
            return False
        n = len(lics)
        nombres = ", ".join(priv_nombre(l.get("user_name") or l.get("user_email")) for l in lics[:3]) + \
            (f" y {n - 3} más" if n > 3 else "")
        if not self.confirmar("Bloquear licencias" if bloquear else "Reactivar licencias",
                              (f"¿Bloquear <b>{n}</b> licencia{'s' if n > 1 else ''} ({nombres})?<br><br>Sus programas se "
                               "cerrarán y pedirán licencia." if bloquear else
                               f"¿Reactivar <b>{n}</b> licencia{'s' if n > 1 else ''} ({nombres})?<br><br>Sus programas "
                               "volverán a funcionar solos."),
                              "Sí, bloquear" if bloquear else "Sí, reactivar", peligro=bloquear):
            return False
        srv, app = self.servidor(), self.cfg.get("nombre_app", "")
        avisar = self.cfg.get("avisar_al_bloquear", True) and not bloquear

        def trabajar():
            fallos = []
            for lic in lics:
                try:
                    if bool(lic.get("disabled")) != bloquear or not bloquear:
                        self._bloquear_en_tienda(lic, bloquear)
                    if srv and lic.get("hash"):
                        srv.fijar_estado(lic["hash"], estado_srv if bloquear else "activa",
                                         "El vendedor retiró esta licencia." if bloquear else "")
                except Exception as e:  # noqa: BLE001
                    fallos.append(f"{priv_nombre(lic.get('user_name') or lic.get('user_email'))}: {e}")
            hashes = [l["hash"] for l in lics if l.get("hash")]
            if avisar and srv and hashes:
                srv.enviar_aviso(hashes, "reactivada", f"Tu licencia de {app} está activa otra vez",
                                 "El vendedor reactivó tu licencia. Ya puedes seguir usando el programa.")
            return fallos

        def despues(fallos):
            for lic in lics:
                self._gumroad_bloqueadas(lic, bloquear)
                if not bloquear:
                    self.cfg["auto_bloqueadas"].pop(lic["id"], None)
            self._registrar(f"{'Bloqueó' if bloquear else 'Reactivó'} {n} licencia{'s' if n > 1 else ''} en masa",
                            lics[0])
            self.guardar()
            if fallos:
                self.aviso(f"{len(fallos)} no se pudieron cambiar", fallos[0], "error")

        self.accion(trabajar, mensaje=f"{n} licencia{'s' if n > 1 else ''} " +
                    ("bloqueada" if bloquear else "reactivada") + ("s" if n > 1 else ""), despues=despues)
        return True

    def liberar_usos(self, lics: list[dict]) -> bool:
        """Resta un uso a cada clave de Gumroad (para que puedan activarla en otra computadora)."""
        gr = self.gumroad()
        lics = [l for l in lics if l and l["plataforma"] == "gumroad"]
        if not gr or not lics:
            self.aviso("Solo Gumroad", "Liberar usos aplica a las claves de Gumroad.", "info")
            return False
        n = len(lics)
        if not self.confirmar("Liberar un uso", f"¿Restar un uso a <b>{n}</b> clave{'s' if n > 1 else ''} de Gumroad?",
                              "Sí, liberar", peligro=False):
            return False

        def trabajar():
            return {l["key"]: gr.liberar_uso(self._producto_gumroad(l), l["key"]) for l in lics}

        self.accion(trabajar, mensaje=f"{n} uso{'s' if n > 1 else ''} liberado{'s' if n > 1 else ''}",
                    despues=lambda r: self.usos_gumroad.update(r))
        return True

    def avisar_licencias(self, lics: list[dict], tipo: str = "info"):
        """Abre «Nuevo aviso» con esas licencias como destinatarias."""
        lics = [l for l in lics if l and l.get("hash")]
        if not self.servidor():
            self.conectar_servidor()
            return
        if not lics:
            self.aviso("Sin destinatarios", "Esas licencias no tienen huella en el servidor de control.", "info")
            return
        self._aviso_a_hashes([l["hash"] for l in lics], f"{len(lics)} licencia{'s' if len(lics) > 1 else ''} elegida"
                             f"{'s' if len(lics) > 1 else ''}", tipo)

    def _aviso_a_hashes(self, hashes: list[str], descripcion: str, tipo: str = "info"):
        from dialogos import DialogoAviso
        d = DialogoAviso([(f"👥  {descripcion}", hashes)], self.cfg.get("nombre_app", ""), self, 0, tipo)
        if d.exec() != DialogoAviso.DialogCode.Accepted:
            return
        datos = d.datos()

        def creado(filas):
            if datos["bloquear"] and filas:
                ids = [l["id"] for l in self.modelo["licencias"] if l.get("hash") in set(hashes)]
                self.cfg["remociones"][str(filas[0]["id"])] = {"licencias": ids, "fecha": datos["fecha_limite"],
                                                               "destino": datos["destino"]}
                self.guardar()

        self.accion(self.servidor().enviar_aviso, hashes, datos["tipo"], datos["titulo"], datos["mensaje"],
                    datos["fecha_limite"], mensaje="Aviso enviado", despues=creado)

    # ---------------------------------------------------------------- productos
    def producto(self, clave: str) -> dict | None:
        return self.modelo.get("producto_por_clave", {}).get(clave)

    def licencias_de_producto(self, p: dict) -> list[dict]:
        return self._licencias(p.get("lic_ids") or [])

    def bloquear_producto(self, p: dict, bloquear: bool) -> bool:
        return self.bloquear_licencias(self.licencias_de_producto(p), bloquear)

    def avisar_producto(self, p: dict):
        lics = [l for l in self.licencias_de_producto(p) if l.get("hash")]
        if not self.servidor():
            self.conectar_servidor()
            return
        if not lics:
            self.aviso("Sin compradores con licencia", "Este producto no tiene licencias conectadas al servidor de "
                                                      "control.", "info")
            return
        self._aviso_a_hashes([l["hash"] for l in lics], f"Compradores de {p['nombre']} ({len(lics)})")

    def publicar_producto(self, p: dict, publicar: bool) -> bool:
        gr = self.gumroad()
        if not gr or p["plataforma"] != "gumroad":
            self.aviso("Solo Gumroad", "Publicar u ocultar desde aquí funciona con productos de Gumroad.", "info")
            return False
        if not self.confirmar("Publicar producto" if publicar else "Ocultar producto",
                              f"¿{'Publicar' if publicar else 'Ocultar'} <b>{p['nombre']}</b> en Gumroad?<br><br>"
                              + ("Volverá a estar a la venta." if publicar else
                                 "Nadie podrá comprarlo hasta que lo publiques otra vez. Los clientes actuales no se "
                                 "ven afectados."), "Sí, publicar" if publicar else "Sí, ocultar", peligro=not publicar):
            return False
        self.accion(gr.publicar_producto, p["id"], publicar,
                    mensaje="Producto publicado" if publicar else "Producto oculto")
        return True

    def abrir_producto(self, p: dict):
        if p.get("url"):
            self.abrir_url(p["url"])
        else:
            self.aviso("Sin enlace", "Esta plataforma no entregó el enlace de compra de este producto.", "info")

    def crear_cupon(self, p: dict):
        gr = self.gumroad()
        if not gr or p["plataforma"] != "gumroad":
            self.aviso("Solo Gumroad", "Los cupones se crean en Gumroad.", "info")
            return
        from dialogos_nuevos import DialogoCupon
        d = DialogoCupon(p, self)
        if d.exec() != DialogoCupon.DialogCode.Accepted:
            return
        c = d.datos()

        def listo(r):
            self.aviso("Cupón creado", f"{r.get('name') or c['nombre']} · {p['nombre']}", "ok")

        self.accion(gr.crear_codigo, p["id"], c["nombre"], c["valor"], c["porcentaje"], c["usos_max"],
                    despues=listo)

    def ver_cupones(self, p: dict):
        if not self.gumroad() or p["plataforma"] != "gumroad":
            self.aviso("Solo Gumroad", "Los cupones se crean en Gumroad.", "info")
            return
        from dialogos_nuevos import DialogoCupones
        DialogoCupones(p, self).exec()

    # ---------------------------------------------------------------- ventas
    def puede_reembolsar(self, venta: dict) -> bool:
        cliente = self.clientes.get(venta["plataforma"])
        return bool(cliente and getattr(cliente, "puede_reembolsar", False) and venta.get("valida"))

    def reembolsar_venta(self, venta: dict, parcial: bool = False) -> bool:
        cliente = self.clientes.get(venta["plataforma"])
        nombre_pl = PLATAFORMAS[venta["plataforma"]]["nombre"]
        if not cliente or not getattr(cliente, "puede_reembolsar", False):
            self.aviso(f"Hazlo en {nombre_pl}", f"{nombre_pl} no permite reembolsar desde el panel. Abre su sitio web.",
                       "info")
            return False
        centavos = 0
        if parcial:
            from interfaz import pedir_texto
            texto = pedir_texto(self, "Reembolso parcial", f"¿Cuánto reembolsar de {venta['total_txt']}? (número, en "
                                f"{venta['moneda'] or 'la moneda de la venta'})", "", "5.00")
            if not texto:
                return False
            try:
                centavos = int(round(float(texto.replace(",", ".")) * 100))
            except ValueError:
                self.aviso("Número no válido", "Escribe solo el monto, por ejemplo 5.00", "error")
                return False
        quien = priv_nombre(venta["cliente"] or venta["correo"])
        if not self.confirmar("Reembolsar compra",
                              f"¿Reembolsar {'<b>parte</b> de ' if parcial else ''}la compra de <b>{quien}</b> "
                              f"({venta['total_txt']}) en {nombre_pl}?<br><br>El dinero se devuelve al comprador y "
                              "<b>no se puede deshacer</b>."
                              + ("<br>Su licencia se bloqueará sola en el siguiente refresco." if not parcial else ""),
                              "Sí, reembolsar"):
            return False
        gumroad = isinstance(cliente, Gumroad)
        args = (venta["id_api"], centavos) if gumroad else (venta, centavos)
        self.accion(cliente.reembolsar, *args, mensaje="Reembolso hecho",
                    despues=lambda _: self._registrar(f"Reembolsó la compra de {venta['producto']}",
                                                      {"user_name": venta["cliente"], "user_email": venta["correo"],
                                                       "plataforma": venta["plataforma"]}))
        return True

    def reenviar_recibo(self, venta: dict) -> bool:
        gr = self.gumroad()
        if not gr or venta["plataforma"] != "gumroad":
            self.aviso("Solo Gumroad", "Reenviar el recibo funciona con ventas de Gumroad.", "info")
            return False
        self.accion(gr.reenviar_recibo, venta["id_api"], mensaje="Recibo reenviado")
        return True

    # ---------------------------------------------------------------- webhooks
    def abrir_webhooks(self):
        if not self.gumroad():
            self.conectar("gumroad")
            return
        from dialogos_nuevos import DialogoWebhooks
        DialogoWebhooks(self).exec()

    def url_webhook(self) -> str:
        """URL de la función gumroad_webhook en tu Supabase (con tu secreto)."""
        sv = self.cfg.get("servidor") or {}
        if not sv.get("url"):
            return ""
        secreto = self.cfg.setdefault("webhook_secreto", "")
        if not secreto:
            import secrets
            secreto = self.cfg["webhook_secreto"] = secrets.token_urlsafe(24)
            self.guardar()
        return f"{sv['url'].rstrip('/')}/functions/v1/gumroad-webhook?secreto={secreto}"

    # ---------------------------------------------------------------- mensajes a muchas personas
    def destinatarios(self, filtro: dict) -> list[dict]:
        """Personas que cumplen el filtro: producto (clave), plataforma, estado ('con','sin','reembolsos','todas'),
        y 'solo_contacto' (con teléfono o correo)."""
        m = self.modelo
        producto = filtro.get("producto") or ""
        claves_producto = set((m["producto_por_clave"].get(producto) or {}).get("personas_claves") or [])
        res = []
        for p in m["personas"]:
            if producto and p["clave"] not in claves_producto:
                continue
            if filtro.get("plataforma") and filtro["plataforma"] not in p["plataformas"]:
                continue
            est = filtro.get("estado") or "todas"
            if (est == "con" and not p["tiene"]) or (est == "sin" and p["tiene"]) or \
                    (est == "reembolsos" and not p["reembolsos"]):
                continue
            res.append(p)
        return res

    def enviar_mensaje_masivo(self, personas: list[dict], canal: str, titulo: str, texto: str,
                              producto: str = "") -> dict:
        """Prepara el envío y devuelve lo que hizo. canal: 'programa' | 'whatsapp' | 'correo' | 'copiar'.

        - programa: un aviso dentro del programa a las licencias de esas personas (servidor de control).
        - whatsapp: devuelve la cola de enlaces wa.me (la ventana los abre uno por uno).
        - correo: abre el programa de correo con los destinatarios en copia oculta, de 40 en 40.
        - copiar: copia los correos separados por coma.
        """
        app = self.cfg.get("nombre_app", "")
        r = {"canal": canal, "enviados": 0, "sin_dato": 0, "cola": []}
        if canal == "programa":
            srv = self.servidor()
            hashes = [l["hash"] for p in personas for l in p["licencias"] if l.get("hash")]
            if not srv:
                raise ErrorApi("Conecta el servidor de control para avisar dentro del programa.")
            if not hashes:
                r["sin_dato"] = len(personas)
                return r
            srv.enviar_aviso(sorted(set(hashes)), "info", rellenar(titulo, app=app, producto=producto, nombre=""),
                             rellenar(texto, app=app, producto=producto, nombre="", clave=""))
            r["enviados"] = len(set(hashes))
            return r
        if canal == "whatsapp":
            for p in personas:
                tel = solo_digitos(self.cfg["telefonos"].get(p["clave"]) or self.cfg["telefonos"].get(
                    (p.get("correo") or "").lower(), ""))
                if not tel:
                    r["sin_dato"] += 1
                    continue
                clave = p["licencias"][0]["key"] if p["licencias"] else ""
                cuerpo = rellenar(texto, nombre=p["nombre"] or "", app=app, producto=producto
                                  or (p["productos"][0] if p.get("productos") else app), clave=clave)
                r["cola"].append({"persona": p["clave"], "nombre": p["nombre"], "telefono": tel,
                                  "url": f"https://wa.me/{tel}?text={urllib.parse.quote(cuerpo)}"})
            r["enviados"] = len(r["cola"])
            return r
        correos = sorted({(p.get("correo") or "").strip() for p in personas if p.get("correo")})
        r["sin_dato"] = len(personas) - len(correos)
        if canal == "copiar":
            QApplication.clipboard().setText(", ".join(correos))
            r["enviados"] = len(correos)
            return r
        asunto = rellenar(titulo, app=app, producto=producto, nombre="")
        cuerpo = rellenar(texto, nombre="", app=app, producto=producto, clave="")
        for i in range(0, len(correos), LIMITE_CORREOS):
            lote = correos[i:i + LIMITE_CORREOS]
            r["cola"].append({"url": f"mailto:?bcc={urllib.parse.quote(','.join(lote))}&subject="
                                     f"{urllib.parse.quote(asunto)}&body={urllib.parse.quote(cuerpo)}",
                              "cantidad": len(lote)})
        r["enviados"] = len(correos)
        return r

    def abrir_mensaje_masivo(self, producto: str = ""):
        from dialogos_nuevos import DialogoMensajeMasivo
        DialogoMensajeMasivo(self, producto).exec()

    def registro_envio(self, canal: str, n: int):
        self._registrar(f"Mensaje a {n} persona{'s' if n != 1 else ''} por {canal}")
        self.guardar()

    # ---------------------------------------------------------------- selección de plataformas
    @staticmethod
    def limpiar_nombre_producto(texto: str) -> str:
        return re.sub(r"\s+", " ", texto or "").strip()
