"""Offline-first, opt-in transit pack manager proof of concept (stdlib only).

No network I/O. Caller supplies local payload paths and trusted catalog entries.
The application never discovers or installs additional agencies automatically.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import tempfile

AGENCIES = ("cttransit", "hartford", "pvta", "amtrak")
POLICIES = ("auto", "ask", "manual")


class PackError(ValueError):
    pass


def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_catalog(catalog):
    if not isinstance(catalog, dict) or not isinstance(catalog.get("packages"), dict):
        raise PackError("Catalog requires a packages mapping")
    for key, p in catalog["packages"].items():
        if not isinstance(key, str) or not key or "/" in key or "\\" in key or key in (".", ".."):
            raise PackError("Unsafe package ID")
        if not isinstance(p, dict) or p.get("id") != key:
            raise PackError("Package ID mismatch")
        if not isinstance(p.get("sha256"), str) or len(p["sha256"]) != 64:
            raise PackError("Missing SHA-256")
        try:
            int(p["sha256"], 16)
        except ValueError as exc:
            raise PackError("Invalid SHA-256") from exc
        if not isinstance(p.get("bytes"), int) or p["bytes"] < 0:
            raise PackError("Invalid size")
        if not isinstance(p.get("version"), str) or not p["version"]:
            raise PackError("Missing version")
        if not isinstance(p.get("dependencies", []), list) or any(not isinstance(x, str) for x in p["dependencies"]):
            raise PackError("Invalid dependencies")
        if p.get("kind") not in ("agency", "shared"):
            raise PackError("Invalid kind")
        if p["kind"] == "agency" and p.get("agency") not in AGENCIES:
            raise PackError("Unknown agency")
        if p["kind"] == "shared" and p.get("agency") is not None:
            raise PackError("Shared pack cannot claim agency")
    return catalog


def resolve(catalog, agencies):
    validate_catalog(catalog)
    chosen = set(agencies)
    if not chosen.issubset(AGENCIES):
        raise PackError("Unknown selected agency")
    packages = catalog["packages"]
    roots = [k for k, p in packages.items() if p["kind"] == "agency" and p["agency"] in chosen]
    missing = sorted(chosen - {packages[k]["agency"] for k in roots})
    result, visiting, visited = [], set(), set()

    def visit(key):
        if key in visiting:
            raise PackError("Dependency cycle")
        if key in visited:
            return
        if key not in packages:
            raise PackError("Missing dependency: " + key)
        visiting.add(key)
        for dependency in packages[key].get("dependencies", []):
            dep = packages.get(dependency)
            if dep and dep["kind"] == "agency" and dep["agency"] not in chosen:
                raise PackError("Dependency would install an unselected agency")
            visit(dependency)
        visiting.remove(key)
        visited.add(key)
        result.append(key)

    for key in sorted(roots):
        visit(key)
    return {"selected_agencies": sorted(chosen), "packages": result,
            "missing_agencies": missing,
            "total_bytes": sum(packages[k]["bytes"] for k in result),
            "dependencies": {k: packages[k].get("dependencies", []) for k in result}}


class OfflinePackManager:
    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.packs = self.root / "packs"
        self.packs.mkdir(exist_ok=True)
        self.state_file = self.root / "state.json"

    def state(self):
        if not self.state_file.exists():
            return {"selected_agencies": [], "update_policy": "ask", "installed": {}}
        return json.loads(self.state_file.read_text(encoding="utf-8"))

    def _save(self, state):
        fd, name = tempfile.mkstemp(dir=self.root, prefix=".state-")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(state, stream, indent=2, sort_keys=True)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(name, self.state_file)
        finally:
            if os.path.exists(name):
                os.unlink(name)

    def plan(self, catalog, agencies):
        return resolve(catalog, agencies)

    def install(self, catalog, agencies, payloads, *, approved=False, update_policy="auto"):
        """Install only explicitly approved selections from local files.

        All packages verified before any activation. Existing versions remain
        untouched until replacement is ready. Does not download anything.
        """
        if not approved:
            raise PackError("Explicit user approval required")
        if update_policy not in POLICIES:
            raise PackError("Unknown update policy")
        plan = resolve(catalog, agencies)
        if plan["missing_agencies"]:
            raise PackError("Unavailable agency data: " + ", ".join(plan["missing_agencies"]))
        entries = catalog["packages"]
        staging = Path(tempfile.mkdtemp(prefix=".stage-", dir=self.root))
        prepared = {}
        try:
            for key in plan["packages"]:
                if key not in payloads:
                    raise PackError("Missing local payload: " + key)
                source = Path(payloads[key])
                if not source.is_file() or source.stat().st_size != entries[key]["bytes"]:
                    raise PackError("Payload size mismatch: " + key)
                target = staging / (key + ".pack")
                shutil.copyfile(source, target)
                if digest(target) != entries[key]["sha256"]:
                    raise PackError("Checksum mismatch: " + key)
                if entries[key].get("media_type") == "application/vnd.sqlite3":
                    with sqlite3.connect("file:" + str(target) + "?mode=ro", uri=True) as conn:
                        if conn.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                            raise PackError("SQLite integrity failure: " + key)
                prepared[key] = target
            old = self.state()
            new_installed = dict(old["installed"])
            # Content-addressed filenames mean no valid active payload is overwritten.
            for key, source in prepared.items():
                filename = key + "-" + entries[key]["sha256"] + ".pack"
                target = self.packs / filename
                if not target.exists():
                    os.replace(source, target)
                new_installed[key] = {"file": filename, "version": entries[key]["version"],
                                      "sha256": entries[key]["sha256"],
                                      "agency": entries[key].get("agency")}
            self._save({"selected_agencies": plan["selected_agencies"],
                        "update_policy": update_policy, "installed": new_installed})
            return self.state()
        finally:
            shutil.rmtree(staging, ignore_errors=True)

    def check_update(self, catalog, key):
        """Return eligibility only; no network access or installation."""
        validate_catalog(catalog)
        state = self.state()
        p = catalog["packages"].get(key)
        old = state["installed"].get(key)
        if not p or not old or state["update_policy"] != "auto":
            return False
        if p["kind"] == "agency" and p["agency"] not in state["selected_agencies"]:
            return False
        # New dependencies require fresh approval even for an existing pack.
        if any(dep not in state["installed"] for dep in p.get("dependencies", [])):
            return False
        return old["sha256"] != p["sha256"]

    def verify_installed(self):
        result = {}
        for key, entry in self.state()["installed"].items():
            path = self.packs / entry["file"]
            result[key] = path.is_file() and digest(path) == entry["sha256"]
        return result
