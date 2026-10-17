(function () {
  // Mobile menu
  var menuBtn = document.querySelector(".menu-btn");
  var nav = document.getElementById("site-nav");
  if (menuBtn && nav) {
    menuBtn.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      menuBtn.setAttribute("aria-expanded", String(open));
    });
  }

  // Papel picado: fill any <g data-flags> with flags that follow the string's curve.
  var ns = "http://www.w3.org/2000/svg";
  var colors = ["#D63837", "#F6B934", "#2D8050", "#EBA38D", "#2D60AC"];
  document.querySelectorAll("g[data-flags]").forEach(function (group) {
    for (var i = 0; i < 19; i++) {
      var x = 6 + i * 64;
      var t = x / 1220;
      var y = 10 + 4 * t * (1 - t) * 24;
      var g = document.createElementNS(ns, "g");
      g.setAttribute("class", "flag-wrap");
      g.setAttribute("transform", "translate(" + x + " " + (y - 2) + ")");
      var flag = document.createElementNS(ns, "rect");
      flag.setAttribute("class", "flag");
      flag.setAttribute("width", "60");
      flag.setAttribute("height", "74");
      flag.setAttribute("fill", colors[i % colors.length]);
      flag.setAttribute("mask", "url(#cut)");
      flag.setAttribute("transform", "scale(0.94 1.18)");
      g.appendChild(flag);
      group.appendChild(g);
    }
  });

  // Legal table of contents: always open on wide screens, collapsed on phones.
  var toc = document.querySelector("details.toc");
  if (toc && window.matchMedia("(min-width: 64rem)").matches) toc.open = true;

  // Legal table of contents: highlight the section in view.
  var tocLinks = document.querySelectorAll(".toc a");
  if (tocLinks.length && "IntersectionObserver" in window) {
    var byId = {};
    tocLinks.forEach(function (a) { byId[a.getAttribute("href").slice(1)] = a; });
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        tocLinks.forEach(function (a) { a.classList.remove("active"); });
        var link = byId[e.target.id];
        if (link) link.classList.add("active");
      });
    }, { rootMargin: "-90px 0px -70% 0px" });
    document.querySelectorAll(".prose h2[id]").forEach(function (h) { observer.observe(h); });
  }

  // Waitlist form. Set data-endpoint on the form to a URL that accepts JSON POSTs.
  var form = document.getElementById("join");
  if (!form) return;
  var thanks = document.getElementById("thanks");
  var email = document.getElementById("wl-email");
  var consent = document.getElementById("wl-consent");
  var emailErr = document.getElementById("wl-email-err");
  var consentErr = document.getElementById("wl-consent-err");
  var sendErr = document.getElementById("wl-send-err");

  function check() {
    var okEmail = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email.value.trim());
    email.setAttribute("aria-invalid", String(!okEmail));
    emailErr.hidden = okEmail;
    consentErr.hidden = consent.checked;
    if (!okEmail) { email.focus(); return false; }
    if (!consent.checked) { consent.focus(); return false; }
    return true;
  }

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    sendErr.hidden = true;
    if (!check()) return;
    var data = Object.fromEntries(new FormData(form).entries());
    data.consent = true;
    data.page_language = document.documentElement.lang;
    var done = function () { form.hidden = true; thanks.hidden = false; thanks.focus(); };
    var endpoint = form.dataset.endpoint;
    if (!endpoint) { console.warn("TANDA waitlist: no endpoint set; submission not sent.", data); done(); return; }
    var btn = form.querySelector("button[type=submit]");
    btn.disabled = true;
    fetch(endpoint, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) })
      .then(function (r) { if (!r.ok) throw new Error(String(r.status)); done(); })
      .catch(function () { btn.disabled = false; sendErr.hidden = false; });
  });
})();
