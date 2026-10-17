#!/usr/bin/env python3
"""Build the static TANDA website.

Reads page sources from src/site/pages/{en,es}/, wraps them in the shared
layout (utility bar, header with mega menus, footer), and writes finished
HTML to site/, which Vercel serves as-is. Standard library only. Run from
the repo root:

    python3 scripts/build_site.py

Page sources start with a front-matter comment:

    <!--
    title: Pricing
    description: One-sentence summary for search engines.
    nav: pricing            # which main-nav item is active (optional)
    layout: marketing       # marketing | legal
    updated: October 17, 2026   # legal pages only
    applies: tanda website      # legal pages only (optional)
    -->

Inside a page, {{root}} expands to the relative path to the site root for
that language, {{site}} to the relative path to the site/ folder,
{{endpoint}} to WAITLIST_ENDPOINT, and {{contact:KEY}} to the contact
detail KEY from CONTACT below.
"""

import html
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "site"
OUT = ROOT / "site"

# Fill these in before launch. Empty contact values render a neutral fallback sentence.
SITE_URL = ""  # e.g. "https://www.example.com" — enables canonical and hreflang tags
WAITLIST_ENDPOINT = ""  # URL that accepts a JSON POST. Empty = sign-ups are not sent anywhere.
CONTACT = {
    "privacy_email": "",
    "support_email": "",
    "legal_email": "",
    "accessibility_email": "",
    "mailing_address": "",
}

LANGS = ("en", "es")

# Main navigation. Each item opens a mega menu: links (label, description) plus a promo panel.
NAV = {
    "en": [
        {"key": "banking", "label": "Banking", "links": [
            ("banking.html", "Banking overview", "Everything planned for everyday money"),
            ("banking.html#checking", "Checking", "Direct deposit, clear status, statements"),
            ("banking.html#savings", "Savings", "Named goals, automatic transfers, round-ups"),
            ("banking.html#cards", "Debit cards", "Virtual right away, physical by mail"),
            ("banking.html#transfers", "Transfers", "Free standard ACH, optional instant"),
            ("banking.html#overdraft", "Overdraft coverage", "TANDA Spot and Savings Backup"),
        ], "promo": ("var(--sol)", "No planned monthly fee", "Our goal for core checking and savings.", "pricing.html", "See planned pricing")},
        {"key": "help", "label": "Help & safety", "links": [
            ("help-and-safety.html", "Help & safety overview", "How we help and protect you"),
            ("help-and-safety.html#assist", "TANDA Assist", "Answers in English or Spanish"),
            ("help-and-safety.html#shield", "TANDA Shield", "Scam warnings and Emergency Lock"),
            ("help-and-safety.html#trusted-helper", "Trusted Helper", "Family guidance, your control"),
            ("help-and-safety.html#support", "Talk to a person", "Bilingual chat and phone"),
        ], "promo": ("var(--talavera)", "Assist never moves money", "It can explain and guide, but every action needs your confirmation.", "help-and-safety.html#assist", "How Assist works")},
        {"key": "pricing", "label": "Pricing", "links": [
            ("pricing.html#fees", "Planned fees", "Every planned fee in one table"),
            ("pricing.html#tanda-plus", "TANDA+", "Optional membership, $7.99/month"),
            ("pricing.html#rewards", "TANDA Rewards", "Offers from local and national merchants"),
            ("legal/disclosures.html", "Important disclosures", "Conditions behind every claim"),
        ], "promo": ("var(--bugambilia)", "TANDA Spot: up to $50", "Fee-free overdraft coverage for eligible customers.", "banking.html#overdraft", "About TANDA Spot")},
        {"key": "about", "label": "About", "links": [
            ("about.html#story", "Our story", "Why TANDA exists"),
            ("about.html#commitments", "Our commitments", "How we plan to work"),
            ("faq.html", "FAQ", "Straight answers"),
            ("legal/index.html", "Legal center", "Disclosures, privacy and terms"),
        ], "promo": ("var(--verde)", "Not a savings circle", "Our name honors a tradition of trust. Your money stays in your own account.", "about.html#story", "Read our story")},
    ],
    "es": [
        {"key": "banking", "label": "Banca", "links": [
            ("banking.html", "Resumen de la banca", "Todo lo previsto para tu dinero diario"),
            ("banking.html#checking", "Cuenta de cheques", "Depósito directo, estados claros"),
            ("banking.html#savings", "Ahorros", "Metas con nombre, transferencias automáticas"),
            ("banking.html#cards", "Tarjetas de débito", "Virtual al instante, física por correo"),
            ("banking.html#transfers", "Transferencias", "ACH estándar gratis, instantánea opcional"),
            ("banking.html#overdraft", "Cobertura de sobregiro", "TANDA Spot y Respaldo de Ahorros"),
        ], "promo": ("var(--sol)", "Sin cargo mensual previsto", "Nuestra meta para las cuentas básicas de cheques y ahorros.", "pricing.html", "Ver precios previstos")},
        {"key": "help", "label": "Ayuda y seguridad", "links": [
            ("help-and-safety.html", "Resumen de ayuda y seguridad", "Cómo te ayudamos y protegemos"),
            ("help-and-safety.html#assist", "TANDA Assist", "Respuestas en español o en inglés"),
            ("help-and-safety.html#shield", "TANDA Shield", "Avisos de estafa y Bloqueo de Emergencia"),
            ("help-and-safety.html#trusted-helper", "Persona de Confianza", "Guía de tu familia, control tuyo"),
            ("help-and-safety.html#support", "Habla con una persona", "Chat y teléfono bilingües"),
        ], "promo": ("var(--talavera)", "Assist nunca mueve dinero", "Puede explicar y guiar, pero cada acción necesita tu confirmación.", "help-and-safety.html#assist", "Cómo funciona Assist")},
        {"key": "pricing", "label": "Precios", "links": [
            ("pricing.html#fees", "Cargos previstos", "Todos los cargos previstos en una tabla"),
            ("pricing.html#tanda-plus", "TANDA+", "Membresía opcional, $7.99 al mes"),
            ("pricing.html#rewards", "TANDA Rewards", "Ofertas de comercios locales y nacionales"),
            ("legal/disclosures.html", "Divulgaciones importantes", "Las condiciones de cada afirmación"),
        ], "promo": ("var(--bugambilia)", "TANDA Spot: hasta $50", "Cobertura de sobregiro sin cargos para clientes elegibles.", "banking.html#overdraft", "Sobre TANDA Spot")},
        {"key": "about", "label": "Nosotros", "links": [
            ("about.html#story", "Nuestra historia", "Por qué existe TANDA"),
            ("about.html#commitments", "Nuestros compromisos", "Cómo planeamos trabajar"),
            ("faq.html", "Preguntas frecuentes", "Respuestas directas"),
            ("legal/index.html", "Centro legal", "Divulgaciones, privacidad y términos"),
        ], "promo": ("var(--verde)", "No es un círculo de ahorro", "Nuestro nombre honra una tradición de confianza. Tu dinero se queda en tu propia cuenta.", "about.html#story", "Lee nuestra historia")},
    ],
}

STRINGS = {
    "en": {
        "skip": "Skip to content",
        "menu": "Menu",
        "nav_label": "Main",
        "utility_label": "Quick links",
        "status": "Coming to California and Texas. Accounts are not open yet.",
        "utility": [("help-and-safety.html#shield", "Security"), ("faq.html", "FAQ"), ("legal/index.html", "Legal")],
        "cta": "Join the waitlist",
        "switch_label": "Español",
        "switch_title": "Ver esta página en español",
        "home": "Home",
        "footer_tagline": "Bilingual, digital-first banking for every generation. Planned for California and Texas.",
        "footer_cols": [
            ("Banking", [("banking.html#checking", "Checking"), ("banking.html#savings", "Savings"), ("banking.html#cards", "Debit cards"),
                         ("banking.html#transfers", "Transfers"), ("pricing.html", "Pricing")]),
            ("Help & safety", [("help-and-safety.html#assist", "TANDA Assist"), ("help-and-safety.html#shield", "TANDA Shield"),
                               ("help-and-safety.html#trusted-helper", "Trusted Helper"), ("faq.html", "FAQ")]),
            ("Company", [("about.html", "About TANDA"), ("about.html#commitments", "Our commitments"), ("waitlist.html", "Join the waitlist")]),
            ("Legal", [("legal/disclosures.html", "Important disclosures"), ("legal/privacy.html", "Privacy notice"),
                       ("legal/terms.html", "Terms of use"), ("legal/accessibility.html", "Accessibility")]),
        ],
        "not_bank": "TANDA is a financial technology company, not a bank.",
        "footer_note": ("Banking services will be provided by an FDIC-insured partner bank, to be named. TANDA accounts are not yet "
                        "available, and nothing on this site is an offer to open an account or an offer of credit. Products, features, "
                        "fees and benefits described are planned, depend on partner-bank approval and regulatory review, and may change."),
        "footer_refs": ("Superscript numbers refer to the numbered sections of our "
                        "<a href=\"{root}legal/disclosures.html\">Important disclosures</a>."),
        "rights": "All rights reserved.",
        "legal_center": "Legal center",
        "last_updated": "Last updated",
        "applies_to": "Applies to",
        "on_this_page": "On this page",
        "translation_note": "",
        "home_title": "tanda. Bilingual banking for California and Texas",
        "contact_fallback": "Contact details will be published here before accounts open.",
    },
    "es": {
        "skip": "Ir al contenido",
        "menu": "Menú",
        "nav_label": "Principal",
        "utility_label": "Accesos rápidos",
        "status": "Muy pronto en California y Texas. Las cuentas aún no están disponibles.",
        "utility": [("help-and-safety.html#shield", "Seguridad"), ("faq.html", "Preguntas"), ("legal/index.html", "Legal")],
        "cta": "Únete a la lista",
        "switch_label": "English",
        "switch_title": "View this page in English",
        "home": "Inicio",
        "footer_tagline": "Banca bilingüe y digital para todas las generaciones. Prevista para California y Texas.",
        "footer_cols": [
            ("Banca", [("banking.html#checking", "Cuenta de cheques"), ("banking.html#savings", "Ahorros"), ("banking.html#cards", "Tarjetas de débito"),
                       ("banking.html#transfers", "Transferencias"), ("pricing.html", "Precios")]),
            ("Ayuda y seguridad", [("help-and-safety.html#assist", "TANDA Assist"), ("help-and-safety.html#shield", "TANDA Shield"),
                                   ("help-and-safety.html#trusted-helper", "Persona de Confianza"), ("faq.html", "Preguntas frecuentes")]),
            ("Empresa", [("about.html", "Sobre TANDA"), ("about.html#commitments", "Nuestros compromisos"), ("waitlist.html", "Lista de espera")]),
            ("Legal", [("legal/disclosures.html", "Divulgaciones importantes"), ("legal/privacy.html", "Aviso de privacidad"),
                       ("legal/terms.html", "Términos de uso"), ("legal/accessibility.html", "Accesibilidad")]),
        ],
        "not_bank": "TANDA es una empresa de tecnología financiera, no un banco.",
        "footer_note": ("Los servicios bancarios los brindará un banco asociado asegurado por la FDIC, que se dará a conocer más adelante. "
                        "Las cuentas TANDA aún no están disponibles y nada en este sitio es una oferta para abrir una cuenta ni una oferta "
                        "de crédito. Los productos, funciones, cargos y beneficios descritos son planes, dependen de la aprobación del banco "
                        "asociado y de la revisión regulatoria, y pueden cambiar."),
        "footer_refs": ("Los números en superíndice remiten a las secciones numeradas de nuestras "
                        "<a href=\"{root}legal/disclosures.html\">Divulgaciones importantes</a>."),
        "rights": "Todos los derechos reservados.",
        "legal_center": "Centro legal",
        "last_updated": "Última actualización",
        "applies_to": "Se aplica a",
        "on_this_page": "En esta página",
        "translation_note": ("Esta es una traducción al español para tu conveniencia. Si hay alguna diferencia entre esta "
                             "versión y la versión en inglés, prevalecerá la versión en inglés."),
        "home_title": "tanda. Banca bilingüe para California y Texas",
        "contact_fallback": "Los datos de contacto se publicarán aquí antes de abrir las cuentas.",
    },
}

FONT_LINK = "https://fonts.googleapis.com/css2?family=Albert+Sans:ital,wght@0,400;0,600;0,700;0,800;1,400&display=swap"

LAYOUT = """<!doctype html>
<!-- Generated by scripts/build_site.py from {source}. Edit the source, not this file. -->
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title}</title>
<meta name="description" content="{description}">
<meta name="theme-color" content="#00573D">
{seo}<link rel="icon" href="{site}assets/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{font_link}">
<link rel="stylesheet" href="{site}assets/styles.css">
</head>
<body class="layout-{layout}">
<a class="skip" href="#main">{skip}</a>
{sprites}
<div class="utility">
  <div class="wrap">
    <p>{status}</p>
    <nav aria-label="{utility_label}">
{utility}
      <a class="lang-switch" href="{switch_href}" hreflang="{other_lang}" lang="{other_lang}" title="{switch_title}">{switch_label}</a>
    </nav>
  </div>
</div>
<header class="site-header">
  <div class="wrap">
    <a class="wordmark" href="{root}index.html" aria-label="tanda. home">tanda.</a>
    <button class="menu-btn" type="button" aria-expanded="false" aria-controls="site-nav">{menu}</button>
    <nav class="nav" id="site-nav" aria-label="{nav_label}">
      <ul>
{nav}
      </ul>
    </nav>
    <a class="btn btn-primary header-cta" href="{root}waitlist.html">{cta}</a>
  </div>
</header>
<main id="main">
{main}
</main>
<footer class="site-footer">
  <div class="palette-strip" aria-hidden="true"><span></span><span></span><span></span><span></span><span></span><span></span></div>
  <div class="footer-top">
    <div class="wrap">
      <div class="footer-brand">
        <a class="wordmark" href="{root}index.html">tanda.</a>
        <p>{footer_tagline}</p>
      </div>
{footer_cols}
    </div>
  </div>
  <div class="footer-legal">
    <div class="wrap">
      <p class="not-bank">{not_bank}</p>
      <p>{footer_note}</p>
      <p>{footer_refs}</p>
      <div class="footer-bottom">
        <p>&copy; 2026 TANDA. {rights}</p>
        <p><a href="{switch_href}" hreflang="{other_lang}" lang="{other_lang}">{switch_label}</a></p>
      </div>
    </div>
  </div>
</footer>
<script src="{site}assets/site.js" defer></script>
</body>
</html>
"""

LEGAL_MAIN = """<div class="legal-shell">
  <div class="wrap">
    <nav class="breadcrumb" aria-label="Breadcrumb"><a href="{root}index.html">{home}</a><span aria-hidden="true">/</span>{center_crumb}</nav>
    <header class="doc-head">
      <p class="eyebrow">tanda. &nbsp;|&nbsp; {legal_center}</p>
      <h1>{h1}</h1>
      <dl class="doc-meta">
        <div><dt>{last_updated_label}</dt><dd>{updated}</dd></div>
        {applies}
      </dl>
      {translation_note}
    </header>
    <div class="doc-body">
      {toc}
      <article class="prose" id="doc">
{content}
      </article>
    </div>
  </div>
</div>"""

# Shared SVG: the folk-art flower and line icons (24-unit grid, stroked).
SPRITES = """<svg width="0" height="0" class="sprites" aria-hidden="true" focusable="false">
  <defs>
    <g id="flor">
      <ellipse cx="0" cy="-27" rx="12" ry="22"/>
      <ellipse cx="0" cy="-27" rx="12" ry="22" transform="rotate(45)"/>
      <ellipse cx="0" cy="-27" rx="12" ry="22" transform="rotate(90)"/>
      <ellipse cx="0" cy="-27" rx="12" ry="22" transform="rotate(135)"/>
      <ellipse cx="0" cy="-27" rx="12" ry="22" transform="rotate(180)"/>
      <ellipse cx="0" cy="-27" rx="12" ry="22" transform="rotate(225)"/>
      <ellipse cx="0" cy="-27" rx="12" ry="22" transform="rotate(270)"/>
      <ellipse cx="0" cy="-27" rx="12" ry="22" transform="rotate(315)"/>
    </g>
    <g id="i-checking"><rect x="3" y="6" width="18" height="13" rx="2"/><path d="M3 10h18"/><circle cx="16.5" cy="14.5" r="1"/></g>
    <g id="i-savings"><circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="4.5"/><circle cx="12" cy="12" r="0.8"/></g>
    <g id="i-card"><rect x="2.5" y="5.5" width="19" height="13" rx="2"/><path d="M2.5 10h19M6 15h4"/></g>
    <g id="i-transfer"><path d="M4 8h15l-3.5-3.5M20 16H5l3.5 3.5"/></g>
    <g id="i-spot"><path d="M3 12a9 9 0 0 1 18 0z"/><path d="M12 12v6a2 2 0 0 0 4 0"/></g>
    <g id="i-plus"><path d="M12 3.5l2.6 5.3 5.9.9-4.3 4.1 1 5.8-5.2-2.7-5.2 2.7 1-5.8-4.3-4.1 5.9-.9z"/></g>
    <g id="i-assist"><path d="M4 5h16v11H9.5L5 19.5V16H4z"/><path d="M10.2 8.8a1.9 1.9 0 1 1 2.6 1.8c-.5.2-.8.6-.8 1.1v.4"/><circle cx="12" cy="13.6" r="0.4"/></g>
    <g id="i-shield"><path d="M12 3l7.5 3v6c0 4.5-3.2 7.6-7.5 9-4.3-1.4-7.5-4.5-7.5-9V6z"/><path d="M8.8 12l2.2 2.2 4.2-4.4"/></g>
    <g id="i-people"><circle cx="9" cy="8" r="3"/><path d="M3.5 19.5a5.5 5.5 0 0 1 11 0"/><circle cx="17" cy="9" r="2.4"/><path d="M15.8 14.2a4.6 4.6 0 0 1 5.2 4.8"/></g>
    <g id="i-phone"><rect x="7" y="2.5" width="10" height="19" rx="2"/><path d="M11 18.5h2"/></g>
    <g id="i-monitor"><rect x="3" y="4" width="18" height="12" rx="1.5"/><path d="M8.5 20h7M12 16v4"/></g>
    <g id="i-lock"><rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/></g>
  </defs>
</svg>"""


def parse_front_matter(text):
    m = re.match(r"\s*<!--(.*?)-->\s*", text, re.S)
    if not m:
        raise ValueError("missing front matter")
    meta = {}
    for line in m.group(1).strip().splitlines():
        key, _, value = line.partition(":")
        meta[key.strip()] = value.split("  #")[0].strip()
    return meta, text[m.end():]


def slugify(text):
    text = re.sub(r"<[^>]+>", "", text).lower()
    text = re.sub(r"^[\d.]+\s*", "", text)
    for a, b in (("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"), ("ñ", "n"), ("ü", "u")):
        text = text.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def add_heading_ids(content):
    """Give every <h2> without an id one, and return (content, [(id, text)])."""
    toc = []

    def repl(m):
        attrs, inner = m.group(1), m.group(2)
        idm = re.search(r'id="([^"]+)"', attrs)
        hid = idm.group(1) if idm else slugify(inner)
        toc.append((hid, re.sub(r"<[^>]+>", "", inner)))
        if not idm:
            attrs = f' id="{hid}"' + attrs
        return f"<h2{attrs}>{inner}</h2>"

    content = re.sub(r"<h2([^>]*)>(.*?)</h2>", repl, content, flags=re.S)
    return content, toc


def contact(key, lang):
    value = CONTACT.get(key, "")
    if not value:
        return f'<span class="contact-pending">{STRINGS[lang]["contact_fallback"]}</span>'
    if "email" in key:
        return f'<a href="mailto:{html.escape(value)}">{html.escape(value)}</a>'
    return html.escape(value)


def render_nav(lang, root, active):
    items = []
    for item in NAV[lang]:
        mid = f'mega-{item["key"]}'
        links = "\n".join(
            f'              <li><a href="{root}{href}"><strong>{label}</strong><span>{desc}</span></a></li>'
            for href, label, desc in item["links"])
        color, ptitle, ptext, phref, plink = item["promo"]
        current = " current" if item["key"] == active else ""
        items.append(f"""        <li class="nav-item{current}">
          <button class="nav-trigger" type="button" aria-expanded="false" aria-controls="{mid}">{item["label"]}</button>
          <div class="mega" id="{mid}">
            <div class="mega-inner">
            <ul class="mega-links">
{links}
            </ul>
            <div class="mega-promo" style="--promo: {color}">
              <strong>{ptitle}</strong>
              <p>{ptext}</p>
              <a class="text-link" href="{root}{phref}">{plink}</a>
            </div>
            </div>
          </div>
        </li>""")
    return "\n".join(items)


def render(path, lang):
    rel = path.relative_to(SRC / "pages" / lang)
    depth = len(rel.parts) - 1
    root = "../" * depth
    site = root + ("../" if lang == "es" else "")
    s = STRINGS[lang]
    meta, content = parse_front_matter(path.read_text(encoding="utf-8"))

    def expand(text):
        text = text.replace("{{root}}", root).replace("{{site}}", site).replace("{{endpoint}}", html.escape(WAITLIST_ENDPOINT))
        return re.sub(r"\{\{contact:(\w+)\}\}", lambda m: contact(m.group(1), lang), text)

    content = expand(content)
    layout = meta.get("layout", "marketing")
    is_center = rel.as_posix() == "legal/index.html"

    if layout == "legal":
        content, toc = add_heading_ids(content)
        toc_html = ""
        if len(toc) > 2:
            items = "\n".join(f'<li><a href="#{i}">{t}</a></li>' for i, t in toc)
            toc_html = (f'<details class="toc"><summary class="toc-title">{s["on_this_page"]}</summary>'
                        f'<nav aria-label="{s["on_this_page"]}"><ol>{items}</ol></nav></details>')
        applies = ""
        if meta.get("applies"):
            applies = f'<div><dt>{s["applies_to"]}</dt><dd>{meta["applies"]}</dd></div>'
        note = f'<p class="translation-note">{s["translation_note"]}</p>' if s["translation_note"] else ""
        if is_center:
            center_crumb = f'<span aria-current="page">{s["legal_center"]}</span>'
        else:
            center_crumb = (f'<a href="{root}legal/index.html">{s["legal_center"]}</a><span aria-hidden="true">/</span>'
                            f'<span aria-current="page">{meta["title"]}</span>')
        main = LEGAL_MAIN.format(root=root, home=s["home"], center_crumb=center_crumb, legal_center=s["legal_center"],
                                 h1=meta["title"], last_updated_label=s["last_updated"], updated=meta.get("updated", ""),
                                 applies=applies, translation_note=note, toc=toc_html, content=content)
    else:
        main = content
        hero_open = '<section class="page-hero">\n  <div class="wrap">'
        if hero_open in main:
            crumbs = (f'\n    <nav class="crumbs" aria-label="Breadcrumb"><a href="{root}index.html">{s["home"]}</a>'
                      f'<span aria-hidden="true">/</span><span aria-current="page">{meta["title"]}</span></nav>')
            main = main.replace(hero_open, hero_open + crumbs, 1)

    utility = "\n".join(f'      <a href="{root}{h}">{t}</a>' for h, t in s["utility"])

    def col(title, links):
        items = "".join(f'<li><a href="{root}{h}">{t}</a></li>' for h, t in links)
        return f'      <div class="footer-col"><p class="footer-title">{title}</p><ul>{items}</ul></div>'

    footer_cols = "\n".join(col(t, links) for t, links in s["footer_cols"])

    other = "es" if lang == "en" else "en"
    switch_href = root + ("es/" if lang == "en" else "../") + rel.as_posix()

    seo = ""
    if SITE_URL:
        en_url = f"{SITE_URL}/{rel.as_posix()}".replace("/index.html", "/")
        es_url = f"{SITE_URL}/es/{rel.as_posix()}".replace("/index.html", "/")
        own = en_url if lang == "en" else es_url
        seo = (f'<link rel="canonical" href="{own}">\n<link rel="alternate" hreflang="en" href="{en_url}">\n'
               f'<link rel="alternate" hreflang="es" href="{es_url}">\n'
               f'<link rel="alternate" hreflang="x-default" href="{en_url}">\n')

    title = s["home_title"] if rel.as_posix() == "index.html" else f'{meta["title"]} | tanda.'
    return LAYOUT.format(
        source=path.relative_to(ROOT).as_posix(), lang=lang, title=html.escape(title, quote=False),
        description=html.escape(meta.get("description", "")), seo=seo, site=site, font_link=FONT_LINK,
        layout=layout, skip=s["skip"], sprites=SPRITES, status=s["status"], utility_label=s["utility_label"],
        utility=utility, root=root, menu=s["menu"], nav_label=s["nav_label"],
        nav=render_nav(lang, root, meta.get("nav")), switch_href=switch_href, other_lang=other,
        switch_title=s["switch_title"], switch_label=s["switch_label"], cta=s["cta"], main=main,
        footer_tagline=s["footer_tagline"], footer_cols=footer_cols, not_bank=s["not_bank"],
        footer_note=s["footer_note"], footer_refs=s["footer_refs"].format(root=root), rights=s["rights"])


def main():
    if OUT.exists():
        for child in OUT.iterdir():
            if child.name == "README.md":
                continue
            shutil.rmtree(child) if child.is_dir() else child.unlink()
    OUT.mkdir(exist_ok=True)
    shutil.copytree(SRC / "assets", OUT / "assets")

    sources = {lang: sorted(p.relative_to(SRC / "pages" / lang) for p in (SRC / "pages" / lang).rglob("*.html"))
               for lang in LANGS}
    if sources["en"] != sources["es"]:
        missing = set(sources["en"]) ^ set(sources["es"])
        raise SystemExit(f"English and Spanish pages differ: {sorted(map(str, missing))}")

    count = 0
    for lang in LANGS:
        for rel in sources[lang]:
            out = OUT / (rel if lang == "en" else Path("es") / rel)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(render(SRC / "pages" / lang / rel, lang), encoding="utf-8")
            count += 1
    print(f"Built {count} pages into {OUT.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
