// Saved patents page: the patents saved in this browser, newest first.
import { $, listOf, miniCard, decorateCards } from "./app.js";

function draw() {
  const items = listOf("saved");
  $("#savedGrid").innerHTML = items.map(miniCard).join("");
  $("#savedEmpty").hidden = items.length > 0;
  decorateCards($("#savedGrid"));
}
draw();
document.addEventListener("py:saved", e => { if (!e.detail.on) setTimeout(draw, 250); });
