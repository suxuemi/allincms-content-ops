#!/usr/bin/env python3
"""One-line capture: route a quick note into wiki/lessons.md or wiki/backlog.md.

Usage:
  python3 scripts/note.py "we should try X" --kind idea
  python3 scripts/note.py "every draft must cite a source URL" --kind rule --why "audit missed a stock photo"

`--kind` decides the destination per references/routing-matrix.md:
  idea | todo | question | external  → wiki/backlog.md   (priority: med, status: open)
  rule | correction                  → wiki/lessons.md   (status: proposed)

The whole point: capture cost low enough that nothing gets lost in chat.
"""
import argparse
import datetime as _dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import JsonlLogger, shared_writer_lock  # noqa: E402


BACKLOG_KINDS = {
    "idea": "idea",
    "todo": "todo",
    "question": "question",
    "external": "external_read",
}

LESSONS_KINDS = {
    "rule": "new_scenario",
    "correction": "user_correction",
}

# Reverse map: accept the YAML trigger value as a CLI alias too, so `--kind new_scenario` works the same as `--kind rule`.
TRIGGER_ALIASES = {v: k for k, v in {**BACKLOG_KINDS, **LESSONS_KINDS}.items()}

# Sentinel that note.py looks for to anchor insertion safely, even when the
# target file contains embedded ``` (block scalars with patches, etc.).
SENTINEL = "<!-- entries-end -->"


def find_project_root(start):
    p = Path(start).expanduser().resolve()
    for parent in [p, *p.parents]:
        if (parent / "PROJECT_INDEX.md").exists():
            return parent
    return None


def yaml_escape(s):
    s = (s or "").strip()
    if not s:
        return '""'
    if any(c in s for c in '"\'\n#:'):
        return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return s


def _insert_entry(text, entry):
    """Anchor on SENTINEL when present; otherwise insert above the last
    line that is *exactly* ``` (avoids hitting fences embedded inside block scalars)."""
    if SENTINEL in text:
        return text.replace(SENTINEL, entry.rstrip() + "\n\n" + SENTINEL, 1)
    lines = text.splitlines()
    idx = next((i for i in range(len(lines) - 1, -1, -1) if lines[i].strip() == "```"), None)
    if idx is None:
        return text.rstrip() + "\n" + entry
    lines.insert(idx, entry.rstrip())
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def append_backlog(project_root, kind, note, context, priority):
    path = project_root / "wiki" / "backlog.md"
    if not path.is_file():
        print(f"error: {path} missing — run init_content_ops_project.py first", file=sys.stderr)
        return 2
    entry = f"""
- date: {_dt.date.today().isoformat()}
  trigger: {BACKLOG_KINDS[kind]}
  note: {yaml_escape(note)}
  context: {yaml_escape(context)}
  priority: {priority}
  status: open
"""
    with shared_writer_lock(project_root, "backlog"):
        text = path.read_text(encoding="utf-8")
        path.write_text(_insert_entry(text, entry), encoding="utf-8")
    print(f"appended to {path}")
    return 0


def append_lessons(project_root, kind, note, context, scope, destination):
    path = project_root / "wiki" / "lessons.md"
    if not path.is_file():
        print(f"error: {path} missing — run init_content_ops_project.py first", file=sys.stderr)
        return 2
    entry = f"""
- date: {_dt.date.today().isoformat()}
  trigger: {LESSONS_KINDS[kind]}
  rule: {yaml_escape(note)}
  why: {yaml_escape(context)}
  scope: {scope}
  proposed_destination: {yaml_escape(destination)}
  status: proposed
"""
    with shared_writer_lock(project_root, "lessons"):
        text = path.read_text(encoding="utf-8")
        path.write_text(_insert_entry(text, entry), encoding="utf-8")
    print(f"appended to {path}")
    return 0


def main():
    epilog = "kind → trigger mapping (CLI also accepts the trigger name as an alias):\n" + "\n".join(
        f"  {k:12s} → {v}" for k, v in {**BACKLOG_KINDS, **LESSONS_KINDS}.items()
    )
    parser = argparse.ArgumentParser(description=__doc__, epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("note", help="the note in plain text, one sentence")
    parser.add_argument("--kind", required=True,
                        choices=list(BACKLOG_KINDS) + list(LESSONS_KINDS) + list(TRIGGER_ALIASES),
                        help="route by kind (or by trigger alias — see epilog mapping)")
    parser.add_argument("--why", default="", help="context / reason (used as `why` for lessons or `context` for backlog)")
    parser.add_argument("--priority", default="med", choices=["low", "med", "high"], help="backlog only")
    parser.add_argument("--scope", default="project", choices=["skill", "project"], help="lessons only")
    parser.add_argument("--destination", default="TBD — review and assign before merging", help="lessons only: proposed_destination")
    parser.add_argument("--project-root", default=".", help="project root (default .)")
    parser.add_argument("--log", action="store_true")
    args = parser.parse_args()

    project_root = find_project_root(args.project_root) or Path(args.project_root).expanduser().resolve()
    logger = JsonlLogger("note", project_root=project_root if args.log else None)
    kind = TRIGGER_ALIASES.get(args.kind, args.kind)
    logger.info("capture", kind=kind, note=args.note[:120])

    if kind in BACKLOG_KINDS:
        return append_backlog(project_root, kind, args.note, args.why, args.priority)
    return append_lessons(project_root, kind, args.note, args.why, args.scope, args.destination)


if __name__ == "__main__":
    raise SystemExit(main())
