#!/usr/bin/env python3
import argparse
import datetime as dt
import hashlib
import html.parser
import json
import re
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urlparse


class TextExtractor(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip = False
        self.title = ""
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript"}:
            self.skip = True
        if tag == "title":
            self.in_title = True
        if tag in {"p", "br", "h1", "h2", "h3", "li", "tr"}:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript"}:
            self.skip = False
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        text = " ".join(data.split())
        if not text:
            return
        if self.in_title:
            self.title += text + " "
        if not self.skip:
            self.parts.append(text)

    def text(self):
        return "\n".join(line.strip() for line in " ".join(self.parts).splitlines() if line.strip())


def slugify(value):
    cleaned = []
    for char in value.lower():
        if char.isalnum():
            cleaned.append(char)
        elif char in {" ", "-", "_", ".", "/"}:
            cleaned.append("-")
    slug = "".join(cleaned).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug[:80] or "competitor"


def append_line(path, line):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("", encoding="utf-8")
    with path.open("a", encoding="utf-8") as fh:
        fh.write(line.rstrip() + "\n")


def ensure_index(path, title, header):
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# {title}\n\n{header}\n", encoding="utf-8")


def parse_simple_competitors_yml(path):
    text = path.read_text(encoding="utf-8")
    items = []
    current_name = None
    current_type = ""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- name:"):
            current_name = stripped.split(":", 1)[1].strip().strip('"')
        elif stripped.startswith("type:"):
            current_type = stripped.split(":", 1)[1].strip().strip('"')
        elif stripped.startswith("- url:"):
            url = stripped.split(":", 1)[1].strip().strip('"')
            items.append({"name": current_name or urlparse(url).netloc, "url": url, "type": current_type or "page"})
    return items


def load_targets(path):
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        items = []
        for competitor in data.get("competitors", []):
            for page in competitor.get("pages", []):
                items.append({
                    "name": competitor.get("name") or urlparse(page.get("url", "")).netloc,
                    "url": page.get("url"),
                    "type": page.get("type", "page"),
                })
        return [item for item in items if item.get("url")]
    return parse_simple_competitors_yml(path)


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "allincms-content-ops/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read(), resp.headers.get("Content-Type", "")


def extract_topics(text, title):
    candidates = []
    for line in re.split(r"[\n。.!?]", text):
        clean = " ".join(line.split())
        if 28 <= len(clean) <= 120:
            lowered = clean.lower()
            if any(word in lowered for word in ["how", "why", "guide", "pricing", "compare", "seo", "cms", "website", "product", "case", "launch"]):
                candidates.append(clean)
    topics = []
    if title.strip():
        topics.append(title.strip())
    for candidate in candidates:
        if candidate not in topics:
            topics.append(candidate)
        if len(topics) >= 8:
            break
    return topics


def main():
    parser = argparse.ArgumentParser(description="Fetch competitor pages, detect changes, and update raw/monitoring indexes.")
    parser.add_argument("project_root")
    parser.add_argument("--config", default="monitoring/competitors.yml")
    args = parser.parse_args()

    root = Path(args.project_root).expanduser().resolve()
    config = (root / args.config).resolve()
    if not config.exists():
        print(f"Missing competitor config: {config}", file=sys.stderr)
        return 2

    today = dt.date.today().isoformat()
    run_dir = root / "monitoring" / "runs" / today
    raw_index = root / "raw" / "competitors" / "index.md"
    monitor_index = root / "monitoring" / "index.md"
    ensure_index(raw_index, "Competitor Raw Index", "| Date | Competitor | URL | Change | Topic | Status | Wiki link |\n|---|---|---|---|---|---|---|")
    ensure_index(monitor_index, "Monitoring Index", "| Date | Competitor | Run path | New topics | User decision |\n|---|---|---|---|---|")
    run_dir.mkdir(parents=True, exist_ok=True)

    fetch_log = []
    diff_lines = ["# Diff Summary\n"]
    topic_lines = ["# Topics\n", "| Competitor | URL | Topic | Approval status | Notes |", "|---|---|---|---|---|"]
    targets = load_targets(config)
    state_path = root / "monitoring" / "state.json"
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}

    for target in targets:
        name = target["name"]
        url = target["url"]
        page_type = target.get("type", "page")
        try:
            body, content_type = fetch(url)
        except Exception as exc:
            fetch_log.append(f"- FAIL {name} {url}: {exc}")
            continue
        digest = hashlib.sha256(body).hexdigest()
        key = url
        old_digest = state.get(key, {}).get("sha256")
        change = "new" if not old_digest else ("changed" if old_digest != digest else "unchanged")
        state[key] = {"sha256": digest, "checked_at": today, "name": name, "type": page_type}

        parser_html = TextExtractor()
        decoded = body.decode("utf-8", errors="ignore")
        parser_html.feed(decoded)
        text = parser_html.text()
        title = parser_html.title.strip() or url

        raw_dir = root / "raw" / "competitors" / f"{today}-{slugify(name)}-{slugify(urlparse(url).path or page_type)}"
        raw_dir.mkdir(parents=True, exist_ok=True)
        (raw_dir / "source.html").write_bytes(body)
        extracted = raw_dir / "extracted.md"
        extracted.write_text(f"""---
competitor: "{name}"
url: "{url}"
page_type: "{page_type}"
collected_at: "{today}"
change: "{change}"
sha256: "{digest}"
rights: "competitor monitoring; do not copy"
---

# {title}

{text[:60000]}
""", encoding="utf-8")

        topics = extract_topics(text, title) if change in {"new", "changed"} else []
        for topic in topics:
            topic_lines.append(f"| {name} | {url} | {topic} | proposed | Confirm before writing or publishing |")
            append_line(raw_index, f"| {today} | {name} | {url} | {change} | {topic} | proposed |  |")
        fetch_log.append(f"- {change.upper()} {name} {url} {content_type} `{extracted.relative_to(root)}`")
        diff_lines.append(f"- {name} `{change}` {url}")
        append_line(monitor_index, f"| {today} | {name} | `{run_dir.relative_to(root)}` | {len(topics)} | pending |")

    (run_dir / "fetch-log.md").write_text("# Fetch Log\n\n" + "\n".join(fetch_log) + "\n", encoding="utf-8")
    (run_dir / "diff-summary.md").write_text("\n".join(diff_lines) + "\n", encoding="utf-8")
    (run_dir / "topics.md").write_text("\n".join(topic_lines) + "\n", encoding="utf-8")
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    print(run_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
