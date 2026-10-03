// /patents/US-11112282-B2/ -> the patent's page. /patents/11112282, /patents/EP500000, /patents/CA2000001 or /patents/AU2002254354 -> redirect to it.
import { item, find, respond, notFound, segments, readOnly, validId, archiveRecord, archiveShell } from "../_lib.js";
import { renderArchive } from "../_archive.js";

export async function onRequest(ctx) {
  const bad = readOnly(ctx);
  if (bad) return bad;
  const url = new URL(ctx.request.url), parts = segments(ctx);
  if (parts.length !== 1) return notFound(ctx);
  const id = parts[0].toUpperCase();
  if (!validId(id)) {
    const cc = id.match(/^(EP|CA|AU)/)?.[1] || "US", num = id.replace(/^(US|EP|CA|AU)/, "").replace(/[A-Z]\d?$/, "").replace(/[^0-9]/g, "");
    const found = cc === "EP" ? /^\d{1,7}$/.test(num) && (await find(ctx, num.padStart(7, "0"), "EP"))
      : cc !== "US" ? /^\d{1,10}$/.test(num) && (await find(ctx, num, cc)) : /^\d{5,11}$/.test(num) && (await find(ctx, num));
    return found ? Response.redirect(new URL(`/patents/${found}/`, url), 301) : notFound(ctx);
  }
  if (id !== parts[0] || !url.pathname.endsWith("/")) return Response.redirect(new URL(`/patents/${id}/`, url), 301);
  const page = await item(ctx, "p", id);
  if (page) return respond(ctx, page, "text/html; charset=utf-8", "public, max-age=600", true);
  const rec = await archiveRecord(ctx, id);
  return rec ? respond(ctx, renderArchive(await archiveShell(ctx), rec), "text/html; charset=utf-8", "public, max-age=3600", false) : notFound(ctx);
}
