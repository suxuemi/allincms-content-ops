#!/usr/bin/env python3
"""Discover sitemap URLs for a list of domains and emit competitors.yml rows.

For each input domain/URL it probes in this order:
  1. <origin>/sitemap.xml
  2. <origin>/sitemap_index.xml
  3. <origin>/robots.txt   → Sitemap: <url>  lines

Output is YAML you can paste into `monitoring/competitors.yml`. The script
never writes that file itself — the operator should review and approve.
"""
import argparse
import re
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urlparse


HEADERS = {"User-Agent": "allincms-content-ops/sitemap-discover"}
TIMEOUT = 15


def _origin(url):
    if "://" not in url:
        url = "https://" + url
    p = urlparse(url)
    if not p.netloc:
        return None, url
    return f"{p.scheme}://{p.netloc}", url


def _head_ok(url):
    try:
        req = urllib.request.Request(url, headers=HEADERS, method="HEAD")
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.status == 200
    except Exception:
        # some servers reject HEAD; fall back to a tiny GET
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                return resp.status == 200 and (resp.read(64) or True)
        except Exception:
            return False


def _fetch_text(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def _name_from_origin(origin):
    host = urlparse(origin).netloc.lower()
    host = host[4:] if host.startswith("www.") else host
    return host.split(".", 1)[0] or host


def discover(domain):
    origin, _ = _origin(domain)
    if not origin:
        return {"input": domain, "origin": None, "error": "invalid domain"}
    candidates = []
    sm1 = origin + "/sitemap.xml"
    if _head_ok(sm1):
        candidates.append(sm1)
    sm2 = origin + "/sitemap_index.xml"
    if _head_ok(sm2):
        candidates.append(sm2)
    robots_url = origin + "/robots.txt"
    robots_lines = []
    try:
        txt = _fetch_text(robots_url)
        for m in re.finditer(r"(?im)^\s*Sitemap:\s*(\S+)", txt):
            robots_lines.append(m.group(1).strip())
    except Exception:
        pass
    for u in robots_lines:
        if u not in candidates:
            candidates.append(u)
    return {
        "input": domain,
        "origin": origin,
        "candidates": candidates,
        "robots_url": robots_url,
        "robots_sitemaps": robots_lines,
    }


def emit_yaml_row(result):
    name = _name_from_origin(result["origin"]) if result.get("origin") else "unknown"
    cands = result.get("candidates") or []
    primary = cands[0] if cands else ""
    lines = [
        f"  - name: {name}",
        f"    homepage: {result['origin']}",
        f"    sitemap: {primary}",
    ]
    if len(cands) > 1:
        lines.append(f"    # alternates: {', '.join(cands[1:])}")
    if not primary:
        lines.append("    # WARNING: no sitemap discovered; check the site manually before adding")
    lines.append("    google_site_filter: \"site:%s\"" % urlparse(result["origin"]).netloc)
    lines.append("    primary_query_overlap: []")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("domains", nargs="*", help="domain or URL; repeat or pass --from-file")
    parser.add_argument("--from-file", help="path with one domain/URL per line")
    args = parser.parse_args()

    inputs = list(args.domains)
    if args.from_file:
        for line in Path(args.from_file).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                inputs.append(line)
    if not inputs:
        parser.error("provide one or more domains, or --from-file")

    print("# sitemap_discover output — review, then paste under `competitors:` in monitoring/competitors.yml")
    print("# generated for", len(inputs), "input(s)\n")
    print("competitors:")
    any_found = False
    for d in inputs:
        result = discover(d)
        if result.get("origin") and result.get("candidates"):
            any_found = True
            print(emit_yaml_row(result))
            print()
        else:
            print(f"  # {d}: NO sitemap discovered (origin={result.get('origin')}; checked /sitemap.xml, /sitemap_index.xml, /robots.txt Sitemap: lines)")
            print(f"  #   manual next step: visit {result.get('origin') or d} and check site footer / page source for sitemap link")
            print()
    return 0 if any_found else 4


if __name__ == "__main__":
    raise SystemExit(main())
