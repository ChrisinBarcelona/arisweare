// ARIS storefront behaviour: mobile menu, category filter, WhatsApp ordering.
(function () {
  "use strict";

  // Mobile menu
  var toggle = document.querySelector(".menu-toggle");
  var nav = document.getElementById("site-nav");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      toggle.setAttribute("aria-expanded", String(open));
      toggle.textContent = open ? "Close" : "Menu";
    });
    nav.addEventListener("click", function (ev) {
      if (ev.target.closest("a")) {
        nav.classList.remove("open");
        toggle.setAttribute("aria-expanded", "false");
        toggle.textContent = "Menu";
      }
    });
  }

  // Category filter on the home page (?c=tops, or the filter buttons)
  var grid = document.querySelector(".shop .grid");
  var buttons = document.querySelectorAll(".filters [data-filter]");
  var count = document.querySelector(".shop .count");
  function applyFilter(cat) {
    if (!grid) return;
    var shown = 0;
    grid.querySelectorAll(".card").forEach(function (card) {
      var match = cat === "all" || card.dataset.cat === cat;
      card.hidden = !match;
      if (match) shown++;
    });
    buttons.forEach(function (b) { b.setAttribute("aria-pressed", String(b.dataset.filter === cat)); });
    document.querySelectorAll(".nav-primary [data-cat]").forEach(function (a) {
      if (a.dataset.cat === cat || (cat === "all" && a.dataset.cat === "shop")) a.setAttribute("aria-current", "page");
      else a.removeAttribute("aria-current");
    });
    if (count) count.textContent = shown + (shown === 1 ? " piece" : " pieces");
  }
  if (grid) {
    buttons.forEach(function (b) {
      b.addEventListener("click", function () {
        var cat = b.dataset.filter;
        applyFilter(cat);
        var u = new URL(location.href);
        if (cat === "all") u.searchParams.delete("c"); else u.searchParams.set("c", cat);
        history.replaceState(null, "", u.pathname + u.search + "#shop");
      });
    });
    // Header links point at ?c=… — handle them without a reload when already on the home page
    document.querySelectorAll(".nav-primary [data-cat]").forEach(function (a) {
      a.addEventListener("click", function (ev) {
        var cat = a.dataset.cat === "shop" ? "all" : a.dataset.cat;
        ev.preventDefault();
        applyFilter(cat);
        history.replaceState(null, "", cat === "all" ? location.pathname + "#shop" : location.pathname + "?c=" + cat + "#shop");
        document.getElementById("shop").scrollIntoView();
      });
    });
    var initial = new URLSearchParams(location.search).get("c");
    var known = Array.prototype.some.call(buttons, function (b) { return b.dataset.filter === initial; });
    if (initial && known) {
      applyFilter(initial);
      requestAnimationFrame(function () { document.getElementById("shop").scrollIntoView(); });
    }
  }

  // WhatsApp ordering on product pages
  var form = document.querySelector("form.order");
  if (form) {
    var hint = form.querySelector(".size-hint");
    form.addEventListener("change", function () { if (hint) hint.textContent = ""; });
    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var picked = form.querySelector('input[name="size"]:checked');
      if (!picked) {
        if (hint) hint.textContent = "— please choose a size";
        var first = form.querySelector('input[name="size"]');
        if (first) first.focus();
        return;
      }
      var lines = form.dataset.message.split("\n");
      // Insert the size right after the product name line
      var nameIdx = lines.findIndex(function (l) { return /^\*.*\*$/.test(l); });
      lines.splice(nameIdx + 1, 0, "Size: " + picked.value);
      var text = lines.join("\n");
      window.open("https://wa.me/" + form.dataset.wa + "?text=" + encodeURIComponent(text), "_blank", "noopener");
    });
  }

  var y = document.querySelector("[data-year]");
  if (y) y.textContent = new Date().getFullYear();
})();
