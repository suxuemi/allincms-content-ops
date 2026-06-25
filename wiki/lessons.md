# Lessons

Run-time corrections, new scenarios, failed-audit patterns, and competitor angles surfaced during real work. Single channel for routing knowledge back into the skill — never edit SKILL.md or `allincms-content-ops/references/*` directly to record a lesson; propose it here, get user approval, then a future agent merges to destination.

See `allincms-content-ops/references/llm-knowledge-base.md` → **Lessons File Contract** for the entry shape and graduation flow.

## Status legend

- `proposed`: surfaced this run, awaiting user review
- `approved`: user agreed (added `approved_by` + `approved_at`); awaiting merge by next agent
- `merged`: applied into destination file (link the commit / diff via `merge_note`)
- `rejected`: declined; one-line reason preserved as anti-pattern memory

## How approval works (so future-you doesn't stall)

- User approval = adding `approved_by: <name>` and `approved_at: <date>` to the entry, OR a one-line confirmation referencing the entry's date + first 40 chars of the rule.
- Once approved, the **next agent run** (any mode) executes Workflow step 0 (lessons sweep) and merges. No further human action needed after approval.
- If an `approved` entry sits > 14 days, `python3 allincms-content-ops/scripts/audit_content.py --check-lessons-drain .` flags it — manually drain at that point.

## Entries

```yaml
- date: 2026-06-26
  trigger: new_scenario
  rule: adversarial reviewer must run in a fresh subagent with no draft access
  why: self-audit reliably scored 9+ even on pages with unsourced claims
  scope: skill
  proposed_destination: allincms-content-ops/references/audits.md#reviewer-isolation-protocol
  status: merged
  merge_note: encoded into skill v0 during bootstrap

- date: 2026-06-26
  trigger: competitor_pattern
  rule: add an RSS-based finder to monitor_competitors workflow (some competitors don't ship sitemap.xml updates promptly but ship RSS within minutes)
  why: sitemap diff has latency; RSS gives near-real-time new-post signal
  scope: skill
  proposed_destination: allincms-content-ops/scripts/ — new feed_diff.py beside sitemap_diff.py
  status: proposed

- date: 2026-06-26
  trigger: competitor_pattern
  rule: add a Google "site:competitor.com after:30d" finder using a web-search-capable subagent
  why: catches pages competitors publish without sitemap or RSS exposure (paywalled, geo-gated, slow-indexed); also surfaces what Google considers fresh+relevant
  scope: skill
  proposed_destination: allincms-content-ops/scripts/ — new google_site_finder.py + capability check (needs web search)
  status: proposed

- date: 2026-06-26
  trigger: competitor_pattern
  rule: add a keyword-watcher finder (X / 小红书 / LinkedIn / Reddit) for emerging persona language
  why: SERP lags; community language predicts query drift. Out of scope for v1 (needs per-platform API or scraping).
  scope: skill
  proposed_destination: allincms-content-ops/scripts/ — new social_keyword_finder.py
  status: proposed

- date: 2026-06-26
  trigger: new_scenario
  rule: add a "finder subagent" SOP step that uses web search + scraping to actively propose new raw materials beyond the configured competitor list
  why: current monitoring is reactive (only watches what we tell it); a finder can suggest new competitors / topics the team hasn't noticed
  scope: skill
  proposed_destination: allincms-content-ops/SKILL.md → Workflow as optional step 1.5
  status: proposed

- date: 2026-06-26
  trigger: new_scenario
  rule: extend audit_content.py to flag overuse of the same title/hook/CTA snippet from wiki/copy-library.md
  why: copy library exists (content-system-tables.md) but no audit gate prevents lazy reuse across drafts
  scope: skill
  proposed_destination: allincms-content-ops/scripts/audit_content.py
  status: proposed

- date: 2026-06-26
  trigger: new_scenario
  rule: add a "credibility evidence" requirement — every full-mode draft must declare at least 1 of {data table, customer screenshot, product video, real-world comparison} with a path
  why: borrowed from observed top-performing Chinese SEO playbook (人工增加可信度); current audit only catches AI smell, doesn't enforce evidence presence
  scope: skill
  proposed_destination: |
    DECIDE before merging — do not implement both:
    - Option A: add a binary Hard Gate "credibility_evidence frontmatter missing/empty" in audits.md; do not change the 8-area scorecard.
    - Option B: extend `Source grounding` (1.2) to 1.5 and split into "source trace" (0.7) + "credibility artifact" (0.8); no new Hard Gate.
    Adding both double-counts and confuses reviewers about which dimension to deduct from.
  status: proposed_blocked_on_decision

- date: 2026-06-26
  trigger: new_scenario
  rule: credibility evidence — implement Option C (hybrid)
  why: "A only verifies path exists (author can drop a stock image); B only weights, lets authors trade 0.3 pts for skipping work; C combines binary gate + Source grounding sub-question + new reviewer lens, keeps 8-area scorecard intact"
  scope: skill
  proposed_destination: |
    Implemented via hybrid (Option C) in this same session:
    - audit_content.py: REQUIRED_FRONTMATTER += credibility_evidence; path existence check; meta length checks
    - SKILL.md Hard Gates: empty credibility_evidence OR missing artifact = block
    - audits.md Source grounding row + adversarial lens pool += credibility_artifact
    - codex-adversarial-reviewer.md lens table + score rule (high-severity credibility_artifact → Source grounding < 70%)
  status: merged
  merge_note: applied 2026-06-26 by hybrid Option C decision (codex subagent recommended C over A/B)

<!-- entries-end -->
```
