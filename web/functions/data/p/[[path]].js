// /data/p/US-11112282-B2.json -> what the Claude kit and the studio need about that patent.
import { item, respond, notFound, segments, readOnly, validId, archiveRecord } from "../../_lib.js";
import { kitOf } from "../../_archive.js";

export async function onRequest(ctx) {
  const bad = readOnly(ctx);
  if (bad) return bad;
  const parts = segments(ctx), id = (parts[0] || "").replace(/\.json$/, "");
  if (parts.length !== 1 || !parts[0].endsWith(".json") || !validId(id)) return notFound(ctx);
  const data = await item(ctx, "k", id);
  if (data) return respond(ctx, data, "application/json; charset=utf-8", "public, max-age=3600", true);
  const rec = await archiveRecord(ctx, id);
  return rec ? respond(ctx, JSON.stringify(kitOf(rec)), "application/json; charset=utf-8", "public, max-age=3600", false) : notFound(ctx);
}
