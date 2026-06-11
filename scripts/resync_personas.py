"""Recompute spotlight/song picks in all published reports after a persona
roster change. Pure-local (no API calls): the picks are seeded by date/week
plus the persona pool, so editing config/personas.json and running this
brings every report JSON and state.json in line.

    python scripts/resync_personas.py
"""
import json
import os
import sys
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from config import REPORTS_DIR
from sections import song
from sections.spotlight import _save_state, pick_for_week, week_key


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    files = sorted(fn for fn in os.listdir(REPORTS_DIR) if fn.endswith(".json"))
    dates = [date.fromisoformat(fn[:-5]) for fn in files]

    # Re-simulate the weekly spotlight chain in order
    week_picks = {}
    prev = None
    for d in dates:
        wk = week_key(d)
        if wk not in week_picks:
            week_picks[wk] = pick_for_week(wk, previous_persona=prev)
            prev = week_picks[wk]

    changed = 0
    for fn, d in zip(files, dates):
        path = os.path.join(REPORTS_DIR, fn)
        with open(path, encoding="utf-8") as f:
            rep = json.load(f)
        s = rep["sections"]
        before = json.dumps([s.get("spotlight"), s.get("song")])
        if s.get("spotlight") is not None:
            s["spotlight"]["persona"] = week_picks[week_key(d)]
        if s.get("song") is not None:
            s["song"] = song.get_data(d)
        if json.dumps([s.get("spotlight"), s.get("song")]) != before:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(rep, f, indent=2, ensure_ascii=False)
                f.write("\n")
            changed += 1

    last_wk = week_key(dates[-1])
    _save_state({"spotlight_week": last_wk, "spotlight_persona": week_picks[last_wk]})
    print(f"resynced {changed}/{len(files)} reports; state.json -> {last_wk}: {week_picks[last_wk]}")


if __name__ == "__main__":
    main()
