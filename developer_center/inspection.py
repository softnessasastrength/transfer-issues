"""On-demand read-only inspection and bounded, terminal-safe local log previews."""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import sqlite3
import stat
import sys

from .adapters import ROOT, git_value

HELP = {
    "navigation": "D dashboard | T test evidence | G git | E environment | L logs | P packs | H help | Q quit",
    "dashboard": "Up/down selects an operation; Enter starts it. Ctrl+C interrupts the foreground command.",
    "panels": "Up/down scrolls. Left/right selects older/newer log previews. R refreshes on demand.",
    "doctor": "Check the existing Python/SQLite/Gradle toolchain; installs nothing.",
    "test": "Run deterministic Python regressions; loopback HTTP tests need socket permission.",
    "android-test": "Run Gradle debug JVM unit tests; may reuse cached results and download build dependencies.",
    "android-build": "Assemble debug APK incrementally; not a device or airplane-mode test.",
    "logs": "Displays only the last 64 KiB of a regular local .log file; no log files are deleted.",
    "packs": "Validate existing exported local packs; does not download/install or certify current service.",
    "privacy": "Logs and inspection output can contain private paths. Review before sharing.",
    "references": "docs/development/developer-command-center.md | docs/development/baseline-20261113.md",
}


def git_inspection(root: Path = ROOT) -> dict:
    return {"branch": git_value(root, 'branch', '--show-current'),
            "commit": git_value(root, 'rev-parse', 'HEAD'),
            "changes": git_value(root, 'status', '--short'),
            "local_branches": git_value(root, 'branch', '--format=%(refname:short) %(objectname:short)'),
            "recent_commits": git_value(root, 'log', '-8', '--format=%h %s'),
            "scope": "Local refs only; no fetch, checkout, commit or remote URL disclosure"}


def environment(root: Path = ROOT) -> dict:
    sdk = os.environ.get('ANDROID_HOME') or os.environ.get('ANDROID_SDK_ROOT')
    return {"python": sys.version.split()[0], "sqlite": sqlite3.sqlite_version,
            "tools": {name: shutil.which(name) for name in ('python3', 'git', 'java', 'gradle', 'adb')},
            "sdk_environment_configured": bool(sdk),
            "android_35_platform_present": bool(sdk and (Path(sdk) / 'platforms/android-35/android.jar').is_file()),
            "android_35_build_tools_present": bool(sdk and (Path(sdk) / 'build-tools/35.0.0').is_dir()),
            "free_bytes": shutil.disk_usage(root).free,
            "scope": "Presence checks only; use doctor/build for actual execution. No setup changes."}


def logs(output: Path) -> list[dict]:
    records = []
    for path in output.glob('*.log'):
        try:
            info = path.lstat()
            if stat.S_ISREG(info.st_mode):
                records.append({"name": path.name, "bytes": info.st_size, "modified_epoch": info.st_mtime})
        except OSError:
            continue  # A build may rename/remove a log during inspection.
    return sorted(records, key=lambda record: (record['modified_epoch'], record['name']), reverse=True)


def log_preview(output: Path, name: str) -> dict:
    """Refuse traversal, symlinks and special files; do not execute log control codes."""
    if Path(name).name != name or not name.endswith('.log'):
        raise ValueError('Choose a .log filename inside the history directory')
    result = {"name": name, "status": "unavailable", "text": ""}
    try:
        descriptor = os.open(output / name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(descriptor, 'rb') as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode):
                raise ValueError('Only regular log files can be previewed')
            start = max(0, info.st_size - 65536)
            stream.seek(start)
            text = stream.read(65536).decode('utf-8', errors='replace')
        # Escape sequences become inert visible fragments; retain newlines/tabs.
        safe = ''.join(c for c in text if c.isprintable() or c in '\n\t')
        result.update(status='available', bytes=info.st_size, truncated=start > 0,
                      text=safe.expandtabs(4), modified_epoch=info.st_mtime)
    except (OSError, ValueError) as exc:
        result['detail'] = str(exc)
    return result


def pack_inspection(directory: Path = ROOT / 'build/lan-packs') -> dict:
    """Validate already-exported local packs; never install or fetch networks."""
    from scripts.verify_lan_catalog import verify

    result = {"directory": str(directory), "status": "unavailable",
              "scope": "Exported local catalogue; not Android-installed coverage or current service",
              "limitations": "No publisher authentication, freshness, basemap or complete-offline certification"}
    try:
        result.update(verify(directory))
        result['status'] = 'validated'
    except (OSError, ValueError) as exc:
        result['status'] = 'invalid' if (directory / 'catalog.json').exists() else 'unavailable'
        result['detail'] = str(exc)
    return result
