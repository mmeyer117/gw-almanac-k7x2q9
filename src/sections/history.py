"""This Day in History — Wikipedia 'On This Day' API.

Editorial filters:
- Skip-list of overused events (per project spec).
- Prefer events at least 30 years old.
- Prefer non-tragedy events when alternatives exist (a morning group-chat
  digest shouldn't default to mass-casualty news; tragedies still appear
  when they're all that's available for a date).
- Pick is seeded by the date so same-day re-runs are stable.
"""
import random
import re

import requests

from config import USER_AGENT

ENDPOINT = "https://api.wikimedia.org/feed/v1/wikipedia/en/onthisday/events/{month}/{day}"

SKIP_KEYWORDS = [
    "John F. Kennedy",
    "Pearl Harbor",
    "moon landing",
    "Berlin Wall",
    "9/11",
    "September 11, 2001",
    "World Trade Center",
    "Titanic",
    "Hiroshima",
    "Nagasaki",
]

TRAGEDY_PATTERN = re.compile(
    r"\b(kill|killed|killing|massacre|mass shooting|shooting|bombing|"
    r"terrorist|assassinat|execut|crashes|crash kills|dead|deaths)\b",
    re.IGNORECASE,
)


def get_data(d):
    """Returns {year, text} or None."""
    url = ENDPOINT.format(month=d.month, day=d.day)
    try:
        resp = requests.get(url, timeout=20, headers={"User-Agent": USER_AGENT})
        resp.raise_for_status()
        events = resp.json().get("events", [])
        if not events:
            return None

        filtered = [
            ev for ev in events
            if not any(skip.lower() in ev.get("text", "").lower() for skip in SKIP_KEYWORDS)
        ] or events

        older = [ev for ev in filtered if (d.year - ev.get("year", d.year)) >= 30]
        pool = older or filtered

        upbeat = [ev for ev in pool if not TRAGEDY_PATTERN.search(ev.get("text", ""))]
        pool = upbeat or pool

        rng = random.Random(f"{d.isoformat()}-history")
        chosen = rng.choice(pool)
        return {"year": chosen.get("year"), "text": chosen.get("text")}
    except Exception:
        return None


def format_text(data):
    if not data:
        return None
    return f"📜 THIS DAY IN HISTORY\nOn this day in {data['year']}, {data['text']}"
