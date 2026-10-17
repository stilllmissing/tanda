# TANDA website

A static, bilingual (English/Español) website for TANDA's pre-launch phase, with a waitlist. Its content follows the PRD v1.1 and MRD v1.0 in `docs/`.

**Don't edit the HTML in `site/` directly.** It is generated from `src/site/` by `scripts/build_site.py`. Edit the source, rebuild, and commit both.

```sh
python3 scripts/build_site.py         # rebuild site/ (Python 3.9+, no dependencies)
python3 -m http.server -d site 8000   # preview at http://localhost:8000
```

## Structure

| Path | What it is |
|---|---|
| `src/site/pages/en/` | English page sources. Each starts with a front-matter comment (title, description, nav, layout). |
| `src/site/pages/es/` | Spanish page sources, with the same file names. The build fails if a page exists in only one language. |
| `src/site/assets/` | Shared CSS, JS and favicon, copied to `site/assets/`. |
| `scripts/build_site.py` | Wraps each page in the shared header and footer, builds the legal table of contents, and fills in contact details. |

Pages: home, Banking, Help & safety, Pricing, About, FAQ, Waitlist, and the legal section: Legal center, Important disclosures, Privacy notice, Terms of use, Accessibility statement. Spanish versions are under `/es/`.

**Layouts:** `marketing` uses the brand treatment (papel picado, folk-art flowers). `legal` is a plain document layout with breadcrumbs, last-updated date, a table of contents built from `<h2>` headings, and print styles.

**Disclosure references:** superscript numbers on marketing pages link to the matching numbered section of `legal/disclosures.html` (for example, `#d6` for TANDA Spot). Keep the numbers in sync if you add or reorder sections.

## Deploy on Vercel

`vercel.json` at the repo root serves `site/` with Vercel's static builder. Its `builds` setting overrides the dashboard's framework preset, so nothing gets installed or built on Vercel; it serves the committed `site/` folder. Leave the project's Root Directory as the repo root.

## Before going live

- [ ] **Legal review.** The disclosures, privacy notice, terms and accessibility statement are drafts written from the PRD and MRD. Counsel and the partner bank must review them, including governing law and any dispute-resolution terms.
- [ ] **Contact details.** Fill in `CONTACT` (and `SITE_URL` for canonical/hreflang tags) at the top of `scripts/build_site.py`, then rebuild. Until then, legal pages say contact details will be published before accounts open.
- [ ] **Waitlist endpoint.** Set `data-endpoint` on `<form id="join">` in both `waitlist.html` sources to a URL that accepts a JSON `POST`. **Until it's set, sign-ups are not sent anywhere**, though visitors still see the confirmation.
- [ ] **Privacy notice accuracy.** Update it if you add analytics, cookies or an email provider.
- [ ] **Spanish.** Get a professional translation review. The current Spanish is a draft.
- [ ] **Partner bank.** Name it only once it is contracted and approved.
- [ ] **Artwork.** Replace the concept card art and papel picado with commissioned or licensed original work.
- [ ] **Accessibility audit.** Run a WCAG 2.2 AA audit with real assistive technology.
