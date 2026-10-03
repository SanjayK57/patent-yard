// /data/p/US-11112282-B2.json -> what the Claude kit and the studio need about that patent.
import { item, respond, notFound, segments, readOnly, validId, worldId, archiveRecord } from "../../_lib.js";
import { kitOf } from "../../_archive.js";
import { worldRecord, worldKit } from "../../_world.js";

export async function onRequest(ctx) {
  const bad = readOnly(ctx);
  if (bad) return bad;
  const parts = segments(ctx), id = (parts[0] || "").replace(/\.json$/, "");
  if (parts.length !== 1 || !parts[0].endsWith(".json") || !(validId(id) || worldId(id))) return notFound(ctx);
  if (!validId(id)) return worldKitResponse(ctx, id);
  const data = await item(ctx, "k", id);
  if (data) return respond(ctx, data, "application/json; charset=utf-8", "public, max-age=3600", true);
  const rec = await archiveRecord(ctx, id);
  return rec ? respond(ctx, JSON.stringify(kitOf(rec)), "application/json; charset=utf-8", "public, max-age=3600", false) : worldKitResponse(ctx, id);
}

// the Claude kit only works from patents that are past their term
async function worldKitResponse(ctx, id) {
  const r = await worldRecord(id);
  return r && r.free ? respond(ctx, JSON.stringify(worldKit(r)), "application/json; charset=utf-8", "public, max-age=86400", false) : notFound(ctx);
}
