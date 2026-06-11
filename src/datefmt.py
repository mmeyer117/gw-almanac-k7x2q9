"""Cross-platform date formatting (Windows lacks strftime %-d / %-m / %-I)."""
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

CT = ZoneInfo("America/Chicago")
UTC = ZoneInfo("UTC")


def now_ct():
    return datetime.now(CT)


def long_date(d):
    """'Wednesday, June 10, 2026' — no platform-specific padding flags."""
    return f"{d:%A}, {d:%B} {d.day}, {d.year}"


def time_12h(dt):
    """'7:15 PM' from an aware datetime."""
    hour = dt.hour % 12 or 12
    ampm = "AM" if dt.hour < 12 else "PM"
    return f"{hour}:{dt.minute:02d} {ampm}"


def game_time_label(dt_ct, report_date):
    """'Today 7:15 PM CT' / 'Tomorrow 1:15 PM CT' / 'Sat 6/13, 7:15 PM CT'."""
    d = dt_ct.date()
    if d == report_date:
        day = "Today"
    elif d == report_date + timedelta(days=1):
        day = "Tomorrow"
    else:
        day = f"{dt_ct:%a} {dt_ct.month}/{dt_ct.day},"
    return f"{day} {time_12h(dt_ct)} CT"


def parse_espn_date(s):
    """ESPN dates like '2026-06-09T23:10Z' -> aware UTC datetime."""
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def to_ct(dt):
    return dt.astimezone(CT)
