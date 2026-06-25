# AllinCMS Backend Operations

## Browser Rules

- Use the logged-in browser session for `workspace.laicms.com`.
- If login expires, stop and ask the user to log in. Do not guess APIs or use search as a workaround.
- A visible dashboard can be cached while fresh routes still redirect to sign-in; test a real route before long editing sessions.
- Prefer direct known routes after confirming site ID:
- Posts: `/SITE_ID/posts`
  - Products: `/SITE_ID/products`
  - Media: `/SITE_ID/media`
  - Themes: `/SITE_ID/themes`
  - Forms: `/SITE_ID/forms`
  - Domains: `/SITE_ID/domains`

## Article Fill Checklist

For each article:

- Title
- Slug
- Summary/excerpt
- Markdown/HTML body
- Category
- Tags
- Cover image
- SEO title
- SEO description
- Related product/module links where supported
- Publish status

Clear old categories, tags, and covers before adding new ones when editing existing posts.

For batch updates, maintain a local checklist with post ID, old taxonomy, new taxonomy, cover source, audit score, and published URL so no article keeps residual settings.

## Cover Image Selection

Priority:

1. Article-specific screenshot or diagram.
2. Product/module screenshot matching the topic.
3. Process diagram generated from the article.
4. AI-generated visual only when no source image exists and the user allows it.

Each batch should avoid repeated cover images unless the items are intentionally in one cluster.

## Theme Page and Copilot Rules

AllinCMS theme Copilot can insert default ecommerce copy. After every insert/update, inspect the iframe preview and later the live page.

Known risky defaults:

- `hero-commerce` may insert "New season arrivals", "Shop new arrivals", "Weekender Tote", and "Free shipping".
- `feature-grid-proof` may insert retail/material/shipping copy.
- Duplicate block keys make updates ambiguous; delete duplicates first or target exact index.
- Long Copilot prompts may stall. Use one tool action per prompt when needed: insert, inspect, update, delete.

## Generating a Reviewer-Accessible Preview URL

The adversarial reviewer (SOP step 7) is an isolated subagent without your workspace login. It needs an artifact it can fetch without auth. Pick the first option that works:

1. **Public preview URL** — if AllinCMS supports a share/preview token for DRAFT posts, generate it from the post settings, set TTL ≥ 24h, and pass that URL as `preview_url:` in `audits/<slug>-<date>-reviewer-input.yaml`. Most reliable.
2. **Rendered HTML snapshot** — if the preview URL requires login, render the DRAFT to a static file:
   - In the AllinCMS preview iframe, "Save Page As → Webpage Complete" or use the browser's `document.documentElement.outerHTML` via devtools to dump.
   - Save to `audits/<slug>-<date>-preview.html` (include CSS / inlined images so it renders standalone).
   - Pass that path as `preview_html_path:` in the reviewer-input YAML.
3. **Front-end staging URL** — if the site has a non-public staging mirror that does not require login, point there.

If none works, halt the publish — do not proceed with an audit the reviewer cannot execute. `scripts/spawn_reviewer.py` validates that one of `preview_url` / `preview_html_path` exists before writing the input file.

## Publishing Rules

- Do not publish while page status is `Draft` unless final audit passes.
- After clicking Publish, confirm status changes to `Published`.
- Open the front-end URL with a cache-busting query and re-audit.
- Save screenshot evidence for desktop and 390px mobile when visual quality matters.
- Update local indexes before declaring the publish task complete.

## Published Index Fields

Add to `web/published/index.md`:

- Published URL
- AllinCMS site ID
- Post/page/product ID when known
- Title
- Route/slug
- Category
- Tags
- Persona
- Primary query
- Cover URL
- Published time
- Audit score
- Source draft path
