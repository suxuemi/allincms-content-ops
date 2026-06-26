# Tooling Matrix

Which hosts have been verified to run this skill end-to-end, and what they cover.

## Verified end-to-end

| Host | File R/W | Shell | Browser | Subagent | Web fetch | Audit link |
|---|:-:|:-:|:-:|:-:|:-:|---|

_No rows yet — the first publish that produces an `audits/<slug>-<date>.md` with `pass: true` populates this table per the verification protocol below. Do not promote a row here without that artifact._

## Designed-for (intended hosts, awaiting first end-to-end run)

| Host | File R/W | Shell | Browser | Subagent | Web fetch | Notes |
|---|:-:|:-:|:-:|:-:|:-:|---|
| Codex CLI + Chrome MCP | ✓ | ✓ | ✓ (Chrome MCP) | ✓ (new session) | ✓ | Reference design. AllinCMS browser ops via Chrome MCP with logged-in profile. Not yet proven with a published audit. |
| Claude Code + MCP browsers | ✓ | ✓ | ✓ (Claude in Chrome / Control Chrome MCP) | ✓ (`Agent` tool, `subagent_type=general-purpose`) | ✓ (WebFetch) | Default host for this repo. Not yet proven with a published audit. |

A row graduates from "designed-for" to "verified" only after the verification protocol below succeeds.

## Partial coverage (use with downgrade)

| Host | Gap | Forced downgrade |
|---|---|---|
| Claude Code without browser MCP | no browser automation | "draft handoff" mode: produce draft + reviewer-input.yaml + manual fill checklist; stop before publish step. |
| Plain Codex / SSH session | no browser, no subagent | review must be a second human session; manual AllinCMS fill. |
| Cursor / Cline / Aider / Continue / Trae / Windsurf (rule-file IDEs) | varies — most lack browser automation and subagent spawn | follow `references/agent-onboarding.md` to mount this skill; expect to stop at SOP step 5 (draft ready) and hand off the remainder to a verified host. |

## Capability requirements per SOP step

| Step | Required capabilities |
|---|---|
| 0 Lessons sweep | file R/W |
| 1 Ingest | file R/W, shell, web fetch (if URL inputs) — file-only if URLs pre-downloaded |
| 2 Compile wiki | file R/W |
| 3 Search intent | file R/W |
| 4 Draft | file R/W |
| 5 Media | file R/W, shell (PicGo) |
| 6 AllinCMS fill (DRAFT) | **browser automation** |
| 7 Adversarial audit | shell, **subagent spawn**, web fetch (if `preview_url`) or file R/W (if `preview_html_path`) |
| 8 Publish | **browser automation**, shell |
| 9 Reflect → lessons | file R/W |

If your host lacks a "**bold**" capability for a step you need, stop and hand off. Do not fake the step.

## Doctor → user-facing phrasing (single source for first-contact Phase 0)

When `doctor.py` reports a non-strong cell, the AI uses the `user_facing_phrasing` column below — not the raw tier name. **Strong cells produce no line** (no news is good news).

| Capability | tier × category | user_facing_phrasing |
|---|---|---|
| `git` | missing × critical | `先装 git 才能跑这套 skill — https://git-scm.com/downloads` |
| `python` | missing × critical | `Python 至少要 3.9，升级一下再继续` |
| `pdftotext` | degraded × ingest | `想丢 PDF 给我得装 pdftotext (brew install poppler / apt install poppler-utils)，现在跳过没事` |
| `pandoc` | degraded × ingest | `想丢 Word / PPT 给我得装 pandoc (brew install pandoc / apt install pandoc)，现在跳过没事` |
| `picgo` | degraded × media | `想批量上传图片要先打开 PicGo 桌面端（Settings → PicGo-Server 开启）` |
| `current_site` | missing × open_backend_or_monitor | `打开后台 / 跑监控时我会先开 workspace 引导登录确认，自动补 site_id / 域名 — 不用现在手填` |
| `current_site` | missing × publish | `Current Site 字段会在第一次开后台时由 discovery 自动补上；不用现在手填` |
| `published_index` | degraded × internal_links | `还没发过文章，内链建议会是空的（第一篇发完就有了）` |
| `version_file` | missing × version | `VERSION 文件没了，重新装一次 skill` |

Maintainer: when adding a new `doctor.py` check, add the row here in the same PR. Keeping translation in `tooling-matrix.md` (single source) prevents drift with a separate `doctor-translation.md` (rejected in v0.6.0-r1 Fprocess.1).

## Verification protocol

To add a new "verified" row:

1. Run a real publish on this host (light-mode is not enough — must be full-mode with passing audit).
2. Save the resulting `audits/<slug>-<date>.md` (`pass: true`) and screenshots of the published front-end URL.
3. Update this matrix; link to the audit file.
4. Add a `proposed` entry to `wiki/lessons.md` describing host-specific quirks discovered, so the next agent on the same host inherits the lessons.
