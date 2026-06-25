#!/usr/bin/env python3
"""Review AI suggestions in a monitoring capture file.

Two modes:
  - per-capture single suggestion: `review_capture.py <capture.md> --suggestion <id> --accept|--reject|--needs-edit "..."`
  - inbox listing: `review_capture.py --inbox [--project-root .]` prints a markdown checklist of all
    pending suggestions across captures; user edits the file's status fields directly (the file IS the UI).

Rejected suggestions are mirrored to `wiki/anti-patterns.md` so future agents won't re-suggest them.
"""
import argparse
import datetime as _dt
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import JsonlLogger, shared_writer_lock  # noqa: E402


AI_BLOCK_RE = re.compile(r"<!-- ai-suggestions-start -->(.*?)<!-- ai-suggestions-end -->", re.S)


def _yaml_escape(s):
    """Escape for double-quoted YAML scalar (newlines → \\n, quote → \\\")."""
    s = str(s)
    s = s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "")
    return s


def _yaml_quoted(s):
    return f'"{_yaml_escape(s)}"'


def find_project_root(start):
    p = Path(start).expanduser().resolve()
    for parent in [p, *p.parents]:
        if (parent / "PROJECT_INDEX.md").exists():
            return parent
    return None


def parse_suggestions(block_text):
    """Very small parser: split entries on lines starting with `- id:`."""
    entries = []
    cur = None
    for line in block_text.splitlines():
        if line.lstrip().startswith("- id:"):
            if cur is not None:
                entries.append(cur)
            cur = {"id": line.split(":", 1)[1].strip(), "_lines": [line]}
        elif cur is not None:
            cur["_lines"].append(line)
            m = re.match(r"\s+(\w+):\s*(.*)$", line)
            if m and m.group(1) not in cur:
                cur[m.group(1)] = m.group(2).strip()
    if cur is not None:
        entries.append(cur)
    return entries


def update_suggestion(text, suggestion_id, new_status, edit_text=None, reviewer=""):
    """Rewrite the ai_suggestions block, flipping one entry."""
    m = AI_BLOCK_RE.search(text)
    if not m:
        return text, False
    block = m.group(1)
    entries = parse_suggestions(block)
    today = _dt.date.today().isoformat()
    touched = False
    out = []
    for e in entries:
        if e["id"] == suggestion_id:
            touched = True
            for i, line in enumerate(e["_lines"]):
                if re.match(r"\s+status:", line):
                    e["_lines"][i] = re.sub(r"status:\s*\S+", f"status: {new_status}", line)
                if re.match(r"\s+reviewer:", line) and reviewer:
                    e["_lines"][i] = re.sub(r'reviewer:\s*".*?"', f'reviewer: {_yaml_quoted(reviewer)}', line)
                if re.match(r"\s+reviewed_at:", line):
                    e["_lines"][i] = re.sub(r'reviewed_at:\s*".*?"', f'reviewed_at: "{today}"', line)
                if edit_text and re.match(r"\s+text:", line) and new_status == "needs_edit":
                    m_line = re.match(r"(\s+)text:\s*(.*)$", line)
                    indent = m_line.group(1) if m_line else "  "
                    raw_val = (m_line.group(2) if m_line else "").strip()
                    # tolerate single-quote, double-quote, or bare scalar values
                    if raw_val.startswith(('"', "'")):
                        old_val = raw_val[1:-1] if raw_val.endswith(raw_val[0]) else raw_val[1:]
                    else:
                        old_val = raw_val
                    e["_lines"].insert(i + 1, f"{indent}original_text: {_yaml_quoted(old_val)}")
                    e["_lines"][i] = f"{indent}text: {_yaml_quoted(edit_text)}"
        out.extend(e["_lines"])
    if not touched:
        return text, False
    new_block = "\n".join(out)
    new_full = text[:m.start(1)] + "\n" + new_block + "\n" + text[m.end(1):]
    return new_full, True


def mirror_to_anti_patterns(project_root, capture_path, suggestion_id, suggestion_text, rationale):
    ap = project_root / "wiki" / "anti-patterns.md"
    if not ap.is_file():
        ap.write_text("# Anti-patterns\n\nRejected AI suggestions / patterns. Future agents check here before proposing.\n\n<!-- entries-end -->\n", encoding="utf-8")
    SENTINEL = "<!-- entries-end -->"
    entry = (
        f"\n- date: {_dt.date.today().isoformat()}\n"
        f"  origin: {_yaml_quoted(capture_path)}\n"
        f"  suggestion_id: {_yaml_quoted(suggestion_id)}\n"
        f"  text: {_yaml_quoted(suggestion_text)}\n"
        f"  rationale: {_yaml_quoted(rationale)}\n"
    )
    with shared_writer_lock(project_root, "anti_patterns"):
        text = ap.read_text(encoding="utf-8")
        if SENTINEL in text:
            text = text.replace(SENTINEL, entry.rstrip() + "\n\n" + SENTINEL, 1)
        else:
            text = text.rstrip() + "\n" + entry
        ap.write_text(text, encoding="utf-8")


def inbox(project_root):
    sites = project_root / "monitoring" / "sites"
    if not sites.is_dir():
        print("(no monitoring/sites yet)")
        return 0
    today = _dt.date.today().isoformat()
    print(f"# Capture review inbox — {today}\n")
    total = 0
    for cap in sorted(sites.rglob("captures/*.md")):
        text = cap.read_text(encoding="utf-8", errors="ignore")
        m = AI_BLOCK_RE.search(text)
        if not m:
            continue
        entries = parse_suggestions(m.group(1))
        pending = [e for e in entries if e.get("status", "").strip() == "pending"]
        if not pending:
            continue
        rel = cap.relative_to(project_root).as_posix()
        print(f"## {rel}")
        for e in pending:
            print(f"- [ ] {e['id']}  ({e.get('kind', 'unknown')}): {e.get('text', '')}")
        print()
        total += len(pending)
    print(f"_total pending: {total}_")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("capture", nargs="?", help="path to capture .md (omit if using --inbox)")
    parser.add_argument("--suggestion", help="suggestion id within the capture")
    parser.add_argument("--accept", action="store_true")
    parser.add_argument("--reject", action="store_true")
    parser.add_argument("--needs-edit", metavar="NEW_TEXT")
    parser.add_argument("--reason", default="", help="reason (recorded for reject)")
    parser.add_argument("--reviewer", default="")
    parser.add_argument("--inbox", action="store_true")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--log", action="store_true")
    args = parser.parse_args()

    project_root = find_project_root(args.project_root) or Path(args.project_root).expanduser().resolve()
    logger = JsonlLogger("review_capture", project_root=project_root if args.log else None)

    if args.inbox:
        return inbox(project_root)

    if not (args.capture and args.suggestion):
        parser.error("provide CAPTURE and --suggestion, or use --inbox")

    if sum([args.accept, args.reject, bool(args.needs_edit)]) != 1:
        parser.error("pick exactly one of --accept / --reject / --needs-edit")

    cap_path = Path(args.capture).expanduser().resolve()
    if not cap_path.is_file():
        print(f"error: capture not found: {cap_path}", file=sys.stderr)
        return 2

    text = cap_path.read_text(encoding="utf-8")

    if args.accept:
        new_status = "accepted"
    elif args.reject:
        new_status = "rejected"
    else:
        new_status = "needs_edit"

    edit_text = args.needs_edit
    with shared_writer_lock(project_root, f"capture:{cap_path.name}"):
        new_text, touched = update_suggestion(text, args.suggestion, new_status, edit_text=edit_text, reviewer=args.reviewer)
        if not touched:
            print(f"error: suggestion id={args.suggestion} not found in {cap_path}", file=sys.stderr)
            return 3
        cap_path.write_text(new_text, encoding="utf-8")

    if args.reject:
        # mirror to wiki/anti-patterns.md
        m = AI_BLOCK_RE.search(new_text)
        if m:
            for e in parse_suggestions(m.group(1)):
                if e["id"] == args.suggestion:
                    mirror_to_anti_patterns(
                        project_root, cap_path.relative_to(project_root).as_posix(),
                        args.suggestion, e.get("text", ""), args.reason or e.get("rationale", ""),
                    )
                    break

    logger.info("review", capture=str(cap_path), suggestion=args.suggestion, status=new_status)
    print(f"{cap_path}: {args.suggestion} → {new_status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
