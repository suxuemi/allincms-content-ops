# Monitoring System

How competitor pages get from "spotted in a sitemap" to "an audited topic in our backlog". Designed adversarially with Codex (Q1 review, 2026-06-26).

## Layered architecture

```
raw/competitors/<comp>/<YYYY-MM-DD>/<slug>.md         # immutable original (never edited)
raw/competitors/<comp>/<YYYY-MM-DD>/<slug>.meta.json  # fetch metadata (status, headers, hash)

monitoring/
  competitors.yml                                     # configured competitors
  sites/
    <comp>/
      index.md                                        # full per-competitor capture index
      captures/
        <YYYY-MM-DD>__<slug>.md                       # one capture: frontmatter + AI distill + audit-status suggestions
  daily/
    <YYYY-MM-DD>.md                                   # cross-site daily new-additions index
  runs/sitemap/
    diff-<date>.md                                    # sitemap_diff run output
  index.md                                            # top-level rolling pointer
```

## Trust boundary (iron rule)

| Folder | Trust | Mutability | Who writes |
|---|---|---|---|
| `raw/competitors/**` | source-of-truth | append-only | `capture_url.py` (one-shot) |
| `monitoring/sites/<comp>/captures/*` | `ai-generated` by default | append-only per `(url, content_hash)` | `capture_url.py` + `review_capture.py` |
| `monitoring/sites/<comp>/index.md` | aggregate | SENTINEL-anchored rewrite | scripts via `_lib.shared_writer_lock` |
| `monitoring/daily/<date>.md` | aggregate | SENTINEL-anchored rewrite | scripts via lock |

**AI cannot edit `## borrow_angles`** (human-curated). It writes only inside `<!-- ai:* -->` tagged blocks; reviewer accepting a suggestion strips the tag and upgrades `trust:`.

## Capture file shape

`monitoring/sites/<comp>/captures/<date>__<slug>.md`:

```yaml
---
schema_version: 1
url: https://competitor.com/blog/x
canonical_url: https://competitor.com/blog/x
title: <one line>
competitor: <comp slug from competitors.yml>
type: article          # article | product | landing | asset
language: en
captured_at: 2026-06-26T08:14:03+08:00
first_seen_at: 2026-06-26
last_seen_at: 2026-06-26
source_sitemap: https://competitor.com/sitemap.xml
source_run: runs/sitemap/diff-2026-06-26.md
content_hash: sha256:<hex>
raw_path: raw/competitors/<comp>/2026-06-26/<slug>.md
trust: ai-generated   # ai-generated | human-verified | mixed
review_status: pending  # pending | accepted | rejected | needs_edit
reviewer: ""
reviewed_at: ""
tags: []
---

## extract
<!-- ai:extract -->
3–8 sentence objective summary (no opinion). AI-generated.
<!-- /ai:extract -->

## key_points
<!-- ai:key_points -->
- factual bullet 1 (with a number or quote)
- factual bullet 2
<!-- /ai:key_points -->

## borrow_angles
<!-- human:borrow_angles -->
- (left blank for human to fill — AI may NOT write here)
<!-- /human:borrow_angles -->

## ai_suggestions
<!-- ai-suggestions-start -->
- id: s1
  status: pending      # pending | accepted | rejected | needs_edit
  kind: content_idea   # content_idea | product_hint | asset_reuse | anti_pattern
  text: <suggestion text>
  rationale: <why>
  reviewer: ""
  reviewed_at: ""
<!-- ai-suggestions-end -->
```

## Dedup keys

- `(url, content_hash)` — same URL, new hash → new capture file, `first_seen_at` copied from prior capture, `last_seen_at` = today.
- Same URL, same hash → only `last_seen_at` bumped on the existing capture; no new file.
- The cross-site daily index dedupes by `(competitor, url)` before writing.

## Index updates

Both indexes use SENTINEL anchors (same model as `wiki/lessons.md`, `wiki/backlog.md`):

```
<!-- captures-start -->
| ... table rows ... |
<!-- captures-end -->
```

Writers must **read-modify-write** the SENTINEL block (not append) so the `(url)` dedup works on the merged set. `_lib.shared_writer_lock` guards against concurrent monitor runs.

## Scripts

| Script | Verb | Atomicity |
|---|---|---|
| `capture_url.py <url> --competitor <c> --type <t>` | fetch + write raw + create capture + update both indexes | one URL, one transaction |
| `monitor_run.py .` | sitemap_diff → for each new URL: capture_url | rate-limited, locked |
| `review_capture.py <capture.md> --suggestion <id> --accept\|--reject\|--needs-edit` | flip suggestion status; if all accepted/rejected, capture `review_status` graduates | per-capture lock |
| `review_capture.py --inbox` | list all `review_status: pending` as markdown checklist | read-only |

`--no-ai` mode (default for v0): capture is created with the four section headers but bodies empty. Human fills `borrow_angles`; AI distill comes later.

## AI suggestion lifecycle

```
capture written              → all suggestions status=pending
review_capture --accept      → status=accepted; on full-accept capture trust upgrades to mixed
review_capture --reject      → status=rejected; suggestion text mirrored to wiki/anti-patterns.md
review_capture --needs-edit  → status=needs_edit; original text preserved in `original_text:`
```

`note.py --kind anti_pattern` reaches the same anti-patterns file (single source).

## Anti-patterns (encoded as guard rails)

1. **AI sneaks into `## borrow_angles`** — `capture_url.py` asserts that section contains no `<!-- ai:* -->` tag before writing; abort otherwise.
2. **Same URL re-captured on minor edits** — must compute `content_hash` after stripping date strings / timestamps / view counters; without that scrub, every weekly footer update triggers a "new" capture.
3. **Concurrent monitor_run flood** — SENTINEL block is rewritten under `shared_writer_lock(project_root, "monitoring_site:<comp>")` + `shared_writer_lock(project_root, "monitoring_daily")`. Never `with open(..., "a")` for index files.
