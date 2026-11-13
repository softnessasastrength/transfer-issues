"""Fixed command adapters and durable, private local execution records."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
COMMANDS = {
    key: ("bash", "crostini-dev.sh", key)
    for key in ("doctor", "test", "android-test", "android-build")
}


@dataclass(frozen=True)
class Result:
    action: str
    started_utc: str
    seconds: float
    exit_code: int
    log: str
    commit: str
    changes: str


def run_action(action: str, root: Path = ROOT, output: Path | None = None) -> Result:
    """Run a known command with inherited terminal; record interruption/failure.

    Commands share the terminal process group, so Ctrl+C reaches Gradle and its
    launcher. No detached child session or user-supplied shell is used.
    """
    command = COMMANDS[action]  # Reject unknown commands before creating files.
    output = output or root / "build" / "developer-center"
    output.mkdir(parents=True, exist_ok=True)
    identifier = uuid.uuid4().hex
    log = output / f"{identifier}.log"
    started = datetime.now(timezone.utc).isoformat()
    commit = git_value(root, "rev-parse", "HEAD")
    changes = git_value(root, "status", "--short")
    begin = time.monotonic()
    with os.fdopen(os.open(log, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600),
                   "w", encoding="utf-8") as stream:
        try:
            process = subprocess.Popen(command, cwd=root, stdout=stream,
                                       stderr=subprocess.STDOUT)
            try:
                code = process.wait()
            except KeyboardInterrupt:
                # Terminal SIGINT reaches both parent and child. Reap before return.
                try:
                    code = process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
                code = 130
        except OSError as exc:
            stream.write(f"Launch failed: {exc}\n")
            code = 127
    result = Result(action, started, round(time.monotonic() - begin, 3), code, str(log), commit, changes)
    temporary = output / f".{identifier}.tmp"
    with os.fdopen(os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600),
                   "w", encoding="utf-8") as stream:
        json.dump(asdict(result), stream, indent=2)
    temporary.replace(output / f"{identifier}.json")
    return result


def git_value(root: Path, *args: str) -> str:
    try:
        result = subprocess.run(("git", *args), cwd=root, capture_output=True,
                                text=True, timeout=5, check=False)
        return result.stdout.strip() if result.returncode == 0 else "UNAVAILABLE"
    except (OSError, subprocess.TimeoutExpired):
        return "UNAVAILABLE"


def snapshot(root: Path = ROOT, output: Path | None = None) -> dict:
    output = output or root / "build" / "developer-center"
    history = []
    for path in sorted(output.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:10]:
        try:
            history.append(json.loads(path.read_text()))
        except (OSError, ValueError):
            history.append({"error": f"Unreadable history: {path.name}"})
    artifacts = []
    for path in sorted((root / "android/app/build/outputs/apk").glob("**/*.apk")):
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        artifacts.append({"path": str(path.relative_to(root)), "bytes": path.stat().st_size,
                          "sha256": digest.hexdigest()})
    usage = shutil.disk_usage(root)
    return {"branch": git_value(root, "branch", "--show-current"),
            "commit": git_value(root, "rev-parse", "--short", "HEAD"),
            "changes": git_value(root, "status", "--short"),
            "tools": {name: shutil.which(name) is not None
                      for name in ("python3", "git", "java", "gradle", "adb")},
            "disk_free_bytes": usage.free, "disk_total_bytes": usage.total,
            "history": history, "artifacts": artifacts}
