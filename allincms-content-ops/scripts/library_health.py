#!/usr/bin/env python3
"""Internal-library health check — runs against the local knowledge base.

Complements:
  - `site_health_check.py` (live published front-end)
  - `audit_content.py` (per-draft frontmatter / residue / lengths)

This script looks at the **library itself**: are raw captures still cited,
are wiki pages drifting unread, are internal links dead, is the copy library
being overused, are glossary terms drifting?

Checks (each opt-in via flag; default = all):
  1. dead_links     — internal markdown links that don't resolve to a file
  2. orphan_raw     — raw/* captures with no wiki page citing them (> 30d old)
  3. stale_wiki     — wiki/* pages not edited > 90d AND `consumed_by` empty
  4. copy_overuse   — wiki/copy-library.md snippets reused in > N drafts
  5. glossary_drift — terms used in web/ drafts that don't appear in glossary
  6. seo_stale      — web/ pages with last_seo_check > 180d (already in --status)

Output: `audits/library-health-<date>.md` + appends `proposed` rows to
`wiki/backlog.md` for issues classified as actionable.
"""
import argparse
import datetime as _dt
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import JsonlLogger, shared_writer_lock  # noqa: E402


COPY_OVERUSE_THRESHOLD = 3
ORPHAN_RAW_DAYS = 30
STALE_WIKI_DAYS = 90
SEO_STALE_DAYS = 180


def find_project_root(start):
    p = Path(start).expanduser().resolve()
    for parent in [p, *p.parents]:
        if (parent / "PROJECT_INDEX.md").exists():
            return parent
    return None


def iter_markdown(root):
    if not root.is_dir():
        return
    for p in root.rglob("*.md"):
        if ".git" in p.parts or "node_modules" in p.parts:
            continue
        # `_ai-drafts/` is the staging area where first-contact Phase 2.5
        # parks AI-bootstrapped wiki/products/<slug>.md and wiki/personas/<slug>.md
        # before the user promotes them. Library health treats those as
        # work-in-progress, not authoritative wiki content — skip them.
        if "_ai-drafts" in p.parts:
            continue
        yield p


# ----- check 1: dead internal links -----

LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def check_dead_links(project_root):
    issues = []
    for source_dir in ["raw", "wiki", "web", "allincms-content-ops/references", "docs"]:
        base = project_root / source_dir
        for md in iter_markdown(base):
            text = md.read_text(encoding="utf-8", errors="ignore")
            for url in LINK_RE.findall(text):
                # skip external / anchors / mailto
                if url.startswith(("http://", "https://", "#", "mailto:", "tel:")):
                    continue
                if url.startswith(("/Users/", "/")):
                    target = Path(url)
                else:
                    target = (md.parent / url.split("#", 1)[0]).resolve()
                if not target.exists():
                    issues.append({"check": "dead_link", "file": str(md.relative_to(project_root)), "link": url})
    return issues


# ----- check 2: orphan raw captures -----


def check_orphan_raw(project_root):
    issues = []
    raw = project_root / "raw"
    wiki = project_root / "wiki"
    if not (raw.is_dir() and wiki.is_dir()):
        return issues
    today = _dt.date.today()
    # build a "cited-from-wiki" set
    cited = set()
    for md in iter_markdown(wiki):
        text = md.read_text(encoding="utf-8", errors="ignore")
        for m in re.finditer(r"raw/[A-Za-z0-9_\-/.]+\.(?:md|pdf|png|jpg|jpeg)", text):
            cited.add(m.group(0))
    for p in raw.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in {".md", ".mdx"}:
            continue
        if p.name.lower() == "index.md":
            continue
        rel = p.relative_to(project_root).as_posix()
        if rel in cited:
            continue
        age = (today - _dt.date.fromtimestamp(p.stat().st_mtime)).days
        if age > ORPHAN_RAW_DAYS:
            issues.append({"check": "orphan_raw", "file": rel, "age_days": age})
    return issues


# ----- check 3: stale wiki -----


def check_stale_wiki(project_root):
    issues = []
    wiki = project_root / "wiki"
    if not wiki.is_dir():
        return issues
    today = _dt.date.today()
    for md in iter_markdown(wiki):
        if md.name.lower() in {"index.md", "lessons.md", "backlog.md", "glossary.md", "content-opportunities.md", "copy-library.md", "llm-knowledge-base.md"}:
            continue
        text = md.read_text(encoding="utf-8", errors="ignore")
        consumed = re.search(r"^consumed_by:\s*(.+)$", text, re.M)
        has_consumers = consumed and consumed.group(1).strip() not in ("", "[]")
        age = (today - _dt.date.fromtimestamp(md.stat().st_mtime)).days
        if age > STALE_WIKI_DAYS and not has_consumers:
            issues.append({
                "check": "stale_wiki",
                "file": str(md.relative_to(project_root)),
                "age_days": age,
                "consumed_by": "empty" if not consumed else "missing_field",
            })
    return issues


# ----- check 4: copy-library overuse -----


def check_copy_overuse(project_root):
    issues = []
    cl = project_root / "wiki" / "copy-library.md"
    web = project_root / "web"
    if not (cl.is_file() and web.is_dir()):
        return issues
    text = cl.read_text(encoding="utf-8", errors="ignore")
    # snippets live under `copy: "..."` lines
    snippets = re.findall(r"copy:\s*[\"']([^\"'\n]{8,})[\"']", text)
    if not snippets:
        return issues
    # build a corpus of web bodies
    bodies = []
    for md in iter_markdown(web):
        if md.name.lower() == "index.md":
            continue
        bodies.append((md, md.read_text(encoding="utf-8", errors="ignore")))
    for s in snippets:
        hits = [str(m.relative_to(project_root)) for m, body in bodies if s in body]
        if len(hits) > COPY_OVERUSE_THRESHOLD:
            issues.append({"check": "copy_overuse", "snippet": s[:60], "uses": len(hits), "files": hits[:5]})
    return issues


# ----- check 5: glossary drift -----


def _glossary_terms(project_root):
    g = project_root / "wiki" / "glossary.md"
    if not g.is_file():
        return set()
    text = g.read_text(encoding="utf-8", errors="ignore")
    terms = set()
    # table rows beginning "| <term> |"
    for line in text.splitlines():
        m = re.match(r"\|\s*([A-Za-z][\w\-/ ]{2,40})\s*\|", line)
        if m:
            term = m.group(1).strip()
            if term.lower() not in {"term (canonical en)", "term", "english (canonical)"}:
                terms.add(term)
    # also pick up bullet-list entries: - **term**: …
    for m in re.finditer(r"^\s*-\s*\*\*([^*]{3,40})\*\*", text, re.M):
        terms.add(m.group(1).strip())
    return terms


SUSPECT_JARGON = re.compile(r"\b(GEO|AEO|E-E-A-T|fan-out|persona|hreflang|canonical|consumed_by|residue|differentiation)\b", re.I)


def check_glossary_drift(project_root):
    issues = []
    terms_lower = {t.lower() for t in _glossary_terms(project_root)}
    web = project_root / "web"
    if not web.is_dir():
        return issues
    used = {}
    for md in iter_markdown(web):
        if md.name.lower() == "index.md":
            continue
        text = md.read_text(encoding="utf-8", errors="ignore")
        for m in SUSPECT_JARGON.finditer(text):
            term = m.group(1)
            used.setdefault(term.lower(), []).append(str(md.relative_to(project_root)))
    for term_lower, files in used.items():
        if term_lower not in terms_lower:
            issues.append({"check": "glossary_drift", "term": term_lower, "files": sorted(set(files))[:5]})
    return issues


# ----- check 6: SEO stale (mirror of audit_content.py --status logic) -----


def check_seo_stale(project_root):
    issues = []
    web = project_root / "web"
    if not web.is_dir():
        return issues
    today = _dt.date.today()
    for md in iter_markdown(web):
        if md.name.lower() == "index.md":
            continue
        text = md.read_text(encoding="utf-8", errors="ignore")
        m = re.search(r"^last_seo_check:\s*(\d{4}-\d{2}-\d{2})", text, re.M)
        if not m:
            continue
        try:
            d = _dt.date.fromisoformat(m.group(1))
        except ValueError:
            continue
        age = (today - d).days
        if age > SEO_STALE_DAYS:
            issues.append({"check": "seo_stale", "file": str(md.relative_to(project_root)), "age_days": age})
    return issues


def check_ai_drafted_unreviewed(project_root):
    """Flag wiki pages with frontmatter `trust: ai-drafted` + `needs_human_review: true`.

    Created by `first-contact.md` Phase 2 when AI bootstraps `wiki/company.md`
    (or similar) from a user's 3-line answer / fetched homepage. The flag means
    "human still needs to read this once" — surface in dashboards so it doesn't
    rot into pseudo-ground-truth.
    """
    issues = []
    wiki = project_root / "wiki"
    if not wiki.is_dir():
        return issues
    today = _dt.date.today()
    for md in iter_markdown(wiki):
        text = md.read_text(encoding="utf-8", errors="ignore")
        if not re.search(r"^trust:\s*ai-drafted", text, re.M):
            continue
        if not re.search(r"^needs_human_review:\s*true", text, re.M):
            continue
        age = (today - _dt.date.fromtimestamp(md.stat().st_mtime)).days
        issues.append({
            "check": "ai_drafted_unreviewed",
            "file": str(md.relative_to(project_root)),
            "age_days": age,
        })
    return issues


CHECKS = {
    "dead_links": check_dead_links,
    "orphan_raw": check_orphan_raw,
    "stale_wiki": check_stale_wiki,
    "copy_overuse": check_copy_overuse,
    "glossary_drift": check_glossary_drift,
    "seo_stale": check_seo_stale,
    "ai_drafted_unreviewed": check_ai_drafted_unreviewed,
}


def write_report(project_root, issues_by_check):
    today = _dt.date.today().isoformat()
    report = project_root / "audits" / f"library-health-{today}.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"# Library health {today}", ""]
    total = 0
    for check, issues in issues_by_check.items():
        lines.append(f"## {check}  ({len(issues)})")
        total += len(issues)
        for i in issues[:50]:
            lines.append(f"- {i}")
        if len(issues) > 50:
            lines.append(f"- … (+{len(issues) - 50} more)")
        lines.append("")
    lines.append(f"_total issues: {total}_")
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report, total


def append_backlog(project_root, total, report_path, today):
    if total == 0:
        return
    backlog = project_root / "wiki" / "backlog.md"
    if not backlog.is_file():
        return
    SENTINEL = "<!-- entries-end -->"
    note = f"library_health found {total} issue(s) — see {report_path.relative_to(project_root)}"
    entry = f"""
- date: {today}
  trigger: todo
  note: "{note}"
  context: "auto-appended by scripts/library_health.py"
  priority: med
  status: open
"""
    with shared_writer_lock(project_root, "backlog"):
        text = backlog.read_text(encoding="utf-8")
        if SENTINEL in text:
            text = text.replace(SENTINEL, entry.rstrip() + "\n\n" + SENTINEL, 1)
        else:
            text = text.rstrip() + "\n" + entry
        backlog.write_text(text, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("project_root", nargs="?", default=".")
    parser.add_argument("--only", action="append", choices=list(CHECKS), help="run only specified check(s); repeatable")
    parser.add_argument("--no-backlog", action="store_true")
    parser.add_argument("--log", action="store_true")
    args = parser.parse_args()

    project_root = find_project_root(args.project_root) or Path(args.project_root).expanduser().resolve()
    logger = JsonlLogger("library_health", project_root=project_root if args.log else None)
    to_run = args.only or list(CHECKS)
    issues_by_check = {name: CHECKS[name](project_root) for name in to_run}
    report, total = write_report(project_root, issues_by_check)
    print(f"report={report}")
    print(f"total_issues={total}")
    if not args.no_backlog:
        append_backlog(project_root, total, report, _dt.date.today().isoformat())
    logger.info("run_end", total=total, report=str(report), checks=list(to_run))
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main())
