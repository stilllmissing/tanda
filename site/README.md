# TANDA pre-launch website

A single-page, bilingual (English/Español) marketing site with a waitlist. It is plain HTML, CSS and JS with no build step. Its content follows the PRD v1.1 and MRD v1.0 in `docs/`.

## Run it

Open `index.html` in a browser, or serve the folder with any static host (GitHub Pages, Netlify, Vercel, S3):

```sh
python3 -m http.server -d site 8000
```

## Deploy on Vercel

`vercel.json` at the repo root tells Vercel this is a static site: no framework, no install or build step, and `site/` is the output directory. Leave the project's Root Directory as the repo root.

## How it works

- **Language:** English is in the HTML. Spanish lives in the `es` dictionary in the inline script. Keys match the `data-i18n` attributes. The visitor's choice is remembered. A `#es` link opens the site in Spanish, and Spanish browsers default to it.
- **Theme:** light and dark follow the visitor's system setting. Colors are tokens in `:root`, using the PRD v1.1 palette.
- **Waitlist:** set `data-endpoint` on `<form id="join">` to a URL that accepts a JSON `POST` (HubSpot, Formspree, your own API). **Until it's set, sign-ups are not sent anywhere.** The form still shows the confirmation and logs a console warning.

## Before going live

These come from the MRD's compliance guardrails and acceptance criteria:

- [ ] Get the Spanish copy professionally translated and reviewed. The current Spanish is a draft.
- [ ] Have legal/compliance and the partner bank review every claim and disclosure.
- [ ] Wire the waitlist endpoint and add a privacy policy link.
- [ ] Name the partner bank in the footer and FAQ only once it is contracted and approved.
- [ ] Replace the concept card art and papel picado with commissioned or licensed original artwork.
- [ ] Run an accessibility audit (WCAG 2.2 AA) with real screen readers.
