#!/usr/bin/env python3
"""Run a full monitoring round: sitemap_diff → capture each new URL.

v0 wiring (Codex Q1 review):
  - reads `monitoring/competitors.yml`
  - for each competitor with `sitemap:` configured: runs sitemap_diff to find new URLs
  - for each new URL (up to --limit): invokes capture_url.py (subprocess) with the same
    --source-sitemap / --source-run / --competitor

  This is a thin orchestrator. It does NOT re-implement sitemap parsing or capture
  logic; both live in dedicated scripts.
"""
import argparse
import datetime as _dt
import random
import re
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).parent))
from _lib import JsonlLogger  # noqa: E402
from sitemap_diff import load_competitors_yml, parse_sitemap, fetch, diff_against_cache  # noqa: E402


def find_project_root(start):
    p = Path(start).expanduser().resolve()
    for parent in [p, *p.parents]:
        if (parent / "PROJECT_INDEX.md").exists():
            return parent
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("project_root", nargs="?", default=".")
    parser.add_argument("--competitor", help="only run this competitor (slug)")
    parser.add_argument("--limit", type=int, default=10, help="max URLs to capture per competitor (default 10)")
    parser.add_argument("--dry-run", action="store_true", help="list URLs but don't capture")
    parser.add_argument("--log", action="store_true")
    args = parser.parse_args()

    project_root = find_project_root(args.project_root) or Path(args.project_root).expanduser().resolve()
    logger = JsonlLogger("monitor_run", project_root=project_root if args.log else None)

    comps = load_competitors_yml(project_root / "monitoring" / "competitors.yml")
    if args.competitor:
        comps = [c for c in comps if c.get("name") == args.competitor]
    if not comps:
        print("no competitors configured (or filter matched nothing)", file=sys.stderr)
        return 2

    today = _dt.date.today().isoformat()
    total_captured = 0
    total_failed = 0

    capture_script = Path(__file__).with_name("capture_url.py")
    last_hit_per_host = {}
    MIN_GAP_S = 2.0  # per-host throttle to avoid WAF / 429

    for comp in comps:
        name = comp.get("name", "")
        sitemap_url = comp.get("sitemap", "")
        if not (name and sitemap_url):
            continue
        print(f"## {name}")
        try:
            xml = fetch(sitemap_url)
        except Exception as e:
            print(f"  sitemap fetch failed: {e}")
            logger.warn("sitemap_fetch_failed", competitor=name, url=sitemap_url, reason=str(e))
            continue
        urls = parse_sitemap(xml)
        added, removed, first_run = diff_against_cache(project_root, name, urls)
        if first_run:
            print(f"  first run: seeded {len(urls)} URLs; 0 captured")
            continue
        if not added:
            print("  no new URLs")
            continue
        capped = added[: args.limit]
        for u in capped:
            print(f"  + {u}")
            if args.dry_run:
                continue
            host = urlparse(u).netloc
            gap = time.time() - last_hit_per_host.get(host, 0)
            if gap < MIN_GAP_S:
                time.sleep(MIN_GAP_S - gap + random.uniform(0, 0.5))
            last_hit_per_host[host] = time.time()
            r = subprocess.run(
                [sys.executable, str(capture_script), u,
                 "--competitor", name, "--source-sitemap", sitemap_url,
                 "--source-run", f"runs/sitemap/diff-{today}.md", "--project-root", str(project_root)],
                capture_output=True, text=True,
            )
            if r.returncode == 0:
                total_captured += 1
            else:
                total_failed += 1
                print(f"    capture failed (rc={r.returncode}):")
                for ln in (r.stderr or "").splitlines()[-5:]:
                    print(f"      {ln}")

    print(f"\ncaptured={total_captured} failed={total_failed}")
    logger.info("run_end", captured=total_captured, failed=total_failed)
    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
