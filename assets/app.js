// ARIS storefront behaviour: mobile menu, category filter, WhatsApp ordering.
(function () {
  "use strict";

  // ---------- Mobile menu
  var toggle = document.querySelector(".menu-toggle");
  var nav = document.getElementById("site-nav");
  function setMenu(open) {
    if (!toggle || !nav) return;
    nav.classList.toggle("open", open);
    toggle.setAttribute("aria-expanded", String(open));
    toggle.textContent = open ? "Close" : "Menu";
  }
  if (toggle && nav) {
    toggle.addEventListener("click", function () { setMenu(!nav.classList.contains("open")); });
    nav.addEventListener("click", function (ev) { if (ev.target.closest("a")) setMenu(false); });
    document.addEventListener("keydown", function (ev) {
      if (ev.key === "Escape" && nav.classList.contains("open")) { setMenu(false); toggle.focus(); }
    });
    document.addEventListener("click", function (ev) {
      if (nav.classList.contains("open") && !ev.target.closest(".site-header")) setMenu(false);
    });
  }

  // ---------- Category filter on the home page (?c=tops, or the filter buttons)
  var shop = document.getElementById("shop");
  var grid = shop && shop.querySelector(".grid");
  var buttons = document.querySelectorAll(".filters [data-filter]");
  var count = document.querySelector("#shop .count");
  var navLinks = document.querySelectorAll(".nav-primary [data-cat]");

  function markNav(key) {
    navLinks.forEach(function (a) {
      if (a.dataset.cat === key) a.setAttribute("aria-current", "page");
      else a.removeAttribute("aria-current");
    });
  }
  function applyFilter(cat) {
    if (!grid) return;
    var shown = 0;
    grid.querySelectorAll(".card").forEach(function (card) {
      var match = cat === "all" || card.dataset.cat === cat;
      card.hidden = !match;
      if (match) shown++;
    });
    buttons.forEach(function (b) { b.setAttribute("aria-pressed", String(b.dataset.filter === cat)); });
    markNav(cat === "all" ? "shop" : cat);
    if (count) count.textContent = shown + (shown === 1 ? " piece" : " pieces");
  }
  function setUrl(cat, hash) {
    var q = cat && cat !== "all" ? "?c=" + cat : "";
    history.replaceState(null, "", location.pathname + q + hash);
  }

  if (grid) {
    buttons.forEach(function (b) {
      b.addEventListener("click", function () { applyFilter(b.dataset.filter); setUrl(b.dataset.filter, "#shop"); });
    });
    // Header links point at ?c=… / #… — handle them in place when already on the home page
    navLinks.forEach(function (a) {
      a.addEventListener("click", function (ev) {
        var key = a.dataset.cat;
        var target = key === "experiences" ? document.getElementById("experiences") : shop;
        if (!target) return;
        ev.preventDefault();
        if (key === "experiences") { markNav("experiences"); setUrl(null, "#experiences"); }
        else { var cat = key === "shop" ? "all" : key; applyFilter(cat); setUrl(cat, "#shop"); }
        target.scrollIntoView();
        var heading = target.querySelector("h2");
        if (heading) { heading.setAttribute("tabindex", "-1"); heading.focus({ preventScroll: true }); }
      });
    });
    // Arriving from another page with ?c=… or #section: filter, then scroll once the layout has settled
    var initial = new URLSearchParams(location.search).get("c");
    var known = Array.prototype.some.call(buttons, function (b) { return b.dataset.filter === initial; });
    if (initial && known) applyFilter(initial);
    var landing = location.hash ? document.getElementById(location.hash.slice(1)) : (known ? shop : null);
    if (landing) {
      if (landing.id === "experiences") markNav("experiences");
      var jump = function () {
        var html = document.documentElement, prev = html.style.scrollBehavior;
        html.style.scrollBehavior = "auto";
        landing.scrollIntoView();
        html.style.scrollBehavior = prev;
      };
      requestAnimationFrame(jump);
      window.addEventListener("load", jump, { once: true });
    }
  }

  // ---------- WhatsApp ordering / booking
  function openExternal(href) {
    var a = document.createElement("a");
    a.href = href;
    a.target = "_blank";
    a.rel = "noopener";
    document.body.appendChild(a);
    a.click();
    a.remove();
  }
  document.querySelectorAll("form.order").forEach(function (form) {
    var hint = form.querySelector(".size-hint");
    form.addEventListener("change", function () { if (hint) hint.textContent = ""; });
    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var picked = form.querySelector('input[name="choice"]:checked');
      if (!picked) {
        if (hint) hint.textContent = "— please choose one";
        var first = form.querySelector('input[name="choice"]');
        if (first) first.focus();
        return;
      }
      var text = form.dataset.message.replace("{choice}", form.dataset.choice + ": " + picked.value);
      openExternal("https://wa.me/" + form.dataset.wa + "?text=" + encodeURIComponent(text));
    });
  });

  var y = document.querySelector("[data-year]");
  if (y) y.textContent = new Date().getFullYear();
})();
