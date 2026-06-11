"""St. Louis Sports — ESPN's public JSON endpoints, verified live 2026-06-10.

Fixes vs v1 (all confirmed by probing the real API):
- MLB path is sports/baseball/mlb (v1's sports/mlb returns HTTP 400).
- NHL path is sports/hockey/nhl.
- City SC's ESPN team id is 21812 (v1's 17012 returns HTTP 500).
- Game status lives at competitions[0].status, not event.status.
- Scores can be objects ({value, displayValue}) or plain strings.
- Soccer schedules return past results only; upcoming needs ?fixture=true.

Rules: in-season teams only; only data present in the API response — never
fabricate pitchers, goalies, lineups, or series framing.

`events_override` lets the backfill inject a pre-fetched, cached event list
per team (from date-range scoreboard queries) instead of hitting the API for
every backdated day.
"""
from datetime import timedelta

import requests

from config import USER_AGENT
from datefmt import CT, game_time_label, now_ct, parse_espn_date, to_ct

TEAMS = {
    "Cardinals": {
        "sport": "baseball", "league": "mlb", "team_id": "24", "emoji": "⚾",
        "season_months": [2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
    },
    "Blues": {
        "sport": "hockey", "league": "nhl", "team_id": "19", "emoji": "🏒",
        "season_months": [9, 10, 11, 12, 1, 2, 3, 4, 5, 6],
    },
    "City SC": {
        "sport": "soccer", "league": "usa.1", "team_id": "21812", "emoji": "⚽",
        "season_months": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
        "needs_fixture_call": True,
    },
}

SCHEDULE_URL = "https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/teams/{team_id}/schedule"


def _get(url, params=None):
    resp = requests.get(url, params=params, timeout=20,
                        headers={"User-Agent": USER_AGENT})
    resp.raise_for_status()
    return resp.json()


def _score_value(raw):
    """Score may be '7', 7, or {'value': 7.0, 'displayValue': '7'}."""
    if isinstance(raw, dict):
        return raw.get("displayValue") or (
            str(int(raw["value"])) if raw.get("value") is not None else None)
    if raw is None:
        return None
    return str(raw)


def fetch_team_events(team_name):
    """All schedule events for a team (results + fixtures for soccer)."""
    info = TEAMS[team_name]
    url = SCHEDULE_URL.format(**info)
    events = list(_get(url).get("events", []))
    if info.get("needs_fixture_call"):
        try:
            events += _get(url, params={"fixture": "true"}).get("events", [])
        except Exception:
            pass
    return events


def _parse_event(ev, team_id):
    try:
        dt_utc = parse_espn_date(ev["date"])
    except Exception:
        return None
    comp = (ev.get("competitions") or [{}])[0]
    competitors = comp.get("competitors", [])
    if len(competitors) < 2:
        return None

    home = next((c for c in competitors if c.get("homeAway") == "home"), competitors[0])
    away = next((c for c in competitors if c.get("homeAway") == "away"), competitors[1])
    is_home = str(home.get("team", {}).get("id")) == str(team_id)
    us, them = (home, away) if is_home else (away, home)
    opp_team = them.get("team", {})

    status = (comp.get("status") or {}).get("type", {})
    team_score = _score_value(us.get("score"))
    opp_score = _score_value(them.get("score"))

    won = us.get("winner")
    draw = False
    if won is None and status.get("completed") and team_score and opp_score:
        try:
            won = float(team_score) > float(opp_score)
        except ValueError:
            won = None
    if status.get("completed") and team_score is not None and team_score == opp_score:
        draw = True
        won = False

    return {
        "datetime_utc": dt_utc,
        "completed": bool(status.get("completed")),
        "opponent": opp_team.get("shortDisplayName") or opp_team.get("displayName") or "TBD",
        "is_home": is_home,
        "team_score": team_score,
        "opp_score": opp_score,
        "won": bool(won) if won is not None else None,
        "draw": draw,
        "venue": (comp.get("venue") or {}).get("fullName", ""),
    }


def _team_data(team_name, report_date, events):
    info = TEAMS[team_name]
    parsed = [p for p in (_parse_event(ev, info["team_id"]) for ev in events) if p]
    parsed.sort(key=lambda p: p["datetime_utc"])

    yesterday = report_date - timedelta(days=1)
    # For a backdated report, a since-completed game on/after the report date
    # was still "upcoming" from that morning's perspective.
    historical = report_date < now_ct().date()
    yesterdays_game = None
    next_game = None

    for p in parsed:
        game_date_ct = to_ct(p["datetime_utc"]).date()
        if p["completed"] and game_date_ct == yesterday:
            yesterdays_game = p  # keep the latest (handles doubleheaders)
        upcoming = (game_date_ct > report_date) or (
            game_date_ct == report_date and (historical or not p["completed"]))
        if upcoming and next_game is None:
            next_game = p

    if not yesterdays_game and not next_game:
        return None

    def _ser(p, with_score):
        if not p:
            return None
        out = {
            "opponent": p["opponent"],
            "is_home": p["is_home"],
            "venue": p["venue"],
            "datetime_utc": p["datetime_utc"].isoformat(),
        }
        if with_score:
            out.update(team_score=p["team_score"], opp_score=p["opp_score"],
                       won=p["won"], draw=p["draw"])
        else:
            dt_ct = to_ct(p["datetime_utc"])
            out["label"] = game_time_label(dt_ct, report_date)
        return out

    return {
        "team": team_name,
        "emoji": info["emoji"],
        "yesterday": _ser(yesterdays_game, with_score=True),
        "next": _ser(next_game, with_score=False),
    }


def get_data(report_date, events_override=None):
    """Returns {teams: [...]} or None if every team is offseason/silent."""
    teams_out = []
    for team_name, info in TEAMS.items():
        if report_date.month not in info["season_months"]:
            continue
        try:
            if events_override and team_name in events_override:
                events = events_override[team_name]
            else:
                events = fetch_team_events(team_name)
        except Exception:
            continue
        if not events:
            continue
        data = _team_data(team_name, report_date, events)
        if data:
            teams_out.append(data)
    return {"teams": teams_out} if teams_out else None


def format_text(data):
    if not data or not data.get("teams"):
        return None
    lines = []
    for t in data["teams"]:
        parts = []
        y = t.get("yesterday")
        if y:
            if y.get("draw"):
                outcome = "D"
            else:
                outcome = "W" if y.get("won") else "L"
            loc = "vs. " if y["is_home"] else "@ "
            parts.append(f"Yesterday: {outcome} {y['team_score']}-{y['opp_score']} {loc}{y['opponent']}")
        n = t.get("next")
        if n:
            loc = "vs." if n["is_home"] else "@"
            parts.append(f"Next: {n['label']} {loc} {n['opponent']}")
        if parts:
            lines.append(f"{t['emoji']} {t['team']}: " + " | ".join(parts))
    if not lines:
        return None
    return "🦁 ST. LOUIS SPORTS\n" + "\n".join(lines)
