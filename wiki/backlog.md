# Backlog

Open TODOs, ideas, things to try, external reads, unblocked-but-deprioritized work, questions to verify. See `allincms-content-ops/references/routing-matrix.md` → "What goes in lessons.md vs backlog.md".

Entries do NOT graduate into the skill (that's `lessons.md`'s job). Prune periodically.

## Schema

```yaml
- date: YYYY-MM-DD
  trigger: idea | todo | question | external_read
  note: <one sentence>
  context: <why noted; link if external>
  priority: low | med | high
  status: open | doing | done | dropped
```

## Entries

```yaml
- date: 2026-06-26
  trigger: todo
  note: run first real end-to-end publish to populate tooling-matrix Verified table
  context: tooling-matrix.md verification protocol — no row claims "verified" without an audit link
  priority: high
  status: open

- date: 2026-06-26
  trigger: idea
  note: build a /status one-shot that combines audit summary + lessons pending + backlog high-priority + sitemap diff freshness
  context: avoid having to remember 4 separate commands; user requested a "one place to see everything"
  priority: med
  status: open

- date: 2026-06-26
  trigger: question
  note: do AllinCMS DRAFT posts have a token-based public preview URL? If not, the rendered-HTML fallback in allincms-backend.md is the only viable path for reviewer step.
  context: blocks first real end-to-end run (Q above)
  priority: high
  status: open

- date: 2026-06-26
  trigger: todo
  note: write scripts/publish_index_append.py to auto-append to web/published/index.md
  context: SKILL.md step 8 and routing-matrix.md both say "hand-edit for now"; small script eliminates a known forget-prone step
  priority: med
  status: open

- date: 2026-06-26
  trigger: todo
  note: implement hreflang machine check in audit_content.py (paired slugs with sibling language)
  context: markdown-style-guide.md and corpus-layout.md both reference hreflang but the audit doesn't verify reciprocity
  priority: low
  status: open


<!-- entries-end -->
```
