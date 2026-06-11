"""Sports Fact of the Day — curated local JSON, zero runtime hallucination.

Data format (v2): every entry carries a sport tag for the site's stats view.
    {"by_date": {"MM-DD": {"text": ..., "sport": ...}},
     "general": [{"text": ..., "sport": ...}, ...]}

Selection: a date-keyed fact wins; otherwise the general pool rotates by
day-of-year with a yearly offset — deterministic, and consecutive days can
never repeat a fact (unlike random picks).
"""
import json
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "sports_facts.json")


def _load():
    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


def _normalize(entry):
    if isinstance(entry, str):
        return {"text": entry, "sport": "general"}
    return {"text": entry["text"], "sport": entry.get("sport", "general")}


def get_data(d):
    """Returns {text, sport} or None."""
    try:
        data = _load()
    except (OSError, json.JSONDecodeError):
        return None

    key = f"{d:%m-%d}"
    if key in data.get("by_date", {}):
        return _normalize(data["by_date"][key])

    general = data.get("general", [])
    if not general:
        return None
    doy = d.timetuple().tm_yday
    idx = (doy + d.year * 7) % len(general)
    return _normalize(general[idx])


def format_text(data):
    if not data:
        return None
    return f"🏆 SPORTS FACT OF THE DAY\n{data['text']}"
