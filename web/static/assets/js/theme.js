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
    if (s.drawings === "original") d.setAttribute("data-drawings", "original");
  } catch (e) {}
})();
// Page-to-page transitions (site.css @view-transition): a skipped transition is normal, not an error.
addEventListener("pagereveal", function (e) { if (e.viewTransition) { e.viewTransition.ready.catch(function () {}); e.viewTransition.finished.catch(function () {}); } });
addEventListener("pageswap", function (e) { if (e.viewTransition) { e.viewTransition.ready.catch(function () {}); e.viewTransition.finished.catch(function () {}); } });
