#!/usr/bin/env python3
"""Persistent regression check for the SKILL's own meta-rules.

Every codex round that surfaces a structural finding lands a pattern here
so the next maintainer (or CI) can grep for regressions in one command.
Patterns are facts that should remain present in the named file. A check
fails when its pattern goes missing — which means the underlying rule has
been quietly removed or renamed.

Add one entry per high-severity finding. Use `--check <slug>` to run one;
no flag runs all.
"""
import argparse
import re
import sys
from pathlib import Path


CHECKS = {
    # Codex round v0.6.0-r1 (UX texture from real-run screenshot)
    "first-contact-phase-0-preamble": {
        "file": "allincms-content-ops/references/first-contact.md",
        "pattern": r"Phase 0: Preamble",
        "intent": "first user-facing message contract is documented as a phase, not implicit",
    },
    "first-contact-self-check-banned-phrases": {
        "file": "allincms-content-ops/references/first-contact.md",
        "pattern": r"Self-check before sending Phase 0",
        "intent": "banned-phrase self-check section exists; falsifiability of don't-narrate rule",
    },
    "first-contact-dont-narrate-section": {
        "file": "allincms-content-ops/references/first-contact.md",
        "pattern": r"Don't narrate the protocol",
        "intent": "general don't-narrate rule covers the whole session, not just Phase 0",
    },
    "first-contact-narrate-whitelist": {
        "file": "allincms-content-ops/references/first-contact.md",
        "pattern": r"必须报告",
        "intent": "whitelist prevents over-fitting silence to breaking changes (Fclassification.2)",
    },
    "first-contact-progress-formula": {
        "file": "allincms-content-ops/references/first-contact.md",
        "pattern": r"N formula",
        "intent": "X/N progress is dynamic; formula prevents AI from inventing N (Ffalsifiability.2)",
    },
    "tooling-matrix-user-phrasing-column": {
        "file": "allincms-content-ops/references/tooling-matrix.md",
        "pattern": r"user_facing_phrasing",
        "intent": "translation lives in tooling-matrix single source (Fprocess.1 chose against new file)",
    },
    "tooling-matrix-doctor-translation-rows": {
        "file": "allincms-content-ops/references/tooling-matrix.md",
        "pattern": r"missing × publish",
        "intent": "tooling-matrix has at least the doctor.py categories represented",
    },
    "protocol-leak-samples-file": {
        "file": "audits/protocol-leak-samples.md",
        "pattern": r"Protocol Leak Samples",
        "intent": "per-release sample of real first-message + leak annotations",
    },
    "protocol-leak-samples-v05-baseline": {
        "file": "audits/protocol-leak-samples.md",
        "pattern": r"Sample 1.*v0\.5\.0",
        "intent": "v0.5 leak baseline preserved (regression diff source)",
    },
    "codex-round-v060": {
        "file": "audits/codex-rounds/v0.6.0-r1.md",
        "pattern": r"Codex Round v0\.6\.0-r1",
        "intent": "v0.6.0 codex round persisted to disk",
    },

    # Codex round v0.5.0-r1 (newbie first-mile)
    "doctor-script": {
        "file": "allincms-content-ops/scripts/doctor.py",
        "pattern": r"def check_pdftotext",
        "intent": "newbie diagnostic script exists",
    },
    "doctor-three-tier-vocab": {
        "file": "allincms-content-ops/scripts/doctor.py",
        "pattern": r"strong.*degraded.*missing",
        "intent": "doctor reuses tooling-matrix three-tier vocabulary (Fprocess.1)",
    },
    "doctor-cache-gitignored": {
        "file": ".gitignore",
        "pattern": r"\.doctor-cache\.json",
        "intent": "doctor cache is gitignored",
    },
    "check-draft-script": {
        "file": "allincms-content-ops/scripts/check_draft.py",
        "pattern": r"teaching mode",
        "intent": "check_draft.py is the teaching tool (no blocking, no side effects)",
    },
    "audit-replace-me-gate": {
        "file": "allincms-content-ops/scripts/audit_content.py",
        "pattern": r"unreplaced_placeholders",
        "intent": "Hard Gate against __REPLACE_ME__ leak from examples (Fhistorical.1)",
    },
    "examples-zh-replace-me": {
        "file": "examples/sample-article-zh/article.md",
        "pattern": r"__REPLACE_ME__",
        "intent": "Chinese example uses __REPLACE_ME__ for identity fields",
    },
    "examples-en-replace-me": {
        "file": "examples/sample-article-en/article.md",
        "pattern": r"__REPLACE_ME__",
        "intent": "English example uses __REPLACE_ME__ for identity fields",
    },
    "examples-readme-warning": {
        "file": "examples/README.md",
        "pattern": r"DO NOT COPY identity fields",
        "intent": "examples/README explicitly warns against identity leak",
    },
    "first-contact-phase-minus-two": {
        "file": "allincms-content-ops/references/first-contact.md",
        "pattern": r"Phase -2: Doctor",
        "intent": "Phase -2 (doctor) runs before Phase -1",
    },
    "first-contact-draft-and-ship-path": {
        "file": "allincms-content-ops/references/first-contact.md",
        "pattern": r"check_draft\.py",
        "intent": "draft & ship path steps now reference check_draft.py teaching",
    },
    "readme-doctor-section": {
        "file": "README.md",
        "pattern": r"第一次用？",
        "intent": "README has the newbie doctor section above the AI install prompt",
    },
    "codex-round-v050": {
        "file": "audits/codex-rounds/v0.5.0-r1.md",
        "pattern": r"Codex Round v0\.5\.0-r1",
        "intent": "v0.5.0 codex round persisted to disk",
    },

    # Codex round v0.4.0-r1 (material ingestion + H1 dedup + internal links)
    "audit-warn-prefixes-frozenset": {
        "file": "allincms-content-ops/scripts/audit_content.py",
        "pattern": r"WARN_PREFIXES = frozenset",
        "intent": "warning issues live in an explicit frozenset, not scattered string checks",
    },
    "audit-warnings-summary-line": {
        "file": "allincms-content-ops/scripts/audit_content.py",
        "pattern": r"warnings=\{total_warnings\}",
        "intent": "audit stdout reports warnings count separately (CI backward-compat)",
    },
    "audit-body-h1-version-gated": {
        "file": "allincms-content-ops/scripts/audit_content.py",
        "pattern": r"body_h1_duplicate",
        "intent": "H1 duplicate check exists; gated on created_with_version >= 0.4.0",
    },
    "new-draft-created-with-version": {
        "file": "allincms-content-ops/scripts/new_draft.py",
        "pattern": r'created_with_version: "0\.4\.0"',
        "intent": "scaffold injects version stamp so version-gated checks work",
    },
    "new-draft-no-h1-in-body": {
        "file": "allincms-content-ops/scripts/new_draft.py",
        "pattern": r"AllinCMS 渲染 frontmatter `title:` 作为页面 H1",
        "intent": "scaffold body templates no longer carry `# {title}` (H1 duplication source)",
    },
    "library-health-ignores-ai-drafts": {
        "file": "allincms-content-ops/scripts/library_health.py",
        "pattern": r'"_ai-drafts" in p\.parts',
        "intent": "library_health excludes _ai-drafts/ staging from checks",
    },
    "first-contact-phase-2-5": {
        "file": "allincms-content-ops/references/first-contact.md",
        "pattern": r"Phase 2\.5: Material ingestion",
        "intent": "Phase 2.5 conditional ingestion guidance is present",
    },
    "first-contact-ai-drafts-subdir": {
        "file": "allincms-content-ops/references/first-contact.md",
        "pattern": r"_ai-drafts/",
        "intent": "AI bootstraps go to _ai-drafts/ subdir, not wiki/products/ root",
    },
    "ingest-sources-extractor-missing-exit": {
        "file": "allincms-content-ops/scripts/ingest_sources.py",
        "pattern": r"__EXTRACTOR_MISSING__",
        "intent": "ingest_sources surfaces missing extractor instead of silent fallback",
    },
    "suggest-internal-links-script": {
        "file": "allincms-content-ops/scripts/suggest_internal_links.py",
        "pattern": r"def score_candidate",
        "intent": "internal-links suggester script exists",
    },
    "suggest-internal-links-fixture-test": {
        "file": "tests/test_suggest_links.py",
        "pattern": r"def test_overlap_topscore",
        "intent": "scoring is locked by a fixture-based test (Ffalsifiability.1)",
    },
    "codex-round-v040": {
        "file": "audits/codex-rounds/v0.4.0-r1.md",
        "pattern": r"Codex Round v0\.4\.0-r1",
        "intent": "v0.4.0 codex round persisted to disk",
    },

    # Codex round v0.3.0-r1 (Update Checklist)
    "audits-codex-rounds-dir": {
        "file": "audits/codex-rounds/v0.3.0-r1.md",
        "pattern": r"Codex Round v0\.3\.0-r1",
        "intent": "first persisted codex round output; if missing, the traceability mechanism collapsed",
    },
    "design-reviewer-brief": {
        "file": "allincms-content-ops/references/codex-design-reviewer.md",
        "pattern": r"^# Codex Design Reviewer Brief$",
        "intent": "design-time review brief (separate from content review)",
    },
    "contributing-historical-reconciliation": {
        "file": "CONTRIBUTING.md",
        "pattern": r"Historical reconciliation",
        "intent": "v0.2.0 reconciliation note must remain; otherwise maintainers re-debate yank",
    },
    "contributing-trivial-hardlimits": {
        "file": "CONTRIBUTING.md",
        "pattern": r"Hard limit on self-classifying as Trivial",
        "intent": "trivial-class escape hatch must stay closed",
    },
    "contributing-no-percentages": {
        "file": "CONTRIBUTING.md",
        "pattern": r"per-finding response",
        "intent": "no arbitrary % thresholds for codex compliance",
    },
    "contributing-mid-session-sweep-clause": {
        "file": "CONTRIBUTING.md",
        "pattern": r"Sweep dispatch",
        "intent": "step 0 sweep cannot smuggle Substantive lesson merges",
    },
    "contributing-self-versioning": {
        "file": "CONTRIBUTING.md",
        "pattern": r"Checklist itself versioning",
        "intent": "meta-loop closed: changes to checklist run through the checklist",
    },

    # Codex round v0.2.0-r9 (semver introduction)
    "version-file-exists": {
        "file": "VERSION",
        "pattern": r"^\d+\.\d+\.\d+",
        "intent": "single source of truth for skill version",
    },
    "changelog-keep-format": {
        "file": "CHANGELOG.md",
        "pattern": r"Keep a Changelog",
        "intent": "CHANGELOG follows a documented format",
    },
    "lessons-changelog-bridge": {
        "file": "allincms-content-ops/SKILL.md",
        "pattern": r"Lessons → CHANGELOG bridge",
        "intent": "step 0 must write CHANGELOG entry on lesson merge",
    },
    "update-skill-semver-aware": {
        "file": "allincms-content-ops/scripts/update_skill.py",
        "pattern": r"def parse_semver",
        "intent": "update_skill compares versions, not just commit counts",
    },
    "update-skill-major-ack": {
        "file": "allincms-content-ops/scripts/update_skill.py",
        "pattern": r"--ack-major",
        "intent": "MAJOR cross requires explicit ack flag",
    },
    "update-skill-pin-file": {
        "file": "allincms-content-ops/scripts/update_skill.py",
        "pattern": r"\.allincms-skill-pin",
        "intent": "pin file honored to silence upgrade nudges",
    },
    "update-skill-shallow-handling": {
        "file": "allincms-content-ops/scripts/update_skill.py",
        "pattern": r"is_shallow",
        "intent": "shallow clone unshallow fallback",
    },

    # Codex round v0.2.0-r8 (update_skill design)
    "first-contact-phase-minus-one": {
        "file": "allincms-content-ops/references/first-contact.md",
        "pattern": r"Phase -1: Skill sync",
        "intent": "freshness check runs BEFORE Phase 1 (not collide with SKILL step 0)",
    },
    "first-contact-mid-session-ban": {
        "file": "allincms-content-ops/references/first-contact.md",
        "pattern": r"Mid-session ban",
        "intent": "update_skill must not run outside Phase -1",
    },
    "first-contact-zip-fallback": {
        "file": "allincms-content-ops/references/first-contact.md",
        "pattern": r"zip 装的",
        "intent": "no-git users get a downgrade path",
    },
    "first-contact-changed-contracts-reread": {
        "file": "allincms-content-ops/references/first-contact.md",
        "pattern": r"actually Re-Read",
        "intent": "after pulling new contracts, AI must re-read",
    },
    "skill-step-0-reread-on-pull": {
        "file": "allincms-content-ops/SKILL.md",
        "pattern": r"CHANGED-CONTRACT-FILES",
        "intent": "step 0 acknowledges Phase -1's pull",
    },
    "update-skill-emit-changed-contracts": {
        "file": "allincms-content-ops/scripts/update_skill.py",
        "pattern": r"CHANGED-CONTRACT-FILES",
        "intent": "update_skill emits the re-read manifest",
    },

    # Codex round v0.2.0-r7 (first-contact v3)
    "first-contact-sentinel": {
        "file": "allincms-content-ops/scripts/init_content_ops_project.py",
        "pattern": r"<!-- first-contact: unfilled -->",
        "intent": "Phase 1 detection sentinel seeded by init",
    },
    "first-contact-path-a-prime": {
        "file": "allincms-content-ops/references/first-contact.md",
        "pattern": r"Path A′",
        "intent": "AI-bootstrapped wiki/company.md cannot be paraphrased as ground truth",
    },
    "first-contact-token-bind": {
        "file": "allincms-content-ops/references/first-contact.md",
        "pattern": r"Token-bind self-check",
        "intent": "Phase 3 scenarios must reference user-supplied tokens",
    },
    "first-contact-fetch-consent": {
        "file": "allincms-content-ops/references/first-contact.md",
        "pattern": r"Wait for explicit consent",
        "intent": "Path B fetch needs user OK; silence is not consent",
    },
    "first-contact-min-signal-gate": {
        "file": "allincms-content-ops/references/first-contact.md",
        "pattern": r"Minimum signal gate",
        "intent": "SPA / Cloudflare cases refuse to draft from low-signal fetch",
    },
    "library-health-ai-drafted-check": {
        "file": "allincms-content-ops/scripts/library_health.py",
        "pattern": r"check_ai_drafted_unreviewed",
        "intent": "needs_human_review flag actually enforced",
    },
    "corpus-ai-drafted-schema": {
        "file": "allincms-content-ops/references/corpus-layout.md",
        "pattern": r"AI-drafted wiki pages",
        "intent": "schema for trust / needs_human_review fields documented",
    },
    "skill-current-site-tiered": {
        "file": "allincms-content-ops/SKILL.md",
        "pattern": r"Not gated on Current Site",
        "intent": "STOP gate is tiered — light/read is exempt",
    },
}


def find_project_root(start):
    p = Path(start).expanduser().resolve()
    for parent in [p, *p.parents]:
        if (parent / "VERSION").exists() or (parent / "PROJECT_INDEX.md").exists():
            return parent
    return None


def run_check(name, spec, project_root):
    target = project_root / spec["file"]
    if not target.is_file():
        return False, f"file missing: {spec['file']}"
    text = target.read_text(encoding="utf-8", errors="ignore")
    if not re.search(spec["pattern"], text, re.M | re.I):
        return False, f"pattern absent in {spec['file']}: /{spec['pattern']}/  ({spec['intent']})"
    return True, None


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="append", help="run one check by slug (repeatable); omit to run all")
    parser.add_argument("--list", action="store_true", help="list all check slugs and exit")
    parser.add_argument("--project-root", default=".", help="project root (default .)")
    args = parser.parse_args()

    if args.list:
        for name in sorted(CHECKS):
            print(name)
        return 0

    project_root = find_project_root(args.project_root) or Path(args.project_root).expanduser().resolve()
    to_run = args.check or sorted(CHECKS)
    bad = 0
    for name in to_run:
        if name not in CHECKS:
            print(f"unknown check: {name}", file=sys.stderr)
            bad += 1
            continue
        ok, err = run_check(name, CHECKS[name], project_root)
        if not ok:
            print(f"FAIL  {name}: {err}", file=sys.stderr)
            bad += 1

    total = len(to_run)
    if bad:
        print(f"\n{bad}/{total} skill-meta check(s) failed", file=sys.stderr)
        return 1
    print(f"{total}/{total} skill-meta checks pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
