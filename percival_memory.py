"""Explicit, device-local Percival preferences; no hidden behavioural memory."""
import json
import os
import pathlib
import tempfile


ROOT = pathlib.Path(__file__).resolve().parent
PATH = pathlib.Path(os.environ.get("PERCIVAL_PREFERENCES", ROOT / "data" / "percival_preferences.json"))
ALLOWED = {"home_stop", "default_origin", "default_host", "default_depart_time", "default_return_deadline", "mode", "radius"}


def _validate(values):
    unknown = set(values) - ALLOWED
    if unknown:
        raise ValueError("Unknown preference(s): " + ", ".join(sorted(unknown)))
    result = {}
    for key, value in values.items():
        if key in {"home_stop", "default_origin", "default_host"}:
            if not isinstance(value, str) or not value.strip() or len(value) > 200:
                raise ValueError(key + " must be a non-empty stop ID")
            result[key] = value.strip()
        elif key in {"default_depart_time", "default_return_deadline", "radius"}:
            if not isinstance(value, int) or isinstance(value, bool):
                raise ValueError(key + " must be an integer")
            upper = 3000 if key == "radius" else 172799
            if not 0 <= value <= upper:
                raise ValueError(key + " is out of range")
            result[key] = value
        elif key == "mode":
            if value not in {"walk", "scooter"}:
                raise ValueError("mode must be walk or scooter")
            result[key] = value
    return result


def get():
    if not PATH.exists():
        return {}
    try:
        data = json.loads(PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise RuntimeError("Cannot read Percival preferences: " + str(exc))
    if not isinstance(data, dict):
        raise RuntimeError("Percival preferences must be a JSON object")
    return _validate(data)


def set_values(values):
    merged = get()
    merged.update(_validate(values))
    PATH.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix="percival-preferences-", dir=str(PATH.parent), text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(merged, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temp_name, PATH)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
    return merged


def clear():
    if PATH.exists():
        PATH.unlink()
    return {}
