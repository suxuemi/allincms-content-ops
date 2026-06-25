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
