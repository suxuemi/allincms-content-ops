#!/usr/bin/env python3
"""Batch upload images through a local PicGo server.

PicGo (https://github.com/Molunerfinn/PicGo) exposes a /upload HTTP endpoint
on 127.0.0.1:36677 by default. This script POSTs a JSON list of absolute
local paths, captures the returned remote URLs, writes a manifest, and
appends rows to `media/index.md` when invoked under a content-ops project.
"""
import argparse
import datetime as _dt
import json
import os
import socket
import sys
from pathlib import Path
from urllib import error as _urlerror, request

sys.path.insert(0, str(Path(__file__).parent))
from _lib import JsonlLogger, shared_writer_lock  # noqa: E402


IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}


def post_json(url, payload, timeout=60):
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def is_listening(host, port, timeout=2):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def find_project_root(start):
    p = Path(start).expanduser().resolve()
    if p.is_file():
        p = p.parent
    for parent in [p, *p.parents]:
        if (parent / "PROJECT_INDEX.md").exists():
            return parent
    return None


def append_media_index(project_root, entries):
    """Append uploaded rows to media/index.md (locked)."""
    path = project_root / "media" / "index.md"
    if not path.is_file():
        return 0
    today = _dt.date.today().isoformat()
    rows = []
    for e in entries:
        if not e.get("url"):
            continue
        src = e["source"]
        url = e["url"]
        rows.append(f"| {src} | (uploaded {today}) | {url} | | |")
    if not rows:
        return 0
    with shared_writer_lock(project_root, "media_index"):
        with path.open("a", encoding="utf-8") as f:
            f.write("\n".join(rows) + "\n")
    return len(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", help="image file or directory")
    parser.add_argument("--out", default=None, help="manifest JSON path; default: <project>/media/uploaded/picgo-<date>.json or ./picgo-manifest.json")
    parser.add_argument("--server", default=os.environ.get("PICGO_SERVER", "http://127.0.0.1:36677"))
    parser.add_argument("--endpoint", default=os.environ.get("PICGO_ENDPOINT", "/upload"))
    parser.add_argument("--no-index", action="store_true", help="don't append rows to media/index.md")
    parser.add_argument("--log", action="store_true", help="write structured JSONL log to logs/picgo_batch_upload-<date>.jsonl")
    parser.add_argument("--dry-run", action="store_true", help="list what would be uploaded without contacting PicGo")
    args = parser.parse_args()

    src = Path(args.input).expanduser().resolve()
    project_root = find_project_root(src)
    logger = JsonlLogger("picgo_batch_upload", project_root=project_root if (args.log and project_root) else None)

    if src.is_dir():
        files = [p for p in sorted(src.rglob("*")) if p.is_file() and p.suffix.lower() in IMAGE_EXTS]
    elif src.is_file() and src.suffix.lower() in IMAGE_EXTS:
        files = [src]
    else:
        print(f"error: input is not an image or a directory containing images: {src}", file=sys.stderr)
        logger.error("invalid_input", input=str(src))
        return 2

    if not files:
        print(f"error: no uploadable images under {src} (supported: {sorted(IMAGE_EXTS)})", file=sys.stderr)
        logger.warn("empty_input", input=str(src))
        return 2

    if args.dry_run:
        print(f"dry-run: would upload {len(files)} file(s) via {args.server}{args.endpoint}")
        for p in files:
            print(f"  - {p}")
        logger.info("dry_run", count=len(files))
        return 0

    # Pre-flight: server must be listening.
    from urllib.parse import urlparse
    parsed = urlparse(args.server)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    if not is_listening(host, port):
        print(f"error: PicGo server not reachable at {host}:{port}. Start PicGo and ensure the server is enabled in Settings → PicGo-Server.", file=sys.stderr)
        logger.error("server_unreachable", host=host, port=port)
        return 3

    url = args.server.rstrip("/") + "/" + args.endpoint.lstrip("/")
    payload = {"list": [str(p) for p in files]}
    try:
        response = post_json(url, payload)
    except _urlerror.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", errors="ignore")[:500]
        except Exception:
            pass
        print(f"error: PicGo returned HTTP {e.code}: {body}", file=sys.stderr)
        logger.error("upload_http_error", code=e.code, body=body)
        return 4
    except _urlerror.URLError as e:
        print(f"error: cannot reach PicGo: {e.reason}", file=sys.stderr)
        logger.error("upload_url_error", reason=str(e.reason))
        return 5

    result = response.get("result") or response.get("data") or []
    success = bool(response.get("success", len(result) == len(files)))
    file_entries = [
        {"source": str(path), "url": result[i] if i < len(result) else None}
        for i, path in enumerate(files)
    ]
    manifest = {
        "server": args.server,
        "endpoint": args.endpoint,
        "count": len(files),
        "uploaded": sum(1 for e in file_entries if e["url"]),
        "success": success,
        "files": file_entries,
        "raw_response": response,
    }

    if args.out:
        out = Path(args.out).expanduser().resolve()
    elif project_root:
        out_dir = project_root / "media" / "uploaded"
        out_dir.mkdir(parents=True, exist_ok=True)
        out = out_dir / f"picgo-{_dt.date.today().isoformat()}.json"
    else:
        out = Path("picgo-manifest.json").resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(out)

    appended = 0
    if project_root and not args.no_index:
        appended = append_media_index(project_root, file_entries)
        print(f"appended_to_media_index={appended}")

    logger.info("run_end", uploaded=manifest["uploaded"], count=manifest["count"], manifest=str(out), media_index_rows=appended)
    return 0 if success else 6


if __name__ == "__main__":
    raise SystemExit(main())
