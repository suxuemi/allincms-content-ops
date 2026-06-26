#!/usr/bin/env python3
"""Diagnose the environment so newbies aren't surprised mid-workflow.

One stop check before first-contact:
  - critical tools (git, python ≥ 3.9) — strong / missing
  - content extractors (pdftotext, pandoc) — strong / degraded / missing
  - publish prerequisites (PicGo server, Current Site fields filled) — strong / degraded / missing
  - skill-internal state (VERSION file, web/published index seeded) — strong / degraded / missing

Output uses the `tooling-matrix.md` vocabulary — three tiers `strong` / `degraded` / `missing`.
Each finding links to a `references/tooling-matrix.md` anchor for remediation.
Result cached to `.doctor-cache.json` (gitignored); first-contact Phase -1
reads the cache if present and < 24h old.

Exit codes:
  0 — all strong, or only degraded
  1 — one or more missing in publish-required category
  2 — critical missing (git / python)
"""
import argparse
import datetime as _dt
import json
import shutil
import socket
import subprocess
import sys
from pathlib import Path

# Import logger; degrade gracefully if _lib is missing (e.g. running outside skill)
try:
    sys.path.insert(0, str(Path(__file__).parent))
    from _lib import JsonlLogger  # noqa: E402
except ImportError:
    JsonlLogger = None  # type: ignore


TM_ANCHOR = "https://github.com/suxuemi/allincms-content-ops/blob/main/allincms-content-ops/references/tooling-matrix.md"


def find_project_root(start):
    p = Path(start).expanduser().resolve()
    for parent in [p, *p.parents]:
        if (parent / "VERSION").exists() or (parent / "PROJECT_INDEX.md").exists():
            return parent
    return None


def tier_label(tier):
    return {"strong": "[OK]  ", "degraded": "[WARN]", "missing": "[FAIL]"}[tier]


def check_git():
    if not shutil.which("git"):
        return "missing", "install git: https://git-scm.com/downloads", f"{TM_ANCHOR}#git"
    try:
        v = subprocess.run(["git", "--version"], capture_output=True, text=True, timeout=3)
        return "strong", v.stdout.strip(), f"{TM_ANCHOR}#git"
    except Exception as e:
        return "degraded", f"git present but errored: {e}", f"{TM_ANCHOR}#git"


def check_python():
    v = sys.version_info
    if v < (3, 9):
        return "missing", f"python {v.major}.{v.minor} < 3.9; upgrade for f-string features used in scripts", f"{TM_ANCHOR}#python"
    return "strong", f"python {v.major}.{v.minor}.{v.micro}", f"{TM_ANCHOR}#python"


def check_pdftotext():
    if not shutil.which("pdftotext"):
        return "degraded", "missing pdftotext (poppler-utils). Workaround: convert PDFs to .md manually before ingest. To install: brew install poppler / apt install poppler-utils", f"{TM_ANCHOR}#pdf-extraction"
    return "strong", "pdftotext present (PDFs ingest automatically)", f"{TM_ANCHOR}#pdf-extraction"


def check_pandoc():
    if not shutil.which("pandoc"):
        return "degraded", "missing pandoc (Word/PPT → md). Workaround: export to .md manually. To install: brew install pandoc / apt install pandoc", f"{TM_ANCHOR}#docx-pptx-extraction"
    return "strong", "pandoc present (.docx/.pptx ingest automatically)", f"{TM_ANCHOR}#docx-pptx-extraction"


def check_picgo():
    try:
        with socket.create_connection(("127.0.0.1", 36677), timeout=1):
            return "strong", "PicGo server reachable at 127.0.0.1:36677", f"{TM_ANCHOR}#picgo"
    except OSError:
        return "degraded", "PicGo server not running. Launch PicGo desktop app and enable PicGo-Server in settings. (Optional — only needed when batch-uploading images.)", f"{TM_ANCHOR}#picgo"


def check_current_site(project_root):
    pi = project_root / "PROJECT_INDEX.md" if project_root else None
    if not pi or not pi.is_file():
        return "missing", "PROJECT_INDEX.md not found. Run scripts/init_content_ops_project.py with --site-id etc.", f"{TM_ANCHOR}#current-site"
    text = pi.read_text(encoding="utf-8", errors="ignore")
    fields = ["AllinCMS site id", "Front-end domain", "Workspace URL", "Browser profile", "Default content language"]
    empty = []
    for f in fields:
        # look for "- {f}:" followed by non-whitespace or end-of-line
        import re as _re
        m = _re.search(rf"^-\s*{_re.escape(f)}:\s*(.*)$", text, _re.M)
        if not m or not m.group(1).strip() or m.group(1).strip() in {"TODO", "<your-domain>"}:
            empty.append(f)
    if empty:
        return "missing", f"Current Site missing: {', '.join(empty)}. Re-init or hand-fill PROJECT_INDEX.md.", f"{TM_ANCHOR}#current-site"
    return "strong", "all 5 Current Site fields populated", f"{TM_ANCHOR}#current-site"


def check_published_index(project_root):
    pi = project_root / "web" / "published" / "index.md" if project_root else None
    if not pi or not pi.is_file():
        return "degraded", "web/published/index.md not found; suggest_internal_links.py will return empty", f"{TM_ANCHOR}#published-index"
    text = pi.read_text(encoding="utf-8", errors="ignore")
    # count non-header table rows
    data_rows = [l for l in text.splitlines() if l.startswith("|") and not l.startswith("|---") and "Date" not in l and "URL" not in l[:20]]
    if not data_rows:
        return "degraded", "web/published/index.md has no published rows yet. First publish will seed it.", f"{TM_ANCHOR}#published-index"
    return "strong", f"{len(data_rows)} published row(s) — suggest_internal_links has material to score", f"{TM_ANCHOR}#published-index"


def check_version_file(project_root):
    vf = project_root / "VERSION" if project_root else None
    if not vf or not vf.is_file():
        return "missing", "VERSION file absent. This skill is unversioned in your local; pull latest from upstream.", f"{TM_ANCHOR}#version"
    return "strong", f"local skill version: v{vf.read_text().strip()}", f"{TM_ANCHOR}#version"


CHECKS = [
    ("git",            "critical",         check_git),
    ("python",         "critical",         check_python),
    ("pdftotext",      "ingest",           check_pdftotext),
    ("pandoc",         "ingest",           check_pandoc),
    ("picgo",          "media",            check_picgo),
    ("current_site",   "publish",          lambda pr=None: check_current_site(pr)),
    ("published_index","internal_links",   lambda pr=None: check_published_index(pr)),
    ("version_file",   "version",          lambda pr=None: check_version_file(pr)),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("project_root", nargs="?", default=".")
    parser.add_argument("--json", action="store_true", help="output machine-readable JSON")
    parser.add_argument("--no-cache", action="store_true", help="do not write .doctor-cache.json")
    args = parser.parse_args()

    project_root = find_project_root(args.project_root) or Path(args.project_root).expanduser().resolve()

    results = []
    for name, cat, fn in CHECKS:
        try:
            if fn.__code__.co_argcount == 0:
                tier, msg, link = fn()
            else:
                tier, msg, link = fn(project_root)
        except Exception as e:
            tier, msg, link = "missing", f"check raised {type(e).__name__}: {e}", f"{TM_ANCHOR}#unknown"
        results.append({"name": name, "category": cat, "tier": tier, "message": msg, "link": link})

    if args.json:
        print(json.dumps({
            "version": 1,
            "generated_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
            "results": results,
        }, indent=2, ensure_ascii=False))
    else:
        print(f"# skill doctor — {_dt.date.today().isoformat()}\n")
        for r in results:
            print(f"{tier_label(r['tier'])}  {r['name']:18s}  ({r['category']})  {r['message']}")
            if r['tier'] != 'strong':
                print(f"           → {r['link']}")
        # summary
        missing = [r for r in results if r['tier'] == 'missing']
        publish_blocking = [r for r in missing if r['category'] in {"critical", "publish"}]
        critical_miss = [r for r in missing if r['category'] == "critical"]
        print()
        if critical_miss:
            print(f"!! {len(critical_miss)} critical tool missing — fix before doing anything else")
        elif publish_blocking:
            print(f"!  {len(publish_blocking)} publish-required item missing — can still draft, can't publish yet")
        else:
            degraded = [r for r in results if r['tier'] == 'degraded']
            if degraded:
                print(f"ok — {len(degraded)} optional item degraded (workaround available)")
            else:
                print("ok — all systems strong")

    if not args.no_cache and project_root:
        cache = {
            "version": 1,
            "generated_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
            "results": results,
        }
        (project_root / ".doctor-cache.json").write_text(json.dumps(cache, indent=2, ensure_ascii=False))

    if JsonlLogger and project_root:
        try:
            JsonlLogger("doctor", project_root=project_root).info(
                "ran",
                strong=sum(1 for r in results if r['tier'] == 'strong'),
                degraded=sum(1 for r in results if r['tier'] == 'degraded'),
                missing=sum(1 for r in results if r['tier'] == 'missing'),
            )
        except Exception:
            pass

    critical_miss = sum(1 for r in results if r['tier'] == 'missing' and r['category'] == 'critical')
    if critical_miss:
        return 2
    publish_miss = sum(1 for r in results if r['tier'] == 'missing' and r['category'] in {'critical', 'publish'})
    return 1 if publish_miss else 0


if __name__ == "__main__":
    raise SystemExit(main())
