// Patent pages, drawing sheets and kit data are packed into shard files, web/dist/shard/<kind>/<n>.bin (written by
// pipeline/website.py write_shard), because a free Cloudflare Pages site holds at most 20,000 files and the register
// is far larger. A shard is "PYS2", uint32 n, n sorted entries (crc32(key), offset, length), then the items, each
// uint16 key length + key + payload: a binary search finds an item with no parsing, inside the free plan's 10 ms.
import SITE from "./site.json";

export const validId = id => /^(US-[A-Z]*\d{5,11}-[A-Z]\d?|EP-\d{7}-[AB]\d|CA-\d{1,7}-[A-Z]\d?|AU-\d{10}-[A-Z])$/.test(id);
// any office's number, with or without a kind code: CN-112345678-A, JP-H11123456-A, DE-102005012345 (functions/_world.js)
export const worldId = id => /^[A-Z]{2}-[A-Z0-9]{1,24}(-[A-Z][0-9]?)?$/.test(id);
const shardOf = num => Number(num) % SITE.shards;

const CRC = Array.from({ length: 256 }, (_, n) => { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xEDB88320 ^ (c >>> 1) : c >>> 1; return c >>> 0; });
const crc32 = s => { let c = 0xFFFFFFFF; for (const b of new TextEncoder().encode(s)) c = CRC[(c ^ b) & 255] ^ (c >>> 8); return (c ^ 0xFFFFFFFF) >>> 0; };
const dec = new TextDecoder();

async function open(ctx, kind, num) {
  const res = await ctx.env.ASSETS.fetch(new URL(`/shard/${kind}/${shardOf(num)}.bin`, ctx.request.url));
  if (!res.ok) return null;
  const buf = new Uint8Array(await res.arrayBuffer()), dv = new DataView(buf.buffer, buf.byteOffset, buf.byteLength);
  const n = dv.getUint32(4, true);
  return { buf, dv, n, base: 8 + 12 * n };
}

// the first item under `key` whose stored key passes `ok`, as [stored key, payload]
function lookup(s, key, ok) {
  const h = crc32(key);
  let lo = 0, hi = s.n;
  while (lo < hi) { const mid = (lo + hi) >> 1; if (s.dv.getUint32(8 + 12 * mid, true) < h) lo = mid + 1; else hi = mid; }
  for (let i = lo; i < s.n && s.dv.getUint32(8 + 12 * i, true) === h; i++) {
    const off = s.base + s.dv.getUint32(12 + 12 * i, true), len = s.dv.getUint32(16 + 12 * i, true);
    const kl = s.buf[off] | (s.buf[off + 1] << 8), k = dec.decode(s.buf.subarray(off + 2, off + 2 + kl));
    if (ok(k)) return [k, s.buf.subarray(off + 2 + kl, off + len)];
  }
  return null;
}

export async function item(ctx, kind, id, key = id) {
  const s = await open(ctx, kind, id.split("-")[1].replace(/\D/g, ""));
  return (s && lookup(s, key, k => k === key)?.[1]) || null;
}

// "11112282" -> "US-11112282-B2", ("0500000", "EP") -> "EP-0500000-B1", likewise "CA" and "AU", when the register or the archive has it
export async function find(ctx, num, cc = "US") {
  for (const kind of cc === "US" ? ["p", "a"] : ["a"]) {
    const s = await open(ctx, kind, num), hit = s && lookup(s, `${cc}-${num}`, k => k.startsWith(`${cc}-${num}-`));
    if (hit) return hit[0];
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
