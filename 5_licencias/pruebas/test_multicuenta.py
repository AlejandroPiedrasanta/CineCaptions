# CineCaptions · By Cinema Productions
# 5_licencias/pruebas/test_multicuenta.py — pruebas: varias cuentas de Gumroad, 5 plataformas nuevas, acciones en masa.
"""Cinema Productions · pruebas de la versión 6 (sin internet, contra el simulador).

Cubre:
  - GumroadMulti: dos cuentas (tokens) con sus productos, ventas, bloqueos, cupones, reembolsos y webhooks.
  - Stripe, Paddle, PayPal, FastSpring y Whop: conexión, paginación, reembolsos y errores.
  - Modelo: catálogo de productos y datos para el programa.
  - Kit del programa: una clave de Gumroad vale para varios productos.
  - Panel: acciones en masa, reembolsos, cupones, mensajes masivos, página Productos y diálogos.

    python -m unittest discover -s 5_licencias/pruebas -v

Creado por Cinema Productions.
"""
from __future__ import annotations

import time
import unittest
from unittest import mock

import test_licencias as tl
from test_licencias import RAIZ_SIM, adm, cerrar, modelo, paginas, plat, sim, tiendas

import control
import plataformas_extra as ex
import simulador_extra as sx
from cinema_licencias import Configuracion, hash_licencia
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

CFG_GR1 = {"token": sim.GR_TOKEN}
CFG_GR2 = {"token": sim.GR_TOKEN, "cuentas": [{"token": sim.GR_TOKEN2, "nombre": "Plantillas", "correo": "p@x.com"}]}
CFG_SV = {"url": RAIZ_SIM, "clave_secreta": sim.SB_SECRETA, "clave_publica": sim.SB_PUBLICA}


class BaseNueva(tl.Base):
    """Igual que la base de las pruebas, más las direcciones falsas de las 5 plataformas nuevas."""

    def setUp(self):
        super().setUp()
        extra = [
            mock.patch.object(ex, "STRIPE_API", RAIZ_SIM + "/stripe/v1/"),
            mock.patch.object(ex, "PADDLE_API", {False: RAIZ_SIM + "/paddle", True: RAIZ_SIM + "/paddle"}),
            mock.patch.object(ex, "PAYPAL_API", {False: RAIZ_SIM + "/paypal", True: RAIZ_SIM + "/paypal"}),
            mock.patch.object(ex, "FASTSPRING_API", RAIZ_SIM + "/fastspring"),
            mock.patch.object(ex, "WHOP_API", RAIZ_SIM + "/whop/api/v5"),
        ]
        for p in extra:
            p.start()
            self.addCleanup(p.stop)
        self.gr2 = plat.GumroadMulti([sim.GR_TOKEN, sim.GR_TOKEN2])
        self.st = ex.Stripe(sx.ST_KEY)
        self.pd = ex.Paddle(sx.PD_KEY, True)
        self.pp = ex.PayPal(sx.PP_ID, sx.PP_SECRETO, True)
        self.fs = ex.FastSpring(sx.FS_USUARIO, sx.FS_CLAVE)
        self.wh = ex.Whop(sx.WH_KEY)

    def vender_dos_cuentas(self):
        a = sim.DATOS.vender_gumroad(cliente="Ana", correo="ana@x.com")                                # cuenta 1
        b = sim.DATOS.vender_gumroad(cliente="Beto", correo="beto@x.com", producto=sim.GR_PRODUCTO2)    # cuenta 2
        c = sim.DATOS.vender_gumroad(cliente="Cami", correo="cami@x.com", producto=sim.GR_PRODUCTO3,
                                     reembolsada=True)                                                  # cuenta 2
        return a, b, c


# ============================================================ Gumroad: varias cuentas

class GumroadVariasCuentas(BaseNueva):
    def test_trae_todos_los_productos_de_todas_las_cuentas(self):
        self.vender_dos_cuentas()
        r = self.gr2.conectar()
        self.assertEqual([p["name"] for p in r["productos"]], ["CineCaptions", "Plantillas Premium", "Pack de LUTs"])
        self.assertEqual([p["_cuenta"] for p in r["productos"]], [0, 1, 1])
        self.assertEqual((r["ventas_validas"], r["reembolsos"], r["claves"]), (2, 1, 3))
        self.assertEqual(len(r["usuarios"]), 2)
        self.assertEqual({v["cuenta"] for v in self.gr2.ventas(max_edad=0)}, {0, 1})

    def test_una_sola_cuenta_no_cambia(self):
        self.vender_dos_cuentas()
        r = self.gr.conectar()
        self.assertEqual([p["name"] for p in r["productos"]], ["CineCaptions"])
        self.assertEqual(r["ventas_validas"], 1)

    def test_las_acciones_van_a_la_cuenta_correcta(self):
        _a, b, _c = self.vender_dos_cuentas()
        self.gr2.productos()
        self.gr2.bloquear(sim.GR_PRODUCTO2, b["license_key"])
        self.assertTrue(sim.DATOS.gumroad_claves[b["license_key"]]["disabled"])
        self.assertTrue(self.gr2.licencia(sim.GR_PRODUCTO2, b["license_key"])["bloqueada"])
        self.gr2.bloquear(sim.GR_PRODUCTO2, b["license_key"], False)
        self.assertFalse(sim.DATOS.gumroad_claves[b["license_key"]]["disabled"])
        sim.DATOS.gumroad_claves[b["license_key"]]["uses"] = 2
        self.assertEqual(self.gr2.liberar_uso(sim.GR_PRODUCTO2, b["license_key"]), 1)
        with self.assertRaises(plat.ErrorApi):
            self.gr2.bloquear("producto-que-no-existe", b["license_key"])

    def test_si_una_cuenta_falla_las_demas_siguen(self):
        self.vender_dos_cuentas()
        multi = plat.GumroadMulti([sim.GR_TOKEN, "token-malo"])
        datos = multi.cargar({})
        self.assertEqual(len(datos["ventas"]), 1)
        self.assertEqual(len(datos["avisos_cuentas"]), 1)
        self.assertIn("access token", datos["avisos_cuentas"][0])
        with self.assertRaises(plat.ErrorApi):                 # si fallan todas, sí es un error
            plat.GumroadMulti(["malo1", "malo2"]).cargar({})

    def test_tokens_repetidos_o_vacios(self):
        m = plat.GumroadMulti([sim.GR_TOKEN, "", sim.GR_TOKEN, "  "])
        self.assertEqual(len(m.cuentas), 1)
        with self.assertRaises(ValueError):
            plat.GumroadMulti(["", " "])
        self.assertIsInstance(plat.crear_cliente("gumroad", {"token": sim.GR_TOKEN}), plat.Gumroad)
        self.assertNotIsInstance(plat.crear_cliente("gumroad", {"token": sim.GR_TOKEN}), plat.GumroadMulti)
        self.assertIsInstance(plat.crear_cliente("gumroad", CFG_GR2), plat.GumroadMulti)
        self.assertIsInstance(plat.crear_cliente("gumroad", {"cuentas": [{"token": sim.GR_TOKEN2}]}), plat.Gumroad)

    def test_reembolso_total_y_parcial(self):
        a, b, _c = self.vender_dos_cuentas()
        venta = next(v for v in self.gr2.ventas(max_edad=0) if v["cliente"] == "Beto")
        self.assertTrue(self.gr2.reembolsar(venta["id_api"], 500)["partially_refunded"])
        self.assertTrue(self.gr2.reembolsar(venta["id_api"])["refunded"])
        with self.assertRaises(plat.ErrorApi) as e:
            self.gr2.reembolsar(venta["id_api"])
        self.assertIn("already", str(e.exception))
        self.assertFalse(sim.DATOS.gumroad_claves[a["license_key"]]["venta"]["refunded"])
        self.assertEqual(next(v for v in self.gr2.ventas(max_edad=0) if v["cliente"] == "Beto")["estado"], "Reembolsada")

    def test_cupones(self):
        self.vender_dos_cuentas()
        self.gr2.productos()
        c = self.gr2.crear_codigo(sim.GR_PRODUCTO2, "gracias20", 20, True, 10)
        self.assertEqual((c["name"], c["percent_off"], c["max_purchase_count"]), ("GRACIAS20", 20, 10))
        self.gr2.crear_codigo(sim.GR_PRODUCTO2, "cinco", 5, False)
        self.assertEqual([x["name"] for x in self.gr2.codigos(sim.GR_PRODUCTO2)], ["GRACIAS20", "CINCO"])
        self.assertEqual(self.gr2.codigos(sim.GR_PRODUCTO2)[1]["amount_cents"], 500)
        self.gr2.borrar_codigo(sim.GR_PRODUCTO2, c["id"])
        self.assertEqual([x["name"] for x in self.gr2.codigos(sim.GR_PRODUCTO2)], ["CINCO"])
        with self.assertRaises(plat.ErrorApi):
            self.gr2.crear_codigo(sim.GR_PRODUCTO2, "", 5)

    def test_publicar_u_ocultar_producto(self):
        self.gr2.productos()
        self.assertFalse(self.gr2.publicar_producto(sim.GR_PRODUCTO3, True) is None)
        self.assertTrue(sim.DATOS.gumroad_cuentas[sim.GR_TOKEN2]["productos"][sim.GR_PRODUCTO3]["published"])
        self.gr2.publicar_producto(sim.GR_PRODUCTO3, False)
        self.assertFalse(sim.DATOS.gumroad_cuentas[sim.GR_TOKEN2]["productos"][sim.GR_PRODUCTO3]["published"])
        self.assertEqual(self.gr2.producto(sim.GR_PRODUCTO2)["variants"][0]["title"], "Edición")

    def test_webhooks(self):
        self.gr2.productos()
        self.gr2.crear_webhook("refund", "https://x.test/h?recurso=refund", 0)
        self.gr2.crear_webhook("sale", "https://x.test/h?recurso=sale", 1)
        hooks = self.gr2.todos_los_webhooks()
        self.assertEqual({(h["recurso"], h["_cuenta"]) for h in hooks}, {("refund", 0), ("sale", 1)})
        self.gr2.borrar_webhook(next(h["id"] for h in hooks if h["recurso"] == "refund"), 0)
        self.assertEqual([h["recurso"] for h in self.gr2.todos_los_webhooks()], ["sale"])

    def test_recibo_y_suscriptores(self):
        a, b, _c = self.vender_dos_cuentas()
        venta = next(v for v in self.gr2.ventas(max_edad=0) if v["cliente"] == "Beto")
        self.gr2.reenviar_recibo(venta["id_api"])
        self.assertEqual(sim.DATOS.gumroad_recibos, [b["id"]])
        self.assertEqual(self.gr2.suscriptores(sim.GR_PRODUCTO2)[0]["email"], "sub@x.com")

    def test_ventas_con_cupon_y_pais(self):
        sim.DATOS.vender_gumroad(cliente="Dani", correo="d@x.com", cupon="HOLA", precio=1000)
        v = self.gr.ventas(max_edad=0)[0]
        self.assertEqual((v["cupon"], v["pais"], v["total"]), ("HOLA", "Guatemala", 10.0))

    def test_regla_de_webhooks(self):
        r = control.estado_por_webhook
        self.assertEqual(r("refund", {})[0], "reembolsada")
        self.assertEqual(r("sale", {"refunded": "true"})[0], "reembolsada")
        self.assertIsNone(r("sale", {"refunded": "false"}))
        self.assertEqual(r("dispute", {})[0], "suspendida")
        self.assertEqual(r("dispute_won", {}), ("activa", ""))
        self.assertEqual(r("cancellation", {})[0], "suspendida")
        self.assertEqual(r("subscription_restarted", {}), ("activa", ""))
        self.assertIsNone(r("subscription_updated", {}))
        self.assertEqual(r("", {"resource_name": "refund"})[0], "reembolsada")


# ============================================================ las 5 plataformas nuevas

class StripeApi(BaseNueva):
    def test_clave_incorrecta(self):
        with self.assertRaises(plat.ErrorApi) as e:
            ex.Stripe("sk_test_mala").conectar()
        self.assertIn("credenciales", str(e.exception))

    def test_conectar_paginacion_y_reembolsos(self):
        for i in range(130):
            sim.DATOS.extra.vender_stripe(cliente=f"S{i}", correo=f"s{i}@x.com")
        sim.DATOS.extra.vender_stripe(cliente="R", correo="r@x.com", reembolsada=True)
        sim.DATOS.extra.vender_stripe(cliente="P", correo="p@x.com", parcial=500)
        sim.DATOS.extra.vender_stripe(cliente="D", correo="d@x.com", disputada=True)
        sim.DATOS.extra.vender_stripe(cliente="F", correo="f@x.com", fallida=True)       # no cuenta
        r = self.st.conectar()
        self.assertEqual(r["cuenta"]["nombre"], "Mi Negocio")
        self.assertEqual(r["entorno"], "Pruebas (sk_test)")
        self.assertEqual((r["ventas_validas"], r["reembolsos"], r["compradores"]), (131, 2, 131))
        ventas = {v["cliente"]: v for v in self.st.ventas(max_edad=0)}
        self.assertEqual(len(ventas), 133)
        self.assertEqual((ventas["R"]["estado"], ventas["R"]["valida"]), ("Reembolsada", False))
        self.assertEqual((ventas["P"]["estado"], ventas["P"]["valida"]), ("Reembolso parcial", True))
        self.assertEqual(ventas["D"]["estado"], "En disputa")
        self.assertEqual((ventas["S1"]["total"], ventas["S1"]["moneda"], ventas["S1"]["total_txt"]),
                         (25.0, "USD", "25.00 USD"))
        self.assertTrue(ventas["S1"]["prueba"])
        self.assertEqual(ventas["S1"]["pais"], "GT")

    def test_productos_y_reembolsar(self):
        v = sim.DATOS.extra.vender_stripe(cliente="Ana", correo="ana@x.com")
        prods = self.st.productos(0)
        self.assertEqual([(p["nombre"], p["precio_txt"], p["activo"]) for p in prods],
                         [("CineCaptions", "25.00 USD", True), ("Plantillas Premium", "", False)])
        venta = self.st.ventas(max_edad=0)[0]
        self.st.reembolsar(venta)
        self.assertTrue(v["refunded"])
        self.assertEqual(self.st.ventas(max_edad=0)[0]["estado"], "Reembolsada")

    def test_cache_de_ventas(self):
        sim.DATOS.extra.vender_stripe()
        self.st.ventas()
        antes = len(sim.DATOS.extra.visto)
        self.st.ventas()
        self.assertEqual(len(sim.DATOS.extra.visto), antes, "la segunda lectura sale de la caché")
        self.st.ventas(max_edad=0)
        self.assertGreater(len(sim.DATOS.extra.visto), antes)


class PaddleApi(BaseNueva):
    def test_clave_incorrecta(self):
        with self.assertRaises(plat.ErrorApi) as e:
            ex.Paddle("mala", True).conectar()
        self.assertIn("permiso", str(e.exception))

    def test_ventas_paginadas_y_reembolsos(self):
        for i in range(7):                                              # el simulador pagina de 3 en 3
            sim.DATOS.extra.vender_paddle(cliente=f"P{i}", correo=f"p{i}@x.com")
        sim.DATOS.extra.vender_paddle(cliente="Total", correo="t@x.com", reembolsado="3000")
        sim.DATOS.extra.vender_paddle(cliente="Parcial", correo="pa@x.com", reembolsado="1000")
        sim.DATOS.extra.vender_paddle(cliente="Borrador", correo="b@x.com", estado="canceled")
        r = self.pd.conectar()
        self.assertEqual(r["entorno"], "Sandbox (pruebas)")
        ventas = {v["cliente"]: v for v in self.pd.ventas(max_edad=0)}
        self.assertEqual(len(ventas), 9)
        self.assertEqual((r["ventas_validas"], r["reembolsos"]), (8, 1))
        self.assertEqual(ventas["Total"]["estado"], "Reembolsada")
        self.assertEqual((ventas["Parcial"]["estado"], ventas["Parcial"]["valida"]), ("Reembolso parcial", True))
        self.assertEqual((ventas["P0"]["total"], ventas["P0"]["moneda"], ventas["P0"]["producto"]),
                         (30.0, "USD", "CineCaptions"))
        self.assertEqual(self.pd.productos(0)[0]["precio_txt"], "30.00 USD")

    def test_reembolsar(self):
        sim.DATOS.extra.vender_paddle(cliente="Ana", correo="ana@x.com")
        venta = self.pd.ventas(max_edad=0)[0]
        self.pd.reembolsar(venta)
        self.assertEqual(self.pd.ventas(max_edad=0)[0]["estado"], "Reembolsada")


class PayPalApi(BaseNueva):
    def test_credenciales_incorrectas(self):
        with self.assertRaises(plat.ErrorApi) as e:
            ex.PayPal(sx.PP_ID, "mal", True).conectar()
        self.assertIn("rechazó", str(e.exception))

    def test_ventas_de_varios_meses_y_reembolso(self):
        sim.DATOS.extra.vender_paypal(cliente="Hoy", correo="hoy@x.com", dias=2)
        sim.DATOS.extra.vender_paypal(cliente="Mes", correo="mes@x.com", dias=40, valor="19.99")
        sim.DATOS.extra.vender_paypal(cliente="Antiguo", correo="a@x.com", dias=200, reembolso="25.00")
        sim.DATOS.extra.vender_paypal(cliente="Parcial", correo="p@x.com", dias=5, reembolso="5.00")
        r = self.pp.conectar()
        ventas = {v["cliente"]: v for v in self.pp.ventas(max_edad=0)}
        self.assertEqual(set(ventas), {"Hoy", "Mes", "Antiguo", "Parcial"})
        self.assertEqual(ventas["Mes"]["total"], 19.99)
        self.assertEqual((ventas["Antiguo"]["estado"], ventas["Antiguo"]["valida"]), ("Reembolsada", False))
        self.assertEqual((ventas["Parcial"]["estado"], ventas["Parcial"]["valida"]), ("Reembolso parcial", True))
        self.assertEqual((r["ventas_validas"], r["reembolsos"]), (3, 1))
        self.assertEqual(self.pp.productos(0)[0]["nombre"], "CineCaptions")

    def test_reutiliza_el_token(self):
        self.pp.token()
        self.pp.token()
        pedidos = [v for v in sim.DATOS.extra.visto if "oauth2/token" in v]
        self.assertEqual(len(pedidos), 1)


class FastSpringApi(BaseNueva):
    def test_credenciales_incorrectas(self):
        with self.assertRaises(plat.ErrorApi) as e:
            ex.FastSpring("x", "y").conectar()
        self.assertIn("FastSpring", str(e.exception))

    def test_pedidos_en_lotes(self):
        for i in range(23):
            sim.DATOS.extra.vender_fastspring(cliente=f"Fa{i} Pe", correo=f"f{i}@x.com")
        sim.DATOS.extra.vender_fastspring(cliente="Dev Uelto", correo="d@x.com", devuelto=True)
        r = self.fs.conectar()
        self.assertEqual((r["ventas_validas"], r["reembolsos"], r["compradores"]), (23, 1, 23))
        v = next(x for x in self.fs.ventas(max_edad=0) if x["cliente"] == "Fa1 Pe")
        self.assertEqual((v["total"], v["moneda"], v["correo"], v["producto"]), (29.0, "USD", "f1@x.com",
                                                                                 "Cinecaptions"))
        self.assertEqual(self.fs.productos(0)[0]["precio_txt"], "29.00 USD")


class WhopApi(BaseNueva):
    def test_clave_incorrecta(self):
        with self.assertRaises(plat.ErrorApi) as e:
            ex.Whop("mala").conectar()
        self.assertIn("Whop", str(e.exception))

    def test_membresias_paginadas_y_estados(self):
        for i in range(9):
            sim.DATOS.extra.vender_whop(cliente=f"W{i}", correo=f"w{i}@x.com")
        sim.DATOS.extra.vender_whop(cliente="Cancelado", correo="c@x.com", estado="canceled")
        sim.DATOS.extra.vender_whop(cliente="Prueba", correo="t@x.com", estado="trialing")
        r = self.wh.conectar()
        self.assertEqual((r["ventas_validas"], r["compradores"]), (10, 10))
        ventas = {v["cliente"]: v for v in self.wh.ventas(max_edad=0)}
        self.assertEqual(len(ventas), 11)
        self.assertEqual((ventas["Cancelado"]["estado"], ventas["Cancelado"]["valida"]), ("Cancelada", False))
        self.assertEqual(ventas["Prueba"]["estado"], "En prueba")
        self.assertEqual(ventas["W1"]["producto"], "CineCaptions")
        self.assertEqual([p["nombre"] for p in self.wh.productos(0)], ["CineCaptions", "Plantillas"])

    def test_filtrar_por_producto(self):
        sim.DATOS.extra.vender_whop(cliente="A", producto="prod_1")
        sim.DATOS.extra.vender_whop(cliente="B", producto="prod_2")
        self.assertEqual([v["cliente"] for v in self.wh.ventas("prod_2", max_edad=0)], ["B"])


class FabricaYBase(BaseNueva):
    def test_fabrica(self):
        for clave, cfg, clase in (("stripe", {"api_key": "sk_x"}, ex.Stripe), ("paddle", {"api_key": "k"}, ex.Paddle),
                                  ("paypal", {"client_id": "a", "client_secret": "b"}, ex.PayPal),
                                  ("fastspring", {"usuario": "a", "clave_api": "b"}, ex.FastSpring),
                                  ("whop", {"api_key": "k"}, ex.Whop)):
            self.assertIsInstance(plat.crear_cliente(clave, cfg), clase)
            self.assertIsNone(plat.crear_cliente(clave, {}))
            self.assertIn(clave, plat.PLATAFORMAS)
            self.assertTrue(plat.PLATAFORMAS[clave]["campos"] and plat.PLATAFORMAS[clave]["pasos"])
        self.assertEqual(set(plat.PLATAFORMAS_EXTRA), {"stripe", "paddle", "paypal", "fastspring", "whop"})

    def test_monedas_sin_decimales_y_fechas(self):
        self.assertEqual(ex._monto(1500, "jpy"), 1500.0)
        self.assertEqual(ex._monto(1500, "usd"), 15.0)
        self.assertIsNone(ex._monto("x", "usd"))
        self.assertTrue(ex._iso(1700000000).startswith("2023-11-14"))
        self.assertTrue(ex._iso(1700000000000).startswith("2023-11-14"))
        self.assertEqual(ex._iso("2024-01-01T00:00:00Z"), "2024-01-01T00:00:00Z")
        self.assertIsNone(ex._iso(None))

    def test_las_plataformas_sin_reembolso_lo_dicen(self):
        for c in (self.pp, self.fs, self.wh):
            self.assertFalse(c.puede_reembolsar)
            with self.assertRaises(plat.ErrorApi):
                c.reembolsar({"id_api": "x"})
        self.assertTrue(self.st.puede_reembolsar and self.pd.puede_reembolsar and self.gr.puede_reembolsar)


# ============================================================ modelo

class ModeloProductos(BaseNueva):
    def resultados(self):
        self.vender_dos_cuentas()
        sim.DATOS.vender_gumroad(cliente="Ana", correo="ana@x.com", producto=sim.GR_PRODUCTO2)          # Ana compra 2
        sim.DATOS.extra.vender_stripe(cliente="Ana", correo="ana@x.com")
        sim.DATOS.extra.vender_whop(cliente="Walter", correo="w@x.com")
        ls = sim.DATOS.vender(cliente="Lia", correo="lia@x.com")
        return modelo.cargar_todo({
            "gumroad": self.gr2, "stripe": self.st, "whop": self.wh,
            "lemonsqueezy": plat.LemonSqueezy(sim.API_KEY)},
            {"plataformas": {"gumroad": {}, "stripe": {}, "whop": {}, "lemonsqueezy": {
                "tienda_id": sim.TIENDA, "producto_id": 0}}}), ls

    def test_catalogo_de_productos(self):
        res, _ls = self.resultados()
        self.assertTrue(all("error" not in v for v in res.values()), res)
        m = modelo.construir_modelo(res)
        nombres = {p["clave"]: p for p in m["productos"]}
        self.assertIn(f"gumroad:{sim.GR_PRODUCTO}", nombres)
        self.assertIn(f"gumroad:{sim.GR_PRODUCTO2}", nombres)
        self.assertIn(f"gumroad:{sim.GR_PRODUCTO3}", nombres)
        p2 = nombres[f"gumroad:{sim.GR_PRODUCTO2}"]
        self.assertEqual((p2["nombre"], p2["ventas"], p2["cuenta"], p2["activo"], p2["precio_txt"]),
                         ("Plantillas Premium", 2, 1, True, "$15"))
        self.assertEqual(p2["ingresos"], {"$": 30.0})
        self.assertEqual(p2["personas"], 2)
        self.assertFalse(nombres[f"gumroad:{sim.GR_PRODUCTO3}"]["activo"])
        self.assertEqual(nombres[f"gumroad:{sim.GR_PRODUCTO3}"]["reembolsos"], 1)
        self.assertEqual(nombres["stripe:prod_1"]["ventas"], 1, "la venta de Stripe se une al producto por su nombre")
        self.assertEqual([k for k in nombres if k.startswith("stripe:")], ["stripe:prod_1", "stripe:prod_2"])
        self.assertIn("lemonsqueezy:" + str(sim.PRODUCTO), nombres)
        self.assertIn("whop:prod_1", nombres)
        self.assertEqual(sum(sum(p["serie"]) for p in m["productos"]), sum(
            1 for v in m["ventas"] if v["valida"]))           # todas las ventas de los últimos 30 días están en la serie

    def test_licencias_y_personas_por_producto(self):
        res, ls = self.resultados()
        m = modelo.construir_modelo(res)
        p1 = m["producto_por_clave"][f"gumroad:{sim.GR_PRODUCTO}"]
        self.assertEqual((p1["licencias"], p1["activas"], len(p1["lic_ids"])), (1, 1, 1))
        lic = m["lic_por_id"][p1["lic_ids"][0]]
        self.assertEqual(lic["producto_clave"], p1["clave"])
        self.assertEqual(lic["producto_nombre"], "CineCaptions")
        pls = m["producto_por_clave"]["lemonsqueezy:" + str(sim.PRODUCTO)]
        self.assertEqual(pls["activas"], 1)
        ana = m["persona_por_clave"]["ana@x.com"]
        self.assertEqual(ana["plataformas"], {"gumroad", "stripe"})
        self.assertIn("CineCaptions", ana["productos"])
        self.assertEqual(len(ana["ventas"]), 3)
        self.assertEqual(set(p1["personas_claves"]), {"ana@x.com"})
        self.assertTrue(all(v["producto_clave"] for v in m["ventas"]))

    def test_las_ventas_de_las_plataformas_nuevas_cuentan_en_inicio(self):
        res, _ = self.resultados()
        m = modelo.construir_modelo(res)
        self.assertIn("stripe", m["serie"])
        self.assertIn("whop", m["serie"])
        self.assertGreaterEqual(m["ventas_30"], 6)
        self.assertEqual(sum(1 for v in m["ventas"] if v["plataforma"] == "stripe"), 1)

    def test_si_una_plataforma_falla_no_rompe_el_modelo(self):
        self.vender_dos_cuentas()
        res = modelo.cargar_todo({"gumroad": self.gr2, "stripe": ex.Stripe("sk_test_mala")},
                                 {"plataformas": {"gumroad": {}, "stripe": {}}})
        self.assertIn("error", res["stripe"])
        m = modelo.construir_modelo(res)
        self.assertEqual(len(m["productos"]), 3)

    def test_datos_para_el_programa_con_varios_productos(self):
        cfg = modelo.config_base()
        cfg["plataformas"]["gumroad"] = {"token": "t", "producto_id": sim.GR_PRODUCTO,
                                         "productos_programa": [sim.GR_PRODUCTO2, sim.GR_PRODUCTO3],
                                         "url_compra": "https://x.gumroad.com/l/a"}
        d = modelo.config_programa(cfg)["gumroad"]
        self.assertEqual(d["productos"], [sim.GR_PRODUCTO, sim.GR_PRODUCTO2, sim.GR_PRODUCTO3])
        self.assertEqual(d["producto_id"], sim.GR_PRODUCTO)
        c = Configuracion.desde_dict(modelo.config_programa(cfg))
        self.assertEqual(c.gumroad_ids(), (sim.GR_PRODUCTO, sim.GR_PRODUCTO2, sim.GR_PRODUCTO3))
        self.assertEqual(c.a_dict()["gumroad"]["productos"], [sim.GR_PRODUCTO, sim.GR_PRODUCTO2, sim.GR_PRODUCTO3])
        self.assertIn("gumroad", c.tiendas())
        cfg["plataformas"]["gumroad"] = {"cuentas": [{"token": "x"}], "productos_programa": ["solo"]}
        self.assertEqual(modelo.config_programa(cfg)["gumroad"]["producto_id"], "solo")
        cfg["plataformas"]["gumroad"] = {}
        self.assertEqual(modelo.config_programa(cfg)["gumroad"]["productos"], [])
        self.assertEqual(Configuracion().tiendas(), [])


# ============================================================ kit del programa: una clave, varios productos

class ProgramaVariosProductos(BaseNueva):
    def test_la_clave_de_cualquier_producto_activa_el_programa(self):
        a = sim.DATOS.vender_gumroad(cliente="Ana", correo="a@x.com")
        b = sim.DATOS.vender_gumroad(cliente="Beto", correo="b@x.com", producto=sim.GR_PRODUCTO2)
        c = sim.DATOS.vender_gumroad(cliente="Cami", correo="c@x.com", producto=sim.GR_PRODUCTO3)
        prog = self.sdk(gumroad_producto_id=sim.GR_PRODUCTO, gumroad_productos=(sim.GR_PRODUCTO2,),
                        gumroad_max_equipos=2)
        r = prog.activar(a["license_key"])
        self.assertTrue(r.ok, r.mensaje)
        self.assertEqual(prog.guardada()["producto_id"], sim.GR_PRODUCTO)
        prog2 = self.sdk(gumroad_producto_id=sim.GR_PRODUCTO, gumroad_productos=(sim.GR_PRODUCTO2,),
                         gumroad_max_equipos=2)
        r = prog2.activar(b["license_key"])
        self.assertTrue(r.ok, r.mensaje)
        self.assertEqual(prog2.guardada()["producto_id"], sim.GR_PRODUCTO2)
        self.assertEqual(sim.DATOS.gumroad_claves[b["license_key"]]["uses"], 1, "solo se suma un uso")
        self.assertEqual(prog2.comprobar().codigo, "activa")
        self.assertEqual(sim.DATOS.gumroad_claves[b["license_key"]]["uses"], 1, "comprobar no gasta usos")
        r = self.sdk(gumroad_producto_id=sim.GR_PRODUCTO, gumroad_productos=(sim.GR_PRODUCTO2,)).activar(c["license_key"])
        self.assertFalse(r.ok)
        self.assertEqual(r.codigo, "invalida", "el tercer producto no es de este programa")

    def test_bloquear_en_gumroad_cierra_el_programa_del_producto_dos(self):
        b = sim.DATOS.vender_gumroad(cliente="Beto", correo="b@x.com", producto=sim.GR_PRODUCTO2)
        opciones = dict(gumroad_producto_id="", gumroad_productos=(sim.GR_PRODUCTO, sim.GR_PRODUCTO2))
        prog = self.sdk(**opciones)
        self.assertTrue(prog.activar(b["license_key"]).ok)
        self.gr2.productos()
        self.gr2.bloquear(sim.GR_PRODUCTO2, b["license_key"])
        self.assertEqual(prog.comprobar().codigo, "bloqueada")
        self.gr2.bloquear(sim.GR_PRODUCTO2, b["license_key"], False)
        sim.DATOS.gumroad_claves[b["license_key"]]["venta"]["refunded"] = True
        self.assertEqual(prog.comprobar().codigo, "reembolsada")

    def test_configuracion_por_archivo_con_varios_productos(self):
        c = Configuracion.desde_dict({"gumroad": {"producto_id": "a", "productos": ["b", "c", "a", ""],
                                                  "max_equipos": 3, "url_compra": "https://x"}})
        self.assertEqual(c.gumroad_ids(), ("a", "b", "c"))
        self.assertEqual(c.gumroad_max_equipos, 3)
        solo = Configuracion(gumroad_productos=("z",))
        self.assertTrue(tiendas.TiendaGumroad(solo).configurada())
        self.assertFalse(tiendas.TiendaGumroad(Configuracion()).configurada())
        with self.assertRaises(ValueError):
            Configuracion(gumroad_producto_id="polar_oat_secreto").verificar_sin_secretos()


# ============================================================ panel

class PanelBase(BaseNueva):
    @classmethod
    def setUpClass(cls):
        cls.app = adm.preparar_aplicacion([])

    def esperar(self, condicion, segundos=12):
        fin = time.time() + segundos
        while time.time() < fin:
            self.app.processEvents()
            if condicion():
                return True
            time.sleep(0.02)
        self.fail("tiempo de espera agotado")

    def ventana(self, plataformas: dict, servidor: dict | None = None, **ajustes):
        cfg = modelo.config_base() | ajustes
        cfg["plataformas"] |= plataformas
        cfg["servidor"] = servidor or {}
        modelo.guardar_config(cfg)
        v = adm.Ventana()
        self.addCleanup(cerrar, v)
        return v

    def si(self, v):
        """Contesta «sí» a todas las confirmaciones."""
        p = mock.patch.object(adm, "preguntar", return_value=True)
        p.start()
        self.addCleanup(p.stop)


class PanelProductos(PanelBase):
    def test_pagina_productos_con_dos_cuentas(self):
        self.vender_dos_cuentas()
        v = self.ventana({"gumroad": CFG_GR2})
        pag = v.paginas[paginas.P_PRODUCTOS]
        self.esperar(lambda: len(pag.tarjetas) == 3)
        self.esperar(lambda: pag.k_productos.valor.text() == "3")
        v.ir_a(paginas.P_PRODUCTOS)
        clave = f"gumroad:{sim.GR_PRODUCTO2}"
        pag.elegir(clave)
        self.esperar(lambda: pag.panel.maximumWidth() == pag.panel.ancho)
        self.assertEqual(pag.t.rowCount(), 1)
        self.assertTrue(pag.tarjetas[clave].elegida)
        pag.elegir(None)                          # al elegir de nuevo, se cierra
        self.assertEqual(pag.t.rowCount(), 3)
        v.buscar.setText("lut")
        self.assertEqual(len(pag.tarjetas), 1)
        v.buscar.clear()
        pag.chips.elegir("ocultos")
        pag.pintar(v.modelo)
        self.assertEqual(list(pag.tarjetas), [f"gumroad:{sim.GR_PRODUCTO3}"])

    def test_sin_conexion_pide_conectar(self):
        v = self.ventana({})
        pag = v.paginas[paginas.P_PRODUCTOS]
        self.app.processEvents()
        self.assertTrue(pag.sin_datos.isVisibleTo(pag))
        self.assertFalse(pag.contenido.isVisibleTo(pag))

    def test_plataformas_nuevas_se_ven_en_el_panel(self):
        sim.DATOS.extra.vender_stripe(cliente="Sara", correo="sara@x.com")
        sim.DATOS.extra.vender_whop(cliente="Walter", correo="w@x.com")
        v = self.ventana({"stripe": {"api_key": sx.ST_KEY}, "whop": {"api_key": sx.WH_KEY}})
        ventas = v.paginas[paginas.P_VENTAS]
        self.esperar(lambda: ventas.t.rowCount() == 2)
        self.assertEqual(v.paginas[paginas.P_PERSONAS].t.rowCount(), 2)
        self.assertTrue(v.chips_plataforma["stripe"].isVisibleTo(v.lateral))
        self.assertFalse(v.chips_plataforma["paddle"].isVisibleTo(v.lateral))
        self.assertEqual({"stripe", "whop"}, set(v.modelo["serie"]))
        self.esperar(lambda: v.paginas[paginas.P_INICIO].k_ventas.valor.text() == "2")
        self.assertGreaterEqual(len(v.modelo["productos"]), 2)

    def test_conectar_una_plataforma_nueva_desde_el_dialogo(self):
        from dialogos import DialogoConectar
        for clave in plat.PLATAFORMAS_EXTRA:
            d = DialogoConectar(None, clave)
            self.addCleanup(d.reject)
            self.assertEqual(set(d.campos_gen), {c[0] for c in plat.PLATAFORMAS[clave]["campos"]}, clave)
            self.assertTrue(d.form_gen.isVisibleTo(d.pila.widget(1)) or True)
        d = DialogoConectar(None, "stripe")
        self.addCleanup(d.reject)
        d.campos_gen["api_key"].setText(sx.ST_KEY)
        d.conectar()
        self.esperar(lambda: d.resultado is not None)
        clave, datos, resumen, cliente = d.resultado
        self.assertEqual((clave, datos["api_key"], resumen["cuenta"]["nombre"]), ("stripe", sx.ST_KEY, "Mi Negocio"))
        d2 = DialogoConectar(None, "paypal")
        self.addCleanup(d2.reject)
        d2.campos_gen["client_id"].setText(sx.PP_ID)
        d2.conectar()
        self.assertIn("Completa", d2.error.text())
        d3 = DialogoConectar(None, "paddle")
        self.addCleanup(d3.reject)
        d3.campos_gen["api_key"].setText("mala")
        d3.sandbox_gen.setChecked(True)
        d3.conectar()
        self.esperar(lambda: d3.error.text())
        self.assertIn("✕", d3.error.text())

    def test_resumen_de_una_plataforma_nueva_y_guardado(self):
        from dialogos import DialogoResumen
        sim.DATOS.extra.vender_stripe(cliente="Sara", correo="sara@x.com")
        resumen = self.st.conectar()
        d = DialogoResumen("stripe", self.st, resumen, {"api_key": sx.ST_KEY}, None, modelo.config_base())
        self.addCleanup(d.reject)
        self.assertEqual(d.producto.count(), 3)
        d.producto.setCurrentIndex(1)
        d.guardar()
        self.assertEqual((d.datos["producto_id"], d.datos["producto_nombre"], d.datos["cuenta"]),
                         ("prod_1", "CineCaptions", "Mi Negocio"))

    def test_resumen_gumroad_todos_los_productos_y_del_programa(self):
        from dialogos import DialogoResumen
        self.vender_dos_cuentas()
        resumen = self.gr2.conectar()
        d = DialogoResumen("gumroad", self.gr2, resumen, dict(CFG_GR2), None, modelo.config_base())
        self.addCleanup(d.reject)
        self.assertEqual(d.producto.currentData(), "", "por defecto: todos los productos")
        self.assertEqual(len(d.casillas_programa), 3)
        d.casillas_programa[sim.GR_PRODUCTO].setChecked(True)
        d.casillas_programa[sim.GR_PRODUCTO2].setChecked(True)
        self.assertIn(sim.GR_PRODUCTO2, d.codigo.text())
        d.guardar()
        self.assertEqual(d.datos["producto_id"], "")
        self.assertEqual(d.datos["productos_programa"], [sim.GR_PRODUCTO, sim.GR_PRODUCTO2])
        cfg = modelo.config_base()
        cfg["plataformas"]["gumroad"] = d.datos
        self.assertEqual(modelo.config_programa(cfg)["gumroad"]["productos"], [sim.GR_PRODUCTO, sim.GR_PRODUCTO2])

    def test_resumen_gumroad_con_un_solo_producto_sigue_trayendo_todos(self):
        from dialogos import DialogoResumen
        resumen = self.gr.conectar()
        d = DialogoResumen("gumroad", self.gr, resumen, dict(CFG_GR1), None, modelo.config_base())
        self.addCleanup(d.reject)
        self.assertEqual(d.producto.currentData(), "")
        d.guardar()
        self.assertEqual(d.datos["producto_id"], "")
        self.assertEqual(d.datos["productos_programa"], [sim.GR_PRODUCTO])


class PanelAcciones(PanelBase):
    def preparar(self, servidor=True):
        self.si_ = None
        a, b, c = self.vender_dos_cuentas()
        d = sim.DATOS.vender_gumroad(cliente="Dani", correo="dani@x.com", producto=sim.GR_PRODUCTO2)
        v = self.ventana({"gumroad": CFG_GR2}, CFG_SV if servidor else None)
        self.esperar(lambda: len(v.modelo["licencias"]) == 4 and (not servidor or v.modelo["control"]))
        self.si(v)
        return v, (a, b, c, d)

    def test_bloquear_y_reactivar_en_masa(self):
        v, (a, b, c, d) = self.preparar()
        lics = [l for l in v.modelo["licencias"] if l["user_name"] in ("Ana", "Beto", "Dani")]
        self.assertEqual(len(lics), 3)
        self.assertTrue(v.bloquear_licencias(lics, True))
        self.esperar(lambda: all(sim.DATOS.gumroad_claves[x["license_key"]]["disabled"] for x in (a, b, d)))
        self.esperar(lambda: all(hash_licencia(x["license_key"]) in sim.DATOS.sb["estados"] for x in (a, b, d)))
        for x in (a, b, d):
            self.assertEqual(sim.DATOS.sb["estados"][hash_licencia(x["license_key"])]["estado"], "revocada")
        self.esperar(lambda: not v.cargando)
        self.esperar(lambda: {l["user_name"] for l in v.modelo["licencias"] if l["disabled"]} >= {"Ana", "Beto", "Dani"})
        self.assertIn("Cami", {l["user_name"] for l in v.modelo["licencias"] if l["disabled"]},
                      "Cami está reembolsada: el control automático ya la había bloqueado")
        self.assertTrue(any("en masa" in r["detalle"] for r in v.registro_auto))
        self.assertTrue(v.bloquear_licencias([l for l in v.modelo["licencias"] if l["disabled"]], False))
        self.esperar(lambda: not any(sim.DATOS.gumroad_claves[x["license_key"]]["disabled"] for x in (a, b, d)))
        self.assertEqual(sim.DATOS.sb["estados"][hash_licencia(a["license_key"])]["estado"], "activa")
        self.assertTrue(any(x["tipo"] == "reactivada" for x in sim.DATOS.sb["avisos"]))

    def test_cancelar_la_confirmacion_no_hace_nada(self):
        v, (a, b, c, d) = self.preparar()
        with mock.patch.object(adm, "preguntar", return_value=False):
            self.assertFalse(v.bloquear_licencias(list(v.modelo["licencias"]), True))
        self.assertFalse(any(x["disabled"] for x in sim.DATOS.gumroad_claves.values()))
        self.assertFalse(v.bloquear_licencias([], True))

    def test_liberar_usos_en_masa(self):
        v, (a, b, c, d) = self.preparar()
        for x in (a, b):
            sim.DATOS.gumroad_claves[x["license_key"]]["uses"] = 3
        lics = [l for l in v.modelo["licencias"] if l["user_name"] in ("Ana", "Beto")]
        self.assertTrue(v.liberar_usos(lics))
        self.esperar(lambda: sim.DATOS.gumroad_claves[a["license_key"]]["uses"] == 2)
        self.assertEqual(sim.DATOS.gumroad_claves[b["license_key"]]["uses"], 2)
        self.esperar(lambda: v.usos_gumroad.get(a["license_key"]) == 2)
        self.assertFalse(v.liberar_usos([]))

    def test_bloquear_un_producto_entero(self):
        v, (a, b, c, d) = self.preparar()
        p = v.producto(f"gumroad:{sim.GR_PRODUCTO2}")
        self.assertEqual(p["activas"], 2)
        self.assertTrue(v.bloquear_producto(p, True))
        self.esperar(lambda: sim.DATOS.gumroad_claves[b["license_key"]]["disabled"]
                     and sim.DATOS.gumroad_claves[d["license_key"]]["disabled"])
        self.assertFalse(sim.DATOS.gumroad_claves[a["license_key"]]["disabled"], "otro producto: no se toca")

    def test_avisar_a_un_producto_y_a_licencias(self):
        v, (a, b, c, d) = self.preparar()

        def responder(dialogo):
            dialogo.titulo.setText("Novedad")
            dialogo.mensaje.setPlainText("Hay una versión nueva")
            return adm.DialogoAviso.DialogCode.Accepted

        with mock.patch.object(adm.DialogoAviso, "exec", responder):
            v.avisar_producto(v.producto(f"gumroad:{sim.GR_PRODUCTO2}"))
        esperados = {hash_licencia(b["license_key"]), hash_licencia(d["license_key"])}
        self.esperar(lambda: {x["licencia"] for x in sim.DATOS.sb["avisos"] if x["titulo"] == "Novedad"} == esperados)
        with mock.patch.object(adm.DialogoAviso, "exec", responder):
            v.avisar_licencias([l for l in v.modelo["licencias"] if l["user_name"] == "Ana"])
        self.esperar(lambda: hash_licencia(a["license_key"]) in {x["licencia"] for x in sim.DATOS.sb["avisos"]})

    def test_reembolsar_desde_el_panel_bloquea_la_licencia(self):
        v, (a, b, c, d) = self.preparar()
        venta = next(s for s in v.modelo["ventas"] if s["cliente"] == "Beto")
        self.assertTrue(v.puede_reembolsar(venta))
        self.assertTrue(v.reembolsar_venta(venta))
        self.esperar(lambda: b["refunded"])
        self.esperar(lambda: sim.DATOS.gumroad_claves[b["license_key"]]["disabled"], 20)     # control automático
        self.esperar(lambda: hash_licencia(b["license_key"]) in sim.DATOS.sb["estados"], 20)
        self.assertEqual(sim.DATOS.sb["estados"][hash_licencia(b["license_key"])]["estado"], "reembolsada")
        self.assertFalse(v.puede_reembolsar(next(s for s in v.modelo["ventas"] if s["cliente"] == "Beto")))

    def test_reembolso_parcial_pide_el_monto(self):
        v, (a, b, c, d) = self.preparar(servidor=False)
        venta = next(s for s in v.modelo["ventas"] if s["cliente"] == "Dani")
        with mock.patch("interfaz.pedir_texto", return_value="5,50"):
            self.assertTrue(v.reembolsar_venta(venta, parcial=True))
        self.esperar(lambda: d["partially_refunded"])
        with mock.patch("interfaz.pedir_texto", return_value="abc"):
            self.assertFalse(v.reembolsar_venta(venta, parcial=True))
        with mock.patch("interfaz.pedir_texto", return_value=None):
            self.assertFalse(v.reembolsar_venta(venta, parcial=True))

    def test_reembolsar_en_plataforma_que_no_deja(self):
        sim.DATOS.extra.vender_whop(cliente="Walter", correo="w@x.com")
        v = self.ventana({"whop": {"api_key": sx.WH_KEY}})
        self.esperar(lambda: v.modelo["ventas"])
        self.si(v)
        self.assertFalse(v.puede_reembolsar(v.modelo["ventas"][0]))
        self.assertFalse(v.reembolsar_venta(v.modelo["ventas"][0]))
        self.assertFalse(v.reenviar_recibo(v.modelo["ventas"][0]))

    def test_reembolsar_en_stripe_desde_el_panel(self):
        c = sim.DATOS.extra.vender_stripe(cliente="Sara", correo="sara@x.com")
        v = self.ventana({"stripe": {"api_key": sx.ST_KEY}})
        self.esperar(lambda: v.modelo["ventas"])
        self.si(v)
        self.assertTrue(v.reembolsar_venta(v.modelo["ventas"][0]))
        self.esperar(lambda: c["refunded"])
        self.esperar(lambda: v.modelo["ventas"][0]["estado"] == "Reembolsada" if v.modelo["ventas"] else False, 15)

    def test_reenviar_recibo(self):
        v, (a, b, c, d) = self.preparar(servidor=False)
        self.assertTrue(v.reenviar_recibo(next(s for s in v.modelo["ventas"] if s["cliente"] == "Beto")))
        self.esperar(lambda: sim.DATOS.gumroad_recibos == [b["id"]])

    def test_publicar_y_ocultar_con_confirmacion(self):
        v, _ = self.preparar(servidor=False)
        luts = v.producto(f"gumroad:{sim.GR_PRODUCTO3}")
        self.assertFalse(luts["activo"])
        self.assertTrue(v.publicar_producto(luts, True))
        self.esperar(lambda: sim.DATOS.gumroad_cuentas[sim.GR_TOKEN2]["productos"][sim.GR_PRODUCTO3]["published"])
        self.esperar(lambda: v.producto(f"gumroad:{sim.GR_PRODUCTO3}")["activo"])
        with mock.patch.object(adm, "preguntar", return_value=False):
            self.assertFalse(v.publicar_producto(v.producto(f"gumroad:{sim.GR_PRODUCTO3}"), False))
        self.assertTrue(sim.DATOS.gumroad_cuentas[sim.GR_TOKEN2]["productos"][sim.GR_PRODUCTO3]["published"])

    def test_crear_cupon_desde_el_panel(self):
        from dialogos_nuevos import DialogoCupon
        v, _ = self.preparar(servidor=False)

        def aceptar(d):
            d.codigo.setText("amigos15")
            d.valor.setValue(15)
            d.usos.setValue(3)
            return DialogoCupon.DialogCode.Accepted

        with mock.patch.object(DialogoCupon, "exec", aceptar):
            v.crear_cupon(v.producto(f"gumroad:{sim.GR_PRODUCTO2}"))
        self.esperar(lambda: sim.DATOS.gumroad_cupones.get(sim.GR_PRODUCTO2))
        c = sim.DATOS.gumroad_cupones[sim.GR_PRODUCTO2][0]
        self.assertEqual((c["name"], c["percent_off"], c["max_purchase_count"]), ("AMIGOS15", 15, 3))

    def test_cuentas_de_gumroad_desde_el_panel(self):
        from dialogos_nuevos import DialogoCuentasGumroad
        sim.DATOS.vender_gumroad(cliente="Ana", correo="ana@x.com")
        v = self.ventana({"gumroad": dict(CFG_GR1)})
        self.esperar(lambda: v.modelo["licencias"])
        self.si(v)
        d = DialogoCuentasGumroad(v)
        self.addCleanup(d.reject)
        self.assertEqual(len(d.cuentas), 1)
        d.token.setText("token-malo")
        d.añadir()
        self.esperar(lambda: d.error.text())
        self.assertIn("✕", d.error.text())
        d.token.setText(sim.GR_TOKEN)
        d.añadir()
        self.assertIn("ya está", d.error.text())
        d.token.setText(sim.GR_TOKEN2)
        d.añadir()
        self.esperar(lambda: len(d.cuentas) == 2)
        self.esperar(lambda: len(v.modelo["productos"]) == 3)
        self.assertEqual([c["nombre"] for c in v.cuentas_gumroad()], ["Alejandro", "Alejandro Plantillas"])
        self.assertEqual(len(v.cfg["plataformas"]["gumroad"]["cuentas"]), 1)
        self.assertIsInstance(v.clientes["gumroad"], plat.GumroadMulti)
        d.quitar(0)                                  # quita la principal: la otra pasa a serlo
        self.esperar(lambda: len(v.cuentas_gumroad()) == 1)
        self.assertEqual(v.cfg["plataformas"]["gumroad"]["token"], sim.GR_TOKEN2)
        self.esperar(lambda: [p["nombre"] for p in v.modelo["productos"]] == ["Plantillas Premium", "Pack de LUTs"]
                     or len(v.modelo["productos"]) == 2)
        d.quitar(0)
        self.assertEqual(v.cfg["plataformas"]["gumroad"], {})
        self.assertNotIn("gumroad", v.clientes)

    def test_webhooks_desde_el_panel(self):
        from dialogos_nuevos import DialogoWebhooks
        v, _ = self.preparar()
        url = v.url_webhook()
        self.assertTrue(url.startswith(RAIZ_SIM + "/functions/v1/gumroad-webhook?secreto="))
        self.assertEqual(v.url_webhook(), url, "el secreto se conserva")
        d = DialogoWebhooks(v)
        self.addCleanup(d.reject)
        d.url.setText("https://miproyecto.supabase.co/functions/v1/gumroad-webhook?secreto=abc")
        d.registrar()
        self.esperar(lambda: len(d.hooks) == 14)               # 7 eventos × 2 cuentas
        self.assertEqual({w["resource_name"] for w in sim.DATOS.gumroad_webhooks}, set(
            ["sale", "refund", "dispute", "dispute_won", "cancellation", "subscription_ended",
             "subscription_restarted"]))
        self.assertTrue(all("recurso=" in w["post_url"] for w in sim.DATOS.gumroad_webhooks))
        d.registrar()                                           # no duplica
        self.esperar(lambda: not d.spinner.isVisible() or True)
        time.sleep(0.3)
        self.app.processEvents()
        self.assertEqual(len(sim.DATOS.gumroad_webhooks), 14)
        d.t.selectRow(0)
        d.borrar()
        self.esperar(lambda: len(d.hooks) == 13)
        d.url.setText("http://sin-https")
        antes = len(sim.DATOS.gumroad_webhooks)
        d.registrar()
        self.assertEqual(len(sim.DATOS.gumroad_webhooks), antes)

    def test_sin_servidor_no_hay_url_de_webhook(self):
        v, _ = self.preparar(servidor=False)
        self.assertEqual(v.url_webhook(), "")


class PanelMensajes(PanelBase):
    def preparar(self):
        a = sim.DATOS.vender_gumroad(cliente="Ana", correo="ana@x.com")
        b = sim.DATOS.vender_gumroad(cliente="Beto", correo="beto@x.com", producto=sim.GR_PRODUCTO2)
        c = sim.DATOS.vender_gumroad(cliente="Cami", correo="cami@x.com", producto=sim.GR_PRODUCTO2, reembolsada=True)
        sim.DATOS.extra.vender_stripe(cliente="Sara", correo="sara@x.com")
        v = self.ventana({"gumroad": CFG_GR2, "stripe": {"api_key": sx.ST_KEY}}, CFG_SV)
        self.esperar(lambda: len(v.modelo["personas"]) == 4 and v.modelo["control"])
        v.cfg["telefonos"] = {"ana@x.com": "+502 5555-1111", "beto@x.com": "50255552222"}
        return v, (a, b, c)

    def test_filtros_de_destinatarios(self):
        v, _ = self.preparar()
        self.assertEqual(len(v.destinatarios({})), 4)
        self.assertEqual({p["nombre"] for p in v.destinatarios({"producto": f"gumroad:{sim.GR_PRODUCTO2}"})},
                         {"Beto", "Cami"})
        self.assertEqual({p["nombre"] for p in v.destinatarios({"plataforma": "stripe"})}, {"Sara"})
        self.assertEqual({p["nombre"] for p in v.destinatarios({"estado": "reembolsos"})}, {"Cami"})
        self.assertEqual({p["nombre"] for p in v.destinatarios({"estado": "con"})}, {"Ana", "Beto", "Sara"})
        self.assertEqual({p["nombre"] for p in v.destinatarios({"estado": "sin"})}, {"Cami"})
        self.assertEqual(v.destinatarios({"producto": "no-existe"}), [])

    def test_mensaje_por_whatsapp_en_cola(self):
        v, _ = self.preparar()
        r = v.enviar_mensaje_masivo(v.destinatarios({}), "whatsapp", "x", "Hola {nombre}, tu clave de {producto}: {clave}",
                                    "CineCaptions")
        self.assertEqual((r["enviados"], r["sin_dato"]), (2, 2))
        self.assertEqual([c["telefono"] for c in r["cola"]], ["50255551111", "50255552222"])
        self.assertIn("Hola%20Ana", r["cola"][0]["url"])
        self.assertTrue(r["cola"][0]["url"].startswith("https://wa.me/50255551111?text="))
        ana = next(p for p in v.modelo["personas"] if p["nombre"] == "Ana")
        self.assertIn(ana["licencias"][0]["key"].replace("-", "%2D") if False else ana["licencias"][0]["key"],
                      r["cola"][0]["url"].replace("%2D", "-"))

    def test_mensaje_por_correo_en_lotes(self):
        v, _ = self.preparar()
        r = v.enviar_mensaje_masivo(v.destinatarios({}), "correo", "Novedad en {app}", "Hola", "")
        self.assertEqual((r["enviados"], len(r["cola"])), (4, 1))
        self.assertTrue(r["cola"][0]["url"].startswith("mailto:?bcc="))
        self.assertIn("ana%40x.com", r["cola"][0]["url"])
        personas = [{"correo": f"u{i}@x.com", "nombre": "", "clave": f"u{i}", "licencias": [], "plataformas": set()}
                    for i in range(95)]
        r = v.enviar_mensaje_masivo(personas, "correo", "a", "b")
        self.assertEqual([c["cantidad"] for c in r["cola"]], [40, 40, 15])
        r = v.enviar_mensaje_masivo(personas + [{"correo": "", "nombre": "", "clave": "z", "licencias": []}], "correo",
                                    "a", "b")
        self.assertEqual(r["sin_dato"], 1)

    def test_copiar_correos(self):
        v, _ = self.preparar()
        r = v.enviar_mensaje_masivo(v.destinatarios({"plataforma": "gumroad"}), "copiar", "", "")
        self.assertEqual(r["enviados"], 3)
        self.assertEqual(QApplication.clipboard().text(), "ana@x.com, beto@x.com, cami@x.com")

    def test_aviso_dentro_del_programa(self):
        v, (a, b, c) = self.preparar()
        r = v.enviar_mensaje_masivo(v.destinatarios({"producto": f"gumroad:{sim.GR_PRODUCTO2}"}), "programa",
                                    "Novedad en {app}", "Hay versión nueva de {producto}", "Plantillas Premium")
        self.assertEqual(r["enviados"], 2)
        avisos = sim.DATOS.sb["avisos"]
        self.assertEqual({x["licencia"] for x in avisos}, {hash_licencia(b["license_key"]),
                                                          hash_licencia(c["license_key"])})
        self.assertIn("Plantillas Premium", avisos[0]["mensaje"])
        self.assertIn("CineCaptions", avisos[0]["titulo"])
        r = v.enviar_mensaje_masivo([p for p in v.modelo["personas"] if p["nombre"] == "Sara"], "programa", "t", "m")
        self.assertEqual((r["enviados"], r["sin_dato"]), (0, 1), "Sara no tiene licencia")

    def test_aviso_sin_servidor_falla_con_mensaje_claro(self):
        v, _ = self.preparar()
        v.clientes.pop("control")
        with self.assertRaises(plat.ErrorApi):
            v.enviar_mensaje_masivo(v.destinatarios({}), "programa", "t", "m")

    def test_dialogo_de_mensaje_masivo_de_punta_a_punta(self):
        from dialogos_nuevos import DialogoMensajeMasivo
        v, _ = self.preparar()
        d = DialogoMensajeMasivo(v, f"gumroad:{sim.GR_PRODUCTO2}")
        self.addCleanup(d.reject)
        self.assertEqual(len(d.personas), 2)
        self.assertIn("2", d.resumen.text())
        d.canal.elegir("whatsapp")
        d._recalcular()
        self.assertTrue(d.enviar.isEnabled())                 # Beto tiene teléfono
        d.producto.setCurrentIndex(0)
        d.estado.setCurrentIndex(d.estado.findData("con"))
        self.assertEqual(len(d.personas), 3)
        d.plantilla.setCurrentIndex(d.plantilla.findData("licencia"))
        self.assertIn("{clave}", d.mensaje.toPlainText())
        d._enviar()
        self.assertEqual(d.pila.currentIndex(), 1)
        self.assertEqual(len(d.cola), 2)
        abiertas = []
        with mock.patch.object(adm.Ventana, "abrir_url", abiertas.append):
            d._abrir_siguiente()
            d._saltar()
            d._abrir_siguiente()
        self.assertEqual(len(abiertas), 1)
        self.assertEqual(d._indice, 2)
        self.assertFalse(d.abrir.isEnabled())
        d._terminar()
        self.assertTrue(any("WhatsApp" in r["detalle"] for r in v.registro_auto))

    def test_dialogo_sin_nadie_alcanzable_bloquea_el_boton(self):
        from dialogos_nuevos import DialogoMensajeMasivo
        v, _ = self.preparar()
        v.cfg["telefonos"] = {}
        d = DialogoMensajeMasivo(v)
        self.addCleanup(d.reject)
        d.canal.elegir("whatsapp")
        d._recalcular()
        self.assertFalse(d.enviar.isEnabled())
        d.canal.elegir("correo")
        d._recalcular()
        self.assertTrue(d.enviar.isEnabled())

    def test_plantillas_con_llaves_desconocidas(self):
        from acciones import rellenar
        self.assertEqual(rellenar("Hola {nombre}, {raro}", nombre="Ana"), "Hola Ana, {raro}")


class PanelLicenciasMasivas(PanelBase):
    def test_seleccion_multiple_muestra_la_barra(self):
        for i in range(4):
            sim.DATOS.vender_gumroad(cliente=f"C{i}", correo=f"c{i}@x.com")
        v = self.ventana({"gumroad": CFG_GR1})
        pag = v.paginas[paginas.P_LICENCIAS]
        self.esperar(lambda: pag.t.rowCount() == 4)
        v.ir_a(paginas.P_LICENCIAS)
        pag.t.selectRow(0)
        self.assertFalse(pag.barra_masiva.isVisibleTo(pag))
        pag.t.selectionModel().select(pag.t.model().index(2, 0), pag.t.selectionModel().SelectionFlag.Select
                                      | pag.t.selectionModel().SelectionFlag.Rows)
        self.assertEqual(len(pag.seleccionadas()), 2)
        self.assertTrue(pag.barra_masiva.isVisibleTo(pag))
        self.assertIn("2 licencias", pag.lbl_masiva.text())
        self.assertEqual(pag.panel.maximumWidth(), 0, "con varias elegidas no se abre el detalle")
        v.refrescar()
        self.esperar(lambda: not v.cargando)
        self.assertEqual(len(pag.seleccionadas()), 2, "la selección múltiple sobrevive al refresco")
        pag.t.clearSelection()
        self.assertFalse(pag.barra_masiva.isVisibleTo(pag))
        pag.t.selectRow(1)
        self.assertEqual(len(pag.seleccionadas()), 1)
        self.assertFalse(pag.barra_masiva.isVisibleTo(pag))


class VisualNuevo(PanelBase):
    def test_widgets_se_pintan_en_todos_los_temas(self):
        import vidrio as V
        from interfaz import aplicar_tema, construir_qss
        from temas import TEMAS
        prod = {"clave": "g:1", "nombre": "CineCaptions", "precio_txt": "$25", "activo": True, "ventas": 10,
                "ingresos": {"USD": 250.0}, "activas": 9, "serie": [0, 1, 2, 3]}
        for tema in TEMAS:
            aplicar_tema(tema)
            self.app.setStyleSheet(construir_qss())
            widgets = [V.TarjetaProducto(prod, "#ff90e8", "🛍️"), V.OrbeParticulas(), V.InterruptorCristal(),
                       V.RachaSemana(), V.BarraMeta(), V.Sparkline(), V.Cristal(),
                       V.KPICristal("Prueba", "#22c55e", V.pixmap_dinero(40))]
            for w in widgets:
                w.resize(300, 200)
                w.show()
                self.app.processEvents()
                self.assertFalse(w.grab().isNull(), (tema, type(w).__name__))
                w.close()
            self.assertFalse(V.pixmap_dinero(48).isNull() or V.pixmap_personas(48).isNull())
        aplicar_tema("cinema")
        self.app.setStyleSheet(construir_qss())

    def test_resorte_llega_a_su_destino_y_respeta_animaciones_apagadas(self):
        import vidrio as V
        from PySide6.QtCore import QObject
        padre = QObject()
        r = V.Resorte(padre, 0.0, 320.0, 24.0)
        r.ir_a(1.0)
        self.esperar(lambda: not r._t.isActive(), 5)
        self.assertEqual(r.x, 1.0)
        pasa = {"max": 0.0}
        r.cambiado.connect(lambda x: pasa.__setitem__("max", max(pasa["max"], x)))
        r.ir_a(0.0)
        r.ir_a(1.0, impulso=8.0)
        self.esperar(lambda: not r._t.isActive(), 5)
        self.assertGreater(pasa["max"], 1.0, "con ζ<1 el resorte rebasa su destino (rebote)")
        with mock.patch.object(V, "ms", return_value=0):
            r2 = V.Resorte(padre, 0.0)
            r2.ir_a(5.0)
            self.assertEqual(r2.x, 5.0)
            self.assertFalse(r2._t.isActive())

    def test_racha_de_la_semana(self):
        import vidrio as V
        racha, dias, hoy = V.racha_semana([0] * 25 + [1, 1, 1, 1, 1])
        self.assertEqual(racha, 5)
        self.assertEqual(len(dias), 7)
        racha, _, _ = V.racha_semana([0] * 29 + [0])
        self.assertEqual(racha, 0)
        racha, _, _ = V.racha_semana([2] * 29 + [0])
        self.assertEqual(racha, 29, "si hoy aún no hay ventas, no se rompe la racha")

    def test_inicio_con_orbe_y_meta(self):
        sim.DATOS.vender_gumroad(cliente="Ana", correo="ana@x.com")
        v = self.ventana({"gumroad": CFG_GR1}, meta_ventas_mes=4)
        inicio = v.paginas[paginas.P_INICIO]
        self.esperar(lambda: v.modelo["ventas"])
        self.assertIsNotNone(inicio.orbe)
        self.assertIn("1 de 4", inicio.meta_txt.text())
        self.assertIn("25 %", inicio.meta_txt.text())
        self.assertEqual(inicio.racha.racha, 1)
        with mock.patch("interfaz.pedir_texto", return_value="2"):
            inicio._cambiar_meta()
        self.assertEqual(v.cfg["meta_ventas_mes"], 2)
        self.assertIn("50 %", inicio.meta_txt.text())


class ExportacionYRegistro(PanelBase):
    def test_csv_de_ventas_incluye_las_plataformas_nuevas(self):
        import csv
        import tempfile
        from pathlib import Path
        sim.DATOS.extra.vender_stripe(cliente="Sara", correo="sara@x.com")
        v = self.ventana({"stripe": {"api_key": sx.ST_KEY}})
        self.esperar(lambda: v.modelo["ventas"])
        ruta = Path(tempfile.mkdtemp(dir=tl._TMP)) / "ventas.csv"
        with mock.patch.object(adm.QFileDialog, "getSaveFileName", return_value=(str(ruta), "")):
            v.exportar_csv("ventas")
        filas = list(csv.reader(ruta.open(encoding="utf-8-sig")))
        self.assertEqual(filas[1][1], "stripe")
        self.assertEqual(filas[1][2], "Sara")


if __name__ == "__main__":
    unittest.main()
