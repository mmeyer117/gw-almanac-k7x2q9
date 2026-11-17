"""Recompute ONLY the St. Louis sports section in every published report,
from fresh ESPN season schedules. Other sections are left untouched.

Use after changing stl_sports logic, or to repair games ESPN's feed dropped.

    python scripts/rebuild_sports.py
"""
import json
import os
import sys
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from config import REPORTS_DIR
from publish import rebuild_index
from sections import stl_sports


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    files = sorted(fn for fn in os.listdir(REPORTS_DIR) if fn.endswith(".json"))
    dates = [date.fromisoformat(fn[:-5]) for fn in files]
    seasons = range(dates[0].year, dates[-1].year + 2)

    events = {}
    for team in stl_sports.TEAMS:
        events[team] = stl_sports.fetch_team_events(team, seasons=seasons)
        print(f"{team}: {len(events[team])} events (seasons {list(seasons)})")
        if not events[team]:
            sys.exit(f"No events for {team} — refusing to wipe its data.")

    changed = 0
    for fn, d in zip(files, dates):
        path = os.path.join(REPORTS_DIR, fn)
        with open(path, encoding="utf-8") as f:
            rep = json.load(f)
        new = stl_sports.get_data(d, events_override=events)
        if new != rep["sections"].get("stl_sports"):
            rep["sections"]["stl_sports"] = new
            with open(path, "w", encoding="utf-8") as f:
                json.dump(rep, f, indent=2, ensure_ascii=False)
                f.write("\n")
            changed += 1

    index = rebuild_index()
    print(f"updated {changed}/{len(files)} reports")
    for team, badges in index.get("team_badges", {}).items():
        print(f"  {team}: {len(badges)} game days in archive")


if __name__ == "__main__":
    main()
