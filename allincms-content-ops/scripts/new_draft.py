#!/usr/bin/env python3
"""Scaffold a web draft with all required frontmatter pre-filled.

Without this, authors hand-type ~20 fields and `audit_content.py` rejects
the draft on first run for missing keys. Defaults keep the file shape
valid; the author fills meaningful values before the publish gate.
"""
import argparse
import datetime as _dt
import os
import subprocess
import sys
from pathlib import Path


CONTENT_DIRS = {
    "article": "web/drafts",
    "post": "web/posts",
    "page": "web/pages",
    "product": "web/products",
    "guide": "web/drafts",
}


def detect_author():
    try:
        out = subprocess.run(["git", "config", "user.name"], capture_output=True, text=True, timeout=2)
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return os.environ.get("USER", "")


def find_project_root(start):
    p = Path(start).expanduser().resolve()
    for parent in [p, *p.parents]:
        if (parent / "PROJECT_INDEX.md").exists():
            return parent
    return None


def read_project_default_language(project_root):
    p = project_root / "PROJECT_INDEX.md"
    if not p.is_file():
        return None
    import re as _re
    for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
        m = _re.match(r"-\s*Default content language\s*:\s*(.+)$", line.strip())
        if m:
            return m.group(1).strip()
    return None


ZH_BODY = """# {title}

TODO — 用一句话直接回答主要查询，开门见山。

## 子问题 1

TODO

## 子问题 2

TODO

## 子问题 3

TODO
"""

EN_BODY = """# {title}

TODO — replace this body. Open with one sentence answering the primary query.

## Sub-question 1

TODO

## Sub-question 2

TODO

## Sub-question 3

TODO
"""


FRONTMATTER = """---
title: {title}
slug: {slug}
route: /{slug}
content_type: {content_type}
status: draft
persona: {persona}
region: {region}
search_intent: TODO — one sentence describing the reader's job
primary_query: TODO
secondary_queries: []
category: TODO
tags: []
meta_title: TODO (35-65 chars)
meta_description: TODO (120-165 chars)
cover_image: TODO — path under media/uploaded/ or full URL
cover_alt: TODO (under 125 chars)
differentiation: TODO — one sentence: how this page beats the strongest competitor URL borrowed from
credibility_evidence: []  # required: list paths under raw/ or media/ (charts, customer screenshots, product videos, comparisons)
source_wiki: []
source_raw: []
competitors_referenced: []
published_at:
updated_at: {today}
author: {author}
source_external:
related: []
last_seo_check: {today}
allincms:
  site_id:
  post_id:
  category_id:
  tag_ids: []
  published_url:
  canonical_url:
  noindex: false
  schema_recommendation: Article
  hreflang: []
audit:
  content_score:
  aesthetic_score:
  seo_geo_score:
  final_score:
---

"""


def body_for(region, title):
    """Pick a body template by region. zh* → Chinese; everything else → English."""
    if region and region.lower().startswith("zh"):
        return ZH_BODY.format(title=title)
    return EN_BODY.format(title=title)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("slug", help="kebab-case slug, unique site-wide")
    parser.add_argument("--persona", default="TODO", help="persona slug from wiki/personas/")
    parser.add_argument("--region", default=None, help="region, e.g. en-US, zh-CN. Default: PROJECT_INDEX 'Default content language'.")
    parser.add_argument("--content-type", default="article", choices=list(CONTENT_DIRS.keys()))
    parser.add_argument("--title", default=None, help="reader-facing title; default: slug humanised")
    parser.add_argument("--author", default=None, help="override author detection")
    parser.add_argument("--project-root", default=".", help="project root (default .)")
    parser.add_argument("--force", action="store_true", help="overwrite if file exists")
    args = parser.parse_args()

    project_root = find_project_root(args.project_root) or Path(args.project_root).expanduser().resolve()
    out_dir = project_root / CONTENT_DIRS[args.content_type]
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{args.slug}.md"
    if out_path.exists() and not args.force:
        print(f"error: {out_path} already exists (use --force to overwrite)", file=sys.stderr)
        return 2

    region = args.region or read_project_default_language(project_root) or "TODO"
    title = args.title or args.slug.replace("-", " ").title()
    author = args.author or detect_author()
    frontmatter = FRONTMATTER.format(
        title=title,
        slug=args.slug,
        content_type=args.content_type,
        persona=args.persona,
        region=region,
        today=_dt.date.today().isoformat(),
        author=author,
    )
    out_path.write_text(frontmatter + body_for(region, title), encoding="utf-8")
    print(out_path)
    print(f"region={region} body={'zh' if region.lower().startswith('zh') else 'en'}")
    print(f"next: fill TODO fields, then `python3 allincms-content-ops/scripts/audit_content.py {out_path}` to verify")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
