// The cloud half of the daily check, so the site stays honest while the Mac that builds it is off. Every day this
// Worker reads the newest USPTO Official Gazette issues and adds every patent reinstated by a late fee payment to
// the KV list "reinstated". Patent pages (functions/patents) show such a patent as no longer free, and browse hides
// it, until the next full build on the Mac drops it from the register (pipeline/register.py verify does the same
// check there). Free plan: one cron run a day, a few subrequests, one KV write when the list changes.
const ISSUE = w => `https://patentsgazette.uspto.gov/week${String(w).padStart(2, "0")}/OG/TOC.htm`;

const isoWeek = d => {
  const t = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate()));
  t.setUTCDate(t.getUTCDate() + 4 - (t.getUTCDay() || 7));
  return Math.ceil(((t - Date.UTC(t.getUTCFullYear(), 0, 1)) / 864e5 + 1) / 7);
};

// patent numbers in the "Patents Reinstated ..." section of one issue's table of contents (pipeline/uspto.py parse_gazette)
export function reinstated(page) {
  const toc = [...page.matchAll(/<a href="#(ref\d+)">([^<]{8,})</g)].map(m => [m[2].replace(/\s+/g, " ").trim(), m[1]]);
  const ref = toc.find(([t]) => t.startsWith("Patents Reinstated"))?.[1];
  if (!ref) return [];
  const i = page.indexOf(`name="${ref}"`), j = page.indexOf('name="ref', i + 10);
  const text = page.slice(i, j > 0 ? j : undefined).replace(/<[^>]+>/g, " ");
  return [...new Set([...text.matchAll(/(\d{1,2},\d{3},\d{3})\s+\d{2}\/\d{3},\d{3}/g)].map(m => m[1].replace(/,/g, "")))];
}

async function run(env) {
  const week = isoWeek(new Date()), found = [];
  for (const w of [week, week - 1 || 52]) {
    const res = await fetch(ISSUE(w), { headers: { "user-agent": "PatentYard/1.0 (+https://patentyard.pages.dev)" } });
    if (res.ok) found.push(...reinstated(await res.text()));
  }
  const old = (await env.PY_KV.get("reinstated", "json")) || { numbers: [] };
  const all = [...new Set([...old.numbers, ...found])].sort();
  if (all.length !== old.numbers.length)
    await env.PY_KV.put("reinstated", JSON.stringify({ numbers: all.slice(-20000), checked: new Date().toISOString() }));
  return { week, found: found.length, total: all.length };
}

export default {
  async scheduled(event, env, ctx) { ctx.waitUntil(run(env)); },
};
