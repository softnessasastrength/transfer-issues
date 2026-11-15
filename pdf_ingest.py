"""Import reviewed official PDF timetable transcriptions into SQLite.

PDFs are evidence, not executable schedules.  A human-reviewed JSON manifest
must accompany each PDF; this module validates that manifest, records the PDF
hash and extraction provenance, and keeps the normalized rows outside the GTFS
tables.  No PDF row is consumed by routing yet.
"""
import datetime
import hashlib
import json
import pathlib
import re
import sqlite3

TIME_RE = re.compile(r"^(\d{1,3}):(\d{2})(?::(\d{2}))?$")
SHA_RE = re.compile(r"^[0-9a-f]{64}$")
STATUSES = {"pending", "reviewed", "rejected"}
METHODS = {"manual", "pdf_text", "ocr"}


SCHEMA = """
CREATE TABLE IF NOT EXISTS pdf_documents(
 document_id TEXT PRIMARY KEY, feed TEXT NOT NULL, source_url TEXT NOT NULL,
 pdf_sha256 TEXT NOT NULL, retrieved_at TEXT NOT NULL,
 effective_start TEXT NOT NULL, effective_end TEXT NOT NULL,
 extraction_method TEXT NOT NULL, extractor TEXT NOT NULL,
 review_status TEXT NOT NULL, reviewed_at TEXT, reviewer TEXT,
 supersedes TEXT, notes TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS pdf_schedules(
 schedule_id TEXT PRIMARY KEY, document_id TEXT NOT NULL REFERENCES pdf_documents,
 route TEXT NOT NULL, direction TEXT NOT NULL, service_days TEXT NOT NULL,
 confidence TEXT NOT NULL, ambiguity TEXT NOT NULL DEFAULT '',
 routing_eligible INTEGER NOT NULL DEFAULT 0, source_page INTEGER,
 notes TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS pdf_schedule_stops(
 schedule_id TEXT NOT NULL REFERENCES pdf_schedules, seq INTEGER NOT NULL,
 stop_id TEXT, stop_name TEXT NOT NULL, arrival INTEGER NOT NULL,
 departure INTEGER NOT NULL, timepoint INTEGER NOT NULL DEFAULT 1,
 note TEXT NOT NULL DEFAULT '', PRIMARY KEY(schedule_id, seq)
);
CREATE INDEX IF NOT EXISTS pdf_schedules_document ON pdf_schedules(document_id);
CREATE INDEX IF NOT EXISTS pdf_schedule_stops_schedule ON pdf_schedule_stops(schedule_id, seq);
"""


class ManifestError(ValueError):
    """The reviewed manifest is incomplete, ambiguous, or internally invalid."""


def seconds(value):
    match = TIME_RE.fullmatch(str(value).strip())
    if not match:
        raise ManifestError(f"invalid PDF timetable time: {value!r}")
    hour, minute, second = (int(x or 0) for x in match.groups())
    if minute >= 60 or second >= 60:
        raise ManifestError(f"invalid PDF timetable time: {value!r}")
    return hour * 3600 + minute * 60 + second


def _date(value, field):
    try:
        return datetime.date.fromisoformat(value).isoformat()
    except (TypeError, ValueError) as exc:
        raise ManifestError(f"{field} must be an ISO date") from exc


def _required(d, key):
    value = d.get(key)
    if value in (None, ""):
        raise ManifestError(f"missing required field: {key}")
    return value


def validate_manifest(manifest, pdf_bytes, existing_stop_ids=()):
    """Validate and return a normalized copy; never guesses missing fields."""
    doc = dict(_required(manifest, "document"))
    document_id = str(_required(doc, "document_id"))
    feed = str(_required(doc, "feed"))
    url = str(_required(doc, "source_url"))
    if not url.startswith(("https://", "http://")):
        raise ManifestError("source_url must be an official HTTP(S) URL")
    actual_hash = hashlib.sha256(pdf_bytes).hexdigest()
    if doc.get("pdf_sha256") != actual_hash or not SHA_RE.fullmatch(actual_hash):
        raise ManifestError("pdf_sha256 does not match the supplied PDF")
    start = _date(_required(doc, "effective_start"), "effective_start")
    end = _date(_required(doc, "effective_end"), "effective_end")
    if end < start:
        raise ManifestError("effective_end precedes effective_start")
    status = _required(doc, "review_status")
    if status not in STATUSES:
        raise ManifestError(f"unknown review_status: {status}")
    method = _required(doc, "extraction_method")
    if method not in METHODS:
        raise ManifestError(f"unknown extraction_method: {method}")
    extractor = str(_required(doc, "extractor"))
    if method == "ocr" and not extractor.lower().startswith("ocr"):
        raise ManifestError("OCR records must name an OCR extractor")
    reviewed_at = doc.get("reviewed_at")
    if status == "reviewed":
        _date(reviewed_at[:10] if reviewed_at else None, "reviewed_at")
        _required(doc, "reviewer")
    normalized = {"document": {
        "document_id": document_id, "feed": feed, "source_url": url,
        "pdf_sha256": actual_hash, "retrieved_at": str(_required(doc, "retrieved_at")),
        "effective_start": start, "effective_end": end,
        "extraction_method": method, "extractor": extractor,
        "review_status": status, "reviewed_at": reviewed_at,
        "reviewer": doc.get("reviewer"), "supersedes": doc.get("supersedes"),
        "notes": str(doc.get("notes", "")),
    }, "schedules": []}
    ids = set(existing_stop_ids)
    seen = set()
    for schedule in manifest.get("schedules", []):
        schedule = dict(schedule)
        sid = str(_required(schedule, "schedule_id"))
        if sid in seen:
            raise ManifestError(f"duplicate schedule_id: {sid}")
        seen.add(sid)
        confidence = str(_required(schedule, "confidence"))
        ambiguity = str(schedule.get("ambiguity", ""))
        stops = schedule.get("stops")
        if not isinstance(stops, list) or len(stops) < 2:
            raise ManifestError(f"schedule {sid} needs at least two stops")
        previous = -1
        out_stops = []
        for seq, stop in enumerate(stops):
            stop = dict(stop)
            name = str(_required(stop, "stop_name"))
            arr, dep = seconds(_required(stop, "arrival")), seconds(_required(stop, "departure"))
            if dep < arr or arr < previous:
                raise ManifestError(f"non-chronological times in {sid} at sequence {seq}")
            previous = dep
            stop_id = stop.get("stop_id")
            if stop_id is not None and ids and stop_id not in ids:
                raise ManifestError(f"unknown stop_id in {sid}: {stop_id}")
            out_stops.append({"stop_id": stop_id, "stop_name": name, "arrival": arr,
                              "departure": dep, "timepoint": int(bool(stop.get("timepoint", True))),
                              "note": str(stop.get("note", ""))})
        # A PDF timetable cannot route until every timetable stop is explicitly
        # linked to a loaded stop/geometry record.  Names alone are not enough:
        # similarly named stops and missing geometry must remain visible but
        # non-routable.
        linked = all(s["stop_id"] for s in out_stops)
        eligible = int(status == "reviewed" and confidence.lower() == "high" and not ambiguity and linked)
        normalized["schedules"].append({
            "schedule_id": sid, "route": str(_required(schedule, "route")),
            "direction": str(_required(schedule, "direction")),
            "service_days": str(_required(schedule, "service_days")),
            "confidence": confidence, "ambiguity": ambiguity,
            "routing_eligible": eligible, "source_page": schedule.get("source_page"),
            "notes": str(schedule.get("notes", "")), "stops": out_stops,
        })
    if not normalized["schedules"]:
        raise ManifestError("manifest contains no schedules")
    return normalized


def ensure_schema(connection):
    connection.executescript(SCHEMA)


def ingest(connection, manifest, pdf_path, existing_stop_ids=()):
    """Atomically validate and insert one reviewed PDF artifact."""
    pdf_path = pathlib.Path(pdf_path)
    normalized = validate_manifest(manifest, pdf_path.read_bytes(), existing_stop_ids)
    ensure_schema(connection)
    doc = normalized["document"]
    with connection:
        connection.execute("DELETE FROM pdf_schedule_stops WHERE schedule_id IN (SELECT schedule_id FROM pdf_schedules WHERE document_id=?)", (doc["document_id"],))
        connection.execute("DELETE FROM pdf_schedules WHERE document_id=?", (doc["document_id"],))
        connection.execute("DELETE FROM pdf_documents WHERE document_id=?", (doc["document_id"],))
        connection.execute("INSERT INTO pdf_documents VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", tuple(doc.values()))
        for schedule in normalized["schedules"]:
            connection.execute("INSERT INTO pdf_schedules VALUES (?,?,?,?,?,?,?,?,?,?)", (schedule["schedule_id"], doc["document_id"], schedule["route"], schedule["direction"], schedule["service_days"], schedule["confidence"], schedule["ambiguity"], schedule["routing_eligible"], schedule["source_page"], schedule["notes"]))
            connection.executemany("INSERT INTO pdf_schedule_stops VALUES (?,?,?,?,?,?,?,?)", [(schedule["schedule_id"], i, s["stop_id"], s["stop_name"], s["arrival"], s["departure"], s["timepoint"], s["note"]) for i, s in enumerate(schedule["stops"])])
    return normalized


def load_manifest(path):
    return json.loads(pathlib.Path(path).read_text())
