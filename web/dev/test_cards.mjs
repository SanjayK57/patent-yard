// The card contract: assets/js/cards.js and pipeline/site_ui/components.py card_html must draw identical markup.
// Run from the repository root: node web/dev/test_cards.mjs
import { readFileSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { card } from "../static/assets/js/cards.js";

const root = fileURLToPath(new URL("../..", import.meta.url));
const { cards } = JSON.parse(readFileSync(new URL("fixtures/cards.json", import.meta.url)));
const py = JSON.parse(execFileSync(process.env.PYTHON || "python3", ["-c",
  "import json, sys; sys.path.insert(0, 'pipeline'); from site_ui.components import card_html; "
  + "print(json.dumps([card_html(c) for c in json.load(open('web/dev/fixtures/cards.json'))['cards']]))"], { cwd: root }));
let bad = 0;
cards.forEach((c, i) => {
  const js = card(c);
  if (js !== py[i]) {
    bad++;
    const at = [...js].findIndex((ch, k) => ch !== py[i][k]);
    console.log(`card ${i} (${c.id}) differs at ${at}:\n  js: ${js.slice(Math.max(0, at - 60), at + 60)}\n  py: ${py[i].slice(Math.max(0, at - 60), at + 60)}`);
  }
});
console.log(bad ? `FAIL: ${bad} of ${cards.length} cards differ` : `ok: ${cards.length} cards identical in Python and JavaScript`);
process.exit(bad ? 1 : 0);
