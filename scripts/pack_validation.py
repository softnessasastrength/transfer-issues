"""Structural checks for the existing normalized GTFS SQLite agency-pack format.

No data repair, interpolation, freshness certification or network access.
"""
from __future__ import annotations

from datetime import datetime
import sqlite3

COLUMNS = {
    "stops": ("id", "feed", "name", "lat", "lon", "parent", "wheelchair"),
    "routes": ("id", "feed", "short", "name", "type", "color", "agency"),
    "trips": ("id", "route", "service", "headsign", "direction", "shape"),
    "times": ("trip", "seq", "stop", "arr", "dep", "pickup", "dropoff"),
    "calendar": ("service", "start", "end", "days"),
    "exceptions": ("service", "date", "type"),
    "shapes": ("id", "seq", "lat", "lon"),
    "transfers": ("a", "b", "type", "seconds"),
}
KEYS = {"stops": ("id",), "routes": ("id",), "trips": ("id",),
        "times": ("trip", "seq"), "calendar": ("service",),
        "exceptions": ("service", "date"), "shapes": ("id", "seq"),
        "transfers": ("a", "b")}


def _reject(db: sqlite3.Connection, label: str, sql: str, args: tuple = ()) -> None:
    if db.execute(sql, args).fetchone() is not None:
        raise ValueError(label)


def _date(value: object) -> None:
    if not isinstance(value, str) or len(value) != 8 or not value.isascii() or not value.isdigit():
        raise ValueError('Invalid service date')
    try:
        datetime.strptime(value, '%Y%m%d')
    except ValueError as exc:
        raise ValueError('Invalid service date') from exc


def validate_database(db: sqlite3.Connection, agency: str) -> dict[str, int]:
    """Validate schema/keys/references without altering the connected database.

    Caller supplies a read-only connection. Extra columns/tables are permitted;
    required objects must be actual tables, not views. Historical dates are valid.
    """
    for table, required in COLUMNS.items():
        if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone():
            raise ValueError('Missing required table: ' + table)
        columns = {row[1] for row in db.execute(f'PRAGMA table_info("{table}")')}
        if not set(required) <= columns:
            raise ValueError('Missing required columns: ' + table)
        keys = KEYS[table]
        blank = ' OR '.join(f'"{key}" IS NULL OR CAST("{key}" AS TEXT)=\'\'' for key in keys)
        _reject(db, 'Empty key: ' + table, f'SELECT 1 FROM "{table}" WHERE {blank} LIMIT 1')
        names = ','.join(f'"{key}"' for key in keys)
        _reject(db, 'Duplicate key: ' + table,
                f'SELECT 1 FROM "{table}" GROUP BY {names} HAVING COUNT(*)>1 LIMIT 1')
    for table in ('routes', 'stops'):
        _reject(db, 'Agency route coverage mismatch' if table == 'routes' else 'Agency stop coverage mismatch',
                f'SELECT 1 FROM "{table}" WHERE feed IS NULL OR feed!=? LIMIT 1', (agency,))
    references = {
        'trip routes': 'SELECT 1 FROM trips t WHERE NOT EXISTS (SELECT 1 FROM routes r WHERE r.id=t.route) LIMIT 1',
        'stop-time trips': 'SELECT 1 FROM times t WHERE NOT EXISTS (SELECT 1 FROM trips p WHERE p.id=t.trip) LIMIT 1',
        'stop-time stops': 'SELECT 1 FROM times t WHERE NOT EXISTS (SELECT 1 FROM stops s WHERE s.id=t.stop) LIMIT 1',
        'trip service': '''SELECT 1 FROM trips t WHERE
            NOT EXISTS (SELECT 1 FROM calendar c WHERE c.service=t.service) AND
            NOT EXISTS (SELECT 1 FROM exceptions e WHERE e.service=t.service) LIMIT 1''',
        'trip stop times': 'SELECT 1 FROM trips t WHERE NOT EXISTS (SELECT 1 FROM times s WHERE s.trip=t.id) LIMIT 1',
        'transfer stops': '''SELECT 1 FROM transfers t WHERE
            NOT EXISTS (SELECT 1 FROM stops s WHERE s.id=t.a) OR
            NOT EXISTS (SELECT 1 FROM stops s WHERE s.id=t.b) LIMIT 1''',
    }
    for label, sql in references.items():
        _reject(db, 'Broken references: ' + label, sql)
    _reject(db, 'Invalid stop times', '''SELECT 1 FROM times WHERE
        typeof(seq)!='integer' OR seq<0 OR typeof(arr)!='integer' OR arr<0 OR
        typeof(dep)!='integer' OR dep<arr OR pickup IS NULL OR pickup NOT IN (0,1,2,3) OR
        dropoff IS NULL OR dropoff NOT IN (0,1,2,3) LIMIT 1''')
    _reject(db, 'Non-monotonic trip times', '''SELECT 1 FROM (
        SELECT arr, LAG(dep) OVER (PARTITION BY trip ORDER BY seq) AS previous_dep FROM times
        ) WHERE arr<previous_dep LIMIT 1''')
    _reject(db, 'Invalid transfers', '''SELECT 1 FROM transfers WHERE
        type IS NULL OR type NOT IN (0,1,2,3) OR typeof(seconds)!='integer' OR seconds<0 LIMIT 1''')
    for start, end, days in db.execute('SELECT start,end,days FROM calendar'):
        _date(start)
        _date(end)
        if end < start or not isinstance(days, str) or len(days) != 7 or set(days) - {'0', '1'}:
            raise ValueError('Invalid service calendar')
    for day, kind in db.execute('SELECT date,type FROM exceptions'):
        _date(day)
        if kind not in (1, 2):
            raise ValueError('Invalid calendar exception type')
    return {table: db.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0] for table in COLUMNS}
