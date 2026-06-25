#!/usr/bin/env python3
"""Initialize an AllinCMS content ops project.

All five Current Site flags are REQUIRED. The Hard Gate in SKILL.md refuses
to proceed if any of these is empty in PROJECT_INDEX.md, so we collect them
up front instead of writing placeholders.
"""
import argparse
from pathlib import Path


AGENT_ENTRY_COMMON = """# {tool} Entry

Authoritative rules: `allincms-content-ops/SKILL.md`. Do not restate or fork rules here.

Before any action:
1. Mode-select per SKILL.md → **Mode Selection** (light vs full).
2. STOP if `PROJECT_INDEX.md` → **Current Site** has any empty field. Request values; never proceed with placeholders.
3. Run Workflow step 0 (sweep `wiki/lessons.md` for `status: approved` and merge).

Full-mode publish gates: see SKILL.md → **Hard Gates**. Light-mode runbook: see SKILL.md → **Mode Selection**.
"""


def render_project_index(site_id, frontend_domain, workspace_url, browser_profile, default_region, default_content_language):
    return f"""# Project Index

## Entry Points
- raw: `raw/index.md`
- wiki: `wiki/index.md`
- wiki lessons: `wiki/lessons.md`
- web: `web/index.md`
- published: `web/published/index.md`
- categories: `web/categories/index.md`
- tags: `web/tags/index.md`
- monitoring: `monitoring/index.md`
- media: `media/index.md`
- audits: `audits/index.md`

## Current Site

> **Hard prerequisite.** If any field below is empty, STOP and request values from the user before any other action. Do not proceed with placeholders.

- AllinCMS site id: {site_id}
- Front-end domain: {frontend_domain}
- Workspace URL: {workspace_url}
- Browser profile: {browser_profile}
- Default content language: {default_region}

> `Default content language` is site-wide (drives `new_draft.py` body template + `site_health.py` `<html lang>` check). Per-draft `region:` lives in each draft's frontmatter — different axis, not overridden.
- Default content language: {default_content_language}

## Operating Rule

Mode-select first (light vs full per SKILL.md). Full-mode: ingest → wiki → search intent → web draft → media → AllinCMS draft → adversarial audit (isolated subagent) → publish gated by `audits/<slug>-<date>.md` `pass: true` → index → reflect to `wiki/lessons.md`.

Pass criteria: total ≥ 8.5 AND every area ≥ 70% AND zero blocking-residue AND ≥ 5 logged objections with responses.
"""


FILES = {
    "raw/index.md": "# Raw Index\n\n| Date | Source | Type | Rights | Extracted | Wiki links | Notes |\n|---|---|---|---|---|---|---|\n",
    "raw/competitors/index.md": "# Competitor Raw Index\n\n| Date | Competitor | URL | Change | Topic | Status | Wiki link |\n|---|---|---|---|---|---|---|\n",
    "wiki/index.md": "# Wiki Index\n\n- [Company](company.md)\n- [Glossary](glossary.md)\n- [Lessons](lessons.md) — durable rules (proposed → approved → merged)\n- [Backlog](backlog.md) — TODOs / ideas / questions (no graduation, just pruning)\n- [Copy Library](copy-library.md) — reusable proven snippets (audit-passed only)\n- [Content Opportunities](content-opportunities.md)\n- [LLM Knowledge Base](llm-knowledge-base.md)\n- Search-intent briefs: `briefs/`\n- Products: `products/`\n- Personas: `personas/`\n- Methodology: `methodology/`\n- Competitors: `competitors/`\n- Regions: `regions/`\n",
    "wiki/company.md": "<!-- first-contact: unfilled -->\n# Company\n\n## Positioning\n\n## Proof\n\n## Open Questions\n",
    "wiki/glossary.md": "# Glossary\n\n| Term (canonical EN) | 中文 | Definition | Preferred usage |\n|---|---|---|---|\n",
    "wiki/copy-library.md": """# Copy Library

Reusable proven copy snippets. Entries land here only after a `pass: true` audit OR distilled competitor copy marked `do_not_overuse: true`.

See `allincms-content-ops/references/content-system-tables.md` §4 for the contract.

```yaml
# - type: title | hook | h2 | cta | objection_handler | meta_description
#   copy: ""
#   language: en | zh-CN
#   works_for: []          # persona slugs
#   evidence: ""           # link to the published page where it performed (open rate, time on page, conversion)
#   do_not_overuse: false
#   source: "internal: <published-slug>" | "competitor: distilled from <url>"
```
""",
    "wiki/backlog.md": """# Backlog

Open TODOs, ideas, things to try, external reads, unblocked-but-deprioritized work, questions to verify. See `allincms-content-ops/references/routing-matrix.md` → "What goes in lessons.md vs backlog.md".

Entries do NOT graduate into the skill (that's `lessons.md`'s job). Prune periodically.

```yaml
- date: YYYY-MM-DD
  trigger: idea | todo | question | external_read
  note: <one sentence>
  context: <why noted; link if external>
  priority: low | med | high
  status: open | doing | done | dropped
```

## Entries

<!-- entries-end -->
""",
    "wiki/lessons.md": """# Lessons

Run-time corrections, new scenarios, failed-audit patterns, and competitor angles surfaced during real work. Single channel for routing knowledge back into the skill — never edit SKILL.md or `allincms-content-ops/references/*` directly.

See `allincms-content-ops/references/llm-knowledge-base.md` → **Lessons File Contract** for the entry shape.

## Status legend

- `proposed`: surfaced this run, awaiting user review
- `approved`: user agreed (added `approved_by` + `approved_at`); awaiting merge by next agent
- `merged`: applied into destination file (link the commit / diff via `merge_note`)
- `rejected`: declined; one-line reason preserved as anti-pattern memory

## How approval works (so future-you doesn't stall)

- User approval = adding `approved_by: <name>` and `approved_at: <date>` to the entry, OR a one-line confirmation referencing the entry's date + first 40 chars of the rule.
- Once approved, the NEXT agent run (any mode) executes Workflow step 0 (lessons sweep) and merges. No human action needed after approval.
- If an approved entry sits > 14 days, `audit_content.py --check-lessons-drain` flags it; that's the signal to manually drain.

## Entries

""",
    "wiki/content-opportunities.md": "# Content Opportunities\n\n| Status | Topic | Persona | Intent | Source | Proposed route | Notes |\n|---|---|---|---|---|---|---|\n",
    "wiki/llm-knowledge-base.md": "# Project LLM Notes\n\n## Durable Rules\n\n## Source Truth\n\n## Open Questions\n",
    "web/index.md": "# Web Index\n\n- Drafts: `drafts/`\n- Pages: `pages/`\n- Posts: `posts/`\n- Products: `products/`\n- Categories: `categories/index.md`\n- Tags: `tags/index.md`\n- Published: `published/index.md`\n",
    "web/categories/index.md": "# Category Index\n\n| Category | Intent | Routes | Notes |\n|---|---|---|---|\n",
    "web/tags/index.md": "# Tag Index\n\n| Tag | Intent | Routes | Notes |\n|---|---|---|---|\n",
    "web/published/index.md": "# Published Index\n\n| Date | URL | Type | Category | Tags | Persona | Primary query | Cover | Audit score | Source draft |\n|---|---|---|---|---|---|---|---|---|---|\n",
    "monitoring/index.md": "# Monitoring Index\n\n| Date | Competitor | Run path | New topics | User decision |\n|---|---|---|---|---|\n",
    "monitoring/competitors.yml": "competitors: []\n",
    "media/index.md": "# Media Index\n\n| Source | Processed file | Uploaded URL | Alt | Used in |\n|---|---|---|---|---|\n",
    "audits/index.md": "# Audit Index\n\n| Date | Slug | Reviewer subagent | Score | Pass | Audit file | Source draft |\n|---|---|---|---|---|---|---|\n",
    "AGENTS.md": AGENT_ENTRY_COMMON.format(tool="Agent"),
    "CLAUDE.md": AGENT_ENTRY_COMMON.format(tool="Claude"),
    "WORKBUDDY.md": AGENT_ENTRY_COMMON.format(tool="WorkBuddy"),
}


DIRS = [
    "raw/competitors",
    "wiki/products",
    "wiki/personas",
    "wiki/methodology",
    "wiki/competitors",
    "wiki/regions",
    "wiki/briefs",
    "web/drafts",
    "web/pages",
    "web/posts",
    "web/products",
    "web/categories",
    "web/tags",
    "web/published",
    "monitoring/runs",
    "monitoring/runs/sitemap",
    "monitoring/sites",
    "monitoring/daily",
    "media/source",
    "media/processed",
    "media/uploaded",
    "audits",
    "logs",
    ".locks",
]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("project_root")
    parser.add_argument("--site-id", required=True, help="AllinCMS site id")
    parser.add_argument("--front-end-domain", required=True, help="published front-end domain, e.g. example.com")
    parser.add_argument("--workspace-url", required=True, help="AllinCMS workspace URL, e.g. https://workspace.laicms.com")
    parser.add_argument("--browser-profile", required=True, help="which logged-in browser profile to drive (e.g. Default, Profile 2)")
    parser.add_argument("--default-region", required=True, help="default region / language for site operation, e.g. en-US, zh-CN")
    parser.add_argument("--default-content-language", default="zh-CN", help="default language for new web drafts (default zh-CN). Pick from en-US, zh-CN, ja-JP, de-DE, etc.")
    parser.add_argument("--force", action="store_true", help="overwrite existing files")
    args = parser.parse_args()
    root = Path(args.project_root).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    for d in DIRS:
        (root / d).mkdir(parents=True, exist_ok=True)

    files = dict(FILES)
    files["PROJECT_INDEX.md"] = render_project_index(
        site_id=args.site_id,
        frontend_domain=args.front_end_domain,
        workspace_url=args.workspace_url,
        browser_profile=args.browser_profile,
        default_region=args.default_region,
        default_content_language=args.default_content_language,
    )

    # self-check: PROJECT_INDEX must have exactly one `Default content language:` line
    pi = files["PROJECT_INDEX.md"]
    dup = sum(1 for line in pi.splitlines() if line.startswith("- Default content language:"))
    if dup != 1:
        raise RuntimeError(f"init template bug: PROJECT_INDEX.md has {dup} 'Default content language:' lines (expected 1)")

    written = []
    skipped = []
    for rel, content in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and not args.force:
            skipped.append(rel)
            continue
        path.write_text(content, encoding="utf-8")
        written.append(rel)
    print(f"root={root}")
    print(f"written={len(written)} skipped={len(skipped)}")
    if written:
        print("written_files:")
        for item in written:
            print(f"- {item}")
    if skipped:
        print("skipped_existing:")
        for item in skipped:
            print(f"- {item}")


if __name__ == "__main__":
    main()
