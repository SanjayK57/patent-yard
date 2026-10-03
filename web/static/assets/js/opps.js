// Opportunities page: the field chips show only the picks and ranked patents in that field.
import { $$ } from "./app.js";

for (const b of $$(".ofilter [data-of]")) b.addEventListener("click", () => {
  $$(".ofilter [data-of]").forEach(x => x.setAttribute("aria-pressed", String(x === b)));
  for (const el of $$(".opicks [data-of], .ogrid [data-of]")) el.hidden = !!b.dataset.of && el.dataset.of !== b.dataset.of;
});
