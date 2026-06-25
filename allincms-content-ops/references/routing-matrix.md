# Routing Matrix

Where does each kind of new information land? Use this table whenever you're about to write something and aren't sure which file to touch.

| Kind of input | Destination | Channel |
|---|---|---|
| New raw source (file, URL, screenshot) | `raw/<YYYY-MM-DD>-<source>/` | `scripts/ingest_sources.py` (append-only) |
| Distilled fact about company / product / persona / region | `wiki/<topic>.md` | hand-edit, cite raw path |
| Glossary term | `wiki/glossary.md` | hand-edit (English canonical + 中文 row) |
| Reusable proven copy snippet | `wiki/copy-library.md` | only after a `pass: true` audit, or distilled competitor with `do_not_overuse: true` |
| Proposed publishable topic | `wiki/content-opportunities.md` | hand-edit OR finder script append (capped per run) |
| New competitor URL to watch | `monitoring/competitors.yml` | hand-edit |
| Competitor sitemap diff | `monitoring/runs/sitemap/diff-<date>.md` + opportunities | `scripts/sitemap_diff.py` |
| Captured competitor article / product / asset | `raw/competitors/<comp>/<date>/<slug>.md` (immutable) + `monitoring/sites/<comp>/captures/<date>__<slug>.md` (AI distill + suggestions) + per-site and per-day index rows | `scripts/capture_url.py` or `scripts/monitor_run.py` |
| AI suggestion review verdict | flips status inside the capture file; rejected mirrors to `wiki/anti-patterns.md` | `scripts/review_capture.py` |
| User correction or new durable rule | `wiki/lessons.md` (`status: proposed`) | hand-append per Lessons File Contract |
| Open TODO / feature idea / "try this later" | `wiki/backlog.md` | `scripts/note.py "msg" --kind idea/todo/question/external` (or hand-append per Backlog Contract) |
| Live-site health issue (auto-detected) | `audits/site-health-<date>.md` + `proposed` `backlog.md` row | `scripts/site_health_check.py` |
| Library internal-health issue (dead link / orphan raw / stale wiki / glossary drift) | `audits/library-health-<date>.md` + `proposed` `backlog.md` row | `scripts/library_health.py` |
| New competitor candidate sitemap | print only; user pastes into `monitoring/competitors.yml` after verification | `scripts/sitemap_discover.py <domain>` |
| Audit result for a specific draft | `audits/<slug>-<date>.md` | reviewer subagent output |
| Script runtime event / error / debug | `logs/<script>-<date>.jsonl` | scripts auto-log when run with `--log` |
| Published article URL + metadata | `web/published/index.md` | publish step appends (manual hand-edit for now; `scripts/publish_index_append.py` is on the backlog) |
| Image source / processed / uploaded | `media/source/`, `media/processed/`, `media/uploaded/` + `media/index.md` | hand-edit + `picgo_batch_upload.py` manifest |
| Reviewer-input bundle (search intent + preview + competitors) | `audits/<slug>-<date>-reviewer-input.yaml` | `scripts/spawn_reviewer.py` |

## What goes in `wiki/lessons.md` vs `wiki/backlog.md`

**lessons.md** — durable rules that should eventually merge into the skill itself. The graduation flow is `proposed → approved (with approved_by/at) → merged (by next agent's Workflow step 0)`. Triggers: `user_correction`, `new_scenario`, `failed_audit`, `competitor_pattern`. Quick-add: `scripts/note.py "rule text" --kind rule --why "incident" --scope skill`.

**backlog.md** — anything else worth not forgetting: feature ideas, "we should try X someday", external links to read, unblocked-but-deprioritized work, questions to verify. Has no graduation flow; you periodically prune. Triggers: `idea`, `todo`, `question`, `external_read`.

**Backlog entry contract** (so `audit_content.py --status` regex is reliable): write each entry as a single `- date:` block with field order **date, trigger, note, context, priority, status**; keep `status:` on its own line; one blank line between entries.

If unsure: ask "should this eventually become a rule in SKILL.md or references/*?" Yes → lessons. No → backlog.

## Anti-pattern routing

Don't write any of these straight into SKILL.md or `references/*`:

- "From now on we always X" → `wiki/lessons.md` as proposed
- "Let's also support Y someday" → `wiki/backlog.md`
- "Audit failed because Z" → `audits/<slug>-<date>.md` first; if Z reveals a missing rule, **then** lessons.md

Direct edits to SKILL.md / references/* are reserved for: (a) the next agent merging an `approved` lesson, or (b) explicit user instruction to change the contract.

## Subfolder index rule

Not every subfolder needs an `index.md`. Add one only when:

- The folder is expected to hold > 5 sibling files (e.g. `wiki/products/` if you have 10+ products).
- The naming is ambiguous and a TOC reduces grep cost (e.g. `web/drafts/` once you have many in-flight).
- An external reader (human or onboarding agent) needs a starting point.

Skip otherwise — `find` / `glob` / IDE tree is enough. A stale half-empty index is worse than no index.
