# CineCaptions · By Cinema Productions
# 5_licencias/administrador/plataformas_extra.py — Administrador de Licencias: Stripe, Paddle, PayPal, FastSpring y Whop.
"""Cinema Productions · Administrador de Licencias — plataformas de venta adicionales.

Para cuando vendas tu programa o tu SaaS en más sitios: Stripe, Paddle, PayPal, FastSpring y Whop.
Todas devuelven las ventas con la MISMA forma que las demás (ver `venta_base`), así que aparecen en Personas,
Ventas, Productos e Inicio igual que las de Lemon Squeezy o Gumroad.

Estas plataformas no generan claves de licencia que el kit sepa validar: sirven para ver ventas, compradores,
reembolsos e ingresos (y reembolsar desde el panel en Stripe y Paddle). Para dar acceso al programa a esos
compradores usa «Dar licencia» (licencia gratis en Lemon Squeezy) o el servidor de control.

Creado por Cinema Productions.
"""
from __future__ import annotations

import base64
import json
import threading
import time
import urllib.parse
from datetime import datetime, timedelta, timezone

from plataformas import ErrorApi, _detalle, _http, dinero, resumen_ventas

__author__ = "Cinema Productions"

STRIPE_API = "https://api.stripe.com/v1/"
PADDLE_API = {False: "https://api.paddle.com", True: "https://sandbox-api.paddle.com"}
PAYPAL_API = {False: "https://api-m.paypal.com", True: "https://api-m.sandbox.paypal.com"}
FASTSPRING_API = "https://api.fastspring.com"
WHOP_API = "https://api.whop.com/api/v5"

MONEDAS_SIN_DECIMALES = {"BIF", "CLP", "DJF", "GNF", "JPY", "KMF", "KRW", "MGA", "PYG", "RWF", "UGX", "VND", "VUV",
                         "XAF", "XOF", "XPF"}


def _iso(valor) -> str | None:
    """Segundos (o milisegundos) Unix, o un texto ISO → ISO UTC."""
    if valor in (None, ""):
        return None
    if isinstance(valor, str) and not valor.replace(".", "", 1).isdigit():
        return valor
    try:
        n = float(valor)
        n = n / 1000 if n > 1e11 else n
        return datetime.fromtimestamp(n, timezone.utc).isoformat()
    except (TypeError, ValueError, OverflowError, OSError):
        return None


def _monto(menor, moneda: str) -> float | None:
    """Pasa la unidad menor (centavos) a la unidad normal según la moneda."""
    try:
        n = float(menor)
    except (TypeError, ValueError):
        return None
    return n if (moneda or "").upper() in MONEDAS_SIN_DECIMALES else n / 100


def venta_base(plataforma: str, prefijo: str, id_, **campos) -> dict:
    """Forma común de una venta en todo el panel."""
    moneda = (campos.pop("moneda", "") or "").upper()
    total = campos.pop("total", None)
    estado = campos.pop("estado", "Pagada")
    valida = campos.pop("valida", True)
    v = {"plataforma": plataforma, "id": f"{prefijo}-{id_}", "id_api": id_, "referencia": str(id_), "fecha": None,
         "cliente": "", "correo": "", "producto": "", "producto_id": None, "total": total, "moneda": moneda,
         "total_txt": dinero(total, moneda) if total is not None else "—", "estado": estado, "valida": valida,
         "reembolso": None, "recibo": "", "prueba": False, "clave_licencia": "", "pais": "", "cupon": "",
         "variante": "", "suscripcion": "", "cancelada": False, "cantidad": 1, "cuenta": 0}
    v.update(campos)
    if not valida and estado in ("Reembolsada", "Contracargo") and not v["reembolso"]:
        v["reembolso"] = v["fecha"]
    return v


def producto_base(id_, nombre: str, precio: float | None = None, moneda: str = "", activo: bool = True,
                  url: str = "", imagen: str = "", descripcion: str = "") -> dict:
    return {"id": id_, "nombre": nombre or str(id_), "precio": precio, "moneda": (moneda or "").upper(),
            "precio_txt": dinero(precio, moneda.upper()) if precio is not None else "", "activo": activo,
            "url": url, "imagen": imagen, "descripcion": descripcion}


class PlataformaVentas:
    """Base: ventas + productos con caché corta. Cada plataforma implementa `_productos` y `_ventas`."""
    clave = ""
    nombre = ""
    puede_reembolsar = False

    def __init__(self):
        self._cache: tuple[float, tuple, list] | None = None
        self._cache_prod: tuple[float, list] | None = None
        self._lock = threading.Lock()

    # a implementar
    def _cuenta(self) -> dict:
        return {"nombre": self.nombre, "correo": ""}

    def _productos(self) -> list[dict]:
        return []

    def _ventas(self) -> list[dict]:
        return []

    def entorno(self) -> str:
        return ""

    # común
    def productos(self, max_edad: float = 60) -> list[dict]:
        if self._cache_prod and time.time() - self._cache_prod[0] < max_edad:
            return self._cache_prod[1]
        lista = self._productos()
        self._cache_prod = (time.time(), lista)
        return lista

    def ventas(self, producto_id="", max_edad: float = 60) -> list[dict]:
        clave = (producto_id,)
        if self._cache and self._cache[1] == clave and time.time() - self._cache[0] < max_edad:
            return self._cache[2]
        ventas = self._ventas()
        if producto_id:
            ventas = [v for v in ventas if str(v.get("producto_id")) == str(producto_id)]
        ventas.sort(key=lambda v: v.get("fecha") or "", reverse=True)
        self._cache = (time.time(), clave, ventas)
        return ventas

    def conectar(self, producto_id="") -> dict:
        cuenta = self._cuenta()
        ventas = self.ventas(producto_id, max_edad=0)
        return {"plataforma": self.clave, "cuenta": cuenta, "entorno": self.entorno(),
                "productos": self.productos(0), **resumen_ventas(ventas)}

    def cargar(self, pc: dict | None = None) -> dict:
        pc = pc or {}
        return {"ventas": self.ventas(pc.get("producto_id") or ""), "productos": self.productos()}

    def reembolsar(self, venta: dict, centavos: int = 0):
        raise ErrorApi(f"{self.nombre} no permite reembolsar desde el panel. Hazlo en su sitio web.")

    # ayuda para los errores comunes
    def _error(self, e: ErrorApi, mensajes: dict | None = None) -> ErrorApi:
        base = {0: str(e), 401: f"{self.nombre} rechazó las credenciales. Vuelve a conectarlas.",
                403: f"Tus credenciales de {self.nombre} no tienen permiso para esto.",
                429: f"Demasiadas peticiones a {self.nombre}. Espera un minuto."} | (mensajes or {})
        return ErrorApi(base.get(e.codigo, f"Error de {self.nombre} ({e.codigo}). {_detalle(e.cuerpo)}").strip()
                        if e.codigo else str(e), e.codigo, e.cuerpo)


# ============================================================ Stripe

class Stripe(PlataformaVentas):
    clave, nombre = "stripe", "Stripe"
    puede_reembolsar = True

    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key.strip()

    def entorno(self) -> str:
        return "Pruebas (sk_test)" if "_test_" in self.api_key else "Producción"

    def _req(self, metodo: str, ruta: str, datos: dict | None = None):
        cab = {"Authorization": f"Bearer {self.api_key}", "Accept": "application/json"}
        url, cuerpo = STRIPE_API + ruta, None
        datos = {k: v for k, v in (datos or {}).items() if v not in (None, "")}
        if metodo == "GET":
            url += ("?" + urllib.parse.urlencode(datos, doseq=True)) if datos else ""
        else:
            cuerpo = urllib.parse.urlencode(datos, doseq=True).encode()
            cab["Content-Type"] = "application/x-www-form-urlencoded"
        try:
            return _http(metodo, url, cab, cuerpo) or {}
        except ErrorApi as e:
            err = (e.cuerpo or {}).get("error") if isinstance(e.cuerpo, dict) else None
            raise self._error(e, {400: (err or {}).get("message", "Stripe rechazó la petición.")}) from e

    def _todas(self, ruta: str, consulta: dict | None = None, max_paginas: int = 60) -> list[dict]:
        items, despues = [], None
        for _ in range(max_paginas):
            r = self._req("GET", ruta, {"limit": 100} | (consulta or {}) | ({"starting_after": despues} if despues else {}))
            pagina = r.get("data") or []
            items += pagina
            if not r.get("has_more") or not pagina:
                break
            despues = pagina[-1]["id"]
        return items

    def _cuenta(self) -> dict:
        try:
            a = self._req("GET", "account")
        except ErrorApi as e:
            if e.codigo in (401,):
                raise
            a = {}          # las claves restringidas pueden no tener permiso de ver la cuenta
        nombre = ((a.get("business_profile") or {}).get("name") or (a.get("settings") or {}).get("dashboard", {})
                  .get("display_name") or "Stripe")
        self._req("GET", "charges", {"limit": 1})       # comprueba que la clave puede leer cobros
        return {"nombre": nombre, "correo": a.get("email") or "", "id": a.get("id") or "", "pais": a.get("country")}

    def _productos(self) -> list[dict]:
        salida = []
        for p in self._todas("products", {"expand[]": "data.default_price"}):
            precio = p.get("default_price") if isinstance(p.get("default_price"), dict) else {}
            moneda = (precio.get("currency") or "").upper()
            salida.append(producto_base(p["id"], p.get("name"), _monto(precio.get("unit_amount"), moneda)
                                        if precio else None, moneda, bool(p.get("active", True)),
                                        imagen=(p.get("images") or [""])[0], descripcion=p.get("description") or ""))
        return salida

    def _ventas(self) -> list[dict]:
        salida = []
        for c in self._todas("charges", {"expand[]": "data.customer"}):
            if c.get("status") not in ("succeeded",) and not c.get("refunded"):
                continue
            moneda = (c.get("currency") or "").upper()
            total = _monto(c.get("amount"), moneda)
            cliente = c.get("customer") if isinstance(c.get("customer"), dict) else {}
            det = c.get("billing_details") or {}
            reembolsada, parcial = bool(c.get("refunded")), (c.get("amount_refunded") or 0) > 0
            disputada = bool(c.get("disputed"))
            estado = ("En disputa" if disputada else "Reembolsada" if reembolsada
                      else "Reembolso parcial" if parcial else "Pagada")
            meta = c.get("metadata") or {}
            salida.append(venta_base(
                "stripe", "st", c["id"], fecha=_iso(c.get("created")),
                cliente=det.get("name") or cliente.get("name") or "",
                correo=det.get("email") or c.get("receipt_email") or cliente.get("email") or "",
                producto=meta.get("producto") or meta.get("product") or c.get("description") or "Pago de Stripe",
                producto_id=meta.get("product_id") or meta.get("producto_id") or None,
                total=total, moneda=moneda, estado=estado, valida=not (reembolsada or disputada),
                recibo=c.get("receipt_url") or "", prueba=not c.get("livemode", True),
                pais=((c.get("billing_details") or {}).get("address") or {}).get("country") or "",
                reembolso=_iso(c.get("created")) if reembolsada else None))
        return salida

    def reembolsar(self, venta: dict, centavos: int = 0):
        self._req("POST", "refunds", {"charge": venta["id_api"], "amount": centavos or None})
        self._cache = None


# ============================================================ Paddle

class Paddle(PlataformaVentas):
    clave, nombre = "paddle", "Paddle"
    puede_reembolsar = True

    def __init__(self, api_key: str, sandbox: bool = False):
        super().__init__()
        self.api_key, self.sandbox = api_key.strip(), bool(sandbox)

    def entorno(self) -> str:
        return "Sandbox (pruebas)" if self.sandbox else "Producción"

    def _req(self, metodo: str, ruta: str, consulta: dict | None = None, cuerpo=None):
        url = ruta if ruta.startswith("http") else PADDLE_API[self.sandbox] + ruta
        if consulta:
            url += ("&" if "?" in url else "?") + urllib.parse.urlencode(consulta)
        cab = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        try:
            return _http(metodo, url, cab, json.dumps(cuerpo).encode() if cuerpo is not None else None) or {}
        except ErrorApi as e:
            raise self._error(e, {400: _detalle(e.cuerpo) or "Paddle rechazó la petición."}) from e

    def _todas(self, ruta: str, consulta: dict | None = None, max_paginas: int = 60) -> list[dict]:
        items, url, q = [], ruta, consulta
        for _ in range(max_paginas):
            r = self._req("GET", url, q)
            items += r.get("data") or []
            p = (r.get("meta") or {}).get("pagination") or {}
            if not p.get("has_more") or not p.get("next"):
                break
            url, q = p["next"], None
        return items

    def _cuenta(self) -> dict:
        self._req("GET", "/products", {"per_page": 1})
        return {"nombre": "Paddle", "correo": ""}

    def _productos(self) -> list[dict]:
        precios: dict = {}
        for pr in self._todas("/prices", {"per_page": 200}):
            u = pr.get("unit_price") or {}
            precios.setdefault(pr.get("product_id"), (_monto(u.get("amount"), u.get("currency_code")),
                                                      u.get("currency_code")))
        salida = []
        for p in self._todas("/products", {"per_page": 200}):
            precio, moneda = precios.get(p["id"], (None, ""))
            salida.append(producto_base(p["id"], p.get("name"), precio, moneda or "", p.get("status") == "active",
                                        imagen=p.get("image_url") or "", descripcion=p.get("description") or ""))
        return salida

    def _ventas(self) -> list[dict]:
        reembolsos: dict[str, float] = {}
        try:
            for a in self._todas("/adjustments", {"action": "refund", "status": "approved", "per_page": 200}):
                t = a.get("totals") or {}
                reembolsos[a.get("transaction_id")] = reembolsos.get(a.get("transaction_id"), 0) + (
                    _monto(t.get("total"), a.get("currency_code")) or 0)
        except ErrorApi:
            pass
        salida = []
        for t in self._todas("/transactions", {"per_page": 200, "include": "customer",
                                               "status": "completed,paid,billed,canceled"}):
            if t.get("status") == "canceled":
                continue
            moneda = t.get("currency_code") or ""
            total = _monto(((t.get("details") or {}).get("totals") or {}).get("grand_total")
                           or ((t.get("details") or {}).get("totals") or {}).get("total"), moneda)
            devuelto = reembolsos.get(t["id"], 0)
            completo = bool(total) and devuelto >= total - 0.005
            estado = "Reembolsada" if completo else "Reembolso parcial" if devuelto else "Pagada"
            linea = ((t.get("details") or {}).get("line_items") or [{}])[0]
            producto = linea.get("product") or {}
            cliente = t.get("customer") or {}
            salida.append(venta_base(
                "paddle", "pd", t["id"], fecha=_iso(t.get("billed_at") or t.get("created_at")),
                cliente=cliente.get("name") or "", correo=cliente.get("email") or "",
                producto=producto.get("name") or "", producto_id=producto.get("id"), total=total, moneda=moneda,
                estado=estado, valida=not completo, suscripcion=t.get("subscription_id") or "",
                cupon=t.get("discount_id") or "", prueba=self.sandbox,
                reembolso=_iso(t.get("updated_at")) if completo else None))
        return salida

    def reembolsar(self, venta: dict, centavos: int = 0):
        t = self._req("GET", f"/transactions/{venta['id_api']}")
        items = ((t.get("data") or {}).get("details") or {}).get("line_items") or []
        self._req("POST", "/adjustments", cuerpo={
            "action": "refund", "transaction_id": venta["id_api"], "reason": "Reembolso pedido por el vendedor",
            "type": "full", "items": [{"item_id": i["id"], "type": "full"} for i in items]})
        self._cache = None


# ============================================================ PayPal

class PayPal(PlataformaVentas):
    clave, nombre = "paypal", "PayPal"
    MESES = 12

    def __init__(self, client_id: str, client_secret: str, sandbox: bool = False):
        super().__init__()
        self.client_id, self.client_secret, self.sandbox = client_id.strip(), client_secret.strip(), bool(sandbox)
        self._token, self._vence = "", 0.0

    def entorno(self) -> str:
        return "Sandbox (pruebas)" if self.sandbox else "Producción"

    def token(self) -> str:
        with self._lock:
            if self._token and time.time() < self._vence - 120:
                return self._token
            basic = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
            try:
                r = _http("POST", PAYPAL_API[self.sandbox] + "/v1/oauth2/token",
                          {"Authorization": f"Basic {basic}", "Content-Type": "application/x-www-form-urlencoded"},
                          b"grant_type=client_credentials") or {}
            except ErrorApi as e:
                if e.codigo in (400, 401):
                    raise ErrorApi("PayPal rechazó el Client ID o el Secret (revisa que sean de producción o de "
                                   "sandbox según elegiste).", e.codigo) from e
                raise self._error(e) from e
            self._token = r.get("access_token") or ""
            if not self._token:
                raise ErrorApi("PayPal no devolvió un token de acceso.")
            self._vence = time.time() + float(r.get("expires_in") or 3000)
            return self._token

    def _get(self, ruta: str, consulta: dict | None = None):
        url = PAYPAL_API[self.sandbox] + ruta + ("?" + urllib.parse.urlencode(consulta) if consulta else "")
        try:
            return _http("GET", url, {"Authorization": f"Bearer {self.token()}", "Content-Type": "application/json"}) or {}
        except ErrorApi as e:
            raise self._error(e, {403: "Tu app de PayPal no tiene activado «Transaction Search». Actívalo en "
                                       "developer.paypal.com → tu app → Features."}) from e

    def _cuenta(self) -> dict:
        self.token()
        ahora = datetime.now(timezone.utc)
        self._get("/v1/reporting/transactions", {"start_date": (ahora - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S-0000"),
                                                  "end_date": ahora.strftime("%Y-%m-%dT%H:%M:%S-0000"), "page_size": 1})
        return {"nombre": "PayPal", "correo": ""}

    def _movimientos(self) -> list[dict]:
        fin, salida = datetime.now(timezone.utc), []
        for k in range(self.MESES * 30 // 31 + 1):          # PayPal limita cada consulta a 31 días
            hasta = fin - timedelta(days=31 * k)
            desde = hasta - timedelta(days=31)
            for pagina in range(1, 40):
                r = self._get("/v1/reporting/transactions", {
                    "start_date": desde.strftime("%Y-%m-%dT%H:%M:%S-0000"),
                    "end_date": hasta.strftime("%Y-%m-%dT%H:%M:%S-0000"),
                    "fields": "all", "page_size": 500, "page": pagina})
                salida += r.get("transaction_details") or []
                if pagina >= int(r.get("total_pages") or 1):
                    break
        return salida

    def _ventas(self) -> list[dict]:
        ventas, devueltos = {}, {}
        for d in self._movimientos():
            info = d.get("transaction_info") or {}
            monto = info.get("transaction_amount") or {}
            try:
                valor = float(monto.get("value"))
            except (TypeError, ValueError):
                continue
            codigo = str(info.get("transaction_event_code") or "")
            if info.get("transaction_status") not in ("S", None):
                continue
            if valor < 0 and codigo.startswith("T11"):          # reembolso: apunta a la venta original
                devueltos[info.get("paypal_reference_id")] = devueltos.get(info.get("paypal_reference_id"), 0) - valor
                continue
            if valor <= 0 or not codigo.startswith("T00"):
                continue
            pagador = d.get("payer_info") or {}
            nombre = (pagador.get("payer_name") or {})
            items = ((d.get("cart_info") or {}).get("item_details") or [{}])
            ventas[info["transaction_id"]] = venta_base(
                "paypal", "pp", info["transaction_id"], fecha=_iso(info.get("transaction_initiation_date")),
                cliente=nombre.get("alternate_full_name") or " ".join(
                    x for x in (nombre.get("given_name"), nombre.get("surname")) if x),
                correo=pagador.get("email_address") or "", producto=items[0].get("item_name")
                or info.get("transaction_subject") or info.get("transaction_note") or "Pago de PayPal",
                producto_id=items[0].get("item_code") or items[0].get("item_name") or None,
                total=valor, moneda=monto.get("currency_code"), prueba=self.sandbox)
        for id_, v in ventas.items():
            devuelto = devueltos.get(id_, 0)
            if devuelto >= (v["total"] or 0) - 0.005 and devuelto:
                v.update(estado="Reembolsada", valida=False, reembolso=v["fecha"])
            elif devuelto:
                v["estado"] = "Reembolso parcial"
        return list(ventas.values())

    def _productos(self) -> list[dict]:
        vistos: dict = {}
        for v in self.ventas(max_edad=300):
            if v["producto_id"] is not None:
                vistos.setdefault(v["producto_id"], producto_base(v["producto_id"], v["producto"], v["total"],
                                                                  v["moneda"]))
        return list(vistos.values())


# ============================================================ FastSpring

class FastSpring(PlataformaVentas):
    clave, nombre = "fastspring", "FastSpring"

    def __init__(self, usuario: str, clave_api: str):
        super().__init__()
        self.usuario, self.clave_api = usuario.strip(), clave_api.strip()

    def _get(self, ruta: str, consulta: dict | None = None):
        url = FASTSPRING_API + ruta + ("?" + urllib.parse.urlencode(consulta) if consulta else "")
        basic = base64.b64encode(f"{self.usuario}:{self.clave_api}".encode()).decode()
        try:
            return _http("GET", url, {"Authorization": f"Basic {basic}", "Accept": "application/json"}) or {}
        except ErrorApi as e:
            raise self._error(e, {401: "FastSpring rechazó el usuario o la contraseña de la API."}) from e

    @staticmethod
    def _en_lotes(ids: list[str], n: int = 25):
        for i in range(0, len(ids), n):
            yield ids[i:i + n]

    def _cuenta(self) -> dict:
        self._get("/products")
        return {"nombre": "FastSpring", "correo": self.usuario}

    def _productos(self) -> list[dict]:
        r = self._get("/products")
        ids = [p if isinstance(p, str) else p.get("product") for p in r.get("products") or []]
        salida = []
        for lote in self._en_lotes([i for i in ids if i]):
            d = self._get("/products/" + ",".join(lote))
            for p in d.get("products") or []:
                nombre = p.get("display") or {}
                nombre = next(iter(nombre.values()), "") if isinstance(nombre, dict) else str(nombre)
                precios = (p.get("pricing") or {}).get("price") or {}
                moneda, valor = next(iter(precios.items()), ("", None))
                salida.append(producto_base(p.get("product"), nombre or p.get("product"),
                                            float(valor) if isinstance(valor, (int, float)) else None, moneda,
                                            bool(p.get("active", True))))
        return salida

    def _ventas(self) -> list[dict]:
        ordenes, ids = [], []
        for pagina in range(1, 60):
            r = self._get("/orders", {"begin": "2015-01-01", "limit": 100, "page": pagina})
            lista = r.get("orders") or []
            for o in lista:
                (ordenes if isinstance(o, dict) and o.get("items") is not None else ids).append(
                    o if isinstance(o, dict) and o.get("items") is not None else (o if isinstance(o, str)
                                                                                    else o.get("order") or o.get("id")))
            if len(lista) < 100:
                break
        for lote in self._en_lotes([i for i in ids if i], 20):
            d = self._get("/orders/" + ",".join(lote))
            ordenes += d.get("orders") or ([d] if d.get("order") else [])
        salida = []
        for o in ordenes:
            cliente = o.get("customer") or {}
            moneda = o.get("currency") or o.get("payoutCurrency") or ""
            total = o.get("total")
            items = o.get("items") or [{}]
            devuelto = bool(o.get("returns")) or bool(o.get("refunded"))
            salida.append(venta_base(
                "fastspring", "fs", o.get("order") or o.get("id"), fecha=_iso(o.get("changed") or o.get("completed")
                                                                             or o.get("changedInSeconds")),
                cliente=" ".join(x for x in (cliente.get("first"), cliente.get("last")) if x),
                correo=cliente.get("email") or "", producto=items[0].get("display") or items[0].get("product") or "",
                producto_id=items[0].get("product"), total=float(total) if isinstance(total, (int, float)) else None,
                moneda=moneda, estado="Reembolsada" if devuelto else "Pagada", valida=not devuelto,
                referencia=o.get("reference") or "", prueba=bool(o.get("test"))))
        return salida


# ============================================================ Whop

class Whop(PlataformaVentas):
    clave, nombre = "whop", "Whop"
    ESTADOS = {"active": ("Pagada", True), "trialing": ("En prueba", True), "completed": ("Pagada", True),
               "past_due": ("Pago pendiente", True), "canceled": ("Cancelada", False),
               "cancelled": ("Cancelada", False), "expired": ("Expirada", False), "unresolved": ("En disputa", False),
               "drafted": ("Borrador", False), "refunded": ("Reembolsada", False)}

    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key.strip()

    def _get(self, ruta: str, consulta: dict | None = None):
        url = WHOP_API + ruta + ("?" + urllib.parse.urlencode(consulta) if consulta else "")
        try:
            return _http("GET", url, {"Authorization": f"Bearer {self.api_key}", "Accept": "application/json"}) or {}
        except ErrorApi as e:
            raise self._error(e, {401: "Whop rechazó la API key de tu empresa. Créala en Whop → Developer."}) from e

    def _todas(self, ruta: str, consulta: dict | None = None, max_paginas: int = 80) -> list[dict]:
        items = []
        for pagina in range(1, max_paginas + 1):
            r = self._get(ruta, {"per": 50, "page": pagina} | (consulta or {}))
            items += r.get("data") or []
            pg = r.get("pagination") or {}
            if pagina >= int(pg.get("total_page") or pg.get("total_pages") or 1):
                break
        return items

    def _cuenta(self) -> dict:
        self._get("/company/products", {"per": 1})
        return {"nombre": "Whop", "correo": ""}

    @staticmethod
    def _objeto(valor) -> dict:
        return valor if isinstance(valor, dict) else {"id": valor} if valor else {}

    def _productos(self) -> list[dict]:
        return [producto_base(p.get("id"), p.get("name") or p.get("title"), activo=p.get("visibility", "visible")
                              not in ("archived", "hidden"), url=p.get("route") or "",
                              descripcion=p.get("description") or "")
                for p in self._todas("/company/products")]

    def _ventas(self) -> list[dict]:
        nombres = {p["id"]: p["nombre"] for p in self.productos(max_edad=120)}
        salida = []
        for m in self._todas("/company/memberships"):
            estado, valida = self.ESTADOS.get(str(m.get("status") or "").lower(), (str(m.get("status") or "—"), False))
            usuario = self._objeto(m.get("user"))
            producto = self._objeto(m.get("product"))
            plan = self._objeto(m.get("plan"))
            precio = plan.get("initial_price") if isinstance(plan.get("initial_price"), (int, float)) else None
            salida.append(venta_base(
                "whop", "wh", m["id"], fecha=_iso(m.get("created_at")),
                cliente=usuario.get("name") or usuario.get("username") or m.get("username") or "",
                correo=usuario.get("email") or m.get("email") or "",
                producto=producto.get("name") or nombres.get(producto.get("id"), producto.get("id") or ""),
                producto_id=producto.get("id"), total=precio, moneda=plan.get("base_currency") or "usd",
                estado=estado, valida=valida, suscripcion=m["id"] if plan.get("plan_type") == "renewal" else "",
                clave_licencia="", cancelada=bool(m.get("cancel_at_period_end"))))
        return salida


# ============================================================ fábrica

CLASES_EXTRA = {"stripe": Stripe, "paddle": Paddle, "paypal": PayPal, "fastspring": FastSpring, "whop": Whop}


def crear_cliente_extra(plataforma: str, cfg: dict):
    if plataforma == "stripe" and cfg.get("api_key"):
        return Stripe(cfg["api_key"])
    if plataforma == "paddle" and cfg.get("api_key"):
        return Paddle(cfg["api_key"], cfg.get("sandbox", False))
    if plataforma == "paypal" and cfg.get("client_id") and cfg.get("client_secret"):
        return PayPal(cfg["client_id"], cfg["client_secret"], cfg.get("sandbox", False))
    if plataforma == "fastspring" and cfg.get("usuario") and cfg.get("clave_api"):
        return FastSpring(cfg["usuario"], cfg["clave_api"])
    if plataforma == "whop" and cfg.get("api_key"):
        return Whop(cfg["api_key"])
    return None
