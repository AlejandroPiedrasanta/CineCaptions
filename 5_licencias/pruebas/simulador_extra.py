# CineCaptions · By Cinema Productions
# 5_licencias/pruebas/simulador_extra.py — pruebas: Stripe, Paddle, PayPal, FastSpring y Whop FALSOS.
"""Cinema Productions · servidores falsos de Stripe, Paddle, PayPal, FastSpring y Whop (sin internet).

Se enganchan al simulador principal: `atender(manejador, datos, metodo, ruta, consulta, cuerpo)` devuelve True
si la ruta era de uno de ellos. Imitan las respuestas documentadas de cada API (paginación incluida).

    /stripe/v1/...   Bearer sk_test…        account, charges, products, refunds
    /paddle/...      Bearer pdl_…           products, prices, transactions, adjustments
    /paypal/...      Basic id:secret → OAuth  v1/oauth2/token, v1/reporting/transactions
    /fastspring/...  Basic usuario:clave    products, orders
    /whop/api/v5/... Bearer                 company/products, company/memberships

Creado por Cinema Productions.
"""
from __future__ import annotations

import base64
import json
import time
from datetime import datetime, timedelta, timezone

ST_KEY = "sk_test_de_prueba"
PD_KEY = "pdl_sdbx_apikey_de_prueba"
PP_ID, PP_SECRETO = "paypal-id-de-prueba", "paypal-secreto-de-prueba"
PP_TOKEN = "A21AA-paypal-token-de-prueba"
FS_USUARIO, FS_CLAVE = "fs-usuario-de-prueba", "fs-clave-de-prueba"
WH_KEY = "whop_company_key_de_prueba"


def _unix(dias_atras: float = 0) -> int:
    return int((datetime.now(timezone.utc) - timedelta(days=dias_atras)).timestamp())


def _pp_fecha(dias_atras: float = 0) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=dias_atras)).strftime("%Y-%m-%dT%H:%M:%S+0000")


class DatosExtra:
    def __init__(self):
        self.n = 0
        self.stripe: list[dict] = []
        self.paddle: list[dict] = []
        self.paddle_ajustes: list[dict] = []
        self.paypal: list[dict] = []
        self.fastspring: list[dict] = []
        self.whop: list[dict] = []
        self.visto: list[str] = []          # rutas atendidas (para comprobar en las pruebas)

    def _id(self) -> int:
        self.n += 1
        return self.n

    # ---- Stripe
    def vender_stripe(self, cliente="Ana Stripe", correo="ana@stripe.test", producto="CineCaptions", monto=2500,
                      reembolsada=False, parcial=0, disputada=False, dias=1, fallida=False) -> dict:
        n = self._id()
        c = {"id": f"ch_{n:04d}", "object": "charge", "amount": monto, "amount_refunded": monto if reembolsada
             else parcial, "currency": "usd", "status": "failed" if fallida else "succeeded", "paid": not fallida,
             "refunded": reembolsada, "disputed": disputada, "created": _unix(dias), "livemode": False,
             "description": producto, "receipt_url": f"https://pay.stripe.test/receipts/{n}",
             "billing_details": {"name": cliente, "email": correo, "address": {"country": "GT"}},
             "customer": {"id": f"cus_{n}", "name": cliente, "email": correo}, "metadata": {}}
        self.stripe.append(c)
        return c

    # ---- Paddle
    def vender_paddle(self, cliente="Pablo Paddle", correo="pablo@paddle.test", producto="CineCaptions",
                      total="3000", reembolsado="0", dias=1, estado="completed") -> dict:
        n = self._id()
        t = {"id": f"txn_{n:04d}", "status": estado, "customer_id": f"ctm_{n}", "currency_code": "USD",
             "created_at": _pp_fecha(dias), "billed_at": _pp_fecha(dias), "updated_at": _pp_fecha(dias),
             "details": {"totals": {"total": total, "grand_total": total},
                         "line_items": [{"id": f"txnitm_{n}", "product": {"id": "pro_01", "name": producto}}]},
             "customer": {"id": f"ctm_{n}", "name": cliente, "email": correo}}
        self.paddle.append(t)
        if reembolsado != "0":
            self.paddle_ajustes.append({"id": f"adj_{n}", "action": "refund", "status": "approved",
                                        "transaction_id": t["id"], "currency_code": "USD",
                                        "totals": {"total": reembolsado}})
        return t

    # ---- PayPal
    def vender_paypal(self, cliente="Paula PayPal", correo="paula@paypal.test", producto="CineCaptions", valor="25.00",
                      dias=1, reembolso: str | None = None) -> dict:
        n = self._id()
        tid = f"PP{n:06d}"
        d = {"transaction_info": {"transaction_id": tid, "transaction_event_code": "T0006",
                                  "transaction_initiation_date": _pp_fecha(dias), "transaction_status": "S",
                                  "transaction_amount": {"currency_code": "USD", "value": valor},
                                  "transaction_subject": producto},
             "payer_info": {"email_address": correo, "payer_name": {"alternate_full_name": cliente}},
             "cart_info": {"item_details": [{"item_name": producto, "item_code": "cc-1"}]}}
        self.paypal.append(d)
        if reembolso:
            self.paypal.append({"transaction_info": {
                "transaction_id": f"RF{n:06d}", "paypal_reference_id": tid, "transaction_event_code": "T1107",
                "transaction_initiation_date": _pp_fecha(max(dias - 0.1, 0)), "transaction_status": "S",
                "transaction_amount": {"currency_code": "USD", "value": f"-{reembolso}"}}})
        return d

    # ---- FastSpring
    def vender_fastspring(self, cliente="Fabio Spring", correo="fabio@fs.test", producto="cinecaptions",
                          total=29.0, devuelto=False, dias=1) -> dict:
        n = self._id()
        o = {"order": f"FS{n:04d}", "id": f"FS{n:04d}", "reference": f"REF-{n}", "total": total, "currency": "USD",
             "changed": (_unix(dias)) * 1000, "completed": True, "test": True,
             "customer": {"first": cliente.split()[0], "last": " ".join(cliente.split()[1:]), "email": correo},
             "items": [{"product": producto, "display": producto.title(), "subtotal": total}],
             "returns": [{"id": "r1"}] if devuelto else []}
        self.fastspring.append(o)
        return o

    # ---- Whop
    def vender_whop(self, cliente="Walter Whop", correo="walter@whop.test", producto="prod_1", estado="active",
                    dias=1) -> dict:
        n = self._id()
        m = {"id": f"mem_{n:04d}", "status": estado, "valid": estado in ("active", "trialing"),
             "created_at": _unix(dias), "product": producto, "plan": {"id": "plan_1", "initial_price": 19,
                                                                      "base_currency": "usd", "plan_type": "one_time"},
             "user": {"id": f"user_{n}", "username": cliente.lower().replace(" ", "_"), "name": cliente,
                      "email": correo}, "license_key": f"WHOP-{n}"}
        self.whop.append(m)
        return m


# ============================================================ manejador

def _requiere_bearer(h, esperado: str) -> bool:
    return h.headers.get("Authorization") == f"Bearer {esperado}"


def _basic(h, usuario: str, clave: str) -> bool:
    return h.headers.get("Authorization") == "Basic " + base64.b64encode(f"{usuario}:{clave}".encode()).decode()


def _pagina(items: list, limite: int, desde: int) -> tuple[list, bool]:
    return items[desde:desde + limite], desde + limite < len(items)


def atender(h, datos: DatosExtra, metodo: str, ruta: str, q: dict, cuerpo: bytes = b"") -> bool:
    """True si la ruta pertenecía a una de las cinco plataformas (y ya se respondió)."""
    for prefijo, fn in (("/stripe/v1/", _stripe), ("/paddle/", _paddle), ("/paypal/", _paypal),
                        ("/fastspring/", _fastspring), ("/whop/api/v5/", _whop)):
        if ruta.startswith(prefijo):
            datos.visto.append(f"{metodo} {ruta}")
            fn(h, datos, metodo, ruta[len(prefijo):], {k: v[0] if isinstance(v, list) else v for k, v in q.items()},
               cuerpo)
            return True
    return False


# ---- Stripe
def _stripe(h, d: DatosExtra, metodo, ruta, q, cuerpo):
    if not _requiere_bearer(h, ST_KEY):
        return h._responder(401, {"error": {"type": "invalid_request_error", "message": "Invalid API Key provided."}})
    if ruta == "account":
        return h._responder(200, {"id": "acct_1", "business_profile": {"name": "Mi Negocio"},
                                  "email": "dueno@negocio.test", "country": "US"})
    if ruta == "charges" and metodo == "GET":
        lista = list(reversed(d.stripe))
        limite = int(q.get("limit", 10))
        desde = 0
        if q.get("starting_after"):
            desde = next((i for i, c in enumerate(lista) if c["id"] == q["starting_after"]), -1) + 1
        pagina, mas = _pagina(lista, limite, desde)
        return h._responder(200, {"object": "list", "data": pagina, "has_more": mas})
    if ruta == "products":
        precio = {"id": "price_1", "unit_amount": 2500, "currency": "usd"}
        return h._responder(200, {"object": "list", "has_more": False, "data": [
            {"id": "prod_1", "name": "CineCaptions", "active": True, "images": [], "default_price": precio,
             "description": "Subtítulos para DaVinci Resolve"},
            {"id": "prod_2", "name": "Plantillas Premium", "active": False, "images": [], "default_price": None}]})
    if ruta == "refunds" and metodo == "POST":
        import urllib.parse
        datos = {k: v[0] for k, v in urllib.parse.parse_qs(cuerpo.decode()).items()}
        c = next((c for c in d.stripe if c["id"] == datos.get("charge")), None)
        if not c:
            return h._responder(404, {"error": {"message": "No such charge"}})
        c["refunded"], c["amount_refunded"] = True, c["amount"]
        return h._responder(200, {"id": "re_1", "object": "refund", "status": "succeeded", "charge": c["id"]})
    h._responder(404, {"error": {"message": "Unrecognized request URL."}})


# ---- Paddle
def _paddle(h, d: DatosExtra, metodo, ruta, q, cuerpo):
    if not _requiere_bearer(h, PD_KEY):
        return h._responder(403, {"error": {"type": "request_error", "code": "forbidden",
                                           "detail": "You aren't permitted to perform this request."}})
    ruta = "/" + ruta
    base = f"http://{h.headers['Host']}/paddle"
    if ruta == "/products":
        return h._responder(200, {"data": [{"id": "pro_01", "name": "CineCaptions", "status": "active",
                                            "description": "Subtítulos", "image_url": None}],
                                  "meta": {"pagination": {"has_more": False}}})
    if ruta == "/prices":
        return h._responder(200, {"data": [{"id": "pri_1", "product_id": "pro_01",
                                            "unit_price": {"amount": "3000", "currency_code": "USD"}}],
                                  "meta": {"pagination": {"has_more": False}}})
    if ruta == "/adjustments" and metodo == "GET":
        return h._responder(200, {"data": d.paddle_ajustes, "meta": {"pagination": {"has_more": False}}})
    if ruta == "/adjustments" and metodo == "POST":
        c = json.loads(cuerpo)
        t = next((t for t in d.paddle if t["id"] == c["transaction_id"]), None)
        if not t:
            return h._responder(404, {"error": {"detail": "Transaction not found"}})
        total = t["details"]["totals"]["grand_total"]
        d.paddle_ajustes.append({"id": "adj_x", "action": "refund", "status": "approved",
                                 "transaction_id": t["id"], "currency_code": "USD", "totals": {"total": total}})
        return h._responder(201, {"data": d.paddle_ajustes[-1]})
    if ruta == "/transactions" and metodo == "GET":
        lista = d.paddle
        limite, desde = int(q.get("per_page", 50)), int(q.get("desde", 0))
        pagina, mas = _pagina(lista, min(limite, 3), desde)       # páginas chicas para probar el paginado
        siguiente = f"{base}/transactions?per_page={limite}&desde={desde + 3}" if mas else None
        return h._responder(200, {"data": pagina, "meta": {"pagination": {"has_more": mas, "next": siguiente}}})
    if ruta.startswith("/transactions/"):
        t = next((t for t in d.paddle if t["id"] == ruta.split("/")[2]), None)
        return h._responder(200 if t else 404, {"data": t} if t else {"error": {"detail": "not found"}})
    h._responder(404, {"error": {"detail": "Not found"}})


# ---- PayPal
def _paypal(h, d: DatosExtra, metodo, ruta, q, cuerpo):
    if ruta == "v1/oauth2/token":
        if not _basic(h, PP_ID, PP_SECRETO):
            return h._responder(401, {"error": "invalid_client", "error_description": "Client Authentication failed"})
        return h._responder(200, {"access_token": PP_TOKEN, "token_type": "Bearer", "expires_in": 32400})
    if not _requiere_bearer(h, PP_TOKEN):
        return h._responder(401, {"name": "AUTHENTICATION_FAILURE"})
    if ruta == "v1/reporting/transactions":
        def parse(s):
            return datetime.strptime(s.replace("-0000", "+0000").replace("+0000", ""), "%Y-%m-%dT%H:%M:%S").replace(
                tzinfo=timezone.utc)
        desde, hasta = parse(q["start_date"]), parse(q["end_date"])
        if (hasta - desde).days > 31:
            return h._responder(400, {"name": "INVALID_REQUEST", "message": "Date range is greater than 31 days."})
        dentro = [t for t in d.paypal if desde <= parse(t["transaction_info"]["transaction_initiation_date"]) <= hasta]
        tam, pag = int(q.get("page_size", 100)), int(q.get("page", 1))
        return h._responder(200, {"transaction_details": dentro[(pag - 1) * tam:pag * tam], "page": pag,
                                  "total_pages": max(1, -(-len(dentro) // tam)), "total_items": len(dentro)})
    h._responder(404, {"name": "RESOURCE_NOT_FOUND"})


# ---- FastSpring
def _fastspring(h, d: DatosExtra, metodo, ruta, q, cuerpo):
    if not _basic(h, FS_USUARIO, FS_CLAVE):
        return h._responder(401, {"result": "error", "error": {"message": "Unauthorized"}})
    if ruta == "products":
        return h._responder(200, {"action": "product.list", "result": "success", "products": ["cinecaptions"]})
    if ruta.startswith("products/"):
        return h._responder(200, {"products": [{"product": "cinecaptions", "display": {"en": "CineCaptions"},
                                                "pricing": {"price": {"USD": 29}}}]})
    if ruta == "orders":
        tam, pag = int(q.get("limit", 50)), int(q.get("page", 1))
        ids = [o["order"] for o in d.fastspring][(pag - 1) * tam:pag * tam]
        return h._responder(200, {"action": "order.list", "result": "success", "page": pag, "orders": ids})
    if ruta.startswith("orders/"):
        quiero = ruta.split("/", 1)[1].split(",")
        return h._responder(200, {"orders": [o for o in d.fastspring if o["order"] in quiero]})
    h._responder(404, {"result": "error"})


# ---- Whop
def _whop(h, d: DatosExtra, metodo, ruta, q, cuerpo):
    if not _requiere_bearer(h, WH_KEY):
        return h._responder(401, {"error": {"message": "Invalid API key"}})
    tam, pag = int(q.get("per", 10)), int(q.get("page", 1))
    if ruta == "company/products":
        productos = [{"id": "prod_1", "name": "CineCaptions", "visibility": "visible"},
                     {"id": "prod_2", "name": "Plantillas", "visibility": "archived"}]
        return h._responder(200, {"pagination": {"current_page": pag, "total_page": 1}, "data": productos})
    if ruta == "company/memberships":
        total = max(1, -(-len(d.whop) // min(tam, 4)))
        pagina = d.whop[(pag - 1) * min(tam, 4):pag * min(tam, 4)]
        return h._responder(200, {"pagination": {"current_page": pag, "total_page": total}, "data": pagina})
    h._responder(404, {"error": {"message": "Not found"}})
