// Patent pages, drawing sheets and kit data are packed into shard files, web/dist/shard/<kind>/<n>.bin (written by
// pipeline/website.py write_shard), because a free Cloudflare Pages site holds at most 20,000 files and the register
// is far larger. A shard is a 4-byte length, a JSON index {key: [offset, length]}, then the items back to back.
import SITE from "./site.json";

export const validId = id => /^US-[A-Z]*\d{5,11}-[A-Z]\d?$/.test(id);
const shardOf = num => Number(num) % SITE.shards;

async function open(ctx, kind, num) {
  const res = await ctx.env.ASSETS.fetch(new URL(`/shard/${kind}/${shardOf(num)}.bin`, ctx.request.url));
  if (!res.ok) return null;
  const buf = new Uint8Array(await res.arrayBuffer());
  const n = new DataView(buf.buffer, buf.byteOffset, 4).getUint32(0);
  return { buf, start: 4 + n, index: JSON.parse(new TextDecoder().decode(buf.subarray(4, 4 + n))) };
}

export async function item(ctx, kind, id, key = id) {
  const s = await open(ctx, kind, id.split("-")[1].replace(/\D/g, ""));
  const at = s?.index[key];
  return at ? s.buf.subarray(s.start + at[0], s.start + at[0] + at[1]) : null;
}

// "11112282" -> "US-11112282-B2", when the register or the archive has it
export async function find(ctx, num) {
  for (const kind of ["p", "a"]) {
    const s = await open(ctx, kind, num);
    const id = s && Object.keys(s.index).find(k => k.split("-")[1] === num);
    if (id) return id;
  }
  return null;
}

export const gunzip = async bytes => new Response(new Response(bytes).body.pipeThrough(new DecompressionStream("gzip"))).text();
export const archiveRecord = async (ctx, id) => { const b = await item(ctx, "a", id); return b ? JSON.parse(await gunzip(b)) : null; };
let tpl;  // the archive page shell, read once per isolate
export const archiveShell = ctx => (tpl ||= ctx.env.ASSETS.fetch(new URL("/tpl/archive/", ctx.request.url)).then(r => (r.ok ? r.text() : Promise.reject(new Error("shell"))))
  .catch(e => { tpl = null; throw e; }));

export function respond(ctx, body, type, cache, gzipped) {
  const req = ctx.request, h = new Headers(SITE.headers);
  h.set("content-type", type);
  h.set("cache-control", cache);
  if (gzipped && /\bgzip\b/.test(req.headers.get("accept-encoding") || "")) {
    h.set("content-encoding", "gzip");
    return new Response(req.method === "HEAD" ? null : body, { headers: h, encodeBody: "manual" });
  }
  if (gzipped) body = new Response(body).body.pipeThrough(new DecompressionStream("gzip"));
  return new Response(req.method === "HEAD" ? null : body, { headers: h });
}

export async function notFound(ctx) {
  const page = await ctx.env.ASSETS.fetch(new URL("/__missing__/", ctx.request.url));  // the asset server answers with 404.html
  const h = new Headers(SITE.headers);
  h.set("content-type", "text/html; charset=utf-8");
  h.set("cache-control", "public, max-age=60");
  return new Response(ctx.request.method === "HEAD" ? null : await page.text(), { status: 404, headers: h });
}

export const segments = ctx => [].concat(ctx.params.path || []).filter(Boolean).map(decodeURIComponent);
export const readOnly = ctx => (["GET", "HEAD"].includes(ctx.request.method) ? null : new Response(null, { status: 405, headers: { allow: "GET, HEAD" } }));
