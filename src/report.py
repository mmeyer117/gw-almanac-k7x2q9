"""Report assembly: structured data (for the site) + rendered text (for chat).

The structured report contains ONLY persona names — it is what gets committed
to the public repo. Real names are applied at render time from private config
and exist only in the ephemeral message text.
"""
from datetime import datetime, timezone

from config import CHAR_LIMIT
from datefmt import long_date
from sections import history, market, quote, song, sports_fact, spotlight, stl_sports, word


def build(report_date, live=True, espn_events=None, state=None, persist_state=True):
    """Build the structured report dict for a CT calendar date."""
    return {
        "date": report_date.isoformat(),
        "display_date": long_date(report_date),
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sections": {
            "word": word.get_data(report_date),
            "sports_fact": sports_fact.get_data(report_date),
            "stl_sports": stl_sports.get_data(report_date, events_override=espn_events),
            "market": market.get_data(report_date, live=live),
            "quote": quote.get_data(report_date),
            "history": history.get_data(report_date),
            "spotlight": spotlight.get_data(report_date, state=state, persist=persist_state),
            "song": song.get_data(report_date),
        },
    }


def render_text(report, header, name_map=None):
    """The chat-ready plain-text message. None-sections are dropped silently."""
    s = report["sections"]
    blocks = [
        f"{header}\n{report['display_date']}",
        word.format_text(s.get("word")),
        sports_fact.format_text(s.get("sports_fact")),
        stl_sports.format_text(s.get("stl_sports")),
        market.format_text(s.get("market")),
        quote.format_text(s.get("quote")),
        history.format_text(s.get("history")),
        spotlight.format_text(s.get("spotlight"), name_map),
        song.format_text(s.get("song"), name_map),
    ]
    return "\n\n".join(b for b in blocks if b)


def length_warning(text):
    if len(text) > CHAR_LIMIT:
        return f"WARNING: report is {len(text)} chars (limit {CHAR_LIMIT})"
    return None
