"""Weekly Spotlight — one persona per week, Mon-Fri only.

Pick is seeded by the ISO week (stable all week, reproducible for backfill)
and excludes the previous week's persona. state.json stores ONLY the persona
name, so it is safe to commit to a public repo.

`pick_for_week` is pure so the backfill can simulate weeks sequentially;
`get_data` wraps it with state-file persistence for live runs.
"""
import json
import os
import random

from config import STATE_PATH, load_personas


def _load_state():
    if not os.path.exists(STATE_PATH):
        return {}
    try:
        with open(STATE_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def _save_state(state):
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
        f.write("\n")


def week_key(d):
    iso = d.isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


def pick_for_week(wk, previous_persona=None):
    personas = load_personas()
    pool = [p for p in personas if p != previous_persona] or personas
    rng = random.Random(f"{wk}-spotlight")
    return rng.choice(pool)


def get_data(d, state=None, persist=True):
    """Returns {persona, is_new} or None (hidden on weekends)."""
    weekday = d.weekday()  # 0=Mon .. 6=Sun
    if weekday >= 5:
        return None

    state = _load_state() if state is None else state
    wk = week_key(d)

    if state.get("spotlight_week") == wk and state.get("spotlight_persona"):
        persona = state["spotlight_persona"]
    else:
        persona = pick_for_week(wk, previous_persona=state.get("spotlight_persona"))
        state["spotlight_week"] = wk
        state["spotlight_persona"] = persona
        if persist:
            _save_state(state)

    return {"persona": persona, "is_new": weekday == 0}


def format_text(data, name_map=None):
    if not data:
        return None
    name = (name_map or {}).get(data["persona"], data["persona"])
    if data["is_new"]:
        return f"⭐ SPOTLIGHT\nThis week's spotlight: {name}"
    return f"⭐ SPOTLIGHT\nThis week: {name}"
