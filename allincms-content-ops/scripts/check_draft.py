#!/usr/bin/env python3
"""Teach the newbie how to fill a draft's missing fields.

Unlike `audit_content.py` (which blocks publish on contract violations),
this script never modifies anything and never returns non-zero for a
"failing" draft — it only prints, for each missing or weak field, a
one-line suggestion of what to put there and **why it matters**.

The point: a newbie staring at a 20-field frontmatter doesn't know
which 5 fields are make-or-break and what good fills look like. This
script tells them, draft by draft, in their own language.

This is teaching mode. Publish gates remain unchanged.
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
try:
    from audit_content import parse_frontmatter, REQUIRED_FRONTMATTER, META_TITLE_MIN, META_TITLE_MAX, META_DESC_MIN, META_DESC_MAX  # noqa: E402
except ImportError:
    # Allow standalone execution
    REQUIRED_FRONTMATTER = []
    META_TITLE_MIN = META_TITLE_MAX = META_DESC_MIN = META_DESC_MAX = 0
    def parse_frontmatter(text):
        return {}


# Per-field teaching: (field_name, importance, what-to-write, why-it-matters)
GUIDANCE = {
    "title":             ("required", "Reader-facing one-liner under 70 chars. Specific, contains the primary query naturally.", "Search snippet + browser tab + reader's first impression."),
    "slug":              ("required", "Kebab-case unique site-wide (e.g. `how-to-warm-up-domain`). No spaces, no Chinese in slug.", "Becomes part of the URL. Renaming later breaks links."),
    "route":             ("required", "Final URL path. Usually `/{category}/{slug}` (e.g. `/blog/how-to-warm-up-domain`).", "AllinCMS uses this to serve the page."),
    "content_type":      ("required", "One of: article | page | product | guide.", "Drives template selection in AllinCMS."),
    "status":            ("required", "Start as `draft`. Flip to `published` only after audit passes.", "Publish gate enforced by audit_content.py --require-audit-file."),
    "persona":           ("required", "Slug of a wiki/personas/<slug>.md page (e.g. `saas-founder`). If none exists, create one first.", "Sharpens search intent, voice, and credibility evidence selection."),
    "region":            ("required", "ISO-ish (e.g. `en-US`, `zh-CN`, `de-DE`). Match the language you're writing in.", "Drives hreflang + regional norms (currency, compliance) check."),
    "search_intent":     ("required", "ONE sentence: the job the reader is trying to get done. Not a keyword.", "Reviewer scores 'search intent fit' against this. Vague intent → low score."),
    "primary_query":     ("required", "Exact query the page targets (≤ 6 words). The first sentence of body must answer this.", "Used by suggest_internal_links + meta_title sanity."),
    "secondary_queries": ("required", "3–5 long-tail queries this page can also rank for, as a YAML list.", "Each becomes an H2 hook in the body."),
    "category":          ("required", "One AllinCMS category (must exist in CMS first).", "Drives breadcrumb + category index + internal links."),
    "tags":              ("required", "3–8 AllinCMS tags as YAML list. Reuse existing tags first; don't tag-spam.", "Powers tag indexes and suggest_internal_links scoring."),
    "meta_title":        ("required", f"{META_TITLE_MIN}–{META_TITLE_MAX} chars. Different from title — write for SERP click-through.", "Google truncates outside this range."),
    "meta_description":  ("required", f"{META_DESC_MIN}–{META_DESC_MAX} chars. Includes one specific number/proof.", "Google's snippet on results pages."),
    "cover_image":       ("required", "Path under media/uploaded/ OR full URL. Real screenshot or topic-specific generated visual.", "First viewport. No generic stock photo."),
    "cover_alt":         ("required", "≤ 125 chars. Describes the image AND the claim it supports.", "Accessibility + image SEO."),
    "differentiation":   ("required", "ONE sentence: how this page beats the strongest competitor URL you borrowed from.", "Reviewer Hard Gate. Empty → audit fails."),
    "credibility_evidence": ("required", "YAML list of paths (under raw/ or media/) to charts / customer screenshots / videos / comparison tables that EACH have a verifiable source.", "Reviewer Hard Gate. Empty → audit fails. Stock images get caught by reviewer."),
    "source_wiki":       ("required", "YAML list of paths to wiki/* pages this draft cites. Each wiki page's `consumed_by` must reciprocate.", "audit_content --check-backlinks catches one-way refs."),
    "source_raw":        ("required", "YAML list of paths to raw/* captures backing claims.", "Reviewer can audit you didn't make up facts."),
    "published_at":      ("required", "Leave empty until publish step flips it.", ""),
    "updated_at":        ("required", "Today's date (YYYY-MM-DD).", "library_health flags pages with last_seo_check > 180d."),
    "author":            ("required", "Human or team name. `git config user.name` is auto-injected by new_draft.py.", ""),
}

OPTIONAL_GUIDANCE = {
    "competitors_referenced": ("optional", "YAML list of competitor URLs whose angles informed this draft.", "Lets monitoring/captures cross-reference."),
    "related":          ("optional", "3–5 internal links to sibling articles.", "Improves time-on-site + SEO."),
    "source_external":  ("optional", "URL/PDF if heavily based on one external piece.", "Attribution + audit trail."),
    "last_seo_check":   ("optional", "Today's date. Bump on any meta/schema/canonical edit.", "library_health flags pages stale > 180d."),
}


def looks_unfilled(value):
    if value is None:
        return True
    s = str(value).strip()
    if not s or s in {"[]", '""', "''", "TODO", "__REPLACE_ME__"}:
        return True
    if "TODO" in s.upper():
        return True
    return False


def check_draft(path):
    text = path.read_text(encoding="utf-8", errors="ignore")
    fm = parse_frontmatter(text)
    missing = []
    weak = []
    placeholders = []

    for key, (importance, fill, why) in GUIDANCE.items():
        value = fm.get(key)
        if looks_unfilled(value):
            if "__REPLACE_ME__" in str(value or ""):
                placeholders.append((key, importance, fill, why))
            else:
                missing.append((key, importance, fill, why))

    # meta length checks (already filled but wrong length)
    mt = str(fm.get("meta_title", "")).strip()
    if mt and not looks_unfilled(mt) and not (META_TITLE_MIN <= len(mt) <= META_TITLE_MAX):
        weak.append(("meta_title", f"length {len(mt)} is outside {META_TITLE_MIN}-{META_TITLE_MAX}",
                     "Google SERP window."))
    md = str(fm.get("meta_description", "")).strip()
    if md and not looks_unfilled(md) and not (META_DESC_MIN <= len(md) <= META_DESC_MAX):
        weak.append(("meta_description", f"length {len(md)} is outside {META_DESC_MIN}-{META_DESC_MAX}",
                     "Google SERP window."))

    # body H1 check
    body_start = text.find("\n---", 4)
    if body_start != -1:
        body = text[body_start + 4:].lstrip()
        body = re.sub(r"^<!--.*?-->\s*", "", body, count=1, flags=re.S)
        if body.startswith("# "):
            weak.append(("body H1", "body starts with `# `; remove it — AllinCMS renders `title:` as the page H1",
                         "Duplicate H1 hurts SEO and confuses screen readers."))

    return missing, weak, placeholders


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("draft", help="path to draft .md (under web/drafts/ etc.)")
    args = parser.parse_args()

    path = Path(args.draft).expanduser().resolve()
    if not path.is_file():
        print(f"error: draft not found: {path}", file=sys.stderr)
        return 2

    print(f"# Draft coach — {path.name}\n")

    missing, weak, placeholders = check_draft(path)

    if placeholders:
        print(f"## __REPLACE_ME__ placeholders ({len(placeholders)})  STOP — these will block publish\n")
        for key, _, fill, why in placeholders:
            print(f"- `{key}` still has `__REPLACE_ME__`. {fill}")
            if why:
                print(f"   why: {why}")
        print()

    if missing:
        print(f"## Missing required fields ({len(missing)})\n")
        for key, importance, fill, why in missing:
            print(f"- `{key}` — {fill}")
            if why:
                print(f"   why: {why}")
        print()

    if weak:
        print(f"## Weak fields ({len(weak)})\n")
        for key, fill, why in weak:
            print(f"- `{key}`: {fill}")
            if why:
                print(f"   why: {why}")
        print()

    if not (missing or weak or placeholders):
        print("looks complete — run `audit_content.py {path}` for the real gate.".format(path=path))

    print("\nNext: when frontmatter is filled, run")
    print(f"   python3 allincms-content-ops/scripts/audit_content.py {path}")
    print("   python3 allincms-content-ops/scripts/suggest_internal_links.py", str(path))
    # never block — this is teaching mode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
