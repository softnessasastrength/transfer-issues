"""Explicit, device-local Percival preferences; no hidden behavioural memory."""
import json
import os
import pathlib
import tempfile


ROOT = pathlib.Path(__file__).resolve().parent
PATH = pathlib.Path(os.environ.get("PERCIVAL_PREFERENCES", ROOT / "data" / "percival_preferences.json"))
ALLOWED = {"home_stop", "default_origin", "default_host", "default_depart_time", "default_return_deadline", "mode", "radius", "commutes"}
COMMUTE_TARGETS = {"home", "work"}


def _stop_id(key, value):
    if not isinstance(value, str) or not value.strip() or len(value) > 200:
        raise ValueError(key + " must be a non-empty stop ID")
    return value.strip()


def _route_chain(key, value):
    if not isinstance(value, list) or len(value) > 10:
        raise ValueError(key + " must be a list of at most 10 route IDs")
    chain = []
    for route in value:
        if not isinstance(route, str) or ":" not in route or len(route) > 200:
            raise ValueError(key + " entries must be feed-qualified route IDs")
        chain.append(route.strip())
    return chain


def _validate_direction(key, value):
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(key + " must be an object")
    unknown = set(value) - {"routes", "mode"}
    if unknown:
        raise ValueError(key + " has unknown field(s): " + ", ".join(sorted(unknown)))
    result = {}
    if "routes" in value:
        result["routes"] = _route_chain(key + ".routes", value["routes"])
    if "mode" in value:
        if value["mode"] not in {"walk", "scooter"}:
            raise ValueError(key + ".mode must be walk or scooter")
        result["mode"] = value["mode"]
    return result


def _validate_commute(profile):
    if not isinstance(profile, dict):
        raise ValueError("commute profile must be an object")
    unknown = set(profile) - {"id", "name", "home_stop", "work_stop", "outbound", "return", "rideshare_legs"}
    if unknown:
        raise ValueError("Unknown commute field(s): " + ", ".join(sorted(unknown)))
    pid = profile.get("id")
    if not isinstance(pid, str) or not pid.strip() or len(pid) > 64:
        raise ValueError("commute id must be a non-empty string of at most 64 characters")
    name = profile.get("name")
    if not isinstance(name, str) or not name.strip() or len(name) > 200:
        raise ValueError("commute name must be a non-empty string")
    result = {
        "id": pid.strip(),
        "name": name.strip(),
        "home_stop": _stop_id("home_stop", profile.get("home_stop")),
        "work_stop": _stop_id("work_stop", profile.get("work_stop")),
        "outbound": _validate_direction("outbound", profile.get("outbound")),
        "return": _validate_direction("return", profile.get("return")),
        "rideshare_legs": [],
    }
    legs = profile.get("rideshare_legs") or []
    if not isinstance(legs, list) or len(legs) > 4:
        raise ValueError("rideshare_legs must be a list of at most 4 legs")
    for leg in legs:
        if not isinstance(leg, dict) or set(leg) - {"from_stop", "to"}:
            raise ValueError("rideshare legs must have from_stop and to")
        if leg.get("to") not in COMMUTE_TARGETS:
            raise ValueError("rideshare leg 'to' must be 'home' or 'work'")
        result["rideshare_legs"].append({"from_stop": _stop_id("rideshare from_stop", leg.get("from_stop")), "to": leg["to"]})
    return result


def _validate_commutes(value):
    if not isinstance(value, list):
        raise ValueError("commutes must be a list")
    profiles = [_validate_commute(profile) for profile in value]
    ids = [profile["id"] for profile in profiles]
    if len(set(ids)) != len(ids):
        raise ValueError("commute ids must be unique")
    return profiles


def _validate(values):
    unknown = set(values) - ALLOWED
    if unknown:
        raise ValueError("Unknown preference(s): " + ", ".join(sorted(unknown)))
    result = {}
    for key, value in values.items():
        if key in {"home_stop", "default_origin", "default_host"}:
            result[key] = _stop_id(key, value)
        elif key == "commutes":
            result[key] = _validate_commutes(value)
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


def get_commutes():
    return get().get("commutes", [])


def get_commute(key):
    for profile in get_commutes():
        if profile["id"] == key or profile["name"].casefold() == str(key).casefold():
            return profile
    return None


def set_commute(profile):
    profile = _validate_commute(profile)
    commutes = [existing for existing in get_commutes() if existing["id"] != profile["id"]]
    commutes.append(profile)
    set_values({"commutes": commutes})
    return profile


def clear_commute(key):
    commutes = get_commutes()
    kept = [profile for profile in commutes if profile["id"] != key and profile["name"].casefold() != str(key).casefold()]
    if len(kept) != len(commutes):
        set_values({"commutes": kept})
    return kept
