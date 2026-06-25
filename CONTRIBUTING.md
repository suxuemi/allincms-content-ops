# Contributing

This skill versions itself with semver — but reinterpreted for rules-as-code (see Codex 9th-round adversarial review). "Breaking" doesn't mean "any character in `SKILL.md` changed". It means: **previously-passing drafts fail on re-audit**, or **existing files need a schema migration**, or **a Workflow step / Hard Gate / Mode Selection rule was removed or renamed**.

## Historical reconciliation (one-time)

`v0.2.0` was released before this checklist existed. It is **not yanked, not retroactively re-audited**. The checklist is enforced from `v0.3.0` onward; the gap is permanent and acknowledged in `CHANGELOG.md` `## [0.2.0]`. Future maintainers should not re-debate this.

## Update Checklist (every non-trivial change MUST follow)

Pre-existing rules across this skill (consent / adversarial review / single-source / pass criteria) only work if maintainers themselves follow the same discipline when changing the skill. This checklist固化s that.

### 0. Classify the change

| Class | Examples | Required steps |
|---|---|---|
| **Trivial** | typo, single-line comment, broken link fix | Steps 4–8 only |
| **Minor** | script bug fix, new optional reference, docs clarification | All steps; codex round recommended |
| **Substantive** | new script, new Mode rule, new optional contract field, new audit check | All steps; codex round **mandatory** |
| **Breaking** | new Hard Gate, removing or renaming any contract item, schema change | All steps + codex + migration design |

**Hard limit on self-classifying as Trivial**: `git diff --stat` net change ≤ 3 lines AND only `*.md` whitespace / comment / spelling AND the diff does NOT touch `SKILL.md`, `references/`, `scripts/`, or `VERSION`. Any of these conditions fails → Minor or higher. Maintainer-self-judgment is bounded by these mechanical limits, not by feeling.

### 1. Adversarial design review (Substantive / Breaking only)

Before writing any code, send the proposed change to a **fresh codex subagent** using the brief at `allincms-content-ops/references/codex-design-reviewer.md` (a design-time brief — do NOT reuse the content-review brief `codex-adversarial-reviewer.md`; their inputs and lens differ).

**Persistence**: the codex output is committed at `audits/codex-rounds/vX.Y.Z-rN.md` BEFORE implementation begins. CHANGELOG entries reference findings by relative path (e.g. `(audits/codex-rounds/v0.3.0-r1.md#f2.2)`); without the file, IDs are unresolvable and the PR is rejected.

**Per-finding response, not percentages**: for each `high` / `med` finding, write `applied` (with the patch) or `rejected` (with one-sentence reason) into the commit body. Any rejected `high` finding requires a follow-up codex round to confirm before merge; the maintainer cannot self-overrule a high finding alone.

### 2. Implementation

- Make the change.
- If new script / reference: update `SKILL.md` → Resource Map. No silent additions.
- Contract files (`SKILL.md` / `references/*` / `scripts/*`) are touched **only in a standalone maintenance commit**, never bundled with a content op.

### 3. Persistent regression check (not a throwaway heredoc)

Each codex round adds entries to `allincms-content-ops/scripts/audit_skill_meta.py` — one `--check` slug per high-severity structural finding. The script greps for the pattern that proves the rule is still in place; failure means the rule has been quietly removed or renamed.

Heredocs are banned for self-adversarial scans — they vanish after one run. Persistent checks live in `audit_skill_meta.py`.

### 4. Tests

```bash
python3 -m py_compile allincms-content-ops/scripts/*.py
python3 allincms-content-ops/scripts/audit_content.py --check-raw-immutable --check-backlinks --check-lessons-drain .
python3 allincms-content-ops/scripts/check_version_sync.py
python3 allincms-content-ops/scripts/audit_skill_meta.py
```

Plus relevant smoke tests (new script `--help`, semver edge cases, pin-file parsing).

### 5. Decide bump

Walk the decision tree in the next section. **If MAJOR**, double-check: would any current `v0.X` user's drafts fail re-audit? Yes → MAJOR confirmed. No → reconsider whether it's MINOR.

### 6. Sync VERSION

```bash
# edit /VERSION (single line, e.g. "0.3.0")
python3 allincms-content-ops/scripts/bump_version.py
python3 allincms-content-ops/scripts/check_version_sync.py
```

### 7. CHANGELOG entry

Add `## [vX.Y.Z] — YYYY-MM-DD` ABOVE existing release sections. Subsections: `Added` / `Changed` / `Deprecated` / `Removed` / `Fixed` / `Security` / `Migration` (last two optional). Reference codex findings by relative path to `audits/codex-rounds/vX.Y.Z-rN.md#fX.Y` for traceability.

### 8. Commit + tag + release

```bash
git add -A
git commit -m "vX.Y.Z: <one-line summary>

<body: motivation / codex round file / findings applied + rejected (with reason) / verification commands run>"
git push
git tag -a vX.Y.Z -m "vX.Y.Z — <title>"
git push origin vX.Y.Z
gh release create vX.Y.Z --notes-file <extracted CHANGELOG section>
```

### Sweep dispatch (mid-session rule changes)

When `note.py --kind rule` lands a `proposed` lesson and the next session's `SKILL.md` Workflow step 0 sweep merges it: re-classify the merge per § 0 **before applying**. If the merge is Substantive or Breaking, **pause the sweep**, surface to the user, and run the full Update Checklist as a separate maintenance commit. Sweeping must not smuggle a Substantive contract change as a routine merge.

If the merge is Trivial / Minor: complete the sweep, write the bridge line to CHANGELOG `## [Unreleased]`, and continue.

### Emergency / security

If fixing a security issue (residue scan miss, credential leak path, prompt injection vector):

1. Steps 1 (codex round) and 3 (regression script entry) may be deferred — but only when the fix is < 10 lines and obviously a correctness fix (e.g. removing a logged secret). Deferral creates a backlog entry "post-mortem codex round for vX.Y.Z security fix".
2. CHANGELOG entry MUST include a `### Security` heading — this is what triggers `first-contact.md` Phase -1 to break pin-silence.
3. Bump as PATCH (most), MINOR (new check), MAJOR (contract change).
4. Tag and release within 24 hours.

### Checklist itself versioning

This checklist is part of the skill contract:

- Changes to § 0 classification, § 1 codex flow, § 3 regression script policy, § 4 test command list, or any other normative clause → at least MINOR, and must run through this same checklist (元循环 well-defined).
- Changes to § 4 because a downstream script signature changed → same commit as the script change, bump takes the higher of the two.
- First self-application of the checklist (this release) is declared with the marker phrase `self-applied v0.3.0` in the commit body — future self-applications use `self-applied vX.Y.Z` likewise.

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
