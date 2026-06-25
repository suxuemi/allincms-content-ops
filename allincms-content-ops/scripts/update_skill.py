#!/usr/bin/env python3
"""Pull latest skill from upstream while preserving project content.

Two modes (auto-detected):
  - Canonical: working tree clean → `git pull --ff-only` (cleanest)
  - Mixed: project content modified locally → surgical restore of skill paths
    only, then auto-commit the sync so the next run isn't confused by a
    dirty working tree it produced itself.

Skill paths come from upstream's tree (minus PROJECT_PATHS), NOT a
hardcoded list — handles upstream renames, new top-level dirs, and
deletions. Outputs `CHANGED-CONTRACT-FILES:` so the agent knows to
re-read SKILL.md / references/* / scripts/* before continuing.

Concurrent invocations are serialized via .locks/skill_update.lock.
"""
import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import JsonlLogger, shared_writer_lock  # noqa: E402


PROJECT_PATH_PREFIXES = (
    "wiki/", "web/", "raw/", "audits/", "monitoring/", "media/",
    "logs/", ".locks/",
)
PROJECT_FILE_EXACT = {"PROJECT_INDEX.md"}

CONTRACT_FILE_PREFIXES = (
    "allincms-content-ops/SKILL.md",
    "allincms-content-ops/references/",
    "allincms-content-ops/scripts/",
    "AGENTS.md", "CLAUDE.md", "WORKBUDDY.md",
)


def run(cmd, capture=True):
    return subprocess.run(cmd, capture_output=capture, text=True)


def is_project_path(p):
    p = p.strip()
    if p in PROJECT_FILE_EXACT:
        return True
    return any(p.startswith(pp) for pp in PROJECT_PATH_PREFIXES)


def detect_remote(override):
    if override:
        return override if run(["git", "remote", "get-url", override]).returncode == 0 else None
    for r in ("origin", "upstream"):
        if run(["git", "remote", "get-url", r]).returncode == 0:
            return r
    return None


def detect_default_branch(remote, override):
    if override:
        return override
    r = run(["git", "symbolic-ref", f"refs/remotes/{remote}/HEAD"])
    if r.returncode == 0:
        return r.stdout.strip().rsplit("/", 1)[-1]
    for b in ("main", "master"):
        if run(["git", "rev-parse", "--verify", f"{remote}/{b}"]).returncode == 0:
            return b
    return None


def zip_install_msg():
    print("error: this directory is not a git repo.", file=sys.stderr)
    print("       If you installed via zip, get the latest from", file=sys.stderr)
    print("         https://github.com/suxuemi/allincms-content-ops", file=sys.stderr)
    print("       and overwrite ONLY: allincms-content-ops/ + AGENTS.md / CLAUDE.md /", file=sys.stderr)
    print("         WORKBUDDY.md / README.md / INSTALL.md / QUICKSTART.md / LICENSE /", file=sys.stderr)
    print("         .gitignore / docs/", file=sys.stderr)
    print("       Do NOT touch: wiki/ web/ raw/ audits/ monitoring/ media/ PROJECT_INDEX.md", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="show what would change; don't write")
    parser.add_argument("--remote", help="override remote (default: auto-detect origin/upstream)")
    parser.add_argument("--branch", help="override branch (default: auto-detect remote HEAD)")
    parser.add_argument("--log", action="store_true")
    args = parser.parse_args()

    # 1. git repo?
    if run(["git", "rev-parse", "--git-dir"]).returncode != 0:
        zip_install_msg()
        return 2

    project_root = Path(run(["git", "rev-parse", "--show-toplevel"]).stdout.strip())
    logger = JsonlLogger("update_skill", project_root=project_root if args.log else None)

    # 2. detached HEAD → bail
    if run(["git", "symbolic-ref", "-q", "HEAD"]).returncode != 0:
        print("error: HEAD is detached. Checkout a branch first (e.g. `git checkout main`).", file=sys.stderr)
        logger.error("detached_head")
        return 3

    # 3. remote + branch detection
    remote = detect_remote(args.remote)
    if not remote:
        print("error: no `origin` or `upstream` remote configured.", file=sys.stderr)
        logger.error("no_remote")
        return 4
    branch = detect_default_branch(remote, args.branch)
    if not branch:
        print(f"error: cannot determine default branch of {remote}.", file=sys.stderr)
        logger.error("no_branch")
        return 4
    ref = f"{remote}/{branch}"

    # 4. fetch
    r = run(["git", "fetch", "--quiet", remote])
    if r.returncode != 0:
        print(f"error: cannot reach remote {remote} (network? auth?). stderr:\n{r.stderr}", file=sys.stderr)
        logger.error("fetch_failed", stderr=r.stderr[:400])
        return 5

    # 5. how far behind?
    behind = int(run(["git", "rev-list", "--count", f"HEAD..{ref}"]).stdout.strip() or "0")
    if behind == 0:
        print(f"skill is up to date with {ref}.")
        logger.info("up_to_date", ref=ref)
        return 0

    print(f"skill is {behind} commit(s) behind {ref}")

    # 6. Local commits on skill paths that aren't in upstream → bail (would lose them)
    skill_path_args = [p for p in CONTRACT_FILE_PREFIXES + ("README.md", "INSTALL.md", "QUICKSTART.md", "LICENSE", ".gitignore", "docs")]
    r = run(["git", "log", f"{ref}..HEAD", "--oneline", "--"] + skill_path_args)
    if r.stdout.strip():
        print("warning: you have local commits on skill paths that aren't on upstream:", file=sys.stderr)
        for l in r.stdout.splitlines()[:5]:
            print(f"  {l}", file=sys.stderr)
        print("aborting. Push these to upstream first, or move them off skill paths.", file=sys.stderr)
        logger.error("local_commits_on_skill")
        return 6

    # 7. Skill-path dirty (uncommitted) → bail
    r = run(["git", "status", "--porcelain"])
    dirty_lines = [l for l in r.stdout.splitlines() if l.strip()]
    skill_dirty = [l for l in dirty_lines if not is_project_path(l[3:].split(" -> ")[-1])]
    project_dirty = [l for l in dirty_lines if is_project_path(l[3:].split(" -> ")[-1])]
    if skill_dirty:
        print("warning: skill paths have uncommitted edits:", file=sys.stderr)
        for l in skill_dirty[:10]:
            print(f"  {l}", file=sys.stderr)
        print("aborting. Commit or stash these before updating.", file=sys.stderr)
        logger.error("skill_paths_dirty")
        return 7

    # 8. preview
    print(f"\nincoming changes (HEAD..{ref}):")
    print(run(["git", "diff", "--stat", f"HEAD..{ref}"]).stdout)

    if args.dry_run:
        print("(dry-run; no changes applied)")
        return 0

    # 9. Capture pre-update SHA so we can compute CHANGED-CONTRACT-FILES afterwards
    pre_sha = run(["git", "rev-parse", "HEAD"]).stdout.strip()

    with shared_writer_lock(project_root, "skill_update"):
        if project_dirty:
            # Mixed: surgical restore of upstream skill paths only, then auto-commit
            print("mode: mixed (project content modified) — surgical sync of skill paths")
            r = run(["git", "ls-tree", "-r", "--name-only", ref])
            upstream_paths = [p for p in r.stdout.splitlines() if not is_project_path(p)]
            for p in upstream_paths:
                run(["git", "checkout", ref, "--", p])
            # delete local skill files that upstream removed
            r = run(["git", "ls-tree", "-r", "--name-only", "HEAD"])
            local_paths = [p for p in r.stdout.splitlines() if not is_project_path(p)]
            removed = [p for p in local_paths if p not in set(upstream_paths)]
            for p in removed:
                run(["git", "rm", "--", p])
            # auto-commit the sync so the next run sees a clean tree
            sync_sha = run(["git", "rev-parse", "--short", ref]).stdout.strip()
            r = run(["git", "commit", "-m", f"chore(skill): sync to {ref} ({sync_sha})"])
            if r.returncode != 0:
                # No diff to commit (project's skill files already matched upstream tree, only metadata behind)
                run(["git", "merge", "--ff-only", ref])
        else:
            # Canonical: clean working tree → simple ff-only pull
            print("mode: canonical (working tree clean) — git pull --ff-only")
            r = run(["git", "pull", "--ff-only", remote, branch])
            if r.returncode != 0:
                print(r.stderr, file=sys.stderr)
                logger.error("ff_only_failed", stderr=r.stderr[:400])
                return 8

    # 10. CHANGED-CONTRACT-FILES — for the agent to re-read
    r = run(["git", "diff", "--name-only", f"{pre_sha}..HEAD"])
    changed = r.stdout.splitlines() if r.returncode == 0 else []
    contract_changed = [p for p in changed if p.startswith(CONTRACT_FILE_PREFIXES)]
    if contract_changed:
        print("\nCHANGED-CONTRACT-FILES:")
        for p in contract_changed:
            print(f"  {p}")
        print("AGENT MUST RE-READ THESE BEFORE NEXT ACTION.")
    logger.info("updated", behind=behind, contract_changed=len(contract_changed), pre=pre_sha)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
