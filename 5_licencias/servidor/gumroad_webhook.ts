// CineCaptions · By Cinema Productions
// 5_licencias/servidor/gumroad_webhook.ts — Función de Supabase: Gumroad avisa y la licencia se suspende al instante.
//
// Para qué sirve: cuando Gumroad te cobra un reembolso, una disputa o se cancela una suscripción, esta función
// cambia el estado de la licencia en tu servidor de control en el mismo segundo — sin que el Administrador esté
// abierto. El programa del cliente lo ve en su próxima revisión (unos minutos) y se cierra pidiendo licencia.
//
// Cómo ponerla (una sola vez, 3 pasos):
//   1. Instala la CLI de Supabase y entra:   supabase login   ·   supabase link --project-ref TU_PROYECTO
//   2. Guarda un secreto largo (inventa uno):  supabase secrets set GUMROAD_WEBHOOK_SECRET=pon-aqui-un-texto-largo
//   3. Publícala SIN verificación JWT (Gumroad no puede enviar un token):
//        mkdir -p supabase/functions/gumroad-webhook && copia este archivo como index.ts
//        supabase functions deploy gumroad-webhook --no-verify-jwt
//   Luego, en el Administrador: Conexiones → Webhooks de Gumroad → «Registrar todos». La URL ya incluye tu secreto.
//
// La clave de licencia nunca se guarda: se convierte a la misma huella (sha256 de "cinema:CLAVE") que usa el kit.
// Reglas (iguales a control.py → estado_por_webhook):
//   refund / venta reembolsada .......... reembolsada      dispute / venta en disputa ... suspendida
//   dispute_won ......................... activa            cancellation, subscription_ended ... suspendida
//   subscription_restarted .............. activa

import { createClient } from "jsr:@supabase/supabase-js@2";

const sb = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!);
const SECRETO = Deno.env.get("GUMROAD_WEBHOOK_SECRET") ?? "";

async function huella(clave: string): Promise<string> {
  const datos = new TextEncoder().encode(`cinema:${clave.trim().toUpperCase()}`);
  const h = await crypto.subtle.digest("SHA-256", datos);
  return [...new Uint8Array(h)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

const si = (v: unknown) => ["true", "1", "yes", "si", "sí"].includes(String(v ?? "").trim().toLowerCase());

function decidir(recurso: string, d: Record<string, string>): [string, string] | null {
  if (recurso === "refund" || (recurso === "sale" && si(d.refunded))) {
    return ["reembolsada", "La compra de esta licencia fue reembolsada."];
  }
  if (recurso === "dispute" || (recurso === "sale" && si(d.disputed) && !si(d.dispute_won))) {
    return ["suspendida", "La compra de esta licencia está en disputa."];
  }
  if (recurso === "dispute_won") return ["activa", ""];
  if (recurso === "cancellation" || recurso === "subscription_ended") return ["suspendida", "Tu suscripción terminó."];
  if (recurso === "subscription_restarted") return ["activa", ""];
  return null;
}

Deno.serve(async (req) => {
  if (req.method !== "POST") return new Response("Gumroad webhook listo", { status: 200 });
  const url = new URL(req.url);
  if (!SECRETO || url.searchParams.get("secreto") !== SECRETO) return new Response("No autorizado", { status: 401 });

  // Gumroad envía application/x-www-form-urlencoded
  const form = await req.formData();
  const d: Record<string, string> = {};
  form.forEach((v, k) => (d[k] = String(v)));
  const recurso = (url.searchParams.get("recurso") || d.resource_name || "").trim();
  const clave = d.license_key || "";
  const decision = decidir(recurso, d);
  if (!clave || !decision) return new Response("ok (sin cambios)", { status: 200 });

  const [estado, motivo] = decision;
  const licencia = await huella(clave);
  const { error } = await sb.from("cinema_estados").upsert(
    { licencia, estado, motivo: motivo || null, actualizado: new Date().toISOString() },
    { onConflict: "licencia" },
  );
  if (error) return new Response(`Error: ${error.message}`, { status: 500 });
  await sb.from("cinema_eventos").insert({
    licencia, equipo: null, tipo: estado === "activa" ? "reactivada" : "licencia_perdida",
    detalle: `Gumroad: ${recurso}`,
  });
  return new Response(`ok ${estado}`, { status: 200 });
});
