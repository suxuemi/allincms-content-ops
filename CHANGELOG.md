# Changelog

All notable changes to this skill are tracked here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) with semver semantics defined in [CONTRIBUTING.md](CONTRIBUTING.md): **"breaking" means previously-passing drafts fail on re-audit or existing files need schema migration**, not "any contract character changed".

## [Unreleased]

(none yet)

## [0.2.0] — 2026-06-26

Initial public release after eight rounds of Codex-style adversarial review (50+ findings applied across review, scripts, references, first-contact, monitoring, update mechanism).

### Added

- **Karpathy-style living wiki layering**: `raw/` (append-only evidence) → `wiki/` (distilled, rewritable) → `web/` (one-shot publishable). Wiki carries reverse `consumed_by` links for impact tracing.
- **Reviewer isolation contract** (`references/codex-adversarial-reviewer.md`): adversarial reviewer runs in a fresh subagent, no access to draft markdown / wiki sources / author self-assessment. Reviewer-input is packaged via `spawn_reviewer.py` so the subagent receives ONLY a YAML containing search-intent brief + preview URL/HTML + 3 competitor URLs.
- **Pass Criteria 4-way gate** (`references/audits.md`): total ≥ 8.5/10 AND every individual area ≥ 70% AND zero blocking-residue hits AND ≥ 5 reviewer objections logged with author response (`accepted` / `rejected` / `deferred`).
- **Mode Selection** (`SKILL.md`): light vs full classification on every request; light-mode runbook with explicit forbidden-field list; capability prerequisites table; Light-mode runbook for zero-question execution when request names a slug.
- **Capture protocol** (`SKILL.md` Workflow step 9 + `references/feedback-loop.md`): MUST-ask user prompt at end of every full-mode run, in detected language; auto-scan even if user says "no"; route via `scripts/note.py`.
- **Monitoring layer** (`references/monitoring-system.md` + `scripts/capture_url.py` / `monitor_run.py` / `review_capture.py`): trust boundary (immutable `raw/` vs ai-generated `monitoring/sites/` captures), SENTINEL-anchored per-site + daily indexes, `(url, content_hash)` dedup, AI suggestion review lifecycle (pending → accepted / rejected / needs_edit), reject mirrors to `wiki/anti-patterns.md`.
- **first-contact protocol** (`references/first-contact.md`): context-establishing onboarding before any task (Phase -1 skill sync / Phase 1 context probe / Phase 2 three-path establish / Phase 3 token-bound scenarios / Phase 4 routing). Skip clause for users who arrive with a concrete task. AI-drafted `wiki/company.md` flagged with `trust: ai-drafted` + `needs_human_review: true` and enforced by `library_health.py`.
- **Library + site health** (`scripts/library_health.py` / `scripts/site_health_check.py`): internal-library check (dead links / orphan raw / stale wiki / copy_overuse / glossary drift / seo_stale / ai_drafted_unreviewed) and live-site check (sitemap walk + meta length + residue + hreflang reciprocity + canonical presence).
- **Project lessons + backlog channels** (`wiki/lessons.md` / `wiki/backlog.md` + `scripts/note.py`): single-line capture via `note.py --kind <rule|correction|idea|todo|question|external>`. SENTINEL-anchored writes survive YAML block scalars containing embedded code fences. Sweep + merge done by `SKILL.md` Workflow step 0.
- **In-place skill updates** (`scripts/update_skill.py` + `references/first-contact.md` Phase -1): canonical (clean tree → `git pull --ff-only`) vs surgical (project content modified → upstream-driven path enumeration + auto-commit). Emits `CHANGED-CONTRACT-FILES:` so the agent re-reads stale contracts. Mid-session ban; explicit user consent required.
- **Chinese-first docs** with English mirror under `docs/en/`. `Default content language` field in `PROJECT_INDEX.md` drives `new_draft.py` body template selection.
- **Scaffolding scripts**: `init_content_ops_project.py` (5 required `Current Site` flags; refuses to start a project with placeholders), `new_draft.py` (20-field frontmatter scaffold; zh-CN / en-US body templates), `discover_sitemaps.py` / `sitemap_diff.py` / `sitemap_discover.py` (competitor monitoring entry points), `picgo_batch_upload.py` (verified real upload end-to-end on `cos.files.maozhishi.com`).
- **Multi-agent + portable**: same `SKILL.md` honoured by Codex (`AGENTS.md`), Claude Code (`CLAUDE.md`), WorkBuddy (`WORKBUDDY.md`); onboarding for Cursor / Cline / Aider / Continue / Trae / Windsurf in `references/agent-onboarding.md`. POSIX + Windows safe (`fcntl.flock` with `O_EXCL` fallback in `_lib.file_lock`).

### Migration

(none — this is the first tagged release.)

[Unreleased]: https://github.com/suxuemi/allincms-content-ops/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/suxuemi/allincms-content-ops/releases/tag/v0.2.0
