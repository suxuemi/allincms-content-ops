# Changelog

All notable changes to this skill are tracked here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) with semver semantics defined in [CONTRIBUTING.md](CONTRIBUTING.md): **"breaking" means previously-passing drafts fail on re-audit or existing files need schema migration**, not "any contract character changed".

## [Unreleased]

(none yet)

## [0.4.0] — 2026-06-26

Real-use feedback after v0.3.0: AI-drafted articles had H1 duplicated into body, never set internal links, and lacked rich company/product context. This release closes the three loops.

Codex round: [audits/codex-rounds/v0.4.0-r1.md](audits/codex-rounds/v0.4.0-r1.md) (6 findings, 3 high / 3 med, all applied).

### Added

- `references/first-contact.md` § **Phase 2.5: Material ingestion** — conditional (Path B-2 / C only) prompt for users to drop in website URLs / PDFs / PPTs / Word / Notion exports. AI distills to `wiki/products/_ai-drafts/` and `wiki/personas/_ai-drafts/` (subdir, never overwrites human-curated wiki root). Promote is a manual `mv` step (Fhistorical.1).
- `scripts/suggest_internal_links.py` — reads draft frontmatter, scores `web/published/index.md` rows by tag overlap + persona / category match + secondary-query token hits; prints top N pasteable candidates.
- `tests/test_suggest_links.py` — fixture-based ranking lock (Ffalsifiability.1).
- `audit_content.py` two new warning-class checks: `body_h1_duplicate` (gated on `created_with_version >= 0.4.0` so v0.3 drafts aren't flooded — Fclassification.2) and `missing_internal_links` (warn when body has < 3 internal links).
- `audit_content.py` `WARN_PREFIXES` frozenset — explicit registry for warning-class issues; reported on `!`-prefixed lines, counted under new `warnings=N` summary segment (Fclassification.1).
- `wiki/products/_ai-drafts/` and `wiki/personas/_ai-drafts/` staging subdirs; `library_health.py` and `audit_content.py` exclude them from `consumed_by` / orphan / backlink checks.
- `audit_skill_meta.py`: 12 new regression entries covering all v0.4.0-r1 finding patches.

### Changed

- `new_draft.py` body templates no longer carry `# {title}` H1 (AllinCMS renders frontmatter `title:` as the H1; body H1 caused duplication). Body opens directly with a one-sentence summary; subheadings start at `##`. Templates inline a comment pointing to `suggest_internal_links.py` for link picks.
- `new_draft.py` injects `created_with_version: "0.4.0"` into frontmatter — drives version-gated warning checks.
- `ingest_sources.py` surfaces missing extractors (pdftotext / pandoc) loudly: stderr explains how to install or convert; non-zero exit code on failure; body marker `EXTRACTION FAILED:` prevents silent draft-from-empty (Fprocess.2).
- `audit_content.py` summary line shape: `files=N issues=M warnings=W mode=full`. **CI / downstream that parsed only `issues=N` stays correct**; the new `warnings=` field is additive. Tools that also want to react to warnings can grep the new field.
- `SKILL.md` Resource Map registers the new script, test, and `_ai-drafts/` staging directories.

### Migration

(none required — all changes are additive or version-gated.)

If you've been using v0.3 drafts with `# {title}` in the body, they will NOT be flagged automatically (no `created_with_version` field → check skipped). To opt-in to the check on legacy drafts, add `created_with_version: "0.4.0"` to their frontmatter manually.

[0.4.0]: https://github.com/suxuemi/agently-mail/releases/tag/v0.4.0

## [0.3.0] — 2026-06-26

self-applied v0.3.0 — first release authored under the Update Checklist itself defines.

Codex round: [audits/codex-rounds/v0.3.0-r1.md](audits/codex-rounds/v0.3.0-r1.md) (6 findings, 4 high / 2 med, all applied).

### Added

- `CONTRIBUTING.md` § Update Checklist — formalises the discipline every maintainer change must follow. Classification table with hard limits on Trivial self-classification; per-finding response (no arbitrary % thresholds); persistent regression check via `audit_skill_meta.py`; sweep dispatch clause for mid-session rule changes; emergency / security fast-track; meta-loop rule for the checklist's own versioning.
- `CONTRIBUTING.md` § Historical reconciliation — one-time note that `v0.2.0` is not yanked / not retroactively re-audited; the checklist is enforced from `v0.3.0` onward.
- `allincms-content-ops/references/codex-design-reviewer.md` — design-time codex brief (independent from the existing content reviewer). Inputs: diff + classification + motivation + round id. Four default lens: classification / process matrix / historical reconciliation / falsifiability.
- `allincms-content-ops/scripts/audit_skill_meta.py` — persistent regression check (28 entries at v0.3.0 covering rounds r7 / r8 / r9 / r1). Replaces throwaway self-adversarial heredocs.
- `audits/codex-rounds/v0.3.0-r1.md` — first persisted codex round output. From now on, every codex review is persisted here so CHANGELOG references resolve.

### Changed

- `allincms-content-ops/SKILL.md` Resource Map — registers the new reference, script, and audits directory.

### Migration

(none — additive only.)

[0.3.0]: https://github.com/suxuemi/allincms-content-ops/releases/tag/v0.3.0

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

[Unreleased]: https://github.com/suxuemi/allincms-content-ops/compare/v0.4.0...HEAD
[0.2.0]: https://github.com/suxuemi/allincms-content-ops/releases/tag/v0.2.0
