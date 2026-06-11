"""Backfill historical reports with REAL data (no synthesis).

    python scripts/backfill.py 2026-05-12 2026-06-10

Per date:
- Word        -> Merriam-Webster per-date archive page
- Quote       -> Wikiquote per-date QOTD subpage (MediaWiki API)
- History     -> Wikipedia OnThisDay (month/day)
- STL sports  -> ESPN schedules fetched ONCE and reused for every date
- Market      -> Wayback Machine snapshot of the WSJ Markets feed for that
                 exact day (or the day before); omitted when no capture exists
- Fact/Song   -> deterministic from local data (seeded by date)
- Spotlight   -> simulated week-by-week so the sequence matches what live
                 runs would have produced; state.json is left at the final week

Existing report files are overwritten (idempotent).
"""
import os
import sys
import time
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

import report as report_mod
from publish import rebuild_index, write_report_json
from sections import spotlight, stl_sports
from sections.spotlight import _save_state, pick_for_week, week_key


def daterange(start, end):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    start = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 2 else date.today() - timedelta(days=29)
    end = date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else date.today()

    print(f"Backfilling {start} .. {end}")

    print("Prefetching ESPN schedules (one set of calls for the whole window)...")
    espn_events = {}
    for team in stl_sports.TEAMS:
        try:
            espn_events[team] = stl_sports.fetch_team_events(team)
            print(f"  {team}: {len(espn_events[team])} events")
        except Exception as e:
            print(f"  {team}: FAILED ({e})")
            espn_events[team] = []

    # Simulate spotlight weeks in order so picks chain correctly
    weeks = []
    for d in daterange(start, end):
        wk = week_key(d)
        if wk not in weeks:
            weeks.append(wk)
    week_picks = {}
    prev = None
    for wk in weeks:
        week_picks[wk] = pick_for_week(wk, previous_persona=prev)
        prev = week_picks[wk]

    summary = []
    for d in daterange(start, end):
        wk = week_key(d)
        state = {"spotlight_week": wk, "spotlight_persona": week_picks[wk]}
        rep = report_mod.build(d, live=False, espn_events=espn_events,
                               state=state, persist_state=False)
        write_report_json(rep)

        present = [k for k, v in rep["sections"].items() if v]
        missing = [k for k, v in rep["sections"].items() if not v]
        summary.append((d.isoformat(), present, missing))
        print(f"{d}  ok: {len(present)}/8  missing: {', '.join(missing) or '-'}")
        time.sleep(0.6)  # be polite to MW / Wikiquote / Wayback

    index = rebuild_index()
    print(f"\nindex.json: {len(index['dates'])} dates, latest {index['latest']}, "
          f"{len(index['badges'])} badge days")

    # Leave live state.json at the final simulated week
    last_wk = week_key(end)
    _save_state({"spotlight_week": last_wk, "spotlight_persona": week_picks[last_wk]})
    print(f"state.json -> {last_wk}: {week_picks[last_wk]}")

    gaps = [(d, m) for d, _, m in summary if m]
    if gaps:
        print("\nDays with omitted sections (expected for weekends/snapshot gaps):")
        for d, m in gaps:
            print(f"  {d}: {', '.join(m)}")


if __name__ == "__main__":
    main()
