#!/usr/bin/env python3
import argparse
import datetime as _dt
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import JsonlLogger, shared_writer_lock  # noqa: E402


RISK_TERMS = [
    "Free shipping",
    "Shop new arrivals",
    "Weekender Tote",
    "New season arrivals",
    "Everyday essentials",
    "WHY CUSTOMERS COME BACK",
    "Newsletter",
    "Subscribe",
    "Lin Mei",
    "Ahmed Hassan",
    "Carlos Ruiz",
    "Li Mei",
    "20+ countries",
    "images.unsplash.com",
    "coming soon",
    "Lorem ipsum",
    "Shop materials",
    "SHIPPING / RETURNS",
]

AI_SMELL = [
    "in today's fast-paced",
    "seamless experience",
    "cutting-edge",
    "robust solution",
    "revolutionize",
    "game-changer",
    "unlock the power",
    "delve into",
    "ever-evolving landscape",
    "navigate the complexities",
    "in the realm of",
    "leverage synergies",
    "at the end of the day",
    "it's important to note",
    "in conclusion",
    "tapestry of",
    "embark on a journey",
    "harness the power",
    "transformative",
    "paradigm shift",
]

REQUIRED_FRONTMATTER = [
    "title",
    "slug",
    "route",
    "content_type",
    "status",
    "persona",
    "region",
    "search_intent",
    "primary_query",
    "category",
    "tags",
    "meta_title",
    "meta_description",
    "cover_image",
    "cover_alt",
    "differentiation",
    "credibility_evidence",
    "published_at",
    "updated_at",
    "author",
]

# Meta length ranges (Google's commonly accepted SERP window)
META_TITLE_MIN, META_TITLE_MAX = 35, 65
META_DESC_MIN, META_DESC_MAX = 120, 165

WEB_CONTENT_DIRS = {"drafts", "pages", "posts", "products"}


def has_frontmatter(text):
    return text.startswith("---\n") and "\n---" in text[4:]


def parse_frontmatter(text):
    """Tiny YAML subset parser. Supports top-level scalars and multi-line lists.

    Recognised list forms:
      key: [a, b]          → ["a", "b"]
      key:
        - a
        - b               → ["a", "b"]
    """
    if not has_frontmatter(text):
        return {}
    end = text.find("\n---", 4)
    raw = text[4:end]
    data = {}
    last_key = None
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        # multi-line list item under last_key
        if line.startswith(("  - ", "- ")) and last_key is not None:
            item = stripped[2:].strip().strip('"').strip("'")
            cur = data.get(last_key)
            if isinstance(cur, list):
                cur.append(item)
            elif cur in (None, ""):
                data[last_key] = [item]
            else:
                data[last_key] = [cur, item]
            continue
        if ":" in line and not line.startswith(" "):
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            # strip inline YAML comments (unquoted "  # ...")
            if " #" in value and not (value.startswith('"') or value.startswith("'")):
                value = value.split(" #", 1)[0].rstrip()
            data[key] = value
            last_key = key
        else:
            last_key = None
    return data


def is_web_content_file(path):
    parts = set(path.as_posix().split("/"))
    return path.name.lower() != "index.md" and "web" in parts and bool(parts & WEB_CONTENT_DIRS)


def audit_file(path):
    text = path.read_text(encoding="utf-8", errors="ignore")
    lower = text.lower()
    issues = []
    fm = parse_frontmatter(text)
    is_web_content = path.suffix.lower() in {".md", ".mdx"} and is_web_content_file(path)
    if is_web_content:
        missing = [k for k in REQUIRED_FRONTMATTER if k not in fm or not str(fm.get(k, "")).strip()]
        if missing:
            issues.append(f"missing_frontmatter={','.join(missing)}")
        if not str(fm.get("source_wiki", "")).strip() and not str(fm.get("source_raw", "")).strip():
            issues.append("missing_source_trace=source_wiki_or_source_raw")
        # credibility_evidence: accept list (multi-line or inline) or single string
        cred_raw = fm.get("credibility_evidence", "")
        if isinstance(cred_raw, list):
            refs = [str(r).strip() for r in cred_raw if str(r).strip()]
        else:
            s = str(cred_raw).strip()
            if s.startswith("[") and s.endswith("]"):
                refs = [r.strip().strip("\"'") for r in s[1:-1].split(",") if r.strip()]
            elif s:
                refs = [s]
            else:
                refs = []
        if not refs:
            issues.append("missing_credibility_evidence")
        else:
            base_dir = path.parent
            project_root_hint = None
            for parent in [base_dir, *base_dir.parents]:
                if (parent / "PROJECT_INDEX.md").exists():
                    project_root_hint = parent
                    break
            root = (project_root_hint or base_dir).resolve()
            bad_refs = []
            for ref in refs:
                if Path(ref).is_absolute() or ".." in Path(ref).parts:
                    issues.append(f"unsafe_credibility_path={ref}")
                    continue
                candidate = (root / ref).resolve()
                try:
                    candidate.relative_to(root)
                except ValueError:
                    issues.append(f"unsafe_credibility_path={ref}")
                    continue
                if not candidate.exists():
                    bad_refs.append(ref)
            if bad_refs:
                issues.append(f"missing_credibility_artifact={','.join(bad_refs)}")
        # meta length checks
        mt = str(fm.get("meta_title", "")).strip()
        if mt and not (META_TITLE_MIN <= len(mt) <= META_TITLE_MAX):
            issues.append(f"meta_title_length={len(mt)}_out_of_{META_TITLE_MIN}-{META_TITLE_MAX}")
        md = str(fm.get("meta_description", "")).strip()
        if md and not (META_DESC_MIN <= len(md) <= META_DESC_MAX):
            issues.append(f"meta_description_length={len(md)}_out_of_{META_DESC_MIN}-{META_DESC_MAX}")
    if is_web_content:
        for term in RISK_TERMS:
            if term.lower() in lower:
                issues.append(f"risk_term={term}")
        for term in AI_SMELL:
            if term in lower:
                issues.append(f"ai_smell={term}")
    words = re.findall(r"[\w'-]+", text)
    if is_web_content:
        if len(words) < 350:
            issues.append(f"too_short_words={len(words)}")
        if len(words) > 3500:
            issues.append(f"too_long_words={len(words)}")
    if is_web_content and re.search(r"!\[[^\]]*\]\(([^)]+)\)", text):
        for alt, src in re.findall(r"!\[([^\]]*)\]\(([^)]+)\)", text):
            if not alt.strip():
                issues.append(f"missing_image_alt={src}")
            if re.search(r"/(image|pic|img|1|2|3)\.(png|jpe?g|webp|gif)$", src, re.I):
                issues.append(f"generic_image_filename={src}")
    return issues


LIGHT_SKIP = {
    "missing_frontmatter",
    "missing_source_trace",
    "too_short_words",
    "too_long_words",
    "missing_differentiation",
    "broken_backlink",
    "missing_credibility_evidence",
    "missing_credibility_artifact",
    "meta_title_length",
    "meta_description_length",
}


def filter_light(issues):
    kept = []
    for issue in issues:
        head = issue.split("=", 1)[0]
        if head in LIGHT_SKIP:
            continue
        kept.append(issue)
    return kept


def check_raw_immutable(root):
    """Flag raw/** files whose mtime > frontmatter.collected_at."""
    issues = []
    raw_dir = root / "raw"
    if not raw_dir.is_dir():
        return issues
    for path in raw_dir.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".md", ".mdx"}:
            continue
        if path.name.lower() == "index.md":
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        fm = parse_frontmatter(text)
        collected = fm.get("collected_at", "").strip()
        if not collected:
            continue
        try:
            collected_d = _dt.date.fromisoformat(collected[:10])
        except ValueError:
            continue
        mtime_d = _dt.date.fromtimestamp(path.stat().st_mtime)
        if mtime_d > collected_d:
            rel = path.relative_to(root)
            issues.append(f"raw_mutated={rel} mtime={mtime_d} collected_at={collected_d}")
    return issues


def check_wiki_backlinks(root):
    """For each web draft's source_wiki entries, verify the wiki page's consumed_by lists this draft."""
    issues = []
    web_dir = root / "web"
    wiki_dir = root / "wiki"
    if not (web_dir.is_dir() and wiki_dir.is_dir()):
        return issues
    for draft in web_dir.rglob("*.md"):
        if draft.name.lower() == "index.md":
            continue
        if not is_web_content_file(draft):
            continue
        text = draft.read_text(encoding="utf-8", errors="ignore")
        # crude source_wiki list extraction (one-line YAML list form)
        m = re.search(r"^source_wiki:\s*\[([^\]]*)\]", text, re.M)
        if not m:
            continue
        refs = [r.strip().strip("\"'") for r in m.group(1).split(",") if r.strip()]
        draft_rel = draft.relative_to(root).as_posix()
        for ref in refs:
            wiki_path = (root / ref).resolve() if not Path(ref).is_absolute() else Path(ref)
            if not wiki_path.exists():
                issues.append(f"broken_backlink={draft_rel} -> {ref} (wiki missing)")
                continue
            wiki_text = wiki_path.read_text(encoding="utf-8", errors="ignore")
            if draft_rel not in wiki_text:
                issues.append(f"broken_backlink={draft_rel} not in {ref} consumed_by")
    return issues


def main():
    parser = argparse.ArgumentParser(description="Audit AllinCMS content ops files.")
    parser.add_argument("target", help="project root, directory, or individual Markdown/text file")
    parser.add_argument("--light", action="store_true", help="light-mode: skip frontmatter/length/source-trace/backlink checks; keep residue + AI smell + image gates")
    parser.add_argument("--check-raw-immutable", action="store_true", help="scan raw/** for files mutated after collected_at")
    parser.add_argument("--check-backlinks", action="store_true", help="verify wiki consumed_by reciprocity for each web source_wiki reference")
    parser.add_argument("--require-audit-file", metavar="SLUG", help="exit non-zero unless audits/<SLUG>-*.md has a top-level `pass: true` line")
    parser.add_argument("--check-lessons-drain", action="store_true", help="flag wiki/lessons.md entries stuck in `status: approved` > N days")
    parser.add_argument("--lessons-drain-days", type=int, default=14, help="threshold for --check-lessons-drain (default 14)")
    parser.add_argument("--log", action="store_true", help="write structured JSONL log to logs/audit_content-<date>.jsonl")
    parser.add_argument("--status", action="store_true", help="one-stop dashboard: lessons / backlog / audits / sitemap-diff freshness; ignores other flags")
    args = parser.parse_args()
    root = Path(args.target).expanduser().resolve()

    if args.status:
        project_root = root if root.is_dir() else root.parent
        while project_root != project_root.parent and not (project_root / "PROJECT_INDEX.md").exists():
            project_root = project_root.parent
        print_status(project_root)
        return

    if root.is_file():
        targets = [root] if root.suffix.lower() in {".md", ".mdx", ".txt"} else []
        base = root.parent
        project_root = root.parent
        while project_root != project_root.parent and not (project_root / "PROJECT_INDEX.md").exists():
            project_root = project_root.parent
    else:
        base = root
        project_root = root
        targets = [
            p for p in root.rglob("*")
            if p.is_file()
            and p.suffix.lower() in {".md", ".mdx", ".txt"}
            and ".git" not in p.parts
            and "node_modules" not in p.parts
        ]
    total_issues = 0
    for path in sorted(targets):
        issues = audit_file(path)
        if args.light:
            issues = filter_light(issues)
        if issues:
            total_issues += len(issues)
            rel = path.relative_to(base)
            print(f"{rel}")
            for issue in issues:
                print(f"  - {issue}")
    if args.check_raw_immutable and not args.light:
        for issue in check_raw_immutable(project_root):
            total_issues += 1
            print(f"raw_immutability: {issue}")
    if args.check_backlinks and not args.light:
        for issue in check_wiki_backlinks(project_root):
            total_issues += 1
            print(f"backlinks: {issue}")
    if args.require_audit_file:
        audits_dir = project_root / "audits"
        slug = args.require_audit_file
        matches = sorted(audits_dir.glob(f"{slug}-*.md")) if audits_dir.is_dir() else []
        passed = False
        pass_key_re = re.compile(r"^pass:\s*true\s*(#.*)?$")
        for m in matches:
            for line in m.read_text(encoding="utf-8", errors="ignore").splitlines():
                if pass_key_re.match(line.rstrip()):
                    passed = True
                    break
            if passed:
                break
        if not passed:
            total_issues += 1
            print(f"require_audit_file: no audits/{slug}-*.md with top-level `pass: true` line found")
    if args.check_lessons_drain:
        lessons = project_root / "wiki" / "lessons.md"
        if lessons.is_file():
            text = lessons.read_text(encoding="utf-8", errors="ignore")
            today = _dt.date.today()
            entry_re = re.compile(r"-\s*date:\s*(\d{4}-\d{2}-\d{2}).*?status:\s*approved", re.DOTALL)
            for m in entry_re.finditer(text):
                try:
                    d = _dt.date.fromisoformat(m.group(1))
                except ValueError:
                    continue
                if (today - d).days > args.lessons_drain_days:
                    total_issues += 1
                    print(f"lessons_drain: approved entry dated {d} sat > {args.lessons_drain_days} days unmerged")
    print(f"files={len(targets)} issues={total_issues} mode={'light' if args.light else 'full'}")
    logger = JsonlLogger("audit_content", project_root=project_root if args.log else None)
    logger.info("run_end", files=len(targets), issues=total_issues, mode="light" if args.light else "full")
    raise SystemExit(1 if total_issues else 0)


# ---------- status dashboard ----------


def _count_yaml_status(text, key):
    """Crude count of `status: <key>` occurrences in a YAML block."""
    return len(re.findall(rf"^\s*status:\s*{re.escape(key)}\s*$", text, re.M))


def _approved_drain(text, threshold_days=14):
    today = _dt.date.today()
    stale = 0
    for m in re.finditer(r"-\s*date:\s*(\d{4}-\d{2}-\d{2}).*?status:\s*approved", text, re.DOTALL):
        try:
            d = _dt.date.fromisoformat(m.group(1))
        except ValueError:
            continue
        if (today - d).days > threshold_days:
            stale += 1
    return stale


def print_status(project_root):
    print(f"# Content Ops Status — {project_root}")
    print(f"_generated {_dt.date.today().isoformat()}_")

    lessons = project_root / "wiki" / "lessons.md"
    if lessons.is_file():
        t = lessons.read_text(encoding="utf-8", errors="ignore")
        print("\n## wiki/lessons.md")
        print(f"- proposed:               {_count_yaml_status(t, 'proposed')}")
        print(f"- proposed_blocked_on_decision: {_count_yaml_status(t, 'proposed_blocked_on_decision')}")
        print(f"- approved (awaiting merge):    {_count_yaml_status(t, 'approved')}")
        print(f"- approved > 14d stale:         {_approved_drain(t)}")
        print(f"- merged:                  {_count_yaml_status(t, 'merged')}")
        print(f"- rejected:                {_count_yaml_status(t, 'rejected')}")
    else:
        print("\n## wiki/lessons.md  (missing)")

    backlog = project_root / "wiki" / "backlog.md"
    if backlog.is_file():
        t = backlog.read_text(encoding="utf-8", errors="ignore")
        print("\n## wiki/backlog.md")
        print(f"- open:    {_count_yaml_status(t, 'open')}")
        print(f"- doing:   {_count_yaml_status(t, 'doing')}")
        print(f"- done:    {_count_yaml_status(t, 'done')}")
        print(f"- dropped: {_count_yaml_status(t, 'dropped')}")
        # split entries on "- date:" boundaries and check priority+status within each
        entries = re.split(r"\n-\s+(?=date:)", "\n" + t)
        high_open = 0
        for entry in entries:
            if re.search(r"priority:\s*high", entry) and re.search(r"status:\s*(open|doing)\s*$", entry, re.M):
                high_open += 1
        print(f"- high-priority (not done/dropped): {high_open}")
    else:
        print("\n## wiki/backlog.md  (missing)")

    # SEO staleness: drafts/published whose last_seo_check is > 180 days
    web_dir = project_root / "web"
    if web_dir.is_dir():
        stale_seo = 0
        today = _dt.date.today()
        for p in web_dir.rglob("*.md"):
            if p.name.lower() == "index.md":
                continue
            text = p.read_text(encoding="utf-8", errors="ignore")
            m = re.search(r"^last_seo_check:\s*(\d{4}-\d{2}-\d{2})", text, re.M)
            if not m:
                continue
            try:
                d = _dt.date.fromisoformat(m.group(1))
            except ValueError:
                continue
            if (today - d).days > 180:
                stale_seo += 1
        if stale_seo:
            print(f"\n## web/  SEO-stale (last_seo_check > 180d): {stale_seo}")

    audits_dir = project_root / "audits"
    if audits_dir.is_dir():
        files = [p for p in audits_dir.glob("*.md") if p.name != "index.md"]
        passing = 0
        pass_re = re.compile(r"^pass:\s*true\s*(#.*)?$", re.M)
        for p in files:
            if pass_re.search(p.read_text(encoding="utf-8", errors="ignore")):
                passing += 1
        print("\n## audits/")
        print(f"- total audit files:  {len(files)}")
        print(f"- passing:            {passing}")
        print(f"- not passing / open: {len(files) - passing}")

    sitemap_runs = project_root / "monitoring" / "runs" / "sitemap"
    if sitemap_runs.is_dir():
        diffs = sorted(sitemap_runs.glob("diff-*.md"))
        if diffs:
            last = diffs[-1]
            age = (_dt.date.today() - _dt.date.fromisoformat(last.stem.split("-", 1)[1])).days
            print("\n## monitoring/sitemap")
            print(f"- last diff: {last.name} ({age} days ago)")
        else:
            print("\n## monitoring/sitemap  (no diff runs yet)")

    print("\n## next actions")
    print("- review `wiki/lessons.md` proposed → add `approved_by` + `approved_at` to graduate")
    print("- drain `approved > 14d` entries (run any agent — Workflow step 0 will merge)")
    print("- triage `wiki/backlog.md` high-priority")
    print("- if sitemap diff is stale > 7 days, re-run `scripts/sitemap_diff.py .`")


if __name__ == "__main__":
    main()
