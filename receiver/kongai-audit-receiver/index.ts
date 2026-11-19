// Supabase Edge Function: receives Konnect audit-log webhooks and stores them in kongai.kongai_audit_log.
// Auth: the caller must send `Authorization: <token>`; only the token's SHA-256 is stored here.
import postgres from "npm:postgres@3.4.5";

const TOKEN_SHA256 = "1de82cdc63966531fd9ea697a3a0cc1ccc3aef30fc7772decaadf029500a3713";
const sql = postgres(Deno.env.get("SUPABASE_DB_URL")!, { max: 1, prepare: false });

async function sha256(s: string): Promise<string> {
  const d = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s));
  return Array.from(new Uint8Array(d)).map((b) => b.toString(16).padStart(2, "0")).join("");
}

Deno.serve(async (req: Request) => {
  if (req.method !== "POST") return new Response("method not allowed", { status: 405 });
  const auth = req.headers.get("authorization") ?? "";
  const presented = auth.replace(/^Bearer\s+/i, "");
  if ((await sha256(presented)) !== TOKEN_SHA256) return new Response("unauthorized", { status: 401 });
  let bytes = new Uint8Array(await req.arrayBuffer());
  if (bytes[0] === 0x1f && bytes[1] === 0x8b) {
    bytes = new Uint8Array(await new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream("gzip"))).arrayBuffer());
  }
  const body = new TextDecoder().decode(bytes).replaceAll("\u0000", "");
  const headers: Record<string, string> = {};
  req.headers.forEach((v, k) => { if (k !== "authorization") headers[k] = v; });
  await sql`insert into kongai.kongai_audit_log (source_ip, headers, body)
            values (${req.headers.get("x-forwarded-for")}, ${sql.json(headers)}, ${body})`;
  return new Response(JSON.stringify({ ok: true }), { headers: { "content-type": "application/json" } });
});
