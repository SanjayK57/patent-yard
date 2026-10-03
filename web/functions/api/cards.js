// /api/cards?d=0,1,2 -> card text for those All-patents docs (functions/_world.js cards), at most 256 per call
import { cards } from "../_world.js";
import { readOnly } from "../_lib.js";
import SITE from "../site.json";

export async function onRequest(ctx) {
  const bad = readOnly(ctx);
  if (bad) return bad;
  const docs = (new URL(ctx.request.url).searchParams.get("d") || "").split(",").map(Number).filter(d => Number.isInteger(d) && d >= 0).slice(0, 256);
  const h = new Headers(SITE.headers);
  h.set("content-type", "application/json; charset=utf-8");
  h.set("cache-control", "public, max-age=86400");
  return new Response(JSON.stringify(docs.length && SITE.world ? await cards(docs) : []), { headers: h });
}
