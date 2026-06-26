# Changelog

All notable changes to this skill are tracked here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) with semver semantics defined in [CONTRIBUTING.md](CONTRIBUTING.md): **"breaking" means previously-passing drafts fail on re-audit or existing files need schema migration**, not "any contract character changed".

## [Unreleased]

(none yet)

## [0.8.1] — 2026-06-26

User feedback after v0.8.0: "你可以读 ppt pdf word 吗?" → AI (Codex / Claude Code) confidently said yes, it can. User then asked why we're nagging them to install pdftotext / pandoc / markitdown / paddleocr if the AI agent reads these natively. Correct call — v0.5-v0.8's doctor warning was over-recommendation. The same UX pattern that caused v0.7's "请给我 4 个值" feedback. Pulling the noise.

### Removed

- `doctor.py` `check_extraction` function + `check_chinese_ocr` function + the three `_has_markitdown` / `_has_paddleocr` / `_has_legacy_cli` private helpers. Doctor no longer pushes users toward installing CLI extractors.
- `doctor.py` CHECKS entries: `extraction × ingest`, `chinese_ocr × optional`. The dashboard now shows only the checks that matter to interactive AI users.
- `references/tooling-matrix.md` user_facing_phrasing rows: `extraction × ingest`, `chinese_ocr × ingest`.
- `tests/test_doctor_extraction_matrix.py` — tested removed code, no longer meaningful.
- `audit_skill_meta.py` entries: `doctor-extraction-anyof`, `doctor-chinese-ocr-optional`, `test-doctor-extraction-matrix`. Re-anchored `doctor-script` regression slug on `check_git` (a stable check that's been there since v0.5).

### Changed

- `references/ocr-strategy.md` — added a **scope banner** at the top: "this document is for batch / unattended / CI workflows only; interactive AI agents read PDF / Word / PPT natively, you don't need to install any of these CLI tools".
- `SKILL.md` Resource Map — removed the reference to the deleted test file.

### Kept (intentionally — dormant code, doesn't bother anyone)

- `ingest_sources.py` markitdown / paddleocr / pandoc fallback chain stays. Anyone running batch ingestion via cron or CI still has it; never invoked in interactive sessions.
- `r2_setup.py` + `r2_upload.py` + `references/media-pipeline.md` — image hosting is an independent concern, not about document reading.

### Migration

(none — pure removal of UX noise.)

For v0.8.0 users who were seeing `[WARN] extraction` in `doctor.py`: that warning is gone in v0.8.1. The CLI tools you may or may not have installed continue to work as before (or be absent — also fine).

[0.8.1]: https://github.com/suxuemi/allincms-content-ops/releases/tag/v0.8.1

## [0.8.0] — 2026-06-26

Real-use feedback: v0.7 doctor 红字"pdftotext / pandoc 缺失"对新手吓人；用户问能不能上 MarkItDown（Microsoft 2024，pip 装）；同时需要 Cloudflare R2 替代 PicGo（不依赖桌面 app，AI agent 在任何 host 都能调）；discovery 在 Codex vs Claude Code 等不同 host 该用哪个浏览器没说清。

> v0.7 装齐 pdftotext+pandoc 的用户**不需要重装**——doctor 仍判 strong，只是会建议装 markitdown 以覆盖 Excel 等。

Codex round: [audits/codex-rounds/v0.8.0-r1.md](audits/codex-rounds/v0.8.0-r1.md) (7 findings, 4 high / 3 med, all applied).

### Added

- `references/ocr-strategy.md` — tool ladder for document → markdown. Default chain `MarkItDown (Microsoft, MIT) → PaddleOCR (Apache 2.0) fallback` (Fclass.1). Documents license caveats: MinerU AGPL-3.0 is never auto-invoked (Fclass.2). Privacy commitment: all OCR runs local, no hosted APIs.
- `references/media-pipeline.md` — PicGo vs R2 trade-offs, "one host per project" rule with concrete migration path. Surfaces `doctor.media_mix` warning conditions (Fhist.1).
- `scripts/r2_setup.py` — interactive Cloudflare R2 wizard. Walks user through dashboard (account / bucket / API token / optional custom domain), writes credentials to `~/.config/allincms-content-ops/r2.toml` (mode 0600), runs round-trip test upload (auto-cleanup).
- `scripts/r2_upload.py` — batch upload to R2, same CLI shape as `picgo_batch_upload.py`. Idempotent (SHA-keyed object paths). Appends to `media/index.md`. Masks `access_key_id` as `xxx...xxx` in all output; `secret_access_key` never printed (Fclass.3).
- `tests/test_doctor_extraction_matrix.py` — locks the 4 (markitdown × legacy CLI) combinations of `doctor.check_extraction` + the optional/silent behavior of `chinese_ocr` (Ffalsif.1).
- `doctor.py` new checks: `extraction × ingest` (ANY-of: markitdown OR (pdftotext + pandoc)), `chinese_ocr × ingest` (optional — never red), `media_uploader × media`, `media_mix × media` (warns on multi-host `media/index.md`), `--refresh` flag to bypass 24h cache.
- `current-site-discovery.md` § Browser selection per host — 6-row table mapping host to primary + fallback browser; **explicit confirm** before launch ("我打算用 X，依据是 Y。30 秒内回车确认或 manual"); Unknown host → manual fallback (paste HTML approach).
- `audit_skill_meta.py`: 18 new regression entries.

### Changed

- `scripts/ingest_sources.py` overhauled:
  - Fallback chain: markitdown → PaddleOCR (image / image-PDF) → legacy CLI → fail
  - Named constants `EXTRACTION_MIN_CHARS = 100` and `INPUT_SUBSTANTIAL_BYTES = 50_000` replace magic numbers (Fproc.1). Dual gate prevents misfires on legitimately short inputs.
  - Tool-specific outputs preserved to `.raw/<source>.markitdown.md` / `.raw/<source>.paddleocr.md` / etc. — no silent overwrites between fallback tiers.
- `scripts/doctor.py` removed `check_pdftotext` / `check_pandoc` (each was a separate red flag). Replaced with single `check_extraction` (ANY-of). PaddleOCR check moved to `optional` category — never red in dashboard summary (Fclass.1).
- `references/tooling-matrix.md` `user_facing_phrasing` updated: dropped separate pdftotext / pandoc rows, added `extraction` (markitdown recommendation), `chinese_ocr` (silent), `media_uploader` (R2 or PicGo), `media_mix` (warn).
- `SKILL.md` Resource Map registers 5 new files (ocr-strategy, media-pipeline, r2_setup, r2_upload, test_doctor_extraction_matrix).

### Migration

(none required — additive only.)

- v0.7 users with pdftotext + pandoc: nothing to do. doctor still strong, with a one-line nudge to `pipx install markitdown` for Excel coverage.
- v0.7 users without pdftotext / pandoc who were seeing red: `pipx install markitdown` clears the warning. Or install `brew install poppler pandoc` to keep the legacy path.
- PicGo users: continue. R2 is an alternative, not a replacement.

[0.8.0]: https://github.com/suxuemi/allincms-content-ops/releases/tag/v0.8.0

## [0.7.0] — 2026-06-26

Real-run feedback again: user asked "帮我打开后台" and v0.6 AI refused with "请给我这 4 个值: AllinCMS site id / Front-end domain / Workspace URL / Browser profile". User pointed out that `workspace_url` is a constant for all SaaS users, `browser_profile` is auto-detectable, and `site_id` is in the workspace URL after login — none of these should be asked upfront. v0.7 replaces "ask 4 values" with discovery-driven flow.

> Note: pin@0.6 users 不受影响 — discovery 仅在 unpinned 或 ≥0.7 时生效。

Codex round: [audits/codex-rounds/v0.7.0-r1.md](audits/codex-rounds/v0.7.0-r1.md) (7 findings; 2 high / 4 med / 1 low; all applied).

### Added

- `references/current-site-discovery.md` — opportunistic sub-protocol. Opens `workspace.laicms.com` directly when the user requests a backend / publish / monitor action and `Current Site` is incomplete. Handles login wait-and-resume (Fprocess.2), lists sites (1 → confirm; N → pick), auto-fills `site_id` + `front_end_domain` into `PROJECT_INDEX.md` with inline reporting. State-machine boundary with `first-contact.md` Phase 1/2 explicitly defined in Preconditions (Fprocess.1).
- `audits/discovery-fixtures/dashboard-snapshot.md` — regression fixture capturing the expected `workspace.laicms.com` DOM structure (login wall / dashboard / site card / site detail). Updated in the same PR as any workspace redesign (Ffalsifiability.1).
- New optional `Current Site` field: `deployment: saas | self-hosted` (default `saas`). `self-hosted` skips Step 1's SaaS URL default and asks the user for the workspace URL once (Fhistorical.1). Backward safe: existing projects without the field default to `saas`.
- `audit_skill_meta.py`: 11 new regression entries covering discovery preconditions, resume contract, ≥ 2 signal rule, failure budget, self-hosted opt-out, dashboard fixture, SKILL.md Hard Gate routing, tooling-matrix phrasing split, narrate whitelist coverage, and round persistence.

### Changed

- `SKILL.md` Required Context Hard Gate: "STOP and request values" → "first run the opportunistic discovery sub-protocol; only fall back to asking the user explicitly when discovery fails twice in a session / env has no browser / `deployment: self-hosted`".
- `references/tooling-matrix.md` `user_facing_phrasing` for `current_site`: split into two rows (`× open_backend_or_monitor` discovery-aware; `× publish` notes the field will be filled by discovery the first time backend is opened) per Fprocess.3.
- `references/first-contact.md` § Don't narrate § 必须报告 whitelist: explicitly mentions `PROJECT_INDEX.md Current Site auto-fills from current-site-discovery.md — inline-report in the same turn` so discovery's writes are not silent (Fclassification.1).

### Fixed

- `scripts/init_content_ops_project.py` template: removed duplicate `- Default content language:` line that caused the self-check (`PROJECT_INDEX must have exactly one 'Default content language:' line`) to raise. The duplicate was a legacy leftover from the v0.3 field rename — found while adding the `deployment` field to the template. Existing projects unaffected; future `init` runs no longer fail.

### Migration

(none — discovery is a new fallback path; v0.6 ask-4-values flow is preserved as the fallback after 2 discovery failures, no browser, or `deployment: self-hosted`.)

For existing v0.6 users: optionally add `- deployment: saas` to your `PROJECT_INDEX.md` Current Site section to make the opt-out explicit. Absent field defaults to `saas`.

[0.7.0]: https://github.com/suxuemi/allincms-content-ops/releases/tag/v0.7.0

## [0.6.0] — 2026-06-26

UX texture refinement driven by a real-run screenshot. v0.5 shipped doctor + check_draft + examples; a user immediately ran the install prompt and the screenshot showed the AI's first message was 8 lines of dense Chinese including paths / SHAs / "已读 X 和 Y" / "现在按 first-contact 进入 Phase 2" — technically correct, but heavy on the newbie. v0.6 fixes the texture without touching contract.

> Note: 首屏从 8 行压到 3 行是有意的。装没装好用 `python3 allincms-content-ops/scripts/doctor.py -v` 看长版。

Codex round: [audits/codex-rounds/v0.6.0-r1.md](audits/codex-rounds/v0.6.0-r1.md) (7 findings; 2 high / 3 med / 2 low; all applied).

### Added

- `first-contact.md` § **Phase 0: Preamble** — the AI's first user-facing message now has a contract: ≤ 3 substantive lines + 1-line "details on demand" exit. Shape: `✓ 装好了 (v<X.Y.Z> @ <sha> · SKILL.md + first-contact.md) / ✓ 现在能做：… / ⚠ 想做 X 要装 Y / ✗ 发布前要补：…`. Drops self-check narration ("已读取", "没有 rm -rf"); keeps version anchor (Fclassification.1).
- `first-contact.md` § **Self-check before sending Phase 0** — 5 banned phrases (`现在按 first-contact …` / `进入 Phase …` / `按 first-contact 协议 …` / `协议要求 …` / `已读取 SKILL.md 和 …`). AI scans its own first message before sending.
- `first-contact.md` § **Don't narrate the protocol** — applies session-wide, with explicit **必须报告** whitelist (writing files / changing wiki / installing dependencies / running git push / spawning subagent / crossing Hard Gate) so silence doesn't hide legitimate side effects (Fclassification.2).
- `first-contact.md` Phase 2 / 2.5 § **Progress hint** — every fixed-N question now shows `（X/N）` plus a one-line scope hint plus what's coming next. N is computed dynamically: `N = 3 + (Current Site empty fields from doctor) + (Phase 2.5 triggered ? 1 : 0)` with a worked example (Ffalsifiability.2).
- `tooling-matrix.md` new section: **Doctor → user-facing phrasing** — single-source translation table (tier × category → user_facing_phrasing line). Rejected creating `doctor-translation.md` per Fprocess.1 (avoid double source).
- `audits/protocol-leak-samples.md` — per-release real-screenshot samples annotated for protocol-narration leaks. Compensates for the unfalsifiable "don't narrate" rule (Ffalsifiability.1): periodic sampling catches what grep can't. Seeded with the v0.5 leak baseline.
- `audit_skill_meta.py`: 10 new regression entries covering Phase 0, banned phrases, don't-narrate, must-report whitelist, progress formula, tooling-matrix user-phrasing column, leak samples baseline.

### Changed

- `first-contact.md` Phase -2: stopped instructing AI to "report the raw `strong/degraded/missing` tier lines verbatim" — that produced the v0.5 wall of text. Now Phase -2's job is to fill `.doctor-cache.json`; Phase 0 owns the user-facing translation using `tooling-matrix.md` `user_facing_phrasing` column.
- `first-contact.md` Don'ts list expanded: "Don't narrate the protocol", "Don't paraphrase raw doctor tiers".

### Migration

(none — additive only.)

For v0.5 users who depended on the 8-line preamble for verification ("I see 8 lines, AI is doing the right thing"): the version anchor on line 1 (`✓ 装好了 (vX.Y.Z @ <sha> · SKILL.md + first-contact.md)`) is your replacement signal — same trust, less noise. If you want the full long version of the diagnostic, run `python3 allincms-content-ops/scripts/doctor.py -v`.

[0.6.0]: https://github.com/suxuemi/agently-mail/releases/tag/v0.6.0

## [0.5.0] — 2026-06-26

Newbie first-mile optimization. v0.4 had real-use bugs fixed; v0.5 addresses the bigger friction — newbies were never reaching their first publish because of cascading "didn't know I had to install X" / "didn't know what to fill in" failures.

Codex round: [audits/codex-rounds/v0.5.0-r1.md](audits/codex-rounds/v0.5.0-r1.md) (7 findings, 4 high / 3 med; Fclassification.1 caused Design B to be replaced).

### Added

- `scripts/doctor.py` — one-stop environment diagnostic. Three-tier output (`strong` / `degraded` / `missing`) reusing `tooling-matrix.md` vocabulary (Fprocess.1). Each non-strong finding links to a `tooling-matrix.md` anchor with remediation. Result cached to `.doctor-cache.json` so first-contact Phase -2 reads it without re-running.
- `scripts/check_draft.py` — teaching tool for newbies. Scans a draft and explains, field-by-field, what's missing and **why each one matters**. Never modifies files, never returns non-zero. Publish gates stay in `audit_content.py` (Fclassification.1 driver: Design B `--onboarding` flag dropped — would have broken reviewer protocol).
- `examples/sample-article-zh/article.md` and `examples/sample-article-en/article.md` — fully-filled reference drafts. ~400 words each, 3 H2 sections, internal links, credibility evidence references.
- `examples/README.md` — explains how to use examples + warns explicitly against copying identity fields literally.
- `first-contact.md` § `Phase -2: Doctor` — runs before Phase -1 if `.doctor-cache.json` is missing or > 24h old. Surfaces remediation lines verbatim.
- `audit_skill_meta.py`: 12 new regression entries.

### Changed

- `audit_content.py`: new **Hard Gate** `unreplaced_placeholders` — frontmatter containing `__REPLACE_ME__` blocks publish. Backward safe: no v0.4 draft uses this literal, so no existing draft fails re-audit (Fhistorical.1).
- `README.md`: new `## 第一次用？` section above the AI install prompt, separated by `---`. Tells newbies to run doctor first; old users skip past per Fhistorical.2 (visual separator preserves existing muscle memory).
- `first-contact.md` Phase 4 `draft & ship` route: now lists explicit next-step commands — read examples → ask for persona/query → `new_draft.py` → `check_draft.py` → Workflow step 3.
- `SKILL.md` Resource Map registers `doctor.py`, `check_draft.py`, `examples/`.
- `.gitignore`: `.doctor-cache.json` ignored.

### Design changes from review

- **Design B (`--onboarding` flag) dropped** per Fclassification.1: relaxing audit blocking would have left reviewer Pass Criteria untouched (8.5 + each ≥ 70% + ≥ 5 objections); newbie would have escaped audit but been killed by reviewer. Replaced with teaching path (Design C+++): `check_draft.py` explains the rules, examples show what good looks like, `__REPLACE_ME__` Hard Gate catches the lethal "copy example forgot to override" mistake.

### Migration

(none — all additive or backward-safe.)

If you have existing v0.4 drafts that you opt to validate against the new `unreplaced_placeholders` Hard Gate: nothing to do — gate is automatic. To run the teaching tool retroactively: `python3 allincms-content-ops/scripts/check_draft.py <draft.md>`.

[0.5.0]: https://github.com/suxuemi/allincms-content-ops/releases/tag/v0.5.0

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

[Unreleased]: https://github.com/suxuemi/allincms-content-ops/compare/v0.8.1...HEAD
[0.2.0]: https://github.com/suxuemi/allincms-content-ops/releases/tag/v0.2.0
