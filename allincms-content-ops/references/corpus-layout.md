# Corpus Layout

Use this layout for every project so Codex, Claude, WorkBuddy, and humans can share the same knowledge base.

```text
project-root/
  PROJECT_INDEX.md
  AGENTS.md
  CLAUDE.md
  WORKBUDDY.md
  raw/
    index.md
    competitors/index.md
    YYYY-MM-DD-source-name/
  wiki/
    index.md
    company.md
    glossary.md
    content-opportunities.md
    lessons.md
    products/
    personas/
    methodology/
    competitors/
    regions/
    llm-knowledge-base.md
  web/
    index.md
    drafts/
    published/index.md
    pages/
    posts/
    products/
  monitoring/
    index.md
    competitors.yml
    runs/
  media/
    index.md
    source/
    processed/
    uploaded/
  audits/
    index.md
```

## raw/

Raw is append-only. Keep originals and extraction outputs. Examples:

- `raw/2026-06-25-allincms-docs/original.pdf`
- `raw/2026-06-25-allincms-docs/extracted.md`
- `raw/competitors/2026-06-25-competitor-a/pricing-page.md`

Each raw item must have:

- `source_path`
- `source_url` when available
- `source_type`
- `collected_at`
- `rights`
- `extraction_method`
- `summary`
- `linked_wiki_pages`

Raw is append-only. Never edit a captured file after `collected_at`. If the source changes, create a new dated capture and link the two via `supersedes:` / `superseded_by:`. `scripts/audit_content.py --check-raw-immutable` flags any raw file whose mtime is newer than its frontmatter `collected_at`.

## wiki/

Wiki is compiled knowledge. It should not read like pasted source notes. Use short pages with links:

- Company positioning and proof.
- Product capabilities and limits.
- Persona pain points and buying triggers.
- Region and language norms.
- Competitor patterns and gaps.
- SEO/SEM methodology.
- Glossary and preferred terms.
- LLM knowledge-base rules and context engineering notes.

Every important claim should include a raw path or a note that it needs verification.

Each wiki page frontmatter must include `consumed_by: []` (paths of web drafts that cite this page). When a wiki fact changes, the next agent walks `consumed_by` to flag affected web pages for re-audit. `audit_content.py` verifies the back-link is reciprocal.

Use `wiki/llm-knowledge-base.md` for project-specific lessons that future agents need before content work. Keep general skill rules inside this skill; keep product/site facts in the project wiki.

## web/

Web is publishable material. A draft must include frontmatter:

```yaml
title:
slug:
route:
content_type: article|page|product|guide
status: draft|review|published
persona:
region:
search_intent:
primary_query:
secondary_queries: []
category:
tags: []
meta_title:           # 35-65 chars
meta_description:     # 120-165 chars
cover_image:
cover_alt:
source_wiki: []
source_raw: []
differentiation:    # required: how this page beats the strongest competitor URL we borrow from
credibility_evidence: []   # required: list of paths under raw/ or media/ (charts, customer screenshots, product videos, comparisons)
published_at:       # YYYY-MM-DD when status flipped to published
updated_at:         # YYYY-MM-DD of last non-typo edit
author:             # human or team name
related: []         # 3-5 internal links to sibling articles
source_external:    # optional: URL/PDF if heavily based on one external piece
last_seo_check:     # YYYY-MM-DD of the last meta/schema/canonical review
competitors_referenced: []
allincms:
  site_id:
  post_id:
  category_id:
  tag_ids: []
  published_url:
  canonical_url:           # if syndicated; else leave blank
  noindex: false
  schema_recommendation:   # Article | Product | FAQPage | HowTo
  hreflang: []             # [{lang: en, href: ...}], required when sibling-language slug exists (machine check deferred — see wiki/backlog.md)
  site_id:
  post_id:
  category_id:
  tag_ids: []
  published_url:
audit:
  content_score:
  aesthetic_score:
  seo_geo_score:
  final_score:
```

The full required-field list lives in `markdown-style-guide.md`; `audit_content.py` enforces it. Use `scripts/new_draft.py <slug>` to scaffold instead of hand-writing this block.

## Index Rules

- `PROJECT_INDEX.md` is the root table of contents and onboarding file.
- Top-level folders (`raw/`, `wiki/`, `web/`, `monitoring/`, `media/`, `audits/`) each have an `index.md`.
- **Sub-folders are index-free by default.** Add an `index.md` to a sub-folder only when it holds > 5 sibling files, or when naming is ambiguous enough that grep/find won't suffice. A stale half-empty index is worse than no index. See `routing-matrix.md` → Subfolder index rule.
- `web/index.md` links category, tag, page, post, product, draft, and published indexes.
- Every published URL appears exactly once in `web/published/index.md`.
- Every monitored competitor item appears in `raw/competitors/index.md`.
- Every proposed topic appears in `wiki/content-opportunities.md` with status: `proposed`, `approved`, `drafting`, `published`, or `rejected`.
