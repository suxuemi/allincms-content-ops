#!/usr/bin/env python3
"""Capture a single competitor URL into the monitoring layer.

v0 scope (Codex Q1 review):
  - fetch URL → write immutable copy under raw/competitors/<comp>/<date>/<slug>.md
  - write `monitoring/sites/<comp>/captures/<date>__<slug>.md` with frontmatter + 4 empty body sections
  - update `monitoring/sites/<comp>/index.md` and `monitoring/daily/<date>.md` via SENTINEL anchors
  - dedup by (url, content_hash); same content → only bump last_seen_at on existing capture
  - `--no-ai` is the default; AI distill is v1+

Anti-patterns guarded:
  - never appends; both indexes are read-modify-write under locks
  - never lets AI write into `## borrow_angles` (only an empty stub)
"""
import argparse
import datetime as _dt
import hashlib
import json
import re
import sys
import hashlib as _hashlib2
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).parent))
from _lib import JsonlLogger, shared_writer_lock  # noqa: E402


SENTINEL_OPEN = "<!-- captures-start -->"
SENTINEL_CLOSE = "<!-- captures-end -->"
HEADERS = {"User-Agent": "allincms-content-ops/capture-url"}
TIMEOUT = 25


def find_project_root(start):
    p = Path(start).expanduser().resolve()
    for parent in [p, *p.parents]:
        if (parent / "PROJECT_INDEX.md").exists():
            return parent
    return None


def slugify(url):
    """Slug uses FULL path so `/en/pricing` and `/zh/pricing` don't collide.
    Long slugs get hashed-suffixed so two long URLs with identical first 71 chars stay distinct."""
    p = urlparse(url)
    path = re.sub(r"\.html?$", "", p.path, flags=re.I).strip("/")
    base = re.sub(r"[^A-Za-z0-9\-]+", "-", path).strip("-").lower() or p.netloc.replace(".", "-")
    if len(base) > 80:
        base = base[:71] + "-" + _hashlib2.sha1(url.encode("utf-8")).hexdigest()[:8]
    return base or "page"


class _TitleParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_title = False
        self.title = ""

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "title":
            self.in_title = True

    def handle_endtag(self, tag):
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title and not self.title:
            self.title = data.strip()


def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        body = resp.read()
        return resp.status, body


def html_to_text(html_bytes):
    text = html_bytes.decode("utf-8", errors="ignore")
    # Preserve SPA payload scripts (Next/Nuxt) and JSON-LD so SPAs don't all hash-collide on empty body.
    text = re.sub(
        r"<script(?![^>]*\b(?:id=\"__NEXT_DATA__\"|id=\"__NUXT__\"|type=\"application/(?:ld\+)?json\"))[^>]*>.*?</script>",
        " ", text, flags=re.S | re.I,
    )
    text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_title(html_bytes):
    p = _TitleParser()
    try:
        p.feed(html_bytes.decode("utf-8", errors="ignore"))
    except Exception:
        return ""
    return p.title


def stable_hash(text):
    # strip volatile numerics commonly used in counters / dates so footer edits don't trigger spurious captures
    scrubbed = re.sub(r"\b\d{4}-\d{2}-\d{2}\b", "", text)
    scrubbed = re.sub(r"\b\d{1,3}(?:,\d{3})+\b", "", scrubbed)  # numbers like 12,345 (likes / views)
    scrubbed = re.sub(r"\s+", " ", scrubbed).strip()
    return "sha256:" + hashlib.sha256(scrubbed.encode("utf-8")).hexdigest()


def find_existing_capture(project_root, comp, url):
    """Return (capture_path, first_seen_at, content_hash) if this URL has been captured before, else None."""
    site_dir = project_root / "monitoring" / "sites" / comp / "captures"
    if not site_dir.is_dir():
        return None
    for p in sorted(site_dir.glob("*.md")):
        text = p.read_text(encoding="utf-8", errors="ignore")
        m_url = re.search(r"^url:\s*(\S+)\s*$", text, re.M)
        if not m_url or m_url.group(1) != url:
            continue
        m_first = re.search(r"^first_seen_at:\s*(\S+)\s*$", text, re.M)
        m_hash = re.search(r"^content_hash:\s*(\S+)\s*$", text, re.M)
        return p, (m_first.group(1) if m_first else ""), (m_hash.group(1) if m_hash else "")
    return None


def write_raw(project_root, comp, date_str, slug, text, meta):
    raw_dir = project_root / "raw" / "competitors" / comp / date_str
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_md = raw_dir / f"{slug}.md"
    raw_meta = raw_dir / f"{slug}.meta.json"
    # raw is append-only — if it exists already, leave it alone
    if not raw_md.exists():
        raw_md.write_text(
            f"---\ncollected_at: {date_str}\nsource_url: {meta['url']}\n---\n\n{text[:200_000]}\n",
            encoding="utf-8",
        )
    if not raw_meta.exists():
        raw_meta.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    return raw_md.relative_to(project_root).as_posix()


def make_capture_body():
    return (
        "## extract\n"
        "<!-- ai:extract -->\n"
        "(empty in v0; fill with a 3–8 sentence summary — AI or human)\n"
        "<!-- /ai:extract -->\n\n"
        "## key_points\n"
        "<!-- ai:key_points -->\n"
        "- (empty in v0)\n"
        "<!-- /ai:key_points -->\n\n"
        "## borrow_angles\n"
        "<!-- human:borrow_angles -->\n"
        "- (left blank — human-curated only; AI MUST NOT write here)\n"
        "<!-- /human:borrow_angles -->\n\n"
        "## ai_suggestions\n"
        "<!-- ai-suggestions-start -->\n"
        "<!-- ai-suggestions-end -->\n"
    )


def assert_no_ai_in_borrow(text):
    """Defence-in-depth: refuse to write if `## borrow_angles` block has any `<!-- ai:* -->` tag."""
    m = re.search(r"## borrow_angles\s*(.*?)(?=\n## |\Z)", text, re.S)
    if m and re.search(r"<!--\s*ai:", m.group(1)):
        raise RuntimeError("refusing to write: AI tag found inside `## borrow_angles` (human-only section)")


def write_capture(project_root, comp, date_str, slug, frontmatter, body):
    capture_dir = project_root / "monitoring" / "sites" / comp / "captures"
    capture_dir.mkdir(parents=True, exist_ok=True)
    capture_path = capture_dir / f"{date_str}__{slug}.md"
    full = "---\n" + frontmatter + "---\n\n" + body
    assert_no_ai_in_borrow(full)
    capture_path.write_text(full, encoding="utf-8")
    return capture_path


def upsert_index_row(text, row, dedup_url):
    """Replace or insert `row` inside the SENTINEL block. Dedup key is the
    markdown link form `](url)` so `/a` and `/a/b` never substring-collide."""
    needle = f"]({dedup_url})"
    if SENTINEL_OPEN not in text or SENTINEL_CLOSE not in text:
        block = f"{SENTINEL_OPEN}\n{row}\n{SENTINEL_CLOSE}\n"
        return text.rstrip() + "\n\n" + block
    pre, rest = text.split(SENTINEL_OPEN, 1)
    inner, post = rest.split(SENTINEL_CLOSE, 1)
    inner_lines = [l for l in inner.splitlines() if l.strip() and needle not in l]
    inner_lines.append(row)
    return pre + SENTINEL_OPEN + "\n" + "\n".join(inner_lines) + "\n" + SENTINEL_CLOSE + post


def ensure_site_index(project_root, comp):
    p = project_root / "monitoring" / "sites" / comp / "index.md"
    if p.exists():
        return p
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        f"# {comp} — captures index\n\n"
        "| first_seen | type | title | url | review | capture |\n"
        "|---|---|---|---|---|---|\n"
        f"{SENTINEL_OPEN}\n{SENTINEL_CLOSE}\n",
        encoding="utf-8",
    )
    return p


def ensure_daily_index(project_root, date_str):
    p = project_root / "monitoring" / "daily" / f"{date_str}.md"
    if p.exists():
        return p
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        f"# {date_str} new captures\n\n"
        "| competitor | type | title | url | review | capture |\n"
        "|---|---|---|---|---|---|\n"
        f"{SENTINEL_OPEN}\n{SENTINEL_CLOSE}\n",
        encoding="utf-8",
    )
    return p


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("url")
    parser.add_argument("--competitor", required=True, help="slug from monitoring/competitors.yml")
    parser.add_argument("--type", default="article", choices=["article", "product", "landing", "asset"])
    parser.add_argument("--language", default="")
    parser.add_argument("--source-sitemap", default="")
    parser.add_argument("--source-run", default="")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-ai", action="store_true", default=True, help="v0 default — AI distill deferred")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--log", action="store_true")
    args = parser.parse_args()

    project_root = find_project_root(args.project_root) or Path(args.project_root).expanduser().resolve()
    logger = JsonlLogger("capture_url", project_root=project_root if args.log else None)

    try:
        status, body_bytes = fetch(args.url)
    except Exception as e:
        print(f"error: fetch failed: {e}", file=sys.stderr)
        logger.error("fetch_failed", url=args.url, reason=str(e))
        return 1

    if status != 200:
        print(f"error: HTTP {status}", file=sys.stderr)
        logger.error("non_200", url=args.url, status=status)
        return 1

    text = html_to_text(body_bytes)
    title = parse_title(body_bytes) or args.url
    content_hash = stable_hash(text)
    today = _dt.date.today().isoformat()
    captured_at = _dt.datetime.now().astimezone().isoformat(timespec="seconds")
    slug = slugify(args.url)

    existing = find_existing_capture(project_root, args.competitor, args.url)
    if existing and existing[2] == content_hash:
        # Same URL, same content — just bump last_seen_at on the existing capture.
        cap_path, first_seen, _ = existing
        if not args.dry_run:
            t = cap_path.read_text(encoding="utf-8")
            t = re.sub(r"^last_seen_at:\s*\S*", f"last_seen_at: {today}", t, count=1, flags=re.M)
            cap_path.write_text(t, encoding="utf-8")
        print(f"unchanged (last_seen_at bumped): {cap_path}")
        logger.info("unchanged", url=args.url, capture=str(cap_path))
        return 0

    first_seen_at = existing[1] if existing else today

    canonical_url = args.url  # v0: trust input
    meta = {
        "url": args.url, "status": status, "fetched_at": captured_at,
        "content_hash": content_hash, "competitor": args.competitor, "type": args.type,
    }

    if args.dry_run:
        print(f"dry-run: would capture {args.url} as {slug} for {args.competitor}")
        return 0

    raw_path = write_raw(project_root, args.competitor, today, slug, text, meta)

    frontmatter = (
        "schema_version: 1\n"
        f"url: {args.url}\n"
        f"canonical_url: {canonical_url}\n"
        f"title: \"{title.replace(chr(34), chr(39))}\"\n"
        f"competitor: {args.competitor}\n"
        f"type: {args.type}\n"
        f"language: {args.language}\n"
        f"captured_at: {captured_at}\n"
        f"first_seen_at: {first_seen_at}\n"
        f"last_seen_at: {today}\n"
        f"source_sitemap: {args.source_sitemap}\n"
        f"source_run: {args.source_run}\n"
        f"content_hash: {content_hash}\n"
        f"raw_path: {raw_path}\n"
        "trust: ai-generated\n"
        "review_status: pending\n"
        "reviewer: \"\"\n"
        "reviewed_at: \"\"\n"
        "tags: []\n"
    )
    capture_path = write_capture(project_root, args.competitor, today, slug, frontmatter, make_capture_body())
    capture_rel = capture_path.relative_to(project_root).as_posix()

    safe_title = title.replace("|", "/")[:80]
    site_row = f"| {first_seen_at} | {args.type} | {safe_title} | [link]({args.url}) | pending | [md]({capture_path.relative_to(capture_path.parents[1]).as_posix()}) |"
    daily_row = f"| {args.competitor} | {args.type} | {safe_title} | [link]({args.url}) | pending | [md](../sites/{args.competitor}/captures/{capture_path.name}) |"

    site_index = ensure_site_index(project_root, args.competitor)
    daily_index = ensure_daily_index(project_root, today)

    with shared_writer_lock(project_root, f"monitoring_site:{args.competitor}"):
        text_i = site_index.read_text(encoding="utf-8")
        site_index.write_text(upsert_index_row(text_i, site_row, args.url), encoding="utf-8")
    with shared_writer_lock(project_root, "monitoring_daily"):
        text_d = daily_index.read_text(encoding="utf-8")
        daily_index.write_text(upsert_index_row(text_d, daily_row, args.url), encoding="utf-8")

    print(capture_rel)
    logger.info("captured", url=args.url, capture=capture_rel, hash=content_hash)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
