# Agent Onboarding

How to point any AI coding agent / IDE at this skill **without duplicating rules**. The principle: SKILL.md is the single source of truth. Each host's rule file should be a one-line pointer, nothing more.

## The Rule (applies to every host)

Insert exactly this line into the host's rule file or system-prompt prepend:

```
Read allincms-content-ops/SKILL.md in this repo and follow it as your operating contract. Do not restate, fork, or summarize its rules in this file.
```

Any host that supports a rule file or pre-prompt can be onboarded with that one line. Do not copy SKILL.md contents into the host config — that creates a second source of truth that will drift.

## Platform note

Scripts under `scripts/` use `fcntl` for file locks (POSIX). On Windows the locker silently falls back to an exclusive-marker file under `.locks/`; it's best-effort, not crash-safe. For production Windows use, run inside WSL or install `portalocker` and adapt `_lib.file_lock` to call it.

## Per-host file locations (as of 2026-06)

If a host you use isn't listed, check its docs for "rule file" / "system prompt" / "instructions" and use the one-line pointer above.

| Host | File or setting | Notes |
|---|---|---|
| Codex CLI | `AGENTS.md` (root) | Already present in this repo. |
| Claude Code | `CLAUDE.md` (root) | Already present. |
| WorkBuddy | `WORKBUDDY.md` (root) | Already present. |
| Cursor | `.cursor/rules/allincms.mdc` (preferred) or `.cursorrules` (legacy) | Use `.mdc` with `description:` frontmatter so Cursor scope-loads on relevant files. |
| Cline | `.clinerules` | Plain text, repo-root. |
| Aider | `CONVENTIONS.md` and pass `--read CONVENTIONS.md` (or `.aider.conf.yml`: `read: CONVENTIONS.md`). | Aider has no auto-loaded rule file; the read flag is mandatory. |
| Continue | `.continue/rules/allincms.md` or `config.json` → `systemMessage` | Continue auto-loads `.continue/rules/*.md`. |
| Windsurf | `.windsurfrules` | Same model as `.cursorrules`. |
| Generic LLM (system-prompt control) | put the one-line pointer at the top of the system prompt | works for OpenAI Assistants, Anthropic Messages, raw API calls. |

### Unverified (community conventions, confirm before using)

These paths are inferred from community discussions and may have changed. If you use one of these hosts, run the pointer line once, confirm the file is loaded, then open a `proposed` entry in `wiki/lessons.md` recording what worked. Do not assume the path is correct.

| Host | Inferred file | Status |
|---|---|---|
| Trae | `.trae/rules.md` | unverified — check current Trae docs |
| Roo Cline | `.roo/rules.md` | unverified — forked from Cline, conventions may diverge |

## Why not auto-generate all of them

Tempting to dump a stub into every possible rule file. Don't:

- Most users only use 1–2 IDEs. Empty `.windsurfrules` files in a Codex-only user's repo are clutter.
- Rule-file conventions change. Maintaining 10 stubs means 10 places to patch when one host changes its loader.
- The one-line pointer is the contract; the file's filename is the host's job. Let users add their own stub if they need it.

## What each stub MUST and MUST NOT contain

MUST:

- One pointer line to `allincms-content-ops/SKILL.md`.
- The 3 pre-flight steps (mode-select, Current Site STOP, lessons sweep) — these are needed before SKILL.md is even read, so they must live in the stub.

MUST NOT:

- Restate the Hard Gates list.
- Restate the Pass Criteria.
- Restate the Workflow steps.
- Restate the residue word list.

The three root stubs (`AGENTS.md`, `CLAUDE.md`, `WORKBUDDY.md`) follow this discipline as the reference.

## Drift detection

Any new rule that lives in a host stub but not in SKILL.md is a bug. Run periodically:

```bash
# crude check: stubs should all be < 30 lines
wc -l AGENTS.md CLAUDE.md WORKBUDDY.md
# and grep for accidental rule duplication
for f in AGENTS.md CLAUDE.md WORKBUDDY.md; do
  grep -E "Hard Gates|Pass Criteria|Residue|≥ 5 objections" "$f" && echo "BUG: $f restates SKILL rules"
done
```
