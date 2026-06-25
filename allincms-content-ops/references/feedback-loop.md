# Feedback Loop

How the skill keeps improving from user conversations. Without this, agents forget good suggestions the moment the session ends.

## Two channels, one routing rule

- **`wiki/lessons.md`** — durable rules that should merge into the skill (graduation: `proposed → approved → merged`).
- **`wiki/backlog.md`** — TODOs, ideas, questions, external reads (no graduation; periodic prune).

Routing rule: "If a future agent in any project needs this, it's a lesson. If only this project needs it, or it's not yet a rule, it's backlog." See `routing-matrix.md`.

## Capture protocol (mandatory at end of every full-mode run)

The agent MUST ask the user this exact question — pick by `PROJECT_INDEX.md` → `Default content language` (fallback order: `zh-*` → 中文, else → English):

- `zh-*`: 本轮有想要保留的纠正、想试的新方向、或想加进 TODO 的事吗？
- else: Any corrections worth keeping, new directions to try, or TODOs to add from this run?

Then, regardless of answer:

1. Scan the session for user statements matching these patterns:
   - **Corrections** ("no", "don't", "stop doing X", "instead do Y", "actually …")
   - **Validated approaches** ("yes exactly", "perfect, keep doing that", "this is right")
   - **Suggestions** ("you could …", "try X", "what about Y", "next time")
   - **Out-of-scope ideas** ("someday we should", "later", "noted for later")
   - **Questions left open** ("not sure if", "we should verify")
2. For each, classify per the routing rule.
3. Append entries — never edit SKILL.md or `references/*` directly.

## Entry templates

Use `scripts/note.py --kind <rule|correction|idea|todo|question|external>` to write entries — do not hand-edit the YAML; the script enforces the schema below and is sentinel-anchored so concurrent writes don't corrupt the file.

### lessons.md — for corrections / validated approaches

```yaml
- date: <YYYY-MM-DD>
  trigger: user_correction | new_scenario | failed_audit | competitor_pattern
  rule: <one imperative sentence>
  why: <the user's reason — quote them if possible>
  scope: skill | project
  proposed_destination: <file:section that should absorb this>
  status: proposed
```

### backlog.md — for ideas / TODOs / questions

```yaml
- date: <YYYY-MM-DD>
  trigger: idea | todo | question | external_read
  note: <one sentence>
  context: <why noted; quote user; link if external>
  priority: low | med | high
  status: open
```

## Light-mode exception

Light-mode runs do NOT capture lessons or backlog (avoids ceremony noise on typo fixes). If the user explicitly asks "remember this" during a light run, escalate to full-mode for the capture step only.

## Anti-patterns

- **Silent absorption** — applying a user correction this session without recording it. The next session forgets.
- **Bulk dumping** — pasting the entire chat into lessons.md. Each entry must be one rule with `why`.
- **Editing SKILL.md / references/* in response to a user remark** — bypass the proposed/approved flow. The user might say "always X" in the moment but reconsider tomorrow; the flow exists to give them that pause.
- **Asking the capture question, then ignoring the answer** — if the user gives feedback, an entry MUST land in lessons or backlog.

## Detection

`audit_content.py --status` reports `proposed` and `approved (awaiting merge)` counts. If a session ended without capture, the count stays static — easy to spot. Periodic check:

```bash
python3 allincms-content-ops/scripts/audit_content.py --status .
```

If `proposed` grows but `approved` and `merged` don't, the loop is one-sided — user isn't reviewing. Surface that.
