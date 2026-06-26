#!/usr/bin/env python3
"""Suggest internal-link candidates for a draft.

Reads the draft's `tags`, `category`, `persona`, and `secondary_queries`
from frontmatter, then scans `web/published/index.md` for already-published
pages and scores them by overlap. Prints the top N candidates as
markdown-link snippets the author can paste.

Scoring is intentionally simple and explainable — every weight lives at
the top of this file. Fixture-based test under `tests/test_suggest_links.py`
locks the ranking so future weight tweaks surface in CI.
"""
import argparse
import re
import sys
from pathlib import Path

# Weights — covered by tests/test_suggest_links.py
W_TAG_OVERLAP = 3
W_SAME_PERSONA = 2
W_SAME_CATEGORY = 2
W_QUERY_TOKEN_HIT = 1


def parse_frontmatter(text):
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}
    data = {}
    last_key = None
    for line in text[4:end].splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if line.startswith(("  - ", "- ")) and last_key is not None:
            item = stripped[2:].strip().strip('"').strip("'")
            cur = data.get(last_key)
            if isinstance(cur, list):
                cur.append(item)
            elif cur in (None, ""):
                data[last_key] = [item]
            else:
                data[last_key] = [cur, item]
            continue
        if ":" in line and not line.startswith(" "):
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            if value.startswith("[") and value.endswith("]"):
                data[key] = [v.strip().strip('"').strip("'") for v in value[1:-1].split(",") if v.strip()]
            else:
                data[key] = value
            last_key = key
        else:
            last_key = None
    return data


def parse_published_index(text):
    """Extract published rows from web/published/index.md.

    Tolerant of the seed table shape; expects markdown table rows after the
    `| Date | URL | Type | Category | Tags | Persona | Primary query | Cover | Audit score | Source draft |`
    header. Returns list of dicts.
    """
    rows = []
    lines = text.splitlines()
    in_table = False
    for line in lines:
        line = line.strip()
        if line.startswith("|") and "Date" in line and "URL" in line:
            in_table = True
            continue
        if in_table and line.startswith("|---"):
            continue
        if in_table and not line.startswith("|"):
            in_table = False
            continue
        if in_table and line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) < 6:
                continue
            rows.append({
                "date": cells[0],
                "url": cells[1],
                "type": cells[2] if len(cells) > 2 else "",
                "category": cells[3] if len(cells) > 3 else "",
                "tags": [t.strip() for t in cells[4].split(",") if t.strip()] if len(cells) > 4 else [],
                "persona": cells[5] if len(cells) > 5 else "",
                "primary_query": cells[6] if len(cells) > 6 else "",
                "source_draft": cells[-1] if len(cells) > 9 else "",
            })
    return rows


def score_candidate(draft_fm, row):
    score = 0
    reasons = []

    draft_tags = set(t.lower() for t in (draft_fm.get("tags") or []) if t)
    row_tags = set(t.lower() for t in (row.get("tags") or []) if t)
    overlap = draft_tags & row_tags
    if overlap:
        score += W_TAG_OVERLAP * len(overlap)
        reasons.append(f"shared tags: {sorted(overlap)}")

    draft_persona = (draft_fm.get("persona") or "").strip().lower()
    row_persona = (row.get("persona") or "").strip().lower()
    if draft_persona and draft_persona == row_persona:
        score += W_SAME_PERSONA
        reasons.append(f"same persona ({draft_persona})")

    draft_category = (draft_fm.get("category") or "").strip().lower()
    row_category = (row.get("category") or "").strip().lower()
    if draft_category and draft_category == row_category:
        score += W_SAME_CATEGORY
        reasons.append(f"same category ({draft_category})")

    queries = draft_fm.get("secondary_queries") or []
    if isinstance(queries, str):
        queries = [queries]
    tokens = set()
    for q in queries:
        tokens.update(re.findall(r"\w+", str(q).lower()))
    primary = (row.get("primary_query") or "").lower()
    hits = tokens & set(re.findall(r"\w+", primary))
    if hits:
        score += W_QUERY_TOKEN_HIT * len(hits)
        reasons.append(f"query tokens: {sorted(hits)}")

    return score, reasons


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("draft", help="path to draft .md")
    parser.add_argument("--published-index", default=None, help="path to web/published/index.md (default: auto-detect from project root)")
    parser.add_argument("--top", type=int, default=5)
    args = parser.parse_args()

    draft_path = Path(args.draft).expanduser().resolve()
    if not draft_path.is_file():
        print(f"error: draft not found: {draft_path}", file=sys.stderr)
        return 2
    draft_fm = parse_frontmatter(draft_path.read_text(encoding="utf-8", errors="ignore"))

    if args.published_index:
        pi_path = Path(args.published_index).expanduser().resolve()
    else:
        # walk up looking for web/published/index.md
        cur = draft_path.parent
        pi_path = None
        for parent in [cur, *cur.parents]:
            candidate = parent / "web" / "published" / "index.md"
            if candidate.is_file():
                pi_path = candidate
                break
        if pi_path is None:
            print("error: could not auto-detect web/published/index.md; pass --published-index", file=sys.stderr)
            return 3

    rows = parse_published_index(pi_path.read_text(encoding="utf-8", errors="ignore"))
    if not rows:
        print("(no published rows found in index — nothing to suggest yet)")
        return 0

    scored = []
    for row in rows:
        score, reasons = score_candidate(draft_fm, row)
        if score > 0:
            scored.append((score, row, reasons))
    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[: args.top]

    if not top:
        print("(no overlap found — pick anchor pages by category from web/categories/index.md manually)")
        return 0

    print(f"# Internal link candidates for {draft_path.name}\n")
    print(f"draft persona={draft_fm.get('persona', '?')} category={draft_fm.get('category', '?')} tags={draft_fm.get('tags', [])}\n")
    for score, row, reasons in top:
        anchor = row.get("primary_query") or row.get("url", "[link]")
        print(f"- score={score}  [{anchor}]({row.get('url', '')})  ({'; '.join(reasons)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
