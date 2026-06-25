#!/usr/bin/env python3
"""Verify VERSION ↔ agents/openai.yaml.version are in sync.

CI-friendly: exits 0 when synced, 1 when out of sync. Use as a pre-commit
hook or in PR CI.
"""
import re
import sys
from pathlib import Path


def find_repo_root(start):
    p = Path(start).expanduser().resolve()
    for parent in [p, *p.parents]:
        if (parent / "VERSION").exists():
            return parent
    return None


def main():
    root = find_repo_root(Path(__file__))
    if not root:
        print("error: VERSION file not found", file=sys.stderr)
        return 2
    version = (root / "VERSION").read_text().strip()
    yml = (root / "allincms-content-ops" / "agents" / "openai.yaml").read_text()
    m = re.search(r'^version:\s*"?([^"\s]+)"?\s*$', yml, re.M)
    if not m:
        print("warn: openai.yaml has no version field; run bump_version.py", file=sys.stderr)
        return 1
    yml_version = m.group(1)
    if version != yml_version:
        print(f"out of sync: VERSION={version} openai.yaml={yml_version}", file=sys.stderr)
        print("run: python3 allincms-content-ops/scripts/bump_version.py", file=sys.stderr)
        return 1
    print(f"in sync: {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
