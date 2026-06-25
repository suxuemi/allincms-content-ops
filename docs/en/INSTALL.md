[中文](../../INSTALL.md) | English

# Install

This file is written for both a new user and an AI agent. An AI agent should read this file, identify the current tool, then perform the matching install path.

## What Gets Installed

The reusable skill folder is:

`allincms-content-ops/`

It contains:

- `SKILL.md`
- `agents/openai.yaml`
- `references/`
- `scripts/`

## Codex Install

If this folder is not already inside a Codex skill directory, copy or symlink it:

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
ln -sfn "$(pwd)/allincms-content-ops" "${CODEX_HOME:-$HOME/.codex}/skills/allincms-content-ops"
python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py" "$(pwd)/allincms-content-ops"
```

If symlinks are not allowed, copy the folder instead:

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R "$(pwd)/allincms-content-ops" "${CODEX_HOME:-$HOME/.codex}/skills/allincms-content-ops"
```

## Claude Install

Claude should read:

1. [CLAUDE.md](../../CLAUDE.md)
2. [allincms-content-ops/SKILL.md](../../allincms-content-ops/SKILL.md)
3. [PROJECT_INDEX.md](../../PROJECT_INDEX.md)

If using Claude Code project skills, copy or symlink `allincms-content-ops/` into the project skill location used by that environment. Keep this root folder as the source of truth unless the user explicitly asks for a separate copy.

## WorkBuddy Install

WorkBuddy should read:

1. [WORKBUDDY.md](../../WORKBUDDY.md)
2. [allincms-content-ops/SKILL.md](../../allincms-content-ops/SKILL.md)
3. [PROJECT_INDEX.md](../../PROJECT_INDEX.md)

## Initialize A New Content Project

Use this when creating a fresh project structure:

```bash
python3 allincms-content-ops/scripts/init_content_ops_project.py .
```

This creates `raw/`, `wiki/`, `web/`, `monitoring/`, `media/`, `audits/`, and their indexes.

## Verify Install

Run:

```bash
python3 -m py_compile allincms-content-ops/scripts/*.py
python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py" allincms-content-ops
python3 allincms-content-ops/scripts/audit_content.py .
```

Expected result:

- skill validation prints `Skill is valid!`
- script compile exits cleanly
- audit reports no issues unless real web drafts contain missing metadata, AI smell, residue, or image problems
