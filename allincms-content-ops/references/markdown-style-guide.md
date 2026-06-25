# Markdown Style Guide

Every web draft (`web/drafts/`, `web/pages/`, `web/posts/`, `web/products/`) follows this guide. `audit_content.py` enforces the machine-checkable parts; the rest is reviewer-judged.

## Required frontmatter (web content)

`audit_content.py` checks every field is present and non-empty. Missing any blocks publish.

```yaml
---
title:                # under 70 chars; reader-facing
slug:                 # kebab-case, unique site-wide
route:                # final URL path; matches AllinCMS taxonomy
content_type:         # article | page | product | guide
status:               # draft | review | published
persona:              # one persona slug from wiki/personas/
region:               # ISO-ish: en-US, zh-CN, de-DE, …
search_intent:        # one sentence — what the reader's job is
primary_query:        # exact query the page targets
secondary_queries: [] # 3–5 long-tails
category:             # one AllinCMS category
tags: []              # 3–8 AllinCMS tags
meta_title:           # 35–65 chars (Google SERP window)
meta_description:     # 120–165 chars (Google SERP window)
cover_image:          # path under media/uploaded/ or full URL
cover_alt:            # under 125 chars, describes the image AND the claim
differentiation:      # one sentence: how this page beats the strongest competitor URL borrowed from
credibility_evidence: # list of paths (data charts, customer screenshots, product videos, comparisons); each path MUST exist
source_wiki: []       # repo-relative paths to wiki pages cited
source_raw: []        # repo-relative paths to raw captures cited
competitors_referenced: []  # competitor URLs whose ideas informed this draft
published_at:         # YYYY-MM-DD (set when status flips to published)
updated_at:           # YYYY-MM-DD (any non-typo edit bumps this)
author:               # human or team name
source_external:      # optional: URL/PDF if heavily based on one external piece
related: []           # 3–5 internal links to sibling articles
last_seo_check:       # YYYY-MM-DD of the last meta / schema review
allincms:
  site_id:
  post_id:
  category_id:
  tag_ids: []
  published_url:
  canonical_url:        # if syndicated; else leave blank
  noindex: false        # true only for thin/utility pages
  schema_recommendation: Article | Product | FAQPage | HowTo  # what JSON-LD AllinCMS should emit
audit:
  content_score:
  aesthetic_score:
  seo_geo_score:
  final_score:
---
```

## Body conventions

### Length

- 350 – 3500 words (audit_content.py enforces).
- Pages outside this range usually fail Usefulness; if you genuinely need 200 words (e.g. a glossary stub), split into a `content_type: page` with `noindex: true`.

### Heading hierarchy

- `#` is reserved for the page title (AllinCMS may render this from the frontmatter `title:`; do not duplicate in body).
- Top-level body sections use `##`; subsections `###`; never skip levels.
- Each `##` must answer one buyer objection or one sub-query from `secondary_queries`. If a `##` doesn't, delete or merge it.
- Headings must fit their container (< 80 chars rendered).

### Opening

- First sentence answers the primary query directly. No throat-clearing, no "In today's fast-paced world …".
- If the answer needs nuance, provide it in sentence 2. Sentence 3 sends the reader to the right section.

### Links

- Internal: relative path from the publish root (`/blog/foo` not the .md path).
- External: full URL with `https://`. Quote the source when citing competitors so readers can verify.
- Every claim with a number cites its `raw/` source path *and* the public source URL.
- 3 – 8 internal links per page. Fewer = orphan; more = link spam.

### Images

- Filename: kebab-case, primary-query keyword present, under 60 chars, no `image1.png` / `pic.jpg`.
- Alt: under 125 chars, describes the image AND the claim it supports. No generic words ("image", "photo").
- Caption: under 30 words, gives takeaway + invites scrolling.
- Cover image: real screenshot or topic-specific generated visual; no repeated covers across cluster unless intentional.
- Credibility artifacts (entries in `credibility_evidence:`) must include `source:` (customer id, order no, ticket no, or public URL) somewhere on the page so reviewer can verify the artifact isn't stock.

### CTAs

- One primary CTA per page, matching the funnel stage in `search_intent`.
- CTA verbs are concrete: "Book a 15-min demo", "Download the import template" — never "Learn more" / "Get started".
- Secondary CTAs (newsletter, related content) live at most once at the page end. No mid-body popups.

### Bilingual content

- English and zh-CN pages live as separate slugs with `hreflang` set in `allincms`. No machine-translated cross-references.
- Snippets reused across languages enter `wiki/copy-library.md` as separate entries (`language: en` and `language: zh-CN`), never as one bilingual row.

## SEO / GEO checks (machine + manual)

Machine (`audit_content.py`):

- `meta_title` length in 35–65 chars
- `meta_description` length in 120–165 chars
- frontmatter completeness (all required fields non-empty)
- residue terms absent
- AI-smell phrases absent
- image alt present, filename not generic
- `source_wiki` / `source_raw` cited
- `credibility_evidence` paths exist
- web → wiki `consumed_by` reciprocity (run with `--check-backlinks`)

Manual (reviewer + `last_seo_check` cadence):

- canonical_url correctness (especially if syndicated)
- schema_recommendation actually emitted as JSON-LD by AllinCMS theme
- mobile rendering at 390px — no horizontal overflow, no content hidden
- LCP / CLS within target (3.0s / 0.1) — front-end performance
- internal link graph: this page is reachable in ≤ 3 hops from homepage
- breadcrumbs match `route`

## Anti-patterns (auto-flag or reject in review)

- Generic intros ("In today's fast-paced world", "Navigating the complexities of…")
- Lists of features without buyer outcome
- Stock customer testimonials with no source
- Comparison tables where every column is "our product wins"
- "Industry-leading" / "best-in-class" without proof
- Empty `credibility_evidence:` or paths that don't exist
- Translating English to Chinese (or vice versa) instead of writing fresh in target language
- Same `title:` or `meta_title:` reused across pages

## Update protocol

- Every meaningful edit bumps `updated_at` and re-runs `audit_content.py`.
- Every SEO-relevant edit (meta, schema, canonical) also bumps `last_seo_check`.
- A page that drifts > 180 days without `last_seo_check` shows up in `audit_content.py --status` as SEO-stale.
