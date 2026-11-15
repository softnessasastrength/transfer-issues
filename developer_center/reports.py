"""Read local build evidence without declaring it valid for the current checkout."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET


def evidence(path: Path) -> dict:
    """Filesystem time is evidence age, not source-code or execution provenance."""
    modified = path.stat().st_mtime
    return {"source": str(path),
            "modified_utc": datetime.fromtimestamp(modified, timezone.utc).isoformat(),
            "age_seconds": max(0, round(datetime.now(timezone.utc).timestamp() - modified)),
            "current_tree_verified": False}


def python_result(log: Path, record: dict) -> dict:
    result = {"status": "unknown", "commit": record.get("commit"),
              "changes": record.get("changes"), "started_utc": record.get("started_utc"),
              "exit_code": record.get("exit_code"), "current_tree_verified": False}
    try:
        result.update(evidence(log))
        # Stream rather than loading potentially large build logs into the dashboard.
        count = None
        verdict = None
        with log.open(encoding="utf-8", errors="replace") as stream:
            for line in stream:
                match = re.fullmatch(r"Ran (\d+) tests? in [\d.]+s\s*", line)
                if match:
                    count = int(match[1])
                    verdict = None
                elif count is not None and re.fullmatch(r"OK(?: \(.*\))?\s*", line):
                    verdict = "passed"
                elif count is not None and line.startswith("FAILED ("):
                    verdict = "failed"
        result["tests"] = count
        if record.get("exit_code") not in (None, 0):
            result["status"] = "failed"
        elif verdict == "failed":
            result["status"] = "failed"
        elif record.get("exit_code") == 0 and count and verdict == "passed":
            result["status"] = "passed"
        else:
            result["detail"] = "No completed nonempty unittest summary with a successful command exit"
    except OSError as exc:
        result.update(status="unavailable", detail=str(exc))
    return result


def junit_results(directory: Path) -> dict:
    result = {"status": "unavailable", "tests": 0, "failures": 0, "errors": 0,
              "skipped": 0, "reports": [], "issues": [],
              "current_tree_verified": False,
              "provenance": "Local XML; may be cached, mixed-age or from another checkout"}
    for path in sorted(directory.glob("TEST-*.xml")):
        try:
            item = evidence(path)
            root = ET.parse(path).getroot()
            suites = [root] if root.tag == "testsuite" else list(root) if root.tag == "testsuites" else []
            if not suites or any(s.tag != "testsuite" or s.find("testsuite") is not None for s in suites):
                raise ValueError("Unsupported JUnit structure")
            counts = {key: 0 for key in ("tests", "failures", "errors", "skipped")}
            for suite in suites:
                values = {key: int(suite.attrib[key]) for key in counts}
                if any(v < 0 for v in values.values()) or sum(values[k] for k in ("failures", "errors", "skipped")) > values['tests']:
                    raise ValueError("Inconsistent JUnit counts")
                for key, value in values.items():
                    counts[key] += value
            for key, value in counts.items():
                result[key] += value
            result['reports'].append({**item, **counts})
        except (OSError, ET.ParseError, ValueError, KeyError) as exc:
            result['issues'].append({"source": str(path), "detail": str(exc)})
    if result['issues']:
        result['status'] = "invalid"
    elif result['reports']:
        result['status'] = ("failed" if result['failures'] or result['errors'] else
                            "passed" if result['tests'] > result['skipped'] else "no-tests")
    return result


def apk_metadata(apk: Path) -> dict:
    path = apk.parent / "output-metadata.json"
    result = {"status": "unavailable", "current_tree_verified": False,
              "provenance": "Adjacent Gradle metadata; not extracted from or bound to APK bytes"}
    try:
        result.update(evidence(path))
        data = json.loads(path.read_text())
        if not isinstance(data, dict) or not isinstance(data.get('elements'), list):
            raise ValueError("Invalid Gradle metadata structure")
        matches = [element for element in data['elements']
                   if isinstance(element, dict) and element.get('outputFile') == apk.name]
        if len(matches) != 1 or not isinstance(data.get('applicationId'), str):
            raise ValueError("No unique APK metadata entry or application ID")
        entry = matches[0]
        if not isinstance(entry.get('versionCode'), int) or not isinstance(entry.get('versionName'), str):
            raise ValueError("Missing version metadata")
        result.update(status="available", application_id=data['applicationId'],
                      variant=data.get('variantName'), version_code=entry['versionCode'],
                      version_name=entry['versionName'])
    except (OSError, ValueError, TypeError) as exc:
        result['detail'] = str(exc)
        if path.exists():
            result['status'] = "invalid"
    return result
