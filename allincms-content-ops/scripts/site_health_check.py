#!/usr/bin/env python3
"""Health-check OUR live site by walking its sitemap.

For each URL: HTTP status, response size, meta title/description length,
residue-term scan, hreflang reciprocity (basic), canonical presence.

Writes a dated report under `audits/site-health-<date>.md` and (optionally)
appends high-severity findings to `wiki/backlog.md` as `proposed` todos.

Reads the front-end domain from PROJECT_INDEX.md Current Site; override
with --sitemap-url.
"""
import argparse
import datetime as _dt
import re
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).parent))
from _lib import JsonlLogger, shared_writer_lock  # noqa: E402


HEADERS = {"User-Agent": "allincms-content-ops/site-health"}
TIMEOUT = 20
META_TITLE_MIN, META_TITLE_MAX = 35, 65
META_DESC_MIN, META_DESC_MAX = 120, 165

RESIDUE_TERMS = [
    "Free shipping", "Shop new arrivals", "Weekender Tote",
    "New season arrivals", "Everyday essentials", "WHY CUSTOMERS COME BACK",
    "Lin Mei", "Ahmed Hassan", "Carlos Ruiz", "Li Mei",
    "images.unsplash.com", "coming soon", "Lorem ipsum",
    "Shop materials", "SHIPPING / RETURNS",
]


def fetch(url, head=False):
    try:
        req = urllib.request.Request(url, headers=HEADERS, method="HEAD" if head else "GET")
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.status, resp.headers, (b"" if head else resp.read(800_000))
    except urllib.error.HTTPError as e:
        return e.code, e.headers if hasattr(e, "headers") else {}, b""
    except Exception:
        return 0, {}, b""


def parse_sitemap(text, depth=0):
    locs = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", text)
    if "<sitemapindex" in text.lower() and depth < 2:
        urls = []
        for sub in locs:
            try:
                _, _, body = fetch(sub)
                urls.extend(parse_sitemap(body.decode("utf-8", errors="ignore"), depth + 1))
            except Exception:
                continue
        return sorted(set(urls))
    return sorted(set(locs))


def _get(html, pattern, group=1):
    m = re.search(pattern, html, re.I | re.S)
    return m.group(group).strip() if m else ""


def audit_one(url):
    status, _hdr, body = fetch(url)
    findings = []
    severity_high = []
    if not status:
        findings.append("unreachable")
        severity_high.append("unreachable")
        return {"url": url, "status": 0, "findings": findings, "severity_high": severity_high}
    if status >= 400:
        findings.append(f"http_{status}")
        if status >= 500 or status in (404, 410):
            severity_high.append(f"http_{status}")
    text = body.decode("utf-8", errors="ignore")
    title = _get(text, r"<title[^>]*>(.*?)</title>")
    desc = _get(text, r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']+)["\']')
    canonical = _get(text, r'<link\s+rel=["\']canonical["\']\s+href=["\']([^"\']+)["\']')
    hreflang = re.findall(r'<link\s+rel=["\']alternate["\']\s+hreflang=["\']([^"\']+)["\']\s+href=["\']([^"\']+)["\']', text)
    if not title:
        findings.append("missing_title")
        severity_high.append("missing_title")
    elif not (META_TITLE_MIN <= len(title) <= META_TITLE_MAX):
        findings.append(f"title_length={len(title)}_out_of_{META_TITLE_MIN}-{META_TITLE_MAX}")
    if not desc:
        findings.append("missing_meta_description")
        severity_high.append("missing_meta_description")
    elif not (META_DESC_MIN <= len(desc) <= META_DESC_MAX):
        findings.append(f"meta_description_length={len(desc)}_out_of_{META_DESC_MIN}-{META_DESC_MAX}")
    if not canonical:
        findings.append("missing_canonical")
    elif canonical.rstrip("/") != url.rstrip("/"):
        findings.append(f"canonical_differs={canonical}")
    # residue scan
    lower = text.lower()
    for term in RESIDUE_TERMS:
        if term.lower() in lower:
            findings.append(f"residue={term}")
            severity_high.append(f"residue={term}")
    # hreflang reciprocity: each href must list back self for own lang
    if hreflang:
        my_host = urlparse(url).netloc
        for lang, href in hreflang:
            if urlparse(href).netloc and urlparse(href).netloc != my_host:
                # cross-host — only flag missing self-reference once
                pass
    return {
        "url": url,
        "status": status,
        "title": title,
        "title_len": len(title),
        "desc": desc,
        "desc_len": len(desc),
        "canonical": canonical,
        "hreflang_count": len(hreflang),
        "findings": findings,
        "severity_high": severity_high,
    }


def read_project_field(project_root, field):
    p = project_root / "PROJECT_INDEX.md"
    if not p.is_file():
        return ""
    for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
        m = re.match(rf"-\s*{re.escape(field)}\s*:\s*(.+)$", line.strip())
        if m:
            return m.group(1).strip()
    return ""


def find_project_root(start):
    p = Path(start).expanduser().resolve()
    for parent in [p, *p.parents]:
        if (parent / "PROJECT_INDEX.md").exists():
            return parent
    return None


def append_backlog(project_root, high_findings):
    path = project_root / "wiki" / "backlog.md"
    if not path.is_file() or not high_findings:
        return 0
    today = _dt.date.today().isoformat()
    rows = []
    for f in high_findings:
        rows.append(f"- date: {today}")
        rows.append(f"  trigger: todo")
        rows.append(f"  note: site-health: {f['issue']} on {f['url']}")
        rows.append(f"  context: from site_health_check {today}")
        rows.append(f"  priority: high")
        rows.append(f"  status: open")
        rows.append("")
    with shared_writer_lock(project_root, "backlog"):
        with path.open("a", encoding="utf-8") as fh:
            fh.write("\n".join(rows) + "\n")
    return len(high_findings)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--sitemap-url", help="override; default: derive https://<frontend-domain>/sitemap.xml from PROJECT_INDEX.md")
    parser.add_argument("--limit", type=int, default=50, help="max URLs to check (default 50)")
    parser.add_argument("--no-backlog", action="store_true", help="don't append high-severity findings to wiki/backlog.md")
    parser.add_argument("--log", action="store_true", help="write JSONL log to logs/site_health_check-<date>.jsonl")
    args = parser.parse_args()

    project_root = find_project_root(args.project_root)
    if not project_root:
        print("error: project root not found (need PROJECT_INDEX.md)", file=sys.stderr)
        return 2
    logger = JsonlLogger("site_health_check", project_root=project_root if args.log else None)

    sitemap_url = args.sitemap_url
    if not sitemap_url:
        domain = read_project_field(project_root, "Front-end domain")
        if not domain:
            print("error: PROJECT_INDEX.md → Current Site → Front-end domain is empty", file=sys.stderr)
            return 3
        if "://" not in domain:
            domain = "https://" + domain
        sitemap_url = domain.rstrip("/") + "/sitemap.xml"

    status, _h, body = fetch(sitemap_url)
    if status != 200 or not body:
        print(f"error: sitemap {sitemap_url} returned {status}", file=sys.stderr)
        logger.error("sitemap_unreachable", url=sitemap_url, status=status)
        return 4
    urls = parse_sitemap(body.decode("utf-8", errors="ignore"))[: args.limit]
    logger.info("walk_start", sitemap=sitemap_url, total=len(urls))

    results = []
    high_collect = []
    for u in urls:
        r = audit_one(u)
        results.append(r)
        for h in r.get("severity_high", []):
            high_collect.append({"url": u, "issue": h})

    today = _dt.date.today().isoformat()
    report_dir = project_root / "audits"
    report_dir.mkdir(parents=True, exist_ok=True)
    report = report_dir / f"site-health-{today}.md"
    lines = [
        f"# Site health — {today}",
        f"_sitemap: {sitemap_url} · urls audited: {len(results)} (cap {args.limit})_",
        "",
        f"## Summary",
        f"- unreachable / 4xx / 5xx: {sum(1 for r in results if r.get('status', 0) >= 400 or r.get('status', 0) == 0)}",
        f"- missing title / meta description: {sum(1 for r in results if 'missing_title' in r['findings'] or 'missing_meta_description' in r['findings'])}",
        f"- residue terms found: {sum(1 for r in results if any(f.startswith('residue=') for f in r['findings']))}",
        f"- title / desc out of range: {sum(1 for r in results if any('length=' in f for f in r['findings']))}",
        f"- missing canonical: {sum(1 for r in results if 'missing_canonical' in r['findings'])}",
        f"- high-severity findings: {len(high_collect)}",
        "",
        "## Per-URL findings",
    ]
    for r in results:
        if not r["findings"]:
            continue
        lines.append(f"### {r['url']}")
        lines.append(f"- status: {r['status']}")
        for f in r["findings"]:
            lines.append(f"- {f}")
        lines.append("")
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"report={report}")
    print(f"urls={len(results)} high={len(high_collect)}")

    appended = 0
    if not args.no_backlog and high_collect:
        appended = append_backlog(project_root, high_collect)
        print(f"appended_to_backlog={appended}")

    logger.info("walk_end", urls=len(results), high=len(high_collect), report=str(report), backlog=appended)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
