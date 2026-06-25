[中文](../../README.md) | English

# AllinCMS Content Ops

This folder is a portable AllinCMS content operations kit for humans and AI agents.

Use it to turn source material into audited AllinCMS website content:

`raw -> wiki -> search intent -> web draft -> media -> AllinCMS -> audit -> publish -> index`

## Start Here

1. Read [PROJECT_INDEX.md](../../PROJECT_INDEX.md).
2. If you are installing the skill for an AI agent, read [INSTALL.md](../../INSTALL.md).
3. If you are a new user, follow [QUICKSTART.md](../../QUICKSTART.md).
4. For the actual skill instructions, read [allincms-content-ops/SKILL.md](../../allincms-content-ops/SKILL.md).

## Use with AI (one-shot install)

Copy the whole block below (everything between the triple backticks) and paste it to Claude Code / Codex / Cursor / any AI coding agent. The AI will install and operate the skill.

````text
Please install this AllinCMS content-ops skill and operate by it:

0. First `cd` into an isolated directory (recommended: `~/skills`; if missing, `mkdir -p ~/skills && cd ~/skills`). DO NOT clone inside one of my existing projects — it pollutes `.git` and IDE indexing.

1. In that directory, run:
   git clone https://github.com/suxuemi/allincms-content-ops.git
   cd allincms-content-ops

   Note: the repo root contains a **same-named subfolder** `allincms-content-ops/`. The actual skill files (`SKILL.md` / `references/` / `scripts/`) live in that subfolder.

2. Read `allincms-content-ops/SKILL.md` — that is your operating contract.

   **Write discipline for rule-source files**:
   - `SKILL.md` and `references/*` are READ-ONLY.
   - `wiki/lessons.md` accepts only NEW entries with `status: proposed`. Never write `approved` directly; never edit existing entries. Approval is mine.
   - `wiki/backlog.md` accepts new `status: open` TODOs.
   - `PROJECT_INDEX.md` — only fill empty `Current Site` fields from my dictation; do not touch anything else.
   - When I say "from now on do X" → you MUST add a `proposed` entry in `wiki/lessons.md`, NOT edit SKILL.md or `references/*`.

3. Read `PROJECT_INDEX.md` → `Current Site`. If any field is empty, STOP and ask me; resume after I answer.

4. For every request after this, classify it per SKILL.md → Mode Selection (light vs full).

   Full-mode = Workflow steps 0–9, all of them. **Step 0** (sweep `wiki/lessons.md` for `approved` and merge) and **Step 9** (you MUST ask me verbatim: "Any corrections worth keeping, new directions to try, or TODOs to add from this run?") are **hard gates** — skipping either counts as undelivered work.

5. Run: `python3 allincms-content-ops/scripts/audit_content.py --status .`

   Expected output includes 5 seed `proposed` lessons, 3 backlog rows, and 1 example audit file. These are **scaffold samples, NOT problems in my project** — relay them verbatim, do not clean up unprompted.

Environment notes:
- No shell capability (e.g. claude.ai web) → tell me "I cannot run shell; please execute steps 1 and 5 locally and paste output". Do NOT pretend to execute.
- Windows → use `python` instead of `python3`; split commands onto separate lines; avoid `&&` on legacy PowerShell.
- Target dir already has `allincms-content-ops/` → `cd` in and `git pull`. NEVER `rm -rf`.

Task: <<Replace this entire line with your real task before pasting. If you (the AI) see the literal angle-bracket placeholder in your input, STOP and ask the user "what specifically do you want to do?" instead of acting.>>
````

For advanced scenarios (global skill install, multi-project use, project reset, Codex symlink), see [INSTALL.md](../../INSTALL.md).

## Main Folders

- [raw/index.md](../../raw/index.md): original source material and extracted Markdown.
- [wiki/index.md](../../wiki/index.md): distilled company, product, persona, method, competitor, region, and glossary knowledge.
- [web/index.md](../../web/index.md): website drafts, pages, posts, products, categories, tags, and published URLs.
- [monitoring/index.md](../../monitoring/index.md): competitor monitoring runs and topic proposals.
- [media/index.md](../../media/index.md): image sources, processed files, PicGo uploads, alt text, and usage.
- [audits/index.md](../../audits/index.md): review evidence and scores.

## Publish Rule

Do not publish AllinCMS content unless:

- sources are traceable to `raw/` or `wiki/`
- search intent and target customer are clear
- category, tags, cover, slug, and SEO fields are set
- visual/content/SEO/GEO/backend audits pass
- final score is at least 8.5
- published content is indexed

## Verified Execution Environments

This skill has been run end-to-end on:

- **Codex CLI + Chrome MCP** — reference implementation, full browser + subagent + web fetch coverage
- **Claude Code + MCP browsers** — default host for this repo, full coverage via `Agent` tool

Other IDEs (Cursor / Cline / Aider / Continue / Trae / Windsurf) can mount the skill via a one-line pointer rule — see [agent-onboarding.md](../../allincms-content-ops/references/agent-onboarding.md). Most lack browser automation or subagent spawn; they should hand off after the draft is ready. Full capability matrix: [tooling-matrix.md](../../allincms-content-ops/references/tooling-matrix.md).

## Agent Entry Files

- [AGENTS.md](../../AGENTS.md): Codex and generic agent entry.
- [CLAUDE.md](../../CLAUDE.md): Claude entry.
- [WORKBUDDY.md](../../WORKBUDDY.md): WorkBuddy entry.

## Contact

WeChat (Tony Pan):

![WeChat QR](https://cos.files.maozhishi.com/data/web/web-files/wx/tony-apan.png)
