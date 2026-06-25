# Audits

## Pass Criteria (all four required)

1. Total score ≥ 8.5 / 10.
2. Every individual area ≥ 70% of its max points (no single weak dimension can be masked by strong ones).
3. Zero blocking-residue hits (see list below).
4. ≥ 5 adversarial objections logged, each with author response (`accepted` + diff link / `rejected` + reasoning / `deferred` + issue id).

A run that fails any of the four is not publishable, regardless of total score.

## Reviewer Isolation Protocol

Adversarial review MUST run in a fresh subagent — Claude: `Agent` tool with `subagent_type=general-purpose`; Codex: a new session — using the brief in `codex-adversarial-reviewer.md`.

The reviewer receives ONLY:

- the search-intent brief (persona, query, region, conversion)
- the rendered preview URL or HTML (not the draft markdown)
- the top 3 competitor URLs for the same query

The reviewer MUST NOT see: the draft markdown source, the wiki source pages, the author's self-assessment, prior audit files for this slug.

The reviewer computes the score independently. The author may rebut individual objections but cannot edit the reviewer's score directly — a rejected objection still counts as logged, with reasoning visible in `audits/<slug>-<date>.md`.

If the reviewer surfaces < 5 objections or refuses to engage, the audit is invalid; re-run in a different subagent session.

## Scorecard

| Area | Points | Questions |
|---|---:|---|
| Search intent | 1.5 | Is persona, query, pain, and conversion clear? |
| Source grounding | 1.2 | Does it use existing raw/wiki facts and cite internal source paths? Does each artifact listed in `credibility_evidence:` carry a verifiable `source:` (customer id, order no, ticket no, or public URL) rather than a generic stock image? |
| Usefulness | 1.5 | Does it solve the reader's problem without needing another search? |
| SEO/GEO structure | 1.2 | Are title, slug, meta, headings, answer blocks, internal links, and schema recommendation present? |
| Visual/media fit | 1.2 | Are images relevant, clear, localized, and uploaded with alt/caption? |
| AllinCMS backend fit | 1.0 | Are category, tags, cover, route, SEO fields, and publish status correct? |
| Anti-AI and trust | 1.2 | Is it non-generic, claim-safe, no fake names/metrics, no AI smell? |
| Mobile and rendering | 1.2 | Does 390px mobile work with no horizontal overflow and loaded images? |

## Blocking Residue

Fail immediately if any appear:

- `Free shipping`
- `Shop new arrivals`
- `Weekender Tote`
- `New season arrivals`
- `Everyday essentials`
- `WHY CUSTOMERS COME BACK`
- `Newsletter`
- `Subscribe`
- `images.unsplash.com`
- `coming soon`
- `Lorem ipsum`

## Aesthetic Audit

For pages:

- First viewport must signal product/category, not a generic list.
- Use actual product screenshots or meaningful generated visuals.
- Avoid nested cards, generic stock photos, overused gradients, and text walls.
- Headings must fit their containers.
- Buttons should map to real actions.
- Repeated modules must not look like unedited templates.

## Content Audit

Check:

- one primary audience
- one primary search intent
- clear opening answer
- specific examples
- product relevance
- no unsupported claims
- good paragraph rhythm
- complete metadata
- internal links
- glossary consistency

## Adversarial Review

The reviewer (isolated subagent, see Reviewer Isolation Protocol) MUST surface at least 5 objections drawn from this pool:

- skeptical-buyer doubt (what claim would a real buyer push back on?)
- stronger competitor angle (which competitor URL beats this page on the same query, and why?)
- unproven claim (which assertion has no source, number, or example?)
- AI-filler section (which paragraph could be cut with no loss of meaning?)
- weak image (which visual fails to teach, persuade, or fit the region?)
- deletion candidate (what would the page lose nothing from removing?)
- mobile risk (what breaks at 390px or in slow networks?)
- GEO / region miss (what local norm, currency, compliance, or phrasing is wrong?)
- credibility artifact (the page leans on a screenshot / chart / video as trust signal — is the artifact reverse-image-searchable as stock, missing identifiable watermark, or number-free? quote the filename)

For each objection the author records: `accepted` (with diff link) | `rejected` (with reasoning) | `deferred` (with issue id). An audit with < 5 objections, or any unanswered objection, is invalid.

## Evidence

Each final audit writes `audits/<slug>-<date>.md` with:

```yaml
slug:
date:
target_path:
target_url:
reviewer_subagent_id:    # the spawned subagent's id, for traceability
search_intent_brief:     # paste of the brief given to reviewer
competitor_urls: []      # the 3 URLs given to reviewer
score:
  search_intent:
  source_grounding:
  usefulness:
  seo_geo:
  visual_media:
  allincms_backend:
  anti_ai_trust:
  mobile_rendering:
  total:
per_area_min_70pct: true|false
blocking_residue_hits: []
objections:
  - lens: skeptical_buyer | competitor | claim | ai_filler | image | deletion | mobile | geo
    text:
    response: accepted | rejected | deferred
    diff_link_or_reason:
pass: true|false
residual_risks: []
screenshots: []
source_draft_path:
```

A page is publishable iff `pass: true`. The `publish` step refuses to flip AllinCMS status without this file.

**`pass:` must be a top-level YAML key with literal `true` or `false`.** Do not write the string `pass: true` anywhere else in the audit file (objection responses, quoted reviewer notes, etc. must avoid that exact substring at line start). The publish gate (`audit_content.py --require-audit-file <slug>`) parses lines with regex `^pass:\s*true\s*(#.*)?$` to avoid false positives.
