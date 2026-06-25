# Content System: Four Tables

A content ops system is four reusable tables, not one giant doc. Borrowed from working operators; mapped to this skill's layout.

## 1. Knowledge base (`wiki/`)

Already covered by the Karpathy-style wiki model in `llm-knowledge-base.md`. Stable facts: company, products, personas, methods, regions, glossary, lessons.

## 2. Competitor table (`monitoring/competitors.yml` + `raw/competitors/`)

What we watch and what they've published.

`monitoring/competitors.yml` shape:

```yaml
competitors:
  - name: example-co
    homepage: https://example.com
    sitemap: https://example.com/sitemap.xml      # for sitemap-diff finder
    rss: https://example.com/feed                  # optional
    google_site_filter: "site:example.com"         # for google-search finder
    primary_query_overlap: [keyword1, keyword2]    # what we'd both rank for
    last_checked: 2026-06-26
```

Run `scripts/monitor_competitors.py .` to capture changes; `scripts/sitemap_diff.py .` for fast new-URL detection.

## 3. Topic / source pool (`wiki/content-opportunities.md` + `monitoring/runs/`)

Every topic worth considering. Each row needs status (`proposed`/`approved`/`drafting`/`published`/`rejected`), persona, intent, source (raw or competitor URL), and proposed route.

User approval is required to move `proposed → approved`. Do not let the table become a wishlist; prune rejected with one-line reason.

**Finder sink contract.** Finders (sitemap-diff, RSS, Google `site:`, social keyword) share `content-opportunities.md` as the single sink. Hard rules to prevent flooding:

- **Per-run cap**: each finder appends at most 10 new `proposed` rows per run.
- **Cross-finder dedup**: skip a URL if it already appears in any status (`proposed` / `approved` / `drafting` / `published` / `rejected`).
- **Dedup key**: canonical URL with trailing slash and tracking params stripped.
- **First-run seeding**: finders that maintain a snapshot cache (e.g. sitemap_diff) must seed the cache on first encounter and append zero rows; never treat full history as "new".

Scripts that ignore these rules will swamp the table and the approval channel becomes the bottleneck.

## 4. Copy library (`wiki/copy-library.md`)

**Reusable proven copy snippets** — the table we previously lacked. Per snippet:

```yaml
- type: title | hook | h2 | cta | objection_handler | meta_description
  copy: "the exact text"
  language: en | zh-CN | …
  works_for: [persona slugs]
  evidence: link to the published page where it performed (open rate, time on page, conversion)
  do_not_overuse: true | false
  source: "internal: published-page-slug" OR "competitor: distilled from URL"
```

Run rules:

- A snippet enters the library only after a real audit-passed publish OR a competitor distillation marked `do_not_overuse: true` (so we don't copy verbatim).
- The audit_content.py script can be extended to flag drafts that reuse the same `title:` snippet more than N times.
- Bilingual snippets live as two entries (en + zh-CN), never machine-translated cross-references.

## Why four, not one giant table

- Different update cadences: knowledge changes monthly, competitors daily, opportunities per-decision, copy per-published-page.
- Different write authority: wiki updates by anyone with raw evidence; opportunities require user approval; copy library only writes from `pass: true` audits.
- Different consumers: drafts read knowledge + copy; outlines read opportunities + knowledge; finders read competitors.

Mixing them produces a doc where nothing is durable and everything must be reread.
