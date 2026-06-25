#!/usr/bin/env python3
"""Sync `agents/openai.yaml` version from `/VERSION`.

`VERSION` is the single source of truth. This script propagates the value
into the Codex registry manifest. Hand-editing `openai.yaml.version` is
forbidden — `check_version_sync.py` will fail CI.
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
    if not re.match(r"^\d+\.\d+\.\d+(-[A-Za-z0-9.-]+)?$", version):
        print(f"error: invalid semver in VERSION: {version!r}", file=sys.stderr)
        return 3
    yml = root / "allincms-content-ops" / "agents" / "openai.yaml"
    text = yml.read_text()
    if re.search(r"^version:", text, re.M):
        new_text = re.sub(r"^version:.*$", f'version: "{version}"', text, count=1, flags=re.M)
    else:
        new_text = text.rstrip() + f'\nversion: "{version}"\n'
    if new_text != text:
        yml.write_text(new_text)
        print(f"openai.yaml version → {version}")
    else:
        print(f"openai.yaml already at {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
