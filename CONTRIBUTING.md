# Contributing

This skill versions itself with semver — but reinterpreted for rules-as-code (see Codex 9th-round adversarial review). "Breaking" doesn't mean "any character in `SKILL.md` changed". It means: **previously-passing drafts fail on re-audit**, or **existing files need a schema migration**, or **a Workflow step / Hard Gate / Mode Selection rule was removed or renamed**.

## Decide the bump type

Walk this decision tree on every change before committing:

1. Does this change cause **any previously-passing draft** to fail when re-audited under the new rules? → **MAJOR**
2. Does this change require **existing files** in `raw/` / `wiki/` / `web/` / `audits/` / `monitoring/` to be migrated to a new schema (renamed field, removed YAML key, new required frontmatter, etc.)? → **MAJOR**
3. Does this change **rename / remove / reorder** a Workflow step, a Hard Gate item, a Mode Selection rule, a Pass Criteria component, or a script's existing CLI signature? → **MAJOR**
4. Is it a new optional capability — a new script, new reference, new mode, or a new frontmatter field that's **not required** for existing content? → **MINOR**
5. Is it a threshold change that emits a **warning** (not a fail) for content drifting outside the new range? → **MINOR**
6. Is it a threshold that **relaxed** (drafts that used to fail now pass)? → **PATCH**
7. Is it docs / comments / typos / a bug fix that makes formerly-broken behavior work? → **PATCH**

If two answers conflict (e.g. you added a new optional field AND tightened an existing threshold to fail), take the **higher** bump.

**Hard line:** new Hard Gates are almost always MAJOR, even if they look small. Adding a one-line gate that retires 5 existing drafts is the textbook breaking change. Do not minor-wash it.

## Bump procedure

1. Edit `/VERSION` to the new number (single line, no `v` prefix, no trailing whitespace).
2. Run `python3 allincms-content-ops/scripts/bump_version.py` — syncs `allincms-content-ops/agents/openai.yaml` from `VERSION`. Hand-editing `openai.yaml.version` is forbidden.
3. Add a `## [vX.Y.Z] — YYYY-MM-DD` section to `CHANGELOG.md`, **above** the `## [Unreleased]` section. List entries under `### Added` / `### Changed` / `### Deprecated` / `### Removed` / `### Fixed` / `### Security`.
4. If this version crosses a MAJOR boundary and existing project data needs schema migration, include a `### Migration` block in the CHANGELOG entry, OR write a migration script under `allincms-content-ops/scripts/migrate_<from>_<to>.py` and reference it from the entry.
5. `python3 allincms-content-ops/scripts/check_version_sync.py` — must exit 0. (CI runs this on PRs.)
6. Commit with message `release: vX.Y.Z`.
7. `git tag vX.Y.Z && git push origin main vX.Y.Z`
8. `gh release create vX.Y.Z --notes-file <(awk '/^## \[vX.Y.Z\]/,/^## \[/' CHANGELOG.md | head -n -1)`

## Lessons → CHANGELOG bridge

When SKILL.md `Workflow step 0` merges an `approved` lesson from `wiki/lessons.md` into the skill itself (SKILL.md / references/* / scripts/*), the merging agent MUST also add a line to `CHANGELOG.md` `## [Unreleased]`:

```
- merged lesson `<date> / <first 40 chars of rule>` from wiki/lessons.md (sha: <commit>)
```

This is the single bridge between the in-project lessons flow and the release flow. Without it, SKILL.md drifts forward but releases never know what shipped.

`scripts/note.py --kind rule` is for **proposing** lessons (`status: proposed`); it does not graduate them — that remains a deliberate step-0 sweep action and the changelog entry is its handshake with releases.

## Avoiding double-source drift between `VERSION` and `agents/openai.yaml`

`VERSION` is the **single source of truth**. `openai.yaml.version` is a mirror, mechanically synced by `bump_version.py`. `SKILL.md` frontmatter intentionally has **no** version field — keeping it out of the contract file means a version bump never touches contract content, so it never invalidates an in-flight agent reading SKILL.md.

CI / pre-commit must run `check_version_sync.py`; PRs that hand-edit `openai.yaml.version` are rejected.

## Shallow clones

`scripts/update_skill.py` reads upstream `VERSION` via `git show origin/main:VERSION`. Shallow clones (`--depth 1`) can fail this. The script auto-detects and runs `git fetch --unshallow --filter=blob:none origin <branch>` once; if that also fails (corporate proxy, no network) it falls back to commit-count diff display and warns the user that semver labels are unavailable this run.

## Pinning to an old version

A team pinned to an old version (because v0.3 changed something they're not ready to migrate to) drops a `.allincms-skill-pin` file at the project root:

```yaml
pinned_to: v0.2.0
pinned_at: 2026-06-26
reason: "v0.3 changed lessons.md schema; planning Q3 migration"
```

`first-contact.md` Phase -1 honours this:

- silently skips the upgrade nudge in normal sessions
- **breaks silence** only when upstream publishes a release tagged `security:` in CHANGELOG
- when `pinned_at` is > 60 days old, prompts once: "this pin is 90+ days old — re-evaluate?"
- `audit_content.py --check-version` warns if a draft uses a field that didn't exist in the pinned version

The pin file is tracked by git (default) so it's shared with the team. Add it to `.gitignore` if you'd rather keep pins individual.
