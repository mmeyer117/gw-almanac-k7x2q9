"""Song of the Day — a persona is named to pick the group's song.

Seeded by the date: uniform across days, but re-running the same day can never
announce a different person (safe Action retries, reproducible backfill).
"""
import random

from config import load_personas


def get_data(d):
    personas = load_personas()
    rng = random.Random(f"{d.isoformat()}-song")
    return {"persona": rng.choice(personas)}


def format_text(data, name_map=None):
    if not data:
        return None
    name = (name_map or {}).get(data["persona"], data["persona"])
    return f"🎵 SONG OF THE DAY\n{name}"
