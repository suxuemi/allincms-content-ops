#!/usr/bin/env python3
"""Batch upload images to Cloudflare R2 (S3-compatible).

Same CLI shape as picgo_batch_upload.py:
  python3 r2_upload.py <dir-or-files...> [--out manifest.json]

Reads credentials from ~/.config/allincms-content-ops/r2.toml
(populated by r2_setup.py). Never prints secret_access_key. Masks
access_key_id as `xxx...xxx` in any output.

Returns public URLs (via custom_domain if set, else <bucket>.<account>.r2.cloudflarestorage.com).

Per-file behavior:
  - Hashes the file content for an idempotent object key (re-uploading the
    same image returns the same URL).
  - Writes a manifest with `[file → url]` rows.
  - Appends rows to media/index.md (SENTINEL-anchored, like picgo).
"""
import argparse
import datetime as _dt
import hashlib
import json
import logging
import os
import sys
from pathlib import Path

CONFIG_FILE = Path.home() / ".config" / "allincms-content-ops" / "r2.toml"
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}

sys.path.insert(0, str(Path(__file__).parent))
try:
    from _lib import JsonlLogger, shared_writer_lock  # type: ignore
except ImportError:
    JsonlLogger = None
    shared_writer_lock = None

logger = logging.getLogger("r2_upload")


def mask_key(s):
    if not s or len(s) < 10:
        return "***"
    return f"{s[:4]}...{s[-4:]}"


def read_config():
    if not CONFIG_FILE.is_file():
        print(f"error: R2 not configured. Run: python3 allincms-content-ops/scripts/r2_setup.py", file=sys.stderr)
        return None
    out = {}
    for line in CONFIG_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def make_key(path, content_hash):
    # objects/<sha256-prefix>/<basename>
    return f"objects/{content_hash[:8]}/{path.name}"


def public_url(cfg, key):
    if cfg.get("custom_domain"):
        return f"https://{cfg['custom_domain'].rstrip('/')}/{key}"
    # Cloudflare's default public URL pattern needs the bucket to be "publicly accessible"
    # (Settings → Public Access → Allow Access in dashboard). Otherwise use the bucket
    # endpoint with a presigned URL — but for content ops the assumption is public images.
    return f"https://{cfg['account_id']}.r2.cloudflarestorage.com/{cfg['bucket']}/{key}"


def upload_one(client, cfg, path):
    content = path.read_bytes()
    sha = hashlib.sha256(content).hexdigest()
    key = make_key(path, sha)
    # idempotent: check if exists first
    try:
        client.head_object(Bucket=cfg["bucket"], Key=key)
        logger.info("already_present", extra={"path": str(path), "key": key})
    except Exception:
        client.put_object(Bucket=cfg["bucket"], Key=key, Body=content, ContentType=guess_mime(path))
        logger.info("uploaded", extra={"path": str(path), "key": key, "bytes": len(content)})
    return {"source": str(path), "url": public_url(cfg, key), "key": key, "sha256": sha[:16]}


def guess_mime(path):
    return {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".gif": "image/gif",
        ".svg": "image/svg+xml",
    }.get(path.suffix.lower(), "application/octet-stream")


def find_project_root():
    p = Path.cwd().resolve()
    for parent in [p, *p.parents]:
        if (parent / "PROJECT_INDEX.md").exists():
            return parent
    return None


def append_media_index(project_root, entries):
    p = project_root / "media" / "index.md"
    if not p.is_file():
        return
    today = _dt.date.today().isoformat()
    rows = []
    for e in entries:
        rows.append(f"| {e['source']} | (r2 {today}) | {e['url']} | | |")
    if not rows:
        return
    if shared_writer_lock:
        with shared_writer_lock(project_root, "media_index"):
            with p.open("a", encoding="utf-8") as f:
                f.write("\n".join(rows) + "\n")
    else:
        with p.open("a", encoding="utf-8") as f:
            f.write("\n".join(rows) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("inputs", nargs="+", help="files and/or directories")
    parser.add_argument("--out", default=None, help="manifest JSON path (default: media/uploaded/r2-<date>.json)")
    parser.add_argument("--no-index", action="store_true", help="don't append to media/index.md")
    parser.add_argument("--log", action="store_true", help="emit JSONL run log under logs/")
    args = parser.parse_args()

    cfg = read_config()
    if not cfg:
        return 2

    try:
        import boto3  # type: ignore
    except ImportError:
        print("error: boto3 not installed. Install with: pip install boto3", file=sys.stderr)
        return 3

    print(f"R2: account={mask_key(cfg.get('account_id', ''))} bucket={cfg.get('bucket')} key={mask_key(cfg.get('access_key_id', ''))}")
    client = boto3.client(
        "s3",
        endpoint_url=f"https://{cfg['account_id']}.r2.cloudflarestorage.com",
        aws_access_key_id=cfg["access_key_id"],
        aws_secret_access_key=cfg["secret_access_key"],
        region_name="auto",
    )

    files = []
    for src in args.inputs:
        p = Path(src).expanduser().resolve()
        if p.is_dir():
            files.extend(sorted(p.rglob("*") if False else p.glob("*")))
        elif p.is_file():
            files.append(p)
    files = [f for f in files if f.is_file() and f.suffix.lower() in IMAGE_EXTS]
    if not files:
        print("error: no image files found in inputs", file=sys.stderr)
        return 2

    entries = []
    for f in files:
        try:
            entries.append(upload_one(client, cfg, f))
        except Exception as e:
            print(f"  ✗ {f}: {e}", file=sys.stderr)

    project_root = find_project_root()
    if args.out:
        out_path = Path(args.out).expanduser().resolve()
    elif project_root:
        out_dir = project_root / "media" / "uploaded"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"r2-{_dt.date.today().isoformat()}.json"
    else:
        out_path = Path("r2-manifest.json").resolve()

    manifest = {
        "host": "r2",
        "bucket": cfg["bucket"],
        "custom_domain": cfg.get("custom_domain"),
        "uploaded": len(entries),
        "files": entries,
    }
    out_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(out_path)

    appended = 0
    if project_root and not args.no_index:
        try:
            append_media_index(project_root, entries)
            appended = len(entries)
        except Exception as e:
            print(f"warning: media/index.md not updated: {e}", file=sys.stderr)
    print(f"appended_to_media_index={appended}")

    if args.log and JsonlLogger and project_root:
        JsonlLogger("r2_upload", project_root=project_root).info(
            "run_end", uploaded=len(entries), manifest=str(out_path)
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
