#!/usr/bin/env python3
"""Sitemap-based new-URL detector for competitor monitoring.

Reads `monitoring/competitors.yml`, fetches each competitor's sitemap.xml
(recursively if it's a sitemap index), diffs against the last cached
snapshot under `monitoring/runs/sitemap/`, and (optionally) appends new
URLs to `wiki/content-opportunities.md` — capped per run, deduped against
all existing rows.

First-run safety: when no cache exists for a competitor, seeds the cache
and appends zero opportunity rows (so a fresh setup never floods the table).
"""
import argparse
import datetime as _dt
import re
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import JsonlLogger, shared_writer_lock  # noqa: E402


PER_RUN_CAP = 10
MAX_SITEMAP_DEPTH = 3


def fetch(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": "allincms-content-ops/sitemap-diff"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def parse_sitemap(text, fetch_fn=fetch, depth=0):
    """Return list of page URLs. Recurses into <sitemapindex> entries."""
    locs = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", text)
    if "<sitemapindex" in text.lower() and depth < MAX_SITEMAP_DEPTH:
        urls = []
        for sub in locs:
            try:
                urls.extend(parse_sitemap(fetch_fn(sub), fetch_fn, depth + 1))
            except Exception as e:
                print(f"warning: failed to fetch sub-sitemap {sub}: {e}", file=sys.stderr)
        return sorted(set(urls))
    return sorted(set(locs))


try:
    import yaml  # type: ignore

    def load_competitors_yml(path):
        if not path.is_file():
            return []
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return data.get("competitors", []) or []

except ImportError:

    def load_competitors_yml(path):
        if not path.is_file():
            return []
        print("warning: pyyaml not installed; only `name` and `sitemap` fields will be parsed reliably", file=sys.stderr)
        items = []
        current = None
        for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = raw.rstrip()
            if "#" in line:
                line = line.split("#", 1)[0].rstrip()
            if line.startswith("  - "):
                if current:
                    items.append(current)
                current = {}
                rest = line[4:]
                if ":" in rest:
                    k, v = rest.split(":", 1)
                    current[k.strip()] = v.strip().strip('"').strip("'")
            elif line.startswith("    ") and current is not None and ":" in line:
                k, v = line.strip().split(":", 1)
                current[k.strip()] = v.strip().strip('"').strip("'")
        if current:
            items.append(current)
        return items


def canonical_url(url):
    u = url.strip()
    u = re.sub(r"[?&](utm_[^=]+|fbclid|gclid|mc_[ce]id|ref|source)=[^&]*", "", u)
    u = u.rstrip("?&")
    u = u.rstrip("/")
    return u


def diff_competitor(project_root, comp, source_text):
    """Returns (added, removed, first_run). First-run never reports added."""
    name = comp.get("name") or "unknown"
    cache_dir = project_root / "monitoring" / "runs" / "sitemap"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / f"{name}.last.txt"
    new_urls = parse_sitemap(source_text)
    first_run = not cache_path.exists()
    cache_path.write_text("\n".join(new_urls) + "\n", encoding="utf-8")
    if first_run:
        return [], [], True
    old_urls = set(cache_path.read_text(encoding="utf-8").splitlines())
    # cache was just overwritten with new — load the pre-overwrite via re-read won't help.
    # Instead, compute against what we just wrote vs what was there: we re-do via a second file.
    return [], [], True  # unreachable; restructured below in main


def diff_against_cache(project_root, name, new_urls):
    cache_dir = project_root / "monitoring" / "runs" / "sitemap"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / f"{name}.last.txt"
    first_run = not cache_path.exists()
    if first_run:
        cache_path.write_text("\n".join(new_urls) + "\n", encoding="utf-8")
        return [], [], True
    old_urls = set(cache_path.read_text(encoding="utf-8").splitlines())
    cache_path.write_text("\n".join(new_urls) + "\n", encoding="utf-8")
    added = sorted(u for u in new_urls if u not in old_urls)
    removed = sorted(u for u in old_urls if u not in set(new_urls))
    return added, removed, False


def existing_urls_in_opportunities(project_root):
    path = project_root / "wiki" / "content-opportunities.md"
    if not path.is_file():
        return set()
    text = path.read_text(encoding="utf-8", errors="ignore")
    return {canonical_url(u) for u in re.findall(r"https?://[^\s|)\]]+", text)}


def append_opportunities(project_root, competitor_name, added, existing_canon, cap):
    path = project_root / "wiki" / "content-opportunities.md"
    if not path.is_file():
        return 0
    today = _dt.date.today().isoformat()
    rows = []
    for url in added:
        if canonical_url(url) in existing_canon:
            continue
        rows.append(f"| proposed | (from {competitor_name} sitemap diff {today}) | | | {url} | | needs user approval |")
        existing_canon.add(canonical_url(url))
        if len(rows) >= cap:
            break
    if not rows:
        return 0
    with shared_writer_lock(project_root, "opportunities"):
        with path.open("a", encoding="utf-8") as f:
            f.write("\n".join(rows) + "\n")
    return len(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("project_root")
    parser.add_argument("--from-file", help="path to a pre-downloaded sitemap.xml (single-competitor mode); requires --name")
    parser.add_argument("--name", help="competitor name when using --from-file")
    parser.add_argument("--no-opportunities", action="store_true", help="don't append rows to wiki/content-opportunities.md")
    parser.add_argument("--cap", type=int, default=PER_RUN_CAP, help=f"max new rows appended per competitor (default {PER_RUN_CAP})")
    parser.add_argument("--log", action="store_true", help="write structured JSONL log to logs/sitemap_diff-<date>.jsonl")
    args = parser.parse_args()
    project_root = Path(args.project_root).expanduser().resolve()
    logger = JsonlLogger("sitemap_diff", project_root=project_root if args.log else None)
    logger.info("run_start", project_root=str(project_root), cap=args.cap, mode="from_file" if args.from_file else "yml")

    runs_dir = project_root / "monitoring" / "runs" / "sitemap"
    runs_dir.mkdir(parents=True, exist_ok=True)
    today = _dt.date.today().isoformat()
    summary_path = runs_dir / f"diff-{today}.md"

    summary_lines = [f"# Sitemap diff {today}", ""]
    total_added = 0
    total_removed = 0
    total_appended = 0

    if args.from_file:
        if not args.name:
            print("error: --from-file requires --name", file=sys.stderr)
            sys.exit(2)
        text = Path(args.from_file).read_text(encoding="utf-8", errors="ignore")
        targets = [({"name": args.name}, text)]
    else:
        comps = load_competitors_yml(project_root / "monitoring" / "competitors.yml")
        targets = []
        for comp in comps:
            sm = comp.get("sitemap")
            if not sm:
                continue
            try:
                text = fetch(sm)
            except Exception as e:
                summary_lines.append(f"## {comp.get('name', '?')}\n- fetch_error: {e}\n")
                continue
            targets.append((comp, text))

    existing_canon = existing_urls_in_opportunities(project_root)

    for comp, text in targets:
        name = comp.get("name", "?")
        urls = parse_sitemap(text)
        added, removed, first_run = diff_against_cache(project_root, name, urls)
        summary_lines.append(f"## {name}")
        if first_run:
            summary_lines.append(f"- first_run: seeded {len(urls)} URLs, 0 added (cache primed)")
            summary_lines.append("")
            continue
        total_added += len(added)
        total_removed += len(removed)
        summary_lines.append(f"- added: {len(added)} (cap {args.cap})")
        for u in added:
            summary_lines.append(f"  - {u}")
        summary_lines.append(f"- removed: {len(removed)}")
        for u in removed:
            summary_lines.append(f"  - {u}")
        if added and not args.no_opportunities:
            appended = append_opportunities(project_root, name, added, existing_canon, args.cap)
            summary_lines.append(f"- appended_to_opportunities: {appended}")
            total_appended += appended
        summary_lines.append("")

    summary_path.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
    logger.info("run_end", added=total_added, removed=total_removed, appended=total_appended, summary=str(summary_path))
    print(f"summary={summary_path}")
    print(f"added={total_added} removed={total_removed} appended={total_appended}")


if __name__ == "__main__":
    main()
