#!/usr/bin/env python3
"""Package adversarial-reviewer input.

Assembles `audits/<slug>-<date>-reviewer-input.yaml` containing exactly:
  - search_intent_brief (from the web draft's frontmatter)
  - preview_url or preview_html_path (from author-supplied flags)
  - competitor_urls (top 3 from monitoring/runs or --competitor flags)

The reviewer subagent is told to read ONLY this YAML. Everything else
(draft markdown, wiki sources, self-assessment) is excluded by design.
"""
import argparse
import datetime as _dt
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import JsonlLogger, shared_writer_lock  # noqa: E402


SEARCH_INTENT_KEYS = [
    "persona",
    "region",
    "primary_query",
    "secondary_queries",
    "funnel_stage",
    "conversion_goal",
    "objections",
]


def parse_frontmatter(text):
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}
    data = {}
    for line in text[4:end].splitlines():
        if ":" in line and not line.startswith(" "):
            key, value = line.split(":", 1)
            data[key.strip()] = value.strip()
    return data


def find_draft(project_root, slug):
    web = project_root / "web"
    if not web.is_dir():
        return None
    matches = [p for p in web.rglob(f"{slug}*.md") if p.name.lower() != "index.md"]
    if not matches:
        return None
    matches.sort(key=lambda p: len(p.name))
    return matches[0]


def yaml_escape(value):
    if value is None:
        return '""'
    s = str(value).strip()
    if not s:
        return '""'
    if any(c in s for c in ":#\n'\""):
        return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return s


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("slug", help="web draft slug (matches web/**/<slug>*.md)")
    parser.add_argument("--project-root", default=".", help="project root (default .)")
    parser.add_argument("--preview-url", help="public/shareable preview URL the reviewer can fetch without login")
    parser.add_argument("--preview-html-path", help="path to a rendered HTML snapshot the reviewer can open")
    parser.add_argument("--competitor", action="append", default=[], metavar="URL", help="competitor URL (repeat 3 times)")
    parser.add_argument("--date", default=None, help="override date stamp (YYYY-MM-DD)")
    parser.add_argument("--log", action="store_true", help="write structured JSONL log to logs/spawn_reviewer-<date>.jsonl")
    args = parser.parse_args()

    project_root = Path(args.project_root).expanduser().resolve()
    draft = find_draft(project_root, args.slug)
    if not draft:
        print(f"error: no draft matching web/**/{args.slug}*.md", file=sys.stderr)
        sys.exit(2)

    fm = parse_frontmatter(draft.read_text(encoding="utf-8", errors="ignore"))
    missing = [k for k in SEARCH_INTENT_KEYS if k not in fm]
    if missing:
        print(f"warning: frontmatter missing keys (will leave blank): {missing}", file=sys.stderr)

    if not (args.preview_url or args.preview_html_path):
        print("error: provide --preview-url OR --preview-html-path (see references/allincms-backend.md)", file=sys.stderr)
        sys.exit(2)
    if args.preview_html_path:
        html_path = Path(args.preview_html_path).expanduser().resolve()
        if not html_path.is_file():
            print(f"error: --preview-html-path does not exist: {html_path}", file=sys.stderr)
            sys.exit(2)

    if len(args.competitor) < 3:
        print(f"error: need exactly 3 --competitor URLs; got {len(args.competitor)}", file=sys.stderr)
        sys.exit(2)
    competitors = args.competitor[:3]

    date_stamp = args.date or _dt.date.today().isoformat()
    out_dir = project_root / "audits"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{args.slug}-{date_stamp}-reviewer-input.yaml"

    logger = JsonlLogger("spawn_reviewer", project_root=project_root if args.log else None)

    lines = [
        "# Reviewer input — the adversarial subagent reads ONLY this file.",
        "# Authored by spawn_reviewer.py; do not edit by hand.",
        "search_intent_brief:",
    ]
    for k in SEARCH_INTENT_KEYS:
        lines.append(f"  {k}: {yaml_escape(fm.get(k, ''))}")
    if args.preview_url:
        lines.append(f"preview_url: {yaml_escape(args.preview_url)}")
    if args.preview_html_path:
        lines.append(f"preview_html_path: {yaml_escape(args.preview_html_path)}")
    lines.append("competitor_urls:")
    for c in competitors:
        lines.append(f"  - {yaml_escape(c)}")
    # credibility_evidence list (path + best-effort source line, so reviewer can apply the credibility_artifact lens)
    cred_raw = fm.get("credibility_evidence", "")
    if isinstance(cred_raw, list):
        cred_refs = [str(r).strip() for r in cred_raw if str(r).strip()]
    else:
        s = str(cred_raw).strip()
        if s.startswith("[") and s.endswith("]"):
            cred_refs = [r.strip().strip("\"'") for r in s[1:-1].split(",") if r.strip()]
        elif s:
            cred_refs = [s]
        else:
            cred_refs = []
    if cred_refs:
        lines.append("credibility_evidence:")
        for ref in cred_refs:
            lines.append(f"  - path: {yaml_escape(ref)}")
            # try to grep a source: line from raw/<...>/ neighbours for traceability
            artifact = (project_root / ref)
            source_hint = ""
            if artifact.exists() and artifact.is_file() and artifact.suffix.lower() in {".md", ".mdx"}:
                txt = artifact.read_text(encoding="utf-8", errors="ignore")
                m = re.search(r"^source:\s*(.+)$", txt, re.M)
                if m:
                    source_hint = m.group(1).strip()
            lines.append(f"    source: {yaml_escape(source_hint)}")

    # Per-slug lock prevents two reviewers being spawned for the same slug concurrently.
    with shared_writer_lock(project_root, f"slug:{args.slug}"):
        out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("reviewer_input_written", slug=args.slug, path=str(out_path), preview="url" if args.preview_url else "html")
    print(out_path)


if __name__ == "__main__":
    main()
