#!/usr/bin/env python3
"""Build the static TANDA website.

Reads page sources from src/site/pages/{en,es}/, wraps them in the shared
layout, and writes finished HTML to site/ (which Vercel serves as-is).
Standard library only. Run from the repo root:

    python3 scripts/build_site.py

Page sources start with a front-matter comment:

    <!--
    title: Pricing
    description: One-sentence summary for search engines.
    nav: pricing            # which nav item is active (optional)
    layout: marketing       # marketing | legal
    updated: October 17, 2026   # legal pages only
    -->

Inside a page, {{root}} expands to the relative path to the site root for
that language, {{site}} to the relative path to the site/ folder, and
{{contact:KEY}} to the contact detail KEY from CONTACT below.
"""

import html
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "site"
OUT = ROOT / "site"

# Fill these in before launch. Empty values render a neutral fallback sentence.
SITE_URL = ""  # e.g. "https://www.example.com" — enables canonical and hreflang tags
CONTACT = {
    "privacy_email": "",
    "support_email": "",
    "legal_email": "",
    "accessibility_email": "",
    "mailing_address": "",
}

LANGS = ("en", "es")

STRINGS = {
    "en": {
        "skip": "Skip to content",
        "menu": "Menu",
        "nav_label": "Main",
        "nav": [("banking", "banking.html", "Banking"), ("help", "help-and-safety.html", "Help & safety"),
                ("pricing", "pricing.html", "Pricing"), ("about", "about.html", "About"), ("faq", "faq.html", "FAQ")],
        "cta": "Join the waitlist",
        "switch_label": "Español",
        "switch_title": "Ver esta página en español",
        "footer_product": "Product",
        "footer_company": "Company",
        "footer_legal": "Legal",
        "footer_links_product": [("banking.html", "Banking"), ("help-and-safety.html", "Help & safety"), ("pricing.html", "Pricing")],
        "footer_links_company": [("about.html", "About"), ("faq.html", "FAQ"), ("waitlist.html", "Waitlist")],
        "footer_links_legal": [("legal/disclosures.html", "Important disclosures"), ("legal/privacy.html", "Privacy notice"),
                               ("legal/terms.html", "Terms of use"), ("legal/accessibility.html", "Accessibility"),
                               ("legal/index.html", "Legal center")],
        "footer_note": ("TANDA is a financial technology company, not a bank. Banking services will be provided by an "
                        "FDIC-insured partner bank, to be named. TANDA accounts are not yet available, and nothing on this "
                        "site is an offer to open an account. Features, fees and benefits described are planned and may change. "
                        "See <a href=\"{root}legal/disclosures.html\">Important disclosures</a>."),
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
        "nav": [("banking", "banking.html", "Banca"), ("help", "help-and-safety.html", "Ayuda y seguridad"),
                ("pricing", "pricing.html", "Precios"), ("about", "about.html", "Nosotros"), ("faq", "faq.html", "Preguntas")],
        "cta": "Únete a la lista",
        "switch_label": "English",
        "switch_title": "View this page in English",
        "footer_product": "Producto",
        "footer_company": "Empresa",
        "footer_legal": "Legal",
        "footer_links_product": [("banking.html", "Banca"), ("help-and-safety.html", "Ayuda y seguridad"), ("pricing.html", "Precios")],
        "footer_links_company": [("about.html", "Nosotros"), ("faq.html", "Preguntas frecuentes"), ("waitlist.html", "Lista de espera")],
        "footer_links_legal": [("legal/disclosures.html", "Divulgaciones importantes"), ("legal/privacy.html", "Aviso de privacidad"),
                               ("legal/terms.html", "Términos de uso"), ("legal/accessibility.html", "Accesibilidad"),
                               ("legal/index.html", "Centro legal")],
        "footer_note": ("TANDA es una empresa de tecnología financiera, no un banco. Los servicios bancarios los brindará un "
                        "banco asociado asegurado por la FDIC, que se dará a conocer más adelante. Las cuentas TANDA aún no "
                        "están disponibles y nada en este sitio es una oferta para abrir una cuenta. Las funciones, cargos y "
                        "beneficios descritos son planes y pueden cambiar. Consulta las "
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

FONT_LINK = ("https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700;"
             "12..96,800&family=Atkinson+Hyperlegible:ital,wght@0,400;0,700;1,400"
             "&family=Public+Sans:ital,wght@0,400;0,600;0,700;1,400&display=swap")

LAYOUT = """<!doctype html>
<!-- Generated by scripts/build_site.py from {source}. Edit the source, not this file. -->
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title}</title>
<meta name="description" content="{description}">
{seo}<link rel="icon" href="{site}assets/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{font_link}">
<link rel="stylesheet" href="{site}assets/styles.css">
</head>
<body class="layout-{layout}">
<a class="skip" href="#main">{skip}</a>
{sprites}
<header class="site-header">
  <div class="wrap">
    <a class="wordmark" href="{root}index.html" aria-label="tanda. home">tanda<span class="dot">.</span></a>
    <button class="menu-btn" type="button" aria-expanded="false" aria-controls="site-nav">{menu}</button>
    <nav class="nav" id="site-nav" aria-label="{nav_label}">
{nav}
    </nav>
    <div class="header-actions">
      <a class="lang-switch" href="{switch_href}" hreflang="{other_lang}" lang="{other_lang}" title="{switch_title}">{switch_label}</a>
      <a class="btn btn-primary header-cta" href="{root}waitlist.html">{cta}</a>
    </div>
  </div>
</header>
<main id="main">
{main}
</main>
<footer class="site-footer">
  <div class="tile-strip" aria-hidden="true"></div>
  <div class="wrap">
    <div class="footer-grid">
      <div class="footer-brand">
        <a class="wordmark" href="{root}index.html">tanda<span class="dot">.</span></a>
      </div>
{footer_cols}
    </div>
    <div class="footer-legal">
      <p>{footer_note}</p>
      <p>&copy; 2026 TANDA. {rights}</p>
    </div>
  </div>
</footer>
<script src="{site}assets/site.js" defer></script>
</body>
</html>
"""

LEGAL_MAIN = """<div class="legal-shell">
  <div class="wrap">
    <nav class="breadcrumb" aria-label="Breadcrumb"><a href="{root}legal/index.html">{legal_center}</a><span aria-hidden="true">/</span><span aria-current="page">{h1}</span></nav>
    <header class="doc-head">
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
    <mask id="cut" maskContentUnits="userSpaceOnUse">
      <path d="M0 0H64V66L58 72L52 66L46 72L40 66L34 72L28 66L22 72L16 66L10 72L4 66L0 70Z" fill="#fff"/>
      <g fill="#000">
        <g transform="translate(32 30) scale(0.3)"><use href="#flor"/></g>
        <circle cx="32" cy="30" r="3.2" fill="#fff"/>
        <path d="M10 8l4 4-4 4-4-4z M54 8l4 4-4 4-4-4z M10 46l4 4-4 4-4-4z M54 46l4 4-4 4-4-4z"/>
        <circle cx="32" cy="8" r="2.2"/><circle cx="32" cy="54" r="2.2"/>
        <circle cx="8" cy="30" r="2.2"/><circle cx="56" cy="30" r="2.2"/>
        <rect x="4" y="60" width="56" height="2"/>
      </g>
    </mask>
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


def render(path, lang):
    rel = path.relative_to(SRC / "pages" / lang)
    depth = len(rel.parts) - 1
    root = "../" * depth
    site = root + ("../" if lang == "es" else "")
    s = STRINGS[lang]
    meta, content = parse_front_matter(path.read_text(encoding="utf-8"))

    def expand(text):
        text = text.replace("{{root}}", root).replace("{{site}}", site)
        return re.sub(r"\{\{contact:(\w+)\}\}", lambda m: contact(m.group(1), lang), text)

    content = expand(content)
    layout = meta.get("layout", "marketing")

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
        main = LEGAL_MAIN.format(root=root, legal_center=s["legal_center"], h1=meta["title"],
                                 last_updated_label=s["last_updated"], updated=meta.get("updated", ""),
                                 applies=applies, translation_note=note, toc=toc_html, content=content)
    else:
        main = content

    current = ' aria-current="page"'
    nav = "\n".join(
        f'      <a href="{root}{href}"{current if meta.get("nav") == key else ""}>{label}</a>'
        for key, href, label in s["nav"])

    def col(title, links):
        items = "".join(f'<li><a href="{root}{h}">{t}</a></li>' for h, t in links)
        return f'      <div class="footer-col"><p class="footer-title">{title}</p><ul>{items}</ul></div>'

    footer_cols = "\n".join([col(s["footer_product"], s["footer_links_product"]),
                             col(s["footer_company"], s["footer_links_company"]),
                             col(s["footer_legal"], s["footer_links_legal"])])

    other = "es" if lang == "en" else "en"
    # Path from this page to the same page in the other language.
    if lang == "en":
        switch_href = root + "es/" + rel.as_posix()
    else:
        switch_href = root + "../" + rel.as_posix()

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
        layout=layout, skip=s["skip"], sprites=SPRITES, root=root, menu=s["menu"], nav_label=s["nav_label"],
        nav=nav, switch_href=switch_href, other_lang=other, switch_title=s["switch_title"],
        switch_label=s["switch_label"], cta=s["cta"], main=main, footer_cols=footer_cols,
        footer_note=s["footer_note"].format(root=root), rights=s["rights"])


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
