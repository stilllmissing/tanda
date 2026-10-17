(function () {
  // Mobile menu button
  var menuBtn = document.querySelector(".menu-btn");
  var nav = document.getElementById("site-nav");
  if (menuBtn && nav) {
    menuBtn.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      menuBtn.setAttribute("aria-expanded", String(open));
    });
  }

  // Mega menus: one open at a time; Escape or a click outside closes.
  var triggers = Array.prototype.slice.call(document.querySelectorAll(".nav-trigger"));
  function closeAll(except) {
    triggers.forEach(function (t) {
      if (t === except) return;
      t.setAttribute("aria-expanded", "false");
      document.getElementById(t.getAttribute("aria-controls")).classList.remove("open");
    });
  }
  triggers.forEach(function (t) {
    t.addEventListener("click", function () {
      var panel = document.getElementById(t.getAttribute("aria-controls"));
      var open = t.getAttribute("aria-expanded") !== "true";
      closeAll(t);
      t.setAttribute("aria-expanded", String(open));
      panel.classList.toggle("open", open);
    });
  });
  document.addEventListener("keydown", function (e) {
    if (e.key !== "Escape") return;
    var open = triggers.filter(function (t) { return t.getAttribute("aria-expanded") === "true"; })[0];
    closeAll();
    if (open) open.focus();
  });
  document.addEventListener("click", function (e) {
    if (!e.target.closest(".nav-item")) closeAll();
  });
  // Following an in-page link from a menu closes it.
  document.querySelectorAll(".mega a").forEach(function (a) {
    a.addEventListener("click", function () { closeAll(); if (nav) nav.classList.remove("open"); });
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
    }, { rootMargin: "-110px 0px -70% 0px" });
    document.querySelectorAll(".prose h2[id]").forEach(function (h) { observer.observe(h); });
  }

  // Waitlist forms. The endpoint comes from WAITLIST_ENDPOINT in scripts/build_site.py.
  document.querySelectorAll("form.join").forEach(function (form) {
    var q = function (sel) { return form.querySelector(sel); };
    var email = q("[data-role=email]");
    var consent = q("[data-role=consent]");
    var emailErr = q("[data-role=email-err]");
    var consentErr = q("[data-role=consent-err]");
    var sendErr = q("[data-role=send-err]");
    var thanks = document.getElementById(form.dataset.thanks);

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      sendErr.hidden = true;
      var okEmail = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email.value.trim());
      email.setAttribute("aria-invalid", String(!okEmail));
      emailErr.hidden = okEmail;
      consentErr.hidden = consent.checked;
      if (!okEmail) { email.focus(); return; }
      if (!consent.checked) { consent.focus(); return; }

      var data = Object.fromEntries(new FormData(form).entries());
      data.consent = true;
      if (!data.language) data.language = document.documentElement.lang;
      data.page_language = document.documentElement.lang;
      var done = function () { form.hidden = true; thanks.hidden = false; thanks.focus(); };
      var endpoint = form.dataset.endpoint;
      if (!endpoint) { console.warn("TANDA waitlist: no endpoint set; submission not sent.", data); done(); return; }
      var btn = q("button[type=submit]");
      btn.disabled = true;
      fetch(endpoint, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) })
        .then(function (r) { if (!r.ok) throw new Error(String(r.status)); done(); })
        .catch(function () { btn.disabled = false; sendErr.hidden = false; });
    });
  });
})();
