// /img/p/US-11112282-B2/1.png -> drawing sheet 1 of that patent.
import { item, respond, notFound, segments, readOnly, validId } from "../../_lib.js";

export async function onRequest(ctx) {
  const bad = readOnly(ctx);
  if (bad) return bad;
  const [id, file, ...rest] = segments(ctx);
  const k = /^(\d{1,2})\.png$/.exec(file || "")?.[1];
  if (rest.length || !k || !validId(id || "")) return notFound(ctx);
  const png = await item(ctx, "i", id, `${id}/${k}`);
  return png ? respond(ctx, png, "image/png", "public, max-age=604800", false) : notFound(ctx);
}
