---
name: allincms-content-ops
description: Operate AllinCMS content systems end to end. Use when creating or updating AllinCMS websites, SEO/GEO articles, product pages, categories, tags, cover images, PicGo image uploads, competitor monitoring, raw/wiki/web knowledge bases, media-to-Markdown extraction, publishing workflows, or quality audits for AI smell, visual polish, search intent, and AllinCMS backend fit.
---

# AllinCMS Content Ops

## Mode Selection (read first)

Classify the request before reading anything else.

- **light-mode**: typo fix, alt-text touch-up, residue-word swap on ONE file, broken-link replace, index entry append, image re-upload to existing slug, OR a single-field patch on these LOW-RISK frontmatter fields ONLY: `meta_title`, `meta_description`, `summary`, `cover_alt`.

  Forbidden in light-mode (auto-escalate to full): `status`, `category`, `tags`, `route`, `slug`, `region`, `search_intent`, `persona`, `differentiation`, `cover_image`, `source_wiki`, `source_raw`, `credibility_evidence`, `published_at`, `author`, any body change > 50 words, any frontmatter field add / remove.

  Action: read ONLY the target file + `wiki/glossary.md`. Skip PROJECT_INDEX / wiki / web / raw / competitors index reads. Skip adversarial review subagent. Run `scripts/audit_content.py --light <single-file>`; if pass, commit and stop. Do NOT update `wiki/lessons.md`, do NOT propose next topics, do NOT touch unrelated indexes.

- **full-mode**: anything that creates, publishes, repositions, restructures, or affects taxonomy / regions / claims / cover images / search intent, or touches any forbidden field above.

  Action: full Required Context + full Workflow + Hard Gates below.

If unsure, default to light-mode and ask one question. Never escalate light → full without user confirmation.

### Capability prerequisites (check before any mode)

The SOP assumes the running agent has these capabilities. Self-check and STOP if any required-for-this-task capability is missing:

| Capability | Needed for | Fallback if absent |
|---|---|---|
| File read/write | every mode | refuse — non-negotiable |
| Shell exec (`python3`) | running scripts | output the commands as a manual checklist for the user to run |
| Browser automation (Chrome MCP, Codex preview, Playwright, or a logged-in human) | SOP steps 6–8 (AllinCMS fill, preview-URL capture) | downgrade to "draft markdown handoff": produce the draft + reviewer-input.yaml + manual fill checklist; STOP before publish |
| Web fetch (URL → HTML) | SOP step 1 URL ingest; SOP step 7 reviewer fetching preview/competitor URLs | step 1: pre-download URLs to local files; step 7: use `preview_html_path:` instead of `preview_url:`, pre-download competitor pages to `raw/competitors/` |
| Subagent spawn | SOP step 7 adversarial reviewer isolation | refuse step 7 — without isolation the audit is invalid. Either move to a host that supports subagents or have a second human reviewer follow `references/codex-adversarial-reviewer.md` in a separate session. |
| Web search | optional finder discovery (sitemap diff, Google `site:`, RSS) | skip auto-finders; rely on `monitoring/competitors.yml` manual list |

See `references/tooling-matrix.md` for verified host environments.

### Light-mode runbook (zero questions when request names a slug or filename)

```bash
# 1. resolve target by slug; alternatives: pass an explicit path
target=$(find web -name "<slug>*.md" -not -path "*/index.md" | head -1)

# 2. read only target + glossary
#    (open $target and wiki/glossary.md)

# 3. apply the patch (your edit tool of choice)

# 4. audit — must exit 0
python3 allincms-content-ops/scripts/audit_content.py --light "$target"

# 5. commit
#    message: "light: <one-line what changed> (<slug>)"
```

Stop after step 5. No `wiki/lessons.md` write, no index updates, no next-topic suggestions, no reviewer spawn.

## Operating Rule

Treat this as a content operation system, not a one-shot writing prompt. Build from existing material first, compile knowledge into `raw/`, `wiki/`, and `web/`, then publish only after adversarial review proves the content is useful, non-generic, visually acceptable, and mapped to search intent.

The knowledge base follows a Karpathy-style living-wiki model: `raw/` is append-only evidence, `wiki/` is distilled memory that can be rewritten, `web/` is publishable output. Run-time corrections and lessons are routed through `wiki/lessons.md` (proposed → approved → merged), never by silently editing SKILL.md or `references/*`.

## Required Context

Before writing or publishing, locate or create the project root and read:

- `PROJECT_INDEX.md` for entry paths and current indexes.
- `wiki/index.md` for compiled knowledge.
- `wiki/lessons.md` for run-time corrections that future agents must respect.
- `web/index.md` for published or publish-ready website content.
- `raw/index.md` and `raw/competitors/index.md` for original source material and monitoring.
- `wiki/glossary.md` for terminology.

If these files do not exist, run `scripts/init_content_ops_project.py <project-root>` with the required flags (see `--help`).

**Site identity is required for actions that write to AllinCMS, publish, capture monitoring, run live site health, or otherwise touch shared/remote state.** If `PROJECT_INDEX.md` → `Current Site` has any empty field, **first run the opportunistic discovery sub-protocol** (`references/current-site-discovery.md`) — it opens the workspace, guides the user through login if needed, lists their sites, and auto-fills `site_id` / `front_end_domain` / `workspace_url` / `browser_profile` (most are constants or auto-detectable). Only fall back to asking the user explicitly when: (a) discovery fails twice in a session, (b) env has no browser automation, or (c) `deployment: self-hosted` is set in `PROJECT_INDEX.md`. Discovery resumes from the first unfilled field — never re-opens login if PROJECT_INDEX already has `site_id`.

**Not gated on Current Site** (allowed with empty fields): local light-mode edits, `audit_content.py --light`, reading wiki/references/raw, `--status` dashboard, `first-contact.md` Phases 1–4 introduction.

The init script (`scripts/init_content_ops_project.py --help`) requires all five as flags so a clean init never writes placeholders.

For cross-agent use, keep the root entry files thin:

- Codex and other agent runners: `AGENTS.md`
- Claude and Claude Code: `CLAUDE.md`
- WorkBuddy or generic assistants: `WORKBUDDY.md`

All three must point back to this skill and the same `PROJECT_INDEX.md`. Do not fork rules across tools.

## Workflow

0. Sweep lessons (both modes, very first action).
   - If `first-contact.md` Phase -1 just pulled new contract files this turn (the `update_skill.py` output included a `CHANGED-CONTRACT-FILES:` section), **re-read** those files before sweeping. The sweep rules themselves may have changed.
   - `grep -nE "^\s*status:\s*approved" wiki/lessons.md` (or open and read).
   - For each `approved` entry: apply the rule into its `proposed_destination`, change status to `merged`, append `merge_note` with the commit hash or diff path.
   - **Lessons → CHANGELOG bridge**: if the merge edited `SKILL.md`, any `references/*`, or any `scripts/*`, add a single line under `## [Unreleased]` in `/CHANGELOG.md` — `- merged lesson \`<date> / <first 40 chars of rule>\` (sha: <commit>)` — and recommend the next release's bump type per the decision tree in `/CONTRIBUTING.md`. Without this bridge, SKILL.md drifts forward but releases never know what shipped.
   - If the destination edit is non-trivial, surface to user before merging; do not silently drop the entry.
   - Verify drain health: `python3 scripts/audit_content.py --check-lessons-drain <project-root>` (flags `approved` entries older than 14 days).

1. Ingest sources into `raw/`.
   - Put PDFs, PPTs, MP4 notes, site exports, screenshots, competitor pages, call notes, and product docs under dated folders.
   - Convert extractable content to Markdown and keep the original path in frontmatter.
   - Never overwrite raw sources; append new material and update `raw/index.md`.
   - Use `scripts/ingest_sources.py <project-root> <files-or-urls...>` for repeatable ingestion.

2. Compile knowledge into `wiki/`.
   - Convert raw material into stable pages for company, products, personas, use cases, methods, SEO/SEM, competitors, objections, region rules, and terminology.
   - Prefer durable facts over transient claims.
   - Mark uncertain facts as `needs_verification`.
   - Use the LLM knowledge-base model in `references/llm-knowledge-base.md`: raw is evidence, wiki is distilled memory, web is publishable output.

3. Plan search intent before writing.
   - Identify target customer, job-to-be-done, funnel stage, query variants, region/language norms, objections, and desired conversion.
   - Read `references/search-intent.md` and use its brief template.

4. Produce website content in `web/`.
   - Scaffold with `python3 scripts/new_draft.py <slug> --persona <p> --region <r> --content-type article` — never hand-author the 20-field frontmatter block; the script fills sensible defaults so audit doesn't kick the draft back.
   - For each page/article, ensure the draft satisfies `references/markdown-style-guide.md`: title, slug, route, category, tags, meta title (35–65), meta description (120–165), `differentiation`, `credibility_evidence`, `published_at` / `updated_at` / `author`, outline, body, images, internal links, AllinCMS backend notes.
   - Combine existing wiki facts with monitored competitor gaps; do not summarize competitors without adding product-specific value.

5. Process images.
   - Select images from source content first. If unsuitable, crop/annotate/generate supporting visuals.
   - Follow regional visual norms and image SEO: descriptive filename, contextual caption, alt text, nearby relevant text.
   - Upload through PicGo when requested; see `references/media-picgo.md` and `scripts/picgo_batch_upload.py`.

6. Fill AllinCMS (DRAFT only).
   - Use the logged-in browser session for `workspace.laicms.com`.
   - Fill title, slug, summary, body, category, tags, cover, SEO fields, route, and related modules.
   - Save with `status=draft`. Do NOT switch to published in this step.
   - Clear old category/tag/cover/template residue before saving.
   - For theme pages, inspect iframe/front-end output after each block change. AllinCMS Copilot can insert retail defaults; do not publish until residue is gone.
   - **Generate a reviewer-accessible artifact** (see `references/allincms-backend.md` → "Generating a reviewer-accessible preview URL"): either a preview URL the isolated subagent can fetch without login, or a saved `audits/<slug>-<date>-preview.html` rendered from the draft. The reviewer in step 7 will refuse the run if this artifact is missing.

7. Audit before publishing.
   - Run `scripts/audit_content.py <project-root>` on local drafts.
   - **Package reviewer input first**: `python3 scripts/spawn_reviewer.py <slug>` writes `audits/<slug>-<date>-reviewer-input.yaml` containing only the search-intent brief, the preview URL or HTML path from step 6, and 3 competitor URLs. The reviewer subagent's prompt may reference only this YAML path — no other content.
   - **Adversarial review must run in a fresh subagent** (Claude: `Agent` tool with `subagent_type=general-purpose`; Codex: a new session) using the brief in `references/codex-adversarial-reviewer.md`. The reviewer MUST NOT see the draft markdown, the wiki sources, or the author's self-assessment.
   - Score with `references/audits.md`; pass requires: total ≥ 8.5/10 **AND** every individual area ≥ 70% of its max **AND** zero blocking-residue hits **AND** at least 5 reviewer objections each with author response (accepted / rejected / deferred).
   - Write the audit record to `audits/<slug>-<date>.md` with `pass:` as a top-level YAML key (literal `true` or `false`); never write the string `pass: true` anywhere else in the file. Publish step greps for this exact key line.

8. Publish and index.
   - Gate: `python3 scripts/audit_content.py --require-audit-file <slug> <project-root>` must exit 0 (parses top-level `pass: true` line).
   - Publish: flip AllinCMS `status` to published.
   - Update `web/published/index.md` (hand-edit for now; `scripts/publish_index_append.py` is on the backlog — verify with `grep -F <slug> web/published/index.md`), `web/index.md`, and any category/tag indexes.
   - Add monitor-derived topics to `raw/competitors/index.md` and `wiki/content-opportunities.md`.
   - Recommend next divergent topics each round, but ask user confirmation before writing and publishing new monitored topics.
   - Use `scripts/monitor_competitors.py <project-root>` to capture configured competitor pages and proposed topics.

9. Reflect, ask, route (full-mode only; light-mode skips entirely).

   **Capture contract** (MUST satisfy all four before declaring complete):

   - **Ask** the user verbatim — pick by `PROJECT_INDEX.md` → `Default content language`:
     - `zh-*`: `本轮有想要保留的纠正、想试的新方向、或想加进 TODO 的事吗？`
     - else: `Any corrections worth keeping, new directions to try, or TODOs to add from this run?`
   - **Scan** the session against the pattern list in `references/feedback-loop.md` § Capture protocol (corrections / validated approaches / suggestions / out-of-scope ideas / open questions). Run regardless of the user's answer — "没有 / no" does NOT skip the scan. Auto-captured entries land with `priority: low` and `context` noting `auto-captured despite user said none` so the user can prune at a glance.
   - **Route** via `scripts/note.py` (one call per entry, never hand-edit lessons.md / backlog.md):
     - corrections, validated approaches → `--kind rule` (→ `wiki/lessons.md`, `status: proposed`)
     - ideas, TODOs, questions, external reads → `--kind idea|todo|question|external` (→ `wiki/backlog.md`, `status: open`)
   - **Never** edit `SKILL.md` or `references/*` in response to a user remark — the next agent's step 0 merges approved entries.

   Self-check: if this step ran but produced zero entries AND the session contained ≥ 1 user correction, that's a Hard Gate violation ("silent absorption"). Re-run the scan before sign-off.

## Resource Map

- `references/sop.md`: end-to-end SOP and stop points.
- `references/corpus-layout.md`: `raw/wiki/web` information architecture and index rules.
- `references/seo-geo.md`: SEO, GEO, structured data, image, mobile, and people-first rules.
- `references/search-intent.md`: customer and query intent analysis workflow.
- `references/allincms-backend.md`: AllinCMS browser, article, media, and theme-page operations.
- `references/media-picgo.md`: extraction, image repair, regional visual rules, and PicGo upload.
- `references/competitor-monitoring.md`: monitoring, topic extraction, and approval workflow.
- `references/audits.md`: aesthetic, content, SEO/GEO, anti-AI, and publish gates.
- `references/glossary.md`: terms every agent should use consistently.
- `references/llm-knowledge-base.md`: Karpathy-style living knowledge-base model and retrieval rules.
- `references/requirements-map.md`: coverage map for the 18 user requirements that shaped this skill.
- `references/codex-adversarial-reviewer.md`: isolated reviewer brief — drop into a fresh Codex/Claude subagent for step 7 audit.
- `references/tooling-matrix.md`: which host environments are verified, what capabilities each SOP step requires, and downgrade paths.
- `references/agent-onboarding.md`: how to mount this skill from Cursor / Cline / Aider / Continue / Trae / Windsurf etc. without duplicating rules.
- `references/routing-matrix.md`: where each kind of new info lands (raw / wiki / lessons / backlog / audits / logs / opportunities).
- `references/markdown-style-guide.md`: required frontmatter, length ranges, link / heading / image / CTA / SEO conventions for every web draft.
- `references/feedback-loop.md`: end-of-run capture protocol — mandatory user prompt + routing to `lessons.md` vs `backlog.md`.
- `scripts/_lib.py`: shared `JsonlLogger` and `file_lock` helpers; imported by scripts that write shared files or emit structured logs.
- `scripts/init_content_ops_project.py`: create a portable project skeleton and indexes.
- `scripts/ingest_sources.py`: copy files or fetch URLs into `raw/`, extract Markdown when possible, and update `raw/index.md`.
- `scripts/monitor_competitors.py`: fetch configured competitor pages, detect changes, write raw captures, and update monitor indexes.
- `scripts/audit_content.py`: scan local Markdown/text drafts for metadata, residue, AI smell, length, and indexing issues.
- `scripts/picgo_batch_upload.py`: upload local images through a PicGo server and write a manifest.
- `scripts/spawn_reviewer.py`: assemble `audits/<slug>-<date>-reviewer-input.yaml` (search-intent + preview + 3 competitors + credibility evidence list) so the adversarial reviewer subagent has exactly one allowed input.
- `scripts/new_draft.py`: scaffold a web draft with all 20 required frontmatter fields pre-filled (auto-detects git author, today's date, content-type folder); reads `Default content language` from PROJECT_INDEX to pick zh / en body template.
- `scripts/sitemap_discover.py`: probe a list of competitor domains for sitemap candidates (robots.txt + `/sitemap.xml` + `/sitemap_index.xml`); emit `competitors.yml`-shaped YAML rows for the operator to review and paste. Never auto-writes.
- `scripts/note.py`: one-line capture — routes by `--kind` into `wiki/backlog.md` (idea/todo/question/external) or `wiki/lessons.md` (rule/correction). Lowest-friction way to drop a thought during a real session.
- `scripts/site_health_check.py`: health-check OUR live site by walking its sitemap — HTTP / response size / meta title-description length / residue scan / hreflang reciprocity / canonical presence; report → `audits/site-health-<date>.md`, high-severity findings append to `backlog.md` as `proposed`.
- `scripts/library_health.py`: periodic internal-library check — dead internal links, orphan raw captures, stale wiki pages, copy-library snippet reuse, glossary terms used-but-not-defined; complements `site_health_check.py` (live site) and `audit_content.py` (per-draft).
- `scripts/capture_url.py`: capture a single competitor URL — fetch + write immutable `raw/competitors/<comp>/<date>/<slug>.md` + write `monitoring/sites/<comp>/captures/<date>__<slug>.md` with frontmatter + 4 body sections + update per-site and per-day indexes (SENTINEL-anchored, dedup on `(url, content_hash)`).
- `scripts/monitor_run.py`: orchestrate a monitoring round — for each competitor in `competitors.yml`, run sitemap_diff and invoke `capture_url.py` on each new URL (up to `--limit`).
- `scripts/review_capture.py`: review AI suggestions in a capture — per-suggestion `--accept | --reject | --needs-edit`, or `--inbox` for a markdown checklist of all pending across captures. Rejected suggestions mirror to `wiki/anti-patterns.md`.
- `references/monitoring-system.md`: full schema and lifecycle for the monitoring layer (capture frontmatter, trust boundary, dedup keys, AI section markers, anti-patterns).
- `references/feedback-loop.md`: capture protocol the agent MUST run at end of every full-mode session (Workflow step 9).
- `references/first-contact.md`: introduction + guidance protocol the agent runs on first contact (when invoked via the README "Use with AI" prompt). Read-only; exempt from the `Current Site` STOP gate. Includes `Phase -1: Skill sync` for freshness check.
- `scripts/update_skill.py`: pull latest skill from upstream while preserving project content (canonical or surgical mode auto-detected); emits `CHANGED-CONTRACT-FILES:` so the agent knows to re-read; semver-aware (refuses MAJOR cross without `--ack-major`; honours `.allincms-skill-pin`); shallow-clone unshallow fallback.
- `scripts/bump_version.py`: sync `agents/openai.yaml` version from `/VERSION` (the single source of truth).
- `scripts/check_version_sync.py`: CI-friendly verifier that `VERSION` ↔ `agents/openai.yaml` are in sync.
- `/VERSION` (repo root): single-line semver; the only place that defines what version this skill is. See `/CONTRIBUTING.md` for bump decision tree.
- `/CHANGELOG.md` (repo root): release notes per version; entries are added when SKILL.md / references/* / scripts/* change (via step 0 lessons→changelog bridge or release bumps).
- `/CONTRIBUTING.md` (repo root): Update Checklist + semver decision tree + bump procedure + pinning policy + lessons→changelog bridge + checklist self-versioning.
- `references/codex-design-reviewer.md`: codex brief for **design-time** review (separate from content-time `codex-adversarial-reviewer.md`). Required for Substantive / Breaking changes per the Update Checklist.
- `scripts/audit_skill_meta.py`: persistent regression check (one switch per high-severity codex finding); replaces throwaway heredoc self-scans. Run in CI after every `audit_content.py` run.
- `audits/codex-rounds/`: per-round codex review outputs. CHANGELOG entries reference findings here by relative path.
- `references/current-site-discovery.md`: opportunistic sub-protocol triggered when a user requests an action needing `Current Site` and some fields are empty — opens workspace, handles login wait+resume, lists sites, auto-fills `site_id` / `front_end_domain`. Replaces the v0.6 "ask 4 values upfront" UX with discovery-driven flow.
- `audits/discovery-fixtures/dashboard-snapshot.md`: regression fixture capturing workspace.laicms.com DOM structure the discovery protocol relies on. Updated in same PR as workspace redesigns.
- `references/ocr-strategy.md`: tool ladder for document → markdown extraction. Default chain `MarkItDown → PaddleOCR fallback`. Documents license caveats (MinerU AGPL not auto-invoked) and the privacy stance (all OCR runs local; no hosted APIs).
- `references/media-pipeline.md`: PicGo vs R2 trade-offs, "one host per project" rule, doctor's `media_mix` warning. Migration is a `v0.9+` script — for now, manual.
- `scripts/r2_setup.py`: interactive Cloudflare R2 wizard. Walks the user through dashboard steps (account / bucket / API token / optional custom domain), writes to `~/.config/allincms-content-ops/r2.toml`, runs a round-trip test upload.
- `scripts/r2_upload.py`: batch-upload images to R2. Same CLI shape as `picgo_batch_upload.py`. Idempotent (SHA-keyed). Appends to `media/index.md`. Masks `access_key_id`; never prints `secret_access_key`.
- `scripts/suggest_internal_links.py`: read a draft's frontmatter, scan `web/published/index.md`, print scored candidates for the author to paste as internal links (≥ 3 / page per markdown-style-guide). Scoring weights at top of file; locked by `tests/test_suggest_links.py`.
- `tests/test_suggest_links.py`: fixture-based ranking test (Ffalsifiability.1 of v0.4.0-r1) — future weight tweaks surface as test diffs.
- `wiki/products/_ai-drafts/` and `wiki/personas/_ai-drafts/` (created on first-contact Phase 2.5): staging area for AI-bootstrapped wiki pages. User promotes by moving out of `_ai-drafts/` and flipping `trust:` to `human-verified`. `library_health.py` and `audit_content.py` skip this subdir.
- `scripts/doctor.py`: one-stop newbie diagnostic. Three-tier output (strong / degraded / missing) matching `tooling-matrix.md` vocabulary. Each non-strong finding links to a `tooling-matrix.md` anchor with remediation. Result cached to `.doctor-cache.json` for first-contact Phase -1.
- `scripts/check_draft.py`: teaching mode for newbies — scans a draft and tells them which fields are missing, what good fills look like, and why each one matters. Never modifies files, never returns non-zero. Publish gates still live in `audit_content.py`.
- `examples/sample-article-zh/` and `examples/sample-article-en/`: fully-filled reference drafts a newbie can read alongside `references/markdown-style-guide.md`. Identity fields use `__REPLACE_ME__` literal; a Hard Gate in `audit_content.py` blocks publishing any draft that still contains this literal (prevents accidental example-identity leakage).
- `scripts/sitemap_diff.py`: fetch each competitor's `sitemap.xml`, diff against the last snapshot, write a dated diff file under `monitoring/runs/sitemap/`, and (optionally) append new URLs as `proposed` opportunities.
- `references/prompt-templates.md`: copy-paste prompts for persona extraction, search-intent brief, outline, competitor distillation, alt text, and lesson proposal.
- `references/content-system-tables.md`: four-table model — knowledge / competitors / opportunities / copy library — with cadence and write-authority rules.

## Hard Gates

These gates apply to full-mode runs and to any run that changes published status, body content >50 words, metadata, taxonomy, or media. Light-mode edits (see Mode Selection) are gated only by: residue terms absent, target file still parses, `audit_content.py --light` exit 0 on the edited file.

Stop and fix before publishing if any of these are true:

- The content cannot be traced to `raw/` or `wiki/`.
- The target customer and search intent are unclear.
- Category, tags, slug, meta title, or meta description are missing.
- `differentiation:` frontmatter is empty (no stated edge over the competitor URL borrowed from).
- `credibility_evidence:` frontmatter is empty OR any listed path does not exist (must list ≥ 1 of: data chart, customer screenshot, product video, real-world comparison table). Reviewer separately rates *quality* via the `credibility_artifact` lens.
- Images have generic filenames, missing alt text, broken URLs, or irrelevant context.
- Total score < 8.5, any individual area < 70% of its max, or any blocking-residue hit.
- Draft contains AI smell, unsupported claims, fake names, fake metrics, placeholder text, or AllinCMS template residue.
- Mobile rendering hides primary content, changes metadata/content materially, or has horizontal overflow.
- Published content is not indexed in `web/published/index.md`.
- Competitor-derived topics have not been confirmed by the user.
- Region, language, currency, compliance, or visual norms are unknown for a region-specific page.
- A file under `raw/**` has been modified after its `collected_at` (raw is append-only — create a new dated capture instead).
- Adversarial review surfaced fewer than 5 objections, or any objection has no recorded author response.
- A wiki page referenced via `source_wiki` does not list this draft in its `consumed_by` (broken backlink).
- `audits/<slug>-<date>.md` does not exist or its pass field is false.

## AllinCMS Residue Terms

Always search drafts, previews, and live pages for:

`Free shipping`, `Shop new arrivals`, `Weekender Tote`, `New season arrivals`, `Everyday essentials`, `WHY CUSTOMERS COME BACK`, `Newsletter`, `Subscribe`, `Lin Mei`, `Ahmed Hassan`, `Carlos Ruiz`, `Li Mei`, `20+ countries`, `images.unsplash.com`, `coming soon`, `Lorem ipsum`, `Shop materials`, `SHIPPING / RETURNS`.
