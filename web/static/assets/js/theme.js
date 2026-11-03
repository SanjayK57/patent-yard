// Applies saved display settings before the page paints, so there is no flash of the wrong theme.
// Settings live in this browser only (localStorage "patentyard.settings"); see settings.js.
(function () {
  try {
    var d = document.documentElement;
    d.classList.add("js");  // scroll-in animations hide content only when a script can show it again
    var s = JSON.parse(localStorage.getItem("patentyard.settings") || "{}");
    if (s.theme === "light" || s.theme === "dark") d.setAttribute("data-theme", s.theme);
    if (s.motion === "reduce") d.setAttribute("data-motion", "reduce");
    if (s.text === "large") d.setAttribute("data-text", "large");
    if (s.drawings === "inverted") d.setAttribute("data-drawings", "inverted");
  } catch (e) {}
})();
// Page-to-page transitions (site.css @view-transition): a skipped transition is normal, not an error.
// Opening a patent from a card carries the card's drawing into the patent page's drawing: both ends get the
// view-transition name "pfig", one element per page, cleared again so a back-navigated page can't hold a stale one.
(function () {
  var named = null;
  function name(el) { if (named) named.style.viewTransitionName = ""; named = el; if (el) el.style.viewTransitionName = "pfig"; }
  function quiet(t) { t.ready.catch(function () {}); t.finished.catch(function () {}); }
  addEventListener("pageswap", function (e) {
    name(null);
    if (!e.viewTransition) return;
    quiet(e.viewTransition);
    var to = e.activation && e.activation.entry && e.activation.entry.url;
    if (!to) return;
    var path = new URL(to).pathname, links = document.querySelectorAll(".card a[href]");
    for (var i = 0; i < links.length; i++) if (links[i].pathname === path) { name(links[i].closest(".card").querySelector(".fig")); break; }
  });
  addEventListener("pagereveal", function (e) {
    name(null);
    if (!e.viewTransition) return;
    quiet(e.viewTransition);
    var fig = document.querySelector(".bigfig, .gfront, .gsheets figure");
    if (fig && fig.getBoundingClientRect().top < innerHeight * 0.8) name(fig);
    e.viewTransition.finished.then(function () { name(null); }, function () { name(null); });
  });
})();
