#!/usr/bin/env python3
import argparse
import datetime as dt
import html.parser
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urlparse


TEXT_EXTS = {".md", ".txt", ".csv", ".json", ".yaml", ".yml", ".html", ".htm", ".xml"}
MEDIA_EXTS = {".pdf", ".ppt", ".pptx", ".doc", ".docx", ".mp4", ".mov", ".m4v", ".avi"}


class TextExtractor(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip = False

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript"}:
            self.skip = True
        if tag in {"p", "br", "h1", "h2", "h3", "li", "tr"}:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript"}:
            self.skip = False

    def handle_data(self, data):
        if not self.skip:
            text = " ".join(data.split())
            if text:
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
    return slug[:80] or "source"


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


def run_converter(command):
    try:
        proc = subprocess.run(command, check=False, capture_output=True, text=True)
    except FileNotFoundError:
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout


def extract_file(path):
    suffix = path.suffix.lower()
    if suffix in TEXT_EXTS:
        text = path.read_text(encoding="utf-8", errors="ignore")
        if suffix in {".html", ".htm"}:
            parser = TextExtractor()
            parser.feed(text)
            return parser.text()
        return text
    if suffix == ".pdf":
        out = run_converter(["pdftotext", str(path), "-"])
        if out:
            return out
        return "__EXTRACTOR_MISSING__:pdftotext (brew install poppler / apt install poppler-utils) OR convert to .md manually and re-run"
    if suffix in {".docx", ".doc", ".pptx", ".ppt"}:
        out = run_converter(["pandoc", str(path), "-t", "markdown"])
        if out:
            return out
        return f"__EXTRACTOR_MISSING__:pandoc (brew install pandoc / apt install pandoc) OR convert {suffix} to .md manually and re-run"
    return ""


def fetch_url(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": "allincms-content-ops/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        content_type = resp.headers.get("Content-Type", "")
        data = resp.read()
    suffix = ".html" if "html" in content_type else ".bin"
    target = dest / f"source{suffix}"
    target.write_bytes(data)
    return target, content_type


def make_markdown(source_name, source_ref, source_type, rights, extracted_text):
    today = dt.date.today().isoformat()
    body = extracted_text.strip()
    if len(body) > 60000:
        body = body[:60000] + "\n\n[truncated]\n"
    if body.startswith("__EXTRACTOR_MISSING__:"):
        # Surface this loudly — first-contact Phase 2.5 brief warns that AI must
        # NOT silently draft from "Extraction unavailable" content (Fprocess.2).
        body = "EXTRACTION FAILED: " + body[len("__EXTRACTOR_MISSING__:"):]
    if not body:
        body = "Extraction unavailable. Keep the original source and summarize manually before compiling wiki pages."
    return f"""---
source_name: "{source_name}"
source_ref: "{source_ref}"
source_type: "{source_type}"
collected_at: "{today}"
rights: "{rights}"
extraction_method: "ingest_sources.py"
linked_wiki_pages: []
---

# {source_name}

{body}
"""


def ingest_one(root, source, rights):
    today = dt.date.today().isoformat()
    parsed = urlparse(source)
    is_url = parsed.scheme in {"http", "https"}
    source_name = parsed.netloc + parsed.path if is_url else Path(source).name
    source_name = source_name.strip("/") or "source"
    folder = root / "raw" / f"{today}-{slugify(source_name)}"
    folder.mkdir(parents=True, exist_ok=True)

    if is_url:
        original, content_type = fetch_url(source, folder)
        source_type = "web"
        source_ref = source
    else:
        input_path = Path(source).expanduser().resolve()
        if not input_path.exists():
            raise FileNotFoundError(source)
        original = folder / input_path.name
        if input_path.is_file():
            shutil.copy2(input_path, original)
        else:
            shutil.copytree(input_path, original, dirs_exist_ok=True)
        source_type = input_path.suffix.lower().lstrip(".") or "directory"
        content_type = ""
        source_ref = str(input_path)

    extracted = extract_file(original) if original.is_file() else ""
    extracted_path = folder / "extracted.md"
    extracted_path.write_text(make_markdown(source_name, source_ref, source_type, rights, extracted), encoding="utf-8")

    raw_index = root / "raw" / "index.md"
    ensure_index(raw_index, "Raw Index", "| Date | Source | Type | Rights | Extracted | Wiki links | Notes |\n|---|---|---|---|---|---|---|")
    append_line(raw_index, f"| {today} | {source_ref} | {source_type} | {rights} | `{extracted_path.relative_to(root)}` |  | {content_type} |")
    return extracted_path


def main():
    parser = argparse.ArgumentParser(description="Ingest files or URLs into raw/ and create extracted Markdown.")
    parser.add_argument("project_root")
    parser.add_argument("sources", nargs="+", help="files, directories, or URLs")
    parser.add_argument("--rights", default="unknown", help="rights/source permission note")
    args = parser.parse_args()
    root = Path(args.project_root).expanduser().resolve()
    if not (root / "raw").exists():
        print(f"Missing raw/ under project root: {root}", file=sys.stderr)
        return 2
    outputs = []
    extractor_misses = 0
    for source in args.sources:
        out = ingest_one(root, source, args.rights)
        outputs.append(out)
        # Surface extractor-missing failures so first-contact Phase 2.5 can't silently draft from empty content (Fprocess.2).
        if out and "EXTRACTION FAILED:" in Path(out).read_text(encoding="utf-8", errors="ignore"):
            extractor_misses += 1
            print(f"warning: extraction failed for {source} — see {out}", file=sys.stderr)
    for path in outputs:
        print(path)
    if extractor_misses:
        print(f"\n{extractor_misses} source(s) failed extraction; install the missing extractor OR convert to .md and re-ingest before the AI drafts from these raw files.", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
