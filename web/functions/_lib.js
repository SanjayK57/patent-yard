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

// Pages serves whole files only (no Range requests), and copying a 2-3 MB file into one buffer took most of the free
// plan's 10 ms of CPU. So files are read as a stream: read(start, end) keeps just those bytes, reads only move forward,
// and close() cancels the rest of the download.
export function stream(res) {
  // one reused 256 KB buffer, filled by readAtLeast (Workers) so a long skip costs a few reads, not hundreds of small chunks
  let reader, buf = new ArrayBuffer(1 << 18), chunk = new Uint8Array(0), at = 0;  // chunk holds bytes [at, at + chunk.length)
  try { reader = res.body.getReader({ mode: "byob" }); } catch { reader = res.body.getReader(); buf = null; }
  const next = () => (!buf ? reader.read() : reader.readAtLeast ? reader.readAtLeast(buf.byteLength, new Uint8Array(buf)) : reader.read(new Uint8Array(buf)));
  return {
    async read(start, end) {
      const out = new Uint8Array(end - start);
      for (let got = 0; got < out.length;) {
        const from = start + got - at;
        if (from < 0) throw new Error("stream reads only move forward");
        if (from >= chunk.length) {
          at += chunk.length;
          const { value, done } = await next();
          if (done || !value) return null;
          chunk = value;
          if (buf) buf = value.buffer;  // the read handed the buffer back; reuse it (its bytes are copied out before the next read)
          continue;
        }
        const n = Math.min(chunk.length - from, out.length - got);
        out.set(chunk.subarray(from, from + n), got);
        got += n;
      }
      return out;
    },
    close: () => reader.cancel().catch(() => {}),
  };
}

// the first item under `key` in shard `kind` whose stored key passes `ok`, as [stored key, payload]
async function lookup(ctx, kind, num, key, ok) {
  const res = await ctx.env.ASSETS.fetch(new URL(`/shard/${kind}/${shardOf(num)}.bin`, ctx.request.url));
  if (!res.ok || !res.body) return null;
  const f = stream(res);
  try {
    const head = await f.read(0, 8), n = head && new DataView(head.buffer).getUint32(4, true), t = n && await f.read(8, 8 + 12 * n);
    if (!t) return null;
    const dv = new DataView(t.buffer), h = crc32(key), base = 8 + 12 * n;
    let lo = 0, hi = n;
    while (lo < hi) { const mid = (lo + hi) >> 1; if (dv.getUint32(12 * mid, true) < h) lo = mid + 1; else hi = mid; }
    for (let i = lo; i < n && dv.getUint32(12 * i, true) === h; i++) {  // entries with one hash are in file order
      const off = base + dv.getUint32(12 * i + 4, true), b = await f.read(off, off + dv.getUint32(12 * i + 8, true));
      if (!b) return null;
      const kl = b[0] | (b[1] << 8), k = dec.decode(b.subarray(2, 2 + kl));
      if (ok(k)) return [k, b.subarray(2 + kl)];
    }
    return null;
  } finally { f.close(); }
}

export async function item(ctx, kind, id, key = id) {
  return (await lookup(ctx, kind, id.split("-")[1].replace(/\D/g, ""), key, k => k === key))?.[1] || null;
}

// "11112282" -> "US-11112282-B2", ("0500000", "EP") -> "EP-0500000-B1", likewise "CA" and "AU", when the register or the archive has it
export async function find(ctx, num, cc = "US") {
  for (const kind of cc === "US" ? ["p", "a"] : ["a"]) {
    const hit = await lookup(ctx, kind, num, `${cc}-${num}`, k => k.startsWith(`${cc}-${num}-`));
    if (hit) return hit[0];
  }
  return null;
}

// Patents the USPTO has reinstated since the last full build, kept daily by the patentyard-watch Worker (web/watch)
// in KV; read at most once every 10 minutes per isolate. Empty when the binding is missing.
let rein, reinAt = 0;
export async function reinstated(ctx) {
  if (!ctx.env.PY_KV) return new Set();
  if (!rein || Date.now() - reinAt > 6e5) {
    reinAt = Date.now();
    rein = ctx.env.PY_KV.get("reinstated", "json").then(v => new Set(v?.numbers || [])).catch(() => new Set());
  }
  return rein;
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
