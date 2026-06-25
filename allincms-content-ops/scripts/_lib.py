"""Shared utilities for content-ops scripts.

Two helpers: a structured JSONL logger and an `flock`-based file lock for
shared writes. Both deliberately tiny — no third-party deps, safe to import
from any script in this folder.
"""
import contextlib
import datetime as _dt
import errno
import json
import os
import re
import sys
import time
from pathlib import Path

try:
    import fcntl  # type: ignore
except ImportError:  # Windows
    fcntl = None  # type: ignore


# ----- logger ----------------------------------------------------------------


class JsonlLogger:
    """Append one JSON object per line. Lines also echo to stderr when verbose."""

    def __init__(self, script_name, log_path=None, project_root=None):
        self.script = script_name
        self.path = None
        if log_path:
            self.path = Path(log_path).expanduser().resolve()
        elif project_root:
            logs_dir = Path(project_root) / "logs"
            logs_dir.mkdir(parents=True, exist_ok=True)
            self.path = logs_dir / f"{script_name}-{_dt.date.today().isoformat()}.jsonl"

    def event(self, level, msg, **fields):
        rec = {
            "ts": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "script": self.script,
            "pid": os.getpid(),
            "level": level,
            "msg": msg,
        }
        rec.update(fields)
        if self.path is not None:
            try:
                with self.path.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            except OSError as e:
                print(f"warning: log write failed ({e})", file=sys.stderr)

    def info(self, msg, **f):
        self.event("info", msg, **f)

    def warn(self, msg, **f):
        self.event("warn", msg, **f)

    def error(self, msg, **f):
        self.event("error", msg, **f)


# ----- file lock -------------------------------------------------------------


_UNSAFE_LOCK_NAME_RE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


@contextlib.contextmanager
def file_lock(lock_path, timeout=30.0, poll=0.2):
    """Acquire an exclusive flock on `lock_path` (created if missing).

    On POSIX uses fcntl.flock. On Windows (no fcntl), falls back to a
    best-effort O_CREAT|O_EXCL lockfile loop — sufficient for single-host
    coordination; not for distributed FS.

    Raises TimeoutError if not acquired within `timeout` seconds.
    """
    lock_path = Path(lock_path)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + timeout

    if fcntl is not None:
        fh = open(lock_path, "a+")
        while True:
            try:
                fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError as e:
                if e.errno not in (errno.EAGAIN, errno.EWOULDBLOCK):
                    fh.close()
                    raise
                if time.monotonic() >= deadline:
                    fh.close()
                    raise TimeoutError(f"could not acquire lock {lock_path} within {timeout}s")
                time.sleep(poll)
        try:
            yield fh
        finally:
            try:
                fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
            finally:
                fh.close()
    else:
        # Windows / no-fcntl fallback: exclusive create marker file.
        marker = lock_path.with_suffix(lock_path.suffix + ".excl")
        while True:
            try:
                fd = os.open(marker, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, str(os.getpid()).encode())
                os.close(fd)
                break
            except FileExistsError:
                if time.monotonic() >= deadline:
                    raise TimeoutError(f"could not acquire lock {marker} within {timeout}s")
                time.sleep(poll)
        try:
            yield None
        finally:
            try:
                marker.unlink()
            except FileNotFoundError:
                pass


def shared_writer_lock(project_root, target):
    """Returns a file_lock CM for a named shared writer.

    `target` is one of: 'lessons', 'opportunities', 'audits_index',
    'media_index', or any 'slug:<slug>' for per-slug reviewer locks.
    """
    locks_dir = Path(project_root) / ".locks"
    safe = _UNSAFE_LOCK_NAME_RE.sub("_", target)
    return file_lock(locks_dir / f"{safe}.lock")
