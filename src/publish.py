"""Publishing: write per-day report JSON and rebuild the site index.

docs/data/reports/YYYY-MM-DD.json   one structured report per day (personas only)
docs/data/index.json                date list + per-day badges for the archive
                                    calendar (a date's badge is the Cardinals
                                    result of the game PLAYED that day, which
                                    arrives in the NEXT morning's report)
"""
import json
import os
from datetime import date, timedelta

from config import DOCS_DATA_DIR, REPORTS_DIR, SITE_NAME


def write_report_json(report):
    os.makedirs(REPORTS_DIR, exist_ok=True)
    path = os.path.join(REPORTS_DIR, f"{report['date']}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
        f.write("\n")
    return path


def _badge_from_game(game):
    if not game:
        return None
    if game.get("draw"):
        return "D"
    if game.get("won") is True:
        return "W"
    if game.get("won") is False:
        return "L"
    return None


def rebuild_index():
    os.makedirs(REPORTS_DIR, exist_ok=True)
    dates = sorted(
        fn[:-5] for fn in os.listdir(REPORTS_DIR)
        if fn.endswith(".json") and len(fn) == 15
    )

    badges = {}
    for d in dates:
        path = os.path.join(REPORTS_DIR, f"{d}.json")
        try:
            with open(path, encoding="utf-8") as f:
                rep = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue
        stl = (rep.get("sections") or {}).get("stl_sports") or {}
        for team in stl.get("teams", []):
            game = team.get("yesterday")
            badge = _badge_from_game(game)
            if badge and team.get("team") == "Cardinals":
                game_day = (date.fromisoformat(d) - timedelta(days=1)).isoformat()
                badges[game_day] = badge

    index = {
        "site": SITE_NAME,
        "latest": dates[-1] if dates else None,
        "dates": list(reversed(dates)),
        "badges": badges,
    }
    path = os.path.join(DOCS_DATA_DIR, "index.json")
    os.makedirs(DOCS_DATA_DIR, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
        f.write("\n")
    return index
